#!/usr/bin/env python3
from math import pi
import os
import json
import time
import argparse
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests

STATE_FILE = os.environ.get("TOPWATCH_STATE_FILE", "topwatch_state.json")

MVRV_NEAR = float(os.environ.get("TOPWATCH_MVRV_NEAR", "6.0"))
MVRV_TOP = float(os.environ.get("TOPWATCH_MVRV_TOP", "7.0"))
PUELL_NEAR = float(os.environ.get("TOPWATCH_PUELL_NEAR", "3.5"))
PUELL_TOP = float(os.environ.get("TOPWATCH_PUELL_TOP", "4.0"))
PI_NEAR_GAP_PCT = float(os.environ.get("TOPWATCH_PI_NEAR_GAP_PCT", "3.0"))

GLASSNODE_BASE = "https://api.glassnode.com/v1/metrics"
COINGECKO_MARKET_CHART = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
def fetch_btc_prices() -> List[Tuple[int, float]]:
    url = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"

    params = {
        "assets": "btc",
        "metrics": "PriceUSD",
        "start_time": "2010-07-18",
        "frequency": "1d",
        "page_size": 10000,
    }

    prices: List[Tuple[int, float]] = []
    next_page_token = None

    while True:
        req_params = dict(params)
        if next_page_token:
            req_params["next_page_token"] = next_page_token

        r = requests.get(url, params=req_params, timeout=30)
        r.raise_for_status()
        payload = r.json()

        rows = payload.get("data", [])
        for row in rows:
            price_raw = row.get("PriceUSD")
            time_raw = row.get("time")

            if price_raw is None or time_raw is None:
                continue

            ts = int(datetime.fromisoformat(time_raw.replace("Z", "+00:00")).timestamp() * 1000)
            prices.append((ts, float(price_raw)))

        next_page_token = payload.get("next_page_token")
        if not next_page_token:
            break

    if len(prices) < 350:
        raise RuntimeError(f"Not enough BTC history downloaded: only {len(prices)} rows")

    prices.sort(key=lambda x: x[0])
    return prices

def sma(values: List[float], window: int) -> List[Optional[float]]:
    out: List[Optional[float]] = [None] * len(values)
    if len(values) < window:
        return out
    running = sum(values[:window])
    out[window - 1] = running / window
    for i in range(window, len(values)):
        running += values[i] - values[i - window]
        out[i] = running / window
    return out


def compute_pi_cycle(prices: List[Tuple[int, float]]) -> Dict[str, Any]:
    closes = [p for _, p in prices]
    sma111 = sma(closes, 111)
    sma350 = sma(closes, 350)

    if sma111[-1] is None or sma350[-1] is None:
        raise RuntimeError("Not enough price history to compute Pi Cycle.")

    upper = sma111[-1]
    lower = sma350[-1] * 2.0
    gap_pct = ((lower - upper) / lower) * 100.0

    crossed = False
    cross_date = None
    for i in range(1, len(closes)):
        a1, b1 = sma111[i - 1], sma350[i - 1]
        a2, b2 = sma111[i], sma350[i]
        if None in (a1, b1, a2, b2):
            continue
        prev_diff = a1 - (b1 * 2.0)
        curr_diff = a2 - (b2 * 2.0)
        if prev_diff <= 0 < curr_diff:
            crossed = True
            cross_date = datetime.fromtimestamp(prices[i][0] / 1000, tz=timezone.utc).date().isoformat()

    near_top = gap_pct <= PI_NEAR_GAP_PCT
    at_or_above = upper >= lower

    return {
        "sma111": upper,
        "sma350x2": lower,
        "gap_pct": gap_pct,
        "near_top": near_top,
        "at_or_above": at_or_above,
        "crossed_historically": crossed,
        "last_cross_date": cross_date,
        "last_price": closes[-1],
        "last_date": datetime.fromtimestamp(prices[-1][0] / 1000, tz=timezone.utc).date().isoformat(),
    }


def _glassnode_get(path: str, api_key: str) -> List[Dict[str, Any]]:
    params = {"a": "BTC", "i": "24h", "api_key": api_key}
    r = requests.get(f"{GLASSNODE_BASE}/{path}", params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, list) or not data:
        raise RuntimeError(f"Unexpected Glassnode response for {path}: {data}")
    return data


def fetch_glassnode_metrics(api_key: str) -> Dict[str, Any]:
    mvrv = _glassnode_get("market/mvrv_z_score", api_key)
    puell = _glassnode_get("indicators/puell_multiple", api_key)
    m = mvrv[-1]
    p = puell[-1]
    return {
        "mvrv": float(m["v"]),
        "mvrv_time": int(m["t"]),
        "puell": float(p["v"]),
        "puell_time": int(p["t"]),
    }


