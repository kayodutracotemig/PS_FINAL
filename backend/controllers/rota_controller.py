from flask import Blueprint, request, jsonify
from services.calcular_rota_service import gerar_link_rota_google_maps
from services.buscar_perfil_service import BuscarPerfilService

rota_bp = Blueprint('rota', __name__)

@rota_bp.route('/rota', methods=['POST'])
def calcular_rota():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'erro': 'Token é obrigatório.'}), 400

    dados = request.get_json(silent=True) or {}
    modo = dados.get('modo', 'driving')

    try:
        service_perfil = BuscarPerfilService()
        usuario, time_obj = service_perfil.executar(token)
        time_nome = time_obj.nome if time_obj else None
        if not time_nome:
            return jsonify({'erro': 'Usuário não possui um time selecionado.'}), 400

        campos_endereco = [usuario.rua, usuario.numero, usuario.bairro, usuario.cidade, usuario.estado, 'Brasil']
        endereco_origem = ', '.join(campo.strip() for campo in campos_endereco if campo and campo.strip())
        if not all((campo or '').strip() for campo in (usuario.rua, usuario.cidade, usuario.estado)):
            return jsonify({'erro': 'Cadastre rua, cidade e estado no seu perfil antes de calcular a rota.'}), 400

        resultado = gerar_link_rota_google_maps(time_nome, endereco_origem, modo)
        return jsonify(resultado), 200
    except ValueError as erro:
        return jsonify({'erro': str(erro)}), 400