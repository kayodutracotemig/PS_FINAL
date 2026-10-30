from datetime import datetime
from models.usuario_model import db

class Jogo(db.Model):
    __tablename__ = 'jogos'

    id = db.Column(db.Integer, primary_key=True)
    time_id = db.Column(db.Integer, nullable=False)
    adversario = db.Column(db.String(100), nullable=False)
    data_hora = db.Column(db.DateTime, nullable=False)
    local = db.Column(db.String(10), nullable=False)
    estadio = db.Column(db.String(150), nullable=True)
    campeonato = db.Column(db.String(100), nullable=True)
    fase = db.Column(db.String(80), nullable=True)
    football_data_match_id = db.Column(db.Integer, unique=True, nullable=True)

    def salvar(self):
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def listar_proximos_por_time(time_id, limite=5):
        agora = datetime.now()
        return Jogo.query.filter(
            Jogo.time_id == time_id,
            Jogo.data_hora >= agora
        ).order_by(Jogo.data_hora.asc()).limit(limite).all()

    @staticmethod
    def listar_passados_por_time(time_id, limite=10):
        agora = datetime.now()
        return Jogo.query.filter(
            Jogo.time_id == time_id,
            Jogo.data_hora < agora
        ).order_by(Jogo.data_hora.desc()).limit(limite).all()