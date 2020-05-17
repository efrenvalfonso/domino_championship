from flask import Blueprint, render_template, redirect, url_for, flash, request
from sqlalchemy import and_

from app import db
from app.forms import GameForm
from app.models import Player, Game

bp = Blueprint('games', __name__, url_prefix='/games')


@bp.route('/new', methods=['GET', 'POST'])
def new():
    open_game = Game.query.filter(Game.finished_at.is_(None)).one_or_none()

    if open_game:
        flash('Hay un juego abierto, terminelo antes de comenzar otro', 'info')

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
