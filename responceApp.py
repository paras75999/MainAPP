import streamlit as st
import json
from PIL import Image
from io import BytesIO

# Import libraries for QR code decoding
from qreader import QReader
import numpy as np
import cv2

# Import your verification functions from the other file
from verityEngine import verify_vc_signature, verify_anchor

st.set_page_config(layout="wide")
st.title("👮‍♂️ First Responder Verification Terminal")
st.markdown("---")

st.header("Scan a Tourist's Digital ID")
st.info("Upload the QR code image downloaded from the Tourist App to verify the Digital ID.")

# File uploader for the QR code image
uploaded_file = st.file_uploader("Upload QR Code Image", type=['png', 'jpg', 'jpeg'])

if uploaded_file is not None:
    with st.spinner("Decoding QR code and running verification checks..."):
        # Read the uploaded image bytes
        image_bytes = uploaded_file.getvalue()
        
        # Convert image bytes into a format that OpenCV can process
        nparr = np.frombuffer(image_bytes, np.uint8)
        cv2_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Create a QReader instance
        qreader = QReader()
        
        # --- THE FINAL FIX: Use the single-step detect_and_decode function ---
        # This is the library's recommended approach and is more robust to internal
        # version mismatches than the two-step process.
        decoded_text_list = qreader.detect_and_decode(image=cv2_img)

        if not decoded_text_list or len(decoded_text_list) == 0 or decoded_text_list[0] is None:
            st.error("No QR code could be detected or decoded in the uploaded image. The image may be blurry or corrupt.")
        else:
            vc_string = decoded_text_list[0]
            vc_json = json.loads(vc_string)

            st.markdown("---")
            st.header("Verification Results")

            col1, col2 = st.columns(2)

            # --- Verification Step 1: Signature Check ---
            with col1:
                st.subheader("1. Signature Integrity")
                st.caption("Checks if the credential has been tampered with since it was issued.")
                is_signature_valid = verify_vc_signature(vc_json.copy())
                if is_signature_valid:
                    st.success("✅ Signature is Valid")
                else:
                    st.error("❌ Signature is INVALID")

            # --- Verification Step 2: Blockchain Anchor Check ---
            with col2:
                st.subheader("2. Blockchain Anchor")
                st.caption("Checks if the credential is officially recorded and not revoked.")
                is_anchor_valid = verify_anchor(vc_string)
                if is_anchor_valid:
                    st.success("✅ Anchor is Verified")
                else:
                    st.warning("⚠️ Anchor NOT FOUND")

            st.markdown("---")

            # --- Final Status and Tourist Information ---
            if is_signature_valid and is_anchor_valid:
                st.success("✅ OVERALL STATUS: FULLY VERIFIED")
                st.balloons()
            elif is_signature_valid and not is_anchor_valid:
                st.warning("⚠️ OVERALL STATUS: Signature Valid, but NOT ANCHORED on the blockchain. The ID is authentic but its current status is unconfirmed. Proceed with caution.")
            else:
                st.error("❌ OVERALL STATUS: INVALID DIGITAL ID. Do not trust this credential.")

            st.subheader("Verified Tourist Information:")
            tourist_info = vc_json.get('credentialSubject', {}).get('touristInfo', {})
            
            info_col1, info_col2 = st.columns(2)
            with info_col1:
                st.metric(label="Name", value=tourist_info.get('name', 'N/A'))
                st.metric(label="Nationality", value=tourist_info.get('nationality', 'N/A'))
                st.metric(label="Passport Number", value=tourist_info.get('passportNumber', 'N/A'))
            with info_col2:
                st.metric(label="Emergency Contact", value=tourist_info.get('emergencyContact', 'N/A'))
                st.metric(label="Blood Type", value=tourist_info.get('bloodType', 'N/A'))
                st.metric(label="Insurance Policy", value=tourist_info.get('insurancePolicyId', 'N/A'))


            with st.expander("View Full Credential JSON"):
                st.json(vc_json)

