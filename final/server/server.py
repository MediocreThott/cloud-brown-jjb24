import os
import json
from flask import Flask, request, redirect, session, url_for, jsonify, render_template_string
from requests_oauthlib import OAuth2Session
from werkzeug.middleware.proxy_fix import ProxyFix
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# --- Configuration ---
CLIENT_ID = os.getenv('YAHOO_CLIENT_ID')
CLIENT_SECRET = os.getenv('YAHOO_CLIENT_SECRET')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

AUTHORIZATION_URL = 'https://api.login.yahoo.com/oauth2/request_auth'
TOKEN_URL = 'https://api.login.yahoo.com/oauth2/get_token'
BASE_API_URL = 'https://fantasysports.yahooapis.com/fantasy/v2'

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
app.secret_key = os.urandom(24) 

# --- Helper Functions ---
def make_yahoo_request(url):
    """Helper to make authenticated Yahoo API requests"""
    if 'oauth_token' not in session:
        return {"error": "User is not authenticated"}
    try:
        oauth = OAuth2Session(CLIENT_ID, token=session['oauth_token'])
        response = oauth.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": f"API call failed: {str(e)}"}

def clean_player_data(player_list):
    """Clean Yahoo's nested player data format"""
    player_dict = {}
    for item in player_list:
        if isinstance(item, dict):
            for key, value in item.items():
                if key == 'name': 
                    player_dict.update(value)
                else: 
                    player_dict[key] = value
    return player_dict

# --- API Tool Functions (for the LLM) ---

def get_user_leagues():
    """Returns all fantasy basketball leagues for the current user with league details."""
    url = f"{BASE_API_URL}/users;use_login=1/games;game_keys=nba/leagues?format=json"
    return make_yahoo_request(url)

def get_league_settings(league_key: str):
    """
    Returns detailed league settings including scoring categories, roster positions, and rules.
    Args:
        league_key (str): The league key (e.g., '423.l.40127')
    """
    url = f"{BASE_API_URL}/league/{league_key}/settings?format=json"
    return make_yahoo_request(url)

def get_league_standings(league_key: str):
    """
    Returns current league standings with team records and rankings.
    Args:
        league_key (str): The league key (e.g., '423.l.40127')
    """
    url = f"{BASE_API_URL}/league/{league_key}/standings?format=json"
    return make_yahoo_request(url)

def get_league_scoreboard(league_key: str, week: str = None):
    """
    Returns matchup information for the league for a specific week.
    Args:
        league_key (str): The league key (e.g., '423.l.40127')
        week (str): The week number (optional, defaults to current week)
    """
    if week:
        url = f"{BASE_API_URL}/league/{league_key}/scoreboard;week={week}?format=json"
    else:
        url = f"{BASE_API_URL}/league/{league_key}/scoreboard?format=json"
    return make_yahoo_request(url)

def get_league_teams(league_key: str):
    """
    Returns all teams in a league with their managers and basic info.
    Args:
        league_key (str): The league key (e.g., '423.l.40127')
    """
    url = f"{BASE_API_URL}/league/{league_key}/teams?format=json"
    return make_yahoo_request(url)

def get_team_roster(team_key: str, week: str = None):
    """
    Returns the roster of players for a specific team.
    Args:
        team_key (str): The team key (e.g., '423.l.40127.t.1')
        week (str): The week number (optional, defaults to current week)
    """
    if week:
        url = f"{BASE_API_URL}/team/{team_key}/roster;week={week}?format=json"
    else:
        url = f"{BASE_API_URL}/team/{team_key}/roster?format=json"
    return make_yahoo_request(url)

def get_team_stats(team_key: str, stat_type: str = "season"):
    """
    Returns statistics for a team.
    Args:
        team_key (str): The team key (e.g., '423.l.40127.t.1')
        stat_type (str): Type of stats - 'season', 'average_season', 'week', 'average_week', 'lastweek', 'lastmonth'
    """
    url = f"{BASE_API_URL}/team/{team_key}/stats;type={stat_type}?format=json"
    return make_yahoo_request(url)

