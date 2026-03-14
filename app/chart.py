import json
from datetime import datetime, timedelta

import matplotlib.pyplot as plt

from app.market_events import EVENTS

def _smooth_series(values, window=5):
    if not values:
        return values

    out = []
    half = window // 2

    for i in range(len(values)):
        start = max(0, i - half)
        end = min(len(values), i + half + 1)
        chunk = [v for v in values[start:end] if v is not None]
        out.append(sum(chunk) / len(chunk) if chunk else None)

    return out


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
            "bottom_probability": x.get("bottom_probability", 0),
            "local_top_probability": x.get("local_top_probability", 0),
            "action": x.get("action", "HOLD"),
            "action_size": x.get("action_size", 0),
            "action_confidence": x.get("action_confidence", 0),
            "action_bias": x.get("action_bias", "NEUTRAL"),
        })

    return parsed

def generate_history_chart():
    data = _load_history()

    cutoff = datetime.now() - timedelta(days=365 * 10)
    data = [x for x in data if x["date"] >= cutoff]

    dates = [x["date"] for x in data]
    prices_raw = [x["btc_price"] for x in data]
    heat_raw = [x["market_heat"] for x in data]
    pi_cycle_raw = [x["pi_cycle_score"] for x in data]
    top_prob_raw = [x["top_probability"] if x["top_probability"] >= 80 else None for x in data]

    prices = _smooth_series(prices_raw, window=9)
    heat = _smooth_series(heat_raw, window=9)
    pi_cycle = _smooth_series(pi_cycle_raw, window=9)

    fig, ax1 = plt.subplots(figsize=(14, 6))

    # price raw + smooth
    ax1.plot(dates, prices_raw, linewidth=1, alpha=0.18)
    ax1.plot(dates, prices, linewidth=2.2)
    ax1.set_ylabel("BTC Price")
    ax1.set_xlabel("Date")

    ax2 = ax1.twinx()

    # heat zones
    ax2.axhspan(0, 20, alpha=0.15)
    ax2.axhspan(20, 40, alpha=0.15)
    ax2.axhspan(40, 60, alpha=0.15)
    ax2.axhspan(60, 80, alpha=0.15)
    ax2.axhspan(80, 100, alpha=0.15)

    # heat raw + smooth
    ax2.plot(dates, heat_raw, linewidth=1, alpha=0.15)
    ax2.plot(dates, heat, linewidth=2, alpha=0.9)
    ax2.plot(dates, pi_cycle, linewidth=1.8, alpha=0.9)

    # top spikes
    ax2.scatter(dates, top_prob_raw, s=18, zorder=5)

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
        ax1.axvline(h, linestyle="--", linewidth=1, color="gray", alpha=0.55)

    # major market events
    for date_str, label in EVENTS.items():
        event_dt = datetime.strptime(date_str, "%Y-%m-%d")
        if event_dt < cutoff:
            continue

        ax1.axvline(event_dt, linestyle=":", linewidth=1, color="purple", alpha=0.22)
        ax1.text(
            event_dt,
            ax1.get_ylim()[1] * 0.93,
            label,
            rotation=90,
            fontsize=7,
            alpha=0.55,
            verticalalignment="top",
            horizontalalignment="right",
        )

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
    prices_raw = [x["btc_price"] for x in data]
    bottom_prob_raw = [x["bottom_probability"] for x in data]
    local_top_prob_raw = [x["local_top_probability"] for x in data]
    cycle_top_prob_raw = [x["top_probability"] for x in data]

    action_score_raw = []
    for x in data:
        action = x["action"]
        if action == "STRONG BUY":
            score = 5
        elif action == "BUY":
            score = 15
        elif action == "ACCUMULATE":
            score = 30
        elif action == "HOLD":
            score = 50
        elif action == "REDUCE":
            score = 65
        elif action == "SELL":
            score = 80
        elif action == "STRONG SELL":
            score = 95
        else:
            score = 50
        action_score_raw.append(score)

    # smoothing
    prices = _smooth_series(prices_raw, window=5)
    action_score = _smooth_series(action_score_raw, window=7)
    bottom_prob = _smooth_series(bottom_prob_raw, window=7)
    local_top_prob = _smooth_series(local_top_prob_raw, window=7)
    cycle_top_prob = _smooth_series(cycle_top_prob_raw, window=7)

    last = data[-1]
    current_action = last["action"]
    current_size = last["action_size"]
    current_bottom = last["bottom_probability"]
    current_local_top = last["local_top_probability"]
    current_cycle_top = last["top_probability"]
    current_conf = last["action_confidence"]

    fig, ax1 = plt.subplots(figsize=(13, 6))

    # raw BTC price faint
    ax1.plot(dates, prices_raw, linewidth=1, alpha=0.20)

    # smoothed BTC price main
    ax1.plot(dates, prices, linewidth=2.4)
    ax1.set_ylabel("BTC Price")
    ax1.set_xlabel("Date")

    ax2 = ax1.twinx()

    # zones
    ax2.axhspan(0, 20, alpha=0.14)
    ax2.axhspan(20, 40, alpha=0.14)
    ax2.axhspan(40, 60, alpha=0.14)
    ax2.axhspan(60, 80, alpha=0.14)
    ax2.axhspan(80, 100, alpha=0.14)

    # raw faint signal lines
    ax2.plot(dates, action_score_raw, linewidth=1, alpha=0.15)
    ax2.plot(dates, bottom_prob_raw, linewidth=1, linestyle="--", alpha=0.15)
    ax2.plot(dates, local_top_prob_raw, linewidth=1, linestyle="--", alpha=0.15)
    ax2.plot(dates, cycle_top_prob_raw, linewidth=1, alpha=0.15)

    # smoothed main lines
    ax2.plot(dates, action_score, linewidth=2.2, label="Action Score")
    ax2.plot(dates, bottom_prob, linewidth=2.0, linestyle="--", label="Bottom Probability")
    ax2.plot(dates, local_top_prob, linewidth=2.0, linestyle="--", label="Local Top Probability")
    ax2.plot(dates, cycle_top_prob, linewidth=1.6, alpha=0.85, label="Cycle Top Probability")

    # markers on latest values
    ax2.scatter([dates[-1]], [action_score[-1]], s=45, zorder=5)
    ax2.scatter([dates[-1]], [bottom_prob[-1]], s=35, zorder=5)
    ax2.scatter([dates[-1]], [local_top_prob[-1]], s=35, zorder=5)

    ax2.set_ylabel("Action / Probability")
    ax2.set_ylim(0, 100)

    info_text = (
        f"Action: {current_action}\n"
        f"Aggressiveness: {current_size}%\n"
        f"Confidence: {current_conf}%\n"
        f"Bottom Prob: {current_bottom}%\n"
        f"Local Top Prob: {current_local_top}%\n"
        f"Cycle Top Prob: {current_cycle_top}%"
    )

    ax1.text(
        0.02,
        0.98,
        info_text,
        transform=ax1.transAxes,
        fontsize=10,
        verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.85),
    )

    ax2.legend(loc="upper right")
    fig.autofmt_xdate()
    plt.title("BTC Action Radar (90 Days)")
    plt.tight_layout()
    plt.savefig("chart_current.png")
    plt.close()



def generate_chart():
    generate_history_chart()
    generate_current_chart()

