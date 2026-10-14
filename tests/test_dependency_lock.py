from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

from packaging.tags import Tag
from packaging.utils import canonicalize_name

import desktop_launcher
import gpu_setup
import install_support
from scripts.build_portable import add_hash, lock_block
from scripts.lock_requirements import installable, render

ROOT = Path(__file__).resolve().parents[1]
SRT_SOURCE = '4884315043a4f0740fd1f878ed6caa376ac06d70e135f306a6dc44632eed0cc0'  # srt-3.5.3.tar.gz on PyPI


def parse_lock(path):
    """Map canonical name to (version, hashes); fail on anything that is not a hashed exact pin."""
    entries, current = {}, None
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        if line.startswith(' '):
            digest = re.fullmatch(r' {4}--hash=sha256:([0-9a-f]{64})( \\)?', line)
            assert digest and current, line
            entries[current][1].append(digest.group(1))
            continue
        pin = re.fullmatch(r'([a-z0-9-]+)==(\S+) \\', line)
        assert pin, line
        current = pin.group(1)
        entries[current] = (pin.group(2), [])
    return entries


def direct_pins(path):
    pins = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.strip() and not line.startswith('#'):
            name, version = line.split('==', 1)
            pins[canonicalize_name(name.split('[', 1)[0])] = version.strip()
    return pins


class LockFileTests(unittest.TestCase):
    def test_locks_pin_every_package_with_hashes_and_match_the_direct_requirements(self):
        for source, lock in (('requirements.txt', 'requirements.lock'),
                             ('requirements-gpu.txt', 'requirements-gpu.lock')):
            with self.subTest(lock=lock):
                entries = parse_lock(ROOT / lock)
                self.assertTrue(all(hashes for _, hashes in entries.values()))
                for name, version in direct_pins(ROOT / source).items():
                    self.assertEqual(entries[name][0], version, name)
        main = parse_lock(ROOT / 'requirements.lock')
        self.assertGreater(len(main), len(direct_pins(ROOT / 'requirements.txt')))  # transitive packages too
        version, hashes = main['srt']
        self.assertEqual(version, '3.5.3')
        # The portable package's copy also accepts the wheel its build made from this archive.
        self.assertEqual(hashes[0], SRT_SOURCE)
        self.assertLessEqual(len(hashes), 2)

    def test_generator_keeps_only_files_this_platform_can_install(self):
        supported = {Tag('cp311', 'cp311', 'win_amd64'), Tag('py3', 'none', 'any')}
        files = [{'filename': 'pkg-1.0-cp311-cp311-win_amd64.whl', 'sha256': 'b' * 64, 'yanked': False},
                 {'filename': 'pkg-1.0-cp311-cp311-manylinux_2_17_x86_64.whl', 'sha256': 'c' * 64, 'yanked': False},
                 {'filename': 'pkg-1.0-py3-none-any.whl', 'sha256': 'a' * 64, 'yanked': True},
                 {'filename': 'pkg-1.0.tar.gz', 'sha256': 'd' * 64, 'yanked': False},
                 {'filename': 'pkg-1.0-py3.11.egg', 'sha256': 'e' * 64, 'yanked': False}]
        self.assertEqual(installable(files, supported), ['b' * 64, 'd' * 64])
        with tempfile.TemporaryDirectory() as folder:
            lock = Path(folder) / 'example.lock'
            lock.write_text(render([('Zeta_Pkg', '2.0', ['f' * 64]), ('alpha', '1.0', ['a' * 64, 'b' * 64])],
                                   'requirements.txt'), encoding='utf-8')
            self.assertEqual(parse_lock(lock), {'alpha': ('1.0', ['a' * 64, 'b' * 64]), 'zeta-pkg': ('2.0', ['f' * 64])})
            self.assertLess(lock.read_text(encoding='utf-8').index('alpha=='),
                            lock.read_text(encoding='utf-8').index('zeta-pkg=='))

    def test_portable_build_adds_the_built_srt_wheel_to_its_lock(self):
        with tempfile.TemporaryDirectory() as folder:
            lock = Path(folder) / 'requirements.lock'
            lock.write_text(render([('srt', '3.5.3', [SRT_SOURCE]), ('streamlit', '1.0', ['a' * 64])],
                                   'requirements.txt'), encoding='utf-8')
            self.assertEqual(lock_block(lock.read_text(encoding='utf-8'), 'srt'),
                             ['srt==3.5.3 \\', f'    --hash=sha256:{SRT_SOURCE}'])
            add_hash(lock, 'srt', 'f' * 64)
            entries = parse_lock(lock)
        self.assertEqual(entries['srt'], ('3.5.3', [SRT_SOURCE, 'f' * 64]))
        self.assertEqual(entries['streamlit'], ('1.0', ['a' * 64]))


class InstallPathTests(unittest.TestCase):
    def test_installer_requires_hashes(self):
        with patch.object(install_support, 'run_installer', return_value=0) as run:
            install_support.install_requirements(ROOT / 'requirements.lock', root=ROOT, progress=lambda _: None)
        command = run.call_args.args[0]
        self.assertIn('--require-hashes', command)
        self.assertEqual(command[-2:], ['-r', str(ROOT / 'requirements.lock')])

    def test_first_setup_and_gpu_install_use_the_locks(self):
        with tempfile.TemporaryDirectory() as folder, \
             patch.object(desktop_launcher, 'dependencies_ready', return_value=False), \
             patch.object(desktop_launcher, 'READY', Path(folder) / 'portable-ready.json'), \
             patch('install_support.install_requirements') as install, patch('setup_runtime.setup'):
            desktop_launcher.prepare()
            self.assertEqual(install.call_args.args[0], desktop_launcher.ROOT / 'requirements.lock')
            with patch.object(gpu_setup, 'ROOT', Path(folder)):
                gpu_setup.install_gpu(progress=lambda _: None)
            self.assertEqual(install.call_args.args[0], Path(folder) / 'requirements-gpu.lock')

    def test_scripts_and_workflows_install_the_hashed_lock(self):
        for name in ('setup.bat', '.github/workflows/windows-tests.yml', '.github/workflows/source-release.yml',
                     '.github/workflows/windows-portable.yml'):
            with self.subTest(file=name):
                text = (ROOT / name).read_text(encoding='utf-8')
                installs = [line for line in text.splitlines() if 'pip install' in line and ' -r ' in line]
                self.assertTrue(installs)
                for line in installs:
                    self.assertIn('--require-hashes', line)
                    self.assertRegex(line, r'requirements\.lock"?$')


if __name__ == '__main__':
    unittest.main()
