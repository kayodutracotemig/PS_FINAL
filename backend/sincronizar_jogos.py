"""Sincroniza os jogos do Brasileirão Série A via football-data.org."""
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from sqlalchemy import text

from app import app, db
from models.jogo_model import Jogo
from models.time_model import Time
from services.texto_util import normalizar_texto

API_URL = 'https://api.football-data.org/v4/competitions/BSA/matches'
FUSO = ZoneInfo('America/Sao_Paulo')
TIME_ALVO = {
    'atleticomineiro': ('atleticomineiro', 'atleticomg', 'atletico-mg', 'camineiro'),
    'cruzeiro': ('cruzeiro', 'cruzeiroec', 'cruzeiroesporteclube'),
}
ESTADIOS = {'atleticomineiro': 'Arena MRV', 'cruzeiro': 'Mineirão'}


def preparar_coluna_externa():
    """Atualiza bancos antigos, inclusive os que receberam o campo anterior."""
    colunas = db.session.execute(text('PRAGMA table_info(jogos)')).fetchall()
    nomes = {coluna[1] for coluna in colunas}
    if not colunas:
        return
    if 'football_data_match_id' not in nomes:
        db.session.execute(text('ALTER TABLE jogos ADD COLUMN football_data_match_id INTEGER'))
    db.session.execute(text(
        'CREATE UNIQUE INDEX IF NOT EXISTS ix_jogos_football_data_match_id '
        'ON jogos (football_data_match_id)'
    ))
    db.session.commit()


def identificar_time(nome_api, times_db):
    nome = normalizar_texto(nome_api or '')
    for chave, aliases in TIME_ALVO.items():
        if nome in aliases and chave in times_db:
            return chave, times_db[chave]
    return None, None


def sincronizar(temporada):
    token = os.getenv('FOOTBALL_DATA_TOKEN')
    if not token:
        raise RuntimeError('Defina FOOTBALL_DATA_TOKEN no arquivo backend/.env.')

    times_db = {
        normalizar_texto(time.nome): time
        for time in Time.query.all()
        if normalizar_texto(time.nome) in ('atleticomg', 'cruzeiro')
    }
    # O nome persistido no projeto é "Atlético MG"; a API chama o clube de
    # "Atlético Mineiro". A chave local usada abaixo é o nome sem espaços.
    if 'atleticomg' in times_db:
        times_db['atleticomineiro'] = times_db['atleticomg']
    if 'atleticomineiro' not in times_db or 'cruzeiro' not in times_db:
        raise RuntimeError('Não encontrei Atlético MG e Cruzeiro no banco.')

    resposta = requests.get(
        API_URL,
        params={'season': temporada},
        headers={'X-Auth-Token': token},
        timeout=30,
    )
    if resposta.status_code == 403:
        raise RuntimeError(
            'football-data.org negou acesso. Confira se seu token está correto '
            'e se o plano permite acessar o Brasileirão Série A.'
        )
    resposta.raise_for_status()
    dados = resposta.json()

    partidas_api = dados.get('matches') or []
    print(f'football-data.org retornou {len(partidas_api)} partida(s) de Série A para {temporada}.')
    clubes_api = set()
    total = 0
    try:
        for partida in partidas_api:
            casa = partida.get('homeTeam') or {}
            fora = partida.get('awayTeam') or {}
            if casa.get('name'):
                clubes_api.add(casa['name'])
            if fora.get('name'):
                clubes_api.add(fora['name'])
            chave, time_db = identificar_time(casa.get('name'), times_db)
            adversario = fora.get('name')
            local = 'casa'
            if not time_db:
                chave, time_db = identificar_time(fora.get('name'), times_db)
                adversario = casa.get('name')
                local = 'fora'
            if not time_db or not adversario or not partida.get('utcDate'):
                continue

            data_hora = datetime.fromisoformat(
                partida['utcDate'].replace('Z', '+00:00')
            ).astimezone(FUSO).replace(tzinfo=None)
            registro = Jogo.query.filter_by(
                football_data_match_id=partida['id']
            ).first()
            if registro is None:
                registro = Jogo(football_data_match_id=partida['id'])
            registro.time_id = time_db.id
            registro.adversario = adversario
            registro.data_hora = data_hora
            registro.local = local
            registro.estadio = partida.get('venue') or (
                ESTADIOS[chave] if local == 'casa' else None
            )
            registro.campeonato = (partida.get('competition') or {}).get(
                'name', 'Brasileirão Série A'
            )
            registro.fase = (partida.get('stage') or '').replace('_', ' ').title() or None
            db.session.add(registro)
            total += 1
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    print(f'Brasileirão Série A: {total} jogo(s) do Atlético-MG e Cruzeiro sincronizado(s).')
    if partidas_api and total == 0:
        print('Nomes de equipes recebidos: ' + ', '.join(sorted(clubes_api)))
    return total


if __name__ == '__main__':
    temporada = int(sys.argv[1]) if len(sys.argv) > 1 else datetime.now(FUSO).year
    with app.app_context():
        preparar_coluna_externa()
        try:
            quantidade = sincronizar(temporada)
            print(f'Total: {quantidade} jogo(s) na temporada {temporada}.')
        except (RuntimeError, requests.RequestException) as erro:
            print(f'Erro: {erro}', file=sys.stderr)
            sys.exit(1)
