import re
from StringIO import StringIO

import httplib2
import feedparser
import scrape

from katapult.core import Strings
from katapult.log import LoggerFactory
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
    return self.__values[key]
  
  def set(self, **kw):
    for k, v in kw.iteritems():
      self.__values[k] = v
      setattr(self, k, v)

  def as_dict(self):
      self.__values()
      
  def __repr__(self):
    return "%s%s" % (self.__class__.__name__, repr(self.__values))


def generate_feed_entries(url, **kw):
    """
    generator; yields feed entries

    keywords:
        max - max number of entries to return
    returns:
        list of FeedEntry instances
    """
    logger = LoggerFactory.logger(__name__)
    max_entries = kw.get("max", None)

    # response, content = httplib2.Http().request(url)
    # if response.status != 200:
    #     raise FeedException("%d for %s" % (response.status, url))
    # logger.debug("url:%s, response:%s" % (url, response))
    # logger.debug("content: (%d) %s" % (len(content), content))
    doc = feedparser.parse(url)
    # logger.debug("doc:%s" % doc)
    
    count = 0
    for e in doc.entries:
        title = e.title
        logger.debug("processing entry '%s'" % title)
        entry = FeedEntry(title=e.title,
        etag=doc.etag,
        link=e.link)

        # TODO: handle modified=None
        entry.set(modified=doc.modified)

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
_space_regex = re.compile(r'(</?br\s*/?>)+')

def iterate_tags(html):
  for match in _tag_regex.finditer(html):
    yield match.group(0)
  
def strip_html(html):
  html = _space_regex.sub(' ', html)
  return _tag_regex.sub('', html)