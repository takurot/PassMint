import qrcode
import io
import base64
from typing import Optional


def generate_qr_png_base64(
    url: str, box_size: int = 10, border: int = 4
) -> str:
    """
    Generate a QR code as a base64-encoded PNG.
    
    Args:
        url: URL to encode in QR code
        box_size: Size of each box in the QR code
        border: Border size
        
    Returns:
        Base64-encoded PNG as data URL
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=box_size,
        border=border,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert PIL image to PNG bytes
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_bytes = buffer.getvalue()
    
    # Encode as base64 data URL
    encoded = base64.b64encode(img_bytes).decode("ascii")
    return f"data:image/png;base64,{encoded}"