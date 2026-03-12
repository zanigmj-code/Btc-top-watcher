from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.config import PI_NEAR_GAP_PCT


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
            cross_date = datetime.fromtimestamp(
                prices[i][0] / 1000, tz=timezone.utc
            ).date().isoformat()

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
        "last_date": datetime.fromtimestamp(
            prices[-1][0] / 1000, tz=timezone.utc
        ).date().isoformat(),
    }