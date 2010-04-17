from django.conf.urls.defaults import *


urlpatterns = patterns('',
    (r"^speak/?$", "antonym_dj.root.views.speak"),
    (r"^search/?$", "antonym_dj.root.views.search")
)
