"""
tests/test_api.py

Pruebas de INTEGRACION de la API de sensores: usan pytest, el cliente de
pruebas de Flask, y una base de datos de MongoDB real (local).

Importante: estas pruebas usan una base de datos de pruebas separada
('monitoreo_industrial_test'), nunca la base de datos real
('monitoreo_industrial'). Al final de cada prueba se elimina por completo
la base de datos de pruebas para dejar todo limpio.

Para las pruebas UNITARIAS que simulan fallos de MongoDB con mocks (sin
necesitar un servidor real), ver tests/test_errores_mongo.py.
"""

import os
import sys

import pytest

# Para poder importar los modulos del proyecto (API, database) estando
# dentro de la carpeta tests/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database
from API import crear_app

NOMBRE_BD_PRUEBAS = "monitoreo_industrial_test"


@pytest.fixture()
def cliente():
    """
    Crea una app Flask que apunta a la base de datos de pruebas y entrega
    un cliente de pruebas (flask test client). Al terminar cada prueba,
    se elimina la base de datos de pruebas completa.
    """
    app = crear_app(nombre_bd=NOMBRE_BD_PRUEBAS)
    app.testing = True

    with app.test_client() as test_client:
        yield test_client

    # Limpieza: solo se borra la base de datos de pruebas, nunca la real.
    database.obtener_cliente().drop_database(NOMBRE_BD_PRUEBAS)


def sensor_de_ejemplo(tipo="temperatura", valor=25.5, ubicacion="Planta A",
                       fecha="2026-11-13T10:30:00Z"):
    """Genera un diccionario con los datos de un sensor valido, para usar en las pruebas."""
    return {"tipo": tipo, "valor": valor, "ubicacion": ubicacion, "fecha": fecha}


# ---------------------------------------------------------------------
# POST /sensores/
# ---------------------------------------------------------------------

def test_post_crea_sensor(cliente):
    respuesta = cliente.post("/sensores/", json=sensor_de_ejemplo())
    cuerpo = respuesta.get_json()

    assert respuesta.status_code == 201
    assert cuerpo["tipo"] == "temperatura"
    assert cuerpo["valor"] == 25.5
    assert cuerpo["ubicacion"] == "Planta A"
    assert "_id" in cuerpo
    assert cuerpo["fecha"] == "2026-11-13T10:30:00Z"


def test_post_falta_un_campo_devuelve_400(cliente):
    datos = sensor_de_ejemplo()
    del datos["ubicacion"]

    respuesta = cliente.post("/sensores/", json=datos)

    assert respuesta.status_code == 400
    assert "error" in respuesta.get_json()


def test_post_valor_fuera_de_rango_devuelve_400(cliente):
    # El rango de temperatura es -10 a 100; 500 esta fuera de rango.
    datos = sensor_de_ejemplo(tipo="temperatura", valor=500)

    respuesta = cliente.post("/sensores/", json=datos)

    assert respuesta.status_code == 400


def test_post_content_type_incorrecto_devuelve_415(cliente):
    respuesta = cliente.post("/sensores/", data="esto no es json", content_type="text/plain")

    assert respuesta.status_code == 415


# ---------------------------------------------------------------------
# GET /sensores/ (general y por tipo)
# ---------------------------------------------------------------------

def test_get_general_sin_datos_devuelve_lista_vacia(cliente):
    respuesta = cliente.get("/sensores/")

    assert respuesta.status_code == 200
    assert respuesta.get_json() == []


def test_get_general_devuelve_todos_los_sensores(cliente):
    cliente.post("/sensores/", json=sensor_de_ejemplo(tipo="temperatura"))
    cliente.post("/sensores/", json=sensor_de_ejemplo(tipo="presion", valor=120))

    respuesta = cliente.get("/sensores/")
    cuerpo = respuesta.get_json()

    assert respuesta.status_code == 200
    assert len(cuerpo) == 2


def test_get_por_tipo_filtra_correctamente(cliente):
    cliente.post("/sensores/", json=sensor_de_ejemplo(tipo="temperatura"))
    cliente.post("/sensores/", json=sensor_de_ejemplo(tipo="presion", valor=120, ubicacion="Planta B"))

    respuesta = cliente.get("/sensores/?tipo=presion")
    cuerpo = respuesta.get_json()

    assert respuesta.status_code == 200
    assert len(cuerpo) == 1
    assert cuerpo[0]["tipo"] == "presion"


