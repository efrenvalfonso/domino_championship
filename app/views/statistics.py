from flask import Blueprint, render_template, request
from sqlalchemy import func, or_, case, and_, not_
from sqlalchemy.orm import aliased

from app import db
from app.models import Player, Game
from app.util import leader_board, versus_leader_board

bp = Blueprint('statistics', __name__, url_prefix='/statistics')


@bp.route('/')
def index():
    return render_template('statistics/index.html',
                           tab=request.args.get('tab', 'leader-board'),
                           leader_board=leader_board(),
                           team_leader_board=team_leader_board(),
                           versus_leader_board=versus_leader_board(),
                           versus_team_leader_board=versus_team_leader_board())


def team_leader_board():
    players1 = aliased(Player)
    players2 = aliased(Player)

    return db.session.query(
        players1.id,
        players1.name,
        players2.id,
        players2.name,
        func.sum(func.coalesce(case([
            (and_(Game.team1_player1_id == players1.id, Game.team1_player2_id == players2.id),
             case([(Game.team1_score >= 150, Game.points)])),
            (and_(Game.team2_player1_id == players1.id, Game.team2_player2_id == players2.id),
             case([(Game.team2_score >= 150, Game.points)]))
        ]), 0)).label('wins_score'),
        func.sum(func.coalesce(case([
            (and_(Game.team1_player1_id == players1.id, Game.team1_player2_id == players2.id),
             case([(Game.team1_score < 150, Game.points)])),
            (and_(Game.team2_player1_id == players1.id, Game.team2_player2_id == players2.id),
             case([(Game.team2_score < 150, Game.points)]))
        ]), 0)).label('loses_score'),
        func.sum(func.coalesce(case([
            (and_(Game.team1_player1_id == players1.id, Game.team1_player2_id == players2.id),
             case([(Game.team1_score < 150, -1)], else_=1) * Game.points),
            (and_(Game.team2_player1_id == players1.id, Game.team2_player2_id == players2.id),
             case([(Game.team2_score < 150, -1)], else_=1) * Game.points)
        ]), 0)).label('balance'),
    ). \
        select_from(Game). \
        join(players1,
             or_(Game.team1_player1_id == players1.id,
                 Game.team2_player1_id == players1.id)). \
        join(players2,
             or_(Game.team1_player2_id == players2.id,
                 Game.team2_player2_id == players2.id)). \
        filter(Game.finished_at.isnot(None), players1.id != players2.id). \
        group_by(players1.id, players2.id). \
        having(or_(db.text('wins_score > 0'), db.text('loses_score > 0'))). \
        order_by(db.text(request.args.get('team_leader_board_order_by', 'balance DESC, wins_score DESC')))


def versus_team_leader_board():
    players1 = aliased(Player)
    players2 = aliased(Player)
    other_players1 = aliased(Player)
    other_players2 = aliased(Player)

    return db.session.query(
        players1.id,
        players1.name,
        players2.id,
        players2.name,
        other_players1.id,
        other_players1.name,
        other_players2.id,
        other_players2.name,
        func.sum(func.coalesce(case([
            (and_(Game.team1_player1_id == players1.id, Game.team1_player2_id == players2.id),
             case([(Game.team1_score >= 150, Game.points)])),
            (and_(Game.team2_player1_id == players1.id, Game.team2_player2_id == players2.id),
             case([(Game.team2_score >= 150, Game.points)]))
        ]), 0)).label('wins_score'),
        func.sum(func.coalesce(case([
            (and_(Game.team1_player1_id == players1.id, Game.team1_player2_id == players2.id),
             case([(Game.team1_score < 150, Game.points)])),
            (and_(Game.team2_player1_id == players1.id, Game.team2_player2_id == players2.id),
             case([(Game.team2_score < 150, Game.points)]))
        ]), 0)).label('loses_score'),
        func.sum(func.coalesce(case([
            (and_(Game.team1_player1_id == players1.id, Game.team1_player2_id == players2.id),
             case([(Game.team1_score < 150, -1)], else_=1) * Game.points),
            (and_(Game.team2_player1_id == players1.id, Game.team2_player2_id == players2.id),
             case([(Game.team2_score < 150, -1)], else_=1) * Game.points)
        ]), 0)).label('balance'),
    ). \
        select_from(Game). \
        join(players1,
             or_(Game.team1_player1_id == players1.id,
                 Game.team2_player1_id == players1.id)). \
        join(players2,
             or_(Game.team1_player2_id == players2.id,
                 Game.team2_player2_id == players2.id)). \
        join(other_players1,
             or_(Game.team1_player1_id == other_players1.id,
                 Game.team2_player1_id == other_players1.id)). \
        join(other_players2,
             or_(Game.team1_player2_id == other_players2.id,
                 Game.team2_player2_id == other_players2.id)). \
        filter(and_(Game.finished_at.isnot(None), players1.id != other_players1.id, players2.id != other_players2.id)). \
        group_by(players1.id, players2.id, other_players1.id, other_players2.id). \
        having(or_(db.text('wins_score > 0'), db.text('loses_score > 0'))). \
        order_by(db.text(request.args.get('versus_team_leader_board_order_by', 'balance DESC, wins_score DESC')))
