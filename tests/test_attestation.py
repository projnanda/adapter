"""Unit tests for the optional Attestix attestation layer.

Auto-skips when the optional `attestix` dependency is not installed. Exercises
attest_registration / verify_registration directly (no network, no HTTP); the
security-critical paths are: a valid proof verifies, tampering on id/url/signature
is rejected, an unknown suite is rejected, and the unconfigured (no-key) path stays
backward-compatible.
"""
import base64
import os

import pytest

pytest.importorskip("attestix")  # skip the whole module if the optional dep is absent

from nanda_adapter.core import attestation

AGENT_ID = "pay-bot"
AGENT_URL = "https://pay.example/a2a"


@pytest.fixture
def agent_key(monkeypatch):
    """Set ATTESTIX_AGENT_KEY to a fresh 32-byte seed (same shape the registry path uses)."""
    seed = base64.urlsafe_b64encode(os.urandom(32)).decode()
    monkeypatch.setenv("ATTESTIX_AGENT_KEY", seed)
    return seed


def test_attest_then_verify_roundtrip(agent_key):
    proof = attestation.attest_registration(AGENT_ID, AGENT_URL)
    assert proof is not None
    assert proof["suite"] == attestation.SUITE
    assert proof["signature"]
    assert attestation.verify_registration(AGENT_ID, AGENT_URL, proof) is True


def test_tampered_url_rejected(agent_key):
    proof = attestation.attest_registration(AGENT_ID, AGENT_URL)
    # proof was signed for AGENT_URL; verifying against a swapped URL must fail
    assert attestation.verify_registration(AGENT_ID, "https://attacker.example/a2a", proof) is False


def test_tampered_agent_id_rejected(agent_key):
    proof = attestation.attest_registration(AGENT_ID, AGENT_URL)
    assert attestation.verify_registration("other-bot", AGENT_URL, proof) is False


def test_garbled_signature_rejected(agent_key):
    proof = attestation.attest_registration(AGENT_ID, AGENT_URL)
    bad = {**proof, "signature": proof["signature"][:-4] + "AAAA"}
    assert attestation.verify_registration(AGENT_ID, AGENT_URL, bad) is False


def test_unknown_suite_rejected(agent_key):
    proof = attestation.attest_registration(AGENT_ID, AGENT_URL)
    assert attestation.verify_registration(AGENT_ID, AGENT_URL, {**proof, "suite": "nope-1"}) is False


def test_no_key_returns_none_and_backward_compat(monkeypatch):
    monkeypatch.delenv("ATTESTIX_AGENT_KEY", raising=False)
    # ensure non-strict (fail-open) default for this case
    monkeypatch.delenv("ATTESTIX_STRICT", raising=False)
    monkeypatch.setattr(attestation, "STRICT", False)
    assert attestation.attest_registration(AGENT_ID, AGENT_URL) is None
    # an unsigned peer (proof=None) is accepted when not strict -> existing network keeps working
    assert attestation.verify_registration(AGENT_ID, AGENT_URL, None) is True


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
