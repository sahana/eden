from __future__ import print_function

# Copyright (c) 2011, Roger Lew [see LICENSE.txt]
# This software is funded in part by NIH Grant P20 RR016454.

"""
This unittests the pure python aggregate functions
defined in the stat_aggregate_funcs module.
"""

import unittest
import sqlite3 as sqlite
import math
from random import normalvariate
from pprint import pprint as pp

import pylab
from dictset import DictSet
import pystaggrelite3
from pystaggrelite3 import isfloat

class getaggTests(unittest.TestCase):
    def test(self):
        for n,a,f in pystaggrelite3.getaggregators():
            self.assertFalse(n in['isfloat','ignore','Counter'])

class histTests(unittest.TestCase):
    def test(self):

        # build the test data
        V=[]
        for i in range(300):
            V.append(normalvariate(100.,10.))

        # build some weight vectors to test
        W1=[.001 for i in range(300)]
        W2=[1. for i in range(300)]
        W2[0]=10000.
        W3=[-1. for i in range(300)]
        W=[W1, W2, W3, None]

        # factorially examine the conditions in this DictSet
        # see: http://code.google.com/p/dictset/
        ds = DictSet({'bins':[1,2,10,171,500],
                     'range':[(0,100),None],
                   'density':[True, False],
                   'weights':[0, 1, 2, 3],
                'cumulative':[True, False]})
        
        for b,r,d,w,c in ds.unique_combinations(
            ['bins','range','density','weights','cumulative']):
            
            print(b,r,d,w,c)
            DN, DB = pystaggrelite3.hist(V, b, r, d, W[w], c)
            pylab.figure()
            RN, RB, patches = pylab.hist(V, b, r, d, W[w], c)
            pylab.close()

            for d,r in zip(DN, RN):
                self.assertAlmostEqual(d, r)

            for d,r in zip(DB, RB):
                self.assertAlmostEqual(d, r)
                
