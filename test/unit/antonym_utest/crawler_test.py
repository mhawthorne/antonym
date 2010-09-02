import unittest

from antonym.crawler import Crawler


class CrawlerTest(unittest.TestCase):
    
    def _test(self):
        urls = [u for u in Crawler.crawl("http://en.wikipedia.org/wiki/Timothy_Leary", limit=100)]
        print '\n'.join(sorted(urls))


if __name__ == '__main__':
    unittest.main()