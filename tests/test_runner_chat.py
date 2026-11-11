import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


ROOT = Path(__file__).resolve().parents[1]
CHAT = ROOT / "fleet/runner-chat"
MESSAGE = {"id": "message-one", "sessionId": "chat-one", "text": "Please answer here.", "userName": "Human"}


class RunnerChatTests(unittest.TestCase):
    def setUp(self):
        self.messages = {"agent-a": [MESSAGE.copy()], "agent-b": [{**MESSAGE, "id": "other", "sessionId": "other-chat"}]}
        self.replies = {}
        self.calls = []
        self.response = None
        self.arrive_on_second_poll = False
        fixture = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                self.serve()

            def do_POST(self):
                self.serve()

            def serve(self):
                token = self.headers.get("Authorization", "").removeprefix("Bearer ")
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"null")
                fixture.calls.append((self.command, self.path, token, body))
                code, result = 200, {"success": True}
                if fixture.response:
                    code, result = fixture.response
                elif token not in fixture.messages:
                    code, result = 401, {"success": False}
                elif self.path == "/chat/pending?unanswered=true":
                    if fixture.arrive_on_second_poll and len(fixture.calls) == 2:
                        fixture.messages[token] = [MESSAGE.copy()]
                    result["messages"] = [m for m in fixture.messages[token] if (token, m["id"]) not in fixture.replies]
                elif self.command == "POST" and any(
                    self.path == "/chat/sessions/" + m["sessionId"] + "/messages" and body.get("replyToMessageId") == m["id"]
                    for m in fixture.messages[token]
                ):
                    fixture.replies.setdefault((token, body["replyToMessageId"]), body["text"])
                else:
                    code, result = 404, {"success": False}
                self.send_response(code)
                if code == 302:
                    self.send_header("Location", fixture.base + "/credential-leak")
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.env = {**os.environ, "HT_TOKEN": "agent-a", "RUNNER_CHAT_BASE": self.base}

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def run_chat(self, *args, token="agent-a", success=True):
        result = subprocess.run([sys.executable, str(CHAT), *args], env={**self.env, "HT_TOKEN": token}, capture_output=True, text=True, timeout=10)
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0)
        if token:
            self.assertNotIn(token, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        return result

    def test_unanswered_replays_across_process_restart_until_exact_reply(self):
        first = self.run_chat("listen", "--once")
        self.assertEqual(first["messages"], [MESSAGE])
        self.assertEqual(self.run_chat("listen", "--once"), first)
        newer = {**MESSAGE, "id": "message-two", "text": "Newer message"}
        self.messages["agent-a"].append(newer)
        self.run_chat("reply", MESSAGE["sessionId"], MESSAGE["id"], "--text", "First answer")
        self.assertEqual(self.run_chat("listen", "--once")["messages"], [newer])
        self.assertEqual(self.replies, {("agent-a", MESSAGE["id"]): "First answer"})
        self.run_chat("reply", MESSAGE["sessionId"], MESSAGE["id"], "--text", "Retry answer")
        self.assertEqual(self.replies, {("agent-a", MESSAGE["id"]): "First answer"})

    def test_each_agent_reads_and_replies_only_to_its_own_chat(self):
        self.assertEqual(self.run_chat("listen", "--once")["messages"], [MESSAGE])
        self.assertEqual(self.run_chat("listen", "--once", token="agent-b")["messages"][0]["id"], "other")
        self.run_chat("reply", "chat-one", "message-one", "--text", "Wrong agent", token="agent-b", success=False)
        self.assertFalse(self.replies)
        self.run_chat("reply", "other-chat", "other", "--text", "Own answer", token="agent-b")
        self.assertEqual(self.run_chat("listen", "--once", token="agent-b")["messages"], [])
        self.assertEqual(self.run_chat("listen", "--once")["messages"], [MESSAGE])

    def test_background_consumer_completes_when_a_message_arrives(self):
        self.messages["agent-a"] = []
        self.arrive_on_second_poll = True
        result = self.run_chat("listen", "--interval", "1", "--timeout", "4")
        self.assertEqual(result["messages"], [MESSAGE])
        self.assertEqual(len(self.calls), 2)
        self.assertTrue(all(call[:2] == ("GET", "/chat/pending?unanswered=true") for call in self.calls))
        self.assertEqual(self.run_chat("listen", "--once")["messages"], [MESSAGE])

    def test_idle_timeout_completes_so_session_can_rearm(self):
        self.messages["agent-a"] = []
        self.assertEqual(self.run_chat("listen", "--timeout", "1")["messages"], [])

    def test_failed_reply_does_not_acknowledge_or_hide_the_message(self):
        self.response = 503, {"success": False, "error": "secret agent-a"}
        failed = self.run_chat("reply", "chat-one", "message-one", "--text", "Answer", success=False)
        self.assertIn("HTTP 503", failed.stderr)
        self.response = None
        self.assertEqual(self.run_chat("listen", "--once")["messages"], [MESSAGE])

    def test_auth_disabled_flag_malformed_inbox_and_redirect_fail_closed(self):
        for response in ((401, {}), (403, {}), (404, {}), (302, {}), (200, {"success": False}), (200, {"success": True, "messages": {}}), (200, {"success": True, "messages": [{}]})):
            with self.subTest(response=response):
                self.calls.clear()
                self.response = response
                self.run_chat("listen", "--once", success=False)
                self.assertEqual(len(self.calls), 1)

    def test_token_required_and_insecure_remote_refused_before_request(self):
        self.run_chat("listen", "--once", token="", success=False)
        self.env["RUNNER_CHAT_BASE"] = "http://example.com/api/mcp"
        self.run_chat("listen", "--once", success=False)
        self.assertFalse(self.calls)

    def test_json_preserves_untrusted_message_as_data(self):
        message = {**MESSAGE, "text": "$(touch /tmp/never-execute)\n'\" 雪"}
        self.messages["agent-a"] = [message]
        self.assertEqual(self.run_chat("listen", "--once")["messages"], [message])
        self.assertFalse(self.replies)

    def test_reply_posts_exact_identifiers_and_text(self):
        self.messages["agent-a"] = [{**MESSAGE, "sessionId": "chat?not/a-path"}]
        self.run_chat("reply", "chat?not/a-path", "message-one", "--text", "Answer", success=False)
        self.assertEqual(self.calls[-1][1], "/chat/sessions/chat%3Fnot%2Fa-path/messages")
        self.assertEqual(self.calls[-1][3], {"text": "Answer", "replyToMessageId": "message-one"})

    def test_actual_launcher_brief_attaches_codex_and_claude_without_changing_claim(self):
        for engine in ("codex", "claude", "opencode", "cursor", "pi-codex", "pi-opencode"):
            with self.subTest(engine=engine), tempfile.TemporaryDirectory() as state:
                pick = {"ticket": "HYCI-315", "source": "kept-slot", "lane": "infra", "brief": "Only this ticket.", "repo": str(ROOT), "title": "Pool chat", "engine": engine, "model": "named-model", "effort": "medium"}
                result = subprocess.run(["bash", str(ROOT / "fleet/runner"), "brief-check", "3"], input=json.dumps(pick), env={**os.environ, "FLEET_RUNNER_STATE": state}, text=True, capture_output=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f"python3 {CHAT} listen as a background shell task", result.stdout)
                self.assertIn("bash tool with background=true", result.stdout)
                self.assertIn("Bash run_in_background=true", result.stdout)
                self.assertIn("After every completion or error, rearm", result.stdout)
                self.assertIn("listen --once and answer pending messages", result.stdout)
                self.assertIn("reply <sessionId> <id>", result.stdout)
                self.assertIn("tmux attach -t ht-or-runner-3 (Cursor Grok RUNNER 3)", result.stdout)
                self.assertIn("existing Claude board-event hooks remain unchanged", result.stdout)
                self.assertIn("Only this ticket.", result.stdout)


if __name__ == "__main__":
    unittest.main()
