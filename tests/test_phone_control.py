"""Phone control must not take ownership of unrelated scrcpy sessions."""
from pathlib import Path
import importlib.util
import os
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('phone_control', ROOT / 'phone-control.py')
phone = importlib.util.module_from_spec(spec)
spec.loader.exec_module(phone)


class PhoneControlTests(unittest.TestCase):
    def test_legacy_detection_ignores_mirroring_and_other_programs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for number, executable, arguments in [
                (123, 'scrcpy', b'scrcpy\0--otg\0'),
                (456, 'scrcpy', b'scrcpy\0--max-fps=120\0'),
                (789, 'other', b'other\0--otg\0'),
            ]:
                folder = root / str(number)
                folder.mkdir()
                (folder / 'exe').symlink_to(root / executable)
                (folder / 'cmdline').write_bytes(arguments)
            folders = list(root.iterdir())
            with patch.object(phone.Path, 'glob', return_value=folders):
                self.assertEqual(phone.manual_sessions(), [123])

    def test_start_uses_a_transient_session_service_and_usb_only(self):
        calls = []
        def run(*arguments, **kwargs):
            calls.append(arguments)
            output = ''
            if arguments[:2] == ('hyprctl', 'getoption'): output = '{"int":0}'
            elif arguments[:2] == ('hyprctl', 'activewindow'): output = '{"address":"0x1"}'
            elif arguments[:2] == ('hyprctl', 'cursorpos'): output = '{"x":5,"y":6}'
            elif arguments[:2] == ('hyprctl', 'clients'):
                output = '[{"pid":123,"address":"0x2","at":[16,16]}]'
                (Path(runtime) / 'steel-phone-capture-state').write_text('1')
            elif arguments[:2] == ('hyprctl', 'dispatch'): output = 'ok'
            elif 'MainPID' in arguments: output = '123'
            return SimpleNamespace(returncode=0, stderr='', stdout=output)
        with tempfile.TemporaryDirectory() as runtime, patch.object(phone.shutil, 'which', return_value='/usr/bin/scrcpy'), \
             patch.object(phone, 'run', side_effect=run), \
             patch.object(phone, 'active', return_value=True), \
             patch.object(phone, 'capture_library', return_value=Path('/runtime/capture.so')), \
             patch.object(phone.time, 'sleep'), \
             patch.dict(os.environ, {'WAYLAND_DISPLAY': 'wayland-test', 'XDG_RUNTIME_DIR': runtime}, clear=True):
            (Path(runtime) / '.ydotool_socket').touch()
            phone.start()
        arguments = next(call for call in calls if call[0] == 'systemd-run')
        self.assertEqual(arguments[0], 'systemd-run')
        self.assertIn('--collect', arguments)
        self.assertIn('--property=PartOf=graphical-session.target', arguments)
        self.assertIn('--setenv=WAYLAND_DISPLAY=wayland-test', arguments)
        self.assertIn('--otg', arguments)
        self.assertFalse(any('send_shortcut' in value for call in calls for value in call))
        self.assertFalse(any('mouse:272' in value for call in calls for value in call))
        self.assertFalse(any('adb' in value or 'HEADLESS' in value for value in arguments))


if __name__ == '__main__':
    unittest.main()
