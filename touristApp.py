import streamlit as st
import json
import qrcode
from PIL import Image
from io import BytesIO

# Import your engine functions
from credntialmain import generate_issuer_id, create_signed_vc, anchor_vc

st.set_page_config(layout="wide")
st.title("🇮🇳 Safe India Tourism - Tourist Digital ID Wallet")
st.markdown("---")

# Use session state to hold the credential
if 'tourist_vc' not in st.session_state:
    st.session_state.tourist_vc = None

col1, col2 = st.columns([1, 2])

with col1:
    st.header("Your Details")
    name = st.text_input("Full Name", "Priya Sharma")
    nationality = st.text_input("Nationality", "British")
    passport = st.text_input("Passport Number", "G987654321")
    contact = st.text_input("Emergency Contact", "+44 20 7946 0999")
    blood_type = st.selectbox("Blood Type", ["O+", "A+", "B+", "AB+", "O-", "A-", "B-", "AB-"])
    insurance = st.text_input("Insurance Policy ID", "INS-AETNA-5588-XYZ")
    
    if st.button("Get My Digital ID", type="primary"):
        with st.spinner("Generating secure keys and issuing your credential..."):
            tourist_data = {
                "name": name, "nationality": nationality, "passportNumber": passport,
                "emergencyContact": contact, "bloodType": blood_type, "insurancePolicyId": insurance
            }
            # Issue the credential
            private_key, issuer_did, verification_method = generate_issuer_id()
            issued_vc = create_signed_vc(tourist_data, private_key, issuer_did, verification_method)
        
        st.success("Credential Issued Successfully!")
        
        with st.spinner("Anchoring your credential to the blockchain for security..."):
            tx_hash = anchor_vc(issued_vc)
            st.session_state.tourist_vc = json.loads(issued_vc)
            st.session_state.tx_hash = tx_hash
        
        if tx_hash:
            st.success(f"Credential Anchored! Transaction Hash: {st.session_state.tx_hash}")
        else:
            st.error("Failed to anchor credential to the blockchain.")


with col2:
    st.header("Your Verifiable Credential")
    if not st.session_state.tourist_vc:
        st.info("Click the 'Get My Digital ID' button to generate your secure credential.")
    else:
        st.success("Your Digital ID is ready. Show this QR code to an authorized first responder or download it.")
        
        # Create QR Code
        qr_data = json.dumps(st.session_state.tourist_vc)
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        
        # Convert to a displayable format for streamlit
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        
        st.image(buffered, width=300)

        # --- NEW: Add a download button for the QR code image ---
        st.download_button(
            label="Download QR Code",
            data=buffered,
            file_name="tourist_qr_code.png",
            mime="image/png"
        )
        
        with st.expander("View Credential JSON"):
            st.json(st.session_state.tourist_vc)

