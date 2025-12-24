import pandas as pd
import talib as ta

# --- TA-Lib Indicator Calculation ---

def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates all required TA-Lib indicators and adds them as columns.
    
    :param df: The raw stock data DataFrame (Open, High, Low, Close, Volume).
    :return: DataFrame with calculated indicators.
    """
    
    # 1. Momentum Indicators: RSI (14), STOCH (14, 3, 3)
    df['RSI'] = ta.RSI(df['Close'], timeperiod=14)
    slowk, slowd = ta.STOCH(df['High'], df['Low'], df['Close'], fastk_period=14, slowk_period=3, slowd_period=3)
    df['STOCH_K'] = slowk
    df['STOCH_D'] = slowd

    # 2. Trend/MA Indicators: EMA 50, EMA 200
    df['EMA_50'] = ta.EMA(df['Close'], timeperiod=50)
    df['EMA_200'] = ta.EMA(df['Close'], timeperiod=200)

    # 3. MACD (Standard 12, 26, 9)
    macd, macdsignal, _ = ta.MACD(df['Close'], fastperiod=12, slowperiod=26, signalperiod=9)
    df['MACD'] = macd
    df['MACD_Signal'] = macdsignal
    
    # 4. Volatility: Bollinger Bands (20, 2)
    upperband, _, lowerband = ta.BBANDS(df['Close'], timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
    df['BB_Upper'] = upperband
    df['BB_Lower'] = lowerband
    
    # 5. Parabolic SAR
    df['SAR'] = ta.SAR(df['High'], df['Low'], acceleration=0.02, maximum=0.2)

    # 6. Directional Movement: ADX (14)
    df['ADX'] = ta.ADX(df['High'], df['Low'], df['Close'], timeperiod=14)

    # 7. Ichimoku Cloud (9, 26, 52 periods) - Calculated components:
    high_9 = df['High'].rolling(window=9).max()
    low_9 = df['Low'].rolling(window=9).min()
    df['Tenkan_Sen'] = (high_9 + low_9) / 2 # Conversion Line (9)

    high_26 = df['High'].rolling(window=26).max()
    low_26 = df['Low'].rolling(window=26).min()
    df['Kijun_Sen'] = (high_26 + low_26) / 2 # Base Line (26)

    # Shifted 26 periods ahead
    df['Senkou_Span_A'] = ((df['Tenkan_Sen'] + df['Kijun_Sen']) / 2).shift(26) 
    
    high_52 = df['High'].rolling(window=52).max()
    low_52 = df['Low'].rolling(window=52).min()
    df['Senkou_Span_B'] = ((high_52 + low_52) / 2).shift(26) 
    
    # Remove NaN rows created by the lookback periods (up to 200 days for EMA_200)
    return df.dropna()


# --- Complex Indicator Condition Checking ---

def find_indicator_occurrences(df: pd.DataFrame, ticker_name: str) -> list[dict]:
    """
    Analyzes the DataFrame to find dates where the complex, multi-factor indicator conditions are met.
    
    :param df: DataFrame with calculated indicators.
    :param ticker_name: The name of the stock ticker.
    :return: A list of dictionaries for the results table.
    """
    results = []

    # --- 1. RSI and MACD (Combining Momentum) ---
    # a. Bullish Confirmation: RSI Oversold Exit AND MACD Bullish Crossover
    indicator_name_1a = "Complex: RSI Exit (>30) + MACD Bullish Crossover"
    condition_1a = (df['RSI'].shift(1) < 30) & (df['RSI'] >= 30) & \
                   (df['MACD'].shift(1) <= df['MACD_Signal'].shift(1)) & \
                   (df['MACD'] > df['MACD_Signal'])
    
    for date_idx in df[condition_1a].index:
        results.append({"Ticker Name": ticker_name, "Indicator": indicator_name_1a, "Occurence Date": date_idx.strftime('%Y-%m-%d')})
        
    # b. Bearish Confirmation: RSI Overbought Exit AND MACD Bearish Crossover
    indicator_name_1b = "Complex: RSI Exit (<70) + MACD Bearish Crossover"
    condition_1b = (df['RSI'].shift(1) > 70) & (df['RSI'] <= 70) & \
                   (df['MACD'].shift(1) >= df['MACD_Signal'].shift(1)) & \
                   (df['MACD'] < df['MACD_Signal'])
    
    for date_idx in df[condition_1b].index:
        results.append({"Ticker Name": ticker_name, "Indicator": indicator_name_1b, "Occurence Date": date_idx.strftime('%Y-%m-%d')})


    # --- 2. EMA and ADX (Trend Confirmation) ---
    # a. Strong Bullish Trend Entry: Golden Cross AND Trend Strength Confirmation (ADX > 25)
    indicator_name_2a = "Complex: Golden Cross (50/200) + ADX Trend Entry (> 25)"
    condition_2a = (df['EMA_50'].shift(1) <= df['EMA_200'].shift(1)) & \
                   (df['EMA_50'] > df['EMA_200']) & \
                   (df['ADX'] > 25)
    
    for date_idx in df[condition_2a].index:
        results.append({"Ticker Name": ticker_name, "Indicator": indicator_name_2a, "Occurence Date": date_idx.strftime('%Y-%m-%d')})
        
    # b. Strong Bearish Trend Entry: Death Cross AND Trend Strength Confirmation (ADX > 25)
    indicator_name_2b = "Complex: Death Cross (50/200) + ADX Trend Entry (> 25)"
    condition_2b = (df['EMA_50'].shift(1) >= df['EMA_200'].shift(1)) & \
                   (df['EMA_50'] < df['EMA_200']) & \
                   (df['ADX'] > 25)
    
    for date_idx in df[condition_2b].index:
        results.append({"Ticker Name": ticker_name, "Indicator": indicator_name_2b, "Occurence Date": date_idx.strftime('%Y-%m-%d')})


    # --- 3. STOCH and Bollinger Bands (Volatility + Momentum Extreme) ---
    # a. Extreme Bullish Reversal: Price outside BBands AND STOCH Bullish Crossover
    indicator_name_3a = "Complex: BBands Lower Touch + STOCH Bullish Crossover"
    condition_3a = (df['Close'] < df['BB_Lower']) & \
                   (df['STOCH_K'].shift(1) <= df['STOCH_D'].shift(1)) & \
                   (df['STOCH_K'] > df['STOCH_D'])
    
    for date_idx in df[condition_3a].index:
        results.append({"Ticker Name": ticker_name, "Indicator": indicator_name_3a, "Occurence Date": date_idx.strftime('%Y-%m-%d')})
        
    # b. Extreme Bearish Reversal: Price outside BBands AND STOCH Bearish Crossover
    indicator_name_3b = "Complex: BBands Upper Touch + STOCH Bearish Crossover"
    condition_3b = (df['Close'] > df['BB_Upper']) & \
                   (df['STOCH_K'].shift(1) >= df['STOCH_D'].shift(1)) & \
                   (df['STOCH_K'] < df['STOCH_D'])
    
    for date_idx in df[condition_3b].index:
        results.append({"Ticker Name": ticker_name, "Indicator": indicator_name_3b, "Occurence Date": date_idx.strftime('%Y-%m-%d')})


    # --- 4. Ichimoku Cloud (Crossover and Price Position) ---
    # a. Strong Bullish Setup: Tenkan/Kijun Crossover AND Price is Above the Cloud
    indicator_name_4a = "Complex: Ichimoku Bullish Cross AND Price Above Cloud"
    Cloud_Bottom = df[['Senkou_Span_A', 'Senkou_Span_B']].min(axis=1) # Lower boundary of the cloud
    
    condition_4a = (df['Tenkan_Sen'].shift(1) <= df['Kijun_Sen'].shift(1)) & \
                   (df['Tenkan_Sen'] > df['Kijun_Sen']) & \
                   (df['Close'] > Cloud_Bottom)
    
    for date_idx in df[condition_4a].index:
        results.append({"Ticker Name": ticker_name, "Indicator": indicator_name_4a, "Occurence Date": date_idx.strftime('%Y-%m-%d')})
        
    # b. Strong Bearish Setup: Tenkan/Kijun Crossover AND Price is Below the Cloud
    indicator_name_4b = "Complex: Ichimoku Bearish Cross AND Price Below Cloud"
    Cloud_Top = df[['Senkou_Span_A', 'Senkou_Span_B']].max(axis=1) # Upper boundary of the cloud

    condition_4b = (df['Tenkan_Sen'].shift(1) >= df['Kijun_Sen'].shift(1)) & \
                   (df['Tenkan_Sen'] < df['Kijun_Sen']) & \
                   (df['Close'] < Cloud_Top)
    
    for date_idx in df[condition_4b].index:
        results.append({"Ticker Name": ticker_name, "Indicator": indicator_name_4b, "Occurence Date": date_idx.strftime('%Y-%m-%d')})


    # --- 5. SAR and EMA (Trend Reversal Confirmation) ---
    # a. Confirmed Bullish Reversal: SAR Reversal AND Close above EMA 50
    indicator_name_5a = "Complex: SAR Bullish Reversal + Price > EMA 50"
    condition_5a = (df['Close'].shift(1) <= df['SAR'].shift(1)) & (df['Close'] > df['SAR']) & \
                   (df['Close'] > df['EMA_50'])
    
    for date_idx in df[condition_5a].index:
        results.append({"Ticker Name": ticker_name, "Indicator": indicator_name_5a, "Occurence Date": date_idx.strftime('%Y-%m-%d')})

    return results
