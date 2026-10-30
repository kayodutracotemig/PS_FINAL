"""Cadastro manual de jogo de Copa do Brasil ou Sul-Americana."""
from datetime import datetime

from app import app, db
from models.jogo_model import Jogo
from models.time_model import Time
from sqlalchemy.exc import SQLAlchemyError
from sincronizar_jogos import preparar_coluna_externa

COMPETICOES = ('Copa do Brasil', 'CONMEBOL Sudamericana')


def escolher_time():
    times = {time.nome: time for time in Time.query.order_by(Time.nome).all()}
    opcoes = [('Atlético MG', 'Atlético MG'), ('Cruzeiro', 'Cruzeiro')]
    print('Time:')
    for numero, (_, nome) in enumerate(opcoes, start=1):
        print(f'  {numero}. {nome}')
    escolha = input('Escolha 1 ou 2: ').strip()
    if escolha not in ('1', '2'):
        raise ValueError('Escolha inválida.')
    nome_time = opcoes[int(escolha) - 1][0]
    if nome_time not in times:
        raise ValueError(f'O time {nome_time} não está cadastrado no banco.')
    return times[nome_time]


def registrar():
    time = escolher_time()
    adversario = input('Adversário: ').strip()
    if not adversario:
        raise ValueError('Informe o adversário.')
    data_texto = input('Data e hora (AAAA-MM-DD HH:MM): ').strip()
    data_hora = datetime.strptime(data_texto, '%Y-%m-%d %H:%M')
    local = input('Mando (casa/fora): ').strip().lower()
    if local not in ('casa', 'fora'):
        raise ValueError('O mando deve ser casa ou fora.')
    estadio = input('Estádio (Enter para deixar em branco): ').strip() or None

    print('Competição:')
    for numero, nome in enumerate(COMPETICOES, start=1):
        print(f'  {numero}. {nome}')
    escolha = input('Escolha 1 ou 2: ').strip()
    if escolha not in ('1', '2'):
        raise ValueError('Escolha inválida.')
    campeonato = COMPETICOES[int(escolha) - 1]
    fase = input('Fase (ex.: fase de grupos, semifinal, final; Enter se não souber): ').strip() or None

    existente = Jogo.query.filter_by(
        time_id=time.id,
        adversario=adversario,
        data_hora=data_hora,
        local=local,
        campeonato=campeonato,
    ).first()
    if existente:
        print(f'Esse jogo já está cadastrado (ID {existente.id}).')
        return

    db.session.add(Jogo(
        time_id=time.id,
        adversario=adversario,
        data_hora=data_hora,
        local=local,
        estadio=estadio,
        campeonato=campeonato,
        fase=fase,
    ))
    db.session.commit()
    print(f'Jogo cadastrado: {time.nome} x {adversario} — {data_texto} — {campeonato}.')


if __name__ == '__main__':
    with app.app_context():
        preparar_coluna_externa()
        try:
            registrar()
        except (ValueError, SQLAlchemyError) as erro:
            db.session.rollback()
            raise SystemExit(f'Erro: {erro}')
