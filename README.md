# WhatsApp Group Wrapped

A Claude Code skill that analyzes your WhatsApp group chats and generates Spotify Wrapped-style reports with roasts, awards, and shareable stats.

## Requirements

- macOS with WhatsApp Desktop installed
- [Claude Code CLI](https://claude.ai/claude-code)
- Python 3 (pre-installed on macOS)

## Installation

Clone this repo and symlink to your Claude skills directory:

```bash
git clone https://github.com/rohankatyal29/whatsapp-group-wrapped.git
ln -s $(pwd)/whatsapp-group-wrapped/.claude/skills/whatsapp-group-wrapped ~/.claude/skills/whatsapp-group-wrapped
```

## Usage

Open Claude Code and run:

```
/whatsapp-group-wrapped Family Chat
```

### List Available Chats

```
/whatsapp-group-wrapped
```

### Privacy Mode (Redact Names)

```
/whatsapp-group-wrapped Family Chat --redact
```

## What the Report Includes

1. **Shareable Summary Card** - Screenshot-ready ASCII card with top stats
2. **Honors** - Custom awards for each person (Night Owl, Speed Demon, etc.)
3. **Roasts** - Gentle, funny roasts based on actual texting patterns
4. **Reply Speed Leaderboard** - Who replies fastest and who leaves you on read
5. **Conversation Chemistry** - Who talks to whom, who starts conversations
6. **Shocking Stats** - Surprising "wait, WHAT?" moments from the data
7. **Peak Moments** - Busiest day, longest silence, streak status
8. **Catchphrases** - Repeated phrases and verbal tics per person
9. **Personality Profiles** - Deep dive on each member's texting style
10. **Group Dynamics Summary** - The soul of your group in 2-3 paragraphs

## Privacy

All analysis runs locally on your machine. Your data never leaves your computer.
