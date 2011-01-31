#!/usr/bin/env python

from itertools import izip_longest
import re
import sys

char_regex = re.compile("\S")

newline_first_char_idx = 7

def first_char_idx(line):
    first_char_idx = -1
    for char_idx, char in enumerate(line):
        if char_regex.match(char):
            first_char_idx = char_idx
            break
    return first_char_idx
    
def write(msg):
    sys.stdout.write(msg)
    # sys.stdout.flush()

line_buffer = []
for line in sys.stdin:
    # print "'%s'\n'%s'" % (line1, line2)
    if first_char_idx(line) == newline_first_char_idx:
        if line_buffer:
            # there's a previous line buffer to output.  print it and clear it.
            sentence = "%s\n" % " ".join(line_buffer)
            write(sentence)
            del line_buffer[0:]
        line_buffer.append(line.strip())
    else:
        line_buffer.append(line.strip())
            
    
            
        
    