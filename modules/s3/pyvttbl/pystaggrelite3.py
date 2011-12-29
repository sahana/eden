from __future__ import print_function

# Copyright (c) 2011, Roger Lew [see LICENSE.txt]
# This software is funded in part by NIH Grant P20 RR016454.

"""
This module contains custom aggregators for sqlite3

sqlite has the following aggregate functions built-in:
    avg(X)
    count(X)
    count(*)
    group_concat(X)
    group_concat(X,Y)
    max(X)
    min(X)
    sum(X)
    total(X)

The aggregate functions in sqlite are much faster then the
methods implemented here. On the downside they are rather
limited. This module implements the following aggregate
functions:
    abs_mean(X)
    arbitrary(X)
    ci(X)
    datarange(X)
    geometric_mean(X)
    hasinf(X)
    hasnan(X)
    kurt(X)
    kurtp(X)
    median(X)
    mode(X)
    prod(X)
    rms(X)
    sem(X)
    skew(X)
    skewp(X)
    stdev(X)
    stdevp(X)
    var(X)
    varp(X)

The respective docstrings for these modules provide more
information as to there specific functionality. The aggregate
functions ignore NULL, non-float text, and nan values. When X
is empty the aggregates return None. Inf values may cause the
aggregate to return None or Inf depending on function. See the
test module for specifics. All the functions except for median
and mode are implemented with running tallies.
"""

import sys
import inspect
from math import sqrt,isnan,isinf,log10,log,exp,floor
from copy import copy
try:
    from collections import Counter
except ImportError:
    from counter import Counter

# Python 2 to 3 workarounds
import sys
if sys.version_info[0] == 2:
    _strobj = basestring
    _xrange = xrange
elif sys.version_info[0] == 3:
    _strobj = str
    _xrange = range

maxfloat=    sys.float_info.max
minfloat=-1.*sys.float_info.max

def getaggregators():
    """returns a generator of the (name,arity,function) of the
    available aggregators"""
    mod=sys.modules[__name__]

    for name,func in inspect.getmembers(mod,inspect.isclass):
        if hasattr(func,'step') and hasattr(func,'finalize'):
            arity=len(inspect.getargspec(func.step).args)-1
            yield (name,arity,func)

def isfloat(x):
    """
    >>> isfloat(12)
    True
    >>> isfloat(12)
    True
    >>> isfloat('a')
    False
    >>> isfloat(float('nan'))
    True
    >>> isfloat(float('inf'))
    True
    """
    try: float(x)
    except: return False
    return True

def _flatten(x):
    """_flatten(sequence) -> list

    Returns a single, flat list which contains all elements retrieved
    from the sequence and all recursively contained sub-sequences
    (iterables).

    Examples:
    >>> [1, 2, [3,4], (5,6)]
    [1, 2, [3, 4], (5, 6)]
    >>> _flatten([[[1,2,3], (42,None)], [4,5], [6], 7, MyVector(8,9,10)])
    [1, 2, 3, 42, None, 4, 5, 6, 7, 8, 9, 10]"""

    result = []
    for el in x:
        #if isinstance(el, (list, tuple)):
        if hasattr(el, "__iter__") and not isinstance(el, basestring):
            result.extend(_flatten(el))
        else:
            result.append(el)
    return result

