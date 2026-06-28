import pytest

from backend.robot_libraries.registry import (
    TELECOM_TRACE_LIBRARY,
    get_robot_keyword_capability,
    list_robot_keyword_capabilities,
)
from backend.tools import tool_registry


def test_robot_keyword_registry_lists_approved_telecom_keywords() -> None:
    capabilities = list_robot_keyword_capabilities(domain="telecom_trace")

    names = {capability.name for capability in capabilities}
    assert names == {
        "Load Sanitized Trace",
        "Verify SIP Header Present",
        "Verify Trace Event Present",
        "Verify Trace Route",
        "Verify Minimum Event Count",
        "Verify Diameter Session Match",
        "Verify Diameter Result Code",
        "Verify Flexible Sequence",
    }
    assert {capability.library for capability in capabilities} == {
        TELECOM_TRACE_LIBRARY
    }
    assert {capability.runtime for capability in capabilities} == {
        "robot_framework"
    }
    assert {capability.risk_level for capability in capabilities} == {"low"}


def test_robot_keyword_registry_rejects_unknown_domain() -> None:
    assert list_robot_keyword_capabilities(domain="network_live") == []


def test_robot_keyword_registry_rejects_unknown_keyword() -> None:
    with pytest.raises(KeyError, match="not approved"):
        get_robot_keyword_capability("Open Live Network Session")


def test_robot_keyword_capability_tool_returns_metadata() -> None:
    assert tool_registry.has("RobotKeywordCapabilityTool") is True

    tool = tool_registry.create("RobotKeywordCapabilityTool")
    capabilities = tool.invoke(domain="telecom_trace")

    assert capabilities[0]["domain"] == "telecom_trace"
    assert capabilities[0]["runtime"] == "robot_framework"
    assert "library" in capabilities[0]
