#!/usr/bin/env python3
"""
WhatsApp Group Wrapped - Data Extraction Script
Runs all SQL queries and outputs JSON for Claude to analyze.
Includes viral features: streaks, emoji stats, reply speed, catchphrases, etc.
"""

import sqlite3
import json
import sys
import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta

# WhatsApp epoch offset (Core Data timestamp to Unix)
WHATSAPP_EPOCH = 978307200

# Database path
DB_PATH = os.path.expanduser(
    "~/Library/Group Containers/group.net.whatsapp.WhatsApp.shared/ChatStorage.sqlite"
)

# Emoji regex pattern
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002702-\U000027B0"  # dingbats
    "\U000024C2-\U0001F251"  # enclosed characters
    "\U0001F900-\U0001F9FF"  # supplemental symbols
    "\U0001FA00-\U0001FA6F"  # chess symbols
    "\U0001FA70-\U0001FAFF"  # symbols extended-A
    "\U00002600-\U000026FF"  # misc symbols
    "\U00002700-\U000027BF"  # dingbats
    "]+",
    flags=re.UNICODE
)


def get_connection():
    """Get database connection."""
    if not os.path.exists(DB_PATH):
        print(json.dumps({"error": f"WhatsApp database not found at {DB_PATH}"}))
        sys.exit(1)
    return sqlite3.connect(DB_PATH)


def list_chats():
    """List available chats with message counts."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ZPARTNERNAME, COUNT(m.Z_PK) as msg_count
        FROM ZWACHATSESSION s
        LEFT JOIN ZWAMESSAGE m ON m.ZCHATSESSION = s.Z_PK
        WHERE ZPARTNERNAME IS NOT NULL
        GROUP BY ZPARTNERNAME
        ORDER BY msg_count DESC
        LIMIT 30;
    """)
    chats = [{"name": row[0], "message_count": row[1]} for row in cursor.fetchall()]
    conn.close()
    return {"chats": chats}


def extract_emojis(text):
    """Extract all emojis from text."""
    if not text:
        return []
    return EMOJI_PATTERN.findall(text)


def get_common_phrases(messages, min_count=3, min_words=2, max_words=5):
    """Extract common phrases (n-grams) from messages."""
    phrase_counts = Counter()

    for msg in messages:
        text = msg.get("text", "")
        if not text:
            continue
        # Clean and split
        words = text.lower().split()
        # Generate n-grams
        for n in range(min_words, min(max_words + 1, len(words) + 1)):
            for i in range(len(words) - n + 1):
                phrase = " ".join(words[i:i+n])
                # Skip if mostly punctuation or very short
                if len(phrase) > 5 and phrase.isascii():
                    phrase_counts[phrase] += 1

    # Return phrases that appear at least min_count times
    return [{"phrase": phrase, "count": count}
            for phrase, count in phrase_counts.most_common(20)
            if count >= min_count]


