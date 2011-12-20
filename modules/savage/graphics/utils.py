from re import match


# Only because we cannot use setattr with the object class
class blank (object):
    pass


class ViewBox:
    def __init__ (self, minX, minY, maxX, maxY):
        self.x = minX
        self.y = minY
        self.width = maxX - minX
        self.height = maxY - minY
    
    def __str__ (self):
        values = map (str, [self.x, self.y, self.width, self.height])
        return ' '.join (values)


class Translate:
    def __init__ (self, x, y):
        self.x = x
        self.y = y
        
    def __str__ (self):
        return 'translate(' + str(self.x) + ',' + str(self.y) + ')'


class Rotate:
    def __init__ (self, angle, x = None, y = None):
        self.angle = angle
        self.x = x
        self.y = y
        
    def __str__ (self):
        output = 'rotate(' + str (self.angle)
        if not ((self.x is None) or (self.y is None)):
            output += ',' + str(self.x) + ',' + str(self.y)
        output += ')'
        return output


def attributesToSVG (dictionary):
    output = []
    for key, value in dictionary.iteritems ():
        if not value is None:
            attr = key + '="' + str (value) + '"'
            output.append (attr)
    return ' '.join (output)

def addAttr (ob, name, cast, default):
    if hasattr (ob, name):
        val = getattr (ob, name)
        setattr (ob, name, cast (val))
    else:
        setattr (ob, name, default)

def boolean (val):
    if isinstance (val, str):
        lower = val.lower ()
        if lower == 'false':
            return False
        elif lower == 'f':
            return False
        elif lower == 'true':
            return True
        elif lower == 't':
            return True
    elif isinstance (val, int):
        if val == 0:
            return False
        elif val == 1:
            return True
    elif isinstance (val, float):
        if val == 0.0:
            return False
        elif val == 1.0:
            return True
    else:
        if val is None:
            return False
    raise RuntimeError ('Cast to boolean failed: Could not convert ' +
                        str (val) + ' to a boolean')

def parseParam (val):
    val = str (val)
    lower = val.lower ()
    if lower == 'none' or lower == 'null' or lower == '':
        return None
    elif lower == 'true':
        return True
    elif lower == 'false':
        return False
    elif not match ('^(-?)(\d+)$', val) is None:
        return int (val)
    elif not match ('^(-?)(\d*)\.(\d*)(e-?\d+)?$', val) is None:
        return float (val)
    else:
        return str (val)

    
