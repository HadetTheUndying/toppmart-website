gunicorn -w 4 -b 0.0.0.0:443 app:app --certfile=fullchain.pem --keyfile=privkey.pem --daemon
gunicorn -b 0.0.0.0:80 app:app --daemon