def analyze_group(group_name):
    """Run all analysis queries for a group (last 12 months only)."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    data = {"group_name": group_name}

    # Calculate 12 months ago in WhatsApp timestamp format
    # WhatsApp uses Core Data timestamp (seconds since 2001-01-01)
    twelve_months_ago = datetime.now() - timedelta(days=365)
    twelve_months_ago_unix = twelve_months_ago.timestamp()
    twelve_months_ago_wa = twelve_months_ago_unix - WHATSAPP_EPOCH

    data["analysis_period"] = {
        "from": twelve_months_ago.strftime("%Y-%m-%d"),
        "to": datetime.now().strftime("%Y-%m-%d"),
        "months": 12
    }

    # 1. Basic Statistics (last 12 months)
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN ZTEXT IS NOT NULL THEN 1 ELSE 0 END) as text_msgs,
            SUM(CASE WHEN ZISFROMME = 1 THEN 1 ELSE 0 END) as from_me,
            SUM(CASE WHEN ZISFROMME = 0 THEN 1 ELSE 0 END) as from_others,
            datetime(MIN(m.ZMESSAGEDATE) + 978307200, 'unixepoch', 'localtime') as first_msg,
            datetime(MAX(m.ZMESSAGEDATE) + 978307200, 'unixepoch', 'localtime') as last_msg,
            CAST((julianday('now') - julianday(datetime(MIN(m.ZMESSAGEDATE) + 978307200, 'unixepoch'))) AS INTEGER) as days_active
        FROM ZWAMESSAGE m
        JOIN ZWACHATSESSION s ON m.ZCHATSESSION = s.Z_PK
        WHERE s.ZPARTNERNAME = ? AND m.ZMESSAGEDATE >= ?;
    """, (group_name, twelve_months_ago_wa))
    row = cursor.fetchone()
    if row:
        data["basic_stats"] = {
            "total_messages": row["total"],
            "text_messages": row["text_msgs"],
            "from_me": row["from_me"],
            "from_others": row["from_others"],
            "first_message": row["first_msg"],
            "last_message": row["last_msg"],
            "days_active": row["days_active"]
        }

    # 2. Hourly Distribution
    cursor.execute("""
        SELECT
            CAST(strftime('%H', datetime(m.ZMESSAGEDATE + 978307200, 'unixepoch', 'localtime')) AS INTEGER) as hour,
            COUNT(*) as count
        FROM ZWAMESSAGE m
        JOIN ZWACHATSESSION s ON m.ZCHATSESSION = s.Z_PK
        WHERE s.ZPARTNERNAME = ? AND m.ZMESSAGEDATE >= ?
        GROUP BY hour ORDER BY hour;
    """, (group_name, twelve_months_ago_wa))
    data["hourly_distribution"] = [{"hour": row["hour"], "count": row["count"]} for row in cursor.fetchall()]

    # Find peak hour
    if data["hourly_distribution"]:
        peak = max(data["hourly_distribution"], key=lambda x: x["count"])
        data["peak_hour"] = peak["hour"]

    # 3. Daily Distribution (0=Sunday, 6=Saturday)
    cursor.execute("""
        SELECT
            CAST(strftime('%w', datetime(m.ZMESSAGEDATE + 978307200, 'unixepoch', 'localtime')) AS INTEGER) as dow,
            COUNT(*) as count
        FROM ZWAMESSAGE m
        JOIN ZWACHATSESSION s ON m.ZCHATSESSION = s.Z_PK
        WHERE s.ZPARTNERNAME = ? AND m.ZMESSAGEDATE >= ?
        GROUP BY dow ORDER BY dow;
    """, (group_name, twelve_months_ago_wa))
    days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    data["daily_distribution"] = [{"day": days[row["dow"]], "day_num": row["dow"], "count": row["count"]} for row in cursor.fetchall()]

    # 4. Monthly Trend
    cursor.execute("""
        SELECT
            strftime('%Y-%m', datetime(m.ZMESSAGEDATE + 978307200, 'unixepoch', 'localtime')) as month,
            COUNT(*) as count
        FROM ZWAMESSAGE m
        JOIN ZWACHATSESSION s ON m.ZCHATSESSION = s.Z_PK
        WHERE s.ZPARTNERNAME = ? AND m.ZMESSAGEDATE >= ?
        GROUP BY month ORDER BY month;
    """, (group_name, twelve_months_ago_wa))
    data["monthly_trend"] = [{"month": row["month"], "count": row["count"]} for row in cursor.fetchall()]

    # 5. Per-Person Message Counts
    cursor.execute("""
        SELECT
            CASE
                WHEN m.ZISFROMME = 1 THEN 'Me'
                WHEN gm.Z_PK IS NOT NULL AND p.ZPUSHNAME IS NOT NULL THEN p.ZPUSHNAME
                WHEN p2.ZPUSHNAME IS NOT NULL THEN p2.ZPUSHNAME
                ELSE 'Unknown'
            END as sender,
            COUNT(*) as count
        FROM ZWAMESSAGE m
        JOIN ZWACHATSESSION s ON m.ZCHATSESSION = s.Z_PK
        LEFT JOIN ZWAGROUPMEMBER gm ON m.ZGROUPMEMBER = gm.Z_PK
        LEFT JOIN ZWAPROFILEPUSHNAME p ON gm.ZMEMBERJID = p.ZJID
        LEFT JOIN ZWAPROFILEPUSHNAME p2 ON m.ZFROMJID = p2.ZJID
        WHERE s.ZPARTNERNAME = ? AND m.ZMESSAGEDATE >= ?
        GROUP BY sender ORDER BY count DESC;
    """, (group_name, twelve_months_ago_wa))
    total = data["basic_stats"]["total_messages"] if data.get("basic_stats") else 1
    data["per_person_counts"] = [
        {"sender": row["sender"], "count": row["count"], "percentage": round(row["count"] / total * 100, 1)}
        for row in cursor.fetchall()
    ]

    # 6. Late Night Texters (11PM-4AM)
    cursor.execute("""
        SELECT
            CASE
                WHEN m.ZISFROMME = 1 THEN 'Me'
                WHEN gm.Z_PK IS NOT NULL AND p.ZPUSHNAME IS NOT NULL THEN p.ZPUSHNAME
                WHEN p2.ZPUSHNAME IS NOT NULL THEN p2.ZPUSHNAME
                ELSE 'Unknown'
            END as sender,
            COUNT(*) as count
        FROM ZWAMESSAGE m
        JOIN ZWACHATSESSION s ON m.ZCHATSESSION = s.Z_PK
        LEFT JOIN ZWAGROUPMEMBER gm ON m.ZGROUPMEMBER = gm.Z_PK
        LEFT JOIN ZWAPROFILEPUSHNAME p ON gm.ZMEMBERJID = p.ZJID
        LEFT JOIN ZWAPROFILEPUSHNAME p2 ON m.ZFROMJID = p2.ZJID
        WHERE s.ZPARTNERNAME = ? AND m.ZMESSAGEDATE >= ?
            AND CAST(strftime('%H', datetime(m.ZMESSAGEDATE + 978307200, 'unixepoch', 'localtime')) AS INTEGER) IN (23, 0, 1, 2, 3, 4)
        GROUP BY sender ORDER BY count DESC LIMIT 5;
    """, (group_name, twelve_months_ago_wa))
    data["late_night_texters"] = [{"sender": row["sender"], "count": row["count"]} for row in cursor.fetchall()]

    # 7. Early Morning Texters (5AM-8AM)
    cursor.execute("""
        SELECT
            CASE
                WHEN m.ZISFROMME = 1 THEN 'Me'
                WHEN gm.Z_PK IS NOT NULL AND p.ZPUSHNAME IS NOT NULL THEN p.ZPUSHNAME
                WHEN p2.ZPUSHNAME IS NOT NULL THEN p2.ZPUSHNAME
                ELSE 'Unknown'
            END as sender,
            COUNT(*) as count
        FROM ZWAMESSAGE m
        JOIN ZWACHATSESSION s ON m.ZCHATSESSION = s.Z_PK
        LEFT JOIN ZWAGROUPMEMBER gm ON m.ZGROUPMEMBER = gm.Z_PK
        LEFT JOIN ZWAPROFILEPUSHNAME p ON gm.ZMEMBERJID = p.ZJID
        LEFT JOIN ZWAPROFILEPUSHNAME p2 ON m.ZFROMJID = p2.ZJID
        WHERE s.ZPARTNERNAME = ? AND m.ZMESSAGEDATE >= ?
            AND CAST(strftime('%H', datetime(m.ZMESSAGEDATE + 978307200, 'unixepoch', 'localtime')) AS INTEGER) IN (5, 6, 7, 8)
        GROUP BY sender ORDER BY count DESC LIMIT 5;
    """, (group_name, twelve_months_ago_wa))
    data["early_morning_texters"] = [{"sender": row["sender"], "count": row["count"]} for row in cursor.fetchall()]

    # 8. Average Message Length Per Person
    cursor.execute("""
        SELECT
            CASE
                WHEN m.ZISFROMME = 1 THEN 'Me'
                WHEN gm.Z_PK IS NOT NULL AND p.ZPUSHNAME IS NOT NULL THEN p.ZPUSHNAME
                WHEN p2.ZPUSHNAME IS NOT NULL THEN p2.ZPUSHNAME
                ELSE 'Unknown'
            END as sender,
            ROUND(AVG(LENGTH(m.ZTEXT)), 1) as avg_len,
            COUNT(*) as msg_count
        FROM ZWAMESSAGE m
        JOIN ZWACHATSESSION s ON m.ZCHATSESSION = s.Z_PK
        LEFT JOIN ZWAGROUPMEMBER gm ON m.ZGROUPMEMBER = gm.Z_PK
        LEFT JOIN ZWAPROFILEPUSHNAME p ON gm.ZMEMBERJID = p.ZJID
        LEFT JOIN ZWAPROFILEPUSHNAME p2 ON m.ZFROMJID = p2.ZJID
        WHERE s.ZPARTNERNAME = ? AND m.ZTEXT IS NOT NULL AND m.ZMESSAGEDATE >= ?
        GROUP BY sender HAVING msg_count >= 5 ORDER BY avg_len DESC;
    """, (group_name, twelve_months_ago_wa))
    data["avg_message_length"] = [
        {"sender": row["sender"], "avg_length": row["avg_len"], "message_count": row["msg_count"]}
        for row in cursor.fetchall()
    ]

    # 9. Media Shared Per Person
    cursor.execute("""
        SELECT
            CASE
                WHEN m.ZISFROMME = 1 THEN 'Me'
                WHEN gm.Z_PK IS NOT NULL AND p.ZPUSHNAME IS NOT NULL THEN p.ZPUSHNAME
                WHEN p2.ZPUSHNAME IS NOT NULL THEN p2.ZPUSHNAME
                ELSE 'Unknown'
            END as sender,
            COUNT(*) as count
        FROM ZWAMESSAGE m
        JOIN ZWACHATSESSION s ON m.ZCHATSESSION = s.Z_PK
        LEFT JOIN ZWAGROUPMEMBER gm ON m.ZGROUPMEMBER = gm.Z_PK
        LEFT JOIN ZWAPROFILEPUSHNAME p ON gm.ZMEMBERJID = p.ZJID
        LEFT JOIN ZWAPROFILEPUSHNAME p2 ON m.ZFROMJID = p2.ZJID
        WHERE s.ZPARTNERNAME = ? AND m.ZTEXT IS NULL AND m.ZMEDIAITEM IS NOT NULL AND m.ZMESSAGEDATE >= ?
        GROUP BY sender ORDER BY count DESC LIMIT 5;
    """, (group_name, twelve_months_ago_wa))
    data["media_sharers"] = [{"sender": row["sender"], "count": row["count"]} for row in cursor.fetchall()]

    # 10. Links Shared Per Person
    cursor.execute("""
        SELECT
            CASE
                WHEN m.ZISFROMME = 1 THEN 'Me'
                WHEN gm.Z_PK IS NOT NULL AND p.ZPUSHNAME IS NOT NULL THEN p.ZPUSHNAME
                WHEN p2.ZPUSHNAME IS NOT NULL THEN p2.ZPUSHNAME
                ELSE 'Unknown'
            END as sender,
            COUNT(*) as count
        FROM ZWAMESSAGE m
        JOIN ZWACHATSESSION s ON m.ZCHATSESSION = s.Z_PK
        LEFT JOIN ZWAGROUPMEMBER gm ON m.ZGROUPMEMBER = gm.Z_PK
        LEFT JOIN ZWAPROFILEPUSHNAME p ON gm.ZMEMBERJID = p.ZJID
        LEFT JOIN ZWAPROFILEPUSHNAME p2 ON m.ZFROMJID = p2.ZJID
        WHERE s.ZPARTNERNAME = ? AND m.ZMESSAGEDATE >= ?
            AND (m.ZTEXT LIKE '%http://%' OR m.ZTEXT LIKE '%https://%' OR m.ZTEXT LIKE '%www.%')
        GROUP BY sender ORDER BY count DESC LIMIT 5;
    """, (group_name, twelve_months_ago_wa))
    data["link_sharers"] = [{"sender": row["sender"], "count": row["count"]} for row in cursor.fetchall()]

    # 11. Questions Asked Per Person
    cursor.execute("""
        SELECT
            CASE
                WHEN m.ZISFROMME = 1 THEN 'Me'
                WHEN gm.Z_PK IS NOT NULL AND p.ZPUSHNAME IS NOT NULL THEN p.ZPUSHNAME
                WHEN p2.ZPUSHNAME IS NOT NULL THEN p2.ZPUSHNAME
                ELSE 'Unknown'
            END as sender,
            COUNT(*) as count
        FROM ZWAMESSAGE m
        JOIN ZWACHATSESSION s ON m.ZCHATSESSION = s.Z_PK
        LEFT JOIN ZWAGROUPMEMBER gm ON m.ZGROUPMEMBER = gm.Z_PK
        LEFT JOIN ZWAPROFILEPUSHNAME p ON gm.ZMEMBERJID = p.ZJID
        LEFT JOIN ZWAPROFILEPUSHNAME p2 ON m.ZFROMJID = p2.ZJID
        WHERE s.ZPARTNERNAME = ? AND m.ZTEXT LIKE '%?%' AND m.ZMESSAGEDATE >= ?
        GROUP BY sender ORDER BY count DESC LIMIT 5;
    """, (group_name, twelve_months_ago_wa))
    data["question_askers"] = [{"sender": row["sender"], "count": row["count"]} for row in cursor.fetchall()]

    # === VIRAL FEATURES ===

    # 12. Busiest Day Ever (in last 12 months)
    cursor.execute("""
        SELECT
            date(datetime(m.ZMESSAGEDATE + 978307200, 'unixepoch', 'localtime')) as day,
            COUNT(*) as count
        FROM ZWAMESSAGE m
        JOIN ZWACHATSESSION s ON m.ZCHATSESSION = s.Z_PK
        WHERE s.ZPARTNERNAME = ? AND m.ZMESSAGEDATE >= ?
        GROUP BY day ORDER BY count DESC LIMIT 1;
    """, (group_name, twelve_months_ago_wa))
    row = cursor.fetchone()
    if row:
        data["busiest_day"] = {"date": row["day"], "message_count": row["count"]}

    # 13. Longest Silence (gap between messages in last 12 months)
    cursor.execute("""
        SELECT
            datetime(m.ZMESSAGEDATE + 978307200, 'unixepoch', 'localtime') as msg_time,
            m.ZMESSAGEDATE as raw_date
        FROM ZWAMESSAGE m
        JOIN ZWACHATSESSION s ON m.ZCHATSESSION = s.Z_PK
        WHERE s.ZPARTNERNAME = ? AND m.ZMESSAGEDATE >= ?
        ORDER BY m.ZMESSAGEDATE;
    """, (group_name, twelve_months_ago_wa))
    messages_times = cursor.fetchall()

    longest_gap = 0
    gap_start = None
    gap_end = None

    for i in range(1, len(messages_times)):
        gap = messages_times[i]["raw_date"] - messages_times[i-1]["raw_date"]
        if gap > longest_gap:
            longest_gap = gap
            gap_start = messages_times[i-1]["msg_time"]
            gap_end = messages_times[i]["msg_time"]

    if longest_gap > 0:
        data["longest_silence"] = {
            "gap_hours": round(longest_gap / 3600, 1),
            "gap_days": round(longest_gap / 86400, 1),
            "from": gap_start,
            "to": gap_end
        }

    # 14. Message Streak Data (last 12 months)
    cursor.execute("""
        SELECT DISTINCT date(datetime(m.ZMESSAGEDATE + 978307200, 'unixepoch', 'localtime')) as day
        FROM ZWAMESSAGE m
        JOIN ZWACHATSESSION s ON m.ZCHATSESSION = s.Z_PK
        WHERE s.ZPARTNERNAME = ? AND m.ZMESSAGEDATE >= ?
        ORDER BY day;
    """, (group_name, twelve_months_ago_wa))
    active_days = [row["day"] for row in cursor.fetchall()]

    # Calculate streaks
    if active_days:
        max_streak = 1
        current_streak = 1

        for i in range(1, len(active_days)):
            prev_date = datetime.strptime(active_days[i-1], "%Y-%m-%d")
            curr_date = datetime.strptime(active_days[i], "%Y-%m-%d")

            if (curr_date - prev_date).days == 1:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 1

        # Check if current streak is still active (includes today or yesterday)
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        is_active = active_days[-1] in [today, yesterday]

        # Calculate current streak
        current_streak = 1
        for i in range(len(active_days) - 1, 0, -1):
            prev_date = datetime.strptime(active_days[i-1], "%Y-%m-%d")
            curr_date = datetime.strptime(active_days[i], "%Y-%m-%d")

            if (curr_date - prev_date).days == 1:
                current_streak += 1
            else:
                break

        data["streak_data"] = {
            "longest_streak": max_streak,
            "current_streak": current_streak if is_active else 0,
            "is_active": is_active,
            "total_active_days": len(active_days)
        }

    # 15. Conversation Starters (who sends first message of the day, last 12 months)
    cursor.execute("""
        WITH daily_first AS (
            SELECT
                date(datetime(m.ZMESSAGEDATE + 978307200, 'unixepoch', 'localtime')) as day,
                MIN(m.ZMESSAGEDATE) as first_msg_time
            FROM ZWAMESSAGE m
            JOIN ZWACHATSESSION s ON m.ZCHATSESSION = s.Z_PK
            WHERE s.ZPARTNERNAME = ? AND m.ZMESSAGEDATE >= ?
            GROUP BY day
        )
        SELECT
            CASE
                WHEN m.ZISFROMME = 1 THEN 'Me'
                WHEN gm.Z_PK IS NOT NULL AND p.ZPUSHNAME IS NOT NULL THEN p.ZPUSHNAME
                WHEN p2.ZPUSHNAME IS NOT NULL THEN p2.ZPUSHNAME
                ELSE 'Unknown'
            END as sender,
            COUNT(*) as count
        FROM ZWAMESSAGE m
        JOIN ZWACHATSESSION s ON m.ZCHATSESSION = s.Z_PK
        JOIN daily_first df ON m.ZMESSAGEDATE = df.first_msg_time
        LEFT JOIN ZWAGROUPMEMBER gm ON m.ZGROUPMEMBER = gm.Z_PK
        LEFT JOIN ZWAPROFILEPUSHNAME p ON gm.ZMEMBERJID = p.ZJID
        LEFT JOIN ZWAPROFILEPUSHNAME p2 ON m.ZFROMJID = p2.ZJID
        WHERE s.ZPARTNERNAME = ? AND m.ZMESSAGEDATE >= ?
        GROUP BY sender ORDER BY count DESC;
    """, (group_name, twelve_months_ago_wa, group_name, twelve_months_ago_wa))
    data["conversation_starters"] = [{"sender": row["sender"], "count": row["count"]} for row in cursor.fetchall()]

    # 16. Get all messages with sender info for emoji and phrase analysis (last 12 months)
    cursor.execute("""
        SELECT
            CASE
                WHEN m.ZISFROMME = 1 THEN 'Me'
                WHEN gm.Z_PK IS NOT NULL AND p.ZPUSHNAME IS NOT NULL THEN p.ZPUSHNAME
                WHEN p2.ZPUSHNAME IS NOT NULL THEN p2.ZPUSHNAME
                ELSE 'Unknown'
            END as sender,
            m.ZTEXT as text,
            datetime(m.ZMESSAGEDATE + 978307200, 'unixepoch', 'localtime') as time
        FROM ZWAMESSAGE m
        JOIN ZWACHATSESSION s ON m.ZCHATSESSION = s.Z_PK
        LEFT JOIN ZWAGROUPMEMBER gm ON m.ZGROUPMEMBER = gm.Z_PK
        LEFT JOIN ZWAPROFILEPUSHNAME p ON gm.ZMEMBERJID = p.ZJID
        LEFT JOIN ZWAPROFILEPUSHNAME p2 ON m.ZFROMJID = p2.ZJID
        WHERE s.ZPARTNERNAME = ? AND m.ZTEXT IS NOT NULL AND m.ZMESSAGEDATE >= ?
        ORDER BY m.ZMESSAGEDATE DESC;
    """, (group_name, twelve_months_ago_wa))
    all_messages = [{"sender": row["sender"], "text": row["text"], "time": row["time"]} for row in cursor.fetchall()]

    # 17. Emoji Stats Per Person
    emoji_by_person = defaultdict(list)
    for msg in all_messages:
        emojis = extract_emojis(msg["text"])
        if emojis:
            emoji_by_person[msg["sender"]].extend(emojis)

    emoji_stats = []
    for sender, emojis in emoji_by_person.items():
        emoji_counter = Counter(emojis)
        top_emojis = emoji_counter.most_common(5)
        emoji_stats.append({
            "sender": sender,
            "total_emojis": len(emojis),
            "unique_emojis": len(emoji_counter),
            "top_emojis": [{"emoji": e, "count": c} for e, c in top_emojis]
        })

    emoji_stats.sort(key=lambda x: x["total_emojis"], reverse=True)
    data["emoji_stats"] = emoji_stats

    # 18. Common Phrases Per Person
    phrases_by_person = {}
    person_messages = defaultdict(list)
    for msg in all_messages:
        person_messages[msg["sender"]].append(msg)

    for sender, msgs in person_messages.items():
        phrases = get_common_phrases(msgs)
        if phrases:
            phrases_by_person[sender] = phrases[:5]  # Top 5 phrases per person

    data["catchphrases"] = phrases_by_person

    # 19. Reply Speed Analysis (last 12 months)
    cursor.execute("""
        SELECT
            CASE
                WHEN m.ZISFROMME = 1 THEN 'Me'
                WHEN gm.Z_PK IS NOT NULL AND p.ZPUSHNAME IS NOT NULL THEN p.ZPUSHNAME
                WHEN p2.ZPUSHNAME IS NOT NULL THEN p2.ZPUSHNAME
                ELSE 'Unknown'
            END as sender,
            m.ZMESSAGEDATE as msg_time,
            LAG(m.ZMESSAGEDATE) OVER (ORDER BY m.ZMESSAGEDATE) as prev_time,
            LAG(CASE
                WHEN m.ZISFROMME = 1 THEN 'Me'
                WHEN gm.Z_PK IS NOT NULL AND p.ZPUSHNAME IS NOT NULL THEN p.ZPUSHNAME
                WHEN p2.ZPUSHNAME IS NOT NULL THEN p2.ZPUSHNAME
                ELSE 'Unknown'
            END) OVER (ORDER BY m.ZMESSAGEDATE) as prev_sender
        FROM ZWAMESSAGE m
        JOIN ZWACHATSESSION s ON m.ZCHATSESSION = s.Z_PK
        LEFT JOIN ZWAGROUPMEMBER gm ON m.ZGROUPMEMBER = gm.Z_PK
        LEFT JOIN ZWAPROFILEPUSHNAME p ON gm.ZMEMBERJID = p.ZJID
        LEFT JOIN ZWAPROFILEPUSHNAME p2 ON m.ZFROMJID = p2.ZJID
        WHERE s.ZPARTNERNAME = ? AND m.ZMESSAGEDATE >= ?
        ORDER BY m.ZMESSAGEDATE;
    """, (group_name, twelve_months_ago_wa))

    reply_times = defaultdict(list)
    for row in cursor.fetchall():
        if row["prev_time"] and row["prev_sender"] and row["sender"] != row["prev_sender"]:
            gap = row["msg_time"] - row["prev_time"]
            # Only count replies within 24 hours
            if 0 < gap < 86400:
                reply_times[row["sender"]].append(gap)

    reply_speed = []
    for sender, times in reply_times.items():
        if len(times) >= 5:  # Need at least 5 replies for meaningful data
            avg_seconds = sum(times) / len(times)
            reply_speed.append({
                "sender": sender,
                "avg_reply_seconds": round(avg_seconds, 0),
                "avg_reply_minutes": round(avg_seconds / 60, 1),
                "reply_count": len(times)
            })

    reply_speed.sort(key=lambda x: x["avg_reply_seconds"])
    data["reply_speed"] = reply_speed

    # 20. Sample Messages for Personality Analysis (last 200)
    data["sample_messages"] = all_messages[:200]

    conn.close()
    return data


