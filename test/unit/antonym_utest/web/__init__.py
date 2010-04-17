from StringIO import StringIO


def new_mock_request_response(moxer):
    """
    returns:
        mock (request, response) tuple
    """
    request = moxer.CreateMockAnything()
    
    response = moxer.CreateMockAnything()
    response.headers = {}
    response.out = StringIO()

    return request, response