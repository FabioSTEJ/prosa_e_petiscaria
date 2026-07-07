import os

basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError(
        'A variavel de ambiente SECRET_KEY nao esta definida. '
        'Defina-a (ex.: no arquivo .env ou no ambiente de execucao) antes de iniciar a aplicacao.'
    )


class Config:
    SECRET_KEY = SECRET_KEY
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'data', 'comandas.db')


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
