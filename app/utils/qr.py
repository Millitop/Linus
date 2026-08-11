"""QR code image generation for card tokens."""
import io

import qrcode


def token_to_qr_png_bytes(token: str) -> bytes:
    """Render a card token as a PNG QR code and return raw PNG bytes."""
    img = qrcode.make(token)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()
