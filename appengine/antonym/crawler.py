import re

import httplib2
from BeautifulSoup import BeautifulSoup


class Crawler:
    """ web cralwer """
    
    @classmethod
    def crawl(cls, url, **kw):
        """
        generator.  yields urls to crawl.
        """
        limit = kw.get('limit')
        http = httplib2.Http()
        response, content = http.request(url, 'GET')
        soup = BeautifulSoup(content)
        link_tags = soup.findAll('a')
        if link_tags:
            count = 0
            for tag in link_tags:
                if count >= limit:
                    break
                    
                href = tag.get('href')
                
                if not href:
                    continue
                    
                if re.match('^\/.*', href):
                    full_href = '%s%s' % (url, href)
                elif re.match('http:.*', href):
                    full_href = href
                else:
                    continue
                    
                yield full_href
                count += 1