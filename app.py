import os
import re
from flask import Flask, render_template, redirect, request, url_for, flash
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, SubmitField, EmailField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length, Email
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

import secrets
secret_key = app.config['SECRET_KEY']
app.secret_key = secret_key

bootstrap = Bootstrap5(app)
csrf = CSRFProtect(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

from models import *

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

twilio = Client(app.config['TWILIO_ACCOUNT_SID'], app.config['TWILIO_AUTH_TOKEN'])

response_regex = r'(\d*)\s+(\d*/\d*|\d\.\d)'


@login_manager.user_loader
def load_user(user_id):
    # since the user_id is just the primary key of our user table, use it in the query for the user
    return User.query.get(int(user_id))

class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        remember = form.remember.data

        user = User.query.filter_by(email=email).first()

        # check if the user actually exists
        # take the user-supplied password, hash it, and compare it to the hashed password in the database
        if not user or not check_password_hash(user.password, password):
            flash('Please check your login details and try again.')
            return redirect(url_for('login')) # if the user doesn't exist or password is wrong, reload the page

        # if the above check passes, then we know the user has the right credentials
        login_user(user, remember=remember)
        return redirect(url_for('root'))
    return render_template('login.html', form=form)

class SignupForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    name = StringField('Name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(8, 20)])
    submit = SubmitField('Signup')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        email = form.email.data
        name = form.name.data
        password = form.password.data

        user = User.query.filter_by(email=email).first() # if this returns a user, then the email already exists in database

        if user: # if a user is found, we want to redirect back to signup page so user can try again
            flash('Email address already exists')
            return redirect(url_for('signup'))

        # create a new user with the form data. Hash the password so the plaintext version isn't saved.
        new_user = User(email=email, name=name, password=generate_password_hash(password, method='scrypt'))

        # add the new user to the database
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))
    return render_template('signup.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name=current_user.name)


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
@login_required
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
@login_required
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
    from_number = request.values['From']
    body = request.values['Body']
    
    print("Incoming SMS [{} => {}]".format(from_number, body))
    
    response = MessagingResponse()
    
    punter = db.session.query(Punter).filter(Punter.phone_number == from_number).first()
    if punter is not None:
        print("{} {} [{}] said '{}'".format(punter.first_name, punter.surname, from_number, body))
        
        if body.lower() == "yes":
            return handle_yes(response)
        elif body.lower() == "no":
            return handle_no(response)
        else:
            return handle_bet(response, body, punter)
    else:
        print("Unable to find punter with phone number {}".format(from_number))
        response.message("I'm sorry I don't know who you are")
        return str(response)
        

def handle_bet(response, body, punter):    
    cleaned_body = body.replace(u'£', '').replace(u'@', ' ')
    match = re.search(response_regex, cleaned_body)
    stake = match.group(1).strip()
    price = match.group(2).strip()
    if match:
        print("we have a match £{} @ {}".format(stake, price)) 
        tip = db.session.query(Tip).order_by(Tip.id.desc()).first()
        if tip is not None:           
            if any(bet.tip_id == tip.id for bet in punter.bets):
                response.message("We have already recorded a response from you for this tip")
            else:
                bet = Bet(punter_id=punter.id, tip_id=tip.id, stake=stake, price=price)
                db.session.add(bet)
                db.session.commit()

                response.message("We have recorded your bet of £{} at {}. Thank you".format(stake, price))

        else: 
            print("Unable to find a tip to record bet of {}@{}".format(stake, price))
            response.message("Unable to find a tip to record your bet against")
    else:
        print("received response '{}'".format(body))
        response.message("I'm sorry, I don't understand, someone will get in touch")
    return str(response)


def handle_yes(response):
    tip = db.session.query(Tip).order_by(Tip.id.desc()).first()
    stake = tip.stake
    if not stake.startswith('£'):
        stake = "£{}".format(stake)
    response.message("Place {} ({}) on {} in the {} at {} don't take less than {}. When you have placed the bet please CONFIRM it with us by replying to this message with ONLY the stake and price of the bet you placed e.g. {} {}".format(stake, tip.bet_type, tip.horse, tip.time, tip.meeting, tip.min_price, stake.replace(u'£', ''), tip.min_price))
    return str(response)


def handle_no(response):
    response.message("Thanks, we'll be in touch next time we have a tip")
    return str(response)


def is_sms_request():
    return 'MessageSid' in request.values.keys()


if __name__ == '__main__':
    app.run()
