import logging
import random
import re
import traceback

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
                # copies list to protect from select() mutating it
                words = self.select(list(parts), min_length, max_length)
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
    
    def select(self, selected, min_length, max_length):
        raise NotImplementedException()


class HybridWordSpeaker(SelectingSpeaker):
    
    def __init__(self, *speakers):
        self.__speakers = speakers
        
    def ingest(self, phrase):
        for s in self.__speakers:
            s.ingest(phrase)

    def compile(self):
        for s in self.__speakers:
            s.compile()
        
    def select(self, selected, min_length, max_length):
        result = None
        for s in self.__speakers:
            try:
                result = s.select(selected, min_length, max_length)
                if result:
                    break
            except Exception, e:
                logging.warn(traceback.format_exc())
        return result


class HybridPhraseSpeaker:
    
    def __init__(self, *speakers):
        self.__speakers = speakers
        
    def ingest(self, phrase):
        for s in self.__speakers:
            s.ingest(phrase)

    def compile(self):
        for s in self.__speakers:
            s.compile()
    
    def speak(self, min_length, max_length):
        for s in self.__speakers:
            try:
                result = s.speak(min_length, max_length)
                break
            except Exception, e:
                logging.error(traceback.format_exc())
        logging.debug("used speaker: %s" % s)
        return result
    
    def __repr__(self):
        return "%s{%s}" % (self.__class__, self.__speakers)


class RandomSpeaker(SelectingSpeaker):

    def __init__(self):
        self.words = set()
    
    def ingest(self, phrase):
        for word in phrase.split():
            self.words.add(word)

    def select(self, selected, min_length, max_length):
        while True:
            w = random.sample(self.words, 1)
            if w not in selected:
                break
        return w

    def compile(self):
        pass


_sentence_tokenizer = PunktSentenceTokenizer()

_sentence_replace_regex = re.compile("\s+", re.DOTALL | re.UNICODE)
_sentence_accept_regex = re.compile("\S+")

def tokenize_sentences(phrase, limit=None):
    phrase = phrase.strip()
    sentences = [s for s in _sentence_tokenizer.tokenize(phrase)]
    if limit and len(sentences) >= limit:
        sentence_generator = random.sample(sentences, limit)
    else:
        sentence_generator = sentences

    for token in sentence_generator:
        # logging.debug("token sentence: '%s'" % token)
        replacement = _sentence_replace_regex.sub(" ", token)
        if replacement != token:
            # logging.debug("replaced '%s' with '%s'" % (token, replacement))
            pass
        if _sentence_accept_regex.match(replacement):
            # logging.debug("sentence: '%s'" % replacement)
            yield replacement
        else:
            logging.debug("ignoring sentence: '%s'" % replacement)


class PhraseSpeaker:
    
    def __init__(self):
        self.__phrases = set()
        
    def compile(self):
        pass
        
    def ingest(self, phrase):
        self.__phrases.add(phrase)
        
    def speak(self, min_length, max_length):
        def is_length_legit(s):
            s_len = len(s)
            return s_len <= max_length and s_len >= min_length
        candidates = filter(is_length_legit, self.__phrases)
        if not candidates:
            raise MissingDataException("no sentences of appropriate length found")
        return random.choice(candidates).strip()


class SentenceTokenizingSpeaker:
    
    def __init__(self, delegate):
        self.__delegate = delegate
        
    def compile(self):
        self.__delegate.compile()
        
    def ingest(self, text):
        for sentence in tokenize_sentences(text):
            self.__delegate.ingest(sentence)
            
    def speak(self, min_length, max_length):
        return self.__delegate.speak(min_length, max_length)


class SentenceSpeaker:
    
    def __init__(self, sentences_per_ingest=None):
        """
        keywords:
            ingest_limit - limits the number of sentences ingested at a time.
                if provided, sentences are randomly selected until the max is reached.
        """
        self.__sentences_per_ingest = sentences_per_ingest
        self.__sentences = set()
        
    def ingest(self, phrase):
        # only ingests ingest_limit sentences if defined
        update_sentences = [s for s in tokenize_sentences(phrase, self.__sentences_per_ingest)]
        
        for sentence in update_sentences:
            logging.debug("ingesting sentence: '%s'" % sentence)
            self.__sentences.add(sentence)
        
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
