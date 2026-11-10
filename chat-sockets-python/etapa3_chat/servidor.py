import socket
import threading
from protocolo import enviar_mensaje, recibir_mensaje

HOST = "127.0.0.1"
PORT = 5000

clientes = []
candado = threading.Lock()


def difundir(mensaje):
    with candado:
        for cliente in clientes:
            try:
                enviar_mensaje(cliente, mensaje)
            except OSError:
                pass


def atender_cliente(conexion, direccion):
    nombre = str(direccion[1])
    with candado:
        clientes.append(conexion)
    print(f"[+] {nombre} conectado")
    difundir(f"*** {nombre} se unió al chat ***")

    try:
        while True:
            mensaje = recibir_mensaje(conexion)
            if mensaje is None:
                break
            print(f"[{nombre}] {mensaje}")
            difundir(f"[{nombre}] {mensaje}")
    except (ConnectionResetError, BrokenPipeError):
        pass
    finally:
        with candado:
            clientes.remove(conexion)
        conexion.close()
        print(f"[-] {nombre} desconectado")
        difundir(f"*** {nombre} salió del chat ***")


servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
servidor.bind((HOST, PORT))
servidor.listen(5)
print(f"Escuchando en {HOST}:{PORT}... (Ctrl+C para apagar)")

try:
    while True:
        conexion, direccion = servidor.accept()
        hilo = threading.Thread(
            target=atender_cliente,
            args=(conexion, direccion),
            daemon=True,
        )
        hilo.start()
except KeyboardInterrupt:
    print("\nApagando servidor...")
finally:
    servidor.close()
