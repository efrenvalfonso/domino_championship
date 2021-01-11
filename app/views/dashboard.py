import math
from datetime import datetime, timedelta

from dateutil.tz import tz
from flask import Blueprint, render_template
from sqlalchemy import and_

from app.forms import GameDataForm
from app.models import Game
from app.util import leader_board, versus_team_leader_board, total_games_leader_board

bp = Blueprint('dashboard', __name__)


@bp.route('/')
def index(tv=False, global_stats=False):
    current_game = Game.query.filter(Game.finished_at.is_(None)).one_or_none()
    today = datetime.now() - timedelta(hours=8)
    beginning_of_today = datetime(today.year, today.month, today.day, 8, 0).astimezone(tz.gettz('UTC'))
    today_games = Game.query. \
        filter(and_(Game.finished_at.isnot(None), Game.started_at.__gt__(beginning_of_today))). \
        order_by(Game.started_at.desc())
    min_games_count = 0
    days_off = 24
    if global_stats:
        first_game = Game.query.order_by(Game.started_at).first()
    else:
        beginning_of_year = datetime(today.year, 1, 1, 8, 0).astimezone(tz.gettz('UTC'))
        first_game = Game.query.filter(Game.started_at.__gt__(beginning_of_year)).order_by(Game.started_at).first()

    if first_game:
        starting_day = first_game.started_at
        starting_day = datetime(starting_day.year, starting_day.month, starting_day.day, 0, 0)
        min_games_count = 7 * ((datetime.now() - starting_day).days / 7)
        min_games_count = int(math.ceil(min_games_count)) - days_off

    if not current_game:
        return render_template('dashboard/index.html',
                               today_games=today_games.limit(10) if tv else today_games,
                               leader_board=leader_board(min_games_count=min_games_count,
                                                         global_stats=global_stats),
                               inactive_leader_board=leader_board(active=False,
                                                                  min_games_count=min_games_count,
                                                                  global_stats=global_stats),
                               tv=tv,
                               min_games_count=min_games_count,
                               leader_board_today=leader_board(True,
                                                               global_stats=global_stats) if tv else None,
                               versus_team_leader_board=versus_team_leader_board(True,
                                                                                 global_stats=global_stats) if tv else None,
                               total_games_leader_board=total_games_leader_board(global_stats=global_stats) if tv else None,
                               total_single_games_leader_board=total_games_leader_board(points=1,
                                                                                        global_stats=global_stats) if tv else None,
                               total_double_games_leader_board=total_games_leader_board(points=2,
                                                                                        global_stats=global_stats) if tv else None,
                               total_triple_games_leader_board=total_games_leader_board(points=3,
                                                                                        global_stats=global_stats) if tv else None,
                               total_lost_games_leader_board=total_games_leader_board(won=False,
                                                                                      global_stats=global_stats) if tv else None,
                               total_lost_single_games_leader_board=total_games_leader_board(won=False,
                                                                                             points=1,
                                                                                             global_stats=global_stats) if tv else None,
                               total_lost_double_games_leader_board=total_games_leader_board(won=False,
                                                                                             points=2,
                                                                                             global_stats=global_stats) if tv else None,
                               total_lost_triple_games_leader_board=total_games_leader_board(won=False,
                                                                                             points=3,
                                                                                             global_stats=global_stats) if tv else None)

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
                           today_games=today_games.limit(10) if tv else today_games,
                           min_games_count=min_games_count,
                           leader_board=leader_board(min_games_count=min_games_count,
                                                     global_stats=global_stats),
                           inactive_leader_board=leader_board(active=False,
                                                              min_games_count=min_games_count,
                                                              global_stats=global_stats),
                           tv=tv,
                           leader_board_today=leader_board(True,
                                                           global_stats=global_stats) if tv else None,
                           versus_team_leader_board=versus_team_leader_board(True,
                                                                             global_stats=global_stats) if tv else None,
                           total_games_leader_board=total_games_leader_board(global_stats=global_stats) if tv else None,
                           total_single_games_leader_board=total_games_leader_board(points=1,
                                                                                    global_stats=global_stats) if tv else None,
                           total_double_games_leader_board=total_games_leader_board(points=2,
                                                                                    global_stats=global_stats) if tv else None,
                           total_triple_games_leader_board=total_games_leader_board(points=3,
                                                                                    global_stats=global_stats) if tv else None,
                           total_lost_games_leader_board=total_games_leader_board(won=False,
                                                                                  global_stats=global_stats) if tv else None,
                           total_lost_single_games_leader_board=total_games_leader_board(won=False,
                                                                                         points=1,
                                                                                         global_stats=global_stats) if tv else None,
                           total_lost_double_games_leader_board=total_games_leader_board(won=False,
                                                                                         points=2,
                                                                                         global_stats=global_stats) if tv else None,
                           total_lost_triple_games_leader_board=total_games_leader_board(won=False,
                                                                                         points=3,
                                                                                         global_stats=global_stats) if tv else None)


@bp.route('/tv')
def tv():
    return index(tv=True)


@bp.route('/global-stats')
def tv():
    return index(global_stats=True)


@bp.route('/tv/global-stats')
def tv():
    return index(tv=True, global_stats=True)
