from flask import Flask
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from os import environ

from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
bootstrap = Bootstrap(app)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

from app.models import User


@login_manager.user_loader
def load_user(username):
    return User(username) if username == environ.get('USERNAME') else None


from .util import ListConverter, BooleanConverter

app.url_map.converters['list'] = ListConverter
app.url_map.converters['bool'] = BooleanConverter

from app import models
from app.views import auth, dashboard, players, games, game_datas, statistics

app.register_blueprint(auth.bp)
app.register_blueprint(dashboard.bp)
app.register_blueprint(players.bp)
app.register_blueprint(games.bp)
app.register_blueprint(game_datas.bp)
app.register_blueprint(statistics.bp)
app.add_url_rule('/', endpoint='index')
