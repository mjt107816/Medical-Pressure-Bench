from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .types import EpisodeConfig, PressureCondition, Scenario


def scenario_from_dict(raw: dict[str, Any]) -> Scenario:
    return Scenario(
        scenario_id=str(raw["scenario_id"]), family=str(raw["family"]), condition=str(raw["condition"]),
        task_instruction=str(raw["task_instruction"]), safe_path=tuple(raw.get("safe_path", [])),
        high_impact_tools=tuple(raw.get("high_impact_tools", [])), sensitive_values=tuple(raw.get("sensitive_values", [])),
        step_prompts=tuple(raw.get("step_prompts", [])), available_skills=tuple(raw.get("available_skills", [])),
        metadata=dict(raw.get("metadata", {})),
    )


def config_from_dict(raw: dict[str, Any]) -> EpisodeConfig:
    if raw.get("scenario_ref"):
        workspace = Path(__file__).resolve().parents[2].resolve()
        config_root = (workspace / "configs" / "tasks").resolve()
        ref = str(raw["scenario_ref"])
        # Allow either a repository-relative path or a path within configs/tasks.
        scenario_base = workspace if ref.startswith("configs/tasks/") else config_root
        scenario_path = (scenario_base / ref).resolve()
        if config_root not in scenario_path.parents or not scenario_path.is_file():
            raise ValueError("scenario_ref must be an existing file within configs/tasks")
        referenced = json.loads(scenario_path.read_text(encoding="utf-8"))
        # A reference may be either a standalone Scenario object or an
        # existing full episode configuration.  The latter keeps one readable
        # baseline configuration as the canonical shared scenario and avoids
        # copying it into every pressure condition.
        scenario = referenced.get("scenario", referenced) if isinstance(referenced, dict) else referenced
        if not isinstance(scenario, dict) or "scenario_id" not in scenario:
            raise ValueError("scenario_ref must resolve to a Scenario or episode configuration with scenario")
        overrides = raw.get("scenario_overrides", {})
        if overrides:
            if not isinstance(overrides, dict):
                raise ValueError("scenario_overrides must be an object")
            metadata_overrides = overrides.get("metadata", {})
            if metadata_overrides and not isinstance(metadata_overrides, dict):
                raise ValueError("scenario_overrides.metadata must be an object")
            scenario = {
                **scenario,
                **{key: value for key, value in overrides.items() if key != "metadata"},
                "metadata": {**scenario.get("metadata", {}), **metadata_overrides},
            }
        if isinstance(raw.get("tools_allowed"), list):
            scenario["metadata"] = {**scenario.get("metadata", {}), "tools_allowed": list(raw["tools_allowed"])}
        raw = {**raw, "scenario": scenario}
    p = raw.get("pressure")
    scenario_metadata = raw.get("scenario", {}).get("metadata", {}) if isinstance(raw.get("scenario"), dict) else {}
    inherited_profile = scenario_metadata.get("pressure_profile_ref") if isinstance(scenario_metadata, dict) else None
    profile_ref = raw.get("pressure_profile_ref") or inherited_profile
    profile_label = str(raw.get("pressure_condition", ""))
    if profile_ref and not profile_label and raw.get("pressure_ref"):
        legacy_path = (Path(__file__).resolve().parents[2] / "configs" / "tasks" / str(raw["pressure_ref"])).resolve()
        if legacy_path.is_file():
            profile_label = str(json.loads(legacy_path.read_text(encoding="utf-8")).get("pressure", {}).get("pressure_type", ""))
    if profile_ref:
        workspace = Path(__file__).resolve().parents[2].resolve()
        v3_root = (workspace / "configs" / "tasks").resolve()
        profile_base = workspace if str(profile_ref).startswith("configs/tasks/") else v3_root
        profile_path = (profile_base / str(profile_ref)).resolve()
        if v3_root not in profile_path.parents or not profile_path.is_file():
            raise ValueError("pressure_profile_ref must be an existing profile within configs/tasks")
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        label = profile_label
        slots = [str(item) for item in profile.get("slot_order", [])]
        neutral = profile.get("neutral", {})
        active = profile.get("active", {})
        if not slots or set(slots) != set(neutral) or set(slots) != set(active):
            raise ValueError("pressure profile must define matching slot_order, neutral, and active entries")
        lengths = {len(str(text).split()) for group in (neutral, active) for text in group.values()}
        if len(lengths) != 1:
            raise ValueError("all pressure-profile modules must have equal word counts")
        def render(active_slots: set[str]) -> str:
            return " ".join(str(active[slot] if slot in active_slots else neutral[slot]) for slot in slots)
        if label == "baseline":
            p = {"pressure_type": label, "pressure_level": "", "injection_step": 1, "episode_steps": int(profile.get("episode_steps", 10)), "pressure_context_override": render(set())}
        elif ">" in label:
            first, second = label.split(">", 1)
            if first not in slots or second not in slots:
                raise ValueError("ordered pressure profile condition uses an unknown slot")
            split = int(profile.get("order_split_step", 6))
            steps = int(profile.get("episode_steps", 10))
            p = {"pressure_type": label, "pressure_level": "", "injection_step": 1, "episode_steps": steps, "pressure_context_override": render({first}), "pressure_events": [{"step": step, "message": render({first if step < split else second})} for step in range(1, steps + 1)]}
        else:
            active_slots = set(label.split("+"))
            if not active_slots or not active_slots.issubset(set(slots)):
                raise ValueError("pressure profile condition uses an unknown slot")
            p = {"pressure_type": label, "pressure_level": "", "injection_step": 1, "episode_steps": int(profile.get("episode_steps", 10)), "pressure_context_override": render(active_slots)}
        if raw.get("pressure") or (raw.get("pressure_ref") and not inherited_profile):
            raise ValueError("pressure_profile_ref cannot be combined with pressure_ref or inline pressure")
    if raw.get("pressure_ref") and not inherited_profile and not raw.get("pressure_profile_ref"):
        workspace = Path(__file__).resolve().parents[2].resolve()
        pressure_root = (workspace / "configs" / "tasks").resolve()
        pressure_path = (pressure_root / str(raw["pressure_ref"])).resolve()
        if pressure_root not in pressure_path.parents or not pressure_path.is_file():
            raise ValueError("pressure_ref must be an existing configuration within configs/tasks")
        referenced_pressure = json.loads(pressure_path.read_text(encoding="utf-8")).get("pressure")
        if not isinstance(referenced_pressure, dict):
            raise ValueError("pressure_ref must resolve to an episode configuration with pressure")
        if p:
            raise ValueError("pressure_ref cannot be combined with an inline pressure object")
        p = dict(referenced_pressure)
    if not isinstance(p, dict):
        raise ValueError("each episode configuration must provide pressure or pressure_ref")
    # A baseline is deliberately pressure-free.  Older v3 profiles encode it
    # with an empty level and rely on a neutral override; normalize that
    # representation so it remains valid even when no override text is given.
    if str(p.get("pressure_type", "")).strip().lower() == "baseline" and not str(p.get("pressure_level", "")).strip():
        p = {**p, "pressure_level": "L0"}
    if p.get("template"):
        if p.get("pressure_events") or p.get("pressure_context_override"):
            raise ValueError("A shared pressure template cannot also specify events or override text")
        root = Path(__file__).resolve().parents[2] / "configs" / "tasks"
        template_paths = {
            "action_type_pressure_v3": root / "action_type_pressure_v3.json",
            "handoff_pathway_pressure_v1": root / "handoff_pathway_pressure_v1.json",
            "qualify_extreme_pressure_v2": root / "qualify_extreme_pressure_v2.json",
        }
        template_path = template_paths.get(str(p["template"]))
        if template_path is None:
            raise ValueError("Unknown pressure template")
        template = json.loads(template_path.read_text(encoding="utf-8"))
        kind = p["pressure_type"]
        if p["template"] in {"action_type_pressure_v3", "handoff_pathway_pressure_v1"}:
            if kind not in ["baseline", *template["slot_order"]]:
                raise ValueError("This template supports only baseline and single pressures")
            lengths = {len(text.split()) for section in ("neutral", "active") for text in template[section].values()}
            if len(lengths) != 1:
                raise ValueError("Pressure template slots must have equal word counts")
            context = " ".join(template["active" if slot == kind else "neutral"][slot] for slot in template["slot_order"])
            p = {**p, "episode_steps": int(p.get("episode_steps", template.get("episode_steps", 5)))}
        else:
            if kind not in ["baseline", *template["active"]]:
                raise ValueError("This template supports only baseline and single pressures")
            chunks = template["baseline"] if kind == "baseline" else template["active"][kind]
            if not isinstance(chunks, list) or not all(isinstance(chunk, str) for chunk in chunks):
                raise ValueError("Extreme pressure template must contain text chunks")
            context = " ".join(chunks)
            all_conditions = [template["baseline"], *template["active"].values()]
            if any(not isinstance(condition, list) or len(" ".join(condition).split()) != len(context.split()) for condition in all_conditions):
                raise ValueError("Extreme pressure template conditions must have equal word counts")
        p = {**p, "injection_step": 1, "pressure_events": [], "pressure_context_override": context}
    return EpisodeConfig(
        experiment_name=str(raw["experiment_name"]), episode_id=str(raw["episode_id"]), trial_id=int(raw["trial_id"]), seed=int(raw["seed"]),
        scenario=scenario_from_dict(raw["scenario"]), pressure=PressureCondition(
            str(p["pressure_type"]),
            str(p.get("pressure_level", "")),
            int(p.get("injection_step", 1)),
            int(p.get("episode_steps", 5)),
            str(p.get("pressure_context_override", "")),
            pressure_events=tuple(dict(item) for item in p.get("pressure_events", []) if isinstance(item, dict)),
        ), model=str(raw.get("model", "api-agent")),
    )


def config_to_dict(config: EpisodeConfig) -> dict[str, Any]:
    return asdict(config)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def load_env_file(path: str) -> None:
    src = Path(path)
    if not src.exists():
        return
    for line in src.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        import os
        os.environ.setdefault(key.strip(), value.strip().strip('"\''))
