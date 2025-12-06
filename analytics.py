import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import numpy as np 

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
    
    # Check for inclusion in city lists
    if any(loc in location for loc in hyderabad_locations):
        return "Hyderabad"
    if any(loc in location for loc in bengaluru_locations):
        return "Bengaluru"
    if any(loc in location for loc in chennai_locations):
        return "Chennai"
    
    # Default common locations to the selected city if they don't match others.
    selected_city = st.session_state.get('selected_city')
    if selected_city and selected_city != "Select City...":
        return selected_city
        
    return "Unknown" # Default for locations not mapped

# --- CORE ANALYSIS FUNCTION ---
def analyze_accident_data(uploaded_csv):
    """
    Analyzes historical accident data (CSV) to identify high-risk zones and trends,
    filtering by the globally selected city.
    """
    if not uploaded_csv:
        return "Error: CSV file is empty.", None
    
    selected_city = st.session_state.get('selected_city')
    if not selected_city or selected_city == "Select City...":
        return "Error: Cannot analyze data. Please select a City on the main dashboard first.", None

    try:
        # 1. Load and Clean Data
        uploaded_csv.seek(0)
        df = pd.read_csv(uploaded_csv)
        
        # 1a. CRITICAL NEW STEP: Create 'City' column if missing for filtering
        if 'City' not in df.columns:
            # THIS LINE IS COMMENTED OUT TO REMOVE THE UI MESSAGE
            # st.info("CSV is missing the 'City' column. Mapping locations to cities based on predefined landmarks.") 
            
            # Use the helper function to populate the City column
            df['City'] = df['Location'].apply(_map_location_to_city)
        
        # 1b. Filter the DataFrame by the selected city
        # Ensure filtering is case-insensitive and handles potential whitespace issues
        df_filtered = df[df['City'].astype(str).str.strip().str.contains(selected_city, case=False, na=False)]
        
        if df_filtered.empty:
            return f"Error: No accident data found in the CSV for the selected city: {selected_city}.", None

        # 2. Proceed with Analysis on the FILTERED DataFrame (df_filtered)
        
        # Standardize/Check Key Columns
        if 'Location' not in df_filtered.columns or 'Date' not in df_filtered.columns:
            return "Error: Filtered data missing 'Location' and 'Date' columns.", None
        
        # Data Cleaning and Feature Engineering
        df_filtered['Date'] = pd.to_datetime(df_filtered['Date'], errors='coerce')
        df_filtered.dropna(subset=['Location', 'Date'], inplace=True)
        df_filtered['DayOfWeek'] = df_filtered['Date'].dt.day_name()
        
        # Perform Statistical Analysis
        high_risk_zone = df_filtered['Location'].value_counts().idxmax()
        total_accidents = len(df_filtered)
        
        # Peak Time Analysis
        if 'Time' in df_filtered.columns:
            df_filtered['Hour'] = pd.to_datetime(df_filtered['Time'], format='%H:%M', errors='coerce').dt.hour
            df_filtered.dropna(subset=['Hour'], inplace=True)
            if not df_filtered.empty:
                peak_hour = df_filtered['Hour'].value_counts().idxmax()
                peak_time_str = f"{peak_hour}:00 - {peak_hour + 1}:00"
            else:
                peak_time_str = "N/A (No valid time data in filtered set)"
        else:
            peak_time_str = "N/A (Time data missing in CSV)"

        # 3. Generate Visualizations
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
            "city": selected_city # Add city to output data for module 3 confirmation
        }
        return analytics_data, df_filtered
    
    except Exception as e:
        return f"An unexpected error occurred during analysis: {e}", None

# --- VISUALIZATION HELPERS (No Change Needed) ---

def _fig_to_base64(fig):
    """Converts a Matplotlib figure to a base64 encoded string."""
    buf = BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode()
    plt.close(fig)
    return img_b64

def _generate_bar_chart(df):
    """Generates a bar chart for top accident locations."""
    # Ensure there is data to plot
    if df.empty:
        return ""
        
    top_locations = df['Location'].value_counts().head(5)
    fig, ax = plt.subplots(figsize=(8, 4))
    top_locations.plot(kind='bar', ax=ax, color='salmon')
    ax.set_title('Top 5 Accident Locations', fontsize=10)
    ax.set_ylabel('Accident Count', fontsize=8)
    ax.tick_params(axis='x', rotation=45, labelsize=7)
    plt.tight_layout()
    return _fig_to_base64(fig)

def _generate_pie_chart(df):
    """Generates a pie chart for accidents by day of week."""
    if df.empty:
        return ""

    day_of_week = df['DayOfWeek'].value_counts()
    fig, ax = plt.subplots(figsize=(8, 4))
    day_of_week.plot(kind='pie', autopct='%1.1f%%', ax=ax, startangle=90)
    ax.set_title('Accidents by Day of Week', fontsize=10)
    ax.set_ylabel('')
    plt.tight_layout()
    return _fig_to_base64(fig)


# --- STREAMLIT MODULE FUNCTION (Update UI based on new logic) ---
def analytics_module():
    """Renders the Data Analytics Module UI."""
    
    selected_city = st.session_state.get('selected_city')
    if not selected_city or selected_city == "Select City...":
        st.info("Please select a City on the main dashboard to run Module 2.")
        return

    st.markdown(f"**Data Analysis Filtered for:** :blue[{selected_city}]")
    st.write("Ensure your uploaded CSV contains accident data for this region.")

    uploaded_csv = st.file_uploader("Upload Historical Accident Data (CSV)", type=["csv"], key="csv_uploader")

    if uploaded_csv:
        if st.button("Run Data Analysis (Module 2)", key="run_analytics", use_container_width=True):
            with st.spinner(f'Analyzing CSV data for {selected_city} with Pandas...'):
                analytics_data, df_raw = analyze_accident_data(uploaded_csv)

            if isinstance(analytics_data, dict) and 'high_risk_zone' in analytics_data:
                st.success(f"✅ Data Analysis Complete! Results for {selected_city}.")
                
                # --- CRITICAL: Save to Session State ---
                st.session_state['analytics_data'] = analytics_data
                
                st.subheader("Key Risk Insights")
                st.markdown(f"* **High-Risk Zone:** :red[{analytics_data['high_risk_zone']}]")
                st.markdown(f"* **Total Accidents Analyzed:** {analytics_data['total_accidents']}")
                st.markdown(f"* **Peak Accident Time:** {analytics_data['peak_time']}")
                
                st.subheader("📊 Visualizations")
                chart_col1, chart_col2 = st.columns(2)
                
                # Display Charts
                if analytics_data['charts']['bar_chart_base64']:
                    chart_col1.image(f"data:image/png;base64,{analytics_data['charts']['bar_chart_base64']}")
                    chart_col1.caption(f"Top 5 Accident Locations in {selected_city}")

                if analytics_data['charts']['pie_chart_base64']:
                    chart_col2.image(f"data:image/png;base64,{analytics_data['charts']['pie_chart_base64']}")
                    chart_col2.caption("Accidents by Day of Week")

            else:
                st.error(f"Module 2 Error: {analytics_data}")
    
    # Display previously saved data if available
    elif st.session_state.get('analytics_data'):
        data = st.session_state['analytics_data']
        if data.get('city') == selected_city:
            st.info(f"Analysis complete. Last run high-risk zone for {selected_city}: **{data['high_risk_zone']}**")
        else:
             st.info(f"Last analysis run was for a different city: {data.get('city', 'N/A')}. Upload CSV again to filter for {selected_city}.")
