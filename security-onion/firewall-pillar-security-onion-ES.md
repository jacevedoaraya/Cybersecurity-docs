# Security Onion: Solución de Fallas en el Enrolamiento de Agentes mediante Configuración de Firewall y Pillar

**Bitácora de diagnóstico y remediación — Entorno de laboratorio SecOps**

| Campo | Valor |
|---|---|
| Entorno | Security Onion (modo Eval), basado en CentOS/Rocky |
| Minion ID | `juanpablo_eval` |
| Objetivo | Resolver la mala configuración de firewall que impedía el enrolamiento de agentes |
| Herramientas usadas | Salt (`salt-call`), nftables/iptables-nft, vi, bash |

---

## 1. Resumen del problema

No era posible enrolar nuevos agentes en el manager de Security Onion. La investigación llevó el problema hasta el firewall interno orientado a Docker (nftables, gestionado a través de la cadena `DOCKER-USER`), el cual no estaba permitiendo el tráfico desde la red de analistas hacia los puertos necesarios para el enrolamiento y el monitoreo (API REST de Elasticsearch y la interfaz web de gestión servida por Nginx).

La solución requirió definir un nuevo pillar de Salt para el host afectado, lo cual a su vez reveló dos vacíos preexistentes en la configuración base del pillar del nodo (faltaban las definiciones de la interfaz del sensor y de la interfaz principal del host), que estaban bloqueando silenciosamente la aplicación del estado de firewall por completo.

---

## 2. Análisis de causa raíz

### 2.1 Pillar de firewall faltante / con nombre incorrecto

Las reglas de firewall de Security Onion se generan por minion a partir de archivos pillar de Salt ubicados en `/opt/so/saltstack/local/pillar/minions/`. El archivo de pillar debe nombrarse exactamente igual al ID del minion de Salt (confirmado con `salt-call grains.get id`), no con un nombre arbitrario.

El archivo se creó inicialmente como `nohacker_eval.sls`, pero el ID real del minion era `juanpablo_eval` — por lo que Salt nunca cargó la configuración deseada.

### 2.2 Dependencias de pillar sin definir (sensor.interface, host.mainint)

Tras corregir el nombre del archivo, la aplicación del estado de firewall falló con un error de renderizado de Jinja en `globals.map.jinja`, una plantilla compartida que usan la mayoría de los estados de Security Onion. Faltaban por completo dos valores requeridos en el árbol de pillar del nodo:

- **`sensor.interface`** — la interfaz de red usada para la captura de tráfico (`bond0`, MTU 9000, sin IP — la interfaz de sniffing).
- **`host.mainint`** — la interfaz de gestión (`ens160`, la que tiene la IP de administración del host).

Estos valores estaban ausentes en todos los archivos de pillar del sistema (confirmado mediante grep recursivo), incluyendo un archivo `adv_juanpablo_eval.sls` vacío (0 bytes) que parecía ser un remanente de una instalación inicial incompleta.

Como estos valores los consume una plantilla global compartida por casi todos los estados de Security Onion, su ausencia estaba bloqueando no solo el estado de firewall, sino potencialmente la aplicación de otros estados en este nodo.

---

## 3. Pasos de remediación

### Paso 1 — Confirmar el ID real del minion

```bash
sudo salt-call grains.get id
```

**Resultado:** devolvió `juanpablo_eval`, confirmando el desajuste en el nombre del archivo de pillar.

### Paso 2 — Crear el archivo de pillar con el nombre correcto y la regla de firewall

```bash
sudo tee /opt/so/saltstack/local/pillar/minions/juanpablo_eval.sls > /dev/null << 'EOF'
firewall:
  hostgroups:
    analyst:
      - 192.168.116.0/24
  role:
    eval:
      chain:
        DOCKER-USER:
          hostgroups:
            analyst:
              portgroups:
                - elasticsearch_rest
                - nginx
EOF
```

**Resultado:** escrito directamente mediante un heredoc (`bash tee`) en lugar de un editor interactivo, para evitar corrupción por una sesión de `vi` trabada y archivos swap sueltos.

### Paso 3 — Refrescar y validar el pillar

