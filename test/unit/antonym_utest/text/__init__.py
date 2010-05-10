import random

from katapult.mocks import MockEntity


WORDS = frozenset(("how", "pakistan", "where", "dinosaurs",
    "a", "elephant", "is", "clowns", 
    "at", "vampires", "or", "electrodes"))

def generate_phrase():
    return " ".join(random.sample(WORDS, 8))
    
def create_content_list(count):
    source_name = "source-%s"
        
    return [MockEntity(key_name=str(count),
        source=MockEntity(key_name=source_name),
        source_name=source_name % count,
        body=generate_phrase()) for i in xrange(count)]