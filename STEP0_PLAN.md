# STEP 0 — Plan (v2): Architecture, Assumptions, Scenarios, Authentic Data Plan

**Project:** Evaluating Germany's proposed capacity mechanism "Kraftwerksstrategie" (RUB)
**Framing (revised):** **Target year 2030** (model-based effect) · **2025 = backcast/calibration & weather year**
**Date compiled:** 2026-06-13  **Status:** Proposal — awaiting "Approved. Proceed to Step 1."

> All model **results** come only from the executed model (Steps 1–2). Below is a *plan* with cited
> input sources. **[VERIFY]** = best-available now, locked from the primary dataset in Step 1.
> Nothing here is a model output.

---

## 0.1 Framing: why 2030 target, 2025 backcast

The Kraftwerksstrategie's plants become operational **by 2031** (BMWE/EU agreement, 15 Jan 2026), so
their price/adequacy effect is only meaningful in a **forward-looking 2030 power system** — high
renewables (EEG: 215 GW PV, 115 GW onshore, 30 GW offshore), coal cut to the KVBG 2030 ceiling
(17 GW), nuclear at zero. The study therefore computes the **model-based effect for target year 2030**.

**2025 is the calibration & weather year:** (i) it validates that the dispatch model reproduces a real,
recent year (generation mix, prices, CCGT full-load hours, CO₂ — vs Destatis/SMARD/Energy-Charts);
(ii) its **hourly weather-driven capacity factors and demand shape** are carried forward and applied to
the 2030 fleet. 2025 is the most recent complete calendar year (full data published by Fraunhofer ISE,
Destatis, BNetzA as of 2026).

This resolves the v1 weakness: a 2024 backcast showed near-zero scarcity (so a small CRM effect); the
2030 projection has genuine residual-load stress, where CRM theory predicts the effect appears.

---

## 0.2 Model architecture (professional-grade)

| Attribute | Specification |
|---|---|
| Framework | PyPSA |
| Spatial scope | **Single node** = Germany / Luxembourg (DE/LU), copperplate |
| Temporal scope | **Hourly, 8760 h**, target year 2030; weather/shape from 2025 (8760 h) |
| Run type | **Operational dispatch LP** — fixed 2030 capacities, minimise total system operating cost |
| Solver | **HiGHS** via `linopy`/`highspy` |
| Calibration | Same model re-run on the **2025 fleet + 2025 actuals**, validated vs reality (Step 2) |
| Objective | Min Σ(marginal_costᵢ × genᵢ,ₜ) + VOLL × unserved_energyₜ − storage value |

### Two model instances (same code, different inputs)
1. **CAL-2025** (calibration): 2025 installed fleet, 2025 actual hourly load, 2025 realised CFs,
   2025 fuel/CO₂ prices → validate against observed 2025 mix/price/CO₂.
2. **TARGET-2030** (the study): 2030 projected fleet, 2030 demand (2025 shape scaled), 2025 weather-year
   CFs, 2030 fuel/CO₂ prices → run **Scenario A vs B** (+ B_low/B_high).

### PyPSA components (TARGET-2030)
`Bus` "DE"; `Load` (2030 demand, 2025 shape); `Generator` per carrier — lignite, hard coal, existing
gas CCGT, existing gas OCGT, **new H₂-ready CCGT (only in B/B_low/B_high)**, oil/other, biomass,
run-of-river hydro, onshore wind, offshore wind, solar PV; `StorageUnit` PHS + utility battery;
**VOLL load-shed generator (€3000/MWh [VERIFY])**; **net cross-border exchange** as an exogenous fixed
hourly profile (2030 from NEP market assumptions, shaped on 2025 ENTSO-E flows) **[VERIFY]**.

**Modelling choices & limitations (explicit):**
- *Single-node copperplate* — no internal grid congestion; defensible for a national price/adequacy study.
- *Weather year* — one meteorological year (2025) applied to 2030; multi-year robustness noted as a limitation (optional: add a 2nd weather year).
- *Cross-border* — exogenous net-exchange profile (single-node cannot endogenise trade); the rigorous alternative is the multi-node extension below.
- *Demand shape* — 2025 hourly profile scaled to the 2030 total; optional overlay of electrification profiles (EV/heat-pump/electrolyser) from NEP/Langfristszenarien.