```bash
sudo salt-call saltutil.refresh_pillar
sudo salt-call pillar.get firewall
```

**Resultado:** se confirmó que Salt ahora fusionaba correctamente el nuevo hostgroup `analyst` con los datos de pillar existentes.

### Paso 4 — Primer intento de state.apply (falla parcial)

```bash
sudo salt-call state.apply firewall
```

**Resultado:** falló con: `Jinja variable ... has no attribute 'sensor'` — se identificó que faltaba la clave de pillar `sensor.interface`.

### Paso 5 — Agregar la interfaz de sensor faltante

```bash
sudo tee -a /opt/so/saltstack/local/pillar/minions/juanpablo_eval.sls > /dev/null << 'EOF'
sensor:
  interface: bond0
EOF
```

**Resultado:** interfaz identificada mediante `ip a` como la interfaz dedicada de captura (sin IP, MTU 9000).

### Paso 6 — Segundo intento de state.apply (falla parcial)

```bash
sudo salt-call state.apply firewall
```

**Resultado:** falló con un nuevo error: `has no attribute 'host'` — rastreado hasta `globals.map.jinja`, que requiere `host.mainint`.

### Paso 7 — Agregar la interfaz de gestión faltante

```bash
sudo tee -a /opt/so/saltstack/local/pillar/minions/juanpablo_eval.sls > /dev/null << 'EOF'
host:
  mainint: ens160
EOF
```

**Resultado:** interfaz identificada mediante `ip a` como la interfaz con la IP de gestión (192.168.140.150).

### Paso 8 — state.apply final (éxito)

```bash
sudo salt-call state.apply firewall
```

**Resultado:** `Succeeded: 8 (changed=4), Failed: 0`. El conjunto de reglas de iptables/nftables se actualizó y recargó mediante `iptables-restore`.

### Paso 9 — Verificar el ruleset de firewall en vivo

```bash
sudo nft list ruleset | grep "192.168.116"
```

**Resultado:** se confirmaron tres nuevas reglas ACCEPT para `192.168.116.0/24` en los puertos 9200 (Elasticsearch), 80 y 443 (Nginx).

---

## 4. Verificación

Se inspeccionó directamente el ruleset final de nftables (no solo la salida del estado de Salt) para confirmar que el cambio surtió efecto en la capa de filtrado de paquetes:

```
ip saddr 192.168.116.0/24 tcp dport 9200 counter packets 0 bytes 0 accept
ip saddr 192.168.116.0/24 tcp dport 80 counter packets 0 bytes 0 accept
ip saddr 192.168.116.0/24 tcp dport 443 counter packets 0 bytes 0 accept
```

Con estas reglas activas, los hosts en la subred de analistas (`192.168.116.0/24`) ahora pueden acceder a la API REST de Elasticsearch y a la interfaz de gestión servida por Nginx, necesarias para el enrolamiento de agentes.

---

## 5. Aprendizajes clave

- Los nombres de archivo de pillar de Salt para configuración por minion deben coincidir exactamente con el ID del minion (`salt-call grains.get id`), no con un nombre asignado informalmente.
- Una sola clave de pillar faltante en una plantilla Jinja compartida (`globals.map.jinja`) puede bloquear silenciosamente estados no relacionados en todo el nodo — siempre hay que rastrear los errores de renderizado de Jinja hasta la clave de pillar específica referenciada en el traceback.
- Cuando una sesión de editor interactivo se vuelve poco confiable (macros trabadas, archivos swap huérfanos), escribir la configuración mediante un heredoc no interactivo (`cat`/`tee << EOF`) es una alternativa más segura y reproducible que editar a mano en `vi`.
- Siempre validar una corrección en dos capas: la capa de orquestación (`salt-call pillar.get` / resumen de `state.apply`) y el estado realmente aplicado (`nft list ruleset`) — que Salt se ejecute con éxito no prueba por sí solo que el comportamiento en tiempo real haya cambiado.

---

*Preparado como parte de una práctica de laboratorio del curso de ciberseguridad sobre despliegue y diagnóstico de un SOC con Security Onion.*
