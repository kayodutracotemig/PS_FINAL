from models.usuario_model import Usuario
from models.jogo_model import Jogo
from models.avaliacao_model import AvaliacaoJogo

class ListarMinhasAvaliacoesService:
    def executar(self, token):
        usuario = Usuario.buscar_por_token(token)
        if not usuario:
            raise ValueError('Sessão inválida. Faça login novamente.')

        avaliacoes = AvaliacaoJogo.query.filter_by(usuario_id=usuario.id) \
            .order_by(AvaliacaoJogo.data_avaliacao.desc()).all()

        resultado = []
        for av in avaliacoes:
            jogo = Jogo.query.get(av.jogo_id)
            if jogo:
                resultado.append({
                    'adversario': jogo.adversario,
                    'data_hora': jogo.data_hora.strftime('%d/%m/%Y'),
                    'nota': av.nota,
                    'comentario': av.comentario
                })
        return resultado