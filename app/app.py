from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy

from . import models

from functools import reduce
from hashlib import md5

from random import getrandbits

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
db = models.db
db.init_app(app)

@app.route('/')
def index():
    return render_template('main.html')
    
def insert_player_no_commit(name, in_sim):
    player = models.Player.query.filter_by(username=name).first()
    if player is None:
        player = models.Player(username=name,in_sim=in_sim)
        db.session.add(player)
        return
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
    players = models.Player.query.all()
    for player in players:
        player.in_sim = False
    db.session.add_all(players)
    db.session.commit()
    return '200'
    
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
            players=[player.serialize for player in players], \
            max_time=max([player.serialize['elapsed'] for player in players]), \
            id=md5(reduce((lambda x, y : x+y), [player.username for player in players]).encode()).hexdigest() # Provide an id associated with the returned array for diff checking
        )                       
    return jsonify(players=[], id="%032x" % getrandbits(128))

# using our dump endpoint
# we want to detect if a player has left or entered the sim
# using the old array and the new array
# and vice versa
@app.route('/sim/dump', methods=['POST'])
def dump():
    players = set(filter(lambda x: x != "", request.form['players'].split(':')))
    current_players = set([player.username for player in models.Player.query.filter_by(in_sim=True).all()])

    for player in players - current_players:
        # player has "joined" the sim
        insert_player_no_commit(player, True)
        
    for player in current_players - players:
        # player has "left" the sim
        insert_player_no_commit(player, False)
    
    # register the number of players in the sim at the current time
    
    db.session.commit()
    return json_in_sim()
    
@app.errorhandler(404)
def page_not_found_error(error):
    return '404'
