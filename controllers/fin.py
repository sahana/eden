# -*- coding: utf-8 -*-

"""
    Finance
"""

module = request.controller
#resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    return s3db.cms_index(module)

# -----------------------------------------------------------------------------
def expense():
    """ RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def voucher_program():
    """ Voucher Programs: RESTful CRUD controller """

    return s3_rest_controller(rheader = s3db.fin_rheader)

# -----------------------------------------------------------------------------
def voucher():
    """ Vouchers: RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def voucher_debit():
    """ Voucher Debits: RESTful CRUD controller """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def payment_service():
    """ Payment Services: RESTful CRUD controller """

    return s3_rest_controller(rheader = s3db.fin_rheader)

# -----------------------------------------------------------------------------
def product():
    """ Billable Products/Services: RESTful CRUD controller """

    # TODO prep
    #      - on product_service tab, limit service selector to services of owner org

    return s3_rest_controller(rheader = s3db.fin_rheader)

# -----------------------------------------------------------------------------
def subscription_plan():
    """ Subscription Plans: RESTful CRUD controller """

    return s3_rest_controller(rheader = s3db.fin_rheader)

# -----------------------------------------------------------------------------
def subscription():
    """ Subscriptions: RESTful CRUD controller """

    return s3_rest_controller(rheader = s3db.fin_rheader)

# END =========================================================================
