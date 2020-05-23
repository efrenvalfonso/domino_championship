from flask import Blueprint, render_template, request

from app.util import leader_board, versus_leader_board, team_leader_board, versus_team_leader_board

bp = Blueprint('statistics', __name__, url_prefix='/statistics')


@bp.route('/')
def index():
    return render_template('statistics/index.html',
                           tab=request.args.get('tab', 'leader-board'),
                           leader_board=leader_board(),
                           team_leader_board=team_leader_board(),
                           versus_leader_board=versus_leader_board(),
                           versus_team_leader_board=versus_team_leader_board())
