from models.usuario_model import db

class Time(db.Model):
    __tablename__ = 'times'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)

    def salvar(self):
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def listar_todos():
        return Time.query.all()

    @staticmethod
    def buscar_por_id(time_id):
        return Time.query.get(time_id)