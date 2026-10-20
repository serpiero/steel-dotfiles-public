"""Keep controllers/preferences intact when selecting the private Steel client."""
from pathlib import Path
import importlib.util
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('steel_style',Path(__file__).resolve().parents[1]/'app-style.py')
style=importlib.util.module_from_spec(spec)
spec.loader.exec_module(style)


class RetroarchStyleTests(unittest.TestCase):
    def test_private_config_is_seeded_once_and_native_is_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);original=root/'original';native=original/'retroarch/retroarch.cfg'
            native.parent.mkdir(parents=True)
            native.write_text('input_player1_joypad_index = "2"\nlibretro_directory = "/usr/lib/libretro"\n')
            before=native.read_bytes()
            client=root/'style/clients/retroarch/retroarch'
            client.parent.mkdir(parents=True);client.touch()
            with patch.object(style,'STYLE',root/'style'),patch.object(style,'ORIGINAL',original):
                args=['retroarch','--menu'];env={};style.retroarch_client(args,env)
                copied=Path(args[args.index('--config')+1])
                self.assertEqual(copied.read_bytes(),before)
                self.assertNotEqual(copied.resolve(),native.resolve())
                copied.write_text('input_player1_joypad_index = "3"\n')
                style.retroarch_client(['retroarch'],{})
                self.assertIn('"3"',copied.read_text())
                self.assertEqual(native.read_bytes(),before)
                self.assertEqual(args[0],str(client))

    def test_explicit_configuration_is_respected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);client=root/'clients/retroarch/retroarch'
            client.parent.mkdir(parents=True);client.touch()
            with patch.object(style,'STYLE',root):
                for option in (['--config','/chosen.cfg'],['-c','/chosen.cfg'],['--config=/chosen.cfg']):
                    args=['retroarch',*option];env={};style.retroarch_client(args,env)
                    self.assertEqual(args,[str(client),*option])
                    self.assertEqual(env,{'OBSIDIAN_RETROARCH_PALETTE':str(root/'native/retroarch.palette')})
