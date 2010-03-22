import random

from google.appengine.ext import db

from katapult import log
from katapult.models.counters import CounterShard, CounterShardConfiguration


# TODO: caching!
class Counter:
        
    def __init__(self, name, **kw):
        self.name = name
        self.__logger = log.LoggerFactory.logger("counter")
        self.__kw = kw

    def __shards(self):
        return CounterShard.find_by_name(self.name)
    
    def exists(self):
        return self.__shards().count() > 0

    def count(self):
        total = 0
        for counter in self.__shards():
            total += counter.count
        return total
        
    def increment(self):
        def counter_call(c):
            c.count += 1
        self.__counter_tx(counter_call)
        return self
        
    # TODO: delete counter if decremented to zero
    def decrement(self):
        def counter_call(c):
            if c.count > 0: 
                c.count -= 1
        self.__counter_tx(counter_call)
        return self

    def delete(self):
        CounterShardConfiguration.get_by_key_name(self.name).delete()
        for c in CounterShard.all().filter("name =", self.name):
            c.delete()
        self.__logger.debug("deleted %s" % self.name)

    def __counter_tx(self, counter_call):
        name = self.name
        config = CounterShardConfiguration.get_or_insert(name, name=name)
        def txn():
            index = random.randint(0, config.shard_count - 1)
            shard_name = "%s/%s" % (name, str(index))
            counter = CounterShard.get_by_key_name(shard_name)
            if counter is None:
                counter = CounterShard(key_name=shard_name, name=name, **self.__kw)
                self.__logger.debug("creating %s" % name)
                
            counter_call(counter)
            
            # I may have decremented a counter down to 0.  in this case I want to delete it
            if counter.count > 0:
                counter.put()
            else:
                counter.delete()
            self.__logger.debug("name:%s count:%s" % (name, counter.count))
        db.run_in_transaction(txn)
