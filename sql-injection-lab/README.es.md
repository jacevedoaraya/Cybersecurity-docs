# Informe de Pruebas de Inyección SQL — Web for Pentester

**Laboratorio:** Web for Pentester (PentesterLab) — Módulo SQL Injections
**Alumno:** Juan Pablo Acevedo Araya
**Fecha:** 1-10-2026
**Máquina virtual objetivo:** `http://192.168.140.136/`

> 🇬🇧 [Read this report in English](README.md)

## Introducción

Este documento recopila la evidencia y el análisis de los 9 ejercicios de inyección SQL (SQL Injection) del laboratorio Web for Pentester. Para cada ejemplo se documenta el payload utilizado, la petición enviada, el resultado observado en la aplicación, si la vulnerabilidad fue explotada con éxito y una breve explicación técnica de la causa raíz.

⚠️ **Nota:** todas las pruebas se realizaron contra una máquina virtual de laboratorio aislada y con fines exclusivamente educativos.

---

## Example 1 — Tautología básica (GET `name`)

**Objetivo:** Inyección SQL clásica tipo tautología (error-based / bypass de filtro) en el parámetro GET `name` de `example1.php`.

- **Payload:** `name=root' OR '1'='1`
- **URL:** `http://192.168.140.136/sqli/example1.php?name=root' OR '1'='1`
- **Resultado:** La aplicación devolvió TODOS los registros de la tabla `users` (id 1-admin, 2-root, 3-user1, 5-user2) en lugar de solo el usuario `root`.
- **¿Vulnerable?** Sí

**Explicación técnica:** El valor de `name` se concatena directamente dentro de la consulta SQL sin sanitizar ni usar consultas parametrizadas: `SELECT id, name, age FROM users WHERE name = '$name'`. Al inyectar `root' OR '1'='1`, la condición `WHERE` queda como `name='root' OR '1'='1'`, y como `'1'='1'` es siempre verdadero, la cláusula `OR` obliga a que se devuelvan todas las filas de la tabla, sin importar el nombre buscado.

![Example 1](images/example1.png)

---

## Example 2 — Bypass de filtro de espacios

**Objetivo:** Inyección SQL tipo tautología (error-based) en el parámetro GET `name` de `example2.php`, con bypass de un filtro de espacios en blanco implementado en el servidor.

- **Payload:** `root'/**/OR/**/'1'='1`
- **URL:** `http://192.168.140.136/sqli/example2.php?name=root'/**/OR/**/'1'='1`
- **Resultado:** Al intentar el payload del Example 1 con espacios normales, la aplicación respondió "ERROR NO SPACE", indicando un filtro que bloquea el carácter espacio. Sustituyendo los espacios por comentarios SQL en línea (`/**/`), el filtro fue evadido y la aplicación devolvió TODOS los registros de la tabla `users`.
- **¿Vulnerable?** Sí

**Explicación técnica:** El servidor intenta mitigar la inyección SQL filtrando el carácter espacio (`" "`) en el parámetro `name`, probablemente mediante `str_replace(" ", "", $input)` o una validación con expresión regular. Sin embargo, este filtro es insuficiente porque MySQL permite usar comentarios de múltiples líneas (`/**/`) como separador de tokens sin necesidad de espacios literales. Esto demuestra que filtrar caracteres específicos (blacklisting) es una defensa débil frente a la inyección SQL; la solución correcta es usar consultas parametrizadas (*prepared statements*).

![Example 2](images/example2.png)

---

## Example 3 — Mismo filtro, mismo bypass

**Objetivo:** Inyección SQL tipo tautología (error-based) en el parámetro GET `name` de `example3.php`, con el mismo filtro de espacios en blanco visto en `example2.php`.

- **Payload:** `root'/**/OR/**/'1'='1`
- **URL:** `http://192.168.140.136/sqli/example3.php?name=root'/**/OR/**/'1'='1`
- **Resultado:** Igual que en example2: "ERROR NO SPACE" con espacios normales, y bypass exitoso con `/**/`, devolviendo todos los registros de `users`.
- **¿Vulnerable?** Sí

**Explicación técnica:** `example3.php` implementa la misma validación de *blacklisting* que `example2.php`. Dado que la lógica de filtrado es idéntica, el mismo bypass aplica. Esto refuerza que un filtro basado en bloquear caracteres específicos no es una defensa robusta, ya que SQL ofrece múltiples formas sintácticas equivalentes de lograr el mismo resultado.

