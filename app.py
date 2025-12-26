# app.py (REVISED FOR PERSISTENCE)

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

# --- CORE ANALYSIS FUNCTION (Moved out of button block) ---

def run_analysis_and_store(selected_tickers, start_date, end_date):
    """Fetches data, runs analysis, and stores results in session state."""
    
    st.session_state['analysis_ran'] = True
    all_results = []
    
    # Progress Bar
    my_bar = st.progress(0, text="Starting analysis...")
    
    for i, ticker in enumerate(selected_tickers):
        my_bar.progress((i + 1) / len(selected_tickers), text=f"Analyzing {ticker}...")
        
        # Fetch data
        data = get_data(ticker, start_date, end_date)
        
        if data is not None and not data.empty:
            # Calculate and find occurrences
            data_with_indicators = calculate_all_indicators(data.copy())
            ticker_results = find_indicator_occurrences(data_with_indicators, ticker)
            all_results.extend(ticker_results)
        else:
            st.warning(f"Could not retrieve data for **{ticker}** in the selected period.")

    my_bar.empty()
    st.success("Analysis Complete!")
    
    # Store results DataFrame in session state
    if all_results:
        results_df = pd.DataFrame(all_results)
        results_df['Occurence Date'] = pd.to_datetime(results_df['Occurence Date'])
        results_df = results_df.sort_values(by=['Occurence Date', 'Ticker Name'], ascending=False).reset_index(drop=True)
        st.session_state['results_df'] = results_df
    else:
        st.session_state['results_df'] = pd.DataFrame() # Store empty DF if no results


# --- Streamlit UI ---

st.set_page_config(
    page_title="Road to Runway",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Road to Runway")

# Initialize session state variables
if 'analysis_ran' not in st.session_state:
    st.session_state['analysis_ran'] = False
if 'results_df' not in st.session_state:
    st.session_state['results_df'] = pd.DataFrame()


# 1. Ticker Dropdown
st.subheader("1. Select Tickers")
tickers = load_tickers()
selected_tickers = st.multiselect(
    "Select Tickers",
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
st.info("The logic is managed in `indicators.py` with complex, multi-factor analysis.")

# --- The Button and Core Logic Call ---
if st.button("Run Analysis", type="primary"):
    if not selected_tickers:
        st.warning("Please select at least one ticker to run the analysis.")
        # Do not st.stop() here, let it continue to display the warning
    else:
        run_analysis_and_store(selected_tickers, start_date, end_date)

# --- RESULTS DISPLAY (Run every time, if results exist) ---

if st.session_state['analysis_ran'] and not st.session_state['results_df'].empty:
    
    results_df = st.session_state['results_df']
    
    st.subheader("4. Indicator Occurrence Results")
    
    # SINGLE MULTI-SELECT FILTER
    st.markdown("**🔍 Filter by Indicators** (select multiple)")
    all_indicators = sorted(results_df['Indicator'].unique())
    
    selected_indicators = st.multiselect(
        "Choose indicators to show:",
        options=all_indicators,
        default=all_indicators,  # Show all by default
        key="indicator_filter"
    )
    
    # Apply simple filter
    if selected_indicators:
        filtered_results = results_df[results_df['Indicator'].isin(selected_indicators)]
    else:
        filtered_results = results_df.copy()
    
    # Show filter summary
    filter_count = len(filtered_results)
    total_count = len(results_df)
    st.caption(f"Showing **{filter_count}** of **{total_count}** total signals")
    
    # Display filtered table
    selected_rows = st.dataframe(
        filtered_results, 
        use_container_width=True, 
        key="results_table_filtered",
        on_select="rerun", 
        selection_mode="single-row"
    )
    
    # Chart on row selection
    if selected_rows.get('selection', {}).get('rows'):
        selected_index = selected_rows['selection']['rows'][0]
        selected_row_data = filtered_results.iloc[selected_index].to_dict()
        display_signal_chart(selected_row_data)

    # Export filtered results
    st.subheader("5. Export Results")
    if not filtered_results.empty:
        excel_data = to_excel(filtered_results)
        st.markdown(
            get_download_link(
                excel_data, 
                f"Filtered_Results_{date.today().strftime('%Y%m%d')}.xlsx",
                f"📥 **Download Filtered Results ({filter_count} signals)**"
            ),
            unsafe_allow_html=True
        )
    else:
        st.info("👆 Select indicators above to see results.")
