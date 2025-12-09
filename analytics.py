import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import numpy as np 
import os # Required for file path checking

# --- CONFIGURATION: SET THE FIXED CSV PATH ---
# IMPORTANT: Save your accident data as 'accidents.csv' in the same folder as app.py
FIXED_CSV_PATH = 'accidents.csv'

# --- LOCATION MAPPING HELPER ---
def _map_location_to_city(location):
    """Maps a specific location name to a corresponding city based on common Indian city landmarks."""
    location = str(location).strip()
    
    # Define location clusters based on common Indian cities
    hyderabad_locations = ["Madhapur", "Hitech City", "Gachibowli", "Raidurg Metro Road", 
                           "Banjara Hills", "Kukatpally", "Ameerpet", "LB Nagar", "Uppal Ring Road"]
    
    bengaluru_locations = ["Silk Board", "Electronic", "Marathahalli", "Whitefield", 
                           "MG Road", "Hebbal Flyover", "Yeshwanthpur"]
    
    chennai_locations = ["Guindy Junc", "T Nagar", "OMR Sholinganallur", "Anna Salai", "Poonamallee"]

    vijayawada_locations = ["Benz Circle", "MG Road", "Ring Road", "Kanuru Road", "Ramavarapadu"]
    
    # Check for inclusion in city lists
    if any(loc in location for loc in hyderabad_locations):
        return "Hyderabad"
    if any(loc in location for loc in bengaluru_locations):
        return "Bengaluru"
    if any(loc in location for loc in chennai_locations):
        return "Chennai"
    if any(loc in location for loc in vijayawada_locations):
        return "Vijayawada"
        
    # Default common locations to the selected city if they don't match others.
    selected_city = st.session_state.get('selected_city')
    if selected_city and selected_city != "Select City...":
        return selected_city
        
    return "Unknown"

# --- VISUALIZATION HELPERS ---

def _fig_to_base64(fig):
    """Converts a Matplotlib figure to a base64 encoded string."""
    buf = BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode()
    plt.close(fig)
    return img_b64

def _generate_bar_chart(df):
    """
    Generates a bar chart for top accident locations.
    MODIFIED: Uses SUM of the 'accidents' column instead of counting rows.
    """
    if df.empty: return ""
    
    # --- MODIFIED LOGIC: Use SUM('accidents') or fallback to row count ---
    if 'accidents' in df.columns:
        # Sum the 'accidents' column grouped by Location
        top_locations = df.groupby('Location')['accidents'].sum().nlargest(5)
    else:
        # Fallback: Count rows if 'accidents' column is missing/unknown
        top_locations = df['Location'].value_counts().head(5)
    # --- END MODIFIED LOGIC ---
    
    fig, ax = plt.subplots(figsize=(8, 4))
    top_locations.plot(kind='bar', ax=ax, color='salmon')
    
    ax.set_title('Top 5 Accident Locations', fontsize=10)
    ax.set_ylabel('Accident Count', fontsize=8)
    ax.tick_params(axis='x', rotation=45, labelsize=7)
    plt.tight_layout()
    return _fig_to_base64(fig)

def _generate_pie_chart(df):
    """Generates a pie chart for accidents by day of week. Note: This still uses row counts for distribution."""
    if df.empty: return ""
    
    # NOTE: Pie chart logic is trickier if you want to use the 'accidents' column.
    # To correctly use 'accidents' column: you'd need to group by DayOfWeek and sum 'accidents'.
    if 'accidents' in df.columns and not df.empty:
        day_of_week_counts = df.groupby('DayOfWeek')['accidents'].sum()
    else:
        # Fallback to counting rows
        day_of_week_counts = df['DayOfWeek'].value_counts()
        
    fig, ax = plt.subplots(figsize=(8, 4))
    day_of_week_counts.plot(kind='pie', autopct='%1.1f%%', ax=ax, startangle=90)
    ax.set_title('Accidents by Day of Week', fontsize=10)
    ax.set_ylabel('')
    plt.tight_layout()
    return _fig_to_base64(fig)

