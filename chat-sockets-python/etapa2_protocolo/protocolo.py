import struct

TAM_CABECERA = 4


def enviar_mensaje(sock, texto):
    datos = texto.encode("utf-8")
    cabecera = struct.pack("!I", len(datos))
    sock.sendall(cabecera + datos)


def recibir_exacto(sock, n):
    datos = b""
    while len(datos) < n:
        pedazo = sock.recv(n - len(datos))
        if not pedazo:
            return None
        datos += pedazo
    return datos


def recibir_mensaje(sock):
    cabecera = recibir_exacto(sock, TAM_CABECERA)
    if cabecera is None:
        return None
    longitud = struct.unpack("!I", cabecera)[0]
    datos = recibir_exacto(sock, longitud)
    if datos is None:
        return None
    return datos.decode("utf-8")
