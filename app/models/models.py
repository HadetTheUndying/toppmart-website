from flask_sqlalchemy import SQLAlchemy

import datetime

db = SQLAlchemy()


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    entered_at = db.Column(db.DateTime(timezone=False), default=datetime.datetime.utcnow)
    left_at = db.Column(db.DateTime(timezone=False), default=datetime.datetime.utcnow)
    accumulated_time = db.Column(db.Integer, default=0)  # Total accumulated time in sim
    in_sim = db.Column(db.Boolean, default=False)
    x = db.Column(db.Float, default=-1)
    z = db.Column(db.Float, default=-1)

    def __str__(self):
        return '%s,%s,%s' % (self.username, self.x, self.z)

    def enter_sim(self):
        self.in_sim = True
        self.entered_at = datetime.datetime.utcnow()

    def leave_sim(self):
        self.in_sim = False
        self.left_at = datetime.datetime.utcnow()

    def set_pos(self, pos):
        self.x = pos[0]
        self.z = pos[1]

    def elapsed(self):
        ref = self.left_at
        if self.in_sim:
            ref = self.entered_at
        return (datetime.datetime.utcnow() - ref).seconds

    def accumulate_time(self):
        self.accumulated_time += (self.left_at - self.entered_at).seconds

    @property
    def serialize(self):
        return {'username': self.username, 'time': self.accumulated_time, 'elapsed': self.elapsed(), 'x': self.x, 'z': self.z}
