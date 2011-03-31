import random

from antonym.core import IllegalArgumentException, MissingDataException, NotImplementedException
from antonym.rrandom import select_weighted_with_replacement
from antonym.text.speakers.core import HybridPhraseSpeaker, HybridWordSpeaker, RandomSpeaker, SentenceSpeaker
from antonym.text.speakers.graph import GraphSpeaker, NxGraphSelectingSpeaker, NxGraphShortestPathSpeaker, NxGraphSpeaker
from antonym.text.speakers.markov import Markov1TreeSpeaker, Markov1Speaker, Markov2Speaker
from antonym.text.speakers.tree import TreeSpeaker


_speaker_aliases = { 'g': lambda: GraphSpeaker(),
    'nx': lambda: NxGraphSpeaker(),
    'nx.sp': lambda: NxGraphShortestPathSpeaker(),
    'nx.s': lambda: NxGraphSelectingSpeaker(),
    'nx-nx.sp-r': lambda: HybridPhraseSpeaker(NxGraphSpeaker(), NxGraphShortestPathSpeaker(), RandomSpeaker()),
    'nx-r': lambda: HybridPhraseSpeaker(NxGraphSpeaker(), RandomSpeaker()),
    'm1': lambda: Markov1Speaker(),
    'm1-t': lambda: Markov1TreeSpeaker(),
    'm2': lambda: Markov2Speaker(),
    'm2-m1': lambda: HybridWordSpeaker(Markov2Speaker(), Markov1Speaker()),
    'r': lambda: RandomSpeaker(),
    's': lambda: SentenceSpeaker(sentences_per_ingest=20),
    's-r': lambda: HybridPhraseSpeaker(SentenceSpeaker(sentences_per_ingest=20), RandomSpeaker()),
    't': lambda: TreeSpeaker()
}
    
def speaker_aliases():
    return _speaker_aliases

def new_speaker(speaker_alias='s'):
    if not speaker_alias in _speaker_aliases:
        raise IllegalArgumentException("speaker not found: '%s'" % speaker_alias)
    return speaker_alias, _speaker_aliases[speaker_alias]()

# TODO: is this causing our memory leak?  module caching is causing the nx graph to stay in memory?
_speakers_weighted = (("s-r", 4), ("nx-r", 6))

def new_random_speaker():
    return new_speaker(select_weighted_with_replacement(_speakers_weighted))
