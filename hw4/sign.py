# File: sign.py

from flask import redirect, request, url_for, render_template
from flask.views import MethodView
import gbmodel

class Sign(MethodView):
    def get(self):
        """
        Handles GET requests to the sign route. Displays the song
        submission form.
        """
        return render_template('sign.html')

    def post(self):
        """
        Handles POST requests from the form submission. Inserts the new
        song into the database and redirects to the entry list.
        """
        model = gbmodel.get_model()
        
        model.insert(
            request.form['title'],
            request.form['genre'],
            request.form['artist'],
            request.form['writer'],
            request.form['release_year'],
            request.form['release_month'],
            request.form['lyrics'],
            request.form['rating'],
            request.form['url']
        )
        return redirect(url_for('index'))
