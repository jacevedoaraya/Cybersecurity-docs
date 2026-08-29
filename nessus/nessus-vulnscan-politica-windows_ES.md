# Reporte de Escaneo de Vulnerabilidades — VM Windows 7 (Nessus Essentials)

**Autor:** Juan Pablo Acevedo Araya
**Contexto:** Curso de ciberseguridad — práctica de escaneo de vulnerabilidades con Nessus Essentials
**Escáner:** Tenable Nessus Essentials
**Nombre del scan:** `Politica_Windows`
**Política del scan:** Advanced Scan (sin credenciales)
**Objetivo:** `192.168.140.132` (VM local, red de laboratorio aislada)
**Duración:** 6 minutos (10:51 AM – 10:57 AM)

> ⚠️ **Nota de alcance:** Este escaneo se realizó contra una máquina virtual personal en una red de laboratorio casero aislada, estrictamente con fines educativos como parte de un curso de ciberseguridad. No se escaneó ningún sistema externo o de terceros.

---

## 1. Objetivo

Realizar un primer escaneo de vulnerabilidades sin credenciales contra una máquina virtual Windows 7 usando Nessus Essentials, documentar los hallazgos, y practicar la lectura/interpretación de reportes de vulnerabilidades de Nessus (CVSS, CVE, VPR, EPSS, remediación).

## 2. Resumen del escaneo

| Elemento | Valor |
|---|---|
| Host | 192.168.140.132 |
| Sistema Operativo | Microsoft Windows 7 Professional (sin soporte) |
| Autenticación | Fallida (escaneo sin credenciales) |
| Total de vulnerabilidades encontradas | 28 |
| Críticas | 2 |
| Altas | 3 |
| Medias | 9 |
| Bajas | 2 |
| Informativas | 12 |

**Nota sobre la autenticación:** el escaneo se ejecutó sin credenciales válidas en el objetivo ("Auth: Fail"), lo que significa que Nessus solo evaluó lo que es visible desde el lado de la red (puertos abiertos, servicios expuestos, debilidades de protocolo) — no el estado interno del sistema operativo (parches instalados, configuraciones locales incorrectas, etc.). Un escaneo con credenciales probablemente revelaría hallazgos adicionales.

## 3. Hallazgos detallados

### 🔴 Críticas

#### 3.1 — Unsupported Windows OS (remote)
- **Plugin ID:** 108797
- **CVSS v3.0 Base Score:** 10.0
- **Descripción:** El sistema operativo instalado (Microsoft Windows 7 Professional) ya no cuenta con soporte de Microsoft, lo que significa que ya no recibe parches de seguridad. Como resultado, es muy probable que contenga vulnerabilidades sin corregir.
- **Solución:** Actualizar a una versión de sistema operativo o service pack que sí cuente con soporte.

#### 3.2 — Microsoft RDP RCE (CVE-2019-0708) "BlueKeep" (uncredentialed check)
- **Plugin ID:** 125313
- **CVE:** CVE-2019-0708
- **VPR (Vulnerability Priority Rating):** 9.5
- **EPSS (Exploit Prediction Scoring System):** 1.0 (máximo — probabilidad muy alta de explotación real)
- **Descripción:** Una vulnerabilidad de ejecución remota de código en el Protocolo de Escritorio Remoto (RDP). Un atacante no autenticado puede enviar solicitudes especialmente diseñadas para ejecutar código arbitrario en el objetivo, sin ninguna interacción del usuario.
- **Solución:** Aplicar los parches oficiales de Microsoft (publicados para Windows XP, 2003, 2008, 7 y 2008 R2).
- **Por qué importa:** BlueKeep es una de las vulnerabilidades "wormeables" (con capacidad de auto-propagarse) más conocidas de la última década — puede potencialmente propagarse automáticamente entre sistemas vulnerables, de forma similar a WannaCry.

### 🟠 Altas

