from flask import Flask, request, jsonify, render_template

from . import models

from functools import reduce
from hashlib import md5

from random import getrandbits

from flask_sslify import SSLify

app = Flask(__name__)
sslify = SSLify(app) # redirect all http:// to https://
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

db = models.db
db.create_all()
db.init_app(app)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)

@app.route('/')
def index():
    return render_template('main.html')


def update_player(name, pos):
    player = models.Player.query.filter_by(username=name).first()
    if player is not None:
        player.set_pos(pos)


def insert_player_no_commit(name, pos, in_sim):
    player = models.Player.query.filter_by(username=name).first()
    x, z = pos
    if player is None:
        player = models.Player(username=name,in_sim=in_sim, x=x, z=z)
        db.session.add(player)
        return

    player.set_pos(pos)
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
    
@app.route('/sim/json/players')
def json_in_sim():
    players = models.Player.query.all()
    if players:
        online_players = [player for player in players if player.in_sim]
        return jsonify(\
            players= [player.serialize for player in online_players], \
            offline_players=[player.serialize for player in players if not player.in_sim], \
            max_time=max([player.serialize['elapsed'] for player in players]), \
            id=md5(reduce((lambda x, y : x+y), [player.username for player in online_players]).encode()).hexdigest() # Provide an id associated with the returned array for diff checking
        )
    return jsonify(players=[], id="%032x" % getrandbits(128))


# using our dump endpoint
# we want to detect if a player has left or entered the sim
# using the old array and the new array
# and vice versa
@app.route('/sim/dump', methods=['POST'])
def dump():
    players = []
    for player_string in request.form['players'].split(':'):
        players.append(player_string.split(","))
    player_names = set(filter(lambda x: x != "", [player[0] for player in players]))
    current_players = set([player.username for player in models.Player.query.filter_by(in_sim=True).all()])

    positions = {}

    for player in players:
        positions[player[0]] = (player[1], player[2])

    joined = player_names - current_players

    # Player already in sim, needs their position updated
    for player in players:
        if player[0] not in joined:
            update_player(player[0], positions[player[0]])

    for player in joined:
        # player has "joined" the sim
        insert_player_no_commit(player, positions[player], True)

    for player in current_players - player_names:
        # player has "left" the sim
        insert_player_no_commit(player, (-1, -1), False)

    # register the number of players in the sim at the current time
    
    db.session.commit()
    return json_in_sim()
    
@app.errorhandler(404)
def page_not_found_error(error):
    return '404'
