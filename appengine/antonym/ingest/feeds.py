import logging
import re
from StringIO import StringIO

import httplib2
import feedparser

from katapult.xml import unescape

from antonym.core import AppException


class FeedException(AppException): pass


class FeedEntry:
  """
  attributes:
    title
    link
    modified
    etag
    raw_content
    stripped_content
  """
    
  def __init__(self, **kw):
    self.__values = {}
    self.set(**kw)
    
  def has(self, key):
    return self.__values.has_key(key)
    
  def get(self, key):
    return self.__values.get(key, None)
  
  def set(self, **kw):
    for k, v in kw.iteritems():
      self.__values[k] = v
      setattr(self, k, v)

  def as_dict(self):
      return self.__values
      
  def __repr__(self):
    return "%s%s" % (self.__class__.__name__, repr(self.__values))


def generate_feed_entries(url, **kw):
    """
    generator; yields feed entries

    keywords:
        max - max number of entries to return
    yields:
        each FeedEntry instance
    """
    logging.debug("generate_feed_entries url:%s" % url)
    max_entries = kw.get("max", None)

    doc = feedparser.parse(url)
    
    count = 0
    for e in doc.entries:
        title = e.title
        logging.debug("generate_feed_entries processing entry '%s'" % title)
        entry = FeedEntry(title=e.title,
            etag=doc.etag,
            link=e.link)

        # TODO: handle modified=None
        if hasattr(e, "modified"):
            entry.set(modified=doc.modified)

        if not hasattr(e, "content"):
            logging.debug("no content found")
            continue

        raw_content = e.content[0]['value']
        
        # unescapes entities
        raw_content = unescape(raw_content)
        
        stripped_content = unicode(strip_html(raw_content))
        entry.set(raw_content=raw_content)
        entry.set(stripped_content=stripped_content)

        yield entry

        count += 1
        if max_entries and count == max_entries:
            break


# used to replace html links with only their hrefs
_link_regex = re.compile(r'<a .*href=()/?></a>')

# used to replace all tags
_tag_regex = re.compile(r'</?\w+[^>]*/?>')

# used to replace linebreaks with spaces
_space_regex = re.compile(r'(</?br\s*/?>|\s)+')

def iterate_tags(html):
  for match in _tag_regex.finditer(html):
    yield match.group(0)
  
def strip_html(html):
  html = _space_regex.sub(' ', html)
  return _tag_regex.sub('', html)