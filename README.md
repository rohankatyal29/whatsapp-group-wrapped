# WhatsApp Group Wrapped

A Claude Code skill that analyzes your WhatsApp groups from the **last 12 months** and generates a **Spotify Wrapped-style report** with roasts, awards, and shareable stats.

**Perfect for sharing on Twitter/X and LinkedIn!**

## What You Get

### Shareable Summary Card
```
╔═══════════════════════════════════════════════════════╗
║          🫖 CHAI FAMILY • 2025 WRAPPED 🫖             ║
╠═══════════════════════════════════════════════════════╣
║   📨 12,847 messages  •  🗓️ 365 days of chaos        ║
║   🌙 Peak vibes: 10 PM  •  🔥 142-day streak         ║
║   👑 TOP TEXTER: Mom (34%)                           ║
║   🦉 NIGHT OWL: Dad (847 msgs after midnight)        ║
║   ⚡ SPEED DEMON: Sis (12 min avg reply)             ║
║   💬 Chat Personality: THE 3AM PHILOSOPHERS           ║
║   "A family that texts at 3am together,              ║
║    stays together"                                    ║
╚═══════════════════════════════════════════════════════╝
         📸 Screenshot this and tag your family!
```

### 10 Report Sections

1. **Summary Card** - Screenshot-ready wrapped-style card
2. **Superlatives** - "Most Likely To..." yearbook awards
3. **Roasts** - Gentle, funny roasts based on actual patterns
4. **Reply Speed Leaderboard** - Who's fastest (and who leaves you on read)
5. **Conversation Chemistry** - Who talks to whom
6. **Shocking Stats** - The "wait, WHAT?" moments
7. **Timeline Milestones** - First message, busiest day, longest silence
8. **Catchphrases** - What everyone keeps saying
9. **Personality Profiles** - Deep dive on each member
10. **Group Dynamics Summary** - The soul of your group

## Features

- **AI-Powered Insights** - Creative, personalized commentary
- **Privacy Mode** - Redact names for public sharing
- **Local Only** - Your data never leaves your machine
- **No Dependencies** - Uses only Python standard library

## Requirements

- macOS with WhatsApp Desktop installed
- Claude Code CLI
- Python 3 (pre-installed on macOS)

## Installation

Add to your `~/.claude/skills/` directory:

```bash
# Option 1: Symlink (recommended)
ln -s /path/to/whatsapp-group-wrapped ~/.claude/skills/whatsapp-group-wrapped

# Option 2: Copy
cp -r /path/to/whatsapp-group-wrapped ~/.claude/skills/
```

## Usage

In Claude Code:

```
Analyze my WhatsApp group "Family Chat"
```

Or use the skill command:
```
/whatsapp-group-wrapped Family Chat
```

### Privacy Mode (Redact Names)

```
/whatsapp-group-wrapped Family Chat --redact
```

### List Available Chats

```
/whatsapp-group-wrapped
```

## How It Works

1. The Python script reads from your local WhatsApp database
2. Extracts 20+ data points including streaks, reply speed, emoji usage
3. Claude generates a creative, personalized 10-section report
4. You screenshot and share!

## Data Extracted

The analyzer extracts:
- Message counts and trends
- Peak hours and days
- Streak data (longest and current)
- Reply speed per person
- Who starts conversations
- Emoji usage and favorites
- Common phrases/catchphrases
- Late night and early morning texters
- Media and link sharers
- And more...

## Files

```
whatsapp-group-wrapped/
├── README.md           # This file
├── SKILL.md            # Claude skill definition
└── references/
    └── whatsapp_data.py    # Data extraction script
```

## Privacy

All data stays on your local machine. The analyzer:
- Reads from your local WhatsApp database
- Processes everything locally with Python
- Never sends data anywhere
- Supports name redaction for sharing

## The Tweet

When you're ready to share:

```
I built WhatsApp Group Wrapped

It analyzes your group chat and generates
a Spotify Wrapped-style report with:

• Shareable stats card
• Who texts at 3am
• Who leaves people on read
• Personalized roasts for everyone

Runs locally - your data never leaves your machine

[Screenshots]
```

## License

MIT License - do whatever you want with it!

---

Made with love for groups who chat too much on WhatsApp
