import json
from pathlib import Path
import tempfile
import unittest
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from unittest.mock import patch
from subtitles import Cue, parse, chunks, stamp, to_srt
from downloader import validate_url
import storage
from config import ALLOWED_MODELS
from local_llm import LocalLLM
import speech
import downloader


class CoreTests(unittest.TestCase):
    def test_subtitle_roundtrip(self):
        cues = [Cue(.123, 2.456, '第一行\n第二行'), Cue(3601, 3602, '測試')]
        self.assertEqual(parse(to_srt(cues), 'srt'), cues)
        self.assertEqual(stamp(3661.9996), '01:01:02.000')

    def test_bilibili_json(self):
        cues = parse('{"body":[{"from":1.25,"to":2.5,"content":"測試"}]}', 'json')
        self.assertEqual(cues[0].start, 1.25)

    def test_vtt_markup_and_timing(self):
        cues = parse('WEBVTT\n\n00:01.234 --> 00:03.456 align:start\n<b>測試</b> &amp;\n', 'vtt')
        self.assertEqual(cues, [Cue(1.234, 3.456, '測試 &')])

    def test_long_cue_does_not_overflow(self):
        result = list(chunks([Cue(0, 10, '字'*9000)]))
        self.assertGreater(len(result), 1)
        self.assertTrue(all(len(x) <= 1500 for x in result))
        self.assertEqual(sum(x.count('字') for x in result), 9000)

    def test_url_allowlist(self):
        for url in ['http://b23.tv/x', 'https://b23.tv.evil.test/x', 'https://user:pass@youtube.com/x', 'file:///C:/x']:
            with self.assertRaises(ValueError):
                validate_url(url)
        self.assertEqual(validate_url('https://b23.tv/example'), 'https://b23.tv/example')

    def test_cloud_rejected(self):
        with self.assertRaises(ValueError):
            LocalLLM('qwen3-vl:cloud')

    def test_cleanup_preserves_unmarked_and_unexpired(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            untouched = root / 'user_files'
            untouched.mkdir()
            (untouched / 'important.txt').write_text('keep')
            def make(name, age):
                task = root / name
                task.mkdir()
                (task / 'task.json').write_text(json.dumps({'owner': storage.MARKER, 'id': name,
                                                          'status': 'failed', 'failed_at': 100000-age}))
                return task
            recent = make('a'*32, 200)
            expired = make('b'*32, 86401)
            storage.cleanup(root, now=100000)
            self.assertTrue(recent.exists())
            self.assertFalse(expired.exists())
            self.assertTrue((untouched / 'important.txt').exists())
            with self.assertRaises(RuntimeError):
                storage.remove_task(untouched, root)

    def test_quota_preserves_failed_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            file = root / 'keep.bin'
            file.write_bytes(b'x'*100)
            with patch.object(storage, 'TEMP_LIMIT', 150), patch.object(storage, 'RESERVE', 60):
                with self.assertRaises(RuntimeError):
                    storage.guard(root=root)
            self.assertTrue(file.exists())

    def test_cleanup_rejects_reparse_ancestor(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task = root / ('a' * 32)
            task.mkdir()
            marker = task / 'task.json'
            marker.write_text(json.dumps({'owner': storage.MARKER, 'id': task.name}))
            original = storage._unsafe
            with patch.object(storage, '_unsafe', side_effect=lambda path: path == root.parent or original(path)):
                with self.assertRaisesRegex(RuntimeError, 'junction'):
                    storage.remove_task(task, root)
            self.assertTrue(marker.exists())

    def test_cuda_failure_retries_cpu(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            devices = []
            def worker(args, **kwargs):
                import subprocess
                device = args[-1]
                devices.append(device)
                if device == 'cuda':
                    return subprocess.CompletedProcess(args, 1, '', 'missing cuDNN')
                (root / 'transcript.json').write_text(json.dumps({'language': 'en', 'cues': [
                    {'start': 0, 'end': 1, 'text': 'CPU fallback works'}]}))
                return subprocess.CompletedProcess(args, 0, '', '')
            with patch.object(speech.subprocess, 'run', side_effect=worker):
                cues, info = speech.transcribe(root / 'audio.wav', root)
            self.assertEqual(devices, ['cuda', 'cpu'])
            self.assertEqual(info['compute_type'], 'int8')
            self.assertTrue(info['fallback_reason'])

    def test_audio_download_does_not_reuse_video_merge_plan(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audio = root / 'audio.m4a'
            audio.write_bytes(b'test-audio')
            info = {'id': 'example', 'webpage_url': 'https://www.youtube.com/watch?v=example',
                    'formats': [{'format_id': 'audio'}], '__postprocessors': ['stale-video-merger']}
            with patch.object(downloader.yt_dlp, 'YoutubeDL') as factory, patch.object(downloader, 'guard'):
                client = factory.return_value.__enter__.return_value
                client.extract_info.return_value = {'id': 'example'}
                client.prepare_filename.return_value = str(audio)
                self.assertEqual(downloader.download(info, root), audio)
                self.assertEqual(factory.call_args.args[0]['format'], 'bestaudio/best')
                client.process_ie_result.assert_not_called()
                client.extract_info.assert_called_once_with(info['webpage_url'], download=True)

    def test_source_spelling_context_is_bounded(self):
        from pipeline import source_context
        context = source_context({'title': 'Yoinks', 'description': 'Source', 'frames': [
            {'description': 'Pure Chinese text'}, {'description': 'Powered by yt-dlp. ffmpeg. '+('English '*500)}]})
        self.assertIn('yt-dlp', context)
        self.assertLessEqual(len(context), 900)


if __name__ == '__main__':
    unittest.main()