def redact_data(data):
    """Replace all names with Person 1, Person 2, etc."""
    # Build name mapping
    all_names = set()

    # Collect all names from various sections
    name_sections = [
        "per_person_counts", "late_night_texters", "early_morning_texters",
        "avg_message_length", "media_sharers", "link_sharers", "question_askers",
        "conversation_starters", "reply_speed", "emoji_stats"
    ]

    for key in name_sections:
        if key in data:
            for item in data[key]:
                if item.get("sender") and item["sender"] not in ["Me", "Unknown", "Other"]:
                    all_names.add(item["sender"])

    for msg in data.get("sample_messages", []):
        if msg.get("sender") and msg["sender"] not in ["Me", "Unknown", "Other"]:
            all_names.add(msg["sender"])

    if "catchphrases" in data:
        for sender in data["catchphrases"].keys():
            if sender not in ["Me", "Unknown", "Other"]:
                all_names.add(sender)

    # Create mapping (sorted for consistency)
    name_mapping = {name: f"Person {i+1}" for i, name in enumerate(sorted(all_names))}
    name_mapping["Me"] = "Me"
    name_mapping["Unknown"] = "Unknown"
    name_mapping["Other"] = "Other"

    # Apply redaction
    data["group_name"] = "[REDACTED GROUP]"

    for key in name_sections:
        if key in data:
            for item in data[key]:
                if item.get("sender"):
                    item["sender"] = name_mapping.get(item["sender"], item["sender"])

    for msg in data.get("sample_messages", []):
        if msg.get("sender"):
            msg["sender"] = name_mapping.get(msg["sender"], msg["sender"])

    if "catchphrases" in data:
        new_catchphrases = {}
        for sender, phrases in data["catchphrases"].items():
            new_sender = name_mapping.get(sender, sender)
            new_catchphrases[new_sender] = phrases
        data["catchphrases"] = new_catchphrases

    # Include private mapping at the end
    data["_private_name_mapping"] = {v: k for k, v in name_mapping.items() if k not in ["Me", "Unknown", "Other"]}

    return data


def main():
    if len(sys.argv) < 2:
        # No arguments - list chats
        print(json.dumps(list_chats(), indent=2, ensure_ascii=False))
        return

    group_name = sys.argv[1]
    redact = "--redact" in sys.argv

    data = analyze_group(group_name)

    if redact:
        data = redact_data(data)

    print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
