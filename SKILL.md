---
name: episode-reel
description: Make the next episode of the user's Instagram reel series "building small businesses a website without being told to". Input is an Instagram link and the repo of a site they rebuilt, plus an optional script. Output is a 1080x1920 reel narrated in the series' locked VoiceStudio voice, with original music, one continuous real-time screen recording of the site, cursor-follow zooms, word-by-word captions and a phone take at the end. Works through checkpoints (script, music, stills) before the final render. Use this whenever the user runs /episode-reel or says "next episode", "episode 2/3/…", or hands over an Instagram link plus a repo for a reel. Also use when they ask for a showcase, screen-recording or Instagram video of a website they built for a small business, even if they don't name the skill.
---

# Episode reel

Each run makes one episode of the series. The user rebuilds a small business's website unasked, then posts a reel that shows the real site and makes two people think "I want that": other small-business owners (who might hire the user's studio, SiteKeep) and the business owner themself, who should feel seen.

Episode 1 is the reference. Its shot lists, script and edit config are in `assets/examples/ep1/`. If the series folder still has `reel-episode-1/`, its final cut and `NOTES.md` show the target. Ep 1 went through four versions; the lessons are folded into this skill. Read `references/lessons.md` once before you start, because it holds what the user rejected and why.

Everything happens in the **series folder**, the folder the agent runs in, with one subfolder per episode: `reel-episode-1/`, `reel-episode-2/`, and so on. The series folder must contain a project-local `.mcp.json` with a `voicestudio` entry (see Setup).

## Inputs

1. **Instagram link**: brand context only (name, what they sell, tone). Never scrape or download from Instagram. If you need profile screenshots, ask the user to drop them into `reel-episode-N/assets/`.
2. **Repo path** of the rebuilt site (a local folder, e.g. `~/repos/<name>`).
3. **Script** (optional). If missing, write one from the repo's markdown (DESIGN_NOTES.md, README or similar: the problem, the talking points, what's fake). See `references/script.md`.

Ask only for what's missing. Keep messages short and decision-oriented: when you ask, give options and your pick.

## Ground rules (and why)

- **The site repo is read-only.** Don't edit, reformat or "fix" it, even when you find a bug. It's the user's client work. All new work goes in `reel-episode-N/`. If something truly can't be recorded otherwise, ask first. Injecting CSS at record time only to hide the Next.js dev badge is fine, and `rec.mjs` already does it.
- **Voice:** VoiceStudio profile **`3a02464e` ("ep1 D sample-locked")** is the series voice. The user dislikes their own voice and picked this one. Don't design, clone or swap voices unless asked. The voice sometimes drops or adds a word, so check every line with `check_lines.py`.
- **MCP stays local.** VoiceStudio is configured only in the series folder's `.mcp.json` (entry `voicestudio`). Never add it to a global config or copy server or client details anywhere else. The tools read that file by walking up from the episode folder. The VoiceStudio app must be open on this Mac (it serves `127.0.0.1`).
- **Truth on screen.**
  - Describe only what the site really does. In ep 1 a made-up "tap a step to check it off" line got called out.
  - Use only numbers from the script or the repo's own copy. Never invent facts.
  - Demo numbers get a "demo numbers" chip.
  - List every claim you couldn't verify in NOTES.md.
- **Music** is original (`synth_bed.py`); never use copyrighted tracks.
- **Dependencies:** keep new ones minimal, and tell the user before installing anything big. Already available: ffmpeg (no drawtext/libass, so captions are HTML), python3 with numpy/scipy/PIL, node with playwright (copied per episode).
- **Never post to Instagram.** The user posts it themselves.

