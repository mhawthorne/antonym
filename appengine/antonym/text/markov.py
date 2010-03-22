#!/usr/bin/env python

import random
import string
from StringIO import StringIO
import sys

from katapult.log import config as logging_config, LoggerFactory

from antonym.core import DataException, IllegalStateException
from antonym import rrandom


def fail(msg, code=1):
    sys.stderr.write("%s\n" % msg)
    sys.exit(code)


class AbstractSpeaker:
    """ defines speaking algorithm, delegating phrase selection to subclasses """
    
    @classmethod
    def _calculate_length(cls, parts):
        # len(parts) at end is for spaces
        return sum([len(w) for w in parts]) + len(parts)
    
    def speak(self, min_length, max_length, **kw):
        logger = LoggerFactory.logger(self.__class__.__name__)
        
        parts = []
        parts_len = 0
        words = None
        while parts_len < max_length:
            attempt = 0
            while not words and attempt < 5:
                # if attempt > 0:
                #     self.__logger.debug("attempt %d selecting for %s" % (attempt, parts))
                words = self.select(parts)
                attempt += 1
            # stops if words couldn't be selected
            if not words:
                break
            # logger.debug("speak words:%s" % repr(words))
            
            # ensures that new words will not push me over max_length
            if parts_len + self._calculate_length(words) > max_length:
                break
                
            parts.extend(words)
            
            # resets words
            words = None
            
            parts_len = self._calculate_length(parts)
        return " ".join(parts)


class Markov1Speaker(AbstractSpeaker):
    """ 1st order Markov chain """
    
    def __init__(self):
        self.__logger = LoggerFactory.logger(self.__class__.__name__)
        
        # keys are words, values are dicts mapping trailing words to frequency
        self.__words = {}
        
        # keys are words, values are tuples of (frequency, list of (word, frequency) tuples)
        self.__words_compiled = {}
        
    def ingest(self, phrase):
        phrase_words = phrase.split()
        phrase_len = len(phrase_words)
        for i in range(phrase_len):
            w1 = phrase_words[i]
            w2 = phrase_words[i + 1] if i < phrase_len-1 else None
            if w1 in self.__words:
                trailing_words = self.__words[w1]
                if w2 in trailing_words:
                    trailing_words[w2] = trailing_words[w2] + 1
                else:
                    trailing_words[w2] = 1
            else:
                trailing_words = {w2: 1}
                self.__words[w1] = trailing_words
    
    def compile(self):
        """ converts word grid into more efficient structure """
        self.__words_compiled = {}
        
        for w1 in self.__words:
            trailing_words = []
            w1_count = 0
            for w2, count in self.__words[w1].iteritems():
                trailing_words.append((w2, count))
                w1_count += count
                
            self.__words_compiled[w1] = (w1_count, trailing_words)
         
        self.__word_weights = []
        for w, p in self.__words_compiled.iteritems():
            self.__word_weights.append((w, p[0]))

         
    def select(self, selected):
        """
        params:
            selected - list of selected words.
        return:
            a tuple of words
        """
        # self.__logger.debug("select selected:%s" % selected)
        
        if not self.__words:
            raise IllegalStateException("no satisfactory content has been ingested")
        elif not self.__words_compiled:
            self.compile()
        
        # select a trailing word via weighted random
        def select_next(current_word):
            # self.__logger.debug("select select_next current_pair:%s" % repr(current_pair))
            word_stats = self.__words_compiled.get(current_word, None)
            next_word = None
            if word_stats:
                # stats were found for this word
                next_word = rrandom.select_weighted_with_replacement(word_stats[1])
            return (next_word,) if next_word else None
        
        if not selected:
            # select first word
            next = (rrandom.select_weighted_with_replacement(self.__word_weights),)
        else:
            # select next word using last word
            next = select_next(selected[-1])

        return next      

    def _speak(self, min_length, max_length, **kw):
        parts = []
        
        # select first word via weighted random
        
        prev = None
        current = rrandom.select_weighted_with_replacement(word_weights)
        
        parts.append(current)
        parts_len = len(current)
        
        # select trailing words via weighted random until we've reached the max length
        def select(current_word):
            return rrandom.select_weighted_with_replacement(self.__words_compiled[current_word][1])
            
        while parts_len < max_length and current is not None:
            prev = current
            current = select(current)
            #self.__logger.debug("prev: '%s' current: '%s' parts_len:%d" % (prev, current, parts_len))
                        
            if current is None:
                # None means the possible end of the sentence
                
                # breaks if we selected an endpoint and we're past the min length
                if parts_len > min_length:
                    break
                    
                # I'm not past the min length, so I only give up after trying to find another word 5 times.
                attempt = 0
                while current is None and attempt < 5:
                    current = select(prev)
                    attempt += 1
            
            # if I wasn't able to find a word, I quit.
            # TODO: consider throwing an exception
            if current is None:
                break
                
            # breaks if next word will push us over the limit
            if parts_len + len(current) >= max_length:
                break
                
            parts.append(current)
            
            # len(parts) at end is for spaces
            parts_len = sum([len(w) for w in parts]) + len(parts)
            
        return " ".join(parts)

    def describe(self):
        parts = []
        for w1, suffix_count in sorted(self.__words.iteritems()):
            parts.append("%s\n" % w1)
            for w2, count in sorted(suffix_count.iteritems(), key=lambda p: p[1], reverse=True):
                parts.append("  %s: %d\n" % (w2, count))
        return "".join(parts)


