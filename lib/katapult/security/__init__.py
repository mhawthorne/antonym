from katapult.requests import RequestHelper


def forbidden():
    """ returns HTTP 403 in all cases """
    def func_call(f):
        def args_call(*args, **kw):
            handler = args[0]
            helper = RequestHelper(handler)
            helper.set_status(403)
        return args_call
    return func_call
