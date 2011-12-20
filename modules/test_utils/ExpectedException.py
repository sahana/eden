
class ExpectedException(object):
    def __init__(self, ExceptionClass):
        self.ExceptionClass = ExceptionClass
    
    def __enter__(self):
        pass

    def __exit__(self, type, value, traceback):
        return issubclass(type, self.ExceptionClass), (
            "%s not raised" % self.ExceptionClass.__name__
        )

