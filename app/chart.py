import json
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import matplotlib.dates as mdates

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


def _plot_colored_price_line(ax, dates, prices, linewidth=2.2, alpha=1.0):
    if len(dates) < 2:
        ax.plot(dates, prices, linewidth=linewidth, alpha=alpha)
        return

    x = mdates.date2num(dates)
    points = list(zip(x, prices))

    segments = []
    colors = []

    for i in range(len(points) - 1):
        p1 = points[i]
        p2 = points[i + 1]
        segments.append([p1, p2])

        if p2[1] >= p1[1]:
            colors.append("#2ca02c")  # green up
        else:
            colors.append("#d62728")  # red down

    lc = LineCollection(segments, colors=colors, linewidths=linewidth, alpha=alpha)
    ax.add_collection(lc)
    ax.autoscale_view()

def generate_history_chart():
    data = _load_history()

    cutoff = datetime.now() - timedelta(days=365 * 6)
    data = [x for x in data if x["date"] >= cutoff]

    dates = [x["date"] for x in data]
    prices_raw = [x["btc_price"] for x in data]
    heat_raw = [x["market_heat"] for x in data]
    pi_cycle_raw = [x["pi_cycle_score"] for x in data]
    top_prob_markers = [x["top_probability"] if x["top_probability"] >= 50 else None for x in data]

    prices = _smooth_series(prices_raw, window=7)
    heat = _smooth_series(heat_raw, window=9)
    pi_cycle = _smooth_series(pi_cycle_raw, window=9)

    fig, ax1 = plt.subplots(figsize=(13, 6))

    # reserve space on the right for info box
    fig.subplots_adjust(right=0.84)

    # faint raw BTC line
    ax1.plot(dates, prices_raw, color="#c7c7c7", linewidth=1, alpha=0.18)

    # main BTC line: green up / red down
    _plot_colored_price_line(ax1, dates, prices, linewidth=2.8, alpha=1.0)
    ax1.plot([], [], color="#2ca02c", linewidth=2.8, label="BTC Price")

    ax1.set_ylabel("BTC Price")
    ax1.set_xlabel("Date")

    ax2 = ax1.twinx()

    # Heat zones background - soft / neutral
    ax2.axhspan(0, 20, color="#eef3f7", alpha=0.18)
    ax2.axhspan(20, 40, color="#e6edf3", alpha=0.18)
    ax2.axhspan(40, 60, color="#dde6ee", alpha=0.18)
    ax2.axhspan(60, 80, color="#d5dfe8", alpha=0.18)
    ax2.axhspan(80, 100, color="#cdd8e2", alpha=0.18)

    # secondary metrics
    ax2.plot(dates, heat_raw, color="#666666", linewidth=1, alpha=0.10)
    ax2.plot(dates, heat, color="#111111", linewidth=1.8, alpha=0.50, label="Market Heat")
    ax2.plot(dates, pi_cycle, color="#1f77b4", linewidth=1.9, alpha=0.90, label="Pi Cycle Score")

    # late-cycle alert markers only
    ax2.scatter(
        dates,
        top_prob_markers,
        color="#c2185b",          # dark pink
        edgecolors="white",
        linewidths=0.7,
        s=48,
        zorder=6,
        alpha=0.95,
        label="Late-Cycle Alerts",
    )

    ax2.set_ylabel("Market Heat / Top Probability")
    ax2.set_ylim(0, 100)

    # halving lines (blue)
    halving_dates = [
        datetime(2012, 11, 28),
        datetime(2016, 7, 9),
        datetime(2020, 5, 11),
        datetime(2024, 4, 20),
    ]

    for h in halving_dates:
        if h >= cutoff:
            ax1.axvline(h, linestyle="--", linewidth=1, color="#1f77b4", alpha=0.55)
            ax1.text(
                h,
                ax1.get_ylim()[1] * 0.97,
                "Bitcoin halving",
                rotation=90,
                fontsize=7,
                color="#1f77b4",
                alpha=0.75,
                verticalalignment="top",
                horizontalalignment="right",
            )

    # events: positive green, negative red
    for event in EVENTS:
        event_dt = datetime.strptime(event["date"], "%Y-%m-%d")
        if event_dt < cutoff:
            continue

        color = "#2ca02c" if event["type"] == "positive" else "#d62728"

        ax1.axvline(event_dt, linestyle=":", linewidth=1, color=color, alpha=0.35)
        ax1.text(
            event_dt,
            ax1.get_ylim()[1] * 0.91,
            event["label"],
            rotation=90,
            fontsize=7,
            color=color,
            alpha=0.72,
            verticalalignment="top",
            horizontalalignment="right",
        )

    # combined legend
    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()

    if handles1 or handles2:
        ax2.legend(
            handles1 + handles2,
            labels1 + labels2,
            loc="upper left",
            framealpha=0.88,
            fontsize=9,
        )

    # latest BTC status text OUTSIDE the chart
    last_date = dates[-1]
    last_price = prices_raw[-1]
    prev_price = prices_raw[-2] if len(prices_raw) >= 2 else prices_raw[-1]

    daily_change_usd = last_price - prev_price
    daily_change_pct = ((last_price - prev_price) / prev_price * 100) if prev_price else 0.0

    if daily_change_usd >= 0:
        change_color = "#2ca02c"
    else:
        change_color = "#d62728"

    # static labels
    fig.text(0.855, 0.20, f"Last Date: {last_date.strftime('%Y-%m-%d')}",
             fontsize=10, ha="right", va="top", color="#222222")
    fig.text(0.855, 0.17, f"BTC Price: ${last_price:,.2f}",
             fontsize=10, ha="right", va="top", color="#222222")

    # colored daily change
    fig.text(0.855, 0.14, "1D Change:",
             fontsize=10, ha="right", va="top", color="#222222")
    fig.text(0.855, 0.11,
             f"{daily_change_usd:+,.2f} USD ({daily_change_pct:+.2f}%)",
             fontsize=10, ha="right", va="top", color=change_color)

    ax1.set_xlim(left=cutoff)

    fig.autofmt_xdate()
    plt.title("BTC Historical Cycle Model")
    plt.tight_layout(rect=[0, 0, 0.84, 1])
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
    ax2.scatter([dates[-1]], [cycle_top_prob[-1]], s=35, zorder=5, color="#c2185b")
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

