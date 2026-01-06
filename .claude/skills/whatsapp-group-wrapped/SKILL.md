# WhatsApp Group Wrapped

Analyze your WhatsApp group chats from the **last 12 months** and generate a viral-worthy report with roasts, awards, and shareable stats!

## Description

This skill reads your local WhatsApp database (macOS only) and generates a comprehensive, entertaining analysis designed for sharing on social media. Everything runs locally - your data never leaves your machine.

## Usage

```
/whatsapp-group-wrapped [group-name]
```

With privacy mode (replaces all names with Person 1, Person 2, etc.):
```
/whatsapp-group-wrapped [group-name] --redact
```

List available chats:
```
/whatsapp-group-wrapped
```

## Requirements

- macOS with WhatsApp Desktop installed
- Python 3 (comes pre-installed on macOS)
- The WhatsApp database at: `~/Library/Group Containers/group.net.whatsapp.WhatsApp.shared/ChatStorage.sqlite`

## Privacy Note

All analysis happens locally on your machine. No data is sent anywhere.

---

## Invocation

When the user asks to analyze a WhatsApp group, run the Python script to get all data, then generate the FULL report with ALL 10 sections.

### Step 1: Get Data

```bash
python3 ~/.claude/skills/whatsapp-group-wrapped/references/whatsapp_data.py "GROUP_NAME"

# Or with redacted names:
python3 ~/.claude/skills/whatsapp-group-wrapped/references/whatsapp_data.py "GROUP_NAME" --redact
```

The script outputs JSON with:
- `analysis_period` - The 12-month window being analyzed (from/to dates)
- `basic_stats` - Total messages, date range, days active
- `peak_hour` - Most active hour
- `per_person_counts` - Message count and percentage per person
- `streak_data` - Longest streak, current streak, active days
- `busiest_day` - The single busiest day ever
- `longest_silence` - Longest gap between messages
- `late_night_texters` - Who texts at 11PM-4AM
- `early_morning_texters` - Who texts at 5AM-8AM
- `reply_speed` - Average reply time per person
- `conversation_starters` - Who initiates conversations
- `emoji_stats` - Emoji usage per person with favorites
- `avg_message_length` - Message length per person
- `media_sharers` - Who shares the most media
- `link_sharers` - Who shares the most links
- `question_askers` - Who asks the most questions
- `catchphrases` - Common phrases per person
- `sample_messages` - Last 200 messages for personality analysis

---

### Step 2: Generate the FULL Report

**⚠️ CRITICAL: Your response MUST start with the ASCII Summary Card below. No introduction, no preamble, no "Here's your analysis" - just output the card FIRST.**

Generate ALL 10 sections in order. **This is not optional - every section must be included.**

---

## SECTION 1: THE SHAREABLE SUMMARY CARD

⚠️ **THIS IS YOUR FIRST OUTPUT. START HERE. DO NOT SKIP.**

Your VERY FIRST output must be a custom ASCII card designed specifically for THIS group.

**Design the card based on what makes THIS group unique:**
- Analyze the data to find the 4-6 MOST interesting/funny/surprising stats
- Choose stats that would make group members laugh or say "that's so us!"
- The layout, emojis, and emphasis should reflect the group's personality
- Create a witty tagline that captures the group's soul

**Use box-drawing characters (╔ ╗ ╚ ╝ ║ ═) and MUST include:**
- Group name with a relevant emoji in the title
- A "Chat Personality Type" (create one that fits THIS group - e.g., "THE 3AM PHILOSOPHERS", "THE MEME FACTORY", "THE WORRY CIRCLE", or invent your own)
- 4-6 standout stats with emojis (pick the most interesting from the data)
- A custom witty tagline at the bottom
- "📸 Screenshot this!" call-to-action

