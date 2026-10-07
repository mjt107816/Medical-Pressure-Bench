#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from benchmark_core.shared.io import config_from_dict, load_env_file, write_json
from benchmark_core.orchestrator.episode_runner import EpisodeRunner
from benchmark_core.runtime import load_api_file, load_api_settings


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one config directory with bounded parallelism")
    parser.add_argument("--config-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--api-config", default="api.config.yaml")
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--max-workers", type=int, default=5)
    args = parser.parse_args()
    output = Path(args.output_dir)
    if output.exists() and any(output.iterdir()):
        raise SystemExit(f"refusing to overwrite non-empty output: {output}")
    output.mkdir(parents=True, exist_ok=True)
    load_env_file(args.env_file)
    api = load_api_settings(load_api_file(args.api_config))
    issues = api.validate()
    if issues:
        raise SystemExit("API configuration errors: " + "; ".join(issues))
    rows = []
    for path in sorted(Path(args.config_dir).glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, dict) and (
            isinstance(raw.get("pressure"), dict)
            or bool(raw.get("pressure_ref"))
            or bool(raw.get("pressure_profile_ref"))
        ):
            rows.append(raw)
    workers = max(1, min(args.max_workers, len(rows)))
    print(f"episodes={len(rows)}; max_workers={workers}; output={output}", flush=True)
    summaries = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(run_one, raw, output, api): raw["episode_id"] for raw in rows}
        for future in as_completed(futures):
            episode_id = futures[future]
            try:
                row = future.result()
                print(f"completed {episode_id}", flush=True)
            except Exception as exc:
                row = {"episode_id": episode_id, "status": "error", "error_type": type(exc).__name__, "error": str(exc)}
                write_json(output / episode_id / "error.json", row)
                print(f"ERROR {episode_id}: {type(exc).__name__}: {exc}", flush=True)
            summaries.append(row)
    summaries.sort(key=lambda row: str(row.get("episode_id", "")))
    write_json(output / "summary.json", summaries)
    write_json(output / "api_config.public.json", api.public_dict())
    failures = [row for row in summaries if row.get("status") != "completed"]
    print(f"finished={len(summaries) - len(failures)}; failures={len(failures)}", flush=True)
    if failures:
        raise SystemExit(1)


def run_one(raw: dict, output: Path, api) -> dict:
    config = config_from_dict(raw)
    run_dir = output / config.episode_id
    result = EpisodeRunner().run(config, api=api)
    write_json(run_dir / "config.json", raw)
    write_json(run_dir / "events.json", result.events)
    write_json(run_dir / "final_state.json", result.final_state)
    write_json(run_dir / "judge_input.json", result.evaluation)
    return {
        "episode_id": config.episode_id,
        "pressure_type": config.pressure.pressure_type,
        "pressure_level": config.pressure.pressure_level,
        "trial_id": config.trial_id,
        "status": "completed",
    }


if __name__ == "__main__":
    main()
