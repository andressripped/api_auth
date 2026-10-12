"""Punto de entrada de la API. Ejecutar con:  python app.py"""
from flask import Flask, jsonify

from rutas.auth_rutas import crear_blueprint


def crear_app(servicio=None) -> Flask:
    """Fábrica de la aplicación (permite inyectar un servicio en las pruebas)."""
    app = Flask(__name__)

    # Permite que las tildes y la ñ salgan tal cual en el JSON de respuesta,
    # en lugar de escaparse como \u00f3.
    app.json.ensure_ascii = False

    app.register_blueprint(crear_blueprint(servicio))

    @app.get("/")
    def salud():
        """Endpoint de comprobación: confirma que la API está arriba."""
        return jsonify(estado="API de autenticación en línea")

    @app.errorhandler(ConnectionError)
    def error_bd(e):
        """Si MySQL no responde, se devuelve 503 sin exponer detalles internos."""
        return jsonify(error="Servicio de base de datos no disponible."), 503

    return app


if __name__ == "__main__":
    # debug=True solo para clase; en producción se usa un servidor WSGI.
    crear_app().run(host="127.0.0.1", port=5000, debug=True)
