import os
from flask import Flask, request, redirect, session, url_for, jsonify
from yahoo_oauth import OAuth2
from yahoo_fantasy_api import Game, League
from werkzeug.middleware.proxy_fix import ProxyFix

CLIENT_ID = os.getenv('YAHOO_CLIENT_ID')
CLIENT_SECRET = os.getenv('YAHOO_CLIENT_SECRET')

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
app.secret_key = os.urandom(24) 

# We do NOT specify a redirect_uri here, we will do it dynamically.
oauth = OAuth2(CLIENT_ID, CLIENT_SECRET, store_token='session')

@app.route("/login")
def login():
    # This is the crucial fix. We build the callback URL based on where the
    # request is coming from, which works in Cloud Shell, Cloud Run, and localhost.
    # request.host_url will be 'https://8080-....cloudshell.dev/'
    callback_url = url_for('callback', _external=True)
    
    # We store it in the session to use it in the callback
    session['callback_url'] = callback_url
    
    # We pass it to the get_login_url method
    return redirect(oauth.get_login_url(redirect_uri=callback_url))

@app.route("/callback")
def callback():
    # We retrieve the dynamic callback URL from the session
    callback_url = session.get('callback_url')
    
    # We must provide the same redirect_uri when handling the response
    oauth.handle_redirect(request.url, redirect_uri=callback_url)
    return redirect(url_for('index'))

# ... ALL OTHER ROUTES (index, leagues, standings, etc.) ARE UNCHANGED ...
@app.route("/")
def index():
    if oauth.token_is_valid():
        return "<h1>Success! Container is running correctly.</h1>"
    else:
        return '<h1>Welcome</h1><p>Please <a href="/login">login with Yahoo</a></p>'

# (The rest of your working API endpoints go here, they don't need to change)
# For brevity, I'm omitting them, but make sure they are in your file.
# ...
# ---

if __name__ == "__main__":
    # This part is for local development only, it's not used in the container
    app.run(ssl_context='adhoc', host='localhost', port=8080, debug=True)