# Drawdown Risk Analysis

This project studies downside risk through a drawdown-based decomposition of asset price dynamics.
Rather than focusing on volatility or returns alone, the analysis identifies discrete peak–trough–recovery
events and characterizes both their **depth** and **time to recovery**.

The objective is to quantify tail risk and persistence across major asset classes.

## Methodology

For each asset, adjusted close prices are transformed into a drawdown series relative to the running peak.
Drawdown events are defined as contiguous periods from peak to recovery, allowing extraction of:

- Maximum drawdown depth
- Peak-to-trough duration
- Trough-to-recovery duration
- Total drawdown length

This event-based approach separates magnitude risk from temporal risk.

## Data

Daily adjusted close prices are sourced from Yahoo Finance for the following ETFs:

- SPY (US equities)
- QQQ (US growth equities)
- IWM (US small-cap equities)
- TLT (US long-duration bonds)
- GLD (Gold)

## Figures

### Drawdown Depth vs Time to Recovery
![Depth vs Recovery](figures/depth_vs_recovery.png)

### Drawdowns Over Time
![Drawdowns Over Time](figures/drawdowns_over_time.png)

## Key Observations

- Deeper drawdowns tend to exhibit longer recovery horizons, though the relationship is nonlinear.
- Small-cap equities display the largest downside tail risk.
- Bonds and gold experience shallower drawdowns but materially longer recovery times.
- Drawdown depth and recovery duration capture orthogonal dimensions of risk not reflected in volatility.

## Extensions

Monte Carlo simulations are used to assess the distribution of future drawdowns under stochastic return dynamics.
