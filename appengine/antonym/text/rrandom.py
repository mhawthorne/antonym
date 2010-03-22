import random

from katapult.log import LoggerFactory


class RandomSpeaker:

    def __init__(self):
        self.words = set()
        self.__logger = LoggerFactory.logger(self.__class__)
    
    def ingest(self, phrase):
        for word in phrase.split():
            self.words.add(word)
        
    def speak(self, min_length, max_length):
        parts = []
        
        def get_phrase_len():
            return sum([len(w) + 2 for w in parts])
            
        for w in random.sample(self.words, max_length):
            if (get_phrase_len() + len(w)) < max_length:
                parts.append(w)
        
        return " ".join(parts)
        
    def compile(self):
        pass