![Example 3](images/example3.png)

---

## Example 4 — Inyección numérica sin comillas

**Objetivo:** Inyección SQL tipo tautología en un parámetro GET numérico (`id`) sin comillas, en `example4.php`, con el mismo filtro de espacios visto en ejemplos anteriores.

- **Payload:** `-1/**/OR/**/1=1`
- **URL:** `http://192.168.140.136/sqli/example4.php?id=-1/**/OR/**/1=1`
- **Resultado:** La aplicación devolvió TODOS los registros de `users`, a pesar de que `id=-1` no existe en la base de datos.
- **¿Vulnerable?** Sí

**Explicación técnica:** A diferencia de los ejemplos 1-3, aquí `id` se usa en un contexto numérico sin comillas: `SELECT id, name, age FROM users WHERE id = $id`. Al no haber comillas que cerrar, basta un operador `OR` seguido de una condición siempre verdadera. Se usó un id negativo (inexistente) para demostrar que las filas devueltas provienen de la tautología inyectada, no de una coincidencia real.

![Example 4](images/example4.png)

---

## Example 5 — UNION-based, extracción de metadatos

**Objetivo:** Inyección SQL tipo UNION-based en el parámetro GET numérico `id` de `example5.php`, con un filtro que exige que el valor comience con un dígito entero (`die("ERROR INTEGER REQUIRED")` si no).

- **Payload:** `0 UNION SELECT version(),database(),user(),4,5`
- **URL:** `http://192.168.140.136/sqli/example5.php?id=0%20UNION%20SELECT%20version(),database(),user(),4,5`
- **Resultado:** Se confirmó primero la inyección boolean-based (`id=2 and 1=1` vs `id=2 and 1=2`). Luego, por `UNION SELECT`, se determinó que la tabla tiene 5 columnas. Finalmente se extrajo: versión de MySQL (`5.1.66-0+squeeze1`), base de datos (`exercises`) y usuario de conexión (`pentestlab@localhost`).
- **¿Vulnerable?** Sí

**Explicación técnica:** El servidor valida que el valor comience con un dígito (bloqueando el signo `-`), pero no sanitiza el resto del valor, permitiendo inyectar una cláusula `UNION SELECT` completa. Esto demuestra que la inyección UNION-based puede extraer no solo datos de otras tablas, sino también metadatos del propio motor de base de datos.

![Example 5](images/example5.png)

---

## Example 6 — UNION-based sin filtros

**Objetivo:** Inyección SQL tipo UNION-based en el parámetro GET numérico `id` de `example6.php`, sin ningún filtro de entrada.

- **Payload:** `0 UNION SELECT version(),database(),user(),4,5`
- **URL:** `http://192.168.140.136/sqli/example6.php?id=0%20UNION%20SELECT%20version(),database(),user(),4,5`
- **Resultado:** Funcionó de inmediato, sin necesidad de ningún bypass, mostrando la misma información del servidor que en example5.
- **¿Vulnerable?** Sí

**Explicación técnica:** El parámetro `id` se concatena directamente en la consulta sin ninguna validación. El hecho de que ejemplos consecutivos repitan la misma vulnerabilidad de fondo mientras varía el nivel de filtrado demuestra, de forma progresiva, que ninguna validación superficial sustituye al uso de consultas parametrizadas.

![Example 6](images/example6.png)

---

## Example 7 — Extracción masiva con `group_concat`

**Objetivo:** Inyección SQL tipo UNION-based con extracción masiva de datos (`group_concat`) en el parámetro GET numérico `id` de `example7.php`, con un filtro que exige que el valor comience con un dígito y además bloquea el espacio en blanco.

- **Payload:** `0\nUNION\nSELECT\n1,group_concat(name,0x3a,passwd,0x7c),3,4,5\nFROM\nusers`
- **URL:** `http://192.168.140.136/sqli/example7.php?id=0%0aUNION%0aSELECT%0a1,group_concat(name,0x3a,passwd,0x7c),3,4,5%0aFROM%0ausers`
- **Resultado:** El payload con espacios normales dio "ERROR INTEGER REQUIRED". Sustituyendo los espacios por saltos de línea (`%0a`), el filtro fue evadido. Con `group_concat` se extrajeron en una sola petición las 4 credenciales completas de la tabla `users`: `admin:admin`, `root:admin21`, `user1:secret`, `user2:azerty`.
- **¿Vulnerable?** Sí

