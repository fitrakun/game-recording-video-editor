"""Render a source-led vertical short with pitch-preserved speech and complete captions."""
import argparse
import json
import math
import re
import shutil
import subprocess as sp
import textwrap
import wave
from pathlib import Path
import numpy as np

SR = 48000

def probe(path):
    return json.loads(sp.check_output(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(path)], text=True))

def tempo(rate):
    if not math.isfinite(rate) or rate <= 0:
        raise ValueError('Audio rate must be positive and finite')
    filters = []
    while rate > 2:
        filters.append('atempo=2'); rate /= 2
    while rate < .5:
        filters.append('atempo=.5'); rate /= .5
    return ','.join(filters + [f'atempo={rate:.9f}'])

def run(args, cwd=None):
    sp.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y'] + list(map(str, args)), check=True, cwd=cwd)

def timestamp(t, ass=False):
    scale = 100 if ass else 1000
    n = round(t * scale)
    return f'{n//(3600*scale):01}:{n//(60*scale)%60:02}:{n//scale%60:02}.{n%scale:02}' if ass else f'{n//(3600*scale):02}:{n//(60*scale)%60:02}:{n//scale%60:02},{n%scale:03}'

def plain(text):
    return re.sub(r'[^\w]+', '', text.casefold(), flags=re.UNICODE)

def wrapped(text):
    if any(c in text for c in ('{', '}', '\\')):
        raise ValueError('Caption text must be plain text, without ASS markup')
    lines = [part for line in text.splitlines() for part in textwrap.wrap(line, width=26, break_long_words=False)]
    if len(lines) > 2 or any(len(line) > 35 for line in lines):
        raise ValueError(f'Caption is too long for two readable lines; split/align phrases: {text}')
    return r'\N'.join(lines)

