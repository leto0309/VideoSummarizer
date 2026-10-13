from pathlib import Path
import re
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LintConfigTests(unittest.TestCase):
    def test_ruff_checks_errors_only_with_the_release_script_exception(self):
        config = tomllib.loads((ROOT / 'ruff.toml').read_text(encoding='utf-8'))
        self.assertEqual(config['lint']['select'], ['E4', 'E7', 'E9', 'F'])
        self.assertEqual(config['lint']['per-file-ignores'], {'scripts/*.py': ['E402']})

    def test_ci_runs_a_pinned_ruff(self):
        workflow = (ROOT / '.github/workflows/windows-tests.yml').read_text(encoding='utf-8')
        self.assertRegex(workflow, r'pip install ruff==\d+\.\d+\.\d+\b')
        self.assertIn('ruff check', workflow)
        version = re.search(r'ruff==(\d+\.\d+\.\d+)', workflow).group(1)
        self.assertIn(f'ruff=={version}', (ROOT / 'CONTRIBUTING.md').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
