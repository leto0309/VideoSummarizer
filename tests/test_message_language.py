import ast
from pathlib import Path
import re
import unittest

from opencc import OpenCC

ROOT = Path(__file__).resolve().parents[1]
# i18n converts its Simplified source text per language; local_llm swaps the zh-TW prompt by matching both names.
# setup_text.py and packaging/Launcher.cs hold explicit Traditional columns, checked in test_setup_text.
INTENTIONAL = {'i18n.py', 'local_llm.py', 'setup_text.py'}
CJK = re.compile(r'[一-鿿]')


class MessageLanguageTests(unittest.TestCase):
    def test_hard_coded_messages_use_simplified_chinese(self):
        t2s = OpenCC('t2s')
        sources = [*ROOT.glob('*.py'), *ROOT.glob('scripts/*.py')]
        found = []
        for path in sources:
            if path.name in INTENTIONAL:
                continue
            text = path.read_text(encoding='utf-8-sig')
            if path.suffix == '.py':
                literals = {node.value for node in ast.walk(ast.parse(text))
                            if isinstance(node, ast.Constant) and isinstance(node.value, str)}
            else:
                literals = set(re.findall(r'"((?:[^"\\]|\\.)*)"', text))
            for literal in literals:
                # The Traditional Chinese language name is written in its own script on purpose.
                if CJK.search(literal) and '繁體中文' not in literal and t2s.convert(literal) != literal:
                    found.append(f'{path.relative_to(ROOT)}: {literal[:60]}')
        self.assertEqual(found, [])


if __name__ == '__main__':
    unittest.main()
