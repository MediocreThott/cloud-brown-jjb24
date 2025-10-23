"""
SQLite3 implementation of the Model class.
"""
import sqlite3

class SQLite3Model:
    """
    SQLite3 implementation of the Model class.  Handles database
    interactions using SQLite3.
    """

    def __init__(self, db_name="songs.db"):
        """
        Initializes the SQLite3Model.

        Args:
            db_name (str, optional): The name of the SQLite3 database file.
                                     Defaults to "songs.db".
        """
        self.db_name = db_name
        self.conn = None

    def get_model(self):
        """
        Returns the SQLite3Model instance itself.  This is a bit of a
        placeholder to match the abstract Model's interface.

        Returns:
            SQLite3Model: The SQLite3Model instance.
        """
        return self

    def connect(self):
        """
        Connects to the SQLite3 database.
        """
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def disconnect(self):
        """
        Disconnects from the SQLite3 database.
        """
        if self.conn:
            self.conn.close()

    def create_table(self):
        """
        Creates the 'songs' table if it doesn't exist.
        """
        self.connect()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS songs (
                title TEXT,
                genre TEXT,
                artist TEXT,
                writer TEXT,
                release_year INTEGER,
                release_month INTEGER,
                lyrics TEXT,
                rating INTEGER,
                url TEXT
            )
        """)
        self.conn.commit()
        self.disconnect()

    def insert(self, title, genre, artist, writer, release_year, release_month, lyrics, rating, url):
        """
        Inserts a new song entry into the database.

        Args:
            title (str): The title of the song.
            genre (str): The genre of the song.
            artist (str): The artist who performs the song.
            writer (str): The writer of the song.
            release_year (int): The year the song was released.
            release_month (int): The month the song was released.
            lyrics (str): The lyrics of the song.
            rating (int): The song rating.
            url (str): The URL of the song.
        """
        self.connect()
        self.cursor.execute("""
            INSERT INTO songs (title, genre, artist, writer, release_year, release_month, lyrics, rating, url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (title, genre, artist, writer, release_year, release_month, lyrics, rating, url))
        self.conn.commit()
        self.disconnect()

    def select(self):
        """
        Retrieves all song entries from the database.

        Returns:
            list: A list of tuples, where each tuple represents a song entry.
        """
        self.connect()
        self.cursor.execute("SELECT * FROM songs")
        rows = self.cursor.fetchall()
        self.disconnect()
        return rows