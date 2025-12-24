# indicators.py

import pandas as pd
import talib as ta

# --- TA-Lib Indicator Calculation ---

def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates all required TA-Lib indicators and adds them as columns.
    """
    
    # 1. Relative Strength Index (RSI) - Period 14
    df['RSI'] = ta.RSI(df['Close'], timeperiod=14)

    # 2. Simple Moving Average (SMA) - Period 200
    df['SMA_200'] = ta.SMA(df['Close'], timeperiod=200)
    
    # 3. MACD (Standard 12, 26, 9)
    macd, macdsignal, _ = ta.MACD(df['Close'], fastperiod=12, slowperiod=26, signalperiod=9)
    df['MACD'] = macd
    df['MACD_Signal'] = macdsignal
    
    # 4. Bollinger Bands (BBANDS) - Period 20, 2 Standard Deviations (2, 2)
    upperband, middleband, lowerband = ta.BBANDS(
        df['Close'], 
        timeperiod=20, 
        nbdevup=2, 
        nbdevdn=2, 
        matype=0  # 0 for Simple Moving Average
    )
    df['BB_Upper'] = upperband
    df['BB_Lower'] = lowerband
    
    # 5. Stochastic Oscillator (STOCH) - Standard periods (14, 3, 3)
    # Returns Slow K (%K) and Slow D (%D)
    slowk, slowd = ta.STOCH(
        df['High'], 
        df['Low'], 
        df['Close'], 
        fastk_period=14, 
        slowk_period=3, 
        slowd_period=3
    )
    df['STOCH_K'] = slowk
    df['STOCH_D'] = slowd
    
    # IMPORTANT: Remove NaN rows created by the lookback periods
    return df.dropna()


# --- Indicator Condition Checking (Your Requirements) ---

def find_indicator_occurrences(df: pd.DataFrame, ticker_name: str) -> list[dict]:
    """
    Analyzes the DataFrame to find dates where the indicator conditions are met.
    """
    results = []

    # --- 1. RSI Oversold Entry (< 30) ---
    indicator_name_1 = "RSI: Oversold Entry (< 30)"
    condition_1 = (df['RSI'].shift(1) >= 30) & (df['RSI'] < 30)
    
    for date_idx in df[condition_1].index:
        results.append({
            "Ticker Name": ticker_name, "Indicator": indicator_name_1, "Occurence Date": date_idx.strftime('%Y-%m-%d')
        })
        
    # --- 2. Price crosses above 200-day SMA ---
    indicator_name_2 = "Price: Crossover above 200 SMA"
    condition_2 = (df['Close'].shift(1) <= df['SMA_200'].shift(1)) & \
                  (df['Close'] > df['SMA_200'])

    for date_idx in df[condition_2].index:
        results.append({
            "Ticker Name": ticker_name, "Indicator": indicator_name_2, "Occurence Date": date_idx.strftime('%Y-%m-%d')
        })
        
    # --- 3. MACD Bullish Crossover ---
    indicator_name_3 = "MACD: Bullish Crossover (MACD > Signal)"
    condition_3 = (df['MACD'].shift(1) <= df['MACD_Signal'].shift(1)) & \
                  (df['MACD'] > df['MACD_Signal'])

    for date_idx in df[condition_3].index:
        results.append({
            "Ticker Name": ticker_name, "Indicator": indicator_name_3, "Occurence Date": date_idx.strftime('%Y-%m-%d')
        })

    # --- 4. NEW: Bollinger Band Lower Band Touch (Oversold/Buy Signal) ---
    # Condition: Close Price touches or crosses BELOW the Lower Bollinger Band
    indicator_name_4 = "BBands: Close Touches Lower Band"
    # 
    condition_4 = (df['Close'] < df['BB_Lower'])

    for date_idx in df[condition_4].index:
        results.append({
            "Ticker Name": ticker_name, "Indicator": indicator_name_4, "Occurence Date": date_idx.strftime('%Y-%m-%d')
        })
        
    # --- 5. NEW: Stochastic Oscillator Bullish Crossover in Oversold Zone ---
    # Condition: %K crosses above %D AND both are below the 20 level (Oversold Zone)
    indicator_name_5 = "STOCH: Bullish Crossover in Oversold (< 20)"
    # Logic: Previous K <= D AND Current K > D AND Current D < 20
    condition_5 = (df['STOCH_K'].shift(1) <= df['STOCH_D'].shift(1)) & \
                  (df['STOCH_K'] > df['STOCH_D']) & \
                  (df['STOCH_D'] < 20)
    
    for date_idx in df[condition_5].index:
        results.append({
            "Ticker Name": ticker_name, "Indicator": indicator_name_5, "Occurence Date": date_idx.strftime('%Y-%m-%d')
        })

    return results