def hist(V, bins=10, range=None, density=False, weights=None, cumulative=False):
    # docstring mostly borrowed from numpy.histogram and pylab.hist
    # numpy doesn't offer the cummulative. pylab.hist always makes a histogram
    # plot. This function requires neither numpy or pylab and returns the
    # same values. It has been tested
    """
    Compute the histogram of a set of data.

    Parameters
    ----------
    V : list_like
        Input data. The histogram is computed over the flattened array.
    bins : int or sequence of scalars, optional
        If `bins` is an int, it defines the number of equal-width
        bins in the given range (10, by default). If `bins` is a sequence,
        it defines the bin edges, including the rightmost edge, allowing
        for non-uniform bin widths.
    range : (float, float), optional
        The lower and upper range of the bins.  If not provided, range
        is simply ``(min(V), max(V))``.  Values outside the range are
        ignored.
    density : bool, optional
        If False, the result will contain the number of samples
        in each bin.  If True, the result is the value of the
        probability *density* function at the bin, normalized such that
        the *integral* over the range is 1. Note that the sum of the
        histogram values will not be equal to 1 unless bins of unity
        width are chosen; it is not a probability *mass* function.
    weights : list_like, optional
        An array of weights, of the same shape as `V`.  Each value in `V`
        only contributes its associated weight towards the bin count
        (instead of 1).  If `density` is True, the weights are normalized,
        so that the integral of the density over the range remains 1
    cumulative : bool, options
        If True, then a histogram is computed where each bin gives the
        counts in that bin plus all bins for smaller values. The last bin
        gives the total number of datapoints. If normed is also True then
        the histogram is normalized such that the last bin equals 1. If
        cumulative evaluates to less than 0 (e.g. -1), the direction of
        accumulation is reversed. In this case, if normed is also True,
        then the histogram is normalized such that the first bin equals 1.

    Returns
    -------
    hist : list
        The values of the histogram. See `density` and `weights` for a
        description of the possible semantics.
    bin_edges : list
        Return the bin edges ``(length(hist)+1)``.

   """
    if bins < 1:
        raise Exception('bins must be >= 1')

    if not isinstance(cumulative, bool):
        raise TypeError('cumulative must be a bool')

    if not isinstance(density, bool):
        raise TypeError('cumulative must be a bool')

    if range == None:
        vmin, vmax = min(V), max(V)
    else:
        vmin, vmax = range

    rng  = vmax - vmin # the range of the histogram
    dbin  = rng / float(bins) # the spacing between the bins

    # build the weights if they aren't specified
    if weights == None:
        W = [1. for i in _xrange(len(V))]
    else:
        W = weights

    if len(V) != len(W):
        raise Exception('V and weights must be same length')

    histCounter = Counter() # a multi-set object from collections
    for i, (v, w) in enumerate(zip(V, W)):
        # the range defines a closed interval. The floor function
        # treats it as open so if we find a value that is equal
        # to max we move it to the appropriate bin.

        if v==vmax: v-=dbin/2.
        # based on the min and the range rescale the data so it
        # has a min of 0 and a max given by the number of bins
        histCounter[floor(bins*(v-vmin)/rng)] += w

    N = [histCounter[0]] # the counts
    B = [vmin] # the bin edges to be returned
    if cumulative:
        for i in _xrange(1, bins):
            B.append((i/float(bins))*rng+vmin)
            N.append(N[-1]+histCounter[i])
    else:
        for i in _xrange(1, bins):
            B.append((i/float(bins))*rng+vmin)
            N.append(histCounter[i])

    B.append(vmax) # append the last edge

    if cumulative and density:
        total = sum(v for k,v in histCounter.items() if k<bins)
        for i in _xrange(bins):
            N[i] /= total

    if not cumulative and density:
        total = sum(v for k,v in histCounter.items() if k<bins)

        for i in _xrange(bins):
            N[i] /= (dbin*total)

##    for n,b in zip(N, B):
##        print(_str(b,'f',3),n)

    return N,B

class ignore:
    """getaggregators shouldn't return this"""
    def __init__(self):
        pass

class hasnan:
    """
    Returns 1 if array contains 1 or more 'nan' values
    Returns 0 if the array does not contain any 'nan' values
    """
    def __init__(self):
        self.value=False

    def step(self, value):
        if isfloat(value):
            if isnan(float(value)):
                self.value=True

    def finalize(self):
        return self.value

class hasinf:
    """
    Returns 1 if array contains 1 or more 'inf' values
    Returns 0 if the array does not contain any 'inf' values
    """
    def __init__(self):
        self.value=False

    def step(self, value):
        if isfloat(value):
            if isinf(float(value)):
                self.value=True

    def finalize(self):
        return self.value

class arbitrary:
    """
    sqlite does not guarentee the order of returned rows will
    be sorted. This will most likely return the first value.
    It is intended to be used in cases where you know all of
    the values are the same.
    """
    def __init__(self):
        self.value=None

    def step(self, value):
        if self.value==None:
            self.value=value

    def finalize(self):
        return self.value

