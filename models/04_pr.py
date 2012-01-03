# -*- coding: utf-8 -*-

"""
    Person Registry

    @author: nursix
    @see: U{http://eden.sahanafoundation.org/wiki/BluePrintVITA}
"""

module = "pr"

# =============================================================================
# Load global names from PR models
# @todo: load only when needed, not globally
#
pe_label = s3db.pr_pe_label

person_id = s3db.pr_person_id
person_represent = s3db.pr_person_represent
pr_gender_opts = s3db.pr_gender_opts
pr_age_group_opts = s3db.pr_age_group_opts
pr_person_comment = s3db.pr_person_comment

group_id = s3db.pr_group_id
pr_group_represent = s3db.pr_group_represent

pr_rheader = s3db.pr_rheader

# END =========================================================================
