import sys
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock, patch

import launcher


class LauncherTests(TestCase):
    def test_unknown_healthy_web_port_is_not_reused(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'logs').mkdir()
            session = Mock()
            session.get.return_value.ok = True
            with patch.object(launcher, 'ROOT', root), patch.object(launcher, 'ensure_server'), \
                 patch.object(launcher, 'startup_status'), patch.object(launcher.requests, 'Session', return_value=session), \
                 patch.object(launcher, 'owned_process', return_value=False), \
                 patch.object(launcher.subprocess, 'Popen') as spawn, \
                 patch.object(sys, 'argv', ['launcher.py', '--headless']):
                with self.assertRaisesRegex(RuntimeError, '未知服務'):
                    launcher.main()
                spawn.assert_not_called()

    def test_existing_project_web_is_reused(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'logs').mkdir()
            (root / 'logs' / 'streamlit.pid').write_text('123')
            session = Mock()
            session.get.return_value.ok = True
            with patch.object(launcher, 'ROOT', root), patch.object(launcher, 'ensure_server'), \
                 patch.object(launcher, 'startup_status'), patch.object(launcher.requests, 'Session', return_value=session), \
                 patch.object(launcher, 'owned_process', return_value=True), \
                 patch.object(launcher.subprocess, 'Popen') as spawn, \
                 patch.object(sys, 'argv', ['launcher.py', '--headless']):
                with self.assertRaises(SystemExit) as result:
                    launcher.main()
                self.assertEqual(result.exception.code, 0)
                spawn.assert_not_called()
