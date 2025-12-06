import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import base64
from io import BytesIO

def analyze_accident_data(uploaded_csv):
    """
    Analyzes historical accident data (CSV) to identify high-risk zones and trends.
    """
    if not uploaded_csv:
        return "Error: CSV file is empty.", None

    try:
        # 1. Load and Clean Data
        uploaded_csv.seek(0)
        df = pd.read_csv(uploaded_csv)

        # Standardize/Check Key Columns (assuming standard names: Location, Date, Time)
        if 'Location' not in df.columns or 'Date' not in df.columns:
            return "Error: CSV must contain 'Location' and 'Date' columns.", None
        
        # Data Cleaning and Feature Engineering
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df.dropna(subset=['Location', 'Date'], inplace=True)
        df['DayOfWeek'] = df['Date'].dt.day_name()
        
        # 2. Perform Statistical Analysis
        high_risk_zone = df['Location'].value_counts().idxmax()
        total_accidents = len(df)
        
        # Peak Time Analysis (assuming an 'Hour' column is derived or exists)
        if 'Time' in df.columns:
            # Simple conversion to hour for analysis
            df['Hour'] = pd.to_datetime(df['Time'], format='%H:%M', errors='coerce').dt.hour
            df.dropna(subset=['Hour'], inplace=True)
            peak_hour = df['Hour'].value_counts().idxmax()
            peak_time_str = f"{peak_hour}:00 - {peak_hour + 1}:00"
        else:
            peak_time_str = "N/A (Time data missing)"

        # 3. Generate Visualizations
        bar_chart_b64 = _generate_bar_chart(df)
        pie_chart_b64 = _generate_pie_chart(df)

        # 4. Compile Results
        analytics_data = {
            "high_risk_zone": high_risk_zone,
            "peak_time": peak_time_str,
            "total_accidents": total_accidents,
            "charts": {
                "bar_chart_base64": bar_chart_b64,
                "pie_chart_base64": pie_chart_b64
            }
        }
        return analytics_data, df
    
    except Exception as e:
        return f"An unexpected error occurred during analysis: {e}", None

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
    day_of_week = df['DayOfWeek'].value_counts()
    fig, ax = plt.subplots(figsize=(8, 4))
    day_of_week.plot(kind='pie', autopct='%1.1f%%', ax=ax, startangle=90)
    ax.set_title('Accidents by Day of Week', fontsize=10)
    ax.set_ylabel('')
    plt.tight_layout()
    return _fig_to_base64(fig)


# --- Streamlit Module Function (CALLED BY app.py) ---
def analytics_module():
    """Renders the Data Analytics Module UI."""
    uploaded_csv = st.file_uploader("Upload Historical Accident Data (CSV)", type=["csv"], key="csv_uploader")

    if uploaded_csv:
        if st.button("Run Data Analysis (Module 2)", key="run_analytics", use_container_width=True):
            with st.spinner('Analyzing CSV data with Pandas...'):
                analytics_data, df_raw = analyze_accident_data(uploaded_csv)

            if isinstance(analytics_data, dict) and 'high_risk_zone' in analytics_data:
                st.success("✅ Data Analysis Complete!")
                
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
                    chart_col1.caption("Top 5 Accident Locations")

                if analytics_data['charts']['pie_chart_base64']:
                    chart_col2.image(f"data:image/png;base64,{analytics_data['charts']['pie_chart_base64']}")
                    chart_col2.caption("Accidents by Day of Week")

            else:
                st.error(f"Module 2 Error: {analytics_data}")
    
    # Display previously saved data if available
    elif st.session_state.get('analytics_data'):
        data = st.session_state['analytics_data']
        st.info(f"Analysis complete. Last run high-risk zone: **{data['high_risk_zone']}**")