def get_team_matchups(team_key: str, weeks: str = None):
    """
    Returns matchup history or specific matchups for a team.
    Args:
        team_key (str): The team key (e.g., '423.l.40127.t.1')
        weeks (str): Comma-separated week numbers (optional, e.g., '1,2,3')
    """
    if weeks:
        url = f"{BASE_API_URL}/team/{team_key}/matchups;weeks={weeks}?format=json"
    else:
        url = f"{BASE_API_URL}/team/{team_key}/matchups?format=json"
    return make_yahoo_request(url)

def get_player_stats(player_keys: str, stat_type: str = "season"):
    """
    Returns statistics for one or more players.
    Args:
        player_keys (str): Comma-separated player keys (e.g., 'nba.p.6450,nba.p.5479')
        stat_type (str): Type of stats - 'season', 'average_season', 'week', 'average_week', 'lastweek', 'lastmonth', 'date' (use with date parameter)
    """
    url = f"{BASE_API_URL}/players;player_keys={player_keys}/stats;type={stat_type}?format=json"
    return make_yahoo_request(url)

def search_players(league_key: str, search_query: str):
    """
    Search for players by name in the context of a league.
    Args:
        league_key (str): The league key (e.g., '423.l.40127')
        search_query (str): Player name to search for (e.g., 'LeBron')
    """
    url = f"{BASE_API_URL}/league/{league_key}/players;search={search_query}?format=json"
    return make_yahoo_request(url)

def get_player_ownership(league_key: str, player_keys: str):
    """
    Returns ownership information for players in a specific league.
    Args:
        league_key (str): The league key (e.g., '423.l.40127')
        player_keys (str): Comma-separated player keys (e.g., 'nba.p.6450,nba.p.5479')
    """
    url = f"{BASE_API_URL}/league/{league_key}/players;player_keys={player_keys}/ownership?format=json"
    return make_yahoo_request(url)

def get_league_transactions(league_key: str, transaction_type: str = None):
    """
    Returns recent league transactions (trades, adds, drops, commish changes).
    Args:
        league_key (str): The league key (e.g., '423.l.40127')
        transaction_type (str): Filter by type - 'add', 'drop', 'trade', 'commish' (optional)
    """
    if transaction_type:
        url = f"{BASE_API_URL}/league/{league_key}/transactions;type={transaction_type}?format=json"
    else:
        url = f"{BASE_API_URL}/league/{league_key}/transactions?format=json"
    return make_yahoo_request(url)

def get_team_transactions(team_key: str):
    """
    Returns transaction history for a specific team.
    Args:
        team_key (str): The team key (e.g., '423.l.40127.t.1')
    """
    url = f"{BASE_API_URL}/team/{team_key}/transactions?format=json"
    return make_yahoo_request(url)

def get_league_draft_results(league_key: str):
    """
    Returns the draft results for a league.
    Args:
        league_key (str): The league key (e.g., '423.l.40127')
    """
    url = f"{BASE_API_URL}/league/{league_key}/draftresults?format=json"
    return make_yahoo_request(url)

def get_player_percent_owned(player_keys: str):
    """
    Returns percent owned across all Yahoo leagues for specified players.
    Args:
        player_keys (str): Comma-separated player keys (e.g., 'nba.p.6450,nba.p.5479')
    """
    url = f"{BASE_API_URL}/players;player_keys={player_keys}/percent_owned?format=json"
    return make_yahoo_request(url)

def get_free_agents(league_key: str, position: str = None, status: str = None, sort: str = None, count: int = 25):
    """
    Returns available free agents in a league.
    Args:
        league_key (str): The league key (e.g., '423.l.40127')
        position (str): Filter by position - 'PG', 'SG', 'SF', 'PF', 'C', 'G', 'F', 'UTIL' (optional)
        status (str): Filter by status - 'A' (all available), 'FA' (free agents), 'W' (waivers) (optional)
        sort (str): Sort criteria - 'NAME', 'OR' (overall rank), 'AR' (actual rank) (optional)
        count (int): Number of results to return (default 25, max 25)
    """
    url = f"{BASE_API_URL}/league/{league_key}/players;status=A"
    
    if position:
        url += f";position={position}"
    if status:
        url += f";status={status}"
    if sort:
        url += f";sort={sort}"
    
    url += f";count={min(count, 25)}?format=json"
    return make_yahoo_request(url)