def test_get_por_tipo_invalido_devuelve_400(cliente):
    respuesta = cliente.get("/sensores/?tipo=humedad")

    assert respuesta.status_code == 400


# ---------------------------------------------------------------------
# PUT y DELETE /sensores/<tipo>
# ---------------------------------------------------------------------

def test_put_por_tipo_actualiza_el_sensor(cliente):
    cliente.post("/sensores/", json=sensor_de_ejemplo())

    respuesta = cliente.put("/sensores/temperatura", json={"valor": 30})
    cuerpo = respuesta.get_json()

    assert respuesta.status_code == 200
    assert cuerpo["valor"] == 30
    assert cuerpo["tipo"] == "temperatura"


def test_put_por_tipo_sin_sensores_devuelve_404(cliente):
    respuesta = cliente.put("/sensores/vibracion", json={"valor": 1})

    assert respuesta.status_code == 404


def test_put_por_tipo_con_valor_fuera_de_rango_devuelve_400(cliente):
    cliente.post("/sensores/", json=sensor_de_ejemplo(tipo="vibracion", valor=1))

    # El rango de vibracion es 0 a 5; 10 esta fuera de rango.
    respuesta = cliente.put("/sensores/vibracion", json={"valor": 10})

    assert respuesta.status_code == 400


def test_put_por_tipo_no_permite_cambiar_tipo(cliente):
    cliente.post("/sensores/", json=sensor_de_ejemplo())

    respuesta = cliente.put("/sensores/temperatura", json={"tipo": "presion"})

    assert respuesta.status_code == 400


def test_delete_por_tipo_elimina_el_sensor(cliente):
    cliente.post("/sensores/", json=sensor_de_ejemplo())

    respuesta = cliente.delete("/sensores/temperatura")

    assert respuesta.status_code == 200
    assert cliente.get("/sensores/?tipo=temperatura").get_json() == []


def test_delete_por_tipo_sin_sensores_devuelve_404(cliente):
    respuesta = cliente.delete("/sensores/presion")

    assert respuesta.status_code == 404


# ---------------------------------------------------------------------
# Multiples sensores del mismo tipo -> 409 Conflict
# ---------------------------------------------------------------------

def test_put_con_varios_sensores_del_mismo_tipo_devuelve_409(cliente):
    cliente.post("/sensores/", json=sensor_de_ejemplo(tipo="temperatura", ubicacion="Planta A"))
    cliente.post("/sensores/", json=sensor_de_ejemplo(tipo="temperatura", ubicacion="Planta B"))

    respuesta = cliente.put("/sensores/temperatura", json={"valor": 50})

    assert respuesta.status_code == 409
    # Confirmamos que ningun documento fue modificado.
    cuerpo = cliente.get("/sensores/?tipo=temperatura").get_json()
    assert len(cuerpo) == 2
    assert {s["valor"] for s in cuerpo} == {25.5}


def test_delete_con_varios_sensores_del_mismo_tipo_devuelve_409(cliente):
    cliente.post("/sensores/", json=sensor_de_ejemplo(tipo="presion", ubicacion="Planta A", valor=100))
    cliente.post("/sensores/", json=sensor_de_ejemplo(tipo="presion", ubicacion="Planta B", valor=200))

    respuesta = cliente.delete("/sensores/presion")

    assert respuesta.status_code == 409
    # Confirmamos que ningun documento fue eliminado.
    cuerpo = cliente.get("/sensores/?tipo=presion").get_json()
    assert len(cuerpo) == 2


# ---------------------------------------------------------------------
# PUT y DELETE /sensores/id/<sensor_id>
# ---------------------------------------------------------------------

def test_put_por_id_actualiza_solo_ese_sensor(cliente):
    cliente.post("/sensores/", json=sensor_de_ejemplo(tipo="temperatura", ubicacion="Planta A"))
    creado = cliente.post(
        "/sensores/", json=sensor_de_ejemplo(tipo="temperatura", ubicacion="Planta B")
    ).get_json()

    respuesta = cliente.put(f"/sensores/id/{creado['_id']}", json={"ubicacion": "Planta C"})
    cuerpo = respuesta.get_json()

    assert respuesta.status_code == 200
    assert cuerpo["ubicacion"] == "Planta C"
    assert cuerpo["tipo"] == "temperatura"

    # El otro sensor del mismo tipo no debe haberse modificado.
    todos = cliente.get("/sensores/?tipo=temperatura").get_json()
    ubicaciones = {s["ubicacion"] for s in todos}
    assert ubicaciones == {"Planta A", "Planta C"}