**Explicación técnica:** `example7.php` combina dos controles vistos antes (prefijo numérico + filtro de espacios), pero el salto de línea (`\n`) cumple la misma función sintáctica que el espacio sin ser el carácter bloqueado. La función `group_concat()` permite concatenar los valores de múltiples filas en una sola celda, exfiltrando toda una tabla en una única petición HTTP.

⚠️ Las contraseñas se almacenan **en texto plano** — una vulnerabilidad adicional independiente de la inyección SQL.

![Example 7](images/example7.png)

---

## Example 8 — Inyección en `ORDER BY` (con backticks)

**Objetivo:** Inyección SQL en la cláusula `ORDER BY`, a través del parámetro GET `order` de `example8.php`, que controla directamente el nombre de la columna usada para ordenar los resultados.

- **Payload:** `` name`DESC-- - ``
- **URL:** `` http://192.168.140.136/sqli/example8.php?order=name`DESC--%20- ``
- **Resultado:** Con la URL original (`order=name`), el orden era ascendente (admin, root, user1, user2). Con el payload, el orden se invirtió completamente (user2, user1, root, admin).
- **¿Vulnerable?** Sí

**Explicación técnica:** El parámetro `order` se concatena como nombre de columna dentro de `ORDER BY`, probablemente envuelto en *backticks*: `` ORDER BY `$order` ``. Al inyectar `` name`DESC-- - ``, se cierra el *backtick*, se añade `DESC` para invertir el orden y se comenta el resto. Este tipo de inyección, menos conocido que las basadas en `WHERE`, también puede usarse para exfiltrar datos de forma ciega en ciertos motores.

![Example 8](images/example8.png)

---

## Example 9 — Inyección en `ORDER BY` (sin comillas)

**Objetivo:** Inyección SQL en la cláusula `ORDER BY` a través del parámetro GET `order` de `example9.php`, sin ningún tipo de comilla ni *backtick* envolviendo el valor en la consulta original.

- **Payload:** `name DESC`
- **URL:** `http://192.168.140.136/sqli/example9.php?order=name%20DESC`
- **Resultado:** El orden se invirtió a descendente (user2, user1, root, admin) sin necesidad de cerrar ninguna comilla.
- **¿Vulnerable?** Sí

**Explicación técnica:** A diferencia de `example8.php`, aquí el parámetro se concatena en texto plano dentro de `ORDER BY`: `ORDER BY $order`. Cualquier palabra clave SQL válida después del nombre de columna se ejecuta directamente, sin ninguna barrera sintáctica que evadir. Es la forma más simple y directa de inyección en un `ORDER BY`.

![Example 9](images/example9.png)

---

## Conclusión general

A lo largo de los 9 ejercicios se cubrieron las principales técnicas de inyección SQL:

| # | Técnica | Punto de inyección | Filtro presente |
|---|---|---|---|
| 1 | Tautología (error-based) | `name` (string) | Ninguno |
| 2-3 | Tautología + bypass de espacios | `name` (string) | Bloqueo de espacio |
| 4 | Tautología numérica | `id` (numérico) | Bloqueo de espacio |
| 5 | UNION-based | `id` (numérico) | Prefijo numérico obligatorio |
| 6 | UNION-based | `id` (numérico) | Ninguno |
| 7 | UNION-based + `group_concat` | `id` (numérico) | Prefijo numérico + espacio |
| 8-9 | Inyección en `ORDER BY` | `order` (nombre de columna) | Backticks (ej. 8) / Ninguno (ej. 9) |

**Lección principal:** en todos los casos, la causa raíz es la **concatenación directa de entrada de usuario dentro de una consulta SQL**. Ningún mecanismo de filtrado basado en bloquear caracteres o palabras específicas (*blacklisting*) resultó suficiente, porque SQL ofrece múltiples formas sintácticas equivalentes de lograr el mismo resultado (comentarios, saltos de línea, funciones, etc.).

**Recomendación:** la única mitigación robusta es el uso de **consultas parametrizadas / prepared statements**, junto con:
- Validación estricta por lista blanca (*whitelisting*) cuando el dato de entrada controla elementos estructurales de la consulta (como nombres de columna en `ORDER BY`).
- Principio de mínimo privilegio para el usuario de base de datos de la aplicación.
- No exponer mensajes de error de la base de datos al usuario final.
- Nunca almacenar contraseñas en texto plano (usar bcrypt, Argon2, etc.).
