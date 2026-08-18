"""QR code image generation. Works for any text payload -- card tokens
(app/card/routes.py) as well as plain URLs (the printable door sign,
app/admin/routes.py::poster).
"""
import io

import qrcode


def token_to_qr_png_bytes(token: str) -> bytes:
    """Render any text (a card token, a URL, ...) as a PNG QR code and
    return raw PNG bytes.
    """
    img = qrcode.make(token)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()
