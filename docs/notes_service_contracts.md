# Notes: Gas Turbine Service Contracts

Background for GT ServiceDeal. Public, general industry knowledge only.

## 1. What a service agreement is
A long-term service agreement (usually 5–15+ years) is a contract in which the
manufacturer maintains a turbine after the customer has bought it.

- **Customer gets:** predictable costs, guaranteed reliability (availability),
  and access to the manufacturer's parts and expertise.
- **Provider gets:** steady recurring revenue and a long-term customer relationship.

## 2. What drives maintenance cost
Turbines wear in two ways:
- **Running hours:** continuous wear from operating at high temperatures.
- **Starts:** each start and stop heats and cools hot parts quickly (thermal
  cycling), causing fatigue.

So cost depends on **how much and how often** a turbine runs. Aeroderivative
turbines have an advantage: the whole engine can often be swapped for a
replacement or lease engine, so the plant is back online quickly.

**Service types** (what the contract can cover):
- **Repairs:** fixing or refurbishing damaged parts.
- **Engines:** whole-engine work such as overhauls, exchanges, or lease engines.
- **Rotables:** high-value components swapped for ready-to-use spares from a
  pool, while the removed part is repaired and returned to the pool.

## 3. Duty cycles, customer segments and personas
- **Duty cycle** = *how* the turbine runs. It drives wear and the preferred pricing model.
- **Customer segment** = *who* owns it. It drives the cost of downtime.

| Duty cycle | How it runs | Wear driven by |
|---|---|---|
| Baseload | Almost nonstop, few starts | Running hours |
| Mid-merit | Daily, ramping with demand, frequent starts | Hours and starts |
| Peaking | Rarely, during demand spikes | Starts |
| Industrial | Continuous duty supporting a process (e.g. oil and gas, CHP) | Running hours |

**Simulation personas (segment + duty cycle):**

| # | Segment | Duty cycle | Top priorities |
|---|---|---|---|
| 1 | Industrial / oil and gas | Industrial | High availability, fixed fee, broad scope |
| 2 | Utility | Mid-merit | Hybrid pricing, cost/availability balance, flexibility |
| 3 | Utility | Peaking | Per-use pricing, low fixed cost, reliable starts |
| 4 | Data centre | Baseload (prime power) | Very high availability, strong penalties, lease engine |

Personas 1 and 4 both run nearly nonstop but differ in cost of downtime, so the
simulation can test how much that changes the deal.

## 4. Pricing models
The pricing model decides **who carries the risk of uncertain usage**.

| Model | Who carries usage risk | Typical fit |
|---|---|---|
| Fixed annual fee | Provider | Baseload, industrial |
| Per hour / per start | Customer | Peaking |
| Hybrid (fixed + variable) | Shared | Mid-merit |

The price also changes during a contract, mainly through **annual escalation**
(linked to inflation) and **usage-based payments**.

## 5. Risk terms
- **Availability guarantee:** % of time the unit is ready to run (e.g. 95–98%).
  Outages the provider isn't responsible for are usually excluded.
- **Penalties (liquidated damages):** paid by the provider if the guarantee is
  missed. Providers cap them (often as a % of the annual fee), because uncapped
  penalties could cost more than the contract earns.
- Stronger guarantees and higher penalty caps are traded for a higher price.

## 6. The customer's alternatives (walk-away options)
A customer doesn't have to sign. It can pay per repair (**time and materials**),
buy a **limited-scope** contract, or use a cheaper **third-party provider**.
Better alternatives mean more bargaining power and a lower walk-away price.

## 7. Regional context: the Gulf
Heat and dust increase wear and filter load, and output drops on hot days.
This raises maintenance costs and makes high availability harder to guarantee.

## 8. Simulation inputs

**Negotiable terms**

| Term | Customer wants | Provider wants |
|---|---|---|
| Length (5–15 years) | Flexibility or locked-in prices | Long term, steady revenue |
| Pricing model (fixed / per use / hybrid) | Depends on duty cycle | Covers risk and readiness costs |
| Base price + escalation | Low price, low escalation | Healthy margin, inflation protection |
| Availability guarantee (95–98%) | As high as possible | Realistic and achievable |
| Penalty cap (% of annual fee) | High | Low |
| Scope (repairs / engines / rotables) | All included | Clear limits, extras paid |
| Lease engine during overhauls | Included | Paid add-on or bargaining chip |

**Trade-offs the agents should discover on their own**
- Higher availability → higher provider cost and risk → higher price.
- More risk on the provider (higher penalty cap, full scope) → higher price.
- Duty cycle shapes the preferred pricing model; segment shapes the cost of downtime.
- Better customer alternatives → lower walk-away price → harder negotiation.

