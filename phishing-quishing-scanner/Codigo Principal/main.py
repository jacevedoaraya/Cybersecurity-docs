import argparse
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from core.domain_generator import DomainGenerator
from core.domain_checker import DomainChecker
from core.quishing_scanner import QuishingScanner
from utils.qr_generator import create_sample_qr

console = Console()

def run_domain_analysis(domain: str):
    console.print(Panel.fit(f"[bold cyan]Analizando Typosquatting & Homóglifos para:[/] {domain}", title="Domain Scanner"))
    
    gen = DomainGenerator(domain)
    variants = list(gen.generate_all())
    console.print(f"[yellow][*] Se generaron {len(variants)} permutaciones posibles.[/yellow]")

    console.print("[cyan][*] Verificando resoluciones DNS y registros activos...[/cyan]")
    checker = DomainChecker(target_domain=domain)
    results = checker.check_batch(variants)

    if not results:
        console.print("[bold green][+] No se encontraron dominios sospechosos actualmente registrados.[/bold green]")
        return

    table = Table(title=f"Dominios Sospechosos Registrados ({len(results)} encontrados)")
    table.add_column("Dominio", style="bold red")
    table.add_column("Direcciones IP", style="magenta")
    table.add_column("Registrar", style="blue")
    table.add_column("Risk Score", justify="right", style="yellow")

    for res in results:
        ips = ", ".join(res["ip_addresses"]) if res["ip_addresses"] else "N/A"
        registrar = res["registrar"] if res["registrar"] else "Desconocido"
        table.add_row(res["domain"], ips, str(registrar), f"{res['risk_score']}/100")

    console.print(table)

def run_qr_analysis(image_path: str, target_brand: str = None):
    console.print(Panel.fit(f"[bold cyan]Escaneando imagen QR:[/] {image_path}", title="Quishing Scanner"))
    
    scanner = QuishingScanner(target_brand_domain=target_brand)
    res = scanner.scan_image(image_path)

    if "error" in res:
        console.print(f"[bold red][!] Error:[/] {res['error']}")
        return

    console.print(f"[bold]Contenido del QR:[/] {res['raw_data']}")
    console.print(f"[bold]URL Final:[/] {res['final_url']}")
    
    color = "red" if res["risk_score"] >= 50 else "green"
    console.print(f"[bold]Score de Riesgo:[/] [{color}]{res['risk_score']}/100[/{color}]")

    if res["risk_factors"]:
        console.print("\n[bold yellow]Indicadores de Amenaza Detectados:[bold yellow]")
        for factor in res["risk_factors"]:
            console.print(f" [bold red]•[/bold red] {factor}")

def main():
    parser = argparse.ArgumentParser(description="Phishing Domain Generator & Quishing Scanner")
    parser.add_argument("-d", "--domain", help="Dominio objetivo para auditar (ej: google.com)")
    parser.add_argument("-q", "--qr", help="Ruta de la imagen QR a escanear")
    parser.add_argument("-b", "--brand", help="Dominio de marca protegida para comparar en el QR (ej: gmail.com)")
    parser.add_argument("--gen-qr", help="Genera un QR de prueba con la URL dada", metavar="URL")

    args = parser.parse_args()

    if args.gen_qr:
        create_sample_qr(args.gen_qr)
        return

    if args.domain:
        run_domain_analysis(args.domain)
    elif args.qr:
        run_qr_analysis(args.qr, args.brand)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
