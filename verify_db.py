"""
verify_db.py

Script de prueba para comprobar que la conexion con MongoDB funciona y
que se pueden insertar, consultar y eliminar documentos en la coleccion
'sensores'.

Este script SOLO toca el documento de prueba que el mismo script crea.
No modifica ni elimina ningun otro documento de la coleccion.

Uso:
    python verify_db.py
"""

import sys
from datetime import datetime, timezone

from pymongo.errors import PyMongoError

from database import (
    MONGO_DB_NAME,
    NOMBRE_COLECCION_SENSORES,
    obtener_cliente,
    obtener_coleccion_sensores,
    verificar_conexion,
)

def _fecha_actual_compatible_con_mongo():
    """
    Genera la fecha/hora actual en UTC, redondeada a milisegundos.

    MongoDB (BSON) solo guarda fechas con precision de milisegundos, no de
    microsegundos. Si no redondeamos aqui, al leer el documento de vuelta
    los microsegundos no coinciden con los originales y la comparacion de
    campos fallaria aunque la fecha sea, en la practica, la misma.
    """
    ahora = datetime.now(timezone.utc)
    milisegundos = ahora.microsecond // 1000
    return ahora.replace(microsecond=milisegundos * 1000)


# Documento de prueba pedido por la actividad.
DOCUMENTO_PRUEBA = {
    "tipo": "temperatura",
    "valor": 25.5,
    "ubicacion": "Planta A",
    "fecha": _fecha_actual_compatible_con_mongo(),
}


def verificar_base_y_coleccion(cliente):
    """Confirma que la base de datos y la coleccion 'sensores' ya existen."""
    nombres_bd = cliente.list_database_names()
    if MONGO_DB_NAME not in nombres_bd:
        print(
            f"Error: la base de datos '{MONGO_DB_NAME}' no existe todavia. "
            "Ejecuta primero 'python init_db.py'."
        )
        return False

    base_datos = cliente[MONGO_DB_NAME]
    if NOMBRE_COLECCION_SENSORES not in base_datos.list_collection_names():
        print(
            f"Error: la coleccion '{NOMBRE_COLECCION_SENSORES}' no existe todavia. "
            "Ejecuta primero 'python init_db.py'."
        )
        return False

    return True


def main():
    print("1) Verificando conexion con MongoDB (ping)...")
    if not verificar_conexion():
        print("Prueba fallida: no hay conexion con MongoDB.")
        return 1
    print("   Conexion OK.")

    cliente = obtener_cliente()
    id_insertado = None
    exit_code = 0

    try:
        print("2) Verificando que la base de datos y la coleccion existan...")
        if not verificar_base_y_coleccion(cliente):
            exit_code = 1
        else:
            print("   Base de datos y coleccion encontradas.")
            coleccion = obtener_coleccion_sensores()

            print("3) Insertando documento de prueba...")
            resultado_insercion = coleccion.insert_one(DOCUMENTO_PRUEBA)
            id_insertado = resultado_insercion.inserted_id
            print(f"   Documento insertado con _id = {id_insertado}")

            print("4) Consultando el documento insertado por su _id...")
            documento_leido = coleccion.find_one({"_id": id_insertado})

            if documento_leido is None:
                print("Error: no se pudo encontrar el documento recien insertado.")
                exit_code = 1
            else:
                print("5) Comparando los campos leidos contra los valores originales...")
                campos_coinciden = (
                    documento_leido.get("tipo") == DOCUMENTO_PRUEBA["tipo"]
                    and documento_leido.get("valor") == DOCUMENTO_PRUEBA["valor"]
                    and documento_leido.get("ubicacion") == DOCUMENTO_PRUEBA["ubicacion"]
                    and documento_leido.get("fecha") == DOCUMENTO_PRUEBA["fecha"]
                )
                if not campos_coinciden:
                    print("Error: los campos leidos no coinciden con los valores originales.")
                    print(f"   Esperado: {DOCUMENTO_PRUEBA}")
                    print(f"   Obtenido: {documento_leido}")
                    exit_code = 1
                else:
                    print("   Los campos coinciden correctamente.")

    except PyMongoError as error:
        print(f"Error durante la prueba: {type(error).__name__}: {error}")
        exit_code = 1

    finally:
        # Pase lo que pase (exito o error), intentamos limpiar UNICAMENTE
        # el documento de prueba que creamos en este script.
        if id_insertado is not None:
            print("6) Eliminando el documento de prueba...")
            try:
                coleccion = obtener_coleccion_sensores()
                resultado_borrado = coleccion.delete_one({"_id": id_insertado})
                if resultado_borrado.deleted_count == 1:
                    print("   Documento de prueba eliminado.")
                else:
                    print("   Aviso: el documento de prueba ya no estaba presente.")
            except PyMongoError as error_borrado:
                print(f"   Error al intentar eliminar el documento de prueba: {error_borrado}")
                exit_code = 1

            print("7) Verificando que el documento de prueba ya no exista...")
            try:
                coleccion = obtener_coleccion_sensores()
                documento_restante = coleccion.find_one({"_id": id_insertado})
                if documento_restante is not None:
                    print("Error: el documento de prueba sigue existiendo despues de la limpieza.")
                    exit_code = 1
                else:
                    print("   Confirmado: el documento de prueba ya no existe.")
            except PyMongoError as error_verificacion:
                print(f"   Error al verificar la limpieza: {error_verificacion}")
                exit_code = 1

        cliente.close()

    if exit_code == 0:
        print("Prueba de conexion y persistencia EXITOSA.")
    else:
        print("Prueba de conexion y persistencia FALLIDA.")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
