"""Read-only editing requirement check; installs nothing."""
import importlib.util
import json
import platform
import shutil
import subprocess

def main():
    r = {'os': platform.system(), 'architecture': platform.machine(), 'python': platform.python_version()}
    for name in ('ffmpeg', 'ffprobe'):
        r[name] = shutil.which(name)
    r['packages'] = {x: importlib.util.find_spec(x) is not None for x in ('numpy', 'PIL', 'voxcpm')}
    if r['ffmpeg']:
        filters = subprocess.check_output(['ffmpeg', '-hide_banner', '-filters'], text=True, stderr=subprocess.STDOUT)
        encoders = subprocess.check_output(['ffmpeg', '-hide_banner', '-encoders'], text=True, stderr=subprocess.STDOUT)
        r['libass'] = any(' ass ' in line for line in filters.splitlines())
        r['libx264'] = 'libx264 ' in encoders
    print(json.dumps(r, indent=2))
    ready = r['ffmpeg'] and r['ffprobe'] and r.get('libass') and r.get('libx264') and all(r['packages'][x] for x in ('numpy', 'PIL'))
    raise SystemExit(0 if ready else 1)

if __name__ == '__main__':
    main()
