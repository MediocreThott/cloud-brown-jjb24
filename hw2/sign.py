"""
View for handling the song submission form.
"""
from flask import redirect, request, url_for, render_template
from flask.views import MethodView  # Corrected import
from model_sqlite3 import SQLite3Model

gbmodel = SQLite3Model()

class Sign(MethodView):
    def get(self):
        """
        Handles GET requests to the sign route.  Displays the song
        submission form.
        """
        return render_template('sign.html')

    def post(self):
        """
        Handles POST requests to the sign route.  Processes the form
        submission and redirects to the index page.
        """
        model = gbmodel
        title = request.form['title']
        genre = request.form['genre']
        artist = request.form['artist']
        writer = request.form['writer']
        release_year = int(request.form['release_year'])
        release_month = int(request.form['release_month'])
        lyrics = request.form['lyrics']
        rating = int(request.form['rating'])
        url = request.form['url']

        model.insert(title, genre, artist, writer, release_year, release_month, lyrics, rating, url)
        return redirect(url_for('index'))