class aggTests(unittest.TestCase):
    """
    this is a generic class for testing the user defined aggregators
    """
    
    def setUp(self):
        # create an sqlite table
        self.con = sqlite.connect(":memory:")
        cur = self.con.cursor()
        cur.execute("""
            create table test(
                t text,
                i integer,
                f float,
                neg float,
                empty float,
                hasnan float,
                hasinf float,
                modefive float,
                n1 float,
                n2 float,
                ones float,
                zeros float
                )
            """)

        # add data to table
        # data = [ 1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7, 8.8, 9.9, 
        #          10.10, 11.11, 12.12, 13.13, 14.14 ]
        cur.executemany("insert into test(t) values (?)",
                        [('%i.%i'%(i,i),) for i in range(1,15)])
        
        cur.executemany("insert into test(f) values (?)",
                        [('%i.%i'%(i,i),) for i in range(1,15)])
        
        cur.executemany("insert into test(neg) values (?)",
                        [('-%i.%i'%(i,i),) for i in range(1,15)])
        
        cur.executemany("insert into test(hasnan) values (?)",
                        [('%i.%i'%(i,i),) for i in range(1,7)]+\
                        [('NaN',)]+\
                        [('%i.%i'%(i,i),) for i in range(8,15)])
        
        cur.executemany("insert into test(hasinf) values (?)",
                        [('%i.%i'%(i,i),) for i in range(1,7)]+\
                        [('Inf',)]+\
                        [('%i.%i'%(i,i),) for i in range(8,15)])
        
        cur.executemany("insert into test(modefive) values (?)",
                        [('%i'%i,) for i in range(1,6)]+\
                        [('5',)]+\
                        [('%i'%i,) for i in range(5,15)])

        cur.execute("insert into test(n1) values (4)")
         
        cur.execute("insert into test(n2) values (4)")
        cur.execute("insert into test(n2) values (5)")

        cur.executemany("insert into test(ones) values (?)",    
                        [('1',) for i in range(1,10)])

        cur.executemany("insert into test(zeros) values (?)",    
                        [('0',) for i in range(1,10)])
        
        # register user defined aggregate with sqlite3
        self.con.create_aggregate(self.name, 1, self.aggregate)

    def tearDown(self):
        #self.cur.close()
        #self.con.close()
        pass

    def Check_float(self):
        """check how aggregate handles float data"""

        if hasattr(self,'expect_float'):
            cur = self.con.cursor()
            cur.execute("select %s(f) from test"%self.name)
            val = cur.fetchone()[0]
            
            if isfloat(val) and isfloat(self.expect_float):
                self.failUnlessAlmostEqual(val, self.expect_float, 6)
            else:
                self.failUnlessEqual(val, self.expect_float)

    def Check_neg(self):
        """check how aggregate handles negative float data"""

        if hasattr(self,'expect_neg'):
            cur = self.con.cursor()
            cur.execute("select %s(neg) from test"%self.name)
            val = cur.fetchone()[0]
            
            if isfloat(val) and isfloat(self.expect_neg):
                self.failUnlessAlmostEqual(val, self.expect_neg, 6)
            else:
                self.failUnlessEqual(val, self.expect_neg)
            
    def Check_text(self):
        """check how aggregate handles text data"""

        if hasattr(self,'expect_text'):
            cur = self.con.cursor()
            cur.execute("select %s(t) from test"%self.name)
            val = cur.fetchone()[0]
            
            if isfloat(val) and isfloat(self.expect_text):
                self.failUnlessAlmostEqual(val, self.expect_text, 6)
            else:
                self.failUnlessEqual(val, self.expect_text)
        
    def Check_empty(self):
        """check how aggregate handles an empty list"""

        if hasattr(self,'expect_empty'):
            cur = self.con.cursor()
            cur.execute("select %s(empty) from test"%self.name)
            val = cur.fetchone()[0]
            
            if isfloat(val) and isfloat(self.expect_empty):
                self.failUnlessAlmostEqual(val, self.expect_empty, 6)
            else:
                self.failUnlessEqual(val, self.expect_empty)

    def Check_nan(self):
        """check how aggregate handles float data containing nan values"""

        if hasattr(self,'expect_nan'):
            cur = self.con.cursor()
            cur.execute("select %s(hasnan) from test"%self.name)
            val = cur.fetchone()[0]
            
            if isfloat(val) and isfloat(self.expect_nan):
                self.failUnlessAlmostEqual(val, self.expect_nan, 6)
            else:
                self.failUnlessEqual(val, self.expect_nan)

    def Check_inf(self):
        """check how aggregate handles float data containing inf values"""
        
        if hasattr(self,'expect_inf'):
            cur = self.con.cursor()
            cur.execute("select %s(hasinf) from test"%self.name)
            val = cur.fetchone()[0]
            
            if isfloat(val) and isfloat(self.expect_inf):
                self.failUnlessAlmostEqual(val, self.expect_inf, 6)
            else:
                self.failUnlessEqual(val, self.expect_inf)

    def Check_modefive(self):
        """special func to check mode aggregate"""

        if hasattr(self,'expect_modefive'):
            cur = self.con.cursor()
            cur.execute("select %s(modefive) from test"%self.name)
            val = cur.fetchone()[0]
            
            if isfloat(val) and isfloat(self.expect_modefive):
                self.failUnlessAlmostEqual(val, self.expect_modefive, 6)
            else:
                self.failUnlessEqual(val, self.expect_modefive)

    def Check_n1(self):
        """special func to check an array of 1"""

        if hasattr(self,'expect_n1'):
            cur = self.con.cursor()
            cur.execute("select %s(n1) from test"%self.name)
            val = cur.fetchone()[0]
            
            if isfloat(val) and isfloat(self.expect_n1):
                self.failUnlessAlmostEqual(val, self.expect_n1, 6)
            else:
                self.failUnlessEqual(val, self.expect_n1)

    def Check_n2(self):
        """special func to check an array of 2"""

        if hasattr(self,'expect_n2'):
            cur = self.con.cursor()
            cur.execute("select %s(n2) from test"%self.name)
            val = cur.fetchone()[0]
            
            if isfloat(val) and isfloat(self.expect_n2):
                self.failUnlessAlmostEqual(val, self.expect_n2, 6)
            else:
                self.failUnlessEqual(val, self.expect_n2)

    def Check_ones(self):
        """special func to check when array is all ones"""

        if hasattr(self,'expect_ones'):
            cur = self.con.cursor()
            cur.execute("select %s(ones) from test"%self.name)
            val = cur.fetchone()[0]
            
            if isfloat(val) and isfloat(self.expect_ones):
                self.failUnlessAlmostEqual(val, self.expect_ones, 6)
            else:
                self.failUnlessEqual(val, self.expect_ones)

    def Check_zeros(self):
        """special func to check when array is all ones"""

        if hasattr(self,'expect_zeros'):
            cur = self.con.cursor()
            cur.execute("select %s(zeros) from test"%self.name)
            val = cur.fetchone()[0]
            
            if isfloat(val) and isfloat(self.expect_ones):
                self.failUnlessAlmostEqual(val, self.expect_zeros, 6)
            else:
                self.failUnlessEqual(val, self.expect_zeros)
                
