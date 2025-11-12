#!/usr/bin/env python3
"""
Generic Test Fixtures for NANDA Agent Testing
Extracted from production patterns, generalized for agent-to-agent testing.
"""

import pytest
from contextlib import contextmanager
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from uuid import uuid4


@pytest.fixture
def mock_registry():
    """
    Mock registry service for testing without external dependencies.
    Provides in-memory agent registration and lookup.
    """
    class MockRegistry:
        def __init__(self):
            self.agents: Dict[str, Dict[str, Any]] = {}
            self.delegations: Dict[str, Dict[str, Any]] = {}

        def register_agent(self, agent_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
            """Register an agent with metadata"""
            self.agents[agent_id] = {
                "agent_id": agent_id,
                "registered_at": datetime.now(timezone.utc).isoformat(),
                **metadata
            }
            return {"status": "registered", "agent_id": agent_id}

        def lookup_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
            """Lookup agent by ID"""
            return self.agents.get(agent_id)

        def grant_delegation(self, delegation: Dict[str, Any]) -> Dict[str, Any]:
            """Grant delegation to agent"""
            delegation_id = delegation.get("delegation_id", f"del:{uuid4().hex[:8]}")
            self.delegations[delegation_id] = delegation
            return {"status": "granted", "delegation_id": delegation_id}

        def verify_delegation(self, agent_id: str, action: str) -> bool:
            """Check if agent has delegation for action"""
            for delegation in self.delegations.values():
                if delegation.get("delegate", {}).get("agent_id") == agent_id:
                    scopes = delegation.get("scope", [])
                    if any(s.get("action") == action for s in scopes):
                        return True
            return False

        def reset(self):
            """Clear all data"""
            self.agents.clear()
            self.delegations.clear()

    registry = MockRegistry()
    return registry


@pytest.fixture
def mock_adapter():
    """
    Mock adapter service for testing agent-to-agent communication.
    Simulates message passing without external services.
    """
    class MockAdapter:
        def __init__(self):
            self.messages: List[Dict[str, Any]] = []
            self.responses: Dict[str, Any] = {}

        def send_message(self, to_agent: str, message: Dict[str, Any]) -> Dict[str, Any]:
            """Send message to agent"""
            message_id = f"msg:{uuid4().hex[:8]}"
            self.messages.append({
                "message_id": message_id,
                "to_agent": to_agent,
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            # Return pre-configured response if available
            return self.responses.get(to_agent, {"status": "sent", "message_id": message_id})

        def configure_response(self, agent_id: str, response: Dict[str, Any]):
            """Configure mock response for specific agent"""
            self.responses[agent_id] = response

        def get_messages(self, to_agent: Optional[str] = None) -> List[Dict[str, Any]]:
            """Retrieve sent messages"""
            if to_agent:
                return [m for m in self.messages if m["to_agent"] == to_agent]
            return self.messages

        def reset(self):
            """Clear all messages"""
            self.messages.clear()
            self.responses.clear()

    adapter = MockAdapter()
    return adapter


@pytest.fixture
def sample_agent_metadata():
    """Sample agent metadata for testing"""
    return {
        "display_name": "Test Agent",
        "capabilities": ["data_processing", "analysis"],
        "labels": ["test", "example"],
        "metadata": {
            "version": "1.0.0",
            "environment": "test"
        }
    }


@pytest.fixture
def sample_delegation():
    """Sample delegation for testing"""
    return {
        "delegation_id": f"del:test:{uuid4().hex[:8]}",
        "delegator": {"did": "did:test:delegator"},
        "delegate": {"agent_id": "test-agent-1"},
        "issued_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": None,
        "scope": [
            {"action": "read", "resource": "*"},
            {"action": "execute", "resource": "workflow:*"}
        ],
        "constraints": {
            "environment": ["test", "development"]
        }
    }


@contextmanager
def stub_external_services(registry=None, adapter=None):
    """
    Context manager to stub external services during tests.
    Pattern extracted from production harness, generalized.

    Usage:
        with stub_external_services(registry=mock_registry, adapter=mock_adapter):
            # Test code that calls external services
            result = my_function()
    """
    # This would patch actual service clients
    # For now, it's a placeholder for the pattern
    original_services = {}

    try:
        # Stub services here
        if registry:
            # Would patch: import nanda.registry as _registry
            # _registry.client = registry
            pass
        if adapter:
            # Would patch: import nanda.adapter as _adapter
            # _adapter.client = adapter
            pass

        yield {
            "registry": registry,
            "adapter": adapter
        }
    finally:
        # Restore original services
        pass


@pytest.fixture
def agent_test_harness(mock_registry, mock_adapter):
    """
    Complete test harness combining registry and adapter mocks.
    Provides full agent testing environment.
    """
    class AgentTestHarness:
        def __init__(self, registry, adapter):
            self.registry = registry
            self.adapter = adapter

        def register_test_agent(self, agent_id: str, **metadata) -> Dict[str, Any]:
            """Helper to register test agent"""
            return self.registry.register_agent(agent_id, metadata)

        def setup_agent_with_delegation(self, agent_id: str, actions: List[str]) -> Dict[str, Any]:
            """Helper to setup agent with specific delegations"""
            self.registry.register_agent(agent_id, {
                "display_name": f"Agent {agent_id}",
                "capabilities": actions
            })

            delegation = {
                "delegation_id": f"del:{agent_id}:{uuid4().hex[:8]}",
                "delegate": {"agent_id": agent_id},
                "scope": [{"action": action, "resource": "*"} for action in actions]
            }
            self.registry.grant_delegation(delegation)

            return {
                "agent_id": agent_id,
                "delegation": delegation
            }

        def simulate_agent_message(self, from_agent: str, to_agent: str, message: Dict[str, Any]) -> Dict[str, Any]:
            """Helper to simulate agent-to-agent communication"""
            return self.adapter.send_message(to_agent, {
                "from": from_agent,
                **message
            })

        def reset(self):
            """Reset all mock services"""
            self.registry.reset()
            self.adapter.reset()

    harness = AgentTestHarness(mock_registry, mock_adapter)
    return harness


# Pytest configuration
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow-running tests")
