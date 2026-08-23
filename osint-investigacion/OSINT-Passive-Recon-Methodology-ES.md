# Metodología de Reconocimiento OSINT Pasivo

Este repositorio documenta, con fines educativos y de portafolio, la metodología que apliqué en un proyecto académico de recopilación y análisis de información mediante técnicas de **OSINT pasivo** (Open Source Intelligence).

> **Nota sobre este repositorio:** los datos reales de personas y organizaciones utilizados durante el ejercicio original fueron omitidos o generalizados intencionalmente. Este documento muestra el **proceso, las herramientas y el razonamiento técnico**, no un inventario de objetivos reales expuestos en internet.

## Principios aplicados

Todo el trabajo se realizó bajo las siguientes reglas:

- Únicamente OSINT **pasivo** (información pública, sin interacción directa con sistemas objetivo).
- Sin escaneo agresivo, fuerza bruta, phishing, ni acceso no autorizado.
- Ante cualquier hallazgo sensible: **documentar sin profundizar ni exponer datos de terceros**.

---

## 1. Geolocalización de imágenes mediante OSINT visual

**Objetivo del ejercicio:** determinar la ubicación geográfica de una fotografía a partir únicamente de su contenido visual y metadatos, sin coordenadas GPS disponibles.

### Herramientas utilizadas

