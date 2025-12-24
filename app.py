# app.py

import streamlit as st
import pandas as pd
from datetime import date, timedelta
from io import BytesIO
import base64
from plotly.subplots import make_subplots

# Import functions from the separate files
from data_utils import load_tickers, get_data
from indicators import calculate_all_indicators, find_indicator_occurrences
from chart_viewer import display_signal_chart

# --- UI Helper Functions (Export/Download) ---

def to_excel(df):
    """Converts a pandas DataFrame to an in-memory Excel file (XLSX)."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Indicator Results')
    processed_data = output.getvalue()
    return processed_data

def get_download_link(data, filename, text):
    """Generates a link to download the in-memory data."""
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">{text}</a>'
    return href

# --- Streamlit UI ---

st.set_page_config(
    page_title="Modular Stock Indicator Finder",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Modular Stock Technical Indicator Finder")
st.markdown("Select tickers and a date range to find technical indicator occurrences.")

# 1. Ticker Dropdown
tickers = load_tickers()
selected_tickers = st.multiselect(
    "1. Select Tickers",
    options=tickers,
    default=tickers[0] if tickers else None,
    help="Select one or more stock tickers from the list loaded from Nifty500.txt"
)

# 2. Period: From and To Date Pickers
st.subheader("2. Select Period")
col1, col2 = st.columns(2)
with col1:
    today = date.today()
    start_date = st.date_input("From Date", today - timedelta(days=365))
with col2:
    end_date = st.date_input("To Date", today)

# Date validation
if start_date >= end_date:
    st.error("Error: 'From Date' must be before 'To Date'.")
    st.stop()

# 3. Indicators Info
st.subheader("3. Indicators Being Tracked")
st.info("The logic is managed in `indicators.py`. Currently tracking: **RSI Oversold**, **Price/200-day SMA Crossover**, and **MACD Bullish Crossover**.")

# --- Processing and Results ---

if st.button("Run Analysis", type="primary"):
    if not selected_tickers:
        st.warning("Please select at least one ticker to run the analysis.")
        st.stop()
        
    all_results = []
    
    # Progress Bar
    my_bar = st.progress(0, text="Starting analysis...")
    
    for i, ticker in enumerate(selected_tickers):
        my_bar.progress((i + 1) / len(selected_tickers), text=f"Analyzing {ticker}...")
        
        # Fetch data (using function from data_utils.py)
        data = get_data(ticker, start_date, end_date)
        
        if data is not None and not data.empty:
            # Calculate and find occurrences (using functions from indicators.py)
            data_with_indicators = calculate_all_indicators(data.copy())
            ticker_results = find_indicator_occurrences(data_with_indicators, ticker)
            all_results.extend(ticker_results)
        else:
            st.warning(f"Could not retrieve data for **{ticker}** in the selected period.")

    my_bar.empty()
    st.success("Analysis Complete!")

    if all_results:
        # 4. Table: Ticker Name, Indicator, Occurence Date
        st.subheader("4. Indicator Occurrence Results")
        results_df = pd.DataFrame(all_results)
        results_df['Occurence Date'] = pd.to_datetime(results_df['Occurence Date'])
        results_df = results_df.sort_values(by=['Occurence Date', 'Ticker Name'], ascending=False).reset_index(drop=True)
        
        # Display DataFrame and allow row selection
        selected_rows = st.dataframe(
            results_df, 
            use_container_width=True, 
            key="results_table",
            on_select="rerun", # Tells Streamlit to rerun the script when a row is selected
            selection_mode="single-row"
        )
        
        # Check if a row was selected
        if selected_rows['selection']['rows']:
            selected_index = selected_rows['selection']['rows'][0]
            selected_row_data = results_df.iloc[selected_index].to_dict()
            
            # 🎯 3. Display Chart on Row Click 🎯
            display_signal_chart(selected_row_data) # Call the function from chart_viewer.py
            
        # 5. Export to Excel Option
        st.subheader("5. Export Results")
        excel_data = to_excel(results_df)
        st.markdown(
            get_download_link(
                excel_data, 
                f"Indicator_Results_{date.today().strftime('%Y%m%d')}.xlsx",
                "📥 **Download Results to Excel (XLSX)**"
            ),
            unsafe_allow_html=True
        )
    else:
        st.success("Analysis Complete: No indicator occurrences found for the selected tickers/period.")
