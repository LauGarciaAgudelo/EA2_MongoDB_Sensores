"""
init_db.py

Script para crear (en caso de que no existan) la base de datos
'monitoreo_industrial' y la coleccion 'sensores'.

"""

import sys

from pymongo.errors import CollectionInvalid, PyMongoError

from database import (
    NOMBRE_COLECCION_SENSORES,
    obtener_base_datos,
    obtener_cliente,
    verificar_conexion,
)


def crear_coleccion_si_no_existe(base_datos):
    colecciones_existentes = base_datos.list_collection_names()

    if NOMBRE_COLECCION_SENSORES in colecciones_existentes:
        print(f"La coleccion '{NOMBRE_COLECCION_SENSORES}' ya existe. No se modifica nada.")
        return

    try:
        base_datos.create_collection(NOMBRE_COLECCION_SENSORES)
        print(f"Coleccion '{NOMBRE_COLECCION_SENSORES}' creada correctamente.")
    except CollectionInvalid:
        print(f"La coleccion '{NOMBRE_COLECCION_SENSORES}' ya existia.")


def main():
    print("Verificando conexion con MongoDB...")
    if not verificar_conexion():
        print("No fue posible inicializar la base de datos: sin conexion a MongoDB.")
        return 1

    cliente = obtener_cliente()
    try:
        base_datos = obtener_base_datos()
        crear_coleccion_si_no_existe(base_datos)

        if NOMBRE_COLECCION_SENSORES not in base_datos.list_collection_names():
            print("Error: la coleccion 'sensores' no esta disponible despues de intentar crearla.")
            return 1

        print(
            f"Base de datos '{base_datos.name}' y coleccion "
            f"'{NOMBRE_COLECCION_SENSORES}' listas para usar."
        )
        return 0
    except PyMongoError as error:
        print(f"Error al inicializar la base de datos: {type(error).__name__}: {error}")
        return 1
    finally:
        cliente.close()


if __name__ == "__main__":
    sys.exit(main())
