import random

from antonym.core import IllegalArgumentException, MissingDataException, NotImplementedException
from antonym.text.speakers.core import HybridSpeaker, SentenceSpeaker
from antonym.text.speakers.graph import GraphSpeaker, NxGraphSpeaker
from antonym.text.speakers.markov import Markov1TreeSpeaker, Markov1Speaker, Markov2Speaker
from antonym.text.speakers.tree import TreeSpeaker


_speaker_aliases = { 'g': lambda: GraphSpeaker(),
    'g.nx': lambda: NxGraphSpeaker(),
    'm1': lambda: Markov1Speaker(),
    'm1.t': lambda: Markov1TreeSpeaker(),
    'm2': lambda: Markov2Speaker(),
    'm2.1': lambda: HybridSpeaker(Markov2Speaker(), Markov1Speaker()),
    'r': lambda: RandomSpeaker(),
    's': lambda: SentenceSpeaker(sentences_per_ingest=20),
    't': lambda: TreeSpeaker()
}

def speaker_aliases():
    return _speaker_aliases

def new_speaker(speaker_alias='s'):
    if not speaker_alias in _speaker_aliases:
        raise IllegalArgumentException("speaker not found: '%s'" % speaker_alias)
    return _speaker_aliases[speaker_alias]()