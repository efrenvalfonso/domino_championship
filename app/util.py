from datetime import datetime

from dateutil.tz import tz
from flask import request
from sqlalchemy import func, case, or_, and_, not_
from sqlalchemy.orm import aliased
from werkzeug.routing import BaseConverter

from app import db
from app.models import Player, Game


class ListConverter(BaseConverter):

    def to_python(self, value):
        return value.split('+')

    def to_url(self, values):
        return '+'.join(BaseConverter.to_url(self, value) for value in values)


class BooleanConverter(BaseConverter):

    def to_python(self, value):
        return False if value == '0' else True

    def to_url(self, value):
        return '1' if value else '0'


def leader_board(today=False):
    query = db.session.query(
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
             isouter=True)

    if today:
        today = datetime.now()
        beginning_of_today = datetime(today.year, today.month, today.day, 0, 0).astimezone(tz.gettz('UTC'))

        query = query.filter(and_(Game.finished_at.isnot(None), Game.started_at.__gt__(beginning_of_today)))
    else:
        query = query.filter(Game.finished_at.isnot(None))

    return query. \
        group_by(Player.id). \
        order_by(db.text(request.args.get('leader_board_order_by', 'balance DESC, wins_score DESC')))


def versus_leader_board():
    players = aliased(Player)
    other_players = aliased(Player)

    return db.session.query(
        players.id,
        players.name,
        other_players.id,
        other_players.name,
        func.sum(func.coalesce(case([
            (and_(or_(Game.team1_player1_id == players.id, Game.team1_player2_id == players.id),
                  not_(or_(Game.team1_player1_id == other_players.id, Game.team1_player2_id == other_players.id))),
             case([(Game.team1_score >= 150, Game.points)])),
            (and_(or_(Game.team2_player1_id == players.id, Game.team2_player2_id == players.id),
                  not_(or_(Game.team2_player1_id == other_players.id, Game.team2_player2_id == other_players.id))),
             case([(Game.team2_score >= 150, Game.points)]))
        ]), 0)).label('wins_score'),
        func.sum(func.coalesce(case([
            (and_(or_(Game.team1_player1_id == players.id, Game.team1_player2_id == players.id),
                  not_(or_(Game.team1_player1_id == other_players.id, Game.team1_player2_id == other_players.id))),
             case([(Game.team1_score < 150, Game.points)])),
            (and_(or_(Game.team2_player1_id == players.id, Game.team2_player2_id == players.id),
                  not_(or_(Game.team2_player1_id == other_players.id, Game.team2_player2_id == other_players.id))),
             case([(Game.team2_score < 150, Game.points)]))
        ]), 0)).label('loses_score'),
        func.sum(func.coalesce(case([
            (and_(or_(Game.team1_player1_id == players.id, Game.team1_player2_id == players.id),
                  not_(or_(Game.team1_player1_id == other_players.id, Game.team1_player2_id == other_players.id))),
             case([(Game.team1_score < 150, -1)], else_=1) * Game.points),
            (and_(or_(Game.team2_player1_id == players.id, Game.team2_player2_id == players.id),
                  not_(or_(Game.team2_player1_id == other_players.id, Game.team2_player2_id == other_players.id))),
             case([(Game.team2_score < 150, -1)], else_=1) * Game.points)
        ]), 0)).label('balance'),
    ). \
        select_from(Game). \
        join(players,
             or_(Game.team1_player1_id == players.id,
                 Game.team1_player2_id == players.id,
                 Game.team2_player1_id == players.id,
                 Game.team2_player2_id == players.id)). \
        join(other_players,
             or_(Game.team1_player1_id == other_players.id,
                 Game.team1_player2_id == other_players.id,
                 Game.team2_player1_id == other_players.id,
                 Game.team2_player2_id == other_players.id)). \
        filter(Game.finished_at.isnot(None)). \
        group_by(players.id, other_players.id). \
        having(or_(db.text('wins_score > 0'), db.text('loses_score > 0'))). \
        order_by(db.text(request.args.get('versus_leader_board_order_by', 'balance DESC, wins_score DESC')))
