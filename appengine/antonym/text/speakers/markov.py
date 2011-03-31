#!/usr/bin/env python

import logging
import random
import string
from StringIO import StringIO
import sys

from katapult.core import KeyCounter

from antonym.core import DataException, IllegalStateException, MissingDataException, NotImplementedException
from antonym import rrandom
from antonym.text.speakers.core import calculate_length, tokenize_sentences, SelectingSpeaker, Symbols
from antonym.text.speakers.tree import add_words_to_tree, SimpleTreeIterator, Tree


class Markov1Speaker(SelectingSpeaker):
    """ 1st order Markov chain """
    
    def __init__(self):
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

         
    def select(self, selected, min_length, max_length):
        """
        params:
            selected - list of selected words.
        return:
            a tuple of words
        """
        if not self.__words:
            raise MissingDataException("no satisfactory content has been ingested")
        elif not self.__words_compiled:
            self.compile()
        
        # select a trailing word via weighted random
        def select_next(current_word):
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


class Markov2Speaker(SelectingSpeaker):
    """ 2nd order Markov chain.  mostly congruent to Markov1Speaker. """
    
    def __init__(self):
        # keys are word 2-tuples, values are dicts mapping trailing words to frequency
        self.__words = {}
        
        # keys are word 2-tuples, values are tuples of (frequency, list of (word, frequency) tuples)
        self.__words_compiled = {}
        
        # maps phrase start and end words to cardinalities
        self.__heads = KeyCounter()
        self.__tails = KeyCounter()
        
        # list of word-cardinality tuples
        self.__heads_compiled = []
        
    def ingest(self, phrase):
        for sentence in tokenize_sentences(phrase, 50, lowercase=True):
            phrase_words = sentence.split()
            phrase_words.append(Symbols.END)
            phrase_len = len(phrase_words)
        
            # phrases under 3 are of no use to a 2nd-order chain
            if phrase_len < 3:
                return
        
            # grabs first 2 words of phrase
            self.__heads.increment((phrase_words[0], phrase_words[1]))
        
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
        del self.__heads_compiled[0:]
        
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
        
        for pair, count in self.__heads.iteritems():
            self.__heads_compiled.append((pair, count))
        
        # logs all head phrases with cardinality > 1
        # logging.debug("heads: %s" % filter(lambda p: p[1] > 1, sorted(self.__heads.items(), key=lambda p: p[1], reverse=True)))

    def select(self, selected, min_length, max_length):
        """
        params:
            selected - list of selected words.
        return:
            a tuple of words
        """
        if not self.__words:
            raise MissingDataException("no satisfactory content has been ingested")
        elif not self.__words_compiled:
            self.compile()
        
        # select a trailing word via weighted random
        def select_next(current_pair):
            pair_stats = self.__words_compiled.get(current_pair, None)
            next_word = None
            if pair_stats:
                # ends if we're past the min length and have END as a potential next word
                if (calculate_length(selected) > min_length) and \
                    Symbols.END in pair_stats:
                    next_word = None
                else:
                    # don't end if we're not longer than min_length
                    logging.debug("select_next %s %s" % (current_pair, str(pair_stats)))
                    
                    # stats were found for this pair
                    # next_word = rrandom.select_weighted_with_replacement(pair_stats[1])
                    next_word = random.choice(pair_stats[1])[0]
                
            if next_word is Symbols.END: next_word = None
            return (next_word,) if next_word else None
            
        # select first pair via weighted random
        if not selected:
            #next = (rrandom.select_weighted_with_replacement(self.__word_weights))
            next = (rrandom.select_weighted_with_replacement(self.__heads_compiled))
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


class Markov1TreeSpeaker:

    def __init__(self):
        self.__tree = Tree()

    def ingest(self, phrase):
        add_words_to_tree(self.__tree, phrase)
        
    def compile(self):
        pass
        
    def speak(self, min_length, max_length):
        iterator = SimpleTreeIterator(self.__tree)
        words = []
        current_node = None
        while iterator.has_next() and calculate_length(words) < max_length:
            current_node = iterator.next()
            words.append(current_node.key)
            
        # has last word been used to end a phrase?  if not, backtrack
        if not current_node.has("end"):
            iterator.previous();
            
        return " ".join(words)
        