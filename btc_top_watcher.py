#!/usr/bin/env python3
import os
import time
import argparse
from datetime import datetime

from app.config import STATE_FILE
from app.data_fetchers import fetch_btc_prices, fetch_glassnode_metrics, send_telegram
from app.indicators import compute_pi_cycle
from app.models import classify
from app.reporting import format_report
from app.state import load_state, save_state


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

    should_send = status in {"NEAR_TOP", "TOP_CONFIRMED"} and (
        status != last_status or today != last_sent_date
    )

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