# Here a test class is defined for each aggregator as a metaclass

hasnanTests=\
    type('hasnanTests',(aggTests,),
                 { 'name':'kurt',
                   'aggregate':pystaggrelite3.hasnan,
                   'expect_float':False,
                   'expect_neg':False,
                   'expect_text':False,
                   'expect_empty':False,
                   'expect_nan':True,
                   'expect_inf':False,
                   'expect_ones':False,
                   'expect_zeros':False
                 }
                )

hasinfTests=\
    type('hasinfTests',(aggTests,),
                 { 'name':'kurt',
                   'aggregate':pystaggrelite3.hasinf,
                   'expect_float':False,
                   'expect_neg':False,
                   'expect_text':False,
                   'expect_empty':False,
                   'expect_nan':False,
                   'expect_inf':True,
                   'expect_ones':False,
                   'expect_zeros':False
                 }
                )

arbitraryTests=\
    type('arbitraryTests',(aggTests,),
                 { 'name':'arbitrary',
                   'aggregate':pystaggrelite3.arbitrary,
                   'expect_float':1.1,
                   'expect_neg':-1.1,
                   'expect_text':'1.1',
                   'expect_empty':None,
                   'expect_nan':1.1,
                   'expect_inf':1.1,
                   'expect_ones':1.,
                   'expect_zeros':0
                  }
                 )

datarangeTests=\
    type('datarangeTests',(aggTests,),
                 { 'name':'datarange',
                   'aggregate':pystaggrelite3.datarange,
                   'expect_float':13.040000000000001,
                   'expect_neg':13.040000000000001,
                   'expect_text':13.040000000000001,
                   'expect_empty':None,
                   'expect_nan':13.040000000000001,
                   'expect_inf':float('inf'),
                   'expect_ones':0.,
                   'expect_zeros':0.
                 }
                )

abs_meanTests=\
    type('abs_meanTests',(aggTests,),
                 { 'name':'abs_mean',
                   'aggregate':pystaggrelite3.abs_mean,
                   'expect_float':7.864285714285715,
                   'expect_neg':7.864285714285715,
                   'expect_text':7.864285714285715,
                   'expect_empty':None,
                   'expect_nan':7.876923076923077,
                   'expect_inf':float('inf'),
                   'expect_ones':1.,
                   'expect_zeros':0.
                 }
                )

geometric_meanTests=\
    type('geometric_meanTests',(aggTests,),
                 { 'name':'geometric_mean',
                   'aggregate':pystaggrelite3.geometric_mean,
                   'expect_float':6.450756824711689,
                   'expect_neg':None,
                   'expect_text':6.450756824711689,
                   'expect_empty':None,
                   'expect_nan':6.363511307721573,
                   'expect_inf':float('inf'),
                   'expect_ones':1.,
                   'expect_zeros':0.
                 }
                )

medianTests=\
    type('medianTests',(aggTests,),
                 { 'name':'median',
                   'aggregate':pystaggrelite3.median,
                   'expect_float':8.25,
                   'expect_neg':-8.25,
                   'expect_text':8.25,
                   'expect_empty':None,
                   'expect_nan':8.8,
                   'expect_inf':9.350000000000001,
                   'expect_modefive':6.5,
                   'expect_ones':1.,
                   'expect_zeros':0.
                 }
                )

