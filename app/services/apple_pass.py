import os
import json
import base64
import uuid
import passpy
from datetime import datetime
from io import BytesIO
from typing import Dict, Any, Optional
import random
import string
from dotenv import load_dotenv

from ..utils.storage import storage

load_dotenv()

# Get Apple Pass certificate from env
APPLE_PASS_CERT_P12 = os.getenv("APPLE_PASS_CERT_P12", "")
APPLE_PASS_CERT_PASSWORD = os.getenv("APPLE_PASS_CERT_PASSWORD", "")

# Apple Pass Type Identifier
PASS_TYPE_IDENTIFIER = "pass.com.passmint.card"
TEAM_IDENTIFIER = "ABCD12345"  # Replace with your Apple Developer Team ID
ORGANIZATION_NAME = "PassMint"
WEBSERVICE_URL = "https://passmint.example.com/api/"


class ApplePassSigner:
    def __init__(self):
        # Decode base64 cert to binary
        if not APPLE_PASS_CERT_P12:
            print("WARNING: Apple Pass certificate not provided")
            self.cert_data = None
        else:
            self.cert_data = base64.b64decode(APPLE_PASS_CERT_P12)
        self.cert_password = APPLE_PASS_CERT_PASSWORD

    async def generate_pass(
        self, design_json: Dict[str, Any], pass_id: str, metadata: Optional[Dict[str, Any]] = None
    ) -> tuple:
        """
        Generate an Apple Wallet .pkpass file
        
        Args:
            design_json: Pass design JSON template
            pass_id: UUID of the pass
            metadata: Optional metadata to include
            
        Returns:
            tuple of (serial_number, deep_link, pass_content)
        """
        if not self.cert_data:
            raise ValueError("Apple Pass certificate not configured")

        # Generate a random serial number
        serial_number = f"PM-{uuid.uuid4().hex[:8].upper()}"
        
        # Build pass.json
        pass_json = {
            "formatVersion": 1,
            "passTypeIdentifier": PASS_TYPE_IDENTIFIER,
            "serialNumber": serial_number,
            "teamIdentifier": TEAM_IDENTIFIER,
            "organizationName": ORGANIZATION_NAME,
            "description": design_json.get("description", "PassMint Card"),
            "logoText": design_json.get("logoText", "PassMint"),
            "foregroundColor": design_json.get("foregroundColor", "rgb(255, 255, 255)"),
            "backgroundColor": design_json.get("backgroundColor", "rgb(60, 90, 150)"),
            "webServiceURL": WEBSERVICE_URL,
            "authenticationToken": uuid.uuid4().hex,
        }
        
        # Set expiration if provided
        if "expires_at" in design_json:
            pass_json["expirationDate"] = design_json["expires_at"]
            
        # Add pass style from the design template
        # This can be one of: boardingPass, coupon, eventTicket, storeCard, generic
        pass_style = design_json.get("style", "generic")
        pass_json[pass_style] = design_json.get(pass_style, {})
        
        # Add barcode
        pass_json["barcodes"] = [
            {
                "message": f"PASSMINT:{pass_id}",
                "format": "PKBarcodeFormatQR",
                "messageEncoding": "utf-8",
                "altText": serial_number
            }
        ]
        
        # Add metadata if provided
        if metadata:
            # Store metadata in user-defined fields, depending on pass style
            fields_key = "primaryFields" if pass_style == "generic" else "primaryFields"
            if fields_key not in pass_json[pass_style]:
                pass_json[pass_style][fields_key] = []
                
            for key, value in metadata.items():
                pass_json[pass_style][fields_key].append({
                    "key": key,
                    "label": key.capitalize(),
                    "value": str(value)
                })
        
        # Create the pass using passpy
        pkpass = passpy.Pass(pass_json)
        
        # Add images from design if provided
        for img_type in ["icon", "logo", "thumbnail"]:
            if img_type in design_json and design_json[img_type]:
                # In a real implementation, would download the image from the URL
                # For now, we'll just assume it's a placeholder
                pkpass.addFile(f"{img_type}.png", BytesIO(b"placeholder"))
                
        # Set the certificates from environment variables
        pkpass.setCertificate(self.cert_data, self.cert_password)
        
        # Generate the .pkpass file
        pkpass_data = pkpass.create()
        
        # Generate a key for storage
        storage_key = f"passes/apple/{pass_id}.pkpass"
        
        # Upload to S3
        file_obj = BytesIO(pkpass_data)
        deep_link = await storage.upload_file(
            file_obj, 
            storage_key, 
            content_type="application/vnd.apple.pkpass"
        )
        
        return serial_number, deep_link, pkpass_data


# Create a singleton instance
apple_pass_signer = ApplePassSigner() 