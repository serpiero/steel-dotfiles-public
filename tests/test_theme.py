"""Regression checks for portable palette compilation and layout isolation."""
from pathlib import Path
import json
import shutil
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import theme


class ThemeTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        for name in ('themes', 'styles', 'features/whatsapp', 'features/rutracker'):
            shutil.copytree(theme.ROOT / name, self.root / name)
        folder = self.root / 'obsidian/firefox'
        folder.mkdir(parents=True)
        shutil.copy2(theme.ROOT / 'obsidian/firefox/darkreader-palette.json', folder)

    def override(self, patch):
        (self.root / 'local-theme.json').write_text(json.dumps(patch))

    def test_aliases_cycle_and_unknown_tokens(self):
        self.assertEqual(theme.resolve_colors({'surface': '{background}', 'background': '#ABCDEF'})['surface'], '#abcdef')
        for colors in ({'a': '{b}', 'b': '{a}'}, {'a': '{missing}'}, {'a': 'red; color: white'}):
            with self.assertRaises(ValueError): theme.resolve_colors(colors)

    def test_recolor_updates_browser_native_apps_and_recipe_together(self):
        self.override({'palette': {'colors': {'background': '#263847', 'accent': '#88bbcc'}}})
        colors = theme.palette(self.root)
        theme.render(self.root, colors)
        for name in ('firefox/userChrome.css', 'firefox/userContent.css', 'application-style/spotify-steel.css', 'application-style/chatgpt.css'):
            rendered = (self.root / 'obsidian' / name).read_text()
            self.assertIn('--steel-background: #263847;', rendered)
            self.assertIn('--steel-accent: #88bbcc;', rendered)
            self.assertNotIn('{{', rendered)
        self.assertIn('263847ff', (self.root / 'obsidian/hyprlock.conf').read_text())
        self.assertIn('#263847d9', (self.root / 'menu.rasi').read_text())
        self.assertIn('re0 = "88bbcc"', (self.root / 'obsidian/colors.lua').read_text())
        recipe = json.loads((self.root / 'obsidian/firefox/darkreader-palette.json').read_text())
        self.assertEqual(recipe['theme']['darkSchemeBackgroundColor'], '#263847')

    def test_phone_zoom_stays_inside_phone_media_query(self):
        self.override({'layout': {'phone': {'contentZoom': 1.5, 'chromeZoom': 1.3}}})
        theme.render(self.root)
        content = (self.root / 'obsidian/firefox/userContent.css').read_text()
        chrome = (self.root / 'obsidian/firefox/userChrome.css').read_text()
        self.assertIn('max-device-width: 1100px', content)
        self.assertIn('zoom: 1.5', content)
        self.assertIn('zoom: 1.3', chrome)

    def test_whatsapp_defaults_compact_alignment_and_domain_scope(self):
        self.override({'layout': {'whatsapp': {'width': 360}}})
        theme.render(self.root)
        script = (self.root / 'features/whatsapp/whatsapp.user.js').read_text()
        self.assertIn('"width":360', script)
        self.assertIn('@match        https://web.whatsapp.com/*', script)
        self.assertIn('translate(-50%, -50%)', script)
        self.assertIn("Keep the live native avatar", script)
        self.assertNotIn("cloneNode", script)
        self.assertNotIn('{{', script)

    def test_rutracker_uses_the_shared_palette(self):
        self.override({'palette': {'colors': {'accent': '#88bbcc', 'text': '#ddeeff'}}})
        theme.render(self.root)
        script = (self.root / 'features/rutracker/rutracker.user.js').read_text()
        self.assertIn('#88bbcc', script)
        self.assertIn('#ddeeff', script)
        self.assertNotIn('{{', script)

    def test_repeated_render_keeps_files_unchanged(self):
        files = theme.render(self.root)
        before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in files}
        theme.render(self.root)
        self.assertEqual(before, {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in files})

    def test_invalid_layout_rejected_before_writing(self):
        self.override({'layout': {'whatsapp': {'width': 120}}})
        with self.assertRaises(ValueError): theme.render(self.root)
        self.assertFalse((self.root / 'obsidian/firefox/userContent.css').exists())

    def test_theme_changes_invalidate_session_cache(self):
        first = theme.fingerprint(self.root)
        self.override({'palette': {'colors': {'accent': '#abccdd'}}})
        self.assertNotEqual(first, theme.fingerprint(self.root))

    def test_spotlight_uses_settings_font_and_shared_palette(self):
        settings=self.root/'ui/settings/config.json'
        settings.parent.mkdir(parents=True,exist_ok=True)
        settings.write_text(json.dumps({'appearance':{'fonts':{'main':'Readex Pro'}}}))
        self.override({'palette':{'colors':{'background':'#263847'}}})
        theme.render(self.root)
        spotlight=(self.root/'spotlight.rasi').read_text()
        self.assertIn('Readex Pro 11.25 @wght=450,wdth=100',spotlight)
        self.assertIn('#263847d9',spotlight)
        self.assertNotIn('{{',spotlight)


if __name__ == '__main__': unittest.main()
