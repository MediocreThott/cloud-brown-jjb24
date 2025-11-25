import os
import json
from flask import Flask, request, redirect, session, url_for, jsonify
from dotenv import load_dotenv
from yahoo_oauth import OAuth2
# We now need both the Game and League classes
from yahoo_fantasy_api import Game, League

load_dotenv()

# --- Configuration ---
CLIENT_ID = os.getenv('YAHOO_CLIENT_ID')
CLIENT_SECRET = os.getenv('YAHOO_CLIENT_SECRET')

app = Flask(__name__)
app.secret_key = os.urandom(24) 

oauth = OAuth2(CLIENT_ID, CLIENT_SECRET, store_token='session')

@app.route("/")
def index():
    if oauth.token_is_valid():
        return """
            <h1>Success! You are authenticated.</h1>
            <p>We can now make API calls.</p>
            <p><a href="/leagues">Click here to fetch your leagues</a></p>
            <p>Once you have a league ID, you can fetch standings by modifying the URL. For example: /league/YOUR_LEAGUE_ID/standings</p>
        """
    else:
        return '<h1>Welcome</h1><p>Please <a href="/login">login with Yahoo</a> to continue.</p>'

@app.route("/login")
def login():
    return redirect(oauth.get_login_url())

@app.route("/callback")
def callback():
    oauth.handle_redirect(request.url)
    return redirect(url_for('index'))

# --- TOOL #1: GET ALL LEAGUES ---
@app.route("/leagues")
def get_leagues():
    if not oauth.token_is_valid():
        return redirect(url_for('login'))
    try:
        game = Game(oauth, 'nba')
        league_ids = game.league_ids()
        return jsonify({ "game": "nba", "leagues": league_ids })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- TOOL #2: GET LEAGUE STANDINGS ---
@app.route("/league/<league_id>/standings")
def get_league_standings(league_id):
    """
    An API endpoint to get the standings for a specific league.
    The <league_id> in the URL is passed as an argument to this function.
    """
    if not oauth.token_is_valid():
        return redirect(url_for('login'))
    try:
        # Now, we instantiate a League object with the specific league_id.
        lg = League(oauth, league_id)
        
        # The standings() method returns a list of teams in order.
        standings_data = lg.standings()

        return jsonify(standings_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(ssl_context='adhoc', host='localhost', port=8080, debug=True)