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
| Standby | Rarely runs, must work instantly | Low wear |
 
**Simulation personas (segment + duty cycle):**
 
| # | Segment | Duty cycle | Top priorities |
|---|---|---|---|
| 1 | Industrial / oil and gas | Baseload | High availability, fixed fee, broad scope |
| 2 | Utility | Mid-merit | Hybrid pricing, cost/availability balance, flexibility |
| 3 | Utility | Peaking | Per-use pricing, low fixed cost, reliable starts |
| 4 | Data centre | Baseload (prime power) | Very high availability, strong penalties, lease engine |
 
Personas 1 and 4 share a duty cycle but differ in cost of downtime, so the
simulation can test whether that alone changes the deal.
 
## 4. Pricing models
The pricing model decides **who carries the risk of uncertain usage**.
 
| Model | Who carries usage risk | Typical fit |
|---|---|---|
| Fixed annual fee | Provider | Baseload, standby (paying for readiness) |
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
 