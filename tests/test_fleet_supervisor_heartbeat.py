import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("supervisor_heartbeat", ROOT / "fleet" / "supervisor-heartbeat.py")
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class SupervisorHeartbeat(unittest.TestCase):
    def test_target_url_adds_id(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"url": "https://example.test/hb"}, f)
            path = f.name
        try:
            with mock.patch.object(mod, "CONFIG", path):
                url = mod.target_url("drill")
        finally:
            os.unlink(path)
        self.assertIn("id=drill", url)
        self.assertTrue(url.startswith("https://example.test/hb"))

    def test_self_check_drill(self):
        with mock.patch.dict(os.environ, {"FLEET_SUPERVISOR_DRILL": "1"}):
            ok, _ = mod.self_check()
        self.assertTrue(ok)

    def test_post_dry(self):
        with mock.patch.object(mod, "bearer", return_value="tok"):
            with mock.patch.object(mod, "target_url", return_value="https://example.test/hb?id=production"):
                ok, msg = mod.post("production", dry=True)
        self.assertTrue(ok)
        self.assertIn("would POST", msg)


if __name__ == "__main__":
    unittest.main()
