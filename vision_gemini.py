import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import io
import json
import base64 # Need to import base64 for the st.image display helper

# --- Helper Function (Shared across modules) ---
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

# --- Core Logic Function ---
def analyze_image_with_gemini(uploaded_file, client: genai.Client):
    """
    Analyzes image using Gemini 2.5 Flash to detect hazards and returns structured data.
    
    NOTE: This function now handles file reading and PIL conversion.
    """
    if not client:
        return {"error": "Gemini client not initialized."}, None

    # 1. Prepare the Image
    try:
        # 1a. CRITICAL: Reset the file pointer to the start before reading
        uploaded_file.seek(0)
        
        # 1b. Read the file bytes
        image_bytes = uploaded_file.read()
        
        # 1c. Open with PIL. This is where the 'cannot identify' error usually occurs.
        img = Image.open(io.BytesIO(image_bytes))
        
    except Exception as e:
        return {"error": f"Failed to process image file: {e}"}, None

    # 2. Define Prompt and Structured Output (Same as before)
    system_instruction = (
        "You are an expert road safety AI analyst. Inspect the image and count infrastructure hazards. "
        "Estimate the location based on visual cues. Output your analysis STRICTLY in JSON format. "
        "Only count visible potholes, broken streetlights, or large road cracks."
    )
    prompt = "Analyze this image for road defects and provide hazard counts and a short summary."

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        response_mime_type="application/json",
        response_schema={
            "type": "object",
            "properties": {
                "location_estimate": {"type": "string"},
                "potholes": {"type": "integer"},
                "broken_lights": {"type": "integer"},
                "large_cracks": {"type": "integer"},
                "ai_confidence_summary": {"type": "string"}
            },
            "required": ["location_estimate", "potholes", "broken_lights", "large_cracks", "ai_confidence_summary"]
        }
    )

    # 3. Make the API Call
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt, img], # Using the PIL Image object 'img'
            config=config
        )
        hazard_data = json.loads(response.text)
        
        # Standardize keys for st.session_state
        final_output = {
            "potholes": hazard_data.get("potholes", 0),
            "broken_lights": hazard_data.get("broken_lights", 0),
            "location": hazard_data.get("location_estimate", "Location Unknown"),
            "summary": hazard_data.get("ai_confidence_summary", "Analysis complete.")
        }
        return final_output, response.text
        
    except Exception as e:
        # Include response text in error if available
        error_text = getattr(response, 'text', 'N/A') if 'response' in locals() else 'N/A'
        return {"error": f"Gemini API error: {e}. Raw response: {error_text}"}, None


# --- Streamlit Module Function (CALLED BY app.py) ---
def vision_module():
    """Renders the Visual Intelligence Module UI."""
    client = get_gemini_client()
    if not client:
        st.error("Cannot run Module 1. Please ensure your Gemini API Key is in `.streamlit/secrets.toml`.")
        return

    uploaded_file = st.file_uploader("Upload Image of Road Hazard", type=["jpg", "jpeg", "png"], key="vision_uploader")
    
    if uploaded_file is not None:
        # Display the image once uploaded (Streamlit handles the file pointer reset for display)
        st.image(uploaded_file, caption='Uploaded Image', width=400)
        
        if st.button("Analyze for Hazards (Module 1)", use_container_width=True):
            with st.spinner("Analyzing image with Gemini Vision..."):
                # Pass the uploaded_file object to the core function
                hazard_data, raw_response = analyze_image_with_gemini(uploaded_file, client)
                
            if "error" in hazard_data:
                st.error(f"Analysis Error: {hazard_data['error']}")
            else:
                st.success("✅ Hazard Detection Complete!")
                
                # --- CRITICAL: Save to Session State ---
                st.session_state['hazard_data'] = hazard_data
                
                st.subheader("Results Summary")
                st.markdown(f"**Location Estimate:** {hazard_data.get('location')}")
                st.markdown(f"**Potholes Detected:** {hazard_data.get('potholes')}")
                st.markdown(f"**Broken Lights:** {hazard_data.get('broken_lights')}")
                st.markdown(f"**AI Summary:** *{hazard_data.get('summary')}*")