modeTests=\
    type('modeTests',(aggTests,),
                 { 'name':'mode',
                   'aggregate':pystaggrelite3.mode,
                   'expect_empty':None,
                   'expect_modefive':5.0,
                   'expect_ones':1.,
                   'expect_zeros':0.
                 }
                )

varpTests=\
    type('varpTests',(aggTests,),
                 { 'name':'varp',
                   'aggregate':pystaggrelite3.varp,
                   'expect_float':15.976081632653049,
                   'expect_neg':15.976081632653049,
                   'expect_text':15.976081632653049,
                   'expect_empty':None,
                   'expect_nan':17.20277514792899 ,
                   'expect_inf':None,
                   'expect_n1':0.,
                   'expect_n2':0.25,
                   'expect_ones':0.,
                   'expect_zeros':0.
                 }
                )

varTests=\
    type('varTests',(aggTests,),
                 { 'name':'var',
                   'aggregate':pystaggrelite3.var,
                   'expect_float':17.205010989010976,
                   'expect_neg':17.205010989010976,
                   'expect_text':17.205010989010976,
                   'expect_empty':None,
                   'expect_nan':18.636339743589737,
                   'expect_inf':None,
                   'expect_n1':None,
                   'expect_n2':0.5,
                   'expect_ones':0.,
                   'expect_zeros':0.
                 }
                )

stdevpTests=\
    type('stdevpTests',(aggTests,),
                 { 'name':'stdevp',
                   'aggregate':pystaggrelite3.stdevp,
                   'expect_float':3.9970090858857263,
                   'expect_neg':3.9970090858857263,
                   'expect_text':3.9970090858857263,
                   'expect_empty':None,
                   'expect_nan':4.147622830963417,
                   'expect_inf':None,
                   'expect_n1':0.0,
                   'expect_n2':0.5,
                   'expect_ones':0.,
                   'expect_zeros':0.
                 }
                )

stdevTests=\
    type('stdevTests',(aggTests,),
                 { 'name':'stdev',
                   'aggregate':pystaggrelite3.stdev,
                   'expect_float':4.14789235504141,
                   'expect_neg':4.14789235504141,
                   'expect_text':4.14789235504141,
                   'expect_empty':None,
                   'expect_nan':4.316982712913006,
                   'expect_inf':None,
                   'expect_n1':None,
                   'expect_n2':math.sqrt(2.)/2.,
                   'expect_ones':0.,
                   'expect_zeros':0.
                 }
                )

semTests=\
    type('semTests',(aggTests,),
                 { 'name':'sem',
                   'aggregate':pystaggrelite3.sem,
                   'expect_float':1.108570862127418,
                   'expect_neg':1.108570862127418,
                   'expect_text':1.108570862127418,
                   'expect_empty':None,
                   'expect_nan':1.1973155789768832,
                   'expect_inf':None,
                   'expect_n1':None,
                   'expect_n2':0.5,
                   'expect_ones':0.,
                   'expect_zeros':0.
                 }
                )

ciTests=\
    type('ciTests',(aggTests,),
                 { 'name':'ci',
                   'aggregate':pystaggrelite3.ci,
                   'expect_float':2.1727988897697394,
                   'expect_neg':2.1727988897697394,
                   'expect_text':2.1727988897697394,
                   'expect_empty':None,
                   'expect_nan':2.3467385347946914,
                   'expect_inf':None,
                   'expect_n1':None,
                   'expect_n2':0.5*1.96,
                   'expect_ones':0.,
                   'expect_zeros':0.
                 }
                )

rmsTests=\
    type('rmsTests',(aggTests,),
                 { 'name':'rms',
                   'aggregate':pystaggrelite3.rms,
                   'expect_float':8.821738571765286,
                   'expect_neg':8.821738571765286,
                   'expect_text':8.821738571765286,
                   'expect_empty':None,
                   'expect_nan':8.902173459762077,
                   'expect_inf':float('inf'),
                   'expect_ones':1.,
                   'expect_zeros':0.
                 }
                )

