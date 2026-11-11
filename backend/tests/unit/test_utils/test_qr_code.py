"""Unit tests for QR code generation utility."""

import io

from PIL import Image

from wedding_api.utils.qr_code import generate_guest_qr_code


def test_generate_guest_qr_code_is_png() -> None:
    token = "abc123"
    frontend = "https://example.com"

    data = generate_guest_qr_code(token, frontend)

    # PNG signature
    assert isinstance(data, (bytes, bytearray))
    assert data.startswith(b"\x89PNG\r\n\x1a\n")


def test_generate_guest_qr_code_loadable_by_pillow() -> None:
    token = "xyz789"
    frontend = "https://example.com"

    data = generate_guest_qr_code(token, frontend)

    buf = io.BytesIO(data)
    img = Image.open(buf)

    # Ensure it's a valid image and has size
    assert img.format == "PNG"
    assert img.size[0] > 0 and img.size[1] > 0


def test_generate_guest_qr_code_different_tokens_produce_different_images() -> None:
    frontend = "https://example.com"

    a = generate_guest_qr_code("token1", frontend)
    b = generate_guest_qr_code("token2", frontend)

    assert a != b


def test_generate_guest_qr_code_empty_token() -> None:
    frontend = "https://example.com"

    data = generate_guest_qr_code("", frontend)

    assert data.startswith(b"\x89PNG\r\n\x1a\n")
