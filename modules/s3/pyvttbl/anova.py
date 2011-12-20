from __future__ import print_function

# Copyright (c) 2011, Roger Lew [see LICENSE.txt]
# This software is funded in part by NIH Grant P20 RR016454.
#
# Change Log
# 04/24/2010
#   fixed bug with specifying plot resolution
#   between subjects plots now have error bars
#
# 04/13/2010
#   fixed bug affecting the non-centrality parameter calculation
#   and the observed power estimates

"""
class to perform one-way and factorial analyses of variance on between,
within, or mixed datasets.

For repeated measure designs Greenhouse-Geisser's epsilon, Huynh-Feldt's
epsilon, and Box's epsilon are calculated. Standard errors and
confidence intervals are calculated for within subjects effects and
interactions.

def epsGG(y, df1)

    given data matrix y returns Greenhouse-Geisser's epsilon

    see __docstring__ for function for more information

def epsHF(y, df1)

    given data matrix y returns Huynh-Feldt's epsilon

    see __docstring__ for function for more information

def epsLB(y, df1)

    given data matrix y returns Box's epsilon

    see __docstring__ for function for more information

def windsor(X, percent)

    given vector X returns the Windsorized trimmed samples, in which the
    trimmed values are replaced by the most extreme value remaining in
    the tail.

class anova:
    def __init__(self,dframe,dv,wfactors=[],bfactors=[],sub='SUBJECT',
                 measure='',exclude={},transform=''):

        Fancy linear algebra is adapted from a matlab script by R.Henson,
        17/3/03
        rik.henson@mrc-cbu.cam.ac.uk
        http://www.mrc-cbu.cam.ac.uk/people/rik.henson/personal/repanova.m

         Input:

         dframe    = a dataframe object with data specified
                     (I'm passing the dataframe object into this function
                     b/c the dataframe class has a ReadCSV method the user
                     can take advantage of to read their data.)

         dv        = text string of label containing dependent variable

         factors   = factors to use for ANOVA
                     will average across unspecified factors
         sub       = text string of label for the subjects data

         measure   = optional name to describe dv (outputs '<dv> of
                     <measure>') intended when dv name is generic
                     (e.g., MEAN, RMS, SD, ...)

         exclude   = a dictionary of levels of factors to exclude from
                     analysis

         transform = either a string specifying a data transformation
                     or a function to perform a data transformation.
                     Error degrees of freedom are trimmed such that:
                         total_df = N - 1 - num_trimmed_samples

             (see Howell, 2001)

             STRING OPTION            TRANSFORM        COMMENTS
             ''                       X                default
             'log','log10'            numpy.log(X)     base 10 transform
             'reciprocal', 'inverse'  1/X
             'square-root', 'sqrt'    numpy.sqrt(X)
             'arcsine', 'arcsin'      numpy.arcsin(X)
             'windsor 10'             windsor(X, 10)   10% windosr trim


        Notes on the Greenhouse-Geisser epsilon calculation:
          Greenhouse-Geisser's epsilon is calculated using the
          Satterthwaite approximation. See Glaser (2003.)


        Notes on Generalized eta square measures of effect size:
          Generalized eta squared is a measure of effect size which
          allows comparibility across between-subjects and
          within-subjects designs. For background and derivation
          see Olejnik and Algina 2003. For further information and
          endorsement see Bakeman 2005.


        Notes on Standard Errors and Confidence Intervals:
          Standard Errors and 95% confidence intervals are calculated
          according to Loftus and Masson (1994).

        Notes on non-centrality and observed power estimation:
          The details and mathematical rational for calculating the
          non-centrality paramenter can be found:
              http://epm.sagepub.com/content/55/6/998.full.pdf+html
              http://www.jstor.org/stable/3701269?seq=2
              http://zoe.bme.gatech.edu/~bv20/public/samplesize.pdf

        References:
          Glaser, D.E. (2003). Variance Components. In R.S.J. Frackowiak, K.J.
              Friston, C. Firth, R. Dolan, C.J., Price, S. Zeki, J. Ashburner,
              & W.D. Penny, (Eds.), Human Brain Function. Academic Press, 2nd.
              edition. [http://www.fil.ion.ucl.ac.uk/spm/doc/books/hbf2/]
          Hopkins, K. D., & Hester, P. R. (1995). The noncentrality parameter
              for the F distribution, mean squares, and effect size: An
              Examination of some mathematical relationshipss. Educational and
              Psychological Measurement, 55 (6), 998-999.
          Howell, D.C. (2001). Statistical Methods for Psychology. Wadsworth
              Publishing, CA.
          Liu, X., & Raudenbush, S. (2004). A note on the noncentrality parameter
              and effect size estimates for the F Test in ANOVA. Journal of Ed.
              and Behavioral Statistics, 29 (2), 251-255.
          Loftus, G.R., & Masson, M.E. (1994). Using confidence intervals in
              within-subjects designs. The Psychonomic Bulletin & Review, 1(4),
              476-490.
          Masson, M.E., & Loftus, G.R. (2003). Using confidence intervals for
              graphically-based data interpretation. Canadian Journal of
              Experimental Pscyhology, 57(3), 203-220.

    def _between(self)

        private function to perform factorial between subjects ANOVA

    def _mixed(self)

        private function to perform mixed within/between factorial ANOVA

    def _within(self)

        private function to perform factorial within subjects ANOVA

    def _num2binvec(self,d,p=0)

        private function to code main effects and interactions

    def output2html(self, fname):

        writes ANOVA results and summary means to html file
        with name specified by fname

    def _between_html(self, fname)

        private function to write between subjects ANOVA results

    def _mixed_html(self, fname)

        private function to write mixed within/between ANOVA results

    def _within_html(self, fname)

        private function to write within subjects ANOVA results

    def _summary_html(self, factors, html)

        private function to write summary tables to html file

        inputs:

            factors = list of factors to write full factorial summary tables
            html = a SimpleHTML.SimpleHTML object
"""

# Python 2 to 3 workarounds
import sys
if sys.version_info[0] == 2:
    _strobj = basestring
    _xrange = xrange
elif sys.version_info[0] == 3:
    _strobj = str
    _xrange = range

import csv
import numpy
import scipy
import pylab

try:
    from collections import OrderedDict
except ImportError:
    from gluon.contrib.simplejson import OrderedDict
from copy import copy
from numpy import any,array,asarray,concatenate, \
                  cov,diag,dot,eye,fix,floor,isnan, \
                  kron,min,max,mean,ones,prod,shape, \
                  sqrt,std,trace,where,zeros
from numpy import remainder as rem
from numpy import sum as nsum
from numpy.random import uniform
from pprint import pprint as pp
from scipy.stats import fprob
try:
    from scipy.stats.stats import stderr
except:
    from scipy.stats import sem as stderr
from scipy.stats.distributions import f,ncf,t
from scipy.signal import detrend
from sets import Set

# Modules I wrote to support the anova class
##from stixbox import qt
##from pyvttbl import DataFrame
from SimpleHTML import *
from texttable import Texttable as TextTable
from texttable import _str

def qf(p,df1,df2):
    return f(df1,df2).ppf(p)

def qt(p,df):
    return t(df).ppf(p)

def ncfcdf(x,df1,df2,nc):
    """
    Noncentral F cumulative distribution function (cdf)

    P = ncfcdf(x,df1,df2,ncA) computes the noncentral
    F cdf at each of the values in {x} using the
    corresponding numerator degrees of freedom in {df1},
    denominator degrees of freedom in {df2}, and positive
    noncentrality parameters in {nc}.
    """
    return ncf(df1,df2,nc).cdf(x)

def observed_power(df,dfe,nc,alpha=0.05):
    """
    http://zoe.bme.gatech.edu/~bv20/public/samplesize.pdf

    observed_power(3,30,16) should yield 0.916
    """
    return 1.-ncfcdf(qf(1.-alpha,df,dfe), df,dfe,nc)

def noncentrality_par(nj,Y,mu,var):
    """
    Returns the noncentrality parameter. Assumes a
    balanced design.

    Y   - list of cell means
    mu  - pop mean estimate
    var - pop variance estimate
    nj  - is the number of observations per cell

    """

    return sum([nj*(y-mu)**2. for y in Y])/var

def f2s(L):
    """Turns a list of floats into a list of strings"""
    for i,l in enumerate(L):
        if isfloat(l):
            L[i] ='%.03f'%float(l)
    return L

def if_else(condition, a, b):
    """Provides Excel-like if/else statements"""
    if condition : return a
    else         : return b

def isfloat(string):
    """Returns True if string is a float"""
    try: float(string)
    except: return False
    return True

def matrix_rank(arr,tol=1e-8):
    """Return the matrix rank of an input array."""

    arr = asarray(arr)

    if len(arr.shape) != 2:
        raise ValueError('Input must be a 2-d array or Matrix object')

    svdvals = scipy.linalg.svdvals(arr)
    return sum(where(svdvals>tol,1,0))

def shape(X, i=-1):
    if i==-1 : return numpy.shape(X)
    else     : return numpy.shape(X)[i]

def std_error(X):
    return std(X)/sqrt(len(X))

def _xunique_combinations(items, n):
    if n==0: yield []
    else:
        for i in xrange(len(items)):
            for cc in _xunique_combinations(items[i+1:],n-1):
                yield [items[i]]+cc

