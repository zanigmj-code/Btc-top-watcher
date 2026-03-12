import requests
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from app.config import GLASSNODE_BASE


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


def send_telegram(bot_token: str, chat_id: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    r = requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=30)
    r.raise_for_status()