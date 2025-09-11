import os
from typing import Optional, Type, Dict
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import pandas as pd
import numpy as np
from binance.client import Client
import ta

class FetchOHLCVInput(BaseModel):
    symbol: str = Field(description="Trading pair, e.g., BTCUSDT")
    timeframe: str = Field(description="Candle timeframe, e.g., 1h, 1d")
    start_date: str = Field(description="Start date for fetching data, e.g., '2023-01-01'")
    end_date: str = Field(description="End date for fetching data, e.g., '2023-01-10'")


class FetchOHLCVTool(BaseTool):
    name: str = "FetchOHLCV"
    description: str = (
        "Fetches historical OHLCV data from Binance, enriches it with technical indicators, "
        "and returns the saved CSV path."
    )
    args_schema: Type[BaseModel] = FetchOHLCVInput

    def _run(self, symbol: str, timeframe: str, start_date: str, end_date: Optional[str] = None) -> Dict[str, str]:
        os.makedirs("data", exist_ok=True)
        path = f"data/{symbol}_{timeframe}_enriched.csv"

        if os.path.exists(path):
            return {"ohlcv_csv_path": path}
        
        api_key = os.getenv("BINANCE_API_KEY")
        api_secret = os.getenv("BINANCE_API_SECRET")
        client = Client(api_key, api_secret)

        if end_date is None:
            end_date = pd.Timestamp.utcnow()
        else:
            end_date = pd.to_datetime(end_date)

        parse_sdate = pd.to_datetime(start_date)
        start_timestamp = parse_sdate.strftime('%Y-%m-%d %H:%M:%S')
        end_timestamp = end_date.strftime('%Y-%m-%d %H:%M:%S')

        all_data = []
        current_start_time = start_timestamp
        batch_number = 1

        while current_start_time < end_timestamp:
            try:
                ohlcv_data = client.get_historical_klines(
                    symbol, timeframe, current_start_time, end_timestamp, limit=1000
                )

                if not ohlcv_data:
                    break

                df = pd.DataFrame(
                    ohlcv_data,
                    columns=[
                        'timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time',
                        'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume',
                        'taker_buy_quote_asset_volume', 'ignore'
                    ]
                )
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                df = df[['open', 'high', 'low', 'close', 'volume']].astype(float)

                all_data.append(df)
                current_start_time = (df.index[-1] + pd.Timedelta(seconds=1)).strftime('%Y-%m-%d %H:%M:%S')
                batch_number += 1

            except Exception as e:
                print(f"Error fetching batch {batch_number}: {e}")
                break

        if not all_data:
            raise RuntimeError(f"Failed to fetch OHLCV data for {symbol}")

        final_df = pd.concat(all_data)
        final_df = self._add_indicators(final_df)
        final_df = final_df.fillna(method="bfill").fillna(method="ffill")

        os.makedirs("data", exist_ok=True)
        final_df.to_csv(path)

        return {"ohlcv_csv_path": path}

    def _add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        # Moving Averages
        for period in [10, 20, 50, 100, 200]:
            df[f"ema_{period}"] = df["close"].ewm(span=period).mean()
            df[f"sma_{period}"] = df["close"].rolling(window=period).mean()

        # RSI
        for period in [7, 14]:
            df[f"rsi_{period}"] = ta.momentum.RSIIndicator(df["close"], window=period).rsi()

        # MACD
        macd = ta.trend.MACD(df["close"])
        df["macd"] = macd.macd()
        df["macd_signal"] = macd.macd_signal()
        df["macd_hist"] = macd.macd_diff()

        # Bollinger Bands
        bb = ta.volatility.BollingerBands(df["close"], window=20)
        df["bb_upper"] = bb.bollinger_hband()
        df["bb_lower"] = bb.bollinger_lband()

        # ATR
        df["atr_14"] = ta.volatility.AverageTrueRange(
            df["high"], df["low"], df["close"], window=14
        ).average_true_range()

        # VWAP
        df["vwap"] = (df["volume"] * (df["high"] + df["low"] + df["close"]) / 3).cumsum() / df["volume"].cumsum()

        return df
