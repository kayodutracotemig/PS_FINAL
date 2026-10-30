from models.usuario_model import Usuario
from models.jogo_model import Jogo

class ProximosJogosService:
    def executar(self, token):
        usuario = Usuario.buscar_por_token(token)

        if not usuario:
            raise ValueError('Sessão inválida. Faça login novamente.')

        if not usuario.time_id:
            raise ValueError('Você precisa selecionar um time antes de ver os jogos.')

        jogos = Jogo.listar_proximos_por_time(usuario.time_id, limite=10)

        resultado = []
        for jogo in jogos:
            resultado.append({
                'id': jogo.id,
                'adversario': jogo.adversario,
                'data_hora': jogo.data_hora.isoformat(),
                'local': jogo.local,
                'estadio': jogo.estadio,
                'campeonato': jogo.campeonato,
                'fase': jogo.fase
            })


        return resultado