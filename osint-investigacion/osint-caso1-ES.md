# Caso 1 — Investigación OSINT de una Persona a través de un Usuario de Red Social

> **Nota:** el username y los datos identificativos de este caso fueron **anonimizados** antes de su publicación, por razones éticas y de privacidad. La metodología, herramientas y pasos documentados son fieles al ejercicio original.

## 🎯 Resumen

Este informe documenta un ejercicio de **OSINT (Open Source Intelligence)** cuyo objetivo es investigar a una persona a partir de un único dato disponible: un **nombre de usuario** encontrado en un registro de logs tras la detección de un posible ataque. No se contaba con más contexto (ni IP, ni correo, ni nombre real), por lo que toda la investigación parte de ese username.

**Usuario investigado:** `TargetUser_Case01`

**Objetivo:** determinar la identidad, actividad y posible motivación del usuario asociado a ese alias, usando únicamente fuentes públicas y herramientas de reconocimiento pasivo.

---

## 🛠 Herramientas utilizadas

| Herramienta | Función | Enlace |
|---|---|---|
| OSINT Framework | Mapa de recursos OSINT organizados por categoría | https://osintframework.com/ |
| Sherlock | Búsqueda de un username en cientos de plataformas y redes sociales | https://github.com/sherlock-project/sherlock |
| cirw.in | Herramienta para decodificar/inspeccionar claves públicas PGP | https://cirw.in/ |
| Nitter | Interfaz alternativa para consultar perfiles de Twitter/X sin necesidad de cuenta | https://nitter.net |

---

## 🔧 Fase 1 — Preparación del entorno

### 1. Exploración de OSINT Framework

Se ingresó a osintframework.com para reconocer las distintas categorías de recursos disponibles (usernames, redes sociales, correo electrónico, dominios, etc.), y así tener un mapa mental de qué herramientas usar según el tipo de dato disponible.

### 2. Instalación de Sherlock

Sherlock es una herramienta de línea de comandos que consulta cientos de sitios web para verificar si un nombre de usuario existe registrado en cada uno de ellos.

Clonación del repositorio en Kali Linux:

```bash
git clone https://github.com/sherlock-project/sherlock.git
```

### 3. Método de instalación

Siguiendo la guía oficial del proyecto, se optó por la instalación vía `apt`, compatible con distribuciones Kali y ParrotOS:

```bash
sudo apt install sherlock
```

### 4. Verificación de la instalación

```bash
sherlock --version
# Sherlock v0.16.0
```

Con esto, el entorno queda listo para iniciar la búsqueda.

---

## 🔎 Fase 2 — Investigación del usuario

### Contexto del caso

Se identificó un posible incidente de seguridad. El único indicio disponible fue un nombre de usuario dejado en un registro de logs:

**Usuario:** `TargetUser_Case01`

No se contaba con ningún otro dato adicional (IP, correo, dispositivo, etc.), por lo que la investigación debía partir exclusivamente de este alias.

### Paso 1 — Búsqueda del username con Sherlock

```bash
sherlock TargetUser_Case01
```

### Paso 2 — Análisis de resultados

Sherlock devolvió 40 coincidencias en distintas plataformas (redes sociales, foros, servicios de desarrollo, comunidades de streaming, marketplaces, etc.):

```
[*] Search completed with 40 results
```

Entre los resultados más relevantes: 7Cups, Archive.org, ArtStation, Envato Forum, GitHub, HackerEarth, Hashnode, LinkedIn, Reddit, Roblox, Spotify, Telegram, Threads, entre otros.

De todos ellos, el análisis se centró en identificar cuál plataforma podía aportar información técnica o de contacto real, más allá de simples perfiles vacíos.

### Paso 3 — Selección de la fuente más relevante: GitHub

Se identificó el siguiente perfil como el de mayor valor investigativo:

```
https://github.com/TargetUser_Case01
```

GitHub suele ser una fuente rica en OSINT porque expone:
- Proyectos y código en los que la persona trabaja.
- Posibles patrones de actividad técnica.
- Claves públicas (PGP/SSH) vinculadas a su identidad digital.
- Commits con metadatos (nombre, correo, zona horaria).

