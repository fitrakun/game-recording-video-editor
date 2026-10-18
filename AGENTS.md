# Working on this skill

The portable entry point is SKILL.md. Keep it agent-neutral; agent-specific discovery paths belong in the installer and setup documentation. agents/openai.yaml is optional Codex metadata.

Preserve the canonical speech-text/caption invariant, pitch-preserving speech speed, source footage, and no-overwrite exports. Keep examples synthetic. Do not commit recordings, generated media, models, runtime environments, credentials, machine-specific paths, or copied third-party skill text.

Run `python -m unittest discover -s tests -v` after helper changes. Speech/render tests using FFmpeg skip when the binary is absent; do not describe those skips as runtime validation. Check Markdown links and skill naming after documentation changes. Verify platform claims against official documentation and distinguish documented support from an actual device test.
