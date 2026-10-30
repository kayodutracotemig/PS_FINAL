from models.usuario_model import Usuario
from models.jogo_model import Jogo
from models.avaliacao_model import AvaliacaoJogo

class ListarJogosPassadosService:
    def executar(self, token):
        usuario = Usuario.buscar_por_token(token)
        if not usuario:
            raise ValueError('Sessão inválida. Faça login novamente.')
        if not usuario.time_id:
            return []

        jogos = Jogo.listar_passados_por_time(usuario.time_id)

        resultado = []
        for jogo in jogos:
            avaliacao = AvaliacaoJogo.buscar(usuario.id, jogo.id)
            resultado.append({
                'id': jogo.id,
                'adversario': jogo.adversario,
                'data_hora': jogo.data_hora.strftime('%d/%m/%Y %H:%M'),
                'local': jogo.local,
                'estadio': jogo.estadio,
                'campeonato': jogo.campeonato,
                'fase': jogo.fase,
                'ja_avaliado': avaliacao is not None
            })
        return resultado