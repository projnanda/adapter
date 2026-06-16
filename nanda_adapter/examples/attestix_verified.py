#!/usr/bin/env python3
"""Attestix-verified NANDA agent.

NANDA's registry maps an agent_id to a URL with no proof of who owns it. This
example shows how to make that binding verifiable: the agent signs its
(agent_id -> agent_url) with an Ed25519 key, peers verify the signature before
trusting a looked-up URL, and a spoofed entry is rejected.

The attestation is opt-in and lives in nanda_adapter.core.attestation. Enable it
by setting ATTESTIX_AGENT_KEY before starting any NANDA agent - no code change to
your improvement logic is required.

Run this file directly for an offline sign/verify demo (no API key, no registry):
    pip install nanda-adapter[attestix]
    python attestix_verified.py
"""
import base64
import os

# attestation is the new sibling module in nanda_adapter/core
from nanda_adapter.core import attestation


def generate_agent_key() -> str:
    """Return a fresh base64url Ed25519 seed for ATTESTIX_AGENT_KEY."""
    return base64.urlsafe_b64encode(os.urandom(32)).decode()


def offline_demo():
    """Prove the security property without a server or registry."""
    # In production you persist this once and export it; here we make one on the fly.
    os.environ["ATTESTIX_AGENT_KEY"] = generate_agent_key()

    agent_id, agent_url = "pirate-agent-7", "https://pirate.example.com/a2a"

    proof = attestation.attest_registration(agent_id, agent_url)
    print(f"Signed registration proof:\n  issuer: {proof['issuer']}\n  suite:  {proof['suite']}\n")

    # A peer who looks this agent up verifies the proof before trusting the URL.
    print("honest lookup           ->", attestation.verify_registration(agent_id, agent_url, proof))
    print("spoofed URL (attacker)  ->", attestation.verify_registration(agent_id, "https://evil.example/a2a", proof))
    print("spoofed agent_id        ->", attestation.verify_registration("admin-agent", agent_url, proof))


def run_verified_agent():
    """Start a real NANDA agent whose registration is Attestix-signed.

    Identical to any other example - the only difference is ATTESTIX_AGENT_KEY in
    the environment, which makes register_with_registry() attach a proof and
    lookup_agent() verify peers' proofs automatically.
    """
    from nanda_adapter import NANDA

    if not os.getenv("ATTESTIX_AGENT_KEY"):
        os.environ["ATTESTIX_AGENT_KEY"] = generate_agent_key()
        print("No ATTESTIX_AGENT_KEY set - generated an ephemeral one for this run.")

    def echo_logic(message_text: str) -> str:
        return message_text

    nanda = NANDA(echo_logic)
    print("Starting Attestix-verified NANDA agent (registration will be signed)...")

    domain = os.getenv("DOMAIN_NAME", "localhost")
    if domain != "localhost":
        nanda.start_server_api(os.getenv("ANTHROPIC_API_KEY"), domain)
    else:
        nanda.start_server()


def main():
    if os.getenv("RUN_AGENT"):
        run_verified_agent()
    else:
        offline_demo()


if __name__ == "__main__":
    main()
