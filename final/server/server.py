import os
import json
from flask import Flask, request, redirect, session, url_for, jsonify
from requests_oauthlib import OAuth2Session
from werkzeug.middleware.proxy_fix import ProxyFix

# --- Configuration ---
CLIENT_ID = os.getenv('YAHOO_CLIENT_ID')
CLIENT_SECRET = os.getenv('YAHOO_CLIENT_SECRET')
API_KEY = os.getenv('FANTASY_API_KEY')
TOKEN_FILE = '/tmp/token.json' # Use a writable directory in Cloud Run

# Yahoo URLs
AUTHORIZATION_URL = 'https://api.login.yahoo.com/oauth2/request_auth'
TOKEN_URL = 'https://api.login.yahoo.com/oauth2/get_token'
BASE_API_URL = 'https://fantasysports.yahooapis.com/fantasy/v2'

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
app.secret_key = os.urandom(24) 

# --- Helper to clean Yahoo's nested data format ---
def clean_player_data(player_list):
    player_dict = {}
    for item in player_list:
        if isinstance(item, dict):
            for key, value in item.items():
                if key == 'name':
                    player_dict.update(value)
                else:
                    player_dict[key] = value
    return player_dict

# --- Authentication Routes (for Humans/Browser to create the token file) ---
@app.route("/")
def index():
    if os.path.exists(TOKEN_FILE):
        return "<h1>SUCCESS! Your server is authenticated. The LLM client can now use the API tools.</h1>"
    return '<h1>Welcome</h1><p>Server is not authenticated. Please <a href="/login">login with Yahoo</a> to enable the client tools.</p>'

@app.route("/login")
def login():
    redirect_uri = url_for('callback', _external=True, _scheme='https')
    # The 'scope' must be provided here, during session creation.
    oauth = OAuth2Session(CLIENT_ID, redirect_uri=redirect_uri, scope=["fspt-r"])
    authorization_url, state = oauth.authorization_url(AUTHORIZATION_URL)
    session['oauth_state'] = state
    return redirect(authorization_url)

@app.route("/callback")
def callback():
    redirect_uri = url_for('callback', _external=True, _scheme='https')
    oauth = OAuth2Session(CLIENT_ID, state=session['oauth_state'], redirect_uri=redirect_uri)
    token = oauth.fetch_token(TOKEN_URL, client_secret=CLIENT_SECRET,
                              authorization_response=request.url)
    with open(TOKEN_FILE, 'w') as f:
        json.dump(token, f)
    return redirect(url_for('index'))

# --- Helper Function for API Tools (for LLM Client) ---
def make_api_request(url_path):
    if not os.path.exists(TOKEN_FILE):
        return jsonify({"error": "Server not authenticated. Please log in via the browser first."}), 401
    try:
        with open(TOKEN_FILE, 'r') as f:
            token = json.load(f)

        oauth = OAuth2Session(CLIENT_ID, token=token)
        full_url = f"{BASE_API_URL}/{url_path}?format=json"
        response = oauth.get(full_url)
        response.raise_for_status()
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- API Tool Endpoints ---
def check_api_key():
    if request.headers.get('X-API-Key') != API_KEY:
        return jsonify({"error": "Invalid API Key"}), 401
    return None

@app.route("/leagues")
def get_leagues():
    key_check = check_api_key()
    if key_check: return key_check
    return make_api_request("users;use_login=1/games;game_keys=nba/leagues")

@app.route("/league/<league_id>/teams")
def get_league_teams(league_id):
    key_check = check_api_key()
    if key_check: return key_check
    return make_api_request(f"league/{league_id}/teams")

@app.route("/league/<league_id>/standings")
def get_league_standings(league_id):
    key_check = check_api_key()
    if key_check: return key_check
    return make_api_request(f"league/{league_id}/standings")

@app.route("/league/<league_id>/matchups")
def get_league_matchups(league_id):
    key_check = check_api_key()
    if key_check: return key_check
    return make_api_request(f"league/{league_id}/scoreboard")

@app.route("/league/<league_id>/players")
def get_players(league_id):
    key_check = check_api_key()
    if key_check: return key_check
    player_status = request.args.get('status', 'FA')
    position = request.args.get('position')
    path = f"league/{league_id}/players;status={player_status}"
    if position:
        path += f";position={position}"
    return make_api_request(path)

@app.route("/league/<league_id>/player_stats")
def get_player_stats(league_id):
    key_check = check_api_key()
    if key_check: return key_check
    player_keys = request.args.get('player_keys')
    stat_type = request.args.get('type', 'season')
    if not player_keys: return jsonify({"error": "player_keys parameter is required"}), 400
    return make_api_request(f"league/{league_id}/players;player_keys={player_keys}/stats;type={stat_type}")

@app.route("/team/<team_key>/roster")
def get_team_roster(team_key):
    key_check = check_api_key()
    if key_check: return key_check
    # This function needs custom parsing logic, so we don't use the generic helper
    if not os.path.exists(TOKEN_FILE):
        return jsonify({"error": "Server not authenticated."}), 401
    try:
        with open(TOKEN_FILE, 'r') as f: token = json.load(f)
        oauth = OAuth2Session(CLIENT_ID, token=token)
        url = f"{BASE_API_URL}/team/{team_key}/roster?format=json"
        response = oauth.get(url)
        response.raise_for_status()
        raw_data = response.json()
        
        players_dict = raw_data['fantasy_content']['team'][1]['roster']['0']['players']
        cleaned_roster = []
        for i in range(players_dict['count']):
            player_data = players_dict[str(i)]['player']
            player_details = clean_player_data(player_data[0])
            selected_pos_info = player_data[1].get('selected_position', [])
            roster_position = 'N/A'
            if len(selected_pos_info) > 1 and 'position' in selected_pos_info[1]:
                roster_position = selected_pos_info[1]['position']
            cleaned_roster.append({
                'name': player_details.get('full', 'N/A'),
                'player_id': player_details.get('player_id', 'N/A'),
                'player_key': player_details.get('player_key', 'N/A'),
                'editorial_team_abbr': player_details.get('editorial_team_abbr', 'N/A'),
                'display_position': player_details.get('display_position', 'N/A'),
                'roster_position': roster_position,
                'status': player_details.get('status', '') 
            })
        return jsonify(cleaned_roster)
    except Exception as e:
        return jsonify({"error": str(e), "message": "Failed to fetch or parse roster data."}), 500