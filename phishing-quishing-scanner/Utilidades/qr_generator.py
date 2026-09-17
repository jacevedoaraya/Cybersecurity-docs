import qrcode
import os

def create_sample_qr(url: str, output_filename: str = "test_phish.png"):
    """Genera una imagen QR de prueba para auditorías de seguridad."""
    os.makedirs("samples", exist_ok=True)
    filepath = os.path.join("samples", output_filename)
    
    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filepath)
    print(f"[+] QR generado con éxito en: {filepath}")
    return filepath
