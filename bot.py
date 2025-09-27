import pandas as pd
from binance.client import Client
from dotenv import load_dotenv
import os
import asyncio
import time
import numpy as np
import json
import ta
from datetime import datetime, timedelta

load_dotenv(override=True)

mainnet_api_key = os.getenv("BINANCE_API_KEY")
mainnet_api_secret = os.getenv("BINANCE_API_SECRET")
testnet_api_key = os.getenv("TESTNET_API_KEY")
testnet_api_secret = os.getenv("TESTNET_SECRET")

class LiveDataManager:
    def __init__(self, symbol, timeframe):
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
        self.last_account_update = 0
    
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
        print(f"Fetching {self.buffer_size} historical candles for {self.symbol}...")
        print(f"Batches needed: {(self.buffer_size + 999) // 1000}")

        all_data = []
        batch_size = 1000
        batches_needed = (self.buffer_size + batch_size - 1) // batch_size
        total_candles_fetched = 0

        for i in range(batches_needed):
            print(f"\n--- Batch {i+1}/{batches_needed} ---")
            
            start_time = None
            end_time = None
            
            if i > 0:
                oldest_candle_time = all_data[0].index[0]
                end_time = int((oldest_candle_time - pd.Timedelta(seconds=1)).timestamp() * 1000)
                print(f"End time: {end_time}")
            
            remaining_candles = self.buffer_size - total_candles_fetched
            current_batch_size = min(batch_size, remaining_candles)
            print(f"Remaining candles: {remaining_candles}")
            print(f"Current batch size: {current_batch_size}")

            try:
                klines = self.data_client.get_klines(
                    symbol=self.symbol,
                    interval=self.timeframe,
                    limit=current_batch_size,
                    startTime=start_time,
                    endTime=end_time
                )
                print(f"API returned {len(klines) if klines else 0} candles")
            except Exception as e:
                print(f"API Error: {e}")
                break
            
            if not klines:
                print("No klines returned, breaking...")
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
            
            print(f"Fetched batch {i+1}/{batches_needed}: {len(df)} candles (Total: {total_candles_fetched})")
            
            if total_candles_fetched >= self.buffer_size:
                print("Reached target candle count, breaking...")
                break
        
        if not all_data:
            raise RuntimeError(f"Failed to fetch historical data for {self.symbol}")
        
        final_df = pd.concat(all_data)
        print(f"✅ Total candles fetched: {len(final_df)}")
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
        import time
        current_time = time.time()
        
        if current_time - self.last_account_update > 300:
            try:
                account = self.trading_client.get_account()
                total_balance = 0
                for balance in account['balances']:
                    free_amount = float(balance['free'])
                    if free_amount > 0:
                        if balance['asset'] in ['USDT', 'USDC', 'FDUSD', 'TUSD', 'DAI', 'USDP']:
                            total_balance += free_amount
                
                self.portfolio_value = total_balance
                self.last_account_update = current_time
                print(f"💰 Portfolio updated: ${self.portfolio_value:.2f}")
            except Exception as e:
                print(f"⚠️ Failed to update portfolio value: {e}")
        
        return self.portfolio_value
    
    def get_actual_position(self):
        try:
            account = self.trading_client.get_account()
            for balance in account['balances']:
                if balance['asset'] == self.symbol.replace('USDT', ''):
                    actual_position = float(balance['free'])
                    if actual_position != self.position:
                        print(f"🔄 Syncing position: {self.position:.6f} → {actual_position:.6f}")
                        self.position = actual_position
                    return actual_position
            return 0
        except Exception as e:
            print(f"⚠️ Failed to get actual position: {e}")
            return self.position
    
    def buy_order(self, quantity):
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
            print(f"✅ Buy order placed: {order['orderId']}")
            self.position = quantity
            self.entry_price = self.data_buffer['close'].iloc[-1]
            return order
        except Exception as e:
            print(f"❌ Buy order failed: {e}")
            return None
    
    def sell_order(self, quantity):
        if quantity <= 0:
            print("❌ Invalid quantity: must be > 0")
            return None
            
        try:
            order = self.trading_client.order_market_sell( 
                symbol=self.symbol,
                quantity=quantity
            )
            print(f"✅ Sell order placed: {order['orderId']}")
            self.position = 0
            self.entry_price = 0
            return order
        except Exception as e:
            print(f"❌ Sell order failed: {e}")
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

