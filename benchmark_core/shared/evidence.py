"""Package task specifications and raw trajectory evidence without scoring."""
from __future__ import annotations

from typing import Any

from .types import EpisodeConfig
from .process_layer import compute_process_variables


def build_judge_input(config: EpisodeConfig, events: list[dict[str, Any]], final_state: dict[str, Any]) -> dict[str, Any]:
    del final_state  # Final state is already represented by the trajectory snapshots.
    metadata = config.scenario.metadata if isinstance(config.scenario.metadata, dict) else {}
    return {
        "task": config.scenario.task_instruction,
        "task_goal": metadata.get("task_goal", ""),
        "pressure": config.pressure.to_dict(),
        "pressure_context": _pressure_context(events),
        "case_context": {
            "condition": config.scenario.condition,
            "safe_path": list(config.scenario.safe_path),
            "high_impact_tools": list(config.scenario.high_impact_tools),
            "approval_available": metadata.get("approval_available", "unknown"),
        },
        "process_variables": compute_process_variables(config, events),
        "events": _trajectory_evidence(events),
    }


def _trajectory_evidence(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for event in events:
        before = event.get("state_before", {}) if isinstance(event.get("state_before", {}), dict) else {}
        result = event.get("tool_result", {}) if isinstance(event.get("tool_result", {}), dict) else {}
        output = result.get("output", {}) if isinstance(result.get("output", {}), dict) else {}
        rows.append({
            "step": event.get("step"),
            "action": str(event.get("action", ""))[:1000],
            "tool_name": event.get("tool_name"),
            "tool_args": event.get("tool_args", {}),
            "skill_name": event.get("skill_name"),
            "tool_ok": result.get("ok"),
            "tool_error": result.get("error"),
            "authorization_before": {
                "identity_verified": bool(before.get("identity_verified")),
                "approval_requested": bool(before.get("approval_requested")),
                "approved": bool(before.get("approved")),
            },
            "tool_outcome": {key: output.get(key) for key in ("status", "safety_outcome", "identity") if key in output},
            "message": str(event.get("message", ""))[:1000],
            "time_pressure_state": event.get("observation", {}).get("time_pressure_state", {}) if isinstance(event.get("observation", {}), dict) else {},
        })
    return rows


def _pressure_context(events: list[dict[str, Any]]) -> str:
    for event in events:
        text = str(event.get("pressure", "")).strip()
        if text:
            return text[:2000]
    return ""
