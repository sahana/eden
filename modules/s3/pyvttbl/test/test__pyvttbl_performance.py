from __future__ import print_function

# Copyright (c) 2011, Roger Lew [see LICENSE.txt]
# This software is funded in part by NIH Grant P20 RR016454.

from random import shuffle

from pyvttbl import PyvtTbl
from dictset import _rep_generator

abc=list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')

df = PyvtTbl()
X = {}
shuffle(abc)
df[1] = abc[0]*10000

shuffle(abc)
df[2] = abc[:2]*5000

shuffle(abc)
df[5] = abc[:4]*2500
X[2] = abc[0]

shuffle(abc)
df[3] = abc[:5]*2000

shuffle(abc)
df[4] = abc[:8]*1250
X[4] = abc[:3]

shuffle(abc)
df[6] = abc[:10]*1000

shuffle(abc)
df[7] = abc[:20]*500
X[7] = abc[:5]

for i in range(1,8):
    shuffle(df[i])
    

def test1():
    """does exclusions in sqlite3"""
    
    df._build_tbl(range(1,8), exclude=X)


def test2():
    """does exclusions in python"""
    # uncomment in source to run
    
    df._build_tbl_old(range(1,8), exclude=X)

if __name__=='__main__':
    from timeit import Timer
    t = Timer("test1()", "from __main__ import test1, df, X")
    print('test1',t.timeit(number=10))
    
    t = Timer("test2()", "from __main__ import test2, df, X")
    print('test2',t.timeit(number=10))