class datarange:
    """
    Returns non if given an empty set.

    Otherwise returns the range of the elements.
    """
    def __init__(self):
        global maxfloat,minfloat

        self.min=maxfloat
        self.max=minfloat

    def step(self, value):
        if isfloat(value):
            v=float(value)
            if not isnan(v):
                if v<self.min:
                    self.min=v
                if v>self.max:
                    self.max=v

    def finalize(self):
        if self.min==maxfloat and self.max==minfloat:
            return None

        return self.max-self.min

class abs_mean:
    """
    Takes the absolute value of the elements and
    computes the mean.
    """
    def __init__(self):
        self.s=0.
        self.N=0

    def step(self, value):
        if isfloat(value):
            v=float(value)
            if not isnan(v):
                self.s+=abs(v)
                self.N+=1

    def finalize(self):
        if self.N==0:
            return None

        return self.s/float(self.N)

class geometric_mean:
    """
    Takes the absolute value of the elements and
    computes the mean. Modeled after scipy.stats.gmean.
    If x contains any values < 0. return nan, if
    """
    def __init__(self):
        self.s=0.
        self.N=0
        self.ret_value = -1

    def step(self, value):
        if isfloat(value):
            v=float(value)
            if not isnan(v):
                if v<0:
                    self.ret_value=None
                elif v==0 and self.ret_value!=None:
                    self.ret_value=0.
                else:
                    self.s+=log(v)
                self.N+=1

    def finalize(self):
        if self.N==0:
            return None

        if self.ret_value != -1:
            return self.ret_value

        return exp(self.s/float(self.N))

class median:
    """
    Returns the median of the elements.
    """
    def __init__(self):
        self.sequence=[]

    def step(self, value):
        if isfloat(value):
            v=float(value)
            if not isnan(v):
                self.sequence.append(v)

    def finalize(self):
        N=len(self.sequence)
        if N==0:
            return None

        if N%2==0:
            return sum(sorted(self.sequence)[int(N/2-1):int(N/2)+1])/2.
        else:
            return sorted(self.sequence)[int(N/2)]

class mode:
    """
    Returns the mode of the elements.
    """
    def __init__(self):
        self.counter=Counter()

    def step(self, value):
        if isfloat(value):
            v=float(value)
            if not isnan(v):
                self.counter[v]+=1

    def finalize(self):
        if self.counter=={}:
            return None

        return self.counter.most_common()[0][0]

class var:
    """
    The variance is calculated using the "n-1" method.

    Estimates variance based on a sample. The variance  is a
    measure of how widely values are dispersed from the average
    value (the mean). Assumes that its arguments are a sample of
    the population. If your data represents the entire population,
    then compute the standard deviation using VARP.

    s^2 = \frac{1}{N-1} \sum_{i=1}^N (x_i - \overline{x})^2,
    """
    def __init__(self):
        self.x=[0.,-1.,-1.,-1.,-1.]

    def step(self, value):
        [n,oldM,newM,oldS,newS]=self.x

        if isfloat(value):
            v=float(value)
            if not isnan(v):
                n+=1

                if (n == 1):
                    oldM = newM = v
                    oldS = 0.0
                else:
                    newM = oldM + (v - oldM)/n
                    newS = oldS + (v - oldM)*(v - newM)

                    # set up for next iteration
                    oldM = copy(newM)
                    oldS = copy(newS)

                self.x=[n,oldM,newM,oldS,newS]

    def finalize(self):
        [n,oldM,newM,oldS,newS]=self.x
        if n<2:
            return None

        return newS/(n-1.)

