"""The negotiating agents (design.md, section 6).

Each agent is Claude with a private brief and a set of tools. Agents never do
maths themselves: their calculator tools run the formulas in scoring.py.
Each turn ends with the agent calling the `respond` tool to choose an action.
"""
import json

import anthropic
from pydantic import ValidationError

from config import load_settings
from offer import Offer
from scoring import persona_economics, provider_score, customer_score, check_risk_rules

S = load_settings()
MODEL = "claude-haiku-5-5"
MAX_STEPS_PER_TURN = 8   # model calls per turn; the last one must be a response

# --- The 8 contract terms, as a JSON schema the agents fill in -----------------
TERMS_SCHEMA = {
    "type": "object",
    "properties": {
        "annual_fee_m": {"type": "number", "description": "Year-1 annual fee in $ millions, 1.5 to 12.0 in steps of 0.1"},
        "pricing_model": {"type": "string", "enum": ["fixed", "hybrid", "per_hour"]},
        "escalation": {"type": "number", "description": "Yearly price increase as a decimal: one of 0.02, 0.025, 0.03, 0.035, 0.04, 0.045, 0.05"},
        "length_years": {"type": "integer", "enum": [5, 7, 10, 15]},
        "availability": {"type": "number", "description": "Availability guarantee in %: one of 95.0, 95.5, 96.0, 96.5, 97.0, 97.5, 98.0"},
        "penalty_cap": {"type": "number", "description": "Max yearly penalty as a decimal share of the annual fee: one of 0.05, 0.10, 0.15, 0.20, 0.25, 0.30"},
        "repairs": {"type": "boolean"},
        "engines": {"type": "boolean"},
        "rotables": {"type": "boolean"},
        "lease_engine": {"type": "boolean", "description": "Lease engine provided during overhauls"},
    },
    "required": ["annual_fee_m", "pricing_model", "escalation", "length_years", "availability",
                 "penalty_cap", "repairs", "engines", "rotables", "lease_engine"],
}

TERMS_TEXT = """Negotiable contract terms (only these values are allowed):
- Annual fee (year 1): $1.5M to $12.0M, in $0.1M steps
- Pricing model: fixed (whole fee fixed), hybrid (50% fixed, 50% scales with actual running hours), per_hour (10% fixed, 90% scales with actual running hours). The fee is always quoted at the customer's expected hours.
- Escalation: 2.0% to 5.0% per year, in 0.5% steps
- Contract length: 5, 7, 10 or 15 years
- Availability guarantee: 95.0% to 98.0%, in 0.5% steps
- Penalty cap: 5% to 30% of the annual fee, in 5% steps (max penalty paid per year if the guarantee is missed)
- Scope: repairs, engines, rotables, each included or not (at least one)
- Lease engine during overhauls: yes or no"""


def _respond_tool(actions: list[str], description: str) -> dict:
    return {
        "name": "respond",
        "description": description,
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": actions,
                           "description": "walk_away ends the negotiation permanently, with no deal and no chance to revisit."},
                "message": {"type": "string", "description": "Short message to the other side (2-4 sentences)"},
                "terms": {**TERMS_SCHEMA, "description": "Full contract terms. Required for 'offer' and 'counter'."},
            },
            "required": ["action", "message"],
        },
    }


class Agent:
    """One Claude-powered negotiator with its own private conversation history."""

    def __init__(self, role: str, system_prompt: str, calculator: dict, calculate, respond_tool: dict):
        self.role = role
        self.system = system_prompt
        self.tools = [calculator, respond_tool]
        self.calculate = calculate          # Python function that runs the formulas
        self.messages = []
        self.client = anthropic.Anthropic()
        self.tool_calls = []                # calculator calls made, for the log

    def take_turn(self, incoming: str) -> dict:
        """Gives the agent the other side's latest message; returns its chosen action."""
        # The previous turn ended with a tool result (a "user" message), so add the
        # other side's reply to that same message to keep user/assistant turns alternating.
        if self.messages and self.messages[-1]["role"] == "user":
            self.messages[-1]["content"].append({"type": "text", "text": incoming})
        else:
            self.messages.append({"role": "user", "content": [{"type": "text", "text": incoming}]})
        for step in range(1, MAX_STEPS_PER_TURN + 1):
            # On the last step, the agent must respond (no more calculator calls).
            last_step = step == MAX_STEPS_PER_TURN
            choice = {"type": "tool", "name": "respond"} if last_step else {"type": "any"}
            response = self.client.messages.create(
                model=MODEL, max_tokens=1500, system=self.system,
                tools=self.tools, tool_choice=choice, messages=self.messages,
            )
            self.messages.append({"role": "assistant", "content": response.content})
            results = []
            action = None
            for block in response.content:
                if block.type != "tool_use":
                    continue
                if block.name == "respond":
                    result, action = self._check_response(block.input)
                else:
                    result = self._run_calculator(block.input)
                results.append({"type": "tool_result", "tool_use_id": block.id,
                                "content": json.dumps(result), "is_error": "error" in result})
            if step == MAX_STEPS_PER_TURN - 1 and action is None:
                results.append({"type": "text", "text": "You have used all your calculator checks for this turn. Call the respond tool now."})
            self.messages.append({"role": "user", "content": results})
            if action is not None:
                return action
        return {"action": "walk_away", "message": "(No valid response after several attempts.)",
                "offer": None, "forced": True}

    def _run_calculator(self, terms: dict) -> dict:
        try:
            offer = Offer(**terms)
        except ValidationError as e:
            error = {"error": f"Invalid terms: {e.errors()[0]['msg']}"}
            self.tool_calls.append({"terms": terms, "result": error})
            return error
        result = self.calculate(offer)
        self.tool_calls.append({"terms": offer.summary(), "result": result})
        return result

    def _check_response(self, data: dict):
        action = data.get("action")
        needs_terms = action in ("offer", "counter")
        if needs_terms:
            if "terms" not in data:
                self.tool_calls.append({"respond_error": "missing terms", "data": data})
                return {"error": f"'{action}' needs full terms. Try again."}, None
            try:
                offer = Offer(**data["terms"])
            except ValidationError as e:
                self.tool_calls.append({"respond_error": e.errors()[0]["msg"], "data": data})
                return {"error": f"Invalid terms: {e.errors()[0]['msg']}. Try again."}, None
        else:
            offer = None
        return {"status": "received"}, {"action": action, "message": data.get("message", ""), "offer": offer}