def epsGG(y, df1):
    """
    (docstring is adapted from Trujillo-Ortiz (2006); see references)

    The Greenhouse-Geisser epsilon value measures by how much the
    sphericity assumption is violated. Epsilon is then used to adjust
    for the potential bias in the F statistic. Epsilon can be 1, which
    means that the sphericity assumption is met perfectly. An epsilon
    smaller than 1 means that the sphericity assumption is violated.
    The further it deviates from 1, the worse the violation; it can be
    as low as epsilon = 1/(k - 1), which produces the lower bound of
    epsilon (the worst case scenario). The worst case scenario depends
    on k, the number of levels in the repeated measure factor. In real
    life epsilon is rarely exactly 1. If it is not much smaller than 1,
    then we feel comfortable with the results of repeated measure ANOVA.
    The Greenhouse-Geisser epsilon is derived from the variance-
    covariance matrix of the data. For its evaluation we need to first
    calculate the variance-covariance matrix of the variables (S). The
    diagonal entries are the variances and the off diagonal entries are
    the covariances. From this variance-covariance matrix, the epsilon
    statistic can be estimated. Also we need the mean of the entries on
    the main diagonal of S, the mean of all entries, the mean of all
    entries in row i of S, and the individual entries in the variance-
    covariance matrix. There are three important values of epsilon. It
    can be 1 when the sphericity is met perfectly. This epsilon
    procedure was proposed by Greenhouse and Geisser (1959). Greenhouse-
    Geisser's epsilon is calculated using the Satterthwaite
    approximation. See Glaser (2003.)

      Syntax: function epsGG(y,df1)

      Inputs:
         y   = Input matrix can be a data matrix
               (size n-data x k-treatments)
         df1 = degrees of freedom of treatment

      Output:
         Greenhouse-Geisser epsilon value.

     $$We suggest you could take-a-look to the PDF document ''This Week's
       Citation Classics'' CCNumber 28, July 12, 1982, web-page
       [http://garfield.library.upenn.edu/classics1982/A1982NW45700001.pdf]$$

    Example 2 of Maxwell and Delaney (p.497). This is a repeated measures
    example with two within and a subject effect. We have one dependent
    variable:reaction time, two independent variables: visual stimuli
    are tilted at 0, 4, and 8 degrees; with noise absent or present.
    Each subject responded to 3 tilt and 2 noise given 6 trials. Data are,

                          0           4           8
                     -----------------------------------
            Subject    A     P     A     P     A     P
            --------------------------------------------
               1      420   480   420   600   480   780
               2      420   360   480   480   480   600
               3      480   660   480   780   540   780
               4      420   480   540   780   540   900
               5      540   480   660   660   540   720
               6      360   360   420   480   360   540
               7      480   540   480   720   600   840
               8      480   540   600   720   660   900
               9      540   480   600   720   540   780
              10      480   540   420   660   540   780
            --------------------------------------------

    The three measurements of reaction time were averaging across noise
    ausent/present. Given,

                             Tilt
                      -----------------
            Subject     0     4     8
            ---------------------------
               1       450   510   630
               2       390   480   540
               3       570   630   660
               4       450   660   720
               5       510   660   630
               6       360   450   450
               7       510   600   720
               8       510   660   780
               9       510   660   660
              10       510   540   660
            ---------------------------

    We need to estimate the Greenhouse-Geisser epsilon associated with
    the angle of rotation of the stimuli.

    Reference:
      Glaser, D.E. (2003). Variance Components. In R.S.J. Frackowiak, K.J.
          Friston, C. Firth, R. Dolan, C.J., Price, S. Zeki, J. Ashburner,
          & W.D. Penny, (Eds.), Human Brain Function. Academic Press, 2nd.
          edition. [http://www.fil.ion.ucl.ac.uk/spm/doc/books/hbf2/]
      Greenhouse, S.W. and Geisser, S. (1959), On methods in the analysis
          of profile data. Psychometrika, 24:95-112.
      Maxwell, S.E. and Delaney, H.D. (1990), Designing Experiments and
          Analyzing Data: A model comparison perspective. Pacific Grove,
          CA: Brooks/Cole.
      Trujillo-Ortiz, A., R. Hernandez-Walls, A. Castro-Perez and K.
          Barba-Rojo. (2006). epsGG:Greenhouse-Geisser epsilon. A MATLAB
          file. [WWW document]. URL
          http://www.mathworks.com/matlabcentral/fileexchange
          /loadFile.do?objectId=12839
    """
    if df1 == 1. : return 1.

    V = cov(y) # sample covariance
    return trace(V)**2 / (df1*trace(dot(V.T,V)))

def epsHF(y, df1):
    """
    This is ported from a Matlab function written by Trujillo-Ortiz et
    al. 2006 (see references) with an important modification. If the
    calculated epsilon values is greater than 1, it returns 1.

    The Huynh-Feldt epsilon its a correction of the Greenhouse-Geisser
    epsilon. This due that the Greenhouse-Geisser epsilon tends to
    underestimate epsilon when epsilon is greater than 0.70 (Stevens,
    1990). An estimated epsilon = 0.96 may be actually 1. Huynh-Feldt
    correction is less conservative. The Huynh-Feldt epsilon is
    calculated from the Greenhouse-Geisser epsilon. As the Greenhouse-
    Geisser epsilon, Huynh-Feldt epsilon measures how much the
    sphericity assumption or compound symmetry is violated. The idea of
    both corrections its analogous to pooled vs. unpooled variance
    Student's t-test: if we have to estimate more things because
    variances/covariances are not equal, then we lose some degrees of
    freedom and P-value increases. These epsilons should be 1.0 if
    sphericity holds. If not sphericity assumption appears violated.
    We must to have in mind that the greater the number of repeated
    measures, the greater the likelihood of violating assumptions of
    sphericity and normality (Keselman et al, 1996) . Therefore, we need
    to have the most conservative F values. These are obtained by
    setting epsilon to its lower bound, which represents the maximum
    violation of these assumptions. When a significant result is
    obtained, it is assumed to be robust. However, since this test may
    be overly conservative, Greenhouse and Geisser (1958, 1959)
    recommend that when the lower-bound epsilon gives a nonsignificant
    result, it should be followed by an approximate test (based on a
    sample estimate of epsilon).

      Syntax: function epsHF(y,df1)

      Inputs:
         y   = Input matrix can be a data matrix
               (size n-data x k-treatments)
         df1 = degrees of freedom of treatment

      Output:
         Huynh-Feldt epsilon value.

    See docstring for epsGG() for information on formatting X.

    Reference:
      Geisser, S, and Greenhouse, S.W. (1958), An extension of Box's
          results on the use of the F distribution in multivariate
          analysis. Annals of Mathematical Statistics, 29:885-891.
      Greenhouse, S.W. and Geisser, S. (1959), On methods in the
          analysis of profile data. Psychometrika, 24:95-112.
      Huynh, M. and Feldt, L.S. (1970), Conditions under which mean
          square rate in repeated measures designs have exact-F
          distributions. Journal of the American Statistical
          Association, 65:1982-1989
      Keselman, J.C, Lix, L.M. and Keselman, H.J. (1996), The analysis
          of repeated measurements: a quantitative research synthesis.
          British Journal of Mathematical and Statistical Psychology,
          49:275-298.
      Maxwell, S.E. and Delaney, H.D. (1990), Designing Experiments
          and Analyzing Data: A model comparison perspective. Pacific
          Grove, CA: Brooks/Cole.
      Trujillo-Ortiz, A., R. Hernandez-Walls, A. Castro-Perez and K.
          Barba-Rojo. (2006). epsGG:Greenhouse-Geisser epsilon. A
          MATLAB file. [WWW document].
          http://www.mathworks.com/matlabcentral/fileexchange
          /loadFile.do?objectId=12839
    """
    if df1 == 1. : return 1.

    k,n = shape(y)      # number of treatments
    eGG = epsGG(y, df1) # Greenhouse-Geisser epsilon

    N = n*(k-1.)*eGG-2.
    D = (k-1.)*((n-1.)-(k-1.)*eGG)
    eHF = N/D                 # Huynh-Feldt epsilon estimation

    if   eHF < eGG : return eGG
    elif eHF > 1.  : return 1.
    else           : return eHF

def epsLB(y, df1):
    """
    This is ported from a Matlab function written by Trujillo-Ortiz et
    al. 2006. See references.

    EPBG Box's conservative epsilon.
    The Box's conservative epsilon value (Box, 1954), measures by how
    much the sphericity assumption is violated. Epsilon is then used to
    adjust for the potential bias in the F statistic. Epsilon can be 1,
    which means that the sphericity assumption is met perfectly. An
    epsilon smaller than 1 means that the sphericity assumption is
    violated. The further it deviates from 1, the worse the violation;
    it can be as low as epsilon = 1/(k - 1), which produces the lower
    bound of epsilon (the worst case scenario). The worst case scenario
    depends on k, the number of levels in the repeated measure factor.
    In real life epsilon is rarely exactly 1. If it is not much smaller
    than 1, then we feel comfortable with the results of repeated
    measure ANOVA. The Box's conservative epsilon is derived from the
    lower bound of epsilon, 1/(k - 1). Box's conservative epsilon is no
    longer widely used. Instead, the Greenhouse-Geisser's epsilon
    represents its maximum-likelihood estimate.

      Syntax: function epsLB(y,df1)

      Inputs:
         y   = Input matrix can be a data matrix
               (size n-data x k-treatments)
         df1 = degrees of freedom of treatment

      Output:
         Box's conservative epsilon value.

    See docstring for epsGG() for information on formatting X.

    Reference:
      Box, G.E.P. (1954), Some theorems on quadratic forms applied in
          the study of analysis of variance problems, II. Effects of
          inequality of variance and of correlation between errors in
          the two-way classification. Annals of Mathematical Statistics.
          25:484-498.
      Trujillo-Ortiz, A., R. Hernandez-Walls, A. Castro-Perez and K.
          Barba-Rojo. (2006). epsGG:Greenhouse-Geisser epsilon. A MATLAB
          file. [WWW document].
          http://www.mathworks.com/matlabcentral/fileexchange
          /loadFile.do?objectId=12839
    """
    if df1 == 1. : return 1.

    k = shape(y,0)  # number of treatments
    box = 1./(k-1.) # Box's conservative epsilon estimation

    if box*df1 < 1. : box = 1. / df1

    return box

