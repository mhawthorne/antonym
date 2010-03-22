from unittest import main, TestCase

import mox

from antonym.model import ArtifactContent, ArtifactInfo, ArtifactSource
from antonym.web.cron import CronTwitterMixHandler
from antonym.web.tweeter import TwitterConnector

from katapult.mocks import MockEntity, MockKey, MockQuery


class CronTwitterMixHandlerTest(TestCase):    

    def test_get(self):
        pass
        
        # mocker = mox.Mox()
        # mocker.StubOutWithMock(ArtifactSource, "all", use_mock_anything=True)
        # mocker.StubOutWithMock(ArtifactInfo, "all", use_mock_anything=True)
        # mocker.StubOutWithMock(ArtifactContent, "find_by_guid", use_mock_anything=True)
        # mocker.StubOutWithMock(TwitterConnector, "new_api", use_mock_anything=True)
        # 
        # # source is selected from random
        # ArtifactSource.all().AndReturn(MockQuery(range(5)))
        # 
        # # artifacts for source are selected
        # keys = [i for i in range(10)]
        # ArtifactInfo.all().AndReturn(MockQuery(keys))
        # 
        # # content is selected by key name
        # for k in keys:
        #     ArtifactContent.find_by_guid(str(k)).AndReturn(MockEntity(MockKey(k)))
        # 
        # mocker.ReplayAll()
        # CronTwitterMixHandler().get()
        # mocker.VerifyAll()


if __name__ == "__main__":
    main()