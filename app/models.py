from flask_sqlalchemy import SQLAlchemy

import datetime, time

db = SQLAlchemy()


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    entered_at = db.Column(db.DateTime(timezone=False), default=datetime.datetime.utcnow)
    left_at = db.Column(db.DateTime(timezone=False), default=datetime.datetime.utcnow)
    accumulated_time = db.Column(db.Integer, default=0) # Total accumulated time in sim
    in_sim = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return 'Player(%s,%s,%r,%r,%s)' % (self.id, self.username, self.entered_at, self.left_at, self.accumulated_time)
        
    def enter_sim(self):
        self.in_sim = True
        self.entered_at = datetime.datetime.utcnow()
       
    def leave_sim(self):
        self.in_sim = False
        self.left_at = datetime.datetime.utcnow()
    
    def elapsed(self):
        ref = self.left_at
        if self.in_sim:
            ref = self.entered_at
        return (datetime.datetime.utcnow() - ref).seconds
    
    def accumulate_time(self):
        self.accumulated_time += (self.left_at - self.entered_at).seconds
        
    @property
    def serialize(self):
        return { 'username': self.username, 'elapsed': self.elapsed() }


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(80), nullable=False)
    time = db.Column(db.DateTime(timezone=False), default=datetime.datetime.utcnow)
