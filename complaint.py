import streamlit as st
from google import genai
from google.genai import types
from datetime import datetime
import json
import base64

# Assume get_gemini_client() is available via a shared helper or copied here
def get_gemini_client():
    """Initializes and returns the Gemini client from Streamlit secrets."""
    try:
        api_key = st.secrets.get("gemini_api", {}).get("key")
        if not api_key:
            return None
        client = genai.Client(api_key=api_key)
        return client
    except Exception:
        return None

def generate_formal_letter(hazard_data: dict, analytics_data: dict, client: genai.Client):
    """
    Generates a formal complaint letter using Gemini based on structured input data.
    """
    current_date = datetime.now().strftime("%B %d, %Y")
    
    # 1. Extract and format data points
    potholes = hazard_data.get('potholes', 0)
    broken_lights = hazard_data.get('broken_lights', 0)
    location = hazard_data.get('location', 'An unspecified location from image.')

    risk_zone = analytics_data.get('high_risk_zone', 'N/A')
    total_accidents = analytics_data.get('total_accidents', 'Unknown')
    peak_time = analytics_data.get('peak_time', 'Unknown')
    
    # Structure the input for the prompt
    input_data_string = f"""
    - **Date of Report:** {current_date}
    - **Recipient:** The Commissioner, Municipal Corporation
    - **Primary Hazard Location:** {location}
    - **Visual Findings:** Detected {potholes} potholes and {broken_lights} broken streetlights.
    - **Statistical Urgency:** The area, {risk_zone}, is a high-risk zone with {total_accidents} accidents recorded historically. Accidents peak between {peak_time}.
    """

    # 2. Define the Prompt
    system_instruction = (
        "You are an automated Civic Reporter. Generate a professional, formal complaint letter "
        "to the Municipal Commissioner. The letter must have a clear SUBJECT line, formal salutations, "
        "and separate body paragraphs detailing the Visual Findings and Statistical Urgency. "
        "Demand immediate, specific action based on the data provided."
    )
    
    user_prompt = f"Using the following input data, generate the complete formal complaint letter. The SUBJECT line must mention the primary location and nature of the issue:\n\n{input_data_string}"

    # 3. Make the API Call
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[user_prompt],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction
            )
        )
        return response.text
        
    except Exception as e:
        return f"ERROR: Gemini API call failed during letter generation. Reason: {e}"


# --- Streamlit Module Function (CALLED BY app.py) ---
def complaint_module():
    """Renders the Civic Reporting Module UI."""
    st.header("3️⃣ Civic Reporting Module")
    st.markdown("Automatically drafts a formal complaint based on collected data.")
    
    hazard_data = st.session_state.get('hazard_data')
    analytics_data = st.session_state.get('analytics_data')
    
    if not hazard_data or not analytics_data:
        st.warning("⚠️ Please successfully run Module 1 and Module 2 first.")
        st.info("Status: Hazard Data Loaded? " + ("✅" if hazard_data else "❌") + 
                " | Analytics Data Loaded? " + ("✅" if analytics_data else "❌"))
        return
    
    st.success("Inputs Loaded: Ready to generate a data-backed report.")
    
    st.subheader("Inputs Summary")
    st.markdown(f"* **Hazard Location:** {hazard_data.get('location', 'N/A')}")
    st.markdown(f"* **Risk Zone:** {analytics_data.get('high_risk_zone', 'N/A')}")
    st.markdown(f"* **Total Accidents:** {analytics_data.get('total_accidents', 'N/A')}")
    
    st.markdown("---")

    client = get_gemini_client()
    if not client:
        st.error("Cannot connect to Gemini. Check your API key.")
        return

    if st.button("Generate Formal Complaint Letter", key="run_complaint", use_container_width=True):
        with st.spinner("Drafting formal letter with Gemini Text Generation..."):
            complaint_letter = generate_formal_letter(hazard_data, analytics_data, client)

        if complaint_letter.startswith("ERROR:"):
            st.error(complaint_letter)
        else:
            st.success("✅ Complaint Letter Generated!")
            st.code(complaint_letter, language='markdown')
            
            # Download button
            st.download_button(
                label="Download Complaint Letter (.md)",
                data=complaint_letter,
                file_name="road_rakshak_complaint.md",
                mime="text/markdown",
                use_container_width=True
            )