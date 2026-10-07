# Rule-based result reports

`completion_quality.md`, `operational_efficiency.md`, and `risk_exposure.md` copy the three existing final metric reports from the source workspace. They describe the fixed scoring rules and reported aggregates for CQ, Eop, and RES. `rule_recomputed_scores.json` is an independent calculation from the archived configuration, event, and final-state JSON files using `scripts/run_judge.py`.

All 85 CQ values and 85 RES values in the reports match the independent recomputation to two decimal places. Of 80 paired Eop changes, 76 match within 0.01 point; four Gemini changes differ. The exact differences and calculation details are recorded in `docs/scoring.md`. `run_inventory.json` records archived run counts, file counts, and archive hashes.
