from flask import Flask, request, jsonify

from . import helpers

app = Flask(__name__)
app.config['SHARED_PRIM_SECRET'] = 0x4832984321;

@app.route('/')
def hello_world():
    return 'Hello world!'

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