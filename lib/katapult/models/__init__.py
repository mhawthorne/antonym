import random
import sha
import uuid

from katapult.core import DataException


class IdGenerator:
    
    @classmethod
    def hash(cls, string):
        return sha.new(string).hexdigest()

    @classmethod
    def uuid(cls):
        return uuid.uuid1().hex


class Models:
    
    @classmethod
    def to_hash(cls, model):
        result = {}
        for p in model.properties():
            result[p] = getattr(model, p)
        return result
        
    @classmethod
    def find_random(cls, q, count):
        """
        params:
            q - Query
            count - number of items to reutnr
        returns:
            list of items
        raises:
            DataException if query returns no results
        """
        q_count = q.count()
        if not q_count:
            raise DataException("query returned no results")
        if count > q_count:
            count = q_count
        return random.sample([m for m in q], count)