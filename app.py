import os
from flask import Flask, render_template, redirect, request, url_for
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

import secrets
secret_key = secrets.token_urlsafe(16)
app.secret_key = secret_key

bootstrap = Bootstrap5(app)
csrf = CSRFProtect(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

from models import *


class TipForm(FlaskForm):
    horse = StringField('Horse', validators=[DataRequired()])
    time = StringField('Time', validators=[DataRequired()])
    meeting = StringField('Meeting', validators=[DataRequired()])
    min_price = StringField('Mininum Price', validators=[DataRequired()])
    bet_type = StringField('Bet Type', validators=[DataRequired()])
    stake = StringField('Stake', validators=[DataRequired()])
    submit = SubmitField('Add Tip')


class PunterForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(3, 20)])
    surname = StringField('Surname', validators=[DataRequired(), Length(3, 40)])
    phone_number = StringField('Phone Number', validators=[DataRequired(), Length(12, 14)])
    submit = SubmitField('Add User')


@app.route('/', methods=['GET', 'POST'])
def root():
    tips = db.session.query(Tip).order_by(Tip.id)
    form = TipForm()
    if form.validate_on_submit():
        tip = Tip(horse=form.horse.data, time=form.time.data, meeting=form.meeting.data, min_price=form.min_price.data, bet_type=form.bet_type.data, stake=form.stake.data)
        db.session.add(tip)
        db.session.commit()
        return redirect(url_for('root'))
    return render_template('index.html', form=form, tips=tips)


@app.route('/punters/', methods=['GET', 'POST'])
def punters():
    punters = db.session.query(Punter).order_by(Punter.id)
    form = PunterForm()        
    if form.validate_on_submit():
        punter = Punter(first_name=form.first_name.data, surname=form.surname.data, phone_number=form.phone_number.data)
        db.session.add(punter)
        db.session.commit()
        return redirect(url_for('punters'))
    return render_template('punters.html', form=form, punters=punters)


if __name__ == '__main__':
    app.run()
