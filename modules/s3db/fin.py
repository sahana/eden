# -*- coding: utf-8 -*-

""" Finance Tables

    @copyright: 2015-2021 (c) Sahana Software Foundation
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

__all__ = ("FinExpensesModel",
           "FinVoucherModel",
           "FinPaymentServiceModel",
           "FinProductModel",
           "FinSubscriptionModel",
           "fin_rheader",
           "fin_voucher_permitted_programs",
           )

from gluon import *
from ..s3 import *
from s3layouts import S3PopupLink

# =============================================================================
class FinExpensesModel(S3Model):
    """ Model for Expenses """

    names = ("fin_expense",
             "fin_expense_id",
             )

    def model(self):

        T = current.T

        # -------------------------------------------------------------------------
        # Expenses
        #
        tablename = "fin_expense"
        self.define_table(tablename,
                          self.super_link("doc_id", "doc_entity"),
                          Field("name", length=128, notnull=True,
                                label = T("Short Description"),
                                ),
                          s3_date(),
                          Field("value", "double",
                                label = T("Value"),
                                represent = lambda v: \
                                    IS_FLOAT_AMOUNT.represent(v, precision=2),
                                ),
                          s3_currency(),
                          s3_comments(),
                          *s3_meta_fields(),
                          on_define = lambda table: \
                            [table.created_by.set_attributes(represent = s3_auth_user_represent_name),
                             #table.created_on.set_attributes(represent = S3DateTime.datetime_represent),
                             ]
                          )

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Expense"),
            title_display = T("Expense Details"),
            title_list = T("Expenses"),
            title_update = T("Edit Expense"),
            title_upload = T("Import Expenses"),
            label_list_button = T("List Expenses"),
            label_delete_button = T("Delete Expense"),
            msg_record_created = T("Expense added"),
            msg_record_modified = T("Expense updated"),
            msg_record_deleted = T("Expense removed"),
            msg_list_empty = T("No Expenses currently registered")
            )

        crud_form = S3SQLCustomForm("name",
                                    "date",
                                    "value",
                                    "currency",
                                    S3SQLInlineComponent(
                                        "document",
                                        name = "document",
                                        label = T("Attachments"),
                                        fields = [("", "file")],
                                    ),
                                    "comments",
                                    )

        # Resource Configuration
        self.configure(tablename,
                       crud_form = crud_form,
                       list_fields = [("date"),
                                      (T("Organization"), "created_by$organisation_id"),
                                      (T("By"), "created_by"),
                                      "name",
                                      "comments",
                                      "document.file",
                                      ],
                       super_entity = "doc_entity",
                       )

        represent = S3Represent(lookup = tablename)

        expense_id = S3ReusableField("expense_id", "reference %s" % tablename,
                                     label = T("Expense"),
                                     ondelete = "CASCADE",
                                     represent = represent,
                                     requires = IS_EMPTY_OR(
                                                IS_ONE_OF(current.db, "fin_expense.id",
                                                          represent,
                                                          orderby="fin_expense.name",
                                                          sort=True,
                                                          )),
                                     sortby = "name",
                                     )

        # ---------------------------------------------------------------------
        # Return global names to s3.*
        #
        return {"fin_expense_id": expense_id,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """
            Return safe defaults in case the model has been deactivated.
        """

        return {"fin_expense_id": S3ReusableField.dummy("expense_id"),
                }

# =============================================================================
class FinVoucherModel(S3Model):
    """ Model for Voucher Programs """

    names = ("fin_voucher_program",
             "fin_voucher",
             "fin_voucher_debit",
             "fin_voucher_transaction",
             )

    def model(self):

        T = current.T

        db = current.db
        s3 = current.response.s3
        settings = current.deployment_settings

        define_table = self.define_table
        crud_strings = s3.crud_strings

        NONE = current.messages["NONE"]

        # Representation of bearer/provider
        pe_represent = self.pr_PersonEntityRepresent(show_label = False,
                                                     show_link = False,
                                                     show_type = False,
                                                     )

        personalize = settings.get_fin_voucher_personalize()
        bearer_dob = personalize == "dob"
        bearer_pin = personalize == "pin"

        # -------------------------------------------------------------------------
        # Voucher Program
        # - holds the overall credit/compensation balance for a voucher program
        #
        program_status = (("PLANNED", T("Planned")),
                          ("ACTIVE", T("Active")),
                          ("SUSPENDED", T("Suspended")),
                          ("CLOSED", T("Closed")),
                          )

        org_group_id = self.org_group_id
        org_group_represent = org_group_id.attr.represent
        org_group_requires = IS_EMPTY_OR(IS_ONE_OF(db, "org_group.id",
                                                   org_group_represent,
                                                   sort = True,
                                                   ))

        tablename = "fin_voucher_program"
        define_table(tablename,
                     self.org_organisation_id(
                            label = T("Administrator##fin"),
                            empty = False,
                            ),
                     self.project_project_id(
                            label = T("Project"),
                            ),
                     Field("name",
                           label = T("Title"),
                           requires = IS_NOT_EMPTY(), # TODO unique?
                           ),
                     Field("description", "text",
                           label = T("Description"),
                           represent = s3_text_represent,
                           widget = s3_comments_widget,
                           ),
                     Field("status",
                           label = T("Status"),
                           default = "ACTIVE",
                           represent = S3Represent(options = dict(program_status)),
                           requires = IS_IN_SET(program_status,
                                                zero = None,
                                                sort = False,
                                                ),
                           ),
                     s3_date("end_date",
                             label = T("End Date"),
                             ),
                     org_group_id("issuers_id",
                            label = T("Issuers##fin"),
                            requires = org_group_requires,
                            ),
                     org_group_id("providers_id",
                            label = T("Providers##fin"),
                            requires = org_group_requires,
                            ),
                     Field("credit", "integer",
                           default = 0,
                           label = T("Credit Balance"),
                           writable = False,
                           ),
                     Field("compensation", "integer",
                           default = 0,
                           label = T("Compensation Balance"),
                           writable = False,
                           ),
                     # Voucher Details:
                     Field("default_credit", "integer",
                           label = T("Default Credit per Voucher"),
                           default = 1,
                           requires = IS_INT_IN_RANGE(1),
                           # TODO setting to expose?
                           readable = False,
                           writable = False,
                           ),
                     Field("validity_period", "integer",
                           label = T("Validity Period for Vouchers (Days)"),
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(1)),
                           represent = lambda v, row=None: str(v) if v else NONE,
                           ),
                     Field("voucher_instructions", "text",
                           label = T("Voucher Instructions"),
                           represent = s3_text_represent,
                           widget = s3_comments_widget,
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # List fields
        list_fields = ["name",
                       "organisation_id",
                       "issuers_id",
                       "providers_id",
                       "end_date",
                       "status",
                       ]

        # Table Configuration
        self.configure(tablename,
                       list_fields = list_fields,
                       )

        # Components
        self.add_components(tablename,
                            fin_voucher = "program_id",
                            fin_voucher_debit = "program_id",
                            fin_voucher_transaction = "program_id",
                            )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Program"),
            title_display = T("Program Details"),
            title_list = T("Programs"),
            title_update = T("Edit Program"),
            label_list_button = T("List Programs"),
            label_delete_button = T("Delete Program"),
            msg_record_created = T("Program created"),
            msg_record_modified = T("Program updated"),
            msg_record_deleted = T("Program deleted"),
            msg_list_empty = T("No Programs currently registered"),
        )

        # Reusable Field
        represent = S3Represent(lookup = tablename)
        program_id = S3ReusableField("program_id", "reference %s" % tablename,
                                     label = T("Program"),
                                     represent = represent,
                                     requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "%s.id" % tablename,
                                                              represent,
                                                              )),
                                     )

        # -------------------------------------------------------------------------
        # Voucher
        # - represents a credit granted to the bearer to purchase a
        #   service/product under the program
        #
        tablename = "fin_voucher"
        define_table(tablename,
                     program_id(empty = False),
                     Field("pe_id", "reference pr_pentity",
                           label = T("Bearer##fin"),
                           represent = pe_represent,
                           requires = IS_EMPTY_OR(IS_ONE_OF(db, "pr_pentity.pe_id",
                                                            pe_represent,
                                                            instance_types = ["org_organisation"],
                                                            )),
                           ),
                     Field("signature", length=64,
                           label = T("Voucher ID"),
                           writable = False,
                           ),
                     s3_date("bearer_dob",
                             label = T("Beneficiary Date of Birth"),
                             readable = bearer_dob,
                             writable = bearer_dob,
                             empty = not bearer_dob,
                             ),
                     Field("bearer_pin",
                           label = T("PIN"),
                           readable = bearer_pin,
                           writable = bearer_pin,
                           requires = [IS_NOT_EMPTY(), IS_LENGTH(maxsize=10, minsize=4)] if bearer_pin else None,
                           ),
                     Field("balance", "integer",
                           label = T("Balance##fin"),
                           default = 0,
                           writable = False,
                           ),
                     s3_date(label = T("Issued On"),
                             default = "now",
                             writable = False,
                             ),
                     s3_date("valid_until",
                             label = T("Valid Until"),
                             writable = False,
                             ),
                     s3_comments(),
                     *s3_meta_fields())

        # TODO Bearer notes?

        # Table Configuration
        self.configure(tablename,
                       deletable = False,
                       editable = False,
                       create_onvalidation = self.voucher_create_onvalidation,
                       create_onaccept = self.voucher_create_onaccept,
                       )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Voucher"),
            title_display = T("Voucher Details"),
            title_list = T("Vouchers"),
            title_update = T("Edit Voucher"),
            label_list_button = T("List Vouchers"),
            label_delete_button = T("Delete Voucher"),
            msg_record_created = T("Voucher created"),
            msg_record_modified = T("Voucher updated"),
            msg_record_deleted = T("Voucher deleted"),
            msg_list_empty = T("No Vouchers currently registered"),
        )

        # Reusable field
        voucher_id = S3ReusableField("voucher_id", "reference %s" % tablename,
                                     ondelete = "RESTRICT",
                                     requires = IS_ONE_OF(db, "%s.id" % tablename),
                                     )

        # TODO rheader + primary controller

        # -------------------------------------------------------------------------
        # Voucher debit
        # - represents a claim for compensation of the provider for redeeming
        #   a voucher
        #
        tablename = "fin_voucher_debit"
        define_table(tablename,
                     program_id(empty = False),
                     voucher_id(writable = False),
                     Field("pe_id", "reference pr_pentity",
                           label = T("Provider##fin"),
                           represent = pe_represent,
                           requires = IS_EMPTY_OR(IS_ONE_OF(db, "pr_pentity.pe_id",
                                                            pe_represent,
                                                            instance_types = ["org_organisation"],
                                                            )),
                           ),
                     Field("signature", length=64,
                           label = T("Voucher ID"),
                           requires = IS_ONE_OF(db, "fin_voucher.signature"),
                           widget = S3QRInput(),
                           ),
                     s3_date("bearer_dob",
                             label = T("Beneficiary Date of Birth"),
                             readable = bearer_dob,
                             writable = bearer_dob,
                             empty = not bearer_dob,
                             ),
                     Field("bearer_pin",
                           label = T("PIN"),
                           readable = bearer_pin,
                           writable = bearer_pin,
                           requires = IS_NOT_EMPTY() if bearer_pin else None,
                           ),
                     s3_date(default = "now",
                             label = T("Date Effected"),
                             writable = False,
                             ),
                     Field("balance", "integer",
                           label = T("Balance##fin"),
                           default = 0,
                           writable = False,
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # Table Configuration
        self.configure(tablename,
                       editable = False,
                       deletable = False,
                       onvalidation = self.debit_onvalidation,
                       create_onaccept = self.debit_create_onaccept,
                       )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Accept Voucher"),
            title_display = T("Accepted Voucher"),
            title_list = T("Accepted Vouchers"),
            title_update = T("Edit Accepted Voucher"),
            label_list_button = T("List Accepted Vouchers"),
            label_delete_button = T("Delete Accepted Voucher"),
            msg_record_created = T("Voucher accepted"),
            msg_record_modified = T("Accepted Voucher updated"),
            msg_record_deleted = T("Accepted Voucher deleted"),
            msg_list_empty = T("No Accepted Vouchers currently registered"),
        )

        # Reusable field
        debit_id = S3ReusableField("debit_id", "reference %s" % tablename,
                                   ondelete = "RESTRICT",
                                   requires = IS_ONE_OF(db, "%s.id" % tablename),
                                   )

        # -------------------------------------------------------------------------
        # Voucher transaction
        # - records a debt transaction for a voucher program

        # Transaction types:
        #  - ISS: credit -x => voucher +x
        #  - DBT: credit +1 <= voucher -1, debit +1 <= compensation -1
        #  - CMP: debit -1 => compensation +1
        #
        transaction_types = {"ISS": T("Issued##fin"),
                             "DBT": T("Redeemed##fin"),
                             "CMP": T("Compensated##fin"),
                             }

        tablename = "fin_voucher_transaction"
        define_table(tablename,
                     program_id(empty = False),
                     s3_datetime(default="now"),
                     Field("type",
                           label = T("Type"),
                           represent = S3Represent(options=transaction_types),
                           requires = IS_IN_SET(transaction_types),
                           ),
                     Field("credit", "integer",
                           default = 0,
                           ),
                     Field("voucher", "integer",
                           default = 0,
                           ),
                     Field("debit", "integer",
                           default = 0,
                           ),
                     Field("compensation", "integer",
                           default = 0,
                           ),
                     voucher_id(),
                     debit_id(),
                     Field("ouuid",
                           readable = False,
                           writable = False,
                           ),
                     Field("vhash", "text",
                           readable = False,
                           writable = False,
                           ),
                     *s3_meta_fields())

        # List Fields
        list_fields = ["program_id",
                       "date",
                       "type",
                       (T("Voucher"), "voucher_id$signature"),
                       (T("Bearer##fin"), "voucher_id$pe_id"),
                       "debit_id$pe_id",
                       ]

        # Table Configuration
        self.configure(tablename,
                       list_fields = list_fields,
                       orderby = "fin_voucher_transaction.date desc",
                       insertable = False,
                       editable = False,
                       deletable = False,
                       )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Transaction"),
            title_display = T("Transaction Details"),
            title_list = T("Transactions"),
            title_update = T("Edit Transaction"),
            label_list_button = T("List Transactions"),
            label_delete_button = T("Delete Transaction"),
            msg_record_created = T("Transaction created"),
            msg_record_modified = T("Transaction updated"),
            msg_record_deleted = T("Transaction deleted"),
            msg_list_empty = T("No Transactions currently registered"),
        )
        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """ Safe defaults for names in case the module is disabled """

        #dummy = S3ReusableField.dummy

        return {#"example_example_id": dummy("example_id"),
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def voucher_create_onvalidation(form):
        """
            Form validation of new vouchers:
            - check that program is active and hasn't ended
        """

        db = current.db
        s3db = current.s3db

        table = s3db.fin_voucher
        ptable = s3db.fin_voucher_program

        form_vars = form.vars

        if "program_id" in form_vars:
            program_id = form_vars.program_id
        else:
            program_id = table.program_id.default

        query = (ptable.id == program_id) & \
                (ptable.deleted == False)
        program = db(query).select(ptable.status,
                                   ptable.end_date,
                                   limitby = (0, 1),
                                   ).first()
        if program:
            if program.status != "ACTIVE":
                form.errors["program_id"] = T("Program inactive")
            end_date = program.end_date
            if end_date and end_date < current.request.utcnow.date():
                form.errors["program_id"] = T("Program has ended")

    # -------------------------------------------------------------------------
    @staticmethod
    def voucher_create_onaccept(form):
        """
            Onaccept of new voucher:
            - transfer initial credit to the voucher (issue)
            - generate voucher signature
            - set expiration date (TODO)

            @param form: the FORM
        """

        # Get record ID
        form_vars = form.vars
        if "id" in form_vars:
            record_id = form_vars.id
        elif hasattr(form, "record_id"):
            record_id = form.record_id
        else:
            return

        table = current.s3db.fin_voucher
        query = (table.id == record_id)
        voucher = current.db(query).select(table.id,
                                           table.uuid,
                                           table.program_id,
                                           limitby = (0, 1),
                                           ).first()

        if not voucher:
            return

        update = {}
        program = fin_VoucherProgram(voucher.program_id)

        # Set end-date if program prescribes it
        pdata = program.program
        if pdata:
            validity_period = pdata.validity_period
            if validity_period:
                now = current.request.utcnow
                update["valid_until"] = (now + datetime.timedelta(days=validity_period)).date()

        # Generate voucher signature
        import uuid
        vn = "0%s0%s" % (voucher.program_id, voucher.id)
        update["signature"] = "%s%s" % (str(uuid.uuid4().int)[:(16-len(vn))], vn)

        voucher.update_record(**update)
        program.issue(voucher.id)

    # -------------------------------------------------------------------------
    @staticmethod
    def debit_onvalidation(form):
        """
            Validate debit:
            - identify the voucher to debit
            - verify bearer identity features, program and voucher status
        """

        T = current.T
        s3db = current.s3db

        form_vars = form.vars

        if "signature" not in form_vars:
            form.errors["signature"] = T("Missing voucher signature")
            return

        if "program_id" in form_vars:
            program_id = form_vars.program_id
        else:
            table = s3db.fin_voucher_debit
            program_id = table.program_id.default

        signature = form_vars["signature"]
        error = None

        settings = current.deployment_settings

        # Find the voucher
        vtable = s3db.fin_voucher
        ptable = s3db.fin_voucher_program
        join = ptable.on(ptable.id == vtable.program_id)
        query = (vtable.signature == signature) & \
                (vtable.deleted == False)
        row = current.db(query).select(vtable.id,
                                       vtable.bearer_dob,
                                       vtable.bearer_pin,
                                       vtable.balance,
                                       vtable.valid_until,
                                       ptable.id,
                                       ptable.status,
                                       ptable.end_date,
                                       join = join,
                                       limitby = (0, 1),
                                       ).first()

        field = "signature"
        if not row:
            error = T("Invalid voucher")
        else:
            program = row.fin_voucher_program
            voucher = row.fin_voucher

            today = current.request.utcnow.date()
            valid_until = voucher.valid_until

            personalize = settings.get_fin_voucher_personalize()

            # Voucher must match the selected program
            if program_id and str(program_id) != str(program.id):
                error = T("Voucher is for a different program")

            if not error:
                # Verify bearer identity feature (if required)
                if personalize == "dob" and voucher.bearer_dob:
                    bearer_dob = form_vars.get("bearer_dob")
                    if bearer_dob != voucher.bearer_dob:
                        field = "bearer_dob"
                        error = T("Incorrect Date of Birth")
                elif personalize == "pin" and voucher.bearer_pin:
                    bearer_pin = form_vars.get("bearer_pin")
                    if bearer_pin != voucher.bearer_pin:
                        field = "bearer_pin"
                        error = T("Incorrect PIN")

            if not error:
                # Verify program status
                if program.status != "ACTIVE":
                    error = T("Voucher program suspended")
                elif program.end_date and program.end_date < today:
                    error = T("Voucher program has ended")
                # Verify voucher status
                elif valid_until and valid_until < today:
                    error = T("Voucher expired")
                elif voucher.balance <= 0:
                    error = T("Voucher credit exhausted")

        if error:
            form.errors[field] = error

    # -------------------------------------------------------------------------
    @staticmethod
    def debit_create_onaccept(form):
        """
            Onaccept of debit:
            - transfer credit (redeem)

            @param form: the FORM
        """

        # Get record ID
        form_vars = form.vars
        if "id" in form_vars:
            record_id = form_vars.id
        elif hasattr(form, "record_id"):
            record_id = form.record_id
        else:
            return

        db = current.db
        s3db = current.s3db

        # Look up the debit
        table = s3db.fin_voucher_debit
        query = (table.id == record_id)
        debit = db(query).select(table.id,
                                 table.signature,
                                 limitby = (0, 1),
                                 ).first()

        if not debit:
            return

        # Look up the voucher from signature
        vtable = s3db.fin_voucher
        query = (vtable.signature == debit.signature) & \
                (vtable.deleted == False)
        voucher = db(query).select(vtable.id,
                                   vtable.program_id,
                                   limitby = (0, 1),
                                   ).first()
        if not voucher:
            return
        debit.update_record(program_id = voucher.program_id,
                            voucher_id = voucher.id,
                            )

        program = fin_VoucherProgram(voucher.program_id)
        program.debit(voucher.id, debit.id)

# =============================================================================
class FinPaymentServiceModel(S3Model):
    """ Model for Payment Services """

    names = ("fin_payment_service",
             "fin_payment_log",
             "fin_service_id",
             )

    def model(self):

        T = current.T
        define_table = self.define_table

        # -------------------------------------------------------------------------
        # Payments Service
        #
        api_types = {"PAYPAL": "PayPal",
                     }

        tablename = "fin_payment_service"
        define_table(tablename,
                     Field("name",
                           requires = IS_NOT_EMPTY(),
                           ),
                     self.org_organisation_id(empty=False),
                     Field("api_type",
                           default = "PAYPAL",
                           label = T("API Type"),
                           requires = IS_IN_SET(api_types,
                                                zero = None,
                                                ),
                           represent = S3Represent(options = api_types),
                           ),
                     Field("base_url",
                           label = T("Base URL"),
                           requires = IS_EMPTY_OR(
                                           IS_URL(mode = "generic",
                                                  allowed_schemes = ["http", "https"],
                                                  prepend_scheme = "https",
                                                  )),
                           ),
                     Field("use_proxy", "boolean",
                           default = False,
                           label = T("Use Proxy"),
                           represent = s3_yes_no_represent,
                           ),
                     Field("proxy",
                           label = T("Proxy Server"),
                           ),
                     Field("username",
                           label = T("Username (Client ID)"),
                           ),
                     Field("password", "password",
                           label = T("Password (Client Secret)"),
                           # TODO password widget
                           ),
                     Field("token_type",
                           label = T("Token Type"),
                           readable = False,
                           writable = False,
                           ),
                     Field("access_token",
                           label = T("Access Token"),
                           readable = False,
                           writable = False,
                           ),
                     s3_datetime("token_expiry_date",
                                 default = None,
                                 label = T("Token expires on"),
                                 #readable = False,
                                 writable = False,
                                 ),
                     *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Payment Service"),
            title_display = T("Payment Service Details"),
            title_list = T("Payment Services"),
            title_update = T("Edit Payment Service"),
            title_upload = T("Import Payment Services"),
            label_list_button = T("List Payment Services"),
            label_delete_button = T("Delete Payment Service"),
            msg_record_created = T("Payment Service added"),
            msg_record_modified = T("Payment Service updated"),
            msg_record_deleted = T("Payment Service removed"),
            msg_list_empty = T("No Payment Services currently registered")
            )

        # Components
        self.add_components(tablename,
                            fin_payment_log = "service_id",
                            fin_product_service = "service_id",
                            fin_subscription_plan_service = "service_id",
                            fin_subscription = "service_id",
                            )

        # TODO Implement represent using API type + org name
        represent = S3Represent(lookup=tablename, show_link=True)
        service_id = S3ReusableField("service_id", "reference %s" % tablename,
                                     label = T("Payment Service"),
                                     ondelete = "RESTRICT",
                                     represent = represent,
                                     requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(current.db, "%s.id" % tablename,
                                                              represent,
                                                              orderby = "%s.name" % tablename,
                                                              sort = True,
                                                              )),
                                     sortby = "name",
                                     )

        # -------------------------------------------------------------------------
        # Payments Log
        #
        tablename = "fin_payment_log"
        define_table(tablename,
                     service_id(empty = False,
                                ondelete = "CASCADE",
                                ),
                     s3_datetime(default="now",
                                 ),
                     Field("action"),
                     Field("result"),
                     Field("reason", "text"),
                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Return global names to s3.*
        #
        return {"fin_service_id": service_id,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """
            Return safe defaults in case the model has been deactivated.
        """

        return {"fin_service_id": S3ReusableField.dummy("service_id"),
                }

# =============================================================================
class FinProductModel(S3Model):
    """ Model to manage billable products/services """

    names = ("fin_product",
             "fin_product_id",
             "fin_product_service",
             )

    def model(self):

        T = current.T

        db = current.db
        s3 = current.response.s3

        configure = self.configure
        define_table = self.define_table
        crud_strings = s3.crud_strings

        # ---------------------------------------------------------------------
        # Products; represent billable products or services
        #
        # TODO provide mapping per service-type
        product_types = {"SERVICE": T("Service"),
                         "PHYSICAL": T("Physical Product"),
                         "DIGITAL": T("Digital Product"),
                         }

        tablename = "fin_product"
        define_table(tablename,
                     # The organisation offering the product/service
                     # Merchant Name needed by PayPal
                     self.org_organisation_id(),
                     Field("name",
                           label = T("Name"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("description", "text",
                           label = T("Description"),
                           ),
                     # TODO move into link table w/service
                     Field("type",
                           label = T("Type"),
                           default = "SERVICE",
                           requires = IS_IN_SET(product_types, zero=None),
                           ),
                     # TODO move into link table w/service
                     # TODO template to override default
                     # TODO make lookup-table, provide mapping per service-type
                     # https://developer.paypal.com/docs/api/catalog-products/v1/
                     Field("category",
                           label = T("Category"),
                           default = "GENERAL",
                           writable = False,
                           ),
                     # TODO product image
                     # TODO product homepage
                     s3_comments(),
                     *s3_meta_fields())

        # Table configuration
        configure(tablename,
                  deduplicate = S3Duplicate(primary = ("name",)),
                  )

        # Components
        self.add_components(tablename,
                            fin_subscription_plan = "product_id",
                            fin_product_service = "product_id"
                            )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Product"),
            title_display = T("Product Details"),
            title_list = T("Products"),
            title_update = T("Edit Product"),
            label_list_button = T("List Products"),
            label_delete_button = T("Delete Product"),
            msg_record_created = T("Product created"),
            msg_record_modified = T("Product updated"),
            msg_record_deleted = T("Product deleted"),
            msg_list_empty = T("No Products currently registered"),
        )

        # Reusable field
        represent = S3Represent(lookup=tablename, show_link=True)
        product_id = S3ReusableField("product_id", "reference %s" % tablename,
                                     label = T("Product"),
                                     represent = represent,
                                     requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "%s.id" % tablename,
                                                              represent,
                                                              )),
                                     sortby = "name",
                                     comment = S3PopupLink(c="fin",
                                                           f="product",
                                                           tooltip=T("Create a new product"),
                                                           ),
                                     )

        # ---------------------------------------------------------------------
        # Link product<=>service
        #
        tablename = "fin_product_service"
        define_table(tablename,
                     product_id(
                         empty = False,
                         ondelete = "CASCADE",
                         ),
                     self.fin_service_id(
                         empty = False,
                         ondelete = "CASCADE",
                         ),
                     Field("is_registered", "boolean",
                           default = False,
                           readable = False,
                           writable = False,
                           ),
                     Field("refno",
                           label = T("Reference Number"),
                           writable = False,
                           ),
                     *s3_meta_fields())

        # TODO Limit service selector to services of product-org
        #      => in product controller prep

        # Table configuration
        configure(tablename,
                  editable = False,
                  deletable = False, # TODO must retire, not delete
                  onaccept = self.product_service_onaccept,
                  ondelete = self.product_service_ondelete,
                  )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Register Product with Payment Service"),
            title_display = T("Registration Details"),
            title_list = T("Registered Payment Services"),
            title_update = T("Edit Registration"),
            label_list_button = T("List Registrations"),
            label_delete_button = T("Delete Registration"),
            msg_record_created = T("Product registered with Payment Service"),
            msg_record_modified = T("Registration updated"),
            msg_record_deleted = T("Registration deleted"),
            msg_list_empty = T("Product not currently registered with any Payment Services"),
            )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"fin_product_id": product_id,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """ Safe defaults for names in case the module is disabled """

        return {"fin_product_id": S3ReusableField.dummy("product_id"),
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def product_service_onaccept(form):
        """
            Onaccept of product<=>service link:
            - register product with the service (or update the registration)
        """

        # Get record
        form_vars = form.vars
        try:
            record_id = form_vars.id
        except AttributeError:
            record_id = None
        if not record_id:
            return

        # If not bulk:
        if not current.response.s3.bulk:

            table = current.s3db.fin_product_service
            query = (table.id == record_id) & \
                    (table.deleted == False)
            row = current.db(query).select(table.product_id,
                                           table.service_id,
                                           limitby = (0, 1),
                                           ).first()
            if not row:
                return

            from s3.s3payments import S3PaymentService
            try:
                adapter = S3PaymentService.adapter(row.service_id)
            except (KeyError, ValueError) as e:
                current.response.error = "Service registration failed: %s" % e
            else:
                success = adapter.register_product(row.product_id)
                if not success:
                    current.response.error = "Service registration failed"

    # -------------------------------------------------------------------------
    @staticmethod
    def product_service_ondelete(row):
        """
            Ondelete of product<=>service link:
            - retire product from service (if supported by service)
        """

        # TODO implement
        pass

# =============================================================================
class FinSubscriptionModel(S3Model):
    """ Model to manage subscription-based payments """

    names = ("fin_subscription_plan",
             "fin_subscription_plan_service",
             "fin_subscription",
             )

    def model(self):

        T = current.T

        db = current.db
        s3 = current.response.s3

        configure = self.configure
        crud_strings = s3.crud_strings
        define_table = self.define_table
        set_method = self.set_method

        # ---------------------------------------------------------------------
        # Subscription Plans
        #
        plan_statuses = {"ACTIVE": T("Active"),
                         "INACTIVE": T("Inactive"),
                         }
        interval_units = {"DAY": T("Days"),
                          "WEEK": T("Weeks"),
                          "MONTH": T("Months"),
                          "YEAR": T("Year"),
                          }
        price_represent = lambda v, row=None: IS_FLOAT_AMOUNT.represent(v,
                                                                        precision = 2,
                                                                        fixed = True,
                                                                        )

        tablename = "fin_subscription_plan"
        define_table(tablename,
                     self.fin_product_id(
                         empty = False,
                         ondelete = "CASCADE",
                         ),
                     Field("name",
                           label = T("Name"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("description",
                           label = T("Description"),
                           ),
                     Field("interval_unit",
                           label = T("Interval Unit"),
                           default = "MONTH",
                           requires = IS_IN_SET(interval_units,
                                                zero = None,
                                                ),
                           ),
                     Field("interval_count", "integer",
                           label = T("Interval"),
                           requires = IS_INT_IN_RANGE(1, 365),
                           ),
                     Field("fixed", "boolean",
                           label = T("Fixed-term"),
                           default = False,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Fixed-term"),
                                                           T("Subscription plan has a fixed total number of cycles"),
                                                           ),
                                         ),
                           ),
                     # TODO show only if fixed is checked
                     Field("total_cycles", "integer",
                           label = T("Total Cycles"),
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 999)),
                           ),
                     Field("price", "double",
                           label = T("Price"),
                           requires = IS_FLOAT_AMOUNT(minimum = 0.01,
                                                      ),
                           represent = price_represent,
                           ),
                     s3_currency(),
                     Field("status",
                           default = "ACTIVE",
                           requires = IS_IN_SET(plan_statuses,
                                                zero = None,
                                                ),
                           represent = S3Represent(options = plan_statuses),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # Components
        self.add_components(tablename,
                            fin_subscription_plan_service = "plan_id",
                            fin_subscription = "plan_id",
                            )

        # Table Configuration
        configure(tablename,
                  list_fields = ["product_id",
                                 "name",
                                 "interval_count",
                                 "interval_unit",
                                 "fixed",
                                 "total_cycles",
                                 "price",
                                 "currency",
                                 "status",
                                 ],
                  onvalidation = self.subscription_plan_onvalidation,
                  )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Subscription Plan"),
            title_display = T("Subscription Plan Details"),
            title_list = T("Subscription Plans"),
            title_update = T("Edit Subscription Plan"),
            label_list_button = T("List Subscription Plans"),
            label_delete_button = T("Delete Subscription Plan"),
            msg_record_created = T("Subscription Plan created"),
            msg_record_modified = T("Subscription Plan updated"),
            msg_record_deleted = T("Subscription Plan deleted"),
            msg_list_empty = T("No Subscription Plans currently registered"),
            )

        # Reusable field
        represent = fin_SubscriptionPlanRepresent(show_link=True)
        plan_id = S3ReusableField("plan_id", "reference %s" % tablename,
                                  label = T("Plan"),
                                  represent = represent,
                                  requires = IS_ONE_OF(db, "%s.id" % tablename,
                                                       represent,
                                                       ),
                                  sortby = "name",
                                  #comment = S3PopupLink(c="fin",
                                  #                      f="subscription_plan",
                                  #                      tooltip=T("Create a new subscription plan"),
                                  #                      ),
                                  )

        # ---------------------------------------------------------------------
        # Link subscription_plan<=>service
        # - when a subscription plan is registered with a payment service
        # - tracks service-specific reference numbers
        #
        # TODO limit service selector to product owner
        # TODO limit service selector to unregistered services
        #
        tablename = "fin_subscription_plan_service"
        define_table(tablename,
                     plan_id(
                         ondelete = "CASCADE",
                         ),
                     self.fin_service_id(
                         ondelete = "CASCADE",
                         ),
                     Field("is_registered", "boolean",
                           default = False,
                           readable = False,
                           writable = False,
                           ),
                     Field("refno",
                           label = T("Reference Number"),
                           writable = False,
                           ),
                     *s3_meta_fields())

        configure(tablename,
                  editable = False,
                  deletable = False,
                  onvalidation = self.subscription_plan_service_onvalidation,
                  onaccept = self.subscription_plan_service_onaccept,
                  #ondelete = self.subscription_plan_service_ondelete, TODO
                  )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Register Plan with Payment Service"),
            title_display = T("Registration Details"),
            title_list = T("Registered Payment Services"),
            title_update = T("Edit Registration"),
            label_list_button = T("List Registrations"),
            label_delete_button = T("Delete Registration"),
            msg_record_created = T("Plan registered with Payment Service"),
            msg_record_modified = T("Registration updated"),
            msg_record_deleted = T("Registration deleted"),
            msg_list_empty = T("Plan not currently registered with any Payment Services"),
            )

        # ---------------------------------------------------------------------
        # Subscription
        # - track subscriptions and their status
        #
        subscription_statuses = {
            "NEW":              T("Registration Pending"),
            "APPROVAL_PENDING": T("Approval Pending"),
            "APPROVED":         T("Approved"), # but not yet activated
            "ACTIVE":           T("Active"),
            "SUSPENDED":        T("Suspended"),
            "CANCELLED":        T("Cancelled"),
            "EXPIRED":          T("Expired"),
            }

        subscriber_represent = self.pr_PersonEntityRepresent(show_label=False)

        tablename = "fin_subscription"
        define_table(tablename,
                     self.super_link("pe_id", "pr_pentity",
                                     label = T("Subscriber"),
                                     ondelete = "RESTRICT",
                                     represent = subscriber_represent,
                                     readable = True,
                                     writable = False,
                                     ),
                     plan_id(ondelete = "CASCADE",
                             writable = False,
                             ),
                     self.fin_service_id(ondelete = "CASCADE",
                                         writable = False,
                                         ),
                     s3_datetime("start_date",
                                 label = T("Start Date"),
                                 writable = False,
                                 ),
                     s3_datetime("end_date",
                                 label = T("End Date"),
                                 writable = False,
                                 ),
                     Field("status",
                           default = "NEW",
                           requires = IS_IN_SET(subscription_statuses,
                                                zero = None,
                                                ),
                           represent = S3Represent(options = subscription_statuses),
                           writable = False,
                           ),
                     s3_datetime("status_date",
                                 label = T("Status verified on"),
                                 default = "now",
                                 writable = False,
                                 ),
                     Field("deliverable", "boolean",
                           label = T("Deliverable"),
                           default = False,
                           writable = False,
                           ),
                     Field("balance", "double",
                           label = T("Payment Balance"),
                           writable = False,
                           ),
                     Field("refno",
                           label = T("Reference Number"),
                           writable = False,
                           ),
                     Field("approval_url",
                           label = T("Approval URL"),
                           writable = False,
                           ),
                     *s3_meta_fields())

        configure(tablename,
                  list_fields = ["created_on", # TODO replace by explicit start_date
                                 "pe_id",
                                 "plan_id",
                                 "service_id",
                                 "status",
                                 "status_date",
                                 ],
                  insertable = False,   # create via adapter.register_subscription(plan_id, pe_id)
                  editable = False,
                  deletable = False,
                  )

        # Configure payment service callback methods
        from s3.s3payments import S3Payments
        set_method("fin", "subscription",
                   method = "approve",
                   action = S3Payments,
                   )
        set_method("fin", "subscription",
                   method = "confirm",
                   action = S3Payments,
                   )
        set_method("fin", "subscription",
                   method = "cancel",
                   action = S3Payments,
                   )
        set_method("fin", "subscription",
                   method = "status",
                   action = S3Payments,
                   )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Subscription"),
            title_display = T("Subscription Details"),
            title_list = T("Subscriptions"),
            title_update = T("Edit Subscription"),
            label_list_button = T("List Subscriptions"),
            label_delete_button = T("Delete Subscription"),
            msg_record_created = T("Subscription created"),
            msg_record_modified = T("Subscription updated"),
            msg_record_deleted = T("Subscription deleted"),
            msg_list_empty = T("No Subscriptions currently registered"),
            )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """ Safe defaults for names in case the module is disabled """

        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def subscription_plan_onvalidation(form):
        """
            Form validation for subscription plans
            - interval can be at most 1 year
            - fixed-term plan must specify number of cycles
        """

        T = current.T

        form_vars = form.vars

        # Verify interval length <= 1 year
        try:
            unit = form_vars.interval_unit
            count = form_vars.interval_count
        except AttributeError:
            pass
        else:
            MAX_INTERVAL = {"DAY": 365, "WEEK": 52, "MONTH": 12, "YEAR": 1}
            limit = MAX_INTERVAL.get(unit)
            if limit and count > limit:
                form.errors.interval_count = T("Interval can be at most 1 year")

        # Verify total cycles specified for fixed-term plan
        try:
            fixed = form_vars.fixed
            total_cycles = form_vars.total_cycles
        except AttributeError:
            pass
        else:
            if fixed and not total_cycles:
                form.errors.total_cycles = T("Fixed-term plan must specify number of cycles")

    # -------------------------------------------------------------------------
    @staticmethod
    def subscription_plan_service_onvalidation(form):
        """
            Form validation of subscription_plan<=>service link:
            - make sure the same plan is linked to a service only once
        """

        table = current.s3db.fin_subscription_plan_service

        form_vars = form.vars

        if "id" in form_vars:
            record_id = form_vars.id
        elif hasattr(form, "record_id"):
            record_id = form.record_id
        else:
            record_id = None

        plan_id = form_vars.get("plan_id", table.plan_id.default)
        if not plan_id:
            return

        try:
            service_id = form_vars.service_id
        except AttributeError:
            pass
        else:
            query = (table.plan_id == plan_id) & \
                    (table.service_id == service_id) & \
                    (table.deleted == False)
            if record_id:
                query &= (table.id != record_id)
            if current.db(query).count():
                msg = current.T("Plan is already registered with this service")
                if "service_id" in form_vars:
                    form.errors.service_id = msg
                else:
                    form.errors.plan_id = msg

    # -------------------------------------------------------------------------
    @staticmethod
    def subscription_plan_service_onaccept(form):
        """
            Onaccept of subscription_plan<=>service link:
            - register plan with the service (or update the registration)
        """

        # Get record
        form_vars = form.vars
        try:
            record_id = form_vars.id
        except AttributeError:
            record_id = None
        if not record_id:
            return

        # If not bulk:
        if not current.response.s3.bulk:

            table = current.s3db.fin_subscription_plan_service
            query = (table.id == record_id) & \
                    (table.deleted == False)
            row = current.db(query).select(table.plan_id,
                                           table.service_id,
                                           limitby = (0, 1),
                                           ).first()
            if not row:
                return

            from s3.s3payments import S3PaymentService
            try:
                adapter = S3PaymentService.adapter(row.service_id)
            except (KeyError, ValueError) as e:
                current.response.error = "Service registration failed: %s" % e
            else:
                success = adapter.register_subscription_plan(row.plan_id)
                if not success:
                    current.response.error = "Service registration failed"

# =============================================================================
class fin_SubscriptionPlanRepresent(S3Represent):
    """ Representation of subscription plan IDs """

    def __init__(self, show_link=False):
        """
            Constructor

            @param show_link: show representation as clickable link
        """

        super(fin_SubscriptionPlanRepresent, self).__init__(
                                                lookup = "fin_subscription_plan",
                                                show_link = show_link,
                                                )

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=None):
        """
            Custom rows lookup

            @param key: the key Field
            @param values: the values
            @param fields: unused (retained for API compatibility)
        """

        table = self.table

        count = len(values)
        if count == 1:
            query = (key == values[0])
        else:
            query = key.belongs(values)

        ptable = current.s3db.fin_product
        left = [ptable.on(ptable.id == table.product_id)]

        rows = current.db(query).select(table.id,
                                        table.name,
                                        ptable.name,
                                        left = left,
                                        limitby = (0, count),
                                        )
        self.queries += 1

        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a row

            @param row: the Row
        """

        try:
            plan = row.fin_subscription_plan
            product = row.fin_product
        except AttributeError:
            plan = row
            product = None

        if product:
            reprstr = "%s: %s" % (product.name, plan.name)
        else:
            reprstr = plan.name

        return reprstr

