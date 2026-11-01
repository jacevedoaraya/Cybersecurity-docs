# Robin en una VM de OSINT: guía de instalación con Gemini, Ollama y lanzador de escritorio

🌐 [English](README.md) | **Español**

Esta guía documenta la instalación y configuración de [Robin](https://github.com/apurvsinghgautam/robin), una herramienta de OSINT para la dark web que usa modelos de lenguaje (LLM) para refinar búsquedas, filtrar resultados de buscadores `.onion` y generar resúmenes de investigación.

Se documentan tres etapas, en el orden en que se realizaron:

1. **Robin con Gemini** (API en la nube de Google).
2. **Robin con Ollama** (modelo local, sin enviar datos a proveedores de IA).
3. **Lanzador de escritorio** para iniciar Robin con un doble clic.

Cada etapa incluye sus pros y contras, y al final hay una comparación general.

> ⚠️ **Aviso legal.** Robin está pensado solo para fines educativos e investigaciones legales. Acceder a cierto contenido de la dark web puede ser ilegal según tu jurisdicción. Úsalo bajo tu propia responsabilidad y cumple las leyes y políticas que te apliquen.

---

## Índice

- [Entorno utilizado](#entorno-utilizado)
- [Parte 0: preparación del sistema](#parte-0-preparación-del-sistema)
- [Parte 1: Robin con Gemini](#parte-1-robin-con-gemini)
- [Parte 2: Robin con Ollama (modelo local)](#parte-2-robin-con-ollama-modelo-local)
- [Parte 3: lanzador de escritorio](#parte-3-lanzador-de-escritorio)
- [Comparación general](#comparación-general)
- [Cambiar entre Gemini y Ollama](#cambiar-entre-gemini-y-ollama)
- [Solución de problemas](#solución-de-problemas)
- [Recomendaciones de seguridad](#recomendaciones-de-seguridad)
- [Créditos](#créditos)

---

## Entorno utilizado

| Componente | Detalle |
|---|---|
| Virtualización | VirtualBox, red en modo **NAT** |
| Sistema operativo | Debian GNU/Linux 13 (trixie), escritorio XFCE |
| Recursos (con Gemini) | 4 GB de RAM, 2 núcleos |
| Recursos (con Ollama) | 12 GB de RAM, 3 núcleos (equipo anfitrión: 20 GB, 4 núcleos) |
| Disco | 60 GB |
| Robin | Imagen oficial `apurvsg/robin:latest` |
| Puerto de la interfaz | `8501` (Streamlit) |

---

## Parte 0: preparación del sistema

### 0.1 Snapshot de la VM

Antes de empezar, crea una instantánea en VirtualBox desde **Máquina → Tomar instantánea...**. Si algo falla, podrás volver a un estado limpio.

### 0.2 Actualizar el sistema

```bash
cat /etc/os-release              # confirma la distribución
sudo apt update && sudo apt upgrade -y
```

### 0.3 Instalar Docker y Tor

```bash
sudo apt install -y docker.io tor
sudo systemctl enable --now docker tor
```

Verificación de Tor. En Debian, `tor.service` es un servicio "maestro" que aparece como `active (exited)`; el que hace el trabajo real es `tor@default`:

```bash
systemctl status tor@default     # debe decir: active (running)
sudo ss -tlnp | grep 9050        # debe mostrar 127.0.0.1:9050
```

> **Nota:** durante las pruebas se comprobó que el contenedor de Robin **trae su propio Tor** (en el arranque muestra `Starting Tor... Tor is ready.`). El servicio Tor del sistema no es estrictamente necesario para Robin, aunque no causa conflictos.
>
> **Tor Browser no sustituye al servicio Tor.** El navegador incluye su propio Tor, pero solo funciona mientras está abierto y solo para ese navegador (puerto 9150).

### 0.4 Descargar la imagen oficial

```bash
sudo docker pull apurvsg/robin:latest
```

> Usa solo la imagen y el repositorio del autor original (`apurvsinghgautam/robin`). Existen muchos forks; una copia modificada podría contener código malicioso.

### 0.5 Carpeta de trabajo

```bash
mkdir -p ~/robin/investigations && cd ~/robin
id -u                            # debe devolver 1000
```

El contenedor se ejecuta como UID 1000. Crear la carpeta `investigations` antes del primer arranque evita que Docker la cree como `root` y que Robin no pueda guardar las investigaciones.

---

## Parte 1: Robin con Gemini

### 1.1 Obtener la API key

1. Entra a <https://aistudio.google.com/app/apikey> con tu cuenta de Google. Es recomendable hacerlo desde el navegador **dentro de la VM**, para poder copiar y pegar la clave directamente.
2. Usa la clave existente o haz clic en **Create API key**.
3. Copia la clave (empieza con `AIza...`).

### 1.2 Crear el archivo `.env`

```bash
cd ~/robin
nano .env
```

Contenido, en una sola línea y sin espacios:

```
GOOGLE_API_KEY=AIzaTuClaveAqui
```

En la terminal se pega con **Ctrl+Shift+V**. Para guardar: **Ctrl+O**, **Enter**, **Ctrl+X**.

Protege el archivo y verifícalo sin mostrar la clave:

```bash
chmod 600 .env
cut -d= -f1 .env                 # debe mostrar solo: GOOGLE_API_KEY
```

> Robin también acepta `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `MISTRAL_API_KEY` y `OPENROUTER_API_KEY`. Basta con una.

### 1.3 Ejecutar Robin

```bash
cd ~/robin
sudo docker run --rm \
   -v "$(pwd)/.env:/app/.env" \
   -v "$(pwd)/investigations:/app/investigations" \
   -e STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
   --add-host=host.docker.internal:host-gateway \
   -p 127.0.0.1:8501:8501 \
   apurvsg/robin:latest
```

Qué hace cada opción:

| Opción | Función |
|---|---|
| `-v .../.env:/app/.env` | Entrega la API key al contenedor |
| `-v .../investigations:...` | Conserva las investigaciones entre reinicios |
| `-e STREAMLIT_BROWSER_GATHER_USAGE_STATS=false` | Desactiva la telemetría de Streamlit |
| `--add-host=host.docker.internal:host-gateway` | Permite al contenedor llegar a servicios de la VM (necesario para Ollama) |
| `-p 127.0.0.1:8501:8501` | Publica la interfaz **solo** en la VM, no en la red |

Salida esperada:

```
Tor is ready.
Refreshing model list from providers...
  google       24 models
Starting Robin: AI-Powered Dark Web OSINT Tool...
```

> La línea `External URL` que muestra Streamlit es solo informativa. Como el puerto está ligado a `127.0.0.1`, la interfaz no es accesible desde fuera de la VM.

### 1.4 Usar la interfaz

Abre **Firefox** (no Tor Browser) en `http://localhost:8501`. La interfaz está en la propia VM y Robin ya hace las búsquedas por Tor internamente. Tor Browser normalmente no puede abrir `localhost`.

Para abrir manualmente un enlace `.onion` de los resultados, cópialo y ábrelo en **Tor Browser**, nunca en Firefox.

### 1.5 Pros y contras de Gemini

| ✅ Pros | ❌ Contras |
|---|---|
| Rápido: las investigaciones terminan en poco tiempo | Las búsquedas y el contenido extraído se envían a Google para su análisis |
| Muy buena calidad de resumen y filtrado | Las llamadas a la API **no pasan por Tor**: Google ve la IP pública real |
| Pocos recursos: funciona con 4 GB de RAM y 2 núcleos | En el nivel gratuito, Google puede usar el contenido para mejorar sus productos (consulta los términos vigentes) |
| Configuración sencilla: una sola línea en `.env` | Depende de una cuenta de Google y de conexión a internet |
| Nivel gratuito disponible | Límites de uso (rate limits) del plan gratuito |
| Acceso a varios modelos (24 detectados) | La API key es un secreto que hay que proteger; si se filtra, alguien podría usarla a tu nombre |

---

## Parte 2: Robin con Ollama (modelo local)

Con Ollama, el modelo de IA corre dentro de la VM. Lo único que sale a internet son las búsquedas y el scraping, que van por Tor.

### 2.1 Aumentar los recursos de la VM

Un modelo de 8B parámetros necesita bastante RAM. Comprueba los recursos actuales:

```bash
free -h
nproc
df -h ~
```

Si hace falta, apaga la VM (`sudo poweroff`) y en VirtualBox ve a **Configuración → Sistema**:

- **Placa base → Memoria base:** 12288 MB.
- **Procesador:** 3.

Deja siempre memoria suficiente para el equipo anfitrión (en este caso, 8 GB y 1 núcleo).

Guía orientativa de modelos según la RAM de la VM:

| RAM de la VM | Modelo sugerido | Comentario |
|---|---|---|
| < 8 GB | `llama3.2:1b` / `llama3.2:3b` | Funciona, pero con resultados limitados |
| 8–16 GB | `llama3.1:8b` | Buen equilibrio (el usado en esta guía) |
| > 16 GB | Modelos mayores | Mejor calidad, más lentos sin GPU |

### 2.2 Instalar Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

En una VM aparecerá `No NVIDIA/AMD GPU detected. Ollama will run in CPU-only mode.` Es normal.

### 2.3 Permitir que el contenedor llegue a Ollama

Por defecto Ollama escucha solo en `127.0.0.1:11434`, que el contenedor no puede alcanzar.

```bash
sudo systemctl edit ollama.service
```

En el espacio entre `### Anything between here...` y `### Edits below this comment will be discarded`, escribe:

```ini
[Service]
Environment="OLLAMA_HOST=0.0.0.0"
```

Guarda, reinicia y verifica:

```bash
sudo systemctl daemon-reload && sudo systemctl restart ollama
sudo ss -tlnp | grep 11434       # debe mostrar *:11434
```

> Con la red de VirtualBox en modo NAT, la red local no puede llegar a la VM, por lo que Ollama no queda expuesto. Si usas modo **Adaptador puente**, protege el puerto 11434 con un firewall.

### 2.4 Descargar y probar el modelo

```bash
ollama pull llama3.1:8b          # ~4.9 GB
ollama run llama3.1:8b "Hola, responde en una frase"
```

### 2.5 Desactivar la clave de Gemini

Para garantizar que nada se envíe a Google, comenta la línea en `.env`:

```bash
nano ~/robin/.env
```

```
#GOOGLE_API_KEY=AIza...
```

Para Ollama **no se necesita** ninguna variable en `.env`: Robin usa por defecto `http://host.docker.internal:11434`.

### 2.6 Ejecutar Robin

Usa el mismo comando de la sección 1.3. En el arranque ya no aparecerá la línea `google 24 models`.

En la interfaz, el modelo aparece en la barra lateral como **`[ollama] llama3.1:8b`** ("Locally detected Ollama models are automatically added to this list").

### 2.7 Pros y contras de Ollama

| ✅ Pros | ❌ Contras |
|---|---|
| **Privacidad total del análisis:** ni las búsquedas ni el contenido extraído salen hacia un proveedor de IA | Exige mucha RAM: 8 GB como mínimo práctico, 12 GB o más recomendados |
| Sin API keys, cuentas ni secretos que proteger | **Lento** sin GPU: cada investigación puede tardar varios minutos |
| Sin costo por uso ni límites de peticiones | Menor calidad de filtrado y resumen que los modelos grandes en la nube |
| El análisis funciona sin depender de servicios externos | Ocupa ~5 GB de disco por modelo |
| Control completo sobre el modelo y su versión | Configuración más compleja (systemd, `OLLAMA_HOST`) |
| | Escuchar en `0.0.0.0` requiere cuidar la configuración de red de la VM |
| | La VM se vuelve lenta mientras el modelo trabaja |

---

## Parte 3: lanzador de escritorio

Para evitar escribir el comando largo cada vez, se crea un script y un ícono en el escritorio.

### 3.1 Script de inicio

El script arranca Robin y abre Firefox automáticamente cuando la interfaz está lista.

```bash
cat > ~/robin/iniciar.sh << 'EOF'
#!/bin/bash
cd ~/robin
( until curl -s http://localhost:8501 >/dev/null; do sleep 2; done
  firefox http://localhost:8501 ) &
sudo docker run --rm \
   -v "$(pwd)/.env:/app/.env" \
   -v "$(pwd)/investigations:/app/investigations" \
   -e STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
   --add-host=host.docker.internal:host-gateway \
   -p 127.0.0.1:8501:8501 \
   apurvsg/robin:latest
EOF
chmod +x ~/robin/iniciar.sh
```

Desde la terminal basta con ejecutar `~/robin/iniciar.sh`.

### 3.2 Ícono en el escritorio (XFCE)

```bash
cat > "$(xdg-user-dir DESKTOP)/Robin.desktop" << 'EOF'
[Desktop Entry]
Type=Application
Name=Robin
Comment=AI-Powered Dark Web OSINT Tool
Exec=xfce4-terminal --title=Robin -e "bash -c '~/robin/iniciar.sh; read -p \"Robin se detuvo. Presiona Enter para cerrar...\"'"
Icon=utilities-terminal
Terminal=false
EOF
chmod +x "$(xdg-user-dir DESKTOP)/Robin.desktop"
```

### 3.3 Uso

1. Doble clic en el ícono **Robin**.
2. La primera vez aparece "Untrusted application launcher". Elige **Mark As Secure And Launch**.
3. Escribe la contraseña de `sudo` en la ventana de terminal.
4. Firefox se abre solo con la interfaz.

Para detener Robin: en la ventana "Robin", **Ctrl+C** y luego **Enter**.

### 3.4 Pros y contras del lanzador

| ✅ Pros | ❌ Contras |
|---|---|
| Inicio con un doble clic | Sigue pidiendo la contraseña de `sudo` en cada arranque |
| Abre el navegador automáticamente | Depende de XFCE (`xfce4-terminal`); en otros escritorios hay que cambiar el comando |
| Evita errores al escribir el comando largo | Las rutas (`~/robin`) y el navegador (`firefox`) están fijos en el script |
| Siempre usa las mismas opciones de seguridad | La ventana de terminal debe permanecer abierta mientras Robin funciona |
| Fácil de editar en un solo archivo | Requiere marcar el lanzador como confiable la primera vez |

> **Sobre evitar `sudo`:** agregar el usuario al grupo `docker` eliminaría la contraseña, pero ese grupo equivale en la práctica a acceso de `root`. En esta guía se mantiene `sudo` a propósito.

---

## Comparación general

| Criterio | Gemini | Ollama (`llama3.1:8b`) |
|---|---|---|
| Privacidad del análisis | Baja: el contenido va a Google | Alta: todo queda en la VM |
| Exposición de IP al proveedor de IA | Sí (la API no usa Tor) | No aplica |
| Velocidad | Alta | Baja (solo CPU) |
| Calidad de resultados | Alta | Media |
| RAM necesaria en la VM | ~4 GB | ~12 GB recomendados |
| Disco adicional | Mínimo | ~5 GB por modelo |
| Costo | Gratis con límites / pago por uso | Gratis |
| Dificultad de configuración | Baja | Media |
| Requiere cuenta externa | Sí | No |

**¿Cuál elegir?**

- **Gemini:** para pruebas, aprendizaje o equipos con pocos recursos, cuando las búsquedas no son sensibles.
- **Ollama:** para investigaciones donde la confidencialidad importa más que la velocidad.
- **Lanzador de escritorio:** recomendable en ambos casos, por comodidad.

---

## Cambiar entre Gemini y Ollama

Solo hay que editar `~/robin/.env` y reiniciar Robin:

| Para usar | Línea en `.env` |
|---|---|
| Gemini | `GOOGLE_API_KEY=AIza...` (sin `#`) |
| Solo Ollama | `#GOOGLE_API_KEY=AIza...` (comentada) |

Si la clave está activa y Ollama también corre, ambos aparecerán en el selector de modelos de la interfaz.

---

## Solución de problemas

| Problema | Causa probable | Solución |
|---|---|---|
| `tor.service` aparece como `active (exited)` | Comportamiento normal en Debian | Revisa `systemctl status tor@default` |
| `No such file or directory` al ejecutar `iniciar.sh` | El script no se creó | Repite la sección 3.1 |
| Al salir de nano pregunta "Save modified buffer?" | No se guardó con Ctrl+O | Presiona `Y` y luego `Enter` |
| No aparecen modelos de Ollama | Ollama escucha solo en `127.0.0.1` | Revisa la sección 2.3 y `ss -tlnp \| grep 11434` |
| No se guardan investigaciones | La carpeta pertenece a `root` o el UID no es 1000 | Crea la carpeta antes del primer arranque; revisa `id -u` |
| El lanzador no hace nada | El escritorio no usa `xfce4-terminal` | Cambia el comando de terminal en `Robin.desktop` |

Prueba de conexión entre el contenedor y Ollama (con Robin en marcha, desde otra terminal):

```bash
sudo docker exec $(sudo docker ps -q --filter ancestor=apurvsg/robin:latest) \
  python -c "import urllib.request;print(urllib.request.urlopen('http://host.docker.internal:11434/api/tags').read()[:300])"
```

---

## Recomendaciones de seguridad

- Toma un **snapshot** de la VM antes de cambios importantes.
- Mantén la red de VirtualBox en modo **NAT**.
- Publica la interfaz solo en `127.0.0.1` (`-p 127.0.0.1:8501:8501`).
- Protege `.env` con `chmod 600` y **nunca** lo subas a GitHub. Agrega `.env` a tu `.gitignore`.
- Abre enlaces `.onion` solo en Tor Browser y no descargues archivos de esos sitios.
- Actualiza la imagen periódicamente con `sudo docker pull apurvsg/robin:latest`.
- Para borrar investigaciones locales: `rm -f ~/robin/investigations/*`.

Ejemplo de `.gitignore` para este repositorio:

```
.env
investigations/
```

---

## Créditos

- **Robin** fue creado por [Apurv Singh Gautam](https://github.com/apurvsinghgautam) y se distribuye bajo licencia MIT: <https://github.com/apurvsinghgautam/robin>
- **Ollama:** <https://ollama.com>
- **Tor Project:** <https://www.torproject.org>

Esta guía documenta una instalación personal en un entorno de laboratorio y no está afiliada al autor de Robin.
