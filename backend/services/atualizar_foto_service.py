import os
import uuid
from flask import current_app
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
        # root_path = pasta do app.py, não importa de onde você rodou o comando
        caminho_pasta = os.path.join(current_app.root_path, 'static', 'fotos')
        os.makedirs(caminho_pasta, exist_ok=True)  # cria se não existir
        caminho_completo = os.path.join(caminho_pasta, nome_arquivo)

        arquivo.save(caminho_completo)

        usuario.foto = f'/static/fotos/{nome_arquivo}'
        usuario.atualizar()

        return usuario