from app import app, db
from app.models import Player, Game, GameData


@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'Player': Player,
        'Game': Game,
        'GameData': GameData,
    }
