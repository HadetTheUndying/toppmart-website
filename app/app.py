from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy

from . import models, helpers

from functools import reduce
from hashlib import md5

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
db = models.db
db.init_app(app)

@app.route('/')
def index():
    return render_template('main.html')
    
def insert_without_commit(name, in_sim):
    player = models.Player.query.filter_by(username=name).first()
    in_sim = in_sim.lower() in ['true']
    if player is None:
        player = models.Player(username=name,in_sim=in_sim)
        db.session.add(player)
        db.session.commit()
        return 'Could not find %s but inserted it.' % name
    # Player exists and left the sim
    if player.in_sim and not in_sim:
        player.leave_sim()
        player.accumulate_time()
    elif not player.in_sim and in_sim:
        # Entered the sim
        player.enter_sim()
    db.session.add(player)
    
# Reset the state of all players currently in the sim and accumulate time (sim crash, script reset)
@app.route('/sim/reset')
def reset():
    return
    
@app.route('/sim/json/<name>')
def json(name):
    player = models.Player.query.filter_by(username=name).first()
    if player:
        return jsonify(player.serialize)
    return 'Could not find player'
    
@app.route('/sim/json/in_sim')
def json_in_sim():
    players = models.Player.query.filter_by(in_sim=True).all()
    if players:
        return jsonify(\
            players = [player.serialize for player in players], \
            max_time = max([player.serialize['elapsed'] for player in players]), \
            id = md5(reduce((lambda x, y : x+y), [player.username for player in players]).encode()).hexdigest()
        )                       
    return 'There are no players in the sim.'

# data is formatted as <name><in_sim>:<name><in_sim>, ...
@app.route('/sim/dump/<data>')
def dump(data):
    players = helpers.parse_players_dump(data)
    for player in players:
        insert_without_commit(player.username, player.in_sim)
    db.session.commit()
    return json_in_sim()
    
@app.errorhandler(404)
def page_not_found_error(error):
    return '404'