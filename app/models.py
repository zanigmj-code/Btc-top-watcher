from typing import Any, Dict, Optional, Tuple

from app.config import MVRV_NEAR, MVRV_TOP, PUELL_NEAR, PUELL_TOP


def classify(pi: Dict[str, Any], metrics: Optional[Dict[str, Any]]) -> Tuple[str, Dict[str, bool]]:
    pi_near = bool(pi["near_top"])
    pi_top = bool(pi["at_or_above"])

    mvrv_near = metrics is not None and metrics["mvrv"] >= MVRV_NEAR
    mvrv_top = metrics is not None and metrics["mvrv"] >= MVRV_TOP
    puell_near = metrics is not None and metrics["puell"] >= PUELL_NEAR
    puell_top = metrics is not None and metrics["puell"] >= PUELL_TOP

    near_count = sum([pi_near, mvrv_near, puell_near])
    top_all = all([pi_top, mvrv_top, puell_top]) if metrics is not None else False

    if top_all:
        status = "TOP_CONFIRMED"
    elif near_count >= 2:
        status = "NEAR_TOP"
    else:
        status = "NORMAL"

    return status, {
        "pi_near": pi_near,
        "pi_top": pi_top,
        "mvrv_near": bool(mvrv_near),
        "mvrv_top": bool(mvrv_top),
        "puell_near": bool(puell_near),
        "puell_top": bool(puell_top),
    }


def compute_rainbow_score(pi: Dict[str, Any]) -> Dict[str, Any]:
    price = float(pi["last_price"])
    sma350_base = float(pi["sma350x2"]) / 2.0
    ratio = price / sma350_base if sma350_base > 0 else 0

    if ratio >= 4.5:
        score = 20
        zone = "RED"
        state = "Extreme overextension"
    elif ratio >= 3.5:
        score = 16
        zone = "ORANGE"
        state = "Very overheated"
    elif ratio >= 2.7:
        score = 12
        zone = "YELLOW"
        state = "Heated"
    elif ratio >= 2.0:
        score = 8
        zone = "LIGHT_GREEN"
        state = "Bull trend"
    elif ratio >= 1.4:
        score = 4
        zone = "GREEN"
        state = "Healthy"
    else:
        score = 1
        zone = "BLUE"
        state = "Cool"

    return {
        "score": score,
        "max_score": 20,
        "ratio": ratio,
        "zone": zone,
        "state": state,
    }


def compute_mvrv_approx(pi: Dict[str, Any]) -> Dict[str, Any]:
    price = float(pi["last_price"])
    sma350_base = float(pi["sma350x2"]) / 2.0
    value = price / sma350_base if sma350_base > 0 else 0

    if value >= 3.5:
        score = 20
        state = "Top zone"
    elif value >= 3.0:
        score = 16
        state = "Very elevated"
    elif value >= 2.4:
        score = 12
        state = "Elevated"
    elif value >= 1.8:
        score = 8
        state = "Moderate"
    elif value >= 1.3:
        score = 4
        state = "Healthy"
    else:
        score = 1
        state = "Cool"

    return {
        "score": score,
        "max_score": 20,
        "value": value,
        "state": state,
    }


def compute_puell_approx(pi: Dict[str, Any]) -> Dict[str, Any]:
    price = float(pi["last_price"])
    sma111_val = float(pi["sma111"])
    value = price / sma111_val if sma111_val > 0 else 0

    if value >= 2.4:
        score = 15
        state = "Top zone"
    elif value >= 2.0:
        score = 12
        state = "Very elevated"
    elif value >= 1.6:
        score = 9
        state = "Elevated"
    elif value >= 1.25:
        score = 6
        state = "Moderate"
    elif value >= 1.0:
        score = 3
        state = "Healthy"
    else:
        score = 1
        state = "Cool"

    return {
        "score": score,
        "max_score": 15,
        "value": value,
        "state": state,
    }


def compute_pi_cycle_score(pi: Dict[str, Any]) -> Dict[str, Any]:
    gap = float(pi["gap_pct"])

    if pi["at_or_above"]:
        score = 45
        state = "Crossed"
    elif gap <= 3:
        score = 38
        state = "Very close"
    elif gap <= 7:
        score = 30
        state = "Close"
    elif gap <= 12:
        score = 22
        state = "Approaching"
    elif gap <= 20:
        score = 14
        state = "Warming up"
    elif gap <= 30:
        score = 8
        state = "Still far"
    else:
        score = 2
        state = "Far"

    return {
        "score": score,
        "max_score": 45,
        "gap": gap,
        "state": state,
    }


def compute_top_probability_components(pi: Dict[str, Any]) -> Dict[str, Any]:
    pi_comp = compute_pi_cycle_score(pi)
    rainbow_comp = compute_rainbow_score(pi)
    mvrv_comp = compute_mvrv_approx(pi)
    puell_comp = compute_puell_approx(pi)

    total_score = (
        pi_comp["score"]
        + rainbow_comp["score"]
        + mvrv_comp["score"]
        + puell_comp["score"]
    )

    probability = min(100, round(total_score))

    if probability >= 75:
        level = "EXTREME"
    elif probability >= 50:
        level = "HIGH"
    elif probability >= 25:
        level = "ELEVATED"
    else:
        level = "LOW"

    drivers = []

    if pi_comp["score"] >= 22:
        drivers.append(f"Pi Cycle: {pi_comp['state']}")
    if rainbow_comp["score"] >= 12:
        drivers.append(f"Rainbow: {rainbow_comp['zone']}")
    if mvrv_comp["score"] >= 12:
        drivers.append(f"MVRV Approx: {mvrv_comp['state']}")
    if puell_comp["score"] >= 9:
        drivers.append(f"Puell Approx: {puell_comp['state']}")

    if not drivers:
        drivers.append("No major top signals yet")

    return {
        "probability": probability,
        "level": level,
        "total_score": total_score,
        "pi_cycle": pi_comp,
        "rainbow": rainbow_comp,
        "mvrv_approx": mvrv_comp,
        "puell_approx": puell_comp,
        "drivers": drivers,
    }