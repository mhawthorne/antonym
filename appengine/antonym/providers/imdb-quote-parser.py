#!/usr/bin/env python

import csv
import htmlentitydefs
import re
import sys

from BeautifulSoup import BeautifulSoup
from httplib2 import Http

# fight club
# http://www.imdb.com/title/tt0137523/quotes

# american psycho
# http://www.imdb.com/title/tt0144084/quotes

# mad men
# http://www.imdb.com/character/ch0031457/quotes

def encode(val):
    return val.encode("utf-8")

# from http://effbot.org/zone/re-sub.htm#unescape-html
#
# Removes HTML or XML character references and entities from a text string.
#
# @param text The HTML (or XML) source text.
# @return The plain text, as a Unicode string, if necessary.
def unescape(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)

extras_regex = re.compile("^:\s+|\s+$", re.U | re.M)
name_replace_regex = re.compile(r"[\s\.]+", re.U)
    
def iterate_quotes_standard(content, names=()):
    """
    params:
        names - list of names to include in results

    yields:
        (name, quote) tuples
    """
    soup = BeautifulSoup(content)
    
    kw = {"class": "sodatext" }
    q_divs = soup.findAll("div", **kw)
    for q_div in q_divs:
        # print "q_div:%s" % q_div
        a_tags = q_div.findAll("a")
        for a in a_tags:
            # a = a_tags[0]
            quote_tag = a.parent.nextSibling
            # print "a:%s\nquote_tag:%s" % (a, quote_tag)
            # need a way to detect a quote_tag with child tags
            if quote_tag:
                # print unicode(quote_tag)
                name = name_replace_regex.sub(".", extras_regex.sub("", a.string)).lower()
                quote = unescape(extras_regex.sub("", unicode(quote_tag)))
                yield (encode(name), encode(quote))

def iterate_quotes_character(content, names=()):
    # print content
    soup = BeautifulSoup(content)
    
    name_regex = re.compile(r"/name/.+")
    
    for a_tag in soup.findAll("a"):
        if name_regex.match(a_tag['href']):
            quote_tag = a_tag.parent.nextSibling
            name = name_replace_regex.sub(".", extras_regex.sub("", a_tag.string)).lower()
            quote = unescape(extras_regex.sub("", unicode(quote_tag)))
            yield (encode(name), encode(quote))


if __name__ == "__main__":
    if len(sys.argv) > 2:
        sys.stderr.write("ERROR - expected <s|c> [source_name_override]\n")
        sys.exit(1)
    
    format = sys.argv.pop(1)
    source_name_override = sys.argv.pop(1) if len(sys.argv) == 2 else None
    writer = csv.writer(sys.stdout)
    if format == "s":
        iterate_quotes = iterate_quotes_standard
    elif format == "c":
        iterate_quotes = iterate_quotes_character 
    else:
        raise Exception("unrecognized format: %s" % format)
        
    for q in iterate_quotes(sys.stdin.read()):
        name, quote = q
        # hack to avoid quotes with italics and other html
        if len(quote) > 5:
            if source_name_override is not None:
                q = (source_name_override, quote)
            writer.writerow(q)