from datetime import datetime

from flask import Blueprint, redirect, url_for, flash

from app import db
from app.forms import GameDataForm
from app.models import Game, GameData

bp = Blueprint('game_datas', __name__, url_prefix='/game-datas')


@bp.route('/new', methods=['POST'])
def new():
    form = GameDataForm()

    if form.validate_on_submit():
        game_data = GameData(game_id=form.game_id.data,
                             is_for_team1=form.is_for_team1.data == 1,
                             score=form.score.data)

        db.session.add(game_data)

        game = Game.query.filter(Game.id == form.game_id.data).one()

        if form.is_for_team1.data:
            game.team1_score += form.score.data
        else:
            game.team2_score += form.score.data

        db.session.commit()

        if game.team1_score >= 150 or game.team2_score >= 150:  # End of game
            game.finished_at = datetime.utcnow()

            if game.team1_score == 0 or game.team2_score == 0:  # Pollona
                game.points = 2
            else:
                hundred_loser = None

                if 100 <= game.team1_score < 150:
                    hundred_loser = {'is_team1': True, 'score': game.team1_score}
                elif 100 <= game.team2_score < 150:
                    hundred_loser = {'is_team1': False, 'score': game.team2_score}

                if hundred_loser:
                    for gd in game.game_datas:
                        if gd.is_for_team1 == hundred_loser['is_team1']:  # While loser won
                            hundred_loser['score'] -= gd.score
                        else:  # Winner wins his first data
                            if hundred_loser['score'] == 0:  # Recula
                                game.points = 3
                            break

            flash('{} de {}/{} sobre {}/{}!!!'.format(
                'Victoria' if game.points == 1 else ('POLLONA' if game.points == 2 else 'RECULA'),
                game.team1_player1.name if game.team1_score >= 150 else game.team2_player1.name,
                game.team1_player2.name if game.team1_score >= 150 else game.team2_player2.name,
                game.team2_player1.name if game.team1_score >= 150 else game.team1_player1.name,
                game.team2_player2.name if game.team1_score >= 150 else game.team1_player2.name
            ), 'info' if game.points == 1 else ('warning' if game.points == 2 else 'danger'))

            db.session.commit()
    else:
        flash(form.score.errors[-1], 'error')

    return redirect(url_for('index'))
