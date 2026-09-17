import cv2
from pyzbar.pyzbar import decode
import requests
from urllib.parse import urlparse
from core.domain_generator import DomainGenerator

SHORTENER_DOMAINS = [
    "bit.ly", "tinyurl.com", "t.co", "is.gd", 
    "buff.ly", "adf.ly", "ow.ly", "rb.gy"
]

class QuishingScanner:
    def __init__(self, target_brand_domain: str = None):
        self.target_brand_domain = target_brand_domain

    def scan_image(self, image_path: str) -> dict:
        """Decodifica un código QR desde una imagen y analiza su URL."""
        img = cv2.imread(image_path)
        if img is None:
            return {"error": f"No se pudo cargar la imagen: {image_path}"}

        decoded_objects = decode(img)
        if not decoded_objects:
            return {"error": "No se detectaron códigos QR en la imagen."}

        qr_data = decoded_objects[0].data.decode('utf-8')
        
        analysis = {
            "raw_data": qr_data,
            "is_url": False,
            "final_url": qr_data,
            "redirect_chain": [],
            "uses_shortener": False,
            "risk_score": 0,
            "risk_factors": []
        }

        if qr_data.startswith("http://") or qr_data.startswith("https://"):
            analysis["is_url"] = True
            self._analyze_url(qr_data, analysis)

        return analysis

    def _analyze_url(self, url: str, analysis: dict):
        """Analiza la URL extrayendo indicadores de riesgo y vectores de quishing."""
        parsed = urlparse(url)
        domain = parsed.hostname.lower() if parsed.hostname else ""

        # Check 1: Detección de acortadores de URL
        if domain in SHORTENER_DOMAINS:
            analysis["uses_shortener"] = True
            analysis["risk_factors"].append("Uso de acortador de URL para ocultar el destino real.")
            analysis["risk_score"] += 25

        # Check 2: Verificación de imitación de marca / Typosquatting
        if self.target_brand_domain and domain:
            gen = DomainGenerator(self.target_brand_domain)
            variants = gen.generate_all()
            
            if domain in variants:
                analysis["risk_factors"].append(
                    f"¡ALERTA DE QUISHING! La URL ({domain}) es una imitación de la marca protegida ({self.target_brand_domain})."
                )
                analysis["risk_score"] += 60

        # Check 3: Cadenas de Redirección HTTP y análisis de respuesta
        try:
            response = requests.get(url, allow_redirects=True, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
            analysis["final_url"] = response.url
            if len(response.history) > 0:
                analysis["redirect_chain"] = [r.url for r in response.history] + [response.url]
                analysis["risk_factors"].append(f"El QR realiza {len(response.history)} redirección(es).")
                analysis["risk_score"] += 20
        except Exception:
            analysis["risk_factors"].append("Servidor no disponible o rechazó la conexión (patrón habitual en dominios no confiables).")
            analysis["risk_score"] += 15

        # Normalizar Risk Score (Máximo 100)
        analysis["risk_score"] = min(analysis["risk_score"], 100)
