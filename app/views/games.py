from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash, request

from app import db
from app.forms import GameForm
from app.models import Player, Game, GameData

bp = Blueprint('games', __name__, url_prefix='/games')


@bp.route('/new', methods=['GET', 'POST'])
def new():
    open_game = Game.query.filter(Game.finished_at.is_(None)).one_or_none()

    if open_game:
        flash('Hay un juego abierto, terminelo antes de comenzar otro', 'error')

        return redirect(url_for('index'))

    form = GameForm()
    players = [(0, '')] + [(p.id, p.name) for p in Player.query.order_by(Player.name)]
    form.team1_player1_id.choices = players
    form.team1_player2_id.choices = players
    form.team2_player1_id.choices = players
    form.team2_player2_id.choices = players

    if form.validate_on_submit():
        team1_player1_id = form.team1_player1_id.data
        team1_player2_id = form.team1_player2_id.data
        team2_player1_id = form.team2_player1_id.data
        team2_player2_id = form.team2_player2_id.data

        if team1_player1_id > team1_player2_id:
            team1_player1_id, team1_player2_id = team1_player2_id, team1_player1_id

        if team2_player1_id > team2_player2_id:
            team2_player1_id, team2_player2_id = team2_player2_id, team2_player1_id

        game = Game(team1_player1_id=team1_player1_id,
                    team1_player2_id=team1_player2_id,
                    team2_player1_id=team2_player1_id,
                    team2_player2_id=team2_player2_id)
        db.session.add(game)
        db.session.commit()

        return redirect(url_for('index'))

    if request.args.get('continue') is not None:
        last_game = Game.query.filter(Game.finished_at.isnot(None)).order_by(Game.started_at.desc()).first()

        if last_game:
            if last_game.team1_score > last_game.team2_score:
                form.team1_player1_id.default = last_game.team1_player1_id
                form.team1_player2_id.default = last_game.team1_player2_id
            else:
                form.team1_player1_id.default = last_game.team2_player1_id
                form.team1_player2_id.default = last_game.team2_player2_id

    return render_template('games/new.html',
                           title='Comenzar juego',
                           players=players,
                           form=form)


@bp.route('/end/<int:game_id>/team1_won/<bool:team1_won>', methods=['POST'])
def end(game_id, team1_won):
    game = Game.query.filter(Game.id == game_id).one_or_none()

    if game:
        if team1_won:
            game_data = GameData(game_id=game_id, is_for_team1=team1_won, score=150 - game.team1_score)
            game.team1_score += game_data.score
        else:
            game_data = GameData(game_id=game_id, is_for_team1=team1_won, score=150 - game.team2_score)
            game.team2_score += game_data.score

        game.finished_at = datetime.utcnow()

        db.session.add(game_data)
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
        flash('Ha ocurrido un error', 'error')

    return redirect(url_for('index'))


@bp.route('/reopen-last-game', methods=['POST'])
def reopen_last_game():
    if Game.query.filter(Game.finished_at.is_(None)).one_or_none():
        flash('Hay un juego abierto, terminelo antes de comenzar otro', 'error')
    else:
        last_game = Game.query.order_by(Game.finished_at.desc()).first()

        if last_game:
            game_data = last_game.game_datas[-1]

            if game_data.is_for_team1:
                last_game.team1_score -= game_data.score
            else:
                last_game.team2_score -= game_data.score

            last_game.finished_at = None
            last_game.points = 1
            db.session.delete(game_data)
            db.session.commit()
        else:
            flash('No hay juegos en el sistema', 'error')

    return redirect(url_for('index'))


@bp.route('delete/<int:game_id>', methods=['POST'])
def delete(game_id):
    game = Game.query.filter(Game.id == game_id).one_or_none()

    if game:
        db.session.delete(game)
        db.session.commit()
    else:
        flash('Ha ocurrido un error', 'error')

    return redirect(url_for('index'))