class varp:
    """
    The variance is calculated using the "n" method.

    Calculates variance based on the entire population given as
    arguments. The variance is a measure of how widely values are
    dispersed from the average value (the mean). Assumes that its
    arguments are the entire population. If your data represents a
    sample of the population, then compute the variance using VAR.

    {s_N}^2 = \frac{1}{N} \sum_{i=1}^N (x_i - \overline{x})^2,
    """
    def __init__(self):
        self.x=[0.,-1.,-1.,-1.,-1.]

    def step(self, value):
        [n,oldM,newM,oldS,newS]=self.x

        if isfloat(value):
            v=float(value)
            if not isnan(v):
                n+=1

                if (n == 1):
                    oldM = newM = v
                    oldS = 0.0
                else:
                    newM = oldM + (v - oldM)/n
                    newS = oldS + (v - oldM)*(v - newM)

                    # set up for next iteration
                    oldM = copy(newM)
                    oldS = copy(newS)

                self.x=[n,oldM,newM,oldS,newS]

    def finalize(self):
        [n,oldM,newM,oldS,newS]=self.x
        if n==0:
            return None
        if n==1:
            return 0.

        return newS/float(n)

class stdev:
    """
    The standard deviation is calculated using the "n-1" method.

    Estimates standard deviation based on a sample. The standard
    deviation is a measure of how widely values are dispersed from
    the average value (the mean). Assumes that its arguments are a
    sample of the population. If your data represents the entire
    population, then compute the standard deviation using STDEVP.

    s^2 = \sqrt{\frac{1}{N-1} \sum_{i=1}^N (x_i - \overline{x})^2},
    """
    def __init__(self):
        self.x=[0.,-1.,-1.,-1.,-1.]

    def step(self, value):
        [n,oldM,newM,oldS,newS]=self.x

        if isfloat(value):
            v=float(value)
            if not isnan(v):
                n+=1

                if (n == 1):
                    oldM = newM = v
                    oldS = 0.0
                else:
                    newM = oldM + (v - oldM)/n
                    newS = oldS + (v - oldM)*(v - newM)

                    # set up for next iteration
                    oldM = copy(newM)
                    oldS = copy(newS)

                self.x=[n,oldM,newM,oldS,newS]

    def finalize(self):
        [n,oldM,newM,oldS,newS]=self.x
        if n<2:
            return None

        return sqrt(newS/(n-1.))

class stdevp:
    """
    The standard deviation is calculated using the "n" method.

    Calculates standard deviation based on the entire population
    given as arguments. The standard deviation is a measure of how
    widely values are dispersed from the average value (the mean).
    Assumes that its arguments are the entire population. If your
    data represents a sample of the population, then compute the
    standard deviation using STDEV.

    s_N = \sqrt{\frac{1}{N} \sum_{i=1}^N (x_i - \overline{x})^2}.
    """
    def __init__(self):
        self.x=[0.,-1.,-1.,-1.,-1.]

    def step(self, value):
        [n,oldM,newM,oldS,newS]=self.x

        if isfloat(value):
            v=float(value)
            if not isnan(v):
                n+=1

                if (n == 1):
                    oldM = newM = v
                    oldS = 0.0
                else:
                    newM = oldM + (v - oldM)/n
                    newS = oldS + (v - oldM)*(v - newM)

                    # set up for next iteration
                    oldM = copy(newM)
                    oldS = copy(newS)

                self.x=[n,oldM,newM,oldS,newS]

    def finalize(self):
        [n,oldM,newM,oldS,newS]=self.x
        if n==0:
            return None
        if n==1:
            return 0.

        return sqrt(newS/float(n))

class sem:
    """
    The standard error of the mean (SEM) is the standard
    deviation of the sample mean estimate of a population mean.
    SEM is estimated by the sample estimate of the population
    standard deviation (sample standard deviation) divided by
    the square root of the sample size.

    SE_\bar{x}\ = \frac{s}{\sqrt{n}},
    where {s} is the sample standard deviation
    """
    def __init__(self):
        self.x=[0.,-1.,-1.,-1.,-1.]

    def step(self, value):
        [n,oldM,newM,oldS,newS]=self.x

        if isfloat(value):
            v=float(value)
            if not isnan(v):
                n+=1

                if (n == 1):
                    oldM = newM = v
                    oldS = 0.0
                else:
                    newM = oldM + (v - oldM)/n
                    newS = oldS + (v - oldM)*(v - newM)

                    # set up for next iteration
                    oldM = copy(newM)
                    oldS = copy(newS)

                self.x=[n,oldM,newM,oldS,newS]

    def finalize(self):
        [n,oldM,newM,oldS,newS]=self.x
        if n<2:
            return None

        return sqrt(newS/(n-1.))/sqrt(n)

