# MedicalPressureBench

This repository contains the experiment configurations, simulated clinical-agent environment, evaluation code, and result index for the MedicalPressureBench study. The benchmark tests how organizational pressure changes an agent's actions on clinical workflow tasks. All tools operate on simulated state.

## Repository map

| Path | Contents |
| --- | --- |
| [`configs/tasks/`](configs/tasks/) | Source JSON configurations for 200 tasks, including baseline and pressure conditions. |
| [`agent_os/`](agent_os/) | Agent implementation and model interaction. |
| [`benchmark_core/`](benchmark_core/) | Simulated environment, pressure injection, tool execution, and episode recording. |
| [`judge/`](judge/) | Deterministic CQ, Eop, and RES rules; run with [`scripts/run_judge.py`](scripts/run_judge.py). |
| [`scripts/analyze_clinical_obligation_retention.py`](scripts/analyze_clinical_obligation_retention.py) | Rule-based paired clinical-obligation audit. |
| [`scripts/`](scripts/) | Episode runners and the result packaging script. |
| [`tests/`](tests/) | Smoke checks for episode execution and deterministic scoring. |
| [`results/summary/`](results/summary/) | Metric reports, independent rule recomputation, and run inventory. |
| [`results/samples/`](results/samples/) | Complete baseline/time episode pairs for each model group. |
| [`results/manifest.csv`](results/manifest.csv) | Per-episode index into the raw-result archives. |
| [`docs/reproduction.md`](docs/reproduction.md) | Setup, a local smoke test, and result retrieval. |
| [`docs/data_dictionary.md`](docs/data_dictionary.md) | Description of the JSON files and manifest columns. |

The source set contains 3,436 JSON configurations; the archived results contain 3,400 episode directories per model group. The outputs are packaged by model group as `raw_runs_<model>.zip` files in the local `release_assets/` directory. These large archives are excluded from this Git repository. The packaging script omits API connection metadata files and removes connection details and local machine paths from other JSON. It preserves simulated `/workspace/` task paths. Their SHA-256 hashes are recorded in [`results/archive_checksums.sha256`](results/archive_checksums.sha256). The `model_group` labels identify result folders and should not be interpreted as frozen model checkpoint IDs.

**Reported outcomes use recorded tool actions and final simulated states with fixed rules. No LLM served as an automated judge for the reported outcomes.** The historical filename `judge_input.json` contains unscored trajectory evidence. The standalone experimental LLM Judge implementations were excluded from this paper repository. See [scoring and verification notes](docs/scoring.md).

## Quick smoke test

Python 3.11 is recommended. From this repository root:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/run_experiment.py \
  --config-dir configs/tasks/task_147_radiopharmaceutical_release_gate \
  --output-dir outputs/smoke \
  --demo --limit 1
```

The demo agent makes no external API calls. To run a model, copy `api.config.example.yaml` to `api.config.yaml`, fill in the provider, model, API base URL, and endpoint, provide a key through `.env` or an environment variable, and omit `--demo`. No service address is included in the repository. See [reproduction instructions](docs/reproduction.md).

## Scope and provenance

The configuration directory retains the full v3 source set, including historical condition-name aliases. The run archives retain the episode JSON and incomplete runs, with connection metadata and local machine paths removed. The per-episode manifest records which files are present. The rule recomputation matches the existing CQ and RES tables, while four Gemini Eop changes differ from the earlier efficiency report; details are in `docs/scoring.md`. Per-run checkpoint IDs and retry settings are not fully recoverable from the current outputs.