class Markov2Speaker(AbstractSpeaker):
    """ 2nd order Markov chain.  mostly congruent to Markov1Speaker. """
    
    def __init__(self):
        self.__logger = LoggerFactory.logger(self.__class__.__name__)
        
        # keys are word 2-tuples, values are dicts mapping trailing words to frequency
        self.__words = {}
        
        # keys are word 2-tuples, values are tuples of (frequency, list of (word, frequency) tuples)
        self.__words_compiled = {}
        
    def ingest(self, phrase):
        phrase_words = phrase.split()
        phrase_len = len(phrase_words)
        
        # phrases under 3 are of no use to a 2nd-order chain
        if phrase_len < 3:
            return
            
        for i in range(phrase_len - 2):
            w1 = phrase_words[i]
            w2 = phrase_words[i + 1]
            w3 = phrase_words[i + 2]
            
            w_pair = (w1, w2)
            if w_pair in self.__words:
                trailing_words = self.__words[w_pair]
                if w3 in trailing_words:
                    trailing_words[w3] = trailing_words[w3] + 1
                else:
                    trailing_words[w3] = 1
            else:
                trailing_words = {w3: 1}
                self.__words[w_pair] = trailing_words

    def compile(self):
        """ converts word grid into more efficient structure """
        self.__words_compiled.clear()
        # self.__logger.debug("compile words:%s" % self.__words)
        for w_pair in self.__words:
            trailing_words = []
            w_pair_count = 0
            for w, count in self.__words[w_pair].iteritems():
                trailing_words.append((w, count))
                w_pair_count += count
                
            self.__words_compiled[w_pair] = (w_pair_count, trailing_words)

        # builds list of (word 2-tuple, frequency) tuples
        self.__word_weights = []
        for w_pair, p in self.__words_compiled.iteritems():
            self.__word_weights.append((w_pair, p[0]))
        
    def select(self, selected):
        """
        params:
            selected - list of selected words.
        return:
            a tuple of words
        """
        # self.__logger.debug("select selected:%s" % selected)
        
        if not self.__words:
            raise IllegalStateException("no satisfactory content has been ingested")
        elif not self.__words_compiled:
            self.compile()
        
        # select a trailing word via weighted random
        def select_next(current_pair):
            # self.__logger.debug("select select_next current_pair:%s" % repr(current_pair))
            pair_stats = self.__words_compiled.get(current_pair, None)
            next_word = None
            if pair_stats:
                # stats were found for this pair
                next_word = rrandom.select_weighted_with_replacement(pair_stats[1])
            return (next_word,) if next_word else None
            
        # select first pair via weighted random
        if not selected:
            next = (rrandom.select_weighted_with_replacement(self.__word_weights))
        else:
            # select using last 2 words as params
            next = select_next((selected[-2], selected[-1]))

        return next      
        
    def describe(self):
        parts = []
        for w_pair, suffix_count in sorted(self.__words.iteritems()):
            parts.append("%s %s\n" % w_pair)
            for w_tail, count in sorted(suffix_count.iteritems(), key=lambda p: p[1], reverse=True):
                parts.append("  %s: %d\n" % (w_tail, count))
        return "".join(parts)


