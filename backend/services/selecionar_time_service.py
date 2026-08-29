from models.usuario_model import Usuario
from models.time_model import Time

class SelecionarTimeService:
    def executar(self, token, time_id):
        usuario = Usuario.buscar_por_token(token)

        if not usuario:
            raise ValueError('Sessão inválida. Faça login novamente.')

        time = Time.buscar_por_id(time_id)

        if not time:
            raise ValueError('Time não encontrado.')

        usuario.time_id = time.id
        usuario.atualizar()

        return usuario, time