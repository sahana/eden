def hex_to_color (hex):
    hex = str (hex)
    if hex.startswith ('0x'):
        hex = hex[2:]
    if len (hex) != 6:
        raise RuntimeError (hex + ' is not a hex color')
    red = int ('0x' + hex[0:2], 0)
    green = int ('0x' + hex[2:4], 0)
    blue = int ('0x' + hex[4:6], 0)
    return Color (*map (clampInt, [red, green, blue]))


def clampInt (value):
    value = int (value)
    if value > 255:
        return 255
    elif value < 0:
        return 0
    else:
        return value

def clampFloat (value):
    value = float (value)
    if value > 1.0:
        return 1.0
    elif value < 0.0:
        return 0.0
    else:
        return value

class Color:
    def __init__ (self, red, green, blue):
        self.red = float (red)
        self.green = float (green)
        self.blue = float (blue)
        
    def interpolate (self, c, percent):
        percent = float (percent)
        if percent > 1.0 or percent < 0.0:
            raise RuntimeError ('Cannot interpolate color: perecent out of range')
        return ((c * percent) + (self * (1.0 - percent)))

    def __add__ (self, c):
        r = self.red + c.red
        g = self.green + c.green
        b = self.blue + c.blue
        return Color (r, g, b)

    def __mul__ (self, scalar):
        r = self.red * scalar
        g = self.green * scalar
        b = self.blue * scalar
        return Color (r, g, b)

    def __str__ (self):
        rgb = 'rgb('
        rgb += str(int(self.red))+ ',' 
        rgb += str(int(self.green))+ ',' 
        rgb += str(int(self.blue))+ ')' 
        return rgb

red = Color (255, 0, 0)
green = Color (0, 255, 0)
blue = Color (0, 0, 255)
black = Color (0, 0, 0)
white = Color (255, 255, 255)
