import logging
import urllib

from django.http import HttpResponse, HttpResponseNotFound, HttpResponsePermanentRedirect
from django.template import Context, loader

from antonym.accessors import ArtifactAccessor
from antonym.mixer import Mixer


def speak(request):
    t = loader.get_template("speak.html")
    q = request.REQUEST.get("q", None)
    if q:
        sources, content = Mixer.mix_after_search(urllib.unquote(q))
    else:
        sources, content = Mixer.mix_random()
        
    logging.debug("content: %s" % content)
    c = Context(dict(sources=sources, content=content))
    return HttpResponse(t.render(c))

def search(request):
    t = loader.get_template("search.html")
    q = request.REQUEST.get("q", None)
    contents = None
    if not q:
        msg = "no query provided"
    else:
        q = urllib.unquote(q)
        contents = ArtifactAccessor.search(q)
        msg = "%d results found for query '%s'" % (len(contents), q)
    c = Context(dict(msg=msg, contents=contents))
    return HttpResponse(t.render(c))
    