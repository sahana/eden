# -*- coding: utf-8 -*-

"""
    S3 Python-2/3 Alternatives

    @copyright: 2019 (c) Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
"""

import sys
import locale

PY2 = sys.version_info[0] == 2

if PY2:
    import cPickle as pickle
    try:
        from cStringIO import StringIO  # faster, where available
    except ImportError:
        from StringIO import StringIO
    import urlparse
    import urllib2
    from urllib2 import HTTPError, URLError, urlopen
    from urllib import urlencode
    from urllib import quote as urllib_quote
    from HTMLParser import HTMLParser
    import Cookie
    reduce = reduce
    basestring = basestring
    unichr = unichr
    unicodeT = unicode
    STRING_TYPES = (str, unicode)
    long = long
    INTEGER_TYPES = (int, long)
    from types import ClassType
    CLASS_TYPES = (type, ClassType)
    xrange = xrange
    sorted_locale = lambda x: sorted(x, cmp=locale.strcoll)
else:
    import pickle
    from io import StringIO
    from urllib import parse as urlparse
    from urllib import request as urllib2
    from urllib.error import HTTPError, URLError
    from urllib.request import urlopen
    from urllib.parse import urlencode
    from urllib.parse import quote as urllib_quote
    from html.parser import HTMLParser
    from http import cookies as Cookie
    from functools import reduce
    basestring = str
    unichr = chr
    unicodeT = str
    STRING_TYPES = (str,)
    long = int
    INTEGER_TYPES = (int,)
    ClassType = type
    CLASS_TYPES = (type,)
    xrange = range
    sorted_locale = lambda x: sorted(x, key=locale.strxfrm)
