#!/usr/bin/env python3
"""
Example Unit Tests for NANDA Agent Bridge
Demonstrates testing patterns without external dependencies.
"""

import pytest
from datetime import datetime, timezone


@pytest.mark.unit
class TestAgentRegistration:
    """Test agent registration functionality"""

    def test_register_agent_success(self, mock_registry, sample_agent_metadata):
        """Test successful agent registration"""
        agent_id = "test-agent-001"

        result = mock_registry.register_agent(agent_id, sample_agent_metadata)

        assert result["status"] == "registered"
        assert result["agent_id"] == agent_id

        # Verify agent is retrievable
        agent = mock_registry.lookup_agent(agent_id)
        assert agent is not None
        assert agent["display_name"] == sample_agent_metadata["display_name"]

    def test_lookup_nonexistent_agent(self, mock_registry):
        """Test looking up agent that doesn't exist"""
        result = mock_registry.lookup_agent("nonexistent-agent")
        assert result is None

    def test_register_multiple_agents(self, mock_registry):
        """Test registering multiple agents"""
        agents = [
            ("agent-1", {"display_name": "Agent 1"}),
            ("agent-2", {"display_name": "Agent 2"}),
            ("agent-3", {"display_name": "Agent 3"})
        ]

        for agent_id, metadata in agents:
            result = mock_registry.register_agent(agent_id, metadata)
            assert result["status"] == "registered"

        # Verify all agents are registered
        for agent_id, metadata in agents:
            agent = mock_registry.lookup_agent(agent_id)
            assert agent is not None
            assert agent["display_name"] == metadata["display_name"]


@pytest.mark.unit
class TestAgentDelegation:
    """Test delegation system"""

    def test_grant_delegation_success(self, mock_registry, sample_delegation):
        """Test granting delegation to agent"""
        result = mock_registry.grant_delegation(sample_delegation)

        assert result["status"] == "granted"
        assert "delegation_id" in result

    def test_verify_delegation_with_permission(self, mock_registry, sample_delegation):
        """Test delegation verification for authorized action"""
        mock_registry.grant_delegation(sample_delegation)

        agent_id = sample_delegation["delegate"]["agent_id"]
        has_permission = mock_registry.verify_delegation(agent_id, "read")

        assert has_permission is True

    def test_verify_delegation_without_permission(self, mock_registry, sample_delegation):
        """Test delegation verification for unauthorized action"""
        mock_registry.grant_delegation(sample_delegation)

        agent_id = sample_delegation["delegate"]["agent_id"]
        has_permission = mock_registry.verify_delegation(agent_id, "delete")

        assert has_permission is False


@pytest.mark.unit
class TestAgentMessaging:
    """Test agent-to-agent messaging"""

    def test_send_message_success(self, mock_adapter):
        """Test sending message to agent"""
        to_agent = "agent-receiver"
        message = {"type": "request", "data": {"key": "value"}}

        result = mock_adapter.send_message(to_agent, message)

        assert result["status"] == "sent"
        assert "message_id" in result

        # Verify message was recorded
        messages = mock_adapter.get_messages(to_agent)
        assert len(messages) == 1
        assert messages[0]["to_agent"] == to_agent
        assert messages[0]["message"] == message

    def test_configure_mock_response(self, mock_adapter):
        """Test configuring mock responses"""
        agent_id = "test-agent"
        expected_response = {"status": "success", "result": {"processed": True}}

        mock_adapter.configure_response(agent_id, expected_response)
        result = mock_adapter.send_message(agent_id, {"test": "message"})

        assert result == expected_response

    def test_multiple_messages_to_same_agent(self, mock_adapter):
        """Test sending multiple messages"""
        to_agent = "agent-receiver"
        messages = [
            {"type": "request", "seq": 1},
            {"type": "request", "seq": 2},
            {"type": "request", "seq": 3}
        ]

        for msg in messages:
            mock_adapter.send_message(to_agent, msg)

        sent_messages = mock_adapter.get_messages(to_agent)
        assert len(sent_messages) == 3
        assert all(m["to_agent"] == to_agent for m in sent_messages)


