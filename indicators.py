# indicators.py

import pandas as pd
import talib as ta

def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates all required TA-Lib indicators and adds them as columns.
    
    :param df: The raw stock data DataFrame (Open, High, Low, Close, Volume).
    :return: DataFrame with calculated indicators.
    """
    # 1. Relative Strength Index (RSI) - Period 14
    df['RSI'] = ta.RSI(df['Close'], timeperiod=14)

    # 2. Simple Moving Average (SMA) - Period 200
    df['SMA_200'] = ta.SMA(df['Close'], timeperiod=200)
    
    # 3. MACD (Standard 12, 26, 9)
    macd, macdsignal, _ = ta.MACD(df['Close'], fastperiod=12, slowperiod=26, signalperiod=9)
    df['MACD'] = macd
    df['MACD_Signal'] = macdsignal
    
    # IMPORTANT: Remove NaN rows created by the lookback periods of TA-Lib
    return df.dropna()


def find_indicator_occurrences(df: pd.DataFrame, ticker_name: str) -> list[dict]:
    """
    Analyzes the DataFrame to find dates where the indicator conditions are met.
    
    :param df: DataFrame with calculated indicators.
    :param ticker_name: The name of the stock ticker.
    :return: A list of dictionaries for the results table.
    """
    results = []

    # --- CONDITION 1: RSI Oversold Entry (< 30) ---
    indicator_name_1 = "RSI: Oversold Entry (< 30)"
    # Logic: Previous day RSI was >= 30 AND Current day RSI is < 30
    condition_1 = (df['RSI'].shift(1) >= 30) & (df['RSI'] < 30)
    
    for date_idx in df[condition_1].index:
        results.append({
            "Ticker Name": ticker_name,
            "Indicator": indicator_name_1,
            "Occurence Date": date_idx.strftime('%Y-%m-%d')
        })
        
    # --- CONDITION 2: Price crosses above 200-day SMA ---
    indicator_name_2 = "Price: Crossover above 200 SMA"
    # Logic: Previous day Close was <= 200 SMA AND Current day Close is > 200 SMA
    condition_2 = (df['Close'].shift(1) <= df['SMA_200'].shift(1)) & \
                  (df['Close'] > df['SMA_200'])

    for date_idx in df[condition_2].index:
        results.append({
            "Ticker Name": ticker_name,
            "Indicator": indicator_name_2,
            "Occurence Date": date_idx.strftime('%Y-%m-%d')
        })
        
    # --- CONDITION 3: MACD Bullish Crossover ---
    indicator_name_3 = "MACD: Bullish Crossover (MACD > Signal)"
    # Logic: Previous day MACD was <= Signal AND Current day MACD is > Signal
    condition_3 = (df['MACD'].shift(1) <= df['MACD_Signal'].shift(1)) & \
                  (df['MACD'] > df['MACD_Signal'])

    for date_idx in df[condition_3].index:
        results.append({
            "Ticker Name": ticker_name,
            "Indicator": indicator_name_3,
            "Occurence Date": date_idx.strftime('%Y-%m-%d')
        })

    return results

# You can easily add more conditions here (e.g., RSI Overbought, Death Cross, etc.)!