## 9. Numbers to find (public sources, Step 3)
- Gas turbine maintenance costs (NREL Annual Technology Baseline, Lazard)
- Typical hours and starts per year by duty cycle (EIA)
- Cost of downtime for data centres and industrial plants (industry surveys)
- Typical inflation rates for escalation

## 10. Out of scope for v1
Output and heat-rate guarantees, true-ups and bonuses, termination fees,
liability caps beyond penalties, detailed maintenance event schedules.
Possible additions for v2.
 
## 11. Terminology
 
### Industry terms
| Term | Meaning |
|---|---|
| Aeroderivative turbine | A gas turbine derived from a jet engine; compact, quick to start, and the engine can be swapped out for maintenance |
| Availability | Share of time a turbine is ready to run (e.g. 97% = unavailable 3% of the time). Defined in industry standard IEEE 762 |
| Availability guarantee | The availability level the provider promises in the contract |
| Baseload | Duty cycle: runs almost nonstop, few starts |
| Capacity factor | Electricity actually generated ÷ maximum possible over a period. A measure of how hard a plant runs |
| CHP (combined heat and power) | A plant that produces both electricity and useful heat, common at industrial sites |
| Customer segment | Who owns the turbine (utility, industrial, data centre). Drives the cost of downtime |
| Downtime cost | Money a customer loses per hour its turbine is unavailable when needed |
| Duty cycle | How a turbine runs: baseload, mid-merit, peaking or industrial |
| EFORd | Equivalent forced outage rate on demand: how often a unit is unavailable when it's actually needed |
| Engines (service type) | Whole-engine work: overhauls, exchanges, lease engines |
| Escalation | Yearly price increase in a contract, usually linked to inflation |
| Fixed O&M | Maintenance costs that don't depend on how much the plant runs (staff, routine upkeep, readiness). Measured per kW per year |
| Industrial (duty cycle) | Continuous duty supporting a process, e.g. oil and gas or CHP |
| kW / MW | Units of power (plant size). 1 MW = 1,000 kW |
| Lease engine | A replacement engine fitted while the customer's own engine is overhauled, reducing downtime |
| Liquidated damages (penalties) | Payments the provider makes if it misses a guarantee |
| Long-term service agreement | Multi-year contract in which the manufacturer maintains a turbine |
| Mid-merit | Duty cycle: runs daily, ramping with demand, frequent starts |
| MWh | Unit of electricity generated: 1 MW running for 1 hour |
| O&M | Operations and maintenance: the cost of running and maintaining a plant |
| Peaking | Duty cycle: runs rarely, during demand spikes (under about 1,500 hours a year) |
| Penalty cap | The maximum penalty the provider pays per year, often a % of the annual fee |
| Pricing model | How the fee is charged: fixed, per hour/start, or hybrid |
| Repairs (service type) | Fixing or refurbishing damaged parts |
| Rotables | High-value components swapped for ready spares from a pool, while the removed part is repaired and returned to the pool |
| Running hours | Hours a turbine operates. Drives continuous wear |
| Scope | Which services the contract covers |
| Starts | Each time a turbine starts up. Causes wear from heating and cooling |
| Third-party provider | A service company that isn't the turbine's original manufacturer |
| Time and materials | Paying for each repair as needed, with no contract |
| True-up | Yearly price adjustment if actual use differs from what the contract assumed |
| Variable O&M | Maintenance costs that grow with use. Measured per MWh |
 
### Simulation and analysis terms
| Term | Meaning |
|---|---|
| Agent | An AI (LLM) playing one role in the negotiation, e.g. customer or sales |
| BATNA / walk-away | Best alternative to a negotiated agreement: what a side does if there's no deal |
| Calibration check | Testing that every persona has at least one possible deal |
| Discount rate | Rate used to convert future money into today's value (8% in this project) |
| Expected value | A cost or gain weighted by how likely it is, e.g. chance of missing the guarantee × penalty |
| Net present value (NPV) | Total value of money over several years, converted into today's money |
| Pareto frontier | The set of deals where neither side can gain without the other losing. Used to measure value left on the table |
| Persona | A customer profile: segment + duty cycle + numbers |
| Risk reviewer | Agent that blocks offers breaking the provider's rules |
| Sensitivity check | Changing an assumption to see if the findings still hold |
| Setup | One version of the experiment (e.g. without the risk reviewer) |
| ZOPA | Zone of possible agreement: the range of deals better than walking away for both sides |