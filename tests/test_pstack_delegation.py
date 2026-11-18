"""Keep known pstack duplicates out of the local overrides."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PstackDelegationTest(unittest.TestCase):
    def test_house_rules_delegates_existing_pstack_behavior(self):
        text = (ROOT / 'house-rules.md').read_text().lower()
        duplicates = {
            'shipping.md': (
                r'every pr gets a pstack verifier',
                r'an agent that did not write it',
                r'runs the change like a user',
                r'posts pass, pass\+notes or fail',
                r'a bot review or green ci is not a verdict',
            ),
            'principle-never-block-on-the-human/SKILL.md': (
                r'no chat ever waits for valentin to keep working',
            ),
            'poteto-mode/SKILL.md': (r'no need to ask anyone',),
            'correct/SKILL.md': (
                r'a check beats a sentence',
                r'drop a line once its mistake can.t happen',
            ),
        }
        for source, patterns in duplicates.items():
            with self.subTest(source=source):
                for pattern in patterns:
                    self.assertIsNone(re.search(pattern, text),
                                      f'Delegate to pstack {source}: {pattern}')
                self.assertIn(source.lower(), text, f'Link to pstack {source}')

    def test_audit_link_survives_sync_to_other_repositories(self):
        text = (ROOT / 'house-rules.md').read_text()
        match = re.search(r'\[audit\]\(([^)]+)\)', text)
        self.assertIsNotNone(match, 'Keep the line audit accessible')
        self.assertTrue(match.group(1).startswith('https://github.com/'),
                        'Use an absolute audit URL in synced rules')

    def test_local_verifier_difference_survives(self):
        text = (ROOT / 'house-rules.md').read_text().lower()
        self.assertIn('another model family', text)
        self.assertIn('github-hosted', text)
        self.assertIn('no self-hosted runner', text)


if __name__ == '__main__':
    unittest.main()
