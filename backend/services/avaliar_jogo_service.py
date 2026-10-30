from datetime import datetime
from models.usuario_model import Usuario
from models.jogo_model import Jogo
from models.avaliacao_model import AvaliacaoJogo

class AvaliarJogoService:
    def executar(self, token, jogo_id, nota, comentario=None):
        usuario = Usuario.buscar_por_token(token)
        if not usuario:
            raise ValueError('Sessão inválida. Faça login novamente.')

        jogo = Jogo.query.get(jogo_id)
        if not jogo:
            raise ValueError('Jogo não encontrado.')

        if jogo.time_id != usuario.time_id:
            raise ValueError('Você só pode avaliar jogos do seu time.')

        if jogo.data_hora > datetime.now():
            raise ValueError('Esse jogo ainda não aconteceu.')

        # a nota pode chegar como texto ("5"); int() converte e, se não der, avisamos
        try:
            nota = int(nota)
        except (TypeError, ValueError):
            raise ValueError('A nota deve ser um número inteiro de 1 a 5.')

        if not (1 <= nota <= 5):
            raise ValueError('A nota deve ser entre 1 e 5.')

        if AvaliacaoJogo.buscar(usuario.id, jogo_id):
            raise ValueError('Você já avaliou esse jogo.')

        avaliacao = AvaliacaoJogo(usuario_id=usuario.id, jogo_id=jogo_id, nota=nota, comentario=comentario)
        avaliacao.salvar()
        return {'mensagem': 'Avaliação registrada com sucesso.'}