def windsor(X, percent):
    """
    given numpy array X returns the Windsorized trimmed samples, in
    which the trimmed values are replaced by the most extreme value
    remaining in the tail. percent should be less than 1.

    Example:

      X = array([ 3,  7, 12, 15, 17, 17, 18, 19, 19, 19,
                 20, 22, 24, 26, 30, 32, 32, 33, 36, 50])

      windsor(X, .10)

      array([12, 12, 12, 15, 17, 17, 18, 19, 19, 19,
             20, 22, 24, 26, 30, 32, 32, 33, 33, 33])
    """
    X=array(X)
    X_copy=sorted(copy(X))
    num2exc=int(round(len(X_copy)*percent))

    if num2exc==0:
        minval=X_copy[0]
        maxval=X_copy[-1]
    else:
        minval=X_copy[ num2exc]
        maxval=X_copy[-(num2exc+1)]

    X[where(X<minval)]=minval
    X[where(X>maxval)]=maxval

    return X,num2exc*2.

##X=array([3,7,19,19,20,22,24,12,15,17,32,32,33,36,17,18,19,26,30,50])
##print windsor(X,.1)

class Anova(OrderedDict):
    def __init__(self, *args, **kwds):


        if kwds.has_key('df'):
            self.df = kwds['df']
        else:
            self.df = {}

        if kwds.has_key('wfactors'):
            self.wfactors = kwds['wfactors']
        else:
            self.wfactors = []

        if kwds.has_key('bfactors'):
            self.bfactors = kwds['bfactors']
        else:
            self.bfactors = []

        if kwds.has_key('alpha'):
            self.alpha = kwds['alpha']
        else:
            self.alpha = 0.05

        if kwds.has_key('measure'):
            self.measure = kwds['measure']
        else:
            self.measure = ''

        if kwds.has_key('dv'):
            self.dv = kwds['dv']
        else:
            self.dv = None

        if kwds.has_key('sub'):
            self.sub = kwds['sub']
        else:
            self.sub = 'SUBJECT'

        if kwds.has_key('transform'):
            self.transform = kwds['transform']
        else:
            self.transform = ''

        if len(args) == 1:
            super(Anova, self).__init__(args[0])
        else:
            super(Anova, self).__init__()

    def run(self, dataframe, dv, wfactors=None, bfactors=None,
                 sub='SUBJECT', measure='', transform='', alpha=0.05):
        """
        Fancy linear algebra is adapted from a matlab script by R.Henson,
        17/3/03
        rik.henson@mrc-cbu.cam.ac.uk
        http://www.mrc-cbu.cam.ac.uk/people/rik.henson/personal/repanova.m

        """
        if wfactors == None:
            wfactors = []

        if bfactors == None:
            bfactors = []

        ## Intialize self variables

        # holds a reference to a pyvttbl.DataFrame object
        self.df=dataframe

        # a string label/key to the dependent variable data in self.df
        self.dv=dv

        # a list of within-participant factors
        self.wfactors=wfactors

        # a list of between-participant factors
        self.bfactors=bfactors

        # a string label/key to the participant/case data in self.df
        self.sub=sub

        # a descriptive title for the output
        self.measure=measure

        self.plots=[]

        # a list of all the factors
        factors=wfactors+bfactors
        self.dftrim=0.

        # check to see if a data should be transformed
        if   transform in ['log','log10']:
            self.transform=numpy.log10
            tstr='LOG_'

        elif transform in ['reciprocal','inverse']:
            self.transform=lambda X:1./X
            tstr='RECIPROCAL_'

        elif transform in ['square-root','sqrt']:
            self.transform=numpy.sqrt
            tstr='SQRT_'

        elif transform in ['arcsine','arcsin'] :
            self.transform=numpy.arcsin
            tstr='ARCSIN_'

        elif transform in ['windsor01']:
            self.transform=lambda X: windsor(X,.01)
            tstr='WINDSOR01_'

        elif transform in ['windsor05']:
            self.transform=lambda X: windsor(X,.05)
            tstr='WINDSOR05_'

        elif transform in ['windsor10']:
            self.transform=lambda X: windsor(X,.10)
            tstr='WINDSOR10_'

        if transform!='':
            if 'windsor' in transform:
                self.df[tstr+self.dv], self.dftrim = \
                                       self.transform(self.df[self.dv])
                print('%i degrees of freedom lost from trim'%int(self.dftrim))
            else:
                self.df[tstr+self.dv] = self.transform(self.df[self.dv])

            self.dv = tstr+self.dv

        # self.pt is a PyvtTbl (list of lists)
        #     rows = replications (eg subjects)
        #     columns = conditions
        self.pt=self.df.pivot(self.dv,rows=[self.sub],cols=factors)

        # self.pt_asarray is the same data as self.pt except as a numpy array
        self.pt_asarray = array(self.pt, dtype=numpy.float64)

