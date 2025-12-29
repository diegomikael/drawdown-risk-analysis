from __future__ import annotations

import pandas as pd
import yfinance as yf

DEFAULT_TICKERS = ["SPY", "QQQ", "IWM", "TLT", "GLD"]


def _fetch_adj_close_yahoo(
    tickers: list[str],
    start: str,
    end: str | None,
) -> pd.DataFrame:
    df = yf.download(
        tickers=tickers,
        start=start,
        end=end,
        auto_adjust=False,   # keep explicit "Adj Close"
        progress=False,
        group_by="column",
        actions=False,
        threads=True,
    )

    if df is None or df.empty:
        return pd.DataFrame()

    if isinstance(df.columns, pd.MultiIndex):
        if "Adj Close" not in df.columns.get_level_values(0):
            return pd.DataFrame()
        adj = df["Adj Close"].copy()
    else:
        if "Adj Close" not in df.columns:
            return pd.DataFrame()
        adj = df[["Adj Close"]].copy()
        adj.columns = tickers

    adj.index = pd.to_datetime(adj.index)
    adj = adj.sort_index()
    adj = adj.dropna(how="all")

    return adj


def _fetch_close_stooq(
    tickers: list[str],
    start: str,
) -> pd.DataFrame:
    """
    Fallback data source using Stooq.

    Note: Stooq provides 'Close' (not total-return adjusted like Yahoo 'Adj Close').
    For drawdown mechanics this is still useful, but document the limitation.
    """
    stooq_map = {
        "SPY": "spy.us",
        "QQQ": "qqq.us",
        "IWM": "iwm.us",
        "TLT": "tlt.us",
        "GLD": "gld.us",
    }

    series = []
    for t in tickers:
        s = stooq_map.get(t, t.lower())
        url = f"https://stooq.com/q/d/l/?s={s}&i=d"
        df = pd.read_csv(url)
        if df.empty or "Date" not in df.columns or "Close" not in df.columns:
            continue

        df["Date"] = pd.to_datetime(df["Date"])
        df = df.set_index("Date").sort_index()
        series.append(df["Close"].rename(t))

    if not series:
        return pd.DataFrame()

    prices = pd.concat(series, axis=1)
    prices = prices.loc[prices.index >= pd.to_datetime(start)]
    prices = prices.dropna(how="all")
    return prices


def fetch_adj_close(
    tickers: list[str] = DEFAULT_TICKERS,
    start: str = "2005-01-01",
    end: str | None = None,
    allow_fallback: bool = True,
) -> pd.DataFrame:
    """
    Fetch prices for the given tickers.

    Primary source: Yahoo Finance (Adjusted Close).
    Fallback source: Stooq (Close) if Yahoo fails/returns empty and allow_fallback=True.
    """
    adj = _fetch_adj_close_yahoo(tickers=tickers, start=start, end=end)
    if not adj.empty:
        return adj

    if allow_fallback:
        fallback = _fetch_close_stooq(tickers=tickers, start=start)
        if not fallback.empty:
            return fallback

    raise RuntimeError(
        "No price data downloaded. Yahoo (yfinance) returned empty/blocked and fallback failed."
    )


if __name__ == "__main__":
    prices = fetch_adj_close()
    print(prices.tail())
