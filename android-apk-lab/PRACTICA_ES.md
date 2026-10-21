# 🔍 Cómo revisar una app de Android por dentro (sin ejecutarla)

**Práctica de ciberseguridad · Octubre de 2026**
🇬🇧 [Read this in English](PRACTICE_EN.md) · 🏠 [Volver al inicio](../README.md)

> Este documento está escrito para que lo entienda **alguien que sabe poco de programación**. Si una palabra te suena rara, mira el [glosario](#-glosario-palabras-que-vas-a-encontrar).

---

## 1. ¿De qué trata esta práctica?

Cuando instalas una app en tu celular Android, lo que se instala es un archivo llamado **APK**. Ese archivo es como una **caja cerrada** con todo lo que la app necesita: su código, sus imágenes, la lista de permisos y la firma de quien la hizo.

En esta práctica **abrimos esa caja sin encender la app** y la revisamos por dentro, como quien lee un libro antes de comprarlo. A eso se le llama **análisis estático**.

Buscamos tres cosas:

- ¿Hay **secretos** guardados dentro de la app (claves, contraseñas)?
- ¿La app tiene **defensas** (por ejemplo, detectar si el teléfono está "trucado")?
- ¿Hay **malas prácticas** que un atacante podría aprovechar?

Lo hicimos de **dos maneras** y comparamos los resultados:

| Método | Cómo es |
|---|---|
| 🧑‍🔧 **A mano** | Nosotros leemos el código con herramientas, línea por línea |
| 🤖 **Automático** | Un programa llamado **MobSF** revisa la app y entrega un reporte |

## 2. ⚠️ Aviso importante

La app que usamos se llama **UnCrackable-Level1**. La creó la organización **OWASP** *precisamente para practicar*, así que es legal y seguro revisarla.

**Nunca analices una app que no sea tuya o para la que no tengas permiso por escrito.**

## 3. Resultado en una frase

> Una app puede tener cifrado, pero si **la clave está guardada dentro de la misma app**, cualquiera puede abrirla. Con unas pocas herramientas y diez líneas de Python recuperamos un "secreto" **sin ejecutar la app**.

---

## 4. ¿Qué necesitas?

| Cosa | Para qué sirve |
|---|---|
| Kali Linux (en máquina virtual) | El sistema donde hicimos todo |
| Java | Lo necesitan casi todas las herramientas |
| apktool, jadx, dex2jar, JD-GUI | Herramientas para "abrir" el APK |
| Docker | Para ejecutar MobSF |
| Python 3 | Para el reto final |

Versiones usadas: Java 25, apktool 2.10.0, jadx 1.5.0 (script) y 1.5.6 (Kali), dex2jar 2.4 (script) y 2.1 (Kali), JD-GUI 1.6.6, MobSF 4.5.4, Python 3.14.

---

## 5. Paso a paso

### Paso 1 · Preparar la carpeta de trabajo
```bash
mkdir -p ~/TOOLS/MOVIL
cd ~/TOOLS/MOVIL
unzip ~/Downloads/android-apk-lab.zip
cd android-apk-lab
```
**¿Qué hace?** Crea una carpeta y descomprime en ella el proyecto.

### Paso 2 · Instalar las herramientas que faltan
```bash
sudo apt update
sudo apt install -y dex2jar jd-gui
```
**¿Qué hace?** Instala dos programas que no venían en Kali.

### Paso 3 · Ejecutar el laboratorio automático
```bash
bash ./scripts/run_lab.sh 2>&1 | tee evidence/mi_salida.txt
```
**¿Qué hace?** Un script descarga la app y las herramientas, y hace casi todo el trabajo mecánico. Guarda la salida en un archivo como evidencia.

Lo primero que comprueba es que **la app sea la original**:

- **Hash (huella digital):** `1da8bf57d266109f9a07c01bf7111a1975ce01f190b9d914bcd3ae3dbef96f21`. Si alguien cambiara aunque sea una letra de la app, esta huella sería distinta.
- **Firma:** creada por *Jeroen Willemsen, OWASP*, válida hasta 2043.

### Paso 4 · Abrir la caja (descomprimir)
El APK es en realidad un ZIP. Al descomprimirlo vimos:

- `AndroidManifest.xml`: la lista de permisos y puertas de entrada de la app.
- `classes.dex`: **todo el código** de la app, pero en un formato que una persona no puede leer.
- `res/` y `resources.arsc`: imágenes y textos.
- `META-INF/`: la firma.

Detalle curioso: el `AndroidManifest.xml` salió **ilegible**, porque Android lo guarda en formato binario. Para confirmar que era eso (y no un archivo dañado) miramos sus primeros bytes:

```bash
head -c 16 work/unzip_out/AndroidManifest.xml | od -An -tx1
```
Empezaba con `03 00 08 00`, que es la señal de un manifiesto binario de Android.

> 💡 El comando `file` dijo que era una "imagen Targa". **Se equivocó.** Moraleja: no te fíes de una sola herramienta.

### Paso 5 · Hacer legible el manifiesto (apktool)
```bash
java -jar apktool.jar d UnCrackable-Level1.apk -o apktool_out
```
Ahora sí pudimos leerlo. Lo que encontramos:

- `allowBackup="true"`: permite sacar una copia de los datos de la app.
- **No pide ningún permiso** (no accede a cámara, contactos, internet, etc.).

### Paso 6 · Convertir el código a algo que podamos leer
El código viene en un formato para máquinas. Hay **dos formas** de convertirlo a Java (un lenguaje que sí se puede leer):

| Camino | Pasos | Resultado |
|---|---|---|
| 🕰️ **Clásico** | `dex2jar` → abrir con **JD-GUI** | 7 clases |
| 🆕 **Moderno** | **jadx** (hace todo en un paso) | 6 archivos |

**Comparación (nuestra experiencia):** el mismo código se veía **distinto** en cada herramienta, y **jadx fue más fácil de leer**. En JD-GUI los nombres de las variables salen más genéricos.

### Paso 7 · Leer el código: ¿qué hace la app?
En jadx fuimos abriendo las clases. Esto entendimos:

**① Al abrir la app (`onCreate`)** hace **dos revisiones** antes de mostrar la pantalla:

| Revisión | Qué comprueba | Si es verdadera |
|---|---|---|
| 1.ª | ¿El teléfono tiene **root**? (clase `c`) | Muestra "Root detected!" y **se cierra** |
| 2.ª | ¿La app está en **modo depuración**? (clase `b`) | Muestra "App is debuggable!" y **se cierra** |

> 🔑 **Root** significa que el teléfono fue modificado para dar permisos de administrador total. Los atacantes lo usan; por eso muchas apps lo detectan.

**② Cómo detecta root** (clase `c`), con **tres trucos**:

1. Busca un programa llamado `su` en las carpetas del sistema.
2. Mira si el sistema tiene la etiqueta `test-keys` (típica de sistemas modificados).
3. Revisa si existen **7 archivos** típicos de herramientas de root.

**③ Cuando pulsas "Verify"** la app compara lo que escribiste con un secreto guardado. Y aquí está el problema, que vemos en el siguiente paso.

### Paso 8 · El hallazgo principal: la clave está dentro de la app

La app guarda **dos cosas** directamente en su código:

1. Una **clave** (una cadena de letras y números en hexadecimal).
2. Un **texto cifrado** (otra cadena, en un formato llamado Base64).

Cuando pulsas "Verify", la app **descifra** el texto con esa clave y compara el resultado con lo que escribiste.

> 🏠 **Analogía:** es como poner una caja fuerte en la puerta de tu casa y **pegar la llave con cinta a un lado de la caja**. La caja es buena, pero no protege nada.

**Lo demostramos con un script propio en Python** (el *reto*). Hizo lo mismo que la app, en cuatro pasos:

```python
import base64
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import unpad

CLAVE_HEX   = "<cadena hexadecimal copiada de jadx>"
CIFRADO_B64 = "<cadena Base64 copiada de jadx>"

clave   = bytes.fromhex(CLAVE_HEX)            # 1. convertir la clave a bytes
cifrado = base64.b64decode(CIFRADO_B64)       # 2. convertir el texto cifrado a bytes
maquina = AES.new(clave, AES.MODE_ECB)        # 3. preparar el descifrado
print(unpad(maquina.decrypt(cifrado), 16).decode())   # 4. descifrar y mostrar
```

El script **recuperó el secreto** sin ejecutar la app, sin root y sin adivinar nada. *(El secreto se deja fuera de este documento para no arruinar el ejercicio a quien lo quiera hacer.)*

**Un detalle técnico que aprendimos:** al verificar el tamaño de lo que copiamos, la primera vez dio **12 bytes** en lugar de 32. El texto cifrado debe medir un múltiplo de 16 bytes, y eso nos avisó de que lo habíamos copiado **incompleto** (jadx cortaba la línea por la derecha).

### Paso 9 · La revisión automática con MobSF
```bash
sudo docker pull opensecurity/mobile-security-framework-mobsf:latest
sudo docker run -it --rm -p 127.0.0.1:8000:8000 opensecurity/mobile-security-framework-mobsf:latest
```
Luego, en el navegador: `http://127.0.0.1:8000`, subimos el APK y esperamos el reporte.

> 🔒 `127.0.0.1` hace que MobSF solo sea visible **desde tu propio equipo**. MobSF imprime una "REST API Key" en la terminal: **no la publiques**.

**Resultado de MobSF:**

| Dato | Valor |
|---|---|
| Puntaje de seguridad | **55 / 100** |
| Rastreadores | 0 de 432 |
| Avisos del manifiesto | 1 alto, 1 advertencia |
| Avisos del código | 4 |

El reporte completo está en [`evidence/mobsf_report.pdf`](../evidence/mobsf_report.pdf).

---

## 6. 📋 Hallazgos (qué problemas encontramos)

**Cómo leer la columna "Gravedad":** *Alta* = hay que arreglarlo pronto · *Media* = conviene arreglarlo · *Baja / Info* = detalle a mejorar.

| # | Hallazgo | Explicado simple | Gravedad | ¿Quién lo encontró? |
|---|---|---|---|---|
| **H1** | Clave y secreto escritos en el código | La llave está pegada a la caja fuerte | **Alta** | 🧑‍🔧 Solo a mano |
| **H2** | Cifrado en modo ECB | Un modo antiguo: partes iguales del mensaje se ven iguales al cifrarse | **Media** (MobSF: Alta) | 🧑‍🔧 y 🤖 |
| **H3** | `allowBackup = true` | Se pueden copiar los datos de la app con un cable USB | **Media** | 🧑‍🔧 y 🤖 |
| **H4** | Detección de root fácil de evadir | Busca nombres y rutas conocidas; quien los conoce los puede esquivar | **Info** | 🧑‍🔧 y 🤖 |
| **H5** | Detección de depuración básica | Solo mira una marca; no detecta herramientas como Frida | **Info** | 🧑‍🔧 Solo a mano |
| **H6** | Ofuscación débil | Solo cambia nombres a `a`, `b`, `c`; el código sigue siendo legible | **Baja** | 🧑‍🔧 Solo a mano |
| **H7** | Actividad principal expuesta por defecto | Con esta versión de Android, la pantalla inicial queda accesible para otras apps | **Info** | 🧑‍🔧 *(MobSF no lo marcó)* |
| **H8** | Funciona en Android 4.4 (`minSdk 19`) | Se puede instalar en teléfonos viejos que ya no reciben parches | **Alta** según MobSF | 🤖 Solo MobSF |
| **H9** | La app escribe un mensaje de error en el registro | Un detalle: mejor no registrar información interna | **Info** | 🤖 |

> 📝 **Sobre H7:** nuestra lectura del manifiesto dice que queda expuesta por defecto, pero MobSF reporta 0 actividades expuestas. **No sabemos cuál es la causa**; queda como pregunta abierta. Una posible explicación es que MobSF no cuente la pantalla de inicio, pero **no lo verificamos**.
>
> 📝 **Sobre H4:** MobSF mostró dos avisos opuestos sobre `c.java` ("puede pedir root" y "tiene detección de root"). Por el código sabemos que la app **detecta** root, no lo pide, así que el primer aviso parece un **falso positivo**.

## 7. 🤖 vs 🧑‍🔧 : comparación

| | MobSF (automático) | A mano |
|---|---|---|
| ⏱️ Velocidad | Muy rápido | Más lento |
| 🔎 Profundidad | Superficial | Muy profundo |
| ✅ Encontró | `minSdk 19`, aviso del registro | La clave escrita en el código, detección de depuración, ofuscación |
| ❌ No encontró | **La clave escrita en el código** (el hallazgo más grave) | El `minSdk 19` ni lo marcó como problema |
| 🎓 Aprendes | Qué revisar | Por qué y cómo ocurre |

## 8. 💬 Conclusiones

*Escritas por el autor de la práctica:*

1. **Los hallazgos hechos a mano son más profundos** que los de una app automática.
2. **MobSF es rápida, pero se salta algunas cosas.** En nuestro caso, no marcó el hallazgo más grave.
3. **Hay que usar dos métodos** para revisar una app: uno automático para cubrir terreno rápido, y uno manual para entender de verdad qué pasa.

## 9. 🛠️ Cómo se arreglaría la app

| Problema | Solución |
|---|---|
| Clave en el código (H1) | **No guardar secretos en la app.** Comprobarlos en un servidor, o usar el almacén seguro de Android (*Keystore*) |
| Modo ECB (H2) | Usar un modo moderno, como AES-GCM |
| `allowBackup` (H3) | Ponerlo en `false` |
| Android antiguo (H8) | Subir la versión mínima soportada |
| Defensas débiles (H4, H5, H6) | Complementarlas con verificaciones desde el servidor |

## 10. 🧯 Problemas que tuvimos (y cómo se resolvieron)

| Problema | Por qué pasó | Solución |
|---|---|---|
| `cd /TOOLS` no funciona | La `/` inicial busca en la raíz del sistema | Usar `~/TOOLS` |
| `LS: command not found` | Linux distingue mayúsculas | Escribir `ls` |
| `file` dijo "imagen Targa" | Esa herramienta no reconoce el formato | Verificar los bytes con `od` |
| jadx-gui: "File not found" | Usé una ruta relativa | Usar ruta completa con `$PWD` |
| Python: `No module named 'Crypto'` | En el paquete de Kali el módulo se llama **`Cryptodome`** | Cambiar el `import` |
| El texto cifrado medía 12 bytes | Copié la cadena incompleta | Copiarla completa y comprobar el tamaño |
| El PDF de MobSF no estaba donde pensaba | Firefox lo guardó en otra carpeta | Buscarlo con `find` |

## 11. 📚 Glosario: palabras que vas a encontrar

| Palabra | Significado simple |
|---|---|
| **APK** | El archivo con el que se instala una app de Android (una "caja" comprimida) |
| **Manifiesto** | La lista de permisos y puertas de entrada de la app |
| **Decompilar** | Convertir el código de la app a algo que una persona pueda leer |
| **Hash** | Una "huella digital" del archivo; si cambia una letra, cambia la huella |
| **Cifrar / descifrar** | Convertir un mensaje en algo ilegible / volverlo legible con una clave |
| **AES** | Un método muy usado de cifrado |
| **Clave** | El "código secreto" para cifrar o descifrar |
| **Hexadecimal** | Una forma de escribir números con 0-9 y a-f |
| **Base64** | Una forma de escribir datos usando letras y números |
| **Root** | Permisos de administrador total en un teléfono Android |
| **Ofuscación** | Hacer el código difícil de leer (por ejemplo, cambiando nombres) |
| **Análisis estático** | Revisar una app sin ejecutarla |
| **MobSF** | Programa que revisa apps móviles de forma automática |
| **Falso positivo** | Un aviso que parece un problema pero no lo es |

## 12. 📁 Estructura del repositorio

```
android-apk-lab/
├── README.md                  ← portada (español e inglés)
├── .gitignore
├── docs/
│   ├── PRACTICA_ES.md         ← este documento
│   └── PRACTICE_EN.md         ← versión en inglés
├── scripts/
│   └── run_lab.sh             ← automatiza los primeros pasos
├── reto/
│   └── solve.py               ← el script de Python del reto
└── evidence/
    ├── salida_run_lab.txt     ← salida de referencia
    ├── mi_salida.txt          ← salida de mi ejecución
    ├── hallazgos_automaticos.txt
    └── mobsf_report.pdf       ← reporte de MobSF
```

## 13. 🙏 Créditos

- App de práctica: [OWASP MASTG Crackmes](https://github.com/OWASP/mastg)
- Herramientas: [Apktool](https://github.com/iBotPeaches/Apktool) · [jadx](https://github.com/skylot/jadx) · [dex2jar](https://github.com/pxb1988/dex2jar) · [JD-GUI](https://github.com/java-decompiler/jd-gui) · [MobSF](https://github.com/MobSF/Mobile-Security-Framework-MobSF)
- El script y las guías se prepararon con asistencia de IA (Claude). Los comandos fueron ejecutados y verificados por el autor, y las conclusiones son suyas.
