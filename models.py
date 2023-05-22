from app import db
from flask_login import UserMixin


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    name = db.Column(db.String(1000))


class Punter(db.Model):
    __tablename__ = 'punters'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String, nullable=False)
    surname = db.Column(db.String, nullable=False)
    phone_number = db.Column(db.String, nullable=False)
    bets = db.relationship('Bet', backref='punter', lazy='joined')


class Tip(db.Model):
    __tablename__ = 'tips'

    WIN = 'win'
    EACH_WAY = 'e/w'

    id = db.Column(db.Integer, primary_key=True)
    horse = db.Column(db.String, nullable=False)
    time = db.Column(db.String, nullable=False)
    meeting = db.Column(db.String, nullable=False)
    bet_type = db.Column(db.String, nullable=False)
    min_price = db.Column(db.String, nullable=False)
    stake = db.Column(db.String, nullable=False)
    bets = db.relationship('Bet', backref='tip', lazy='joined')


class Bet(db.Model):
    __tablename__ = 'bets'

    id = db.Column(db.Integer, primary_key=True)
    punter_id = db.Column(db.String, nullable=False)
    tip_id = db.Column(db.String, nullable=False)
    stake = db.Column(db.String, nullable=False)
    price = db.Column(db.String, nullable=False)
    tip_id = db.Column(db.Integer, db.ForeignKey('tips.id'))
    punter_id = db.Column(db.Integer, db.ForeignKey('punters.id'))
