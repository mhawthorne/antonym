#!/usr/bin/env python

import csv
import random
import sys
import traceback

from antonym.text.speakers import speaker_aliases
from katapult.log import config as log_config

speaker_calls = speaker_aliases()

def speaker_list_string():
    return ' | '.join(sorted(speaker_calls.keys()))

log_config()

if len(sys.argv) < 2:
    sys.stderr.write('ERROR - expected <speaker> [count] (%s)\n' % speaker_list_string())
    sys.exit(1)

speaker_name = sys.argv.pop(1)
speak_count = int(sys.argv.pop()) if len(sys.argv) > 1 else 50
    
speaker_call = speaker_calls.get(speaker_name, None)
if not speaker_call:
    sys.stderr.write("ERROR - speaker '%s' not found (available: %s)\n" % (speaker_name, speaker_list_string()))
    sys.exit(2)

speaker = speaker_call()

for row in csv.reader(sys.stdin):
    msg = row[1]
    speaker.ingest(msg)

speaker.compile()
#print speaker.describe()

sizes = [i * 10 for i in range(12,15)]

for i in range(speak_count):
    max_size = random.choice(sizes)
    # min_size = int(max_size * 0.8)
    min_size = 1
    try:
        text = speaker.speak(min_size, max_size)
        print "- (%d/%d) [%d] %s" % (min_size, max_size, len(text), text)
    except Exception, e:
        traceback.print_exc()