### Optional extensions (listed, NOT included unless approved)
- Multi-node DE + neighbours (NTC links, endogenous trade).
- Capacity-expansion LP (model *chooses* new firm capacity vs fixed +10 GW).
- Multiple weather years (e.g. 2025 + a Dunkelflaute-heavy year) for adequacy robustness.

---

## 0.3 Authentic data plan (one row per input series)

Two blocks: **(A) 2025 actuals** (calibration + weather/shape) and **(B) 2030 projections** (the
forward fleet/demand/prices). No synthetic profiles in the canonical plan.

### Block A — 2025 actuals (calibration & weather year)

| # | Series | Primary source (dataset) | URL | Units | Obtain via | Fallback (+flag) |
|---|---|---|---|---|---|---|
| 1 | 2025 hourly load | ENTSO-E — *Actual Total Load, DE_LU* | transparency.entsoe.eu | MW | Energy-Charts API / `entsoe-py` | SMARD.de `[DATA-GAP]` |
| 2 | 2025 gen per type | ENTSO-E — *Actual Generation per Production Type* | transparency.entsoe.eu | MW | Energy-Charts API | SMARD.de `[DATA-GAP]` |
| 3 | 2025 installed cap per type | ENTSO-E IGCPT + BNetzA MaStR/Kraftwerksliste | transparency.entsoe.eu ; marktstammdatenregister.de | MW | API / CSV | Fraunhofer ISE `[DATA-GAP]` |
| 4 | 2025 day-ahead price (validation) | ENTSO-E — *Day-ahead Prices, DE_LU* | transparency.entsoe.eu | €/MWh | Energy-Charts API | SMARD.de `[DATA-GAP]` |
| 5–7 | 2025 realised CF wind on/offshore, PV | derived: ENTSO-E gen ÷ installed cap (or renewables.ninja MERRA-2 2025) | transparency.entsoe.eu ; renewables.ninja | CF 0–1 | computed / ninja API | the other of the two `[DATA-GAP]` |
| 8 | 2025 RoR hydro profile | ENTSO-E actual hydro RoR | transparency.entsoe.eu | MW | Energy-Charts API | SMARD.de `[DATA-GAP]` |
| 9 | 2025 net cross-border flow | ENTSO-E *Cross-Border Physical Flows* | transparency.entsoe.eu | MW | API | SMARD.de `[DATA-GAP]` |
| 10 | 2025 generation/consumption totals (cross-check) | Destatis; AG Energiebilanzen; Fraunhofer ISE *Stromerzeugung 2025* | destatis.de ; ag-energiebilanzen.de ; energy-charts.info | TWh | web/CSV | UBA `[VERIFY]` |

### Block B — 2030 projections (forward fleet, demand, prices)

| # | Series | Primary source (dataset) | URL | Units | Status |
|---|---|---|---|---|---|
| 11 | 2030 installed capacity per carrier | **NEP Szenariorahmen 2037/2045 (V2025), Scenario B** (BNetzA-approved 30 Apr 2025); cross-check BMWE *Langfristszenarien* (T45) | netzentwicklungsplan.de ; langfristszenarien.de | GW | **[VERIFY]** lock exact in Step 1 |
| 12 | 2030 RE targets (anchors) | **EEG 2023** statutory: PV 215, onshore 115, offshore 30 GW | gesetze-im-internet.de/eeg_2014 ; bmwe | GW | confirmed |
| 13 | 2030 coal capacity | **KVBG** Anlage 2: 2030 ceiling **17 GW = 8 hard coal + 9 lignite** | bundesnetzagentur.de (Kohleausstieg) | GW | confirmed (statutory) |
| 14 | 2030 gross demand | NEP Szenariorahmen 2025 (Scn B); EEG planning value 750 TWh; Prognos 658 TWh | netzentwicklungsplan.de | TWh | **[VERIFY]** (range 658–750; lock NEP B value) |
| 15 | 2030 gas/coal/CO₂ price assumptions | **NEP Szenariorahmen 2025** commodity-price annex; BMWE Langfristszenarien | netzentwicklungsplan.de | €/MWh, €/t | **[VERIFY]** extract from PDF in Step 1 |
| 16 | Tech costs/efficiency (CAPEX/FOM/VOM/η/life) | Danish Energy Agency Technology Catalogue via PyPSA `technology-data` | ens.dk ; github.com/PyPSA/technology-data | mixed | **[VERIFY]** |
| 17 | CO₂ intensity per fuel | Umweltbundesamt CC 29/2022 | umweltbundesamt.de | t/MWh_th | **[VERIFY]** |
| 18 | Policy (Kraftwerksstrategie / KWSG) | BMWE press release 15.01.2026; KWSG | bundeswirtschaftsministerium.de | qual.+GW | confirmed |

