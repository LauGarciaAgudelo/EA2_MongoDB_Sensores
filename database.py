"""
database.py

Modulo encargado de la conexion a MongoDB local para el proyecto de
sensores industriales.

"""

import os

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "monitoreo_industrial")
NOMBRE_COLECCION_SENSORES = "sensores"

TIMEOUT_CONEXION_MS = 5000

_cliente = None

def obtener_cliente():
   
    global _cliente
    if _cliente is None:
        _cliente = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=TIMEOUT_CONEXION_MS,
            tz_aware=True,
        )
    return _cliente


def obtener_base_datos(nombre_bd=None):

    cliente = obtener_cliente()
    return cliente[nombre_bd or MONGO_DB_NAME]


def obtener_coleccion_sensores(nombre_bd=None):
    base_datos = obtener_base_datos(nombre_bd)
    return base_datos[NOMBRE_COLECCION_SENSORES]


def verificar_conexion():

    try:
        cliente = obtener_cliente()
        cliente.admin.command("ping")
        return True
    except ServerSelectionTimeoutError:
        print(
            "Error: no se pudo conectar con MongoDB (tiempo de espera agotado). "
            "Verifica que el servicio de MongoDB este corriendo localmente."
        )
        return False
    except PyMongoError as error:
        print(f"Error al conectar con MongoDB: {type(error).__name__}")
        return False


if __name__ == "__main__":

    if verificar_conexion():
        print(f"Conexion exitosa. Base de datos configurada: {MONGO_DB_NAME}")
    else:
        print("No fue posible conectar con MongoDB.")
