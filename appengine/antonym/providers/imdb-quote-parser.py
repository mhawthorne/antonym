#!/usr/bin/env python

import csv
import re
import sys

from BeautifulSoup import BeautifulSoup
from httplib2 import Http

# fight club
# http://www.imdb.com/title/tt0137523/quotes

# american psycho
# http://www.imdb.com/title/tt0144084/quotes


def iterate_quotes(url, names=()):
    """
    params:
        names - list of names to include in results

    yields:
        (name, quote) tuples
    """
    response, content = Http().request(url, "GET")
    status = response.status
    if status != 200:
        raise Exception("unexpected response: %d" % status)
        
    soup = BeautifulSoup(content)
    
    extras_regex = re.compile("^:\s+|\s+$", re.U | re.M)
    
    kw = {"class": "sodatext" }
    q_divs = soup.findAll("div", **kw)
    for q_div in q_divs:
        # print q_div
        a_tags = q_div.findAll("a")
        a = a_tags[0]
        quote_tag = a.parent.nextSibling
        # need a way to detect a quote_tag with child tags
        if quote_tag:
            # print unicode(quote_tag)
            name = extras_regex.sub("", a.string).replace(" ", ".").lower()
            quote = extras_regex.sub("", unicode(quote_tag))
            yield (name, quote)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.stderr.write("ERROR - expected <url>\n")
        sys.exit(1)
    
    url = sys.argv.pop(1)
    writer = csv.writer(sys.stdout)
    for q in iterate_quotes(url):
        name, quote = q
        # hack to avoid quotes with italics and other html
        if len(quote) > 5:
            writer.writerow(q)