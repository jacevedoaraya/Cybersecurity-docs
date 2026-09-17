# 🛡️ Phishing Domain Generator & Quishing Scanner

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge)
![Kali Linux](https://img.shields.io/badge/Kali_Linux-Supported-dragon?style=for-the-badge)

Herramienta desarrollada en Python para Threat Intelligence y análisis defensivo enfocada en la detección de **Typosquatting/Ataques de Homóglifos** y análisis de vectores de **Quishing (QR Phishing)**.

---

## ⚡ Características Principales

- 🌐 **Generador de Variantes de Dominio:** Simulaciones de omisión, repetición, teclado QWERTY y caracteres Unicode/IDN confusables.
- 🔎 **Inteligencia en Tiempo Real:** Resoluciones DNS concurrentes y consultas WHOIS con algoritmo de Puntaje de Riesgo (Risk Score 0-100).
- 📲 **Escáner de Quishing:** Decodificación de códigos QR desde imágenes, detección de acortadores y alertas de imitación de marca.
- 🎨 **CLI Visual:** Interfaz gráfica estilizada en terminal mediante la librería `Rich`.

---

## 🚀 Guía de Uso

### 1. Auditoría de Typosquatting en Dominios
```bash
1. Main.py
python main.py -d google.com
2. Generar Código QR de Prueba
python main.py --gen-qr "[https://gmai.com](https://gmai.com)"
3. Escanear Imagen QR (Quishing)
python main.py -q samples/test_phish.png -b gmail.com
🛠️ Estructura del Proyecto
phishing-quishing-scanner/
├── core/
│   ├── domain_generator.py
│   ├── domain_checker.py
│   └── quishing_scanner.py
├── utils/
│   ├── qr_generator.py
│   └── reporter.py
├── samples/
├── main.py
├── requirements.txt
└── README.md
