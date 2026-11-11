"""QR code generation utility for invited guests."""

import io

import qrcode
from qrcode.image.pil import PilImage


def generate_guest_qr_code(token: str, frontend_url: str) -> bytes:
    """Generate a QR code for an invited guest."""
    # Construct the invitation URL with the token
    # Guest will see invitation first, then click RSVP to get prefilled form
    invitation_url = f"{frontend_url}/?token={token}"

    # Create QR code instance
    qr = qrcode.QRCode(
        version=1,  # Size of the QR code (1 is smallest)
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,  # Size of each box in pixels
        border=4,  # Border size in boxes
    )

    # Add data to the QR code
    qr.add_data(invitation_url)
    qr.make(fit=True)

    # Create an image
    img: PilImage = qr.make_image(fill_color="black", back_color="white")

    # Save to bytes buffer
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer.getvalue()