##        print('%i NaN values found.'%len(self.pt_asarray[isnan(self.pt_asarray)]))

        # Replace NaN values with mean of dv
        self.pt_asarray[isnan(self.pt_asarray)]=mean(self.df[self.dv])

        # A vector with as many entries as factors, each entry being
        # the number of levels for that factor
        #
        # Data matrix self.pt_asarray must have as many columns (conditions)
        # as the product of the elements of the factor matrix D
        #
        # First factor rotates slowest; last factor fastest
        self.D=[len(self.df.conditions[f]) for f in factors]

        if len(wfactors)!=0 and len(bfactors)==0:
            self._within()

        if len(wfactors)==0 and len(bfactors)!=0:
            self._between()

        if len(wfactors)!=0 and len(bfactors)!=0:
            self._mixed()

    def _between(self):
        factors=self.bfactors
        pt_asarray = self.pt_asarray
        D = self.D
        df = self.df

        Nf = len(D)      # Number of factors
        Nd = prod(D)     # Total number of conditions
        Ne = 2**Nf - 1   # Number of effects
        Nr,Nn = shape(pt_asarray) # Number of replications (eg subjects)
                                  # x treatments
        conditions = self.df.conditions

        if shape(pt_asarray,1) != Nd:
            raise Exception('data has %d conditions; design only %d',
                            shape(pt_asarray,1),Nd)

        sc, sy = {}, {}
        for f in xrange(1,Nf+1):
            # create main effect/interaction component contrasts
            sc[(f,1)] = ones((D[f-1],1))
            sc[(f,2)] = detrend(eye(D[f-1]),type='constant')

            # create main effect/interaction components for means
            sy[(f,1)] = ones((D[f-1],1))/D[f-1]
            sy[(f,2)] = eye(D[f-1])

        # Loop through effects
        # Do fancy calculations
        # Record the results of the important fancy calcuations
        for e in xrange(1,Ne+1):

            # code effects so we can build contrasts
            cw = self._num2binvec(e,Nf)
            efs = asarray(factors)[Nf-1-where(asarray(cw)==2.)[0][::-1]]
            r = {}

            # create full contrasts
            c = sc[(1,cw[Nf-1])];
            for f in xrange(2,Nf+1):
                c = kron(c, sc[(f,cw[Nf-f])])

            Nc = shape(c,1) # Number of conditions in effect
            No = Nd/Nc*1.   # Number of observations per condition in effect

            # project data to contrast sub-space
            y  = dot(pt_asarray,c)
            nc = shape(y,1)

            # calculate component means
            cy = sy[(1, cw[Nf-1])]
            for f in xrange(2,Nf+1):
                cy = kron(cy, sy[(f,cw[Nf-f])] )

            r['y2'] = mean(dot(pt_asarray,cy),0)

            # calculate df, ss, and mss
            b = mean(y,0)
            r['df'] = float(matrix_rank(c))
            r['ss'] = nsum(y*b.T)*Nc
            r['mss'] = r['ss']/r['df']

            self[tuple(efs)]=r

        ss_total = nsum((pt_asarray-mean(pt_asarray))**2)
        ss_error = ss_total
        dfe=len(self.df[self.dv])-1.-self.dftrim

        for i in xrange(1,len(factors)+1):
            for efs in _xunique_combinations(factors, i):
                ss_error -= self[tuple(efs)]['ss']
                dfe -= self[tuple(efs)]['df']

        # calculate F, p, and standard errors
        for i in xrange(1,len(factors)+1):
            for efs in _xunique_combinations(factors, i):

                r = self[tuple(efs)]

                r['sse'] = ss_error
                r['dfe'] = dfe
                r['mse'] = ss_error / dfe
                r['F'] = r['mss']/r['mse']
                r['p'] = fprob(r['df'],r['dfe'],r['F'])

                # calculate Generalized eta effect size
                r['eta'] = r['ss']/(r['ss']+r['sse'])

                # calculate observations per cell
                r['obs']  = len(conditions[self.sub])
                r['obs'] /= prod([len(conditions[f])*1. for f in efs])

                # calculate Loftus and Masson standard errors
                r['critT'] = abs(qt(.05/2.,r['dfe']))
                r['se'] = sqrt(r['mse']/r['obs'])*r['critT']/1.96
                r['ci'] = sqrt(r['mse']/r['obs'])*r['critT']

                # calculate non-centrality and observed power
                dstd = std(self.df[self.dv])
                dmu  = mean(self.df[self.dv])

                r['lambda'] = noncentrality_par(r['obs'],r['y2'],dmu,dstd**2.)
                r['power'] = observed_power( r['df'], r['dfe'], r['lambda'] )

                # record to dict
                self[tuple(efs)] = r

    def _mixed(self):
        ## Programmer note:
        ## The order of in which things happen is extremely critical.
        ## Use extreme caution when modifying this function.

        bfactors = self.bfactors
        wfactors = self.wfactors
        factors = wfactors+bfactors
        pt_asarray = self.pt_asarray
        D = self.D
        df = self.df
        conditions=self.df.conditions

        Nf = len(D)      # Number of factors
        Nd = prod(D)     # Total number of conditions
        Ne = 2**Nf - 1   # Number of effects
        Nr,Nn = shape(pt_asarray) # Number of replications (eg subjects)
                                  # x treatments

        if shape(pt_asarray,1) != Nd:
            raise Exception('data has %d conditions; design only %d',
                            shape(pt_asarray,1),Nd)

        sc,sy = {},{}
        for f in xrange(1,Nf+1):
            # create main effect/interaction component contrasts
            sc[(f,1)] = ones((D[f-1],1))
            sc[(f,2)] = detrend(eye(D[f-1]),type='constant')

            # create main effect/interaction components for means
            sy[(f,1)] = ones((D[f-1],1))/D[f-1]
            sy[(f,2)] = eye(D[f-1])

        # Loop through effects
        # Do fancy calculations
        # Record the results of the important fancy calcuations
        for e in xrange(1,Ne+1):

            # code effects so we can build contrasts
            cw = self._num2binvec(e,Nf)
            efs = asarray(factors)[Nf-1-where(asarray(cw)==2.)[0][::-1]]
            r={}

            # create full contrasts
            c = sc[(1,cw[Nf-1])];
            for f in xrange(2,Nf+1):
                c = kron(c, sc[(f,cw[Nf-f])])

            Nc = shape(c,1) # Number of conditions in effect
            No = Nd/Nc*1.   # Number of observations per condition in effect

            # project data to contrast sub-space
            y = dot(pt_asarray,c)

            # calculate component means
            cy = sy[(1, cw[Nf-1])]
            for f in xrange(2,Nf+1):
                cy = kron(cy, sy[(f,cw[Nf-f])] )

            r['y2'] = mean(dot(pt_asarray,cy),0)

            # df for effect
            r['df'] =  prod([len(conditions[f])-1. for f in efs])

            # calculate Greenhouse-Geisser & Huynh-Feldt epsilons
            r['eps_gg'] = epsGG(y, r['df'])
            r['eps_hf'] = epsHF(y, r['df'])
            r['eps_lb'] = epsLB(y, r['df'])

            # calculate ss, sse, mse, mss, F, p, and standard errors
            b = mean(y,0)

            # Sphericity assumed
            r['ss']  = nsum(y*b.T)
            r['ss'] /= No/(prod([len(conditions[f]) for f in bfactors])*1.)
            r['mss'] = r['ss']/r['df']

            self[tuple(efs)] = r

        # calculate sse, dfe, and mse for between subjects effects
        dfe_sum   = 0. # for df trim
        ss_total  = nsum((pt_asarray-mean(pt_asarray))**2)
        sub_means = df.pivot(self.dv, cols=[self.sub])
        sub_means = array(sub_means, dtype=numpy.float64)

        ss_bsub  =  nsum((sub_means-mean(pt_asarray))**2)
        ss_bsub *= (prod([len(conditions[f]) for f in wfactors])*1.)

        df_b  = prod([len(conditions[f]) for f in bfactors])
        df_b *= Nr/prod([len(conditions[f]) for f in bfactors])
        df_b -= 1.

        dfe_b  =  prod([len(conditions[f]) for f in bfactors])
        dfe_b *= (Nr/prod([len(conditions[f]) for f in bfactors])-1.)

        dfe_sum += dfe_b

        sse_b = ss_bsub
        self.befs = [] # list of between subjects effects
        for i in xrange(1,len(bfactors)+1):
            for efs in _xunique_combinations(bfactors, i):
                sse_b -= self[tuple(efs)]['ss']
                self.befs.append(efs)

        mse_b=sse_b/dfe_b

        # store calculations to reuslts dictionary
        self[(self.sub,)] = {'ss'  : ss_bsub,
                             'sse' : sse_b,
                             'mse' : mse_b,
                             'df'  : df_b,
                             'dfe' : dfe_b}
        self[('TOTAL',)] = {'ss' : ss_total,
                            'df' : Nr/prod([len(conditions[f])*1.
                                              for f in bfactors])*Nd-1}
        self[('WITHIN',)] = {'ss' : ss_total-ss_bsub,
                             'df' : self[('TOTAL',)]['df']-df_b}

        ss_err_tot=0.

        # calculate ss, df, and mss for within subjects effects
        self.wefs=[]
        for i in xrange(1, len(wfactors)+1):
            for efs in _xunique_combinations(wfactors, i):

                self.wefs.append(efs)
                efs+=[self.sub]

                r={}
                tmp=array(df.pivot(self.dv, cols=efs), dtype=numpy.float64)
                r['ss']  = nsum((tmp-mean(pt_asarray))**2)
                r['ss'] *= prod([len(conditions[f]) for f in wfactors
                                 if f not in efs])

                for j in xrange(1, len(efs+bfactors)+1):
                    for efs2 in _xunique_combinations(efs+bfactors, j):

                        if efs2 not in self.befs and efs2!=efs:
                            if self.sub in efs2 and \
                            len(Set(efs2).intersection(Set(bfactors)))>0:
                                pass

                            else:
                                r['ss'] -= self[tuple(efs2)]['ss']

                ss_err_tot+=r['ss']

                r['df']  = prod([len(conditions[f]) for f in bfactors])
                r['df'] *= prod([len(conditions[f])-1. for f in efs \
                                 if f in wfactors])
                r['df'] *= Nr/prod([len(conditions[f])*1. for f in bfactors])-1.
                dfe_sum += r['df']

                r['mss'] = r['ss']/r['df']

                self[tuple(efs)]=r

        # trim df for between subjects effects
        self[(self.sub,)]['dfe'] = dfe_b - (dfe_b/dfe_sum) * self.dftrim
        ss_err_tot+=mse_b*dfe_b

        # calculate mse, dfe, sse, F, p, and standard errors
        # between subjects effects
        for i in xrange(1,len(bfactors)+1):
            for efs in _xunique_combinations(bfactors, i):
                r = self[tuple(efs)]

                r['sse'] = mse_b*dfe_b
                r['dfe'] = self[(self.sub,)]['dfe']
                r['mse'] = r['sse']/r['dfe']
                r['F'] = r['mss']/r['mse']
                r['p'] = fprob(r['df'],r['dfe'],r['F'])

                # calculate Generalized eta effect size
                r['eta'] = r['ss']/(r['ss']+ss_err_tot)

                # calculate observations per cell
                r['obs'] = len(conditions[self.sub])
                r['obs']/= prod([len(conditions[f])*1. for f in efs])

                # calculate Loftus and Masson standard errors
                r['critT'] = abs(qt(.05/2.,r['dfe']))
                r['se'] = sqrt(r['mse']/r['obs'])*r['critT']/1.96
                r['ci'] = sqrt(r['mse']/r['obs'])*r['critT']

                # calculate non-centrality and observed power
                dstd=std(self.df[self.dv])
                dmu  = mean(self.df[self.dv])

                r['lambda'] = noncentrality_par(r['obs'],r['y2'],dmu,dstd**2.)
                r['power'] = observed_power( r['df'], r['dfe'], r['lambda'] )

                # record to dict
                self[tuple(efs)] = r

        # calculate mse, dfe, sse, F, p, and standard errors
        # within subjects effects
        for i in xrange(1,len(factors)+1):
            for efs in _xunique_combinations(factors, i):

                if efs not in self.befs:
                    r=self[tuple(efs)]
                    r2=self[tuple([f for f in efs if f not in bfactors] +
                                  [self.sub])]

                    r['dfe'] = r2['df'] - (r2['df']/dfe_sum) * self.dftrim
                    r['sse'] = r2['ss']
                    r['mse'] = r2['mss']
                    r['F'] = r['mss']/r['mse']
                    r['p'] = fprob(r['df'],r['dfe'],r['F'])

                    # calculate Generalized eta effect size
                    r['eta'] = r['ss']/(r['ss']+ss_err_tot)

                    # calculate observations per cell
                    r['obs'] = Nr/prod([len(conditions[f])*1. for f in bfactors])
                    r['obs'] *= prod([len(conditions[f])*1. for f in factors])
                    r['obs'] /= prod([len(conditions[f])*1. for f in efs])

                    # calculate Loftus and Masson standard errors
                    r['critT'] = abs(qt(.05/2.,r['dfe']))
                    r['se'] = sqrt(r['mse']/r['obs'])*r['critT']/1.96
                    r['ci'] = sqrt(r['mse']/r['obs'])*r['critT']

                    # calculate non-centrality and observed power
                    dave=array(df.pivot(self.dv,cols=efs),
                               dtype=numpy.float64).flatten()
                    dstd=std(self.df[self.dv])
                    dmu  = mean(self.df[self.dv])

                    r['lambda']=noncentrality_par(r['obs'],dave,dmu,dstd**2.)
                    r['power']=observed_power( r['df'], r['dfe'], r['lambda'] )

                    # Greenhouse-Geisser, Huynh-Feldt, Lower-Bound
                    for x in ['_gg','_hf','_lb']:
                        r['df%s'%x] = r['df']*r['eps%s'%x]
                        r['dfe%s'%x] = r['dfe']*r['eps%s'%x]
                        r['mss%s'%x] = r['ss']/r['df%s'%x]
                        r['mse%s'%x] = r['sse']/r['dfe%s'%x]
                        r['F%s'%x] = r['mss%s'%x]/r['mse%s'%x]
                        r['p%s'%x] = fprob(r['df%s'%x],
                                               r['dfe%s'%x],
                                               r['F%s'%x])
                        r['obs%s'%x] = r['obs']
                        r['critT%s'%x] = abs(qt(.05/2.,r['dfe%s'%x]))
                        r['se%s'%x] = sqrt(r['mse']/r['obs%s'%x])*\
                                         r['critT%s'%x]/1.96
                        r['ci%s'%x] = sqrt(r['mse']/r['obs%s'%x])*\
                                         r['critT%s'%x]

                        # calculate non-centrality and observed power
                        r['lambda%s'%x] = r['lambda']
                        r['power%s'%x] = observed_power( r['df%s'%x],
                                                       r['df%s'%x],
                                                       r['lambda'] )

                    # record to dict
                    self[tuple(efs)]=r

    def _within(self):
        factors = self.wfactors
        pt_asarray = self.pt_asarray
        D = self.D
        df = self.df
        conditions=self.df.conditions

        Nf = len(D)      # Number of factors
        Nd = prod(D)     # Total number of conditions
        Ne = 2**Nf - 1   # Number of effects
        Nr,Nn = shape(pt_asarray) # Number of replications (eg subjects)
                                  # x treatments

        if shape(pt_asarray,1) != Nd:
            raise Exception('data has %d conditions; design only %d',
                            shape(pt_asarray,1),Nd)

        sc,sy = {},{}
        for f in xrange(1,Nf+1):
            # create main effect/interaction component contrasts
            sc[(f,1)] = ones((D[f-1],1))
            sc[(f,2)] = detrend(eye(D[f-1]),type='constant')

            # create main effect/interaction components for means
            sy[(f,1)] = ones((D[f-1],1))/D[f-1]
            sy[(f,2)] = eye(D[f-1])

        # Calulate dfs and dfes
        dfe_sum=0.
        for i in xrange(1,len(factors)+1):
            for efs in _xunique_combinations(factors, i):
                r={}

                r['df']  = prod([len(conditions[f])-1 for f in factors if \
                                 f in efs])
                r['dfe'] = float(r['df']*(Nr-1.))
                dfe_sum  += r['dfe'] # for df trim

                self[tuple(efs)]=r

        # Loop through effects
        # Do fancy calculations
        # Record the results of the important fancy calcuations
        for e in xrange(1,Ne+1):
            # code effects so we can build contrasts
            cw = self._num2binvec(e,Nf)
            efs = asarray(factors)[Nf-1-where(asarray(cw)==2.)[0][::-1]]
            r=self[tuple(efs)] # unpack dictionary

            # create full contrasts
            c = sc[(1,cw[Nf-1])];
            for f in xrange(2,Nf+1):
                c = kron(c, sc[(f,cw[Nf-f])])

            Nc = shape(c,1) # Number of conditions in effect
            No = Nd/Nc*1.   # Number of observations per condition in effect

            # project data to contrast sub-space
            y  = dot(pt_asarray,c)
            nc = shape(y,1)

            # calculate component means
            cy = sy[(1, cw[Nf-1])]
            for f in xrange(2,Nf+1):
                cy = kron(cy, sy[(f,cw[Nf-f])] )

            r['y2'] = mean(dot(pt_asarray,cy),0)

            # calculate Greenhouse-Geisser & Huynh-Feldt epsilons
            r['eps_gg'] = epsGG(y, r['df'])
            r['eps_hf'] = epsHF(y, r['df'])
            r['eps_lb'] = epsLB(y, r['df'])

            # calculate ss, sse, mse, mss, F, p, and standard errors
            b = mean(y,0)

            # Sphericity assumed
            r['dfe'] -= (r['dfe']/dfe_sum) * self.dftrim
            r['ss']   =  nsum(y*b.T)
            r['mse']  = (nsum(diag(dot(y.T,y)))-r['ss'])/r['dfe']
            r['sse']  =  r['dfe']*r['mse']

            r['ss'] /=  No
            r['mss'] =  r['ss']/r['df']
            r['sse']/=  No
            r['mse'] =  r['sse']/r['dfe']

            r['F'] =  r['mss']/r['mse']
            r['p'] =  fprob(r['df'],r['dfe'],r['F'])

            # calculate observations per cell
            r['obs'] =  Nr*No

            # calculate Loftus and Masson standard errors
            r['critT'] = abs(qt(.05/2.,r['dfe']))
            r['se'] = sqrt(r['mse']/r['obs'])*r['critT']/1.96
            r['ci'] = sqrt(r['mse']/r['obs'])*r['critT']

            # calculate non-centrality and observed power
            dstd = std(self.df[self.dv])
            dmu  = mean(self.df[self.dv])

            r['lambda'] = noncentrality_par(r['obs'],r['y2'],dmu,dstd**2.)
            r['power'] = observed_power(r['df'], r['dfe'], r['lambda'])

            # Greenhouse-Geisser, Huynh-Feldt, Lower-Bound
            for x in ['_gg','_hf','_lb']:
                r['df%s'%x]  = r['df']*r['eps%s'%x]
                r['dfe%s'%x] = r['dfe']*r['eps%s'%x]
                r['mss%s'%x] = r['ss']/r['df%s'%x]
                r['mse%s'%x] = r['sse']/r['dfe%s'%x]
                r['F%s'%x] = r['mss%s'%x]/r['mse%s'%x]
                r['p%s'%x] = fprob(r['df%s'%x],r['dfe%s'%x],r['F%s'%x])
                r['obs%s'%x] = Nr*No
                r['critT%s'%x] = abs(qt(.05/2.,r['dfe%s'%x]))
                r['se%s'%x] = sqrt(r['mse']/r['obs%s'%x])*r['critT%s'%x]/1.96
                r['ci%s'%x] = sqrt(r['mse']/r['obs%s'%x])*r['critT%s'%x]

                # calculate non-centrality and observed power
                r['lambda%s'%x]=r['lambda']
                r['power%s'%x]=observed_power( r['df%s'%x],
                                               r['df%s'%x],
                                               r['lambda'] )

            # record to dict
            self[tuple(efs)]=r

        # Calculate parameters need to calculate effect size estimates
        sub_means   =  mean(pt_asarray, axis=1)
        ss_subject  =  nsum((sub_means-mean(pt_asarray))**2)
        ss_subject *= (prod([len(conditions[f]) for f in factors])*1.)
        ss_err_tot  =  sum([r['sse'] for r in self.values()])

        # Loop through and calculate Generalize eta effect sizes
        for efs,r in self.items():
            r['eta']   = r['ss']/(ss_subject + ss_err_tot)
            self[tuple(efs)]=r

    def _num2binvec(self,d,p=0):
        """Sub-function to code all main effects/interactions"""
        d,p=float(d),float(p)
        d=abs(round(d))

        if d==0.:
            b=0.
        else:
            b=[]
            while d>0.:
                b.insert(0,float(rem(d,2.)))
                d=floor(d/2.)

        return list(array(list(zeros((p-len(b))))+b)+1.)

    def __html__(self):
        if self.measure == '':
            title  = '%s ~'%self.dv
        else:
            title  = '%s of %s ~'%(measure, self.dv)

        factors = self.wfactors + self.bfactors
        title += ''.join([' %s *'%f for f in factors])[:-2]
        html=SimpleHTML(title)

        if len(self.wfactors)!=0 and len(self.bfactors)==0:
            self._within_html(html)

        if len(self.wfactors)==0 and len(self.bfactors)!=0:
            self._between_html(html)

        if len(self.wfactors)!=0 and len(self.bfactors)!=0:
            self._mixed_html(html)

        self._summary_html(html, factors)

        return str(html)

    def output2html(self, fname):
        with open(fname, 'wb') as f:
            f.write(self.__html__())

    def _between_html(self, html):
        factors = self.bfactors
        D = self.D

        html.add(br(2))
        txt='Tests of Between-Subjects Effects'
        html.add(h(a(txt,name='1_'+md5sum(txt)),2,'center'))

        # Write ANOVA results
        if self.measure=='':
            html.add(h('Measure: %s'%self.dv))
        else:
            html.add(h('Measure: %s of %s'%(self.dv,self.measure)))

        thead='Source,Type III Sum of Squares,df,MS,F,Sig.,'\
              '&#951;<sup>2</sup><sub><sub>G</sub></sub>,Obs.,'\
              'SE of x&#772;,&#177;95% CI,&lambda;,Obs. Power'.split(',')
        tbodys=[[]]

        for i in xrange(1,len(factors)+1):
            for efs in _xunique_combinations(factors, i):
                r=self[tuple(efs)]
                src=''.join(['%s * '%f for f in efs])[:-3]
                tbodys[-1].append(f2s([src,r['ss'],r['df'],
                                       r['mss'],r['F'],r['p'],
                                       r['eta'],r['obs'],r['se'],
                                       r['ci'],r['lambda'],r['power']]))

        tbodys[-1].append(f2s(['Error',self[(factors[0],)]['sse'],
                                       self[(factors[0],)]['dfe'],
                                       self[(factors[0],)]['mse'],
                                       '','','','','','','','']))

        ss_total=nsum((self.df[self.dv]-mean(self.df[self.dv]))**2)
        df_total=len(self.df[self.dv])-1-self.dftrim

        tbodys.append([f2s(['Total',ss_total,df_total,
                       '','','','','','','','',''])])

        html.add(table(tbodys, thead))

    def _mixed_html(self, html):
        bfactors=self.bfactors
        wfactors=self.wfactors
        factors=wfactors+bfactors
        D = self.D
        df = self.df
        conditions=self.df.conditions

        # Write Tests of Between-Subjects Effects
        html.add(br(2))
        txt='Tests of Between-Subjects Effects'
        html.add(h(a(txt,name='1_'+md5sum(txt)),2,'center'))

        if self.measure=='':
            html.add(h('Measure: %s'%self.dv))
        else:
            html.add(h('Measure: %s of %s'%(self.dv,self.measure)))

        thead='Source,Type III Sum of Squares,df,MS,F,Sig.,'\
               '&#951;<sup>2</sup><sub><sub>G</sub></sub>,Obs.,'\
               'SE of x&#772;,&#177;95% CI,&lambda;,Obs. Power'.split(',')
        tbodys=[]

        tbodys.append([f2s(['Between Subjects',
                            self[('SUBJECT',)]['ss'],
                            self[('SUBJECT',)]['df'],
                            '','','','','','','','',''])])

        tbodys.append([])

        for i in xrange(1,len(bfactors)+1):
            for efs in _xunique_combinations(bfactors, i):
                r=self[tuple(efs)]
                src='&nbsp;'*9+''.join(['%s * '%f for f in efs])[:-3]
                tbodys[-1].append(f2s([src,r['ss'],r['df'],r['mss'],
                                       r['F'],r['p'],r['eta'],r['obs'],
                                       r['se'],r['ci'],r['lambda'],r['power']]))

        tbodys.append([f2s(['&nbsp;'*9+'Error',
                            self[('SUBJECT',)]['sse'],
                            self[('SUBJECT',)]['dfe'],
                            self[('SUBJECT',)]['mse'],
                            '','','','','','','',''])])

        html.add(table(tbodys, thead))

        # Write Tests of Within-Subjects Effects
        html.add(br(2))
        txt='Tests of Within-Subjects Effects'
        html.add(h(a(txt,name='1_'+md5sum(txt)),2,'center'))

        if self.measure=='':
            html.add(h('Measure: %s'%self.dv))
        else:
            html.add(h('Measure: %s of %s'%(self.dv,self.measure)))
        thead='Source,,Type III Sum of Squares,&#949;,df,MS,F,Sig.,'\
               '&#951;<sup>2</sup><sub><sub>G</sub></sub>,Obs.,'\
               'SE of x&#772;,&#177;95% CI,&lambda;,Obs. Power'.split(',')
        tbodys=[]

        defs=[]
        for i in xrange(1,len(wfactors)+1):
            for efs in _xunique_combinations(wfactors, i):
                defs.append(efs)

                tbodys.append([])
                r=self[tuple(efs)]
                src=''.join(['%s * '%f for f in efs])[:-3]
                tbodys[-1].append(f2s([src,'Sphericity Assumed',
                   r['ss'],' - ',r['df'],r['mss'],r['F'],
                   r['p'],r['eta'],r['obs'],r['se'],
                   r['ci'], r['lambda'],r['power']]))
                tbodys[-1].append(f2s(['', 'Greenhouse-Geisser',
                   r['ss'],r['eps_gg'],r['df_gg'],r['mss_gg'],r['F_gg'],
                   r['p_gg'],r['eta'],r['obs_gg'],r['se_gg'],r['ci_gg'],
                   r['lambda_gg'],r['power_gg']]))
                tbodys[-1].append(f2s(['', 'Huynh-Feldt',
                   r['ss'],r['eps_hf'],r['df_hf'],r['mss_hf'],r['F_hf'],
                   r['p_hf'],r['eta'],r['obs_hf'],r['se_hf'],r['ci_hf'],
                   r['lambda_hf'],r['power_hf']]))
                tbodys[-1].append(f2s(['', 'Box',
                   r['ss'],r['eps_lb'],r['df_lb'],r['mss_lb'],r['F_lb'],
                   r['p_lb'],r['eta'],r['obs_lb'],r['se_lb'],r['ci_lb'],
                   r['lambda_lb'],r['power_lb']]))

                for i in xrange(1,len(factors)+1):
                    for efs2 in _xunique_combinations(factors, i):
                        if efs2 not in self.befs and \
                           efs2 not in defs and \
                           efs2 not in self.wefs \
                           and len(Set(efs2).difference(Set(efs+bfactors)))==0:
                            defs.append(efs2)

                            tbodys.append([])
                            r=self[tuple(efs2)]
                            src=''.join(['%s * '%f for f in efs2])[:-3]
                            tbodys[-1].append(f2s([src,'Sphericity Assumed',
                               r['ss'],' - ',r['df'],r['mss'],r['F'],r['p'],
                               r['eta'],r['obs'],r['se'],
                               r['ci'],r['lambda'],r['power']]))
                            tbodys[-1].append(f2s(['', 'Greenhouse-Geisser',
                               r['ss'],r['eps_gg'],r['df_gg'],r['mss_gg'],
                               r['F_gg'],r['p_gg'],r['eta'],r['obs_gg'],
                               r['se_gg'],r['ci_gg'],
                               r['lambda_gg'],r['power_gg']]))
                            tbodys[-1].append(f2s(['', 'Huynh-Feldt',
                               r['ss'],r['eps_hf'],r['df_hf'],r['mss_hf'],
                               r['F_hf'],r['p_hf'],r['eta'],r['obs_hf'],
                               r['se_hf'],r['ci_hf'],
                               r['lambda_hf'],r['power_hf']]))
                            tbodys[-1].append(f2s(['', 'Box',
                               r['ss'],r['eps_lb'],r['df_lb'],r['mss_lb'],
                               r['F_lb'],r['p_lb'],r['eta'],r['obs_lb'],
                               r['se_lb'],r['ci_lb'],
                               r['lambda_lb'],r['power_lb']]))

                tbodys.append([])
                src='Error(%s)'%''.join(['%s * '%f for f in efs if
                                         f not in bfactors])[:-3]
                tbodys[-1].append(f2s([src,'Sphericity Assumed',
                   r['sse'],' - ',r['dfe'],r['mse'],
                   '','','','','','','','']))
                tbodys[-1].append(f2s(['', 'Greenhouse-Geisser',
                   r['sse'],r['eps_gg'],r['dfe_gg'],r['mse_gg'],
                   '','','','','','','','']))
                tbodys[-1].append(f2s(['', 'Huynh-Feldt',
                   r['sse'],r['eps_hf'],r['dfe_hf'],r['mse_hf'],
                   '','','','','','','','']))
                tbodys[-1].append(f2s(['', 'Box',
                   r['sse'],r['eps_lb'],r['dfe_lb'],r['mse_lb'],
                   '','','','','','','','']))

        html.add(table(tbodys, thead))

    def _within_html(self, html):
        factors=self.wfactors

        html.add(br(2))
        txt='Tests of Within-Subjects Effects'
        html.add(h(a(txt,name='1_'+md5sum(txt)),2,'center'))

        # Write ANOVA
        if self.measure=='':
            html.add(h('Measure: %s'%self.dv))
        else:
            html.add(h('Measure: %s of %s'%(self.dv,self.measure)))
        thead='Source,,Type III Sum of Squares,&#949;,df,MS,F,Sig.,'\
               '&#951;<sup>2</sup><sub><sub>G</sub></sub>,Obs.,'\
               'SE of x&#772;,&#177;95% CI,&lambda;,Obs. Power'.split(',')
        tbodys=[]

        for i in xrange(1,len(factors)+1):
            for efs in _xunique_combinations(factors, i):
                tbodys.append([])
                r=self[tuple(efs)]
                src=''.join(['%s * '%f for f in efs])[:-3]
                tbodys[-1].append(f2s([src,'Sphericity Assumed',
                   r['ss'],' - ',r['df'],r['mss'],r['F'],r['p'],
                   r['eta'],r['obs'],r['se'],
                   r['ci'],r['lambda'],r['power']]))
                tbodys[-1].append(f2s(['', 'Greenhouse-Geisser',
                   r['ss'],r['eps_gg'],r['df_gg'],r['mss_gg'],r['F_gg'],
                   r['p_gg'],r['eta'],r['obs_gg'],r['se_gg'],
                   r['ci_gg'],r['lambda_gg'],r['power_gg']]))
                tbodys[-1].append(f2s(['', 'Huynh-Feldt',
                   r['ss'],r['eps_hf'],r['df_hf'],r['mss_hf'],r['F_hf'],
                   r['p_hf'],r['eta'],r['obs_hf'],r['se_hf'],
                   r['ci_hf'],r['lambda_hf'],r['power_hf']]))
                tbodys[-1].append(f2s(['', 'Box',
                   r['ss'],r['eps_lb'],r['df_lb'],r['mss_lb'],r['F_lb'],
                   r['p_lb'],r['eta'],r['obs_lb'],r['se_lb'],
                   r['ci_lb'],r['lambda_lb'],r['power_lb']]))

                tbodys.append([])
                src='Error(%s)'%src
                tbodys[-1].append(f2s([src,'Sphericity Assumed',
                   r['sse'],' - ',r['dfe'],r['mse'],
                   '','','','','','','','']))
                tbodys[-1].append(f2s(['', 'Greenhouse-Geisser',
                   r['sse'],r['eps_gg'],r['dfe_gg'],r['mse_gg'],
                   '','','','','','','','']))
                tbodys[-1].append(f2s(['', 'Huynh-Feldt',
                   r['sse'],r['eps_hf'],r['dfe_hf'],r['mse_hf'],
                   '','','','','','','','']))
                tbodys[-1].append(f2s(['', 'Box',
                   r['sse'],r['eps_lb'],r['dfe_lb'],r['mse_lb'],
                   '','','','','','','','']))

        html.add(table(tbodys, thead))

    def _summary_html(self, html, factors):

        # Write Summary Means
        html.add(br(2))
        txt='Tables of Estimated Marginal Means'
        html.add(h(a(txt,name='1_'+md5sum(txt)),2,'center'))

        for i in xrange(1,len(factors)+1):
            for efs in _xunique_combinations(factors, i):
                html.add(br())
                txt='Estimated Marginal Means for ' + \
                     ''.join(['%s * '%f for f in efs])[:-3]
                html.add(h(a(txt,name='2_'+md5sum(txt))))

                ys=self.df.pivot(self.dv,rows=efs,aggregate='tolist')
                names=ys.rnames

                dave=array([   mean(y[0]) for y in ys ])
                dsem=array([ stderr(y[0]) for y in ys ])

                dlowr=dave-(dsem*1.96)
                dhghr=dave+(dsem*1.96)

                thead=efs+['Mean','Std. Error',
                           '95% Lower Bound',
                           '95% Upper Bound']
                tbodys=[[]]

                for i,name in enumerate(names):
                    cs=[c[1] for c in name]
                    tbodys[-1].append(f2s(cs+[dave[i],dsem[i],
                                              dlowr[i],dhghr[i]]))

                html.add(table(tbodys, thead))


    def __str__(self):
        if self.measure == '':
            title  = '%s ~'%self.dv
        else:
            title  = '%s of %s ~'%(measure, self.dv)

        factors = self.wfactors + self.bfactors
        title += ''.join([' %s *'%f for f in factors])[:-2]

        s = [title]
        if len(self.wfactors)!=0 and len(self.bfactors)==0:
            s.append(self._within_str())

        if len(self.wfactors)==0 and len(self.bfactors)!=0:
            s.append(self._between_str())

        if len(self.wfactors)!=0 and len(self.bfactors)!=0:
            s.append(self._mixed_str())

        s.append(self._summary_str(factors))
        return ''.join(s)

    def _between_str(self):
        factors = self.bfactors
        D = self.D

        s = ['\n\nTESTS OF BETWEEN-SUBJECTS EFFECTS\n\n']

        # Write ANOVA results
        if self.measure=='':
            s.append('Measure: %s\n'%self.dv)
        else:
            s.append('Measure: %s of %s\n'%(self.dv,self.measure))

        tt = TextTable(max_width=0)
        tt.set_cols_dtype(['t'] + ['a']*11)
        tt.set_cols_align(['l'] + ['r']*11)
        tt.set_deco(TextTable.HEADER | TextTable.FOOTER)
        tt.header('Source,Type III\nSS,df,MS,F,Sig.,et2_G,'
                  'Obs.,SE,95% CI,lambda,Obs.\nPower'.split(','))

        for i in xrange(1,len(factors)+1):
            for efs in _xunique_combinations(factors, i):
                r=self[tuple(efs)]
                src=''.join(['%s * '%f for f in efs])[:-3]
                tt.add_row([src,r['ss'],r['df'],
                            r['mss'],r['F'],r['p'],
                            r['eta'],r['obs'],r['se'],
                            r['ci'],r['lambda'],r['power']])

        tt.add_row(['Error',self[(factors[0],)]['sse'],
                   self[(factors[0],)]['dfe'],
                   self[(factors[0],)]['mse'],
                   '','','','','','','',''])

        ss_total = nsum((self.df[self.dv]-mean(self.df[self.dv]))**2)
        df_total = len(self.df[self.dv])-1-self.dftrim

        tt.footer(['Total',ss_total,df_total,
                   '','','','','','','','',''])

        s.append(tt.draw())
        return ''.join(s)

    def _mixed_str(self):
        bfactors=self.bfactors
        wfactors=self.wfactors
        factors=wfactors+bfactors
        D = self.D
        df = self.df
        conditions=self.df.conditions

        # Write Tests of Between-Subjects Effects

        s = ['\n\nTESTS OF BETWEEN-SUBJECTS EFFECTS\n\n']

        # Write ANOVA results
        if self.measure=='':
            s.append('Measure: %s\n'%self.dv)
        else:
            s.append('Measure: %s of %s\n'%(self.dv,self.measure))

        tt = TextTable(max_width=0)
        tt.set_cols_dtype(['t'] + ['a']*11)
        tt.set_cols_align(['l'] + ['r']*11)
        tt.set_deco(TextTable.HEADER | TextTable.FOOTER)
        tt.header('Source,Type III\nSS,df,MS,F,Sig.,et2_G,'
                  'Obs.,SE,95% CI,lambda,Obs.\nPower'.split(','))

        tt.add_row(['Between Subjects',
                    self[('SUBJECT',)]['ss'],
                    self[('SUBJECT',)]['df'],
                    '','','','','','','','',''])

        for i in xrange(1,len(bfactors)+1):
            for efs in _xunique_combinations(bfactors, i):
                r=self[tuple(efs)]
                src=''.join(['%s * '%f for f in efs])[:-3]
                tt.add_row([src,r['ss'],r['df'],
                            r['mss'],r['F'],r['p'],
                            r['eta'],r['obs'],r['se'],
                            r['ci'],r['lambda'],r['power']])

        tt.footer(['Error',
                   self[('SUBJECT',)]['sse'],
                   self[('SUBJECT',)]['dfe'],
                   self[('SUBJECT',)]['mse'],
                   '','','','','','','',''])
        s.append(tt.draw())


        # Write Tests of Within-Subjects Effects

        s.append('\n\nTESTS OF WITHIN SUBJECTS EFFECTS\n\n')

        # Write ANOVA
        if self.measure=='':
            s.append('Measure: %s\n'%self.dv)
        else:
            s.append('Measure: %s of %s\n'%(self.dv,self.measure))

        tt = TextTable(max_width=0)
        tt.set_cols_dtype(['t']*2 + ['a']*12)
        tt.set_cols_align(['l']*2 + ['r']*12)
        tt.set_deco(TextTable.HEADER | TextTable.HLINES)
        tt.header('Source,,Type III\nSS,eps,df,MS,F,Sig.,'
                  'et2_G,Obs.,'
                  'SE,95% CI,lambda,Obs.\nPower'.split(','))

        defs=[]
        for i in xrange(1,len(wfactors)+1):
            for efs in _xunique_combinations(wfactors, i):
                defs.append(efs)
                treatment = []
                r=self[tuple(efs)]
                src=' *\n'.join(efs)
                treatment.append([src,'Sphericity Assumed',
                   r['ss'],' - ',r['df'],r['mss'],r['F'],r['p'],
                   r['eta'],r['obs'],r['se'],
                   r['ci'],r['lambda'],r['power']])
                treatment.append(['', 'Greenhouse-Geisser',
                   r['ss'],r['eps_gg'],r['df_gg'],r['mss_gg'],r['F_gg'],
                   r['p_gg'],r['eta'],r['obs_gg'],r['se_gg'],
                   r['ci_gg'],r['lambda_gg'],r['power_gg']])
                treatment.append(['', 'Huynh-Feldt',
                   r['ss'],r['eps_hf'],r['df_hf'],r['mss_hf'],r['F_hf'],
                   r['p_hf'],r['eta'],r['obs_hf'],r['se_hf'],
                   r['ci_hf'],r['lambda_hf'],r['power_hf']])
                treatment.append(['', 'Box',
                   r['ss'],r['eps_lb'],r['df_lb'],r['mss_lb'],r['F_lb'],
                   r['p_lb'],r['eta'],r['obs_lb'],r['se_lb'],
                   r['ci_lb'],r['lambda_lb'],r['power_lb']])

                row = []
                for i in _xrange(14):
                    row.append('\n'.join(_str(treatment[j][i])
                                         for j in _xrange(4)))
                tt.add_row(row)

                for i in xrange(1,len(factors)+1):
                    for efs2 in _xunique_combinations(factors, i):
                        if efs2 not in self.befs and \
                           efs2 not in defs and \
                           efs2 not in self.wefs \
                           and len(Set(efs2).difference(Set(efs+bfactors)))==0:
                            defs.append(efs2)
                            treatment = []
                            r=self[tuple(efs2)]
                            src=''.join(['%s * '%f for f in efs2])[:-3]
                            treatment.append([src,'Sphericity Assumed',
                               r['ss'],' - ',r['df'],r['mss'],r['F'],r['p'],
                               r['eta'],r['obs'],r['se'],
                               r['ci'],r['lambda'],r['power']])
                            treatment.append(['', 'Greenhouse-Geisser',
                               r['ss'],r['eps_gg'],r['df_gg'],r['mss_gg'],
                               r['F_gg'],r['p_gg'],r['eta'],r['obs_gg'],
                               r['se_gg'],r['ci_gg'],
                               r['lambda_gg'],r['power_gg']])
                            treatment.append(['', 'Huynh-Feldt',
                               r['ss'],r['eps_hf'],r['df_hf'],r['mss_hf'],
                               r['F_hf'],r['p_hf'],r['eta'],r['obs_hf'],
                               r['se_hf'],r['ci_hf'],
                               r['lambda_hf'],r['power_hf']])
                            treatment.append(['', 'Box',
                               r['ss'],r['eps_lb'],r['df_lb'],r['mss_lb'],
                               r['F_lb'],r['p_lb'],r['eta'],r['obs_lb'],
                               r['se_lb'],r['ci_lb'],
                               r['lambda_lb'],r['power_lb']])

                            row = []
                            for i in _xrange(14):
                                row.append('\n'.join(_str(treatment[j][i])
                                                     for j in _xrange(4)))
                            tt.add_row(row)

                error = []

                src='Error(%s)'%' *\n'.join([f for f in efs if
                                             f not in bfactors])
                error.append([src,'Sphericity Assumed',
                   r['sse'],' - ',r['dfe'],r['mse'],
                   '','','','','','','',''])
                error.append(['', 'Greenhouse-Geisser',
                   r['sse'],r['eps_gg'],r['dfe_gg'],r['mse_gg'],
                   '','','','','','','',''])
                error.append(['', 'Huynh-Feldt',
                   r['sse'],r['eps_hf'],r['dfe_hf'],r['mse_hf'],
                   '','','','','','','',''])
                error.append(['', 'Box',
                   r['sse'],r['eps_lb'],r['dfe_lb'],r['mse_lb'],
                   '','','','','','','',''])

                row = []
                for i in _xrange(14):
                    row.append('\n'.join(_str(error[j][i])
                                         for j in _xrange(4)))
                tt.add_row(row)

        s.append(tt.draw())
        return ''.join(s)

    def _within_str(self):
        factors=self.wfactors

        s = ['\n\nTESTS OF WITHIN SUBJECTS EFFECTS\n\n']

        # Write ANOVA
        if self.measure=='':
            s.append('Measure: %s\n'%self.dv)
        else:
            s.append('Measure: %s of %s\n'%(self.dv,self.measure))

        tt = TextTable(max_width=0)
        tt.set_cols_dtype(['t']*2 + ['a']*12)
        tt.set_cols_align(['l']*2 + ['r']*12)
        tt.set_deco(TextTable.HEADER | TextTable.HLINES)
        tt.header('Source,,Type III\nSS,eps,df,MS,F,Sig.,'
                  'et2_G,Obs.,'
                  'SE,95% CI,lambda,Obs.\nPower'.split(','))

        for i in xrange(1,len(factors)+1):
            for efs in _xunique_combinations(factors, i):
                treatment = []
                r=self[tuple(efs)]
                src=' *\n'.join(efs)
                treatment.append([src,'Sphericity Assumed',
                   r['ss'],' - ',r['df'],r['mss'],r['F'],r['p'],
                   r['eta'],r['obs'],r['se'],
                   r['ci'],r['lambda'],r['power']])
                treatment.append(['', 'Greenhouse-Geisser',
                   r['ss'],r['eps_gg'],r['df_gg'],r['mss_gg'],r['F_gg'],
                   r['p_gg'],r['eta'],r['obs_gg'],r['se_gg'],
                   r['ci_gg'],r['lambda_gg'],r['power_gg']])
                treatment.append(['', 'Huynh-Feldt',
                   r['ss'],r['eps_hf'],r['df_hf'],r['mss_hf'],r['F_hf'],
                   r['p_hf'],r['eta'],r['obs_hf'],r['se_hf'],
                   r['ci_hf'],r['lambda_hf'],r['power_hf']])
                treatment.append(['', 'Box',
                   r['ss'],r['eps_lb'],r['df_lb'],r['mss_lb'],r['F_lb'],
                   r['p_lb'],r['eta'],r['obs_lb'],r['se_lb'],
                   r['ci_lb'],r['lambda_lb'],r['power_lb']])

                row = []
                for i in _xrange(14):
                    row.append('\n'.join(_str(treatment[j][i])
                                         for j in _xrange(4)))
                tt.add_row(row)

                error = []
                src='Error(%s)'%src
                error.append([src,'Sphericity Assumed',
                   r['sse'],' - ',r['dfe'],r['mse'],
                   '','','','','','','',''])
                error.append(['', 'Greenhouse-Geisser',
                   r['sse'],r['eps_gg'],r['dfe_gg'],r['mse_gg'],
                   '','','','','','','',''])
                error.append(['', 'Huynh-Feldt',
                   r['sse'],r['eps_hf'],r['dfe_hf'],r['mse_hf'],
                   '','','','','','','',''])
                error.append(['', 'Box',
                   r['sse'],r['eps_lb'],r['dfe_lb'],r['mse_lb'],
                   '','','','','','','',''])

                row = []
                for i in _xrange(14):
                    row.append('\n'.join(_str(error[j][i])
                                         for j in _xrange(4)))
                tt.add_row(row)

        s.append(tt.draw())

        return ''.join(s)

    def _summary_str(self, factors):

        # Write Summary Means
        s = ['\n\nTABLES OF ESTIMATED MARGINAL MEANS\n\n']
        for i in xrange(1,len(factors)+1):
            for efs in _xunique_combinations(factors, i):
                s.append('Estimated Marginal Means for ' + \
                     ''.join(['%s * '%f for f in efs])[:-3] + '\n')

                ys=self.df.pivot(self.dv,rows=efs,aggregate='tolist')
                names=ys.rnames

                dave=array([   mean(y[0]) for y in ys ])
                dsem=array([ stderr(y[0]) for y in ys ])

                dlowr=dave-(dsem*1.96)
                dhghr=dave+(dsem*1.96)

                tt = TextTable(max_width=0)
                tt.set_cols_dtype(['t']*len(efs) + ['a','a','a','a'])
                tt.set_cols_align(['l']*len(efs) + ['r','r','r','r'])
                tt.set_deco(TextTable.HEADER)

                tt.header(efs+['Mean','Std. Error',
                               '95% Lower Bound',
                               '95% Upper Bound'])

                for i,name in enumerate(names):
                    cs=[c[1] for c in name]
                    tt.add_row(cs+[dave[i],dsem[i],dlowr[i],dhghr[i]])

                s.append(tt.draw())
                s.append('\n\n')

        return ''.join(s)

    def plot(self, val, xaxis,
             seplines=None,
             sepxplots=None,
             sepyplots=None,
             xmin='AUTO',xmax='AUTO',ymin='AUTO',ymax='AUTO',
             fname='.png',
             quality='low',
             errorbars='ci'):
        """
        This functions is basically wraps the plot function from the
        dataframe module. It attempts to find the appropriate error bar
        term. Creats a filename if necessary and calls plot.
        """

        # Build filename
        if fname=='.png' or fname=='.svg':
            fname=md5sum(str(uniform()))+fname

        # Attempt to find errorbars
        factors=self.wfactors+self.bfactors
        efs=[f for f in factors if f in [xaxis,seplines,sepxplots,sepyplots]]

        if errorbars=='ci':
            if len(self.wfactors)==0 and len(self.bfactors)!=0:
                yerr=self[tuple(efs)]['ci']
            else:
                yerr=self[tuple(efs)]['ci_gg']
        elif errorbars=='se':
            if len(self.wfactors)==0 and len(self.bfactors)!=0:
                yerr=self[tuple(efs)]['se']
            else:
                yerr=self[tuple(efs)]['se_gg']
        else:
            yerr=None

        self.df.interaction_plot(val, xaxis, seplines=seplines,
                                 sepxplots=sepxplots,
                                 sepyplots=sepyplots,
                                 xmin=xmin, xmax=xmax,
                                 ymin=ymin, ymax=ymax,
                                 fname=fname,
                                 quality=quality,
                                 yerr=yerr)

        if '.png' in fname:
            dpi=100
            if quality=='medium' : dpi=200
            elif quality=='high' : dpi=300

            im=pylab.imread(fname)[:,:,0]
            imh,imw=shape(im)

            width,height=imw*1.,imh*1.
            if imw > 1000:
                width=1000.
                height=width*(imh*1./imw*1.)

            if height > 1000:
                height=1000.
                width=height*(imw*1./imh*1.)

