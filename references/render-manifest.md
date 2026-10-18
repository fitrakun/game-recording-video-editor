# Renderer manifest

Run `python /path/to/skill/scripts/render_short.py project.json`. Paths in JSON are relative to the JSON file, and the current working directory can be anywhere. Output versions must have different names. `--validate-only` checks source bounds, crops, speech durations, subtitle coverage, overlaps, and layout without rendering.

The renderer writes `<output-stem>-assets/` containing the processed speech, scene parts, ASS, SRT, script, review sheet, and report. It fully decodes the export and measures loudness. Inspect the sheet yourself; it is not an automatic creative review.

## Fields

- `source`: local source video path.
- `output`: separately named destination MP4; source/output must differ. Existing outputs are preserved.
- `title`: game name. `font`: installed font, default Arial. Optional `fonts_dir` supplies font files.
- `narration_rate`: baseline speed multiplier, default **1.25**. Optional per-speech `rate` overrides it. Engine synthesis stays 1.0; the renderer uses pitch-preserving `atempo` once. To accelerate an already accelerated version again, compute the new total multiplier explicitly.
- `game_gain`: original audio gain, default 0.65. `sfx`: optional list of `{start, kind}` with `kind` equal to `whoosh` or `hit` (generated locally, no music download).
- `scenes`: ordered `{in, out, duration, crop?, y?, height?}`. `in`/`out` are source seconds; `duration` is edited seconds. Timeline starts are cumulative. Default sharp full frame is centered over a blurred synchronized background. A crop is `[x,y,width,height]` in source pixels. Renderer shows the crop at canvas width; optional `height` overrides the default aspect-preserving height (avoid distortion). Default `y` centers the sharp footage. Choose a deliberate safe rectangle. Different scene speeds are pitch-preserving for source audio too.
- `speech`: `{start, text, wav, rate?, cues?}`. Start is edited timeline seconds. WAV is real speech at baseline speed. Silence at either end is trimmed conservatively; interior pauses remain. No automatic time squeezing to fit a slot: overlaps/overruns are errors so the editor can make a conscious change.
- `cues` optional: list `{start,end,text}` with times relative to the **untrimmed baseline WAV**. Times are translated through actual padding trim and speech rate. Their concatenated words must equal `text`; punctuation/case are ignored, but words and numerals are not silently rewritten. If omitted, one cue spans the complete trimmed utterance. Keep one cue to two readable lines; split natural speech phrases or supply true alignment for longer narration.
- `headlines`: optional `{start,end,text,y?,size?,color?}`. ASS color is BGR hexadecimal (`67EFFF` is yellow). Headlines may summarize; subtitles cannot. Text containing a newline is wrapped explicitly. Default subtitle position is y=1450 on a 1080×1920 canvas; optional `caption_y` moves it. Set headlines outside the main action.
- `pointers`: optional `{start,end,x,y}`. A yellow downward pointer ends just above `(x,y)` in final 1080×1920 canvas pixels. Use only after verifying the object's actual on-screen position; keep it brief if the camera moves. Timing is edited timeline time. The renderer does not track objects automatically.

`example-project.json` is a runnable manifest shape, not a fixed creative template. Supply a real `gameplay.mp4` and corresponding WAVs; update timings to their measured durations. The renderer rejects missing audio rather than silently inventing a substitute.

## Timing and revisions

Write the approved exact phrase once. Use `synthesize.py` against the same `speech` list, or provide existing WAVs. On text changes, use a new WAV filename to avoid stale cached narration. Re-render after narration/cue/speed changes; do not paste new subtitles on top of the prior burned-in video. Reuse the original gameplay and baseline WAVs.

For a narration-only speed change, leave scene durations unchanged and retime speech cues. Review any newly exposed gaps. If the user also wants a faster whole edit, shorten scenes and update all speech/headline/effect starts. Do not equate these two requests.

## macOS and Windows

All commands are subprocess argument lists, `pathlib` paths, and portable Python. Font paths are optional. ASS is copied to the render working directory, avoiding FFmpeg filter escaping of drive letters, spaces, or apostrophes. FFmpeg binaries, dependencies, and models still need native installation on the destination. Mac runtime behavior is documented, not tested by packaging on Windows.