def test_put_por_id_no_permite_cambiar_tipo(cliente):
    creado = cliente.post("/sensores/", json=sensor_de_ejemplo()).get_json()

    respuesta = cliente.put(f"/sensores/id/{creado['_id']}", json={"tipo": "vibracion"})

    assert respuesta.status_code == 400


def test_put_por_id_formato_invalido_devuelve_400(cliente):
    respuesta = cliente.put("/sensores/id/no-es-un-id-valido", json={"valor": 1})

    assert respuesta.status_code == 400


def test_put_por_id_inexistente_devuelve_404(cliente):
    id_inexistente = "000000000000000000000000"  # 24 caracteres hex validos, pero no existe

    respuesta = cliente.put(f"/sensores/id/{id_inexistente}", json={"valor": 1})

    assert respuesta.status_code == 404


def test_delete_por_id_elimina_solo_ese_sensor(cliente):
    primero = cliente.post(
        "/sensores/", json=sensor_de_ejemplo(tipo="presion", ubicacion="Planta A", valor=100)
    ).get_json()
    cliente.post("/sensores/", json=sensor_de_ejemplo(tipo="presion", ubicacion="Planta B", valor=200))

    respuesta = cliente.delete(f"/sensores/id/{primero['_id']}")

    assert respuesta.status_code == 200

    restantes = cliente.get("/sensores/?tipo=presion").get_json()
    assert len(restantes) == 1
    assert restantes[0]["ubicacion"] == "Planta B"


def test_delete_por_id_inexistente_devuelve_404(cliente):
    id_inexistente = "000000000000000000000000"  # 24 caracteres hex validos, pero no existe

    respuesta = cliente.delete(f"/sensores/id/{id_inexistente}")

    assert respuesta.status_code == 404


# =======================================================================
# FASE 4 — Pruebas ampliadas (auditoria de validaciones y casos limite)
# =======================================================================
#
# Todo lo que sigue tambien son pruebas de INTEGRACION (MongoDB real) y
# usan la misma fixture 'cliente' de arriba. Se agrupan aparte solo para
# que se note que fueron incorporadas en la auditoria de la Fase 4.

# --- Validacion de 'tipo' ------------------------------------------------

@pytest.mark.parametrize("tipo_invalido", [
    None, "", "   ", 123, True, ["temperatura"], {"a": 1}, "TEMPERATURA", "humedad",
])
def test_post_tipo_invalido(cliente, tipo_invalido):
    respuesta = cliente.post("/sensores/", json=sensor_de_ejemplo(tipo=tipo_invalido))

    assert respuesta.status_code == 400


def test_get_por_tipo_invalido_en_query_string_tambien_rechaza(cliente):
    # El mismo validar_tipo() se usa en POST y en el filtro de GET; aqui se
    # confirma que el comportamiento es consistente entre ambos.
    respuesta = cliente.get("/sensores/?tipo=HUMEDAD")

    assert respuesta.status_code == 400


# --- Limites de 'valor' (inclusivos) ----------------------------------

@pytest.mark.parametrize("tipo, limite", [
    ("temperatura", -10), ("temperatura", 100),
    ("presion", 0), ("presion", 500),
    ("vibracion", 0), ("vibracion", 5),
])
def test_post_valor_en_el_limite_es_valido(cliente, tipo, limite):
    respuesta = cliente.post("/sensores/", json=sensor_de_ejemplo(tipo=tipo, valor=limite))

    assert respuesta.status_code == 201
    assert respuesta.get_json()["valor"] == float(limite)


@pytest.mark.parametrize("tipo, fuera_de_rango", [
    ("temperatura", -10.01), ("temperatura", 100.01),
    ("presion", -0.01), ("presion", 500.01),
    ("vibracion", -0.01), ("vibracion", 5.01),
])
def test_post_valor_fuera_del_limite_es_invalido(cliente, tipo, fuera_de_rango):
    respuesta = cliente.post("/sensores/", json=sensor_de_ejemplo(tipo=tipo, valor=fuera_de_rango))

    assert respuesta.status_code == 400