##            # if this is the first plot write 'Summary Plots' header
##            if self.plots==[]:
##                html.add(h(a('Summary Plots',name='1_'+md5sum('Summary Plots')),2,'center'))
##
            # Build title
            txt=['Summary Plot of %s ~ %s'%(val, xaxis)]
            if seplines!=''  : txt.append(' * %s'%seplines)
            if sepxplots!='' : txt.append(' * %s'%sepxplots)
            if sepyplots!='' : txt.append(' * %s'%sepyplots)
            txt=''.join(txt)

##            html.add(br(1))
##            html.add(h(a(txt,name='2_'+md5sum(txt))))
##
##            if yerr!=None:
##
##                if errorbars=='ci':
##                    html.add(p('Using Greenhouse-Geisser CI from %s of %f'%(efs,yerr)))
##                elif errorbars=='se':
##                    html.add(p('Using Greenhouse-Geisser SE from %s of %f'%(efs,yerr)))
##
##
##            html.add(a(img(fname,width=int(width),height=int(height)),href=fname))
            self.plots.append(txt)

    def __repr__(self):
        if self == {}:
            return 'Anova()'

        s = []
        for k, v in self.items():
            s.append("(%s, %s)"%(repr(k), repr(v)))
        args = '[' + ', '.join(s) + ']'

        kwds = []
        if self.df != {}:
            kwds.append(", df=%s"%repr(self.df))

        if self.wfactors != []:
            kwds.append(", wfactors=%s"%repr(self.wfactors))

        if self.bfactors != []:
            kwds.append(", bfactors=%s"%repr(self.bfactors))

        if self.alpha != 0.05:
            kwds.append(", alpha=%s"%self.alpha)

        if self.measure != '':
            kwds.append(", measure='%s'"%self.measure)

        if self.dv != None:
            kwds.append(", dv='%s'"%self.dv)

        if self.sub != 'SUBJECT':
            kwds.append(", sub='%s'"%self.sub)

        if self.transform != '':
            kwds.append(", transform='%s'"%self.transform)

        kwds= ''.join(kwds)

        return 'Anova(%s%s)'%(args,kwds)

