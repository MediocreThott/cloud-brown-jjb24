import os
from flask import Flask, request, redirect, session, url_for
from dotenv import load_dotenv
from yahoo_oauth import OAuth2

load_dotenv()

# --- Configuration ---
CLIENT_ID = os.getenv('YAHOO_CLIENT_ID')
CLIENT_SECRET = os.getenv('YAHOO_CLIENT_SECRET')

app = Flask(__name__)
app.secret_key = os.urandom(24) 

oauth = OAuth2(CLIENT_ID, CLIENT_SECRET, store_token='session')

@app.route("/")
def index():
    """The main page. Checks auth status."""
    # ---- THIS IS THE CORRECTED LINE ----
    if oauth.token_is_valid():
        return "<h1>Success!</h1><p>You are authenticated. We can now make API calls.</p>"
    else:
        return '<h1>Welcome</h1><p>Please <a href="/login">login with Yahoo</a> to continue.</p>'

@app.route("/login")
def login():
    """Starts the OAuth2 flow by redirecting the user to Yahoo."""
    return redirect(oauth.get_login_url())

@app.route("/callback")
def callback():
    """Handles the redirect back from Yahoo and gets the token."""
    oauth.handle_redirect(request.url)
    return redirect(url_for('index'))

if __name__ == "__main__":
    # Runs the app with a self-signed SSL cert for local HTTPS
    app.run(ssl_context='adhoc', host='localhost', port=8080, debug=True)