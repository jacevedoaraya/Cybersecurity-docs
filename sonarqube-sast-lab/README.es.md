# 🔍 Laboratorio SAST con SonarQube

[English](README.md) | **Español**

![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![SonarQube](https://img.shields.io/badge/SonarQube-Community-4E9BCD?logo=sonarqube&logoColor=white)
![Java](https://img.shields.io/badge/Java-Maven-ED8B00?logo=openjdk&logoColor=white)
![Kali](https://img.shields.io/badge/Kali-Linux-557C94?logo=kalilinux&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

Laboratorio práctico que despliega **SonarQube Community** con **Docker Compose** y lo usa para ejecutar **SAST (Static Application Security Testing)** sobre **OWASP WebGoat**, una aplicación Java vulnerable a propósito. Se realizó como proyecto de un curso de ciberseguridad y está documentado como pieza de portafolio.

> ⚠️ **Solo con fines educativos.** Escanea únicamente código propio, código hecho para practicar (como WebGoat) o código con autorización por escrito para probarlo.

---

## 📑 Tabla de contenido
- [¿Qué es SAST?](#-qué-es-sast)
- [Arquitectura](#-arquitectura)
- [Requisitos](#-requisitos)
- [Estructura del repositorio](#-estructura-del-repositorio)
- [Inicio rápido](#-inicio-rápido)
- [Guía paso a paso](#-guía-paso-a-paso)
- [Resultados: escaneo de WebGoat](#-resultados-escaneo-de-webgoat)
- [Cómo leer y reportar hallazgos](#-cómo-leer-y-reportar-hallazgos)
- [Solución de problemas](#-solución-de-problemas)
- [Notas de seguridad](#-notas-de-seguridad)
- [Referencias](#-referencias)

---

## 🧠 ¿Qué es SAST?
**SAST** analiza el **código fuente sin ejecutarlo** para encontrar errores, vulnerabilidades y código de baja calidad de forma temprana. Complementa a **DAST** (pruebas sobre la aplicación en ejecución) y a la revisión manual.

**SonarQube** escanea el código y muestra los hallazgos en un panel web, clasificados por **tipo** y **severidad**:

| Tipo | Significado |
|---|---|
| **Bug** | Error de código que probablemente cause un comportamiento incorrecto. |
| **Vulnerability** | Fallo de seguridad explotable. |
| **Security Hotspot** | Código sensible que requiere **revisión manual**. |
| **Code Smell** | Problema de mantenibilidad; no siempre es un riesgo de seguridad. |

## 🏗️ Arquitectura
```
 ┌──────────────┐   mvn sonar:sonar    ┌────────────────────┐      ┌──────────────────┐
 │  WebGoat     │ ───────────────────► │ SonarQube :9000    │ ───► │ PostgreSQL 16    │
 │  (Maven/Java)│   (con token)        │ (contenedor Docker)│      │ (contenedor Docker)│
 └──────────────┘                      └────────────────────┘      └──────────────────┘
                                                │
                                         Firefox → http://localhost:9000
```

## ✅ Requisitos
- Linux (probado en **Kali Linux**)
- **Docker** y **Docker Compose** v2
- **JDK** (probado con OpenJDK 25.0.4) y **Maven**
- **Git**
- ~4 GB de RAM libre para SonarQube

Verificar:
```bash
java -version && javac -version && mvn -version && docker --version
```

## 📁 Estructura del repositorio
```
sonarqube-sast-lab/
├── README.md                  # Documentación en inglés
├── README.es.md               # Documentación en español
├── LICENSE
├── .gitignore
├── .env.example               # Plantilla de credenciales (copiar a .env)
├── docker-compose.yml         # SonarQube + PostgreSQL
├── scripts/
│   ├── setup-sysctl.sh        # Parámetros del kernel que requiere SonarQube
│   └── scan.sh                # Compila y escanea un proyecto Maven
├── docs/
│   ├── finding-template.md    # Plantilla bilingüe de reporte de hallazgo
│   └── screenshots/           # Imágenes de evidencia
└── projects/                  # Proyectos clonados a escanear (ignorado por git)
```

## ⚡ Inicio rápido
```bash
git clone https://github.com/<tu-usuario>/sonarqube-sast-lab.git
cd sonarqube-sast-lab

cp .env.example .env                 # edita la contraseña
./scripts/setup-sysctl.sh            # agrega --persist para conservarlo tras reiniciar
docker compose up -d
docker ps                            # ambos contenedores deben estar "Up"
```
Abre **http://localhost:9000**, entra con `admin` / `admin` y **cambia la contraseña** cuando te lo pida.

## 🪜 Guía paso a paso

### 1. Preparar el sistema
SonarQube incluye Elasticsearch, que necesita límites del kernel más altos:
```bash
sudo sysctl -w vm.max_map_count=524288
sudo sysctl -w fs.file-max=131072
```
Estos valores se pierden al reiniciar. Usa `./scripts/setup-sysctl.sh --persist` para hacerlos permanentes.

### 2. Levantar SonarQube
```bash
docker compose up -d
docker ps
```
Esperado: `sonarqube` (puerto `9000`) y `sonar-postgres` (puerto `5432`) en estado **Up**.

### 3. Primer ingreso
Entra a `http://localhost:9000` con `admin` / `admin`. Define una contraseña nueva y segura y guárdala en un gestor de contraseñas.

### 4. Clonar el proyecto a analizar
```bash
cd projects
git clone https://github.com/WebGoat/WebGoat.git
cd ..
```

### 5. Crear el proyecto en SonarQube
En la interfaz web elige **Create a local project** y completa:

| Campo | Valor |
|---|---|
| Project display name | `WebGoat` |
| Project key | `WebGoat` |
| Main branch name | `main` |

Luego elige **Locally** y **genera un token**. Cópialo de inmediato; solo se muestra una vez.

### 6. Compilar y escanear
```bash
export SONAR_TOKEN="<tu-token>"
./scripts/scan.sh projects/WebGoat WebGoat
```
Equivale a:
```bash
mvn clean install -DskipTests          # ~4.5 min la primera vez → BUILD SUCCESS
mvn org.sonarsource.scanner.maven:sonar-maven-plugin:sonar \
  -Dsonar.host.url=http://localhost:9000 \
  -Dsonar.token=$SONAR_TOKEN \
  -Dsonar.projectKey=WebGoat
```
> En versiones antiguas de SonarQube usa `-Dsonar.login` en lugar de `-Dsonar.token`.

### 7. Revisar los resultados
Abre el proyecto en el panel → **Issues**, **Security Hotspots**, **Measures**, **Code**.

## 📊 Resultados: escaneo de WebGoat

| Métrica | Valor |
|---|---|
| Tiempo de compilación (`mvn clean install -DskipTests`) | 04:29 min |
| Total de issues | **529** |
| Bugs | 33 |
| Vulnerabilidades | **8** |
| Code Smells | 488 |
| Esfuerzo estimado de corrección | 6 d 4 h |

Ejemplos de hallazgos vistos en el panel:
- `VulnerableTaskHolder.java`: *Complete the task associated to this TODO comment* (Code Smell · Info).
- *Remove this use of "exec"; it is deprecated* (Code Smell · Minor · etiquetas `cert`, `cwe`, `obsolete`).
- `AsciiDoctorTemplateResolver.java`: *Define a constant instead of duplicating the literal "classpath:" 4 times* (Code Smell).

> 📸 Agrega tus capturas del panel en `docs/screenshots/` y referéncialas aquí:
> `![Panel](docs/screenshots/dashboard.png)`

## 📝 Cómo leer y reportar hallazgos
Entender los resultados de SonarQube requiere **conocimientos básicos de programación**. No pegues los 529 issues en un informe. En su lugar:
1. Filtra por **Vulnerability** y revisa primero los **Security Hotspots**.
2. Confirma si cada uno es **verdadero o falso positivo**.
3. Documéntalo con [`docs/finding-template.md`](docs/finding-template.md): descripción, impacto, evidencia y recomendación.
4. Mapea cada hallazgo a un **CWE** y a una categoría del **OWASP Top 10**.

## 🛠️ Solución de problemas

| Problema | Solución |
|---|---|
| El contenedor de SonarQube se detiene o reinicia | Ejecuta `./scripts/setup-sysctl.sh` (los límites del kernel se pierden al reiniciar). Revisa `docker logs sonarqube`. |
| `permission denied` en Docker | `sudo usermod -aG docker $USER` y reinicia la sesión. |
| Puerto 9000 ocupado | Cambia el mapeo en `docker-compose.yml` (p. ej. `"9001:9000"`). |
| `command not found: javac` | Instala un JDK (`sudo apt install default-jdk`). |
| `docker-compose.yml: No such file` | El nombre lleva **guion**, no punto. |
| `Not authorized` al escanear | Token incorrecto o revocado; genera uno nuevo. |
| Primera compilación lenta | Es normal; Maven descarga dependencias (~4–5 min). |

## 🔐 Notas de seguridad
- Nunca subas contraseñas ni tokens al repositorio. Usa `.env` (ignorado por git) y la variable de entorno `SONAR_TOKEN`.
- Si un token se filtra, **revócalo** en SonarQube (*My Account → Security*) y crea uno nuevo.
- Cambia de inmediato las credenciales por defecto `admin/admin`.
- Esta configuración es para laboratorios locales; no expongas el puerto 9000 a internet.

## 📚 Referencias
- [Documentación de SonarQube](https://docs.sonarsource.com/sonarqube/latest/)
- [OWASP WebGoat](https://github.com/WebGoat/WebGoat)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE – Common Weakness Enumeration](https://cwe.mitre.org/)

## 📄 Licencia
Publicado bajo la [Licencia MIT](LICENSE).
