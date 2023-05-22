from flask import Blueprint
from . import app
from . import db


@app.route('/login')
def login():
    return 'Login'

@app.route('/signup')
def signup():
    return 'Signup'

@app.route('/logout')
def logout():
    return 'Logout'