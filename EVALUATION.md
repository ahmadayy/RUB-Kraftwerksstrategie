# EVALUATION.md — Honest Self-Assessment

**Project:** Evaluating Germany's proposed capacity mechanism *Kraftwerksstrategie* (RUB).
**Scope of this file:** a sceptical, peer-review-style audit of the **model-based results only**
(Layer 2). Every figure quoted here is read directly from `results/comparison_table.csv` and
`results/sensitivity_table.csv` — nothing is re-estimated. Benchmarks are real and cited.

Scenarios: **A = without new capacity (0 GW, no CRM)**, **B = with the Kraftwerksstrategie
(+10 GW H₂-ready CCGT)**. Calibration: modelled 2025 mean price €89.7 vs realised €89.3
(**0.4% error**).

---

## 1. Sanity checks (value-by-value, against cited real-world benchmarks)

| Metric | A | B | Verdict | Benchmark (cited) |
|---|---|---|---|---|
| Mean price (€/MWh) | 113.0 | 92.6 | **Plausible** | DE day-ahead €78.5 (2024), €95 (2023) [BNetzA/SMARD]; Agora 2030 range €52–123 |
| Median price (€/MWh) | 108.6 | 104.2 | **Plausible** | as above |
| Price volatility, std (€/MWh) | 205.0 | 40.2 | **Plausible** | A inflated by VOLL spikes; B is a normal high-RES spread |
| Scarcity (LoL) hours | 8 | 0 | **Borderline (A)** | reliability standard ≈ 3 h/yr LOLE [ENTSO-E ERAA] — A sits just above it, B at 0 |
| Unserved energy (GWh) | 32.2 | 0.0 | **Plausible** | ~0.005% of 677 TWh demand — a thin residual gap |
| CCGT full-load hours | 5517 | 4926 | **Borderline-HIGH** ⚠ | historical 2,000–4,500 h (2022–24); 2030 structurally higher (coal at KVBG floor, nuclear gone) but still high |
| OCGT full-load hours | 1447 | 709 | **Plausible** | peakers run few hours by design |
| Renewable curtailment (%) | 2.5 | 2.5 | **LOW side** ⚠ | 2030 studies ~5–15%; single-node ignores grid-congestion curtailment (the dominant real cause) |
| Renewable share (%) | 72.4 | 71.8 | **Plausible** | below the 80%-of-*demand* EEG 2023 target (this is share of *generation*) |
| Net imports (TWh) | 7.1 | 1.6 | **Plausible** | DE net trade swings by several TWh year-to-year [Agora] |
| CO₂ emissions (Mt) | 101.3 | 88.7 | **Plausible** | DE power-sector emissions, falling toward 2030 [Agora/UBA] |
| Total system cost (bn €) | 26.75 | 25.80 | **Plausible** | right order of magnitude for annual operating + new-build cost |

**Flags:** two magnitudes are off in the *optimistic* direction — **CCGT full-load hours are
high** (5517 h) and **curtailment is low** (2.5%).
Both trace to the single-node, perfect-foresight design (see §4), not to a coding error. The
**scarcity numbers are small and knife-edge** (one weather year), so the *exact* 8→0 should be read
as "a thin residual gap that the policy closes," not a precise forecast.

---

## 2. Direction-of-effect check (A → B vs CRM theory)

| Effect | Theory expects | Model found | Match? | Diagnosis |
|---|---|---|---|---|
| Scarcity hours | ↓ | 8 → 0 | ✅ | firm capacity covers the deficit |
| Unserved energy | ↓ | 32.2 → 0.0 GWh | ✅ | same event as scarcity |
| Average price | ↓ / neutral | 113.0 → 92.6 (-18%) | ✅ | spikes removed |
| CCGT capacity factor | ↓ | 63.0% → 56.2% | ✅ | capacity dilution |
| Curtailment | ↑ slightly | unchanged (2.5%) | ⚠ deviation | **genuine, not artefact**: flexible firm gas/imports never run in surplus hours, so they cannot raise curtailment. A "slight rise" would need an inflexible must-run plant; the new CCGT is dispatchable |
| Total system cost | ↑ | 26.75 → 25.80 bn (-3.5%) | ⚠ diverges | **genuine finding**: efficient new gas (MC ≈ €91) displaces costlier gas, peakers and imports; saving > annualised build cost. Robust to VOLL removal (excl-VOLL also −3.2%) but **conditional on 2030 fuel/CO₂ prices** |
| CO₂ emissions | ambiguous | 101.3 → 88.7 Mt (-12%) | ✅ resolved ↓ | efficient gas displaces coal and high-MC imports |

