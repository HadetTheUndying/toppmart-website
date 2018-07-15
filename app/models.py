from flask_sqlalchemy import SQLAlchemy

from datetime import datetime

db = SQLAlchemy()

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    entered_at = db.Column(db.DateTime(timezone=False), default=datetime.utcnow)
    left_at = db.Column(db.DateTime(timezone=False), default=datetime.utcnow)
    accumulated_time = db.Column(db.Integer, default=0) # Total accumulated time in sim
    in_sim = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return 'Player(%s,%s,%r,%r,%s)' % (self.id, self.username, self.entered_at, self.left_at, self.accumulated_time)
        