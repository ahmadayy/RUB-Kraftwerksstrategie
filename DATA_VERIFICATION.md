# DATA_VERIFICATION.md — Verification of `[VERIFY]` Model Inputs

**Purpose:** independently verify every `[VERIFY]`-tagged input in `config.py` against real, official
sources (web research, June 2026). Nothing here is fabricated; where a figure is a genuine *forward
assumption* (e.g. the 2030 CO₂ price) it is verified as *within published official scenarios* and the
range is given. Values that are legal targets or measured statistics are confirmed exactly.

**Verdict legend:** ✅ Confirmed (matches official/measured) · 🟡 Defensible assumption (within
published scenarios) · 🟠 At the edge of the range (consider noting/adjusting) · ⚪ Catalogue range
(exact source cell not retrievable online).

---

## A. 2030 fleet — renewable targets (legal, EEG 2023 / WindSeeG)

| Parameter | config value | Verified value | Verdict | Source |
|---|---|---|---|---|
| Solar PV 2030 | 215 GW | **215 GW** (EEG 2023 statutory target) | ✅ Confirmed | Bundesregierung; Open Energy Tracker |
| Onshore wind 2030 | 115 GW | **115 GW** (EEG 2023 statutory target) | ✅ Confirmed | Bundesregierung; Clean Energy Wire |
| Offshore wind 2030 | 30 GW | **≥30 GW by 2030** (WindSeeG; 40 GW by 2035, 70 GW by 2045) | ✅ Confirmed | German Offshore Wind Foundation; Norton Rose Fulbright |
| Renewables = 80% of demand 2030 | (context) | **80% target** (EEG 2023) | ✅ Confirmed | Bundesregierung |

## B. 2030 fleet — coal (Coal Phase-Out Act / KVBG)

| Parameter | config value | Verified value | Verdict | Source |
|---|---|---|---|---|
| Lignite 2030 | 9 GW | **~9 GW to remain by 2030** | ✅ Confirmed | Clean Energy Wire; Agora Energiewende |
| Hard coal 2030 | 8 GW | **8 GW to remain by 2030** | ✅ Confirmed | Clean Energy Wire; Agora Energiewende |

## C. 2025 calibration fleet (measured, end-2024/2025)

| Parameter | config value | Verified value | Verdict | Source |
|---|---|---|---|---|
| Solar PV 2025 | 100 GW | **99.3 GW end-2024** (BNetzA); ~100 GW early 2025 | ✅ Confirmed | Bundesnetzagentur via PV-Tech; BSW Solar |
| Onshore wind 2025 | 63 GW | **63.55 GW end-2024** | ✅ Confirmed | Fraunhofer ISE / Wind power in Germany |
| Offshore wind 2025 | 9.2 GW | **9.2 GW end-2024** | ✅ Confirmed | Fraunhofer ISE / Wind power in Germany |
| Lignite 2025 | 15 GW | **~15 GW remained end-2025** | ✅ Confirmed | Clean Energy Wire |
| Hard coal 2025 | 13 GW | **~13–15 GW end-2025** (more retired via auction) | 🟡 In range | Clean Energy Wire |
| Gas CCGT / OCGT 2025 | 20 / 14 GW | German gas fleet ~35 GW total; CCGT/OCGT split ~20/14 plausible | ⚪ Consistent, split not separately pinned | BNetzA fleet totals |

## D. Prices (2025 measured / 2030 assumed)

| Parameter | config value | Verified value | Verdict | Source |
|---|---|---|---|---|
| CO₂ (EUA) 2025 | 75 €/t | 2025 EUA traded **€60–80; ~€75 average** | ✅ Confirmed | Statista; Enerdata |
| CO₂ (EUA) 2030 | 110 €/t | Consensus **~€126/t** (range **€80–147**); BNEF €149 | 🟠 In range but below consensus | GMK Center consensus; BloombergNEF |
| Gas (TTF) 2025 | 35 €/MWh_th | 2025 TTF fell ~40% over the year; full-year avg ~€38–42, ending ~€30–35 | 🟡 Low end of range; corroborated by the 0.4% calibration | Trading Economics |
| Gas (TTF) 2030 | 30 €/MWh_th | Forward curve/scenarios ~€25–32 for 2030 | 🟡 Defensible forward assumption | Trading Economics futures |
| Hard-coal fuel | 11 €/MWh_th | ~API2 coal equivalent; in normal range | 🟡 Defensible | — |

