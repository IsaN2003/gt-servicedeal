"""The structure of a contract offer (design.md, section 1).

Every offer an agent makes must fit this structure. Any value outside the
allowed list in configs/settings.yaml is rejected with a clear error message,
so every offer that gets through can be scored.
"""
from typing import Literal

from pydantic import BaseModel, model_validator

from config import load_settings

SETTINGS = load_settings()
TERMS = SETTINGS["terms"]


class Offer(BaseModel):
    annual_fee_m: float                                   # $ millions, year 1
    pricing_model: Literal["fixed", "hybrid", "per_hour"]
    escalation: float                                     # e.g. 0.035 = 3.5% per year
    length_years: int
    availability: float                                   # e.g. 97.0 = 97%
    penalty_cap: float                                    # e.g. 0.10 = 10% of annual fee
    repairs: bool
    engines: bool
    rotables: bool
    lease_engine: bool

    @model_validator(mode="after")
    def check_allowed_values(self):
        fee = TERMS["annual_fee_m"]
        steps = round((self.annual_fee_m - fee["min"]) / fee["step"], 6)
        if not (fee["min"] <= self.annual_fee_m <= fee["max"]) or steps != int(steps):
            raise ValueError(
                f"annual_fee_m must be between {fee['min']} and {fee['max']} "
                f"in steps of {fee['step']} (got {self.annual_fee_m})"
            )
        for field in ["escalation", "length_years", "availability", "penalty_cap"]:
            allowed = TERMS[field]
            value = getattr(self, field)
            if not any(abs(value - a) < 1e-9 for a in allowed):
                raise ValueError(f"{field} must be one of {allowed} (got {value})")
        if not (self.repairs or self.engines or self.rotables):
            raise ValueError("scope must include at least one of repairs, engines, rotables")
        return self

    def scope_share(self) -> float:
        """Share of full maintenance cost covered by this offer's scope."""
        shares = SETTINGS["scope_cost_share"]
        return (shares["repairs"] * self.repairs
                + shares["engines"] * self.engines
                + shares["rotables"] * self.rotables)

    def full_scope(self) -> bool:
        return self.repairs and self.engines and self.rotables

    def summary(self) -> str:
        """A one-line, human-readable description of the offer."""
        scope = [name for name in ["repairs", "engines", "rotables"] if getattr(self, name)]
        return (
            f"${self.annual_fee_m:.1f}M/yr, {self.pricing_model}, "
            f"{self.escalation:.1%} escalation, {self.length_years} yrs, "
            f"{self.availability:.1f}% availability, {self.penalty_cap:.0%} penalty cap, "
            f"scope: {'+'.join(scope)}, lease engine: {'yes' if self.lease_engine else 'no'}"
        )


if __name__ == "__main__":
    good = Offer(annual_fee_m=4.8, pricing_model="hybrid", escalation=0.035,
                 length_years=7, availability=96.0, penalty_cap=0.10,
                 repairs=True, engines=True, rotables=True, lease_engine=False)
    print("Valid offer:", good.summary())
    print("Scope share:", good.scope_share())

    try:
        Offer(annual_fee_m=4.8, pricing_model="hybrid", escalation=0.035,
              length_years=8, availability=96.0, penalty_cap=0.10,
              repairs=True, engines=True, rotables=True, lease_engine=False)
    except ValueError as e:
        print("Rejected as expected:", str(e).splitlines()[1].strip())
