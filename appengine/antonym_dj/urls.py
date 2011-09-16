from django.conf.urls.defaults import *

prefix = "-/"

urlpatterns = patterns('',
    (r"^%sspeak/?(.+)?$" % prefix, "antonym_dj.root.views.speak"),
    (r"^%ssearch$" % prefix, "antonym_dj.root.views.search"),
    (r"^%sshell$" % prefix, "antonym_dj.root.views.shell"),
    (r"^$", "antonym_dj.root.views.shell")
)
