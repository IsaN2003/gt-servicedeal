"""The negotiating agents (design.md, section 6): customer, sales and pricing analyst.

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
DEFAULT_MODEL = "claude-haiku-5-5"     # setups.yaml can choose another model
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

    def __init__(self, role: str, system_prompt: str, helper_tool, run_helper, respond_tool: dict,
                 model: str = DEFAULT_MODEL):
        self.role = role
        self.system = system_prompt
        self.model = model
        # helper_tool can be None: then the agent's only tool is respond
        self.tools = [helper_tool, respond_tool] if helper_tool else [respond_tool]
        self.run_helper = run_helper        # Python function behind the helper tool
        self.messages = []
        self.client = anthropic.Anthropic()
        self.tool_calls = []                # helper tool calls made, for the log

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
                model=self.model, max_tokens=1500, system=self.system,
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
                    result = self.run_helper(block.input)
                    self.tool_calls.append({"tool": block.name, "input": block.input, "result": result})
                results.append({"type": "tool_result", "tool_use_id": block.id,
                                "content": json.dumps(result), "is_error": "error" in result})
            if step == MAX_STEPS_PER_TURN - 1 and action is None:
                results.append({"type": "text", "text": "You have used all your tool checks for this turn. Call the respond tool now."})
            self.messages.append({"role": "user", "content": results})
            if action is not None:
                return action
        return {"action": "walk_away", "message": "(No valid response after several attempts.)",
                "offer": None, "forced": True}

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


def _calculator(calculate):
    """Turns a scoring function into a tool runner: validate the terms, then calculate."""
    def run(terms: dict) -> dict:
        try:
            offer = Offer(**terms)
        except ValidationError as e:
            return {"error": f"Invalid terms: {e.errors()[0]['msg']}"}
        return calculate(offer)
    return run


# --- Building the agents ----------------------------------------------------------

def make_customer(persona: dict, calculator_on: bool = True, model: str = DEFAULT_MODEL) -> Agent:
    econ = persona_economics(persona)

    def calculate(offer: Offer) -> dict:
        c = customer_score(offer, persona)
        return {
            "savings_vs_alternative_m": round(c["value"] / 1e6, 2),
            "within_budget": c["within_budget"],
            "note": "Savings over the whole contract, in today's money, compared with your alternative. Positive = better than your alternative.",
        }

    if calculator_on:
        tool_text = ("You have a tool, evaluate_offer, that tells you how much any set of terms would save you over the whole "
                     "contract compared with your alternative (in today's money), and whether the fee is within budget. "
                     "Use it to check the sales team's offers and to explore counter-offers.")
    else:
        tool_text = "You have no calculator: judge offers from the information above."

    system = f"""You are the head of procurement for a {persona['name']}. You are negotiating a long-term service agreement for your 105 MW aeroderivative gas turbine plant with the manufacturer's sales team.