def prepare_speech(doc, root, total):
    mix = np.zeros((round(total * SR), 2), np.float32)
    captions, timing = [], []
    previous_end = 0
    for item in sorted(doc.get('speech', []), key=lambda r: r['start']):
        path = (root / item['wav']).resolve()
        raw = sp.check_output(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-i', str(path), '-ar', str(SR), '-ac', '2', '-f', 'f32le', '-'])
        x = np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
        if not len(x):
            raise ValueError(f'Empty speech: {path}')
        mono = x.mean(axis=1); n = len(mono) // 960
        if n == 0:
            raise ValueError(f'Speech too short: {path}')
        rms = np.sqrt(np.mean(mono[:n*960].reshape(n, 960)**2, axis=1))
        active = np.flatnonzero(rms > .0035)
        if not len(active):
            raise ValueError(f'Silent narration: {path}')
        lo = max(0, int(active[0] * 960 - .04 * SR))
        hi = min(len(x), int((active[-1] + 1) * 960 + .08 * SR))
        original_duration = len(x) / SR
        rate = float(item.get('rate', doc.get('narration_rate', 1.25)))
        x = x[lo:hi]
        result = sp.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', '-', '-af', tempo(rate), '-f', 'f32le', '-'], input=x.tobytes(), stdout=sp.PIPE, check=True)
        x = np.frombuffer(result.stdout, np.float32).reshape(-1, 2).copy()
        start = float(item['start']); end = start + len(x) / SR
        if start < previous_end - .001 or start < 0 or end > total + .001:
            raise ValueError(f'Speech overlaps/overruns timeline at {start:.2f}s; adjust scene lengths or speech starts: {item["text"]}')
        previous_end = end
        x *= .55 / max(float(np.max(np.abs(x))), .001)
        at = round(start * SR); mix[at:at+len(x)] += x
        cues = item.get('cues')
        if cues:
            if plain(' '.join(c['text'] for c in cues)) != plain(item['text']):
                raise ValueError(f'Captions omit/change spoken words: {item["text"]}')
            last = 0
            for cue in cues:
                a, b = float(cue['start']), float(cue['end'])
                if a < last or b <= a or b > original_duration + .02:
                    raise ValueError('Cue times must be ordered within the untrimmed baseline WAV')
                last = b
                ca = start + max(0, a - lo / SR) / rate
                cb = min(end, start + (b - lo / SR) / rate)
                if cb <= ca:
                    raise ValueError('Caption cue was entirely removed by silence trim')
                captions.append((ca, cb, cue['text']))
        else:
            captions.append((start, end, item['text']))
        timing.append({'text': item['text'], 'start': start, 'end': end, 'rate': rate, 'baseline_wav': str(path)})
    for _, _, text in captions:
        wrapped(text)
    return mix, captions, timing

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('manifest', type=Path)
    p.add_argument('--validate-only', action='store_true')
    args = p.parse_args()
    manifest = args.manifest.resolve(); root = manifest.parent
    doc = json.loads(manifest.read_text(encoding='utf-8-sig'))
    source = (root / doc['source']).resolve(); output = (root / doc['output']).resolve()
    if source == output:
        raise ValueError('Output must differ from source')
    source_info = probe(source)
    v = next(s for s in source_info['streams'] if s['codec_type'] == 'video')
    source_duration = float(source_info['format']['duration'])
    has_audio = any(s['codec_type'] == 'audio' for s in source_info['streams'])
    scenes = doc['scenes']; total = sum(float(s['duration']) for s in scenes)
    if not scenes or total <= 0 or total > 180:
        raise ValueError('Need an edited short of 0–180 seconds')
    for scene in scenes:
        a, b, d = (float(scene[k]) for k in ('in', 'out', 'duration'))
        if not 0 <= a < b <= source_duration + .001 or d <= 0:
            raise ValueError(f'Invalid scene time: {scene}')
        crop = scene.get('crop', [0, 0, v['width'], v['height']])
        x, y, w, h = crop
        if min(x, y) < 0 or min(w, h) <= 0 or x+w > v['width'] or y+h > v['height']:
            raise ValueError(f'Crop outside source: {crop}')
        fh = int(scene.get('height', round(1080*h/w/2)*2))
        fy = int(scene.get('y', (1920-fh)//2))
        if fy < 0 or fy + fh > 1920:
            raise ValueError('Sharp foreground must stay within the 1920px canvas')
    mix, captions, timing = prepare_speech(doc, root, total)
    for h in doc.get('headlines', []):
        if not 0 <= h['start'] < h['end'] <= total:
            raise ValueError('Headline outside timeline')
        wrapped(h['text'])
    report = {'duration': total, 'speech': timing, 'caption_count': len(captions), 'captions_complete': True}
    if args.validate_only:
        print(json.dumps(report, indent=2)); return
    if output.exists():
        raise SystemExit(f'Existing export preserved: {output}. Choose a new version filename.')
    output.parent.mkdir(parents=True, exist_ok=True)
    work = output.parent / (output.stem + '-assets'); work.mkdir(exist_ok=True)
    rng = np.random.default_rng(13)
    for effect in doc.get('sfx', []):
        start = float(effect['start'])
        if not 0 <= start < total:
            raise ValueError('Sound effect outside timeline')
        t = np.arange(round(.22*SR)) / SR
        if effect['kind'] == 'hit':
            sound = np.sin(2*np.pi*(80*t-45*t*t))*np.exp(-t*16)*.16
        elif effect['kind'] == 'whoosh':
            sound = np.convolve(rng.normal(0, 1, len(t)), np.ones(11)/11, 'same')*np.sin(np.pi*t/.22)**2*.06
        else:
            raise ValueError('Unknown sound effect')
        at = round(start*SR); n = min(len(sound), len(mix)-at)
        mix[at:at+n] += sound[:n, None]
    with wave.open(str(work/'voice.wav'), 'wb') as f:
        f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR)
        f.writeframes((np.clip(mix, -.95, .95)*32767).astype('<i2').tobytes())
    font = doc.get('font', 'Arial')
    if any(c in font for c in ',\n\r'):
        raise ValueError('Invalid font name')
    ass = f'''[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,{font},70,&H00FFFFFF,&H0067EFFF,&H001C1815,&H90000000,-1,0,0,0,100,100,0,0,1,4,2,5,60,60,0,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    def event(a, b, text, y, size=70, color='FFFFFF'):
        if not re.fullmatch('[0-9A-Fa-f]{6}', color):
            raise ValueError('Color must be six BGR hex digits')
        return f'Dialogue: 1,{timestamp(a,True)},{timestamp(b,True)},Caption,,0,0,0,,{{\\an5\\pos(540,{y})\\fs{size}\\c&H{color}&\\fscx95\\fscy95\\t(0,100,\\fscx100\\fscy100)\\fad(25,35)}}{wrapped(text)}\n'
    for a, b, text in captions:
        ass += event(a, b, text, doc.get('caption_y', 1450))
    if doc.get('title'):
        ass += event(0, total, doc['title'], 170, 32)
    for h in doc.get('headlines', []):
        ass += event(h['start'], h['end'], h['text'], h.get('y', 340), h.get('size', 76), h.get('color', '67EFFF'))
    for arrow in doc.get('pointers', []):
        a, b = arrow['start'], arrow['end']
        x, y = arrow['x'], arrow['y']
        if not 0 <= a < b <= total or not 50 <= x <= 1030 or not 160 <= y <= 1800:
            raise ValueError('Pointer must fit the canvas and timeline')
        # Downward arrow tip at the verified object; stays above the object itself.
        points = [(x-45,y-150),(x-31,y-150),(x+2,y-53),(x+25,y-77),(x+12,y-12),(x-41,y-47),(x-15,y-47)]
        shape = 'm '+' '.join(map(str,points[0]))+' l '+' '.join(str(z) for point in points[1:] for z in point)
        ass += f'Dialogue: 3,{timestamp(a,True)},{timestamp(b,True)},Caption,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord0\\shad0\\c&H67EFFF&}}{shape}{{\\p0}}\n'
    (work/'captions.ass').write_text(ass, encoding='utf-8-sig')
    (work/'subtitles.srt').write_text('\n\n'.join(f'{i+1}\n{timestamp(a)} --> {timestamp(b)}\n{text}' for i,(a,b,text) in enumerate(captions))+'\n', encoding='utf-8')
    (work/'script.txt').write_text('\n'.join(s['text'] for s in doc.get('speech', [])), encoding='utf-8')
    (work/'manifest.json').write_text(json.dumps(doc, indent=2), encoding='utf-8')
    # Resolve all source and WAV paths before switching FFmpeg's working directory.
    for i, scene in enumerate(scenes):
        a, b, d = (float(scene[k]) for k in ('in', 'out', 'duration'))
        x, y, w, h = scene.get('crop', [0, 0, v['width'], v['height']])
        fh = int(scene.get('height', round(1080*h/w/2)*2)); fy = int(scene.get('y', (1920-fh)//2))
        speed = (b-a)/d
        vf = f'[0:v]setpts=(PTS-STARTPTS)/{speed},fps=30,split=2[b][f];[b]scale=270:480:force_original_aspect_ratio=increase,crop=270:480,boxblur=10:2,eq=brightness=-0.15,scale=1080:1920[bg];[f]crop={w}:{h}:{x}:{y},scale=1080:{fh}:flags=lanczos[fg];[bg][fg]overlay=0:{fy},setsar=1[v]'
        inp = ['-ss', a, '-t', b-a, '-i', source]
        if not has_audio:
            inp += ['-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo']
        run(inp + ['-filter_complex', vf, '-map', '[v]', '-map', '0:a:0' if has_audio else '1:a:0', '-af', tempo(speed)+',apad', '-t', d, '-c:v', 'libx264', '-preset', 'veryfast', '-crf', 18, '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-ar', SR, f'part{i:03}.mp4'], work)
        print(f'scene {i+1}/{len(scenes)}', flush=True)
    (work/'join.txt').write_text('\n'.join(f"file 'part{i:03}.mp4'" for i in range(len(scenes))))
    run(['-f', 'concat', '-safe', 0, '-i', 'join.txt', '-c', 'copy', 'gameplay.mp4'], work)
    ass_filter = 'ass=captions.ass'
    if doc.get('fonts_dir'):
        shutil.copytree((root/doc['fonts_dir']).resolve(), work/'fonts', dirs_exist_ok=True)
        ass_filter += ':fontsdir=fonts'
    gain = float(doc.get('game_gain', .65))
    if not math.isfinite(gain) or gain < 0:
        raise ValueError('game_gain must be nonnegative and finite')
    audio = f'[0:a]volume={gain},afade=t=out:st={max(0,total-.6)}:d=0.6[game];[1:a]asplit=2[voice][key];[game][key]sidechaincompress=threshold=0.025:ratio=5:attack=10:release=180[duck];[duck][voice]amix=inputs=2:normalize=0:duration=longest,loudnorm=I=-15:TP=-2:LRA=8[a]'
    run(['-i', 'gameplay.mp4', '-i', 'voice.wav', '-filter_complex', f'[0:v]{ass_filter}[v];'+audio, '-map', '[v]', '-map', '[a]', '-t', total, '-c:v', 'libx264', '-preset', 'fast', '-crf', 18, '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-ar', SR, '-movflags', '+faststart', output], work)
    run(['-i', output, '-f', 'null', '-'])
    run(['-i', output, '-vf', f'fps=1/{max(total/8,.1)},scale=270:480,tile=4x2', '-frames:v', 1, work/'review.jpg'])
    loudness = sp.run(['ffmpeg', '-hide_banner', '-i', str(output), '-af', 'loudnorm=I=-15:TP=-2:LRA=8:print_format=json', '-vn', '-f', 'null', '-'], capture_output=True, text=True, check=True).stderr
    match = re.search(r'\{\s*"input_i".*?\}', loudness, flags=re.S)
    report.update({'output': str(output), 'probe': probe(output), 'full_decode': 'passed', 'loudness': json.loads(match.group()) if match else 'unavailable', 'visual_review': 'Inspect review.jpg; not automatically approved'})
    (work/'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(output)

if __name__ == '__main__':
    main()

