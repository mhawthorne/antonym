from unittest import main, TestCase

from antonym.ingest import feeds


def _default_html():
  html = """<h1>header</h1>
<title>title</title>
<p>hello <a href="a">basic link</a></p>
<p>hello <a href="2_3.html">numbers link</a></p>"""
  return html


class IngestTest(TestCase):
  
  def test_iterate_tags(self):
    tags = [t for t in feeds.iterate_tags(_default_html())]
    self.assertEqual(len(tags), 12)

  def test_strip_html(self):
    expected = """header title hello basic link hello numbers link"""
    stripped = feeds.strip_html(_default_html())
    self.assertEqual(stripped, expected)
    
  def test_generate_feed_entries(self):
    results = [e for e in feeds.generate_feed_entries("http://gilesbowkett.blogspot.com/feeds/posts/default")]
    for e in results:
        raw_content = e.get('raw_content')
        stripped_content = e.get('stripped_content')
        
        # debugging
        # print e.get('title')
        # print 'stripped_content:\n%s' % stripped_content
        # print 'raw_content:\n%s' % raw_content
        # print
        
        self.assert_(e.has('title'), "missing: title")
        self.assert_(e.has('etag'), "missing: etag")
        self.assert_(e.has('modified'), "missing: modified")
        self.assert_(e.has('link'), "missing: link")

        # TODO: verify no HTML in stripped content
        # stripped content can be an empty string
        self.assert_(stripped_content is not None, "missing: stripped_content")
        self.assert_(raw_content, "missing: raw_content")


if __name__ == '__main__':
  main()