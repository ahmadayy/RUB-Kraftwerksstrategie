"""
config.py
=========
Central configuration for the PyPSA dispatch model evaluating Germany's
*Kraftwerksstrategie* (capacity remuneration mechanism).

Two-layer study design
-----------------------
* Calibration / weather year .... 2025  (authentic hourly data, validates the model)
* Target / policy year .......... 2030  (projected fleet, the actual experiment)

Scenarios (all at TARGET 2030)
------------------------------
* A      -- Baseline, NO CRM           : 2030 fleet, gas = existing fleet only
* B      -- Kraftwerksstrategie (CANON) : A + 10 GW new H2-ready CCGT
* B_low  -- sensitivity                 : A +  5 GW new CCGT
* B_high -- sensitivity                 : A + 20 GW new CCGT

ALL numeric parameters live in this file.  model.py imports them and contains
no hard-coded numbers (zero-hardcoding rule).  Every value carries a source tag
in the comment; values still to be locked against a primary table are marked
[VERIFY].  Nothing here is a model *result* -- results are produced only by
running model.py.

Author: RUB group project  |  generated for local execution
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# 0. GENERAL
# ---------------------------------------------------------------------------
COUNTRY = "de"                 # Energy-Charts country code (Germany)
BIDDING_ZONE = "DE-LU"         # ENTSO-E / Energy-Charts day-ahead price zone
CALIBRATION_YEAR = 2025        # authentic weather + demand year
TARGET_YEAR = 2030             # policy evaluation year
HOURS_PER_YEAR = 8760          # 2025 and 2030 are both non-leap (8760 h)

# ---------------------------------------------------------------------------
# 1. COMMODITY PRICES  (per thermal MWh and per tonne CO2)
#    2025 = realised market averages; 2030 = official-scenario assumptions.
#    Lock 2030 values against the NEP Szenariorahmen 2025 commodity annex /
#    BMWE Langfristszenarien in a final pass.                       [VERIFY]
# ---------------------------------------------------------------------------
CO2_PRICE_EUR_T = {                 # EUA price, EUR / t CO2
    2025: 75.0,                     # EEX/ICAP realised 2025 avg            [VERIFY]
    2030: 110.0,                    # NEP/Langfristszenarien 2030 assumption [VERIFY]
}

FUEL_PRICE_EUR_MWH_TH = {           # fuel cost, EUR / MWh_thermal (LHV)
    2025: {"gas": 35.0, "hardcoal": 11.0, "lignite": 3.5, "oil": 40.0, "biomass": 25.0},
    2030: {"gas": 30.0, "hardcoal": 11.0, "lignite": 3.5, "oil": 40.0, "biomass": 25.0},
}
#   gas 2025 ~ TTF realised; 2030 ~ scenario       [VERIFY: EEX / NEP annex]
#   hardcoal ~ API2; lignite domestic (~untraded); biomass ~ DEA/Fraunhofer

# ---------------------------------------------------------------------------
# 2. CO2 EMISSION INTENSITY per fuel  (t CO2 / MWh_thermal)
#    Source: Umweltbundesamt, "CO2 Emission Factors for Fossil Fuels,
#    Update 2022" (CC 29/2022).  Biomass treated as zero under the EU ETS.
# ---------------------------------------------------------------------------
CO2_INTENSITY_T_MWH_TH = {
    "gas": 0.201,
    "hardcoal": 0.337,
    "lignite": 0.364,
    "oil": 0.267,
    "biomass": 0.0,
}

# ---------------------------------------------------------------------------
# 3. TECHNOLOGY PARAMETERS
#    Efficiency (net, LHV) and variable O&M.
#    Source: Danish Energy Agency Technology Catalogue (via PyPSA
#    technology-data); Fraunhofer ISE cross-check.                  [VERIFY]
# ---------------------------------------------------------------------------
EFFICIENCY = {          # net electrical efficiency (fraction, LHV)
    "ccgt_new": 0.60,   # modern H2-ready CCGT (Kraftwerksstrategie build)
    "ccgt_exist": 0.52, # existing combined-cycle fleet
    "ocgt": 0.40,       # existing open-cycle / peakers
    "hardcoal": 0.43,
    "lignite": 0.38,
    "oil": 0.38,
    "biomass": 0.35,
}

VOM_EUR_MWH = {         # variable O&M, EUR / MWh_electrical
    "ccgt_new": 4.0, "ccgt_exist": 4.0, "ocgt": 3.0,
    "hardcoal": 3.6, "lignite": 3.3, "oil": 3.0, "biomass": 4.0,
    "wind_onshore": 1.3, "wind_offshore": 3.0, "solar": 0.0, "ror": 0.5,
}

# Which fuel each combustion technology burns (for marginal-cost build-up)
FUEL_OF_TECH = {
    "ccgt_new": "gas", "ccgt_exist": "gas", "ocgt": "gas",
    "hardcoal": "hardcoal", "lignite": "lignite", "oil": "oil",
    "biomass": "biomass",
}

# Variable-renewable + run-of-river technologies (price-taker, ~zero fuel)
VRE_TECHS = ("wind_onshore", "wind_offshore", "solar", "ror")

# Mapping technology -> carrier label used in outputs / figures
CARRIER_OF_TECH = {
    "lignite": "Lignite", "hardcoal": "Hard coal",
    "ccgt_exist": "Gas CCGT (existing)", "ccgt_new": "Gas CCGT (new H2-ready)",
    "ocgt": "Gas OCGT", "oil": "Oil", "biomass": "Biomass",
    "ror": "Run-of-river", "wind_onshore": "Wind onshore",
    "wind_offshore": "Wind offshore", "solar": "Solar PV",
}

# ---------------------------------------------------------------------------
# 4. INSTALLED CAPACITY  (MW)
#    2025 calibration fleet  -- realised (BNetzA / ENTSO-E end-2024/2025) [VERIFY]
#    2030 baseline fleet     -- EEG-2023 RE targets, KVBG coal ceiling,
#                               existing gas carried forward (no-strategy).
# ---------------------------------------------------------------------------
CAPACITY_2025_MW = {
    "lignite": 15000, "hardcoal": 13000,
    "ccgt_exist": 20000, "ocgt": 14000, "oil": 4000,
    "biomass": 9000, "ror": 5000,
    "wind_onshore": 63000, "wind_offshore": 9200, "solar": 100000,
    "ccgt_new": 0,
}

CAPACITY_2030_BASE_MW = {
    # Coal: KVBG 2030 statutory ceiling (8 GW hard coal + 9 GW lignite)
    "lignite": 9000, "hardcoal": 8000,
    # Existing gas carried forward (Scenario-A "no-strategy" counterfactual)
    "ccgt_exist": 20000, "ocgt": 14000, "oil": 1500,
    "biomass": 8000, "ror": 5000,
    # Renewables: EEG-2023 / NEP Szenariorahmen 2025 (Scenario B) 2030 targets
    "wind_onshore": 115000, "wind_offshore": 30000, "solar": 215000,
    # New H2-ready CCGT added per scenario (see SCENARIOS)
    "ccgt_new": 0,
}

# Capacity factor reference -- annual-average installed capacity used by
# data_loader.py to convert 2025 generation [MW] into a per-unit CF profile.
# (Profiles are then re-scaled by the 2030 capacities above.)
CF_REFERENCE_CAPACITY_2025_MW = {
    "wind_onshore": 63000, "wind_offshore": 9200, "solar": 100000, "ror": 5000,
}

# ---------------------------------------------------------------------------
# 5. STORAGE  (StorageUnit parameters)
#    PHS ~ 9.4 GW (BNetzA); battery 2030 ~ NEP flexibility build-out  [VERIFY]
# ---------------------------------------------------------------------------
STORAGE = {
    2025: {
        "PHS":     {"p_nom_mw": 9400, "max_hours": 6.0, "eff_store": 0.87, "eff_dispatch": 0.87},
        "Battery": {"p_nom_mw": 2000, "max_hours": 2.0, "eff_store": 0.96, "eff_dispatch": 0.96},
    },
    2030: {
        "PHS":     {"p_nom_mw": 9400,  "max_hours": 6.0, "eff_store": 0.87, "eff_dispatch": 0.87},
        "Battery": {"p_nom_mw": 25000, "max_hours": 2.0, "eff_store": 0.96, "eff_dispatch": 0.96},
    },
}

# ---------------------------------------------------------------------------
# 6. DEMAND
#    2025 demand comes from the authentic load series (data_loader).
#    2030 gross demand -- NEP Szenariorahmen 2025 (Scn B) central value;
#    EEG planning value 750 TWh, Prognos 658 TWh bracket it.          [VERIFY]
# ---------------------------------------------------------------------------
DEMAND_2030_TWH = 680.0          # gross electricity demand, TWh/yr   [VERIFY]

# ---------------------------------------------------------------------------
# 7. SCARCITY / RELIABILITY
# ---------------------------------------------------------------------------
VOLL_EUR_MWH = 3000.0            # value of lost load (ACER/ENTSO-E ERAA convention)
LOAD_SHED_PNOM_MW = 200000.0     # uncapacitated backstop generator size

# ---------------------------------------------------------------------------
# 7b. CAPACITY-COST ECONOMICS for the NEW CCGT (for total-system-cost metric)
#     CAPEX/FOM: Danish Energy Agency Technology Catalogue (CCGT).  [VERIFY]
#     Used to annualise the policy's added capacity cost so Scenario B's
#     total system cost includes building the new plants.
# ---------------------------------------------------------------------------
ECON_NEW_CCGT = {
    "capex_eur_per_kw": 900.0,     # overnight investment
    "fom_eur_per_kw_yr": 20.0,     # fixed O&M
    "lifetime_yr": 30,
}
DISCOUNT_RATE = 0.05               # for the capital recovery factor


def capital_recovery_factor(rate: float, life: int) -> float:
    """Annuity factor: rate / (1 - (1+rate)^-life)."""
    return rate / (1.0 - (1.0 + rate) ** (-life))


def annualised_new_ccgt_cost_eur(p_nom_mw: float) -> float:
    """Annualised CAPEX + FOM of new CCGT capacity (EUR/yr)."""
    crf = capital_recovery_factor(DISCOUNT_RATE, ECON_NEW_CCGT["lifetime_yr"])
    p_nom_kw = p_nom_mw * 1000.0
    return (crf * ECON_NEW_CCGT["capex_eur_per_kw"]
            + ECON_NEW_CCGT["fom_eur_per_kw_yr"]) * p_nom_kw


# ---------------------------------------------------------------------------
# 8. SCENARIO DEFINITION  -- new H2-ready CCGT added in 2030 (MW)
# ---------------------------------------------------------------------------
SCENARIOS = {
    "A":      0,        # No CRM (counterfactual)
    "B":      10000,    # Kraftwerksstrategie -- canonical (10 GW long-run tranche)
    "B_low":  5000,     # sensitivity
    "B_high": 20000,    # sensitivity
}
CANONICAL_SCENARIO = "B"
MAIN_SCENARIOS = ("A", "B")           # used in main figures / comparison_table
SENSITIVITY_SCENARIOS = ("B_low", "B", "B_high")

# ---------------------------------------------------------------------------
# 9. MODELLING SWITCHES
# ---------------------------------------------------------------------------
# Cross-border imports for the 2030 scenarios. True (default) adds a capped import
# option = interconnector imports from neighbours, which brings scarcity hours,
# unserved energy and the (VOLL-inflated) mean price toward real-world benchmarks
# while preserving the A->B effect. Set False for the conservative islanded
# sensitivity. The 2025 CALIBRATION always stays islanded (already validated,
# ~0.4% price error), so this switch only affects the 2030 runs.
INCLUDE_CROSSBORDER = True
IMPORT_CAP_MW = 20000.0          # available import capability (~German cross-border NTC, ENTSO-E)
IMPORT_PRICE_EUR_MWH = 150.0     # elevated neighbour price during German scarcity
                                 # (> domestic gas ~104; reflects correlated regional stress)
SOLVER_NAME = "highs"            # HiGHS via linopy

# ---------------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------------
def marginal_cost(tech: str, year: int) -> float:
    """Short-run marginal cost of a technology (EUR / MWh_electrical).

    MC = (fuel_price + CO2_intensity * CO2_price) / efficiency + VOM
    For VRE / run-of-river only the (near-zero) VOM applies.
    """
    if tech in VRE_TECHS:
        return VOM_EUR_MWH[tech]
    fuel = FUEL_OF_TECH[tech]
    eff = EFFICIENCY[tech]
    fuel_price = FUEL_PRICE_EUR_MWH_TH[year][fuel]
    co2_cost_th = CO2_INTENSITY_T_MWH_TH[fuel] * CO2_PRICE_EUR_T[year]
    return (fuel_price + co2_cost_th) / eff + VOM_EUR_MWH[tech]


def co2_intensity_el(tech: str) -> float:
    """CO2 emission intensity per MWh_electrical for a thermal technology."""
    if tech in VRE_TECHS:
        return 0.0
    fuel = FUEL_OF_TECH[tech]
    return CO2_INTENSITY_T_MWH_TH[fuel] / EFFICIENCY[tech]


def capacities_for(scenario: str) -> dict:
    """Return the 2030 capacity dict for a scenario (adds new CCGT)."""
    caps = dict(CAPACITY_2030_BASE_MW)
    caps["ccgt_new"] = float(SCENARIOS[scenario])
    return caps


def all_techs() -> list:
    """All generation technologies in model order (merit-order-ish)."""
    return [
        "wind_onshore", "wind_offshore", "solar", "ror", "biomass",
        "lignite", "hardcoal", "ccgt_new", "ccgt_exist", "ocgt", "oil",
    ]


if __name__ == "__main__":
    # Quick self-print of the implied 2030 merit order (sanity only).
    print("Implied marginal costs (EUR/MWh_el):")
    for yr in (CALIBRATION_YEAR, TARGET_YEAR):
        print(f"\n  Year {yr}:")
        rows = [(t, marginal_cost(t, yr), co2_intensity_el(t)) for t in all_techs()]
        for t, mc, ci in sorted(rows, key=lambda x: x[1]):
            print(f"    {t:16s} MC={mc:7.2f}   CO2_el={ci:5.3f} t/MWh")
