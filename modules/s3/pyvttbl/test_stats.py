from __future__ import print_function

# Copyright (c) 2011, Roger Lew [see LICENSE.txt]
# This software is funded in part by NIH Grant P20 RR016454.

import unittest
import warnings
import os
import math
from random import shuffle, random
try:
    from collections import Counter,OrderedDict
except ImportError:
    from gluon.contrib.simplejson import OrderedDict
    from counter import Counter
from dictset import DictSet,_rep_generator
from math import isnan, isinf, floor
import numpy as np
from pprint import pprint as pp
from pyvttbl import DataFrame, PyvtTbl, Descriptives,  Marginals, Histogram, \
     Ttest, Anova1way, ChiSquare1way, ChiSquare2way, Correlation, \
     _flatten, _isfloat, _isint

from anova import Anova

class Test_posthoc(unittest.TestCase):
    def test0(self):
        # http://www.utdallas.edu/~herve/abdi-NewmanKeuls2010-pretty.pdf
        d = [[21.0, 20.0, 26.0, 46.0, 35.0, 13.0, 41.0, 30.0, 42.0, 26.0],
             [23.0, 30.0, 34.0, 51.0, 20.0, 38.0, 34.0, 44.0, 41.0, 35.0],
             [35.0, 35.0, 52.0, 29.0, 54.0, 32.0, 30.0, 42.0, 50.0, 21.0],
             [44.0, 40.0, 33.0, 45.0, 45.0, 30.0, 46.0, 34.0, 49.0, 44.0],
             [39.0, 44.0, 51.0, 47.0, 50.0, 45.0, 39.0, 51.0, 39.0, 55.0]]
        conditions_list = 'Contact Hit Bump Collide Smash'.split()
        D=Anova1way()
        D.run(d, conditions_list=conditions_list)
##        print(D)

    def test1(self):
        # http://www.utdallas.edu/~herve/abdi-NewmanKeuls2010-pretty.pdf
        d = [[21.0, 20.0, 26.0, 46.0, 35.0, 13.0, 41.0, 30.0, 42.0, 26.0],
             [23.0, 30.0, 34.0, 51.0, 20.0, 38.0, 34.0, 44.0, 41.0, 35.0],
             [35.0, 35.0, 52.0, 29.0, 54.0, 32.0, 30.0, 42.0, 50.0, 21.0],
             [44.0, 40.0, 33.0, 45.0, 45.0, 30.0, 46.0, 34.0, 49.0, 44.0],
             [39.0, 44.0, 51.0, 47.0, 50.0, 45.0, 39.0, 51.0, 39.0, 55.0]]
        conditions_list = 'Contact Hit Bump Collide Smash'.split()
        D=Anova1way(posthoc='snk')
        D.run(d, conditions_list=conditions_list)
        print(D)

class Test_anova(unittest.TestCase):
    def test0(self):
        ## Within test
        df=DataFrame()
        fname='error~subjectXtimeofdayXcourseXmodel.csv'
        df.read_tbl(fname)
        aov=Anova()
        aov.run(df,'ERROR',wfactors=['TIMEOFDAY','COURSE','MODEL'])#,transform='windsor05')
        aov.output2html(fname[:-4]+'RESULTS.htm')
##        print(aov)

    def test1(self):
        df=DataFrame()
        fname='error~subjectXtimeofdayXcourseXmodel.csv'
        df.read_tbl(fname)
        aov=df.anova('ERROR',wfactors=['TIMEOFDAY','COURSE','MODEL'])#,transform='windsor05')
        aov.output2html(fname[:-4]+'RESULTS.htm')

    def test2(self):
        ## Between-Subjects test
        df=DataFrame()
        fname='words~ageXcondition.csv'
        df.read_tbl(fname)
        aov=Anova()
        aov.run(df,'WORDS',bfactors=['AGE','CONDITION'])

    def test3(self):
        ## Mixed Between/Within test
        df=DataFrame()
        fname='suppression~subjectXgroupXcycleXphase.csv'
        df.read_tbl(fname)
        df['SUPPRESSION']=[.01*x for x in df['SUPPRESSION']]
        aov=Anova()
        aov.run(df,'SUPPRESSION',wfactors=['CYCLE','PHASE'],bfactors=['GROUP'])#,transform='win
##        print(repr(aov))

