import json
import hashlib
import base64
from web3 import Web3
from dotenv import load_dotenv
import base58
import os

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

def verify_vc_signature(vc_json):
    """
    Verifies the JWS signature of a Verifiable Credential.
    This is the counterpart to the create_signed_vc function.
    """
    print("--- Verifying VC Signature ---")
    
    try:
        proof = vc_json.pop('proof')
        if not proof:
            raise Exception("Credential has no proof.")

        # Reconstruct the signing input from the payload
        payload_bytes = json.dumps(vc_json, separators=(',', ':')).encode('utf-8')
        encoded_header = proof['jws'].split('..')[0]
        signing_input = f"{encoded_header}.".encode('utf-8') + payload_bytes

        # Decode the signature from the JWS
        signature_bytes = base64.urlsafe_b64decode(proof['jws'].split('..')[1] + '==')

        # Derive the public key from the verificationMethod DID
        did_key_identifier = proof['verificationMethod'].split('#')[1]
        prefixed_public_bytes = base58.b58decode(did_key_identifier)
        # Remove the 2-byte multicodec prefix (0xed01)
        public_bytes = prefixed_public_bytes[2:]
        
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_bytes)

        # The verify() function will raise an exception if the signature is invalid
        public_key.verify(signature_bytes, signing_input)
        
        print("✅ Signature is valid.")
        return True
    except Exception as e:
        print(f"❌ Signature verification failed: {e}")
        return False

def verify_anchor(vc_string):
    """
    Checks the blockchain to see if the VC's hash is anchored.
    """
    print("\n--- Verifying Blockchain Anchor ---")
    load_dotenv()
    RPC_URL = os.getenv('RPC_URL')
    
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    
    with open('anchor_address.txt', 'r') as f:
        contract_address = f.read().strip()
    with open('anchor_abi.json', 'r') as f:
        contract_abi = json.load(f)

    contract = w3.eth.contract(address=contract_address, abi=contract_abi)
    print(f"- Checking against contract at: {contract_address}")
    
    vc_json = json.loads(vc_string)
    canonical_vc_string = json.dumps(vc_json, separators=(',', ':'), sort_keys=True)
    vc_hash = hashlib.sha256(canonical_vc_string.encode('utf-8')).digest()
    print(f"- Calculated Canonical Hash: {vc_hash.hex()}")

    is_anchored = contract.functions.isAnchored(vc_hash).call()
    
    if is_anchored:
        print("✅ Hash is anchored on the blockchain.")
    else:
        print("❌ Hash NOT FOUND on the blockchain.")
        
    return is_anchored
