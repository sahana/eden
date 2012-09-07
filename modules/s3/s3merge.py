# -*- coding: utf-8 -*-

""" S3 Record Merger

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @copyright: 2009-2012 (c) Sahana Software Foundation
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

__all__ = ["S3Merge"]

from s3rest import S3Method

# =============================================================================
class S3Merge(S3Method):
    """ Interactive Record Merger """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Apply Merge methods

            @param r: the S3Request
            @param attr: dictionary of parameters for the method handler

            @returns: output object to send to the view
        """

        # Not implemented yet
        r.error(405, manager.ERROR.BAD_METHOD)

# END =========================================================================
