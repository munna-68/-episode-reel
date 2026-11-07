# episode-reel

An agent skill that turns a rebuilt small-business website into a vertical Instagram reel (1080x1920, 30 fps). The reel is one continuous, real-time screen recording of the real site: cursor-follow zooms, the site's own page transitions, word-by-word captions, a narrated voice-over in a fixed VoiceStudio voice, an original synthesized music bed, and a phone take at the end.

It was built for the series *"building small businesses a website without being told to"*. Episode 1 (Valley Girl Kitchen) is included as the worked example, and episode 2 (Kensal Bakes) as the example of a client-derived look.

## What a run looks like
1. You give the agent an Instagram link (brand context only, never scraped), the site's repo path, and optionally a script.
2. **Script checkpoint:** it writes or adapts the script from the repo's markdown; you approve or edit it.
3. **Voice:** generated line by line in the series voice, then every line is transcribed and checked.
4. **Music checkpoint:** short previews of the voice over a few original beds; you pick one.
5. **Stills checkpoint:** it records the site with Playwright on a fake clock (frame-exact 60 fps) and shows stills in a look designed from the client's own site: background, fonts and caption colours that complement their web design. Only the layout is shared across episodes.
6. **Final render:** mastered to −14 LUFS, safe-zone and glitch checks, NOTES.md with claims to verify.

The repo of the site being showcased is treated as read-only.

## Install
The skill is the folder itself (`SKILL.md` + `scripts/`, `references/`, `assets/`).

- **Claude Code:** copy or symlink this folder to `<project>/.claude/skills/episode-reel/` (one project only) or `~/.claude/skills/episode-reel/` (everywhere). Then run `/episode-reel`.
- **Other agents** (Codex and other SKILL.md-aware agents): put it in that agent's skills folder. Or point the agent's instructions (for example `AGENTS.md`) at `SKILL.md` and tell it to follow that workflow.

## Requirements
- macOS or Linux with `ffmpeg`, `python3` (numpy, scipy, Pillow) and Node 18+. Playwright and Chromium are installed per episode.
- VoiceStudio running locally with its MCP server. Configure it **only** in the series folder's `.mcp.json` (see SKILL.md → Setup); the tools read it from there.
- A voice profile. The default ID in `scripts/speak.py` is the creator's own; change it to yours.

## Layout
```
SKILL.md                 workflow + rules the agent follows
references/              script guide, recording guide, edit.json schema, lessons from episodes 1 and 2
scripts/                 recorder, edit builder, audio + voice tools, render/finish/check scripts
assets/comp/one.html     the 1080x1920 compositor (themed per episode from the client's site)
assets/examples/ep1/     episode 1 shot lists, script lines, voice timing, edit.json
assets/examples/ep2/     episode 2 edit.json with a full client-derived theme
```
