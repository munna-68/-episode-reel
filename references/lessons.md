# Lessons from episode 1 (four versions)

What the user rejected, in their words, and what fixed it. Read this before planning a new episode, so the first version already avoids these.

## Voice and music (settled; reuse)
- They dislike their own voice ("I hate my voice"). Series voice: VoiceStudio **3a02464e "ep1 D sample-locked"**.
- A designed voice drifted in pitch across a long take, and a clone made from a drifted take sounded "bitchy". The fix was cloning from the exact approved sample clip. Generate **line by line**; never one long block.
- Breaths and dead air annoyed them, so `clean_vo.py` removes them.
- Music was first "too loud", then too quiet. The locked balance is music **4 LU under the voice, +2 dB in gaps, 9 kHz high-cut, master −14 LUFS**. Favourite bed: `deep` at 104 BPM.

## v1 → rejected ("there are so many issues")
- **Slow-motion preloader.** "The preloader should happen in a real time thing." → The fake-clock recorder, with no time remapping ever.
- **Many cuts, each with a scale or rise entrance.** "The cuts seem like really bad… so jarring." → One continuous take, then one crossfade to the phone.
- **Window size and position changed per scene.** "At 23 s the window is so small… at 28 s it becomes bigger." → One fixed window for the whole video.
- **Keyframed push-ins.** "The zoom in effect that you added looks really bad… zoom into mouse." → Zoom only around interactions, following the smoothed cursor, eased in and out.
- **A detail-by-detail script** (colours, effects). "I don't like how you're talking about colors and every small detail." → A story script: the problem, one home, what each feature does for a business, the pitch to owners.
- **A made-up behaviour.** "That's not how the method works… you probably made that up. Use the real website." → Describe only what you've seen the site do.

## v2 → mostly loved ("I love the render, I love the voice"), but:
- **A stop-and-go opening and a parked mouse.** "We start scrolling at 7 s, stop at 10 s and stay there… hovering our mouse at 16 s, it's weird." → `scrollPath` makes one never-stopping scroll; the cursor drifts with it.
- **A search glitch:** a card invisible after filtering (the site's scroll reveal plus FLIP). → Browse the grid first, then zoom tight on the search box until the filter settles.

## v3 → "the beginning is still way too slow"
- "People have ADHD… the beginning should be a hook. It should be the most impressive part." → The opening voice was cut to four short lines, with a fast scroll at about 500 px/s. The first click moved from 27 s to **14 s**.
- **The preloader "has like a second of glitch".** The site's dive left letter-mask pieces sliding over the photo. → A stitch (zoom through the letter, dissolve into the clean hero).

## v4 → approved
63 s total. Everything from the first click onward was unchanged from v2. Start new episodes from v4's shape.

## Episode 2: a look per client
- "Can you make the background, the fonts… suit this particular website? It shouldn't be the same for every episode." → Each episode gets its own theme from the client's colours and type (ep 2: crimson studio, butter chips, condensed Archivo caps, DM Mono subtitles). Only the layout stays fixed.
- The phone take's scroll to the footer showed text as a double image: the 2-frame blend at ~1000 px/s. Fix: `blend.sh … --crisp` for the phone, and one even `scrollPath` instead of a long final sine scroll.
- A beat the voice names ("fully booked") needs about 1.5 s on screen with the cursor on it, so the follow-zoom actually frames it before the next move.

## Working style they asked for
- Short, decision-oriented messages; when asking, give options and a pick.
- Ask before creative commitments: script, music, stills. Don't ask about things already settled above.
- Let them hear audio before the video is built.
- They are fine with videos over 60 s if it's "a banger", but never at the cost of the hook.
