from models.usuario_model import Usuario
from models.favorito_model import Favorito
from models.jogo_model import Jogo

class ListarFavoritosService:
    def executar(self, token):
        usuario = Usuario.buscar_por_token(token)
        if not usuario:
            raise ValueError('Sessão inválida. Faça login novamente.')

        favoritos = Favorito.listar_por_usuario(usuario.id)

        resultado = []
        for fav in favoritos:
            jogo = Jogo.query.get(fav.jogo_id)
            if jogo:
                resultado.append({
                    'jogo_id': jogo.id,
                    'adversario': jogo.adversario,
                    'data_hora': jogo.data_hora.strftime('%d/%m/%Y %H:%M'),
                    'estadio': jogo.estadio
                })
        return resultado