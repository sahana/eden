# -*- coding: utf-8 -*-

""" Sahana Eden Deployments Model

    @copyright: 2011-2013 (c) Sahana Software Foundation
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

__all__ = ["S3DeploymentModel",
           "S3DeploymentAlertModel",
           ]

from gluon import *

from ..s3 import *

# =============================================================================
class S3DeploymentModel(S3Model):

    names = ["deploy_deployment",
             "deploy_human_resource"]

    def model(self):

        T = current.T
        db = current.db
        define_table = self.define_table
        configure = self.configure
        super_link = self.super_link

        # ---------------------------------------------------------------------
        # Deployment
        #
        tablename = "deploy_deployment"
        table = define_table(tablename,
                             super_link("doc_id", "doc_entity"),
                             Field("title"),
                             self.gis_location_id(),
                             Field("event_type"),        # @todo: replace by link
                             Field("status", "integer"), # @todo: lookup?
                             *s3_meta_fields())

        # Table configuration
        configure(tablename,
                  super_entity="doc_entity")

        # Reusable field
        represent = S3Represent(lookup=tablename, fields=["title"])
        deployment_id = S3ReusableField("deployment_id", table,
                                        requires = IS_ONE_OF(db,
                                                             "deploy_deployment.id",
                                                             represent),
                                        represent = represent,
                                        label = T("Deployment"),
                                        ondelete = "CASCADE")

        # ---------------------------------------------------------------------
        # Deployment of human resources
        #
        tablename = "deploy_human_resource"
        table = define_table(tablename,
                             self.hrm_human_resource_id(empty=False,
                                                        label=T("Member")),
                             deployment_id(),
                             s3_date("start_date",
                                     label = T("Start Date")),
                             s3_date("end_date",
                                     label = T("End Date")),
                             *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Deployment of assets
        #
        # @todo: deploy_asset
        
        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict(deploy_deployment_id = deployment_id)

    # -------------------------------------------------------------------------
    def defaults(self):
        """
            Safe defaults for model-global names in case module is disabled
        """
        deployment_id = S3ReusableField("deployment_id", "integer",
                                        readable=False, writable=False)
        return dict(deploy_deployment_id = deployment_id)

# =============================================================================
class S3DeploymentAlertModel(S3Model):

    names = ["deploy_alert",
             "deploy_group",
             "deploy_response"]

    def model(self):

        define_table = self.define_table

        # ---------------------------------------------------------------------
        # Alerts
        #
        tablename = "deploy_alert"
        table = define_table(tablename,
                             *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Person entity to send alerts to
        #
        tablename = "deploy_group"
        table = define_table(tablename,
                             *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Responses to Alerts
        #
        tablename = "deploy_response"
        table = define_table(tablename,
                             *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict()

    # -------------------------------------------------------------------------
    def defaults(self):
        """
            Safe defaults for model-global names in case module is disabled
        """
        return dict()

# END =========================================================================