## E. Demand 2030

| Parameter | config value | Verified value | Verdict | Source |
|---|---|---|---|---|
| Gross demand 2030 | 680 TWh | Official **realistic range 600–700 TWh**; median of projections ~**640 TWh**; EEG planning 750; Prognos 658 | 🟡 Central-high, inside official range | Enerdata (658); S&P Global (Reiche reality-check, 600–700, median ~640); BMWE (750) |

## F. Technology costs & efficiencies (Danish Energy Agency catalogue / PyPSA technology-data)

| Parameter | config value | Verified value | Verdict | Source |
|---|---|---|---|---|
| New CCGT CAPEX | 900 €/kW | DEA large CCGT ≈ **880–1,000 €/kW** (some entries 480–1,069) | 🟡 Within DEA range | Danish Energy Agency; PyPSA/technology-data |
| New CCGT efficiency | 60% | DEA CCGT ≈ **58–62%** | ✅ Within DEA range | Danish Energy Agency |
| New CCGT fixed O&M | 20 €/kW/yr | DEA CCGT FOM ≈ **~29 €/kW/yr** | 🟠 Slightly low | Danish Energy Agency |
| Efficiencies (OCGT 40%, hard coal 43%, lignite 38%) | — | DEA/literature: OCGT ~38–42%, hard coal ~43–46%, lignite ~38–43% | ✅ Within range | Danish Energy Agency |

## G. CO₂ emission intensities (Umweltbundesamt CC 29/2022)

| Fuel | config (t CO₂/MWh_th) | UBA standard factor | Verdict |
|---|---|---|---|
| Natural gas | 0.201 | ~0.20 | ✅ Confirmed |
| Hard coal | 0.337 | ~0.335–0.34 | ✅ Confirmed |
| Lignite | 0.364 | ~0.36–0.41 (type-dependent) | ✅ Confirmed (mid-range) |
| Oil | 0.267 | ~0.266–0.28 | ✅ Confirmed |

## H. Storage 2030

| Parameter | config value | Verified value | Verdict | Source |
|---|---|---|---|---|
| Pumped-hydro 2030 | 9.4 GW | ~9.4 GW (stable existing fleet) | ✅ Confirmed | BNetzA |
| Battery 2030 | 25 GW | NEP **central ~15 GW**, **high scenario ~25 GW** by 2030 | 🟠 = NEP *high* scenario (central is ~15 GW) | NEP 2037/2045; Renewables Now |

---

## Summary verdict

- **Confirmed exactly (legal targets / measured):** all 2030 renewable targets (215/115/30 GW), both
  2030 coal figures (9/8 GW), the 2025 solar/wind fleet (100/63/9.2 GW), the 2025 CO₂ price (€75),
  the CCGT efficiency (60%), and all four UBA CO₂ factors. **No problems.**
- **Defensible forward assumptions (within published ranges):** 2030 demand (680 TWh — inside the
  official 600–700 range), 2030 gas (€30), CCGT CAPEX (€900/kW). **Keep, with the source noted.**
