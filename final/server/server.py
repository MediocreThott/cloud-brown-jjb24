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
# GOOGLE_API_KEY is NO LONGER NEEDED here. Authentication is automatic.

AUTHORIZATION_URL = 'https://api.login.yahoo.com/oauth2/request_auth'
TOKEN_URL = 'https://api.login.yahoo.com/oauth2/get_token'
BASE_API_URL = 'https://fantasysports.yahooapis.com/fantasy/v2'

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
app.secret_key = os.urandom(24) 

# --- Helper to clean Yahoo's messy data format ---
def clean_player_data(player_list):
    # This function is correct and does not need to change.
    player_dict = {}
    for item in player_list:
        if isinstance(item, dict):
            for key, value in item.items():
                if key == 'name': player_dict.update(value)
                else: player_dict[key] = value
    return player_dict

# --- API Tool Functions (for the LLM) ---
# These do not need to change.
def get_leagues():
    """Returns a list of all fantasy basketball league IDs for the current user."""
    if 'oauth_token' not in session: return "User is not authenticated."
    try:
        oauth = OAuth2Session(CLIENT_ID, token=session['oauth_token'])
        url = f"{BASE_API_URL}/users;use_login=1/games;game_keys=nba/leagues?format=json"
        response = oauth.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e: return f"API call failed: {e}"

def get_teams(league_id: str):
    """Returns a list of all teams and their managers for a given league ID."""
    if 'oauth_token' not in session: return "User is not authenticated."
    try:
        oauth = OAuth2Session(CLIENT_ID, token=session['oauth_token'])
        url = f"{BASE_API_URL}/league/{league_id}/teams?format=json"
        response = oauth.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e: return f"API call failed: {e}"

# --- LLM and Chat Setup ---
# genai.configure() is NO LONGER NEEDED. The library handles it automatically.
model = genai.GenerativeModel(
    model_name='gemini-1.5-pro-latest', # Using a standard, powerful model
    tools=[get_leagues, get_teams]
)

# --- Main App Routes ---
@app.route("/")
def index():
    if 'oauth_token' in session: return redirect(url_for('chat_ui'))
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
    session['chat_history'] = []
    return redirect(url_for('chat_ui'))

@app.route("/chat")
def chat_ui():
    if 'oauth_token' not in session: return redirect(url_for('login'))
    return render_template_string("""
        <!DOCTYPE html><html><head><title>Fantasy Agent</title></head>
        <body><h1>Fantasy Basketball Agent</h1>
        <div id="chatbox" style="border:1px solid #ccc; height:400px; overflow-y:scroll; padding:10px;"></div>
        <input type="text" id="userInput" placeholder="Ask a question..." style="width:80%;" onkeyup="if(event.keyCode===13)sendMessage()">
        <button onclick="sendMessage()">Send</button>
        <script>
            async function sendMessage() {
                const input = document.getElementById('userInput');
                const query = input.value; if (!query) return;
                addToChatbox('You: ' + query); input.value = '';
                try {
                    const response = await fetch('/ask', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({query: query})
                    });
                    const data = await response.json();
                    if (data.response) {
                        let formattedResponse = data.response.replace(/\\n/g, '<br>');
                        addToChatbox('LLM: ' + formattedResponse);
                    } else if (data.error) {
                        addToChatbox('Error: ' + JSON.stringify(data.error));
                    } else { addToChatbox('Received an unexpected response format.'); }
                } catch (e) { addToChatbox('Error: ' + e); }
            }
            function addToChatbox(message) {
                const chatbox = document.getElementById('chatbox');
                chatbox.innerHTML += '<div>' + message + '</div>';
                chatbox.scrollTop = chatbox.scrollHeight;
            }
        </script></body></html>
    """)

@app.route("/ask", methods=['POST'])
def ask():
    if 'oauth_token' not in session: return jsonify({"error": "Not authenticated"}), 401
    try:
        data = json.loads(request.get_data()); query = data.get('query')
    except: query = None
    if not query: return jsonify({"error": "No query provided"}), 400
    try:
        chat = model.start_chat(
            history=session.get('chat_history', []),
            enable_automatic_function_calling=True
        )
        response = chat.send_message(query)
        session['chat_history'] = [msg for msg in chat.history if msg.role != 'model' or (msg.parts and msg.parts[0].function_call is None)]
        session.modified = True
        return jsonify({"response": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500