**Reachability checked (2026-06-13):** Energy-Charts API → HTTP 200; BMWE Kraftwerksstrategie release →
full text retrieved; NEP/Szenariorahmen, EEG, KVBG, Langfristszenarien, Fraunhofer ISE *Stromerzeugung
2025*, Destatis 2025 → all confirmed as published, citable documents (URLs in table). ENTSO-E &
renewables.ninja APIs need a free token (noted); Energy-Charts (token-free, aggregates ENTSO-E/SMARD)
is the primary programmatic channel. OPSD time series frozen ~2020 → plant-list cross-check only.

---

## 0.4 Full parameter & assumptions table (TARGET-2030)

### (a) Installed capacity per carrier — 2030
2025 column = calibration fleet (locked from ENTSO-E/MaStR). 2030 column = projection; renewables &
coal are statutory/approved anchors; **gas is the policy variable** (see scenarios). All 2030 thermal
values **[VERIFY]** vs NEP Szenariorahmen 2025 (Scn B) / Langfristszenarien.

| Carrier | 2025 (GW) | 2030 (GW) | 2030 anchor |
|---|---|---|---|
| Solar PV | ~105 [VERIFY] | **215** | EEG 2023 / NEP B |
| Onshore wind | ~64 [VERIFY] | **115** | EEG 2023 / NEP B |
| Offshore wind | ~9.2 [VERIFY] | **30** | EEG 2023 / NEP B |
| Biomass | ~9 [VERIFY] | ~8 [VERIFY] | NEP B |
| Run-of-river hydro | ~5 [VERIFY] | ~5 [VERIFY] | NEP B |
| Lignite | ~15 [VERIFY] | **9** | KVBG 2030 ceiling |
| Hard coal | ~13 [VERIFY] | **8** | KVBG 2030 ceiling |
| Natural gas (existing) | ~34 [VERIFY] | **~34** [VERIFY] | **Scenario A counterfactual** (no-strategy gas) |
| Oil / other fossil | ~4 [VERIFY] | ~2 [VERIFY] | NEP B |
| Nuclear | 0 | 0 | — |
| Pumped-hydro storage | ~9.4 [VERIFY] | ~10 [VERIFY] | NEP B |
| Utility battery storage | ~2 [VERIFY] | ~tens of GWh [VERIFY] | NEP B (key flex) |
| **New H₂-ready CCGT** | 0 | **+0 / +10 / +5 / +20** | **Kraftwerksstrategie — scenario variable** |
| 2030 gross demand | ~510 TWh (2025) [VERIFY] | **~650–750 TWh** [VERIFY] | NEP B 2030 (EEG 750; Prognos 658) |

### (b) Techno-economic parameters (DEA Technology Catalogue via PyPSA `technology-data`; FFE/Fraunhofer cross-check)
CAPEX/FOM don't affect dispatch (capacities fixed); listed for completeness + optional investment run.
Dispatch uses **η, VOM, fuel, CO₂**. All **[VERIFY]** vs pinned `technology-data` CSV.

| Tech | VOM €/MWh_el | η (% LHV) | (CAPEX €/kW, life yr — reference) |
|---|---|---|---|
| New H₂-ready CCGT (B) | ~4.0 | **58–60** | ~900–1050, 25–30 |
| Existing CCGT | ~4.0 | ~52 [VERIFY] | sunk |
| Existing OCGT | ~3.0 | ~40 | ~450, 25 |
| Hard coal | ~3.6 | ~43 | sunk |
| Lignite | ~3.3 | ~38 | sunk |
| Biomass | ~4.0 | ~35 | — |
| Wind on/offshore, PV | ~0–3 | — | — |
| PHS / battery | ~0.5 | round-trip ~0.75 / ~0.86 | — |

### (c) Fuel, CO₂ price, CO₂ intensity — 2025 (calibration) vs 2030 (projection)
2030 column **[VERIFY]** — locked from NEP Szenariorahmen 2025 commodity annex / Langfristszenarien.

