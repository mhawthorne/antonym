from unittest import main, TestCase

from mox import Mox
from twitter import Api

from antonym.ttwitter import ReadOnlyTwitterApi


class ReadOnlyTwitterApiTest(TestCase):
    
    def test_get_friends(self):
        m = Mox()
        
        api = m.CreateMock(Api)
        ro_api = ReadOnlyTwitterApi(api)
        
        api.GetFriends()
        
        m.ReplayAll()
        ro_api.GetFriends()
        m.VerifyAll()


if __name__ == "__main__":
    main()