prodTests=\
    type('prodTests',(aggTests,),
                 { 'name':'prod',
                   'aggregate':pystaggrelite3.prod,
                   'expect_float':216047570729.97736,
                   'expect_neg':216047570729.97736,
                   'expect_text':216047570729.97736,
                   'expect_empty':None,
                   'expect_nan':28058126068.82824,
                   'expect_inf':float('inf'),
                   'expect_n1':4.,
                   'expect_n2':20.,
                   'expect_ones':1.,
                   'expect_zeros':0.
                 }
                )

skewTests=\
    type('skewTests',(aggTests,),
                 { 'name':'skew',
                   'aggregate':pystaggrelite3.skew,
                   'expect_float':-0.14872815083272467,
                   'expect_neg':0.14872815083272467,
                   'expect_text':-0.14872815083272467,
                   'expect_empty':None,
                   'expect_nan':-0.15515079014695105,
                   'expect_inf':None,
                   'expect_ones':None,
                   'expect_zeros':None
                 }
                )

skewpTests=\
    type('skewpTests',(aggTests,),
                 { 'name':'skewp',
                   'aggregate':pystaggrelite3.skewp,
                   'expect_float':-0.1322935682076316,
                   'expect_neg':0.1322935682076316,
                   'expect_text':-0.1322935682076316,
                   'expect_empty':None,
                   'expect_nan':-0.13664205273197477,
                   'expect_inf':None,
                   'expect_ones':None,
                   'expect_zeros':None
                 }
                )

kurtTests=\
    type('kurtTests',(aggTests,),
                 { 'name':'kurt',
                   'aggregate':pystaggrelite3.kurt,
                   'expect_float':-1.138508154575547,
                   'expect_neg':-1.138508154575547,
                   'expect_text':-1.138508154575547,
                   'expect_empty':None,
                   'expect_nan':-1.329835362052564,
                   'expect_inf':None,
                   'expect_ones':None,
                   'expect_zeros':None
                 }
                )

kurtpTests=\
    type('kurtTests',(aggTests,),
                 { 'name':'kurtp',
                   'aggregate':pystaggrelite3.kurtp,
                   'expect_float':-1.1706824430972933,
                   'expect_neg':-1.1706824430972933,
                   'expect_text':-1.1706824430972933,
                   'expect_empty':None,
                   'expect_nan':-1.2992969632487026,
                   'expect_inf':None,
                   'expect_ones':None,
                   'expect_zeros':None
                 }
                )

def suite():
    return unittest.TestSuite((
               unittest.makeSuite(hasnanTests,         "Check"),
               unittest.makeSuite(hasinfTests,         "Check"),
               unittest.makeSuite(arbitraryTests,      "Check"),
               unittest.makeSuite(varpTests,           "Check"),
               unittest.makeSuite(varTests,            "Check"),
               unittest.makeSuite(stdevpTests,         "Check"),
               unittest.makeSuite(stdevTests,          "Check"),
               unittest.makeSuite(semTests,            "Check"),
               unittest.makeSuite(ciTests,             "Check"),
               unittest.makeSuite(rmsTests,            "Check"),
               unittest.makeSuite(prodTests,           "Check"),
               unittest.makeSuite(skewpTests,          "Check"),
               unittest.makeSuite(skewTests,           "Check"),
               unittest.makeSuite(kurtpTests,          "Check"),
               unittest.makeSuite(kurtTests,           "Check"),
               unittest.makeSuite(datarangeTests,      "Check"),
               unittest.makeSuite(abs_meanTests,       "Check"),
               unittest.makeSuite(geometric_meanTests, "Check"),
               unittest.makeSuite(modeTests,           "Check"),
               unittest.makeSuite(medianTests,         "Check"),
               unittest.makeSuite(getaggTests),
               unittest.makeSuite(histTests)
                              ))

if __name__ == "__main__":
    # run tests
    runner = unittest.TextTestRunner()
    runner.run(suite())
