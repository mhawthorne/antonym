from google.appengine.ext import db


class CounterShardConfiguration(db.Model):
    """ Tracks the number of shards for each named counter. """

    name = db.StringProperty(required=True)
    shard_count = db.IntegerProperty(required=True, default=1)


class CounterShard(db.Expando):
    """
    Shards for each named counter.
    """
  
    name = db.StringProperty(required=True)
    count = db.IntegerProperty(required=True, default=0)

    @classmethod
    def find_by_name(cls, name):
        return cls.all().filter("name =", name)
        
    @classmethod
    def find_descending(cls, **kw):
        q = cls.all()
        for k, v in kw.iteritems():
            q.filter("%s =" % k, v)
        q.order("-count")
        return q