class TwittovSpeaker:
    """ This maintains a dictionary of Markov chains and heads. """

    def __init__(self):
        self.chains = {}
        self.heads = []
        self.tails = []
        self.__logger = LoggerFactory.logger(self.__class__.__name__)

    def ingest(self, phrase):
        
        """ Processes the text and gathers a->b relations for the database. Input
                can be either a sequence of strings, or a single string.
        """
        words = phrase.split()

        if len(words) >= 3:
            head = (words[0], words[1])
            if head not in self.heads:
                self.heads.append(head)

            tail = (words[-2], words[-1])
            if tail not in self.tails:
                self.tails.append(tail)

        for w1, w2, w3 in self.__triples(words):
            pair = (w1, w2)
            if pair not in self.chains:
                self.chains[pair] = [w3]
            else:
                self.chains[pair].append(w3)
    
    def describe(self):
        return repr(self.chains)
    
    def speak(self, min_length, max_length, **kw):
        """ Uses our markov chains to generate text of a minimum no. words. """
        randomness = kw.pop("randomness", 1)
        attempts = kw.pop("attempts", 1)
        text = kw.pop("text", None)
        
        # If text is empty, we have to generate a seed.
        tries = 0
        while not text:
            text = self.__generate_seed(randomness)
            tries += 1
            if tries > attempts:
                raise DataException("Couldn't produce a seed. Try decreasing the randomness.")
                
        text_len = len(text)
        if text_len >= max_length:
            return self.__prettify(text)

        else:
            text.extend(self.__generate_seed(randomness))
            return self.speak(min_length, max_length, randomness=randomness, text=text)

    def __generate_seed(self, randomness):
    
        """ Uses the Markov chains to generate a single sentence. If we can't meetz
                the randomness threshold, the function returns False.
        """
        self.__logger.debug("heads: %s" % self.heads)
        if not self.heads: raise DataException("insufficient data has been ingested")
            
        seed = random.choice(self.heads)
        #self.__logger.debug("seed: %s" % [seed])
        
        text = [ seed[0], seed[1], random.choice(self.chains[seed]) ]

        branches = 0
        while (text[-2], text[-1]) in self.chains:
            results = self.chains[(text[-2], text[-1])]
            branches = branches + len(results) - 1
            text.append(random.choice(results))

            # If it's long and we're at a tail, we can stop.
            if len(text) >= 10 and (text[-2], text[-1]) in self.tails:
                break

            # We check to make sure we're not infinite looping.
            if len(text) >= 3 and text[-1] == text[-2] and text[-2] == text[-3]:
                break
            
        # if branches < randomness:
        #     return False 

        #text.append('\n')
        return text 

    def __prettify(self, textArray):
        """ Converts the text to a string, and then converts to paragraphs. """
        return " ".join(textArray)
        
        # text = string.join(textArray)
        # text = text.split('\n')
        # 
        # i = 1
        # length = len(text)
        # while i < length:
        #     if not i % 6:
        #         i += 1
        #         text.insert(i, '\n\n')
        #     i += 1
        #     length = len(text)
        # 
        # text = string.join(text).strip()
        # return text
        
    def __triples(self, words):

        """ Generates triples from the given data string. So if our string were
                "What a lovely day", we'd generate (What, a, lovely) and then
                (a, lovely, day).
        """

        if len(words) < 3:
            return

        for i in range(len(words) - 2):
            yield (words[i], words[i+1], words[i+2])
