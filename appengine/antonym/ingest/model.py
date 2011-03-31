from datetime import datetime
import logging

from google.appengine.api import users

from antonym.accessors import ArtifactAccessor, UrlResourceAccessor
from antonym.ingest import feeds


def ingest_feed_entries(feed, user, error_call=None):
    """
    yields:
        (artifact guid, entry) tuple
    """
    # TODO: use etag from previous ingest
    for entry in feeds.generate_feed_entries(feed.url):
        try:
            stripped_content = entry.get("stripped_content")
            if stripped_content:
                # ensures this is a non-empty entry
                link = entry.get("link")
                raw_modified = entry.get("modified")
                if raw_modified:
                    modified = datetime(*raw_modified[0:-2])
                else:
                    modified = None
                logging.debug("%s modified %s (%s)" % (link, modified, modified.__class__))
                url_resource = UrlResourceAccessor.get_or_create(link,
                    source_modified=modified,
                    feed=feed)
            
                # TODO: check if there is already an artifact for this resource
                info_key, content_key, source_key, created = ArtifactAccessor.find_or_create(source=feed.artifact_source.name,
                    content_type="text/plain",
                    body=stripped_content,
                    url = link,
                    url_resource=url_resource,
                    modified_by=user)
                
                yield info_key.name(), entry, created
        except Exception, e:
            if error_call:
                error_call(entry, e)
            else:
                raise e
                
    # update etag and modified time of feed