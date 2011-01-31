from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from katapult.requests import RequestHelper

from antonym.model import TwitterResponse
from antonym.web.services import require_service_user


class ResponsesHandler(webapp.RequestHandler):
  
    @require_service_user()
    def get(self):
        helper = RequestHelper(self)
        count = int(self.request.get("count", 10))
        start_idx = int(self.request.get("start", 1))
        
        q = TwitterResponse.find_latest()
        q_results = q.fetch(count, start_idx) if start_idx > 1 else q.fetch(count)
        
        processed_results = []
        for r in q_results:
            r_hash = {"type": r.tweet_type, 
                "timestamp": r.timestamp.isoformat(),
                "message-id": r.message_id,
                "response-id": r.response_id,
                "user": r.user}
            processed_results.append(r_hash)
        helper.write_json(processed_results)
