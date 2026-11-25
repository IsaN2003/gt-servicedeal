"""Scoring formulas (design.md, section 4) and risk rules (section 5).

Used in three places:
- the pricing analyst's cost calculator (provider side, during the negotiation)
- the customer's offer calculator (customer side, during the negotiation)
- the evaluation afterwards (both sides, as the benchmark)
"""
from config import load_settings, load_personas
from offer import Offer

S = load_settings()
PLANT_MW = load_personas()["plant_mw"]


def persona_economics(p: dict) -> dict:
    """Numbers calculated from a persona: provider cost, budget, walk-away cost."""
    kw = PLANT_MW * 1000
    mwh = PLANT_MW * p["hours_per_year"]
    fixed = kw * S["eia"]["fixed_om_per_kw_year"]
    variable = mwh * S["eia"]["variable_om_per_mwh"]
    full_cost = fixed + variable                         # C in design.md
    walk_downtime = (1 - S["walkaway"]["availability"] / 100) * p["hours_per_year"] * p["downtime_cost_per_hour"]
    return {
        "full_cost": full_cost,
        "variable_cost_share": variable / full_cost,
        "max_budget": full_cost * p["budget_multiplier"],
        "walkaway_cost_year1": S["walkaway"]["cost_share"] * full_cost + walk_downtime,
    }


def _discount(t: int) -> float:
    """Converts money in year t into today's money."""
    return 1 / (1 + S["discount_rate"]) ** (t - 1)


def _miss_probability(availability: float) -> float:
    return S["miss_probability"][availability]


def provider_score(offer: Offer, p: dict) -> dict:
    """Provider profit over the contract, in today's money."""
    econ = persona_economics(p)
    C = econ["full_cost"]
    fee = offer.annual_fee_m * 1e6
    fee_var_share = S["fee_variable_share"][offer.pricing_model]
    mismatch = abs(econ["variable_cost_share"] - fee_var_share)

    total_profit = total_revenue = 0.0
    for t in range(1, offer.length_years + 1):
        cost_growth = (1 + S["cost_inflation"]) ** (t - 1)
        revenue = fee * (1 + offer.escalation) ** (t - 1)
        service_cost = C * offer.scope_share() * cost_growth
        availability_cost = service_cost * S["availability_cost_per_point"] * (offer.availability - 95)
        lease_cost = S["lease_engine_cost_share"] * C * cost_growth if offer.lease_engine else 0.0
        expected_penalty = _miss_probability(offer.availability) * offer.penalty_cap * revenue
        usage_risk = S["risk_weight"] * p["usage_uncertainty"] * revenue * mismatch

        profit = revenue - service_cost - availability_cost - lease_cost - expected_penalty - usage_risk
        total_profit += profit * _discount(t)
        total_revenue += revenue * _discount(t)

    return {
        "profit": total_profit,
        "revenue": total_revenue,
        "margin": total_profit / total_revenue,
    }


def customer_score(offer: Offer, p: dict) -> dict:
    """Customer value compared with the walk-away option, in today's money."""
    econ = persona_economics(p)
    C = econ["full_cost"]
    H, D = p["hours_per_year"], p["downtime_cost_per_hour"]
    fee = offer.annual_fee_m * 1e6
    fee_var_share = S["fee_variable_share"][offer.pricing_model]
    bonus = S["lease_engine_availability_bonus"] if offer.lease_engine else 0.0
    effective_availability = min(offer.availability + bonus, S["max_effective_availability"]) / 100

    total_value = 0.0
    for t in range(1, offer.length_years + 1):
        cost_growth = (1 + S["cost_inflation"]) ** (t - 1)
        fee_paid = fee * (1 + offer.escalation) ** (t - 1)
        uncovered = S["uncovered_cost_multiplier"] * C * (1 - offer.scope_share()) * cost_growth
        downtime = (1 - effective_availability) * H * D
        penalty_received = _miss_probability(offer.availability) * offer.penalty_cap * fee_paid
        usage_risk = S["risk_weight"] * p["usage_uncertainty"] * fee_paid * fee_var_share

        deal_cost = fee_paid + uncovered + downtime - penalty_received + usage_risk
        walkaway_cost = (S["walkaway"]["cost_share"] * C * cost_growth
                         + (1 - S["walkaway"]["availability"] / 100) * H * D)
        total_value += (walkaway_cost - deal_cost) * _discount(t)

    return {
        "value": total_value,
        "within_budget": fee <= econ["max_budget"],
        "max_budget": econ["max_budget"],
    }


def check_risk_rules(offer: Offer, p: dict) -> list[str]:
    """Returns the list of broken risk rules (empty list = all rules pass)."""
    r = S["risk_rules"]
    broken = []
    if offer.penalty_cap > r["max_penalty_cap"] + 1e-9:
        broken.append(f"R1: penalty cap {offer.penalty_cap:.0%} exceeds the {r['max_penalty_cap']:.0%} limit")
    margin = provider_score(offer, p)["margin"]
    if margin < r["min_margin"]:
        broken.append(f"R2: expected margin {margin:.1%} is below the {r['min_margin']:.0%} minimum")
    if offer.length_years >= r["long_contract_years"] and offer.escalation < r["min_escalation_long"] - 1e-9:
        broken.append(f"R3: contracts of {r['long_contract_years']}+ years need escalation of at least {r['min_escalation_long']:.1%}")
    if offer.availability >= r["top_availability"] and not offer.full_scope():
        broken.append(f"R4: {r['top_availability']:.0f}% availability is only allowed with full scope")
    return broken


if __name__ == "__main__":
    personas = load_personas()["personas"]
    midmerit = personas["midmerit"]

    print("Persona economics (mid-merit utility):")
    for k, v in persona_economics(midmerit).items():
        print(f"  {k}: {v:,.2f}")

    examples = {
        "Agents' example deal": Offer(annual_fee_m=4.8, pricing_model="hybrid", escalation=0.035,
                                      length_years=7, availability=96.0, penalty_cap=0.10,
                                      repairs=True, engines=True, rotables=True, lease_engine=False),
        "Better deal found by benchmark": Offer(annual_fee_m=4.9, pricing_model="hybrid", escalation=0.04,
                                                length_years=10, availability=97.0, penalty_cap=0.05,
                                                repairs=True, engines=True, rotables=True, lease_engine=True),
    }
    for name, offer in examples.items():
        prov = provider_score(offer, midmerit)
        cust = customer_score(offer, midmerit)
        print(f"\n{name}: {offer.summary()}")
        print(f"  Provider: profit ${prov['profit']/1e6:.2f}M, margin {prov['margin']:.1%}")
        print(f"  Customer: value ${cust['value']/1e6:.2f}M, within budget: {cust['within_budget']}")
        print(f"  Risk rules broken: {check_risk_rules(offer, midmerit) or 'none'}")
