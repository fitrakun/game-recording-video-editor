"""Install for Codex, Claude Code, OpenCode, or a shared Agent Skills directory."""
import argparse
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--agent', choices=['codex','claude','opencode','agents'], default='codex')
    p.add_argument('--project', type=Path, help='Install for one project instead of globally')
    p.add_argument('--dest', type=Path, help='Explicit parent skills directory, overriding agent/project location')
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--replace', action='store_true', help='Back up an existing installation before replacing it')
    args = p.parse_args()
    source = Path(__file__).resolve().parent.parent
    name='game-recording-video-editor'
    global_dirs={
        'codex': Path(os.environ.get('CODEX_HOME', str(Path.home()/'.codex')))/'skills',
        'claude': Path.home()/'.claude'/'skills',
        'opencode': Path(os.environ.get('XDG_CONFIG_HOME',str(Path.home()/'.config')))/'opencode'/'skills',
        'agents': Path.home()/'.agents'/'skills',
    }
    project_dirs={'codex':'.agents','claude':'.claude','opencode':'.opencode','agents':'.agents'}
    parent=args.dest or ((args.project/project_dirs[args.agent]/'skills') if args.project else global_dirs[args.agent])
    parent = parent.expanduser().resolve()
    target = parent / name
    if args.dry_run:
        print(f'{args.agent}: {target}')
        return
    if target == source:
        print(f'Already installed: {target}')
        return
    if target.exists() and not args.replace:
        raise SystemExit(f'Existing installation preserved: {target}. Review before updating.')
    parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        backup=parent.parent/'skill-backups'/f'{name}-{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")}'
        backup.parent.mkdir(parents=True,exist_ok=True)
        target.rename(backup)
        print(f'Previous installation backed up: {backup}')
    shutil.copytree(source, target, ignore=shutil.ignore_patterns('.git', '.venv', 'venv', '.env', '.env.*', '__pycache__', '*.pyc', '*.mp4', '*.mov', '*.mkv', '*.wav', '*.mp3', '*.flac', '*.zip', '*-assets', '*-frames'))
    print(f'Installed for {args.agent}: {target}\nReload your agent session to discover the skill.')

if __name__ == '__main__':
    main()