class ci:
    """
    95% confidence interval based on the standard error of the
    mean. The confidence interval is estimated as 1.96*SEM.

    The lower bound can be computed as mean-ci. The upper
    bound can be computed as mean+ci.

    CI=1.96*SE_\bar{x}\
    """
    def __init__(self):
        self.x=[0.,-1.,-1.,-1.,-1.]

    def step(self, value):
        [n,oldM,newM,oldS,newS]=self.x

        if isfloat(value):
            v=float(value)
            if not isnan(v):
                n+=1

                if (n == 1):
                    oldM = newM = v
                    oldS = 0.0
                else:
                    newM = oldM + (v - oldM)/n
                    newS = oldS + (v - oldM)*(v - newM)

                    # set up for next iteration
                    oldM = copy(newM)
                    oldS = copy(newS)

                self.x=[n,oldM,newM,oldS,newS]

    def finalize(self):
        [n,oldM,newM,oldS,newS]=self.x
        if n<2:
            return None

        return sqrt(newS/(n-1.))/sqrt(n)*1.96

class rms:
    """
    The root mean square (abbreviated RMS or rms), also known as
    the quadratic mean, is a statistical measure of the magnitude
    of a varying quantity.

     x_{\mathrm{rms}} = \sqrt {{{x_1}^2 + {x_2}^2 + \cdots + {x_n}^2} \over n}
    """
    def __init__(self):
        self.ss=0.
        self.N=0

    def step(self, value):
        if isfloat(value):
            v=float(value)
            if not isnan(v):
                self.ss+=v**2.
                self.N+=1

    def finalize(self):
        if self.N==0:
            return None

        return sqrt(self.ss/float(self.N))

class prod:
    """
    Return the product of the elements
    """
    def __init__(self):
        self.p=1.
        self.N=0

    def step(self, value):
        if isfloat(value):
            v=float(value)
            if not isnan(v):
                self.p*=v
                self.N+=1

    def finalize(self):
        if self.N==0:
            return None

        return self.p

class skewp:
    """
    skewness population estimate is based on the
    cumulants calculated from the raw moments.

    G_1 = \frac{k_3}{k_2^{3/2}},
    where {k_3} and {k_2} are the 3rd and 2nd order cumulants
    respectively.

    see also:
        http://mathworld.wolfram.com/Skewness.html
        http://mathworld.wolfram.com/RawMoment.html
        http://mathworld.wolfram.com/Cumulant.html
        http://www.tc3.edu/instruct/sbrown/stat/shape.htm#SkewnessCompute
    """
    def __init__(self):
        self.s1=0.
        self.s2=0.
        self.s3=0.
        self.N=0

    def step(self, value):
        if isfloat(value):
            v=float(value)
            if not isnan(v):
                ov=copy(v)
                self.s1+=v
                v*=ov
                self.s2+=v
                v*=ov
                self.s3+=v
                self.N+=1

    def finalize(self):
        if self.N<3:
            return None

        self.N=float(self.N)

        # calculate unbiased raw moments
        m1=self.s1/self.N
        m2=self.s2/self.N
        m3=self.s3/self.N

        # from the raw moments calculate cumulants
        k1 = m1
        k2 = m2 - m1**2
        k3 = 2.*m1**3. - 3.*m1*m2 + m3

        num=k3
        den=k2**1.5

        if den==0: return None
        else: return num/den

