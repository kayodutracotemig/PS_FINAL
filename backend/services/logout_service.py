from models.usuario_model import Usuario

class LogoutService:
    def executar(self, token):
        usuario = Usuario.buscar_por_token(token)

        if not usuario:
            raise ValueError('Sessão inválida ou já encerrada.')

        usuario.token = None
        usuario.atualizar()

        return usuario