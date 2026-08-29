from flask import Blueprint, request, jsonify
from services.buscar_perfil_service import BuscarPerfilService
from services.atualizar_localizacao_service import AtualizarLocalizacaoService
from services.atualizar_foto_service import AtualizarFotoService

perfil_bp = Blueprint('perfil', __name__)


@perfil_bp.route('/perfil', methods=['GET'])
def ver_perfil():
    token = request.headers.get('Authorization')

    if not token:
        return jsonify({'erro': 'Token é obrigatório.'}), 400

    try:
        service = BuscarPerfilService()
        usuario, time = service.executar(token)
        return jsonify({
            'id': usuario.id,
            'nome': usuario.nome,
            'email': usuario.email,
            'time': time.nome if time else None,
            'foto': usuario.foto,
            'endereco': {
                'rua': usuario.rua,
                'numero': usuario.numero,
                'bairro': usuario.bairro,
                'cidade': usuario.cidade,
                'estado': usuario.estado
            }
        }), 200
    except ValueError as erro:
        return jsonify({'erro': str(erro)}), 401


@perfil_bp.route('/perfil/localizacao', methods=['PUT'])
def atualizar_localizacao():
    dados = request.get_json()
    token = dados.get('token')
    rua = dados.get('rua')
    numero = dados.get('numero')
    bairro = dados.get('bairro')
    cidade = dados.get('cidade')
    estado = dados.get('estado')

    if not token:
        return jsonify({'erro': 'Token é obrigatório.'}), 400

    try:
        service = AtualizarLocalizacaoService()
        usuario = service.executar(token, rua, numero, bairro, cidade, estado)
        return jsonify({
            'mensagem': 'Endereço atualizado com sucesso!',
            'endereco': {
                'rua': usuario.rua,
                'numero': usuario.numero,
                'bairro': usuario.bairro,
                'cidade': usuario.cidade,
                'estado': usuario.estado
            }
        }), 200
    except ValueError as erro:
        return jsonify({'erro': str(erro)}), 400


@perfil_bp.route('/perfil/foto', methods=['PUT'])
def atualizar_foto():
    token = request.form.get('token')
    arquivo = request.files.get('foto')

    if not token:
        return jsonify({'erro': 'Token é obrigatório.'}), 400

    try:
        service = AtualizarFotoService()
        usuario = service.executar(token, arquivo)
        return jsonify({
            'mensagem': 'Foto atualizada com sucesso!',
            'foto': usuario.foto
        }), 200
    except ValueError as erro:
        return jsonify({'erro': str(erro)}), 400