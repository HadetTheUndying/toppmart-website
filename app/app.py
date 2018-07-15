from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

from . import models
from . import helpers

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
models.db.init_app(app)

@app.route('/insert/<name>')
def insert(name):
    player = models.Player.query.filter_by(username=name).first()
    if player is None:
        player = models.Player(username=name)
        db.session.add(player)
        db.session.commit()
        return 'Could not find %s but inserted it.' % name
    return 'Found %r' % player
    
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