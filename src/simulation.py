from __future__ import annotations
import numpy as np
import pandas as pd


def monte_carlo_paths(
    prices: pd.Series,
    n_sims: int = 10_000,
    horizon_days: int = 252,
    seed: int | None = None,
) -> np.ndarray:
    """
    Simulate future price paths using geometric Brownian motion.
    """
    if seed is not None:
        np.random.seed(seed)

    returns = prices.pct_change().dropna()
    mu = returns.mean()
    sigma = returns.std()

    dt = 1 / 252
    paths = np.zeros((horizon_days + 1, n_sims))
    paths[0] = prices.iloc[-1]

    shocks = np.random.normal(
        (mu - 0.5 * sigma**2) * dt,
        sigma * np.sqrt(dt),
        size=(horizon_days, n_sims),
    )

    paths[1:] = paths[0] * np.exp(np.cumsum(shocks, axis=0))
    return paths


def monte_carlo_drawdowns(paths: np.ndarray) -> np.ndarray:
    """
    Compute max drawdown for each simulated path.
    """
    peaks = np.maximum.accumulate(paths, axis=0)
    drawdowns = paths / peaks - 1
    return drawdowns.min(axis=0)
