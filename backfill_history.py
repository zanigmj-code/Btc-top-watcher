from datetime import datetime, timedelta, timezone
import json

from app.data_fetchers import fetch_btc_prices
from app.indicators import compute_pi_cycle
from app.models import (
    compute_top_probability_components,
    compute_cycle_position,
    compute_market_heat_score,
    compute_pi_cycle_score,
)



def main():
    prices = fetch_btc_prices()

    cutoff = datetime.now(timezone.utc) - timedelta(days=365 * 5)
    cutoff_ms = int(cutoff.timestamp() * 1000)

    filtered = prices

    history = []

    for i in range(len(filtered)):
        partial_prices = filtered[: i + 1]

        if len(partial_prices) < 350:
            continue

        try:
            pi = compute_pi_cycle(partial_prices)
            prob = compute_top_probability_components(pi)
            cycle = compute_cycle_position(pi)
            heat = compute_market_heat_score(pi)
            pi_score = compute_pi_cycle_score(pi)

            history.append({
                "date": pi["last_date"],
                "btc_price": round(pi["last_price"], 2),
                "top_probability": prob["probability"],
                "market_heat": heat["score"],
                "cycle_position": cycle["percent"],
                "cycle_phase": cycle["phase"],
                "pi_cycle_score": pi_score["score"],
            })
        except Exception:
            continue

    with open("history.json", "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

    print(f"Backfilled {len(history)} rows into history.json")


if __name__ == "__main__":
    main()