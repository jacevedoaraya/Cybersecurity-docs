# 🔍 How to inspect an Android app from the inside (without running it)

**Cybersecurity practice · October 2026**
🇪🇸 [Leer en español](PRACTICA_ES.md) · 🏠 [Back to home](../README.md)

> This document is written for **someone with little programming knowledge**. If a word sounds unfamiliar, check the [glossary](#-glossary-words-youll-come-across).

---

## 1. What is this practice about?

When you install an app on your Android phone, what gets installed is a file called an **APK**. Think of it as a **closed box** holding everything the app needs: its code, images, list of permissions, and the signature of whoever made it.

In this practice we **open that box without turning the app on** and look inside, like reading a book before buying it. This is called **static analysis**.

We look for three things:

- Are there **secrets** stored inside the app (keys, passwords)?
- Does the app have **defenses** (for example, detecting a "tampered" phone)?
- Are there **bad practices** an attacker could take advantage of?

We did it in **two ways** and compared the results:

| Method | What it is like |
|---|---|
| 🧑‍🔧 **By hand** | We read the code with tools, line by line |
| 🤖 **Automatic** | A program called **MobSF** scans the app and produces a report |

## 2. ⚠️ Important notice

The app we used is called **UnCrackable-Level1**. The **OWASP** organization created it *specifically for practice*, so it is legal and safe to examine.

**Never analyze an app that isn't yours or that you don't have written permission to test.**

## 3. The result in one sentence

> An app can use encryption, but if **the key is stored inside the app itself**, anyone can open it. With a few tools and ten lines of Python we recovered a "secret" **without running the app**.

---

## 4. What do you need?

| Item | What it is for |
|---|---|
| Kali Linux (virtual machine) | The system where we did everything |
| Java | Most of the tools need it |
| apktool, jadx, dex2jar, JD-GUI | Tools to "open" the APK |
| Docker | To run MobSF |
| Python 3 | For the final challenge |

Versions used: Java 25, apktool 2.10.0, jadx 1.5.0 (script) and 1.5.6 (Kali), dex2jar 2.4 (script) and 2.1 (Kali), JD-GUI 1.6.6, MobSF 4.5.4, Python 3.14.

---

## 5. Step by step

### Step 1 · Prepare the working folder
```bash
mkdir -p ~/TOOLS/MOVIL
cd ~/TOOLS/MOVIL
unzip ~/Downloads/android-apk-lab.zip
cd android-apk-lab
```
**What does it do?** Creates a folder and unpacks the project into it.

### Step 2 · Install the missing tools
```bash
sudo apt update
sudo apt install -y dex2jar jd-gui
```
**What does it do?** Installs two programs that were not included in Kali.

### Step 3 · Run the automatic lab
```bash
bash ./scripts/run_lab.sh 2>&1 | tee evidence/mi_salida.txt
```
**What does it do?** A script downloads the app and the tools, and does most of the mechanical work. It saves the output to a file as evidence.

The first thing it checks is that **the app is the original one**:

- **Hash (fingerprint):** `1da8bf57d266109f9a07c01bf7111a1975ce01f190b9d914bcd3ae3dbef96f21`. If anyone changed even a single letter of the app, this fingerprint would be different.
- **Signature:** created by *Jeroen Willemsen, OWASP*, valid until 2043.

### Step 4 · Open the box (unzip)
The APK is really a ZIP. After unzipping it we saw:

- `AndroidManifest.xml`: the list of permissions and entry points of the app.
- `classes.dex`: **all the code** of the app, but in a format a person cannot read.
- `res/` and `resources.arsc`: images and texts.
- `META-INF/`: the signature.

A curious detail: the `AndroidManifest.xml` came out **unreadable**, because Android stores it in a binary format. To confirm it was that (and not a damaged file) we looked at its first bytes:

```bash
head -c 16 work/unzip_out/AndroidManifest.xml | od -An -tx1
```
It started with `03 00 08 00`, which is the signature of an Android binary manifest.

> 💡 The `file` command said it was a "Targa image". **It was wrong.** Lesson: don't trust a single tool.

### Step 5 · Make the manifest readable (apktool)
```bash
java -jar apktool.jar d UnCrackable-Level1.apk -o apktool_out
```
Now we could read it. What we found:

- `allowBackup="true"`: allows a copy of the app's data to be taken.
- **It requests no permissions** (no camera, contacts, internet, etc.).

### Step 6 · Turn the code into something we can read
The code comes in a format meant for machines. There are **two ways** to convert it to Java (a language people can read):

| Path | Steps | Result |
|---|---|---|
| 🕰️ **Classic** | `dex2jar` → open with **JD-GUI** | 7 classes |
| 🆕 **Modern** | **jadx** (does everything in one step) | 6 files |

**Comparison (our experience):** the same code looked **different** in each tool, and **jadx was easier to read**. In JD-GUI, variable names come out more generic.

### Step 7 · Read the code: what does the app do?
In jadx we opened the classes one by one. This is what we understood:

**① When the app opens (`onCreate`)** it makes **two checks** before showing the screen:

| Check | What it tests | If true |
|---|---|---|
| 1st | Is the phone **rooted**? (class `c`) | Shows "Root detected!" and **closes** |
| 2nd | Is the app in **debug mode**? (class `b`) | Shows "App is debuggable!" and **closes** |

> 🔑 **Root** means the phone was modified to grant full administrator permissions. Attackers use it, which is why many apps detect it.

**② How it detects root** (class `c`), with **three tricks**:

1. It looks for a program called `su` in the system folders.
2. It checks whether the system has the `test-keys` tag (typical of modified systems).
3. It checks whether **7 files** typical of root tools exist.

**③ When you press "Verify"** the app compares what you typed with a stored secret. And here is the problem, which we see in the next step.

### Step 8 · The main finding: the key is inside the app

The app stores **two things** directly in its code:

1. A **key** (a string of letters and numbers in hexadecimal).
2. An **encrypted text** (another string, in a format called Base64).

When you press "Verify", the app **decrypts** the text with that key and compares the result with what you typed.

> 🏠 **Analogy:** it is like installing a safe next to your front door and **taping the key to the side of the safe**. The safe is good, but it protects nothing.

**We proved it with our own Python script** (the *challenge*). It did the same as the app, in four steps:

```python
import base64
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import unpad

HEX_KEY    = "<hexadecimal string copied from jadx>"
B64_CIPHER = "<Base64 string copied from jadx>"

key    = bytes.fromhex(HEX_KEY)               # 1. turn the key into bytes
cipher = base64.b64decode(B64_CIPHER)         # 2. turn the encrypted text into bytes
engine = AES.new(key, AES.MODE_ECB)           # 3. prepare the decryption
print(unpad(engine.decrypt(cipher), 16).decode())   # 4. decrypt and show
```

The script **recovered the secret** without running the app, without root, and without guessing anything. *(The secret is left out of this document so as not to spoil the exercise for anyone who wants to try it.)*

**A technical detail we learned:** when we checked the size of what we copied, the first time it gave **12 bytes** instead of 32. The encrypted text must be a multiple of 16 bytes long, and that warned us we had copied it **incomplete** (jadx was cutting the line on the right).

### Step 9 · The automatic review with MobSF
```bash
sudo docker pull opensecurity/mobile-security-framework-mobsf:latest
sudo docker run -it --rm -p 127.0.0.1:8000:8000 opensecurity/mobile-security-framework-mobsf:latest
```
Then, in the browser: `http://127.0.0.1:8000`, we uploaded the APK and waited for the report.

> 🔒 `127.0.0.1` makes MobSF visible **only from your own computer**. MobSF prints a "REST API Key" in the terminal: **do not publish it**.

**MobSF result:**

| Item | Value |
|---|---|
| Security score | **55 / 100** |
| Trackers | 0 of 432 |
| Manifest alerts | 1 high, 1 warning |
| Code alerts | 4 |

The full report is in [`evidence/mobsf_report.pdf`](../evidence/mobsf_report.pdf).

---

## 6. 📋 Findings (what problems we found)

**How to read the "Severity" column:** *High* = fix soon · *Medium* = worth fixing · *Low / Info* = a detail to improve.

| # | Finding | Explained simply | Severity | Who found it? |
|---|---|---|---|---|
| **H1** | Key and secret written in the code | The key is taped to the safe | **High** | 🧑‍🔧 By hand only |
| **H2** | ECB encryption mode | An old mode: equal parts of a message look equal once encrypted | **Medium** (MobSF: High) | 🧑‍🔧 and 🤖 |
| **H3** | `allowBackup = true` | The app's data can be copied through a USB cable | **Medium** | 🧑‍🔧 and 🤖 |
| **H4** | Root detection is easy to bypass | It looks for known names and paths; anyone who knows them can avoid them | **Info** | 🧑‍🔧 and 🤖 |
| **H5** | Basic debug detection | It only checks one flag; it does not detect tools like Frida | **Info** | 🧑‍🔧 By hand only |
| **H6** | Weak obfuscation | It only renames things to `a`, `b`, `c`; the code is still readable | **Low** | 🧑‍🔧 By hand only |
| **H7** | Main screen exposed by default | With this Android version, the start screen is reachable by other apps | **Info** | 🧑‍🔧 *(MobSF did not flag it)* |
| **H8** | Works on Android 4.4 (`minSdk 19`) | It can be installed on old phones that no longer get patches | **High** per MobSF | 🤖 MobSF only |
| **H9** | The app writes an error message to the log | A small detail: better not to log internal information | **Info** | 🤖 |

> 📝 **About H7:** our reading of the manifest says it is exposed by default, but MobSF reports 0 exposed activities. **We do not know the cause**; it remains an open question. One possible explanation is that MobSF does not count the launcher screen, but **we did not verify it**.
>
> 📝 **About H4:** MobSF showed two opposite alerts about `c.java` ("may request root" and "has root detection"). From the code we know the app **detects** root, it does not request it, so the first alert looks like a **false positive**.

## 7. 🤖 vs 🧑‍🔧 : comparison

| | MobSF (automatic) | By hand |
|---|---|---|
| ⏱️ Speed | Very fast | Slower |
| 🔎 Depth | Shallow | Very deep |
| ✅ Found | `minSdk 19`, the log alert | The key written in the code, debug detection, obfuscation |
| ❌ Missed | **The key written in the code** (the most serious finding) | It did not flag `minSdk 19` as a problem |
| 🎓 You learn | What to check | Why and how it happens |

## 8. 💬 Conclusions

*Written by the author of the practice:*

1. **Findings made by hand are deeper** than those from an automatic app.
2. **MobSF is fast, but it skips some things.** In our case, it did not flag the most serious finding.
3. **You should use two methods** to review an app: an automatic one to cover ground quickly, and a manual one to truly understand what is going on.

## 9. 🛠️ How the app would be fixed

| Problem | Solution |
|---|---|
| Key in the code (H1) | **Don't store secrets in the app.** Check them on a server, or use Android's secure store (*Keystore*) |
| ECB mode (H2) | Use a modern mode, such as AES-GCM |
| `allowBackup` (H3) | Set it to `false` |
| Old Android (H8) | Raise the minimum supported version |
| Weak defenses (H4, H5, H6) | Complement them with server-side checks |

## 10. 🧯 Problems we had (and how they were solved)

| Problem | Why it happened | Solution |
|---|---|---|
| `cd /TOOLS` doesn't work | The leading `/` looks in the system root | Use `~/TOOLS` |
| `LS: command not found` | Linux is case-sensitive | Type `ls` |
| `file` said "Targa image" | That tool does not recognize the format | Check the bytes with `od` |
| jadx-gui: "File not found" | I used a relative path | Use the full path with `$PWD` |
| Python: `No module named 'Crypto'` | In Kali's package the module is called **`Cryptodome`** | Change the `import` |
| The encrypted text was 12 bytes | I copied the string incomplete | Copy it in full and check the size |
| MobSF's PDF wasn't where I expected | Firefox saved it elsewhere | Find it with `find` |

## 11. 📚 Glossary: words you'll come across

| Word | Simple meaning |
|---|---|
| **APK** | The file used to install an Android app (a compressed "box") |
| **Manifest** | The list of permissions and entry points of the app |
| **Decompile** | Turn the app's code into something a person can read |
| **Hash** | A "fingerprint" of the file; change one letter and the fingerprint changes |
| **Encrypt / decrypt** | Turn a message into something unreadable / make it readable again with a key |
| **AES** | A very common encryption method |
| **Key** | The "secret code" used to encrypt or decrypt |
| **Hexadecimal** | A way of writing numbers using 0-9 and a-f |
| **Base64** | A way of writing data using letters and numbers |
| **Root** | Full administrator permissions on an Android phone |
| **Obfuscation** | Making code hard to read (for example, by renaming things) |
| **Static analysis** | Reviewing an app without running it |
| **MobSF** | A program that reviews mobile apps automatically |
| **False positive** | An alert that looks like a problem but isn't |

## 12. 📁 Repository structure

```
android-apk-lab/
├── README.md                  ← home page (Spanish and English)
├── .gitignore
├── docs/
│   ├── PRACTICA_ES.md         ← Spanish version
│   └── PRACTICE_EN.md         ← this document
├── scripts/
│   └── run_lab.sh             ← automates the first steps
├── reto/
│   └── solve.py               ← the challenge's Python script
└── evidence/
    ├── salida_run_lab.txt     ← reference output
    ├── mi_salida.txt          ← output from my run
    ├── hallazgos_automaticos.txt
    └── mobsf_report.pdf       ← MobSF report
```

## 13. 🙏 Credits

- Practice app: [OWASP MASTG Crackmes](https://github.com/OWASP/mastg)
- Tools: [Apktool](https://github.com/iBotPeaches/Apktool) · [jadx](https://github.com/skylot/jadx) · [dex2jar](https://github.com/pxb1988/dex2jar) · [JD-GUI](https://github.com/java-decompiler/jd-gui) · [MobSF](https://github.com/MobSF/Mobile-Security-Framework-MobSF)

