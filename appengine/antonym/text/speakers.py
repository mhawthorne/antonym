import random

from antonym.core import NotImplementedException


class AbstractSpeaker:
    """ defines speaking algorithm, delegating phrase selection to subclasses """
    
    @classmethod
    def _calculate_length(cls, parts):
        # len(parts) at end is for spaces
        return sum([len(w) for w in parts]) + len(parts)
    
    def speak(self, min_length, max_length, **kw):
        parts = []
        parts_len = 0
        words = None
        while parts_len < max_length:
            attempt = 0
            while not words and attempt < 5:
                words = self.select(parts)
                attempt += 1
            # stops if words couldn't be selected
            if not words:
                break
            
            # ensures that new words will not push me over max_length
            if parts_len + self._calculate_length(words) > max_length:
                break
                
            parts.extend(words)
            
            # resets words
            words = None
            
            parts_len = self._calculate_length(parts)
        return " ".join(parts)

    # "abstract" methods
    
    def ingest(self, phrase):
        raise NotImplementedException()
        
    def select(self, selected):
        raise NotImplementedException()
        
        
class HybridSpeaker(AbstractSpeaker):
    
    def __init__(self, *speakers):
        self.__speakers = speakers
        
    def ingest(self, phrase):
        for s in self.__speakers:
            s.ingest(phrase)

    def compile(self):
        for s in self.__speakers:
            s.compile()
        
    def select(self, selected):
        result = None
        for s in self.__speakers:
            result = s.select(selected)
            if result:
                break
        return result


class RandomSpeaker:

    def __init__(self):
        self.words = set()
    
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