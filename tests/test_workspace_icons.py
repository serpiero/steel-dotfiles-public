"""Check artwork selection with synthetic themes, independent of display scale."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import workspace_icons


class WorkspaceIconTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)

    def theme(self, name, sizes, inherits=''):
        folder = self.root / name
        folder.mkdir()
        text = '[Icon Theme]\nDirectories=' + ','.join(sizes) + '\nInherits=' + inherits + '\n'
        for directory, size in sizes.items():
            (folder / directory).mkdir(parents=True)
            text += f'[{directory}]\nSize={size}\n'
        (folder / 'index.theme').write_text(text)
        return folder

    def test_vector_and_application_variant_preferred(self):
        folder = self.theme('selected', {'16/apps': 16, '48/apps': 48, '64/apps': 64})
        for name in ('16/apps/browser.svg', '48/apps/browser.svg', '64/apps/browser.png'):
            (folder / name).write_text('fixture')
        chosen = workspace_icons.sources('selected', [self.root])
        self.assertEqual(chosen['browser'], (folder / '48/apps/browser.svg').as_uri())
        self.assertEqual(chosen, workspace_icons.sources('selected', [self.root]))

    def test_theme_inheritance_keeps_selected_artwork(self):
        selected = self.theme('selected', {'16/apps': 16}, 'parent')
        parent = self.theme('parent', {'48/apps': 48}, 'selected')
        (selected / '16/apps/browser.png').write_text('fixture')
        (parent / '48/apps/browser.svg').write_text('fixture')
        (parent / '48/apps/terminal.svg').write_text('fixture')
        chosen = workspace_icons.sources('selected', [self.root])
        self.assertEqual(chosen['browser'], (selected / '16/apps/browser.png').as_uri())
        self.assertEqual(chosen['terminal'], (parent / '48/apps/terminal.svg').as_uri())

    def test_missing_theme_uses_standard_fallback(self):
        fallback = self.theme('hicolor', {'48/apps': 48})
        (fallback / '48/apps/terminal.svg').write_text('fixture')
        self.assertEqual(workspace_icons.sources('missing', [self.root]), {
            'terminal': (fallback / '48/apps/terminal.svg').as_uri(),
        })


if __name__ == '__main__':
    unittest.main()
