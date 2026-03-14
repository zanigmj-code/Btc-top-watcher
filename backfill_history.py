from datetime import datetime, timedelta, timezone
import json
from app.indicators import compute_pi_cycle, compute_trend_metrics

from app.data_fetchers import fetch_btc_prices
from app.indicators import compute_pi_cycle
from app.models import (
    compute_top_probability_components,
    compute_cycle_position,
    compute_market_heat_score,
    compute_pi_cycle_score,
    compute_bottom_probability,
    compute_local_top_probability,
    compute_action_signal,
)



def main():
    prices = fetch_btc_prices()
    print(f"Downloaded total BTC rows: {len(prices)}")

    filtered = prices
    history = []

    for i in range(len(filtered)):
        partial_prices = filtered[: i + 1]

        if len(partial_prices) < 350:
            continue

        try:
            pi = compute_pi_cycle(partial_prices)
            trend = compute_trend_metrics(partial_prices)
            prob = compute_top_probability_components(pi)
            cycle = compute_cycle_position(pi)
            heat = compute_market_heat_score(pi, trend)
            pi_score = compute_pi_cycle_score(pi)
            bottom = compute_bottom_probability(pi, trend)
            local_top = compute_local_top_probability(pi, trend)
            action = compute_action_signal(pi, trend)

            history.append({
                "date": pi["last_date"],
                "btc_price": round(pi["last_price"], 2),
                "top_probability": prob["probability"],
                "market_heat": heat["score"],
                "cycle_position": cycle["percent"],
                "cycle_phase": cycle["phase"],
                "pi_cycle_score": pi_score["score"],
                "bottom_probability": bottom["probability"],
                "local_top_probability": local_top["probability"],
                "action": action["action"],
                "action_size": action["size"],
                "action_confidence": action["confidence"],
                "action_bias": action["bias"],
            })

        except Exception as e:
            print(f"[WARN] Skipping row {i}: {e}")
            continue

    print(f"Prepared history rows: {len(history)}")
    if history:
        print(f"First row date: {history[0]['date']}")
        print(f"Last row date: {history[-1]['date']}")

    with open("history.json", "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

    print(f"Backfilled {len(history)} rows into history.json")


if __name__ == "__main__":
    main()