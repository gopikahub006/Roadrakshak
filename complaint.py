import streamlit as st
import base64
import urllib.parse
# Ensure you have your Gemini client imports if you are using the model here
# from google import genai
# import os 

# --- HELPER FUNCTION: DOWNLOAD BUTTON ---
def get_download_link(text, filename="Civic_Complaint_Letter.txt", link_text="Download Complaint Letter"):
    """Generates a downloadable link for the given text content."""
    b64 = base64.b64encode(text.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}" style="display: inline-block; padding: 10px 20px; background-color: #2F88D9; color: white; text-align: center; text-decoration: none; border-radius: 5px; font-weight: bold;">{link_text}</a>'
    return href

# --- HELPER FUNCTION: SEND EMAIL BUTTON (mailto) ---
def get_mailto_link(recipient, subject, body, button_text="Send Email"):
    """Generates a mailto link that opens the user's default email client."""
    
    # URL encode the subject and body to handle special characters
    encoded_subject = urllib.parse.quote(subject)
    encoded_body = urllib.parse.quote(body)
    
    # Construct the mailto URI
    mailto_uri = f"mailto:{recipient}?subject={encoded_subject}&body={encoded_body}"
    
    # Create the link (will be rendered as a blue button via Streamlit Markdown/HTML)
    link = f'<a href="{mailto_uri}" target="_blank" style="display: inline-block; padding: 10px 20px; background-color: #4CAF50; color: white; text-align: center; text-decoration: none; border-radius: 5px; font-weight: bold;">{button_text}</a>'
    return link


def generate_final_letter(subject, body, analytics_data):
    """
    Generates the final formal letter, displays it, and shows action buttons.
    """
    # 1. Generate the content (Placeholder for actual Gemini Call)
    # -----------------------------------------------------------------------------------
    city = analytics_data.get('city', 'Local City')
    
    # Use the edited subject and body for the final template
    final_letter_content = f"""
[Your Name/Organization Name - e.g., A Concerned Resident]
[Your Address]
[Your City, Postal Code]
[Your Email Address]
[Your Phone Number]

December 06, 2025

The Commissioner
Municipal Corporation
{city}

SUBJECT: {subject}

Respected Commissioner,
{body}

Sincerely,
A Concerned Resident
"""
    # -----------------------------------------------------------------------------------
    
    # Save the final content to session state
    st.session_state['final_letter_content'] = final_letter_content
    
    # 2. Display the Generated Letter
    st.success("✅ Formal Complaint Generated!")
    st.text_area(
        "Review Final Complaint Letter:", 
        value=final_letter_content.strip(),
        height=400,
        key="final_letter_display"
    )
    
    # 3. Display Action Buttons
    st.markdown("---")
    st.subheader("Action Steps")
    
    recipient_email = "commissioner@municipalcorp.gov" 
    
    col_email, col_download, col_confirm = st.columns([2, 1, 3])
    
    # 3a. Send Email Button (Opens External Mail Client)
    with col_email:
        mailto_html = get_mailto_link(
            recipient=recipient_email, 
            subject=subject, 
            body=final_letter_content.strip(),
            button_text="Send Email"
        )
        st.markdown(mailto_html, unsafe_allow_html=True)
    
    # 3b. Download Button
    with col_download:
        # Use the download link helper
        st.markdown(get_download_link(final_letter_content, link_text="Download"), unsafe_allow_html=True)

    # 3c. Email Confirmation Button (Simulated Popup)
    with col_confirm:
        # This button simulates the successful action after the user sends the email externally
        if st.button("Email Sent Successfully (Click to Confirm)", key="email_confirm", type="primary"):
            st.balloons()
            st.toast('Email sent successfully!', icon='📧')
            st.success("🎉 Email Sent Successfully! Thank you for your civic contribution.")


# --- STREAMLIT MODULE FUNCTION ---

