import logging
from unittest import main, TestCase

from google.appengine.api import users
from google.appengine.api.users import User

import mox

from katapult.mocks import Mock

from antonym.mixer import Mixer
from antonym.web.mixtures import MixtureHandler, MixtureResponseHandler
from antonym.web.services import Services

from antonym_utest.web import new_mock_request_response


def mixer_stub(moxer):
    mixer_mock = moxer.CreateMock(Mixer)

    # moxer.StubOutWithMock(Mixer, '__init__')
    # Mixer.__init__(mox.IgnoreArg())
    
    moxer.StubOutWithMock(Mixer, '__new__')
    Mixer.__new__(Mixer, mox.IgnoreArg()).AndReturn(mixer_mock)
    
    return mixer_mock


class MixtureHandlerTest(TestCase):
    
    def test_get_single_source(self):
        moxer, handler, mixer = self.__init()
        
        source_name = "mhawthorne"
        mixer.mix_sources(source_name).AndReturn(((Mock(name="source1"),), "hello"))
        
        moxer.ReplayAll()
        handler.get(source_name)
        moxer.VerifyAll()

    def test_get_multiple_sources(self):
        moxer, handler, mixer = self.__init()
        
        source_name = "mhawthorne;mmattozzi"
        source_names = source_name.split(";")
        mixer.mix_sources(*source_names).AndReturn(((Mock(name="source1"),), "hello"))
        
        moxer.ReplayAll()
        handler.get(source_name)
        moxer.VerifyAll()
        
    def test_get_no_source(self):
        moxer, handler, mixer = self.__init()
        mixer.mix_random_limit_sources(2, degrade=True).AndReturn(((Mock(name="source1"),), "hello"))
        
        moxer.ReplayAll()
        handler.get(None)
        moxer.VerifyAll()

    def test_get_q(self):
        moxer = mox.Mox()
        
        request, response = new_mock_request_response(moxer)
        handler = MixtureResponseHandler()
        handler.initialize(request, response)
        
        message = "hello"
        request.get("q", None).AndReturn(message)
        mixer = mixer_stub(moxer)
        mixer.mix_response(message).AndReturn(((Mock(name="source1")), "all your base are belong to us"))
        
        moxer.ReplayAll()
        handler.get()
        moxer.VerifyAll()

    def __init(self):
        moxer = mox.Mox()
        
        # moxer.StubOutWithMock(users, "get_current_user")
        
        request, response = new_mock_request_response(moxer)
        
        handler = MixtureHandler()
        handler.initialize(request, response)
        # username = Services.API_USER
        # users.get_current_user().AndReturn(Mock(email=lambda: username))
        
        # defaults to no query and speaker
        request.get("s", None).AndReturn(None)
        request.get("q", None).AndReturn(None)
        
        return moxer, handler, mixer_stub(moxer)


class _MixtureResponseHandlerTest(TestCase):
    
    def test_get_no_q(self):
        moxer = mox.Mox()
        
        request, response = new_mock_request_response(moxer)
        handler = MixtureResponseHandler()
        handler.initialize(request, response)
        
        request.get("q", None).AndReturn(None)
        response.set_status(400)
        response.clear()
        
        moxer.ReplayAll()
        handler.get()
        moxer.VerifyAll()

    def test_get(self):
        moxer = mox.Mox()
        
        request, response = new_mock_request_response(moxer)
        handler = MixtureResponseHandler()
        handler.initialize(request, response)
        
        message = "hello"
        request.get("q", None).AndReturn(message)
        mixer = mixer_stub(moxer)
        mixer.mix_response(message).AndReturn(((Mock(name="source1")), "all your base are belong to us"))
        
        moxer.ReplayAll()
        handler.get()
        moxer.VerifyAll()


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main()