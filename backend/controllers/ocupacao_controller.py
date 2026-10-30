from flask import Blueprint, request, jsonify
from services.ocupacao_service import OcupacaoService
from services.buscar_perfil_service import BuscarPerfilService
from services.texto_util import normalizar_texto

ocupacao_bp = Blueprint('ocupacao', __name__)

@ocupacao_bp.route('/previsao', methods=['POST'])
def obter_previsao():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'erro': 'Token é obrigatório.'}), 400

    dados = request.get_json(silent=True) or {}
    importancia = dados.get('importancia', 'comum')
    adversario = dados.get('adversario', 'Desconhecido')
    campeonato = dados.get('campeonato')
    fase = dados.get('fase')
    data_hora = dados.get('data_hora')
    capacidade_disponivel = dados.get('capacidade_disponivel')
    clima = dados.get('clima')
    historico_por_setor = dados.get('historico_por_setor')
    capacidades_setores = dados.get('capacidades_setores')
    precos_setores = dados.get('precos_setores')

    try:
        # 1. Identifica qual o time do usuário
        service_perfil = BuscarPerfilService()
        usuario, time_obj = service_perfil.executar(token)

        if not time_obj:
            return jsonify({'erro': 'Usuário sem time selecionado.'}), 400

        # Define o ID do estádio baseado no time
        estadio_id = "arena_mrv" if "atletico" in normalizar_texto(time_obj.nome) else "mineirao"

        # 2. Calcula a previsão de ocupação
        service_ocupacao = OcupacaoService()
        resultado = service_ocupacao.calcular_previsao(
            estadio_id,
            adversario,
            importancia,
            campeonato,
            fase,
            data_hora,
            capacidade_disponivel,
            clima,
            historico_por_setor,
            capacidades_setores,
            precos_setores,
        )

        return jsonify(resultado), 200
    except ValueError as e:
        return jsonify({'erro': str(e)}), 400
