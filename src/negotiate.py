"""Runs one negotiation (design.md, section 8): customer vs sales, with the pricing
analyst helping sales and the risk reviewer checking every sales offer.

Usage:  python src/negotiate.py midmerit          (setup A, the baseline)
        python src/negotiate.py midmerit B        (any setup in configs/setups.yaml)
        persona: industrial, midmerit, peaking or datacentre
"""
import truststore
truststore.inject_into_ssl()          # lets Python work alongside Kaspersky

import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()                         # loads ANTHROPIC_API_KEY from .env

from config import load_settings, load_personas, load_setups
from agents import make_customer, make_sales, make_pricing_analyst, make_risk_reviewer
from scoring import provider_score, customer_score, check_risk_rules
from events import EventLog

S = load_settings()
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
MAX_REVIEWS_PER_TURN = 3      # blocked attempts allowed per sales turn before it counts as no deal


def run_negotiation(persona_key: str, setup: str = "A") -> dict:
    persona = load_personas()["personas"][persona_key]
    cfg = load_setups()[setup]
    model = cfg["model"]
    analyst = make_pricing_analyst(persona, model) if cfg["pricing_analyst"] else None
    reviewer = make_risk_reviewer(persona, model) if cfg["risk_reviewer"] else None
    customer = make_customer(persona, cfg["customer_calculator"], model)
    sales = make_sales(persona, analyst, cfg["sales_calculator"], reviewer is not None, model)
    print(f"Setup {setup}: {cfg['description']} ({model})")

    run_id = f"{setup}_{persona_key}_{datetime.now():%Y%m%d_%H%M%S}"
    log = EventLog(run_id, persona_key, setup)
    log.add("negotiation_start", "system", 0, max_rounds=S["max_rounds"],
            description=cfg["description"], model=model,
            agents=["customer", "sales"] + (["pricing_analyst"] if analyst else []) + (["risk_reviewer"] if reviewer else []),
            customer_calculator=cfg["customer_calculator"], sales_calculator=cfg["sales_calculator"])

    deal, sales_offer, customer_counter = None, None, None
    to_sales = "The customer is ready. Open the negotiation with your first offer."

    def show(round_no, who, act):
        print(f"\n[Round {round_no}] {who.upper()} → {act['action'].upper()}")
        print(f"  \"{act['message']}\"")
        if act["offer"]:
            print(f"  Terms: {act['offer'].summary()}")

    def log_action(round_no, who, act):
        log.add(act["action"], who, round_no, message=act["message"],
                offer=act["offer"].model_dump() if act["offer"] else None)

    for round_no in range(1, S["max_rounds"] + 1):
        # --- Sales turn (with risk review before anything reaches the customer) ---
        incoming = f"[Round {round_no} of {S['max_rounds']}]\n{to_sales}"
        for attempt in range(1, MAX_REVIEWS_PER_TURN + 1):
            asked_before = len(sales.consultations)
            calcs_before = len(sales.tool_calls)
            act = sales.take_turn(incoming)

            # Setup C2 only: sales' own calculator checks
            for calc in sales.tool_calls[calcs_before:]:
                if calc["tool"] == "estimate_profit":
                    log.add("sales_calc", "sales", round_no, terms=calc["input"], result=calc["result"])

            # Sales' questions to the analyst, the analyst's calculations, and its answers
            for c in sales.consultations[asked_before:]:
                log.add("ask_analyst", "sales", round_no, question=c["question"], terms=c["terms"])
                for calc in c["analyst_calcs"]:
                    log.add("analyst_calc", "pricing_analyst", round_no, terms=calc["input"], result=calc["result"])
                log.add("analyst_reply", "pricing_analyst", round_no, message=c["answer"])
                print(f"\n[Round {round_no}] SALES → PRICING ANALYST: \"{c['question']}\"")
                print(f"  ANALYST: \"{c['answer']}\"")

            show(round_no, "sales", act)

            # Which terms would this action commit the provider to?
            if act["action"] == "offer":
                terms = act["offer"]
            elif act["action"] == "accept" and customer_counter is not None:
                terms = customer_counter
            else:
                terms = None

            broken = check_risk_rules(terms, persona) if (terms and reviewer) else []
            if not broken:
                log_action(round_no, "sales", act)      # only actions that pass review are logged as offers/accepts
                break
            note = reviewer.take_turn(f"Offer from sales: {terms.summary()}\nRules broken (from the rule checker): {broken}")
            log.add("blocked", "risk_reviewer", round_no, message=note["message"], rules_broken=broken,
                    blocked_action=act["action"], sales_message=act["message"], offer=terms.model_dump())
            print(f"\n[Round {round_no}] RISK REVIEWER → BLOCKED")
            print(f"  \"{note['message']}\"")
            incoming = (f"Your {act['action']} was BLOCKED by the risk reviewer and did not reach the customer.\n"
                        f"Reviewer's note: \"{note['message']}\"\nRevise and try again.")
        else:
            log.add("blocked_out", "risk_reviewer", round_no, attempts=MAX_REVIEWS_PER_TURN)
            print(f"\n[Round {round_no}] Sales was blocked {MAX_REVIEWS_PER_TURN} times in a row. Negotiation ends with no deal.")
            break

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
        calcs_before = len(customer.tool_calls)
        act = customer.take_turn(f"[Round {round_no} of {S['max_rounds']}]\nSales team says: \"{act['message']}\"\nTheir offer: {sales_offer.summary()}")
        for calc in customer.tool_calls[calcs_before:]:
            log.add("customer_calc", "customer", round_no, terms=calc["input"], result=calc["result"])
        show(round_no, "customer", act)
        log_action(round_no, "customer", act)
        if act["action"] == "walk_away":
            break
        if act["action"] == "accept":
            deal = sales_offer
            break
        customer_counter = act["offer"]
        to_sales = f"Customer says: \"{act['message']}\"\nTheir counter-offer: {customer_counter.summary()}"

    # --- Results ---
    print("\n" + "=" * 70)
    result = {"run_id": run_id, "persona": persona_key, "setup": setup, "rounds": round_no,
              "deal": deal.model_dump() if deal else None}
    if deal:
        prov, cust = provider_score(deal, persona), customer_score(deal, persona)
        result.update({"provider_profit_m": round(prov["profit"] / 1e6, 2), "margin": round(prov["margin"], 4),
                       "customer_value_m": round(cust["value"] / 1e6, 2), "within_budget": cust["within_budget"],
                       "rules_broken": check_risk_rules(deal, persona)})
        log.add("deal_closed", "system", round_no, **{k: v for k, v in result.items() if k not in ("run_id", "persona", "setup")})
        print(f"DEAL after {round_no} round(s): {deal.summary()}")
        print(f"  Provider score: ${result['provider_profit_m']}M profit, margin {prov['margin']:.1%}")
        print(f"  Customer score: ${result['customer_value_m']}M savings vs walk-away, within budget: {cust['within_budget']}")
        print(f"  Risk rules broken: {result['rules_broken'] or 'none'}")
    else:
        log.add("no_deal", "system", round_no, rounds=round_no)
        print(f"NO DEAL after {round_no} round(s).")

    LOG_DIR.mkdir(exist_ok=True)
    path = LOG_DIR / f"{run_id}.jsonl"
    log.save(path)
    print(f"\nLog saved: {path}  ({len(log.events)} events)")
    return result


if __name__ == "__main__":
    persona_arg = sys.argv[1] if len(sys.argv) > 1 else "midmerit"
    setup_arg = sys.argv[2] if len(sys.argv) > 2 else "A"
    run_negotiation(persona_arg, setup_arg)
