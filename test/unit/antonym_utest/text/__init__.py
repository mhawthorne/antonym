import random

from katapult.mocks import MockEntity


WORDS = frozenset(("how", "pakistan", "where", "dinosaurs",
    "a", "elephant", "is", "clowns", 
    "at", "vampires", "or", "electrodes"))

def generate_phrase(length):
    return " ".join(random.sample(WORDS, length))
    
def create_content_list(count, phrase_length=8):
    source_name = "source-%s"
        
    return [MockEntity(key_name=str(count),
        source=MockEntity(key_name=source_name),
        source_name=source_name % count,
        body=generate_phrase(phrase_length)) for i in xrange(count)]