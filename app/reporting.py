from typing import Any, Dict, Optional

from app.models import compute_top_probability_components, compute_cycle_position

def explain_indicator(name: str, state: str, extra: str = "") -> str:
    explanations = {
        ("Pi Cycle", "Crossed"): "Pi Cycle has crossed. Historically this occurs near the final market top.",
        ("Pi Cycle", "Very close"): "111-day SMA is very close to the 2×350-day SMA. Market may be approaching a cycle top.",
        ("Pi Cycle", "Close"): "Pi Cycle is getting close. This typically occurs in the late phase of a bull run.",
        ("Pi Cycle", "Approaching"): "Bull market is maturing, but a top signal is not confirmed yet.",
        ("Pi Cycle", "Warming up"): "Market momentum is building, but the cycle top is still some distance away.",
        ("Pi Cycle", "Still far"): "The cycle top is still relatively far away according to Pi Cycle.",
        ("Pi Cycle", "Far"): "Based on Pi Cycle, the market top is still far away.",

        ("Rainbow", "RED"): "Historically extreme market euphoria and high probability of a cycle top.",
        ("Rainbow", "ORANGE"): "Market is very overheated and approaching typical top territory.",
        ("Rainbow", "YELLOW"): "Market is heated but not necessarily at the peak yet.",
        ("Rainbow", "LIGHT_GREEN"): "Healthy bull market trend.",
        ("Rainbow", "GREEN"): "Market is in a normal growth phase.",
        ("Rainbow", "BLUE"): "Market is cool with no signs of euphoria.",

        ("MVRV", "Top zone"): "Investors are in extreme profit levels. Historically associated with market tops.",
        ("MVRV", "Very elevated"): "Market profitability is very high.",
        ("MVRV", "Elevated"): "Profitability is rising. Market may start overheating.",
        ("MVRV", "Moderate"): "Typical bull market conditions.",
        ("MVRV", "Healthy"): "Market conditions are healthy without signs of excess.",
        ("MVRV", "Cool"): "Investors are not in extreme profit yet.",

        ("Puell", "Top zone"): "Miner revenues are historically in a top zone.",
        ("Puell", "Very elevated"): "Miner revenues are very high.",
        ("Puell", "Elevated"): "Miner profitability is above average.",
        ("Puell", "Moderate"): "Normal market conditions.",
        ("Puell", "Healthy"): "Healthy miner revenue levels.",
        ("Puell", "Cool"): "Miner revenues are not overheated.",
    }

    return explanations.get((name, state), extra or state)


def format_report(pi: Dict[str, Any], metrics: Optional[Dict[str, Any]], status: str, flags: Dict[str, bool]) -> str:
    prob = compute_top_probability_components(pi)
    cycle = compute_cycle_position(pi)    
    pi_pct = round(prob["pi_cycle"]["score"] / prob["pi_cycle"]["max_score"] * 100)
    rainbow_pct = round(prob["rainbow"]["score"] / prob["rainbow"]["max_score"] * 100)
    mvrv_pct = round(prob["mvrv_approx"]["score"] / prob["mvrv_approx"]["max_score"] * 100)
    puell_pct = round(prob["puell_approx"]["score"] / prob["puell_approx"]["max_score"] * 100)

    lines = []
    lines.append(f"BTC Top Watcher: {status}")
    lines.append(f"Top Probability: {prob['probability']}% ({prob['level']})")
    lines.append(f"Cycle Position: {cycle['percent']}%")
    lines.append(f"Cycle Phase: {cycle['phase']}")
    lines.append(f"Date: {pi['last_date']}")
    lines.append(f"BTC price: ${pi['last_price']:,.2f}")
    lines.append("")

    lines.append("Indicator Breakdown")
    lines.append(
        f"- Pi Cycle: {pi_pct}% "
        f"({prob['pi_cycle']['state']} = {explain_indicator('Pi Cycle', prob['pi_cycle']['state'])})"
    )
    lines.append(
        f"- Rainbow Top: {rainbow_pct}% "
        f"({prob['rainbow']['zone']} = {explain_indicator('Rainbow', prob['rainbow']['zone'])})"
    )
    lines.append(
        f"- MVRV Approx: {mvrv_pct}% "
        f"({prob['mvrv_approx']['state']} = {explain_indicator('MVRV', prob['mvrv_approx']['state'])})"
    )
    lines.append(
        f"- Puell Approx: {puell_pct}% "
        f"({prob['puell_approx']['state']} = {explain_indicator('Puell', prob['puell_approx']['state'])})"
    )
    lines.append("")

    lines.append("Pi Cycle")
    lines.append(f"- 111 SMA: {pi['sma111']:,.2f}")
    lines.append(f"- 2 x 350 SMA: {pi['sma350x2']:,.2f}")
    lines.append(f"- Gap: {pi['gap_pct']:.2f}%")
    lines.append(f"- Near top: {'YES' if flags['pi_near'] else 'NO'}")
    lines.append(f"- Top: {'YES' if flags['pi_top'] else 'NO'}")
    if pi.get("last_cross_date"):
        lines.append(f"- Last historical cross: {pi['last_cross_date']}")
    lines.append("")

    lines.append("Rainbow Top")
    lines.append(f"- Price / 350d SMA: {prob['rainbow']['ratio']:.2f}")
    lines.append(f"- Zone: {prob['rainbow']['zone']}")
    lines.append(f"- State: {prob['rainbow']['state']}")
    lines.append("")

    lines.append("MVRV Approx")
    lines.append(f"- Value: {prob['mvrv_approx']['value']:.2f}")
    lines.append(f"- State: {prob['mvrv_approx']['state']}")
    lines.append("")

    lines.append("Puell Approx")
    lines.append(f"- Value: {prob['puell_approx']['value']:.2f}")
    lines.append(f"- State: {prob['puell_approx']['state']}")
    lines.append("")

    lines.append("Top Drivers")
    for driver in prob["drivers"]:
        lines.append(f"- {driver}")

    return "\n".join(lines)