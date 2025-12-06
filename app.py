import streamlit as st
import pandas as pd
# Import the main functions from your module files. 
# These must match the function names defined in your individual .py files.
from vision_gemini import vision_module
from analytics import analytics_module
from complaint import complaint_module

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Road Rakshak 2.0", page_icon="🚦", layout="wide")

# Initialize session state variables to store data across modules
# This is CRITICAL for passing results from Module 1 & 2 to Module 3.
if 'hazard_data' not in st.session_state:
    st.session_state['hazard_data'] = None
if 'analytics_data' not in st.session_state:
    st.session_state['analytics_data'] = None

# --- 2. TITLE AND HEADER ---
st.title("🚦 Road Rakshak 2.0")
st.markdown("**Multimodal AI for Road Safety** | Gemini Launchpad Hackathon")
st.markdown("---")

# --- 3. TAB STRUCTURE ---
# Create tabs for each module
tab1, tab2, tab3 = st.tabs(["1️⃣ Visual Intelligence", "2️⃣ Data Analytics", "3️⃣ Civic Reporting"])

# --- TAB 1: Visual Intelligence Module (vision_gemini.py) ---
with tab1:
    st.subheader("Module 1: Hazard Detection from Images (Gemini Vision)")
    # Executes the vision_module function from vision_gemini.py
    vision_module()

# --- TAB 2: Data Analytics Module (analytics.py) ---
with tab2:
    st.subheader("Module 2: Accident Risk Zone Analysis (Pandas)")
    # Executes the analytics_module function from analytics.py
    analytics_module()

# --- TAB 3: Civic Reporting Module (complaint.py) ---
with tab3:
    st.subheader("Module 3: Automated Complaint Generation (Gemini Text)")
    # Executes the complaint_module function from complaint.py
    complaint_module()

# --- 4. FOOTER ---
st.markdown("---")
st.markdown("Tip: Run Module 1, then Module 2, then Module 3 in order for the report generation to work!")