# IMC Prosperity 4: Round 1 Plan

This document outlines the approach for analyzing the historical data and developing a profitable algorithmic trading strategy for Round 1 of the IMC Prosperity 4 competition.

## Background Context

We are participating in a simulation trading game. Our task is to build a Python trading algorithm (a `Trader` class with a `run()` method) that gets called iteratively with market state (order books, trades) and outputs orders to execute. We also need to analyze 6 CSV files containing historical prices and trades over 3 previous "days" (`day_-2`, `day_-1`, `day_0`) to find trading opportunities.

- **Available Products in Round 1 Data**: `INTARIAN_PEPPER_ROOT`, `ASH_COATED_OSMIUM`.
- **Latency / Performance limit**: The `run` method must execute in at most 900ms latency but usually under 100ms.
- **Allowed Libraries**: `pandas`, `numpy`, `statistics`, `math`, `typing`, `jsonpickle`.

## Phase 1: Exploratory Data Analysis (EDA)

Before writing the trading algorithm, we need to understand the characteristics of each asset. We will perform EDA using Python.

### 1. Data Aggregation
- Load the 3 `prices_round_1_day_*.csv` files and concatenate them in chronological order.
- Load the 3 `trades_round_1_day_*.csv` files and concatenate them.
- Ensure correct data types for all columns, standardizing column names if needed.

### 2. Time Series Analysis & Visualizations
We will write a one-off Python script to generate plots (saved as images) for each product to understand market dynamics:
- **Price Trajectory**: Plot the `mid_price` over time. Does it mean-revert or trend?
- **Spread Analysis**: Calculate `ask_price_1 - bid_price_1` over time to see the bid-ask spread to inform our market making minimum spread.
- **Volume Profile**: Visualize `bid_volume` vs `ask_volume` imbalances to detect momentum.
- **Volatility**: Calculate the rolling standard deviation of returns.

### 3. Correlation Analysis
- Plot `INTARIAN_PEPPER_ROOT` vs `ASH_COATED_OSMIUM` to check for cointegration or lead-lag relationships. 

### 4. Trade Execution Analysis
- Analyze the `trades` dataset. At what prices are executions occurring compared to the best bid/ask?
- Calculate average transaction sizes to inform order sizing.

> [!TIP]
> The EDA script will live in the scratch directory and save metric outputs and charts into the artifacts directory so we can easily view the results in the chat.

## Phase 2: Algorithm Strategy Development

Based on typical market regimes for round 1, we will implement specific trading strategies.

### 1. Identify Position Limits
We need to determine the strict position limits for INTARIAN_PEPPER_ROOT and ASH_COATED_OSMIUM defined for Round 1, ensuring our algorithm handles inventory management up to that limit to avoid order rejection.

### 2. Base Strategies 
We will outline the code structure in `trader.py`:
- **Market Making**: For mean-reverting or stable assets. We quote bids and asks around a calculated theoretical fair value while keeping the inventory close to 0 to manage risk (inventory control).
- **Statistical Arbitrage / Pairs Trading**: If we see cointegration between the two assets during EDA, we can trade the ratio or spread between them.
- **Trend Following / Momentum**: If an asset trends strongly, we might employ short-term moving average crossovers.

### 3. State Management
We will use the `traderData` string property and the `jsonpickle` library to store state between iterations if necessary (e.g., EMA of prices, past inventory). Wait, we can also use simple object variables within the `Trader` class if state persists locally, but `traderData` is required for safe deserialization on AWS Lambda.

## Phase 3: Verification & Local Testing

- Create a local backtesting or runner script `local_runner.py` using the `datamodel.py` structure.
- Feed the historical `prices` CSV data row by row (simulating `TradingState` objects) into our `Trader.run()` method.
- Calculate Profit and Loss (PnL) for the historical days to ensure our strategy makes a positive return.

---

> [!IMPORTANT]
> **User Review Required**
> 1. Do we know the exact position limits for `INTARIAN_PEPPER_ROOT` and `ASH_COATED_OSMIUM`? I couldn't find them explicitly in the `competition_info.md` provided, except references to check the "Rounds section on Wiki". If not, we might need to assume a safe number or look it up.
> 2. Would you like me to use `matplotlib` and `seaborn` for generating the EDA charts, or a specific library?
> 3. Does the EDA plan cover all the specific signals you are curious about for Round 1?

## Next Steps

Once this plan is approved:
1. I will write and run the EDA Python script on the 6 CSV files in `ROUND1/`.
2. I will summarize the statistical findings in a new artifact and present the charts.
3. We will iterate on the trading strategy based on the data findings.
