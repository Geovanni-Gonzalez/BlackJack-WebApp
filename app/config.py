"""Environment-aware configuration.

Select with the APP_ENV variable (development | production).
Secrets are read from the environment; production refuses the insecure
development fallback for SECRET_KEY.
"""
import os


class BaseConfig:
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///blackjack.db')
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-only-insecure-key')
    RATELIMIT_DEFAULTS = ["1000 per day", "200 per hour"]


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class ProductionConfig(BaseConfig):
    DEBUG = False

    def __init__(self):
        if os.environ.get('SECRET_KEY') in (None, '', 'dev-only-insecure-key'):
            raise RuntimeError("SECRET_KEY must be set to a secure value in production.")
        self.SECRET_KEY = os.environ['SECRET_KEY']


def get_config():
    env = os.environ.get('APP_ENV', 'development').lower()
    return ProductionConfig() if env.startswith('prod') else DevelopmentConfig()
