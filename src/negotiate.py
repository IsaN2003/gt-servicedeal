"""Runs one negotiation between the customer and sales agents (design.md, section 8).

Usage:  python src/negotiate.py midmerit
        (persona: industrial, midmerit, peaking or datacentre)
"""
import truststore
truststore.inject_into_ssl()          # lets Python work alongside Kaspersky

import json
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()                         # loads ANTHROPIC_API_KEY from .env

from config import load_settings, load_personas
from agents import make_customer, make_sales
from scoring import provider_score, customer_score, check_risk_rules

S = load_settings()
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"


def run_negotiation(persona_key: str) -> dict:
    persona = load_personas()["personas"][persona_key]
    customer, sales = make_customer(persona), make_sales(persona)
    events, deal = [], None
    sales_offer, customer_counter = None, None
    to_sales = "The customer is ready. Open the negotiation with your first offer."

    def log(round_no, who, action):
        offer = action["offer"]
        events.append({"round": round_no, "agent": who, "action": action["action"],
                       "message": action["message"], "offer": offer.model_dump() if offer else None})
        print(f"\n[Round {round_no}] {who.upper()} → {action['action'].upper()}")
        print(f"  \"{action['message']}\"")
        if offer:
            print(f"  Terms: {offer.summary()}")

    for round_no in range(1, S["max_rounds"] + 1):
        # --- Sales turn ---
        act = sales.take_turn(f"[Round {round_no} of {S['max_rounds']}]\n{to_sales}")
        log(round_no, "sales", act)
        if act["action"] == "walk_away":
            break
        if act["action"] == "accept":
            if customer_counter is None:
                to_sales = "There is no counter-offer to accept yet. Make an offer."
                continue
            deal = customer_counter
            break
        sales_offer = act["offer"]

        # --- Customer turn ---
        act = customer.take_turn(f"[Round {round_no} of {S['max_rounds']}]\nSales team says: \"{act['message']}\"\nTheir offer: {sales_offer.summary()}")
        log(round_no, "customer", act)
        if act["action"] == "walk_away":
            break
        if act["action"] == "accept":
            deal = sales_offer
            break
        customer_counter = act["offer"]
        to_sales = f"Customer says: \"{act['message']}\"\nTheir counter-offer: {customer_counter.summary()}"

    # --- Results ---
    print("\n" + "=" * 70)
    result = {"persona": persona_key, "deal": deal.model_dump() if deal else None, "rounds": round_no}
    if deal:
        prov, cust = provider_score(deal, persona), customer_score(deal, persona)
        result.update({"provider_profit_m": round(prov["profit"] / 1e6, 2), "margin": round(prov["margin"], 4),
                       "customer_value_m": round(cust["value"] / 1e6, 2), "within_budget": cust["within_budget"],
                       "rules_broken": check_risk_rules(deal, persona)})
        print(f"DEAL after {round_no} round(s): {deal.summary()}")
        print(f"  Provider score: ${result['provider_profit_m']}M profit, margin {prov['margin']:.1%}")
        print(f"  Customer score: ${result['customer_value_m']}M savings vs walk-away, within budget: {cust['within_budget']}")
        print(f"  Risk rules broken: {result['rules_broken'] or 'none'}")
    else:
        print(f"NO DEAL after {round_no} round(s).")

    LOG_DIR.mkdir(exist_ok=True)
    path = LOG_DIR / f"{persona_key}_{datetime.now():%Y%m%d_%H%M%S}.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for e in events:
            f.write(json.dumps(e) + "\n")
        f.write(json.dumps({"result": result, "sales_tool_calls": sales.tool_calls,
                            "customer_tool_calls": customer.tool_calls}) + "\n")
    print(f"\nLog saved: {path}")
    return result


if __name__ == "__main__":
    run_negotiation(sys.argv[1] if len(sys.argv) > 1 else "midmerit")
