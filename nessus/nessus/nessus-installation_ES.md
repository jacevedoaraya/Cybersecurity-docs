
# Bitácora de Instalación y Solución de Problemas de Nessus

**Autor:** Juan Pablo Acevedo Araya
**Contexto:** Curso de ciberseguridad — instalación de Tenable Nessus (Essentials) en Windows
**Fecha:** Agosto 2026

> Este documento registra los problemas reales encontrados durante la instalación de Nessus, sus causas raíz y las soluciones aplicadas — útil como referencia personal y como pieza de portafolio que demuestra habilidades de troubleshooting.

---

## 1. Objetivo

Instalar Tenable Nessus en una laptop con Windows para una clase de ciberseguridad, terminando con una licencia funcional de **Nessus Essentials** (gratuita, sin vencimiento, hasta 16 hosts) asociada a una cuenta de usuario personal.

## 2. Entorno

- **Sistema operativo:** Windows 10/11
- **Producto intentado:** Nessus Professional (trial) → luego cambiado a Nessus Essentials
- **Almacenamiento probado:** Disco duro externo (unidad G:) → Disco duro externo (unidad D:) → **Disco interno (C:)** (configuración final que funcionó)

## 3. Cronología de problemas y soluciones

### Problema 1 — Registro con Gmail personal en vez de correo de trabajo
**Problema:** El formulario de registro del trial de Nessus Professional rechazó una dirección de Gmail personal, exigiendo un "correo de trabajo".
**Solución:** Se registró con un correo institucional/de trabajo en su lugar. Se confirmó que esto es legal — ninguna ley prohíbe usar un correo laboral para un registro de un curso personal —, aunque vale la pena revisar la política interna de la empresa sobre uso aceptable del correo.

### Problema 2 — "Error: You are not authorized to perform this request" al crear la cuenta
**Problema:** Al crear el usuario administrador local de Nessus a través del asistente web, el proceso falló con este error de autorización.
**Causa raíz probable:** Desincronización de sesión/tiempo en el asistente de configuración, a veces asociada a un estado residual de un paso anterior fallido.
**Intentos de solución:** Refrescar la página, limpiar caché, reiniciar el servicio de Windows de Nessus (`services.msc` → Tenable Nessus → Reiniciar).

### Problema 3 — Login fallido con "credenciales inválidas" al terminar la instalación
**Problema:** Después de que terminara la compilación de plugins y apareciera la pantalla de login, la cuenta creada no permitía iniciar sesión.
**Causa raíz:** Es probable que la cuenta nunca se haya creado completamente en el backend debido al Problema 2 — el asistente *parecía* avanzar, pero el registro del usuario quedó incompleto.
**Solución:** Se usó la herramienta de línea de comandos `nessuscli` para gestionar usuarios directamente, evitando el asistente web:
```bash
# En Windows, cd solo no cambia de unidad — usar /d
cd /d "G:\Programas"

# Crear un nuevo usuario administrador
nessuscli adduser

# Listar usuarios existentes (para verificar qué quedó guardado realmente)
nessuscli lsuser

# Eliminar un usuario si es necesario
nessuscli rmuser <usuario>

# Restablecer la contraseña de un usuario existente
nessuscli chpasswd <usuario>
```
Debe ejecutarse desde una **terminal elevada (como Administrador)**, ubicada en la carpeta donde se instaló Nessus (contiene `nessuscli.exe`).

### Problema 4 — El usuario `jacevedoaraya` seguía fallando, incluso tras reinstalar
**Problema:** Ese nombre de usuario específico siempre producía `An error occurred` al crearlo con `nessuscli adduser`, aunque `nessuscli lsuser` mostraba que no existía ningún usuario.
**Causa raíz probable:** Estado residual/huérfano asociado exactamente a ese nombre de usuario desde el intento fallido anterior por la web (Problema 2), no visible mediante `lsuser` pero que igual bloqueaba su recreación.
**Solución:** Simplemente se usó un nombre de usuario distinto (ej. `jpacevedo`) — funcionó de inmediato (`User added`).

### Problema 5 — "Only a Nessus Manager license allows you to create more than one user"
**Problema:** Se intentó crear un segundo usuario sin haber eliminado el primero.
**Causa raíz:** Las licencias Essentials/trial de Professional solo permiten **un usuario local a la vez**.
**Solución:** Eliminar el usuario existente primero (`nessuscli rmuser <usuario>`), confirmar la eliminación con `nessuscli lsuser`, y luego crear el nuevo.

### Problema 6 — El escáner aparecía como "Unregistered Scanner" / Activation Code: N/A
**Problema:** El login funcionó, pero la página "About" mostraba el escáner como no registrado — es decir, la activación del trial nunca se completó, probablemente relacionado con la solicitud fallida del Problema 2.
**Solución:** Se obtuvo el código de activación real desde el portal de la cuenta de Tenable (sección `My Trials` / `My Products` — **no** desde el correo de confirmación, que no lo mostraba), y se ingresó manualmente en **Settings → About → Overview → Activation Code (ícono de lápiz)**.

