from models.usuario_model import Usuario
from models.time_model import Time

class MudarTimeService:
    def executar(self, token, novo_time_id):
        usuario = Usuario.buscar_por_token(token)

        if not usuario:
            raise ValueError('Sessão inválida. Faça login novamente.')

        if not usuario.time_id:
            raise ValueError('Você ainda não selecionou um time. Use a seleção de time primeiro.')

        novo_time = Time.buscar_por_id(novo_time_id)

        if not novo_time:
            raise ValueError('Time não encontrado.')

        if usuario.time_id == novo_time.id:
            raise ValueError('Você já está torcendo para este time.')

        usuario.time_id = novo_time.id
        usuario.atualizar()

        return usuario, novo_time