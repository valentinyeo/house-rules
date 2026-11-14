import datetime as dt
import fcntl
import json
import os
import re
from pathlib import Path


class Owners:
    def __init__(self, state, roster):
        self.directory = Path(state) / "ticket-owners"
        self.roster = Path(roster)

    def exists(self, runner):
        return 1 <= int(runner) <= int(json.loads(self.roster.read_text())["runners"])

    def read(self, key):
        path = self.directory / key
        try:
            record = json.loads(path.read_text())
        except FileNotFoundError:
            return None
        if record.get("ticket") != key or not isinstance(record.get("runner"), int):
            raise ValueError(f"invalid ticket owner: {key}")
        return record if self.exists(record["runner"]) else None

    def bind(self, key, runner, selection=None):
        if not re.fullmatch(r"(?:HTPR|HYFA|IGSH|SOFT|HYCI)-\d+", key):
            raise ValueError("invalid ticket key")
        self.directory.mkdir(parents=True, exist_ok=True)
        with (self.directory / ".lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            record = self.read(key)
            if record and record["runner"] != int(runner):
                raise RuntimeError(f"{key} belongs to Runner {record['runner']} until Done")
            # "since" orders a runner's tickets when it owns two (HYCI-431 second-ticket lane): the first-bound one wins every pick
            record = record or {"ticket": key, "runner": int(runner),
                                "since": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
            if selection and not record.get("model"):
                record.update({k: selection[k] for k in ("engine", "model", "effort")})
            path = self.directory / key
            tmp = path.with_name(f".{key}.{os.getpid()}")
            tmp.write_text(json.dumps(record) + "\n")
            os.replace(tmp, path)
            return record

    def release(self, key):
        """Drop the owner record: the ticket is free for any runner again. True when a record existed (2026-11-13: TOO HARD hands
        the ticket to a stronger runner, so the first runner's pin must go)."""
        self.directory.mkdir(parents=True, exist_ok=True)
        with (self.directory / ".lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                (self.directory / key).unlink()
            except FileNotFoundError:
                return False
            return True

    def prepare(self, tickets, write=True):
        for ticket in tickets:
            record = self.read(ticket["key"])
            if record is None:
                runners = [int(m[1]) for name, _ in ticket["holders"]
                           if (m := re.fullmatch(r"runner (\d+)", name)) and self.exists(int(m[1]))]
                if runners:
                    record = self.bind(ticket["key"], runners[0]) if write else {
                        "ticket": ticket["key"], "runner": runners[0]}
            ticket["_owner"] = record


def store():
    home = Path.home()
    return Owners(os.environ.get("FLEET_PICK_STATE", home / ".local/state/fleet-pick"),
                  Path(__file__).resolve().with_name("roster.json"))