# --- Building the two agents ------------------------------------------------------

def make_customer(persona: dict) -> Agent:
    econ = persona_economics(persona)

    def calculate(offer: Offer) -> dict:
        c = customer_score(offer, persona)
        return {
            "savings_vs_alternative_m": round(c["value"] / 1e6, 2),
            "within_budget": c["within_budget"],
            "note": "Savings over the whole contract, in today's money, compared with your alternative. Positive = better than your alternative.",
        }

    system = f"""You are the head of procurement for a {persona['name']}. You are negotiating a long-term service agreement for your 105 MW aeroderivative gas turbine plant with the manufacturer's sales team.

Your situation (private: never reveal your exact budget, downtime cost or alternative's figures):
- Your turbine runs about {persona['hours_per_year']:,} hours a year with about {persona['starts_per_year']} starts; actual hours can vary by about ±{persona['usage_uncertainty']:.0%} year to year.
- Every hour the turbine is unavailable when you need it costs you about ${persona['downtime_cost_per_hour']:,}.
- The most you can approve is an annual fee of ${econ['max_budget']/1e6:.1f}M (year 1).
- Your alternative if there is no deal: a third-party provider at roughly ${econ['full_cost']/1e6:.1f}M a year, with only about 92% availability and no lease engine.

{TERMS_TEXT}

You have a tool, evaluate_offer, that tells you how much any set of terms would save you over the whole contract compared with your alternative (in today's money), and whether the fee is within budget. Use it to check the sales team's offers and to explore counter-offers.

Your goal: get the best deal you can for your company. Only accept a deal that is better than your alternative. Walk away if you cannot get one.

How the negotiation works: you and the sales team take turns, for up to {S['max_rounds']} rounds. Walking away ends the negotiation for good: there is no later chance to reach a deal. If no deal is agreed by the last round, there is no deal.

Each turn, finish by calling the respond tool: accept the latest offer, counter with full terms, or walk_away."""

    calculator = {"name": "evaluate_offer",
                  "description": "Calculates your savings vs your alternative for a set of contract terms, and whether the fee is within budget.",
                  "input_schema": TERMS_SCHEMA}
    respond = _respond_tool(["accept", "counter", "walk_away"],
                            "Your action this turn: accept the sales team's latest offer, counter with full terms, or walk away.")
    return Agent("customer", system, calculator, calculate, respond)


def make_sales(persona: dict) -> Agent:
    r = S["risk_rules"]

    def calculate(offer: Offer) -> dict:
        p = provider_score(offer, persona)
        return {
            "profit_m": round(p["profit"] / 1e6, 2),
            "margin": f"{p['margin']:.1%}",
            "rules_broken": check_risk_rules(offer, persona) or "none",
            "note": "Profit over the whole contract, in today's money.",
        }

    system = f"""You are a sales manager in the services business of a gas turbine manufacturer. You are negotiating a long-term service agreement for a customer's 105 MW aeroderivative gas turbine plant.

What you know about the customer: a {persona['name']} running its turbine about {persona['hours_per_year']:,} hours a year ({persona['duty_cycle']} duty). You do not know their budget, their cost of downtime, or their alternatives.

{TERMS_TEXT}

Company rules every deal must follow:
- Penalty cap no more than {r['max_penalty_cap']:.0%} of the annual fee
- Expected margin of at least {r['min_margin']:.0%}
- Contracts of {r['long_contract_years']}+ years need escalation of at least {r['min_escalation_long']:.1%}
- {r['top_availability']:.0f}% availability only with full scope (repairs, engines and rotables)

You have a tool, estimate_profit, that calculates the company's profit and margin for any set of terms and lists any rules broken. Use it to check offers before you make them and to evaluate the customer's counter-offers.

Your goal: close a profitable deal that follows company rules. No deal is better than a deal that loses money or breaks the rules.

How the negotiation works: you and the customer take turns, for up to {S['max_rounds']} rounds. Walking away ends the negotiation for good: there is no later chance to reach a deal. If no deal is agreed by the last round, there is no deal.

Each turn, finish by calling the respond tool: make an offer with full terms, accept the customer's latest counter-offer, or walk_away."""

    calculator = {"name": "estimate_profit",
                  "description": "Calculates the company's profit and margin for a set of contract terms, and lists any company rules broken.",
                  "input_schema": TERMS_SCHEMA}
    respond = _respond_tool(["offer", "accept", "walk_away"],
                            "Your action this turn: make an offer with full terms, accept the customer's latest counter-offer, or walk away.")
    return Agent("sales", system, calculator, calculate, respond)
