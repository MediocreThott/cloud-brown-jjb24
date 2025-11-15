# File: index.py

from flask import render_template
from flask.views import MethodView
import gbmodel

class Index(MethodView):
    def get(self):
        """
        Handles GET requests to the index route. Retrieves and displays
        all song entries from the configured model.
        """
        model = gbmodel.get_model()
        entries = [dict(title=row[0], genre=row[1], artist=row[2], writer=row[3],
                        release_year=row[4], release_month=row[5], lyrics=row[6],
                        rating=row[7], url=row[8]) for row in model.select()]
        return render_template('index.html', entries=entries)
