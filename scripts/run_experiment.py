#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from benchmark_core.shared.io import config_from_dict, load_env_file, write_json
from benchmark_core.orchestrator.episode_runner import EpisodeRunner
from benchmark_core.runtime import load_api_file, load_api_settings


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--matrix")
    p.add_argument("--config-dir", help="Run all individual JSON configs in a directory")
    p.add_argument("--output-dir", default="runs/phase1")
    p.add_argument("--api-config", default="api.config.yaml")
    p.add_argument("--env-file", default=".env")
    p.add_argument("--demo", action="store_true")
    p.add_argument("--limit", type=int)
    p.add_argument("--start", type=int, default=0)
    p.add_argument("--pressure-levels", nargs="+", help="Only run selected pressure levels, e.g. L0 L3 L5")
    p.add_argument("--pressure-types", nargs="+", help="Only run selected pressure types")
    p.add_argument("--scenario-prefixes", nargs="+", help="Only run scenario IDs with one of these prefixes")
    p.add_argument("--episode-ids", nargs="+", help="Only run the explicitly listed episode IDs")
    p.add_argument("--resume", action="store_true", help="Skip episodes that already have judge_input.json")
    args = p.parse_args()
    if not args.matrix and not args.config_dir:
        p.error("provide --matrix or --config-dir")
    load_env_file(args.env_file)
    if args.config_dir:
        rows = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(Path(args.config_dir).glob("*.json"))]
        # A config directory may also contain a manifest.json or other metadata.
        # v3 conditions may inherit pressure through a reference/profile rather
        # than repeat an inline pressure block, so keep all three valid forms.
        rows = [
            row for row in rows
            if isinstance(row, dict)
            and (
                isinstance(row.get("pressure"), dict)
                or bool(row.get("pressure_ref"))
                or bool(row.get("pressure_profile_ref"))
            )
        ]
    else:
        rows = json.loads(Path(args.matrix).read_text(encoding="utf-8"))
    if args.pressure_levels:
        levels = set(args.pressure_levels)
        rows = [row for row in rows if str(row.get("pressure", {}).get("pressure_level")) in levels]
    if args.pressure_types:
        types = set(args.pressure_types)
        rows = [row for row in rows if str(row.get("pressure", {}).get("pressure_type")) in types]
    if args.scenario_prefixes:
        prefixes = tuple(args.scenario_prefixes)
        rows = [row for row in rows if str(row.get("scenario", {}).get("scenario_id", "")).startswith(prefixes)]
    if args.episode_ids:
        episode_ids = set(args.episode_ids)
        rows = [row for row in rows if str(row.get("episode_id", "")) in episode_ids]
    rows = rows[args.start:]
    if args.limit:
        rows = rows[:args.limit]
    api = None
    if not args.demo:
        api = load_api_settings(load_api_file(args.api_config))
        issues = api.validate()
        if issues:
            raise SystemExit("API configuration errors: " + "; ".join(issues))
    runner = EpisodeRunner()
    summary = []
    for raw in rows:
        config = config_from_dict(raw)
        run_dir = Path(args.output_dir) / config.episode_id
        input_path = run_dir / "judge_input.json"
        legacy_input_path = run_dir / "evaluation.json"
        if args.resume and (input_path.exists() or legacy_input_path.exists()):
            evaluation = json.loads((input_path if input_path.exists() else legacy_input_path).read_text(encoding="utf-8"))
            summary.append({"episode_id": config.episode_id, "pressure_type": config.pressure.pressure_type, "pressure_level": config.pressure.pressure_level, "trial_id": config.trial_id, **evaluation})
            print(f"skipped existing {config.episode_id}", flush=True)
            continue
        try:
            result = runner.run(config, api=api, demo=args.demo)
            write_json(run_dir / "config.json", raw)
            write_json(run_dir / "events.json", result.events)
            write_json(run_dir / "final_state.json", result.final_state)
            write_json(run_dir / "judge_input.json", result.evaluation)
            error_path = run_dir / "error.json"
            if error_path.exists():
                error_path.unlink()
            summary.append({"episode_id": config.episode_id, "pressure_type": config.pressure.pressure_type, "pressure_level": config.pressure.pressure_level, "trial_id": config.trial_id, "status": "completed", **result.evaluation})
            print(f"completed {config.episode_id}", flush=True)
        except Exception as exc:
            write_json(run_dir / "config.json", raw)
            write_json(run_dir / "error.json", {"status": "error", "error_type": type(exc).__name__, "error": str(exc)})
            summary.append({"episode_id": config.episode_id, "pressure_type": config.pressure.pressure_type, "pressure_level": config.pressure.pressure_level, "trial_id": config.trial_id, "status": "error", "error_type": type(exc).__name__, "error": str(exc)})
            print(f"ERROR {config.episode_id}: {type(exc).__name__}: {exc}", flush=True)
    write_json(Path(args.output_dir) / "summary.json", summary)
    if api is not None:
        write_json(Path(args.output_dir) / "api_config.public.json", api.public_dict())
    print(f"completed {len(summary)} episodes")


if __name__ == "__main__":
    main()
