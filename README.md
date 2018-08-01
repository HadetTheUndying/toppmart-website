# Toppmart Website

A Flask + SQLAlchemy + AngularJS app to collect stats about ToppMart.

Currently a work in progress.

# How it works

Data is sent to the server through a POST request from Second Life to the `/sim/dump` endpoint. Data is formatted as a colon separated list of player names (ex. user1:user2:user3).