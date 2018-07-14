from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from . import helpers

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)

from . import models

@app.route('/')
def hello_world():
    return User.query.filter_by(username='admin').first()
    
@app.route('/dump')
def dump():
    if request.method != 'POST':
        try:
            players = helpers.parse_players_dump(request.form['players']) # get the players in the sim
            return jsonify(players)
        except KeyError:
            return 'Please specify a \'players\' array.'
    else:
        return 'Must be a POST request.'
    
@app.errorhandler(404)
def page_not_found_error(error):
    return '404'