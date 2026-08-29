from flask import Blueprint, request, jsonify
from services.cadastrar_usuario_service import CadastrarUsuarioService
from services.login_service import LoginService
from services.logout_service import LogoutService

usuario_bp = Blueprint('usuario', __name__)


@usuario_bp.route('/usuarios/cadastro', methods=['POST'])
def cadastrar():
    dados = request.get_json()

    nome = dados.get('nome')
    email = dados.get('email')
    senha = dados.get('senha')

    if not nome or not email or not senha:
        return jsonify({'erro': 'Nome, email e senha são obrigatórios.'}), 400

    try:
        service = CadastrarUsuarioService()
        usuario = service.executar(nome, email, senha)
        return jsonify({
            'mensagem': 'Usuário cadastrado com sucesso!',
            'id': usuario.id,
            'nome': usuario.nome,
            'email': usuario.email
        }), 201
    except ValueError as erro:
        return jsonify({'erro': str(erro)}), 400


@usuario_bp.route('/usuarios/login', methods=['POST'])
def login():
    dados = request.get_json()

    email = dados.get('email')
    senha = dados.get('senha')

    if not email or not senha:
        return jsonify({'erro': 'Email e senha são obrigatórios.'}), 400

    try:
        service = LoginService()
        usuario = service.executar(email, senha)
        return jsonify({
            'mensagem': 'Login realizado com sucesso!',
            'id': usuario.id,
            'nome': usuario.nome,
            'email': usuario.email,
            'token': usuario.token
        }), 200
    except ValueError as erro:
        return jsonify({'erro': str(erro)}), 401


@usuario_bp.route('/usuarios/logout', methods=['POST'])
def logout():
    dados = request.get_json()
    token = dados.get('token')

    if not token:
        return jsonify({'erro': 'Token é obrigatório.'}), 400

    try:
        service = LogoutService()
        service.executar(token)
        return jsonify({'mensagem': 'Logout realizado com sucesso!'}), 200
    except ValueError as erro:
        return jsonify({'erro': str(erro)}), 401