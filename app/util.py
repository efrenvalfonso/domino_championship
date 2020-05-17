from flask import request
from sqlalchemy import func, case, or_
from werkzeug.routing import BaseConverter

from app import db
from app.models import Player, Game


class ListConverter(BaseConverter):

    def to_python(self, value):
        return value.split('+')

    def to_url(self, values):
        return '+'.join(BaseConverter.to_url(self, value) for value in values)


def leader_board():
    return db.session.query(
        Player.id,
        Player.name,
        (func.sum(func.coalesce(case([
            (or_(Game.team1_player1_id == Player.id, Game.team1_player2_id == Player.id),
             case([(Game.team1_score >= 150, Game.points)])),
            (or_(Game.team2_player1_id == Player.id, Game.team2_player2_id == Player.id),
             case([(Game.team2_score >= 150, Game.points)]))
        ]), 0)) + Player.manual_wins).label('wins_score'),
        (func.sum(func.coalesce(case([
            (or_(Game.team1_player1_id == Player.id, Game.team1_player2_id == Player.id),
             case([(Game.team1_score < 150, Game.points)])),
            (or_(Game.team2_player1_id == Player.id, Game.team2_player2_id == Player.id),
             case([(Game.team2_score < 150, Game.points)]))
        ]), 0)) + Player.manual_loses).label('loses_score'),
        (func.sum(func.coalesce(case([
            (or_(Game.team1_player1_id == Player.id, Game.team1_player2_id == Player.id),
             case([(Game.team1_score < 150, -1)], else_=1) * Game.points),
            (or_(Game.team2_player1_id == Player.id, Game.team2_player2_id == Player.id),
             case([(Game.team2_score < 150, -1)], else_=1) * Game.points)
        ]), 0)) + Player.manual_wins - Player.manual_loses).label('balance'),
    ). \
        select_from(Player). \
        join(Game,
             or_(Game.team1_player1_id == Player.id,
                 Game.team1_player2_id == Player.id,
                 Game.team2_player1_id == Player.id,
                 Game.team2_player2_id == Player.id),
             isouter=True). \
        group_by(Player.id). \
        order_by(db.text(request.args.get('leader_board_order_by', 'balance DESC')))
