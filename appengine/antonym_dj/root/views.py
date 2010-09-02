import logging
import urllib

from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.template import Context, loader

from antonym.accessors import ArtifactAccessor
from antonym.mixer import Mixer
from antonym.web.tweeter import TwitterConnector


def speak(request, raw_sources):
    sources = None
    if raw_sources:
        sources = sources.split(";") if ";" in raw_sources else (raw_sources,)
    
    q = request.REQUEST.get("q", None)
    if q:
        mix_sources, mix_content = Mixer.mix_after_search(urllib.unquote(q))
    else:
        if sources:
            mix_sources, mix_content = Mixer.mix_sources(*sources)
        else:
            mix_sources, mix_content = Mixer.mix_random()
            
    logging.debug("mix_content: %s" % mix_content)
    c = Context(dict(sources=mix_sources, content=mix_content))
    t = loader.get_template("speak.html")
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
    
def shell(request):
    t = loader.get_template("shell.html")
    c = Context()
    return HttpResponse(t.render(c))
