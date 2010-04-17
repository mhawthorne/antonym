from unittest import main, TestCase

import mox

from katapult.log import config as log_config
from katapult.mocks import MockEntity, MockQuery

from antonym.accessors import TwitterResponseAccessor
from antonym.model import ArtifactContent
from antonym.web.tweeter import TwitterActor, TwitterConnector


class TwitterActorTest(TestCase):

    def test_act_no_messages(self):
        moxer = mox.Mox()
        
        moxer.StubOutWithMock(TwitterResponseAccessor, "get_by_message_id", use_mock_anything=True)
        moxer.StubOutWithMock(TwitterConnector, "new_api", use_mock_anything=True)
        moxer.StubOutWithMock(TwitterActor, "_choose_to_act", use_mock_anything=True)
        moxer.StubOutWithMock(ArtifactContent, "all", use_mock_anything=True)
        
        TwitterActor._choose_to_act().AndReturn(TwitterActor.ACT)
        
        api = moxer.CreateMockAnything()
        TwitterConnector.new_api().AndReturn(api)
        
        # no messages
        api.GetDirectMessages().AndReturn([])
        api.GetReplies().AndReturn([])
        
        source = MockEntity(key_name="m", name="mhawthorne")
        content_create_call = lambda c_id: MockEntity(key_name=source.name, source=source, source_name=source.name, body="content for %s" % c_id)
        ArtifactContent.all().AndReturn(MockQuery(xrange(0,10), create_call=content_create_call))
        
        TwitterConnector.new_api().AndReturn(api)
        api.PostUpdate(mox.IsA(str))
        
        moxer.ReplayAll()
        TwitterActor.act()
        moxer.VerifyAll()


if __name__ == '__main__':
    log_config()
    main()