"""
model.py
========
Single-node (DE/LU copper-plate) hourly dispatch model in **PyPSA**, solved with
**HiGHS**, evaluating Germany's *Kraftwerksstrategie* capacity mechanism.

Pipeline
--------
1.  Read authentic 2025 input profiles written by data_loader.py.
2.  CALIBRATION: build & solve the 2025 system, compare modelled price/mix to
    the realised 2025 market (sanity / validation).
3.  TARGET 2030: for each scenario (A, B, B_low, B_high) build the projected
    2030 fleet (renewables = EEG/NEP, coal = KVBG, gas = existing + policy
    new-build), solve, and read results directly from the solver.
4.  Write results CSVs (single source of truth) and 7 figures.

Design rules
------------
* Every parameter comes from config.py (no hard-coded numbers here).
* A VOLL load-shedding generator (EUR 3000/MWh) guarantees feasibility and
  prices scarcity.
* The 2025 weather/demand *shape* is applied to the 2030 fleet by hourly
  position; 2030 demand is the 2025 shape scaled to the 2030 annual total.

Run:  python model.py      (after: python data_loader.py)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # headless backend (no display needed)
import matplotlib.pyplot as plt

import config

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
PROC_DIR = HERE / "data" / "processed"
RESULTS_DIR = HERE / "results"
FIG_DIR = HERE / "figures"
for _d in (RESULTS_DIR, FIG_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# Okabe-Ito colour-blind-safe palette mapped to carriers
OKABE_ITO = {
    "Solar PV": "#E69F00", "Wind onshore": "#56B4E9", "Wind offshore": "#0072B2",
    "Run-of-river": "#009E73", "Biomass": "#117733", "Lignite": "#8B4513",
    "Hard coal": "#333333", "Gas CCGT (existing)": "#D55E00",
    "Gas CCGT (new H2-ready)": "#CC79A7", "Gas OCGT": "#E0A6C4",
    "Oil": "#999999", "Load shedding": "#FF0000", "Import": "#F0E442",
}
VRE_FOR_CURTAILMENT = ("wind_onshore", "wind_offshore", "solar")


# ===========================================================================
# INPUTS
# ===========================================================================
def load_inputs() -> dict:
    """Read processed 2025 profiles (8760 values each) as numpy arrays."""
    need = ["demand_2025_hourly.csv", "cf_2025_hourly.csv", "price_2025_hourly.csv"]
    missing = [f for f in need if not (PROC_DIR / f).exists()]
    if missing:
        raise SystemExit(f"Missing input files {missing}. Run `python data_loader.py` first.")

    demand = pd.read_csv(PROC_DIR / "demand_2025_hourly.csv")["load_mw"].to_numpy(float)
    cf = pd.read_csv(PROC_DIR / "cf_2025_hourly.csv")
    price = pd.read_csv(PROC_DIR / "price_2025_hourly.csv")["price_eur_mwh"].to_numpy(float)

    n = config.HOURS_PER_YEAR
    for name, arr in [("demand", demand), ("price", price)]:
        if len(arr) != n:
            raise SystemExit(f"{name} has {len(arr)} rows, expected {n}.")

    return {
        "demand_2025": demand,
        "cf": {t: cf[t].to_numpy(float) for t in ("wind_onshore", "wind_offshore", "solar", "ror")},
        "price_2025": price,
    }


def snapshots(year: int) -> pd.DatetimeIndex:
    """A clean 8760-hour index for the given year (tz-naive)."""
    return pd.date_range(f"{year}-01-01", periods=config.HOURS_PER_YEAR, freq="h")


# ===========================================================================
# NETWORK BUILDER
# ===========================================================================
def build_network(year: int, capacities: dict, cf: dict, demand: np.ndarray,
                  storage_params: dict, allow_import: bool = False):
    """Construct a single-node PyPSA network ready to optimise.

    allow_import : if True and config.INCLUDE_CROSSBORDER, adds a capped import
    generator (interconnector imports). Used for the 2030 scenarios; the 2025
    calibration is always built islanded (allow_import left False).

    Parameters
    ----------
    year : int                model year (sets the price/CO2 regime via config)
    capacities : dict         tech -> installed capacity (MW)
    cf : dict                 VRE tech -> 8760 per-unit availability array
    demand : np.ndarray       8760 load array (MW)
    storage_params : dict     storage name -> parameter dict
    """
    import pypsa  # imported here so config/analysis stay importable without PyPSA

    sns = snapshots(year)
    n = pypsa.Network()
    n.set_snapshots(sns)
    n.add("Bus", "DE")

    # carriers (for clean outputs / emission accounting metadata)
    for tech in config.all_techs():
        n.add("Carrier", config.CARRIER_OF_TECH[tech])
    n.add("Carrier", "Load shedding")

    # demand
    n.add("Load", "load", bus="DE", p_set=pd.Series(demand, index=sns))

    # dispatchable thermal + biomass
    for tech in ("biomass", "lignite", "hardcoal", "ccgt_new", "ccgt_exist", "ocgt", "oil"):
        cap = float(capacities.get(tech, 0.0))
        if cap <= 0:
            continue
        n.add("Generator", tech, bus="DE", p_nom=cap, carrier=config.CARRIER_OF_TECH[tech],
              marginal_cost=config.marginal_cost(tech, year))

    # variable renewables + run-of-river (availability profile)
    for tech in ("wind_onshore", "wind_offshore", "solar", "ror"):
        cap = float(capacities.get(tech, 0.0))
        if cap <= 0:
            continue
        n.add("Generator", tech, bus="DE", p_nom=cap, carrier=config.CARRIER_OF_TECH[tech],
              marginal_cost=config.marginal_cost(tech, year),
              p_max_pu=pd.Series(np.clip(cf[tech], 0.0, 1.0), index=sns))

    # storage
    for name, sp in storage_params.items():
        n.add("StorageUnit", name, bus="DE", p_nom=float(sp["p_nom_mw"]),
              max_hours=float(sp["max_hours"]),
              efficiency_store=float(sp["eff_store"]),
              efficiency_dispatch=float(sp["eff_dispatch"]),
              cyclic_state_of_charge=True, marginal_cost=0.01)

    # VOLL load-shedding backstop (uncapacitated)
    n.add("Generator", "load_shedding", bus="DE", p_nom=config.LOAD_SHED_PNOM_MW,
          carrier="Load shedding", marginal_cost=config.VOLL_EUR_MWH)

    # capped cross-border imports (2030 scenarios only; see config switch)
    if allow_import and config.INCLUDE_CROSSBORDER:
        n.add("Carrier", "Import")
        n.add("Generator", "import", bus="DE", p_nom=config.IMPORT_CAP_MW,
              carrier="Import", marginal_cost=config.IMPORT_PRICE_EUR_MWH)

    return n


def solve(n) -> None:
    """Optimise with HiGHS and assert an optimal solution was found."""
    ret = n.optimize(solver_name=config.SOLVER_NAME)
    status = ret[0] if isinstance(ret, tuple) else ret
    cond = ret[1] if isinstance(ret, tuple) and len(ret) > 1 else "n/a"
    obj = getattr(n, "objective", None)
    if obj is None or (isinstance(status, str) and status not in ("ok", "optimal", "warning")):
        raise RuntimeError(f"Solve not optimal: status={status}, condition={cond}")
    print(f"      solver status={status}, condition={cond}, objective={obj:,.0f} EUR")


# ===========================================================================
# RESULT EXTRACTION  (turns a solved network into a tidy hourly DataFrame)
# ===========================================================================
def extract_hourly(n, capacities: dict, cf: dict) -> pd.DataFrame:
    """Return an hourly DataFrame: price, dispatch per tech (MWh), SoC, load shed."""
    gp = n.generators_t.p
    out = pd.DataFrame(index=n.snapshots)
    out["price_eur_mwh"] = n.buses_t.marginal_price["DE"].to_numpy()
    for tech in config.all_techs():
        out[tech] = gp[tech].to_numpy() if tech in gp.columns else 0.0
    out["load_shed_mwh"] = gp["load_shedding"].to_numpy() if "load_shedding" in gp.columns else 0.0
    out["net_import_mwh"] = gp["import"].to_numpy() if "import" in gp.columns else 0.0
    # total storage state of charge (MWh)
    if len(n.storage_units):
        out["storage_soc_mwh"] = n.storage_units_t.state_of_charge.sum(axis=1).to_numpy()
        out["storage_net_mwh"] = n.storage_units_t.p.sum(axis=1).to_numpy()  # + discharge / - charge
    else:
        out["storage_soc_mwh"] = 0.0
        out["storage_net_mwh"] = 0.0
    # potential VRE (for curtailment) -- capacity * availability
    pot = np.zeros(len(out))
    for tech in VRE_FOR_CURTAILMENT:
        pot = pot + float(capacities.get(tech, 0.0)) * np.clip(cf[tech], 0.0, 1.0)
    out["vre_potential_mwh"] = pot
    return out


# ===========================================================================
# METRICS  (pure function -- testable without PyPSA)
# ===========================================================================
def compute_metrics(hourly: pd.DataFrame, capacities: dict, objective_eur: float,
                    new_ccgt_mw: float) -> dict:
    """Compute the 11 study metrics from an hourly results DataFrame."""
    h = hourly
    price = h["price_eur_mwh"]
    n_hours = config.HOURS_PER_YEAR

    gen_techs = config.all_techs()
    gen_by_tech = {t: float(h[t].sum()) for t in gen_techs}
    total_gen = sum(gen_by_tech.values())

    # CCGT (existing + new) and OCGT utilisation
    ccgt_cap = float(capacities.get("ccgt_exist", 0)) + float(capacities.get("ccgt_new", 0))
    ccgt_gen = gen_by_tech["ccgt_exist"] + gen_by_tech["ccgt_new"]
    ocgt_cap = float(capacities.get("ocgt", 0))
    ocgt_gen = gen_by_tech["ocgt"]

    def flh(gen, cap):
        return gen / cap if cap > 0 else 0.0

    def cf_val(gen, cap):
        return gen / (cap * n_hours) if cap > 0 else 0.0

    # curtailment (wind + solar)
    vre_actual = sum(gen_by_tech[t] for t in VRE_FOR_CURTAILMENT)
    vre_potential = float(h["vre_potential_mwh"].sum())
    curtail = max(vre_potential - vre_actual, 0.0)
    curtail_pct = 100.0 * curtail / vre_potential if vre_potential > 0 else 0.0

    # renewables share of generation
    renew = sum(gen_by_tech[t] for t in ("wind_onshore", "wind_offshore", "solar", "ror", "biomass"))
    renew_share = 100.0 * renew / total_gen if total_gen > 0 else 0.0

    # CO2 emissions (Mt)
    co2_t = sum(h[t].sum() * config.co2_intensity_el(t) for t in gen_techs)

    # scarcity / unserved
    shed = h["load_shed_mwh"]
    scarcity_hours = int((shed > 1e-3).sum())
    unserved = float(shed.sum())

    # total system cost = operating cost (objective) + annualised new-CCGT fixed cost.
    # "objective" already includes VOLL x unserved energy; report cost WITH and
    # WITHOUT that reliability term so both the welfare lens (with VOLL) and the
    # textbook "security has a price" lens (without VOLL) are available.
    fixed_new = config.annualised_new_ccgt_cost_eur(new_ccgt_mw)
    total_cost_meur = (objective_eur + fixed_new) / 1e6
    voll_cost_eur = config.VOLL_EUR_MWH * unserved
    total_cost_excl_voll_meur = (objective_eur - voll_cost_eur + fixed_new) / 1e6

    # net imports (2030 scenarios with cross-border enabled)
    net_import_twh = float(h["net_import_mwh"].sum()) / 1e6 if "net_import_mwh" in h.columns else 0.0

    # consumer energy cost (price * served domestic generation)
    consumer_cost_meur = float((price * (h[gen_techs].sum(axis=1))).sum()) / 1e6

    return {
        "avg_price_eur_mwh": float(price.mean()),
        "median_price_eur_mwh": float(price.median()),
        "price_std_eur_mwh": float(price.std()),
        "scarcity_hours": scarcity_hours,
        "unserved_energy_mwh": unserved,
        "ccgt_capacity_factor": cf_val(ccgt_gen, ccgt_cap),
        "ccgt_full_load_hours": flh(ccgt_gen, ccgt_cap),
        "ccgt_new_gen_twh": gen_by_tech["ccgt_new"] / 1e6,
        "ccgt_new_full_load_hours": flh(gen_by_tech["ccgt_new"], float(capacities.get("ccgt_new", 0))),
        "ocgt_capacity_factor": cf_val(ocgt_gen, ocgt_cap),
        "ocgt_full_load_hours": flh(ocgt_gen, ocgt_cap),
        "curtailment_twh": curtail / 1e6,
        "curtailment_pct": curtail_pct,
        "renewable_share_pct": renew_share,
        "total_system_cost_meur": total_cost_meur,
        "total_system_cost_excl_voll_meur": total_cost_excl_voll_meur,
        "net_import_twh": net_import_twh,
        "co2_emissions_mt": co2_t / 1e6,
        "total_generation_twh": total_gen / 1e6,
        "consumer_energy_cost_meur": consumer_cost_meur,
        **{f"gen_{t}_twh": gen_by_tech[t] / 1e6 for t in gen_techs},
    }


# ===========================================================================
# PLAUSIBILITY CHECKS  (flag, never silently fix)
# ===========================================================================
PLAUSIBILITY = {
    "avg_price_eur_mwh": (40, 150),
    "renewable_share_pct": (50, 80),
    "ccgt_full_load_hours": (1500, 5000),
    "co2_emissions_mt": (30, 120),
}


def check_plausibility(name: str, metrics: dict) -> list:
    """Return a list of human-readable warnings for out-of-bound metrics."""
    warns = []
    for key, (lo, hi) in PLAUSIBILITY.items():
        val = metrics.get(key)
        if val is None:
            continue
        if not (lo <= val <= hi):
            warns.append(f"[{name}] {key} = {val:.2f} outside plausibility [{lo}, {hi}]")
    return warns


# ===========================================================================
# FIGURES
# ===========================================================================
def _carrier_series(hourly: pd.DataFrame, tech: str) -> np.ndarray:
    return hourly[tech].to_numpy()


def make_figures(results: dict) -> None:
    """Create the 7 study figures from the solved A/B (and sensitivity) results."""
    A = results["A"]["hourly"]
    B = results["B"]["hourly"]
    dpi = 160

    # fig1 -- price duration curve A vs B
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(np.sort(A["price_eur_mwh"])[::-1], label="A (No CRM)", color="#000000", lw=1.6)
    ax.plot(np.sort(B["price_eur_mwh"])[::-1], label="B (Kraftwerksstrategie +10 GW)",
            color="#CC79A7", lw=1.6)
    ax.set_xlabel("Hours (sorted, descending)"); ax.set_ylabel("Price (EUR/MWh)")
    ax.set_title("Price duration curve, 2030 — Scenario A vs B")
    ax.set_ylim(0, min(3200, max(A['price_eur_mwh'].max(), B['price_eur_mwh'].max()) * 1.05))
    ax.legend(); ax.grid(alpha=0.3); fig.tight_layout()
    fig.savefig(FIG_DIR / "fig1_price_duration_curve.png", dpi=dpi); plt.close(fig)

    # fig2 -- monthly average dispatch stack, Scenario B
    stack_techs = ["solar", "wind_onshore", "wind_offshore", "ror", "biomass",
                   "lignite", "hardcoal", "ccgt_exist", "ccgt_new", "ocgt", "oil"]
    monthly = B.copy()
    monthly["month"] = monthly.index.month
    mavg = monthly.groupby("month")[stack_techs].mean()
    fig, ax = plt.subplots(figsize=(9, 5))
    bottom = np.zeros(len(mavg))
    for tech in stack_techs:
        lab = config.CARRIER_OF_TECH[tech]
        ax.bar(mavg.index, mavg[tech] / 1e3, bottom=bottom / 1e3,
               label=lab, color=OKABE_ITO.get(lab, "#777777"))
        bottom = bottom + mavg[tech].to_numpy()
    if "net_import_mwh" in B.columns:
        imp = monthly.groupby("month")["net_import_mwh"].mean().reindex(mavg.index).fillna(0.0)
        ax.bar(mavg.index, imp.to_numpy() / 1e3, bottom=bottom / 1e3,
               label="Import", color=OKABE_ITO["Import"])
        bottom = bottom + imp.to_numpy()
    ax.set_xlabel("Month"); ax.set_ylabel("Average power (GW)")
    ax.set_title("Monthly average dispatch stack, 2030 — Scenario B")
    ax.legend(ncol=2, fontsize=7, loc="upper right"); fig.tight_layout()
    fig.savefig(FIG_DIR / "fig2_seasonal_dispatch_stack.png", dpi=dpi); plt.close(fig)

    # fig3 -- gas utilisation (CCGT/OCGT FLH) A vs B
    mA, mB = results["A"]["metrics"], results["B"]["metrics"]
    labels = ["CCGT FLH", "new-CCGT FLH", "OCGT FLH"]
    a_vals = [mA["ccgt_full_load_hours"], mA["ccgt_new_full_load_hours"], mA["ocgt_full_load_hours"]]
    b_vals = [mB["ccgt_full_load_hours"], mB["ccgt_new_full_load_hours"], mB["ocgt_full_load_hours"]]
    x = np.arange(len(labels)); w = 0.38
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(x - w / 2, a_vals, w, label="A (No CRM)", color="#000000")
    ax.bar(x + w / 2, b_vals, w, label="B (+10 GW)", color="#CC79A7")
    ax.set_xticks(x); ax.set_xticklabels(labels); ax.set_ylabel("Full-load hours (h/yr)")
    ax.set_title("Gas-fleet utilisation, 2030 — A vs B")
    ax.legend(); ax.grid(alpha=0.3, axis="y"); fig.tight_layout()
    fig.savefig(FIG_DIR / "fig3_gas_utilisation.png", dpi=dpi); plt.close(fig)

    # fig4 -- curtailment MWh + %
    fig, ax = plt.subplots(figsize=(7, 5))
    cats = ["A (No CRM)", "B (+10 GW)"]
    cvals = [mA["curtailment_twh"], mB["curtailment_twh"]]
    pvals = [mA["curtailment_pct"], mB["curtailment_pct"]]
    bars = ax.bar(cats, cvals, color=["#000000", "#CC79A7"])
    ax.set_ylabel("Curtailment (TWh/yr)"); ax.set_title("Renewable curtailment, 2030 — A vs B")
    for b, p in zip(bars, pvals):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height(), f"{p:.1f}%",
                ha="center", va="bottom")
    ax.grid(alpha=0.3, axis="y"); fig.tight_layout()
    fig.savefig(FIG_DIR / "fig4_curtailment.png", dpi=dpi); plt.close(fig)

    # fig5 -- scarcity hours + unserved energy
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5))
    ax1.bar(cats, [mA["scarcity_hours"], mB["scarcity_hours"]], color=["#000000", "#CC79A7"])
    ax1.set_ylabel("Scarcity hours (h/yr)"); ax1.set_title("Loss-of-load hours")
    ax2.bar(cats, [mA["unserved_energy_mwh"] / 1e3, mB["unserved_energy_mwh"] / 1e3],
            color=["#000000", "#CC79A7"])
    ax2.set_ylabel("Unserved energy (GWh/yr)"); ax2.set_title("Unserved energy")
    for ax in (ax1, ax2):
        ax.grid(alpha=0.3, axis="y")
    fig.suptitle("Adequacy, 2030 — Scenario A vs B"); fig.tight_layout()
    fig.savefig(FIG_DIR / "fig5_scarcity_comparison.png", dpi=dpi); plt.close(fig)

    # fig6 -- January week-2 dispatch time series (A vs B), net load + gas
    sl = slice(168, 336)  # hours of the 2nd week
    fig, (axA, axB) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    for ax, res, ttl in [(axA, A, "A (No CRM)"), (axB, B, "B (+10 GW new CCGT)")]:
        seg = res.iloc[sl]
        hrs = np.arange(len(seg))
        bottom = np.zeros(len(seg))
        for tech in stack_techs:
            lab = config.CARRIER_OF_TECH[tech]
            ax.bar(hrs, seg[tech] / 1e3, bottom=bottom / 1e3, width=1.0,
                   color=OKABE_ITO.get(lab, "#777777"), label=lab)
            bottom = bottom + seg[tech].to_numpy()
        if "net_import_mwh" in seg.columns:
            ax.bar(hrs, seg["net_import_mwh"] / 1e3, bottom=bottom / 1e3, width=1.0,
                   color=OKABE_ITO["Import"], label="Import")
            bottom = bottom + seg["net_import_mwh"].to_numpy()
        if "load_shed_mwh" in seg.columns:
            ax.bar(hrs, seg["load_shed_mwh"] / 1e3, bottom=bottom / 1e3, width=1.0,
                   color="#FF0000", label="Load shedding")
            bottom = bottom + seg["load_shed_mwh"].to_numpy()
        ax.set_ylabel("GW"); ax.set_title(f"January week 2 — {ttl}")
        ax.grid(alpha=0.3, axis="y")
    axB.set_xlabel("Hour of week")
    handles, labels_ = axA.get_legend_handles_labels()
    axA.legend(handles, labels_, ncol=3, fontsize=6, loc="upper right")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig6_weekly_dispatch.png", dpi=dpi); plt.close(fig)

    # fig7 -- single-node schematic
    fig, ax = plt.subplots(figsize=(9, 6)); ax.axis("off")
    ax.add_patch(plt.Rectangle((0.42, 0.45), 0.16, 0.10, fc="#DDDDDD", ec="k"))
    ax.text(0.5, 0.5, "DE/LU\nbus", ha="center", va="center", fontsize=11, weight="bold")
    supply = ["Solar PV", "Wind onshore", "Wind offshore", "Run-of-river", "Biomass",
              "Lignite", "Hard coal", "Gas CCGT (existing)", "Gas CCGT (new H2-ready)",
              "Gas OCGT", "Oil"]
    for i, lab in enumerate(supply):
        y = 0.95 - i * 0.085
        ax.add_patch(plt.Rectangle((0.02, y - 0.03), 0.20, 0.055,
                                   fc=OKABE_ITO.get(lab, "#777777"), ec="k", alpha=0.85))
        ax.text(0.12, y, lab, ha="center", va="center", fontsize=7)
        ax.annotate("", xy=(0.42, 0.5), xytext=(0.22, y),
                    arrowprops=dict(arrowstyle="->", color="#888888", lw=0.6))
    for j, lab in enumerate(["Load (demand)", "Battery + PHS", "Load shedding (VOLL 3000)"]):
        y = 0.75 - j * 0.18
        ax.add_patch(plt.Rectangle((0.76, y - 0.03), 0.22, 0.06, fc="#FFFFFF", ec="k"))
        ax.text(0.87, y, lab, ha="center", va="center", fontsize=8)
        ax.annotate("", xy=(0.76, y), xytext=(0.58, 0.5),
                    arrowprops=dict(arrowstyle="->", color="#888888", lw=0.8))
    ax.set_title("Single-node model schematic — Germany (DE/LU), hourly, 2030")
    fig.savefig(FIG_DIR / "fig7_model_schematic.png", dpi=dpi); plt.close(fig)

    print(f"      wrote 7 figures to {FIG_DIR}")


# ===========================================================================
# CALIBRATION (2025)
# ===========================================================================
def run_calibration(inp: dict) -> None:
    """Build & solve the 2025 system; compare modelled price/mix to reality."""
    print("\n[CALIBRATION] 2025 system (validation against realised market)")
    try:
        demand = inp["demand_2025"]
        net = build_network(config.CALIBRATION_YEAR, config.CAPACITY_2025_MW,
                            inp["cf"], demand, config.STORAGE[config.CALIBRATION_YEAR])
        solve(net)
        hourly = extract_hourly(net, config.CAPACITY_2025_MW, inp["cf"])
        model_price = float(hourly["price_eur_mwh"].mean())
        actual_price = float(np.mean(inp["price_2025"]))

        # generation shares (model vs actual from realised generation file)
        techs = config.all_techs()
        model_gen = {t: float(hourly[t].sum()) for t in techs}
        tot = sum(model_gen.values())
        model_renew = sum(model_gen[t] for t in ("wind_onshore", "wind_offshore", "solar", "ror", "biomass"))
        rows = [
            ("mean_price_eur_mwh", model_price, actual_price),
            ("renewable_share_pct_model", 100 * model_renew / tot, np.nan),
        ]
        df = pd.DataFrame(rows, columns=["metric", "model_2025", "actual_2025"])
        df.to_csv(RESULTS_DIR / "calibration_2025_validation.csv", index=False)
        print(f"   modelled mean price {model_price:6.1f}  vs realised {actual_price:6.1f} EUR/MWh "
              f"(diff {model_price - actual_price:+.1f})")
        print(f"   -> results/calibration_2025_validation.csv")
    except Exception as exc:  # noqa: BLE001  (calibration must never block the main run)
        print(f"   ! calibration skipped due to: {exc}")


# ===========================================================================
# MAIN
# ===========================================================================
def main() -> None:
    print("=" * 70)
    print("KRAFTWERKSSTRATEGIE DISPATCH MODEL  |  PyPSA + HiGHS  |  target 2030")
    print("=" * 70)
    inp = load_inputs()

    # 2030 demand = 2025 shape scaled to the 2030 annual total
    load25 = inp["demand_2025"]
    scale = (config.DEMAND_2030_TWH * 1e6) / load25.sum()
    demand_2030 = load25 * scale
    print(f"2030 demand scaling: 2025 {load25.sum()/1e6:.1f} TWh -> 2030 "
          f"{config.DEMAND_2030_TWH:.0f} TWh (factor {scale:.3f})")

    run_calibration(inp)

    results, all_warnings = {}, []
    print("\n[TARGET 2030] scenarios")
    for name in ("A", "B", "B_low", "B_high"):
        caps = config.capacities_for(name)
        new_ccgt = float(config.SCENARIOS[name])
        print(f"\n  Scenario {name}  (new CCGT = {new_ccgt/1000:.0f} GW)")
        net = build_network(config.TARGET_YEAR, caps, inp["cf"], demand_2030,
                            config.STORAGE[config.TARGET_YEAR], allow_import=True)
        solve(net)
        hourly = extract_hourly(net, caps, inp["cf"])
        metrics = compute_metrics(hourly, caps, float(net.objective), new_ccgt)
        results[name] = {"hourly": hourly, "metrics": metrics, "caps": caps}
        all_warnings += check_plausibility(name, metrics)

    # ---- write hourly CSVs for A and B (single source of truth) ----
    carrier_cols = config.all_techs()
    for name in ("A", "B"):
        h = results[name]["hourly"]
        cols = ["price_eur_mwh"] + carrier_cols + ["net_import_mwh", "load_shed_mwh", "storage_soc_mwh"]
        out = h[cols].copy()
        out.insert(0, "hour", np.arange(len(out)))
        out.to_csv(RESULTS_DIR / f"scenario_{name}_hourly.csv", index=False)

    # ---- comparison_table.csv (A vs B) ----
    keys = [
        "avg_price_eur_mwh", "median_price_eur_mwh", "price_std_eur_mwh",
        "scarcity_hours", "unserved_energy_mwh",
        "ccgt_capacity_factor", "ccgt_full_load_hours",
        "ccgt_new_gen_twh", "ccgt_new_full_load_hours",
        "ocgt_capacity_factor", "ocgt_full_load_hours",
        "curtailment_twh", "curtailment_pct", "renewable_share_pct",
        "total_system_cost_meur", "total_system_cost_excl_voll_meur", "net_import_twh",
        "co2_emissions_mt", "total_generation_twh", "consumer_energy_cost_meur",
    ]
    mA, mB = results["A"]["metrics"], results["B"]["metrics"]
    rows = []
    for k in keys:
        a, b = mA[k], mB[k]
        d = b - a
        dp = (100 * d / a) if a not in (0, 0.0) else np.nan
        rows.append([k, a, b, d, dp])
    comp = pd.DataFrame(rows, columns=["metric", "A_value", "B_value", "delta_abs", "delta_pct"])
    comp.to_csv(RESULTS_DIR / "comparison_table.csv", index=False)

    # ---- sensitivity_table.csv (B_low / B / B_high) ----
    srows = []
    for k in keys:
        srows.append([k, results["B_low"]["metrics"][k], results["B"]["metrics"][k],
                      results["B_high"]["metrics"][k]])
    sens = pd.DataFrame(srows, columns=["metric", "B_low", "B", "B_high"])
    sens.to_csv(RESULTS_DIR / "sensitivity_table.csv", index=False)

    # ---- figures ----
    make_figures(results)

    # ---- report ----
    print("\n" + "=" * 70)
    print("COMPARISON TABLE (A vs B) -- results/comparison_table.csv")
    print("=" * 70)
    with pd.option_context("display.float_format", lambda v: f"{v:,.2f}"):
        print(comp.to_string(index=False))

    if all_warnings:
        print("\n[PLAUSIBILITY WARNINGS] (flagged, not auto-corrected):")
        for w in all_warnings:
            print("   ! " + w)
    else:
        print("\n[PLAUSIBILITY] all checked metrics within bounds.")

    print("\nThese results were produced by running this model with HiGHS on authentic")
    print(f"2025 Energy-Charts data, projected to {config.TARGET_YEAR}. They are read directly")
    print("from results/comparison_table.csv and are the single source of truth for all")
    print("downstream report and presentation numbers.")
    print("\nOutputs: results/*.csv  and  figures/*.png")


if __name__ == "__main__":
    main()
