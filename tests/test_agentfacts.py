#!/usr/bin/env python3

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "nanda_adapter" / "core"))

from agentfacts import (  # noqa: E402
    AgentFactsError,
    build_registration_payload,
    load_agent_facts,
    normalize_agent_facts,
)


def test_registration_payload_omits_agent_facts_by_default():
    payload = build_registration_payload("agent-1", "https://agent.test/a2a", None)

    assert payload == {
        "agent_id": "agent-1",
        "agent_url": "https://agent.test/a2a",
        "api_url": None,
    }


def test_registration_payload_includes_nandini_data_facts_url():
    facts = {
        "id": "agent-1",
        "agent_name": "urn:agent:test:agent-1",
        "label": "Weather Agent",
        "data_facts_url": "https://agent.test/.well-known/data-facts.json",
    }

    payload = build_registration_payload(
        "agent-1",
        "https://agent.test/a2a",
        "https://agent.test/api",
        facts,
    )

    assert payload["agent_facts"]["data_facts_url"] == (
        "https://agent.test/.well-known/data-facts.json"
    )
    assert payload["agent_facts"]["label"] == "Weather Agent"


def test_registration_payload_accepts_nandatown_datafacts_urls():
    facts = {"data_facts_url": "df://sha256-abc123"}

    payload = build_registration_payload("agent-1", "https://agent.test/a2a", None, facts)

    assert payload["agent_facts"]["data_facts_url"] == "df://sha256-abc123"


def test_agent_facts_rejects_bad_data_facts_url():
    with pytest.raises(AgentFactsError, match="data_facts_url"):
        normalize_agent_facts({"data_facts_url": "not-a-url"})


def test_agent_facts_must_be_json_serializable():
    with pytest.raises(AgentFactsError, match="JSON serializable"):
        normalize_agent_facts({"data_facts_url": "df://dataset", "bad": object()})


def test_load_agent_facts_from_json_file(tmp_path):
    facts_path = tmp_path / "agentfacts.json"
    facts_path.write_text(
        json.dumps({"id": "agent-1", "data_facts_url": "df://dataset"}),
        encoding="utf-8",
    )

    loaded = load_agent_facts(facts_path)

    assert loaded == {"id": "agent-1", "data_facts_url": "df://dataset"}
