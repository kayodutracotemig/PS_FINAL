from flask import Blueprint, request, jsonify
from services.avaliar_jogo_service import AvaliarJogoService
from services.listar_minhas_avaliacoes_service import ListarMinhasAvaliacoesService

avaliacao_bp = Blueprint('avaliacao', __name__)

@avaliacao_bp.route('/jogos/<int:jogo_id>/avaliar', methods=['POST'])
def avaliar_jogo(jogo_id):
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'erro': 'Token é obrigatório.'}), 400

    dados = request.get_json(silent=True) or {}
    nota = dados.get('nota')
    comentario = dados.get('comentario')

    if nota is None:
        return jsonify({'erro': 'A nota é obrigatória.'}), 400

    try:
        service = AvaliarJogoService()
        resultado = service.executar(token, jogo_id, nota, comentario)
        return jsonify(resultado), 200
    except ValueError as erro:
        return jsonify({'erro': str(erro)}), 400


@avaliacao_bp.route('/avaliacoes', methods=['GET'])
def minhas_avaliacoes():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'erro': 'Token é obrigatório.'}), 400
    try:
        service = ListarMinhasAvaliacoesService()
        avaliacoes = service.executar(token)
        return jsonify(avaliacoes), 200
    except ValueError as erro:
        return jsonify({'erro': str(erro)}), 400