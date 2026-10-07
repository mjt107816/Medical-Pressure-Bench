from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

PRESSURE_LEVELS = tuple(f"L{i}" for i in range(6))
DOSE_PRESSURE_LEVELS = tuple(f"P{i}" for i in range(20))
EXTENDED_PRESSURE_LEVELS = tuple(f"P{i}" for i in range(25))
PRESSURE_TYPES = ("operational", "social", "time", "authority", "regulatory", "peer", "memory", "performance")


@dataclass(frozen=True)
class PressureCondition:
    pressure_type: str
    pressure_level: str
    injection_step: int = 1
    episode_steps: int = 5
    # Optional exact wording for preregistered separability experiments.
    # When present, the runner uses this text instead of the generic ladder.
    pressure_context_override: str = ""
    # Optional one-shot pressure messages keyed by step, used for order experiments.
    pressure_events: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    family: str
    condition: str  # risky or benign
    task_instruction: str
    safe_path: tuple[str, ...]
    high_impact_tools: tuple[str, ...]
    step_prompts: tuple[str, ...] = ()
    available_skills: tuple[str, ...] = ()
    sensitive_values: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EpisodeConfig:
    experiment_name: str
    episode_id: str
    trial_id: int
    seed: int
    scenario: Scenario
    pressure: PressureCondition
    model: str = "api-agent"


@dataclass
class Decision:
    action_summary: str = ""
    tool_name: str | None = None
    tool_args: dict[str, Any] = field(default_factory=dict)
    skill_name: str | None = None
    skill_args: dict[str, Any] = field(default_factory=dict)
    message: str = ""
    raw_output: str = ""
    parse_repaired: bool = False
    api_telemetry: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ToolResult:
    ok: bool
    output: dict[str, Any] = field(default_factory=dict)
    side_effects: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass
class EpisodeResult:
    config: EpisodeConfig
    events: list[dict[str, Any]]
    final_state: dict[str, Any]
    evaluation: dict[str, Any]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
