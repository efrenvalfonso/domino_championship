from datetime import datetime

from sqlalchemy_serializer import SerializerMixin

from app import db


class Player(db.Model, SerializerMixin):
    __tablename__ = 'players'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64, collation='NOCASE'), index=True, unique=True, nullable=False)
    manual_wins = db.Column(db.Integer, nullable=False, default=0)
    manual_loses = db.Column(db.Integer, nullable=False, default=0)

    games = db.relationship("Game",
                            primaryjoin="or_(Player.id==Game.team1_player1_id, Player.id==Game.team1_player2_id, "
                                        "Player.id==Game.team2_player1_id, Player.id==Game.team2_player2_id)")

    @property
    def text(self):
        return self.name

    def __repr__(self):
        return '<Player %r>' % self.name


class Game(db.Model):
    __tablename__ = 'games'

    id = db.Column(db.Integer, primary_key=True)

    team1_player1_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    team1_player2_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    team2_player1_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    team2_player2_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)

    started_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    finished_at = db.Column(db.DateTime)

    team1_score = db.Column(db.Integer, nullable=False, default=0)
    team2_score = db.Column(db.Integer, nullable=False, default=0)
    points = db.Column(db.Integer, nullable=False, default=1)

    team1_player1 = db.relationship('Player', foreign_keys=[team1_player1_id])
    team1_player2 = db.relationship('Player', foreign_keys=[team1_player2_id])
    team2_player1 = db.relationship('Player', foreign_keys=[team2_player1_id])
    team2_player2 = db.relationship('Player', foreign_keys=[team2_player2_id])
    game_datas = db.relationship("GameData", backref='game', order_by='GameData.timestamp', cascade="all,delete")

    def __repr__(self):
        return '<Game %r>' % '{}/{} vs. {}/{}'.format(
            self.team1_player1.name,
            self.team1_player2.name,
            self.team1_player1.name,
            self.team1_player2.name
        )


class GameData(db.Model):
    __tablename__ = 'game_datas'

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)
    is_for_team1 = db.Column(db.Boolean, nullable=False)
    score = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return '<GameData %r>' % '{} -> {}'.format(
            self.game_id,
            self.score
        )
