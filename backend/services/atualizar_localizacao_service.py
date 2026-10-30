from models.usuario_model import Usuario

class AtualizarLocalizacaoService:
    def executar(self, token, rua, numero, bairro, cidade, estado):
        usuario = Usuario.buscar_por_token(token)

        if not usuario:
            raise ValueError('Sessão inválida. Faça login novamente.')

        if not rua or not cidade or not estado:
            raise ValueError('Rua, cidade e estado são obrigatórios.')

        usuario.rua = rua.strip()
        usuario.numero = numero.strip() if numero else None
        usuario.bairro = bairro.strip() if bairro else None
        usuario.cidade = cidade.strip()
        usuario.estado = estado.strip().upper()

        usuario.atualizar()

        return usuario