def load_state(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(path: str, state: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def send_telegram(bot_token: str, chat_id: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    r = requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=30)
    r.raise_for_status()


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
def compute_top_probability(pi: Dict[str, Any], metrics: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    score = 0.0
    reasons = []

    # Pi Cycle score
    gap = float(pi["gap_pct"])

    if pi["at_or_above"]:
        score += 45
        reasons.append("Pi Cycle crossed")
    elif gap <= 3:
        score += 35
        reasons.append("Pi Cycle very close")
    elif gap <= 10:
        score += 22
        reasons.append("Pi Cycle close")
    elif gap <= 20:
        score += 12
        reasons.append("Pi Cycle approaching")
    elif gap <= 30:
        score += 6
        reasons.append("Pi Cycle still far but improving")

    # MVRV score
    if metrics is not None:
        mvrv = float(metrics["mvrv"])
        if mvrv >= 7:
            score += 30
            reasons.append("MVRV in top zone")
        elif mvrv >= 6:
            score += 22
            reasons.append("MVRV elevated")
        elif mvrv >= 5:
            score += 14
            reasons.append("MVRV warming up")
        elif mvrv >= 4:
            score += 8
            reasons.append("MVRV moderately elevated")

        # Puell score
        puell = float(metrics["puell"])
        if puell >= 4:
            score += 25
            reasons.append("Puell in top zone")
        elif puell >= 3.5:
            score += 18
            reasons.append("Puell elevated")
        elif puell >= 3:
            score += 10
            reasons.append("Puell warming up")
        elif puell >= 2:
            score += 5
            reasons.append("Puell moderately elevated")

    probability = min(100, round(score))

    if probability >= 80:
        level = "EXTREME"
    elif probability >= 60:
        level = "HIGH"
    elif probability >= 35:
        level = "ELEVATED"
    else:
        level = "LOW"

    return {
        "probability": probability,
        "level": level,
        "score": score,
        "reasons": reasons,
    }

def compute_rainbow_score(pi: Dict[str, Any]) -> Dict[str, Any]:
    price = float(pi["last_price"])

    # Jednoduchý approx model podle vzdálenosti ceny od 350d SMA
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

    # Hrubý proxy model: cena vs 350d průměr
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

    # Hrubý proxy model: cena vs 111d průměr
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

def explain_indicator(name: str, state: str, extra: str = "") -> str:
    explanations = {
        ("Pi Cycle", "Crossed"): "Pi Cycle has crossed. Historically this occurs near the final market top.",
        ("Pi Cycle", "Very close"): "111-day SMA is very close to the 2×350-day SMA. Market may be approaching a cycle top.",
        ("Pi Cycle", "Close"): "Pi Cycle is getting close. This typically occurs in the late phase of a bull run.",
        ("Pi Cycle", "Approaching"): "Bull market is maturing, but a top signal is not confirmed yet.",
        ("Pi Cycle", "Warming up"): "Market momentum is building, but the cycle top is still some distance away.",
        ("Pi Cycle", "Still far"): "The cycle top is still relatively far away according to Pi Cycle.",
        ("Pi Cycle", "Far"): "Based on Pi Cycle, the market top is still far away.",

        ("Rainbow", "RED"): "Historically extreme market euphoria and high probability of a cycle top.",
        ("Rainbow", "ORANGE"): "Market is very overheated and approaching typical top territory.",
        ("Rainbow", "YELLOW"): "Market is heated but not necessarily at the peak yet.",
        ("Rainbow", "LIGHT_GREEN"): "Healthy bull market trend.",
        ("Rainbow", "GREEN"): "Market is in a normal growth phase.",
        ("Rainbow", "BLUE"): "Market is cool with no signs of euphoria.",

        ("MVRV", "Top zone"): "Investors are in extreme profit levels. Historically associated with market tops.",
        ("MVRV", "Very elevated"): "Market profitability is very high.",
        ("MVRV", "Elevated"): "Profitability is rising. Market may start overheating.",
        ("MVRV", "Moderate"): "Typical bull market conditions.",
        ("MVRV", "Healthy"): "Market conditions are healthy without signs of excess.",
        ("MVRV", "Cool"): "Investors are not in extreme profit yet.",

        ("Puell", "Top zone"): "Miner revenues are historically in a top zone.",
        ("Puell", "Very elevated"): "Miner revenues are very high.",
        ("Puell", "Elevated"): "Miner profitability is above average.",
        ("Puell", "Moderate"): "Normal market conditions.",
        ("Puell", "Healthy"): "Healthy miner revenue levels.",
        ("Puell", "Cool"): "Miner revenues are not overheated.",
    }

    return explanations.get((name, state), extra or state)

def format_report(pi: Dict[str, Any], metrics: Optional[Dict[str, Any]], status: str, flags: Dict[str, bool]) -> str:
    prob = compute_top_probability_components(pi)

    pi_pct = round(prob['pi_cycle']['score'] / prob['pi_cycle']['max_score'] * 100)
    rainbow_pct = round(prob['rainbow']['score'] / prob['rainbow']['max_score'] * 100)
    mvrv_pct = round(prob['mvrv_approx']['score'] / prob['mvrv_approx']['max_score'] * 100)
    puell_pct = round(prob['puell_approx']['score'] / prob['puell_approx']['max_score'] * 100)

    lines = []
    lines.append(f"BTC Top Watcher: {status}")
    lines.append(f"Top Probability: {prob['probability']}% ({prob['level']})")
    lines.append(f"Date: {pi['last_date']}")
    lines.append(f"BTC price: ${pi['last_price']:,.2f}")
    lines.append("")

    lines.append("Indicator Breakdown")
    lines.append(
        f"- Pi Cycle: {pi_pct}% "
        f"({prob['pi_cycle']['state']} = {explain_indicator('Pi Cycle', prob['pi_cycle']['state'])})"
    )
    lines.append(
        f"- Rainbow Top: {rainbow_pct}% "
        f"({prob['rainbow']['zone']} = {explain_indicator('Rainbow', prob['rainbow']['zone'])})"
    )
    lines.append(
        f"- MVRV Approx: {mvrv_pct}% "
        f"({prob['mvrv_approx']['state']} = {explain_indicator('MVRV', prob['mvrv_approx']['state'])})"
    )
    lines.append(
        f"- Puell Approx: {puell_pct}% "
        f"({prob['puell_approx']['state']} = {explain_indicator('Puell', prob['puell_approx']['state'])})"
    )
    lines.append("")

    lines.append("Pi Cycle")
    lines.append(f"- 111 SMA: {pi['sma111']:,.2f}")
    lines.append(f"- 2 x 350 SMA: {pi['sma350x2']:,.2f}")
    lines.append(f"- Gap: {pi['gap_pct']:.2f}%")
    lines.append(f"- Near top: {'YES' if flags['pi_near'] else 'NO'}")
    lines.append(f"- Top: {'YES' if flags['pi_top'] else 'NO'}")
    if pi.get("last_cross_date"):
        lines.append(f"- Last historical cross: {pi['last_cross_date']}")
    lines.append("")

    lines.append("Rainbow Top")
    lines.append(f"- Price / 350d SMA: {prob['rainbow']['ratio']:.2f}")
    lines.append(f"- Zone: {prob['rainbow']['zone']}")
    lines.append(f"- State: {prob['rainbow']['state']}")
    lines.append("")

    lines.append("MVRV Approx")
    lines.append(f"- Value: {prob['mvrv_approx']['value']:.2f}")
    lines.append(f"- State: {prob['mvrv_approx']['state']}")
    lines.append("")

    lines.append("Puell Approx")
    lines.append(f"- Value: {prob['puell_approx']['value']:.2f}")
    lines.append(f"- State: {prob['puell_approx']['state']}")
    lines.append("")

    lines.append("Top Drivers")
    for driver in prob["drivers"]:
        lines.append(f"- {driver}")

    return "\n".join(lines)

def run_once(print_only: bool = False) -> str:
    prices = fetch_btc_prices()
    print(f"Downloaded BTC rows: {len(prices)}")
    pi = compute_pi_cycle(prices)

    metrics = None
    api_key = os.environ.get("GLASSNODE_API_KEY")
    if api_key:
        try:
            metrics = fetch_glassnode_metrics(api_key)
        except Exception as e:
            metrics = None
            print(f"[WARN] Glassnode metrics failed: {e}")

    status, flags = classify(pi, metrics)
    report = format_report(pi, metrics, status, flags)

    if print_only:
        return report

    state = load_state(STATE_FILE)
    last_status = state.get("last_status")
    last_sent_date = state.get("last_sent_date")
    today = pi["last_date"]

    should_send = status in {"NEAR_TOP", "TOP_CONFIRMED"} and (status != last_status or today != last_sent_date)

    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if should_send and bot_token and chat_id:
        send_telegram(bot_token, chat_id, report)
        state["last_status"] = status
        state["last_sent_date"] = today
        save_state(STATE_FILE, state)
    elif should_send:
        print("[WARN] Alert state reached, but TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set.")

    return report

def main() -> None:
    parser = argparse.ArgumentParser(description="Monitor BTC cycle-top indicators and alert on nearing top.")
    parser.add_argument("--once", action="store_true", help="Run one check and print the report.")
    parser.add_argument("--watch", action="store_true", help="Run forever and check on an interval.")
    parser.add_argument("--interval-minutes", type=int, default=60, help="Polling interval for --watch mode.")
    args = parser.parse_args()

    if not args.once and not args.watch:
        args.once = True

    if args.once:
        report = run_once(print_only=False)
        print(report)
        with open("last_report.txt", "w", encoding="utf-8") as f:
            f.write(report)
        return

    while True:
        try:
            print(f"[{datetime.now().isoformat(timespec='seconds')}] Running check...")
            report = run_once(print_only=False)
            print(report)
            with open("last_report.txt", "w", encoding="utf-8") as f:
                f.write(report)
        except Exception as e:
            print(f"[ERROR] {e}")
        time.sleep(max(1, args.interval_minutes) * 60)

if __name__ == "__main__":
    main()


