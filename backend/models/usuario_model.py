from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Usuario(db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    time_id = db.Column(db.Integer, nullable=True)
    foto = db.Column(db.String(300), nullable=True)
    token = db.Column(db.String(200), nullable=True)

    rua = db.Column(db.String(150), nullable=True)
    numero = db.Column(db.String(20), nullable=True)
    bairro = db.Column(db.String(100), nullable=True)
    cidade = db.Column(db.String(100), nullable=True)
    estado = db.Column(db.String(2), nullable=True)

    def salvar(self):
        db.session.add(self)
        db.session.commit()

    def atualizar(self):
        db.session.commit()

    def deletar(self):
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def listar_todos():
        return Usuario.query.all()

    @staticmethod
    def buscar_por_id(usuario_id):
        return Usuario.query.get(usuario_id)

    @staticmethod
    def buscar_por_email(email):
        return Usuario.query.filter_by(email=email).first()

    @staticmethod
    def buscar_por_token(token):
        return Usuario.query.filter_by(token=token).first()