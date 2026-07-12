#!/usr/bin/env python3
"""AgentFacts helpers for NANDA registry registration."""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from typing import Any, Mapping, Optional, Union
from urllib.parse import urlparse


class AgentFactsError(ValueError):
    """Raised when AgentFacts metadata cannot be used for registration."""


def _validate_data_facts_url(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AgentFactsError("data_facts_url must be a non-empty string")

    normalized = value.strip()
    parsed = urlparse(normalized)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return normalized
    if parsed.scheme == "df" and (parsed.netloc or parsed.path):
        return normalized

    raise AgentFactsError(
        "data_facts_url must be an http(s) URL or a df:// DataFacts URL"
    )


def normalize_agent_facts(agent_facts: Optional[Mapping[str, Any]]) -> Optional[dict]:
    """Return a JSON-safe AgentFacts copy with NANDini fields validated.

    The adapter intentionally validates only the bridge fields it owns. Full
    AgentFacts schema validation belongs in the registry/catalog service.
    """

    if agent_facts is None:
        return None
    if not isinstance(agent_facts, Mapping):
        raise AgentFactsError("agent_facts must be a JSON object")

    normalized = copy.deepcopy(dict(agent_facts))
    if "data_facts_url" in normalized:
        normalized["data_facts_url"] = _validate_data_facts_url(
            normalized["data_facts_url"]
        )

    try:
        json.dumps(normalized)
    except TypeError as exc:
        raise AgentFactsError("agent_facts must be JSON serializable") from exc

    return normalized


def load_agent_facts(path: Union[str, os.PathLike]) -> dict:
    """Load AgentFacts JSON from disk and validate adapter-owned fields."""

    facts_path = Path(path)
    with facts_path.open("r", encoding="utf-8") as handle:
        loaded = json.load(handle)
    return normalize_agent_facts(loaded) or {}


def load_agent_facts_from_env() -> Optional[dict]:
    """Load AgentFacts from AGENT_FACTS_PATH when the variable is set."""

    path = os.getenv("AGENT_FACTS_PATH")
    if not path:
        return None
    return load_agent_facts(path)


def build_registration_payload(
    agent_id: str,
    agent_url: str,
    api_url: Optional[str],
    agent_facts: Optional[Mapping[str, Any]] = None,
) -> dict:
    """Build the registry payload, including AgentFacts when provided."""

    payload = {
        "agent_id": agent_id,
        "agent_url": agent_url,
        "api_url": api_url,
    }
    normalized = normalize_agent_facts(agent_facts)
    if normalized is not None:
        payload["agent_facts"] = normalized
    return payload
