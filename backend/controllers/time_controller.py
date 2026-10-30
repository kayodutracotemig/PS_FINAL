from flask import Blueprint, request, jsonify
from models.time_model import Time
from services.selecionar_time_service import SelecionarTimeService
from services.mudar_time_service import MudarTimeService

time_bp = Blueprint('time', __name__)


@time_bp.route('/times', methods=['GET'])
def listar_times():
    times = Time.listar_todos()
    resultado = [{'id': time.id, 'nome': time.nome} for time in times]
    return jsonify(resultado), 200


@time_bp.route('/times/selecionar', methods=['POST'])
def selecionar_time():
    dados = request.get_json(silent=True) or {}
    token = dados.get('token')
    time_id = dados.get('time_id')

    if not token or not time_id:
        return jsonify({'erro': 'Token e time_id são obrigatórios.'}), 400

    try:
        service = SelecionarTimeService()
        usuario, time = service.executar(token, time_id)
        return jsonify({
            'mensagem': f'Time selecionado: {time.nome}',
            'usuario_id': usuario.id,
            'time_id': time.id,
            'time_nome': time.nome
        }), 200
    except ValueError as erro:
        return jsonify({'erro': str(erro)}), 400


@time_bp.route('/times/mudar', methods=['PUT'])
def mudar_time():
    dados = request.get_json(silent=True) or {}
    token = dados.get('token')
    novo_time_id = dados.get('time_id')

    if not token or not novo_time_id:
        return jsonify({'erro': 'Token e time_id são obrigatórios.'}), 400

    try:
        service = MudarTimeService()
        usuario, time = service.executar(token, novo_time_id)
        return jsonify({
            'mensagem': f'Time atualizado para: {time.nome}',
            'usuario_id': usuario.id,
            'time_id': time.id,
            'time_nome': time.nome
        }), 200
    except ValueError as erro:
        return jsonify({'erro': str(erro)}), 400