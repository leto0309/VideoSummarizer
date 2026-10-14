import importlib.metadata
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
import yt_dlp

import desktop_launcher
from i18n import friendly_error, tr
import ytdlp_update

ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = (ROOT / 'requirements.txt').read_text(encoding='utf-8')
PINNED = {line.split('==')[0].split('[')[0]: line.split('==')[1]
          for line in REQUIREMENTS.splitlines() if line.strip() and not line.startswith('#')}


def installed_versions(**changes):
    versions = {**PINNED, **changes}
    return lambda package: versions[package]


class YtDlpUpdateTests(unittest.TestCase):
    def test_newer_download_component_does_not_trigger_setup_again(self):
        for changes, ready in (({}, True),
                               ({'yt-dlp': '2099.1.1.000000.dev0', 'yt-dlp-ejs': '9.9.9'}, True),
                               ({'yt-dlp': '2020.1.1'}, False),
                               ({'yt-dlp-ejs': '0.0.1'}, False),
                               ({'streamlit': '99.0.0'}, False)):
            with self.subTest(changes=changes), \
                 patch.object(importlib.metadata, 'version', side_effect=installed_versions(**changes)):
                self.assertEqual(desktop_launcher.dependencies_ready(), ready)

    def run_update(self, restore):
        with tempfile.TemporaryDirectory() as folder, \
             patch('install_support.run_installer', return_value=0) as run, \
             patch.object(ytdlp_update, 'LOCK', Path(folder) / '.pipeline.lock'):
            ytdlp_update.update(restore=restore, progress=lambda message: None)
        return run.call_args

    def test_update_installs_newest_nightly_into_this_python(self):
        call = self.run_update(restore=False)
        command = call.args[0]
        self.assertEqual(command[:4], [ytdlp_update.sys.executable, '-m', 'pip', 'install'])
        self.assertIn('--upgrade', command)
        self.assertIn('--pre', command)
        self.assertEqual(command[-1], 'yt-dlp[default]')
        self.assertIn(str(ROOT / 'tools/pip-cache'), command)
        self.assertEqual(call.kwargs['timeout'], 600)

    def test_restore_reinstalls_the_hashed_lock(self):
        command = self.run_update(restore=True).args[0]
        self.assertNotIn('--upgrade', command)
        self.assertIn('--require-hashes', command)
        self.assertEqual(command[-2:], ['-r', str(ROOT / 'requirements.lock')])

    def test_update_waits_for_running_summary_and_names_pypi_on_failure(self):
        from filelock import FileLock
        with tempfile.TemporaryDirectory() as folder:
            lock = Path(folder) / '.pipeline.lock'
            with patch.object(ytdlp_update, 'LOCK', lock), \
                 patch('install_support.run_installer') as run:
                with FileLock(str(lock)), self.assertRaisesRegex(RuntimeError, '摘要任务'):
                    ytdlp_update.update(progress=lambda message: None)
                run.assert_not_called()
                run.return_value = 1
                with self.assertRaises(subprocess.CalledProcessError) as failed:
                    ytdlp_update.update(progress=lambda message: None)
        self.assertIn('PyPI', failed.exception.__notes__[0])

    def test_platform_errors_point_to_the_updater(self):
        message = friendly_error(yt_dlp.utils.DownloadError('ERROR: Unable to extract'), 'zh-CN')
        self.assertEqual(message, tr('zh-CN', 'error_platform'))
        self.assertIn('update-ytdlp.bat', message)

    def test_batch_file_runs_the_updater_with_the_bundled_python(self):
        script = (ROOT / 'update-ytdlp.bat').read_text(encoding='utf-8')
        self.assertIn('runtime\\python.exe', script)
        self.assertIn('ytdlp_update.py --restore', script)


def page(vram, cuda_runtime):
    with patch('config.gpu_info', return_value={'name': 'Test GPU', 'vram_mib': vram, 'driver': None}), \
         patch('gpu_setup.installed', return_value=cuda_runtime), \
         patch('whisper_models.cached_model', return_value=None), \
         patch('preferences.load', return_value={'ui_language': 'zh-CN', 'summary_language': 'follow'}), \
         patch('preferences.save'):
        app = AppTest.from_file(str(ROOT / 'app.py')).run(timeout=30)
    return app


class GpuHintTests(unittest.TestCase):
    def test_hint_and_default_follow_gpu_and_runtime_state(self):
        for vram, runtime, hint, mode in ((0, False, 'gpu_cpu', 'cpu'), (0, True, 'gpu_cpu', 'cpu'),
                                          (12227, False, 'gpu_suggest', 'cpu'), (12227, True, 'gpu_ready', 'auto')):
            with self.subTest(vram=vram, runtime=runtime):
                app = page(vram, runtime)
                self.assertFalse(app.exception)
                self.assertTrue(app.info[0].value.endswith(tr('zh-CN', hint)), app.info[0].value)
                self.assertEqual(app.selectbox(key='mode').value, mode)
        self.assertIn('install-gpu.bat', tr('zh-CN', 'gpu_suggest'))

    def test_about_shows_the_download_component_version(self):
        app = page(0, False)
        expected = tr('zh-CN', 'ytdlp_version', version=importlib.metadata.version('yt-dlp'))
        self.assertIn(expected, [item.value for item in app.expander[0].markdown])


if __name__ == '__main__':
    unittest.main()
