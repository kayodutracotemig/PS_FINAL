import os
from sqlalchemy import text

from flask import Flask, send_from_directory

from config import Config
from models.usuario_model import db
from models.time_model import Time
# importar os models garante que o db.create_all() crie TODAS as tabelas
import models.avaliacao_model  # noqa: F401
import models.favorito_model  # noqa: F401
from controllers.usuario_controller import usuario_bp
from controllers.time_controller import time_bp
from controllers.perfil_controller import perfil_bp
from controllers.ingresso_controller import ingresso_bp
from controllers.favorito_controller import favorito_bp
from controllers.avaliacao_controller import avaliacao_bp
from controllers.rota_controller import rota_bp
from controllers.ocupacao_controller import ocupacao_bp

# Caminho ABSOLUTO da pasta frontend, calculado a partir deste arquivo.
# (O caminho relativo '../frontend' dependia de onde você rodava o comando.)
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))

app = Flask(__name__)
app.config.from_object(Config)

# Sem CORS: o próprio Flask serve o frontend (mesma origem), então o navegador
# não bloqueia nada. Isso também elimina a dependência flask-cors, que não
# estava instalada no venv enviado e fazia o servidor nem subir.

db.init_app(app)
app.register_blueprint(usuario_bp)
app.register_blueprint(time_bp)
app.register_blueprint(perfil_bp)
app.register_blueprint(ingresso_bp)
app.register_blueprint(favorito_bp)
app.register_blueprint(avaliacao_bp)
app.register_blueprint(rota_bp)
app.register_blueprint(ocupacao_bp, url_prefix='/ocupacao')


@app.route('/')
def servir_index():
    return send_from_directory(FRONTEND_DIR, 'index.html')


@app.route('/<path:filename>')
def servir_estatico(filename):
    # send_from_directory já devolve 404 sozinho se o arquivo não existir
    # e bloqueia tentativas de sair da pasta (ex.: ../../.env).
    return send_from_directory(FRONTEND_DIR, filename)


def popular_times():
    if Time.query.count() == 0:
        Time(nome='Atlético MG').salvar()
        Time(nome='Cruzeiro').salvar()


# Roda ao importar o módulo, então funciona com `python app.py` E com `flask run`.
with app.app_context():
    db.create_all()
    colunas_jogos = db.session.execute(text('PRAGMA table_info(jogos)')).fetchall()
    if colunas_jogos and 'fase' not in {coluna[1] for coluna in colunas_jogos}:
        db.session.execute(text('ALTER TABLE jogos ADD COLUMN fase VARCHAR(80)'))
        db.session.commit()
    popular_times()


if __name__ == '__main__':
    app.run(debug=True)
