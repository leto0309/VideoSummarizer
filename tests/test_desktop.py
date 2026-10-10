import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import desktop_launcher as desktop


class DesktopTests(unittest.TestCase):
    def test_missing_dependencies_require_setup(self):
        with patch.object(desktop, 'dependencies_ready', return_value=False):
            self.assertTrue(desktop.needs_setup())

    def test_failed_pip_does_not_mark_setup_complete(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with patch.object(desktop, 'ROOT', root), patch.object(desktop, 'READY', root / 'ready.json'), \
                 patch.object(desktop, 'dependencies_ready', return_value=False), \
                 patch('install_support.install_requirements', side_effect=subprocess.CalledProcessError(1, 'pip')) as run:
                with self.assertRaises(subprocess.CalledProcessError):
                    desktop.prepare()
                self.assertEqual(run.call_args.args[0], root / 'requirements.txt')
                self.assertFalse((root / 'ready.json').exists())

    def test_ready_requires_tools_and_marker(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            ready = root / 'ready.json'
            with patch.object(desktop, 'ROOT', root), patch.object(desktop, 'READY', ready), \
                 patch.object(desktop, 'dependencies_ready', return_value=True):
                self.assertTrue(desktop.needs_setup())
                ready.write_text(json.dumps({'version': 1}))
                self.assertTrue(desktop.needs_setup())
                for name in ('tools/ollama/ollama.exe', 'tools/node/node.exe'):
                    file = root / name
                    file.parent.mkdir(parents=True, exist_ok=True)
                    file.write_bytes(b'test')
                self.assertFalse(desktop.needs_setup())

    def test_bootstrap_check_works_without_site_packages(self):
        result = subprocess.run([sys.executable, '-S', str(desktop.ROOT / 'desktop_launcher.py'), '--check'],
                                capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 10, result.stderr)
