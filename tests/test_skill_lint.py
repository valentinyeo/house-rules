import contextlib
import importlib.machinery
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/skill-lint"
loader = importlib.machinery.SourceFileLoader("skill_lint", str(SCRIPT))
spec = importlib.util.spec_from_loader(loader.name, loader)
lint = importlib.util.module_from_spec(spec)
loader.exec_module(lint)
FIXTURES = Path(__file__).parent / "fixtures/skill-lint"
HEADER = "---\nname: sample\ndescription: Use when preparing a local release.\n---\n\n"
COPIED = "Keep only prose that changes a decision and delegate to the original skill by path."


class SkillLintTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.pstack = self.root / "upstream/skills"
        self.source = self.pstack / "poteto-mode/SKILL.md"
        self.source.parent.mkdir(parents=True)
        self.source.write_text(HEADER + COPIED + "\n")
        self.house = self.root / "house-rules.md"
        self.house.write_text("Use the private team workspace for each customer's billing records.\n")
        self.file = self.root / "skills/sample/SKILL.md"
        self.file.parent.mkdir(parents=True)
        self.sources = lint.Sources(self.pstack, self.house)

    def check(self, body="Distinct instructions for this product.\n", header=HEADER, **kwargs):
        self.file.write_text(header + body)
        return lint.lint(self.file, self.root, self.pstack, self.house, self.sources, [], **kwargs)

    def cli(self, *args, env=None):
        environment = env if env is not None else {key: value for key, value in os.environ.items() if key != "GITHUB_EVENT_PATH"}
        return subprocess.run(["python3", str(SCRIPT), "--root", str(self.root), "--pstack", str(self.pstack), "--house-rules", str(self.house), *args], text=True, capture_output=True, env=environment)

    def git(self, *args):
        return lint.git(self.root, *args)

    def commit(self):
        self.git("add", ".")
        self.git("-c", "user.name=Skill Lint", "-c", "user.email=skill-lint@example.invalid", "commit", "-qm", "fixture")
        return self.git("rev-parse", "HEAD")

    def test_small_original_skill_passes(self):
        self.assertEqual(self.check(), [])

    def test_budget_counts_the_whole_file(self):
        errors = self.check("word " * 801)
        self.assertIn("exceed budget 800", "\n".join(errors))
        self.assertTrue(all(error.startswith("skills/sample/SKILL.md:") for error in errors))

    def test_higher_budget_requires_frontmatter_reason(self):
        header = HEADER.replace("name: sample", "skill-word-budget: 1000\nname: sample")
        self.assertIn("add skill-word-budget-reason", "\n".join(self.check("word " * 850, header)))
        header = header.replace("name: sample", "skill-word-budget-reason: Reference protocol must remain together.\nname: sample")
        self.assertEqual(self.check("word " * 850, header), [])

    def test_body_reason_cannot_raise_budget(self):
        self.assertIn("add skill-word-budget-reason", "\n".join(self.check("skill-word-budget-reason: outside frontmatter", HEADER.replace("name: sample", "skill-word-budget: 1000\nname: sample"))))

    def test_invalid_budget_and_boolean_reason_fail(self):
        for value in ("many", "true", "799", "900.5"):
            with self.subTest(value=value):
                self.assertIn("set skill-word-budget", "\n".join(self.check(header=HEADER.replace("name: sample", f"skill-word-budget: {value}\nname: sample"))))
        self.assertIn("add skill-word-budget-reason", "\n".join(self.check(header=HEADER.replace("name: sample", "skill-word-budget: 1000\nskill-word-budget-reason: true\nname: sample"))))

    def test_exact_and_near_copy_link_to_source(self):
        for sentence in (COPIED, "- **Keep** only prose that changes a decision; delegate to the original skill by path."):
            with self.subTest(sentence=sentence):
                errors = self.check(sentence)
                self.assertTrue(any(f"link to {self.source}:" in error and "instead of restating" in error for error in errors))

    def test_wrapped_copy_and_house_rules_copy_fail(self):
        self.assertTrue(any("instead of restating" in e for e in self.check(COPIED.replace(" and ", "\nand "))))
        self.assertTrue(any(str(self.house) in e for e in self.check(self.house.read_text())))

    def test_unrelated_shared_vocabulary_passes(self):
        self.assertEqual(self.check("Read the release skill when a customer changes the billing address."), [])

    def test_fenced_examples_are_not_rules_or_links(self):
        self.assertEqual(self.check("```md\n" + COPIED + "\n[example](missing.md)\n```\n"), [])

    def test_frontmatter_is_valid_yaml_with_required_strings(self):
        for header in ("", "---\nname: []\ndescription: false\n---\n", "---\nname: [\n---\n", "---\n- list\n---\n"):
            with self.subTest(header=header):
                self.assertTrue(self.check(header=header))
        self.assertEqual(self.check(header="---\nname: sample\ndescription: >-\n  Use for local release checks.\n---\n"), [])

    def test_file_and_skill_references_must_exist(self):
        for body in ("Read [details](missing.md).", "Read `missing.md`.", "Run `/pstack:missing`.", "Run `/missing`."):
            with self.subTest(body=body):
                self.assertIn("fix the link or add the referenced skill/file", "\n".join(self.check(body)))
        (self.file.parent / "details.md").write_text("details")
        self.assertEqual(self.check("Read [details](details.md#section), `/pstack:poteto-mode` and `/sample`."), [])

    def test_urls_and_templated_references_are_not_missing_files(self):
        self.assertEqual(self.check("Read [web](https://example.org/page) or [template](../<name>/SKILL.md)."), [])

    def test_reference_definitions_and_space_containing_paths(self):
        self.assertIn("missing reference absent.md", "\n".join(self.check("[details]: absent.md\n")))
        (self.file.parent / "release notes.md").write_text("notes")
        self.assertEqual(self.check("Read [notes](<release notes.md>)."), [])

    def test_explicit_pstack_names_and_native_commands(self):
        self.assertIn("missing reference /pstack:absent", "\n".join(self.check("Use pstack `absent`.")))
        self.assertEqual(self.check("Use `/clear`, `/rename`, `/compact` or `/loop` in the harness."), [])

    def test_playbook_paths_and_source_line_numbers(self):
        playbook = self.pstack / "poteto-mode/playbooks/authoring-a-skill.md"
        playbook.parent.mkdir()
        playbook.write_text("# Policy\n\n" + COPIED)
        self.assertEqual(self.check("Read `playbooks/authoring-a-skill.md`."), [])
        self.assertTrue(any(str(self.source) + ":6" in e for e in self.check(COPIED)))

    def test_new_skill_needs_real_pstack_prior_art(self):
        for body in ("No prior art.", "Prior art: pstack imaginary-skill was checked.", "Prior art: another-stack poteto-mode."):
            with self.subTest(body=body):
                self.assertIn("add 'Prior art:", "\n".join(self.check(body, new=True)))
        self.assertEqual(self.check("Prior art: pstack poteto-mode was checked for release policy.", new=True), [])

    def test_growth_requires_file_specific_pr_body_line(self):
        previous = HEADER + "word " * 50
        errors = self.check("word " * 100, previous=previous)
        self.assertIn("Skill growth: skills/sample/SKILL.md <reason>", "\n".join(errors))
        self.assertTrue(self.check("word " * 100, previous=previous, pr_body="Skill growth: skills/other/SKILL.md New protocol."))
        self.assertTrue(self.check("word " * 100, previous=previous, pr_body="Skill growth: skills/sample/SKILL.md"))
        self.assertEqual(self.check("word " * 100, previous=previous, pr_body="Skill growth: skills/sample/SKILL.md New protocol."), [])

    def test_twenty_percent_boundary_does_not_need_growth_line(self):
        previous = HEADER + "word " * (100 - len(HEADER.split()))
        self.assertEqual(self.check("word " * (120 - len(HEADER.split())), previous=previous), [])
        self.assertTrue(self.check("word " * (121 - len(HEADER.split())), previous=previous))

    def test_highest_version_across_marketplaces(self):
        for suffix in ("first/pstack/0.15.9/skills", "second/pstack/0.15.43/skills", "third/pstack/0.15.42/skills"):
            (self.root / ".claude/plugins/cache" / suffix).mkdir(parents=True)
        self.assertEqual(lint.newest_pstack(self.root).parent.name, "0.15.43")

    def test_real_past_2261_word_mistake_fails(self):
        text = (FIXTURES / "valentin-mode-old.md").read_text()
        self.assertEqual(len(text.split()), 2261)
        self.file.write_text(text)
        result = self.cli("skills/sample/SKILL.md")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("2261 words exceed budget 800", result.stdout)
        self.assertIn("skill-lint: FAIL", result.stdout)

    def test_current_snapshot_has_no_budget_finding(self):
        self.file.write_text((FIXTURES / "valentin-mode-current.md").read_text())
        errors = lint.lint(self.file, self.root, self.pstack, self.house, self.sources, [])
        self.assertFalse(any("exceed budget" in e for e in errors), errors)

    def test_diff_checks_changed_skills_only(self):
        self.check("word " * 1000)
        self.git("init", "-q")
        base = self.commit()
        (self.root / "notes.md").write_text("unrelated")
        self.commit()
        result = self.cli("--base", base)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("0 skills", result.stdout)
        self.file.write_text(HEADER + "word " * 1001)
        result = self.cli("--base", base)
        self.assertEqual(result.returncode, 1)
        self.assertIn("exceed budget", result.stdout)

    def test_new_file_in_diff_and_event_body(self):
        self.git("init", "-q")
        (self.root / "notes.md").write_text("base")
        base = self.commit()
        self.check()
        self.commit()
        result = self.cli("--base", base)
        self.assertIn("add 'Prior art:", result.stdout)
        self.check("Prior art: pstack poteto-mode was checked for release policy.")
        self.commit()
        self.assertEqual(self.cli("--base", base).returncode, 0)
        base = self.git("rev-parse", "HEAD")
        self.check("Prior art: pstack poteto-mode was checked for release policy.\n" + "word " * 100)
        self.commit()
        self.assertIn("Skill growth:", self.cli("--base", base).stdout)
        event = self.root / "event.json"
        event.write_text('{"pull_request":{"body":"Skill growth: skills/sample/SKILL.md Added release steps."}}')
        result = self.cli("--base", base, env={**os.environ, "GITHUB_EVENT_PATH": str(event)})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_push_keeps_other_gates_without_requiring_a_pr_body(self):
        self.check("word " * 50)
        self.git("init", "-q")
        base = self.commit()
        self.check("word " * 100)
        self.commit()
        event = self.root / "push.json"
        event.write_text(json.dumps({"before": base, "after": self.git("rev-parse", "HEAD")}))
        environment = {**os.environ, "GITHUB_EVENT_NAME": "push", "GITHUB_EVENT_PATH": str(event)}
        result = self.cli("--base", base, env=environment)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        environment["GITHUB_EVENT_NAME"] = "pull_request"
        self.assertIn("Skill growth:", self.cli("--base", base, env=environment).stdout)
        environment["GITHUB_EVENT_NAME"] = "push"
        self.check("word " * 1000)
        result = self.cli("--base", base, env=environment)
        self.assertEqual(result.returncode, 1)
        self.assertIn("exceed budget 800", result.stdout)
        self.check("Read [required](missing.md).")
        self.assertIn("missing reference missing.md", self.cli("--base", base, env=environment).stdout)

    def test_verifier_verdict_comes_from_its_verdict_line(self):
        # SOFT-2802: CI runs both required commands as its own steps, so the verdict no longer
        # depends on matching the reviewer's shell strings, which failed in both directions.
        workflow = lint.yaml.safe_load((SCRIPT.parent.parent / ".github/workflows/skill-lint.yml").read_text())
        steps = workflow["jobs"]["pstack-verifier"]["steps"]
        runs = "\n".join(step.get("run", "") for step in steps)
        self.assertIn("python3 -m unittest discover -s lint-source/tests -p test_skill_lint.py -v", runs)
        self.assertIn('bash "$RUNNER_TEMP/skill-lint-command"', runs)
        step = next(step for step in steps if step.get("name") == "Post current-head verdict with execution evidence")
        program = step["run"].split("\n", 1)[1].rsplit("\nPY", 1)[0]
        cases = [
            ("VERDICT: PASS", "PASS"),
            ("VERDICT: PASS+NOTES\nnotes", "PASS+NOTES"),
            ("\n  VERDICT: PASS", "PASS"),
            ("status line\nVERDICT: PASS", "FAIL"),
            ("VERDICT: FAIL", "FAIL"),
            ("no verdict here", "FAIL"),
            ("", "FAIL"),
            ("VERDICT: FAIL\n\nprior run:\nVERDICT: PASS", "FAIL"),
            ("VERDICT: PASS\n\nprevious run printed:\nVERDICT: FAIL", "PASS"),
            ("I could not finish.\n```\nVERDICT: PASS\n```", "FAIL"),
            ("VERDICT: PASSING", "FAIL"),
        ]
        for text, want in cases:
            expected = 0 if want != "FAIL" else 1
            with self.subTest(text=text):
                events = [{"type": "message_end", "message": {"role": "assistant", "content": [{"type": "text", "text": text}]}}]
                (self.root / "skill-verifier.jsonl").write_text("\n".join(map(json.dumps, events)))
                environment = {"RUNNER_TEMP": str(self.root), "HEAD": "head-sha", "PR": "604", "GITHUB_REPOSITORY": "valentinyeo/house-rules"}
                with mock.patch.dict(os.environ, environment), mock.patch("subprocess.run", return_value=subprocess.CompletedProcess([], 0)), contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaises(SystemExit) as result:
                        exec(compile(program, "workflow-verdict", "exec"), {})
                self.assertEqual(result.exception.code, expected)
                verdict = (self.root / "skill-verdict.md").read_text().splitlines()[0]
                self.assertEqual(verdict, f"pstack-verifier: {want} @ head-sha")

    def test_renamed_skill_is_not_new(self):
        self.check()
        self.git("init", "-q")
        base = self.commit()
        renamed = self.file.parent.parent / "renamed"
        self.file.parent.rename(renamed)
        self.commit()
        result = self.cli("--base", base)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
