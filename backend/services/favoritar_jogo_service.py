from models.usuario_model import Usuario
from models.jogo_model import Jogo
from models.favorito_model import Favorito

class FavoritarJogoService:
    def executar(self, token, jogo_id):
        usuario = Usuario.buscar_por_token(token)
        if not usuario:
            raise ValueError('Sessão inválida. Faça login novamente.')

        jogo = Jogo.query.get(jogo_id)
        if not jogo:
            raise ValueError('Jogo não encontrado.')

        favorito_existente = Favorito.buscar(usuario.id, jogo_id)

        if favorito_existente:
            favorito_existente.deletar()
            return {'favoritado': False}
        else:
            novo_favorito = Favorito(usuario_id=usuario.id, jogo_id=jogo_id)
            novo_favorito.salvar()
            return {'favoritado': True}