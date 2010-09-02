import random
import sha
import uuid

from katapult.core import DataException


def get_reference_safely(entity, name):
    try:
        return getattr(entity, name)
    except Exception, e:
        return None

def entity_to_hash(entity):
    result = {}
    for p in entity.properties():
        result[p] = getattr(entity, p)
    return result

def entity_has_property(entity, prop):
    """
    returns:
        True if entity has the property
    """
    return prop in entity.properties()


def random_query_results(query, count, fetch_count=1000):
    """
    returns:
        count items
    raises:
        DataException - if count items cannot be found
    """
    q_count = query.count()
    if not q_count:
        raise DataException("query returned no results")
    if count > q_count:
        count = q_count
    # TODO: do I need q.fetch here or not
    return random.sample([m for m in query.fetch(fetch_count)], count)


class IdGenerator:
    
    @classmethod
    def hash(cls, string):
        return sha.new(string).hexdigest()

    @classmethod
    def uuid(cls):
        return uuid.uuid1().hex


class Models:
    
    # deprecated
    @classmethod
    def to_hash(cls, model):
        result = {}
        for p in model.properties():
            result[p] = getattr(model, p)
        return result
    
    # deprecated    
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
        # TODO: do I need q.fetch here or not
        return random.sample([m for m in q.fetch(1000)], count)