def get_matchup_details(team_key: str, week: str):
    """
    Returns detailed matchup information for a team in a specific week.
    Args:
        team_key (str): The team key (e.g., '423.l.40127.t.1')
        week (str): The week number
    """
    url = f"{BASE_API_URL}/team/{team_key}/matchups;weeks={week}?format=json"
    return make_yahoo_request(url)

# --- LLM and Chat Setup ---
genai.configure(api_key=GOOGLE_API_KEY)

# System instructions embedded directly
SYSTEM_INSTRUCTIONS = """You are an intelligent fantasy basketball assistant with direct access to Yahoo Fantasy Sports API. You have comprehensive tools to analyze leagues, teams, players, and matchups. Your job is to proactively gather information and provide complete, insightful answers without asking the user for permission to access data.

CRITICAL INSTRUCTIONS - READ CAREFULLY:

1. BE PROACTIVE - NEVER ASK FOR PERMISSION TO USE TOOLS
   - When a user asks a question, immediately use whatever tools are necessary to answer it
   - DO NOT ask "Would you like me to check the standings?" - JUST CHECK THEM
   - DO NOT ask "Should I look up player stats?" - JUST LOOK THEM UP
   - The user expects you to automatically gather all relevant information
   - If you need data from multiple tools, call all of them without asking

2. MULTI-TOOL USAGE - THINK COMPREHENSIVELY
   When answering questions, consider ALL relevant data sources:
   
   For "Is [team] good?" questions:
   - Call get_league_standings() to see their rank and record
   - Call get_team_roster() to see their players
   - Call get_team_stats() to see their statistical performance
   - Synthesize ALL this data into a comprehensive answer
   
   For "Should I start [player]?" questions:
   - Call get_team_roster() to see the current lineup
   - Call get_player_stats() to check their recent performance
   - Call get_matchup_details() to see the current matchup situation
   - Give a definitive recommendation based on all data

3. CONTEXTUAL UNDERSTANDING
   - Remember information the user has told you in the conversation
   - If user says "my team is Pritchard's Pit Crew", remember this
   - Don't keep asking for the same information repeatedly

4. BE AN EXPERT - Act decisively and provide complete answers using multiple tools automatically."""

model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    tools=[
        get_user_leagues, get_league_settings, get_league_standings, get_league_scoreboard,
        get_league_teams, get_team_roster, get_team_stats, get_team_matchups,
        get_player_stats, search_players, get_player_ownership, get_league_transactions,
        get_team_transactions, get_league_draft_results, get_player_percent_owned,
        get_free_agents, get_matchup_details
    ],
    system_instruction=SYSTEM_INSTRUCTIONS
)

# --- Main App Routes ---
@app.route("/")
def index():
    if 'oauth_token' in session: 
        return redirect(url_for('chat_ui'))
    return '<h1>Welcome</h1><p>Please <a href="/login">login with Yahoo</a> to start the agent.</p>'

@app.route("/login")
def login():
    redirect_uri = url_for('callback', _external=True, _scheme='https')
    oauth = OAuth2Session(CLIENT_ID, redirect_uri=redirect_uri, scope=["fspt-r"])
    authorization_url, state = oauth.authorization_url(AUTHORIZATION_URL)
    session['oauth_state'] = state
    return redirect(authorization_url)

@app.route("/callback")
def callback():
    redirect_uri = url_for('callback', _external=True, _scheme='https')
    oauth = OAuth2Session(CLIENT_ID, state=session['oauth_state'], redirect_uri=redirect_uri)
    token = oauth.fetch_token(TOKEN_URL, client_secret=CLIENT_SECRET, authorization_response=request.url)
    session['oauth_token'] = token
    session['simple_history'] = []  # Store simple text history
    return redirect(url_for('chat_ui'))

