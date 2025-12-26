import pandas as pd
import talib as ta

# --- TA-Lib Indicator Calculation ---

def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates ALL TA-Lib indicators including new additions.
    """
    # Existing indicators (RSI, STOCH, EMA, MACD, BB, SAR, ADX, Ichimoku)...
    df['RSI'] = ta.RSI(df['Close'], timeperiod=14)
    slowk, slowd = ta.STOCH(df['High'], df['Low'], df['Close'], fastk_period=14, slowk_period=3, slowd_period=3)
    df['STOCH_K'] = slowk
    df['STOCH_D'] = slowd
    df['EMA_50'] = ta.EMA(df['Close'], timeperiod=50)
    df['EMA_200'] = ta.EMA(df['Close'], timeperiod=200)
    macd, macdsignal, _ = ta.MACD(df['Close'], fastperiod=12, slowperiod=26, signalperiod=9)
    df['MACD'] = macd
    df['MACD_Signal'] = macdsignal
    upperband, _, lowerband = ta.BBANDS(df['Close'], timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
    df['BB_Upper'] = upperband
    df['BB_Lower'] = lowerband
    df['SAR'] = ta.SAR(df['High'], df['Low'], acceleration=0.02, maximum=0.2)
    df['ADX'] = ta.ADX(df['High'], df['Low'], df['Close'], timeperiod=14)
    
    # Ichimoku (unchanged)
    high_9 = df['High'].rolling(window=9).max()
    low_9 = df['Low'].rolling(window=9).min()
    df['Tenkan_Sen'] = (high_9 + low_9) / 2
    high_26 = df['High'].rolling(window=26).max()
    low_26 = df['Low'].rolling(window=26).min()
    df['Kijun_Sen'] = (high_26 + low_26) / 2
    df['Senkou_Span_A'] = ((df['Tenkan_Sen'] + df['Kijun_Sen']) / 2).shift(26) 
    high_52 = df['High'].rolling(window=52).max()
    low_52 = df['Low'].rolling(window=52).min()
    df['Senkou_Span_B'] = ((high_52 + low_52) / 2).shift(26) 
    
    # NEW: Trend Indicators
    df['SMA_20'] = ta.SMA(df['Close'], timeperiod=20)
    df['WMA_20'] = ta.WMA(df['Close'], timeperiod=20)
    df['KAMA_10'] = ta.KAMA(df['Close'], timeperiod=10)
    df['T3_10'] = ta.T3(df['Close'], timeperiod=10)
    df['DEMA_20'] = ta.DEMA(df['Close'], timeperiod=20)
    df['TEMA_20'] = ta.TEMA(df['Close'], timeperiod=20)
    
    # NEW: Momentum Indicators
    df['CCI_20'] = ta.CCI(df['High'], df['Low'], df['Close'], timeperiod=20)
    df['WILLR_14'] = ta.WILLR(df['High'], df['Low'], df['Close'], timeperiod=14)
    df['ULTOSC'] = ta.ULTOSC(df['High'], df['Low'], df['Close'], timeperiod1=7, timeperiod2=14, timeperiod3=28)
    df['TRIX_14'] = ta.TRIX(df['Close'], timeperiod=14)
    slowk, slowd = ta.STOCHRSI(df['Close'], timeperiod=14, fastk_period=5, fastd_period=3, fastd_matype=0)
    df['STOCHRSI_K'] = slowk
    df['STOCHRSI_D'] = slowd
    
    # NEW: Volume Indicators
    df['OBV'] = ta.OBV(df['Close'], df['Volume'])
    df['AD'] = ta.AD(df['High'], df['Low'], df['Close'], df['Volume'])
    df['ADOSC_3_10'] = ta.ADOSC(df['High'], df['Low'], df['Close'], df['Volume'], 
                                fastperiod=3, slowperiod=10)
    
    # NEW: Volatility Indicators
    df['ATR_14'] = ta.ATR(df['High'], df['Low'], df['Close'], timeperiod=14)
    df['NATR_14'] = ta.NATR(df['High'], df['Low'], df['Close'], timeperiod=14)
    df['TRANGE'] = ta.TRANGE(df['High'], df['Low'], df['Close'])
    
    # NEW: Price Transforms (for later use)
    df['TYPPRICE'] = ta.TYPPRICE(df['High'], df['Low'], df['Close'])
    df['WCLPRICE'] = ta.WCLPRICE(df['High'], df['Low'], df['Close'])
    df['MEDPRICE'] = ta.MEDPRICE(df['High'], df['Low'])
    
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

        # 6. ATR + Trend (breakout with volatility)
    indicator_name_6a = "Complex: Price > EMA50 + ATR High Volatility"
    atr_threshold = df['ATR_14'].rolling(window=100).mean()
    condition_6a = (df['Close'] > df['EMA_50']) & (df['ATR_14'] > atr_threshold)

    for date_idx in df[condition_6a].index:
        results.append({
            "Ticker Name": ticker_name,
            "Indicator": indicator_name_6a,
            "Occurence Date": date_idx.strftime('%Y-%m-%d')
        })

    # 7. MFI Oversold + RSI Oversold
    indicator_name_7a = "Complex: RSI < 30 + MFI < 20"
    condition_7a = (df['RSI'] < 30) & (df['MFI_14'] < 20)

    for date_idx in df[condition_7a].index:
        results.append({
            "Ticker Name": ticker_name,
            "Indicator": indicator_name_7a,
            "Occurence Date": date_idx.strftime('%Y-%m-%d')
        })

    # --- 6. Multi-MA Trend Confirmation ---
    indicator_name_6a = "Complex: DEMA/TEMA Golden Cross + SMA20 Uptrend"
    condition_6a = (df['DEMA_20'].shift(1) <= df['TEMA_20'].shift(1)) & \
                   (df['DEMA_20'] > df['TEMA_20']) & \
                   (df['Close'] > df['SMA_20'])
    
    for date_idx in df[condition_6a].index:
        results.append({"Ticker Name": ticker_name, "Indicator": indicator_name_6a, "Occurence Date": date_idx.strftime('%Y-%m-%d')})

    # --- 7. Momentum Divergence Confirmation ---
    indicator_name_7a = "Complex: CCI Oversold + WILLR Exit + ULTOSC Bullish"
    condition_7a = (df['CCI_20'] < -100) & \
                   (df['WILLR_14'].shift(1) < -80) & (df['WILLR_14'] > -80) & \
                   (df['ULTOSC'] > 30)
    
    for date_idx in df[condition_7a].index:
        results.append({"Ticker Name": ticker_name, "Indicator": indicator_name_7a, "Occurence Date": date_idx.strftime('%Y-%m-%d')})

    # --- 8. Volume Surge + Volatility Breakout ---
    indicator_name_8a = "Complex: OBV New High + ATR Expansion + ADOSC > 0"
    obv_high = df['OBV'].rolling(window=20).max()
    atr_ma = df['ATR_14'].rolling(window=10).mean()
    condition_8a = (df['OBV'] == obv_high) & \
                   (df['ATR_14'] > 1.5 * atr_ma) & \
                   (df['ADOSC_3_10'] > 0)
    
    for date_idx in df[condition_8a].index:
        results.append({"Ticker Name": ticker_name, "Indicator": indicator_name_8a, "Occurence Date": date_idx.strftime('%Y-%m-%d')})

    # --- 9. Triple Momentum Confirmation ---
    indicator_name_9a = "Complex: STOCHRSI Bullish + TRIX Zero Cross + RSI Recovery"
    condition_9a = (df['STOCHRSI_K'].shift(1) <= df['STOCHRSI_D'].shift(1)) & \
                   (df['STOCHRSI_K'] > df['STOCHRSI_D']) & \
                   (df['TRIX_14'].shift(1) <= 0) & (df['TRIX_14'] > 0) & \
                   (df['RSI'] > 40)
    
    for date_idx in df[condition_9a].index:
        results.append({"Ticker Name": ticker_name, "Indicator": indicator_name_9a, "Occurence Date": date_idx.strftime('%Y-%m-%d')})

    # --- 10. KAMA Acceleration + NATR Contraction ---
    indicator_name_10a = "Complex: KAMA Up + NATR Low Volatility + TYPPRICE > SMA"
    condition_10a = (df['Close'] > df['KAMA_10']) & \
                    (df['NATR_14'] < df['NATR_14'].rolling(20).mean()) & \
                    (df['TYPPRICE'] > df['SMA_20'])
    
    for date_idx in df[condition_10a].index:
        results.append({"Ticker Name": ticker_name, "Indicator": indicator_name_10a, "Occurence Date": date_idx.strftime('%Y-%m-%d')})
    
    return results