**Two deviations from the naive CRM script — both diagnosed as genuine, explainable findings, not
modelling artefacts.** The cost-down result is the headline non-obvious finding and is flagged as
*assumption-conditional*.

---

## 3. Layer-consistency verdict (does the model confirm, nuance, or contradict the literature?)

| Metric | Part 1 (literature) | Part 2 (model) | Verdict |
|---|---|---|---|
| Price level & volatility | down / much less volatile (Bublitz et al., 2019) | mean -18%, volatility -80% | **Confirms** |
| Resource adequacy | improves (Bhagwat et al., 2017; ACER & CEER, 2013) | 8→0 h; unserved →0 | **Confirms**, but **nuanced**: benefit is *modest* under 20 GW imports |
| CCGT utilisation | falls — capacity dilution | FLH 5517→4926 | **Confirms** |
| Curtailment | unchanged / slight rise | unchanged | **Confirms** |
| Total system cost | rises — "security has a price" | falls -3.5% | **Contradicts (genuine)** — efficient displacement, conditional on prices |
| CO₂ | ambiguous | down -12% | **Resolves** to a decrease |
| Missing money (Cramton & Stoft, 2005; Joskow, 2008) | spikes reward firm capacity | B removes those very spikes | **Illustrates** — the rationale for the payment |
| Interconnectors substitute (Newbery, 2016) | imports vs capacity are substitutes | imports -78% | **Confirms** the substitution |

**Synthesis:** Part 2 **confirms** the core CRM literature on adequacy, prices and utilisation;
**nuances** it on the *magnitude* of the adequacy benefit (import-dependent); and **productively
contradicts** the textbook "CRM adds cost" claim with a robust, price-conditional efficiency result
that still rests on the missing-money rationale.

---

## 4. Limitations that could mislead (and the direction of the bias)

1. **Single-node (copper-plate).** No internal grid / congestion. **Bias: optimistic** — it
   *understates curtailment* (real German curtailment is largely grid-driven redispatch) and
   *overstates* how smoothly gas covers load, flattering both adequacy and curtailment.
2. **Data basis — REAL, not synthetic.** The 2025 hourly demand, generation and price are
   **authentic measured data** from Fraunhofer ISE **Energy-Charts** (re-publishing Bundesnetzagentur/
   SMARD and ENTSO-E; CC BY 4.0). renewables.ninja was *not* used; **no `[SYNTHETIC-FALLBACK]` series
   exist.** *Caveat:* renewable capacity factors were derived as *generation ÷ installed capacity*,
   so the **hourly shape is authentic** but absolute CF *levels* can be slightly distorted, and only
   **one weather year (2025)** underlies the 2030 runs.
3. **Perfect-foresight LP, no unit commitment.** No forecast error, no start-up/min-load, no
   reserves. **Bias: optimistic on adequacy** — a real operator without perfect foresight would see
   more tight hours and higher cost.
4. **No investment endogeneity.** The 10 GW is *imposed*, not chosen. The model can *show* the
   missing-money gap exists but **cannot capture it endogenously** — it assumes the policy delivers
   the plant.
5. **Simplified cost structure.** No start-up costs, no ramping limits, single fuel/CO₂ prices.
   **Bias: optimistic on cost/CO₂** — free cycling understates real part-load cost and emissions.
6. **Dispatch-only, single reference/weather year.** The headline adequacy numbers (8 vs 0) come
   from one mild year and a fixed 20 GW import assumption; **a Dunkelflaute year or imports = 0 would
   change them materially.** Magnitudes are fragile; directions are not.

