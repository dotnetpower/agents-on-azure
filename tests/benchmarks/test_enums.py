"""Tests for benchmarks.enums module."""

import pytest
from benchmarks.enums import Framework, Messaging, Scenario, Topology


class TestFramework:
    """Tests for the Framework enum."""

    def test_all_members_exist(self) -> None:
        assert len(Framework) == 4

    @pytest.mark.parametrize(
        ("member", "value"),
        [
            (Framework.MICROSOFT_AGENT_FRAMEWORK, "microsoft-agent-framework"),
            (Framework.LANGGRAPH, "langgraph"),
            (Framework.SEMANTIC_KERNEL, "semantic-kernel"),
            (Framework.AUTOGEN, "autogen"),
        ],
    )
    def test_values(self, member: Framework, value: str) -> None:
        assert member.value == value

    def test_str_enum_behavior(self) -> None:
        """Framework inherits from str, so it can be used as a string."""
        assert isinstance(Framework.LANGGRAPH, str)
        assert Framework.LANGGRAPH == "langgraph"

    def test_from_value(self) -> None:
        assert Framework("langgraph") is Framework.LANGGRAPH

    def test_invalid_value_raises(self) -> None:
        with pytest.raises(ValueError):
            Framework("unknown-framework")


class TestMessaging:
    """Tests for the Messaging enum."""

    def test_all_members_exist(self) -> None:
        assert len(Messaging) == 4

    def test_none_variant(self) -> None:
        assert Messaging.NONE.value == "none"

    @pytest.mark.parametrize(
        ("member", "value"),
        [
            (Messaging.SERVICE_BUS, "servicebus"),
            (Messaging.EVENT_HUBS, "eventhubs"),
            (Messaging.EVENT_GRID, "eventgrid"),
        ],
    )
    def test_azure_services(self, member: Messaging, value: str) -> None:
        assert member.value == value


class TestTopology:
    """Tests for the Topology enum."""

    def test_all_members_exist(self) -> None:
        assert len(Topology) == 4

    @pytest.mark.parametrize(
        ("member", "value"),
        [
            (Topology.LINEAR, "linear"),
            (Topology.FAN_OUT, "fan-out"),
            (Topology.FAN_IN, "fan-in"),
            (Topology.CHOREOGRAPHY, "choreography"),
        ],
    )
    def test_values(self, member: Topology, value: str) -> None:
        assert member.value == value


class TestScenario:
    """Tests for the Scenario enum."""

    def test_all_members_exist(self) -> None:
        assert len(Scenario) == 7

    def test_single_agent_scenario(self) -> None:
        assert Scenario.SINGLE_AGENT.value == "single-agent"

    def test_resiliency_scenario(self) -> None:
        assert Scenario.RESILIENCY.value == "resiliency"
