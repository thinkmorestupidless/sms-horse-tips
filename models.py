from app import db


class Punter(db.Model):
    __tablename__ = 'punters'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String, nullable=False)
    surname = db.Column(db.String, nullable=False)
    phone_number = db.Column(db.String, nullable=False)
    bets = db.relationship('Bet', backref='punter', lazy='joined')

    # surname = db.relationship('Question', backref='survey', lazy='dynamic')

    # def __init__(self):
    #     self.title = title

    # @property
    # def has_questions(self):
    #     return self.questions.count() > 0


class Tip(db.Model):
    __tablename__ = 'tips'

    # TEXT = 'text'
    # NUMERIC = 'numeric'
    # BOOLEAN = 'boolean'

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

    # kind = db.Column(db.Enum(TEXT, NUMERIC, BOOLEAN, name='question_kind'))
    # survey_id = db.Column(db.Integer, db.ForeignKey('surveys.id'))
    # answers = db.relationship('Answer', backref='question', lazy='dynamic')

    # def __init__(self):
    #     self.content = content
    #     self.kind = kind

    # def next(self):
    #     return self.survey.questions.filter(Question.id > self.id).order_by('id').first()


class Bet(db.Model):
    __tablename__ = 'bets'

    id = db.Column(db.Integer, primary_key=True)
    punter_id = db.Column(db.String, nullable=False)
    tip_id = db.Column(db.String, nullable=False)
    stake = db.Column(db.String, nullable=False)
    price = db.Column(db.String, nullable=False)
    tip_id = db.Column(db.Integer, db.ForeignKey('tips.id'))
    punter_id = db.Column(db.Integer, db.ForeignKey('punters.id'))

    # content = db.Column(db.String, nullable=False)
    # session_id = db.Column(db.String, nullable=False)
    # question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))

    # @classmethod
    # def update_content(cls, session_id, question_id, content):
    #     existing_answer = cls.query.filter(
    #         Answer.session_id == session_id and Answer.question_id == question_id
    #     ).first()
    #     existing_answer.content = content
    #     db.session.add(existing_answer)
    #     db.session.commit()

    # def __init__(self, content, question, session_id):
    #     self.content = content
    #     self.question = question
    #     self.session_id = session_id