# --- Tipos de dato incorrectos para 'valor' ---------------------------

@pytest.mark.parametrize("valor_invalido", ["25", True, False, None, [1, 2], {"a": 1}])
def test_post_valor_con_tipo_de_dato_incorrecto(cliente, valor_invalido):
    respuesta = cliente.post("/sensores/", json=sensor_de_ejemplo(valor=valor_invalido))

    assert respuesta.status_code == 400


@pytest.mark.parametrize("token_crudo", ["NaN", "Infinity", "-Infinity"])
def test_post_valor_no_finito_es_invalido(cliente, token_crudo):
    # NaN/Infinity no son JSON estandar, pero el modulo json de Python los
    # acepta por defecto; por eso se envian como texto crudo (no con
    # json=...) para simular ese caso real.
    cuerpo = (
        '{"tipo":"temperatura","valor":%s,"ubicacion":"Planta A",'
        '"fecha":"2026-11-13T10:30:00Z"}' % token_crudo
    )
    respuesta = cliente.post("/sensores/", data=cuerpo, content_type="application/json")

    assert respuesta.status_code == 400


# --- Validacion de 'ubicacion' ----------------------------------------

@pytest.mark.parametrize("ubicacion_invalida", ["", "   ", None, 123, [1, 2], {"a": 1}])
def test_post_ubicacion_invalida(cliente, ubicacion_invalida):
    respuesta = cliente.post("/sensores/", json=sensor_de_ejemplo(ubicacion=ubicacion_invalida))

    assert respuesta.status_code == 400


def test_post_ubicacion_normaliza_espacios_exteriores(cliente):
    respuesta = cliente.post("/sensores/", json=sensor_de_ejemplo(ubicacion="   Planta Z   "))

    assert respuesta.status_code == 201
    assert respuesta.get_json()["ubicacion"] == "Planta Z"


# --- Validacion de 'fecha' ---------------------------------------------

@pytest.mark.parametrize("fecha_invalida", [
    "", None, "no-es-fecha", "2026-13-01T00:00:00Z", "2026-02-30T00:00:00Z",
    123, ["2026-11-13"],
])
def test_post_fecha_invalida(cliente, fecha_invalida):
    respuesta = cliente.post("/sensores/", json=sensor_de_ejemplo(fecha=fecha_invalida))

    assert respuesta.status_code == 400


def test_post_fecha_solo_con_dia_es_valida_iso8601(cliente):
    # "2026-11-13" es ISO 8601 valido (fecha sin hora); se interpreta como
    # medianoche UTC. Esto es un comportamiento esperado, no un error.
    respuesta = cliente.post("/sensores/", json=sensor_de_ejemplo(fecha="2026-11-13"))

    assert respuesta.status_code == 201
    assert respuesta.get_json()["fecha"] == "2026-11-13T00:00:00Z"


@pytest.mark.parametrize("fecha_entrada", [
    "2026-11-13T10:30:00Z",
    "2026-11-13T05:30:00-05:00",  # mismo instante que el de arriba, con offset
    "2026-11-13T10:30:00",  # sin zona horaria: se asume UTC
])
def test_post_fecha_se_normaliza_a_utc(cliente, fecha_entrada):
    respuesta = cliente.post("/sensores/", json=sensor_de_ejemplo(fecha=fecha_entrada))

    assert respuesta.status_code == 201
    assert respuesta.get_json()["fecha"] == "2026-11-13T10:30:00Z"


def test_post_fecha_mantiene_precision_de_milisegundos(cliente):
    respuesta = cliente.post(
        "/sensores/", json=sensor_de_ejemplo(fecha="2026-11-13T10:30:00.123456Z")
    )

    assert respuesta.status_code == 201
    # Los microsegundos (123456) se redondean a milisegundos (123000),
    # que es la precision maxima que MongoDB puede almacenar.
    assert respuesta.get_json()["fecha"] == "2026-11-13T10:30:00.123000Z"


# --- Validacion del cuerpo JSON ----------------------------------------

def test_post_cuerpo_vacio_devuelve_400(cliente):
    respuesta = cliente.post("/sensores/", data="", content_type="application/json")

    assert respuesta.status_code == 400


