from flask import Blueprint, request, jsonify
from services.comprar_ingresso_service import ComprarIngressoService
from services.proximos_jogos_service import ProximosJogosService

ingresso_bp = Blueprint('ingresso', __name__)


@ingresso_bp.route('/ingressos/comprar', methods=['GET'])
def comprar_ingresso():
    token = request.headers.get('Authorization')

    if not token:
        return jsonify({'erro': 'Token é obrigatório.'}), 400

    try:
        service = ComprarIngressoService()
        link = service.executar(token)
        return jsonify({'link': link}), 200
    except ValueError as erro:
        return jsonify({'erro': str(erro)}), 400


@ingresso_bp.route('/jogos/proximos', methods=['GET'])
def proximos_jogos():
    token = request.headers.get('Authorization')

    if not token:
        return jsonify({'erro': 'Token é obrigatório.'}), 400

    try:
        service = ProximosJogosService()
        jogos = service.executar(token)
        return jsonify(jogos), 200
    except ValueError as erro:
        return jsonify({'erro': str(erro)}), 400