# =============================================================================
def fin_rheader(r, tabs=None):
    """ FIN Resource Headers """

    if r.representation != "html":
        # Resource headers only used in interactive views
        return None

    tablename, record = s3_rheader_resource(r)
    if tablename != r.tablename:
        resource = current.s3db.resource(tablename, id=record.id)
    else:
        resource = r.resource

    rheader = None
    rheader_fields = []

    if record:

        T = current.T
        if tablename == "fin_voucher_program":

            if not tabs:
                tabs = [(T("Basic Details"), None),
                        (T("Vouchers"), "voucher"),
                        (T("Transactions"), "voucher_transaction"),
                        ]
            rheader_fields = [["organisation_id"],
                              ]
            rheader_title = "name"

        elif tablename == "fin_payment_service":

            if not tabs:
                tabs = [(T("Basic Details"), None),
                        (T("Registered Products"), "product_service"),
                        (T("Subscription Plans"), "subscription_plan_service"),
                        (T("Subscriptions"), "subscription"),
                        (T("Log"), "payment_log"),
                        ]

            rheader_fields = [["organisation_id",
                               "api_type",
                               ],
                              ]
            rheader_title = None

        elif tablename == "fin_product":

            if not tabs:
                tabs = [(T("Basic Details"), None),
                        (T("Payment Services"), "product_service"),
                        (T("Subscription Plans"), "subscription_plan"),
                        ]

            rheader_fields = [["type"],
                              ["organisation_id"],
                              ]
            rheader_title = "name"

        elif tablename == "fin_subscription_plan":

            if not tabs:
                tabs = [(T("Basic Details"), None),
                        (T("Payment Services"), "subscription_plan_service"),
                        (T("Subscriptions"), "subscription"),
                        ]

            rheader_fields = [["product_id"],
                              ]
            rheader_title = "name"

        else:
            return None

        # Generate rheader XML
        rheader = S3ResourceHeader(rheader_fields, tabs, title=rheader_title)(
                        r,
                        table = resource.table,
                        record = record,
                        )

    return rheader