## Setup (once per machine)
- **VoiceStudio** desktop app running locally, with its MCP server (Streamable HTTP, e.g. `http://127.0.0.1:3900/mcp/`).
- **A project-local `.mcp.json` in the series folder**, never a global one:
  ```json
  {"mcpServers": {"voicestudio": {"type": "http", "url": "http://127.0.0.1:3900/mcp/", "headers": {"X-OmniVoice-Client-Id": "<your-client-id>"}}}}
  ```
  The tools read it by walking up from the episode folder. Agents without MCP support still work, because the Python tools call the server directly.
- **Series voice:** the default profile is `3a02464e`, the creator's locked voice. On another VoiceStudio install, pass `--voice <profile_id>` to `speak.py` (or edit its default) after picking a voice with the user.
- **Tools:** ffmpeg, python3 with numpy, scipy and Pillow, node 18+. `new_episode.sh` installs playwright per episode. Chromium comes from `npx playwright install chromium` if missing; ask before installing.

## Workflow

If your agent shows a task list, keep it current. Send the user status pings during long waits (recording and rendering take minutes). "Send a file" below means SendUserFile in the Claude desktop app. Otherwise, give the full path so the user can open it.

### 0. Set up
```
cd <series folder>
zsh <this skill's folder>/scripts/new_episode.sh        # -> reel-episode-N/ with tools/, comp/one.html, NOTES.md
```
- Check VoiceStudio: `check_health` through the voicestudio MCP tools, or `python3 -c "import sys; sys.path.insert(0,'tools'); from vs_rpc import *; print(call(session(),'check_health',{}))"` from the episode folder. If it's down, ask the user to open VoiceStudio.app.
- Start the site in the background: `cd <repo> && npm run dev -- -p 3000`. Then curl every route you'll visit once, so dev compiles don't stall page transitions mid-take.

### 1. Study the site (no checkpoint)
- Read the repo's markdown first: problem, talking points, "what's fake". Then read the routes and components you'll show. Note each real interaction (hover states, transitions, filters, toggles) and exactly what it does.
- Run `python3 tools/brand_tokens.py <repo> --out brief/brand.json` for colours and fonts (used by the theme in step 5).
- Note anything that will look glitchy on camera: preloader artifacts, scroll-reveal content that a filter pulls into view before it has faded in, nav that hides on scroll. `references/recording.md` lists the known patterns and fixes.

