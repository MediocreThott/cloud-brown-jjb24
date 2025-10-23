"""
Joshua Brown hw2 python flask app.
"""
import flask
from flask.views import MethodView
from index import Index
from sign import Sign

app = flask.Flask(__name__) 

app.add_url_rule('/',
                 view_func=Index.as_view('index'),
                 methos=["GET"])

app.add_url_rule('/sign',
                 view_func=Sign.as_view('sign'),
                 methods=['GET', 'POST'])

if __name == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

