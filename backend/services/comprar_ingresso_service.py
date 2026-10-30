from models.usuario_model import Usuario

LINKS_POR_TIME = {
    1: 'https://ingressos.galonaveia.com.br/',
    2: 'https://socio.cruzeiro.com.br/jogos'
}

class ComprarIngressoService:
    def executar(self, token):
        usuario = Usuario.buscar_por_token(token)

        if not usuario:
            raise ValueError('Sessão inválida. Faça login novamente.')

        if not usuario.time_id:
            raise ValueError('Você precisa selecionar um time antes de comprar ingressos.')

        link = LINKS_POR_TIME.get(usuario.time_id)

        if not link:
            raise ValueError('Não há link de ingressos disponível para o seu time.')

        return link