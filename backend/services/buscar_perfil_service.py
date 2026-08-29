from models.usuario_model import Usuario
from models.time_model import Time

class BuscarPerfilService:
    def executar(self, token):
        usuario = Usuario.buscar_por_token(token)

        if not usuario:
            raise ValueError('Sessão inválida. Faça login novamente.')

        time = None
        if usuario.time_id:
            time = Time.buscar_por_id(usuario.time_id)

        return usuario, time