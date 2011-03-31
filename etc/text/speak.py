#!/usr/bin/env python

import csv
import logging
from optparse import OptionParser
import random
import sys
import traceback

from antonym.text.speakers import speaker_aliases
from katapult.log import basic_config

speaker_calls = speaker_aliases()

def speaker_list_string():
    return ' | '.join(sorted(speaker_calls.keys()))

def run(speaker_name, speak_count, options):
    speaker_call = speaker_calls.get(speaker_name, None)
    if not speaker_call:
        sys.stderr.write("ERROR - speaker '%s' not found (available: %s)\n" % (speaker_name, speaker_list_string()))
        sys.exit(2)

    speaker = speaker_call()

    for i, row in enumerate(csv.reader(sys.stdin)):
        msg = row[1]
        speaker.ingest(msg)

    print "ingested %d lines of input" % (i+1)
    
    speaker.compile()
    print speaker.describe()

    sizes = [i * 10 for i in range(12,15)]

    successes = 0
    for i in range(speak_count):
        max_size = random.choice(sizes)
        min_size = int(max_size * 0.5)
        # min_size = 1
        size_str = "(%d/%d)" % (min_size, max_size)
        try:
            text = speaker.speak(min_size, max_size)
            print "+ %s [%d] %s" % (size_str, len(text), text)
            successes += 1
        except Exception, e:
            # traceback.print_exc()
            print "! %s %s: %s" % (size_str, e.__class__.__name__, e)
        
    print "%d/%d successes (%.1f%%)" % (successes, speak_count, float(successes)/speak_count * 100)
    

op = OptionParser()
op.add_option("-v", "--verbose", dest="verbose", default=False, action="store_true", help="verbose logging")

options, args = op.parse_args()
basic_config()
if not options.verbose:
    logging.getLogger().setLevel(logging.INFO)    

if len(args) != 2:
    sys.stderr.write('ERROR - expected <speaker> [count] (%s)\n' % speaker_list_string())
    sys.exit(1)

name, count = args

run(name, int(count), options)