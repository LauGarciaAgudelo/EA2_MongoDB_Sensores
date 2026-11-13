"""
tests/test_errores_mongo.py

Pruebas UNITARIAS (no de integración) que verifican el manejo de errores
cuando MongoDB falla. En vez de detener el servicio real de MongoDB, se
usa "monkeypatch" (inyección de dependencias controlada) para reemplazar
la colección de sensores por un doble de prueba (`unittest.mock.MagicMock`)
que simula distintos tipos de fallo.

Estas pruebas NO necesitan que MongoDB esté corriendo: todo lo que llega
a "tocar la base de datos" está reemplazado por el mock.
"""

import os
import sys

import pytest
from bson import ObjectId
from pymongo.errors import OperationFailure, PyMongoError, ServerSelectionTimeoutError

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database
from API import crear_app


@pytest.fixture()
def cliente_con_mongo_simulado(monkeypatch):
    """
    Entrega (cliente_de_pruebas, coleccion_falsa). 'coleccion_falsa' es un
    MagicMock que reemplaza la coleccion real de MongoDB: se puede
    configurar para que sus metodos (find, insert_one, etc.) lancen la
    excepcion que se quiera simular.
    """
    from unittest.mock import MagicMock

    coleccion_falsa = MagicMock()
    monkeypatch.setattr(
        database, "obtener_coleccion_sensores", lambda *args, **kwargs: coleccion_falsa
    )

    app = crear_app(nombre_bd="no-se-usa-porque-esta-simulado")
    app.testing = True

    with app.test_client() as test_client:
        yield test_client, coleccion_falsa


SENSOR_VALIDO = {
    "tipo": "temperatura",
    "valor": 25.5,
    "ubicacion": "Planta A",
    "fecha": "2026-11-13T10:30:00Z",
}


# --- MongoDB no disponible / timeout -> 503 ----------------------------

def test_get_devuelve_503_si_mongodb_no_responde(cliente_con_mongo_simulado):
    cliente, coleccion_falsa = cliente_con_mongo_simulado
    coleccion_falsa.find.side_effect = ServerSelectionTimeoutError("tiempo de espera agotado")

    respuesta = cliente.get("/sensores/")

    assert respuesta.status_code == 503
    assert "error" in respuesta.get_json()


def test_post_devuelve_503_si_mongodb_no_responde(cliente_con_mongo_simulado):
    cliente, coleccion_falsa = cliente_con_mongo_simulado
    coleccion_falsa.insert_one.side_effect = ServerSelectionTimeoutError("tiempo de espera agotado")

    respuesta = cliente.post("/sensores/", json=SENSOR_VALIDO)

    assert respuesta.status_code == 503


def test_put_por_tipo_devuelve_503_si_mongodb_no_responde(cliente_con_mongo_simulado):
    cliente, coleccion_falsa = cliente_con_mongo_simulado
    coleccion_falsa.count_documents.side_effect = ServerSelectionTimeoutError("tiempo de espera agotado")

    respuesta = cliente.put("/sensores/temperatura", json={"valor": 1})

    assert respuesta.status_code == 503


# --- Errores de lectura/escritura de PyMongo (no de disponibilidad) -> 500 --

def test_get_devuelve_500_si_falla_la_lectura(cliente_con_mongo_simulado):
    cliente, coleccion_falsa = cliente_con_mongo_simulado
    coleccion_falsa.find.side_effect = OperationFailure("fallo de lectura simulado")

    respuesta = cliente.get("/sensores/")

    assert respuesta.status_code == 500


def test_post_devuelve_500_si_falla_la_escritura(cliente_con_mongo_simulado):
    cliente, coleccion_falsa = cliente_con_mongo_simulado
    coleccion_falsa.insert_one.side_effect = OperationFailure("fallo de escritura simulado")

    respuesta = cliente.post("/sensores/", json=SENSOR_VALIDO)

    assert respuesta.status_code == 500


def test_delete_por_id_devuelve_500_si_falla_la_escritura(cliente_con_mongo_simulado):
    cliente, coleccion_falsa = cliente_con_mongo_simulado
    # find_one debe funcionar (para encontrar el sensor); delete_one falla.
    coleccion_falsa.find_one.return_value = {
        "_id": ObjectId("000000000000000000000000"),
        "tipo": "temperatura",
        "valor": 1,
        "ubicacion": "X",
    }
    coleccion_falsa.delete_one.side_effect = PyMongoError("fallo de escritura simulado")

    respuesta = cliente.delete("/sensores/id/000000000000000000000000")

    assert respuesta.status_code == 500


# --- Excepciones totalmente inesperadas (bugs) -> 500 genérico ---------

def test_error_inesperado_devuelve_500_sin_exponer_detalle(cliente_con_mongo_simulado, capsys):
    cliente, coleccion_falsa = cliente_con_mongo_simulado
    coleccion_falsa.find.side_effect = RuntimeError(
        "detalle interno que NUNCA deberia llegar al cliente"
    )

    respuesta = cliente.get("/sensores/")

    assert respuesta.status_code == 500
    cuerpo = respuesta.get_json()
    assert cuerpo == {"error": "Error interno inesperado."}
    # El detalle real del error no debe aparecer en la respuesta al cliente...
    assert "detalle interno" not in str(cuerpo)

    # ...pero si debe quedar registrado en la consola del servidor, para
    # que se pueda depurar. Esto cumple "registrar errores tecnicos en el
    # servidor" sin "ocultar" el error (solo no se expone al cliente).
    salida_consola = capsys.readouterr().out
    assert "RuntimeError" in salida_consola


def test_error_de_mongo_no_expone_uri_ni_credenciales_al_cliente(cliente_con_mongo_simulado, capsys):
    cliente, coleccion_falsa = cliente_con_mongo_simulado
    mensaje_con_credenciales = "mongodb://usuario:clave-secreta@localhost:27017/: Connection refused"
    coleccion_falsa.find.side_effect = ServerSelectionTimeoutError(mensaje_con_credenciales)

    respuesta = cliente.get("/sensores/")

    assert respuesta.status_code == 503
    cuerpo = respuesta.get_json()
    # La respuesta al cliente debe ser un mensaje generico, nunca la URI real.
    assert "usuario" not in str(cuerpo)
    assert "clave-secreta" not in str(cuerpo)

    # El detalle (en este caso simulado) si puede quedar en la consola del
    # servidor, que no es visible para un cliente externo de la API.
    salida_consola = capsys.readouterr().out
    assert "clave-secreta" in salida_consola