#### 3.3 — MS12-020: Vulnerabilities in Remote Desktop Could Allow Remote Code Execution
- **Plugin ID:** 58435
- **Descripción:** Existe una vulnerabilidad de ejecución remota de código arbitrario en la implementación de RDP, debido a un manejo incorrecto de un objeto en memoria. Un atacante remoto no autenticado podría explotar esto enviando paquetes RDP especialmente diseñados, pudiendo también causar una denegación de servicio.
- **Solución:** Aplicar los parches oficiales de Microsoft (Windows XP, 2003, Vista, 2008, 7 y 2008 R2).

#### 3.4 — MS17-010: Security Update for Microsoft Windows SMB Server (4013389) — "EternalBlue"
- **Plugin ID:** 97833
- **CVEs:** CVE-2017-0143, CVE-2017-0144, CVE-2017-0145, CVE-2017-0146, CVE-2017-0147, CVE-2017-0148
- **Descripción:** Múltiples vulnerabilidades de ejecución remota de código en SMBv1 debido a un manejo incorrecto de ciertas solicitudes. Un atacante no autenticado puede explotarlas mediante un paquete especialmente diseñado para ejecutar código arbitrario, o divulgar información sensible.
- **Por qué importa:** Este es el conjunto de vulnerabilidades detrás de **EternalBlue**, el exploit filtrado por el grupo Shadow Brokers y usado para propagar el ransomware **WannaCry** y el malware destructivo **NotPetya** en 2017 — entre los ciberataques más dañinos de la historia.
- **Solución:** Aplicar los parches oficiales de Microsoft (Vista, 2008, 7, 2008 R2, 2012, 8.1, RT 8.1, 2012 R2, 10 y 2016, incluyendo parches de emergencia para sistemas sin soporte como XP y 2003).

### 🟡 Medias

#### 3.5 — Remote Desktop Protocol Server Man-in-the-Middle Weakness
- **Plugin ID:** 18405
- **CVE:** CVE-2005-1794
- **CVSS v3.0 Base Score:** 6.5
- **Descripción:** El servidor RDP no valida su identidad ante el cliente durante la configuración del cifrado, ya que almacena una clave privada RSA fija y públicamente conocida. Un atacante posicionado en la red puede interceptar la conexión y realizar un ataque de intermediario (MITM), pudiendo capturar credenciales de autenticación.
- **Solución:** Forzar el uso de SSL/TLS como capa de transporte para RDP, y/o habilitar la opción "Allow connections only from computers running Remote Desktop with Network Level Authentication."

#### 3.6 — TLS Version 1.0 Protocol Detection
- **Plugin ID:** 104743
- **CVSS v3.0 Base Score:** 6.5
- **Descripción:** El servicio remoto acepta conexiones usando TLS 1.0, un protocolo obsoleto con fallos criptográficos conocidos. PCI DSS v3.2 exige deshabilitar TLS 1.0 por completo desde el 30 de junio de 2018.
- **Solución:** Habilitar TLS 1.2 y 1.3, y deshabilitar TLS 1.0.

#### 3.7 — SSL Certificate Signed Using Weak Hashing Algorithm
- **Plugin ID:** 35291
- **CVEs:** CVE-2004-2761, CVE-2005-4900
- **CVSS v3.0 Base Score:** 5.3
- **Descripción:** La cadena de certificados SSL fue firmada usando un algoritmo de hash criptográficamente débil (SHA-1), el cual es vulnerable a ataques de colisión. Un atacante podría, en teoría, falsificar otro certificado con la misma firma digital.
- **Solución:** Contactar a la autoridad certificadora para que el certificado sea reemitido con un algoritmo más robusto (ej. SHA-256).

---

## 4. Resumen del análisis de riesgo

| # | Hallazgo | Severidad | CVSS v3 | Causa raíz |
|---|---|---|---|---|
| 1 | Unsupported Windows OS | Crítica | 10.0 | Sistema operativo sin soporte (EOL) |
| 2 | BlueKeep (CVE-2019-0708) | Crítica | — (VPR 9.5) | Servicio RDP sin parchar |
| 3 | MS12-020 RDP RCE | Alta | — | Servicio RDP sin parchar |
| 4 | MS17-010 / EternalBlue | Alta | — | Servicio SMBv1 sin parchar |
| 5 | RDP MITM Weakness | Media | 6.5 | Configuración de cifrado RDP débil por defecto |
| 6 | TLS 1.0 habilitado | Media | 6.5 | Configuración TLS obsoleta |
| 7 | Firma de certificado SSL débil | Media | 5.3 | Algoritmo de firma de certificado débil |

