from datetime import datetime
from models.usuario_model import db

class AvaliacaoJogo(db.Model):
    __tablename__ = 'avaliacoes'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    jogo_id = db.Column(db.Integer, db.ForeignKey('jogos.id'), nullable=False)
    nota = db.Column(db.Integer, nullable=False)
    comentario = db.Column(db.String(300), nullable=True)
    data_avaliacao = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def salvar(self):
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def buscar(usuario_id, jogo_id):
        return AvaliacaoJogo.query.filter_by(usuario_id=usuario_id, jogo_id=jogo_id).first()