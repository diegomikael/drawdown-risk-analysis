from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src.data import DEFAULT_TICKERS, fetch_adj_close
from src.risk import compute_drawdown, extract_drawdown_events
from src.simulation import monte_carlo_drawdowns, monte_carlo_paths


FIG_DIR = Path("figures")
OUT_DIR = Path("outputs")


def summarize_events(all_events: pd.DataFrame) -> pd.DataFrame:
    """Aggregate drawdown event stats by ticker."""
    g = all_events.groupby("ticker", dropna=False)

    summary = pd.DataFrame(
        {
            "n_events": g.size(),
            "worst_depth": g["depth"].min(),                 # most negative
            "avg_depth": g["depth"].mean(),
            "longest_total_days": g["total_days"].max(),
            "avg_total_days": g["total_days"].mean(),
        }
    ).reset_index()

    return summary.sort_values("worst_depth")  # most negative at top


def plot_depth_vs_recovery(all_events: pd.DataFrame, outpath: Path) -> None:
    """Scatter: drawdown depth vs time to recovery."""
    plt.figure(figsize=(10, 6))

    for ticker, df in all_events.groupby("ticker"):
        plt.scatter(df["depth"], df["trough_to_recovery_days"], label=ticker, alpha=0.7)

    plt.title("Drawdown Depth vs Time to Recovery")
    plt.xlabel("Depth (more negative = worse)")
    plt.ylabel("Days to Recover")
    plt.legend()
    plt.tight_layout()
    plt.savefig(outpath, dpi=150)
    plt.close()


def plot_drawdowns_over_time(prices: pd.DataFrame, outpath: Path) -> None:
    """Plot drawdown series over time for each ticker."""
    plt.figure(figsize=(12, 6))

    for ticker in prices.columns:
        dd_df = compute_drawdown(prices[ticker])
        plt.plot(dd_df.index, dd_df["drawdown"], label=ticker)

    plt.title("Drawdowns Over Time")
    plt.xlabel("Date")
    plt.ylabel("Drawdown (relative to running peak)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(outpath, dpi=150)
    plt.close()


def plot_mc_maxdd_hist(
    prices: pd.Series,
    ticker: str,
    horizon_days: int,
    n_sims: int,
    seed: int | None,
    outpath: Path,
) -> pd.DataFrame:
    """Monte Carlo GBM -> max drawdown distribution + tail stats."""
    paths = monte_carlo_paths(
        prices=prices,
        n_sims=n_sims,
        horizon_days=horizon_days,
        seed=seed,
    )
    max_dd = monte_carlo_drawdowns(paths)

    p1 = float(pd.Series(max_dd).quantile(0.01))
    p5 = float(pd.Series(max_dd).quantile(0.05))
    p50 = float(pd.Series(max_dd).quantile(0.50))

    plt.figure(figsize=(10, 6))
    plt.hist(max_dd, bins=60)
    plt.axvline(p1, linestyle="--", linewidth=2, label=f"1% = {p1:.1%}")
    plt.axvline(p5, linestyle="--", linewidth=2, label=f"5% = {p5:.1%}")
    plt.axvline(p50, linestyle="--", linewidth=2, label=f"Median = {p50:.1%}")
    plt.title(f"Monte Carlo {horizon_days/252:.0f}Y Max Drawdown Distribution ({ticker})")
    plt.xlabel("Max Drawdown")
    plt.ylabel("Frequency")
    plt.legend()
    plt.tight_layout()
    plt.savefig(outpath, dpi=150)
    plt.close()

    return pd.DataFrame(
        {
            "ticker": [ticker],
            "horizon_days": [horizon_days],
            "n_sims": [n_sims],
            "p01_max_drawdown": [p1],
            "p05_max_drawdown": [p5],
            "p50_max_drawdown": [p50],
        }
    )


def main() -> None:
    FIG_DIR.mkdir(exist_ok=True)
    OUT_DIR.mkdir(exist_ok=True)

    # 1) Fetch data
    prices = fetch_adj_close()

    # 2) Extract drawdown events for each ticker
    events_list: list[pd.DataFrame] = []
    for ticker in prices.columns:
        ev = extract_drawdown_events(prices[ticker])
        ev = ev.copy()
        ev["ticker"] = ticker
        events_list.append(ev)

    all_events = pd.concat(events_list, ignore_index=True)

    # Keep only events that actually recovered (your function sets recovered=True for those)
    if "recovered" in all_events.columns:
        all_events = all_events[all_events["recovered"] == True].copy()

    # 3) Save tables
    all_events.to_csv(OUT_DIR / "drawdown_events.csv", index=False)

    summary = summarize_events(all_events)
    summary.to_csv(OUT_DIR / "drawdown_summary.csv", index=False)

    # 4) Save historical figures
    plot_depth_vs_recovery(all_events, FIG_DIR / "depth_vs_recovery.png")
    plot_drawdowns_over_time(prices, FIG_DIR / "drawdowns_over_time.png")

    # 5) Monte Carlo (SPY by default)
    spy = prices["SPY"].dropna()
    mc_tail = plot_mc_maxdd_hist(
        prices=spy,
        ticker="SPY",
        horizon_days=252 * 5,
        n_sims=10_000,
        seed=42,
        outpath=FIG_DIR / "mc_maxdd_dist_SPY.png",
    )
    mc_tail.to_csv(OUT_DIR / "mc_tail_SPY.csv", index=False)

    print("Done.")
    print(f"Figures saved to: {FIG_DIR}/")
    print(f"Outputs saved to: {OUT_DIR}/")


if __name__ == "__main__":
    main()