**Hilo conductor:** Casi todos los hallazgos se remontan a dos causas raíz — (1) un sistema operativo sin soporte y sin parchar, y (2) configuraciones de protocolo heredadas/inseguras por defecto (RDP sin NLA, SMBv1, TLS 1.0). Esto es esperado e intencional para una VM de laboratorio con Windows 7 usada para practicar escaneo de vulnerabilidades, pero ilustra claramente por qué los sistemas sin soporte acumulan riesgo crítico con el tiempo.

## 5. Prioridades de remediación recomendadas

1. **Inmediato:** Parchar o deshabilitar RDP si no es estrictamente necesario (resuelve BlueKeep y MS12-020 — ambas vulnerabilidades RCE Crítica/Alta).
2. **Inmediato:** Parchar las vulnerabilidades de SMBv1 (MS17-010) o deshabilitar SMBv1 por completo si no se requiere por compatibilidad con sistemas heredados.
3. **Corto plazo:** Habilitar Network Level Authentication (NLA) para RDP y así mitigar la debilidad de MITM.
4. **Corto plazo:** Deshabilitar TLS 1.0 y forzar el uso de TLS 1.2/1.3.
5. **Largo plazo:** Dado que el sistema operativo en sí no tiene soporte, la solución más efectiva es actualizar a una versión de Windows actualmente soportada — parchar vulnerabilidades individuales en un sistema EOL es una mitigación temporal, no una solución permanente.

## 6. Lecciones aprendidas

1. **Los escaneos sin credenciales son limitados.** Con `Auth: Fail`, Nessus solo puede ver lo que está expuesto por la red — un escaneo con credenciales (con credenciales válidas de administrador de Windows) probablemente revelaría vulnerabilidades locales adicionales, parches faltantes y configuraciones incorrectas.
2. **Nessus Essentials no permite exportar a PDF/HTML** — esa función requiere una licencia paga (Nessus Professional/Expert). Los hallazgos tuvieron que revisarse manualmente dentro de la interfaz web (paneles de detalle por vulnerabilidad), lo cual es más lento pero funciona bien para documentación a pequeña escala.
3. **El VPR y el EPSS importan tanto como el CVSS.** El puntaje CVSS de BlueKeep no fue la métrica más alta mostrada, pero su **EPSS de 1.0** (probabilidad casi certera de explotación real) y su **VPR de 9.5** lo convierten en el hallazgo más urgente de todo el escaneo — un buen recordatorio de que el CVSS por sí solo no siempre cuenta toda la historia del riesgo.
4. **Un puñado de causas raíz explica la mayoría de los hallazgos.** En vez de tratar 28 vulnerabilidades como 28 problemas separados, agruparlas por causa raíz (SO sin soporte, mala configuración de RDP, SMBv1, TLS obsoleto) hace que la planificación de remediación sea mucho más manejable.
5. **Los CVEs históricos siguen siendo muy relevantes en laboratorios de entrenamiento.** Aunque MS17-010 (EternalBlue) y CVE-2019-0708 (BlueKeep) tienen varios años, siguen siendo ejemplos de libro de texto para entender la ejecución remota de código y las vulnerabilidades con capacidad de propagación tipo gusano — precisamente por eso siguen apareciendo de forma prominente en una máquina de laboratorio Windows 7 sin parchar.

---

## 📎 Referencia rápida — Escala de severidad de vulnerabilidades (Nessus / CVSS v3)

| Severidad | Rango CVSS v3 |
|---|---|
| Crítica | 9.0 – 10.0 |
| Alta | 7.0 – 8.9 |
| Media | 4.0 – 6.9 |
| Baja | 0.1 – 3.9 |
| Informativa | 0.0 (solo informativo) |
