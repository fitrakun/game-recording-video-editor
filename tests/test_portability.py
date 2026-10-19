import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import wave

ROOT=Path(__file__).resolve().parents[1]
NAME='game-recording-video-editor'

class InstallerTests(unittest.TestCase):
    def command(self,*args):
        return subprocess.run([sys.executable,str(ROOT/'scripts/install_skill.py'),*map(str,args)],capture_output=True,text=True)

    def test_agent_project_destinations(self):
        with tempfile.TemporaryDirectory(prefix='skill test ') as tmp:
            for agent,folder in [('codex','.agents'),('claude','.claude'),('opencode','.opencode'),('agents','.agents')]:
                result=self.command('--agent',agent,'--project',tmp,'--dry-run')
                self.assertEqual(result.returncode,0,result.stderr)
                self.assertIn(str(Path(tmp)/folder/'skills'/NAME),result.stdout)
                self.assertFalse((Path(tmp)/folder).exists())

    def test_install_preserves_existing_and_can_back_up(self):
        with tempfile.TemporaryDirectory(prefix='skill install ') as tmp:
            parent=Path(tmp)/'skills'
            result=self.command('--agent','claude','--dest',parent)
            self.assertEqual(result.returncode,0,result.stderr)
            installed=parent/NAME
            self.assertTrue((installed/'SKILL.md').is_file())
            self.assertFalse(list(installed.rglob('*.pyc')))
            marker=installed/'personal-note.txt';marker.write_text('keep me')
            result=self.command('--dest',parent)
            self.assertNotEqual(result.returncode,0)
            self.assertEqual(marker.read_text(),'keep me')
            result=self.command('--dest',parent,'--replace')
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertFalse((installed/'personal-note.txt').exists())
            backups=list((Path(tmp)/'skill-backups').glob(NAME+'-*'))
            self.assertEqual(len(backups),1)
            self.assertEqual((backups[0]/'personal-note.txt').read_text(),'keep me')

    def test_downloaded_zip_folder_uses_canonical_name(self):
        with tempfile.TemporaryDirectory(prefix='skill zip ') as tmp:
            checkout=Path(tmp)/(NAME+'-main')
            shutil.copytree(ROOT,checkout,ignore=shutil.ignore_patterns('.git','__pycache__','*.pyc'))
            (checkout/'.env').write_text('PRIVATE_SETTING=not-for-copying')
            (checkout/'private-recording.mp4').write_bytes(b'not real media')
            result=subprocess.run([sys.executable,str(checkout/'scripts/install_skill.py'),'--dest',str(Path(tmp)/'target')],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertTrue((Path(tmp)/'target'/NAME/'SKILL.md').is_file())
            self.assertFalse((Path(tmp)/'target'/NAME/'.env').exists())
            self.assertFalse((Path(tmp)/'target'/NAME/'private-recording.mp4').exists())

@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'FFmpeg/ffprobe required for real audio checks')
class CaptionAudioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import numpy as np
        except ImportError:
            raise unittest.SkipTest('NumPy required')
        spec=importlib.util.spec_from_file_location('skill_renderer',ROOT/'scripts/render_short.py')
        cls.renderer=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.renderer)
        cls.np=np

    def fixture(self,path):
        np=self.np
        t=np.arange(48000)/48000
        audio=(np.sin(2*np.pi*220*t)*.2*32767).astype('<i2')
        with wave.open(str(path),'wb') as w:
            w.setnchannels(1);w.setsampwidth(2);w.setframerate(48000);w.writeframes(audio.tobytes())

    def test_speed_and_captions_share_real_audio_boundaries(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.fixture(root/'phrase.wav')
            doc={'narration_rate':1.25,'speech':[{'start':.2,'text':'I actually found it!','wav':'phrase.wav'}]}
            mix,cues,timing=self.renderer.prepare_speech(doc,root,2)
            self.assertEqual(cues[0][2],'I actually found it!')
            self.assertAlmostEqual(timing[0]['end']-.2,.8,delta=.04)
            self.assertEqual(cues[0][1],timing[0]['end'])
            self.assertEqual(mix.shape,(96000,2))

    def test_missing_caption_words_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.fixture(root/'phrase.wav')
            doc={'speech':[{'start':0,'text':'I actually found it!','wav':'phrase.wav','cues':[{'start':0,'end':1,'text':'Found it!'}]}]}
            with self.assertRaisesRegex(ValueError,'omit/change spoken words'):
                self.renderer.prepare_speech(doc,root,2)

if __name__=='__main__':
    unittest.main()
