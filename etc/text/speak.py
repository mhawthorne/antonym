#!/usr/bin/env python

import csv
import random
import sys

from antonym.text.markov import Markov1Speaker, Markov2Speaker
from antonym.text.rrandom import RandomSpeaker
from katapult.log import config as log_config


speakers = { 'markov1': Markov1Speaker(),
    'markov2' : Markov2Speaker(),
    'random': RandomSpeaker() }

def speaker_list_string():
    return ' | '.join(speakers.keys())

log_config()

if len(sys.argv) < 2:
    sys.stderr.write('ERROR - expected <speaker> [count] (%s)\n' % speaker_list_string())
    sys.exit(1)

speaker_name = sys.argv.pop(1)
speak_count = int(sys.argv.pop()) if len(sys.argv) > 1 else 50
    
speaker = speakers.get(speaker_name)
if not speaker:
    sys.stderr.write("ERROR - speaker '%s' not found (available: %s)\n" % (speaker_name, speaker_list_string()))
    sys.exit(2)

for row in csv.reader(sys.stdin):
    msg = row[2]
    speaker.ingest(msg)

speaker.compile()
#print speaker.describe()

sizes = [i * 10 for i in range(12,15)]

for i in range(speak_count):
    max_size = random.choice(sizes)
    min_size = int(max_size * 0.8)
    text = speaker.speak(min_size, max_size)
    print "- (%d/%d) [%d] %s" % (min_size, max_size, len(text), text)