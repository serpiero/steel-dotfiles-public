"""Guard Aerion's native launch identity and HSL palette contract."""
from pathlib import Path
import importlib.util
import tempfile
import unittest
import json
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('steel_app_style',ROOT/'app-style.py')
style=importlib.util.module_from_spec(spec)
spec.loader.exec_module(style)

class AerionStyleTests(unittest.TestCase):
    def test_wrapper_resolves_native_and_injects_only_once(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);wrapper=root/'web-runtime/bin';wrapper.mkdir(parents=True)
            stock=root/'native';stock.mkdir();native=stock/'aerion';native.write_text('#!/bin/sh\nexit 0\n');native.chmod(0o755)
            library=root/'style/webkit-style.so';library.parent.mkdir()
            base={'PATH':str(wrapper)+':'+str(stock),'LD_PRELOAD':str(library)+':/other/library.so:'+str(library),
                  'XDG_CONFIG_HOME':str(root/'style/config'),'OBSIDIAN_WEBKIT_CSS':str(root/'style/webkit.css')}
            with patch.object(style,'ROOT',root),patch.object(style,'STYLE',library.parent),patch.object(style,'CONFIG',root/'style/config'),patch.object(style,'ORIGINAL',root/'original'),patch.object(style,'webkit_library',return_value=library):
                args=['aerion'];environment=style.aerion_environment(args,base)
                self.assertEqual(args,[str(native)])
                self.assertEqual(environment['LD_PRELOAD'].split(':').count(str(library)),1)
                self.assertIn('/other/library.so',environment['LD_PRELOAD'])
                self.assertEqual(environment['XDG_CONFIG_HOME'],str(root/'original'))
                restored=style.original_environment(environment)
                self.assertNotIn(str(library),restored['LD_PRELOAD'])
                self.assertNotIn('OBSIDIAN_WEBKIT_CSS',restored)

    def test_manual_activation_waits_for_start_hidden_handoff(self):
        owner=123
        replies=[SimpleNamespace(returncode=0,stdout=json.dumps(x)) for x in [[],[{'pid':owner}],[]]]
        replies.append(SimpleNamespace(returncode=0,stdout=''))
        with patch.object(style.os,'kill'),patch.object(style.subprocess,'run',side_effect=replies) as run,patch('time.sleep'):
            style.activate_aerion_once('/native/aerion',owner)
        self.assertEqual(run.call_args_list[-1].args[0],['/native/aerion'])
        self.assertEqual(run.call_count,4)

    def test_autostart_keeps_its_background_marker(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);original=root/'original';folder=original/'autostart';folder.mkdir(parents=True)
            target=folder/'io.github.hkdb.Aerion.desktop';target.write_text('[Desktop Entry]\nName=Aerion\nExec=/usr/local/bin/aerion\n')
            with patch.object(style,'ROOT',root),patch.object(style,'ORIGINAL',original),patch.object(style,'STYLE',root/'style'):
                style.update_aerion_autostart();first=target.read_text();style.update_aerion_autostart()
            self.assertIn('STEEL_AUTOSTART=1',first)
            self.assertEqual(target.read_text(),first)

    def test_webkit_style_preserves_surface_and_email_frame_scope(self):
        stylesheet=(ROOT/'styles/applications/webkit.css').read_text()
        injector=(ROOT/'obsidian/application-style/webkit-style.c').read_text()
        self.assertIn('{{palette.background_hsl}}',stylesheet)
        self.assertIn('html:has(#app)',stylesheet)
        self.assertNotIn('background-color: transparent',stylesheet)
        self.assertIn('WEBKIT_USER_CONTENT_INJECT_TOP_FRAME',injector)
        self.assertNotIn('WEBKIT_USER_CONTENT_INJECT_ALL_FRAMES',injector)

if __name__=='__main__':unittest.main()
