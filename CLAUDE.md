# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single-node, hourly **PyPSA** dispatch model of the German (DE/LU) power system that evaluates the
**Kraftwerksstrategie** capacity mechanism: Scenario **A** (no policy) vs **B** (+10 GW H₂-ready CCGT)
in 2030, calibrated against real 2025 data. Academic group project (RUB). Pure Python batch scripts —
no web service, no package, no test suite.

(General behavioural guidelines — "Think before coding / Simplicity / Surgical changes /
Goal-driven" — live in the parent `../CLAUDE.md` and are already in context; they are not repeated here.)

## Commands

Two-step pipeline — inputs must be fetched before the model runs:

```bash
python data_loader.py   # fetch + clean authentic 2025 hourly data -> data/processed/*.csv
python model.py         # calibrate, solve A/B/B_low/B_high, write results/*.csv + figures/*.png
```

- **Use the project venv to run:** `./venv/Scripts/python.exe model.py`. The bare system `python`
  does NOT have PyPSA. The venv has PyPSA 1.2.3 + HiGHS installed. (`requirements.txt` pins
  pypsa 0.29 / numpy<2 for *fresh* installs; the venv intentionally differs — don't "fix" the pin.)
- `data/processed/*.csv` are already committed, so `model.py` can be re-run repeatedly without
  re-fetching. Only re-run `data_loader.py` to refresh the Energy-Charts download (token-free,
  ~1 min, deliberate 1 s sleeps between month requests).
- **No lint/test tooling exists.** Verification = run `model.py` and read what it prints: the
  calibration mean-price error, the generation-mix line, and the `[PLAUSIBILITY WARNINGS]` block.
- `python config.py` prints the implied merit order (marginal-cost sanity check) without solving —
  the fastest way to check a fuel/CO₂/efficiency change before a full run.
- `build_report.py` regenerates `report.docx` from the results CSVs, but its `ROOT` is a hardcoded
  cloud path (`/sessions/.../mnt/...`); it will not run locally until `ROOT` is edited.

## Architecture & data flow

```
config.py ──▶ data_loader.py ──▶ model.py ──▶ results/*.csv ──▶ build_report.py / report / slides
(params)      (2025 inputs)      (solve+metrics+figures)   (single source of truth)
```

- **config.py is the one parameter store.** `model.py` contains NO hardcoded numbers — every
  capacity, fuel/CO₂ price, efficiency, emission factor and switch is read from config. This
  "zero-hardcoding" rule is load-bearing: change an assumption in config, re-run, and all results
  and figures update consistently. Each value is source-tagged in a comment; unverified ones are
  marked `[VERIFY]`.
- **Two reference years.** 2025 = calibration (real measured weather/demand/price). 2030 = the
  policy experiment (projected fleet). The 2030 demand is the 2025 hourly *shape* scaled to a 2030
  annual total (`DEMAND_2030_TWH`).
- **`results/comparison_table.csv` is the single source of truth** for every downstream number
  (report, slides). Nothing recomputes model metrics outside `model.py`.

### model.py core pipeline

`build_network(year, capacities, cf, demand, storage, allow_import)` builds a PyPSA single-bus
network → `solve()` (HiGHS) → `extract_hourly()` (tidy 8760-row DataFrame) → `compute_metrics()`
(pure, PyPSA-free function returning the study metrics) → CSV/figure writers in `main()`.

- Hourly price = the bus marginal price (running cost of the most expensive dispatched unit).
  `config.marginal_cost()` = `(fuel + CO₂_intensity·CO₂_price)/efficiency + VOM`. VRE and
  run-of-river are price-takers (VOM only); `VRE_TECHS` lists them.
- A VOLL load-shedding generator (`VOLL_EUR_MWH`) is always added so the LP is feasible and
  scarcity hours are priced.
- Two must-run bands add heat-sector realism without unit commitment: `BIOMASS_MUSTRUN_PU`
  (fixed biomass baseband) and `CHP_GAS_MUSTRUN_PU` (existing-CCGT heat-led floor). These are the
  only calibration handles — the generation mix is a validation, not a tuned target.
- 2030 is solved **twice**: with capped cross-border imports (`INCLUDE_CROSSBORDER`,
  `IMPORT_CAP_MW`, `IMPORT_PRICE_EUR_MWH`) and **islanded** (no imports), to bracket adequacy.
  The 2025 calibration is ALWAYS islanded.
- `check_plausibility()` flags out-of-band metrics but never auto-corrects (warnings only).

### Calibration (run_calibration in model.py)

Validates the model against realised 2025: the price distribution → `calibration_2025_validation.csv`
(+ fig8), and an import-adjusted generation mix → `calibration_2025_generation.csv` (+ fig9).
Verified 2025 benchmarks are hardcoded in config (`ACTUAL_2025_GEN_TWH`, `ACTUAL_2025_PRICE_STATS`,
`ACTUAL_2025_RENEWABLE_SHARE_PCT`) so the validation CSVs are always complete regardless of the
downloaded file. A deterministic merit-order LP matches the MEAN price and the generation MIX but
NOT the price tails (no negative-price hours, no scarcity spikes) — a documented design limitation
of a single-node LP without unit commitment, not a bug. The whole routine is wrapped so a
calibration failure never blocks the main 2030 run.

## Project invariants (do not break)

- **Never change config.py parameters unless explicitly asked** — they are calibrated and source-tagged.
- Input CSV columns stay **snake_case** (no spaces, no capitals). `EC_NAME_MAP` in data_loader.py
  maps Energy-Charts production-type names to these internal labels.
- All timestamps are **UTC-aware**; never strip tz. Profiles are exactly **8760 hours**
  (`HOURS_PER_YEAR`); 2025 and 2030 are both non-leap.
- Solar CF values below 0.001 are zeroed; all CFs clipped to [0, 1].
- **Surgical edits only:** fixing one metric must not touch unrelated functions. Every model number
  reported anywhere must trace to a results CSV produced by an actual run — never typed, estimated,
  rounded to look cleaner, or recomputed from memory.

## Reporting workflow (from AGENTS.md)

The report and presentation follow a strict **two-layer separation**: Layer 1 (qualitative CRM
literature — no model numbers) and Layer 2 (quantitative — only verified model outputs). Build and
RUN the model before writing any Layer-2 result; cross-check headline metrics two ways and against a
real-world benchmark before reporting. AGENTS.md defines the full gated, checkpoint-after-each-step
workflow and the data-integrity rules.
