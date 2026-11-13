"""
validaciones.py

Funciones reutilizables para validar los datos de un sensor antes de
guardarlos en MongoDB. Todas las funciones lanzan 'ErrorValidacion'
(definida en errores.py) cuando un dato no es valido, para que API.py
pueda convertir ese error en una respuesta HTTP 400 con un mensaje claro.
"""

import math
from datetime import datetime, timezone

from errores import ErrorValidacion

# Tipos de sensor permitidos y su rango valido (minimo, maximo).
RANGOS_POR_TIPO = {
    "temperatura": (-10, 100),
    "presion": (0, 500),
    "vibracion": (0, 5),
}

TIPOS_VALIDOS = set(RANGOS_POR_TIPO.keys())

# Campos que debe tener un sensor al crearlo (POST) y los que se pueden
# modificar al actualizarlo (PUT). El campo 'tipo' nunca es modificable.
CAMPOS_SENSOR = {"tipo", "valor", "ubicacion", "fecha"}
CAMPOS_ACTUALIZABLES = {"valor", "ubicacion", "fecha"}


def validar_tipo(tipo):
    """Comprueba que 'tipo' sea uno de los tres tipos de sensor permitidos."""
    if not isinstance(tipo, str) or tipo not in TIPOS_VALIDOS:
        raise ErrorValidacion(
            f"El campo 'tipo' debe ser uno de: {sorted(TIPOS_VALIDOS)}."
        )
    return tipo


def validar_valor(valor, tipo):
    """
    Comprueba que 'valor' sea un numero finito (no booleano) y que este
    dentro del rango permitido para el tipo de sensor indicado.
    """
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ErrorValidacion("El campo 'valor' debe ser un numero (no booleano).")
    if not math.isfinite(valor):
        raise ErrorValidacion("El campo 'valor' debe ser un numero finito.")

    minimo, maximo = RANGOS_POR_TIPO[tipo]
    if not (minimo <= valor <= maximo):
        raise ErrorValidacion(
            f"El valor para un sensor de '{tipo}' debe estar entre {minimo} y {maximo}."
        )
    return float(valor)


def validar_ubicacion(ubicacion):
    """Comprueba que 'ubicacion' sea una cadena no vacia (sin contar espacios)."""
    if not isinstance(ubicacion, str) or not ubicacion.strip():
        raise ErrorValidacion("El campo 'ubicacion' debe ser un texto no vacio.")
    return ubicacion.strip()


def validar_fecha(fecha_texto):
    """
    Comprueba que 'fecha' sea una cadena en formato ISO 8601 y la convierte
    a un datetime en UTC, redondeado a milisegundos (la precision maxima
    que MongoDB puede almacenar).

    Si la fecha no incluye zona horaria (por ejemplo "2026-11-13T10:30:00"),
    se asume que ya esta en UTC.
    """
    if not isinstance(fecha_texto, str) or not fecha_texto.strip():
        raise ErrorValidacion(
            "El campo 'fecha' debe ser una cadena en formato ISO 8601, "
            "por ejemplo: 2026-11-13T10:30:00Z."
        )

    texto = fecha_texto.strip()
    # Python entiende el sufijo "+00:00" pero no la "Z" de UTC, asi que la
    # traducimos antes de interpretar la fecha.
    if texto.endswith("Z"):
        texto = texto[:-1] + "+00:00"

    try:
        fecha = datetime.fromisoformat(texto)
    except ValueError:
        raise ErrorValidacion(
            "El campo 'fecha' no tiene un formato ISO 8601 valido, "
            "por ejemplo: 2026-11-13T10:30:00Z."
        )

    if fecha.tzinfo is None:
        # Sin zona horaria: se asume UTC (ver nota en README/BITACORA).
        fecha = fecha.replace(tzinfo=timezone.utc)
    else:
        fecha = fecha.astimezone(timezone.utc)

    milisegundos = fecha.microsecond // 1000
    return fecha.replace(microsecond=milisegundos * 1000)


def _validar_campos_desconocidos(datos, campos_permitidos):
    """Lanza un error si 'datos' trae alguna clave fuera de 'campos_permitidos'."""
    desconocidos = set(datos.keys()) - campos_permitidos
    if desconocidos:
        raise ErrorValidacion(f"Campos no permitidos: {sorted(desconocidos)}.")


def validar_datos_creacion(datos):
    """
    Valida el cuerpo JSON para crear un sensor (POST /sensores/).
    Exige los cuatro campos obligatorios y devuelve el documento ya listo
    para insertar en MongoDB (con 'fecha' convertida a datetime UTC).
    """
    if not isinstance(datos, dict):
        raise ErrorValidacion("El cuerpo de la solicitud debe ser un objeto JSON.")

    _validar_campos_desconocidos(datos, CAMPOS_SENSOR)

    faltantes = CAMPOS_SENSOR - set(datos.keys())
    if faltantes:
        raise ErrorValidacion(f"Faltan campos obligatorios: {sorted(faltantes)}.")

    tipo = validar_tipo(datos["tipo"])
    valor = validar_valor(datos["valor"], tipo)
    ubicacion = validar_ubicacion(datos["ubicacion"])
    fecha = validar_fecha(datos["fecha"])

    return {"tipo": tipo, "valor": valor, "ubicacion": ubicacion, "fecha": fecha}


def validar_datos_actualizacion(datos, tipo_actual):
    """
    Valida el cuerpo JSON para actualizar un sensor (PUT). Solo permite
    modificar 'valor', 'ubicacion' y 'fecha'; 'tipo' y '_id' son
    inmutables. Devuelve unicamente los campos que se deben actualizar.
    """
    if not isinstance(datos, dict):
        raise ErrorValidacion("El cuerpo de la solicitud debe ser un objeto JSON.")

    if "tipo" in datos:
        raise ErrorValidacion("No se permite modificar el campo 'tipo'.")
    if "_id" in datos:
        raise ErrorValidacion("No se permite modificar el campo '_id'.")

    _validar_campos_desconocidos(datos, CAMPOS_ACTUALIZABLES)

    if not datos:
        raise ErrorValidacion(
            "Debe incluir al menos un campo para actualizar: valor, ubicacion o fecha."
        )

    actualizacion = {}
    if "valor" in datos:
        actualizacion["valor"] = validar_valor(datos["valor"], tipo_actual)
    if "ubicacion" in datos:
        actualizacion["ubicacion"] = validar_ubicacion(datos["ubicacion"])
    if "fecha" in datos:
        actualizacion["fecha"] = validar_fecha(datos["fecha"])

    return actualizacion
