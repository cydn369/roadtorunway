# chart_viewer.py

import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import timedelta
import pandas as pd
from plotly.subplots import make_subplots 

# Function to fetch data for the specific chart period
@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_chart_data(ticker, start_date, end_date):
    """Fetches limited historical data using yfinance."""
    try:
        # Use yf.download for simple chart fetching
        data = yf.download(ticker, start=start_date, end=end_date, auto_adjust=False)
        return data
    except Exception as e:
        st.error(f"Error fetching chart data for {ticker}: {e}")
        return None

def display_signal_chart(selected_row):
    """
    Displays a candlestick chart for the selected ticker and date range.
    """
    if selected_row is None:
        return

    ticker = selected_row['Ticker Name']
    indicator = selected_row['Indicator']
    
    # 1. Date Extraction and Conversion (The Final Fix)
    # 💡 CHANGE: Convert to a Pandas Timestamp and keep it that way for arithmetic.
    signal_timestamp = pd.to_datetime(selected_row['Occurence Date'])
    signal_date_str = signal_timestamp.strftime('%Y-%m-%d') # Use this for display

    # 2. Define the chart window (+- 30 days)
    # Arithmetic is performed on the flexible Pandas Timestamp object.
    chart_start_date = signal_timestamp - timedelta(days=30)
    chart_end_date = signal_timestamp + timedelta(days=30)
    
    st.subheader(f"📊 Chart Context for {ticker}")
    st.markdown(f"**Signal:** {indicator} on **{signal_date_str}**")

    # Fetch data
    df = get_chart_data(ticker, chart_start_date, chart_end_date)
    
    if df is None or df.empty:
        st.warning(f"No historical data available for {ticker} between {chart_start_date} and {chart_end_date}.")
        return

    # --- Create Candlestick Chart with Volume ---
    
    # 1. Candlestick Trace
    candlestick = go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Candlestick',
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
        row_heights=[0.7, 0.3] # Allocate 70% to price, 30% to volume
    )
    
    # Add Price Chart
    fig.add_trace(candlestick, row=1, col=1)
    
    # Add Volume Chart
    fig.add_trace(volume_bar, row=2, col=1)

    # Add a marker line for the signal date 
    fig.add_vline(x=signal_date, line_width=2, line_dash="dash", line_color="orange", row=1, col=1, 
                  annotation_text="Signal Date", annotation_position="top right")

    # Update Layout
    fig.update_layout(
        title=f"{ticker} Price & Volume around Signal Date ({signal_date})",
        xaxis_tickformat='%Y-%m-%d',
        xaxis_rangeslider_visible=False, # Hide the bottom slider for clean view
        height=600,
        margin=dict(l=20, r=20, t=50, b=20)
    )

    # Clean up y-axes
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1, showgrid=False)
    
    st.plotly_chart(fig, use_container_width=True)