# =============================================================================
class fin_VoucherProgram(object):
    """
        Helper to record transactions in voucher programs
    """

    def __init__(self, program_id):
        """
            Constructor

            @param program_id: the voucher program ID
        """

        self.program_id = program_id
        self._program = None

    # -------------------------------------------------------------------------
    @property
    def program(self):
        """
            The program record (lazy property)

            @returns: the program record (Row)
        """

        program = self._program
        if program is None:

            # Look up program
            table = current.s3db.fin_voucher_program
            query = (table.id == self.program_id) & \
                    (table.status == "ACTIVE") & \
                    (table.deleted == False)
            program = current.db(query).select(table.id,
                                               table.uuid,
                                               table.status,
                                               table.default_credit,
                                               table.validity_period,
                                               table.end_date,
                                               table.credit,
                                               table.compensation,
                                               limitby = (0, 1),
                                               ).first()
            self._program = program

        return program

    # -------------------------------------------------------------------------
    def issue(self, voucher_id, credit=None):
        """
            Transfer credit from the program to the voucher

            @param voucher_id: the new voucher
            @param credit: the initial credit to transfer to the voucher

            @returns: the number of credit transferred to the voucher,
                      or None on failure
        """

        program = self.program
        if not program:
            return None

        table = current.s3db.fin_voucher
        query = (table.id == voucher_id) & \
                (table.program_id == program.id) & \
                (table.deleted == False)
        voucher = current.db(query).select(table.id,
                                           table.balance,
                                           limitby = (0, 1),
                                           ).first()
        if not voucher:
            return None

        if not isinstance(credit, int):
            credit = program.default_credit
        if credit > 0:

            transaction = {"type": "ISS",
                           "credit": -credit,
                           "voucher": credit,
                           "voucher_id": voucher_id,
                           }
            if self.__transaction(transaction):
                voucher.update_record(
                    balance = voucher.balance + transaction["voucher"],
                    )
                program.update_record(
                    credit = program.credit + transaction["credit"],
                    )
            else:
                return None

        return credit if credit > 0 else 0

    # -------------------------------------------------------------------------
    def debit(self, voucher_id, debit_id, credit=None):
        """
            Transfer credit to the provider when redeeming a voucher, i.e.
            debit a voucher.

            Actually a double transaction:
                1) transfer credit from the program's compensation account
                   to the debit
                2) return credit from the voucher to the program's credit
                   account

            @param voucher_id: the voucher ID
            @param debit_id: the debit ID
            @param credit: the credit to transfer (default 1)

            @returns: the credit deducted from the voucher
        """

        program = self.program
        if not program:
            return None
        program_id = program.id

        db = current.db
        s3db = current.s3db

        vtable = s3db.fin_voucher
        query = (vtable.id == voucher_id) & \
                (vtable.program_id == program_id) & \
                (vtable.deleted == False)
        voucher = db(query).select(vtable.id,
                                   vtable.balance,
                                   limitby = (0, 1),
                                   ).first()
        if not voucher:
            return None

        dtable = s3db.fin_voucher_debit
        query = (dtable.id == debit_id) & \
                (dtable.program_id == program_id) & \
                (dtable.deleted == False)
        debit = db(query).select(dtable.id,
                                 dtable.balance,
                                 limitby = (0, 1),
                                 ).first()
        if not debit:
            return None

        if not isinstance(credit, int):
            credit = 1
        if credit > 0:

            transaction = {"type": "DBT",
                           "credit": credit,
                           "voucher": -credit,
                           "debit": credit,
                           "compensation": -credit,
                           "voucher_id": voucher_id,
                           "debit_id": debit_id,
                           }

            if self.__transaction(transaction):
                voucher.update_record(
                    balance = voucher.balance + transaction["voucher"],
                    )
                debit.update_record(
                    balance = debit.balance + transaction["debit"],
                    )
                program.update_record(
                    credit = program.credit + transaction["credit"],
                    compensation = program.compensation + transaction["compensation"]
                    )
            else:
                return None

        return credit

    # -------------------------------------------------------------------------
    def compensate(self, debit_id):
        # TODO implement this once we have a compensation model
        pass

    # -------------------------------------------------------------------------
    def verify(self, transaction_id):
        """
            Verify integrity of a transaction (=check the vhash)

            @param transaction_id: the transaction record ID

            @returns: True|False whether the transaction is intact
        """

        db = current.db
        table = current.s3db.fin_voucher_transaction

        # Get the transaction record
        query = (table.id == transaction_id)
        transaction = db(query).select(table.ALL,
                                       limitby = (0, 1),
                                       ).first()
        if not transaction:
            return False

        # Get preceding transaction's hash
        ouuid = transaction.ouuid
        if ouuid:
            query = (table.uuid == ouuid) & \
                    (table.program_id == transaction.program_id)
            p_transaction = db(query).select(table.vhash,
                                             limitby = (0, 1),
                                             ).first()
            if p_transaction is None:
                return False
            ohash = p_transaction.vhash
        else:
            ohash = None

        # Verify the hash
        data = {"ouuid": ouuid,
                "date": transaction.date,
                "type": transaction.type,
                "credit": transaction.credit,
                "voucher": transaction.voucher,
                "debit": transaction.debit,
                "compensation": transaction.compensation,
                "voucher_id": transaction.voucher_id,
                "debit_id": transaction.debit_id,
                }
        vhash = self._hash(data, ohash)

        return vhash == transaction.vhash

    # -------------------------------------------------------------------------
    def audit(self, correct=False):
        """
            Run a full audit of the entire program:
            - verify all transactions
            - verify all balances, vouchers and debits

            @param correct: correct any incorrect balances

            @returns: audit report

            TODO: implement
        """

        return True

    # -------------------------------------------------------------------------
    def _hash(self, transaction, ohash):
        """
            Generate a verification hash (vhash) for the transaction

            @param transaction: the transaction data
            @param ohash: the hash of the preceding transaction

            @returns: the hash as string
        """

        # Generate signature from transaction data
        signature = {}
        signature.update(transaction)
        signature["date"] = s3_format_datetime(transaction["date"])

        # Hash it, together with program UUID and ohash
        data = {"puuid": self.program.uuid,
                "ohash": ohash,
                "signature": signature,
                }
        inp = json.dumps(data, separators=SEPARATORS)

        crypt = CRYPT(key = current.deployment_settings.hmac_key,
                      digest_alg = "sha512",
                      salt = False,
                      )
        return str(crypt(inp)[0])

    # -------------------------------------------------------------------------
    def __transaction(self, data):
        """
            Record a transaction under this program

            @param data: the transaction details

            @returns: True|False for success or failure
        """

        program = self.program
        if not program:
            return False

        # Prevent recording of unbalanced transactions
        total = data.get("credit", 0) + \
                data.get("voucher", 0) + \
                data.get("debit", 0) + \
                data.get("compensation", 0)
        if total != 0:
            # Invalid - total change must always be 0
            return False

        # Get last preceding transaction in this program
        table = current.s3db.fin_voucher_transaction
        query = (table.program_id == program.id)
        row = current.db(query).select(table.uuid,
                                       table.vhash,
                                       limitby = (0, 1),
                                       orderby = ~(table.created_on)
                                       ).first()
        if row:
            ouuid = row.uuid
            ohash = row.vhash
        else:
            # This is the first transaction
            ouuid = ohash = None

        # Build the transaction record
        transaction = {"ouuid": ouuid,
                       "date": current.request.utcnow,
                       "type": None,
                       "credit": 0,
                       "voucher": 0,
                       "debit": 0,
                       "compensation": 0,
                       "voucher_id": None,
                       "debit_id": None
                       }
        transaction.update(data)
        transaction["ouuid"] = ouuid
        transaction["vhash"] = self._hash(transaction, ohash)
        transaction["program_id"] = program.id

        s3db = current.s3db

        # Write the transaction
        table = s3db.fin_voucher_transaction
        transaction["id"] = table.insert(**transaction)

        # Post-process it
        current.auth.s3_set_record_owner(table, transaction)
        s3db.onaccept(table, transaction, method="create")

        return True