# --- CORE ANALYSIS FUNCTION (Modified to accept file path) ---
def analyze_accident_data(data_source):
    """Analyzes historical accident data, accepting a file path."""
    
    selected_city = st.session_state.get('selected_city')
    if not selected_city or selected_city == "Select City...":
        return "Error: Cannot analyze data. Please select a City on the main dashboard first.", None
    
    try:
        # Load Data from fixed file path
        if isinstance(data_source, str) and os.path.exists(data_source):
            df = pd.read_csv(data_source)
        else:
             return "Error: Fixed CSV file not found or path is incorrect. Ensure 'accidents.csv' is in the root directory.", None
             
        # 1a. CRITICAL: Create 'City' column if missing for filtering (Silent Mapping)
        if 'City' not in df.columns:
            df['City'] = df['Location'].apply(_map_location_to_city)
        
        # 1b. Filter the DataFrame by the selected city
        df_filtered = df[df['City'].astype(str).str.strip().str.contains(selected_city, case=False, na=False)]
        
        if df_filtered.empty:
            return f"Error: No accident data found in the CSV for the selected city: {selected_city}.", None

        # 2. Proceed with Analysis on the FILTERED DataFrame (df_filtered)
        
        df_filtered['Date'] = pd.to_datetime(df_filtered['Date'], errors='coerce')
        df_filtered.dropna(subset=['Location', 'Date'], inplace=True)
        df_filtered['DayOfWeek'] = df_filtered['Date'].dt.day_name()
        
        # --- MODIFIED LOGIC for total_accidents and high_risk_zone ---
        if 'accidents' in df_filtered.columns:
            # 1. Sum the total count from the 'accidents' column
            total_accidents = df_filtered['accidents'].sum() 
            
            # 2. Determine high-risk zone based on the SUM of accidents
            high_risk_zone = df_filtered.groupby('Location')['accidents'].sum().idxmax()
        else:
            # Fallback: count the number of rows if accident count column is missing
            total_accidents = len(df_filtered)
            high_risk_zone = df_filtered['Location'].value_counts().idxmax()
        # --- END MODIFIED LOGIC ---
        
        peak_time_str = "N/A (Time data missing in CSV)"
        # Note: If you want to calculate peak time based on the SUM of accidents, 
        # you would need to group by Hour and sum the 'accidents' column here too.
        if 'Time' in df_filtered.columns:
            df_filtered['Hour'] = pd.to_datetime(df_filtered['Time'], format='%H:%M', errors='coerce').dt.hour
            df_filtered.dropna(subset=['Hour'], inplace=True)
            if not df_filtered.empty:
                peak_hour = df_filtered['Hour'].value_counts().idxmax()
                peak_time_str = f"{peak_hour}:00 - {peak_hour + 1}:00"

        # 3. Generate Visualizations (The data passed to the visualization functions is df_filtered)
        bar_chart_b64 = _generate_bar_chart(df_filtered)
        pie_chart_b64 = _generate_pie_chart(df_filtered)

        # 4. Compile Results
        analytics_data = {
            "high_risk_zone": high_risk_zone,
            "peak_time": peak_time_str,
            "total_accidents": total_accidents,
            "charts": {
                "bar_chart_base64": bar_chart_b64,
                "pie_chart_base64": pie_chart_b64
            },
            "city": selected_city
        }
        return analytics_data, df_filtered
    
    except Exception as e:
        return f"An unexpected error occurred during analysis: {e}", None

# --- STREAMLIT MODULE FUNCTION (AUTO-RUN) ---
# NOTE: This function remains the same as it correctly handles caching and display flow
def analytics_module():
    """Triggers the analysis immediately using the fixed CSV file."""
    
    st.markdown(f"**Data Source:** :green[Pre-loaded] from `{FIXED_CSV_PATH}`")
    
    # 1. Check if City is selected
    selected_city = st.session_state.get('selected_city')
    if not selected_city or selected_city == "Select City...":
        st.info("Please select a City on the main dashboard to run Module 2.")
        return

    # Initialize data and status message variables
    data = None
    run_status_message = None

    # 2. Check and Run/Cache Analysis
    if st.session_state.get('analytics_data') and st.session_state['analytics_data'].get('city') == selected_city:
        # Data is cached, no re-run needed
        data = st.session_state['analytics_data']
        run_status_message = f"✅ Data Analysis Complete! Results for {selected_city} loaded from cache."
    else:
        # Auto-Run Analysis
        with st.spinner(f'Analyzing background CSV data for {selected_city}...'):
            analytics_data, df_raw = analyze_accident_data(FIXED_CSV_PATH)
            
            if isinstance(analytics_data, dict) and 'high_risk_zone' in analytics_data:
                st.session_state['analytics_data'] = analytics_data
                data = analytics_data
                run_status_message = f"✅ Data Analysis Complete! Results for {selected_city}."
            else:
                st.error(f"Module 2 Error: {analytics_data}")
                return # Stop if analysis failed

    # 3. Display Results 
    if data:
        st.success(run_status_message) # Show the single, consolidated status message
        
        st.subheader("Key Risk Insights")
        st.markdown(f"* **High-Risk Zone:** :red[{data['high_risk_zone']}]")
        st.markdown(f"* **Total Accidents Analyzed:** {data['total_accidents']}")
        st.markdown(f"* **Peak Accident Time:** {data['peak_time']}")
        
        st.subheader("📊 Visualizations")
        chart_col1, chart_col2 = st.columns(2)
        
        if data['charts']['bar_chart_base64']:
            chart_col1.image(f"data:image/png;base64,{data['charts']['bar_chart_base64']}")
            chart_col1.caption(f"Top 5 Accident Locations in {data['city']}")

        if data['charts']['pie_chart_base64']:
            chart_col2.image(f"data:image/png;base64,{data['charts']['pie_chart_base64']}")
            chart_col2.caption("Accidents by Day of Week")
