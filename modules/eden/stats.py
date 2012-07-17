# -*- coding: utf-8 -*-


""" Sahana Eden Stats Model

    @copyright: 2012-2012 (c) Sahana Software Foundation
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

__all__ = ["S3StatsModel",
           "S3StatsDemographicModel",
           ]

from gluon import *
from gluon.storage import Storage

from ..s3 import *
# =============================================================================
class S3StatsModel(S3Model):
    """
        Statistics Management
    """

    names = ["stats_parameter",
             "stats_data",
             "stats_aggregate",
             "stats_param_id",
            ]

    def model(self):

        T = current.T
        db = current.db

        location_id = self.gis_location_id

        # Shortcuts

        super_entity = self.super_entity
        super_key = self.super_key
        super_link = self.super_link
        define_table = self.define_table

        #----------------------------------------------------------------------
        # The super entity - stats_parameter
        #
        sp_types = Storage(vulnerability_indicator = T("Vulnerability"),
                           stats_demographic = T("Demographic"),
                           survey_question_type = T("Survey"),
                           project_beneficary_type = T("Project"),
                           climate_parameter = T("Climate"),
                          )
        tablename = "stats_parameter"
        table = super_entity(tablename,
                             "parameter_id",
                             sp_types,
                             Field("name",
                                   label = T("Statistic Name")),
                             Field("description",
                                   label = T("Statistic Description")),
                            )

        # Reusable Field
        param_id = S3ReusableField("parameter_id", table,
                                    sortby="name",
                                    requires = IS_NULL_OR(
                                               IS_ONE_OF(current.db, "stats_parameter.parameter_id",
                                                         orderby="stats_parameter.name",
                                                         sort=True)),
                                    label = T("Statistics Parameter"),
                                    ondelete = "CASCADE")

        #----------------------------------------------------------------------
        # The super entity - stats_data
        #
        sd_types = Storage(vulnerability_data = T("Vulnerability"),
                           stats_demographic_data = T("Demographic"),
                           survey_answer = T("Survey"),
                           project_beneficary = T("Project"),
                           climate_data = T("Climate"),
                          )
        tablename = "stats_data"
        table = super_entity(tablename,
                             "data_id",
                             sd_types,
                             param_id(),
                             location_id(),
                             self.doc_source_id(),
                             Field("value",
                                   "double",
                                   ),
                            )

        #----------------------------------------------------------------------
        # Stats Aggregated data
        #
        tablename = "stats_aggregate"
        table = define_table(tablename,
                             param_id(),
                             location_id(),
                             Field("start_date", "date",
                                   label = T("Start Date"),
                                   ),
                             Field("end_date", "date",
                                   label = T("End Date"),
                                   ),
                             Field("min", "double",
                                   label = T("Minimum"),
                                  ),
                             Field("max", "double",
                                   label = T("Maximum"),
                                  ),
                             Field("mean", "double",
                                   label = T("Mean"),
                                  ),
                             Field("median", "double",
                                   label = T("Median"),
                                  ),
                             Field("mean_ad", "double",
                                   label = T("Mean Absolute Deviation"),
                                  ),
                             Field("std", "double",
                                   label = T("Standard Deviation"),
                                  ),
                             Field("variance", "double",
                                   label = T("Variance"),
                                  ),
                             *s3_meta_fields()
                            )

        # ---------------------------------------------------------------------
        # Pass model-global names to response.s3
        #
        return Storage(stats_param_id = param_id)

    # -------------------------------------------------------------------------
    def defaults(self):
        """ Safe defaults if the module is disabled """
        param_id = S3ReusableField("parameter_id", "integer",
                                    readable=False,
                                    writable=False
                                   )
        return Storage(stats_param_id = param_id)

# =============================================================================
class S3StatsDemographicModel(S3Model):
    """
        Demographic Management
    """

    names = ["stats_demographic",
             "stats_demographic_data",
            ]

    def model(self):

        T = current.T
        # Shortcuts
        define_table = self.define_table
        stats_param_id  = self.stats_param_id
        super_link = self.super_link

        #----------------------------------------------------------------------
        # Demographic
        #
        tablename = "stats_demographic"
        table = define_table(tablename,
                             super_link("parameter_id", "stats_parameter"),
                             Field("name",
                                   label = T("Demographic Name")),
                             Field("description",
                                   label = T("Demographic Description")),
                             s3_comments(),
                             *s3_meta_fields()
                            )

        #----------------------------------------------------------------------
        # Demographic Data
        #
        tablename = "stats_demographic_data"
        table = define_table(tablename,
                             super_link("data_id", "stats_data"),
                             stats_param_id(),
                             self.gis_location_id(),
                             Field("value",
                                   "double",
                                   label = T("Demographic Value")),
                             s3_comments(),
                             *s3_meta_fields()
                            )

        # ---------------------------------------------------------------------
        # Pass model-global names to response.s3
        #
        return Storage()

    # -------------------------------------------------------------------------
    def defaults(self):
        """ Safe defaults if the module is disabled """

        return Storage()
# =============================================================================


# END =========================================================================