def test_post_json_malformado_devuelve_400(cliente):
    respuesta = cliente.post("/sensores/", data="{esto no es json valido", content_type="application/json")

    assert respuesta.status_code == 400


def test_post_array_en_lugar_de_objeto_devuelve_400(cliente):
    respuesta = cliente.post("/sensores/", data="[1, 2, 3]", content_type="application/json")

    assert respuesta.status_code == 400


def test_post_campo_desconocido_devuelve_400(cliente):
    datos = sensor_de_ejemplo()
    datos["campo_extra"] = "no deberia estar aqui"

    respuesta = cliente.post("/sensores/", json=datos)

    assert respuesta.status_code == 400


def test_post_content_type_con_charset_se_acepta(cliente):
    # "application/json; charset=utf-8" tambien debe considerarse JSON valido.
    import json as json_module
    respuesta = cliente.post(
        "/sensores/",
        data=json_module.dumps(sensor_de_ejemplo()),
        content_type="application/json; charset=utf-8",
    )

    assert respuesta.status_code == 201


# --- PUT: cuerpo vacio y solicitudes invalidas que no deben modificar datos --

def test_put_con_cuerpo_vacio_devuelve_400(cliente):
    cliente.post("/sensores/", json=sensor_de_ejemplo(tipo="vibracion", valor=1))

    respuesta = cliente.put("/sensores/vibracion", json={})

    assert respuesta.status_code == 400


def test_put_invalido_no_modifica_el_documento_existente(cliente):
    cliente.post("/sensores/", json=sensor_de_ejemplo(tipo="vibracion", valor=1))

    # Intento invalido: el valor queda fuera del rango permitido (0 a 5).
    respuesta = cliente.put("/sensores/vibracion", json={"valor": 999})
    assert respuesta.status_code == 400

    # El documento original no debe haber cambiado.
    sensor_actual = cliente.get("/sensores/?tipo=vibracion").get_json()[0]
    assert sensor_actual["valor"] == 1.0


def test_conflicto_409_no_modifica_ni_elimina_ningun_documento(cliente):
    cliente.post("/sensores/", json=sensor_de_ejemplo(tipo="presion", valor=100, ubicacion="Planta A"))
    cliente.post("/sensores/", json=sensor_de_ejemplo(tipo="presion", valor=200, ubicacion="Planta B"))

    respuesta_put = cliente.put("/sensores/presion", json={"valor": 300})
    assert respuesta_put.status_code == 409

    respuesta_delete = cliente.delete("/sensores/presion")
    assert respuesta_delete.status_code == 409

    # Los dos documentos originales deben seguir exactamente iguales.
    sensores = sorted(cliente.get("/sensores/?tipo=presion").get_json(), key=lambda s: s["valor"])
    assert [s["valor"] for s in sensores] == [100.0, 200.0]
    assert [s["ubicacion"] for s in sensores] == ["Planta A", "Planta B"]


# --- Identificadores de MongoDB invalidos (variantes) ------------------

@pytest.mark.parametrize("id_invalido", [
    "abc",                                     # muy corto
    "123",                                     # muy corto
    "zzzzzzzzzzzzzzzzzzzzzzzz",                # longitud correcta, no es hexadecimal
    "6af76af76af76af76af76af76af76af76af76af7",  # demasiado largo
    "6af773f6a0e01f88bb30f19Z",                 # 24 caracteres, pero 'Z' no es hex
])
def test_put_por_id_formatos_invalidos_variados(cliente, id_invalido):
    respuesta = cliente.put(f"/sensores/id/{id_invalido}", json={"valor": 1})

    assert respuesta.status_code == 400


# --- Metodos HTTP no permitidos -----------------------------------------

def test_metodo_no_permitido_en_sensores_sin_tipo(cliente):
    respuesta = cliente.delete("/sensores/")

    assert respuesta.status_code == 405


def test_metodo_no_permitido_en_sensores_id(cliente):
    creado = cliente.post("/sensores/", json=sensor_de_ejemplo()).get_json()

    respuesta = cliente.get(f"/sensores/id/{creado['_id']}")

    assert respuesta.status_code == 405


def test_ruta_inexistente_devuelve_404(cliente):
    respuesta = cliente.get("/esta-ruta-no-existe")

    assert respuesta.status_code == 404
