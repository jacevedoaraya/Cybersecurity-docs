import json
from datetime import datetime

class Reporter:
    @staticmethod
    def export_json(data: dict, output_filename: str = "report.json"):
        data["timestamp"] = datetime.now().isoformat()
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"[+] Reporte JSON guardado en: {output_filename}")

    @staticmethod
    def export_html(data: dict, output_filename: str = "report.html"):
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Security Threat Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #1a1a1a; color: #fff; padding: 20px; }}
                h1 {{ color: #e74c3c; }}
                .card {{ background-color: #2d2d2d; border-radius: 8px; padding: 15px; margin-bottom: 15px; }}
                .high {{ color: #e74c3c; font-weight: bold; }}
            </style>
        </head>
        <body>
            <h1>Phishing & Quishing Threat Report</h1>
            <p><strong>Fecha de Generación:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <div class="card">
                <h2>Resultados del Análisis</h2>
                <pre>{json.dumps(data, indent=4, ensure_ascii=False)}</pre>
            </div>
        </body>
        </html>
        """
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"[+] Reporte HTML guardado en: {output_filename}")
