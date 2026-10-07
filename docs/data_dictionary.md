# Data dictionary

## Task configurations

`configs/tasks/<task>/<condition>.json` defines an episode. The main fields are `episode_id`, `trial_id`, `seed`, `model`, `scenario`, and `pressure`. `scenario` contains the simulated task, resources, tools, and completion predicates. `pressure` describes the condition and when it is introduced. Some condition labels retain historical aliases.

## Episode files

| File | Meaning |
| --- | --- |
| `config.json` | Configuration recorded for the run, when present. |
| `events.json` | Ordered observations, actions, tool results, and model output metadata. |
| `final_state.json` | Final simulated state and recorded effects. |
| `judge_input.json` | Unscored trajectory evidence; the filename is historical. |
| `error.json` | Failure information, when present. |

CQ, Eop, and RES are computed with fixed rules from the configuration, events, and final state. The released archive builder omits API connection metadata and redacts local machine paths and network addresses.

## Result index

Each row in `results/manifest.csv` represents one episode directory. `model_group`, `task`, and `episode_id` identify it. `condition` and `trial_id` come from the archived run when available, otherwise from the matching source configuration. `source_config` points to that configuration. `available_files` lists its JSON filenames. `release_asset` and `archive_directory` identify the original archive location. `status` is `complete` when `events.json`, `final_state.json`, and `judge_input.json` are present; otherwise it is `error` or `partial`.
