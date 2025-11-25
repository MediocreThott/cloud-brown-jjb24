import os
import json
from flask import Flask, request, redirect, session, url_for, jsonify
from yahoo_oauth import OAuth2
from yahoo_fantasy_api import Game, League
from werkzeug.middleware.proxy_fix import ProxyFix


# --- Configuration ---
CLIENT_ID = os.getenv('YAHOO_CLIENT_ID')
CLIENT_SECRET = os.getenv('YAHOO_CLIENT_SECRET')

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
app.secret_key = os.urandom(24) 

oauth = OAuth2(CLIENT_ID, CLIENT_SECRET, store_token='session')

# ... (Helper functions and routes up to waivers are unchanged and correct) ...
def clean_player_data(player_list):
    player_dict = {}
    for item in player_list:
        if isinstance(item, dict):
            player_dict.update(item)
    return player_dict

@app.route("/")
def index():
    if oauth.token_is_valid():
        return "<h1>Success! Your MCP Server is fully functional and feature-complete.</h1>"
    else:
        return '<h1>Welcome</h1><p>Please <a href="/login">login with Yahoo</a> to continue.</p>'

@app.route("/login")
def login():
    return redirect(oauth.get_login_url())

@app.route("/callback")
def callback():
    oauth.handle_redirect(request.url)
    return redirect(url_for('index'))

@app.route("/leagues")
def get_leagues():
    if not oauth.token_is_valid(): return redirect(url_for('login'))
    try:
        game = Game(oauth, 'nba')
        return jsonify({ "game": "nba", "leagues": game.league_ids() })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/league/<league_id>/standings")
def get_league_standings(league_id):
    if not oauth.token_is_valid(): return redirect(url_for('login'))
    try:
        lg = League(oauth, league_id)
        return jsonify(lg.standings())
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
@app.route("/league/<league_id>/teams")
def get_league_teams(league_id):
    if not oauth.token_is_valid(): return redirect(url_for('login'))
    try:
        lg = League(oauth, league_id)
        return jsonify(lg.teams())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/league/<league_id>/matchups")
def get_league_matchups(league_id):
    if not oauth.token_is_valid(): return redirect(url_for('login'))
    try:
        lg = League(oauth, league_id)
        return jsonify(lg.matchups())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/team/<team_key>/roster")
def get_team_roster(team_key):
    if not oauth.token_is_valid(): return redirect(url_for('login'))
    try:
        base_url = f"https://fantasysports.yahooapis.com/fantasy/v2/team/{team_key}/roster"
        response = oauth.session.get(f"{base_url}?format=json")
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
                'name': player_details.get('name', {}).get('full', 'N/A'),
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

@app.route("/league/<league_id>/free_agents")
def get_free_agents(league_id):
    if not oauth.token_is_valid(): return redirect(url_for('login'))
    try:
        lg = League(oauth, league_id)
        position = request.args.get('position')
        if position:
            free_agents = lg.free_agents(position)
        else:
            free_agents = lg.free_agents('P,G,F,C')
        return jsonify(free_agents)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/league/<league_id>/waivers")
def get_waivers(league_id):
    if not oauth.token_is_valid(): return redirect(url_for('login'))
    try:
        lg = League(oauth, league_id)
        raw_waivers = lg.waivers()
        cleaned_waivers = []
        for player in raw_waivers:
            cleaned_waivers.append({
                "name": player.get("name"),
                "player_id": player.get("player_id"),
                "player_key": player.get("player_key"),
                "waiver_end_date": player.get("waiver_end_date"),
                "percent_owned": player.get("percent_owned")
            })
        return jsonify(cleaned_waivers)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/league/<league_id>/player_stats")
def get_player_stats(league_id):
    if not oauth.token_is_valid(): return redirect(url_for('login'))
    try:
        lg = League(oauth, league_id)
        player_ids = request.args.get('player_ids') # Using player_ids now
        if not player_ids:
            return jsonify({"error": "player_ids parameter is required"}), 400
        ids_list = player_ids.split(',')
        player_stats = lg.player_stats(ids_list, "season")
        return jsonify(player_stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- NEW, WORKING STATS TOOLS ---
@app.route("/league/<league_id>/player_stats_last_week")
def get_player_stats_last_week(league_id):
    if not oauth.token_is_valid(): return redirect(url_for('login'))
    try:
        lg = League(oauth, league_id)
        player_ids = request.args.get('player_ids')
        if not player_ids:
            return jsonify({"error": "player_ids parameter is required"}), 400
        ids_list = player_ids.split(',')
        player_stats = lg.player_stats(ids_list, "lastweek")
        return jsonify(player_stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
@app.route("/league/<league_id>/player_stats_last_month")
def get_player_stats_last_month(league_id):
    if not oauth.token_is_valid(): return redirect(url_for('login'))
    try:
        lg = League(oauth, league_id)
        player_ids = request.args.get('player_ids')
        if not player_ids:
            return jsonify({"error": "player_ids parameter is required"}), 400
        ids_list = player_ids.split(',')
        player_stats = lg.player_stats(ids_list, "lastmonth")
        return jsonify(player_stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(ssl_context='adhoc', host='localhost', port=8080, debug=True)