### Paso 4 — Análisis del contenido del repositorio

Al revisar los repositorios del usuario, se observó actividad relacionada con conexión a servidores para minería de criptomonedas (Bitcoin), lo cual sugiere una posible motivación económica detrás del incidente detectado.

### Paso 5 — Repositorio "PGP"

Entre los repositorios, se encontró uno llamado `PGP`, utilizado normalmente para alojar claves públicas empleadas en firmas y cifrado digital. El usuario había publicado ahí su clave pública PGP.

> **¿Qué es PGP?** Pretty Good Privacy es un estándar de cifrado que permite firmar y cifrar mensajes o archivos. Cada clave pública suele llevar asociado un identificador de usuario (nombre + correo electrónico) que puede revelar información de contacto real.

### Paso 6 — Extracción del correo desde la clave pública

Usando cirw.in para inspeccionar la clave PGP publicada, se logró extraer el identificador de correo electrónico asociado a dicha clave.

### Paso 7 — Análisis del dominio de correo

El correo hallado pertenecía a **ProtonMail**, un proveedor de correo enfocado en cifrado y privacidad de extremo a extremo.

**Implicación para la investigación:** el uso de ProtonMail indica que el usuario tiene un perfil consciente de la privacidad/OPSEC. Esto reduce significativamente la viabilidad de continuar la investigación por esa vía, ya que:
- No expone metadatos como lo haría un proveedor convencional (Gmail, Outlook).
- Dificulta correlacionar el correo con otras cuentas o filtraciones de datos.
- Cualquier intento de acceso no autorizado a ese correo sería tanto técnicamente costoso como ilegal, por lo que queda fuera del alcance de un análisis OSINT pasivo y ético.

### Paso 8 — Verificación cruzada en Nitter

Se utilizó Nitter para buscar el usuario original y confirmar actividad en redes sociales tipo Twitter/X:

**Usuario probado:** `TargetUser_Case01`

### Paso 9 — Prueba con variante del usuario

Se intentó también con una variante del alias detectada durante la investigación:

**Usuario probado:** `TargetUser_Case01_alt`

No se obtuvieron resultados ni coincidencias verificables para esta variante.

---

## ✅ Conclusiones

1. El usuario investigado (`TargetUser_Case01`) mantiene actividad relacionada con la búsqueda de máquinas vulnerables orientadas a la minería de criptomonedas (Bitcoin), lo que sugiere una motivación económica en el incidente detectado.
2. Se identificó un correo electrónico asociado a través de metadatos de una clave PGP publicada públicamente en GitHub.
3. El uso de un proveedor de correo de alta seguridad (ProtonMail) limita significativamente las posibilidades de profundizar en la investigación por canales OSINT convencionales, dado que dicho proveedor está diseñado específicamente para minimizar la exposición de metadatos.
4. La investigación se considera cerrada en su fase pasiva, ya que cualquier paso adicional (intentar acceder al correo, por ejemplo) excede el alcance ético y legal de un análisis OSINT y pasaría a constituir un acceso no autorizado.

---

## ⚠️ Nota ética y legal

Este ejercicio se realizó utilizando únicamente fuentes de información pública (redes sociales, repositorios de código abierto, claves PGP publicadas voluntariamente) y con fines de respuesta a incidentes / investigación defensiva. No se realizó ningún acceso no autorizado a sistemas, cuentas o correos. Cualquier aplicación de esta metodología debe respetar la legislación vigente sobre privacidad y protección de datos, así como contar con la debida autorización cuando se realice en un contexto corporativo o de respuesta a incidentes.

---

## 📁 Estructura sugerida para el repositorio en GitHub

```
osint-caso1-usuario-sospechoso/
├── README.md              ← este documento
├── evidencias/
│   ├── sherlock-resultados.png
│   ├── github-perfil.png
│   ├── pgp-key-decode.png
│   └── nitter-busqueda.png
└── notas/
    └── notas-adicionales.md
```

> Recuerda anonimizar o difuminar cualquier dato sensible en las capturas antes de subirlas públicamente (correos reales, IPs, nombres, etc.), incluso si el usuario investigado es ficticio o parte de un laboratorio.
