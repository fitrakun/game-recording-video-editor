# Installation, platforms, and voices

Documentation checked 2026-10-18; verify current upstream requirements before installation.

## Install for your agent

From the extracted repository run `python3 scripts/install_skill.py --agent codex`, `--agent claude`, or `--agent opencode` (Windows: `python` or `py -3.11`). See [the repository README](../README.md) for global/project discovery paths, manual installation, and invocation syntax. The installer copies this whole skill and supporting files, preserves existing installations, and supports dry runs. It does not install software/models or change agent permissions.

The public package includes original instructions, helpers, an example manifest, and an original scripting reference. It links to content-principles as an optional separate upstream skill; it does not republish that third-party text. No recordings, models, accounts, or environment folders are bundled.

## Editing requirements

Python 3.11 is a suitable common choice. Use a dedicated project environment, not a speech app's managed runtime. FFmpeg/ffprobe must be on PATH, with libx264 and libass (`ass` filter). Some Mac FFmpeg builds lack libass; check first. Use an installed font (such as Arial) or provide a font directory. No Node, CUDA, or OpenMontage is needed for the renderer.

macOS, assuming Homebrew is already installed:

```sh
brew install python@3.11 ffmpeg
python3.11 -m venv .venv
.venv/bin/python -m pip install numpy Pillow
.venv/bin/python /path/to/game-recording-video-editor/scripts/preflight.py
```

Windows: install Python and a trusted FFmpeg build, then:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install numpy Pillow
.\.venv\Scripts\python.exe C:\path\to\game-recording-video-editor\scripts\preflight.py
```

Never name helpers `inspect.py`, `json.py`, `wave.py`, or other standard-library names: a previous `inspect.py` shadowed Python's module and broke NumPy. Use subprocess argument lists, not interpolated shell commands.

## VoiceStudio

VoiceStudio currently offers a macOS Electron app with local Apple Silicon inference (guide: macOS 13.3+). Intel Macs currently support the UI with a remote backend, not the local backend, because newer required PyTorch wheels are unavailable. Use the native arm64 app/environment on Apple Silicon, not Rosetta.

- [macOS guide](https://github.com/debpalash/VoiceStudio/blob/main/docs/install/macos.md)
- [Releases](https://github.com/debpalash/VoiceStudio/releases)
- [Engines](https://github.com/debpalash/VoiceStudio/tree/main/docs/engines)

Reuse an installed app. Discover `/health`, `/openapi.json`, `/v1/audio/voices`, and `/engines` on the actual backend, usually `http://localhost:3900`. Confirm the chosen engine/model is ready. KittenTTS Bella was verified in the original Windows session; do not assume it is installed on a new device. OpenAI-compatible aliases are not OpenAI voices or permission for a cloud API.

After discovery, generate one phrase before a batch:

```sh
python scripts/synthesize.py speech.json --provider voicestudio --model kittentts --voice expr-voice-2-f
```

The helper checks health/schema; it does not install models or apps. If needed, supply an API key through `VOICESTUDIO_API_KEY`; it is not saved in the skill.

## Standalone VoxCPM

VoxCPM can supply WAVs instead of VoiceStudio. VoiceStudio is an app/backend; VoxCPM is a speech runtime/model. The renderer accepts either.

Current official core API accepts `device="mps"`, `"cuda"`, or `"cpu"`; auto selection prefers CUDA, MPS, then CPU. This is a documented Apple Silicon path, not a benchmark or a tested promise for a particular Mac. The README still emphasizes CUDA; validate package/device compatibility with a small generation. Intel Macs may hit the same newer-PyTorch wheel limitation.

- [Repository and installation](https://github.com/OpenBMB/VoxCPM)
- [Current cache/device Python API](https://github.com/OpenBMB/VoxCPM/blob/main/src/voxcpm/core.py)
- [Runtime utilities](https://github.com/OpenBMB/VoxCPM/blob/main/src/voxcpm/model/utils.py)

Use a separate native Python 3.11 environment. Install `voxcpm` following current official instructions; do not install CUDA wheels on Mac. Package/model downloads are substantial and not bundled. Obtain the user's choice before model downloads or a provider/voice change. Record installed versions.

```sh
python scripts/synthesize.py speech.json --provider voxcpm --model openbmb/VoxCPM2 --device mps
```

Cached weights are used by default. Add `--allow-model-download` only after download authorization. Local model-directory paths also work. The helper disables denoiser downloads and torch compilation; it does not clone a voice. A fixed seed helps repeatability but does not guarantee identical timbre between phrases. Audition several phrases and choose an authorized stable voice workflow if needed. For richer voice-design controls, inspect the installed current API before adapting it.

Preserve MPS failures and investigate; do not silently label CPU generation as accelerated. An explicit `--device cpu` is possible when dependencies support it, usually slower. On Intel consider an existing compatible local TTS engine or a user-approved remote backend. Existing WAVs can be rendered locally without a TTS model.