| Quantity | 2025 (calibration) | 2030 (projection) | Units | Source |
|---|---|---|---|---|
| Gas (TTF) | ~35 [VERIFY] | ~25–35 [VERIFY] | €/MWh_th | EEX/Energy-Charts ; NEP Szenariorahmen |
| Hard coal (API2) | ~11 [VERIFY] | ~8–12 [VERIFY] | €/MWh_th | Argus/IEA ; NEP |
| Lignite | ~3.5 [VERIFY] | ~3.5 [VERIFY] | €/MWh_th | DEA/literature |
| CO₂ (EUA) | ~75 [VERIFY] | **~100–130 [VERIFY]** | €/t | EEX/ICAP ; NEP/Langfristszenarien |
| CO₂ intensity gas / hard coal / lignite / oil | 0.201 / 0.337 / 0.364 / 0.267 [VERIFY] | same | t/MWh_th | UBA CC 29/2022 |
| VOLL | 3000 [VERIFY] | 3000 [VERIFY] | €/MWh | ACER/ENTSO-E ERAA |

### (d) Marginal cost — full calculation (illustrative 2030 values; locked in Step 1)
**MC = (fuel + CO₂_intensity × CO₂_price) / η + VOM** €/MWh_el, with **2030** gas ≈ 30 €/MWhₜₕ, EUA ≈ 110 €/t:

- **New CCGT (η 0.60):** (30 + 0.201×110)/0.60 + 4.0 = (30+22.11)/0.60 + 4.0 = 52.11/0.60 + 4.0 ≈ **90.9**
- **Existing CCGT (η 0.52):** (30 + 22.11)/0.52 + 4.0 ≈ **104.2**
- **Hard coal (η 0.43):** (10 + 0.337×110)/0.43 + 3.6 = (10+37.07)/0.43 + 3.6 = 47.07/0.43 + 3.6 ≈ **113.1**
- **Lignite (η 0.38):** (3.5 + 0.364×110)/0.38 + 3.3 = (3.5+40.04)/0.38 + 3.3 = 43.54/0.38 + 3.3 ≈ **117.9**
- **Existing OCGT (η 0.40):** (30 + 22.11)/0.40 + 3.0 ≈ **133.3**

**2030 merit order: new CCGT (91) < existing CCGT (104) < hard coal (113) < lignite (118) < OCGT (133).**
**Key 2030 dynamic:** the high carbon price pushes **coal *above* gas** — efficient gas/H₂ CCGT becomes
the firm marginal technology, and in low-VRE "Dunkelflaute" hours the price is set by gas or, if firm
capacity is short, by **scarcity (→ VOLL)**. Adding 10 GW CCGT (Scenario B) is therefore expected to
**cut loss-of-load hours and cap scarcity prices** — the measurable CRM effect this study quantifies.
(Contrast: 2025 calibration has cheap coal *below* gas — the model must reproduce both regimes.)

---

## 0.5 Scenario definitions (all at TARGET-2030)

| ID | Name | Definition (2030 fleet) | Use |
|---|---|---|---|
| **A** | Baseline (No CRM) | 2030 projection (NEP B), gas = existing fleet only (~34 GW), **no Kraftwerksstrategie new build** | **Main report** |
| **B** | Kraftwerksstrategie **[CANONICAL]** | A **+10 GW** new H₂-ready CCGT (η ~0.60) | **Main figures & slides** |
| **B_low** | Sensitivity | A **+5 GW** CCGT | CSV + appendix only |
| **B_high** | Sensitivity | A **+20 GW** CCGT | CSV + appendix only |

