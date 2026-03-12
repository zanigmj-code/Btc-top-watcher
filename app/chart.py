import json
from datetime import datetime

import matplotlib.pyplot as plt


def generate_chart():
    with open("history.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    dates = [datetime.strptime(x["date"], "%Y-%m-%d") for x in data]
    prices = [x["btc_price"] for x in data]
    heat = [x.get("market_heat", x.get("top_probability", 0)) for x in data]

    fig, ax1 = plt.subplots(figsize=(10, 5))

    ax1.set_xlabel("Date")
    ax1.set_ylabel("BTC Price")
    ax1.plot(dates, prices, marker="o")

    ax2 = ax1.twinx()
    ax2.set_ylabel("Market Heat / Top Probability")
    ax2.plot(dates, heat, marker="o")

    fig.autofmt_xdate()
    plt.tight_layout()
    plt.savefig("chart.png")
    plt.close()
