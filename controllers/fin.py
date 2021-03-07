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

    def prep(r):

        if r.component_name == "voucher_billing":

            program = s3db.fin_VoucherProgram(r.id)
            ctable = r.component.table

            # Configure date and status fields
            if not r.component_id:
                field = ctable.date
                field.writable = True
                program.earliest_billing_date(configure=field)
            else:
                query = (ctable.id == r.component_id)
                row = db(query).select(ctable.status, limitby=(0, 1)).first()
                if row and row.status == "SCHEDULED":
                    field = ctable.date
                    field.writable = True
                    program.earliest_billing_date(billing_id = r.component_id,
                                                  configure = field,
                                                  )
                    field = ctable.status
                    field.writable = True
        return True
    s3.prep = prep

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
def voucher_claim():
    """ Compensation Claims: RESTful CRUD controller """

    def prep(r):

        table = r.resource.table

        record = r.record
        if not record or record.status == "NEW":
            # Make additional fields writable in new claims
            writable = ("account_holder",
                        "account_number",
                        "bank_name",
                        "bank_address",
                        "status",
                        )
            for fn in writable:
                field = table[fn]
                if field.readable:
                    field.writable = True

        return True
    s3.prep = prep

    return s3_rest_controller(rheader = s3db.fin_rheader)

# -----------------------------------------------------------------------------
def voucher_invoice():
    """ Voucher Invoice: RESTful CRUD controller """

    def prep(r):

        table = r.resource.table

        record = r.record
        if not record or record.status != "PAID":
            # Make additional fields writable in unpaid invoices
            writable = ("po_number",
                        "status",
                        "reason",
                        )
            for fn in writable:
                field = table[fn]
                if field.readable:
                    field.writable = True

        return True
    s3.prep = prep

    return s3_rest_controller(rheader = s3db.fin_rheader)

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
