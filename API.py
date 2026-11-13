"""
API.py

Aplicacion Flask que expone una API RESTful para gestionar sensores
industriales (temperatura, presion, vibracion) guardados en MongoDB.

"""

import traceback
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from flask import Flask, jsonify, request
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError

import database
import validaciones
from errores import (
    ErrorAPI,
    ErrorValidacion,
    ConflictoMultiplesSensores,
    SensorNoEncontrado,
    TipoContenidoNoSoportado,
)


def crear_app(nombre_bd=None):
 
    app = Flask(__name__)
    app.config["MONGO_DB_NAME"] = nombre_bd or database.MONGO_DB_NAME

    def coleccion_sensores():
        """Devuelve la coleccion 'sensores' de la base configurada en esta app."""
        return database.obtener_coleccion_sensores(app.config["MONGO_DB_NAME"])

    def serializar_sensor(documento):
        resultado = dict(documento)
        resultado["_id"] = str(resultado["_id"])

        fecha = resultado.get("fecha")
        if isinstance(fecha, datetime):
            if fecha.tzinfo is None:
                fecha = fecha.replace(tzinfo=timezone.utc)
            resultado["fecha"] = fecha.astimezone(timezone.utc).isoformat().replace(
                "+00:00", "Z"
            )
        return resultado

    def obtener_json_body():
        content_type = request.content_type or ""
        if "application/json" not in content_type:
            raise TipoContenidoNoSoportado(
                "El Content-Type debe ser 'application/json'."
            )

        datos = request.get_json(silent=True)
        if datos is None:
            raise ErrorValidacion("El cuerpo de la solicitud debe ser JSON valido.")
        return datos

    def validar_object_id(sensor_id):
        try:
            return ObjectId(sensor_id)
        except (InvalidId, TypeError):
            raise ErrorValidacion(f"El identificador '{sensor_id}' no es un ObjectId valido.")

    def obtener_sensor_por_id(object_id):
        sensor = coleccion_sensores().find_one({"_id": object_id})
        if sensor is None:
            raise SensorNoEncontrado(f"No existe ningun sensor con id '{object_id}'.")
        return sensor

    def obtener_sensor_unico_por_tipo(tipo):
        coleccion = coleccion_sensores()
        cantidad = coleccion.count_documents({"tipo": tipo})

        if cantidad == 0:
            raise SensorNoEncontrado(f"No existe ningun sensor de tipo '{tipo}'.")
        if cantidad > 1:
            raise ConflictoMultiplesSensores(
                f"Existen {cantidad} sensores de tipo '{tipo}'. "
                "Usa /sensores/id/<id> para indicar cual quieres modificar o eliminar."
            )
        return coleccion.find_one({"tipo": tipo})

    # ------------------------------------------------------------------
    # Endpoints
    # ------------------------------------------------------------------

    @app.route("/sensores/", methods=["POST"])
    def crear_sensor():
        datos = obtener_json_body()
        documento = validaciones.validar_datos_creacion(datos)

        resultado = coleccion_sensores().insert_one(documento)
        documento["_id"] = resultado.inserted_id

        return jsonify(serializar_sensor(documento)), 201

    @app.route("/sensores/", methods=["GET"])
    def listar_sensores():
        filtro = {}
        tipo_solicitado = request.args.get("tipo")
        if tipo_solicitado is not None:
            filtro["tipo"] = validaciones.validar_tipo(tipo_solicitado)

        sensores = [serializar_sensor(doc) for doc in coleccion_sensores().find(filtro)]
        return jsonify(sensores), 200

    @app.route("/sensores/<tipo>", methods=["PUT"])
    def actualizar_sensor_por_tipo(tipo):
        tipo = validaciones.validar_tipo(tipo)
        sensor_actual = obtener_sensor_unico_por_tipo(tipo)

        datos = obtener_json_body()
        actualizacion = validaciones.validar_datos_actualizacion(datos, tipo)

        coleccion_sensores().update_one({"_id": sensor_actual["_id"]}, {"$set": actualizacion})
        sensor_actualizado = coleccion_sensores().find_one({"_id": sensor_actual["_id"]})

        return jsonify(serializar_sensor(sensor_actualizado)), 200

    @app.route("/sensores/<tipo>", methods=["DELETE"])
    def eliminar_sensor_por_tipo(tipo):
        tipo = validaciones.validar_tipo(tipo)
        sensor = obtener_sensor_unico_por_tipo(tipo)

        coleccion_sensores().delete_one({"_id": sensor["_id"]})

        return jsonify({
            "mensaje": f"Sensor de tipo '{tipo}' eliminado correctamente.",
            "_id": str(sensor["_id"]),
        }), 200

    @app.route("/sensores/id/<sensor_id>", methods=["PUT"])
    def actualizar_sensor_por_id(sensor_id):
        object_id = validar_object_id(sensor_id)
        sensor_actual = obtener_sensor_por_id(object_id)

        datos = obtener_json_body()
        actualizacion = validaciones.validar_datos_actualizacion(datos, sensor_actual["tipo"])

        coleccion_sensores().update_one({"_id": object_id}, {"$set": actualizacion})
        sensor_actualizado = coleccion_sensores().find_one({"_id": object_id})

        return jsonify(serializar_sensor(sensor_actualizado)), 200

    @app.route("/sensores/id/<sensor_id>", methods=["DELETE"])
    def eliminar_sensor_por_id(sensor_id):
        object_id = validar_object_id(sensor_id)
        sensor = obtener_sensor_por_id(object_id)

        coleccion_sensores().delete_one({"_id": object_id})

        return jsonify({
            "mensaje": "Sensor eliminado correctamente.",
            "_id": str(object_id),
        }), 200


    @app.errorhandler(ErrorAPI)
    def manejar_error_api(error):
        return jsonify({"error": error.mensaje}), error.codigo_http

    @app.errorhandler(404)
    def manejar_404(error):
        return jsonify({"error": "Recurso no encontrado."}), 404

    @app.errorhandler(405)
    def manejar_405(error):
        return jsonify({"error": "Metodo no permitido para esta URL."}), 405

    @app.errorhandler(ServerSelectionTimeoutError)
    def manejar_mongo_no_disponible(error):
        print(f"MongoDB no disponible: {error}")
        return jsonify({
            "error": "El servicio de base de datos no esta disponible en este momento."
        }), 503

    @app.errorhandler(PyMongoError)
    def manejar_error_mongo(error):
        print(f"Error de MongoDB: {type(error).__name__}: {error}")
        return jsonify({"error": "Ocurrio un error al comunicarse con la base de datos."}), 500

    @app.errorhandler(Exception)
    def manejar_error_inesperado(error):
        print(f"Error inesperado: {type(error).__name__}: {error}")
        traceback.print_exc()
        return jsonify({"error": "Error interno inesperado."}), 500

    return app

app = crear_app()


if __name__ == "__main__":
    app.run(debug=True)
