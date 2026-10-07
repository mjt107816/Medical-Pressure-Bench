# Reproducing episodes

Run the commands below from the repository root. Python 3.11 is recommended.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/run_experiment.py \
  --config-dir configs/tasks/task_147_radiopharmaceutical_release_gate \
  --output-dir outputs/smoke \
  --demo --limit 1
```

The demo uses no external model service. For a live run, copy `api.config.example.yaml` to `api.config.yaml`, supply the model, provider, API base URL, endpoint, and key, then omit `--demo`. The real connection settings belong in ignored local files or environment variables. `scripts/run_config_dir_parallel.py` runs a fresh configuration directory with multiple workers.

A completed episode writes `config.json`, `events.json`, `final_state.json`, and `judge_input.json`. The last file is unscored trajectory evidence under a historical name. The reported outcome metrics use deterministic rules in `judge/rules.py`.

## Published results

`results/manifest.csv` indexes 17,000 archived episode directories. `results/samples/` contains browsable baseline/time examples. The five large `raw_runs_<model>.zip` archives are intentionally excluded from this Git repository; `results/archive_checksums.sha256` identifies the local archive versions. The summary reports and an independent rule recomputation are under `results/summary/`.

If the five archives are available locally, extract them into the repository root to restore `<model>/<task>/<episode>/`, then run:

```bash
python scripts/run_judge.py \
  --runs-root . \
  --output results/summary/rule_recomputed_scores.json
python scripts/analyze_clinical_obligation_retention.py --root .
```

`scripts/package_results.py --source-root ..` rebuilds the anonymized archives and index when the original model output folders are placed next to the repository.