### Problema 7 — Al trial de Nessus Professional solo le quedaban ~5 días
**Problema:** La licencia de prueba de Professional era de corta duración y poco práctica para el curso.
**Decisión:** Se cambió a **Nessus Essentials** — gratuita, sin vencimiento, con un límite de hosts (16) suficiente para uso académico/laboratorio en casa.

### Problema 8 — La sesión se cerró a mitad de cambiar el código de activación
**Problema:** Al reemplazar el código de Professional por el de Essentials, la sesión se cerró antes de guardar, y el código anterior de Professional quedó activo (incluso extendido un día).
**Intento de solución:** Reintentar el cambio de código sin refrescar la página a mitad de proceso — resultados inconsistentes, lo que llevó al Problema 9.

### Problema 9 — Inconsistencias persistentes llevaron a una reinstalación limpia
**Problema:** Cambiar de licencia sin reinstalar seguía produciendo casos extraños (configuración residual, licencia incorrecta persistiendo).
**Decisión:** Se desinstaló Nessus por completo y se **borraron manualmente las carpetas de datos residuales** (`nessus`, `conf`) de las ubicaciones de instalación anteriores, ya que el desinstalador no siempre las elimina — este dato residual también fue la causa de una inesperada pantalla de **"Nessus is locked — enter encryption password"** en una instalación supuestamente limpia (quedó una base de datos cifrada de una instalación anterior).

### Problema 10 — Instalar en discos externos (G:, luego D:) causó inestabilidad repetida
**Problema:** Los errores de autorización/estado fueron más frecuentes cuando Nessus estaba instalado en discos USB externos.
**Causa raíz (sospechada):** Menor velocidad de E/S y/o diferencias en el manejo de permisos del sistema de archivos en discos externos/removibles frente a un disco interno.
**Solución:** Se reinstaló en el **disco interno C:** — no volvieron a ocurrir errores de autorización, y la compilación de plugins fue notablemente más rápida.

### Problema 11 — "Activation failed" usando el código de Essentials de días atrás
**Problema:** El código de activación de Essentials emitido originalmente falló la validación durante la instalación limpia en C:.
**Causa raíz:** El código había **caducado** (los códigos de activación de Essentials son de un solo uso / con tiempo limitado una vez emitidos, si no se canjean de inmediato).
**Solución:** Se solicitó un **nuevo** código de activación de Essentials mediante el formulario de registro (`Get an activation code` → omitir si se reutiliza → o llenar el formulario de nuevo para obtener uno fresco) y se ingresó de inmediato. Esta vez se validó correctamente y continuó la descarga/compilación de plugins.

## 4. Configuración final funcional

- Nessus instalado en el **disco interno (C:)**
- Licencia: **Nessus Essentials** (gratuita, sin vencimiento, hasta 16 hosts)
- Usuario administrador local creado exitosamente a través del asistente web estándar (no fue necesario el workaround de `nessuscli` en la instalación limpia de C:)

## 5. Lecciones clave aprendidas

1. **Instalar en el disco interno, no en un disco externo/USB.** Los discos externos generaron errores repetidos de autorización y bloqueo, probablemente por velocidad de E/S y/o manejo de permisos.
2. **`cd` por sí solo no cambia de unidad en `cmd` de Windows.** Usar `cd /d "X:\ruta"` para cambiar de unidad y carpeta al mismo tiempo.
3. **`nessuscli` es un respaldo confiable** cuando el asistente web falla al crear un usuario (`adduser`, `lsuser`, `rmuser`, `chpasswd`).
4. **Un nombre de usuario que falló una vez puede quedar "atascado"**, aunque no aparezca en `lsuser` — es más rápido usar un nombre distinto que seguir depurando indefinidamente.
5. **Las licencias Essentials/trial de Professional solo permiten un usuario local** — eliminar el anterior antes de crear uno nuevo.
6. **El código de activación no siempre viene en el correo de bienvenida** — revisar el portal de la cuenta de Tenable (`My Trials`) para obtener el código real y vigente.
7. **Los códigos de activación pueden caducar antes de usarse** — si aparece "Activation failed" con buena conexión a internet, es mejor solicitar un código nuevo que reintentar el mismo repetidamente.
8. **Cuando el estado de la licencia queda inconsistente, una reinstalación limpia (borrando manualmente las carpetas residuales `nessus`/`conf`) suele ser más rápido que seguir depurando en el mismo lugar.**
9. **Nessus Essentials es la opción correcta para cursos/laboratorios caseros:** es gratuita, no vence, y el límite de 16 hosts rara vez es una limitación real para fines de aprendizaje — a diferencia de un trial de Professional que vence en días.

---

## 📎 Referencia rápida — Comandos de `nessuscli`

| Comando | Propósito |
|---|---|
| `cd /d "X:\ruta"` | Cambiar de unidad y carpeta en cmd de Windows |
| `nessuscli adduser` | Crear un usuario nuevo |
| `nessuscli lsuser` | Listar usuarios existentes |
| `nessuscli rmuser <usuario>` | Eliminar un usuario |
| `nessuscli chpasswd <usuario>` | Restablecer la contraseña de un usuario |
