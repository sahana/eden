# -*- coding: utf-8 -*-

"""
    Data Collection
"""

module = request.controller

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():
    "Module's Home Page"

    module_name = settings.modules[module].name_nice
    response.title = module_name
    return dict(module_name=module_name)

# -----------------------------------------------------------------------------
def template():
    """ Manage Data Collection Templates """

    return s3_rest_controller(rheader = s3db.dc_rheader)

# -----------------------------------------------------------------------------
def question():
    """ Manage Data Collection Questions """

    # @todo: prep to populate question_l10n from question

    return s3_rest_controller(rheader = s3db.dc_rheader)

# -----------------------------------------------------------------------------
def collection():
    """ Manage Data Collections """

    # @todo: prep to filter questions selector by template and unanswered

    return s3_rest_controller(rheader = s3db.dc_rheader)

# END =========================================================================
