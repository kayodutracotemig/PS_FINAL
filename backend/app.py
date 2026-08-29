from datetime import datetime
from flask import Flask, send_from_directory
from config import Config
from models.usuario_model import db
from models.time_model import Time
from models.jogo_model import Jogo
from controllers.usuario_controller import usuario_bp
from controllers.time_controller import time_bp
from controllers.perfil_controller import perfil_bp
from controllers.ingresso_controller import ingresso_bp

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
app.register_blueprint(usuario_bp)
app.register_blueprint(time_bp)
app.register_blueprint(perfil_bp)
app.register_blueprint(ingresso_bp)

@app.route('/')
def servir_index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/css/<path:nome_arquivo>')
def servir_css(nome_arquivo):
    return send_from_directory('../frontend/css', nome_arquivo)

@app.route('/js/<path:nome_arquivo>')
def servir_js(nome_arquivo):
    return send_from_directory('../frontend/js', nome_arquivo)

def popular_times():
    if Time.query.count() == 0:
        atletico = Time(nome='Atlético MG')
        cruzeiro = Time(nome='Cruzeiro')
        atletico.salvar()
        cruzeiro.salvar()

def popular_jogos():
    if Jogo.query.count() > 0:
        return

    jogos_atletico = [
        ('29/08/2026 18:30', 'Vitória', 'casa', 'Arena MRV', 'Brasileirão'),
        ('01/09/2026 21:00', 'Cruzeiro', 'casa', 'Arena MRV', 'Copa do Brasil'),
        ('05/09/2026 18:30', 'São Paulo', 'fora', 'MorumBIS', 'Brasileirão'),
        ('09/09/2026 19:00', 'Santos', 'fora', 'Vila Belmiro', 'Sul-Americana'),
        ('12/09/2026 15:00', 'Fluminense', 'casa', 'Arena MRV', 'Brasileirão'),
        ('16/09/2026 19:00', 'Santos', 'casa', 'Arena MRV', 'Sul-Americana'),
        ('19/09/2026 15:00', 'Chapecoense', 'casa', 'Arena MRV', 'Brasileirão'),
        ('07/10/2026 16:00', 'Athletico-PR', 'fora', 'Ligga Arena', 'Brasileirão'),
        ('10/10/2026 16:00', 'Santos', 'casa', 'Arena MRV', 'Brasileirão'),
        ('17/10/2026 16:00', 'Coritiba', 'casa', 'Arena MRV', 'Brasileirão'),
        ('24/10/2026 16:00', 'Flamengo', 'fora', 'Maracanã', 'Brasileirão'),
        ('28/10/2026 16:00', 'Cruzeiro', 'casa', 'Arena MRV', 'Brasileirão'),
        ('04/11/2026 16:00', 'Botafogo', 'fora', 'Nilton Santos', 'Brasileirão'),
        ('18/11/2026 16:00', 'Mirassol', 'fora', 'Maião', 'Brasileirão'),
        ('21/11/2026 16:00', 'Corinthians', 'casa', 'Arena MRV', 'Brasileirão'),
        ('28/11/2026 16:00', 'Vasco', 'casa', 'Arena MRV', 'Brasileirão'),
        ('02/12/2026 16:00', 'Bahia', 'fora', 'Arena Fonte Nova', 'Brasileirão'),
    ]

    jogos_cruzeiro = [
        ('29/08/2026 21:20', 'Vasco', 'fora', 'São Januário', 'Brasileirão'),
        ('01/09/2026 21:00', 'Atlético-MG', 'fora', 'Arena MRV', 'Copa do Brasil'),
        ('05/09/2026 16:00', 'Athletico-PR', 'casa', 'Mineirão', 'Brasileirão'),
        ('12/09/2026 16:00', 'Santos', 'fora', 'Vila Belmiro', 'Brasileirão'),
        ('19/09/2026 16:00', 'Vitória', 'fora', 'Barradão', 'Brasileirão'),
        ('07/10/2026 16:00', 'São Paulo', 'casa', 'Mineirão', 'Brasileirão'),
        ('10/10/2026 16:00', 'RB Bragantino', 'fora', 'Nabi Abi Chedid', 'Brasileirão'),
        ('17/10/2026 16:00', 'Grêmio', 'fora', 'Arena do Grêmio', 'Brasileirão'),
        ('24/10/2026 16:00', 'Remo', 'casa', 'Mineirão', 'Brasileirão'),
        ('28/10/2026 16:00', 'Atlético-MG', 'fora', 'Arena MRV', 'Brasileirão'),
        ('04/11/2026 16:00', 'Bahia', 'casa', 'Mineirão', 'Brasileirão'),
        ('18/11/2026 16:00', 'Palmeiras', 'casa', 'Mineirão', 'Brasileirão'),
        ('21/11/2026 16:00', 'Chapecoense', 'fora', 'Arena Condá', 'Brasileirão'),
        ('28/11/2026 16:00', 'Fluminense', 'fora', 'Maracanã', 'Brasileirão'),
        ('02/12/2026 16:00', 'Internacional', 'casa', 'Mineirão', 'Brasileirão'),
    ]

    for data_str, adversario, local, estadio, campeonato in jogos_atletico:
        jogo = Jogo(
            time_id=1,
            adversario=adversario,
            data_hora=datetime.strptime(data_str, '%d/%m/%Y %H:%M'),
            local=local,
            estadio=estadio,
            campeonato=campeonato
        )
        jogo.salvar()

    for data_str, adversario, local, estadio, campeonato in jogos_cruzeiro:
        jogo = Jogo(
            time_id=2,
            adversario=adversario,
            data_hora=datetime.strptime(data_str, '%d/%m/%Y %H:%M'),
            local=local,
            estadio=estadio,
            campeonato=campeonato
        )
        jogo.salvar()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        popular_times()
        popular_jogos()
    app.run(debug=True)