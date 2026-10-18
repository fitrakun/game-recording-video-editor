"""Create a labeled contact sheet using direct seeks, not a full decode."""
import argparse
import subprocess as sp
from pathlib import Path
from PIL import Image, ImageDraw

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--start', type=float, default=0)
    p.add_argument('--end', type=float, required=True)
    p.add_argument('--step', type=float, default=120)
    args = p.parse_args()
    if not args.source.is_file() or args.start < 0 or args.step <= 0 or args.end <= args.start:
        p.error('Need source and 0 <= start < end, step > 0')
    times = []
    t = args.start
    while t < args.end:
        times.append(t)
        t += args.step
    if len(times) > 100:
        p.error('Use <=100 frames per sheet; split larger ranges')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    folder = args.output.parent / (args.output.stem + '-frames')
    folder.mkdir(exist_ok=True)
    sheet = Image.new('RGB', (1600, 205 * ((len(times) + 4) // 5)), '#171717')
    draw = ImageDraw.Draw(sheet)
    for i, t in enumerate(times):
        target = folder / f'{i:03}-{t:.2f}.jpg'
        sp.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-ss', str(t), '-i', str(args.source), '-frames:v', '1', '-vf', 'scale=320:180', str(target)], check=True)
        with Image.open(target) as img:
            sheet.paste(img, (i % 5 * 320, i // 5 * 205))
        draw.text((i % 5 * 320 + 8, i // 5 * 205 + 183), f'{int(t)//60:02}:{t%60:05.2f} ({t:.2f}s)', fill='white')
    sheet.save(args.output)
    print(args.output.resolve())

if __name__ == '__main__':
    main()
