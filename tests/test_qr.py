import io

import pytest

pyzbar = pytest.importorskip("pyzbar.pyzbar", exc_type=ImportError)
Image = pytest.importorskip("PIL.Image", exc_type=ImportError)

from app.utils.qr import token_to_qr_png_bytes  # noqa: E402


def test_qr_round_trip_encodes_and_decodes_token():
    token = "test-token-abc123"
    png_bytes = token_to_qr_png_bytes(token)

    image = Image.open(io.BytesIO(png_bytes))
    decoded = pyzbar.decode(image)

    assert len(decoded) == 1
    assert decoded[0].data.decode("utf-8") == token
