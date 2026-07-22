from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources


@lru_cache(maxsize=1)
def load_emission_factors() -> dict:
    """Load the bundled, offline emission-factor table (see data/emission_factors.json)."""
    with resources.files("greenledger.data").joinpath("emission_factors.json").open(
        "r", encoding="utf-8"
    ) as f:
        return json.load(f)


def kg_co2e_for(utility_type: str, usage: float) -> float:
    factors = load_emission_factors()
    if utility_type not in factors:
        raise ValueError(f"Unknown utility type: {utility_type}")
    return usage * factors[utility_type]["kg_co2e_per_unit"]
