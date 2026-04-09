import qrcode
import os


def generate_qr(outpass_id):
    folder = "qr_codes"
    os.makedirs(folder, exist_ok=True)

    path = f"{folder}/{outpass_id}.png"
    img = qrcode.make(outpass_id)
    img.save(path)

    return path
