from __future__ import annotations

import pandas as pd
import numpy as np


def compute_drawdown(prices: pd.Series) -> pd.DataFrame:
    """
    Compute running peak and drawdown series for a single price series.
    """
    prices = prices.dropna()
    peak = prices.cummax()
    drawdown = prices / peak - 1.0

    return pd.DataFrame(
        {
            "price": prices,
            "peak": peak,
            "drawdown": drawdown,
        }
    )


def extract_drawdown_events(prices: pd.Series) -> pd.DataFrame:
    """
    Identify drawdown events: peak -> trough -> recovery.

    Returns one row per drawdown event with depth and durations.
    If the series ends while still underwater, the final event is marked unrecovered.
    """
    dd_df = compute_drawdown(prices)

    P = dd_df["price"]
    peak = dd_df["peak"]
    dd = dd_df["drawdown"]

    events: list[dict] = []
    in_drawdown = False

    peak_date = None
    peak_price = None
    trough_date = None
    trough_dd = 0.0

    for date in dd.index:
        if not in_drawdown:
            # Start a drawdown when we go below the running peak
            if dd.loc[date] < 0:
                in_drawdown = True
                peak_date = peak.loc[:date].idxmax()
                peak_price = peak.loc[date]
                trough_date = date
                trough_dd = dd.loc[date]
        else:
            # Update trough
            if dd.loc[date] < trough_dd:
                trough_dd = dd.loc[date]
                trough_date = date

            # Recovery: price back to prior peak price
            if P.loc[date] >= peak_price:
                recovery_date = date
                events.append(
                    {
                        "peak_date": peak_date,
                        "trough_date": trough_date,
                        "recovery_date": recovery_date,
                        "depth": float(trough_dd),
                        "peak_to_trough_days": (trough_date - peak_date).days,
                        "trough_to_recovery_days": (recovery_date - trough_date).days,
                        "total_days": (recovery_date - peak_date).days,
                        "recovered": True,
                    }
                )

                # Reset state
                in_drawdown = False
                peak_date = peak_price = trough_date = None
                trough_dd = 0.0

    # If the series ends while still in drawdown, record an unrecovered event
    if in_drawdown:
        events.append(
            {
                "peak_date": peak_date,
                "trough_date": trough_date,
                "recovery_date": pd.NaT,
                "depth": float(trough_dd),
                "peak_to_trough_days": (trough_date - peak_date).days,
                "trough_to_recovery_days": np.nan,
                "total_days": np.nan,
                "recovered": False,
            }
        )

    return pd.DataFrame(events)


