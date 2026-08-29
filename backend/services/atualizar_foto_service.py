import os
import uuid
from models.usuario_model import Usuario

EXTENSOES_PERMITIDAS = {'png', 'jpg', 'jpeg'}

class AtualizarFotoService:
    def executar(self, token, arquivo):
        usuario = Usuario.buscar_por_token(token)

        if not usuario:
            raise ValueError('Sessão inválida. Faça login novamente.')

        if not arquivo or arquivo.filename == '':
            raise ValueError('Nenhum arquivo foi enviado.')

        extensao = arquivo.filename.rsplit('.', 1)[-1].lower()
        if extensao not in EXTENSOES_PERMITIDAS:
            raise ValueError('Formato de imagem inválido. Use PNG ou JPG.')

        nome_arquivo = f'{uuid.uuid4().hex}.{extensao}'
        caminho_pasta = os.path.join('static', 'fotos')
        caminho_completo = os.path.join(caminho_pasta, nome_arquivo)

        arquivo.save(caminho_completo)

        usuario.foto = f'/static/fotos/{nome_arquivo}'
        usuario.atualizar()

        return usuario