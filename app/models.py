from typing import Any, Dict, Optional, Tuple

from app.config import MVRV_NEAR, MVRV_TOP, PUELL_NEAR, PUELL_TOP
from app.indicators import compute_trend_metrics

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

    cycle_decay = get_cycle_decay_multiplier(pi["last_date"])
    trend_decay = get_trend_decay_multiplier(pi["last_date"])
    decay = cycle_decay * trend_decay

    pi_score = round(min(pi_comp["score"], 30) * decay)
    rainbow_score = round(rainbow_comp["score"] * decay)
    mvrv_score = round(mvrv_comp["score"] * decay)
    puell_score = round(puell_comp["score"] * decay)

    total_score = (
        pi_score
        + rainbow_score
        + mvrv_score
        + puell_score
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

def compute_cycle_position(pi: Dict[str, Any]) -> Dict[str, Any]:
    prob = compute_top_probability_components(pi)
    probability = prob["probability"]

    gap = float(pi["gap_pct"])

    if pi["at_or_above"]:
        percent = 100
    elif gap <= 3:
        percent = 92
    elif gap <= 7:
        percent = 80
    elif gap <= 12:
        percent = 68
    elif gap <= 20:
        percent = 55
    elif gap <= 30:
        percent = 42
    elif gap <= 45:
        percent = 28
    else:
        percent = 15

    # phase detection using both cycle position and probability
    if percent < 35 and probability < 25:
        phase = "Early Bull"
    elif percent < 70 and probability < 50:
        phase = "Mid Bull"
    elif percent >= 70 or probability >= 50:
        phase = "Late Bull"
    else:
        phase = "Transition"

    return {
        "percent": percent,
        "phase": phase,
    }


def compute_market_heat_score(pi: Dict[str, Any], trend: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    prob = compute_top_probability_components(pi)

    if trend is None:
        trend = {
            "price_vs_sma200": 1.0,
            "price_vs_sma350": 1.0,
            "return_90d": 0.0,
            "return_180d": 0.0,
            "return_365d": 0.0,
        }

    trend_strength = compute_trend_strength_score(trend)
    acceleration = compute_acceleration_score(trend)
    distribution = compute_distribution_score(trend)

    # 1) Overextension: rainbow + mvrv + puell
    overextension_score = round(
        (
            prob["rainbow"]["score"]
            + prob["mvrv_approx"]["score"]
            + prob["puell_approx"]["score"]
        )
        / 55
        * 35
    )

    # 2) Cycle exhaustion: Pi Cycle is still the strongest top signal
    cycle_exhaustion_score = round((prob["pi_cycle"]["score"] / 45) * 30)

    # 3) Trend / acceleration / distribution are supporting context, not the main driver
    trend_strength_score = round((trend_strength["score"] / 30) * 12)
    acceleration_score = round((acceleration["score"] / 30) * 12)
    distribution_score = round((distribution["score"] / 44) * 11)

    raw_heat = (
        overextension_score
        + cycle_exhaustion_score
        + trend_strength_score
        + acceleration_score
        + distribution_score
    )

    heat = int(max(0, min(100, round(raw_heat))))
    raw_heat_capped = heat

    if heat >= 85:
        state = "OVERHEATED"
    elif heat >= 65:
        state = "HOT"
    elif heat >= 45:
        state = "WARM"
    elif heat >= 25:
        state = "COOL"
    else:
        state = "COLD"

    return {
        "score": heat,
        "state": state,
        "raw_score": raw_heat,
        "raw_score_capped": raw_heat_capped,
        "overextension_score": overextension_score,
        "cycle_exhaustion_score": cycle_exhaustion_score,
        "trend_strength_score": trend_strength_score,
        "acceleration_score": acceleration_score,
        "distribution_score": distribution_score,
        "trend_strength_state": trend_strength["state"],
        "acceleration_state": acceleration["state"],
        "distribution_state": distribution["state"],
    }

from datetime import datetime


def get_cycle_decay_multiplier(date_str: str) -> float:
    dt = datetime.strptime(date_str, "%Y-%m-%d")

    if dt < datetime(2016, 7, 9):
        return 1.00
    elif dt < datetime(2020, 5, 11):
        return 0.88
    elif dt < datetime(2024, 4, 20):
        return 0.76
    else:
        return 0.66
    
def compute_trade_action(heat: float, top_prob: float):
    if top_prob >= 80:
        return "STRONG SELL", 50

    if heat >= 70:
        return "SELL", 25

    if heat >= 55:
        return "REDUCE", 10

    if heat <= 15 and top_prob < 20:
        return "BUY", 20

    if heat <= 25:
        return "ACCUMULATE", 10

    return "HOLD", 0

def get_trend_decay_multiplier(date_str: str) -> float:
    dt = datetime.strptime(date_str, "%Y-%m-%d")

    start = datetime(2016, 1, 1)
    end = datetime(2032, 1, 1)

    if dt <= start:
        return 1.0

    if dt >= end:
        return 0.85

    total = (end - start).days
    progress = (dt - start).days / total

    return 1.0 - (0.15 * progress)

def compute_trend_strength_score(trend: Dict[str, Any]) -> Dict[str, Any]:
    score = 0

    p200 = float(trend["price_vs_sma200"])
    p350 = float(trend["price_vs_sma350"])

    if p200 >= 1.6:
        score += 15
    elif p200 >= 1.35:
        score += 11
    elif p200 >= 1.15:
        score += 7
    elif p200 >= 1.0:
        score += 4

    if p350 >= 2.4:
        score += 15
    elif p350 >= 1.9:
        score += 11
    elif p350 >= 1.4:
        score += 7
    elif p350 >= 1.1:
        score += 4

    if score >= 24:
        state = "Very strong"
    elif score >= 16:
        state = "Strong"
    elif score >= 8:
        state = "Moderate"
    else:
        state = "Weak"

    return {
        "score": score,
        "max_score": 30,
        "state": state,
    }


def compute_acceleration_score(trend: Dict[str, Any]) -> Dict[str, Any]:
    score = 0

    r90 = float(trend["return_90d"])
    r180 = float(trend["return_180d"])
    r365 = float(trend["return_365d"])

    if r90 >= 80:
        score += 10
    elif r90 >= 40:
        score += 7
    elif r90 >= 20:
        score += 4

    if r180 >= 150:
        score += 10
    elif r180 >= 80:
        score += 7
    elif r180 >= 30:
        score += 4

    if r365 >= 250:
        score += 10
    elif r365 >= 120:
        score += 7
    elif r365 >= 50:
        score += 4

    if score >= 24:
        state = "Explosive"
    elif score >= 16:
        state = "Fast"
    elif score >= 8:
        state = "Healthy"
    else:
        state = "Slow"

    return {
        "score": score,
        "max_score": 30,
        "state": state,
    }

def compute_sell_signal(heat: float, top_prob: float) -> Dict[str, Any]:
    if top_prob >= 85 or heat >= 85:
        return {"action": "STRONG SELL", "size": 50, "state": "Extreme"}
    elif top_prob >= 70 or heat >= 70:
        return {"action": "SELL", "size": 25, "state": "Hot"}
    elif top_prob >= 55 or heat >= 55:
        return {"action": "REDUCE", "size": 10, "state": "Warm"}
    else:
        return {"action": "HOLD", "size": 0, "state": "No sell signal"}


def compute_buy_signal(pi: Dict[str, Any], trend: Dict[str, Any], heat: float) -> Dict[str, Any]:
    p200 = float(trend["price_vs_sma200"])
    p350 = float(trend["price_vs_sma350"])
    r90 = float(trend["return_90d"])
    r180 = float(trend["return_180d"])

    score = 0

    if heat <= 20:
        score += 30
    elif heat <= 30:
        score += 18

    if p200 <= 1.05:
        score += 20
    elif p200 <= 1.15:
        score += 10

    if p350 <= 1.10:
        score += 20
    elif p350 <= 1.25:
        score += 10

    if r90 <= 0:
        score += 15
    elif r90 <= 15:
        score += 8

    if r180 <= 0:
        score += 15
    elif r180 <= 25:
        score += 8

    if pi["gap_pct"] >= 25:
        score += 10

    if score >= 70:
        return {"action": "STRONG BUY", "size": 25, "state": "Deep value"}
    elif score >= 45:
        return {"action": "BUY", "size": 15, "state": "Value zone"}
    elif score >= 25:
        return {"action": "ACCUMULATE", "size": 5, "state": "Light buy"}
    else:
        return {"action": "HOLD", "size": 0, "state": "No buy signal"}
    
def compute_distribution_score(trend: Dict[str, Any]) -> Dict[str, Any]:
    score = 0

    p200 = float(trend["price_vs_sma200"])
    p350 = float(trend["price_vs_sma350"])
    r90 = float(trend["return_90d"])
    r180 = float(trend["return_180d"])
    r365 = float(trend["return_365d"])

    if p200 >= 1.45:
        score += 10
    elif p200 >= 1.25:
        score += 6

    if p350 >= 2.0:
        score += 10
    elif p350 >= 1.6:
        score += 6

    if r90 >= 60:
        score += 8
    elif r90 >= 30:
        score += 4

    if r180 >= 120:
        score += 8
    elif r180 >= 70:
        score += 4

    if r365 >= 180:
        score += 8
    elif r365 >= 100:
        score += 4

    if score >= 34:
        state = "Extreme"
    elif score >= 22:
        state = "High"
    elif score >= 12:
        state = "Elevated"
    else:
        state = "Normal"

    return {
        "score": score,
        "max_score": 44,
        "state": state,
    }

