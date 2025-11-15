# File: gbmodel/model_datastore.py

from .Model import Model
from datetime import datetime
from google.cloud import datastore

def from_datastore(entity):
    """Translates Datastore results into the format expected by the application."""
    if not entity:
        return None
    if isinstance(entity, list):
        entity = entity.pop()
    
    # The order of fields returned here must match the order in index.py
    return [
        entity.get('title'),
        entity.get('genre'),
        entity.get('artist'),
        entity.get('writer'),
        entity.get('release_year'),
        entity.get('release_month'),
        entity.get('lyrics'),
        entity.get('rating'),
        entity.get('url')
    ]

class model(Model):
    def __init__(self):
        # Initialize the Datastore client. It will automatically use the
        # project ID from the environment when running on Google Cloud.
        self.client = datastore.Client()

    def select(self):
        # Query the Datastore for all entities of the Kind 'SongsHW4'.
        # Using 'SongsHW4' ensures data doesn't conflict with other labs.
        query = self.client.query(kind='SongsHW4')
        entities = list(map(from_datastore, query.fetch()))
        return entities

    def insert(self, title, genre, artist, writer, release_year, release_month, lyrics, rating, url):
        # Create a new key for the 'SongsHW4' Kind.
        key = self.client.key('SongsHW4')
        song_entity = datastore.Entity(key)

        # Update the entity with all the song data.
        song_entity.update({
            'title': title,
            'genre': genre,
            'artist': artist,
            'writer': writer,
            'release_year': int(release_year),
            'release_month': int(release_month),
            'lyrics': lyrics,
            'rating': int(rating),
            'url': url,
            'created': datetime.today()
        })

        # Save the entity to Datastore.
        self.client.put(song_entity)
        return True
