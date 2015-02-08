class Dictionary (dict):
    def __init__ (self):
        self._keys = []
        #self._sorted = True
        dict.__init__(self)

    def keys (self):
        return self._keys
    
    def update (self, pairs):
        try:
            for key, value in pairs.iteritems ():
                if not self.has_key (key):
                    self._keys.append (key)
        except AttributeError:
            for pair in pairs:
                if not self.has_key (pair[0]):
                    self._keys.append (pair[0])                   
        #for key in pairs:
        #    print key
        #    try:
        #        self[key]
        #    except KeyError:
        #        self._keys.append (key)
        #self._sorted = False
        dict.update (self, pairs)

    def __iter__ (self):
        return DictIterator (self, iter(self._keys))


class DictIterator:
    def __init__ (self, dictionary, listIter):
        self._dictionary = dictionary
        self._listIter = listIter
        
    def __iter__ (self):
        return self

    def next (self):
        key = self._listIter.next ()
        return (key, self._dictionary[key])


class DefaultDictionary (Dictionary):
    def __init__ (self, default):
        self.default = default
        Dictionary.__init__ (self)

    def __getitem__ (self, item):
        try:
            return dict.__getitem__ (self, item)
        except KeyError:
            if not self.default is None:
                return self.default
            else:
                raise KeyError ()
