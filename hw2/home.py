"""
View for the default landing page.
"""
from flask import render_template
from flask.views import MethodView

class Home(MethodView):
    def get(self):
        """
        Handles GET requests to the home route.  Displays the landing page
        with links to other routes.
        """
        return render_template('home.html')