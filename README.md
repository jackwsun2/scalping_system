# ScalpingSystem

C++17 implementation of a small but complete ETF day-trading research system. It follows the requirements in `doc/Trading-Requirements.md` and intentionally starts with no third-party runtime dependencies, so it can compile and run immediately.

## Features

- Multi-symbol market data interface with CSV loading and generated GLD/SLV sample data.
- Technical indicators: RSI, MACD, Bollinger Bands, ATR, KDJ and VWAP.
- Multi-factor scalping strategy with ATR stop loss and take profit.
- Event-driven backtester with slippage, commission, max holding time, position sizing and daily loss guard.
- Paper-trading replay mode that prints signals and simulated orders.
- Clean C++ interfaces ready for Alpaca, Telegram, SQLite and Dear ImGui/Nana adapters.

## Build

```bash
cmake -S scalping_system -B scalping_system/build
cmake --build scalping_system/build
ctest --test-dir scalping_system/build --output-on-failure
```

## Run

Backtest generated GLD/SLV data:

```bash
./scalping_system/build/scalper --backtest
```

Export sample CSV:

```bash
./scalping_system/build/scalper --write-sample scalping_system/data/sample_bars.csv
```

Backtest a CSV file:

```bash
./scalping_system/build/scalper --backtest --csv scalping_system/data/sample_bars.csv --symbols GLD,SLV
```

Run paper-trading replay:

```bash
./scalping_system/build/scalper --paper --csv scalping_system/data/sample_bars.csv --symbols GLD --delay-ms 100
```

CSV format:

```text
timestamp,symbol,open,high,low,close,volume
2026-05-01 09:30:00,GLD,220.0000,220.2500,219.8000,220.1000,500000
```

## Next Integrations

- `IDataSource`: add Alpaca, Alpha Vantage, Stooq or yfinance-backed adapters.
- `RiskManager`: add broker account and open-order synchronization.
- `run_live_simulation`: replace replay loop with streaming market data and a real execution adapter.
- GUI: build a Dear ImGui/ImPlot monitor against the existing strategy/backtest APIs.

This project is for research and engineering validation only. It is not investment advice.
