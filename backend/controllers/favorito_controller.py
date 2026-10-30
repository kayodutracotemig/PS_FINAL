from flask import Blueprint, request, jsonify
from services.favoritar_jogo_service import FavoritarJogoService
from services.listar_favoritos_service import ListarFavoritosService

favorito_bp = Blueprint('favorito', __name__)

@favorito_bp.route('/jogos/<int:jogo_id>/favoritar', methods=['POST'])
def favoritar_jogo(jogo_id):
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'erro': 'Token é obrigatório.'}), 400
    try:
        service = FavoritarJogoService()
        resultado = service.executar(token, jogo_id)
        return jsonify(resultado), 200
    except ValueError as erro:
        return jsonify({'erro': str(erro)}), 400

@favorito_bp.route('/favoritos', methods=['GET'])
def listar_favoritos():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'erro': 'Token é obrigatório.'}), 400
    try:
        service = ListarFavoritosService()
        favoritos = service.executar(token)
        return jsonify(favoritos), 200
    except ValueError as erro:
        return jsonify({'erro': str(erro)}), 400