@pytest.mark.integration
class TestAgentTestHarness:
    """Test the complete agent test harness"""

    def test_setup_agent_with_delegation(self, agent_test_harness):
        """Test setting up agent with delegations"""
        agent_id = "test-agent-001"
        actions = ["read", "write", "execute"]

        result = agent_test_harness.setup_agent_with_delegation(agent_id, actions)

        assert result["agent_id"] == agent_id
        assert "delegation" in result

        # Verify agent is registered
        agent = agent_test_harness.registry.lookup_agent(agent_id)
        assert agent is not None

        # Verify delegations are granted
        for action in actions:
            has_permission = agent_test_harness.registry.verify_delegation(agent_id, action)
            assert has_permission is True

    def test_simulate_agent_communication(self, agent_test_harness):
        """Test simulating agent-to-agent communication"""
        from_agent = "agent-sender"
        to_agent = "agent-receiver"
        message = {"type": "task", "task_id": "task-001"}

        result = agent_test_harness.simulate_agent_message(from_agent, to_agent, message)

        assert result["status"] == "sent"

        # Verify message was sent
        messages = agent_test_harness.adapter.get_messages(to_agent)
        assert len(messages) == 1
        assert messages[0]["message"]["from"] == from_agent

    def test_harness_reset(self, agent_test_harness):
        """Test resetting test harness"""
        # Setup some data
        agent_test_harness.register_test_agent("agent-1", display_name="Agent 1")
        agent_test_harness.adapter.send_message("agent-2", {"test": "message"})

        # Verify data exists
        assert agent_test_harness.registry.lookup_agent("agent-1") is not None
        assert len(agent_test_harness.adapter.get_messages()) > 0

        # Reset
        agent_test_harness.reset()

        # Verify data is cleared
        assert agent_test_harness.registry.lookup_agent("agent-1") is None
        assert len(agent_test_harness.adapter.get_messages()) == 0


@pytest.mark.integration
class TestEndToEndWorkflow:
    """Test complete agent workflow scenarios"""

    def test_agent_registration_and_communication_flow(self, agent_test_harness):
        """Test full workflow: register agents, grant permissions, communicate"""
        # Step 1: Register two agents
        sender_id = "agent-sender"
        receiver_id = "agent-receiver"

        agent_test_harness.register_test_agent(sender_id, display_name="Sender Agent")
        agent_test_harness.register_test_agent(receiver_id, display_name="Receiver Agent")

        # Step 2: Grant delegations
        agent_test_harness.setup_agent_with_delegation(sender_id, ["send_message"])
        agent_test_harness.setup_agent_with_delegation(receiver_id, ["receive_message"])

        # Step 3: Verify permissions
        assert agent_test_harness.registry.verify_delegation(sender_id, "send_message") is True
        assert agent_test_harness.registry.verify_delegation(receiver_id, "receive_message") is True

        # Step 4: Send message
        message = {"type": "greeting", "content": "Hello from sender"}
        result = agent_test_harness.simulate_agent_message(sender_id, receiver_id, message)

        assert result["status"] == "sent"

        # Step 5: Verify message delivery
        messages = agent_test_harness.adapter.get_messages(receiver_id)
        assert len(messages) == 1
        assert messages[0]["message"]["content"] == "Hello from sender"

    def test_agent_workflow_with_response(self, agent_test_harness):
        """Test workflow with configured response"""
        sender_id = "agent-sender"
        receiver_id = "agent-receiver"

        # Setup agents
        agent_test_harness.setup_agent_with_delegation(sender_id, ["request"])
        agent_test_harness.setup_agent_with_delegation(receiver_id, ["respond"])

        # Configure mock response from receiver
        expected_response = {
            "status": "success",
            "result": {"processed": True, "data": "response data"}
        }
        agent_test_harness.adapter.configure_response(receiver_id, expected_response)

        # Send message and get response
        message = {"type": "request", "data": {"query": "test"}}
        response = agent_test_harness.adapter.send_message(receiver_id, message)

        assert response == expected_response
        assert response["result"]["processed"] is True


@pytest.mark.slow
class TestLargeScaleScenarios:
    """Test scenarios with many agents (marked as slow)"""

    def test_many_agents_registration(self, agent_test_harness):
        """Test registering many agents"""
        num_agents = 100

        for i in range(num_agents):
            agent_id = f"agent-{i:04d}"
            agent_test_harness.register_test_agent(
                agent_id,
                display_name=f"Agent {i}",
                index=i
            )

        # Verify all agents are registered
        for i in range(num_agents):
            agent_id = f"agent-{i:04d}"
            agent = agent_test_harness.registry.lookup_agent(agent_id)
            assert agent is not None
            assert agent["index"] == i

    def test_many_messages(self, agent_test_harness):
        """Test sending many messages"""
        receiver_id = "agent-receiver"
        num_messages = 1000

        for i in range(num_messages):
            message = {"seq": i, "data": f"message-{i}"}
            agent_test_harness.adapter.send_message(receiver_id, message)

        messages = agent_test_harness.adapter.get_messages(receiver_id)
        assert len(messages) == num_messages
