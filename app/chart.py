import json
from datetime import datetime

import matplotlib.pyplot as plt
from datetime import datetime, timedelta


def _load_history():
    with open("history.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    parsed = []
    for x in data:
        parsed.append({
            "date": datetime.strptime(x["date"], "%Y-%m-%d"),
            "btc_price": x["btc_price"],
            "market_heat": x.get("market_heat", x.get("top_probability", 0)),
            "top_probability": x.get("top_probability", 0),
            "pi_cycle_score": x.get("pi_cycle_score", 0),
        })

    return parsed


def generate_history_chart():
    data = _load_history()

    cutoff = datetime.now() - timedelta(days=365 * 10)
    data = [x for x in data if x["date"] >= cutoff]

    dates = [x["date"] for x in data]
    prices = [x["btc_price"] for x in data]
    heat = [x["market_heat"] for x in data]
    pi_cycle = [x["pi_cycle_score"] for x in data]
    top_prob = [x["top_probability"] if x["top_probability"] >= 80 else None for x in data]

    fig, ax1 = plt.subplots(figsize=(14, 6))

    # BTC price
    ax1.plot(dates, prices, color="#1f77b4", linewidth=2)
    ax1.set_ylabel("BTC Price")
    ax1.set_xlabel("Date")

    # Heat axis
    ax2 = ax1.twinx()

    # heat zones
    ax2.axhspan(0, 20, color="#2c7bb6", alpha=0.15)
    ax2.axhspan(20, 40, color="#abd9e9", alpha=0.15)
    ax2.axhspan(40, 60, color="#ffffbf", alpha=0.15)
    ax2.axhspan(60, 80, color="#fdae61", alpha=0.15)
    ax2.axhspan(80, 100, color="#d7191c", alpha=0.15)

    # market heat
    ax2.plot(dates, heat, color="#2ca02c", linewidth=2, alpha=0.8)
    ax2.plot(dates, pi_cycle, color="#9467bd", linewidth=1.5, alpha=0.9)
    # top probability spikes
    ax2.scatter(dates, top_prob, color="red", s=20, zorder=5)

    ax2.set_ylabel("Market Heat / Top Probability")
    ax2.set_ylim(0, 100)

    # halving lines
    halving_dates = [
        datetime(2012, 11, 28),
        datetime(2016, 7, 9),
        datetime(2020, 5, 11),
        datetime(2024, 4, 20),
    ]

    for h in halving_dates:
        ax1.axvline(h, linestyle="--", linewidth=1, color="gray")

    cutoff = datetime.now() - timedelta(days=365 * 10)
    ax1.set_xlim(left=cutoff)

    fig.autofmt_xdate()
    plt.title("BTC Historical Cycle Model")
    plt.tight_layout()
    plt.savefig("chart_history.png")
    plt.close()

def generate_current_chart(days: int = 90):
    data = _load_history()
    data = data[-days:] if len(data) > days else data

    dates = [x["date"] for x in data]
    prices = [x["btc_price"] for x in data]
    heat = [x["market_heat"] for x in data]
    top_prob = [x["top_probability"] if x["top_probability"] >= 80 else None for x in data]

    fig, ax1 = plt.subplots(figsize=(13, 6))

    # BTC price
    ax1.plot(dates, prices, color="#1f77b4", linewidth=2)
    ax1.set_ylabel("BTC Price")
    ax1.set_xlabel("Date")

    # Market Heat axis
    ax2 = ax1.twinx()

    # heat color zones
    ax2.axhspan(0, 20, color="#2c7bb6", alpha=0.15)
    ax2.axhspan(20, 40, color="#abd9e9", alpha=0.15)
    ax2.axhspan(40, 60, color="#ffffbf", alpha=0.15)
    ax2.axhspan(60, 80, color="#fdae61", alpha=0.15)
    ax2.axhspan(80, 100, color="#d7191c", alpha=0.15)

    # heat line
    ax2.plot(dates, heat, color="#2ca02c", linewidth=2, alpha=0.8)

    # top probability markers
    ax2.scatter(dates, top_prob, color="red", s=25, zorder=5)

    ax2.set_ylabel("Market Heat / Top Probability")
    ax2.set_ylim(0, 100)

    fig.autofmt_xdate()
    plt.title("BTC Current Market Detail")
    plt.tight_layout()
    plt.savefig("chart_current.png")
    plt.close()


def generate_chart():
    generate_history_chart()
    generate_current_chart()

