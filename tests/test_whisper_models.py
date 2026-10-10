import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import speech
import whisper_models as models


def model_files(folder):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'model.bin').write_bytes(b'fixture-not-real-weights')
    (folder / 'config.json').write_text('{}')
    (folder / 'tokenizer.json').write_text('{}')
    (folder / 'vocabulary.txt').write_text('test')


class WhisperModelTests(unittest.TestCase):
    def test_offline_flat_model_needs_no_hub_import(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / 'whisper' / 'small'
            model_files(folder)
            with patch.object(models, 'MODELS', root), \
                 patch.dict(sys.modules, {'huggingface_hub': None}):
                self.assertEqual(models.ensure_model(), folder)

    def test_old_snapshot_cache_is_reused_without_network(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cache = root / 'whisper' / 'models--Systran--faster-whisper-small'
            folder = cache / 'snapshots' / ('a' * 40)
            model_files(folder)
            (cache / 'refs').mkdir()
            (cache / 'refs' / 'main').write_text('../outside')
            with patch.object(models, 'MODELS', root), \
                 patch.dict(sys.modules, {'huggingface_hub': None}):
                self.assertEqual(models.ensure_model(), folder)

    def test_partial_model_is_not_ready(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            model_files(folder)
            (folder / 'model.bin').write_bytes(b'')
            self.assertFalse(models.complete(folder))
            (folder / 'model.bin').write_bytes(b'weights')
            (folder / 'tokenizer.json').write_text('incomplete JSON')
            self.assertFalse(models.complete(folder))

    def test_download_failure_is_not_retried_on_cpu(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            download = Mock(side_effect=TimeoutError('connection timed out'))
            with patch.object(models, 'MODELS', root / 'models'), patch.object(models, 'ROOT', root), \
                 patch.dict(sys.modules, {'huggingface_hub': SimpleNamespace(snapshot_download=download)}), \
                 patch.object(speech.subprocess, 'run') as worker:
                with self.assertRaisesRegex(models.ModelUnavailableError, '切换 CPU'):
                    speech.transcribe(root / 'audio.wav', root)
                worker.assert_not_called()
                download.assert_called_once()
                self.assertIn('TimeoutError', (root / 'logs' / 'whisper-download.log').read_text())

    def test_public_download_has_no_auth_and_checks_completeness(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / 'models' / 'whisper' / 'snapshots' / 'test'
            model_files(folder)
            download = Mock(return_value=str(folder))
            with patch.object(models, 'MODELS', root / 'models'), patch.object(models, 'ROOT', root), \
                 patch.dict(sys.modules, {'huggingface_hub': SimpleNamespace(snapshot_download=download)}):
                self.assertEqual(models.ensure_model(), folder)
                self.assertFalse(download.call_args.kwargs['token'])
                self.assertEqual(download.call_args.kwargs['endpoint'], 'https://huggingface.co')
                (folder / 'model.bin').write_bytes(b'')
                with self.assertRaises(models.ModelUnavailableError):
                    models.ensure_model()

    def test_inference_workers_share_resolved_local_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / 'local-model'
            devices = []
            def worker(args, **kwargs):
                self.assertEqual(args[-2], str(folder))
                devices.append(args[-1])
                if args[-1] == 'cuda':
                    return subprocess.CompletedProcess(args, 1, '', 'missing cuDNN')
                (root / 'transcript.json').write_text(json.dumps({'language': 'en', 'cues': [
                    {'start': 0, 'end': 1, 'text': 'local model'}]}))
                return subprocess.CompletedProcess(args, 0, '', '')
            with patch.object(speech, 'ensure_model', return_value=folder) as prepare, \
                 patch.object(speech.subprocess, 'run', side_effect=worker):
                speech.transcribe(root / 'audio.wav', root)
            prepare.assert_called_once()
            self.assertEqual(devices, ['cuda', 'cpu'])

    def test_worker_loads_only_local_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            factory = Mock()
            factory.return_value.transcribe.return_value = ([], SimpleNamespace(language='en'))
            with patch.object(speech, 'configure_runtime'), \
                 patch.dict(sys.modules, {'faster_whisper': SimpleNamespace(WhisperModel=factory),
                                          'ctranslate2': SimpleNamespace()}):
                speech._worker('audio.wav', str(root / 'transcript.json'), str(root / 'model'), 'cpu')
            self.assertTrue(factory.call_args.kwargs['local_files_only'])
            self.assertEqual(factory.call_args.args[0], str(root / 'model'))


if __name__ == '__main__':
    unittest.main()
