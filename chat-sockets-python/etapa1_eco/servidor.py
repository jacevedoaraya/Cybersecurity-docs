import socket

HOST = "127.0.0.1"
PORT = 5000

servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
servidor.bind((HOST, PORT))
servidor.listen(5)
print(f"Escuchando en {HOST}:{PORT}... (Ctrl+C para apagar)")

try:
    while True:
        conexion, direccion = servidor.accept()
        print(f"Cliente conectado desde {direccion}")

        while True:
            datos = conexion.recv(1024)
            if not datos:
                print("El cliente se desconectó")
                break
            print(f"Recibido: {datos.decode('utf-8').strip()}")
            conexion.sendall(datos)

        conexion.close()
except KeyboardInterrupt:
    print("\nApagando servidor...")
finally:
    servidor.close()