class Test_correlation(unittest.TestCase):
    def test0(self):
        R="""Correlation([(('t1', 't2'), {'p': 9.699461194116956e-12, 'r': 0.9577922077922078}), (('t1', 't3'), {'p': 2.2594982244811486e-09, 'r': -0.924025974025974}), (('t2', 't3'), {'p': 6.850166042119375e-08, 'r': -0.8896103896103895})], conditions_list=['t1', 't2', 't3'], coefficient='spearman', N=21)"""
        A=[24,61,59,46,43,44,52,43,58,67,62,57,71,49,54,43,53,57,49,56,33]
        B=[42.93472681237495, 78.87307334936268, 75.37292628918023, 65.49076317291956, 55.55965179772366, 56.777730638998236, 62.19451880792437, 54.73710611356715, 72.10021832823149, 85.94377749485642, 78.2087578930983, 72.01681829338037, 84.27889316830063, 60.20516982367225, 65.6276497088971, 62.36549856901088, 69.18772114281175, 67.00548667483324, 59.042687027269466, 71.99214593063917, 45.00831155783992]
        C=[-53.05540625388731, -96.33996451998567, -92.32465861908086, -70.90536432779966, -55.953777697739255, -74.12814626217357, -75.89188834814621, -64.24093256012688, -89.62208010083313, -87.41075066046812, -80.40932820298143, -77.99906284144805, -95.31607277596169, -61.672429800914486, -85.26088499198657, -63.4402296673869, -74.84950736563589, -85.00433219746624, -71.5901436929124, -76.43243666219388, -48.01082320924727]

        cor=Correlation()
        cor.run([A,B,C],['t1','t2','t3'],coefficient='spearman')
        self.assertEqual(repr(cor),R)

    def test1(self):
        R="""Bivariate Correlations

                         A           B           C
======================================================
A   spearman                 1       0.958      -0.924
    Sig (2-tailed)           .   9.699e-12   2.259e-09
    N                       21          21          21
------------------------------------------------------
B   spearman             0.958           1      -0.890
    Sig (2-tailed)   9.699e-12           .       0.000
    N                       21          21          21
------------------------------------------------------
C   spearman            -0.924      -0.890           1
    Sig (2-tailed)   2.259e-09       0.000           .
    N                       21          21          21

Larzelere and Mulaik Significance Testing

 Pair     i   Correlation       P       alpha/(k-i+1)   Sig.
============================================================
A vs. B   1         0.958   9.699e-12           0.017   **
A vs. C   2         0.924   2.259e-09           0.025   **
B vs. C   3         0.890   6.850e-08           0.050   **   """
        df=DataFrame()
        df['A']=[24,61,59,46,43,44,52,43,58,67,62,57,71,49,54,43,53,57,49,56,33]
        df['B']=[42.93472681237495, 78.87307334936268, 75.37292628918023, 65.49076317291956, 55.55965179772366, 56.777730638998236, 62.19451880792437, 54.73710611356715, 72.10021832823149, 85.94377749485642, 78.2087578930983, 72.01681829338037, 84.27889316830063, 60.20516982367225, 65.6276497088971, 62.36549856901088, 69.18772114281175, 67.00548667483324, 59.042687027269466, 71.99214593063917, 45.00831155783992]
        df['C']=[-53.05540625388731, -96.33996451998567, -92.32465861908086, -70.90536432779966, -55.953777697739255, -74.12814626217357, -75.89188834814621, -64.24093256012688, -89.62208010083313, -87.41075066046812, -80.40932820298143, -77.99906284144805, -95.31607277596169, -61.672429800914486, -85.26088499198657, -63.4402296673869, -74.84950736563589, -85.00433219746624, -71.5901436929124, -76.43243666219388, -48.01082320924727]

        cor=df.correlation(['A','B','C'],coefficient='spearman')
        self.assertEqual(str(cor),R)

    def test2(self):
        df = DataFrame()
        df.read_tbl('iqbrainsize.txt', delimiter='\t')
        cor = df.correlation(df.names())
        print(cor)