# =============================================================================
def fin_voucher_permitted_programs(mode="issuer"):
    """
        Get a list of programs and organisations the current user
        is permitted to issue/accept vouchers for

        @param mode: the permission to look for ('issuer'|'provider')

        @returns: tuple of lists (program_ids, org_ids, pe_ids)
    """

    s3db = current.s3db

    otable = s3db.org_organisation
    ptable = s3db.fin_voucher_program
    mtable = s3db.org_group_membership

    permitted_realms = current.auth.permission.permitted_realms
    if mode == "issuer":
        fn = "issuers_id"
        realms = permitted_realms("fin_voucher", "create")
    else:
        fn = "providers_id"
        realms = permitted_realms("fin_voucher_debit", "create")

    if realms is not None and not realms:
        # No access to any programs for any orgs
        return None, None, None

    today = current.request.utcnow.date()
    join = [mtable.on((mtable.organisation_id == otable.id) & \
                      (mtable.deleted == False)),
            ptable.on((ptable[fn] == mtable.group_id) & \
                      (ptable.deleted == False) & \
                      (ptable.status == "ACTIVE") & \
                      ((ptable.end_date == None) | (ptable.end_date >= today))),
            ]

    query = (otable.deleted == False)
    if realms:
        query = (otable.pe_id.belongs(realms)) & query

    rows = current.db(query).select(otable.id,
                                    otable.pe_id,
                                    ptable.id,
                                    join = join,
                                    )

    program_ids = set()
    org_ids = set()
    pe_ids = set()
    for row in rows:
        program_ids.add(row.fin_voucher_program.id)

        organisation = row.org_organisation
        org_ids.add(organisation.id)
        pe_ids.add(organisation.pe_id)

    return list(program_ids), list(org_ids), list(pe_ids)

# END =========================================================================
