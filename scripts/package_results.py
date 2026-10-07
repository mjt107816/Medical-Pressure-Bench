#!/usr/bin/env python3
"""Index model runs and prepare one GitHub Release ZIP per model."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


MODELS = ("gpt", "claude", "gemini", "qwen", "deepseek")
OUTPUT_FILES = ("events.json", "final_state.json", "judge_input.json")
LOCAL_PATH = re.compile(r"/(?:Users|home|Volumes)/[^\s\"'<>]+")
URL = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)
IPV4 = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")
IPV4_BYTES = re.compile(rb"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")
PRIVATE_KEYS = {
    "api_base", "api_endpoint", "api_key", "base_url", "gateway_url",
    "access_token", "refresh_token", "authorization_header", "password",
}
PRIVATE_MARKERS = (
    b"/Users/", b"/home/", b"/Volumes/", b"http:" + b"//", b"https:" + b"//",
    *(f'"{key}"'.encode() for key in PRIVATE_KEYS),
)


def public_json(path: Path) -> bytes:
    """Remove connection details and local paths from published run JSON."""
    data = path.read_bytes()
    if path.name == "api_config.public.json":
        config = json.loads(data)
        for key in (*PRIVATE_KEYS, "token", "secret"):
            config.pop(key, None)
        return (json.dumps(config, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    # /workspace/ is part of the simulated task state and must stay intact.
    if not any(marker in data for marker in PRIVATE_MARKERS) and not IPV4_BYTES.search(data):
        return data

    def redact(value):
        if isinstance(value, str):
            value = LOCAL_PATH.sub("<REDACTED_LOCAL_PATH>", value)
            value = URL.sub("<REDACTED_URL>", value)
            return IPV4.sub("<REDACTED_IP>", value)
        if isinstance(value, list):
            return [redact(item) for item in value]
        if isinstance(value, dict):
            return {key: redact(item) for key, item in value.items() if key not in PRIVATE_KEYS}
        return value

    return (json.dumps(redact(json.loads(data)), ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def verify_public_archive(archive: Path) -> None:
    """Fail before publishing an index for an archive with known private data."""
    with ZipFile(archive) as zip_file:
        for name in zip_file.namelist():
            if not name.endswith(".json"):
                continue
            if name.endswith("api_config.public.json"):
                raise ValueError(f"API connection metadata file remains in {archive.name}: {name}")
            data = zip_file.read(name)
            if any(marker in data for marker in PRIVATE_MARKERS) or IPV4_BYTES.search(data):
                raise ValueError(f"connection detail or local path remains in {archive.name}: {name}")
            if name.endswith("api_config.public.json"):
                config = json.loads(data)
                if any(key in config for key in (*PRIVATE_KEYS, "token", "secret")):
                    raise ValueError(f"connection metadata remains in {archive.name}: {name}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True,
                        help="Directory containing the five source model folders")
    parser.add_argument("--output-root", type=Path, default=Path(__file__).resolve().parents[1],
                        help="Destination repository root")
    parser.add_argument("--index-only", action="store_true",
                        help="Reuse existing ZIPs and regenerate the manifest and checksums")
    args = parser.parse_args()
    source_root = args.source_root.resolve()
    output_root = args.output_root.resolve()
    assets = output_root / "release_assets"
    results = output_root / "results"
    summary = results / "summary"
    assets.mkdir(parents=True, exist_ok=True)
    summary.mkdir(parents=True, exist_ok=True)

    configs_root = output_root / "configs" / "tasks"
    if not configs_root.is_dir():
        raise SystemExit("missing experiment configuration directory")
    configs = {}
    for path in sorted(configs_root.glob("task_*/*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, dict) and raw.get("episode_id"):
            configs[str(raw["episode_id"])] = {
                "path": path.relative_to(output_root).as_posix(),
                "condition": raw.get("pressure", {}).get("pressure_type", ""),
                "trial_id": raw.get("trial_id", ""),
            }

    rows = []
    inventory = {}
    checksums = []
    for model in MODELS:
        model_root = source_root / model
        if not model_root.is_dir():
            raise SystemExit(f"missing model directory: {model_root}")
        files = sorted(
            path for path in model_root.rglob("*.json")
            if path.is_file() and path.name != "api_config.public.json"
        )
        asset_name = f"raw_runs_{model}.zip"
        archive = assets / asset_name
        if not args.index_only:
            temporary_archive = archive.with_suffix(".zip.tmp")
            with ZipFile(temporary_archive, "w", compression=ZIP_DEFLATED, compresslevel=6, allowZip64=True) as zip_file:
                for path in files:
                    archive_name = f"{model}/{path.relative_to(model_root).as_posix()}"
                    zip_file.writestr(archive_name, public_json(path))
            temporary_archive.replace(archive)
        elif not archive.is_file():
            raise SystemExit(f"missing existing archive: {archive}")
        verify_public_archive(archive)
        if archive.stat().st_size >= 2 * 1024 ** 3:
            raise SystemExit(f"Release asset exceeds 2 GiB: {archive}")
        digest = sha256(archive)
        checksums.append(f"{digest}  {asset_name}")

        status_counts = Counter()
        episode_dirs = sorted({path.parent for path in files if path.name in OUTPUT_FILES or path.name == "error.json"})
        for episode_dir in episode_dirs:
            relative = episode_dir.relative_to(model_root)
            if len(relative.parts) != 2:
                continue
            task, directory_name = relative.parts
            present = sorted(path.name for path in episode_dir.glob("*.json"))
            if "error.json" in present:
                status = "error"
            elif all(name in present for name in OUTPUT_FILES):
                status = "complete"
            else:
                status = "partial"
            status_counts[status] += 1
            raw_config = None
            if (episode_dir / "config.json").is_file():
                try:
                    raw_config = json.loads((episode_dir / "config.json").read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    pass
            run_metadata = None
            if (episode_dir / "run_metadata.json").is_file():
                try:
                    run_metadata = json.loads((episode_dir / "run_metadata.json").read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    pass
            episode_id = (raw_config.get("episode_id") if isinstance(raw_config, dict) else None) or (
                run_metadata.get("episode_id") if isinstance(run_metadata, dict) else None) or directory_name
            source_config = configs.get(episode_id, {})
            pressure = raw_config.get("pressure", {}) if isinstance(raw_config, dict) else {}
            rows.append({
                "model_group": model,
                "task": task,
                "episode_id": episode_id,
                "condition": pressure.get("pressure_type") or source_config.get("condition", ""),
                "trial_id": raw_config.get("trial_id", source_config.get("trial_id", "")) if isinstance(raw_config, dict) else (
                    run_metadata.get("trial_id", source_config.get("trial_id", "")) if isinstance(run_metadata, dict) else source_config.get("trial_id", "")),
                "status": status,
                "source_config": source_config.get("path", ""),
                "available_files": ";".join(present),
                "release_asset": asset_name,
                "archive_directory": f"{model}/{relative.as_posix()}",
            })
        inventory[model] = {
            "json_files": len(files),
            "episodes": sum(status_counts.values()),
            "status_counts": dict(status_counts),
            "source_bytes": sum(path.stat().st_size for path in files),
            "asset": asset_name,
            "asset_bytes": archive.stat().st_size,
            "sha256": digest,
        }
        print(f"{model}: {inventory[model]['episodes']} episodes, {len(files)} JSON, {archive.stat().st_size} ZIP bytes", flush=True)

    fields = ("model_group", "task", "episode_id", "condition", "trial_id", "status",
              "source_config", "available_files", "release_asset", "archive_directory")
    with (results / "manifest.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    (summary / "run_inventory.json").write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (results / "archive_checksums.sha256").write_text("\n".join(checksums) + "\n", encoding="utf-8")
    print(f"indexed {len(rows)} episode directories", flush=True)


if __name__ == "__main__":
    main()
