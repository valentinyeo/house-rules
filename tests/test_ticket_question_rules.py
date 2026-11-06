import importlib.machinery
import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


lint_mod = load("ticket_lint", ROOT / "skills/tickets/scripts/ticket-lint")
sweep = load("blocker_sweep", ROOT / "skills/tickets/scripts/blocker-sweep.py")


class QuestionLintTest(unittest.TestCase):
    def bad(self, body):
        if "Question:" in body:
            body = ("What this is: The app needs your choice today.\n"
                    "This is your call, not an agent choice.\n"
                    "Yes changes the app as described below.\n"
                    "No keeps the app as it stands.\n\n" + body)
            for part in ("My recommendation", "Why", "Yes", "No"):
                if part + ":" not in body:
                    body += f"\n\n{part}: Keep the app working."
        return "\n".join(lint_mod.question_rules(body))

    def test_money_ask_without_amount_is_refused(self):
        body = "Question: **Should we keep the paid plan?**\n\nMy recommendation: Yes.\n\nWhy: it saves money."
        self.assertIn("no amount", self.bad(body))

    def test_money_ask_with_amount_passes(self):
        body = "Question: **Should we keep the paid plan at $20 a month?**\n\nMy recommendation: Yes.\n\nWhy: it saves money."
        self.assertEqual(self.bad(body), "")

    def test_free_is_an_amount(self):
        body = "Question: **Should we move the logs to the free bucket?**\n\nWhy: no charge."
        self.assertEqual(self.bad(body), "")

    def test_once_ask_is_refused(self):
        body = "Question: **Should this go live once the checks pass?**\n\nMy recommendation: Yes."
        self.assertIn("once X", self.bad(body))

    def test_his_own_words_are_not_refused(self):
        body = 'Question: **Should we cut the paid calls?**\n\n> "this costs money once a month"\n\nWhy: no charge.'
        self.assertEqual(self.bad(body), "")

    def test_plain_comment_is_not_checked(self):
        self.assertEqual(self.bad("Money is tight and we pay a lot once a week."), "")


class SweepStaleTest(unittest.TestCase):
    def test_answered_wins(self):
        self.assertEqual(sweep.classify(True, "ticket sits in Done", True), "ANSWERED")

    def test_done_column_is_stale(self):
        self.assertEqual(sweep.classify(False, "ticket sits in No Flag", True), "STALE")

    def test_question_without_question_line(self):
        self.assertEqual(sweep.classify(False, "", False), "NO-QUESTION")

    def test_real_question_waits(self):
        self.assertEqual(sweep.classify(False, "", True), "WAITING")

    def test_merged_pr_after_the_question_is_stale(self):
        task = {"pullRequests": [
            {"number": 2498, "lifecycle": "merged", "updatedAt": "2026-10-29T15:52:58.823Z"},
        ]}
        self.assertIn("2498", sweep.merged_since(task, "2026-10-24T21:42:54.239Z"))

    def test_merged_pr_before_the_question_is_not_stale(self):
        task = {"pullRequests": [
            {"number": 2115, "lifecycle": "merged", "updatedAt": "2026-10-20T03:38:53.133Z"},
        ]}
        self.assertEqual(sweep.merged_since(task, "2026-10-24T21:42:54.239Z"), "")

    def test_open_pr_is_not_stale(self):
        task = {"pullRequests": [
            {"number": 2500, "lifecycle": "open", "updatedAt": "2026-10-30T15:52:58.823Z"},
        ]}
        self.assertEqual(sweep.merged_since(task, "2026-10-24T21:42:54.239Z"), "")


if __name__ == "__main__":
    unittest.main()
