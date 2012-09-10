# -*- coding: utf-8 -*-

"""
    Global tables and re-usable fields
"""

# =============================================================================
# Import models
#
from s3.s3model import S3Model
import eden as models
current.models = models
current.s3db = s3db = S3Model()

# Explicit import statements to have them reload automatically in debug mode
import eden.asset
import eden.auth
import eden.cap
import eden.climate
import eden.cms
import eden.cr
import eden.delphi
import eden.doc
import eden.dvi
import eden.dvr
import eden.event
import eden.fire
import eden.flood
import eden.gis
import eden.hms
import eden.hrm
import eden.inv
import eden.irs
import eden.member
import eden.msg
import eden.ocr
import eden.org
import eden.patient
import eden.pr
import eden.sit
import eden.proc
import eden.project
import eden.req
import eden.scenario
import eden.security
import eden.stats
import eden.supply
import eden.support
import eden.survey
import eden.sync
import eden.translate
import eden.transport
import eden.vehicle
import eden.vol
import eden.vulnerability

# =============================================================================
# Make available for S3Models
# - legacy for backwards compatibility w docs & custom modules
from s3.s3fields import S3ReusableField, s3_comments, s3_meta_fields
s3.comments = s3_comments
s3.meta_fields = s3_meta_fields

# END =========================================================================
