import unittest

from antonym.crawler import Crawler


class CrawlerTest(unittest.TestCase):
    
    def test(self):
        urls = [u for u in Crawler.crawl("http://en.wikipedia.org/", limit=50)]
        print '\n'.join(sorted(urls))
        
if __name__ == '__main__':
    unittest.main()