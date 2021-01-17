from flask import Blueprint, render_template, request
from flask_login import login_required

from app.util import leader_board, versus_leader_board, team_leader_board, versus_team_leader_board

bp = Blueprint('statistics', __name__, url_prefix='/statistics')


@bp.route('/')
@login_required
def index():
    return render_template('statistics/index.html',
                           tab=request.args.get('tab', 'leader-board'),
                           leader_board=leader_board(),
                           team_leader_board=team_leader_board(),
                           versus_leader_board=versus_leader_board(),
                           versus_team_leader_board=versus_team_leader_board())
