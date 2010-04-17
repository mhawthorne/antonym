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
                modified = datetime(*entry.get("modified")[0:-2])
                logging.debug("%s modified %s (%s)" % (link, modified, modified.__class__))
                url_resource = UrlResourceAccessor.get_or_create(link,
                    source_modified=modified)
            
                # TODO: check if there is already an artifact for this resource
                info_key, content_key, source_key = ArtifactAccessor.create(source=feed.artifact_source.name,
                    content_type="text/plain",
                    body=stripped_content,
                    url_resource=url_resource,
                    modified_by=user)
                
                yield info_key.name(), entry
        except Exception, e:
            if error_call:
                error_call(entry, e)
            else:
                raise e