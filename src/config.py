"""Loads the project's settings and personas from the configs/ folder."""
from pathlib import Path
import yaml

CONFIG_DIR = Path(__file__).resolve().parent.parent / "configs"


def load_settings() -> dict:
    with open(CONFIG_DIR / "settings.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_personas() -> dict:
    with open(CONFIG_DIR / "personas.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_setups() -> dict:
    with open(CONFIG_DIR / "setups.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)["setups"]


if __name__ == "__main__":
    settings = load_settings()
    data = load_personas()
    print("Settings loaded:", len(settings), "entries")
    print("Personas loaded:", ", ".join(data["personas"]))
    print("Setups loaded:", ", ".join(load_setups()))
