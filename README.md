# Crypto-Bot

Crypto-Bot is an AI-powered cryptocurrency research and backtesting framework, leveraging multi-agent capabilities to generate, evaluate, and optimize trading strategies. Built on [crewAI](https://crewai.com), Crypto-Bot allows agents to collaborate on complex tasks, from picking trending coins to generating backtest-ready strategies.

## Features

* **Trending Coin Finder** – Identifies promising coins from news, market reports, and social sentiment.
* **Strategy Ideator** – Generates actionable trading strategies using technical indicators like EMA, SMA, RSI, MACD, Bollinger Bands, ATR, and VWAP.
* **Backtester** – Simulates strategy performance using historical OHLCV data, calculates metrics such as profit, drawdown, Sharpe ratio, and provides recommendations.
* **Iterative Refinement** – Backtester can trigger strategy modifications until a satisfactory result is achieved.
* **Structured Outputs** – Returns concise, structured performance metrics compatible with automation.

## Installation

Ensure Python >= 3.10 < 3.14 is installed. This project uses [UV](https://docs.astral.sh/uv/) for package management.

Install `uv`:

```bash
pip install uv
```

Navigate to the project directory and install dependencies:

```bash
crewai install
```

### Environment Variables

Create a `.env` file and add your API keys:

```env
GEMINI_API_KEY=XX
SERPER_API_KEY=XX
TEST_API=XX
TEST_SECRET=XX
BINANCE_API_KEY=XX
BINANCE_API_SECRET=XX
```

## Configuration

* `src/crypto/config/agents.yaml` – Define your agents, roles, and goals.
* `src/crypto/config/tasks.yaml` – Define tasks and workflows for your agents.
* `src/crypto/crew.py` – Add custom logic, tools, and arguments for agents.
* `src/crypto/main.py` – Add custom inputs and run the crew.

## Running Crypto-Bot

Start the AI agents and execute tasks:

```bash
crewai run
```

The framework will process trending coins, generate strategies, backtest them, and output structured performance metrics.

## Output

* Backtest results are stored in `output/backtest_data.json`.
* Metrics include win rate, profit factor, Sharpe ratio, max drawdown, total return, and trade count.

## Contributing

Contributions are welcome!

* Add new indicators or trading strategies.
* Improve backtesting logic or data handling.
* Expand agent capabilities for advanced research.

## Support

* [crewAI Documentation](https://docs.crewai.com)

Harness the power of AI-driven multi-agent research to explore, test, and refine cryptocurrency trading strategies efficiently.