async def main():
    data_manager = LiveDataManager("ETHUSDT", "1h")
    data_manager.initialize()
    
    try:
        with open('output/backtest_results.json', 'r') as f:
            backtest_data = json.load(f)
        strategy = backtest_data.get('strategy', {})
    except FileNotFoundError:
        print("❌ Strategy file not found. Please run the CrewAI workflow first.")
        return
    except json.JSONDecodeError:
        print("❌ Invalid strategy file format.")
        return
    
    print(f"🚀 Trading Strategy: {strategy.get('strategy_id')}")
    
    data_manager.get_portfolio_value()
    print(f"📊 Portfolio Value: ${data_manager.portfolio_value:.2f}")
    print(f"📈 Allocation: {strategy.get('allocation', 25)}%")
    print(f"🛡️ Stop Loss: {strategy.get('stop_loss', 3)}%")
    print(f"💰 Take Profit: {strategy.get('take_profit', 8)}%")
    print(f"📍 Current Position: {data_manager.position} {data_manager.symbol}")
    print("-" * 50)
    print("🔄 Starting trading loop... (Press Ctrl+C to stop)")
    print("-" * 50)
    
    try:
        while True:
            new_candle = data_manager.check_for_new_candle()
            
            if new_candle:
                data_manager.update_with_new_candle(new_candle)
                signals = data_manager.check_strategy_signals(strategy)
                data_manager.get_actual_position()
                
                current_price = data_manager.data_buffer['close'].iloc[-1]
                if data_manager.position > 0 and data_manager.entry_price > 0:
                    pnl = ((current_price - data_manager.entry_price) / data_manager.entry_price) * 100
                    print(f"📊 Position: {data_manager.position:.6f} {data_manager.symbol} | P&L: {pnl:+.2f}%")
                elif data_manager.position > 0:
                    print(f"📊 Position: {data_manager.position:.6f} {data_manager.symbol} | P&L: N/A (no entry price)")
                
                print(f"📊 Strategy Conditions Check:")
                print(f"   Price: ${current_price:.2f}")
                print(f"   Entry Signal: {'✅' if signals['entry'] else '❌'} {'Met' if signals['entry'] else 'Not met'}")
                print(f"   Exit Signal: {'✅' if signals['exit'] else '❌'} {'Met' if signals['exit'] else 'Not met'}")
                
                if signals['entry']:
                    print("🟢 ENTRY SIGNAL!")
                    print(f"   Entry Rules: {strategy.get('entry_rules')}")
                    
                    current_price = data_manager.data_buffer['close'].iloc[-1]
                    allocation = strategy.get('allocation', 25) / 100
                    try:
                        portfolio_value = data_manager.portfolio_value
                    except AttributeError:
                        print("❌ Portfolio value not available, skipping trade")
                        continue
                    
                    if current_price > 0:
                        quantity = (portfolio_value * allocation) / current_price
                        quantity = round(quantity, 6)
                    else:
                        print("❌ Invalid price data, skipping trade")
                        continue
    
                    
                    print(f"💰 Attempting to buy {quantity:.6f} {data_manager.symbol} at ${current_price:.2f}")
                    order = data_manager.buy_order(quantity)
                    if order:
                        print(f"🎯 Position opened: {data_manager.position:.6f} {data_manager.symbol}")
                    
                elif signals['exit']:
                    print("🔴 EXIT SIGNAL!")
                    print(f"   Exit Rules: {strategy.get('exit_rules')}")
                    
                    if data_manager.position > 0:
                        print(f"💰 Attempting to sell {data_manager.position:.6f} {data_manager.symbol}")
                        order = data_manager.sell_order(data_manager.position)
                        if order:
                            print(f"🎯 Position closed: {data_manager.symbol}")
                    else:
                        print("⚠️ No position to sell")
                
                print("-" * 50)
                await asyncio.sleep(30)
    
    except KeyboardInterrupt:
        print("\n🛑 Trading stopped by user")
        print(f"📊 Final Position: {data_manager.position:.6f} {data_manager.symbol}")
        if data_manager.position > 0 and data_manager.entry_price > 0:
            current_price = data_manager.data_buffer['close'].iloc[-1]
            pnl = ((current_price - data_manager.entry_price) / data_manager.entry_price) * 100
            print(f"💰 Final P&L: {pnl:+.2f}%")
        elif data_manager.position > 0:
            print(f"💰 Final P&L: N/A (no entry price)")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("🛑 Trading stopped due to error")

if __name__ == "__main__":
    asyncio.run(main())