**Example structure** (but customize stats based on what's interesting):
```
╔═══════════════════════════════════════════════════════════╗
║          🫖 CHAI FAMILY • 2025 WRAPPED 🫖             ║
╠═══════════════════════════════════════════════════════════╣
║                                                       ║
║   [4-6 lines of the MOST interesting stats           ║
║    formatted with emojis, tailored to THIS group]    ║
║                                                       ║
║   💬 Chat Personality: [CUSTOM TYPE FOR THIS GROUP]   ║
║                                                       ║
║   "[Witty tagline that captures THIS group's vibe]"  ║
║                                                       ║
╚═══════════════════════════════════════════════════════════╝
         📸 Screenshot this and tag your family!
```

**The card should feel like it was made FOR this specific group, not a generic template.**

---

## SECTION 2: HONORS 🏆

Give each person exactly **ONE award** based on their most distinctive data pattern. Pick the trait that defines them most.

**One award per person. Choose the BEST fit:**
- 👑 The Conversation Starter
- 🦉 The Night Owl
- 📚 The Novelist
- ⚡ The Speed Demon
- 💀 The Slow Responder
- 📸 The Paparazzi
- 🔗 The Link Curator
- ❓ The Question Asker
- 🎭 The Emoji Artist
- 🤫 The Silent Observer

Format: Name, award title, the stat that earned it, and a witty one-liner.

---

## SECTION 3: THE ROASTS 🔥

Generate gentle, funny roasts for EACH person based on their actual data patterns. These should be:
- Based on REAL patterns from the data (makes them hit harder)
- Gentle and loving, not mean
- Specific enough to feel personal
- Share-worthy (people should want to tag the person)

**Roast Templates (customize with actual data):**

For slow repliers:
> "Takes 3 hours to reply to a text but somehow always knows what everyone's doing"

For verbose texters:
> "Types like they're getting paid per word. Every message is a TED talk."

For emoji users:
> "Has never sent a message without an emoji. Literally incapable."

For night owls:
> "Their phone's Do Not Disturb mode is purely decorative"

For early birds:
> "Sends 'Good morning!' at 5:47 AM like that's a normal thing to do"

For lurkers:
> "Has read 847 messages. Replied to 12. We see you."

For media sharers:
> "The family paparazzi. No moment is too small to document."

---

## SECTION 4: REPLY SPEED LEADERBOARD ⚡

Rank everyone by their average reply time. Use medals for top 3.

```
⚡ RESPONSE TIME RANKINGS ⚡

1. 🥇 Sis     - 12 min (phone? surgically attached)
2. 🥈 Mom     - 45 min (has priorities, apparently)
3. 🥉 You     - 2 hrs (we see you lurking)
4. 💀 Dad     - 6 hrs (reads, forgets, remembers at 3am)
```

Add a witty comment for each person based on their speed.

---

## SECTION 5: CONVERSATION CHEMISTRY 💬

Show who talks to whom and who initiates. Include:
- Who starts the most conversations
- Any notable "reply patterns"
- Who gets ignored the most (if data shows it)

Example insights:
> "Mom starts 45% of all daily conversations - the glue holding this chat together"
> "Dad and Sis have an 89% reply rate to each other - suspicious alliance detected"

---

## SECTION 6: SHOCKING STATS 🚨

Find the MOST surprising patterns in the data and call them out dramatically. These should make people say "wait, WHAT?"

Look for:
- Unexpected contrasts (quiet person sends most emojis)
- Extreme outliers (someone texts 10x more than average at 3am)
- Surprising totals (collectively sent more emojis than words)
- Unusual patterns (busiest day was a random Tuesday)

Format with dramatic reveal:
```
🚨 PLOT TWIST ALERT 🚨

Dad has sent more emojis than everyone else COMBINED.

Yes, really. 2,847 emojis.
The man discovered 🙏 in 2024 and never looked back.
```

---

## SECTION 7: PEAK MOMENTS 📅

Highlight exactly **THREE key moments** from the last 12 months:

1. **Busiest Day** - Date, message count, and speculate why (holiday? drama? big news?)
2. **The Great Silence** - Longest gap between messages and what might have caused it
3. **Current Streak Status** - Are they on fire or has the chat gone cold?

Keep it to THREE moments only. Make each one feel like a story beat.

---

## SECTION 8: CATCHPHRASES & VERBAL TICS 🗣️

Highlight repeated phrases per person. These are the inside jokes and signature expressions.

Format:
```
🗣️ THINGS WE CAN'T STOP SAYING

Mom: "be safe" (said 412 times - we get it, Mom)
Dad: "as per my last message" (47 times - corporate habits die hard)
Sis: "lmaooo" (89 times - exactly 3 o's every time)
```

---

## SECTION 9: PERSONALITY PROFILES 👤

For each person with significant activity, create a detailed personality profile based on ALL their data patterns:

**Include:**
- **Role/Title**: A creative title (e.g., "The Family CEO", "The Chaos Agent")
- **Texting Style**: Verbose/concise, formal/casual, emoji heavy/light
- **Peak Hours**: When they're most active
- **Signature Move**: What makes their messages unique
- **Fun Fact**: A quirky observation from the data

Make each profile feel personalized and accurate.

---

## SECTION 10: GROUP DYNAMICS SUMMARY 💫

**THE HEART OF THE REPORT**

Write 2-3 paragraphs capturing the SOUL of this group. This should:
- Feel like it was written by someone who knows the group
- Reference specific patterns from the data
- Capture the group's "vibe"
- Be warm and celebratory
- Make people feel seen

Cover:
- What brings this group together
- The unwritten rules of the chat
- Who plays what role
- What makes this group special
- A closing thought that makes people smile

---

## Output Style Guidelines

**This report should feel like it was written by a witty friend, NOT a data tool.**

- Use emojis liberally (it's WhatsApp analysis!)
- Be playful and entertaining
- Include humor that lands
- Make it something people would WANT to share
- Create moments that make people laugh or say "that's so true!"
- Reference actual data to make insights feel earned
- The tone should match the group's vibe

**Remember:** Only the numbers come from the database. Everything else - headers, roasts, awards, narrative - should be uniquely crafted for THIS specific group based on their actual patterns.

---

## Redact Mode

If `--redact` is used, the script automatically replaces names with "Person 1", "Person 2", etc.

**When in redact mode:**
- Use the pseudonyms throughout the report
- The group name becomes "[REDACTED GROUP]"
- At the END, include a private mapping for the user's reference
- Make the report equally entertaining with pseudonyms

---

## Final Checklist

Before finishing, verify you included:
- [ ] Shareable Summary Card (screenshot-ready, at TOP)
- [ ] Honors (ONE award per person)
- [ ] The Roasts
- [ ] Reply Speed Leaderboard
- [ ] Conversation Chemistry
- [ ] Shocking Stats
- [ ] Peak Moments (exactly THREE)
- [ ] Catchphrases
- [ ] Personality Profiles
- [ ] Group Dynamics Summary

**All 10 sections are REQUIRED. No shortcuts.**

**DO NOT include:**
- Monthly message journey / monthly trends chart
- Hourly distribution charts ("when the city buzzes")
- Weekly rhythm charts
- "First message ever" (misleading in 12-month context)