- **Two values sit at the edge — worth a sentence in the report (or an optional re-run):**
  1. **CO₂ 2030 = €110/t** is *inside* the €80–147 forecast band but *below* the ~€126 consensus.
     It is therefore **conservative** (a higher CO₂ price would push coal out faster and *strengthen*
     the policy's CO₂ benefit). Optionally re-run at €120–126 for a central case.
  2. **Battery 2030 = 25 GW** corresponds to the NEP **high** scenario; the **central** estimate is
     ~15 GW. More storage slightly flatters flexibility. Optionally re-run at 15 GW (central).
- **Could not pin the exact catalogue cell online:** the precise DEA CCGT CAPEX/FOM numbers (the
  catalogue is a downloadable spreadsheet). The values used sit within the published DEA ranges; FOM
  (€20/kW/yr) is slightly below the DEA figure (~€29/kW/yr). **Not fabricated — flagged as catalogue-range.**

## Recommended action
All inputs are **defensible as they stand** — you can submit without changing the model. The only two
you might *optionally* revisit are the 2030 CO₂ price and the 2030 battery capacity; both are
honestly within published scenarios, and **changing either requires re-running the model** (the
results CSVs would change). If you want the central-case re-run (€126 CO₂, 15 GW battery), I can set
it up — but it is not required for the work to be correct.

---

## Sources
- Bundesregierung — Development of renewable energies (EEG 2023 targets): https://www.bundesregierung.de/breg-en/news/amendment-of-the-renewables-act-2060448
- Open Energy Tracker — Renewable electricity (Germany): https://openenergytracker.org/en/docs/germany/electricity/
- German Offshore Wind Foundation — Status quo (30 GW by 2030, WindSeeG): https://www.offshore-stiftung.de/en/status-quo-offshore-windenergy.php
- Norton Rose Fulbright — Global offshore wind: Germany: https://www.nortonrosefulbright.com/en/knowledge/publications/22341fc4/global-offshore-wind-germany
- Clean Energy Wire — Coal in Germany (8 GW hard coal + 9 GW lignite by 2030): https://www.cleanenergywire.org/factsheets/coal-germany
- Agora Energiewende — Germany's coal/gas phase-out: https://www.agora-energiewende.org/about-us/the-german-energiewende/what-are-germanys-nuclear-coal-and-fossil-gas-phase-out-strategies
- Fraunhofer ISE — Public Electricity Generation 2024 (fleet, 62.7% renewables): https://www.ise.fraunhofer.de/en/press-media/press-releases/2025/public-electricity-generation-2024-renewable-energies-cover-more-than-60-percent-of-german-electricity-consumption-for-the-first-time.html
- PV-Tech / Bundesnetzagentur — Germany 99.3 GW solar end-2024: https://www.pv-tech.org/germany-installed-16-2gw-solar-pv-in-2025/
- Enerdata — Germany electricity demand 658 TWh in 2030: https://www.enerdata.net/publications/daily-energy-news/germanys-electricity-forecast-reach-658-twh-2030.html
- S&P Global — Reiche "reality check" report (2030 demand 600–700 TWh, median ~640): https://www.spglobal.com/commodity-insights/en/news-research/latest-news/electric-power/091525-germanys-reiche-presents-reality-check-et-report-aimed-at-reducing-costs
- GMK Center — EU ETS consensus €126/t by 2030 (range €80–147): https://gmk.center/en/infographic/carbon-price-in-the-eu-ets-to-hit-e126-t-by-2030/
- BloombergNEF — EU ETS 2030 price forecast: https://about.bnef.com/insights/commodities/europes-new-emissions-trading-system-expected-to-have-worlds-highest-carbon-price-in-2030-at-e149-bloombergnef-forecast-reveals/
- Statista — EU ETS price 2025: https://www.statista.com/statistics/1322214/carbon-prices-european-union-emission-trading-scheme/
- Trading Economics — EU natural gas (TTF): https://tradingeconomics.com/commodity/eu-natural-gas
- Renewables Now — Germany 15 GW/57 GWh storage by 2030 (NEP central), 25 GW high: https://renewablesnow.com/news/germany-could-reach-15-gw57-gwh-of-storage-by-2030-846447/
- Danish Energy Agency — Technology Catalogues: https://ens.dk/en/analyses-and-statistics/technology-catalogues
- PyPSA/technology-data (DEA-derived cost database): https://github.com/PyPSA/technology-data
- Umweltbundesamt — CO₂ emission factors for fossil fuels, CC 29/2022 (already in report references)
