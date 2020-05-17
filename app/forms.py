from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, IntegerField
from wtforms.validators import DataRequired, Length, NumberRange, InputRequired
from wtforms.widgets import HiddenInput


class HiddenInteger(IntegerField):
    widget = HiddenInput()


class PlayerForm(FlaskForm):
    name = StringField('Nombre', validators=[InputRequired(message='El nombre es requerido'),
                                             DataRequired(message='El nombre es requerido'),
                                             Length(max=64, message='El nombre es demasiado largo')])
    manual_wins = IntegerField('Puntos ganados iniciales', default=0)
    manual_loses = IntegerField('Puntos perdidos iniciales', default=0)
    submit = SubmitField('Guardar')


class GameForm(FlaskForm):
    team1_player1_id = SelectField('Pareja 1 / Jugador 1', coerce=int,
                                   validators=[DataRequired(message='Debe definir un jugador')])
    team1_player2_id = SelectField('Pareja 1 / Jugador 2', coerce=int,
                                   validators=[DataRequired(message='Debe definir un jugador')])
    team2_player1_id = SelectField('Pareja 2 / Jugador 1', coerce=int,
                                   validators=[DataRequired(message='Debe definir un jugador')])
    team2_player2_id = SelectField('Pareja 2 / Jugador 2', coerce=int,
                                   validators=[DataRequired(message='Debe definir un jugador')])
    submit = SubmitField('Comenzar')


class GameDataForm(FlaskForm):
    game_id = HiddenInteger(validators=[DataRequired()])
    is_for_team1 = HiddenInteger(validators=[InputRequired()])
    score = IntegerField('Puntos', validators=[InputRequired(message='Inserte los puntos de la data'),
                                               NumberRange(min=1,
                                                           message='Los puntos tienen que ser numeros positivos')])
    submit = SubmitField('Anotar')
