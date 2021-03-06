from datetime import datetime, timedelta

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


def leader_board(today=False, active=True, min_games_count=0, global_stats=False):
    query = db.session.query(
        Player.id,
        Player.name,
        (func.sum(func.coalesce(case([
            (or_(Game.team1_player1_id == Player.id, Game.team1_player2_id == Player.id),
             case([(Game.team1_score >= 150, Game.points)])),
            (or_(Game.team2_player1_id == Player.id, Game.team2_player2_id == Player.id),
             case([(Game.team2_score >= 150, Game.points)]))
        ]), 0)) + (0 if today else Player.manual_wins)).label('wins_score'),
        (func.sum(func.coalesce(case([
            (or_(Game.team1_player1_id == Player.id, Game.team1_player2_id == Player.id),
             case([(Game.team1_score < 150, Game.points)])),
            (or_(Game.team2_player1_id == Player.id, Game.team2_player2_id == Player.id),
             case([(Game.team2_score < 150, Game.points)]))
        ]), 0)) + (0 if today else Player.manual_loses)).label('loses_score'),
        (func.sum(func.coalesce(case([
            (or_(Game.team1_player1_id == Player.id, Game.team1_player2_id == Player.id),
             case([(Game.team1_score < 150, -1)], else_=1) * Game.points),
            (or_(Game.team2_player1_id == Player.id, Game.team2_player2_id == Player.id),
             case([(Game.team2_score < 150, -1)], else_=1) * Game.points)
        ]), 0)) + (0 if today else (Player.manual_wins - Player.manual_loses))).label('balance'),
        func.sum(func.coalesce(case([
            (or_(Game.team1_player1_id == Player.id, Game.team1_player2_id == Player.id,
                 Game.team2_player1_id == Player.id, Game.team2_player2_id == Player.id), 1)], else_=0),
            0)).label('games_count')
    ). \
        select_from(Player). \
        join(Game,
             or_(Game.team1_player1_id == Player.id,
                 Game.team1_player2_id == Player.id,
                 Game.team2_player1_id == Player.id,
                 Game.team2_player2_id == Player.id),
             isouter=True)

    if today:
        today = datetime.now() - timedelta(hours=8)
        beginning_of_today = datetime(today.year, today.month, today.day, 8, 0).astimezone(tz.gettz('UTC'))
        query = query.filter(Game.finished_at.isnot(None), Game.started_at.__gt__(beginning_of_today))
    else:
        if global_stats:
            query = query.filter(Game.finished_at.isnot(None)). \
                having(db.text(f'games_count {">=" if active else "<"} {str(min_games_count)}'))
        else:
            today = datetime.now() - timedelta(hours=8)
            beginning_of_year = datetime(today.year, 1, 1, 8, 0).astimezone(tz.gettz('UTC'))
            query = query.filter(Game.finished_at.isnot(None), Game.started_at.__gt__(beginning_of_year)). \
                having(db.text(f'games_count {">=" if active else "<"} {str(min_games_count)}'))

    return query. \
        group_by(Player.id). \
        order_by(db.text(request.args.get('leader_board_order_by', 'balance DESC, wins_score DESC')))


def team_leader_board(global_stats=False):
    players1 = aliased(Player)
    players2 = aliased(Player)

    query = db.session.query(
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
                 Game.team2_player2_id == players2.id))

    if global_stats:
        query = query.filter(Game.finished_at.isnot(None), players1.id != players2.id)
    else:
        today = datetime.now() - timedelta(hours=8)
        beginning_of_year = datetime(today.year, 1, 1, 8, 0).astimezone(tz.gettz('UTC'))
        query = query.filter(Game.finished_at.isnot(None), Game.started_at.__gt__(beginning_of_year), players1.id != players2.id)

    return query.group_by(players1.id, players2.id). \
        having(or_(db.text('wins_score > 0'), db.text('loses_score > 0'))). \
        order_by(db.text(request.args.get('team_leader_board_order_by', 'balance DESC, wins_score DESC')))


def versus_leader_board(global_stats=False):
    players = aliased(Player)
    other_players = aliased(Player)

    query = db.session.query(
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
                 Game.team2_player2_id == other_players.id))

    if global_stats:
        query = query.filter(Game.finished_at.isnot(None))
    else:
        today = datetime.now() - timedelta(hours=8)
        beginning_of_year = datetime(today.year, 1, 1, 8, 0).astimezone(tz.gettz('UTC'))
        query = query.filter(Game.finished_at.isnot(None), Game.started_at.__gt__(beginning_of_year))

    return query.group_by(players.id, other_players.id). \
        having(or_(db.text('wins_score > 0'), db.text('loses_score > 0'))). \
        order_by(db.text(request.args.get('versus_leader_board_order_by', 'balance DESC, wins_score DESC')))


def versus_team_leader_board(today=False, global_stats=False):
    players1 = aliased(Player)
    players2 = aliased(Player)
    other_players1 = aliased(Player)
    other_players2 = aliased(Player)

    query = db.session.query(
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
                 Game.team2_player2_id == other_players2.id))

    if today:
        today = datetime.now() - timedelta(hours=8)
        beginning_of_today = datetime(today.year, today.month, today.day, 8, 0).astimezone(tz.gettz('UTC'))
        query = query.filter(Game.finished_at.isnot(None),
                             players1.id != other_players1.id,
                             players2.id != other_players2.id,
                             Game.started_at.__gt__(beginning_of_today))
    else:
        if global_stats:
            query = query.filter(Game.finished_at.isnot(None),
                                 players1.id != other_players1.id,
                                 players2.id != other_players2.id)
        else:
            today = datetime.now() - timedelta(hours=8)
            beginning_of_year = datetime(today.year, 1, 1, 8, 0).astimezone(tz.gettz('UTC'))
            query = query.filter(Game.finished_at.isnot(None),
                                 Game.started_at.__gt__(beginning_of_year),
                                 players1.id != other_players1.id,
                                 players2.id != other_players2.id)

    return query.group_by(players1.id, players2.id, other_players1.id, other_players2.id). \
        having(or_(db.text('wins_score > 0'), db.text('loses_score > 0'))). \
        order_by(db.text(request.args.get('versus_team_leader_board_order_by', 'balance DESC, wins_score DESC')))


def total_games_leader_board(won=True, points=None, global_stats=False):
    query = db.session.query(
        Player.id,
        Player.name,
        func.sum(func.coalesce(case([
            (or_(Game.team1_player1_id == Player.id, Game.team1_player2_id == Player.id),
             case([((Game.team1_score >= 150) if won else (Game.team1_score < 150), 1)])),
            (or_(Game.team2_player1_id == Player.id, Game.team2_player2_id == Player.id),
             case([((Game.team2_score >= 150) if won else (Game.team2_score < 150), 1)]))
        ]), 0)).label('count'),
    ). \
        select_from(Game). \
        join(Player,
             or_(Game.team1_player1_id == Player.id,
                 Game.team1_player2_id == Player.id,
                 Game.team2_player1_id == Player.id,
                 Game.team2_player2_id == Player.id),
             isouter=True)

    if global_stats:
        query = query.filter(Game.finished_at.isnot(None),
                             (Game.points == points) if points else True)
    else:
        today = datetime.now() - timedelta(hours=8)
        beginning_of_year = datetime(today.year, 1, 1, 8, 0).astimezone(tz.gettz('UTC'))
        query = query.filter(Game.finished_at.isnot(None),
                             Game.started_at.__gt__(beginning_of_year),
                             (Game.points == points) if points else True)

    return query.group_by(Player.id). \
        having(db.text('count > 0')). \
        order_by(db.text('count DESC'))
