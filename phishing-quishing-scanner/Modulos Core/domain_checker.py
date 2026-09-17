import dns.resolver
import whois
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

class DomainChecker:
    def __init__(self, target_domain: str, max_threads: int = 10):
        self.target_domain = target_domain
        self.max_threads = max_threads

    def check_domain(self, domain: str) -> dict:
        """Verifica resolución DNS, WHOIS y asigna un puntaje de riesgo."""
        result = {
            "domain": domain,
            "registered": False,
            "ip_addresses": [],
            "registrar": None,
            "creation_date": None,
            "risk_score": 0,
            "risk_level": "LOW"
        }

        # 1. Chequeo DNS (A Records)
        try:
            answers = dns.resolver.resolve(domain, 'A')
            result["ip_addresses"] = [ip.to_text() for ip in answers]
            result["registered"] = True
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout, Exception):
            result["registered"] = False

        # Si no tiene registros DNS, asumimos que no está activo
        if not result["registered"]:
            return result

        # 2. Consulta WHOIS para enriquecimiento de inteligencia
        try:
            w = whois.whois(domain)
            result["registrar"] = w.registrar if hasattr(w, 'registrar') else None
            
            # Formatear la fecha de creación
            creation = w.creation_date if hasattr(w, 'creation_date') else None
            if isinstance(creation, list):
                creation = creation[0]
            if isinstance(creation, datetime):
                result["creation_date"] = creation.strftime("%Y-%m-%d")
            else:
                result["creation_date"] = str(creation) if creation else None
        except Exception:
            pass

        # 3. Cálculo de Nivel de Riesgo (Risk Score)
        score = 50  # Base por estar registrado
        
        # Aumentar riesgo si el dominio es reciente (menos de 1 año)
        if result["creation_date"]:
            try:
                c_date = datetime.strptime(result["creation_date"], "%Y-%m-%d")
                days_old = (datetime.now() - c_date).days
                if days_old < 365:
                    score += 30  # Recientemente registrado
            except ValueError:
                pass

        # Si posee IPs activas asociadas
        if result["ip_addresses"]:
            score += 20

        result["risk_score"] = min(score, 100)
        
        if result["risk_score"] >= 80:
            result["risk_level"] = "HIGH"
        elif result["risk_score"] >= 50:
            result["risk_level"] = "MEDIUM"
        else:
            result["risk_level"] = "LOW"

        return result

    def check_batch(self, domain_list: list) -> list:
        """Procesa múltiples dominios en paralelo usando ThreadPoolExecutor."""
        results = []
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            completed = executor.map(self.check_domain, domain_list)
            for res in completed:
                if res["registered"]:  # Guardamos solo los que realmente existen
                    results.append(res)
        return results


