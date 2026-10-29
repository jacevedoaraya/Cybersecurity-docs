# Cybersecurity Docs 🔐

Documentación y notas técnicas de ciberseguridad, disponibles en **español** e **inglés**.

## 👋 Sobre mí 
Aspirante a **SOC Analyst / Analista de Seguridad**, en formación activa en ciberseguridad defensiva y ofensiva. Este repositorio reúne la documentación técnica que voy generando en mis laboratorios:
configuración y uso de SIEM (Wazuh), hardening de sistemas, pruebas de penetración y análisis OSINT.

## 📂 Contenido

| Carpeta | Descripción |
|---|---|
| [osint-monitoring-pipeline](osint-monitoring-pipeline/) | Pipeline de monitoreo OSINT con Docker: convierte canales de Telegram en feeds (RSS-Bridge), reúne fuentes de inteligencia en FreshRSS y envía alertas al celular (changedetection.io + ntfy) cuando aparecen nuevas víctimas de ransomware en Costa Rica. |
|[**`android-apk-lab/`**](./android-apk-lab/) |Laboratorio de análisis estático de apps Android con apktool, jadx, dex2jar, JD-GUI y MobSF sobre UnCrackable-Level1 (OWASP). Incluye reto de descifrado en Python y comparación entre revisión manual y automática (MobSF 55/100). Guía para principiantes en español e inglés. |
| [`sonarqube-sast-lab/`](sonarqube-sast-lab/) | Laboratorio SAST: despliegue de SonarQube Community con Docker Compose y análisis estático de OWASP WebGoat (529 issues, 8 vulnerabilidades). Guía bilingüe ES/EN |
| [sql-injection-lab/](sql-injection-lab/) | Reporte de pentest de inyección SQL (SQLi) sobre el laboratorio Web for Pentester (PentesterLab): 9 ejemplos con payloads, bypass de filtros, UNION-based injection y extracción de credenciales |
| [`XSS-Web-for-Pentesters/`](./XSS-Web-for-Pentesters/) | Reporte de pentest de Cross-Site Scripting (XSS) sobre el laboratorio Web for Pentester (PentesterLab): payloads, análisis de filtros y contramedidas por cada ejemplo |
| [`phishing-quishing-scanner/`](./phishing-quishing-scanner/) | Generador de dominios de Typosquatting/Homóglifos y escáner de Quishing (QR Phishing) en Python *(Disponible solo en español)* |
| [`siem-wazuh/`](./siem-wazuh) | Configuración, uso y notas sobre Wazuh (SIEM) |
| [`security-onion/`](./security-onion) | Personalización del entorno gráfico (GNOME) y solución de firewall/pillar para enrolamiento de agentes |
| [`pentest-misp/`](./pentest-misp) | Reporte de pentest CTF: explotación de infraestructura Docker + MISP |
| [`osint-investigacion/`](./osint-investigacion) | Caso de investigación OSINT: identificación de usuario a partir de un username (datos anonimizados) |
| [nessus/](nessus/) | Instalación y troubleshooting de Tenable Nessus (Essentials) en Windows, más análisis de vulnerabilidades (scan a VM Windows 7: BlueKeep, EternalBlue, entre otros) |

## 🌐 Idiomas

Cada tema incluye documentación en ambos idiomas, identificada con el sufijo del archivo:
- `*_ES.md` → Español
- `*_EN.md` → English

## 🚧 En construcción

Este repositorio se actualiza de forma continua a medida que se agrega nueva documentación (hardening, análisis de logs, pentesting, entre otros).
