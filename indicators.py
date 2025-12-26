import pandas as pd
import talib as ta

def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
   
    # 1. MOMENTUM: RSI, STOCH, STOCHRSI
    df['RSI'] = ta.RSI(df['Close'], timeperiod=14)
    slowk, slowd = ta.STOCH(df['High'], df['Low'], df['Close'], fastk_period=14, slowk_period=3, slowd_period=3)
    df['STOCH_K'] = slowk
    df['STOCH_D'] = slowd
    slowk_rsi, slowd_rsi = ta.STOCHRSI(df['Close'], timeperiod=14, fastk_period=5, fastd_period=3, fastd_matype=0)
    df['STOCHRSI_K'] = slowk_rsi
    df['STOCHRSI_D'] = slowd_rsi
    
    # 2. TREND: EMAs, SMA, WMA, KAMA, T3, DEMA, TEMA
    df['EMA_50'] = ta.EMA(df['Close'], timeperiod=50)
    df['EMA_200'] = ta.EMA(df['Close'], timeperiod=200)
    df['SMA_20'] = ta.SMA(df['Close'], timeperiod=20)
    df['WMA_20'] = ta.WMA(df['Close'], timeperiod=20)
    df['KAMA_10'] = ta.KAMA(df['Close'], timeperiod=10)
    df['T3_10'] = ta.T3(df['Close'], timeperiod=10)
    df['DEMA_20'] = ta.DEMA(df['Close'], timeperiod=20)
    df['TEMA_20'] = ta.TEMA(df['Close'], timeperiod=20)
    
    # 3. MACD
    macd, macdsignal, _ = ta.MACD(df['Close'], fastperiod=12, slowperiod=26, signalperiod=9)
    df['MACD'] = macd
    df['MACD_Signal'] = macdsignal
    
    # 4. VOLATILITY: BBands, ATR, NATR, TRANGE
    upperband, _, lowerband = ta.BBANDS(df['Close'], timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
    df['BB_Upper'] = upperband
    df['BB_Lower'] = lowerband
    df['ATR_14'] = ta.ATR(df['High'], df['Low'], df['Close'], timeperiod=14)
    df['NATR_14'] = ta.NATR(df['High'], df['Low'], df['Close'], timeperiod=14)
    df['TRANGE'] = ta.TRANGE(df['High'], df['Low'], df['Close'])
    
    # 5. TREND STRENGTH & REVERSAL: SAR, ADX
    df['SAR'] = ta.SAR(df['High'], df['Low'], acceleration=0.02, maximum=0.2)
    df['ADX'] = ta.ADX(df['High'], df['Low'], df['Close'], timeperiod=14)
    
    # 6. ICHIMOKU CLOUD
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
    
    # 7. EXTRA MOMENTUM: CCI, WILLR, ULTOSC, TRIX
    df['CCI_20'] = ta.CCI(df['High'], df['Low'], df['Close'], timeperiod=20)
    df['WILLR_14'] = ta.WILLR(df['High'], df['Low'], df['Close'], timeperiod=14)
    df['ULTOSC'] = ta.ULTOSC(df['High'], df['Low'], df['Close'], timeperiod1=7, timeperiod2=14, timeperiod3=28)
    df['TRIX_14'] = ta.TRIX(df['Close'], timeperiod=14)
    
    # 8. VOLUME: OBV, AD, ADOSC, MFI
    df['OBV'] = ta.OBV(df['Close'], df['Volume'])
    df['AD'] = ta.AD(df['High'], df['Low'], df['Close'], df['Volume'])
    df['ADOSC_3_10'] = ta.ADOSC(df['High'], df['Low'], df['Close'], df['Volume'], fastperiod=3, slowperiod=10)
    df['MFI_14'] = ta.MFI(df['High'], df['Low'], df['Close'], df['Volume'], timeperiod=14)
    
    # 9. PRICE TRANSFORMS
    df['TYPPRICE'] = ta.TYPPRICE(df['High'], df['Low'], df['Close'])
    df['WCLPRICE'] = ta.WCLPRICE(df['High'], df['Low'], df['Close'])
    df['MEDPRICE'] = ta.MEDPRICE(df['High'], df['Low'])
    
    # Drop rows with NaN (first ~250 rows due to EMA_200 + Ichimoku)
    return df.dropna()

def find_indicator_occurrences(df: pd.DataFrame, ticker_name: str) -> list[dict]:

    results = []

    # --- MOMENTUM SIGNALS ---
    # RSI Oversold Exit
    condition_rsi_bull = (df['RSI'].shift(1) < 30) & (df['RSI'] >= 30)
    for date_idx in df[condition_rsi_bull].index:
        results.append({"Ticker Name": ticker_name, "Indicator": "RSI: Oversold Exit (>30)", "Occurence Date": date_idx.strftime('%Y-%m-%d')})
    
    # RSI Overbought Exit  
    condition_rsi_bear = (df['RSI'].shift(1) > 70) & (df['RSI'] <= 70)
    for date_idx in df[condition_rsi_bear].index:
        results.append({"Ticker Name": ticker_name, "Indicator": "RSI: Overbought Exit (<70)", "Occurence Date": date_idx.strftime('%Y-%m-%d')})

    # CCI Oversold
    condition_cci_bull = df['CCI_20'] < -100
    for date_idx in df[condition_cci_bull].index:
        results.append({"Ticker Name": ticker_name, "Indicator": "CCI: Oversold (<-100)", "Occurence Date": date_idx.strftime('%Y-%m-%d')})

    # WILLR Oversold Exit
    condition_willr_bull = (df['WILLR_14'].shift(1) < -80) & (df['WILLR_14'] > -80)
    for date_idx in df[condition_willr_bull].index:
        results.append({"Ticker Name": ticker_name, "Indicator": "WILLR: Oversold Exit (>-80)", "Occurence Date": date_idx.strftime('%Y-%m-%d')})

    # --- TREND SIGNALS ---
    # EMA Golden Cross
    condition_ema_bull = (df['EMA_50'].shift(1) <= df['EMA_200'].shift(1)) & (df['EMA_50'] > df['EMA_200'])
    for date_idx in df[condition_ema_bull].index:
        results.append({"Ticker Name": ticker_name, "Indicator": "EMA: Golden Cross (50>200)", "Occurence Date": date_idx.strftime('%Y-%m-%d')})

    # EMA Death Cross
    condition_ema_bear = (df['EMA_50'].shift(1) >= df['EMA_200'].shift(1)) & (df['EMA_50'] < df['EMA_200'])
    for date_idx in df[condition_ema_bear].index:
        results.append({"Ticker Name": ticker_name, "Indicator": "EMA: Death Cross (50<200)", "Occurence Date": date_idx.strftime('%Y-%m-%d')})

    # DEMA/TEMA Cross
    condition_dema_bull = (df['DEMA_20'].shift(1) <= df['TEMA_20'].shift(1)) & (df['DEMA_20'] > df['TEMA_20'])
    for date_idx in df[condition_dema_bull].index:
        results.append({"Ticker Name": ticker_name, "Indicator": "DEMA: Bull Cross over TEMA", "Occurence Date": date_idx.strftime('%Y-%m-%d')})

    # Strong ADX Trend
    condition_adx_strong = df['ADX'] > 25
    for date_idx in df[condition_adx_strong].index:
        results.append({"Ticker Name": ticker_name, "Indicator": "ADX: Strong Trend (>25)", "Occurence Date": date_idx.strftime('%Y-%m-%d')})

    # --- CROSSOVER SIGNALS ---
    # MACD Bullish Crossover
    condition_macd_bull = (df['MACD'].shift(1) <= df['MACD_Signal'].shift(1)) & (df['MACD'] > df['MACD_Signal'])
    for date_idx in df[condition_macd_bull].index:
        results.append({"Ticker Name": ticker_name, "Indicator": "MACD: Bullish Crossover", "Occurence Date": date_idx.strftime('%Y-%m-%d')})

    # STOCH Bullish Crossover
    condition_stoch_bull = (df['STOCH_K'].shift(1) <= df['STOCH_D'].shift(1)) & (df['STOCH_K'] > df['STOCH_D'])
    for date_idx in df[condition_stoch_bull].index:
        results.append({"Ticker Name": ticker_name, "Indicator": "STOCH: Bullish Crossover", "Occurence Date": date_idx.strftime('%Y-%m-%d')})

    # STOCHRSI Bullish Crossover
    condition_stochrsi_bull = (df['STOCHRSI_K'].shift(1) <= df['STOCHRSI_D'].shift(1)) & (df['STOCHRSI_K'] > df['STOCHRSI_D'])
    for date_idx in df[condition_stochrsi_bull].index:
        results.append({"Ticker Name": ticker_name, "Indicator": "STOCHRSI: Bullish Crossover", "Occurence Date": date_idx.strftime('%Y-%m-%d')})

    # Ichimoku Tenkan Bull Cross
    condition_ichi_bull = (df['Tenkan_Sen'].shift(1) <= df['Kijun_Sen'].shift(1)) & (df['Tenkan_Sen'] > df['Kijun_Sen'])
    for date_idx in df[condition_ichi_bull].index:
        results.append({"Ticker Name": ticker_name, "Indicator": "Ichimoku: Tenkan Bull Cross", "Occurence Date": date_idx.strftime('%Y-%m-%d')})

    # --- VOLATILITY & PRICE SIGNALS ---
    # BB Lower Touch
    condition_bb_bull = df['Close'] < df['BB_Lower']
    for date_idx in df[condition_bb_bull].index:
        results.append({"Ticker Name": ticker_name, "Indicator": "BBands: Lower Band Touch", "Occurence Date": date_idx.strftime('%Y-%m-%d')})

    # SAR Bullish Flip
    condition_sar_bull = (df['Close'].shift(1) <= df['SAR'].shift(1)) & (df['Close'] > df['SAR'])
    for date_idx in df[condition_sar_bull].index:
        results.append({"Ticker Name": ticker_name, "Indicator": "SAR: Bullish Flip", "Occurence Date": date_idx.strftime('%Y-%m-%d')})

    # ATR Expansion
    atr_ma = df['ATR_14'].rolling(20).mean()
    condition_atr_high = df['ATR_14'] > 1.5 * atr_ma
    for date_idx in df[condition_atr_high].index:
        results.append({"Ticker Name": ticker_name, "Indicator": "ATR: High Volatility (1.5x)", "Occurence Date": date_idx.strftime('%Y-%m-%d')})

    # OBV New High
    obv_high = df['OBV'].rolling(20).max()
    condition_obv_high = df['OBV'] == obv_high
    for date_idx in df[condition_obv_high].index:
        results.append({"Ticker Name": ticker_name, "Indicator": "OBV: 20d New High", "Occurence Date": date_idx.strftime('%Y-%m-%d')})

    # TRIX Zero Cross
    condition_trix_bull = (df['TRIX_14'].shift(1) <= 0) & (df['TRIX_14'] > 0)
    for date_idx in df[condition_trix_bull].index:
        results.append({"Ticker Name": ticker_name, "Indicator": "TRIX: Zero Line Cross", "Occurence Date": date_idx.strftime('%Y-%m-%d')})

    return results

