"""Lógica de negocio de autenticación. No conoce Flask ni SQL.

Recibe el DAO por parámetro (inyección de dependencias): así en las pruebas
se puede reemplazar por un DAO falso sin necesidad de una base de datos real.
"""
from config.configuracion import Config
from dao.usuario_dao import UsuarioDAO
from utilidades.seguridad import generar_hash, verificar_clave
from utilidades.validadores import validar_clave, validar_usuario


class ErrorNegocio(Exception):
    """Error controlado. Lleva el código HTTP que la ruta debe devolver."""

    def __init__(self, mensaje: str, codigo: int = 400):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo = codigo


class ServicioAuth:
    def __init__(self, dao=None):
        self.dao = dao or UsuarioDAO()

    def registrar(self, usuario, clave) -> dict:
        """Registra un usuario nuevo. Guarda solo el hash de la contraseña."""
        error = validar_usuario(usuario) or validar_clave(clave)
        if error:
            raise ErrorNegocio(error, 400)

        if self.dao.buscar_por_usuario(usuario):
            raise ErrorNegocio("El usuario ya existe.", 409)

        id_usuario = self.dao.insertar(usuario, generar_hash(clave))
        return {"id_usuario": id_usuario, "usuario": usuario}

    def iniciar_sesion(self, usuario, clave) -> None:
        """Valida credenciales. Si son correctas termina sin error;
        si no, lanza ErrorNegocio 401 (o 423 si el usuario está bloqueado).

        Por seguridad, el mensaje es el mismo si el usuario no existe o si la
        clave es incorrecta: no se revela cuál de los dos falló.
        """
        if not isinstance(usuario, str) or not isinstance(clave, str) \
                or not usuario or not clave:
            raise ErrorNegocio("Error en la autenticación.", 401)

        registro = self.dao.buscar_por_usuario(usuario)
        if registro is None:
            raise ErrorNegocio("Error en la autenticación.", 401)

        if registro["estado"] == "BLOQUEADO":
            raise ErrorNegocio("Usuario bloqueado por intentos fallidos.", 423)

        if not verificar_clave(clave, registro["clave_hash"]):
            self.dao.registrar_fallo(registro["id_usuario"], Config.MAX_INTENTOS)
            raise ErrorNegocio("Error en la autenticación.", 401)

        self.dao.registrar_acceso(registro["id_usuario"])
