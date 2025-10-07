import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
from pathlib import Path
from datetime import datetime
from binance.client import Client
from dotenv import load_dotenv
from util import Color
import time
import numpy as np
import ta
import asyncio
import requests

load_dotenv(override=True)

mainnet_api_key = os.getenv("BINANCE_API_KEY")
mainnet_api_secret = os.getenv("BINANCE_API_SECRET")
testnet_api_key = os.getenv("TESTNET_API_KEY")
testnet_api_secret = os.getenv("TESTNET_SECRET")

class CryptoTrader:
    def __init__(self, name: str = "CryptoBot", strategy_file: str = "output/backtest_results.json"):
        self.name = name
        self.strategy_file = strategy_file
        self.strategy = None
        self.performance = None
        self.logs = []
        self.last_refresh_log = 0
        self.last_price_log = 0
        
        self.load_strategy()
        
        symbol = self.strategy.get('coin_symbol', 'BTCUSDT') if self.strategy else 'BTCUSDT'
        timeframe = self.strategy.get('timeframe', '15m') if self.strategy else '15m'
        
        self.symbol = symbol
        self.timeframe = timeframe
        self.buffer_size = self._calculate_buffer_size()
        self.data_client = Client(mainnet_api_key, mainnet_api_secret)
        self.trading_client = Client(testnet_api_key, testnet_api_secret, testnet=True)
        
        self.data_buffer = None
        self.latest_price = None
        self.last_candle_time = None
        self.position = 0
        self.entry_price = 0
        self.portfolio_value = 0
        self.initial_portfolio_value = 0
        self.usdt_balance = 0
        self.last_account_update = 0
        self.transactions = []
        self.position_initialized = False
        
        if self.strategy:
            try:
                self.initialize()
                self.add_log("info", f"Initialized data buffer with {len(self.data_buffer)} candles")
            except Exception as e:
                self.add_log("error", f"Failed to initialize data buffer: {e}")
        
        try:
            self._force_portfolio_update()
            self.add_log("info", f"Portfolio initialized: ${self.portfolio_value:.2f}")
        except Exception as e:
            self.add_log("error", f"Failed to initialize portfolio: {e}")
        
        self.add_log("info", "CryptoTrader initialized")
        if self.strategy:
            self.add_log("info", f"Monitoring {self.symbol} on {self.timeframe} timeframe")
        else:
            self.add_log("error", "No strategy loaded - please run 'uv run run_crew' first")

    def _get_server_time(self):
        try:
            res = self.trading_client.get_server_time()
            server_time = res['serverTime']
            local_time = int(time.time() * 1000)
            time_diff = local_time - server_time
            print(f"🕐 Server time: {server_time} | Local time: {local_time} | Difference: {time_diff}ms")
            return server_time
        except Exception as e:
            try:
                res = self.data_client.get_server_time()
                server_time = res['serverTime']
                local_time = int(time.time() * 1000)
                time_diff = local_time - server_time
                print(f"🕐 Server time (data client): {server_time} | Local time: {local_time} | Difference: {time_diff}ms")
                return server_time
            except Exception as e2:
                self.add_log("error", f"Failed to get server time: {e2}")
                local_time = int(time.time() * 1000)
                print(f"🕐 Using local time as fallback: {local_time}")
                return local_time

    def _force_portfolio_update(self):
        try:
            # Log timestamps before making the API call
            server_time = self._get_server_time()
            local_time = int(time.time() * 1000)
            time_diff = local_time - server_time
            print(f"🕐 Before portfolio update - Server: {server_time}, Local: {local_time}, Diff: {time_diff}ms")
            
            account = self.trading_client.get_account()
            total_balance = 0
            usdt_balance = 0
            coin_balance = 0
            
            for balance in account['balances']:
                free_amount = float(balance['free'])
                if free_amount > 0:
                    if balance['asset'] == 'USDT':
                        usdt_balance = free_amount
                        total_balance += free_amount
                    elif balance['asset'] == self.symbol.replace('USDT', ''):
                        coin_balance = free_amount
                        # Calculate USDT value of coin holdings
                        if hasattr(self, 'data_buffer') and self.data_buffer is not None:
                            current_price = self.data_buffer['close'].iloc[-1]
                            total_balance += coin_balance * current_price
            
            self.portfolio_value = total_balance
            self.usdt_balance = usdt_balance
            self.position = coin_balance
            self.last_account_update = time.time()
            
            if coin_balance > 0 and not self.position_initialized:
                self.add_log("info", f"Position initialized: {coin_balance:.6f} {self.symbol.replace('USDT', '')}")
                if self.entry_price == 0 and hasattr(self, 'data_buffer') and self.data_buffer is not None:
                    self.entry_price = self.data_buffer['close'].iloc[-1]
                    self.add_log("info", f"Entry price set to current market price: {self.entry_price:.2f} USDT")
                self.position_initialized = True
            
            if self.initial_portfolio_value == 0:
                self.initial_portfolio_value = total_balance
                self.add_log("info", f"Initial portfolio value set: {self.initial_portfolio_value:.2f} USDT")
                    
        except Exception as e:
            # Log timestamps when error occurs
            server_time = self._get_server_time()
            local_time = int(time.time() * 1000)
            time_diff = local_time - server_time
            self.add_log("error", f"Failed to update portfolio: {e}")
            print(f"🕐 Error timestamps - Server: {server_time}, Local: {local_time}, Diff: {time_diff}ms")

    def load_strategy(self):
        try:
            if Path(self.strategy_file).exists():
                with open(self.strategy_file, 'r') as f:
                    data = json.load(f)
                self.strategy = data.get('strategy', {})
                self.performance = data.get('performance', {})
                self.add_log("strategy", f"Loaded strategy: {self.strategy.get('strategy_id', 'Unknown')}")
            else:
                self.add_log("error", "No strategy file found")
        except Exception as e:
            self.add_log("error", f"Error loading strategy: {e}")

    def add_log(self, log_type: str, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs.append((timestamp, log_type, message))
        if len(self.logs) > 50:
            self.logs = self.logs[-50:]
        
        print(f"{timestamp} [{log_type.upper()}] {message}")

    def get_title(self) -> str:
        return ""

    def get_strategy_info(self) -> str:
        if not self.strategy:
            return """
            <div class='strategy-info' style='text-align: center; color: #ff6b6b; padding: 20px;'>
                <h3>⚠️ No Strategy Loaded</h3>
                <p>Please run 'uv run run_crew' to generate a trading strategy</p>
            </div>
            """
        
        performance = self.performance or {}
        win_rate = performance.get('win_rate', 0)
        total_return = performance.get('total_return', 0)
        sharpe_ratio = performance.get('sharpe_ratio', 0)
        
        info = f"""
        <div class='strategy-info'>
            <h3>📊 Strategy Configuration</h3>
            <div class='info-grid'>
                <div class='info-item'>
                    <span class='info-label'>Symbol</span>
                    <span class='info-value'>{self.symbol}</span>
                </div>
                <div class='info-item'>
                    <span class='info-label'>Timeframe</span>
                    <span class='info-value'>{self.timeframe}</span>
                </div>
                <div class='info-item'>
                    <span class='info-label'>Allocation</span>
                    <span class='info-value'>{self.strategy.get('allocation', 0)}%</span>
                </div>
                <div class='info-item'>
                    <span class='info-label'>Stop Loss</span>
                    <span class='info-value'>{self.strategy.get('stop_loss', 0)}%</span>
                </div>
                <div class='info-item'>
                    <span class='info-label'>Take Profit</span>
                    <span class='info-value'>{self.strategy.get('take_profit', 0)}%</span>
                </div>
                <div class='info-item'>
                    <span class='info-label'>Win Rate</span>
                    <span class='info-value' style='color: {"#00d4aa" if win_rate > 50 else "#ff6b6b"}'>
                        {win_rate:.1f}%
                    </span>
                </div>
                <div class='info-item'>
                    <span class='info-label'>Total Return</span>
                    <span class='info-value' style='color: {"#00d4aa" if total_return > 0 else "#ff6b6b"}'>
                        {total_return:+.1f}%
                    </span>
                </div>
                <div class='info-item'>
                    <span class='info-label'>Sharpe Ratio</span>
                    <span class='info-value'>{sharpe_ratio:.2f}</span>
                </div>
            </div>
        </div>
        """
        return info

    def get_coin_price_chart(self):
        if not hasattr(self, 'data_buffer') or self.data_buffer is None:
            fig = go.Figure()
            fig.update_layout(
                height=400,
                xaxis_title="Time",
                yaxis_title=f"{self.symbol} Price",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white", size=12),
                title=dict(
                    text=f"{self.symbol} Price Chart",
                    font=dict(size=16, color="white"),
                    x=0.5
                ),
                showlegend=False,
                xaxis=dict(
                    gridcolor="rgba(255,255,255,0.1)",
                    linecolor="rgba(255,255,255,0.2)",
                    tickfont=dict(size=10, color="white")
                ),
                yaxis=dict(
                    gridcolor="rgba(255,255,255,0.1)", 
                    linecolor="rgba(255,255,255,0.2)",
                    tickfont=dict(size=10, color="white")
                )
            )
            fig.add_annotation(
                text="No market data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=14, color="gray"),
                align="center"
            )
            return fig
        
        chart_data = self.data_buffer.tail(200).copy()
        chart_data = chart_data.reset_index()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=chart_data['timestamp'],
            y=chart_data['close'],
            mode='lines',
            name='Price',
            line=dict(color='#00d4aa', width=2),
            hovertemplate='<b>%{x}</b><br>Price: $%{y:.2f}<extra></extra>'
        ))
        
        if 'ema_10' in chart_data.columns:
            fig.add_trace(go.Scatter(
                x=chart_data['timestamp'],
                y=chart_data['ema_10'],
                mode='lines',
                name='EMA 10',
                line=dict(color='#ff6b6b', width=1, dash='dash'),
                opacity=0.7,
                hovertemplate='<b>%{x}</b><br>EMA 10: $%{y:.2f}<extra></extra>'
            ))
        
        if 'ema_20' in chart_data.columns:
            fig.add_trace(go.Scatter(
                x=chart_data['timestamp'],
                y=chart_data['ema_20'],
                mode='lines',
                name='EMA 20',
                line=dict(color='#4dabf7', width=1, dash='dash'),
                opacity=0.7,
                hovertemplate='<b>%{x}</b><br>EMA 20: $%{y:.2f}<extra></extra>'
            ))
        
        if 'bb_upper' in chart_data.columns and 'bb_lower' in chart_data.columns:
            fig.add_trace(go.Scatter(
                x=chart_data['timestamp'],
                y=chart_data['bb_upper'],
                mode='lines',
                name='BB Upper',
                line=dict(color='rgba(255,255,255,0.3)', width=1),
                opacity=0.5,
                showlegend=False,
                hovertemplate='<b>%{x}</b><br>BB Upper: $%{y:.2f}<extra></extra>'
            ))
            
            fig.add_trace(go.Scatter(
                x=chart_data['timestamp'],
                y=chart_data['bb_lower'],
                mode='lines',
                name='BB Lower',
                line=dict(color='rgba(255,255,255,0.3)', width=1),
                opacity=0.5,
                fill='tonexty',
                fillcolor='rgba(255,255,255,0.05)',
                showlegend=False,
                hovertemplate='<b>%{x}</b><br>BB Lower: $%{y:.2f}<extra></extra>'
            ))
        
        signals = self.check_strategy_signals(self.strategy) if self.strategy else {'entry': False, 'exit': False}
        current_price = chart_data['close'].iloc[-1]
        
        if signals['entry']:
            fig.add_trace(go.Scatter(
                x=[chart_data['timestamp'].iloc[-1]],
                y=[current_price],
                mode='markers',
                name='Entry Signal',
                marker=dict(
                    color='#00d4aa',
                    size=15,
                    symbol='triangle-up',
                    line=dict(color='white', width=2)
                ),
                hovertemplate='<b>Entry Signal</b><br>Price: $%{y:.2f}<extra></extra>'
            ))
        
        if signals['exit']:
            fig.add_trace(go.Scatter(
                x=[chart_data['timestamp'].iloc[-1]],
                y=[current_price],
                mode='markers',
                name='Exit Signal',
                marker=dict(
                    color='#ff6b6b',
                    size=15,
                    symbol='triangle-down',
                    line=dict(color='white', width=2)
                ),
                hovertemplate='<b>Exit Signal</b><br>Price: $%{y:.2f}<extra></extra>'
            ))
        
        fig.update_layout(
            height=400,
            margin=dict(l=50, r=30, t=60, b=50),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white", size=12),
            title=dict(
                text=f"{self.symbol} Price Chart with Technical Indicators",
                font=dict(size=16, color="white"),
                x=0.5,
                xanchor="center"
            ),
            xaxis=dict(
                gridcolor="rgba(255,255,255,0.1)",
                linecolor="rgba(255,255,255,0.2)",
                tickformat="%m/%d %H:%M",
                tickangle=45,
                tickfont=dict(size=10, color="white")
            ),
            yaxis=dict(
                gridcolor="rgba(255,255,255,0.1)",
                linecolor="rgba(255,255,255,0.2)", 
                tickformat=",.2f",
                tickfont=dict(size=10, color="white")
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor="rgba(0,0,0,0.5)",
                bordercolor="rgba(255,255,255,0.2)"
            ),
            hovermode='x unified'
        )
        
        return fig

    def get_holdings_df(self) -> pd.DataFrame:
        self.get_portfolio_value()
        self.get_actual_position()
        
        holdings = []
        
        if self.usdt_balance > 0:
            holdings.append({
                "Symbol": "USDT",
                "Quantity": f"{self.usdt_balance:.2f}",
                "Value (USDT)": f"{self.usdt_balance:.2f}"
            })
        
        if self.position > 0:
            current_price = self.get_latest_data()['close'] if hasattr(self, 'data_buffer') and self.data_buffer is not None else 0
            coin_value = self.position * current_price
            coin_symbol = self.symbol.replace('USDT', '')
            holdings.append({
                "Symbol": coin_symbol,
                "Quantity": f"{self.position:.6f}",
                "Value (USDT)": f"{coin_value:.2f}"
            })
        
        if holdings:
            return pd.DataFrame(holdings)
        return pd.DataFrame(columns=["Symbol", "Quantity", "Value (USDT)"])

    def get_transactions_df(self) -> pd.DataFrame:
        if not self.transactions:
            return pd.DataFrame(columns=["Timestamp", "Symbol", "Quantity", "Price", "Type", "Value", "P&L"])
        
        df_data = []
        for tx in self.transactions:
            row = {
                "Timestamp": tx["timestamp"],
                "Symbol": tx["symbol"],
                "Quantity": tx["quantity"],
                "Price": tx["price"],
                "Type": tx["type"],
                "Value": tx["value"]
            }
            if tx["type"] == "SELL" and "pnl" in tx:
                row["P&L"] = tx["pnl"]
            else:
                row["P&L"] = "-"
            df_data.append(row)
        
        return pd.DataFrame(df_data)

    def get_portfolio_value_display(self) -> str:
        self.get_portfolio_value()
        self.get_actual_position()
        
        if self.initial_portfolio_value > 0:
            total_pnl = ((self.portfolio_value - self.initial_portfolio_value) / self.initial_portfolio_value) * 100
            pnl_class = "positive-pnl" if total_pnl >= 0 else "negative-pnl"
            emoji = "📈" if total_pnl >= 0 else "📉"
            
            position_pnl_text = ""
            if self.position > 0 and self.entry_price > 0:
                current_price = self.get_latest_data()['close'] if hasattr(self, 'data_buffer') and self.data_buffer is not None else 0
                if current_price > 0:
                    position_pnl = ((current_price - self.entry_price) / self.entry_price) * 100
                    position_pnl_class = "positive-pnl" if position_pnl >= 0 else "negative-pnl"
                    position_pnl_text = f"""
                    <div class='subtitle' style='font-size: 0.9rem; margin-top: 4px;'>
                        Position P&L: <span class='{position_pnl_class}'>{position_pnl:+.2f}%</span>
                    </div>
                    """
            
            return f"""
            <div class='portfolio-value'>
                <h2>{self.portfolio_value:,.2f} USDT</h2>
                <div class='subtitle'>
                    {emoji} Total P&L: <span class='{pnl_class}'>{total_pnl:+.2f}%</span>
                </div>
                <div class='subtitle' style='font-size: 0.9rem; margin-top: 4px;'>
                    Initial: {self.initial_portfolio_value:,.2f} USDT
                </div>
                {position_pnl_text}
            </div>
            """
        
        position_text = f"Position: {self.position:.6f} {self.symbol.replace('USDT', '')}" if self.position > 0 else "No Position"
        return f"""
        <div class='portfolio-value'>
            <h2>{self.portfolio_value:,.2f} USDT</h2>
            <div class='subtitle'>
                💰 Portfolio Value
            </div>
            <div class='subtitle' style='font-size: 0.9rem; margin-top: 4px;'>
                {position_text}
            </div>
        </div>
        """

    def get_logs_html(self, previous=None) -> str:
        if not self.logs:
            return """
            <div class='logs-console'>
                <div style='color: #666; text-align: center; padding: 20px;'>
                    📝 No logs available
                </div>
            </div>
            """
        
        mapper = {
            "trace": "#87CEEB",
            "strategy": "#00dddd", 
            "trade": "#00dd00",
            "error": "#ff6b6b",
            "info": "#ffd93d",
            "portfolio": "#4dabf7",
        }
        
        response = ""
        for log in self.logs[-15:]:
            timestamp, log_type, message = log
            color = mapper.get(log_type, "#87CEEB")
            icon = {
                "trace": "🔍",
                "strategy": "⚙️", 
                "trade": "💱",
                "error": "❌",
                "info": "ℹ️",
                "portfolio": "💰",
            }.get(log_type, "📝")
            
            response += f"""
            <div style='margin-bottom: 8px; padding: 4px 0; border-bottom: 1px solid rgba(255,255,255,0.05);'>
                <span style='color: #666; font-size: 11px; margin-right: 8px;'>{timestamp}</span>
                <span style='color: {color}; font-weight: 600; margin-right: 8px;'>[{log_type.upper()}]</span>
                <span style='margin-right: 6px;'>{icon}</span>
                <span style='color: #e0e0e0;'>{message}</span>
            </div>
            """
        
        return f"""
        <div class='logs-console'>
            <div style='color: #00d4aa; font-weight: 600; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid #00d4aa;'>
                📊 Live Activity Log
            </div>
            {response}
        </div>
        """


    def refresh(self):
        current_time = time.time()
        
        if current_time - self.last_refresh_log > 120:
            self.add_log("info", "Refreshing data...")
            self.last_refresh_log = current_time
        
        self.get_portfolio_value()
        self.get_actual_position()
        
        if hasattr(self, 'data_buffer') and self.data_buffer is not None:
            new_candle = self.check_for_new_candle()
            if new_candle:
                self.update_with_new_candle(new_candle)
                self._debug_log_metrics()
                self._check_and_execute_trades()
        
        if current_time - self.last_price_log > 300:
            if hasattr(self, 'data_buffer') and self.data_buffer is not None:
                current_price = self.get_latest_data()['close']
                if current_price > 0:
                    self.add_log("info", f"Current {self.symbol} price: ${current_price:.2f}")
                    self.last_price_log = current_time
                    self._debug_log_status()

    def _debug_log_metrics(self):
        if not hasattr(self, 'data_buffer') or self.data_buffer is None:
            return
            
        latest = self.get_latest_data()
        current_price = latest['close']
        
        print(f"\n{'='*60}")
        print(f"📊 LIVE TRADING METRICS - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}")
        
        print(f"💰 Portfolio Value: {self.portfolio_value:.2f} USDT")
        if self.initial_portfolio_value > 0:
            total_pnl = ((self.portfolio_value - self.initial_portfolio_value) / self.initial_portfolio_value) * 100
            print(f"📈 Total P&L: {total_pnl:+.2f}% (Initial: {self.initial_portfolio_value:.2f} USDT)")
        
        print(f"🪙 Position: {self.position:.6f} {self.symbol.replace('USDT', '')}")
        if self.position > 0 and self.entry_price > 0:
            position_pnl = ((current_price - self.entry_price) / self.entry_price) * 100
            print(f"📊 Position P&L: {position_pnl:+.2f}% (Entry: {self.entry_price:.2f} USDT)")
        
        print(f"💵 USDT Balance: {self.usdt_balance:.2f}")
        
        print(f"💲 Current Price: {current_price:.2f} USDT")
        if 'ema_10' in latest and not pd.isna(latest['ema_10']):
            print(f"📈 EMA 10: {latest['ema_10']:.2f}")
        if 'ema_20' in latest and not pd.isna(latest['ema_20']):
            print(f"📈 EMA 20: {latest['ema_20']:.2f}")
        if 'rsi_14' in latest and not pd.isna(latest['rsi_14']):
            print(f"📊 RSI 14: {latest['rsi_14']:.2f}")
        
        if self.strategy:
            signals = self.check_strategy_signals(self.strategy)
            print(f"🎯 Entry Signal: {'✅ YES' if signals['entry'] else '❌ NO'}")
            print(f"🎯 Exit Signal: {'✅ YES' if signals['exit'] else '❌ NO'}")
            
            allocation = self.strategy.get('allocation', 0)
            print(f"⚙️  Allocation: {allocation}%")
                
            if self.position > 0 and self.entry_price > 0:
                stop_loss_percent = self.strategy.get('stop_loss', 0)
                take_profit_percent = self.strategy.get('take_profit', 0)
                stop_loss_price = self.entry_price * (1 - stop_loss_percent / 100)
                take_profit_price = self.entry_price * (1 + take_profit_percent / 100)
                
                print(f"🛡️  Stop Loss: {stop_loss_percent}% (${stop_loss_price:.2f})")
                print(f"🎯 Take Profit: {take_profit_percent}% (${take_profit_price:.2f})")
            else:
                print(f"🛡️  Stop Loss: {self.strategy.get('stop_loss', 0)}%")
                print(f"🎯 Take Profit: {self.strategy.get('take_profit', 0)}%")
        
        print(f"{'='*60}\n")

    def _debug_log_status(self):
        print(f"\n🔄 STATUS UPDATE - {datetime.now().strftime('%H:%M:%S')}")
        print(f"Portfolio: {self.portfolio_value:.2f} USDT | Position: {self.position:.6f} | Price: {self.get_latest_data()['close']:.2f} USDT")
        
        if self.strategy:
            signals = self.check_strategy_signals(self.strategy)
            if signals['entry'] or signals['exit']:
                print(f"🚨 TRADING SIGNAL: {'ENTRY' if signals['entry'] else 'EXIT'}")
        print()

    def force_gui_refresh(self):
        self._force_portfolio_update()
        self.get_actual_position()

    def _check_and_execute_trades(self):
        if not self.strategy:
            print("⚠️ No strategy loaded for trading")
            return
            
        signals = self.check_strategy_signals(self.strategy)
        
        latest = self.get_latest_data()
        current_price = latest['close']
        
        print(f"\n🔍 SIGNAL DEBUG:")
        print(f"   Open: {latest['open']:.2f}")
        print(f"   Close: {latest['close']:.2f}")
        print(f"   Current Position: {self.position:.6f}")
        print(f"   Entry Signal: {signals['entry']}")
        print(f"   Exit Signal: {signals['exit']}")
        
        if self.position > 0 and self.entry_price > 0:
            stop_loss_percent = self.strategy.get('stop_loss', 0)
            take_profit_percent = self.strategy.get('take_profit', 0)
            
            stop_loss_price = self.entry_price * (1 - stop_loss_percent / 100)
            take_profit_price = self.entry_price * (1 + take_profit_percent / 100)
            
            if current_price <= stop_loss_price:
                print(f"\n🛑 STOP LOSS TRIGGERED!")
                print(f"   Entry Price: {self.entry_price:.2f}")
                print(f"   Current Price: {current_price:.2f}")
                print(f"   Stop Loss Price: {stop_loss_price:.2f}")
                print(f"   Loss: {((current_price - self.entry_price) / self.entry_price) * 100:.2f}%")
                self.add_log("strategy", f"🛑 STOP LOSS TRIGGERED! Loss: {((current_price - self.entry_price) / self.entry_price) * 100:.2f}%")
                self.sell_order()
                return
            
            if current_price >= take_profit_price:
                print(f"\n🎯 TAKE PROFIT TRIGGERED!")
                print(f"   Entry Price: {self.entry_price:.2f}")
                print(f"   Current Price: {current_price:.2f}")
                print(f"   Take Profit Price: {take_profit_price:.2f}")
                print(f"   Profit: {((current_price - self.entry_price) / self.entry_price) * 100:.2f}%")
                self.add_log("strategy", f"🎯 TAKE PROFIT TRIGGERED! Profit: {((current_price - self.entry_price) / self.entry_price) * 100:.2f}%")
                self.sell_order()
                return
        
        if signals['entry'] and self.position == 0:
            print(f"\n🎯 ENTRY SIGNAL DETECTED - Attempting to buy...")
            self.add_log("strategy", f"🎯 ENTRY SIGNAL DETECTED - Attempting to buy...")
            self.buy_order()
            
        elif signals['exit'] and self.position > 0:
            print(f"\n🎯 EXIT SIGNAL DETECTED - Attempting to sell...")
            self.add_log("strategy", f"🎯 EXIT SIGNAL DETECTED - Attempting to sell...")
            self.sell_order()
        else:
            print(f"   No action taken - Position: {self.position:.6f}, Entry: {signals['entry']}, Exit: {signals['exit']}")

    def _calculate_buffer_size(self):
        timeframe_minutes = self._timeframe_to_minutes(self.timeframe)
        total_minutes = 42 * 24 * 60
        candles_needed = total_minutes // timeframe_minutes
        return int(candles_needed)
    
    def _timeframe_to_minutes(self, timeframe):
        timeframe_map = {
            "1m": 1, "5m": 5, "15m": 15, "30m": 30,
            "1h": 60, "2h": 120, "4h": 240, "6h": 360,
            "8h": 480, "12h": 720, "1d": 1440, "3d": 4320, "1w": 10080
        }
        return timeframe_map.get(timeframe, 60)
    
    def fetch_historical_data(self):
        all_data = []
        batch_size = 1000
        batches_needed = (self.buffer_size + batch_size - 1) // batch_size
        total_candles_fetched = 0

        for i in range(batches_needed):
            
            start_time = None
            end_time = None
            
            if i > 0:
                oldest_candle_time = all_data[0].index[0]
                end_time = int((oldest_candle_time - pd.Timedelta(seconds=1)).timestamp() * 1000)
            
            remaining_candles = self.buffer_size - total_candles_fetched
            current_batch_size = min(batch_size, remaining_candles)
            
            try:
                klines = self.data_client.get_klines(
                    symbol=self.symbol,
                    interval=self.timeframe,
                    limit=current_batch_size,
                    startTime=start_time,
                    endTime=end_time
                )
            except Exception as e:
                print(f"API Error: {e}")
                break
            
            if not klines:
                break
            
            df = pd.DataFrame(
                klines,
                columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time',
                    'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume',
                    'taker_buy_quote_asset_volume', 'ignore'
                ]
            )
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            df = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
            
            all_data.insert(0, df)
            total_candles_fetched += len(df)
            
            if total_candles_fetched >= self.buffer_size:
                break
        
        if not all_data:
            raise RuntimeError(f"Failed to fetch historical data for {self.symbol}")
        
        final_df = pd.concat(all_data)
        return final_df
    
    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        for period in [10, 20, 50, 100, 200]:
            df[f"ema_{period}"] = df["close"].ewm(span=period).mean()
            df[f"sma_{period}"] = df["close"].rolling(window=period).mean()

        for period in [7, 14]:
            df[f"rsi_{period}"] = ta.momentum.RSIIndicator(df["close"], window=period).rsi()

        macd = ta.trend.MACD(df["close"])
        df["macd"] = macd.macd()
        df["macd_signal"] = macd.macd_signal()
        df["macd_hist"] = macd.macd_diff()

        bb = ta.volatility.BollingerBands(df["close"], window=20)
        df["bb_upper"] = bb.bollinger_hband()
        df["bb_lower"] = bb.bollinger_lband()

        df["atr_14"] = ta.volatility.AverageTrueRange(
            df["high"], df["low"], df["close"], window=14
        ).average_true_range()

        df["vwap"] = (df["volume"] * (df["high"] + df["low"] + df["close"]) / 3).cumsum() / df["volume"].cumsum()

        return df

    def initialize(self):
        self.data_buffer = self.fetch_historical_data()
        self.data_buffer = self.add_indicators(self.data_buffer)
        self.last_candle_time = self.data_buffer.index[-1]
        print(f"✅ Initialized with {len(self.data_buffer)} candles")
        print(f"Latest candle: {self.last_candle_time}")
        print(f"Latest close price: ${self.data_buffer['close'].iloc[-1]:.2f}")

    def check_for_new_candle(self):
        latest_klines = self.data_client.get_klines(
            symbol=self.symbol,
            interval=self.timeframe,
            limit=1
        )
        
        if not latest_klines:
            return False
        
        latest_candle_time = pd.to_datetime(latest_klines[0][0], unit='ms')
        
        if latest_candle_time > self.last_candle_time:
            return latest_klines[0]
        return False
    
    def update_with_new_candle(self, new_candle):
        df = pd.DataFrame([new_candle], columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time',
            'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume',
            'taker_buy_quote_asset_volume', 'ignore'
        ])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        df = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
        
        self.data_buffer = pd.concat([self.data_buffer, df])
        self.data_buffer = self.data_buffer.tail(self.buffer_size)
        self.data_buffer = self.add_indicators(self.data_buffer)
        self.last_candle_time = df.index[0]
        
        print(f"📊 New candle: {self.last_candle_time} | Close: ${self.data_buffer['close'].iloc[-1]:.2f}")
        
        return True
    
    def get_latest_data(self):
        return self.data_buffer.iloc[-1]

    def get_portfolio_value(self):
        current_time = time.time()
        
        if current_time - self.last_account_update > 300:
            try:
                server_time = self._get_server_time()
                local_time = int(time.time() * 1000)
                time_diff = local_time - server_time
                print(f"🕐 Before portfolio value update - Server: {server_time}, Local: {local_time}, Diff: {time_diff}ms")
                
                account = self.trading_client.get_account()
                total_balance = 0
                usdt_balance = 0
                coin_balance = 0
                
                for balance in account['balances']:
                    free_amount = float(balance['free'])
                    if free_amount > 0:
                        if balance['asset'] == 'USDT':
                            usdt_balance = free_amount
                            total_balance += free_amount
                        elif balance['asset'] == self.symbol.replace('USDT', ''):
                            coin_balance = free_amount
                            if hasattr(self, 'data_buffer') and self.data_buffer is not None:
                                current_price = self.data_buffer['close'].iloc[-1]
                                total_balance += coin_balance * current_price
                
                self.portfolio_value = total_balance
                self.usdt_balance = usdt_balance
                self.position = coin_balance
                self.last_account_update = current_time
            except Exception as e:
                server_time = self._get_server_time()
                local_time = int(time.time() * 1000)
                time_diff = local_time - server_time
                print(f"⚠️ Failed to update portfolio value: {e}")
                print(f"🕐 Error timestamps - Server: {server_time}, Local: {local_time}, Diff: {time_diff}ms")
        
        return self.portfolio_value
    
    def get_actual_position(self):
        try:
            account = self.trading_client.get_account()
            coin_symbol = self.symbol.replace('USDT', '')
            
            for balance in account['balances']:
                if balance['asset'] == coin_symbol:
                    actual_position = float(balance['free'])
                    if actual_position != self.position:
                        self.position = actual_position
                    return actual_position
            
            return 0
        except Exception as e:
            return self.position
    
    def buy_order(self, quantity=None):
        if quantity is None:
            if not self.strategy:
                print("❌ No strategy loaded for allocation calculation")
                return None
            
            allocation = self.strategy.get('allocation', 0) / 100.0
            if allocation <= 0:
                print("❌ Invalid allocation percentage")
                return None
            
            if self.usdt_balance <= 0:
                print("❌ No USDT balance available")
                return None
            
            current_price = self.get_latest_data()['close'] if hasattr(self, 'data_buffer') and self.data_buffer is not None else 0
            if current_price <= 0:
                print("❌ Unable to get current price")
                return None
            

            usdt_to_spend = self.usdt_balance * allocation * 0.99
            quantity = usdt_to_spend / current_price
            try:
                exchange_info = self.trading_client.get_exchange_info()
                symbol_info = next((s for s in exchange_info['symbols'] if s['symbol'] == self.symbol), None)
                if symbol_info:
                    filters = symbol_info['filters']
                    lot_size_filter = next((f for f in filters if f['filterType'] == 'LOT_SIZE'), None)
                    if lot_size_filter:
                        step_size = float(lot_size_filter['stepSize'])
                        precision = len(str(step_size).split('.')[-1].rstrip('0'))
                        quantity = round(quantity, precision)
                    else:
                        quantity = round(quantity, 3)
                else:
                    quantity = round(quantity, 3)
            except Exception as e:
                print(f"⚠️ Could not get exchange info, using default precision: {e}")
                quantity = round(quantity, 3)
            
            print(f"💰 Buying with {allocation*100:.1f}% allocation: {usdt_to_spend:.2f} USDT")
            print(f"💰 Calculated quantity: {quantity:.6f} (rounded to 3 decimals)")
        
        if quantity <= 0:
            print("❌ Invalid quantity: must be > 0")
            return None
            
        if self.position > 0:
            print("⚠️ Already in position, skipping buy")
            return None
        
        try:
            order = self.trading_client.order_market_buy(
                symbol=self.symbol,
                quantity=quantity
            )
            print(f"\n🟢 BUY ORDER EXECUTED!")
            print(f"   Order ID: {order['orderId']}")
            print(f"   Quantity: {quantity:.6f} {self.symbol.replace('USDT', '')}")
            print(f"   Price: {self.data_buffer['close'].iloc[-1]:.2f} USDT")
            print(f"   Value: {quantity * self.data_buffer['close'].iloc[-1]:.2f} USDT")
            
            self.add_log("trade", f"🟢 BUY ORDER EXECUTED! Order ID: {order['orderId']}")
            self.add_log("trade", f"Quantity: {quantity:.6f} {self.symbol.replace('USDT', '')}")
            self.add_log("trade", f"Price: {self.data_buffer['close'].iloc[-1]:.2f} USDT")
            self.add_log("trade", f"Value: {quantity * self.data_buffer['close'].iloc[-1]:.2f} USDT")
            
            current_price = self.data_buffer['close'].iloc[-1]
            transaction = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "symbol": self.symbol.replace('USDT', ''),
                "quantity": f"{quantity:.6f}",
                "price": f"{current_price:.2f}",
                "type": "BUY",
                "value": f"{quantity * current_price:.2f}",
                "order_id": order['orderId']
            }
            self.transactions.append(transaction)
            if len(self.transactions) > 20:
                self.transactions = self.transactions[-20:]
            
            self._force_portfolio_update()
            
            
            if self.position > 0:  
                self.entry_price = current_price
                self.add_log("info", f"Entry price set: {self.entry_price:.2f} USDT")
            
            self.add_log("portfolio", f"Portfolio updated after buy: {self.portfolio_value:.2f} USDT")
            
            notification_msg = f"🟢 BUY ORDER EXECUTED!\n{self.symbol.replace('USDT', '')}: {quantity:.6f} @ ${current_price:.2f}\nValue: ${quantity * current_price:.2f} USDT"
            self.push_notification(notification_msg)
            
            return order
        except Exception as e:
            self.add_log("error", f"❌ BUY ORDER FAILED: {e}")
            print(f"\n❌ BUY ORDER FAILED: {e}")
            return None
    
    def sell_order(self, quantity=None):
        if quantity is None:
            if self.position <= 0:
                print("❌ No position to sell")
                return None
            quantity = self.position
            
            try:
                exchange_info = self.trading_client.get_exchange_info()
                symbol_info = next((s for s in exchange_info['symbols'] if s['symbol'] == self.symbol), None)
                if symbol_info:
                    filters = symbol_info['filters']
                    lot_size_filter = next((f for f in filters if f['filterType'] == 'LOT_SIZE'), None)
                    if lot_size_filter:
                        step_size = float(lot_size_filter['stepSize'])
                        precision = len(str(step_size).split('.')[-1].rstrip('0'))
                        quantity = round(quantity, precision)
                    else:
                        quantity = round(quantity, 3)
                else:
                    quantity = round(quantity, 3)
            except Exception as e:
                print(f"⚠️ Could not get exchange info for sell, using default precision: {e}")
                quantity = round(quantity, 3)
            
            print(f"💰 Selling entire position: {quantity:.6f} {self.symbol.replace('USDT', '')}")
        
        if quantity <= 0:
            print("❌ Invalid quantity: must be > 0")
            return None
            
        if self.position < quantity:
            print(f"❌ Insufficient position: {self.position:.6f} < {quantity:.6f}")
            return None
            
        try:
            current_price = self.data_buffer['close'].iloc[-1]
            order = self.trading_client.order_market_sell(
                symbol=self.symbol,
                quantity=quantity
            )
            print(f"\n🔴 SELL ORDER EXECUTED!")
            print(f"   Order ID: {order['orderId']}")
            print(f"   Quantity: {quantity:.6f} {self.symbol.replace('USDT', '')}")
            print(f"   Price: {current_price:.2f} USDT")
            print(f"   Value: {quantity * current_price:.2f} USDT")
            
            self.add_log("trade", f"🔴 SELL ORDER EXECUTED! Order ID: {order['orderId']}")
            self.add_log("trade", f"Quantity: {quantity:.6f} {self.symbol.replace('USDT', '')}")
            self.add_log("trade", f"Price: {current_price:.2f} USDT")
            self.add_log("trade", f"Value: {quantity * current_price:.2f} USDT")
            
            position_pnl_percent = 0
            position_pnl_value = 0
            if self.entry_price > 0:
                position_pnl_percent = ((current_price - self.entry_price) / self.entry_price) * 100
                position_pnl_value = (current_price - self.entry_price) * quantity
                print(f"   P&L: {position_pnl_percent:+.2f}% ({position_pnl_value:+.2f} USDT)")
                self.add_log("trade", f"P&L: {position_pnl_percent:+.2f}% ({position_pnl_value:+.2f} USDT)")
            
            total_pnl_percent = 0
            total_pnl_value = 0
            if self.initial_portfolio_value > 0:
                total_pnl_percent = ((self.portfolio_value - self.initial_portfolio_value) / self.initial_portfolio_value) * 100
                total_pnl_value = self.portfolio_value - self.initial_portfolio_value
            
            transaction = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "symbol": self.symbol.replace('USDT', ''),
                "quantity": f"{quantity:.6f}",
                "price": f"{current_price:.2f}",
                "type": "SELL",
                "value": f"{quantity * current_price:.2f}",
                "order_id": order['orderId'],
                "pnl": f"{position_pnl_percent:+.2f}%",
                "pnl_value": f"{position_pnl_value:+.2f}"
            }
            self.transactions.append(transaction)
            if len(self.transactions) > 20:
                self.transactions = self.transactions[-20:]
            
            self._force_portfolio_update()
            
            if self.position == 0:  
                self.entry_price = 0
                self.add_log("info", f"Entry price reset - position closed")
            
            self.add_log("portfolio", f"Portfolio updated after sell: {self.portfolio_value:.2f} USDT")
            
            position_pnl_text = f"P&L: {position_pnl_percent:+.2f}% (${position_pnl_value:+.2f})" if position_pnl_percent != 0 else "P&L: N/A"
            total_pnl_text = f"P&L: {total_pnl_percent:+.2f}% (${total_pnl_value:+.2f})" if total_pnl_percent != 0 else "Total P&L: N/A"
            notification_msg = f"🔴 SELL ORDER EXECUTED!\n{self.symbol.replace('USDT', '')}: {quantity:.6f} @ ${current_price:.2f}\nValue: ${quantity * current_price:.2f} USDT\nPosition P&L: {position_pnl_text}\nTotal P&L: {total_pnl_text}"
            self.push_notification(notification_msg)
            
            return order
        except Exception as e:
            self.add_log("error", f"❌ SELL ORDER FAILED: {e}")
            print(f"\n❌ SELL ORDER FAILED: {e}")
            return None
    
    def check_strategy_signals(self, strategy):
        latest_data = self.data_buffer.tail(10)
        safe_ns = {"df": latest_data, "np": np}
        
        try:
            entry_signal = pd.Series(
                eval(strategy.get('entry_rules'), {"__builtins__": {}}, safe_ns), 
                index=latest_data.index
            )
            
            exit_signal = pd.Series(
                eval(strategy.get('exit_rules'), {"__builtins__": {}}, safe_ns), 
                index=latest_data.index
            )
            
            return {
                'entry': bool(entry_signal.iloc[-1]),
                'exit': bool(exit_signal.iloc[-1])
            }
            
        except Exception as e:
            print(f"Error evaluating strategy rules: {e}")
            return {'entry': False, 'exit': False}

    def push_notification(self, message):
        """Send a push notification via ntfy"""
        try:
            ntfy_topic = os.getenv("NTFY_TOPIC")
            ntfy_server = os.getenv("NTFY_SERVER", "https://ntfy.sh")
            
            if ntfy_topic:
                ntfy_url = f"{ntfy_server}/{ntfy_topic}"
                
                full_message = f"🚀 {message}"
                
                response = requests.post(ntfy_url, data=full_message.encode(encoding='utf-8'))
                if response.status_code == 200:
                    print(f"📱 Push notification sent: {message}")
                else:
                    print(f"❌ Failed to send notification: {response.status_code} - {response.text}")
            else:
                print(f"⚠️ Push notification not configured: {message}")
                
        except Exception as e:
            print(f"❌ Failed to send push notification: {e}")

                