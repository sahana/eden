
_UNDEFINED = object()

class Change(object):
    def __init__(self, target, changes):
        self.changes = changes
        self.target = target
    
    def __enter__(self):
        assert not hasattr(self, "originals")
        self.originals = originals = {}
        # store originals and set new values
        for name, value in self.changes.iteritems():
            originals[name] = getattr(self.target, name, _UNDEFINED)
            setattr(self.target, name, value)
        
    def __exit__(self, type, value, traceback):
        # restore originals
        for name, value in self.originals.iteritems():
            if value is _UNDEFINED:
                delattr(self, name)
            else:
                setattr(self.target, name, value)    
        del self.originals
    