| Herramienta | Propósito |
|---|---|
| `exiftool` | Extracción de metadatos EXIF (dispositivo, fecha, parámetros de cámara) |
| [FotoForensics](https://fotoforensics.com) / [Forensically](https://29a.ch/photo-forensics) | Error Level Analysis (ELA), análisis de tablas de cuantización JPEG, extracción de segmentos binarios no estándar |
| `strings`, `binwalk` | Análisis binario de bajo nivel en busca de metadata residual no eliminada por herramientas estándar |
| Yandex Images / Google Lens | Búsqueda inversa de imagen |
| Google Maps, Street View, Google Earth | Triangulación visual del punto exacto de captura |

### Metodología aplicada

1. **Extracción de metadatos EXIF** con `exiftool`, incluyendo variantes extendidas (`-a -u -g1`) para detectar campos ocultos o no estándar.
2. Cuando el EXIF estaba ausente o incompleto, **análisis forense binario** de segmentos no estándar del archivo (por ejemplo, segmentos `APPn` propietarios de fabricante), en busca de cadenas legibles residuales.
3. **Verificación de integridad**, mediante Error Level Analysis (ELA), para descartar manipulación digital del contenido.
4. **Búsqueda inversa de imagen** como método principal de geolocalización cuando no había coordenadas GPS embebidas.
5. **Triangulación visual**: comparación sistemática de la imagen original contra fotografías de referencia geolocalizadas (reseñas de usuarios, fotos esféricas de Google Earth), buscando coincidencias de elementos arquitectónicos, geográficos y de iluminación.

### Aprendizajes clave

- La ausencia de metadatos EXIF no significa ausencia total de información: el análisis binario de segmentos propietarios (fabricante/chipset) puede revelar pistas de hardware incluso cuando el EXIF fue eliminado.
- Las tablas de cuantización JPEG permiten inferir si una imagen fue recomprimida por software estándar después de su captura original — un indicador útil de que una imagen circuló por aplicaciones de mensajería.
- La geolocalización por triangulación visual tiene límites reales: no siempre es posible confirmar un punto exacto, y es más honesto reportar un nivel de confianza que forzar una coordenada no verificada.

---

## 2. Enumeración pasiva de una organización

**Objetivo del ejercicio:** obtener el inventario de activos públicos expuestos en internet por una organización objetivo, sin realizar ningún tipo de escaneo activo o intrusivo.

### Herramientas utilizadas

`whois` · [DNSdumpster](https://dnsdumpster.com) · [crt.sh](https://crt.sh) · [VirusTotal](https://virustotal.com) (Passive DNS / Historical SSL) · `dig` / `nslookup`

### Metodología aplicada

**Paso 1 — Identificación de rangos de red y ASN**

```bash
whois <dominio>
dig <dominio> +short
whois <IP_resultante>       # consulta a LACNIC / ARIN / RIPE según la región
```

A partir del WHOIS del dominio se obtienen los servidores de nombres (nameservers); resolviendo cada uno y consultando su WHOIS de IP se obtiene el **Sistema Autónomo (ASN)** y el/los **rango(s) de red (CIDR)** asignados a la organización.

**Paso 2 — Enumeración de subdominios**

Se utilizan fuentes pasivas de reconocimiento de subdominios:

- **DNSdumpster**: mapea subdominios activos, IPs asociadas y tecnologías web detectadas (servidor, CMS, frameworks).
- **crt.sh**: consulta el histórico de certificados SSL emitidos (Certificate Transparency Logs), que suele revelar subdominios no listados en otras fuentes.

**Paso 3 — Clasificación de infraestructura: propia vs. proveedores**

Cada subdominio/IP identificado se clasifica según a quién pertenece el ASN correspondiente:

| Categoría | Cómo se identifica |
|---|---|
| Infraestructura propia | El ASN corresponde a la organización objetivo |
| Proveedor cloud (AWS / Azure / GCP) | El ASN corresponde al proveedor cloud, aunque el servicio sea gestionado por la organización |
| Proveedor de correo / SaaS | Registros MX, SPF y TXT de verificación (`google-site-verification`, `ms-domain-verification`, etc.) revelan qué proveedores de terceros usa la organización (correo, CDN, MFA, analítica) |

**Paso 4 — Detección de virtual hosts (vhosts)**

Cuando una misma IP aloja múltiples subdominios, se confirma mediante:

- **Passive DNS Replication** (VirusTotal): histórico de qué dominios han resuelto hacia esa IP.
- **Certificados SSL históricos**: la existencia de certificados individuales por dominio, todos apuntando a la misma IP, confirma *name-based virtual hosting* (el servidor decide qué sitio servir según el campo SNI de cada solicitud).

### Aprendizajes clave

- Los registros TXT de un dominio (SPF, verificaciones de propiedad) son una fuente subestimada de reconocimiento pasivo: revelan qué proveedores SaaS usa una organización sin necesidad de tocar ningún servidor.
- Combinar varias fuentes pasivas (DNSdumpster + crt.sh + VirusTotal) da una imagen mucho más completa que depender de una sola herramienta, ya que cada una indexa datos de forma distinta y con distinta frescura.
- El hosting compartido (múltiples vhosts en una sola IP) es un patrón común en instituciones con muchos sitios de bajo tráfico, y es detectable de forma completamente pasiva.

---

## 3. Construcción de dorks de búsqueda avanzada

**Objetivo del ejercicio:** construir y documentar dorks de búsqueda personalizados utilizando operadores avanzados, para identificar categorías de dispositivos y sistemas expuestos en internet (routers, switches, cámaras IP, sistemas de control industrial y portales de administración).

### Fuentes utilizadas

- **Shodan** (`http.title:`, `product:`, `country:`, `port:`)
- **Google Hacking Database (GHDB)** — repositorio público de dorks catalogados y clasificados por categoría de exposición

### Metodología general

1. **Identificar el "fingerprint"** del producto o dispositivo: el título HTML que expone su panel web, o el nombre de producto reconocido por la herramienta de búsqueda.
2. **Construir el dork** combinando el operador correcto con ese valor identificado (por ejemplo, `http.title:"<valor>"`).
3. **Ejecutar y documentar** el resultado a nivel agregado (cantidad de resultados, países, organizaciones, tecnologías), sin acceder a ningún panel, credencial o feed en vivo específico.
4. Cuando la fuente fue el GHDB, se documentó también la ficha del dork (autor, fecha de publicación, categoría), respetando la catalogación original.

### Ejemplos de dorks documentados (categorías, sin datos de objetivos reales)

```
# Portal de administración (software estándar, estructura genérica)
http.title:"phpMyAdmin"
http.title:"Log In" http.html:"wp-login"

# Router (por fabricante/producto)
http.title:"RouterOS"
http.title:"Cisco" http.title:"Router"

# Switch gestionable
http.title:"Cisco" http.title:"Switch"
http.title:"ProCurve"

# Cámara IP (catalogado en GHDB)
intitle:"Toshiba Network Camera"

# Sistema SCADA / ICS (catalogado en GHDB)
intitle:"CircarLife Scada" inurl:/html/index.html
```

### Aprendizajes clave

- La efectividad de un dork no es estática: dorks catalogados hace varios años pueden dejar de arrojar resultados a medida que los sistemas se actualizan, cambian de configuración o son dados de baja — la ausencia de resultados es en sí misma información útil.
- No todo resultado corresponde a un dispositivo real: plataformas como Shodan etiquetan explícitamente ciertos hosts como *honeypots* (señuelos), y es necesario identificarlos y excluirlos del análisis.
- Algunos dorks catalogados en el GHDB están directamente vinculados a vulnerabilidades documentadas (CVE), lo que demuestra que un dork bien construido no es una búsqueda arbitraria: apunta a un patrón de exposición con relevancia de seguridad real.

---

## Reflexión final

Este proyecto reforzó la importancia de la **divulgación responsable** en investigaciones OSINT: la mayoría de las técnicas aquí descritas requieren cero interacción directa con la infraestructura objetivo, y aun así permiten construir un panorama detallado de su superficie de exposición pública. Por esa misma razón, los hallazgos específicos obtenidos durante el ejercicio original (organización, IPs, subdominios y dispositivos concretos) se mantienen fuera de este repositorio público.

---

*Herramientas: exiftool · FotoForensics · Forensically · Yandex Images · Google Earth · whois · DNSdumpster · crt.sh · VirusTotal · Shodan · Google Hacking Database*
