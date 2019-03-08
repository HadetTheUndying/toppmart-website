# Toppmart Website

A `Flask`, `SQLAlchemy` and `AngularJS` app to collect stats about ToppMart (live updates).

![](readme/screenshot.png)

# Setup

```
pip install flask
pip install Flask-SQLAlchemy
pip install gunicorn
```

Make sure you generate your `sqlite3` database file using `db.create_all` in the app context.

# Production mode

Deployment is done using `gunicorn` with `SSL` support

```
export FLASK_APP=app/app.py
export FLASK_ENV=production
cd app
gunicorn -w 4 -b 0.0.0.0:443 app:app --certfile=cert.pem --keyfile=privkey.pem --daemon
```

Then navigate to `localhost` in your browser.

To enable `port 80`, do it manually by running `gunicorn -b 0.0.0.0:80 app:app --daemon` (`llHttpRequest` needs this because `https://` redirects invalidate all `POST` requests).


# How it works

Data is sent to the server through a POST request from Second Life to the `/sim/dump` endpoint. Data is formatted as a colon separated list of player names (ex. `user1:user2:user3`).