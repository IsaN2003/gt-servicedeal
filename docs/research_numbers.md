# Research: Public Numbers for the Simulation

Gathered 24 Nov 2026 from public sources. Every number is marked as either
**[Source]** (taken from a published source) or **[Assumption]** (my own
estimate, based on the sources, to be tested in sensitivity checks).

## 1. Turbine operating and maintenance cost

Reference unit: EIA's aeroderivative combustion turbine plant (105 MW).

| Item | Value | Type |
|---|---|---|
| Fixed O&M | $18.35 per kW per year (2022$) | [Source] EIA |
| Variable O&M | $5.29 per MWh (2022$) | [Source] EIA |
| Heat rate | 9,124 Btu/kWh | [Source] EIA |

**Estimated annual O&M for a 105 MW plant** [Assumption, derived from EIA figures]:
- Fixed part: 105,000 kW × $18.35 ≈ **$1.9M per year**
- Variable part: MWh generated × $5.29

| Duty cycle | Hours/year used | MWh/year | Variable O&M | Total O&M/year |
|---|---|---|---|---|
| Baseload | 7,500 | 787,500 | ≈ $4.2M | ≈ $6.1M |
| Mid-merit | 3,500 | 367,500 | ≈ $1.9M | ≈ $3.9M |
| Peaking | 1,000 | 105,000 | ≈ $0.6M | ≈ $2.5M |
| Industrial | 8,000 | 840,000 | ≈ $4.4M | ≈ $6.4M |

These are total plant O&M figures. In the simulation they serve as the
**provider's cost baseline** for a full-scope contract. A limited-scope contract
covers only part of this. [Assumption]

### Start-related wear

| Item | Value | Type |
|---|---|---|
| Cost per start, aeroderivative gas turbine (median warm start, lower bound, excluding fuel) | $24 per MW of capacity (2011 $) | [Source] NREL/Intertek *Power Plant Cycling Costs* (2012), Table 1-1 |
| Same, in 2022 $ (to match EIA) | ≈ $31 per MW | [Assumption] converted with US CPI (×1.30) |
| Per start for a 105 MW plant | ≈ $3,300 | Calculated |

| Duty cycle | Starts/year | Start-related wear per year |
|---|---|---|
| Baseload | 15 | ≈ $0.05M |
| Mid-merit | 200 | ≈ $0.65M |
| Peaking | 120 | ≈ $0.39M |
| Industrial | 10 | ≈ $0.03M |

This is added to the EIA O&M estimate above. It matters most for mid-merit and
peaking units, which start often.

## 2. Operating profiles by duty cycle

| Duty cycle | Hours/year | Starts/year | Type |
|---|---|---|---|
| Baseload | 6,000–8,000 | 10–30 | [Assumption] Newest US combined-cycle units averaged a 71% capacity factor in 2020 (≈ 6,200 h) [Source] EIA |
| Mid-merit | 2,000–5,000 | 150–300 | [Assumption] between baseload and peaking |
| Peaking | under 1,500 | about 100–150 | [Source] Peaking units defined as under 1,500 h/year; fleet average about 100 starts/year (2006–10, SPS ORAP data via POWER magazine); one US peaking plant logged about 1,000–1,100 hours and 128–145 starts per unit in 2008 |
| Industrial | 7,500–8,500 | 5–20 | [Assumption] continuous duty supporting a process (e.g. oil and gas, CHP); stops mainly for planned maintenance |

Personas take their profile from their duty cycle. Persona 1 uses the
**industrial** profile, and persona 4 (data centre) uses the **baseload** profile.

## 3. Cost of downtime

| Segment | Value | Type |
|---|---|---|
| Data centre | 54% of serious outages cost over $100,000; 16% over $1M (2023 survey). 2026 report: 57% over $100,000; one in five over $1M | [Source] Uptime Institute |
| Oil and gas | About $220,000 per hour (2021); broader industry estimates $50,000–$500,000 per hour | [Source] Senseye/Siemens, industry estimates |
| General industry | $10,000–$500,000 per hour | [Source] ABB 2025 survey |
| Utility (peaking) | Lost margin ≈ MW × power price. Example: 105 MW × $55/MWh ≈ $5,800/hour, higher during price spikes | [Assumption] using EIA's ~$55/MWh price level when peakers ran most |

**Simulation values per hour of downtime** [Assumption, to be varied]:

| Persona | Downtime cost/hour |
|---|---|
| 1. Industrial / oil and gas (baseload) | $150,000 |
| 2. Utility (mid-merit) | $10,000 |
| 3. Utility (peaking) | $20,000 (only during called hours; spikes are costly) |
| 4. Data centre (baseload) | $300,000 |

## 4. Escalation (annual price increase)

| Item | Value | Type |
|---|---|---|
| Latest US annual inflation | 3.7% (September 2026) | [Source] BLS via news reports |
| Negotiable escalation range | 2–5% per year | [Assumption] |

## 5. How these numbers are used

- **Provider cost** = O&M estimate (section 1), scaled by scope and availability guarantee.
- **Customer value of availability** = downtime cost (section 3) × hours of downtime avoided.
  Example: for persona 4, raising availability from 95% to 98% avoids about 260
  hours a year (3% of 8,760 h) × $300,000 ≈ $79M per year in avoided downtime cost.
- **Escalation** applies to the base price each year over the contract length.
- All [Assumption] values get sensitivity checks on Day 4.

## Sources
- NREL/Intertek APTECH, Power Plant Cycling Costs (2012), Table 1-1: https://www.nrel.gov/docs/fy12osti/55433.pdf
- EIA, Cost and Performance Characteristics of New Generating Technologies (AEO assumptions): https://www.eia.gov/aeo/assumptions/pdf/elec_cost_perf.pdf
- EIA, combined-cycle capacity factors by region and age (2021): https://www.eia.gov/todayinenergy/detail.php?id=48036
- EIA, natural gas combustion turbine use and prices (2013): https://www.eia.gov/todayinenergy/detail.php?id=13191
- POWER magazine, Getting Peak Returns out of Peaking Turbines: https://www.powermag.com/getting-peak-returns-out-of-peaking-turbines/
- Peaking unit definition (under 1,500 h/year): https://collections.lib.utah.edu/details?id=7889
- Example peaking plant operating data: https://www.controleng.com/application-update-integrated-plant-control-system/
- Uptime Institute Annual Outage Analysis 2024 (executive summary): https://www.corrierecomunicazioni.it/wp-content/uploads/2024/04/executive-summary.pdf
- TechRepublic on Uptime Institute 2026 outage analysis: https://techrepublic.com/article/news-data-center-outages-decline-costs-rise/
- Senseye/Siemens, The True Cost of Downtime: https://www.automation.com/article/world-largest-manufacturers-lose-almost-1-trillion
- ABB 2025 survey via press release: https://vendordirectory.shrm.org/company/940000/news/3859205/downtime-is-inevitable-long-outages-aren-t
- US CPI, latest annual rate (September 2026): https://stockanalysis.com/news/us-cpi-rises-october-2026/
