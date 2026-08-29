# Vulnerability Scan Report — Windows 7 VM (Nessus Essentials)

**Author:** Juan Pablo Acevedo Araya
**Context:** Cybersecurity coursework — vulnerability scanning practice with Nessus Essentials
**Scanner:** Tenable Nessus Essentials
**Scan Name:** `Politica_Windows`
**Scan Policy:** Advanced Scan (uncredentialed)
**Target:** `192.168.140.132` (local VM, isolated lab network)
**Duration:** 6 minutes (10:51 AM – 10:57 AM)

> ⚠️ **Scope note:** This scan was performed against a personal virtual machine on an isolated home-lab network, strictly for educational purposes as part of a cybersecurity course. No external or third-party systems were scanned.

---

## 1. Objective

Perform a first non-credentialed vulnerability scan against a Windows 7 virtual machine using Nessus Essentials, document the findings, and practice reading/interpreting Nessus vulnerability reports (CVSS, CVE, VPR, EPSS, remediation).

## 2. Scan Summary

| Item | Value |
|---|---|
| Host | 192.168.140.132 |
| Operating System | Microsoft Windows 7 Professional (unsupported) |
| Authentication | Failed (non-credentialed scan) |
| Total Vulnerabilities Found | 28 |
| Critical | 2 |
| High | 3 |
| Medium | 9 |
| Low | 2 |
| Info | 12 |

**Note on authentication:** the scan ran without valid credentials on the target ("Auth: Fail"), meaning Nessus only assessed what's visible from the network side (open ports, exposed services, protocol weaknesses) — not the internal state of the OS (installed patches, local misconfigurations, etc.). A credentialed scan would likely surface additional findings.

## 3. Detailed Findings

### 🔴 Critical

#### 3.1 — Unsupported Windows OS (remote)
- **Plugin ID:** 108797
- **CVSS v3.0 Base Score:** 10.0
- **Description:** The installed OS (Microsoft Windows 7 Professional) is no longer supported by Microsoft, meaning it no longer receives security patches. As a result, it is very likely to contain unaddressed vulnerabilities.
- **Solution:** Upgrade to a supported OS version or service pack.

#### 3.2 — Microsoft RDP RCE (CVE-2019-0708) "BlueKeep" (uncredentialed check)
- **Plugin ID:** 125313
- **CVE:** CVE-2019-0708
- **VPR (Vulnerability Priority Rating):** 9.5
- **EPSS (Exploit Prediction Scoring System):** 1.0 (maximum — very high real-world exploitation likelihood)
- **Description:** A remote code execution vulnerability in Remote Desktop Protocol (RDP). An unauthenticated attacker can send specially crafted requests to execute arbitrary code on the target, without any user interaction.
- **Solution:** Apply Microsoft's official patches (released for Windows XP, 2003, 2008, 7, and 2008 R2).
- **Why it matters:** BlueKeep is one of the most well-known "wormable" vulnerabilities of the last decade — it can potentially spread automatically between vulnerable systems, similar to WannaCry.

### 🟠 High

#### 3.3 — MS12-020: Vulnerabilities in Remote Desktop Could Allow Remote Code Execution
- **Plugin ID:** 58435
- **Description:** An arbitrary remote code execution vulnerability exists in the RDP implementation, due to improper handling of an object in memory. An unauthenticated remote attacker could exploit this by sending specially crafted RDP packets, potentially also causing a denial of service.
- **Solution:** Apply Microsoft's official patches (Windows XP, 2003, Vista, 2008, 7, and 2008 R2).

#### 3.4 — MS17-010: Security Update for Microsoft Windows SMB Server (4013389) — "EternalBlue"
- **Plugin ID:** 97833
- **CVEs:** CVE-2017-0143, CVE-2017-0144, CVE-2017-0145, CVE-2017-0146, CVE-2017-0147, CVE-2017-0148
- **Description:** Multiple remote code execution vulnerabilities in SMBv1 due to improper handling of certain requests. An unauthenticated attacker can exploit these via a specially crafted packet to execute arbitrary code, or disclose sensitive information.
- **Why it matters:** This is the vulnerability set behind **EternalBlue**, the exploit leaked by the Shadow Brokers group and used to spread the **WannaCry** ransomware and the **NotPetya** wiper in 2017 — among the most damaging cyberattacks in history.
- **Solution:** Apply Microsoft's official patches (Vista, 2008, 7, 2008 R2, 2012, 8.1, RT 8.1, 2012 R2, 10, and 2016, including emergency patches for unsupported OS like XP and 2003).

### 🟡 Medium

#### 3.5 — Remote Desktop Protocol Server Man-in-the-Middle Weakness
- **Plugin ID:** 18405
- **CVE:** CVE-2005-1794
- **CVSS v3.0 Base Score:** 6.5
- **Description:** The RDP server does not validate its identity to the client during encryption setup, since it stores a publicly known hard-coded RSA private key. An attacker positioned on the network can intercept the connection and perform a man-in-the-middle attack, potentially capturing authentication credentials.
- **Solution:** Force the use of SSL/TLS as transport for RDP, and/or enable "Allow connections only from computers running Remote Desktop with Network Level Authentication."