class Test_chisquare2way(unittest.TestCase):
    def test0(self):
        R="""Chi-Square: two Factor

SUMMARY
         Guilty     NotGuilty   Total
=====================================
High          105          76     181
        (130.441)    (50.559)
Low           153          24     177
        (127.559)    (49.441)
=====================================
Total         258         100     358

SYMMETRIC MEASURES
                          Value    Approx.
                                    Sig.
===========================================
Cramer's V                0.317   8.686e-10
Contingency Coefficient   0.302   5.510e-09
N of Valid Cases            358

CHI-SQUARE TESTS
                        Value    df       P
===============================================
Pearson Chi-Square      35.930    1   2.053e-09
Continuity Correction   34.532    1   4.201e-09
Likelihood Ratio        37.351    1           0
N of Valid Cases           358                  """
        df=DataFrame()
        df['FAULTS']=list(Counter(Low=177,High=181).elements())
        df['FAULTS'].reverse()
        df['VERDICT']=list(Counter(Guilty=153, NotGuilty=24).elements())
        df['VERDICT'].extend(list(Counter(Guilty=105, NotGuilty=76).elements()))

        x2= df.chisquare2way('FAULTS','VERDICT')
        self.assertEqual(str(x2), R)

    def test1(self):
        """chi-square 2-way"""
        R="""Chi-Square: two Factor

SUMMARY
            Litter      Removed    Trash Can   Total
====================================================
Countrol         385         477          41     903
           (343.976)   (497.363)    (61.661)
Message          290         499          80     869
           (331.024)   (478.637)    (59.339)
====================================================
Total            675         976         121    1772

SYMMETRIC MEASURES
                          Value    Approx.
                                    Sig.
===========================================
Cramer's V                0.121   3.510e-07
Contingency Coefficient   0.120   4.263e-07
N of Valid Cases           1772

CHI-SQUARE TESTS
                     Value    df       P
============================================
Pearson Chi-Square   25.794    2   2.506e-06
Likelihood Ratio     26.056    2   2.198e-06
N of Valid Cases       1772                  """

        df=DataFrame()
        rfactors=['Countrol']*903 + ['Message']*869
        cfactors=['Trash Can']*41 + ['Litter']*385 + ['Removed']*477
        cfactors+=['Trash Can']*80 + ['Litter']*290 + ['Removed']*499

        x2= ChiSquare2way()
        x2.run(rfactors, cfactors)
        self.assertEqual(str(x2), R)

    def test2(self):
        """chi-square 2-way"""
        R="""ChiSquare2way([('chisq', 25.79364579345589), ('p', 2.5059995107347527e-06), ('df', 2), ('lnchisq', 26.055873891205664), ('lnp', 2.1980566132523407e-06), ('ccchisq', None), ('ccp', None), ('N', 1772.0), ('C', 0.11978058926585373), ('CramerV', 0.12064921681366868), ('CramerV_prob', 3.50998747929475e-07), ('C_prob', 4.26267335738495e-07)], counter=Counter({('Message', 'Removed'): 499.0, ('Countrol', 'Removed'): 477.0, ('Countrol', 'Litter'): 385.0, ('Message', 'Litter'): 290.0, ('Message', 'Trash Can'): 80.0, ('Countrol', 'Trash Can'): 41.0}), row_counter=Counter({'Countrol': 903.0, 'Message': 869.0}), col_counter=Counter({'Removed': 976.0, 'Litter': 675.0, 'Trash Can': 121.0}), N_r=2, N_c=3)"""

        rfactors=['Countrol']*903 + ['Message']*869
        cfactors=['Trash Can']*41 + ['Litter']*385 + ['Removed']*477
        cfactors+=['Trash Can']*80 + ['Litter']*290 + ['Removed']*499

        x2= ChiSquare2way()
        x2.run(rfactors, cfactors)
        self.assertEqual(repr(x2), R)

class Test_chisquare1way(unittest.TestCase):
    def test0(self):
        """chi-square 1-way"""
        R="""Chi-Square: Single Factor

SUMMARY
           A   B   C   D
=========================
Observed   4   5   8   15
Expected   8   8   8    8

CHI-SQUARE TESTS
                     Value   df     P
=======================================
Pearson Chi-Square   9.250    3   0.026
Likelihood Ratio     8.613    3   0.035
Observations            32              """

        D=ChiSquare1way()
        D.run([4,5,8,15])
        self.assertEqual(str(D),R)

    def test1(self):
        R="ChiSquare1way([('chisq', 9.25), ('p', 0.026145200026967786), ('df', 3), ('lnchisq', 8.613046045734304), ('lnp', 0.03490361434485369), ('lndf', 3)], conditions_list=['A', 'B', 'C', 'D'])"
        D=ChiSquare1way()
        D.run([4,5,8,15])
        self.assertEqual(repr(D),R)

    def test1(self):
        R="""Chi-Square: Single Factor

SUMMARY
             1        2        3        4
============================================
Observed        7       20       23        9
Expected   14.750   14.750   14.750   14.750

CHI-SQUARE TESTS
                     Value    df     P
========================================
Pearson Chi-Square   12.797    3   0.005
Likelihood Ratio     13.288    3   0.004
Observations             59              """

        df = DataFrame()
        df.read_tbl('chi_test.csv')
        X=df.chisquare1way('RESULT')
        self.assertEqual(str(X),R)

    def test2(self):
        R="""Chi-Square: Single Factor

SUMMARY
             1        2        3        4        5
=====================================================
Observed        7       20       23        9        0
Expected   11.800   11.800   11.800   11.800   11.800

CHI-SQUARE TESTS
                     Value    df        P
=============================================
Pearson Chi-Square   30.746     4   3.450e-06
Likelihood Ratio        nan   nan         nan
Observations             59                   """

        df = DataFrame()
        df.read_tbl('chi_test.csv')
        X=df.chisquare1way('RESULT',{1:11.8 ,2:11.8 ,3:11.8 ,4:11.8 ,5:11.8})
        self.assertEqual(str(X),R)