class skew:
    """
    skewness sample estimate is based on the
    cumulants calculated from the raw moments.

    G_1 = \frac{\sqrt{N(N-1)}}{N-2} \frac{k_3}{k_2^{3/2}},
    where {k_3} and {k_2} are the 3rd and 2nd order cumulants
    respectively.

    see also:
        http://mathworld.wolfram.com/Skewness.html
        http://mathworld.wolfram.com/RawMoment.html
        http://mathworld.wolfram.com/Cumulant.html
        http://www.tc3.edu/instruct/sbrown/stat/shape.htm#SkewnessCompute
    """
    def __init__(self):
        self.s1=0.
        self.s2=0.
        self.s3=0.
        self.N=0

    def step(self, value):
        if isfloat(value):
            v=float(value)
            if not isnan(v):
                ov=copy(v)
                self.s1+=v
                v*=ov
                self.s2+=v
                v*=ov
                self.s3+=v
                self.N+=1

    def finalize(self):
        if self.N<3:
            return None

        self.N=float(self.N)

        # calculate unbiased raw moments
        m1=self.s1/self.N
        m2=self.s2/self.N
        m3=self.s3/self.N

        # from the raw moments calculate cumulants
        k1 = m1
        k2 = m2 - m1**2
        k3 = 2.*m1**3. - 3.*m1*m2 + m3

        num=sqrt(self.N*(self.N-1.))/(self.N-2.)*k3
        den=k2**1.5

        if den==0: return None
        else: return num/den

class kurtp:
    """
    kurtosis population estimate is based on the
    cumulants calculated from the raw moments.

    G_2 = \frac{k_4}{k_{2}^2},
    where {k_4} and {k_2} are the 4th and 2nd order cumulants
    respectively.

    see also:
        http://mathworld.wolfram.com/Kurtosis.html
        http://mathworld.wolfram.com/RawMoment.html
        http://mathworld.wolfram.com/Cumulant.html
    """
    def __init__(self):
        self.s1=0.
        self.s2=0.
        self.s3=0.
        self.s4=0.
        self.N=0

    def step(self, value):
        if isfloat(value):
            v=float(value)
            if not isnan(v):
                ov=copy(v)
                self.s1+=v
                v*=ov
                self.s2+=v
                v*=ov
                self.s3+=v
                v*=ov
                self.s4+=v
                self.N+=1

    def finalize(self):
        if self.N<3:
            return None

        self.N=float(self.N)

        # calculate unbiased raw moments
        m1=self.s1/self.N
        m2=self.s2/self.N
        m3=self.s3/self.N
        m4=self.s4/self.N

        # from the raw moments calculate cumulants
##        k1 = m1
        k2 = m2 - m1**2
##        k3 = 2.*m1**3. - 3.*m1*m2 + m3
        k4 = -6.*m1**4 + 12.*(m1**2)*m2 -3.*m2**2. - 4.*m1*m3 + m4

        num=k4
        den=k2**2.

        if den==0: return None
        else: return num/den

class kurt:
    """
    skewness sample estimate is based on the
    cumulants calculated from the raw moments.

    g_2 = \frac{k_4}{k_{2}^2},

    G_2 = \frac{N-1}{(N-2)(N-3)}[(N+1)g_2 + 6]
    where {k_4} and {k_2} are the 4th and 2nd order cumulants
    respectively.

    see also:
        http://mathworld.wolfram.com/Kurtosis.html
        http://mathworld.wolfram.com/RawMoment.html
        http://mathworld.wolfram.com/Cumulant.html
        http://www.tc3.edu/instruct/sbrown/stat/shape.htm#KurtosisCompute
    """
    def __init__(self):
        self.s1=0.
        self.s2=0.
        self.s3=0.
        self.s4=0.
        self.N=0

    def step(self, value):
        if isfloat(value):
            v=float(value)
            if not isnan(v):
                ov=copy(v)
                self.s1+=v
                v*=ov
                self.s2+=v
                v*=ov
                self.s3+=v
                v*=ov
                self.s4+=v
                self.N+=1

    def finalize(self):
        if self.N<3:
            return None

        self.N=float(self.N)

        # calculate unbiased raw moments
        m1=self.s1/self.N
        m2=self.s2/self.N
        m3=self.s3/self.N
        m4=self.s4/self.N

        # from the raw moments calculate cumulants
##        k1 = m1
        k2 = m2 - m1**2
##        k3 = 2.*m1**3. - 3.*m1*m2 + m3
        k4 = -6.*m1**4 + 12.*(m1**2)*m2 -3.*m2**2. - 4.*m1*m3 + m4

        num=k4
        den=k2**2.

        if den==0.: return None

        g2=num/den
        return (self.N-1.)/((self.N-2.)*(self.N-3.))*((self.N+1.)*g2+6.)


