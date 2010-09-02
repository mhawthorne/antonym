import logging


def get_class(classname):
    """ returns a class for the specified string """
    parts = classname.split('.')
    module = '.'.join(parts[:-1])
    m = __import__(module)
    for comp in parts[1:]:
        m = getattr(m, comp)            
    return m

def decorate_class(klass, decorator, methods=None):
    """
    decorates methods in a class
    
    params:
        klass
        decorator
        methods
        
    returns:
        None
    """
    for n in dir(klass):
        # skips if not in desired methods
        if methods and (n not in methods):
            continue
        f = getattr(klass, n)
        if hasattr(f, 'im_func'):
            setattr(klass, n, decorator(f.im_func))

def create_decorated_class(klass, decorator, methods=None):
    """
    creates a new class with a decorator around the specified methods
    
    params:
        klass
        decorator
        methods
        
    returns:
        decorated class
    """
    class Decorated(klass): pass
    d_klass = Decorated
    decorate_class(d_klass, decorator, methods)
    return d_klass