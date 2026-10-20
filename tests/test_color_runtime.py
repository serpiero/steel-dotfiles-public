"""Profile isolation and real palette transitions, without screenshots or user state."""
from pathlib import Path
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec=importlib.util.spec_from_file_location(name.replace('/','_'),ROOT/name)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


class ColorRuntimeTests(unittest.TestCase):
    def test_firefox_default_detection_and_shared_profile_preservation(self):
        adapter=module('tools/firefox-theme.py')
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory);shared=base/'shared';shared.mkdir()
            (shared/'user.js').write_text('// Original KDE preferences\n')
            (base/'profiles.ini').write_text('[Profile0]\nDefault=1\nIsRelative=1\nPath=shared\n')
            self.assertEqual(adapter.detect_profile(base),shared)
            root=base/'steel';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.git','__pycache__'))
            (root/'INSTALLATION.json').write_text('{}')
            owned=adapter.refresh(root,base)
            self.assertTrue(owned.is_relative_to(root/'firefox'))
            self.assertEqual((shared/'user.js').read_text(),'// Original KDE preferences\n')
            (root/'firefox-profile-path').write_text(str(shared))
            with self.assertRaises(ValueError):adapter.refresh(root,base)

    def test_firefox_binary_snapshot_updates_only_its_own_files(self):
        adapter=module('tools/firefox-live.py')
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory);source=base/'vendor';source.mkdir()
            for name in ('firefox','libxul.so','omni.ja','browser/omni.ja','application.ini'):
                file=source/name;file.parent.mkdir(parents=True,exist_ok=True);file.write_text('vendor')
            root=base/'steel';(root/'obsidian/firefox').mkdir(parents=True)
            for name in ('userChrome.css','userContent.css'):(root/'obsidian/firefox'/name).write_text(':root{}')
            binary=adapter.prepare(root,source);self.assertTrue(binary.is_file())
            self.assertFalse((source/'steel.cfg').exists())
            bootstrap=(binary.parent/'steel.cfg').read_text()
            self.assertIn('loadAndRegisterSheet',bootstrap)
            self.assertIn('unregisterSheet',bootstrap)
            self.assertIn('/hyprland/i',bootstrap)
            before=binary.stat().st_mtime_ns
            self.assertEqual(adapter.prepare(root,source).stat().st_mtime_ns,before)

    def test_wine_shared_prefix_is_never_written(self):
        adapter=module('wine-style.py')
        with tempfile.TemporaryDirectory() as directory:
            shared=Path(directory);(shared/'user.reg').write_text('private')
            self.assertEqual(adapter.apply(shared),{'status':'shared-prefix-preserved'})
            self.assertEqual((shared/'user.reg').read_text(),'private')

    def test_cli_updates_palette_and_rejects_invalid_input_atomically(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'steel';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.git','__pycache__'))
            env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
            def run(*args):return subprocess.run([str(root/'steel-ctl'),'theme',*args],capture_output=True,text=True,env=env)
            result=run('set','background=#234567','accent=#abcdef')
            self.assertEqual(result.returncode,0,result.stderr)
            for name in ('firefox/userChrome.css','firefox/userContent.css','application-style/chatgpt.css','application-style/discord.css','application-style/spotify-steel.css'):
                self.assertIn('--steel-background: #234567;', (root/'obsidian'/name).read_text())
            saved=(root/'local-theme.json').read_bytes()
            self.assertNotEqual(run('set','background=invalid').returncode,0)
            self.assertEqual((root/'local-theme.json').read_bytes(),saved)
