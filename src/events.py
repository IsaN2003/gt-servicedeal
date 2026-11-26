"""Event logging (Day 3, step 4).

Every action in a negotiation is saved as one labelled event: who did it, what
type of action it was, which round, and where that agent is in the deal room.
The log is used for analysis (Day 6) and to replay negotiations in the visual
deal room (Day 6).
"""
import json
from datetime import datetime

# Where each agent normally sits in the deal room
HOME = {
    "customer": "customer_hq",
    "sales": "sales_desk",
    "pricing_analyst": "pricing_lab",
    "risk_reviewer": "risk_office",
    "system": "meeting_room",
}

# Event types, and where the acting agent is when it happens
LOCATION = {
    "negotiation_start": "meeting_room",
    "ask_analyst": "pricing_lab",      # sales walks to the pricing lab
    "analyst_calc": "pricing_lab",
    "analyst_reply": "pricing_lab",
    "customer_calc": "customer_hq",
    "sales_calc": "sales_desk",        # setup C2 only: sales checks numbers at its own desk
    "offer": "meeting_room",           # offers are made in the meeting room
    "counter": "meeting_room",
    "accept": "meeting_room",
    "walk_away": "meeting_room",
    "blocked": "sales_desk",           # the reviewer walks to sales to block an offer
    "blocked_out": "sales_desk",
    "deal_closed": "meeting_room",
    "no_deal": "meeting_room",
}


class EventLog:
    def __init__(self, run_id: str, persona: str, setup: str):
        self.run_id, self.persona, self.setup = run_id, persona, setup
        self.events = []

    def add(self, event_type: str, agent: str, round_no: int, **data) -> dict:
        event = {
            "seq": len(self.events) + 1,                       # order of events
            "time": datetime.now().isoformat(timespec="milliseconds"),
            "run_id": self.run_id, "persona": self.persona, "setup": self.setup,
            "round": round_no,
            "agent": agent,
            "type": event_type,
            "location": LOCATION.get(event_type, HOME.get(agent, "meeting_room")),
            **data,
        }
        self.events.append(event)
        return event

    def save(self, path) -> None:
        with open(path, "w", encoding="utf-8") as f:
            for e in self.events:
                f.write(json.dumps(e) + "\n")
