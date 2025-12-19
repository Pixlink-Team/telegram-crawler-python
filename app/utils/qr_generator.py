"""
QR Code generator utility
"""
import qrcode
import io
import base64
from PIL import Image


def generate_qr_code(data: str) -> str:
    """
    Generate QR code from data and return as base64 encoded string
    
    Args:
        data: Data to encode in QR code (URL)
    
    Returns:
        Base64 encoded PNG image
    """
    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to bytes
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    # Encode to base64
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return f"data:image/png;base64,{img_base64}"
