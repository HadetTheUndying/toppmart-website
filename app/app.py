from flask import Flask, request, jsonify, render_template

from models import models

from functools import reduce
from hashlib import md5

from random import getrandbits


app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
app.config['SECRET_KEY'] = 'CHANGE ME'

db = models.db
db.init_app(app)


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
@app.route('/sim/reset/<token>')
def reset(token):
    if token != app.config['SECRET_KEY']:
        return 'Bad secret'

    players = models.Player.query.all()
    for player in players:
        player.in_sim = False
    player.accumulate_time()
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
        return jsonify(
            players= [player.serialize for player in online_players],
            offline_players=[player.serialize for player in players if not player.in_sim],
            max_time=max([player.serialize['elapsed'] for player in online_players]),
            id=md5(reduce((lambda x, y : x+y), [str(player) for player in online_players]).encode()).hexdigest()
        ) # Provide an id associated with the returned array for diff checking
    return jsonify(players=[], id="%032x" % getrandbits(128))


def parse_dump():
    players = [player_string.split(",") for player_string in request.form['players'].split(':')]
    positions = {}
    for name, x, y in players:
        positions[name] = (x, y)
    return set([name for name, x, y in players if name != ""]), positions


@app.route('/sim/dump/<token>', methods=['POST'])
def dump(token):
    if token != app.config['SECRET_KEY']:
        return 'Bad secret'

    player_names, positions = parse_dump()
    current_players = set([player.username for player in models.Player.query.filter_by(in_sim=True).all()])
    joined = player_names - current_players
    left = current_players - player_names

    # Player already in sim, needs their position updated
    for username in player_names:
        if username not in joined:
            update_player(username, positions[username])

    for player in joined:
        # player has "joined" the sim
        insert_player_no_commit(player, positions[player], True)

    for player in left:
        # player has "left" the sim
        insert_player_no_commit(player, (-1, -1), False)

    db.session.commit()
    return json_in_sim()
    
@app.errorhandler(404)
def page_not_found_error(error):
    return '404'
