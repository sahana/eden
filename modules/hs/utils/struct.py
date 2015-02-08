class Matrix (object):
    def __init__ (self, rows, cols, array=None):
        super (Matrix, self).__init__ ()
        length = rows * cols
        self.rows = rows
        self.cols = cols
        if array:
            if length != len (array):
                raise RuntimeError ("Bad Dimensions")
            self.array = array
        else:
            self.array = []
            for i in range (length):
                self.array.append (0)
            diag = min (rows, cols)
            for i in range (diag):
                self.set (1.0, i, i)

    def index (self, i, j):
        element = (i * self.cols) + j
        if element >= len (self.array):
            raise RuntimeError ('Out of Bounds')
        return element

    def get (self, i, j):
        return self.array [self.index (i, j)]

    def set (self, entry, i, j):
        self.array [self.index (i, j)] = entry

    """def __getattr__ (self, key):
        if key == 'x':
            return self.get (0, 0)
        elif key == 'y':
            return self.get (1, 0)
        else:
            raise AttributeError ('No such attribute')"""

    def __setattr__ (self, key, value):
        if key == 'x':
            self.set (value, 0, 0)
        elif key == 'y':
            self.set (value, 1, 0)
        else:
            super (Matrix, self).__setattr__ (key, value)

    def __str__ (self):
        output = []
        for i in range (self.rows):
            out = []
            for j in range (self.cols):
                out.append (str (self.get (i, j)))
            output.append ('    '.join (out))
        return '\n'.join (output)

    def __neg__ (self):
        negative = []
        for element in self.array:
            negative.append (-element)
        return Matrix (self.rows, self.cols, negative)

    def __isub__ (self, ob):
        #ob = -ob
        self.array = (self + (-ob)).array
        return self

    def __sub__ (self, ob):
        return (self + (-ob))

    def __iadd__ (self, ob):
        if isinstance (ob, Matrix):
            summation = self.matrixAddition (ob)
        else:
            summation =  self.scalarAddition (ob)
        self.array = summation
        return self

    def __add__ (self, ob):
        if isinstance (ob, Matrix):
            summation = self.matrixAddition (ob)
        else:
            summation = self.scalarAddition (ob)
        return Matrix (self.rows, self.cols, summation)

    def matrixAddition (self, matrix):
        if self.rows != matrix.rows or self.cols != matrix.cols:
            raise RuntimeError ('Mismatched Dimensions')
        summation = []
        for a, b in zip (self.array, matrix.array):
            summation.append (a + b)
        return summation

    def scalarAddition (self, scalar):
        summation = []
        for element in self.array:
            summation.append (element * scalar)
        return summation

    def __imul__ (self, ob):
        raise RuntimeError ('Unsafe Operation')

    def __mul__ (self, ob):
        if isinstance (ob, Matrix):
            return self.matrixMultiplication (ob)
        else:
            return self.scalarMultiplication (ob)

    def matrixMultiplication (self, matrix):
        if self.cols != matrix.rows:
            raise RuntimeError ("Mismatched Dimensions")
        product = Matrix (self.rows, matrix.cols)
        for i in range (self.rows):
            for j in range (matrix.cols):
                total = 0
                for k in range (self.cols):
                    total += self.get (i, k) * matrix.get (k, j)
                product.set (total, i, j)
        return product

    def scalarMultiplication (self, scalar):
        product = []
        for element in self.array:
            product.append (element * scalar)
        return Matrix (self.rows, self.cols, product)

    def vector (self):
        if self.rows != 1:
            raise RuntimeError ('Cannot be cast to vector: Bad row dim')
        if self.cols != 3:
            raise RuntimeError ('Cannot be cast to vector: Bad col dim')
        x = self.get (0, 0)
        y = self.get (1, 0)
        w = self.get (2, 0)
        v = Vector (x, y)
        if w != 0:
            v.x /= w
            v.y /= w
        return v


def identity (rows):
    sqr = pow (rows, 2)
    ### Temp
    ### Should default to all 0s later
    array = []
    for i in range (sqr):
        array.append (0)
    ### End Temp
    m = Matrix (rows, rows, array)
    for i in range (rows):
        m.set (1, i, i)
    return m

class Vector:
    def __init__ (self, x, y):
        self.x = x
        self.y = y

    def matrix (self):
        return Matrix (3, 1, [self.x, self.y, 1.0])

    def __add__ (self, v):
        return Vector (self.x + v.x, self.y + v.y)

    def __iadd__ (self, v):
        self.x += v.x
        self.y += v.y
        return self

    def __sub__ (self, v):
        return Vector (self.x - v.x, self.y - v.y)

    def __mul__ (self, scalar):
        return Vector (self.x * scalar, self.y * scalar)

    def __imul__ (self, scalar):
        self.x *= scalar
        self.y *= scalar

    def __str__ (self):
        return str(self.x) + ' ' + str(self.y)

    def matrix (self, dir = False):
        if dir:
            dir = 0
        else:
            dir = 1
        return Matrix (3, 1, [self.x, self.y, dir])

"""class VStruct:
    def __init__ (self, x, y):
        self.x = x
        self.y = y"""
        

#class Vector2D (Matrix):
#    def __init__ (self, x, y):
#        super (Vector2D, self).__init__ (3, 1, [x, y, 1])
#
#    def __getattr__ (self, key):
#        if key == 'x':
#            return self.get (0, 0)
#        elif key == 'y':
#            return self.get (1, 0)
#        else:
#            raise AttributeError ('No such attribute')

"""class Vector:
    def __init__ (self, x, y):
        self.x = x
        self.y = y

    def matrix (self):
        return Matrix (3, 1, [self.x, self.y, 1.0])

    def __add__ (self, v):
        return Vector (self.x + v.x, self.y + v.y)

    def __iadd__ (self, v):
        self.x += v.x
        self.y += v.y
        return self

    def __sub__ (self, v):
        return Vector (self.x - v.x, self.y - v.y)

    def __mul__ (self, scalar):
        return Vector (self.x * scalar, self.y * scalar)

    def __imul__ (self, scalar):
        self.x *= scalar
        self.y *= scalar

    def __str__ (self):
        return str(self.x) + ' ' + str(self.y)"""
