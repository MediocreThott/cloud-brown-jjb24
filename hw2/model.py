"""
Abstract base class for data models.
"""
from abc import ABC, abstractmethod

class Model(ABC):
    """
    Abstract base class for data models.  Defines the interface for
    interacting with data storage.
    """

    @abstractmethod
    def get_model(self):
        """
        Returns a data access object for the model.

        Returns:
            object: A data access object.
        """
        pass

    @abstractmethod
    def insert(self, *args):
        """
        Inserts a new entry into the data store.

        Args:
            *args:  Data to be inserted.  The specific arguments will
                    depend on the derived class.
        """
        pass

    @abstractmethod
    def select(self):
        """
        Retrieves all entries from the data store.

        Returns:
            list: A list of entries.
        """
        pass