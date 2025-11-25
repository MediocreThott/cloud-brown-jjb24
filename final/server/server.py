import os
import json
from flask import Flask, request, redirect, session, url_for, jsonify
from dotenv import load_dotenv
from yahoo_oauth import OAuth2
from yahoo_fantasy_api import Game, League

load_dotenv()

# --- Configuration ---
CLIENT_ID = os.getenv('YAHOO_CLIENT_ID')
CLIENT_SECRET = os.getenv('YAHOO_CLIENT_SECRET')

app = Flask(__name__)
app.secret_key = os.urandom(24) 

oauth = OAuth2(CLIENT_ID, CLIENT_SECRET, store_token='session')

# --- Helper function to simplify the messy Yahoo player data ---
def clean_player_data(player_list):
    """Turns Yahoo's list of single-key dictionaries into one clean dictionary."""
    player_dict = {}
    for item in player_list:
        if isinstance(item, dict):
            player_dict.update(item)
    return player_dict

@app.route("/")
def index():
    if oauth.token_is_valid():
        return """
            <h1>Success! Your MCP Server is fully functional.</h1>
            <p>You can now proceed to the next steps: containerizing and deploying to Cloud Run, and building your LLM client.</p>
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
    if not oauth.token_is_valid(): return redirect(url_for('login'))
    try:
        game = Game(oauth, 'nba')
        return jsonify({ "game": "nba", "leagues": game.league_ids() })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- TOOL #2: GET LEAGUE STANDINGS ---
@app.route("/league/<league_id>/standings")
def get_league_standings(league_id):
    if not oauth.token_is_valid(): return redirect(url_for('login'))
    try:
        lg = League(oauth, league_id)
        return jsonify(lg.standings())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- TOOL #3: GET TEAM ROSTER (WITH ROSTER POSITION) ---
@app.route("/team/<team_key>/roster")
def get_team_roster(team_key):
    if not oauth.token_is_valid(): return redirect(url_for('login'))
    try:
        base_url = f"https://fantasysports.yahooapis.com/fantasy/v2/team/{team_key}/roster"
        response = oauth.session.get(f"{base_url}?format=json")
        response.raise_for_status()
        raw_data = response.json()

        # --- PARSING LOGIC ---
        players_dict = raw_data['fantasy_content']['team'][1]['roster']['0']['players']
        
        cleaned_roster = []
        for i in range(players_dict['count']):
            player_data = players_dict[str(i)]['player']
            
            # Main player details (name, team, etc.)
            player_details = clean_player_data(player_data[0])
            
            # --- NEW LOGIC TO GET ROSTER POSITION ---
            # This data is in the second element of the player_data list
            selected_pos_info = player_data[1].get('selected_position', [])
            roster_position = 'N/A'
            # The position is the second item in the selected_pos_info list
            if len(selected_pos_info) > 1 and 'position' in selected_pos_info[1]:
                roster_position = selected_pos_info[1]['position']

            cleaned_roster.append({
                'name': player_details.get('name', {}).get('full', 'N/A'),
                'player_id': player_details.get('player_id', 'N/A'),
                'editorial_team_abbr': player_details.get('editorial_team_abbr', 'N/A'),
                'display_position': player_details.get('display_position', 'N/A'),
                'roster_position': roster_position, # <-- OUR NEW FIELD
                'status': player_details.get('status', '') 
            })

        return jsonify(cleaned_roster)
        
    except Exception as e:
        return jsonify({"error": str(e), "message": "Failed to fetch or parse roster data."}), 500

if __name__ == "__main__":
    app.run(ssl_context='adhoc', host='localhost', port=8080, debug=True)