class Test_anova1way(unittest.TestCase):
    def test0(self):
        """1 way anova"""
        R="Anova1way([('f', 16.70726997413529), ('p', 4.5885798225758395e-06), ('ns', [14, 15, 16]), ('mus', [62.142857142857146, 57.2, 94.375]), ('vars', [202.13186813186815, 584.7428571428571, 339.5833333333333]), ('ssbn', 12656.046825396828), ('sswn', 15907.864285714284), ('dfbn', 2), ('dfwn', 42), ('msbn', 6328.023412698414), ('mswn', 378.7586734693877)], conditions_list=['A', 'B', 'C'])"
        listOflists=[[42,52,55,59,75,40,79,79,44,56,68,77,75,69],
                     [29,36,29,31,97,88,27,57,54,77,54,52,58,91,78],
                     [91,79,73,75,99,66,114,120,102,68,114,79,115,104,107,104]]

        D=Anova1way()
        D.run(listOflists)
        self.assertEqual(repr(D),R)

    def test1(self):
        """1 way anova"""

        R="""Anova: Single Factor on Measure

SUMMARY
Groups   Count   Sum    Average   Variance
==========================================
A           14    870    62.143    202.132
B           15    858    57.200    584.743
C           16   1510    94.375    339.583

ANOVA
Source of       SS       df      MS        F       P-value
Variation
===========================================================
Treatments   12656.047    2   6328.023   16.707   4.589e-06
Error        15907.864   42    378.759
===========================================================
Total        28563.911   44                                 """
        listOflists=[[42,52,55,59,75,40,79,79,44,56,68,77,75,69],
                     [29,36,29,31,97,88,27,57,54,77,54,52,58,91,78],
                     [91,79,73,75,99,66,114,120,102,68,114,79,115,104,107,104]]

        D=Anova1way()
        D.run(listOflists)
        self.assertEqual(str(D),R)

    def test2(self):
        R="""Anova: Single Factor on SUPPRESSION

SUMMARY
Groups   Count     Sum      Average   Variance
==============================================
AA         128       2048        16    148.792
AB         128   2510.600    19.614    250.326
LAB        128   2945.000    23.008    264.699

ANOVA
Source of       SS       df       MS        F      P-value
Variation
===========================================================
Treatments    3144.039     2   1572.020   7.104   9.348e-04
Error        84304.687   381    221.272
===========================================================
Total        87448.726   383                                """

        df = DataFrame()
        df.read_tbl('suppression~subjectXgroupXageXcycleXphase.csv')
        aov=df.anova1way('SUPPRESSION','GROUP')
        self.assertEqual(str(aov),R)

class Test_ttest1sample(unittest.TestCase):
    def test0(self):
        """1 sample ttest"""
        R=OrderedDict([('t', -17.797126310672542), ('p2tail', 1.0172137120313963e-07), ('p1tail', 5.086068560156982e-08), ('n', 9), ('df', 8), ('mu', 4.555555555555555), ('pop_mean', 20), ('var', 6.777777777777778), ('tc2tail', 2.3060059174895287), ('tc1tail', 1.8595485016703606)])
        A=[3,4, 5,8,9, 1,2,4, 5]
        pop_mean=20

        D=Ttest()
        D.run(A, pop_mean=pop_mean)

        for k in R.keys():
            self.assertTrue(D[k],R[k])

    def test1(self):
        R="""t-Test: One Sample for means

                         SUPPRESSION
====================================
Sample Mean                   19.541
Hypothesized Pop. Mean             0
Variance                     228.326
Observations                     384
df                               383
t Stat                        25.341
P(T<=t) one-tail           3.347e-84
t Critical one-tail            1.649
P(T<=t) two-tail           6.694e-84
t Critical two-tail            1.966 """
        df = DataFrame()
        df.read_tbl('suppression~subjectXgroupXageXcycleXphase.csv')
        ttest=df.ttest('SUPPRESSION')
        self.assertEqual(str(ttest),R)

