import os

STATE_FILE = os.environ.get("TOPWATCH_STATE_FILE", "topwatch_state.json")

MVRV_NEAR = float(os.environ.get("TOPWATCH_MVRV_NEAR", "6.0"))
MVRV_TOP = float(os.environ.get("TOPWATCH_MVRV_TOP", "7.0"))

PUELL_NEAR = float(os.environ.get("TOPWATCH_PUELL_NEAR", "3.5"))
PUELL_TOP = float(os.environ.get("TOPWATCH_PUELL_TOP", "4.0"))

PI_NEAR_GAP_PCT = float(os.environ.get("TOPWATCH_PI_NEAR_GAP_PCT", "3.0"))

GLASSNODE_BASE = "https://api.glassnode.com/v1/metrics"
COINGECKO_MARKET_CHART = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"