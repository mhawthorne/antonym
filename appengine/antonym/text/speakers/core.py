import random

from nltk.tokenize.punkt import PunktSentenceTokenizer

from antonym.core import MissingDataException, NotImplementedException


def calculate_length(words):
    # len(words) at end is for spaces
    return sum([len(w) for w in words]) + len(words)


class Symbols:

    START = "{start}"
    END = "{end}"


class SelectingSpeaker:
    """ defines speaking algorithm, delegating phrase selection to subclasses """
        
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
            
            # TODO: backtrack to last sensible ending
            # ensures that new words will not push me over max_length
            if parts_len + calculate_length(words) > max_length:
                break
                
            parts.extend(words)
            
            # resets words
            words = None
            
            parts_len = calculate_length(parts)
        return " ".join(parts)
    
    # "abstract" methods
    
    def ingest(self, phrase):
        raise NotImplementedException()
    
    def select(self, selected):
        raise NotImplementedException()

class HybridSpeaker(SelectingSpeaker):
    
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


class SentenceSpeaker:
    
    def __init__(self, **kw):
        """
        keywords:
            ingest_limit - limits the number of sentences ingested at a time.
                if provided, sentences are randomly selected until the max is reached.
        """
        self.__sentences_per_ingest = kw.pop("sentences_per_ingest", None)
        self.__sentences = set()
        self.__tokenizer = PunktSentenceTokenizer()
        
    def ingest(self, phrase):
        total_sentences = [s for s in self.__tokenizer.tokenize(phrase)]
        
        # only ingests ingest_limit sentences if defined
        self.__sentences = set()
        if self.__sentences_per_ingest is None:
            self.__sentences.update(total_sentences)
        else:
            if len(total_sentences) > self.__sentences_per_ingest:
                update = random.sample(total_sentences, self.__sentences_per_ingest)
            else:
                update = total_sentences
            self.__sentences.update(update)
        
    def compile(self):
        pass
                
    def speak(self, min_length, max_length):
        # selects random sentence from list
        def is_length_legit(s):
            s_len = len(s)
            return s_len <= max_length and s_len >= min_length
        candidates = filter(is_length_legit, self.__sentences)
        if not candidates:
            raise MissingDataException("no sentences of appropriate length found")
        return random.choice(candidates).strip()
