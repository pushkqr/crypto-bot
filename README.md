# Crypto Trading Bot

An AI-powered cryptocurrency trading system that combines multi-agent strategy generation with live trading capabilities. Built on [CrewAI](https://crewai.com), this system uses collaborative AI agents to research markets, generate trading strategies, backtest them, and execute live trades on testnet.

## 🚀 Features

### **AI-Powered Strategy Generation**
- **Trending Coin Finder** – Identifies promising cryptocurrencies from news, market reports, and social sentiment
- **Coin Picker** – Selects the best investment opportunity with detailed analysis
- **Strategy Generator & Backtester** – Creates and validates trading strategies using technical indicators (EMA, SMA, RSI, MACD, Bollinger Bands, ATR, VWAP)

### **Live Trading System**
- **Real-time Data Management** – Maintains rolling window of historical data with automatic updates
- **Automated Strategy Execution** – Executes trades based on generated strategies with position tracking
- **Risk Management** – Built-in stop-loss, take-profit, and allocation controls
- **Testnet Integration** – Safe testing environment with Binance testnet
- **Professional Dashboard** – Real-time monitoring interface with live charts and analytics

### **Professional Web Interface**
- **Interactive Charts** – Live price charts with technical indicators and trading signals
- **Portfolio Monitoring** – Real-time holdings, transactions, and P&L tracking
- **Activity Logs** – Comprehensive trading activity and system logs
- **Responsive Design** – Modern UI with Merriweather Sans typography
- **Auto-refresh** – Updates every 30 seconds for real-time data

### **Advanced Capabilities**
- **Generic Strategy Support** – Works with any strategy without code changes
- **Dynamic Signal Evaluation** – Uses `eval()` for flexible rule evaluation
- **Automated Pipeline** – Complete workflow from strategy generation to execution
- **Comprehensive Logging** – Detailed trading logs and performance metrics

## 📊 Strategy Metrics

- **Win Rate** – Percentage of profitable trades
- **Profit Factor** – Ratio of gross profit to gross loss
- **Sharpe Ratio** – Risk-adjusted return measure
- **Max Drawdown** – Maximum peak-to-trough decline
- **Total Return** – Overall portfolio performance
- **Trade Count** – Number of trades executed

## 🛠️ Installation

### Prerequisites
- Python >= 3.10 < 3.14
- [UV](https://docs.astral.sh/uv/) package manager

### Setup
```bash
# Install UV
pip install uv

# Clone and navigate to project
git clone https://github.com/pushkqr/crypto-bot
cd crypto

# Install dependencies
uv sync
source .venv/bin/activate  # Linux/WSL
# or
.venv\Scripts\Activate.ps1  # Windows PowerShell
```

### Environment Variables
Create a `.env` file with your API keys:

```env
# CrewAI & Research
GEMINI_API_KEY=your_gemini_key
SERPER_API_KEY=your_serper_key

# Binance API (Mainnet for data)
BINANCE_API_KEY=your_mainnet_key
BINANCE_API_SECRET=your_mainnet_secret

# Binance Testnet (for trading)
TESTNET_API_KEY=your_testnet_key
TESTNET_SECRET=your_testnet_secret

# Push Notifications
PUSHOVER_TOKEN=your_pushover_token
PUSHOVER_USER=your_pushover_user


## 🚀 Quick Start

```bash
uv run app.py
```
This will:
1. Check for existing strategies
2. Ask if you want to execute them
3. Generate new strategies if needed
4. Launch the professional trading dashboard


This opens a real-time web interface with:
- Live price charts with technical indicators
- Portfolio monitoring and P&L tracking
- Current holdings and recent transactions
- Trading activity logs
- Real-time updates every 30 seconds


## 📁 Project Structure

```
crypto/
├── src/crypto/                 # Core CrewAI system
│   ├── main.py                # Entry points
│   ├── crew.py                # Agent definitions
│   ├── config/                # Agent and task configs
│   └── tools/                 # Custom tools
├── app.py                     # Main pipeline script
├── gui.py                     # Gradio web interface
├── trader.py                  # Complete trading system
├── util.py                    # UI utilities and styling
├── output/                    # Generated strategies & results
└── data/                      # Historical data cache
```

## 🔧 Configuration

### **Agent Configuration** (`src/crypto/config/agents.yaml`)
- Define agent roles, goals, and capabilities
- Customize agent behavior and tools

### **Task Configuration** (`src/crypto/config/tasks.yaml`)
- Define workflow tasks and dependencies
- Set output formats and validation rules

### **Trading Parameters** (`trader.py`)
- Symbol and timeframe settings
- Risk management parameters
- Data buffer size configuration

## 📈 Live Trading

### **Supported Exchanges**
- Binance (Testnet for safe testing)
- Mainnet data fetching for accurate indicators


### **Risk Management**
- Position sizing based on portfolio allocation
- Stop-loss and take-profit levels
- Maximum position limits

## 📊 Output Files

- `output/backtest_results.json` – Strategy performance and rules
- `output/investment_decision.md` – Detailed strategy analysis
- `data/` – Cached historical data for faster access

## 🤝 Contributing

Contributions are welcome!

## 📚 Dependencies

- **CrewAI** – Multi-agent framework for strategy generation
- **python-binance** – Binance API integration for live trading
- **ta** – Technical analysis indicators (EMA, SMA, RSI, MACD, etc.)
- **pandas** – Data manipulation and analysis
- **numpy** – Numerical computing
- **pydantic** – Data validation and serialization
- **gradio** – Web interface framework for dashboard
- **plotly** – Interactive charts and visualizations
- **python-dotenv** – Environment variable management
- **requests** – HTTP requests for API calls
