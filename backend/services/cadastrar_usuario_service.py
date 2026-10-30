from models.usuario_model import Usuario
from werkzeug.security import generate_password_hash

class CadastrarUsuarioService:
    def executar(self, nome, email, senha):
        usuario_existente = Usuario.buscar_por_email(email)
        if usuario_existente:
            raise ValueError('Este email já está cadastrado.')

        senha_criptografada = generate_password_hash(senha)

        novo_usuario = Usuario(
            nome=nome,
            email=email,
            senha=senha_criptografada
        )
        novo_usuario.salvar()

        return novo_usuario