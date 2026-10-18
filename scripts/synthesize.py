"""Generate canonical speech phrases using VoiceStudio or cached standalone VoxCPM."""
import argparse
import hashlib
import json
import os
import subprocess as sp
import urllib.request
from pathlib import Path

def request(base, path, data=None):
    headers = {'Content-Type': 'application/json'}
    if os.environ.get('VOICESTUDIO_API_KEY'):
        headers['Authorization'] = 'Bearer ' + os.environ['VOICESTUDIO_API_KEY']
    req = urllib.request.Request(base.rstrip('/') + path, data=json.dumps(data).encode() if data is not None else None, headers=headers)
    with urllib.request.urlopen(req, timeout=240) as response:
        return response.read()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('manifest', type=Path)
    p.add_argument('--provider', choices=['voicestudio', 'voxcpm'], required=True)
    p.add_argument('--url', default='http://localhost:3900')
    p.add_argument('--model', required=True)
    p.add_argument('--voice', default='default')
    p.add_argument('--device', choices=['auto', 'cpu', 'mps', 'cuda'], default='auto')
    p.add_argument('--allow-model-download', action='store_true')
    p.add_argument('--seed', type=int, default=42)
    args = p.parse_args()
    root = args.manifest.resolve().parent
    doc = json.loads(args.manifest.read_text(encoding='utf-8-sig'))
    items = doc['speech']
    model = None
    if args.provider == 'voicestudio':
        health = json.loads(request(args.url, '/health'))
        if health.get('status') != 'ok':
            raise SystemExit('VoiceStudio is not healthy')
        schema = json.loads(request(args.url, '/openapi.json'))
        if '/v1/audio/speech' not in schema.get('paths', {}):
            raise SystemExit('Speech API not available in this VoiceStudio version')
    for item in items:
        target = (root / item['wav']).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        # Generation speed stays 1.0. The renderer applies narration_rate exactly once.
        settings = {'text': item['text'], 'provider': args.provider, 'model': args.model, 'voice': args.voice, 'device': args.device, 'seed': args.seed}
        key = hashlib.sha256(json.dumps(settings, sort_keys=True).encode()).hexdigest()
        receipt = target.with_suffix(target.suffix + '.json')
        if target.exists():
            if receipt.exists() and json.loads(receipt.read_text()).get('key') == key:
                print('cached', target.name, flush=True)
                continue
            raise SystemExit(f'Existing audio preserved: {target}. Use a new WAV filename for changed text/provider.')
        if args.provider == 'voicestudio':
            audio = request(args.url, '/v1/audio/speech', {'model': args.model, 'voice': args.voice, 'input': item['text'], 'response_format': 'wav', 'speed': 1.0})
            target.write_bytes(audio)
        else:
            if model is None:
                from voxcpm import VoxCPM
                import soundfile as sf
                model = VoxCPM.from_pretrained(args.model, load_denoiser=False, optimize=False, device=None if args.device == 'auto' else args.device, local_files_only=not args.allow_model_download)
            audio = model.generate(text=item['text'], cfg_value=2.0, inference_timesteps=10, seed=args.seed)
            sf.write(str(target), audio, model.tts_model.sample_rate)
        probe = json.loads(sp.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=codec_type', '-of', 'json', str(target)], text=True))
        duration = float(probe['format']['duration'])
        if duration <= 0 or not any(s.get('codec_type') == 'audio' for s in probe['streams']):
            raise SystemExit(f'Generation returned invalid audio: {target}')
        receipt.write_text(json.dumps({'key': key, **settings, 'duration': duration}, indent=2), encoding='utf-8')
        print(target.name, round(duration, 3), 'seconds', flush=True)

if __name__ == '__main__':
    main()
