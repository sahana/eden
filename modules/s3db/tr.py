# -*- coding: utf-8 -*-

""" Turkey-specific Tables

    @copyright: 2015-2016 (c) Sahana Software Foundation
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

__all__ = ("S3TurkeyIdentityModel",)

from gluon import *
from ..s3 import *

# =============================================================================
class S3TurkeyIdentityModel(S3Model):
    """ Model for Turkish Identity Cards """

    names = ("tr_identity",)

    def model(self):

        T = current.T

        # -------------------------------------------------------------------------
        # Turkish Identity
        #
        tablename = "tr_identity"
        self.define_table(tablename,
                          self.pr_person_id(),
                          self.gis_location_id(
                            widget = S3LocationSelector(levels=("L1", "L2", "L3"),
                                                        show_map=False,
                                                        ),
                            ),
                          Field("volume_no",
                                label = T("Volume No"),
                                ),
                          Field("family_order_no", "integer",
                                label = T("Family Order No"),
                                ),
                          Field("order_no", "integer",
                                label = T("Order No"),
                                ),
                          *s3_meta_fields()
                          )

        # ---------------------------------------------------------------------
        # Return global names to s3.*
        #
        return {}

# END =========================================================================
