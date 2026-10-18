---
name: game-recording-video-editor
description: Edit local gameplay recordings into engaging narrated vertical Shorts with clear hooks, genuine gameplay payoffs, fast speech, and complete synchronized captions. Use for game highlights and revisions to pacing, voice, subtitles, or framing.
---

# Game Recording Video Editor

Produce the edited MP4, not only a script. This agent-neutral skill captures a workflow for turning game recordings into narrated highlights. It works with agents that can read Markdown, access local media, and run Python/FFmpeg, including Codex, Claude Code, and OpenCode. OpenMontage, Remotion, and VoiceStudio are optional.

Read [scripting.md](references/scripting.md) when scripting. Apply it silently. If the user invokes a separately installed content-principles skill, also follow that skill. Read [setup-and-voices.md](references/setup-and-voices.md) on a new device or voice-provider change. Read [render-manifest.md](references/render-manifest.md) before rendering. Resolve scripts/references relative to this SKILL.md, not a fixed agent installation path. Follow the host agent's permission and tool rules.

## Discover and script

Find the named recording, probe duration/resolution/audio, and preserve it. Export a separately named version. For long recordings, seek directly to sparse frames using `scripts/sample_frames.py`, then sample promising windows densely. Inspect before/during/after the actual event and record source timestamps. A scanner signal alone does not establish a needle find.

If reference videos are supplied, examine accessible footage, pacing, and captions. Disclose access failures; never claim to have watched an unreadable reference. Recreate editing techniques with the user's footage rather than copying reference voices or footage.

Infer the viewer from context (usually someone discovering satisfying or surprising game moments); ask only if audience meaningfully affects the edit. Give the first three seconds a concrete reason to stay, and deliver something interesting within roughly 5–10 seconds. Keep the fun, escalation, discovery, and reaction; remove repeated searching, menus, and idle time. Choose length from the content, usually 30–50 seconds, without padding to a quota.

Story-game example: apparent ending → meaningful exchange → continuation/reveal. Search-game example: tiny target/big obstacle → enjoyable machinery/escalation → spotting challenge → real pickup/reward. These are examples, not mandatory templates.

Original commentary is allowed when requested. Label it editorial narration, not a transcript of recorded player speech. Quote dialogue accurately. Do not invent reactions, completion, mechanics, or numbers. Preserve qualifications such as “more than”; respect exact user corrections. A count above 13 million must not silently become exactly 13 million.

## Voice and captions

Use available local speech first. Announce the engine and voice. The prior Windows voice was VoiceStudio / KittenTTS / Bella (`expr-voice-2-f`), but discover availability on each device. VoxCPM is an alternative, not a mandatory replacement. See the setup reference.

Default to brisk narration: **1.25× baseline speech with pitch preserved**, unless the user chooses otherwise. Record the multiplier and apply it once. A subsequent “1.25× now” is relative to the current delivered version. Do not silently speed gameplay when only voice speed was requested. Audition if playback is available; do not equate probing with listening.

**Subtitles contain every spoken word.** Use canonical `text` for both synthesis and captions. Headlines may summarize, subtitles may not. In particular, do not drop lead-ins like “And I'm looking,” “turned into,” “just,” “straight,” or “I actually.”

- Prefer a natural short phrase per WAV/caption, usually 3–8 words. This gives actual phrase boundaries without invented word alignment. Avoid robotic fragment synthesis.
- Longer WAVs may use timestamped `cues` aligned to the audio. Do not allocate by character count and call it exact. Without alignment, show the complete utterance as one readable cue, or split/regenerate phrases.
- Derive ASS and SRT from the same cues. Recalculate when speech is regenerated, trimmed, or accelerated. Validate concatenated cue text against canonical text.
- Correct missing/slurred generated speech rather than disguising it with different subtitles.

## Edit and verify

Use the bundled FFmpeg helpers for ordinary edits; adapt or use Remotion when richer motion warrants it. If OpenMontage is explicitly requested and available, follow its applicable project instructions; it is not needed for this skill.

Default look: 1080×1920 at 30 fps; sharp gameplay over synchronized blurred footage; readable white/yellow captions; modest pop animation, purposeful cuts, light sound accents; game audio ducked under narration. Match an explicit reference instead of forcing this default. Keep text clear of important HUD, dialogue, objects, and platform controls.

Show the full game when context matters; punch in when the payoff is tiny. Point only at a verified visible object, after any spotting challenge. Use moving footage, with brief slow motion or holds only where useful. Preserve pickup and reward. Avoid long empty gaps after accelerating narration; tighten visuals when requested, while keeping worthwhile game-audio beats.

Synthesis and editing are separate: `scripts/synthesize.py` produces WAVs; `scripts/render_short.py` consumes WAVs and a JSON manifest. The scripts use portable paths and do not require copied Windows virtual environments.

Probe and fully decode the final file. Inspect the opening, dense captions, pickup/reveal, and ending. Measure loudness; correct clipping, missing words, poor crops, and silence. Save the manifest, selected source timestamps, script, SRT, report, and MP4. Return a clickable video link and any real limitation. Distinguish tested behavior from documented platform support: never claim a Mac or VoxCPM test was run on Windows.
