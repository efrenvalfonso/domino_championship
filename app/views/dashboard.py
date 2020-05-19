import datetime

from flask import Blueprint, render_template
from sqlalchemy import and_

from app.forms import GameDataForm
from app.models import Game
from app.util import leader_board, versus_leader_board

bp = Blueprint('dashboard', __name__)


@bp.route('/')
def index(tv=False):
    current_game = Game.query.filter(Game.finished_at.is_(None)).one_or_none()
    last_games = Game.query. \
        filter(
        and_(Game.finished_at.isnot(None), Game.started_at.__gt__(datetime.datetime.utcnow() - datetime.timedelta(1)))). \
        order_by(Game.started_at.desc())

    if not current_game:
        return render_template('dashboard/index.html',
                               last_games=last_games,
                               leader_board=leader_board(),
                               tv=tv,
                               versus_leader_board=versus_leader_board() if tv else None,
                               leader_board_today=leader_board(True) if tv else None)

    current_game_status = 1

    if not (current_game.team1_score == 0 and current_game.team2_score == 0):
        if current_game.team1_score == 0 or current_game.team2_score == 0:  # Pollona
            current_game_status = 2
        else:
            possible_hundred_loser = None
            first_game_data = current_game.game_datas[0]

            if first_game_data.is_for_team1 and 100 <= current_game.team1_score < 150:
                possible_hundred_loser = {'is_team1': True, 'score': current_game.team1_score}
            elif (not first_game_data.is_for_team1) and 100 <= current_game.team2_score < 150:
                possible_hundred_loser = {'is_team1': False, 'score': current_game.team2_score}

            if possible_hundred_loser:
                for gd in current_game.game_datas:
                    if gd.is_for_team1 == possible_hundred_loser['is_team1']:  # While loser won
                        possible_hundred_loser['score'] -= gd.score
                    else:  # Winner wins his first data
                        if possible_hundred_loser['score'] == 0:  # Recula
                            current_game_status = 3
                        break

    title = '{}/{} vs. {}/{}'.format(
        current_game.team1_player1.name,
        current_game.team1_player2.name,
        current_game.team2_player1.name,
        current_game.team2_player2.name,
    )

    team1_game_data_form = GameDataForm(game_id=current_game.id,
                                        is_for_team1=1)
    team2_game_data_form = GameDataForm(game_id=current_game.id,
                                        is_for_team1=0)

    return render_template('dashboard/index.html',
                           title=title,
                           current_game=current_game,
                           current_game_status=current_game_status,
                           team1_game_data_form=team1_game_data_form,
                           team2_game_data_form=team2_game_data_form,
                           last_games=last_games,
                           leader_board=leader_board(),
                           tv=tv,
                           versus_leader_board=versus_leader_board() if tv else None,
                           leader_board_today=leader_board(True) if tv else None)


@bp.route('/tv')
def tv():
    return index(True)
