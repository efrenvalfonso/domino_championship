from flask import Blueprint, render_template, redirect, url_for, jsonify
from sqlalchemy.orm import load_only

from app import db
from app.forms import PlayerForm, PlayerAnnotateForm
from app.models import Player

bp = Blueprint('players', __name__, url_prefix='/players')


@bp.route('/')
def index():
    players = Player.query.order_by(Player.name)

    return render_template('players/index.html', players=players)


@bp.route('/new', methods=['GET', 'POST'])
def new():
    form = PlayerForm()

    if form.validate_on_submit():
        player = Player(name=form.name.data,
                        manual_wins=form.manual_wins.data,
                        manual_loses=form.manual_loses.data)
        db.session.add(player)
        db.session.commit()

        return redirect(url_for('players.index'))
    return render_template('players/new.html', title='Nuevo jugador', form=form)


@bp.route('/annotate', methods=['GET', 'POST'])
def annotate():
    form = PlayerAnnotateForm()
    form.id.choices = [(0, '')] + [(p.id, p.name) for p in Player.query.order_by(Player.name).all()]

    if form.validate_on_submit():
        player = Player.query.filter(Player.id == form.id.data).one_or_none()

        if player:
            player.manual_wins += form.manual_wins.data
            player.manual_loses += form.manual_loses.data

            db.session.commit()

        return redirect(url_for('players.index'))
    return render_template('players/annotate.html', title='Anotar partidos', form=form)


@bp.route('/game-player-for/', defaults={'current_players': []})
@bp.route('/game-player-for/<list:current_players>')
def game_player_for(current_players):
    players = Player.query. \
        filter(~Player.id.in_(current_players or [])). \
        options(load_only(Player.id, Player.name)). \
        order_by(Player.name)
    result = [p.to_dict(only=('id', 'text')) for p in players]

    return jsonify({'results': result})
