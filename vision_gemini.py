import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import io
import json
import base64 

# --- Helper Function (Shared across modules) ---
def get_gemini_client():
    """Initializes and returns the Gemini client from Streamlit secrets."""
    try:
        # Check for API key in Streamlit secrets
        api_key = st.secrets.get("gemini_api", {}).get("key")
        if not api_key:
            return None
        client = genai.Client(api_key=api_key)
        return client
    except Exception:
        # Handles case where the genai library might fail to initialize
        return None

# --- Core Logic Function ---
def analyze_image_with_gemini(uploaded_file, client: genai.Client):
    """
    Analyzes image using Gemini 2.5 Flash to detect hazards and returns structured data.
    """
    if not client:
        return {"error": "Gemini client not initialized."}, None

    # 1. Prepare the Image
    try:
        # CRITICAL: For uploaded files or camera input (bytes), we use io.BytesIO
        uploaded_file.seek(0)
        image_bytes = uploaded_file.read()
        
        # Open with PIL for the API call.
        img = Image.open(io.BytesIO(image_bytes))
        
    except Exception as e:
        return {"error": f"Failed to process image file: {e}"}, None

    # 2. Define Prompt and Structured Output
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
            "potholes": hazard_data.get("potholes", 0) + hazard_data.get("large_cracks", 0), # Combine cracks and potholes for simplicity
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
    """
    Renders the Visual Intelligence Module UI, using a toggle button to control 
    when the camera input is displayed.
    """
    
    # 1. Initialize Gemini Client and Camera State
    client = get_gemini_client()
    if not client:
        st.error("Cannot run Module 1. Please ensure your Gemini API Key is in `.streamlit/secrets.toml`.")
        return
    
    # Initialize the camera visibility state
    if 'show_camera' not in st.session_state:
        st.session_state.show_camera = False

    st.subheader("1️⃣ Capture or Upload Hazard Image")

    # --- 2. INPUT SELECTION ---
    
    input_col1, input_col2 = st.columns(2)

    with input_col1:
        # Option 2: File Upload (Always visible)
        uploaded_file = st.file_uploader("📂 Upload an Image File", type=['png', 'jpg', 'jpeg'])

    with input_col2:
        # Toggle Button: Controls the visibility of the camera input
        if st.button("📸 Open Camera for Live Capture", key="camera_toggle", use_container_width=True):
            # Toggle the state. This triggers a rerun.
            st.session_state.show_camera = not st.session_state.show_camera

    # 3. Conditional Camera Input (Only displayed if show_camera is True)
    camera_image = None
    if st.session_state.show_camera:
        # st.camera_input widget only renders when this block executes
        camera_image = st.camera_input("Capture Road Hazard Now", key="live_camera_input")
        
        # If the user captures an image, the widget returns the image. 
        # If the user clicks 'Clear photo', it returns None. We'll rely on the image being set.


    # --- 4. ANALYSIS LOGIC ---
    
    # Determine which file to analyze
    file_to_analyze = None
    if camera_image is not None:
        file_to_analyze = camera_image
    elif uploaded_file is not None:
        file_to_analyze = uploaded_file

    if file_to_analyze is not None:
        # Display the file
        source_type = 'Camera' if camera_image else 'Upload'
        st.image(file_to_analyze, caption=f"Image Source: {source_type}", width=400)
        
        # --- Analysis Trigger Button ---
        if st.button("Analyze for Hazards (Module 1)", use_container_width=True, key="run_vision_analysis"):
            
            with st.spinner("Analyzing image with Gemini Vision..."):
                # Pass the file object to the core function
                hazard_data, raw_response = analyze_image_with_gemini(file_to_analyze, client)
                
            if "error" in hazard_data:
                st.error(f"Analysis Error: {hazard_data['error']}")
            else:
                st.success("✅ Hazard Detection Complete!")
                
                # --- CRITICAL: Save to Session State ---
                st.session_state['hazard_data'] = hazard_data
                st.session_state['image_processed'] = True # Mark as processed
                
                # --- Display Results ---
                st.subheader("Results Summary")
                
                col_pothole, col_light = st.columns(2)
                
                col_pothole.metric(
                    label="Potholes/Cracks Detected", 
                    value=hazard_data.get('potholes', 0)
                )
                col_light.metric(
                    label="Broken Lights", 
                    value=hazard_data.get('broken_lights', 0)
                )
                
                st.markdown(f"**Location Estimate:** {hazard_data.get('location')}")
                st.markdown(f"**AI Summary:** *{hazard_data.get('summary')}*")
                st.warning("💡 Now proceed to **Module 2: Data Analytics** to run the historical risk assessment.")

    elif st.session_state.get('image_processed'):
        # Show cached results if a file was previously processed
        hazard_data = st.session_state['hazard_data']
        st.info("Cached Visual Analysis Found. Upload or capture a new image to re-run.")
        
        st.subheader("Results Summary (Cached)")
        col_pothole, col_light = st.columns(2)
        col_pothole.metric(label="Potholes/Cracks Detected", value=hazard_data.get('potholes', 0))
        col_light.metric(label="Broken Lights", value=hazard_data.get('broken_lights', 0))
        st.markdown(f"**Location Estimate:** {hazard_data.get('location')}")
        st.markdown(f"**AI Summary:** *{hazard_data.get('summary')}*")
