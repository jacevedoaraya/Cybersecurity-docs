import socket
import threading
from protocolo import enviar_mensaje, recibir_mensaje

HOST = "127.0.0.1"
PORT = 5000


def escuchar(sock):
    while True:
        try:
            mensaje = recibir_mensaje(sock)
        except OSError:
            break
        if mensaje is None:
            print("\rEl servidor cerró la conexión. Escribe 'salir'.")
            break
        print(f"\r{mensaje}\nTú> ", end="", flush=True)


cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    cliente.connect((HOST, PORT))
    print(f"Conectado a {HOST}:{PORT}. Escribe 'salir' para terminar.")

    hilo = threading.Thread(target=escuchar, args=(cliente,), daemon=True)
    hilo.start()

    while True:
        mensaje = input("Tú> ")
        if mensaje == "salir":
            break
        if not mensaje:
            continue
        if mensaje == "largo":
            mensaje = "A" * 1500 + "FIN"
        enviar_mensaje(cliente, mensaje)
except ConnectionRefusedError:
    print("No se pudo conectar. ¿Está corriendo el servidor?")
except (BrokenPipeError, ConnectionResetError):
    print("Se perdió la conexión con el servidor")
except KeyboardInterrupt:
    print()
finally:
    cliente.close()
    print("Desconectado")
