from models.usuario_model import db

class Favorito(db.Model):
    __tablename__ = 'favoritos'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    jogo_id = db.Column(db.Integer, db.ForeignKey('jogos.id'), nullable=False)

    def salvar(self):
        db.session.add(self)
        db.session.commit()

    def deletar(self):
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def buscar(usuario_id, jogo_id):
        return Favorito.query.filter_by(usuario_id=usuario_id, jogo_id=jogo_id).first()

    @staticmethod
    def listar_por_usuario(usuario_id):
        return Favorito.query.filter_by(usuario_id=usuario_id).all()