**Policy anchoring (BMWE, 15 Jan 2026 — official):** 12 GW of new controllable capacity tendered in
2026, of which **10 GW carry the long-run dispatchability criterion** ("moderne und hocheffiziente
Gaskraftwerke", operational by 2031). **Scenario B's +10 GW maps directly onto this 10 GW long-run
tranche.** B_low (5 GW) ≈ partial first-auction new build; B_high (20 GW) ≈ Minister Reiche's earlier
"≥20 GW" ambition / cumulative 2027 + 2029-30 auctions. Earlier figures (23.8 GW Habeck draft; 12.5 GW
interim KWSG target) noted as history, flagged **[VERIFY]** vs the forthcoming statute.

**Counterfactual logic:** A holds gas at today's existing level to 2030 (the system *without* the
strategy's incentivised builds); B adds the policy capacity. The A→B delta isolates the
Kraftwerksstrategie's effect on 2030 prices, dispatch, emissions and adequacy.

---

## 0.6 Result metrics (Step-1 CSVs)
`comparison_table.csv` (A vs B) + `sensitivity_table.csv` (B_low/B/B_high), each: total system cost (€);
mean & median wholesale price (€/MWh = energy-balance shadow price); price volatility & scarcity-hour
count; generation by carrier (TWh); **new-CCGT generation (TWh) & full-load hours (h)**; CO₂ (Mt);
curtailment (TWh); **unserved energy (GWh) / loss-of-load hours / VOLL cost**; net imports (TWh);
firm-capacity margin at peak residual load; implied consumer energy cost (€). Plus
`scenario_*_hourly.csv` (8760-h dispatch) and `calibration_2025_validation.csv` (modelled vs observed).
**Headline metric re-derived two ways** (CCGT FLH = gen÷cap vs Σdispatch÷cap) — must agree.

---

## 0.7 File & folder structure
```
project/
├── data_loader.py     # pulls/caches 2025 actuals (Energy-Charts/ENTSO-E) + 2030 projections; writes provenance.json
├── config.py          # all params as labelled dict: cal_2025{} and target_2030{} blocks
├── model.py           # PyPSA build; runs CAL-2025 (validate) then TARGET-2030 A/B/B_low/B_high
├── requirements.txt   # pinned: pypsa, linopy, highspy, pandas, entsoe-py, matplotlib, (atlite/ninja)
├── README.md          # reproduce (Claude's run + optional local re-run + tokens)
├── EVALUATION.md      # Step-6 self-assessment
├── data/              # raw + cached datasets + provenance.json
├── results/           # comparison_table.csv, sensitivity_table.csv, scenario_*_hourly.csv, calibration_2025_validation.csv
├── figures/           # PNG ≥150 dpi, Okabe–Ito palette
└── report/            # report.docx, presentation.pptx
```

---

## 0.8 Verification table

| Item | Value / Status |
|---|---|
| Target & backcast years set + justified | **Target 2030 / calibration & weather 2025** — policy live 2031; 2030 is where CRM effect bites; 2025 = newest complete year |
| Every input series has an official source | **Yes** — 18 rows (Block A 2025 actuals + Block B 2030 projections) |
| Source URLs + datasets cited | **Yes** — provider + exact dataset per row |
| Reachability of sources checked | Energy-Charts API 200; BMWE retrieved; NEP/EEG/KVBG/Langfristszenarien/Fraunhofer 2025 confirmed; ENTSO-E/ninja token noted; OPSD frozen |
| Fallback named for each series | **Yes** — official proxy + flag per row |
| Marginal cost shown with calculation | **Yes** — 5 worked 2030 examples; coal-above-gas flip identified |
| Canonical scenario defined | **B — +10 GW** (anchored to BMWE 10 GW long-run tranche) |
| Sensitivity scope limited | **CSV + appendix only** (B_low 5 GW, B_high 20 GW) |
| Calibration/validation step defined | **Yes** — CAL-2025 vs observed mix/price/CO₂ before 2030 run |
| All [VERIFY] flags listed | 2030 capacities (esp. gas baseline), 2030 demand (658–750), 2030 fuel/EUA prices (NEP annex), efficiencies, CO₂ intensities, VOLL, tech-cost CSV, battery 2030, policy-GW history |
| Folder structure agreed | **Yes** (0.7) |

---

## 0.9 Decisions flagged for approval
1. **2030 scenario anchor:** I propose **NEP Szenariorahmen 2025, Scenario B** (BNetzA-approved; meets
   EEG targets) as the canonical 2030 fleet/demand source, cross-checked against BMWE Langfristszenarien.
   Alternatives: Langfristszenarien T45-Strom, or Ariadne. (Default: NEP B.)
2. **2030 gross demand value:** anchor to NEP B 2030 **[VERIFY]** within 658–750 TWh; optional demand
   sensitivity. (Default: NEP B value, no extra demand scenario.)
3. **Weather year:** single year 2025 applied to 2030 (default), with multi-year robustness optional.
