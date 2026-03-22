# services/qr_generator.py
# Generates QR codes for distribution records.
# When rations are distributed, a QR code is generated that contains key info.
# The field agent can scan this to confirm the distribution.

# import io
# import qrcode


# def generate_qr_code(data: str) -> bytes:
#     """
#     Generates a QR code image for any string data.
#     Returns: PNG image as bytes (raw binary)
#     """
#     qr = qrcode.QRCode(
#         version=1,                                         # Size of QR code (1 = smallest)
#         error_correction=qrcode.constants.ERROR_CORRECT_L, # Can recover from 7% damage
#         box_size=10,                                       # Pixel size of each box
#         border=4,                                          # White border width
#     )
#     qr.add_data(data)
#     qr.make(fit=True)

#     img = qr.make_image(fill_color="black", back_color="white")

#     # Save image to memory buffer instead of a file
#     buffer = io.BytesIO()
#     img.save(buffer, format="PNG")
#     return buffer.getvalue()


# def generate_distribution_qr(distribution_id: str, beneficiary_id: str, ration_type: str) -> bytes:
#     """
#     Creates a QR code that encodes distribution details.
#     Format: dist:<id>|ben:<id>|type:<ration_type>
#     This QR code acts as a digital receipt / proof of distribution.
#     """
#     payload = f"dist:{distribution_id}|ben:{beneficiary_id}|type:{ration_type}"
#     return generate_qr_code(payload)
