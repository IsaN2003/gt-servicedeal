# Notes: Gas Turbine Service Contracts

## 1. What is a service agreement, and why do both sides want one?
A long-term service agreement is a contract (usually 5–15+ years) in which the
manufacturer maintains a turbine after the customer has bought it: planned
inspections, overhauls, parts, labour, and often unplanned repairs and remote
monitoring.

- **Customer benefits:** predictable maintenance costs, guaranteed reliability
  (availability), access to the manufacturer's parts and expertise, and less
  need for an in-house maintenance team.
- **Provider benefits:** steady, recurring revenue for many years, a long-term
  customer relationship, and chances to sell upgrades and extras later.

## 2. Why do starts matter as well as hours?
Turbines wear in two ways:
- **Running hours:** continuous wear from operating at high temperatures.
- **Starts:** each start and stop heats and cools the hot parts quickly
  (thermal cycling), which causes fatigue and cracking.

So a unit that starts and stops often can need maintenance sooner than its
hours alone suggest. Maintenance intervals, and often contract pricing, are
based on both counts.

**Types of maintenance event** (from smallest to largest):
- **Inspections** (e.g. borescope): quick checks of internal parts
- **Hot-section repairs:** replacing or refurbishing the hottest parts
- **Major overhaul:** a full rebuild; the most expensive and longest event

Aeroderivative turbines (derived from jet engines) have an advantage: the
whole engine can often be swapped out and sent to a shop, with a replacement
or lease engine fitted, so the plant is back online quickly.

## 3. Duty types and what each customer values
Gas turbines run in different duty types, and each one values contract
terms differently.

| Duty type | How it runs | Wear driven by |
|---|---|---|
| Baseload | Almost nonstop, few starts | Running hours |
| Mid-merit | Daily, ramping with demand, frequent starts | Hours and starts |
| Peaking | Rarely, during demand spikes | Starts |
| Industrial / CHP | Powers a factory or site, often supplies heat too | Mostly hours |
| Backup / data centre | Rarely runs, must work instantly | Low wear, extreme cost of failure |

**Baseload / industrial site** (runs almost nonstop):
1. High availability guarantee, because an outage can stop the whole plant
2. Fixed, predictable annual fee
3. Broad scope, including unplanned repairs

**Mid-merit utility** (runs daily, ramping with demand):
1. Pricing model that reflects both hours and starts fairly
2. Balance of cost and availability
3. Flexibility, e.g. adjusting terms if the running pattern changes

**Peaking utility** (runs rarely during demand spikes):
1. Pay per hour or per start rather than a high fixed fee
2. Low fixed annual cost
3. Reliable, fast starts when called on

**Data centre / backup power** (rarely runs, but failure is extremely costly):
1. Very high availability guarantee (e.g. 98%+)
2. Strong penalties if the guarantee is missed
3. Backup/lease engine and remote monitoring to minimise downtime

Key insight: the same contract terms are worth very different amounts to
different customers. That's what makes negotiation possible, and why my
simulation uses these four duty types as customer personas.

## 4. Pricing models and duty type
The pricing model decides **who carries the risk of uncertain usage**.

- **Fixed fee:** the provider carries the risk. If the turbine runs harder
  than expected, the provider absorbs the extra wear.
- **Per hour / per start:** the customer carries the risk. Costs rise with use.
- **Hybrid (fixed + variable):** the risk is shared. Common in practice.

| Duty type | Usual preference | Why |
|---|---|---|
| Baseload | Fixed fee | High, predictable hours, so easy to price; stable budget |
| Industrial / CHP | Fixed, sometimes per hour | Steady running; plants budget annually |
| Mid-merit | Hybrid | Fixed part covers baseline costs; variable part tracks wear |
| Peaking | Mostly per hour/start, small fixed part | Low, unpredictable use; costs line up with when it earns money |
| Backup / data centre | Mostly fixed | Barely runs, so the customer is paying for readiness, not usage |

## 5. How the price changes during a contract
The price agreed at signing usually changes over the contract:
1. **Escalation:** a yearly increase linked to an inflation or materials index.
2. **Usage-based payments:** the bill moves with actual hours or starts.
3. **Operating-profile adjustments:** if the customer runs the turbine much
   harder or differently than assumed, the price is adjusted, sometimes
   through a yearly reconciliation ("true-up").
4. **Performance bonuses and penalties:** bonuses if availability beats the
   guarantee; penalties if it falls short.
5. **Scope changes:** adding services or repairs outside the agreed scope.
6. **Renegotiation points:** reviews at set milestones or after big changes.

## 6. Why would a provider insist on capping penalties?
Penalties (liquidated damages) transfer risk to the provider. If they're
uncapped, one bad year (a major failure, supply delays) could cost more than
the whole contract earns. A cap, often a percentage of the annual fee, limits
the maximum loss and keeps the contract profitable and insurable. Providers
usually accept higher guarantees or higher penalties only in exchange for a
higher price.

Contracts often also include an **overall liability cap** (the most the
provider can owe in total) and **termination terms** (fees for ending the
contract early).

## 7. How availability and performance are measured
- **Availability exclusions:** guarantees usually exclude outages the provider
  isn't responsible for, e.g. customer-caused problems, fuel supply issues, or
  extreme events (force majeure). The exact definition matters as much as the
  percentage.
- **Other performance guarantees:** contracts can also guarantee output (MW)
  or efficiency (heat rate), which naturally decline as the turbine wears.

## 8. The customer's alternatives (walk-away options)
A customer doesn't have to sign a long-term agreement. It can:
- pay for each repair as needed (**time and materials**)
- buy a **parts-only** or **limited-scope** contract
- use a **third-party service provider** instead of the manufacturer, often cheaper

The better a customer's alternatives, the more bargaining power it has. In the
simulation, each customer's walk-away point should reflect its alternatives.

## 9. Regional context: the Gulf
- Heat and dust increase wear and put more load on air filters.
- Turbine output drops on hot days, which matters most at summer peak demand.
- Both affect maintenance costs and how realistic availability targets are.

## 10. Open questions to research (public sources)
- What do typical gas turbine maintenance costs look like? (NREL, Lazard)
- How many hours and starts do peaking vs baseload units run per year? (EIA)
- What does downtime cost a data centre per hour? (industry surveys)
- Do any public utility filings describe service-agreement terms?

## Contract terms to negotiate in the simulation
| Term | Customer wants | Provider wants |
|---|---|---|
| Length (5–15+ years) | Flexibility, or long term to lock in prices | Long term for steady revenue |
| Pricing model (fixed / per use / hybrid) | Depends on duty type | Covers its risk and readiness costs |
| Base price + escalation | Low price, low or capped escalation | Healthy margin, protection against rising costs |
| Availability guarantee (e.g. 95–98%) | As high as possible | Realistic and achievable |
| Penalties (liquidated damages) | High, so the guarantee means something | Capped, to limit risk |
| Scope (parts, labour, unplanned repairs) | Everything covered | Clear limits |
| Extras (backup engine, monitoring, upgrades) | Included free | Paid add-ons or bargaining chips |

## Key trade-offs to model in the simulation
- Higher availability → higher cost and risk for the provider → higher price.
- More risk transferred to the provider (uncapped penalties, full scope) → higher price.
- Customer duty type determines which terms and pricing model it values most.
- Better customer alternatives → lower walk-away price → harder negotiation.