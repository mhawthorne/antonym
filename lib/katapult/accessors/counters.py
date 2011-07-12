import logging
import random

from google.appengine.ext import db

from katapult.models.counters import CounterShard, CounterShardConfiguration


# TODO: caching!
class Counter:
        
    def __init__(self, name, **kw):
        self.name = name
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
        
    def increment(self, amount=1):
        def counter_call(c):
            c.count += amount
        self.__counter_tx(counter_call)
        return self
        
    # TODO: delete counter if decremented to zero
    def decrement(self, amount=1):
        def counter_call(c):
            if c.count > 0: 
                c.count -= amount
        self.__counter_tx(counter_call)
        return self

    def set(self, value):
        """ sets value of counter """
        if value == 0:
            self.delete()
            return
        
        # calculates value to set for all counters    
        counter_q = CounterShard.find_by_name(self.name)
        counter_count = counter_q.count()
        
        if not counter_count:
            # no counters exist, set value to single shard in transaction
            def counter_call(counter):
                counter.count = value
            self.__counter_tx(counter_call)
            return
            
        value_per_counter = float(value) / float(counter_count)
        
        values = []
        # TODO: is there a better way to detect floats than this?
        if (value_per_counter - int(value_per_counter)) > 0:
            # value is a float, I need to found all but last value down, and round last value up
            values.extend([math.floor(value_per_counter.floor) for i in xrange(counter_count)])
            values[-1] = math.ceil(value_per_counter)
        logging.debug("setting counter values across shards: %s" % values)

        # sets values for all counter shards
        for shard, count in zip(counter_q, values):
            shard.count = count
            shard.put()
        
    def delete(self):
        config = CounterShardConfiguration.get_by_key_name(self.name)
        if config:
            config.delete()
        for c in CounterShard.find_by_name(self.name):
            c.delete()
        logging.debug("deleted %s" % self.name)

    def __counter_tx(self, counter_call):
        name = self.name
        config = CounterShardConfiguration.get_or_insert(name, name=name)
        def txn():
            index = random.randint(0, config.shard_count - 1)
            shard_name = "%s/%s" % (name, str(index))
            counter = CounterShard.get_by_key_name(shard_name)
            if counter is None:
                counter = CounterShard(key_name=shard_name, name=name, **self.__kw)
                logging.debug("creating %s" % name)
                
            counter_call(counter)
            
            # I may have decremented a counter down to 0.  in this case I want to delete it
            if counter.count > 0:
                counter.put()
            else:
                counter.delete()
                logging.debug("name:%s count:%s" % (name, counter.count))
        db.run_in_transaction(txn)
