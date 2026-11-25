"""factory-state names a board-15 worker by its parent chat first, and roster-check agrees with itself on workers_by."""
import importlib.machinery
import importlib.util
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
FLEET = ROOT / "fleet"


def load(name, path):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    module = importlib.util.module_from_spec(importlib.util.spec_from_loader(name, loader))
    sys.modules[name] = module
    loader.exec_module(module)
    return module


state = load("factory_state", FLEET / "factory-state")
wake = load("solo_wake", FLEET / "solo-wake")
check = load("roster_check", FLEET / "roster-check")

NOW = datetime(2026, 11, 25, 12, tzinfo=timezone.utc)
LANES = [dict(name="HT Bugs", multibot="HT Bugs", kind="lead", board="15", workers=10,
              workers_by="Valentin 2026-11-25", repo="owner/lane", cwd="/fixture/shared"),
         dict(name="HT Features", multibot="HT Features", kind="lead", board="15", workers=10,
              workers_by="Valentin 2026-11-25", repo="owner/lane", cwd="/fixture/shared")]


class ParentChatNamesTheWorker(unittest.TestCase):
    def test_worker_under_a_chat_is_attributed_though_four_rows_share_the_cwd(self):
        tree = {7: state.Process(1, "node agent-host", "/fixture/shared", False),
                60: state.Process(7, "claude -p task", "/fixture/shared", True)}
        assigned, unattributed = state.attribute_workers(tree, LANES, {}, "/fixture",
                                                         owner_by_pid={7: {"HT Bugs"}})
        self.assertEqual(assigned["HT Bugs"], {60})
        self.assertEqual(unattributed, set())

    def test_shared_cwd_alone_names_no_lane(self):
        tree = {60: state.Process(1, "claude -p task", "/fixture/shared", True)}
        assigned, unattributed = state.attribute_workers(tree, LANES, {}, "/fixture")
        self.assertEqual(unattributed, {60})
        self.assertEqual([name for name, pids in assigned.items() if pids], [])

    def test_one_row_at_the_cwd_still_attributes(self):
        tree = {60: state.Process(1, "claude -p task", "/fixture/shared", True)}
        assigned, unattributed = state.attribute_workers(tree, LANES[:1], {}, "/fixture")
        self.assertEqual(assigned["HT Bugs"], {60})
        self.assertEqual(unattributed, set())

    def test_ticket_reference_and_parent_chat_each_name_their_own_worker(self):
        tickets = {"HT Bugs": {"15": [dict(id=1, uniqueIndex=2, ticketNumber="SOFT-2")]}}
        tree = {7: state.Process(1, "node agent-host", "/fixture/shared", False),
                60: state.Process(1, "hax https://app.hypertask.ai/detail/project-15/2", "/fixture/shared", True),
                61: state.Process(7, "claude -p task", "/fixture/shared", True)}
        assigned, unattributed = state.attribute_workers(tree, LANES, tickets, "/fixture",
                                                         owner_by_pid={7: {"HT Features"}})
        self.assertEqual(assigned["HT Bugs"], {60})
        self.assertEqual(assigned["HT Features"], {61})
        self.assertEqual(unattributed, set())

    def test_chat_owner_comes_from_a_multibot_host_pid(self):
        chats = {"live-v": dict(tmux="live-v", name="HT Verification", sid="native-v", pid=42)}
        rows = LANES + [dict(name="HT Verification", multibot="HT Verification")]
        self.assertEqual(state.chat_owners(rows, chats, {("sid", "native-v"): [dict(pid=42)]}),
                         {42: {"HT Verification"}})

    def test_a_pid_two_rows_claim_names_nobody(self):
        chats = {"live-v": dict(tmux="live-v", name="HT Bugs", sid="native-v")}
        records = {("sid", "native-v"): [dict(pid=42, sessionId="native-v")]}
        self.assertEqual(state.chat_owners([dict(name="HT Bugs"), dict(name="HT Features", tmux="live-v")],
                                           chats, records), {})


class CallerRow(unittest.TestCase):
    def tree(self, directory, chat_pid, caller_parent):
        proc = Path(directory) / "proc"
        proc.mkdir()
        for pid, ppid, command in ((1, 0, "init"), (chat_pid, 1, "node agent-host"),
                                   (55, caller_parent, "pi --mode rpc")):
            path = proc / str(pid)
            path.mkdir()
            (path / "stat").write_text(f"{pid} (name) S {ppid} 0 0")
            (path / "cmdline").write_bytes(command.replace(" ", "\0").encode())
            (path / "cwd").symlink_to("/fixture/shared")
        return proc

    def gather(self, directory, chat_pid, caller_parent, identity):
        home = Path(directory)
        roster = home / "roster.json"
        roster.write_text(json.dumps({"rows": LANES}))
        chats = {"live-bugs": dict(tmux="live-bugs", name="HT Bugs", sid="native-bugs", pid=chat_pid)}
        with mock.patch.object(wake.roster, "hosted_chats", return_value=chats), \
                mock.patch.object(wake, "tmux_states", return_value={}), \
                mock.patch.object(state.os, "getpid", return_value=55):
            return state.gather(wake, NOW, roster, home, self.tree(directory, chat_pid, caller_parent),
                                tasks=lambda board: [], views=lambda view: set(),
                                prs=lambda repo: dict(open=0, red=0, pending=0, green=0, waiting=0),
                                all_rows=False, identity=identity, statuses=lambda board: "Normal")

    def test_default_run_picks_the_callers_row_by_its_chat_pid(self):
        with tempfile.TemporaryDirectory() as directory:
            rows = self.gather(directory, 7, 7, ("/fixture/shared", "owner/lane"))
        self.assertEqual([row.name for row in rows], ["HT Bugs"])

    def test_default_run_lists_every_row_sharing_the_cwd_when_the_chat_is_not_the_caller(self):
        with tempfile.TemporaryDirectory() as directory:
            rows = self.gather(directory, 8, 1, ("/fixture/shared", "owner/lane"))
            rendered = state.render(rows, NOW)
        self.assertEqual([row.name for row in rows], ["HT Bugs", "HT Features"])
        self.assertNotIn("Factory", rendered)

    def test_caller_identity_picks_one_of_the_rows_sharing_the_cwd(self):
        keys = ("live-features", "HT Features")
        self.assertEqual(state.select_rows(LANES, "/fixture/shared", "owner/lane", keys=keys)[0],
                         [LANES[1]])
        self.assertEqual(state.select_rows(LANES, "/fixture/shared", "owner/lane")[0], LANES)

    def test_unknown_caller_still_fails(self):
        with self.assertRaises(ValueError):
            state.select_rows(LANES, "/fixture/elsewhere", "owner/unrelated")


class WorkersByPrefix(unittest.TestCase):
    def test_check_and_its_self_test_agree_on_the_space(self):
        for bad in ("Valentine 2026-11-25", "Valentin", "valentin 2026-11-25"):
            self.assertTrue(check.worker_errors([dict(name="A", workers=10, workers_by=bad)]), bad)
        self.assertEqual(check.worker_errors([dict(name="A", workers=10)]),
                         ["roster.json row A: workers requires workers_by starting Valentin "])
        self.assertEqual(check.worker_errors([dict(name="A", workers=10, workers_by="Valentin 2026-11-25")]), [])

    def test_real_roster_passes_the_same_rule_as_the_self_test(self):
        rows = [row for row in check.roster.static_rows() if "workers" in row]
        self.assertEqual(check.worker_errors(rows), [])
        self.assertTrue(all(row["workers_by"].startswith("Valentin ") for row in rows))


if __name__ == "__main__":
    unittest.main()