class Test_ttest(unittest.TestCase):
    def test0(self):
        """paired ttest"""
        R=OrderedDict([('t', -1.4106912317171967), ('p2tail', 0.19601578492449323), ('p1tail', 0.09800789246224662), ('n1', 9), ('n2', 9), ('df', 8), ('mu1', 4.555555555555555), ('mu2', 7.888888888888889), ('var1', 6.777777777777778), ('var2', 47.111111111111114), ('tc2tail', 2.3060059174895287), ('tc1tail', 1.8595485016703606)])

        A=[3,4, 5,8,9, 1,2,4, 5]
        B=[6,19,3,2,14,4,5,17,1]

        D=Ttest()
        D.run(A,B,paired=True)

        for k in R.keys():
            self.assertTrue(D[k],R[k])

    def test01(self):
        """paired ttest"""
        R="""t-Test: Paired Two Sample for means
                        A        B
=====================================
Mean                   4.556    7.889
Variance               6.778   47.111
Observations               9        9
Pearson Correlation    0.102
df                         8
t Stat                -1.411
P(T<=t) one-tail       0.098
t Critical one-tail    1.860
P(T<=t) two-tail       0.196
t Critical two-tail    2.306          """

        A=[3,4, 5,8,9, 1,2,4, 5]
        B=[6,19,3,2,14,4,5,17,1]

        D=Ttest()
        D.run(A,B,paired=True)

        self.assertEqual(str(D),R)

    def test1(self):
        """independent equal variance ttest"""
        R=OrderedDict([('t', -1.712764845721259), ('p2tail', 0.10493320627442616), ('p1tail', 0.05246660313721308), ('n1', 9), ('n2', 10), ('df', 17), ('mu1', 4.555555555555555), ('mu2', 9.0), ('var1', 6.777777777777777), ('var2', 54.22222222222222), ('vpooled', 31.895424836601304), ('tc2tail', 2.1098158322274685), ('tc1tail', 1.7396057955920696)])

        A=[3,4, 5,8,9, 1,2,4, 5]
        B=[6,19,3,2,14,4,5,17,1,19]

        D=Ttest()
        D.run(A,B,equal_variance=True)

        for k in R.keys():
            self.assertTrue(D[k],R[k])

    def test11(self):
        """independent equal variance ttest"""
        R="""t-Test: Two-Sample Assuming Equal Variances
                        A        B
=====================================
Mean                   4.556        9
Variance               6.778   54.222
Observations               9       10
Pooled Variance       31.895
df                        17
t Stat                -1.713
P(T<=t) one-tail       0.052
t Critical one-tail    1.740
P(T<=t) two-tail       0.105
t Critical two-tail    2.110          """

        A=[3,4, 5,8,9, 1,2,4, 5]
        B=[6,19,3,2,14,4,5,17,1,19]

        D=Ttest()
        D.run(A,B,equal_variance=True)

        self.assertEqual(str(D),R)

    def test2(self):
        """independent unequal variance ttest"""
        R=OrderedDict([('t', -1.7884967184189302), ('p2tail', 0.1002162848567985), ('p1tail', 0.05010814242839925), ('n1', 9), ('n2', 10), ('df', 11.425658453695835), ('mu1', 4.555555555555555), ('mu2', 9.0), ('var1', 6.777777777777777), ('var2', 54.22222222222222), ('tc2tail', 2.1910201758146286), ('tc1tail', 1.789783127605915)])

        A=[3,4, 5,8,9, 1,2,4, 5]
        B=[6,19,3,2,14,4,5,17,1,19]

        D=Ttest()
        D.run(A,B,equal_variance=False)

        for k in R.keys():
            self.assertTrue(D[k],R[k])

    def test21(self):
        """independent unequal variance ttest"""
        R="""t-Test: Two-Sample Assuming Unequal Variances
                        A        B
=====================================
Mean                   4.556        9
Variance               6.778   54.222
Observations               9       10
df                    11.426
t Stat                -1.788
P(T<=t) one-tail       0.050
t Critical one-tail    1.790
P(T<=t) two-tail       0.100
t Critical two-tail    2.191          """

        A=[3,4, 5,8,9, 1,2,4, 5]
        B=[6,19,3,2,14,4,5,17,1,19]

        D=Ttest()
        D.run(A,B,equal_variance=False)

        self.assertEqual(str(D),R)

    def test3(self):
        """independent unequal variance ttest
        http://alamos.math.arizona.edu/~rychlik/math263/class_notes/Chapter7/R/"""
        R=OrderedDict([('t', 2.310889197854228), ('p2tail', 0.026382412254338405), ('p1tail', 0.013191206127169203), ('n1', 21), ('n2', 23), ('df', 37.855400659439084), ('mu1', 51.476190476190474), ('mu2', 41.52173913043478), ('var1', 121.16190476190475), ('var2', 294.0790513833993), ('tc2tail', 2.0246487110853195), ('tc1tail', 1.6861152835190296)])

        A=[24,61,59,46,43,44,52,43,58,67,62,57,71,49,54,43,53,57,49,56,33]
        B=[42,33,46,37,43,41,10,42,55,19,17,55,26,54,60,28,62,20,53,48,37,85,42]

        D=Ttest()
        D.run(A,B,equal_variance=False)

        for k in R.keys():
            self.assertTrue(D[k],R[k])

    def test31(self):
        """independent unequal variance ttest
        http://alamos.math.arizona.edu/~rychlik/math263/class_notes/Chapter7/R/"""
        R="""t-Test: Two-Sample Assuming Unequal Variances
                         A         B
=======================================
Mean                   51.476    41.522
Variance              121.162   294.079
Observations               21        23
df                     37.855
t Stat                  2.311
P(T<=t) one-tail        0.013
t Critical one-tail     1.686
P(T<=t) two-tail        0.026
t Critical two-tail     2.025           """

        A=[24,61,59,46,43,44,52,43,58,67,62,57,71,49,54,43,53,57,49,56,33]
        B=[42,33,46,37,43,41,10,42,55,19,17,55,26,54,60,28,62,20,53,48,37,85,42]

        D=Ttest()
        D.run(A,B,equal_variance=False)

        self.assertEqual(str(D),R)

    def test4(self):
        R="""t-Test: Paired Two Sample for means
                        PRE        POST
=========================================
Mean                    87.250     87.083
Variance              1207.659   1166.629
Observations                12         12
Pearson Correlation      0.995
df                          11
t Stat                   0.163
P(T<=t) one-tail         0.437
t Critical one-tail      1.796
P(T<=t) two-tail         0.873
t Critical two-tail      2.201            """
        df = DataFrame()
        df.read_tbl('example2_prepost.csv')
        ttest = df.ttest('PRE','POST',paired=True)
        self.assertEqual(str(ttest),R)

    def test__repr__(self):
        R="Ttest([('t', 2.310889197854228), ('p2tail', 0.026382412254338405), ('p1tail', 0.013191206127169203), ('n1', 21), ('n2', 23), ('df', 37.855400659439084), ('mu1', 51.476190476190474), ('mu2', 41.52173913043478), ('var1', 121.16190476190475), ('var2', 294.0790513833993), ('tc2tail', 2.0246487110853195), ('tc1tail', 1.6861152835190296)], equal_variance=False, aname='A', bname='B', type='t-Test: Two-Sample Assuming Unequal Variances')"

        A=[24,61,59,46,43,44,52,43,58,67,62,57,71,49,54,43,53,57,49,56,33]
        B=[42,33,46,37,43,41,10,42,55,19,17,55,26,54,60,28,62,20,53,48,37,85,42]

        D=Ttest()
        D.run(A,B,equal_variance=False)
        self.assertEqual(repr(D),R)


def suite():
    return unittest.TestSuite((
            unittest.makeSuite(Test_anova),
            unittest.makeSuite(Test_correlation),
            unittest.makeSuite(Test_chisquare2way),
            unittest.makeSuite(Test_chisquare1way),
            unittest.makeSuite(Test_posthoc),
##            unittest.makeSuite(Test_anova1way),
            unittest.makeSuite(Test_ttest1sample),
            unittest.makeSuite(Test_ttest)
                              ))

if __name__ == "__main__":
    # run tests
    runner = unittest.TextTestRunner()
    runner.run(suite())

