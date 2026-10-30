import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # os.getenv('CHAVE', padrao): se o .env não existir, usa o padrão e o app ainda sobe
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///stadium.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-troque-isto-no-env')
    # recusa uploads maiores que 5 MB (evita encher o disco com fotos gigantes)
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
