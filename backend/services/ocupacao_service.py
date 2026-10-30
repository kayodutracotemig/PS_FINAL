"""Previsão de público e ocupação com médias históricas por setor."""
from datetime import datetime
from zoneinfo import ZoneInfo

from services.texto_util import normalizar_texto


class OcupacaoService:
    FUSO = ZoneInfo('America/Sao_Paulo')

    # Faixas históricas fornecidas pelo usuário (limite inferior/superior).
    # Capacidades são referências por setor; a disponibilidade de cada jogo pode mudar.
    estadios_ref = {
        'arena_mrv': {
            'nome': 'Arena MRV',
            'capacidade_nominal': 44892,
            'setores': [
                {'id': 'brahma_sul', 'nome': 'Brahma Sul', 'cap': 2700, 'faixa': (95, 100)},
                {'id': 'brahma_norte', 'nome': 'Brahma Norte', 'cap': 2961, 'faixa': (90, 100)},
                {'id': 'inter_sul', 'nome': 'Inter Sul', 'cap': 6700, 'faixa': (80, 95)},
                {'id': 'inter_norte_mandante', 'nome': 'Inter Norte — mandante', 'cap': 2863, 'faixa': (80, 95)},
                {'id': 'inter_norte_visitante', 'nome': 'Inter Norte — visitante', 'cap': 4266, 'faixa': (80, 95)},
                {'id': 'brahma_leste', 'nome': 'Brahma Leste', 'cap': 4463, 'faixa': (70, 85)},
                {'id': 'brahma_oeste', 'nome': 'Brahma Oeste', 'cap': 4463, 'faixa': (70, 85)},
                {'id': 'inter_leste', 'nome': 'Inter Leste', 'cap': 7024, 'faixa': (65, 85)},
                {'id': 'inter_oeste', 'nome': 'Inter Oeste', 'cap': 4289, 'faixa': (65, 85)},
                {'id': 'arcelor_norte', 'nome': 'ArcelorMittal Norte', 'cap': 899, 'faixa': (40, 65)},
                {'id': 'arcelor_sul', 'nome': 'ArcelorMittal Sul', 'cap': 331, 'faixa': (40, 65)},
                {'id': 'arcelor_leste', 'nome': 'ArcelorMittal Leste', 'cap': 547, 'faixa': (40, 65)},
                {'id': 'arcelor_oeste', 'nome': 'ArcelorMittal Oeste', 'cap': 544, 'faixa': (40, 65)},
                {'id': 'lounge', 'nome': 'Lounge', 'cap': 1732, 'faixa': (40, 55)},
            ],
        },
        'mineirao': {
            'nome': 'Mineirão',
            'capacidade_nominal': 61927,
            'setores': [
                {'id': 'amarelo', 'nome': 'Amarelo (superior/inferior)', 'cap': 15574, 'faixa': (90, 100)},
                {'id': 'laranja', 'nome': 'Laranja / Sesc Senac (superior/inferior)', 'cap': 15567, 'faixa': (85, 95)},
                {'id': 'vermelho', 'nome': 'Vermelho / Sicoob (superior/inferior)', 'cap': 16344, 'faixa': (70, 85)},
                {'id': 'roxo', 'nome': 'Roxo / APVS (superior/inferior)', 'cap': 14097, 'faixa': (50, 70)},
                # VIP/camarotes são uma subárea sobreposta ao mapa de setores;
                # estimamos o público dela, mas não somamos duas vezes no total.
                {'id': 'vip_camarotes', 'nome': 'Camarotes e Tribuna VIP', 'cap': 2234, 'faixa': (60, 80), 'conta_no_total': False},
            ],
        },
    }

    organizadas_ref = {
        'arena_mrv': {
            'grupos': [
                {'nome': 'Galoucura', 'setor': 'Inter Sul (anel superior)', 'contexto': 'Principal referência atual.'},
                {'nome': 'Outras organizadas do Atlético', 'setor': 'Brahma Sul (referência histórica)', 'contexto': 'Não é setor exclusivo nem localização fixa.'},
            ],
            'aviso': 'A disposição pode mudar por partida. Confira o mapa do evento.',
        },
        'mineirao': {
            'grupos': [
                {'nome': 'Máfia Azul', 'setor': 'Amarelo (inferior e superior)', 'contexto': 'Zona de referência habitual; o nível pode variar.'},
                {'nome': 'Pavilhão Independente e China Azul', 'setor': 'Laranja Inferior', 'contexto': 'Registro específico de uma partida, não uma regra permanente.'},
            ],
            'aviso': 'O posicionamento pode mudar por partida. Confira o mapa do evento.',
        },
    }

    # Índices apenas relativos: servem como fallback enquanto não houver preços
    # médios reais cadastrados para os setores.
    precos_relativos = {
        'arena_mrv': {
            'brahma_sul': 1, 'brahma_norte': 1, 'inter_sul': 2,
            'inter_norte_mandante': 2, 'inter_norte_visitante': 2,
            'brahma_leste': 2, 'brahma_oeste': 3, 'inter_leste': 2,
            'inter_oeste': 3, 'arcelor_norte': 4, 'arcelor_sul': 4,
            'arcelor_leste': 4, 'arcelor_oeste': 4, 'lounge': 5,
        },
        'mineirao': {
            'amarelo': 1, 'laranja': 1, 'vermelho': 2, 'roxo': 3,
            'vip_camarotes': 5,
        },
    }
    setores_com_organizadas = {
        'arena_mrv': {'brahma_sul', 'inter_sul'},
        'mineirao': {'amarelo', 'laranja'},
    }

    def calcular_previsao(
        self,
        estadio_id,
        adversario,
        importancia='comum',
        campeonato=None,
        fase=None,
        data_hora=None,
        capacidade_disponivel=None,
        clima=None,
        historico_por_setor=None,
        capacidades_setores=None,
        precos_setores=None,
    ):
        estadio = self.estadios_ref.get(estadio_id)
        if not estadio:
            raise ValueError('Estádio não reconhecido.')

        fator_relevancia, motivo_relevancia = self._peso_relevancia(
            estadio_id, adversario, importancia, campeonato, fase
        )
        fator_clima_data, motivo_clima = self._peso_clima_data(data_hora, clima)
        fatores = {
            'relevancia': fator_relevancia,
            'clima_data': fator_clima_data,
        }

        resultados_setores = []
        publico_total_baixo = 0
        publico_total_central = 0
        publico_total_alto = 0
        capacidade_total = 0
        for setor in estadio['setores']:
            cap = self._capacidade_setor(setor, capacidades_setores)
            hist = (historico_por_setor or {}).get(setor['id'], [])
            base = self._media_movel_ponderada(hist)
            usa_media_faixa = base is None
            if usa_media_faixa:
                base = sum(setor['faixa']) / 2

            percent_base = min(100, max(0, base))
            percent_baixo = min(100, max(0, setor['faixa'][0] * fator_relevancia * fator_clima_data))
            percent_alto = min(100, max(0, setor['faixa'][1] * fator_relevancia * fator_clima_data))
            percent_central = min(100, max(0, percent_base * fator_relevancia * fator_clima_data))

            publico_baixo = round(cap * percent_baixo / 100)
            publico_central = round(cap * percent_central / 100)
            publico_alto = round(cap * percent_alto / 100)
            resultados_setores.append({
                'id': setor['id'],
                'nome': setor['nome'],
                'capacidade': cap,
                'ocupacao_base_percent': round(percent_base, 1),
                'ocupacao_baixa_percent': round(percent_baixo, 1),
                'ocupacao_percent': round(percent_central, 1),
                'ocupacao_alta_percent': round(percent_alto, 1),
                'publico_baixo': publico_baixo,
                'publico_previsto': publico_central,
                'publico_alto': publico_alto,
                'status': 'estimativa_por_faixa_historica' if usa_media_faixa else 'estimativa_por_media_movel',
                'confianca': 'média' if not usa_media_faixa else 'baixa',
                'cor': self._get_cor_ocupacao(percent_central),
                'conta_no_total': setor.get('conta_no_total', True),
                'preco_medio': self._numero_positivo_float((precos_setores or {}).get(setor['id'])),
                'preco_relativo': self.precos_relativos[estadio_id].get(setor['id'], 3),
                'tem_organizada_referencia': setor['id'] in self.setores_com_organizadas[estadio_id],
            })
            if setor.get('conta_no_total', True):
                publico_total_baixo += publico_baixo
                publico_total_central += publico_central
                publico_total_alto += publico_alto
                capacidade_total += cap

        if capacidade_disponivel:
            capacidade_total = min(
                capacidade_total,
                self._numero_positivo(capacidade_disponivel) or capacidade_total,
            )
            publico_total_central = min(publico_total_central, capacidade_total)
            publico_total_baixo = min(publico_total_baixo, publico_total_central)
            publico_total_alto = min(publico_total_alto, capacidade_total)

        pct_baixo = round(publico_total_baixo / capacidade_total * 100, 1) if capacidade_total else 0
        pct_central = round(publico_total_central / capacidade_total * 100, 1) if capacidade_total else 0
        pct_alto = round(publico_total_alto / capacidade_total * 100, 1) if capacidade_total else 0
        recomendacao = self._recomendar_setor(estadio_id, resultados_setores)

        return {
            'estadio': estadio['nome'],
            'capacidade_usada': capacidade_total,
            'capacidade_origem': 'capacidade de referência por setor; sujeita à liberação do evento',
            'publico_previsto': publico_total_central,
            'ocupacao_geral': pct_central,
            'cenarios': {
                'baixo': {'publico': publico_total_baixo, 'ocupacao_percent': pct_baixo},
                'central': {'publico': publico_total_central, 'ocupacao_percent': pct_central},
                'alto': {'publico': publico_total_alto, 'ocupacao_percent': pct_alto},
            },
            'intervalo': {'inferior': publico_total_baixo, 'superior': publico_total_alto},
            'setores': resultados_setores,
            'setor_recomendado': recomendacao,
            'aviso_setores': (
                'Percentuais baseados nas faixas históricas fornecidas. A capacidade aberta e a venda de ingressos '
                'podem mudar por partida; o mapa oficial prevalece.'
            ),
            'torcidas_organizadas': self.organizadas_ref[estadio_id]['grupos'],
            'aviso_organizacao': self.organizadas_ref[estadio_id]['aviso'],
            'fatores_contexto': fatores,
            'motivo_relevancia': motivo_relevancia,
            'motivo_clima_data': motivo_clima,
            'metodologia': self._metodologia(fator_relevancia, motivo_relevancia, fator_clima_data, motivo_clima),
            'confianca': 'baixa' if any(s['status'] == 'estimativa_por_faixa_historica' for s in resultados_setores) else 'média',
        }

    @staticmethod
    def _media_movel_ponderada(historico):
        """Usa os cinco jogos mais recentes; pesos antigos→recentes: 1,1,1,2,2."""
        if not isinstance(historico, (list, tuple)) or len(historico) < 5:
            return None
        try:
            valores = [float(valor) for valor in historico[-5:]]
        except (TypeError, ValueError):
            return None
        pesos = (1, 1, 1, 2, 2)
        return sum(valor * peso for valor, peso in zip(valores, pesos)) / sum(pesos)

    def _peso_relevancia(self, estadio_id, adversario, importancia, campeonato, fase):
        rival = normalizar_texto(adversario or '')
        comp = normalizar_texto(campeonato or '')
        etapa = normalizar_texto(fase or '')
        classicos = {
            'arena_mrv': {'cruzeiro', 'cruzeiroec', 'cruzeiroesporteclube'},
            'mineirao': {'atletico', 'atleticomg', 'atleticomineiro', 'camineiro', 'atletico-mg'},
        }
        decisivo = any(termo in etapa for termo in ('final', 'semifinal', 'quartas', 'oitavas', 'decisao'))
        decisivo = decisivo or any(termo in comp for termo in ('final', 'semifinal'))
        if rival in classicos[estadio_id] or decisivo or importancia == 'alto_apelo':
            motivos = []
            if rival in classicos[estadio_id]:
                motivos.append('clássico mineiro')
            if decisivo:
                motivos.append('fase decisiva')
            if importancia == 'alto_apelo' and not motivos:
                motivos.append('alto apelo informado')
            return 1.3, ' e '.join(motivos)
        return 1.0, 'jogo comum'

    def _peso_clima_data(self, data_hora, clima):
        tempo = normalizar_texto(clima or '')
        data = self._data_local(data_hora)
        if 'chuva' in tempo or 'chuvoso' in tempo:
            return 0.8, 'chuva informada'
        if data and data.weekday() < 5 and data.hour >= 19:
            return 0.8, 'jogo em dia útil à noite'
        if data and data.weekday() == 6 and any(x in tempo for x in ('sol', 'ensolarado', 'aberto')):
            return 1.1, 'domingo ensolarado informado'
        return 1.0, 'sem ajuste de clima/data'

    @staticmethod
    def _capacidade_setor(setor, capacidades_setores):
        valor = (capacidades_setores or {}).get(setor['id'])
        try:
            capacidade = int(valor)
            if capacidade >= 0:
                return capacidade
        except (TypeError, ValueError):
            pass
        return setor['cap']

    @staticmethod
    def _numero_positivo(valor):
        try:
            numero = int(valor)
            return numero if numero > 0 else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _numero_positivo_float(valor):
        try:
            numero = float(valor)
            return numero if numero > 0 else None
        except (TypeError, ValueError):
            return None

    def _recomendar_setor(self, estadio_id, setores):
        candidatos = [
            setor for setor in setores
            if not setor['tem_organizada_referencia'] and setor['conta_no_total']
        ]
        if not candidatos:
            return None

        precos_reais = [setor['preco_medio'] for setor in candidatos if setor['preco_medio'] is not None]
        tem_precos_reais = len(precos_reais) == len(candidatos)
        if tem_precos_reais:
            menor, maior = min(precos_reais), max(precos_reais)
        else:
            referencias = self.precos_relativos[estadio_id]
            menor, maior = min(referencias.values()), max(referencias.values())

        for setor in candidatos:
            if tem_precos_reais:
                preco = setor['preco_medio']
            else:
                preco = setor['preco_relativo']
            economia = 100 if maior == menor else 100 * (maior - preco) / (maior - menor)
            menor_movimento = max(0, 100 - setor['ocupacao_percent'])
            setor['pontuacao_recomendacao'] = round(
                economia * 0.40 + menor_movimento * 0.60, 1
            )

        melhor = max(candidatos, key=lambda s: (s['pontuacao_recomendacao'], -s['ocupacao_percent']))
        if tem_precos_reais:
            preco_info = f"preço médio informado de R$ {melhor['preco_medio']:.2f}"
        else:
            preco_info = 'faixa de preço relativa estimada; não representa preço atual em reais'
        return {
            'setor': melhor['nome'],
            'id_setor': melhor['id'],
            'pontuacao': melhor['pontuacao_recomendacao'],
            'ocupacao_prevista_percent': melhor['ocupacao_percent'],
            'preco_medio': melhor['preco_medio'],
            'preco_estimado': not tem_precos_reais,
            'motivo': (
                f"Melhor equilíbrio entre preço e menor ocupação prevista; sem referência de torcida organizada. "
                f"Base de preço: {preco_info}."
            ),
            'metodologia': '40% preço relativo e 60% menor ocupação prevista; setores com organizada de referência são excluídos.',
        }

    def _data_local(self, valor):
        if not valor:
            return None
        try:
            data = datetime.fromisoformat(str(valor).replace('Z', '+00:00'))
            if data.tzinfo:
                return data.astimezone(self.FUSO)
            return data
        except ValueError:
            return None

    @staticmethod
    def _metodologia(peso_relevancia, motivo_relevancia, peso_clima, motivo_clima):
        return (
            'Cada setor usa a média móvel ponderada dos cinco jogos mais recentes (pesos 1, 1, 1, 2, 2). '
            'Como não há essa série no banco, o sistema usa o ponto médio da faixa histórica fornecida. '
            f'Peso de relevância: {peso_relevancia:.1f} ({motivo_relevancia}); '
            f'peso de clima/data: {peso_clima:.1f} ({motivo_clima}). Percentual limitado a 100%.'
        )

    @staticmethod
    def _get_cor_ocupacao(percent):
        if percent < 40:
            return 'verde'
        if percent < 70:
            return 'amarelo'
        if percent < 90:
            return 'laranja'
        return 'vermelho'
