# -*- coding: utf-8 -*-

"""
    Global tables and re-usable fields
"""

# =============================================================================
# Import models
#
from s3.s3model import S3Model
import s3db as models
current.models = models

# Explicit import statements to have them reload automatically in debug mode
import s3db.assess
import s3db.asset
import s3db.auth
import s3db.budget
import s3db.cap
import s3db.climate
import s3db.cms
import s3db.cr
import s3db.dc
import s3db.delphi
import s3db.deploy
import s3db.disease
import s3db.doc
import s3db.dvi
import s3db.dvr
import s3db.evr
import s3db.event
import s3db.fire
import s3db.gis
import s3db.hms
import s3db.hrm
import s3db.inv
import s3db.irs
import s3db.member
import s3db.msg
import s3db.ocr
import s3db.org
import s3db.patient
import s3db.po
import s3db.pr
import s3db.sit
import s3db.proc
import s3db.project
import s3db.req
import s3db.s3
import s3db.scenario
import s3db.security
import s3db.setup
import s3db.stats
import s3db.supply
import s3db.support
import s3db.survey
import s3db.sync
import s3db.tour
import s3db.tr
import s3db.translate
import s3db.transport
import s3db.vehicle
import s3db.vol
import s3db.vulnerability
import s3db.water

current.s3db = s3db = S3Model()

# =============================================================================
# Make available for S3Models
# - legacy for backwards compatibility w docs & custom modules
from s3.s3fields import S3ReusableField, s3_comments, s3_meta_fields
s3.comments = s3_comments
s3.meta_fields = s3_meta_fields

# END =========================================================================
