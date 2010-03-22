def get_class(classname):
    """ returns a class for the specified string """
    parts = classname.split('.')
    module = '.'.join(parts[:-1])
    m = __import__(module)
    for comp in parts[1:]:
        m = getattr(m, comp)            
    return m