def complaint_module():
    """Renders the complaint generator module with an auto-filled form."""

    hazard_data = st.session_state.get('hazard_data')
    analytics_data = st.session_state.get('analytics_data')
    
    # Check for required data from previous modules
    if not hazard_data or not analytics_data:
        st.warning("⚠️ Please run Module 1 (Image Analysis) and Module 2 (Data Analytics) first.")
        return

    # --- 1. Auto-Generate Key Fields ---
    city = analytics_data.get('city', 'Unknown City')
    high_risk_zone = analytics_data.get('high_risk_zone', 'Unknown Location')
    total_accidents = analytics_data.get('total_accidents', 'N/A')
    potholes_count = hazard_data.get('potholes', 'N/A')
    hazard_summary = hazard_data.get('ai_summary', 'Road condition summary unavailable.')
    
    # Auto-Generated Subject
    subject_text = f"URGENT: Hazardous Road Conditions (Potholes: {potholes_count}) on {high_risk_zone} ({city})"
    
    # Auto-Generated Complaint Body
    complaint_body_text = f"""
This letter serves to formally report critical road hazards observed on {high_risk_zone} in {city}.

Visual Findings:
{hazard_summary} 
Our system detected {potholes_count} significant hazards (potholes) in the uploaded image.

Statistical Urgency:
This section of road is a proven high-risk zone, with records showing a total of {total_accidents} accidents. Immediate repair is necessary to prevent further incidents.

We urge the Municipal Corporation to prioritize the repair of this section.
"""

    # --- 2. Create and Pre-Fill the Streamlit Form ---

    st.subheader(f"3️⃣ Auto-Generated Complaint for: :blue[{city}]")
    st.info("Review and edit the details below before generating the final letter.")

    with st.form(key='complaint_form'):
        st.markdown("### Destination Details")
        col1, col2 = st.columns(2)
        
        col1.text_input("To:", value="The Commissioner, Municipal Corporation", disabled=True)
        col2.text_input("Destination City:", value=city, disabled=True)
        
        st.markdown("### Complaint Details")
        
        # Subject Auto-Filled and Editable (Using key for retrieval)
        edited_subject = st.text_input("Subject:", value=subject_text, key="edited_subject_input")
        
        st.text_input("Hazard Location:", value=f"{high_risk_zone}, {city}", disabled=True)

        # Body Auto-Filled and Editable (Using key for retrieval)
        edited_body = st.text_area("Complaint Body:", value=complaint_body_text.strip(), height=300, key="edited_body_input")
        
        st.markdown("### Your Contact Information")
        col3, col4 = st.columns(2)
        col3.text_input("Your Name:", value="A Concerned Resident")
        col4.text_input("Your Email:", value="user@example.com")
        
        form_submitted = st.form_submit_button("Generate Final Formal Letter", use_container_width=True, type="primary")
        
    # --- 3. Final Letter Generation Trigger ---
    if form_submitted:
        # Call the final generation function using the current, edited values from the form
        generate_final_letter(edited_subject, edited_body, analytics_data)
        
    # --- 4. Persistent Display (Optional) ---
    # This block allows the buttons/letter to persist if the user re-runs the script 
    # without changing the form content (e.g., clicking the 'Email Sent' button).
    elif st.session_state.get('final_letter_content'):
        st.markdown("---")
        st.info("Last generated complaint is available below.")
        
        # Re-display the generated content and buttons
        subject_for_display = st.session_state.get('final_subject', "Generated Subject")
        
        # Display the letter again
        st.text_area(
            "Review Final Complaint Letter:", 
            value=st.session_state['final_letter_content'].strip(),
            height=400,
            key="final_letter_display_cached"
        )
        
        # Re-display action buttons without re-generating the content
        recipient_email = "commissioner@municipalcorp.gov" 
        col_email, col_download, col_confirm = st.columns([2, 1, 3])
        
        with col_email:
            mailto_html = get_mailto_link(
                recipient=recipient_email, 
                subject=subject_for_display, 
                body=st.session_state['final_letter_content'].strip(),
                button_text="Send Email"
            )
            st.markdown(mailto_html, unsafe_allow_html=True)
        
        with col_download:
            st.markdown(get_download_link(st.session_state['final_letter_content'], link_text="Download"), unsafe_allow_html=True)

        with col_confirm:
            if st.button("Email Sent Successfully (Click to Confirm)", key="email_confirm_cached", type="primary"):
                st.balloons()
                st.toast('Email sent successfully!', icon='📧')
                st.success("🎉 Email Sent Successfully! Thank you for your civic contribution.")
