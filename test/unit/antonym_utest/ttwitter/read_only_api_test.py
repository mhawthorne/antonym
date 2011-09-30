from unittest import main, TestCase

from mox import IgnoreArg, Mox
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
        
    def test_get_user(self):
        m = Mox()
        
        api = m.CreateMock(Api)
        ro_api = ReadOnlyTwitterApi(api)
        
        api.GetUser(IgnoreArg())
        
        m.ReplayAll()
        ro_api.GetUser("mhawthorne")
        m.VerifyAll()
        
        
if __name__ == "__main__":
    main()