#### Within-Subjects test
##df=DataFrame()
##fname='error~subjectXtimeofdayXcourseXmodel.csv'
##df.read_tbl(fname)
##aov=Anova()
##aov.run(df,'ERROR',wfactors=['TIMEOFDAY','COURSE','MODEL'])#,transform='windsor05')
##aov.output2html(fname[:-4]+'RESULTS.htm')
##print(aov)
##
##
#### Between-Subjects test w/ transform
##df=DataFrame()
##fname='words~ageXcondition.csv'
##df.read_tbl(fname)
##aov=Anova()
##aov.run(df,'WORDS',bfactors=['AGE','CONDITION'],transform='windsor05')
##aov.output2html('WINDSOR05_'+fname[:-4]+'RESULTS.htm')
##
##
#### Between-Subjects test
##df=DataFrame()
##fname='words~ageXcondition.csv'
##df.read_tbl(fname)
##aov=Anova()
##aov.run(df,'WORDS',bfactors=['AGE','CONDITION'])
##aov.output2html(fname[:-4]+'RESULTS.htm')
##
##
#### Mixed Between/Within test
##df=DataFrame()
##fname='suppression~subjectXgroupXcycleXphase.csv'
##df.read_tbl(fname)
##df['SUPPRESSION']=[.01*x for x in df['SUPPRESSION']]
##aov=Anova()
##aov.run(df,'SUPPRESSION',wfactors=['CYCLE','PHASE'],bfactors=['GROUP'])#,transform='windsor01')
##aov.plot('SUPPRESSION','CYCLE',seplines='PHASE',quality='high')
##aov.plot('SUPPRESSION','CYCLE',seplines='PHASE',sepyplots='GROUP',quality='high')
##aov.output2html(fname[:-4]+'RESULTS.htm')
