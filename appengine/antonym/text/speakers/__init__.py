import random

from antonym.core import IllegalArgumentException, MissingDataException, NotImplementedException
from antonym.rrandom import select_weighted_with_replacement
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
    return speaker_alias, _speaker_aliases[speaker_alias]()

_speakers_weighted = ((new_speaker("s"), 5), (new_speaker("g.nx"), 5))

def new_random_speaker():
    return select_weighted_with_replacement(_speakers_weighted)