#### 3.6 — TLS Version 1.0 Protocol Detection
- **Plugin ID:** 104743
- **CVSS v3.0 Base Score:** 6.5
- **Description:** The remote service accepts connections using TLS 1.0, an outdated protocol with known cryptographic design flaws. PCI DSS v3.2 has required disabling TLS 1.0 entirely since June 30, 2018.
- **Solution:** Enable TLS 1.2 and 1.3, and disable TLS 1.0.

#### 3.7 — SSL Certificate Signed Using Weak Hashing Algorithm
- **Plugin ID:** 35291
- **CVEs:** CVE-2004-2761, CVE-2005-4900
- **CVSS v3.0 Base Score:** 5.3
- **Description:** The SSL certificate chain was signed using a cryptographically weak hashing algorithm (SHA-1), which is vulnerable to collision attacks. An attacker could theoretically forge another certificate with the same digital signature.
- **Solution:** Contact the certificate authority to have the certificate reissued with a stronger algorithm (e.g. SHA-256).

---

## 4. Risk Analysis Summary

| # | Finding | Severity | CVSS v3 | Root Cause |
|---|---|---|---|---|
| 1 | Unsupported Windows OS | Critical | 10.0 | End-of-life operating system |
| 2 | BlueKeep (CVE-2019-0708) | Critical | — (VPR 9.5) | Unpatched RDP service |
| 3 | MS12-020 RDP RCE | High | — | Unpatched RDP service |
| 4 | MS17-010 / EternalBlue | High | — | Unpatched SMBv1 service |
| 5 | RDP MITM Weakness | Medium | 6.5 | Weak RDP encryption defaults |
| 6 | TLS 1.0 Enabled | Medium | 6.5 | Outdated TLS configuration |
| 7 | Weak SSL Cert Signature | Medium | 5.3 | Weak certificate signing algorithm |

**Common thread:** Nearly all findings trace back to two root causes — (1) an unsupported, unpatched operating system, and (2) legacy/insecure protocol defaults (RDP without NLA, SMBv1, TLS 1.0). This is expected and intentional for a Windows 7 lab VM used for vulnerability-scanning practice, but illustrates clearly why unsupported systems accumulate critical risk over time.

## 5. Recommended Remediation Priorities

1. **Immediate:** Patch or disable RDP if not strictly needed (addresses BlueKeep and MS12-020 — both Critical/High RCE vulnerabilities).
2. **Immediate:** Patch SMBv1 vulnerabilities (MS17-010) or disable SMBv1 entirely if not required for legacy compatibility.
3. **Short-term:** Enable Network Level Authentication (NLA) for RDP to mitigate the MITM weakness.
4. **Short-term:** Disable TLS 1.0 and enforce TLS 1.2/1.3.
5. **Long-term:** Since the OS itself is unsupported, the most effective fix is upgrading to a currently supported Windows version — patching individual vulnerabilities on an EOL system is a temporary mitigation, not a permanent solution.

## 6. Lessons Learned

1. **Non-credentialed scans are limited.** With `Auth: Fail`, Nessus can only see what's exposed over the network — a credentialed scan (with valid Windows admin credentials) would likely reveal additional local vulnerabilities, missing patches, and misconfigurations.
2. **Nessus Essentials doesn't support PDF/HTML export** — that feature requires a paid license (Nessus Professional/Expert). Findings still had to be reviewed manually within the web interface (per-vulnerability detail panels), which is slower but works fine for documentation purposes at a small scale.
3. **VPR and EPSS matter as much as CVSS.** BlueKeep's CVSS score wasn't the highest listed metric shown, but its **EPSS of 1.0** (near-certain real-world exploitation) and **VPR of 9.5** make it the single most urgent finding in this scan — a good reminder that raw CVSS alone doesn't always tell the full risk story.
4. **A handful of root causes explain most findings.** Instead of treating 28 vulnerabilities as 28 separate problems, grouping them by root cause (EOL OS, RDP misconfiguration, SMBv1, outdated TLS) makes remediation planning far more manageable.
5. **Historical CVEs remain highly relevant in training labs.** Even though MS17-010 (EternalBlue) and CVE-2019-0708 (BlueKeep) are several years old, they remain textbook examples for understanding remote code execution and worm-capable vulnerabilities — which is exactly why they still show up prominently on an unpatched Windows 7 lab machine.

---

## 📎 Quick Reference — Vulnerability Severity Scale (Nessus / CVSS v3)

| Severity | CVSS v3 Range |
|---|---|
| Critical | 9.0 – 10.0 |
| High | 7.0 – 8.9 |
| Medium | 4.0 – 6.9 |
| Low | 0.1 – 3.9 |
| Info | 0.0 (informational only) |
