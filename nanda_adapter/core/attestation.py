# attestation.py
"""Optional Attestix-backed attestation for NANDA agent registration.

NANDA's registry binds an agent_id to a URL with no proof: any caller can POST
any agent_id -> any URL, and lookups trust whatever the registry returns. This
module lets an agent sign that binding (agent_id -> agent_url) with an Ed25519
key, and lets peers verify it before trusting a looked-up URL.

It is entirely opt-in:
  * No ATTESTIX_AGENT_KEY set  -> attest_registration() returns None; behaviour
    is byte-for-byte identical to today (unsigned registration).
  * Key set but `attestix` not installed -> degrades to unsigned, with a notice.

Enable: pip install nanda-adapter[attestix]
Generate a key seed:
    python -c "import os,base64; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"
    export ATTESTIX_AGENT_KEY=<that value>
"""
import base64
import os

SUITE = "ed25519-jcs-2026"

# ponytail: fail-open verification (missing proof -> accepted) so a signed agent
# can still talk to the existing unsigned network. Set ATTESTIX_STRICT=1 to reject
# any agent that presents no valid proof, once your peers all sign.
STRICT = os.getenv("ATTESTIX_STRICT", "").lower() in ("1", "true", "yes")


def _binding(agent_id, agent_url):
    return {"agent_id": agent_id, "agent_url": agent_url}


def _signing_key():
    """Ed25519 private key from ATTESTIX_AGENT_KEY (base64url 32-byte seed), or None."""
    raw = os.environ.get("ATTESTIX_AGENT_KEY")
    if not raw:
        return None
    from attestix.auth.crypto import private_key_from_bytes
    return private_key_from_bytes(base64.urlsafe_b64decode(raw))


def attest_registration(agent_id, agent_url):
    """Return a proof dict binding agent_id -> agent_url, or None if unconfigured."""
    try:
        key = _signing_key()
        if key is None:
            return None
        from attestix.auth.crypto import public_key_to_did_key, sign_json_payload
        return {
            "suite": SUITE,
            "issuer": public_key_to_did_key(key.public_key()),
            "signature": sign_json_payload(key, _binding(agent_id, agent_url)),
        }
    except Exception as e:  # missing lib / bad key -> stay unsigned, never crash registration
        print(f"Attestix: skipping registration proof ({e})")
        return None


def verify_registration(agent_id, agent_url, proof):
    """True if a peer's (agent_id -> agent_url) binding is trustworthy.

    No proof -> accepted unless ATTESTIX_STRICT (see STRICT above). A present
    proof must be cryptographically valid AND bind exactly this agent_id+url.
    """
    if not proof:
        return not STRICT
    if proof.get("suite") != SUITE:
        return False  # unknown suite -> can't verify it -> don't trust it
    try:
        from attestix.auth.crypto import did_key_to_public_key, verify_json_signature
        pub = did_key_to_public_key(proof["issuer"])
        return verify_json_signature(pub, _binding(agent_id, agent_url), proof["signature"])
    except Exception as e:
        print(f"Attestix: proof verification error ({e})")
        return False


if __name__ == "__main__":
    # Runnable self-check of the security path (no attestix import needed if installed).
    seed = base64.urlsafe_b64encode(bytes(range(32))).decode()
    os.environ["ATTESTIX_AGENT_KEY"] = seed
    p = attest_registration("agent-1", "https://a.example/a2a")
    assert p and p["suite"] == SUITE, "should produce a proof when key is set"
    assert verify_registration("agent-1", "https://a.example/a2a", p), "valid proof must verify"
    assert not verify_registration("agent-1", "https://evil.example/a2a", p), "swapped URL must fail"
    assert not verify_registration("agent-2", "https://a.example/a2a", p), "swapped id must fail"
    assert not verify_registration("agent-1", "https://a.example/a2a", {**p, "suite": "other"}), "unknown suite must fail"
    assert verify_registration("x", "y", None) is True, "no proof accepted in default (non-strict)"
    print("attestation self-check OK")
