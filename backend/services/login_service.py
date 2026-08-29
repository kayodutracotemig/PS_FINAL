import secrets
from models.usuario_model import Usuario
from werkzeug.security import check_password_hash

class LoginService:
    def executar(self, email, senha):
        usuario = Usuario.buscar_por_email(email)

        if not usuario:
            raise ValueError('Email ou senha inválidos.')

        if not check_password_hash(usuario.senha, senha):
            raise ValueError('Email ou senha inválidos.')

        usuario.token = secrets.token_hex(16)
        usuario.atualizar()

        return usuario