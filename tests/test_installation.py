from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import desktop_launcher
import gpu_setup
import install_support
import setup_runtime


class InstallationTests(unittest.TestCase):
    def test_first_setup_never_calls_cuda_pip(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            tools = root / 'tools'
            (tools / 'ollama').mkdir(parents=True)
            (tools / 'ollama/ollama.exe').touch()
            with patch.object(setup_runtime, 'ROOT', root), patch.object(setup_runtime, 'TOOLS', tools), \
                 patch.object(setup_runtime, 'setup_node'), \
                 patch('requests.sessions.Session.request', side_effect=AssertionError('Bundled Ollama download forbidden')), \
                 patch.object(setup_runtime.subprocess, 'run', side_effect=AssertionError('CUDA pip forbidden')), \
                 patch('launcher.pull') as pull, patch('whisper_models.ensure_model') as whisper:
                setup_runtime.setup()
                pull.assert_called_once()
                whisper.assert_called_once()

    def test_portable_prepare_marks_ready_without_optional_gpu_installer(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with patch.object(desktop_launcher, 'ROOT', root), patch.object(desktop_launcher, 'READY', root / 'portable-ready.json'), \
                 patch.object(desktop_launcher, 'dependencies_ready', return_value=False), \
                 patch.object(install_support, 'install_requirements') as required, \
                 patch.object(setup_runtime, 'setup') as setup, \
                 patch.object(gpu_setup, 'install_gpu', side_effect=AssertionError('GPU install forbidden')):
                desktop_launcher.prepare()
                required.assert_called_once()
                setup.assert_called_once()
                self.assertTrue((root / 'portable-ready.json').is_file())

    def test_visible_progress_from_real_child_process(self):
        with tempfile.TemporaryDirectory() as folder:
            seen = []
            result = install_support.run_installer([sys.executable, '-u', '-c', "print('Progress 1048576 of 2097152',flush=True)"],
                timeout=10, root=folder, progress=seen.append)
            self.assertEqual(result, 0)
            self.assertTrue(any('50.0%' in line for line in seen), seen)
            self.assertIn('Progress 1048576', (Path(folder) / 'logs/install.log').read_text(encoding='utf-8'))

    def test_total_deadline_stops_real_process(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(TimeoutError):
                install_support.run_installer([sys.executable, '-u', '-c', 'import time;time.sleep(30)'],
                    timeout=.3, root=folder, progress=lambda _: None)

    def test_failed_required_install_does_not_mark_ready(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with patch.object(desktop_launcher, 'ROOT', root), patch.object(desktop_launcher, 'READY', root / 'portable-ready.json'), \
                 patch.object(desktop_launcher, 'dependencies_ready', return_value=False), \
                 patch.object(install_support, 'install_requirements', side_effect=TimeoutError('deadline')):
                with self.assertRaises(TimeoutError):
                    desktop_launcher.prepare()
                self.assertFalse((root / 'portable-ready.json').exists())

    def test_failed_gpu_install_preserves_cpu_ready_and_model_data(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            ready = root / 'portable-ready.json'
            ready.write_text('{"version":1}')
            (root / 'models').mkdir()
            model = root / 'models/test.bin'
            model.write_bytes(b'private model')
            with patch.object(gpu_setup, 'ROOT', root), \
                 patch.object(install_support, 'install_requirements', side_effect=TimeoutError('deadline')):
                with self.assertRaisesRegex(RuntimeError, 'CPU'):
                    gpu_setup.install_gpu(progress=lambda _: None)
            self.assertEqual(ready.read_text(), '{"version":1}')
            self.assertEqual(model.read_bytes(), b'private model')

    def test_gpu_install_refuses_active_summary(self):
        from filelock import FileLock
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with FileLock(str(root / '.pipeline.lock')), patch.object(gpu_setup, 'ROOT', root), \
                 patch.object(install_support, 'install_requirements') as install:
                with self.assertRaisesRegex(RuntimeError, '摘要任务'):
                    gpu_setup.install_gpu(progress=lambda _: None)
                install.assert_not_called()

    def test_gpu_install_command_has_explicit_progress_and_deadline(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(install_support, 'run_installer', return_value=0) as run:
            install_support.install_requirements(Path(folder) / 'requirements-gpu.txt', timeout=1200, root=folder)
            command = run.call_args.args[0]
            self.assertEqual(run.call_args.kwargs['timeout'], 1200)
            self.assertEqual(command[command.index('--progress-bar')+1], 'raw')
            self.assertIn('--cache-dir', command)
            self.assertIn('--no-warn-script-location', command)


if __name__ == '__main__':
    unittest.main()
