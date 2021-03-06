from flask import Flask, request, jsonify, render_template

import app.models as models

from functools import reduce
from hashlib import md5

from random import getrandbits

import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
app.config['SECRET_KEY'] = 'CHANGE ME'
app.config['UPDATE_RATE'] = 5.0 # Every 5 seconds update endpoint called

db = models.db
db.init_app(app)


@app.route('/')
def index():
    return render_template('main.html')


def update_player(name, pos):
    player = models.Player.query.filter_by(username=name).first()
    if player is not None:
        weekday = datetime.datetime.today().weekday()
        multiplier = 2.0 if weekday == 5 or weekday == 6 else 1.0
        player.increase_balance(multiplier * app.config['UPDATE_RATE'] / 3600.0)
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
        if player.in_sim:
            player.accumulate_time()
            player.leave_sim()
    db.session.add_all(players)
    db.session.commit()
    return '200'


@app.route('/sim/json/<name>')
def json(name):
    player = models.Player.query.filter_by(username=name).first()
    if player:
        return jsonify(player.serialize)        
    return 'Could not find player'


@app.route('/sim/balance/<token>/<name>')
def balance(token, name):
    if token != app.config['SECRET_KEY']:
        return 'Bad secret'

    player = models.Player.query.filter_by(username=name).first()
    if player:
        return '{:.2f}'.format(player.balance)

    return 'Could not find %s' % name


@app.route('/sim/balance/spend/<token>/<name>/<amt>')
def spend(token, name, amt):
    if token != app.config['SECRET_KEY']:
        return 'Bad secret'

    player = models.Player.query.filter_by(username=name).first()
    amt = float(amt)

    if player and player.balance >= amt > 0:
        player.decrease_balance(amt)
        db.session.commit()
        return 'Spend successful.'

    if not player:
        return '%s does not exist.' % name

    return 'Insufficient funds.'


@app.route('/sim/balance/gain/<token>/<name>/<amt>')
def gain(token, name, amt):
    if token != app.config['SECRET_KEY']:
        return 'Bad secret'

    player = models.Player.query.filter_by(username=name).first()

    if not player:
        return '%s does not exist.' % name

    amt = float(amt)

    if amt > 0:
        player.increase_balance(amt)
        db.session.commit()
        return 'Gain successful.'

    return 'Something went wrong.'


@app.route('/sim/balance/transfer/<token>/<src>/<dst>/<amt>')
def transfer(token, src, dst, amt):
    if token != app.config['SECRET_KEY']:
        return 'Bad secret'

    from sqlalchemy import func
    src_player = models.Player.query.filter_by(username=src).first()
    dst_player = models.Player.query.filter(func.lower(models.Player.username) == func.lower(dst)).first()

    if not src_player:
        return 'Source %s does not exist.' % src

    if not dst_player:
        return 'Destination %s does not exist.' % dst

    amt = float(amt)

    if src_player.balance >= amt > 0:
        src_player.decrease_balance(amt)
        dst_player.increase_balance(amt)
        db.session.commit()
        return 'Transfer to %s of %s successful.' % (dst, amt)

    return 'Insufficient funds.'


@app.route('/sim/top_balances')
def top_balances():
    richest = models.Player.query.order_by(models.Player.balance.desc())[:5]
    return str("\n".join(["%s. %s - %s ToppCoins" % (index + 1, player.username, int(player.balance)) for index, player in enumerate(richest)]))


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
