import flask
import os
from index import Index
from sign import Sign
from home import Home

app = flask.Flask(__name__)  # our Flask app

# Define the URL rules for the application routes
app.add_url_rule('/', view_func=Home.as_view('home'), methods=['GET'])
app.add_url_rule('/entries', view_func=Index.as_view('index'), methods=['GET'])
app.add_url_rule('/sign', view_func=Sign.as_view('sign'), methods=['GET', 'POST'])

if __name__ == '__main__':
    # Cloud Run provides the PORT environment variable
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