---

## 5. Verdict

**(b) Directionally correct, but quantitatively rough.**

Justification: every A→B direction is robust and theory-consistent, the model is calibrated to the
real 2025 price within 0.4%, the sensitivity ladder (5/10/20 GW) is monotonic,
and the integrity chain is clean. However, three design choices — a single node, perfect-foresight
LP, and a single weather year — make several *magnitudes* unreliable: curtailment
(2.5%) is too low, CCGT full-load hours (5517 h)
are high, and the scarcity result (8→0) is knife-edge. The non-obvious cost-down finding is robust
*within* the model but **conditional** on the assumed 2030 fuel and CO₂ prices. The study therefore
supports its qualitative conclusions with confidence but should **not** be read as a precise
quantitative forecast — it is a clean, transparent directional experiment, not an operational
adequacy study.

---

## 6. Integrity check

- **report.docx vs `comparison_table.csv`:** ✅ verified programmatically — Table 3 matches the CSV
  cell-for-cell (15/15 rows).
- **presentation.pptx vs `comparison_table.csv`:** ✅ verified programmatically — slide-18 table
  matches the CSV cell-for-cell (read back from the saved file).
- **report numbers vs presentation numbers:** ✅ identical on all overlapping metrics.
- **Discrepancies found:** **None.**
- **Fabricated citations:** **None** — the deck's reference list is a subset of the report's APA-7th
  reference list (Bublitz et al., 2019; Cramton & Stoft, 2005; Joskow, 2008; Bhagwat et al., 2017;
  Newbery, 2016; ACER & CEER, 2013; European Parliament, 2017; European Union, 2019; Brown et al.,
  2018 [PyPSA]; Huangfu & Hall, 2018 [HiGHS]; Danish Energy Agency, 2024; 50Hertz et al., 2025 [NEP];
  BMWE, 2026; Umweltbundesamt, 2022).

### Outstanding `[VERIFY]` items (from `config.py` / provenance — official figures used, not yet final-source-locked)
- 2030 **CO₂ (EUA) price** = 110 €/t — NEP/Langfristszenarien assumption `[VERIFY]`
- 2030 **gas fuel price** = 30 €/MWh_th — scenario assumption `[VERIFY]`
- 2030 **gross demand** = 680 TWh — NEP Szenariorahmen 2025 (bracketed by Prognos 658 / EEG 750) `[VERIFY]`
- **2025 installed-capacity** fleet (calibration) — realised end-2024/2025 `[VERIFY]`
- **Technology efficiencies / costs** — Danish Energy Agency catalogue `[VERIFY]`
- **2030 battery storage** = 25 GW — NEP flexibility build-out `[VERIFY]`
- **New-CCGT CAPEX/FOM** (900 €/kW; 20 €/kW/yr) — Danish Energy Agency `[VERIFY]`

### Authorship & provenance statement
> **I (Muhammad) ran the PyPSA/HiGHS model and uploaded the results, figures, and any screenshots.
> Claude wrote the report and presentation from those uploaded files only; all model numbers come
> from them.**

---

## 7. Top 5 concrete fixes for more defensible results

1. **Add a North/South split (≥2 nodes) with a transmission constraint** → captures grid congestion,
   correcting the under-stated curtailment and over-stated gas utilisation.
2. **Use multiple weather years (e.g., 30 ERA5 / renewables.ninja years)** → replaces the fragile
   single-year "8 → 0" with a proper LOLE / expected-energy-not-served *distribution*.
3. **Monte Carlo on key assumptions: ±20% gas, ±10% CO₂, ±15% demand** → tests robustness of the
   price, cost and CO₂ results, especially the assumption-conditional cost-down finding.
4. **Add unit commitment + forced-outage rates (start-up, min-load, ramping)** → realistic CCGT
   full-load hours, adequacy and part-load emissions.
5. **Make investment endogenous (capacity-expansion mode)** → lets the model choose the build,
   testing whether 10 GW is optimal and capturing the missing-money problem endogenously.
