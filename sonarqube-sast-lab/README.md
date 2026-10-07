# 🔍 SonarQube SAST Lab

**English** | [Español](README.es.md)

![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![SonarQube](https://img.shields.io/badge/SonarQube-Community-4E9BCD?logo=sonarqube&logoColor=white)
![Java](https://img.shields.io/badge/Java-Maven-ED8B00?logo=openjdk&logoColor=white)
![Kali](https://img.shields.io/badge/Kali-Linux-557C94?logo=kalilinux&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

A hands-on lab that deploys **SonarQube Community** with **Docker Compose** and uses it to run **SAST (Static Application Security Testing)** against **OWASP WebGoat**, an intentionally vulnerable Java application. Built as a cybersecurity course project and documented as a portfolio piece.

> ⚠️ **Educational use only.** Only scan code you own, code made for practice (like WebGoat), or code you have written authorization to test.

---

## 📑 Table of contents
- [What is SAST?](#-what-is-sast)
- [Architecture](#-architecture)
- [Requirements](#-requirements)
- [Repository structure](#-repository-structure)
- [Quick start](#-quick-start)
- [Step-by-step guide](#-step-by-step-guide)
- [Results: WebGoat scan](#-results-webgoat-scan)
- [How to read and report findings](#-how-to-read-and-report-findings)
- [Troubleshooting](#-troubleshooting)
- [Security notes](#-security-notes)
- [References](#-references)

---

## 🧠 What is SAST?
**SAST** analyzes source code **without executing it** to find bugs, vulnerabilities and poor-quality code early in development. It complements **DAST** (testing the running application) and manual review.

**SonarQube** scans the code and presents findings in a web dashboard, classified by **type** and **severity**:

| Type | Meaning |
|---|---|
| **Bug** | Code error likely to cause incorrect behavior. |
| **Vulnerability** | Security flaw that can be exploited. |
| **Security Hotspot** | Security-sensitive code that needs **manual review**. |
| **Code Smell** | Maintainability issue; not always a security risk. |

## 🏗️ Architecture
```
 ┌──────────────┐   mvn sonar:sonar    ┌────────────────────┐      ┌──────────────────┐
 │  WebGoat     │ ───────────────────► │ SonarQube :9000    │ ───► │ PostgreSQL 16    │
 │  (Maven/Java)│   (token auth)       │ (Docker container) │      │ (Docker container)│
 └──────────────┘                      └────────────────────┘      └──────────────────┘
                                                │
                                         Firefox → http://localhost:9000
```

## ✅ Requirements
- Linux (tested on **Kali Linux**)
- **Docker** and **Docker Compose** v2
- **JDK** (tested with OpenJDK 25.0.4) and **Maven**
- **Git**
- ~4 GB of free RAM for SonarQube

Verify:
```bash
java -version && javac -version && mvn -version && docker --version
```

## 📁 Repository structure
```
sonarqube-sast-lab/
├── README.md                  # English documentation
├── README.es.md               # Spanish documentation
├── LICENSE
├── .gitignore
├── .env.example               # Template for credentials (copy to .env)
├── docker-compose.yml         # SonarQube + PostgreSQL
├── scripts/
│   ├── setup-sysctl.sh        # Kernel parameters required by SonarQube
│   └── scan.sh                # Build + scan a Maven project
├── docs/
│   ├── finding-template.md    # Bilingual finding report template
│   └── screenshots/           # Evidence images
└── projects/                  # Cloned target projects (git-ignored)
```

## ⚡ Quick start
```bash
git clone https://github.com/<your-user>/sonarqube-sast-lab.git
cd sonarqube-sast-lab

cp .env.example .env                 # edit the password
./scripts/setup-sysctl.sh            # add --persist to keep it after reboot
docker compose up -d
docker ps                            # both containers should be "Up"
```
Open **http://localhost:9000**, log in with `admin` / `admin` and **change the password** when prompted.

## 🪜 Step-by-step guide

### 1. Prepare the system
SonarQube embeds Elasticsearch, which needs higher kernel limits:
```bash
sudo sysctl -w vm.max_map_count=524288
sudo sysctl -w fs.file-max=131072
```
These values are lost on reboot. Use `./scripts/setup-sysctl.sh --persist` to make them permanent.

### 2. Start SonarQube
```bash
docker compose up -d
docker ps
```
Expected: `sonarqube` (port `9000`) and `sonar-postgres` (port `5432`) in **Up** state.

### 3. First login
Go to `http://localhost:9000` and sign in with `admin` / `admin`. Set a new strong password and store it in a password manager.

### 4. Clone the target project
```bash
cd projects
git clone https://github.com/WebGoat/WebGoat.git
cd ..
```

### 5. Create the project in SonarQube
In the web UI choose **Create a local project** and fill in:

| Field | Value |
|---|---|
| Project display name | `WebGoat` |
| Project key | `WebGoat` |
| Main branch name | `main` |

Then choose **Locally** and **generate a token**. Copy it right away; it is shown only once.

### 6. Build and scan
```bash
export SONAR_TOKEN="<your-token>"
./scripts/scan.sh projects/WebGoat WebGoat
```
This is equivalent to:
```bash
mvn clean install -DskipTests          # ~4.5 min the first time → BUILD SUCCESS
mvn org.sonarsource.scanner.maven:sonar-maven-plugin:sonar \
  -Dsonar.host.url=http://localhost:9000 \
  -Dsonar.token=$SONAR_TOKEN \
  -Dsonar.projectKey=WebGoat
```
> On older SonarQube versions use `-Dsonar.login` instead of `-Dsonar.token`.

### 7. Review the results
Open the project in the dashboard → **Issues**, **Security Hotspots**, **Measures**, **Code**.

## 📊 Results: WebGoat scan

| Metric | Value |
|---|---|
| Build time (`mvn clean install -DskipTests`) | 04:29 min |
| Total issues | **529** |
| Bugs | 33 |
| Vulnerabilities | **8** |
| Code Smells | 488 |
| Estimated remediation effort | 6 d 4 h |

Sample findings seen in the dashboard:
- `VulnerableTaskHolder.java` — *Complete the task associated to this TODO comment* (Code Smell · Info).
- *Remove this use of "exec"; it is deprecated* (Code Smell · Minor · tags `cert`, `cwe`, `obsolete`).
- `AsciiDoctorTemplateResolver.java` — *Define a constant instead of duplicating the literal "classpath:" 4 times* (Code Smell).

> 📸 Add your dashboard screenshots to `docs/screenshots/` and reference them here:
> `![Dashboard](docs/screenshots/dashboard.png)`

## 📝 How to read and report findings
Understanding SonarQube output requires **basic programming knowledge**. Don't paste all 529 issues into a report. Instead:
1. Filter by **Vulnerability** and review **Security Hotspots** first.
2. Confirm whether each one is a **true or false positive**.
3. Document it with [`docs/finding-template.md`](docs/finding-template.md): description, impact, evidence, recommendation.
4. Map each finding to a **CWE** and an **OWASP Top 10** category.

## 🛠️ Troubleshooting

| Problem | Solution |
|---|---|
| SonarQube container exits / restarts | Run `./scripts/setup-sysctl.sh` (kernel limits lost after reboot). Check `docker logs sonarqube`. |
| `permission denied` on Docker | `sudo usermod -aG docker $USER` then log out and in. |
| Port 9000 already in use | Change the mapping in `docker-compose.yml` (e.g. `"9001:9000"`). |
| `command not found: javac` | Install a JDK (`sudo apt install default-jdk`). |
| `docker-compose.yml: No such file` | The name uses a **hyphen**, not a dot. |
| `Not authorized` during scan | Wrong or revoked token; generate a new one. |
| Slow first build | Normal; Maven downloads dependencies (~4–5 min). |

## 🔐 Security notes
- Never commit passwords or tokens. Use `.env` (git-ignored) and the `SONAR_TOKEN` environment variable.
- If a token leaks, **revoke it** in SonarQube (*My Account → Security*) and create a new one.
- Change the default `admin/admin` credentials immediately.
- This setup is for local labs; do not expose port 9000 to the internet.

## 📚 References
- [SonarQube documentation](https://docs.sonarsource.com/sonarqube/latest/)
- [OWASP WebGoat](https://github.com/WebGoat/WebGoat)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE – Common Weakness Enumeration](https://cwe.mitre.org/)

## 📄 License
Released under the [MIT License](LICENSE).