@app.route("/chat")
def chat_ui():
    if 'oauth_token' not in session: 
        return redirect(url_for('login'))
    
    html = """<!DOCTYPE html>
<html>
<head>
    <title>Fantasy Agent</title>
    <style>
        body { font-family: system-ui, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
        h1 { color: #333; text-align: center; }
        #chatbox { background: white; border: 1px solid #ddd; border-radius: 8px; height: 600px; overflow-y: auto; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .message { margin-bottom: 15px; padding: 10px; border-radius: 6px; }
        .user-message { background: #007bff; color: white; margin-left: 20%; }
        .llm-message { background: #f8f9fa; margin-right: 20%; }
        .error-message { background: #f8d7da; color: #721c24; }
        .input-container { display: flex; gap: 10px; }
        #userInput { flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 16px; }
        button { padding: 12px 30px; background: #007bff; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; }
        button:hover { background: #0056b3; }
    </style>
</head>
<body>
    <h1>Fantasy Basketball Agent</h1>
    <div id="chatbox"></div>
    <div class="input-container">
        <input type="text" id="userInput" placeholder="Ask about your team, matchups, players, stats..." />
        <button onclick="sendMessage()">Send</button>
    </div>
    <script>
        document.getElementById('userInput').addEventListener('keyup', function(e) {
            if (e.keyCode === 13) sendMessage();
        });
        
        async function sendMessage() {
            const input = document.getElementById('userInput');
            const query = input.value.trim();
            if (!query) return;
            
            addToChatbox(query, 'user-message');
            input.value = '';
            
            try {
                const response = await fetch('/ask', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({query: query})
                });
                const data = await response.json();
                
                if (data.response) {
                    addToChatbox(data.response, 'llm-message');
                } else if (data.error) {
                    addToChatbox('Error: ' + data.error, 'error-message');
                } else {
                    addToChatbox('Unexpected response.', 'error-message');
                }
            } catch (e) {
                addToChatbox('Error: ' + e.message, 'error-message');
            }
        }
        
        function addToChatbox(message, className) {
            const chatbox = document.getElementById('chatbox');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message ' + className;
            messageDiv.innerHTML = message.replace(/\\n/g, '<br>');
            chatbox.appendChild(messageDiv);
            chatbox.scrollTop = chatbox.scrollHeight;
        }
        
        window.onload = function() {
            addToChatbox('Hello! Ask me about your fantasy basketball team - leagues, standings, matchups, free agents, or player stats!', 'llm-message');
        };
    </script>
</body>
</html>"""
    return render_template_string(html)

@app.route("/ask", methods=['POST'])
def ask():
    if 'oauth_token' not in session: 
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        data = json.loads(request.get_data())
        query = data.get('query')
    except:
        query = None
    
    if not query: 
        return jsonify({"error": "No query provided"}), 400
    
    try:
        # Get simple text history
        history = session.get('simple_history', [])
        
        # Build context string from history
        context = ""
        if history:
            context = "Previous conversation:\n"
            for entry in history[-6:]:  # Last 3 exchanges (6 messages)
                context += f"{entry['role']}: {entry['content']}\n"
            context += "\n"
        
        # Add context to system instruction
        full_query = context + "Current user message: " + query
        
        # Create fresh chat each time but with context
        chat = model.start_chat(enable_automatic_function_calling=True)
        response = chat.send_message(full_query)
        
        # Store this exchange
        if 'simple_history' not in session:
            session['simple_history'] = []
        
        session['simple_history'].append({'role': 'user', 'content': query})
        session['simple_history'].append({'role': 'assistant', 'content': response.text})
        
        # Keep only last 20 messages (10 exchanges)
        session['simple_history'] = session['simple_history'][-20:]
        session.modified = True
        
        return jsonify({"response": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
