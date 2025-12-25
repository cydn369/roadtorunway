# chart_viewer.py (Revised - Focus on Occurence Date)

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots 

# Note: The get_chart_data function remains the same as it correctly handles strings.
@st.cache_data(ttl=600)  
def get_chart_data(ticker, start_date_str, end_date_str):
    """
    Fetches limited historical data using yf.Ticker().history().
    """
    try:
        ticker_obj = yf.Ticker(ticker)
        # Pass ISO-formatted strings directly to history()
        data = ticker_obj.history(start=start_date_str, end=end_date_str, auto_adjust=False)
        return data
    except Exception as e:
        st.error(f"Error fetching chart data for {ticker}: {e}")
        return None

def display_signal_chart(selected_row):
    """
    Displays a candlestick chart for the selected ticker, focusing on the Occurence Date.
    The chart will show a fixed period (e.g., 60 days) leading up to the signal.
    """
    if selected_row is None:
        return

    ticker = selected_row['Ticker Name']
    indicator = selected_row['Indicator']
    
    # 1. Date Extraction
    signal_timestamp = selected_row['Occurence Date']
    
    # --- New Chart Range Calculation ---
    
    # We define a fixed lookback period (e.g., 60 days of history before the signal)
    days_lookback = 60
    
    # The end date for the chart is the signal date itself
    chart_end_date = signal_timestamp
    
    # The start date is 60 days before the signal date, using pd.Timedelta
    chart_start_date = signal_timestamp - pd.Timedelta(days=days_lookback)
    
    # DEBUG PRINT: Show the calculated Timestamps
    print(f"DEBUG: Signal Date (End of Chart): {chart_end_date}")
    print(f"DEBUG: Chart Start Date ({days_lookback} days before): {chart_start_date}")

    # --- Conversion and Display Setup ---
    
    # Convert calculated Timestamps to ISO strings for caching/yfinance
    start_date_str = chart_start_date.strftime('%Y-%m-%d')
    end_date_str = chart_end_date.strftime('%Y-%m-%d')
    signal_date_str = signal_timestamp.strftime('%Y-%m-%d')
    
    st.subheader(f"📊 Chart Context for {ticker}")
    st.markdown(f"**Signal:** {indicator} on **{signal_date_str}**")

    # 4. Fetch data: Pass the STRING variables
    df = get_chart_data(ticker, start_date_str, end_date_str)
    
    if df is None or df.empty:
        st.warning(f"No historical data available for {ticker} between {start_date_str} and {end_date_str}.")
        return

    # --- Create Candlestick Chart with Volume ---
    # 

    # 1. Candlestick Trace
    candlestick = go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Price',
        increasing_line_color='green', 
        decreasing_line_color='red'
    )
    
    # 2. Volume Trace (on a separate subplot)
    volume_bar = go.Bar(
        x=df.index,
        y=df['Volume'],
        name='Volume',
        marker_color='rgba(150, 150, 150, 0.5)'
    )
    
    # 3. Figure Layout and Subplots
    fig = make_subplots(
        rows=2, 
        cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.1, 
        row_heights=[0.7, 0.3] 
    )
    
    # Add Price Chart
    fig.add_trace(candlestick, row=1, col=1)
    
    # Add Volume Chart
    fig.add_trace(volume_bar, row=2, col=1)

    # Add a marker line for the signal date (which is the last data point in this context)
    fig.add_vline(x=signal_timestamp, line_width=2, line_dash="dash", line_color="orange", row=1, col=1, 
                  annotation_text="Signal Date", annotation_position="top right") 

    # Update Layout
    fig.update_layout(
        title=f"{ticker} Price & Volume leading up to Signal Date ({signal_date_str})",
        xaxis_tickformat='%Y-%m-%d',
        xaxis_rangeslider_visible=False, 
        height=600,
        margin=dict(l=20, r=20, t=50, b=20)
    )

    # Clean up y-axes
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1, showgrid=False)
    
    st.plotly_chart(fig, use_container_width=True)
