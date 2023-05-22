import os
import re
from flask import Flask, render_template, redirect, request, url_for
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

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

twilio = Client(app.config['TWILIO_ACCOUNT_SID'], app.config['TWILIO_AUTH_TOKEN'])

response_regex = r'(\d*)\s+(\d*/\d*|\d\.\d)'


from models import *


@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/logout')
def logout():
    return 'Logout'

@app.route('/profile')
def profile():
    return render_template('profile.html')


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

        punters = db.session.query(Punter)
        for punter in punters:
            message = twilio.messages.create(
                body="Are you available and able to place a bet today.  Please answer 'Yes' to obtain the bet information or 'No' if you are not available",
                from_='+447893951917',
                to=punter.phone_number
            )

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


@app.route('/incoming_sms', methods=['POST'])
@csrf.exempt
def incoming_sms():
    body = request.values['Body']
    if body.lower() == "yes":
        return handle_yes()
    elif body.lower() == "no":
        return handle_no()
    else:
        from_number = request.values['From']
        return handle_bet(body, from_number)


def handle_bet(body, from_number):
    response = MessagingResponse()
    cleaned_body = body.replace(u'£', '').replace(u'@', ' ')
    match = re.search(response_regex, cleaned_body)
    stake = match.group(1).strip()
    price = match.group(2).strip()
    if match:
        print("we have a match £{} @ {}".format(stake, price))
        tip = db.session.query(Tip).order_by(Tip.id.desc()).first()
        if tip is not None:
            punter = db.session.query(Punter).filter(Punter.phone_number == from_number).first()
            if punter is not None:
                bet = Bet(punter_id=punter.id, tip_id=tip.id, stake=stake, price=price)
                db.session.add(bet)
                db.session.commit()
            else:
                print("Unable to find punter with phone number {} for bet of {}@{}".format(from_number, stake, price))
        else: 
            print("Unable to find a tip to record bet of {}@{}".format(stake, price))
        
        response.message("We have recorded your bet of £{} at {}. Thank you".format(stake, price))
    else:
        print("received response '{}'".format(body))
        response.message("I'm sorry, I don't understand, someone will get in touch")
    return str(response)


def handle_missing_from_number():
    response = MessagingResponse()
    response.message("Something went wrong on our end, someone will be in touch shortly")
    return str(response)


def handle_yes():
    tip = db.session.query(Tip).order_by(Tip.id.desc()).first()
    stake = tip.stake
    if not stake.startswith('£'):
        stake = "£{}".format(stake)
    response = MessagingResponse()
    response.message("Place {} ({}) on {} in the {} at {} don't take less than {}. When you have placed the bet please CONFIRM it with us by replying to this message with ONLY the stake and price of the bet you placed e.g. £90 4/1".format(stake, tip.bet_type, tip.horse, tip.time, tip.meeting, tip.min_price))
    return str(response)


def handle_no():
    response = MessagingResponse()
    response.message("Thanks, we'll be in touch next time we have a tip")
    return str(response)


def is_sms_request():
    return 'MessageSid' in request.values.keys()


if __name__ == '__main__':
    app.run()
