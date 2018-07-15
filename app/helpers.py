from . import models

# assuming each token is >= 2 chars long
def valid_player_token(token):
    return len(token) >= 2

def parse_players_dump(players):
    players = filter(valid_player_token, players.split(':'))
    truth = ['false', 'true']
    return [models.Player(username=token[:-1],in_sim=truth[int(token[-1])%len(truth)]) for token in players]