Your situation (private: never reveal your exact budget, downtime cost or alternative's figures):
- Your turbine runs about {persona['hours_per_year']:,} hours a year with about {persona['starts_per_year']} starts; actual hours can vary by about ±{persona['usage_uncertainty']:.0%} year to year.
- Every hour the turbine is unavailable when you need it costs you about ${persona['downtime_cost_per_hour']:,}.
- The most you can approve is an annual fee of ${econ['max_budget']/1e6:.1f}M (year 1).
- Your alternative if there is no deal: a third-party provider at roughly ${econ['full_cost']/1e6:.1f}M a year, with only about 92% availability and no lease engine.

{TERMS_TEXT}

{tool_text}

Your goal: get the best deal you can for your company. Only accept a deal that is better than your alternative. Walk away if you cannot get one.

How the negotiation works: you and the sales team take turns, for up to {S['max_rounds']} rounds. Walking away ends the negotiation for good: there is no later chance to reach a deal. If no deal is agreed by the last round, there is no deal.

Each turn, finish by calling the respond tool: accept the latest offer, counter with full terms, or walk_away."""

    calculator = {"name": "evaluate_offer",
                  "description": "Calculates your savings vs your alternative for a set of contract terms, and whether the fee is within budget.",
                  "input_schema": TERMS_SCHEMA}
    respond = _respond_tool(["accept", "counter", "walk_away"],
                            "Your action this turn: accept the sales team's latest offer, counter with full terms, or walk away.")
    if not calculator_on:
        return Agent("customer", system, None, None, respond, model)
    return Agent("customer", system, calculator, _calculator(calculate), respond, model)


def make_pricing_analyst(persona: dict, model: str = DEFAULT_MODEL) -> Agent:
    """The pricing analyst owns the profit calculator and answers sales' questions."""
    r = S["risk_rules"]

    def calculate(offer: Offer) -> dict:
        p = provider_score(offer, persona)
        return {
            "profit_m": round(p["profit"] / 1e6, 2),
            "margin": f"{p['margin']:.1%}",
            "rules_broken": check_risk_rules(offer, persona) or "none",
            "note": "Profit over the whole contract, in today's money.",
        }

    system = f"""You are the pricing analyst in the services business of a gas turbine manufacturer. A sales manager is negotiating a long-term service agreement with a {persona['name']} running its 105 MW aeroderivative plant about {persona['hours_per_year']:,} hours a year with about {persona['starts_per_year']} starts ({persona['duty_cycle']} duty).

Your job: answer the sales manager's questions accurately. You have a tool, estimate_profit, that calculates the company's profit and margin for any set of contract terms and lists any company rules broken. Always use it rather than estimating numbers yourself.

{TERMS_TEXT}

Company rules every deal must follow:
- Penalty cap no more than {r['max_penalty_cap']:.0%} of the annual fee
- Expected margin of at least {r['min_margin']:.0%}
- Contracts of {r['long_contract_years']}+ years need escalation of at least {r['min_escalation_long']:.1%}
- {r['top_availability']:.0f}% availability only with full scope (repairs, engines and rotables)

When you answer, give the numbers clearly and explain which terms are driving the margin. You do not know anything about the customer's budget or priorities, and you do not negotiate.

Finish every answer by calling the respond tool with action "reply" and your answer as the message."""

    calculator = {"name": "estimate_profit",
                  "description": "Calculates the company's profit and margin for a set of contract terms, and lists any company rules broken.",
                  "input_schema": TERMS_SCHEMA}
    respond = {
        "name": "respond",
        "description": "Send your answer to the sales manager.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["reply"]},
                "message": {"type": "string", "description": "Your answer, with the key numbers (3-6 sentences)"},
            },
            "required": ["action", "message"],
        },
    }
    return Agent("pricing_analyst", system, calculator, _calculator(calculate), respond, model)


def _profit_calculator(persona: dict):
    def calculate(offer: Offer) -> dict:
        p = provider_score(offer, persona)
        return {
            "profit_m": round(p["profit"] / 1e6, 2),
            "margin": f"{p['margin']:.1%}",
            "rules_broken": check_risk_rules(offer, persona) or "none",
            "note": "Profit over the whole contract, in today's money.",
        }
    return calculate