### 2. Script ✅ checkpoint
Write or adapt the script with the proven structure in `references/script.md`: a hook in about 3 s, a fast opening (first real click by about 14 s), one line per real on-screen action, a pitch to other business owners, then a closing line to the owner. Save it as `brief/script.md` (a table of line, what's on screen, rough seconds) and as `audio/lines.json`. Send it to the user and wait for approval or edits. They often rewrite lines, so use their wording exactly.

### 3. Voice (no checkpoint: same voice every episode)
```
python3 tools/speak.py audio/lines.json audio/raw            # one wav per line, voice 3a02464e
python3 tools/check_lines.py audio/lines.json audio/raw      # re-voice real slips with --only n
python3 tools/clean_vo.py audio/raw audio/vo_tight.wav --gap 0.2 --report audio/timing_tight.json
```
Draft line start times in `audio/starts.json` (a gap of about 0.25–0.45 s between lines), then:
```
python3 tools/place_vo.py audio/vo_tight.wav audio/timing_tight.json audio/starts.json audio/vo.wav audio/timing.json --dur <total>
python3 tools/word_times.py audio/vo.wav audio/timing.json audio/lines.json audio/words.json --offset 0
```
Starts get finalized after recording, so they line up with the real actions (step 4).

### 4. Music ✅ checkpoint
`python3 tools/music_preview.py` writes 20–25 s previews of the real voice over each candidate bed, at the series mix. Send the files to the user.
- Offer **deep:104 first** (the ep 1 pick and series default), plus one or two alternatives that suit the brand (warm for cosy, pluck for upbeat).
- The mix balance is locked (music 4 LU under the voice, +2 dB in gaps, 9 kHz high-cut). Change it only if the user asks.
- Record the pick in `edit.json` → `"music"`.

### 5. Record the take, then stills ✅ checkpoint
Details are in `references/recording.md`. In short:
1. Write `shots/desktop.mjs`: one continuous real-time take at 1440x900, paced with `r.until(sec)` to the voice beats. `assets/examples/ep1/desktop.mjs` is a worked example.
2. Write `shots/mobile.mjs`: one continuous phone take, about 14 s.
3. Dry-run with `--dry` and look at contact sheets. Fix pacing until nothing is late and nothing parks.
4. Record for real in the background, then run `tools/blend.sh footage/desk footage/desk30` (and the same for `mob`).
5. Re-place the voice to the real marks, then write `edit.json` (`references/edit.md`; ep 1's is in `assets/examples/ep1/edit.json`).
6. Run `python3 tools/build_edit.py` and `node tools/render.mjs stills <frames…>`. Pick 5–6 frames: the hook, the problem graphic, a zoom, a page transition, the dashboard or shop, and the phone with the CTA.

Send the stills to the user, tiled into one or two contact sheets. Ask about the look:
- **(A) the series look**, the same as ep 1 (espresso studio, caramel chips, Archivo wide caps, Yellowtail script). This is the default and keeps the series recognisable.
- **(B) tinted to this client's brand** (theme keys in `edit.json`).

Give your pick.

### 6. Render and deliver
```
node tools/render.mjs film            # out/frames, ~1 min per 1000 frames
python3 tools/make_audio.py           # bed + placed voice + SFX from the take
tools/finish.sh final.mp4             # mux, -14 LUFS, probe, silence + black-frame checks
node tools/check_safe.mjs             # captions, chips and CTA inside the Reels safe zone
```
Before sending, also scan frames yourself:
- contact sheets of the opening and every zoom;
- any glitch spot you noted, frame by frame.

Then write NOTES.md: inputs, the final script, claims to stand behind, placeholders on screen, voice and music, re-render steps. Send `final.mp4` to the user and say what was machine-verified. Ask the user to listen, since you can't hear the mix.

### 7. Feedback rounds
Expect a round or two. Keep each fix surgical. Re-record only the take that changed, keep what they approved, and name each version `final-v2.mp4`, `final-v3.mp4`, and so on, so they can compare. Log each round in NOTES.md.

## What "good" looks like (from episode 1)
- **Real time, one shot.** No slow motion anywhere, especially not the preloader. One continuous desktop take moves through the site like a visitor, using the nav and the site's real page transitions. Then one crossfade to a continuous phone take.
- **The window never moves or resizes.** No per-scene entrance animations, no hard cuts.
- **Zoom only to show an interaction**, eased in and out and following the smoothed cursor. Never a keyframed push-in on a static area.
- **A fast hook.** Scroll continuously at roughly 500 px/s, never stop and go, never let the mouse sit idle. The user called a 27 s run-up "way too slow" and a 14 s one good.
- **Story over details.** Cover the problem, what was built and why it sells. Never narrate colours, fonts or micro-effects.
- **Hide the site's own glitches without touching it.** Frame them out with the zoom, browse first so content has faded in, or stitch over a few frames.
- **Captions:** word by word, wide caps, active word in the accent colour, under the window. In the top zone, one chip plus a script subtitle at a time.

## Files in this skill
- `scripts/`: every tool, copied into each episode's `tools/` by `new_episode.sh`. Each one has usage at the top.
- `assets/comp/one.html`: the compositor (themeable).
- `assets/examples/ep1/`: Episode 1's shot lists, `lines.json`, `starts.json` and `edit.json`.
- `references/script.md`: script structure, the ep 1 script, how to write one from the repo.
- `references/recording.md`: the recorder API, pacing, the dry-run loop, glitch patterns, the phone take.
- `references/edit.md`: the `edit.json` schema, time expressions, zooms, cards, theme, stitch, voice placement, audio.
- `references/lessons.md`: what the user rejected in ep 1, in their words, and what fixed it.
