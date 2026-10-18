# Game Recording Video Editor

An Agent Skill that turns long game recordings into engaging narrated vertical videos. Install it in **Codex, Claude Code, or OpenCode**, or give `SKILL.md` directly to another agent with local file and command access.

The workflow covers finding interesting moments, writing a concrete hook, trimming slow sections, generating local narration, emphasizing tiny discoveries, and exporting a finished video with subtitles containing every spoken word.

## Install

Clone this repository or download and extract its ZIP. From the repository folder, choose your agent:

```sh
git clone https://github.com/fitrakun/game-recording-video-editor.git
cd game-recording-video-editor
```

```sh
# Codex
python3 scripts/install_skill.py --agent codex

# Claude Code
python3 scripts/install_skill.py --agent claude

# OpenCode
python3 scripts/install_skill.py --agent opencode
```

On Windows use `python` or `py -3.11` instead of `python3`. Installation does not require editing shell-specific scripts. Reload your agent session afterward.

| Agent | Default global installation |
|---|---|
| Codex | `~/.codex/skills/game-recording-video-editor` (honors `CODEX_HOME`) |
| Claude Code | `~/.claude/skills/game-recording-video-editor` |
| OpenCode | `~/.config/opencode/skills/game-recording-video-editor` (honors `XDG_CONFIG_HOME`) |
| Shared Agent Skills | `~/.agents/skills/game-recording-video-editor` via `--agent agents` |

For a project-only install, add `--project /path/to/project`. This uses `.agents/skills` for Codex/shared agents, `.claude/skills` for Claude Code, or `.opencode/skills` for OpenCode. An explicit `--dest /path/to/skills` overrides discovery paths. `--dry-run` prints the destination without writing. Existing installations are preserved; `--replace` backs up the old version before updating.

Manual installation also works: copy this entire repository folder into the appropriate skill directory, naming the folder `game-recording-video-editor`. The optional `agents/openai.yaml` adds Codex UI metadata; other agents can ignore it. No Codex-specific tool is required by the editing scripts.

## Use

Codex:

```text
Use $game-recording-video-editor to edit this recording into a vertical short.
Highlight the fun moments and the part where I find the target.
Use brisk 1.25x narration and subtitles matching every spoken word.
File: /path/to/game-recording.mp4
```

Claude Code: invoke `/game-recording-video-editor` with the recording path and editing request. In OpenCode, ask it to load the `game-recording-video-editor` skill. For another agent, ask it to read `SKILL.md`, follow its relative references, and use its own permitted file/shell tools. An ordinary chat-only model without media/filesystem/command tools can read the guidance but cannot render videos.

## Software requirements

- Python with NumPy and Pillow (Python 3.11 is a suitable starting point).
- Native FFmpeg and ffprobe on PATH, with **libx264** and **libass** support.
- A narration source: an existing WAV, installed VoiceStudio engine, or standalone VoxCPM.

The installer only copies the skill. It does not install dependencies or download speech models.

```sh
python3 -m venv .venv
# Use the environment's Python, e.g. .venv/bin/python on Mac/Linux
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/preflight.py
```

Windows equivalent: `.\.venv\Scripts\python.exe`. On macOS, install a suitable FFmpeg build, for example with Homebrew, then confirm `preflight.py` reports libass/libx264. See [platform setup and voice options](references/setup-and-voices.md).

## macOS and local voices

The editing helpers use Python and FFmpeg on Windows, macOS, and Linux. Native dependencies must be installed on each device; copying a Windows virtual environment to a Mac will not work.

VoiceStudio currently supports local generation on **Apple Silicon Macs**. Its current Intel Mac app requires a remote backend. Standalone **VoxCPM** is an alternative WAV generator; its current Python API exposes Apple MPS, CUDA, and CPU devices. Intel compatibility should not be assumed. Verify current upstream requirements and run a small test before a full narration batch.

```sh
# After confirming the chosen VoiceStudio voice/model is installed:
python3 scripts/synthesize.py project.json --provider voicestudio --model kittentts --voice expr-voice-2-f

# Alternative, with standalone VoxCPM installed and weights already cached:
python3 scripts/synthesize.py project.json --provider voxcpm --model openbmb/VoxCPM2 --device mps
```

Model downloads require an explicit choice (`--allow-model-download` for VoxCPM). Engines stay at synthesis speed 1.0; `narration_rate` applies the chosen speed once during editing, preserving pitch. No voice cloning is performed by the supplied adapter.

## Render

Build a project JSON using [the manifest guide](references/render-manifest.md) and [example](references/example-project.json). Paths in JSON are relative to that file. Supply real source footage and WAVs, then:

```sh
python3 scripts/render_short.py /path/to/project.json --validate-only
python3 scripts/render_short.py /path/to/project.json
```

The default output is 1080×1920 at 30 fps, with sharp gameplay over a synchronized blurred background, phrase captions, optional emphasis headlines, pointers, light generated sound accents, and ducked source audio. Narration defaults to 1.25×, configurable per project or phrase. The export includes an asset directory with SRT, script, manifest, contact sheet, and render report.

For accurate subtitles, each short phrase can have its own WAV and canonical text. Longer narration can provide actual timestamped cues. Omitted words are rejected; character-count estimates are not presented as word alignment. Changed speech must be rerendered from the original gameplay, not layered over old burned-in captions.

## Scripting and references

The [bundled scripting guide](references/scripting.md) is original to this repository. The separately maintained [content-principles skill by Remy Gaskell / aiwithremy](https://github.com/aiwithremy/content-principles) can be installed alongside this one. Its text is not republished here.

Agent discovery references: [Claude Code skills](https://code.claude.com/docs/en/skills), [OpenCode skills](https://opencode.ai/docs/skills/), and the [Agent Skills format](https://agentskills.io/specification). Voice references: [VoiceStudio macOS guide](https://github.com/debpalash/VoiceStudio/blob/main/docs/install/macos.md) and [VoxCPM core API](https://github.com/OpenBMB/VoxCPM/blob/main/src/voxcpm/core.py).

## Validation and limits

Tested on Windows: real footage and silent-source rendering, full decode, caption completeness checks, 1.25× narration, pointers, contact sheets, paths containing spaces/apostrophes, no-overwrite installation, and VoiceStudio synthesis. Agent-specific destination mapping is covered by automated tests. Actual Claude Code/OpenCode loading, macOS execution, and standalone VoxCPM inference have not been runtime-tested here. Documentation describes those supported paths without claiming a completed platform test.

```sh
python3 -m unittest discover -s tests -v
```

The package contains no recordings, generated examples, voice models, executables, credentials, or copied third-party skill text. Keep media projects outside the repository. Source timestamps and creative conclusions still need human/agent review: passing format checks does not prove that a chosen moment is compelling or a narration fact is true.

## License

MIT for this repository's original code and instructions. Dependencies, speech models, fonts, and input media retain their own licenses. See [THIRD_PARTY.md](THIRD_PARTY.md).