def make_sales(persona: dict, analyst=None, calculator_on: bool = False, reviewer_on: bool = True,
               model: str = DEFAULT_MODEL) -> Agent:
    r = S["risk_rules"]

    consultations = []   # every question to the analyst, with its calculations, in order (for the event log)

    def ask_analyst(data: dict) -> dict:
        question = data.get("question", "")
        terms = data.get("terms")
        text = f"Question from sales: {question}"
        if terms:
            try:
                text += f"\nTerms to check: {Offer(**terms).summary()}"
            except ValidationError as e:
                return {"error": f"Invalid terms: {e.errors()[0]['msg']}"}
        calcs_before = len(analyst.tool_calls)
        answer = analyst.take_turn(text)
        consultations.append({"question": question, "terms": terms, "answer": answer["message"],
                              "analyst_calcs": analyst.tool_calls[calcs_before:]})
        return {"pricing_analyst_says": answer["message"]}

    if analyst is not None:
        tool_text = ("You cannot calculate profit yourself. Your pricing analyst can: use the ask_pricing_analyst tool to ask "
                     "about the profit and margin of any terms, or any other pricing question.")
    elif calculator_on:
        tool_text = ("You have a tool, estimate_profit, that calculates the company's profit and margin for any set of terms "
                     "and lists any rules broken. Use it to check offers before you make them.")
    else:
        tool_text = "You have no profit calculator and no pricing analyst: judge offers from the information above."
    review_text = ("\n\nEvery offer you make, and any counter-offer you accept, is checked by the risk reviewer before it goes "
                   "to the customer. If it breaks a company rule it is blocked and sent back to you to revise."
                   if reviewer_on else "")

    system = f"""You are a sales manager in the services business of a gas turbine manufacturer. You are negotiating a long-term service agreement for a customer's 105 MW aeroderivative gas turbine plant.

What you know about the customer: a {persona['name']} running its turbine about {persona['hours_per_year']:,} hours a year with about {persona['starts_per_year']} starts ({persona['duty_cycle']} duty). Every start adds wear, so frequent starts raise maintenance costs. You do not know their budget, their cost of downtime, or their alternatives.

{TERMS_TEXT}

Company rules every deal must follow:
- Penalty cap no more than {r['max_penalty_cap']:.0%} of the annual fee
- Expected margin of at least {r['min_margin']:.0%}
- Contracts of {r['long_contract_years']}+ years need escalation of at least {r['min_escalation_long']:.1%}
- {r['top_availability']:.0f}% availability only with full scope (repairs, engines and rotables)

{tool_text}{review_text}

Your goal: close a profitable deal that follows company rules. No deal is better than a deal that loses money or breaks the rules.

How the negotiation works: you and the customer take turns, for up to {S['max_rounds']} rounds. Walking away ends the negotiation for good: there is no later chance to reach a deal. If no deal is agreed by the last round, there is no deal.

Each turn, finish by calling the respond tool: make an offer with full terms, accept the customer's latest counter-offer, or walk_away."""

    ask_tool = {
        "name": "ask_pricing_analyst",
        "description": "Ask your pricing analyst a question, e.g. the profit and margin of a set of terms.",
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "Your question in plain words"},
                "terms": {**TERMS_SCHEMA, "description": "Optional: full contract terms for the analyst to check"},
            },
            "required": ["question"],
        },
    }
    respond = _respond_tool(["offer", "accept", "walk_away"],
                            "Your action this turn: make an offer with full terms, accept the customer's latest counter-offer, or walk away.")
    if analyst is not None:
        sales = Agent("sales", system, ask_tool, ask_analyst, respond, model)
    elif calculator_on:
        calc_tool = {"name": "estimate_profit",
                     "description": "Calculates the company's profit and margin for a set of contract terms, and lists any company rules broken.",
                     "input_schema": TERMS_SCHEMA}
        sales = Agent("sales", system, calc_tool, _calculator(_profit_calculator(persona)), respond, model)
    else:
        sales = Agent("sales", system, None, None, respond, model)
    sales.consultations = consultations
    return sales


def make_risk_reviewer(persona: dict, model: str = DEFAULT_MODEL) -> Agent:
    """The risk reviewer explains why a sales offer was blocked.
    The block decision itself is made by code (check_risk_rules), so it is always correct."""
    r = S["risk_rules"]

    def check(offer: Offer) -> dict:
        return {"rules_broken": check_risk_rules(offer, persona) or "none"}

    system = f"""You are the risk reviewer in the services business of a gas turbine manufacturer. Before any offer from the sales team reaches the customer, it is checked against the company rules:
- R1: penalty cap no more than {r['max_penalty_cap']:.0%} of the annual fee
- R2: expected margin of at least {r['min_margin']:.0%}
- R3: contracts of {r['long_contract_years']}+ years need escalation of at least {r['min_escalation_long']:.1%}
- R4: {r['top_availability']:.0f}% availability only with full scope (repairs, engines and rotables)

You will be given an offer that broke one or more rules, and the list of rules it broke. You can use the check_rules tool to check any terms.

Your job: tell the sales team, briefly and clearly, that the offer is blocked, which rules it broke, and what has to change for it to pass. You do not negotiate and you know nothing about the customer's budget or priorities.

Finish by calling the respond tool with action "block" and your note as the message."""

    checker = {"name": "check_rules",
               "description": "Checks a set of contract terms against the company rules and lists any broken.",
               "input_schema": TERMS_SCHEMA}
    respond = {
        "name": "respond",
        "description": "Send your note to the sales team.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["block"]},
                "message": {"type": "string", "description": "Short note: which rules were broken and what must change (2-4 sentences)"},
            },
            "required": ["action", "message"],
        },
    }
    return Agent("risk_reviewer", system, checker, _calculator(check), respond, model)
