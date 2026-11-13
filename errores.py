"""
errores.py

Excepciones personalizadas que usa la API para traducir situaciones de
negocio (dato invalido, sensor no encontrado, conflicto, etc.) en
respuestas HTTP con el codigo de estado apropiado.

Cada excepcion tiene un atributo 'codigo_http' que API.py utiliza para
construir la respuesta JSON de error correspondiente.
"""


class ErrorAPI(Exception):
    """Clase base para los errores controlados de la API (no para bugs)."""

    codigo_http = 500

    def __init__(self, mensaje):
        super().__init__(mensaje)
        self.mensaje = mensaje


class ErrorValidacion(ErrorAPI):
    """Los datos de entrada no son validos (400 Bad Request)."""

    codigo_http = 400


class SensorNoEncontrado(ErrorAPI):
    """No existe el sensor solicitado (404 Not Found)."""

    codigo_http = 404


class ConflictoMultiplesSensores(ErrorAPI):
    """Hay mas de un sensor del tipo solicitado (409 Conflict)."""

    codigo_http = 409


class TipoContenidoNoSoportado(ErrorAPI):
    """El Content-Type de la solicitud no es 'application/json' (415)."""

    codigo_http = 415


class ServicioNoDisponible(ErrorAPI):
    """MongoDB no esta disponible en este momento (503 Service Unavailable)."""

    codigo_http = 503
