"""
Joshua Brown hw2 python flask app.
"""
import flask
from flask.views import MethodView
from index import Index
from sign import Sign
from model_sqlite3 import SQLite3Model
from home import Home

app = flask.Flask(__name__)  # our Flask app

# Initialize the SQLite3 model
gbmodel = SQLite3Model()
gbmodel.connect() # Connect to the database and create the table

app.add_url_rule('/', view_func=Home.as_view('home'), methods=['GET'])  # Default landing page
app.add_url_rule('/entries', view_func=Index.as_view('index'), methods=['GET'])  # Route to view entries
app.add_url_rule('/sign', view_func=Sign.as_view('sign'), methods=['GET', 'POST'])  # Route for inserting entries

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
