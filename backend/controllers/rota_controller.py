from flask import Blueprint, request, jsonify
from services.calcular_rota_service import calcular_rota_estadio
from services.buscar_perfil_service import BuscarPerfilService

rota_bp = Blueprint('rota', __name__)

@rota_bp.route('/rota', methods=['POST'])
def calcular_rota():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'erro': 'Token é obrigatório.'}), 400

    dados = request.get_json(silent=True) or {}
    latitude = dados.get('latitude')
    longitude = dados.get('longitude')
    modo = dados.get('modo', 'driving')

    if latitude is None or longitude is None:
        return jsonify({'erro': 'Localização é obrigatória.'}), 400

    try:
        # Usando a classe BuscarPerfilService que já existe no seu projeto
        service_perfil = BuscarPerfilService()
        usuario, time_obj = service_perfil.executar(token)

        # Pegamos o nome do time (ex: 'Atletico' ou 'Cruzeiro')
        time_nome = time_obj.nome if time_obj else None

        if not time_nome:
            return jsonify({'erro': 'Usuário não possui um time selecionado.'}), 400

        # Agora calculamos a rota baseada no time
        resultado = calcular_rota_estadio(time_nome, latitude, longitude, modo)
        return jsonify(resultado), 200
    except Exception as erro:
        return jsonify({'erro': str(erro)}), 400