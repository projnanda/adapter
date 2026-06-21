"""Verify the registration payload includes agent_facts when supplied."""
import os
import sys
import unittest
from unittest import mock

# Ensure the package is importable when running this file directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nanda_adapter.core import agent_bridge


class _FakeResponse:
    def __init__(self, status_code=200, text="ok"):
        self.status_code = status_code
        self.text = text


class RegisterPayloadTest(unittest.TestCase):

    def test_payload_omits_agent_facts_by_default(self):
        captured = {}

        def fake_post(url, json=None, **kwargs):
            captured["url"] = url
            captured["json"] = json
            return _FakeResponse()

        with mock.patch.object(agent_bridge.requests, "post", side_effect=fake_post):
            ok = agent_bridge.register_with_registry(
                "agent-x", "https://x.example.com", "https://api.example.com"
            )

        self.assertTrue(ok)
        self.assertNotIn("agent_facts", captured["json"])
        self.assertEqual(captured["json"]["agent_id"], "agent-x")

    def test_payload_includes_agent_facts_when_provided(self):
        captured = {}

        def fake_post(url, json=None, **kwargs):
            captured["json"] = json
            return _FakeResponse()

        facts = {
            "agent_name": "pirate-bot",
            "skills": [{"id": "translate.pirate"}],
        }

        with mock.patch.object(agent_bridge.requests, "post", side_effect=fake_post):
            agent_bridge.register_with_registry(
                "agent-x",
                "https://x.example.com",
                "https://api.example.com",
                agent_facts=facts,
            )

        self.assertEqual(captured["json"]["agent_facts"], facts)


if __name__ == "__main__":
    unittest.main()
