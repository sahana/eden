"""
    Finance Tables

    Copyright: 2015-2022 (c) Sahana Software Foundation

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
           "fin_VoucherProgram",
           "fin_VoucherBilling",
           "fin_rheader",
           "fin_voucher_permitted_programs",
           "fin_voucher_eligibility_types",
           "fin_voucher_start_billing",
           "fin_voucher_settle_invoice",
           )

from collections import OrderedDict

from gluon import *
from ..core import *

# =============================================================================
class FinExpensesModel(DataModel):
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
                          DateField(),
                          Field("value", "double",
                                label = T("Value"),
                                represent = lambda v: \
                                    IS_FLOAT_AMOUNT.represent(v, precision=2),
                                ),
                          CurrencyField(),
                          CommentsField(),
                          on_define = lambda table: \
                            [table.created_by.set_attributes(represent = self.auth_UserRepresent(show_email = False,
                                                                                                 show_link = False)),
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

        crud_form = CustomForm("name",
                               "date",
                               "value",
                               "currency",
                               InlineComponent(
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

        expense_id = FieldTemplate("expense_id", "reference %s" % tablename,
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
    def defaults(self):
        """
            Return safe defaults in case the model has been deactivated.
        """

        return {"fin_expense_id": FieldTemplate.dummy("expense_id"),
                }

# =============================================================================
class FinVoucherModel(DataModel):
    """ Model for Voucher Programs """

    names = ("fin_voucher_program",
             "fin_voucher_billing",
             "fin_voucher_claim",
             "fin_voucher_invoice",
             "fin_voucher_eligibility_type",
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

        use_eligibility_types = settings.get_fin_voucher_eligibility_types()

        price_represent = lambda v, row=None: \
                          IS_FLOAT_AMOUNT.represent(v, precision=2, fixed=True)

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
        org_group_represent = org_group_id().represent
        org_group_requires = IS_EMPTY_OR(IS_ONE_OF(db, "org_group.id",
                                                   org_group_represent,
                                                   sort = True,
                                                   ))
        tablename = "fin_voucher_program"
        define_table(tablename,
                     self.org_organisation_id(
                            label = T("Administrator##fin"),
                            comment = None,
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
                           represent = represent_option(dict(program_status)),
                           requires = IS_IN_SET(program_status,
                                                zero = None,
                                                sort = False,
                                                ),
                           ),
                     DateField("end_date",
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
                     # Compensation Details:
                     Field("unit",
                           label = T("Unit of Service"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Unit of Service"),
                                                           T('Unit to determine the service quantity (e.g. "Meals")'),
                                                           ),
                                         ),
                           ),
                     Field("price_per_unit", "float",
                           label = T("Price per Unit"),
                           default = 0,
                           requires = IS_FLOAT_AMOUNT(0),
                           represent = price_represent,
                           ),
                     CurrencyField(),
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
                     CommentsField(),
                     )

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
                            fin_voucher_eligibility_type = "program_id",
                            fin_voucher_billing = "program_id",
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

        # Foreign Key Template
        represent = S3Represent(lookup = tablename)
        program_id = FieldTemplate("program_id", "reference %s" % tablename,
                                   label = T("Program"),
                                   represent = represent,
                                   requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "%s.id" % tablename,
                                                          represent,
                                                          )),
                                   )

        # -------------------------------------------------------------------------
        # Voucher billing
        # - billing process for a voucher program
        #
        billing_status = (("SCHEDULED", T("Scheduled")),
                          ("ABORTED", T("Aborted")),
                          )
        billing_status_opts = dict(billing_status)

        # Additional statuses that cannot be entered or imported
        billing_status_opts["IN PROGRESS"] = T("In Progress")
        billing_status_opts["COMPLETE"] = T("Completed")

        tablename = "fin_voucher_billing"
        define_table(tablename,
                     program_id(ondelete="RESTRICT"),
                     self.org_organisation_id(
                            label = T("Accountant##billing"),
                            comment = None,
                            ),
                     DateField(default = "now",
                               writable = False, # Only writable while scheduled
                               ),
                     Field("status",
                           default = "SCHEDULED",
                           requires = IS_IN_SET(billing_status,
                                                zero = None,
                                                ),
                           represent = S3Represent(options=billing_status_opts),
                           writable = False, # Only writable while scheduled
                           ),
                     Field("vouchers_total", "integer",
                           label = T("Total number of vouchers"),
                           default = 0,
                           writable = False,
                           ),
                     Field("quantity_total", "integer",
                           label = T("Total quantity of service"),
                           default = 0,
                           writable = False,
                           ),
                     Field("quantity_invoiced", "integer",
                           label = T("Service quantity invoiced"),
                           default = 0,
                           writable = False,
                           ),
                     Field("quantity_compensated", "integer",
                           label = T("Service quantity compensated"),
                           default = 0,
                           writable = False,
                           ),
                     Field("verification", "text",
                           label = T("Verification Details"),
                           represent = s3_text_represent,
                           writable = False,
                           ),
                     Field("task_id", "reference scheduler_task",
                           ondelete = "SET NULL",
                           readable = False,
                           writable = False,
                           ),
                     CommentsField(),
                     )

        # Components
        self.add_components(tablename,
                            fin_voucher_claim = "billing_id",
                            fin_voucher_invoice = "billing_id",
                            )

        # List fields
        list_fields = ["program_id",
                       "date",
                       "organisation_id",
                       "quantity_total",
                       "quantity_invoiced",
                       "quantity_compensated",
                       "status",
                       ]

        # Table configureation
        self.configure(tablename,
                       list_fields = list_fields,
                       deletable = False, # must cancel, not delete
                       onvalidation = self.billing_onvalidation,
                       onaccept = self.billing_onaccept,
                       )

        # Foreign Key Template
        represent = S3Represent(lookup = tablename,
                                fields = ["date"],
                                labels = lambda row: S3DateTime.date_represent(row.date,
                                                                               utc = True,
                                                                               ),
                                )
        billing_id = FieldTemplate("billing_id", "reference %s" % tablename,
                                   label = T("Billing"),
                                   represent = represent,
                                   requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "%s.id" % tablename,
                                                          represent,
                                                          )),
                                   )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Billing"),
            title_display = T("Billing Details"),
            title_list = T("Billings"),
            title_update = T("Edit Billing"),
            label_list_button = T("List Billings"),
            label_delete_button = T("Delete Billing"),
            msg_record_created = T("Billing created"),
            msg_record_modified = T("Billing updated"),
            msg_record_deleted = T("Billing deleted"),
            msg_list_empty = T("No Billings currently registered"),
        )

        # -------------------------------------------------------------------------
        # Voucher invoice
        # - invoice for a provider claim
        #
        workflow = (("NEW", T("New")),
                    ("VERIFIED", T("Verified")),
                    ("APPROVED", T("Approved##actionable")),
                    ("REJECTED", T("Rejected##claim")),
                    ("PAID", T("Paid")),
                    )
        mandatory = ("NEW", "REJECTED", "PAID")

        # Apply custom labels
        custom_labels = settings.get_fin_voucher_invoice_status_labels()
        if custom_labels:
            invoice_status = []
            default = lambda: None
            for k, v in workflow:
                custom_label = custom_labels.get(k, default)
                if custom_label is default:
                    invoice_status.append((k, v))
                elif k in mandatory or custom_label:
                    invoice_status.append((k, T(custom_label) if custom_label else v))
        else:
            invoice_status = workflow

        tablename = "fin_voucher_invoice"
        define_table(tablename,
                     program_id(empty = False,
                                writable = False,
                                ),
                     billing_id(empty = False,
                                writable = False,
                                ),
                     Field("pe_id", "reference pr_pentity",
                           label = T("Provider##fin"),
                           represent = pe_represent,
                           requires = IS_EMPTY_OR(IS_ONE_OF(db, "pr_pentity.pe_id",
                                                            pe_represent,
                                                            instance_types = ["org_organisation"],
                                                            )),
                           writable = False,
                           ),

                     # Date of invoice
                     DateField(label = T("Invoice Date"),
                               default = "now",
                               writable = False,
                               ),

                     # Payer references
                     Field("invoice_no",
                           label = T("Invoice No."),
                           represent = lambda v, row=None: v if v else "-",
                           writable = False,
                           ),
                     Field("refno",
                           label = T("Ref.No."),
                           represent = lambda v, row=None: v if v else "-",
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Ref.No."),
                                                           T("Internal identifier to track the payment (optional), e.g. payment order number"),
                                                           ),
                                         ),
                           ),
                     self.hrm_human_resource_id(
                            label = T("Official in Charge"),
                            widget = None,
                            comment = None,
                            ),

                     # Totals
                     Field("quantity_total", "integer",
                           label = T("Service Quantity"),
                           writable = False,
                           ),
                     Field("price_per_unit", "float",
                           label = T("Price per Unit"),
                           represent = price_represent,
                           writable = False,
                           ),
                     Field("amount_receivable", "float",
                           label = T("Amount Receivable"),
                           represent = price_represent,
                           writable = False,
                           ),
                     CurrencyField(writable = False),

                     # Bank account details
                     Field("account_holder",
                           label = T("Account Holder"),
                           writable = False,
                           ),
                     Field("account_number",
                           label = T("Account Number (IBAN)"),
                           requires = IS_IBAN(),
                           represent = IS_IBAN.represent,
                           writable = False,
                           ),
                     Field("bank_name",
                           label = T("Bank Name"),
                           writable = False,
                           ),
                     Field("bank_address",
                           label = T("Bank Address"),
                           # Enable in template if required:
                           readable = False,
                           writable = False,
                           ),

                     # Status (and reason for status)
                     Field("status",
                           default = "NEW",
                           label = T("Status"),
                           requires = IS_IN_SET(invoice_status,
                                                zero = None,
                                                ),
                           represent = represent_option(dict(invoice_status)),
                           writable = False,
                           ),
                     Field("reason", "text",
                           label = T("Reason for Rejection"),
                           represent = s3_text_represent,
                           widget = s3_comments_widget,
                           writable = False,
                           ),

                     # Verification hash of the underlying claim
                     Field("vhash", "text",
                           readable = False,
                           writable = False,
                           ),
                     # Processing authorization token for async tasks
                     Field("ptoken",
                           readable = False,
                           writable = False,
                           ),
                     CommentsField(),
                     )

        # Components
        self.add_components(tablename,
                            fin_voucher_claim = {"joinby": "invoice_id",
                                                 "multiple": False,
                                                 },
                            )

        # List fields
        list_fields = ["date",
                       "invoice_no",
                       "program_id",
                       "billing_id",
                       "pe_id",
                       "amount_receivable",
                       "refno",
                       "status",
                       ]

        # Filter widgets
        filter_widgets = [TextFilter(["invoice_no",
                                      "refno",
                                      ],
                                     label = T("Search"),
                                     ),
                          OptionsFilter("status",
                                        options = OrderedDict(invoice_status),
                                        sort = False,
                                        ),
                          OptionsFilter("human_resource_id",
                                        ),
                          ]

        self.configure(tablename,
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       insertable = False, # will be auto-created from claim
                       deletable = False,
                       onvalidation = self.invoice_onvalidation,
                       onaccept = self.invoice_onaccept,
                       orderby = "%s.date desc" % tablename,
                       )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Invoice"),
            title_display = T("Invoice Details"),
            title_list = T("Invoices"),
            title_update = T("Edit Invoice"),
            label_list_button = T("List Invoices"),
            label_delete_button = T("Delete Invoice"),
            msg_record_created = T("Invoice created"),
            msg_record_modified = T("Invoice updated"),
            msg_record_deleted = T("Invoice deleted"),
            msg_list_empty = T("No Invoices currently registered"),
        )

        # Foreign Key Template
        represent = fin_VoucherInvoiceRepresent()
        invoice_id = FieldTemplate("invoice_id", "reference %s" % tablename,
                                   label = T("Invoice"),
                                   represent = represent,
                                   requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "%s.id" % tablename,
                                                          represent,
                                                          )),
                                   )


        # -------------------------------------------------------------------------
        # Compensation claim
        # - provider-issued claim for compensation under a billing cycle
        #
        claim_status = (("NEW", T("New")),
                        ("CONFIRMED", T("Confirmed")),
                        #("INVOICED", T("Invoiced")),
                        #("PAID", T("Paid")),
                        )
        claim_status_opts = dict(claim_status)

        # Additional statuses that cannot be entered or imported
        claim_status_opts["INVOICED"] = T("Invoiced")
        paid_label = settings.get_fin_voucher_claim_paid_label()
        claim_status_opts["PAID"] = T(paid_label) if paid_label else T("Paid")

        tablename = "fin_voucher_claim"
        define_table(tablename,
                     program_id(writable=False),
                     billing_id(writable=False),
                     Field("pe_id", "reference pr_pentity",
                           label = T("Provider##fin"),
                           represent = pe_represent,
                           requires = IS_EMPTY_OR(IS_ONE_OF(db, "pr_pentity.pe_id",
                                                            pe_represent,
                                                            instance_types = ["org_organisation"],
                                                            )),
                           writable = False,
                           ),

                     # Date of claim
                     DateField(default = "now",
                               writable = False,
                               ),

                     # Claimant reference number
                     Field("refno",
                           label = T("Ref.No."),
                           represent = lambda v, row=None: v if v else "-",
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Ref.No."),
                                                           T("A reference number for bookkeeping purposes (optional, for your own use)"),
                                                           ),
                                         ),
                           ),

                     # Totals
                     Field("vouchers_total", "integer",
                           label = T("Number of Vouchers"),
                           writable = False,
                           ),
                     Field("quantity_total", "integer",
                           label = T("Service Quantity"),
                           writable = False,
                           ),
                     Field("price_per_unit", "float",
                           label = T("Price per Unit"),
                           represent = price_represent,
                           writable = False,
                           ),
                     Field("amount_receivable", "float",
                           label = T("Amount Receivable"),
                           represent = price_represent,
                           writable = False,
                           ),
                     CurrencyField(writable=False),

                     # Bank account details
                     Field("account_holder",
                           label = T("Account Holder"),
                           represent = lambda v, row=None: v if v else "-",
                           writable = False,
                           ),
                     Field("account_number",
                           label = T("Account Number (IBAN)"),
                           requires = IS_EMPTY_OR(IS_IBAN()),
                           represent = IS_IBAN.represent,
                           writable = False,
                           ),
                     Field("bank_name",
                           label = T("Bank Name"),
                           represent = lambda v, row=None: v if v else "-",
                           writable = False,
                           ),
                     Field("bank_address",
                           label = T("Bank Address"),
                           represent = lambda v, row=None: v if v else "-",
                           # Enable in template if required:
                           readable = False,
                           writable = False,
                           ),

                     # Status
                     Field("status",
                           default = "NEW",
                           label = T("Status"),
                           requires = IS_IN_SET(claim_status,
                                                zero = None,
                                                ),
                           represent = represent_option(claim_status_opts),
                           writable = False,
                           ),

                     # Invoice details
                     invoice_id(writable=False),
                     Field("vhash", "text",
                           readable = False,
                           writable = False,
                           ),

                     CommentsField(),
                     )

        # Components
        self.add_components(tablename,
                            fin_voucher_debit = "claim_id",
                            )

        # List fields
        list_fields = ["id",
                       "refno",
                       "program_id",
                       "date",
                       "vouchers_total",
                       "quantity_total",
                       "amount_receivable",
                       "currency",
                       "status",
                       ]

        # Table configuration
        self.configure(tablename,
                       list_fields = list_fields,
                       insertable = False,
                       deletable = False,
                       onvalidation = self.claim_onvalidation,
                       onaccept = self.claim_onaccept,
                       )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Compensation Claim"),
            title_display = T("Compensation Claim Details"),
            title_list = T("Compensation Claims"),
            title_update = T("Edit Compensation Claim"),
            label_list_button = T("List Compensation Claims"),
            label_delete_button = T("Delete Compensation Claim"),
            msg_record_created = T("Compensation Claim created"),
            msg_record_modified = T("Compensation Claim updated"),
            msg_record_deleted = T("Compensation Claim deleted"),
            msg_list_empty = T("No Compensation Claims currently registered"),
        )

        # Foreign Key Template
        represent = S3Represent(lookup=tablename, fields=["refno", "date"])
        claim_id = FieldTemplate("claim_id", "reference %s" % tablename,
                                 label = T("Compensation Claim"),
                                 represent = represent,
                                 requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "%s.id" % tablename,
                                                          represent,
                                                          )),
                                 )

        # -------------------------------------------------------------------------
        # Voucher eligibility type
        # - represents a eligibility criterion for beneficiaries of a
        #   voucher program
        #
        tablename = "fin_voucher_eligibility_type"
        define_table(tablename,
                     program_id(empty=False),
                     Field("name",
                           label = T("Type of Eligibility"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("issuer_types", "list:reference org_organisation_type",
                           label = T("Permitted Issuers"),
                           represent = S3Represent(lookup = "org_organisation_type",
                                                   multiple = True,
                                                   translate = True,
                                                   ),
                           requires = IS_EMPTY_OR(
                                        IS_ONE_OF(db, "org_organisation_type.id",
                                                  S3Represent(lookup = "org_organisation_type",
                                                              translate = True,
                                                              ),
                                                  multiple = True,
                                                  )),
                           widget = S3MultiSelectWidget(),
                           ),
                     CommentsField(),
                     )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Eligibility Type"),
            title_display = T("Eligibility Type Details"),
            title_list = T("Eligibility Types"),
            title_update = T("Edit Eligibility Type"),
            label_list_button = T("List Eligibility Types"),
            label_delete_button = T("Delete Eligibility Type"),
            msg_record_created = T("Eligibility Type created"),
            msg_record_modified = T("Eligibility Type updated"),
            msg_record_deleted = T("Eligibility Type deleted"),
            msg_list_empty = T("No Eligibility Types currently defined"),
        )

        represent = S3Represent(lookup = tablename, translate = True)
        eligibility_type_id = FieldTemplate("eligibility_type_id", "reference %s" % tablename,
                                            label = T("Type of Eligibility"),
                                            ondelete = "RESTRICT",
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
                           label = T("Issuer##fin"),
                           represent = pe_represent,
                           requires = IS_EMPTY_OR(IS_ONE_OF(db, "pr_pentity.pe_id",
                                                            pe_represent,
                                                            instance_types = ["org_organisation"],
                                                            )),
                           ),
                     eligibility_type_id(
                            readable = use_eligibility_types,
                            writable = use_eligibility_types,
                            ),
                     Field("signature", length=64,
                           label = T("Voucher ID"),
                           writable = False,
                           ),
                     DateField("bearer_dob",
                               future = 0,
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
                     Field("initial_credit", "integer",
                           label = T("Initial Credit##fin"),
                           requires = IS_INT_IN_RANGE(1),
                           readable = False,
                           writable = False,
                           ),
                     Field("credit_spent", "integer",
                           label = T("Credit Redeemed"),
                           default = 0,
                           writable = False,
                           ),
                     Field("single_debit", "boolean",
                           default = True,
                           label = T("Voucher can only be used once"),
                           readable = False,
                           writable = False,
                           ),
                     Field("balance", "integer",
                           label = T("Credit##fin"),
                           default = 0,
                           writable = False,
                           ),
                     DateField(label = T("Issued On"),
                               default = "now",
                               writable = False,
                               ),
                     DateField("valid_until",
                               label = T("Valid Until"),
                               writable = False,
                               ),
                     Field.Virtual("status", self.voucher_status,
                                   label = T("Status"),
                                   ),
                     CommentsField(),
                     )

        # TODO Bearer notes?

        # Table Configuration
        self.configure(tablename,
                       extra_fields = ["balance"],
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

        # Foreign Key Template
        voucher_id = FieldTemplate("voucher_id", "reference %s" % tablename,
                                   ondelete = "RESTRICT",
                                   requires = IS_ONE_OF(db, "%s.id" % tablename),
                                   )

        # -------------------------------------------------------------------------
        # Voucher debit
        # - represents a debt of the program owner owed to the service provider
        #   for redeeming a voucher
        #
        tablename = "fin_voucher_debit"
        define_table(tablename,
                     program_id(empty = False),
                     voucher_id(readable = False,
                                writable = False,
                                ),
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
                           represent = lambda v, row=None: v if v else "-",
                           widget = S3QRInput(),
                           ),
                     DateField("bearer_dob",
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
                     DateField(default = "now",
                               label = T("Date Effected"),
                               writable = False,
                               ),
                     Field("quantity", "integer",
                           label = T("Service Quantity"),
                           requires = IS_INT_IN_RANGE(1),
                           readable = False,
                           writable = False,
                           ),
                     Field("balance", "integer",
                           label = T("Balance##fin"),
                           default = 0,
                           writable = False,
                           ),
                     Field("cancelled", "boolean",
                           label = T("Cancelled##fin"),
                           default = False,
                           represent = s3_yes_no_represent,
                           writable = False,
                           ),
                     Field("cancel_reason",
                           label = T("Reason for Cancellation##fin"),
                           represent = lambda v, row=None: v if v else "-",
                           writable = False,
                           ),
                     # Billing details (internal)
                     billing_id(readable = False,
                                writable = False,
                                ),
                     claim_id(readable = False,
                              writable = False,
                              ),
                     Field.Virtual("status", self.debit_status,
                                   label = T("Status"),
                                   ),
                     CommentsField(),
                     )

        # Table Configuration
        self.configure(tablename,
                       extra_fields = ["balance", "cancelled"],
                       editable = False,
                       deletable = False,
                       onvalidation = self.debit_onvalidation,
                       create_onaccept = self.debit_create_onaccept,
                       )

        self.set_method("fin_voucher_debit",
                        method = "cancel",
                        action = fin_VoucherCancelDebit,
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

        # Foreign Key Template
        debit_id = FieldTemplate("debit_id", "reference %s" % tablename,
                                 ondelete = "RESTRICT",
                                 requires = IS_ONE_OF(db, "%s.id" % tablename),
                                 )

        # -------------------------------------------------------------------------
        # Voucher transaction
        # - records a debt transaction for a voucher program

        # Transaction types:
        #  - ISS: credit -x => voucher +x
        #  - VOI: credit +x => voucher -x
        #  - DBT: credit +1 <= voucher -1, debit +1 <= compensation -1
        #  - CNC: credit -1 => voucher +1, debit -1 => compensation +1
        #  - CMP: debit -1 => compensation +1
        #
        transaction_types = {"ISS": T("Issued##fin"),
                             "VOI": T("Voided##fin"),
                             "DBT": T("Redeemed##fin"),
                             "CMP": T("Compensated##fin"),
                             "CNC": T("Cancelled##fin"),
                             }

        tablename = "fin_voucher_transaction"
        define_table(tablename,
                     program_id(empty = False),
                     DateTimeField(default="now"),
                     Field("type",
                           label = T("Type"),
                           represent = represent_option(transaction_types),
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
                     )

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
        return {"fin_voucher_invoice_status": dict(invoice_status),
                "fin_voucher_claim_status_opts": claim_status_opts,
                "fin_voucher_billing_status_opts": billing_status_opts,
                }

    # -------------------------------------------------------------------------
    def defaults(self):
        """ Safe defaults for names in case the module is disabled """

        return {"fin_voucher_invoice_status": {},
                "fin_voucher_claim_status_opts": {},
                "fin_voucher_billing_status_opts": {},
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def billing_onvalidation(form):
        """
            Validation of billing form:
            - must not change date or status once process has started
            - can only change status to ABORT before start
            - date must be after any active or completed billing
            - date must be on a different day than any scheduled billing
        """

        T = current.T

        db = current.db
        s3db = current.s3db

        form_vars = form.vars
        if "id" in form_vars:
            record_id = form_vars.id
        elif hasattr(form, "record_id"):
            record_id = form.record_id
        else:
            record_id = None

        table = s3db.fin_voucher_billing

        # Get the existing record
        if record_id:
            query = (table.id == record_id)
            record = db(query).select(table.id,
                                      table.program_id,
                                      table.date,
                                      table.status,
                                      limitby=(0, 1),
                                      ).first()
        else:
            record = None

        # Get the program
        if "program_id" in form_vars:
            program_id = form_vars["program_id"]
        elif record:
            program_id = record.program_id
        else:
            program_id = table.program_id.default

        date_error = False
        if record:
            # Update
            if "date" in form_vars:
                date = form_vars["date"]
                if record.status != "SCHEDULED" and record.date != date:
                    form.errors.date = T("Date can only be changed while process has not yet started")
                    date_error = True

            if "status" in form_vars:
                status = form_vars["status"]
                if status != record.status:
                    if record.status != "SCHEDULED":
                        form.errors.status = T("Status cannot be changed once process has started")
                    elif status != "ABORTED":
                        form.errors.status = T("Invalid status")

        if not date_error and "date" in form_vars:
            date = form_vars["date"]
            if date:
                p = fin_VoucherProgram(program_id)
                earliest = p.earliest_billing_date(billing_id = record_id)
                if earliest and date < earliest:
                    form.errors.date = T("Date must be %(min)s or later!") % {"min": earliest}
                else:
                    query = (table.program_id == program_id)
                    if record_id:
                        query &= (table.id != record_id)
                    query &= (table.status == "SCHEDULED") & \
                             (table.date == date) & \
                             (table.deleted == False)
                    row = db(query).select(table.id, limitby = (0, 1)).first()
                    if row:
                        form.errors.date = T("Billing already scheduled for that date")

    # -------------------------------------------------------------------------
    @staticmethod
    def billing_onaccept(form):
        """
            Onaccept-routine for billing
              - schedule task to start the process
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

        # Get the record
        table = s3db.fin_voucher_billing
        query = (table.id == record_id)
        billing = db(query).select(table.id,
                                   table.date,
                                   table.status,
                                   table.task_id,
                                   limitby = (0, 1),
                                   ).first()

        if not billing:
            return

        # Get the scheduler task (if any)
        ttable = s3db.scheduler_task
        task_id = billing.task_id
        if task_id:
            query = (ttable.id == task_id)
            task = db(query).select(ttable.id,
                                    ttable.status,
                                    ttable.start_time,
                                    ttable.next_run_time,
                                    limitby = (0, 1),
                                    ).first()
        else:
            task = None

        if billing.status == "SCHEDULED" and billing.date:

            now = datetime.datetime.utcnow()
            start = datetime.datetime.combine(billing.date, datetime.time(0,0,0))
            if start < now:
                # Earliest start time 30 seconds in the future
                # => to leave a grace period to manually abort the process
                start = now + datetime.timedelta(seconds=30)

            if task:
                # Make sure task starts at the right time
                if task.status not in ("ASSIGNED", "RUNNING"):
                    task.update_record(start_time = start,
                                       next_run_time = start,
                                       stop_time = None,
                                       status = "QUEUED",
                                       enabled = True,
                                       )
            else:
                # Allow application name override
                ttable.application_name.writable = True

                # Schedule task
                scheduler = current.s3task.scheduler
                task = scheduler.queue_task("s3db_task",
                                            application_name = "%s/default" % \
                                                               current.request.application,
                                            pargs = ["fin_voucher_start_billing"],
                                            pvars = {"billing_id": billing.id},
                                            start_time = start,
                                            stop_time = None,
                                            timeout = 1800,
                                            repeats = 1,
                                            )
                task_id = task["id"]

        elif task and task.status == "QUEUED":
            # Remove the task
            task.delete_record()
            task_id = None

        # Store the task_id
        billing.update_record(task_id = task_id,
                              modified_by = table.modified_by,
                              modified_on = table.modified_on,
                              )

    # -------------------------------------------------------------------------
    @staticmethod
    def claim_onvalidation(form):
        """
            Onvalidation of claims:
                - if claim has already been confirmed, or even invoiced,
                  immutable fields can no longer be changed
                - if claim is to be any other status than new, bank account
                  details are required
        """

        form_vars = form.vars
        if "id" in form_vars:
            record_id = form_vars.id
        elif hasattr(form, "record_id"):
            record_id = form.record_id
        else:
            record_id = None

        db = current.db
        s3db = current.s3db

        table = s3db.fin_voucher_claim
        if record_id:
            # Get the record
            query = (table.id == record_id)
            record = db(query).select(table.id,
                                      table.status,
                                      table.invoice_id,
                                      table.account_holder,
                                      table.account_number,
                                      limitby = (0, 1),
                                      ).first()
        else:
            record = None

        T = current.T

        has_status = "status" in form_vars
        status = form_vars.get("status")

        if record:

            change_status = has_status and status != record.status
            check = {"account_holder": T("Account holder is required"),
                     "account_number": T("Account number is required"),
                     }
            if record.invoice_id or record.status != "NEW":
                # This claim has already been invoiced and cannot be changed
                immutable = ("program_id", "billing_id", "pe_id",
                             "date", "vouchers_total", "quantity_total",
                             "price_per_unit", "amount_receivable",
                             "account_holder", "account_number",
                             "status", "invoice_id",
                             )
                for fn in immutable:
                    if fn in form_vars:
                        form.errors[fn] = T("Value can no longer be changed")

            elif record.status == "NEW" and \
                 has_status and not change_status and \
                 all(fn in form_vars and form_vars[fn] or record[fn] for fn in check):

                # Warn if the user has entered bank account details, but
                # not confirmed the claim
                current.response.warning = T('You must change the status to "confirmed" before an invoice can be issued')

            elif change_status and status != "NEW":
                # Changing status of a NEW claim requires account details
                for fn, msg in check.items():
                    value = form_vars[fn] if fn in form_vars else record[fn]
                    if value is None or not value.strip():
                        if fn in form_vars:
                            form.errors[fn] = msg
                        else:
                            form.errors["status"] = msg
                            break

        elif change_status and status != "NEW":
            # A new claim can only have status "NEW"
            form.errors["status"] = T("Invalid status")

    # -------------------------------------------------------------------------
    @staticmethod
    def claim_onaccept(form):

        form_vars = form.vars
        if "id" in form_vars:
            record_id = form_vars.id
        elif hasattr(form, "record_id"):
            record_id = form.record_id
        else:
            return

        db = current.db
        s3db = current.s3db

        table = s3db.fin_voucher_claim
        query = (table.id == record_id)
        record = db(query).select(table.id,
                                  table.billing_id,
                                  table.status,
                                  table.invoice_id,
                                  table.comments,
                                  limitby = (0, 1),
                                  ).first()
        if not record:
            return

        billing_id = record.billing_id
        if billing_id and \
           record.status == "CONFIRMED" and not record.invoice_id:
            error = fin_VoucherBilling.generate_invoice(record.id)[1]
            if error:
                # Write error into comments
                msg = "%s Could not generate invoice - ERROR: %s" % \
                      (current.request.utcnow.isoformat(), error)
                current.response.warning = msg
                comments = [msg]
                if record.comments:
                    comments.append(record.comments)
                record.update_record(comments = "\n\n".join(comments))
            else:
                current.session.information = current.T("Invoice issued")

    # -------------------------------------------------------------------------
    @staticmethod
    def invoice_onvalidation(form):
        """
            Onvalidation of invoices:
              - new invoices can only have status NEW
              - status PAID requires payment order number
              - status REJECTED requires a reason
              - changing status to anything other than NEW or REJECTED
                requires the verification hashes to be intact and the claim
                to have INVOICED status
              - once marked as PAID, the status can no longer be changed
        """

        form_vars = form.vars
        if "id" in form_vars:
            record_id = form_vars.id
        elif hasattr(form, "record_id"):
            record_id = form.record_id
        else:
            record_id = None

        db = current.db
        s3db = current.s3db

        table = s3db.fin_voucher_invoice
        if record_id:
            # Get the record
            query = (table.id == record_id)
            record = db(query).select(table.id,
                                      table.status,
                                      limitby = (0, 1),
                                      ).first()
        else:
            record = None

        T = current.T

        status = form_vars.get("status")
        change_status = "status" in form_vars
        if record:
            change_status = change_status and status != record.status
            status_error = False

            if record.status == "PAID":
                # Status cannot be changed
                if change_status:
                    form.errors.status = T("Status cannot be changed")
                    status_error = True

            elif change_status and status not in ("NEW", "REJECTED"):
                # Verify the hashes
                if not fin_VoucherBilling.check_invoice(record.id):
                    form.errors.status = T("Invoice integrity compromised")
                    status_error = True
                else:
                    # Verify that the claim status is INVOICED
                    ctable = s3db.fin_voucher_claim
                    query = (ctable.invoice_id == record.id) & \
                            (ctable.deleted == False)
                    claim = db(query).select(ctable.id,
                                             ctable.status,
                                             limitby = (0, 1),
                                             ).first()
                    if not claim or claim.status != "INVOICED":
                        form.errors.status = T("Claim has incorrect status")
                        status_error = True

            if not status_error:
                # Check required fields
                if not change_status:
                    status = record.status
                if status == "REJECTED":
                    # Rejection requires a reason
                    ff = fn = "reason"
                    if fn in form_vars:
                        value = form_vars[fn]
                    else:
                        value = record[fn]
                        ff = "status"
                    if value is None or not value.strip():
                        form.errors[ff] = T("Reason must be specified")

        elif change_status and status != "NEW":
            # A new invoice can only have status "NEW"
            form.errors["status"] = T("Invalid status")

    # -------------------------------------------------------------------------
    @staticmethod
    def invoice_onaccept(form):
        """
            Onaccept procedure for invoices:
              - if status is PAID and the claim is still INVOICED,
                start the settle_invoice process (async, if possible)
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

        # Get the record
        table = s3db.fin_voucher_invoice
        query = (table.id == record_id)
        record = db(query).select(table.id,
                                  table.status,
                                  table.ptoken,
                                  limitby = (0, 1),
                                  ).first()
        if not record:
            return

        # Get the underlying claim
        ctable = s3db.fin_voucher_claim
        query = (ctable.invoice_id == record.id) & \
                (ctable.deleted == False)
        claim = db(query).select(ctable.id,
                                 ctable.status,
                                 limitby = (0, 1),
                                 orderby = ctable.id,
                                 ).first()

        if record.status == "PAID" and not record.ptoken and \
           claim.status == "INVOICED":

            # Generate authorization token
            import uuid
            ptoken = str(int(uuid.uuid4()))
            record.update_record(ptoken = ptoken,
                                 modified_by = table.modified_by,
                                 modified_on = table.modified_on,
                                 )
            current.s3task.run_async("s3db_task",
                                     args = ["fin_voucher_settle_invoice"],
                                     vars = {"invoice_id": record.id,
                                             "ptoken": ptoken,
                                             },
                                     timeout = 600,
                                     )

    # -------------------------------------------------------------------------
    @staticmethod
    def voucher_create_onvalidation(form):
        """
            Form validation of new vouchers:
            - check that program is active and hasn't ended
            - if using eligibility types, verify that the chosen type
              matches the program and is permissible for the issuer
        """

        db = current.db
        s3db = current.s3db

        T = current.T
        settings = current.deployment_settings

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

        if settings.get_fin_voucher_eligibility_types() and \
           "eligibility_type_id" in form_vars:

            # Verify that eligibility type matches program
            eligibility_type_id = form_vars["eligibility_type_id"]
            ttable = s3db.fin_voucher_eligibility_type
            if eligibility_type_id:
                query = (ttable.id == eligibility_type_id) & \
                        (ttable.program_id == program_id) & \
                        (ttable.deleted == False)
                etype = db(query).select(ttable.issuer_types,
                                        limitby = (0, 1),
                                        ).first()
                if not etype:
                    form.errors["eligibility_type_id"] = T("Invalid eligibility type")
            else:
                query = (ttable.program_id == program_id) & \
                        (ttable.deleted == False)
                anytype = db(query).select(ttable.id, limitby=(0, 1)).first()
                if anytype:
                    form.errors["eligibility_type_id"] = T("Eligibility type required")
                etype = None

            # Verify that eligibility type is permissible for issuer
            if etype and etype.issuer_types:
                if "pe_id" in form_vars:
                    issuer = form_vars["pe_id"]
                else:
                    issuer = table.pe_id.default
                permitted_types = etype.issuer_types
                otable = s3db.org_organisation
                ltable = s3db.org_organisation_organisation_type
                join = ltable.on((ltable.organisation_id == otable.id) & \
                                 (ltable.organisation_type_id.belongs(permitted_types)) & \
                                 (ltable.deleted == False))
                query = (otable.pe_id == issuer)
                row = db(query).select(otable.id,
                                       join = join,
                                       limitby = (0, 1),
                                       ).first()
                if not row:
                    form.errors["eligibility_type_id"] = T("Eligibility type not permissible for issuer")

    # -------------------------------------------------------------------------
    @staticmethod
    def voucher_create_onaccept(form):
        """
            Onaccept of new voucher:
            - transfer initial credit to the voucher (issue)
            - generate voucher signature
            - set expiration date

            Args:
                form: the FORM
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
                                           table.initial_credit,
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

        # Set default initial credit from program
        if voucher.initial_credit is None:
            default_credit = pdata.default_credit
            if default_credit:
                update["initial_credit"] = default_credit

        # Generate voucher signature
        import uuid
        vn = "0%s0%s" % (voucher.program_id, voucher.id)
        update["signature"] = "%s%s" % (str(uuid.uuid4().int)[:(16-len(vn))], vn)

        voucher.update_record(**update)
        program.issue(voucher.id)

    # -------------------------------------------------------------------------
    @staticmethod
    def voucher_status(row):
        """
            Virtual field indicating the status of the voucher
        """

        T = current.T

        if hasattr(row, "fin_voucher"):
            row = row.fin_voucher
        if hasattr(row, "balance") and row.balance is not None:
            if row.balance > 0:
                return T("Issued##fin")
            else:
                return T("Redeemed##fin")
        else:
            return current.messages["NONE"]

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
                                       vtable.single_debit,
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
            balance = voucher.balance

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
                elif balance <= 0:
                    error = T("Voucher credit exhausted")

            if not error:
                # Verify quantity/balance
                if "quantity" in form_vars:
                    quantity = form_vars["quantity"]
                    if quantity > balance:
                        field = "quantity"
                        error = T("Max %(number)s allowed") % {"number": balance}
                elif balance > 1 and voucher.single_debit:
                    error = T("Group voucher! - use dedicated form")

        if error:
            form.errors[field] = error

    # -------------------------------------------------------------------------
    @staticmethod
    def debit_create_onaccept(form):
        """
            Onaccept of debit:
                - transfer credit (redeem)

            Args:
                form: the FORM
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
                                 table.quantity,
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
        quantity = debit.quantity
        if not quantity:
            quantity = 1
        debit.update_record(program_id = voucher.program_id,
                            voucher_id = voucher.id,
                            quantity = quantity
                            )

        program = fin_VoucherProgram(voucher.program_id)
        program.debit(voucher.id, debit.id)

    # -------------------------------------------------------------------------
    @staticmethod
    def debit_status(row):
        """
            Virtual field indicating the status of the debit
        """

        T = current.T

        if hasattr(row, "fin_voucher_debit"):
            row = row.fin_voucher_debit
        if hasattr(row, "balance") and row.balance is not None:
            if row.balance > 0:
                return T("Compensation pending##fin")
            elif row.cancelled:
                return T("Cancelled##fin")
            else:
                return T("Compensated##fin")
        else:
            return current.messages["NONE"]

# =============================================================================
class fin_VoucherInvoiceRepresent(S3Represent):
    """
        Representation of invoice references (in claims)
    """

    def __init__(self, show_link=False, show_reason=True):
        """
            Args:
                show_link: show representation as clickable link
                show_reason: if invoice was rejected, include the
                             reason for rejection
        """

        super().__init__(lookup = "fin_voucher_invoice",
                         fields = ["invoice_no",
                                   "date",
                                   "status",
                                   "reason",
                                   ],
                         show_link = show_link,
                         )

        self.show_reason = show_reason

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a row

            Args:
                row: the Row
        """

        if hasattr(row, "fin_voucher_invoice"):
            invoice = row.fin_voucher_invoice
        else:
            invoice = row

        table = self.table

        T = current.T

        status = invoice.status
        status_repr = current.s3db.fin_voucher_invoice_status

        repr_str = "%s %s [%s] - %s" % (
                        T("No."),
                        table.invoice_no.represent(invoice.invoice_no),
                        table.date.represent(invoice.date),
                        status_repr.get(status, self.default),
                        )

        if status == "REJECTED" and self.show_reason:
            reason = invoice.reason
            if reason:
                repr_str = DIV(repr_str,
                               P(reason, _class="status-reason"),
                               )
        return repr_str

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
        settings = current.deployment_settings

        if tablename == "fin_voucher_program":

            if not tabs:
                tabs = [(T("Basic Details"), None),
                        (T("Vouchers"), "voucher"),
                        (T("Transactions"), "voucher_transaction"),
                        (T("Billing"), "voucher_billing"),
                        ]
                if settings.get_fin_voucher_eligibility_types():
                    tabs.insert(1, (T("Eligibility Types"), "voucher_eligibility_type"))
            rheader_fields = [["organisation_id"],
                              ]
            rheader_title = "name"

        elif tablename == "fin_voucher_claim":

            if not tabs:
                tabs = [(T("Basic Details"), None),
                        (T("Accepted Vouchers"), "voucher_debit"),
                        ]
            rheader_fields = [["date"],
                              ["status"],
                              ]
            rheader_title = "pe_id"

        elif tablename == "fin_voucher_invoice":

            if not tabs:
                tabs = [(T("Basic Details"), None),
                        ]
            rheader_fields = [["date"],
                              ["status"],
                              ]
            rheader_title = "pe_id"

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
class fin_VoucherProgram:
    """
        Helper to record transactions in voucher programs
    """

    def __init__(self, program_id):
        """
            Args:
                program_id: the voucher program ID
        """

        self.program_id = program_id
        self._program = None

    # -------------------------------------------------------------------------
    @property
    def program(self):
        """
            The program record (lazy property)

            Returns:
                the program record (Row)
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
                                               table.unit,
                                               table.price_per_unit,
                                               table.currency,
                                               limitby = (0, 1),
                                               ).first()
            self._program = program

        return program

    # -------------------------------------------------------------------------
    def issue(self, voucher_id, credit=None):
        """
            Transfer credit from the program to the voucher

            Args:
                voucher_id: the new voucher
                credit: the initial credit to transfer to the voucher

            Returns:
                the number of credit transferred to the voucher,
                or None on failure
        """

        program = self.program
        if not program:
            return None

        s3db = current.s3db
        table = s3db.fin_voucher
        query = (table.id == voucher_id) & \
                (table.program_id == program.id) & \
                (table.deleted == False)
        voucher = current.db(query).select(table.id,
                                           table.initial_credit,
                                           table.balance,
                                           limitby = (0, 1),
                                           ).first()
        if not voucher:
            return None

        if not isinstance(credit, int):
            credit = voucher.initial_credit
        if credit is None:
            credit = program.default_credit
        if credit is None:
            return 0

        balance = voucher.balance
        if balance:
            credit -= balance

        if credit:
            # Transfer initial credit to the voucher
            transaction = {"type": "ISS",
                           "credit": -credit,
                           "voucher": credit,
                           "voucher_id": voucher_id,
                           }
            if self.__transaction(transaction):
                voucher.update_record(
                    balance = voucher.balance + transaction["voucher"],
                    )
                ptable = s3db.fin_voucher_program
                program.update_record(
                    credit = ptable.credit + transaction["credit"],
                    modified_on = ptable.modified_on,
                    modified_by = ptable.modified_by,
                    )
            else:
                return None

        return credit

    # -------------------------------------------------------------------------
    def void(self, voucher_id):
        """
            Charge back the remaining balance of a voucher to the program,
            thereby voiding the voucher

            Args:
                voucher_id: the voucher ID

            Returns:
                the number of credits charged back to the program,
                or None on failure
        """

        program = self.program
        if not program:
            return None

        s3db = current.s3db
        table = s3db.fin_voucher
        query = (table.id == voucher_id) & \
                (table.program_id == program.id) & \
                (table.deleted == False)
        voucher = current.db(query).select(table.id,
                                           table.balance,
                                           limitby = (0, 1),
                                           ).first()
        if not voucher:
            return None
        balance = voucher.balance
        if balance and balance > 0:
            # Transfer remaining balance back to the program
            transaction = {"type": "VOI",
                           "credit": balance,
                           "voucher": -balance,
                           "voucher_id": voucher_id,
                           }
            if self.__transaction(transaction):
                voucher.update_record(
                    balance = voucher.balance + transaction["voucher"],
                    )
                ptable = s3db.fin_voucher_program
                program.update_record(
                    credit = ptable.credit + transaction["credit"],
                    modified_on = ptable.modified_on,
                    modified_by = ptable.modified_by,
                    )
            else:
                return None
        else:
            return 0

        return balance

    # -------------------------------------------------------------------------
    def debit(self, voucher_id, debit_id, credit=None):
        """
            Transfer credit to the provider when redeeming a voucher, i.e.
            debit a voucher.

            Args:
                voucher_id: the voucher ID
                debit_id: the debit ID
                credit: the credit to transfer (default 1)

            Returns:
                the credit deducted from the voucher

            Notes:
                Actually a double transaction:
                1) transfer credit from the program's compensation account
                   to the debit
                2) return credit from the voucher to the program's credit
                   account
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
                                   vtable.single_debit,
                                   vtable.credit_spent,
                                   limitby = (0, 1),
                                   ).first()
        if not voucher:
            return None

        dtable = s3db.fin_voucher_debit
        query = (dtable.id == debit_id) & \
                (dtable.program_id == program_id) & \
                (dtable.deleted == False)
        debit = db(query).select(dtable.id,
                                 dtable.quantity,
                                 dtable.balance,
                                 limitby = (0, 1),
                                 ).first()
        if not debit:
            return None

        if not isinstance(credit, int):
            credit = debit.quantity
        if credit is None:
            credit = 1
        if credit > voucher.balance:
            return None

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
                credit_spent = voucher.credit_spent
                if credit_spent:
                    credit_spent += transaction["debit"]
                else:
                    credit_spent = transaction["debit"]
                voucher.update_record(
                    credit_spent = credit_spent,
                    balance = voucher.balance + transaction["voucher"],
                    )
                debit.update_record(
                    balance = debit.balance + transaction["debit"],
                    )
                ptable = s3db.fin_voucher_program
                program.update_record(
                    credit = ptable.credit + transaction["credit"],
                    compensation = ptable.compensation + transaction["compensation"],
                    modified_on = ptable.modified_on,
                    modified_by = ptable.modified_by,
                    )
                if voucher.balance > 0 and voucher.single_debit:
                    # Voucher can only be debited once
                    self.void(voucher.id)
            else:
                return None

        return credit

    # -------------------------------------------------------------------------
    def cancel(self, debit_id, reason):
        """
            Cancel a debit - transfers the credit back to the voucher, and
            adjusts the program's credit/compensation balances accordingly,
            also reverses any voiding of single-debit vouchers

            Args:
                debit_id: the debit ID
                reason: the reason for cancellation (required)

            Returns:
                tuple (credits, error)
                - the number of credits returned, or None on failure
                - the failure reason

            Notes:
                - Cancelling a debit is only possible while the debit is not
                  part of any other transactions, and has not yet been included
                  in a billing or compensated
                - Implementations should ensure that debits can only be cancelled
                  by the organisation that originally created them (i.e. the provider
                  who has accepted the voucher), so as to not breach trust
        """

        program = self.program
        if not program:
            return None, "Program not found"

        db = current.db
        s3db = current.s3db

        # Reason must not be empty
        if not isinstance(reason, str) or not reason:
            return None, "No reason specified"

        # Get the debit and verify that it can be cancelled
        debit, error = self.cancellable(debit_id)
        if error:
            return None, error

        total_credit = debit.balance

        # Look up all DBT-transactions for this debit (normally only one)
        ttable = s3db.fin_voucher_transaction
        query = (ttable.debit_id == debit.id) & \
                (ttable.type == "DBT") & \
                (ttable.deleted == False)
        rows = db(query).select(ttable.id,
                                ttable.type,
                                ttable.credit,
                                ttable.voucher,
                                ttable.debit,
                                ttable.compensation,
                                ttable.voucher_id,
                                ttable.debit_id,
                                )
        if rows:
            # Totals must match (don't fix)
            if sum(t.debit for t in rows) != total_credit:
                return None, "Debit balance does not match transactions"

            vtable = s3db.fin_voucher
            for row in rows:
                # Get the voucher
                query = (vtable.id == row.voucher_id)
                voucher = db(query).select(vtable.id,
                                           vtable.balance,
                                           vtable.credit_spent,
                                           vtable.single_debit,
                                           vtable.initial_credit,
                                           limitby = (0, 1),
                                           ).first()
                if not voucher:
                    continue

                # Reverse the DBT transaction
                credit = row.debit
                transaction = {"type": "CNC",
                               "credit": -credit,
                               "voucher": credit,
                               "debit": -credit,
                               "compensation": credit,
                               "voucher_id": row.voucher_id,
                               "debit_id": debit.id,
                               }
                if self.__transaction(transaction):

                    # Update the voucher balance
                    voucher.update_record(
                        balance = voucher.balance + transaction["voucher"],
                        credit_spent = voucher.credit_spent + transaction["debit"],
                        )

                    if voucher.single_debit:
                        # Restore the initial credit
                        initial_credit = voucher.initial_credit
                        if initial_credit and initial_credit > voucher.balance:
                            self.issue(voucher.id, initial_credit)

                    # Update the debit
                    debit.update_record(
                        balance = debit.balance + transaction["debit"],
                        quantity = 0,
                        voucher_id = None,
                        signature = None,
                        bearer_dob = None,
                        cancelled = True,
                        cancel_reason = reason,
                        )

                    # Update the program balance
                    ptable = s3db.fin_voucher_program
                    program.update_record(
                        credit = ptable.credit + transaction["credit"],
                        compensation = ptable.compensation + transaction["compensation"],
                        modified_on = ptable.modified_on,
                        modified_by = ptable.modified_by,
                        )

        return total_credit, None

    # -------------------------------------------------------------------------
    def cancellable(self, debit_id):
        """
            Verify if a debit can still be cancelled

            Args:
                debit_id: the debit ID

            Returns:
                tuple (debit, error)
                    - the debit record if cancellable
                    - otherwise None, and the reason why not
        """

        program = self.program
        if not program:
            return None, "Program not found"
        program_id = program.id

        db = current.db
        s3db = current.s3db

        # Get the debit and verify its status
        error = None
        dtable = s3db.fin_voucher_debit
        query = (dtable.id == debit_id) & \
                (dtable.program_id == program_id) & \
                (dtable.deleted == False)
        debit = db(query).select(dtable.id,
                                 dtable.balance,
                                 dtable.billing_id,
                                 dtable.cancelled,
                                 limitby = (0, 1),
                                 ).first()
        if not debit:
            error = "Debit not found"
        elif debit.cancelled:
            error = "Debit already cancelled"
        elif debit.billing_id:
            error = "Debit already included in billing"

        if error:
            return None, error

        # Check if there is any transaction other than DBT for the debit
        ttable = s3db.fin_voucher_transaction
        query = (ttable.debit_id == debit.id) & \
                (ttable.type != "DBT") & \
                (ttable.deleted == False)
        rows = db(query).select(ttable.id, limitby=(0, 1))

        if rows:
            return None, "Debit already part of other transactions"

        return debit, None

    # -------------------------------------------------------------------------
    def compensate(self, debit_id, credit=None):
        """
            Compensate a debit (transfer credit back to the program), usually
            when the provider is compensated for the service rendered

            Args:
                debit_id: the debit ID
                credit: the number of credits compensated

            Returns:
                the number of credits transferred, None on failure
        """

        program = self.program
        if not program:
            return None

        s3db = current.s3db
        table = s3db.fin_voucher_debit
        query = (table.id == debit_id) & \
                (table.program_id == program.id) & \
                (table.deleted == False)
        debit = current.db(query).select(table.id,
                                         table.balance,
                                         limitby = (0, 1),
                                         ).first()
        if not debit:
            return None
        if not isinstance(credit, int):
            credit = debit.balance
        if credit is None or credit > debit.balance:
            return None

        if credit:
            # Transfer remaining balance to the compensation account
            transaction = {"type": "CMP",
                           "compensation": credit,
                           "debit": -credit,
                           "debit_id": debit.id,
                           }
            if self.__transaction(transaction):
                debit.update_record(
                    balance = debit.balance + transaction["debit"],
                    )
                ptable = s3db.fin_voucher_program
                program.update_record(
                    compensation = ptable.compensation + transaction["compensation"],
                    modified_on = ptable.modified_on,
                    modified_by = ptable.modified_by,
                    )
            else:
                return None
        else:
            return 0

        return credit

    # -------------------------------------------------------------------------
    def verify(self, transaction_id):
        """
            Verify integrity of a transaction (=check the vhash)

            Args:
                transaction_id: the transaction record ID

            Returns:
                True|False whether the transaction is intact
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

            Args:
                correct: correct any incorrect balances

            Returns:
                audit report

            TODO implement
        """

        return True

    # -------------------------------------------------------------------------
    def earliest_billing_date(self, billing_id=None, configure=None):
        """
            Get the earliest possible billing date for the program
                - must be after any active or completed billing processes

            Args:
                billing_id: the billing ID
                configure: a Field to configure accordingly
                           (typically fin_voucher_billing.date itself)

            Returns:
                the earliest possible billing date
        """

        program = self.program
        if not program:
            return None

        db = current.db
        s3db = current.s3db

        btable = s3db.fin_voucher_billing
        query = (btable.program_id == program.id) & \
                (btable.status.belongs(("IN PROGRESS", "COMPLETED")))
        if billing_id:
            query &= (btable.id != billing_id)
        query &= (btable.date != None) & (btable.deleted == False)

        row = db(query).select(btable.date,
                               limitby = (0, 1),
                               orderby = ~btable.date,
                               ).first()

        earliest = row.date + datetime.timedelta(days=1) if row else None

        if earliest and configure:
            default = configure.default
            configure.default = max(earliest, default) if default else earliest
            configure.requires = IS_EMPTY_OR(IS_UTC_DATE(minimum=earliest))
            configure.widget = S3CalendarWidget(minimum=earliest)

        return earliest

    # -------------------------------------------------------------------------
    def _hash(self, transaction, ohash):
        """
            Generate a verification hash (vhash) for the transaction

            Args:
                transaction: the transaction data
                ohash: the hash of the preceding transaction

            Returns:
                the hash as string
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
        inp = json.dumps(data, separators=JSONSEPARATORS)

        crypt = CRYPT(key = current.deployment_settings.hmac_key,
                      digest_alg = "sha512",
                      salt = False,
                      )
        return str(crypt(inp)[0])

    # -------------------------------------------------------------------------
    def __transaction(self, data):
        """
            Record a transaction under this program

            Args:
                data: the transaction details

            Returns:
                True|False for success or failure
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
class fin_VoucherBilling:
    """
        Helper to facilitate the billing process for a voucher program
    """

    invoice_fields = ("program_id",
                      "billing_id",
                      "pe_id",
                      "quantity_total",
                      "price_per_unit",
                      "amount_receivable",
                      "currency",
                      "account_holder",
                      "account_number",
                      #"bank_name",
                      #"bank_address",
                      )

    def __init__(self, billing_id):
        """
            Args:
                billing_id: the billing record ID
        """

        self.billing_id = billing_id

        self._record = None
        self._program = None

    # -------------------------------------------------------------------------
    @property
    def billing(self):
        """
            Get the billing record (lazy property)

            Returns:
                Row

            Raises:
                ValueError: if the billing reference is invalid
        """

        billing = self._record
        if not billing:
            btable = current.s3db.fin_voucher_billing
            query = (btable.id == self.billing_id) & \
                    (btable.deleted == False)
            billing = current.db(query).select(btable.id,
                                               btable.program_id,
                                               btable.date,
                                               btable.status,
                                               limitby = (0, 1),
                                               ).first()
            if not billing:
                raise ValueError("Billing record not found")
            self._record = billing

        return billing

    # -------------------------------------------------------------------------
    @property
    def program(self):
        """
            Get the voucher program for this billing process (lazy property)

            Returns:
                fin_VoucherProgram

            Raises:
                ValueError: if the program reference is invalid
        """

        program = self._program
        if not program:
            program = fin_VoucherProgram(self.billing.program_id)
            if not program.program:
                raise ValueError("Invalid program reference")
            self._program = program

        return program

    # -------------------------------------------------------------------------
    def verify(self):
        """
            Verify all relevant debits, fix any incorrect balances

            Returns:
                number of invalid transactions
        """

        db = current.db
        s3db = current.s3db

        billing = self.billing
        program = self.program

        dtable = s3db.fin_voucher_debit
        ttable = s3db.fin_voucher_transaction

        query = (dtable.billing_id == billing.id) & \
                (dtable.claim_id == None) & \
                (dtable.deleted == False)
        left = ttable.on((ttable.debit_id == dtable.id) & \
                         (ttable.deleted == False))
        rows = db(query).select(dtable.id,
                                dtable.balance,
                                ttable.id,
                                ttable.debit,
                                left = left,
                                orderby = dtable.date,
                                )

        log = current.log
        invalid_debit = "Voucher program billing - invalid debit: #%s"
        invalid_transaction = "Voucher program billing - corrupted transaction: #%s"

        invalid = 0
        totals = {}
        debits = {}
        for row in rows:
            debit = row.fin_voucher_debit
            transaction = row.fin_voucher_transaction

            if transaction.id is None:
                # Invalid debit, drop it from billing
                log.warning(invalid_debit % debit.id)
                debit.update_record(billing_id = None,
                                    modified_on = dtable.modified_on,
                                    modified_by = dtable.modified_by,
                                    )
            elif program.verify(transaction.id):
                # Valid transaction
                debit_id = debit.id
                if debit_id in totals:
                    totals[debit_id] += transaction.debit
                else:
                    totals[debit_id] = transaction.debit
                debits[debit_id] = debit
            else:
                # Invalid transaction
                log.error(invalid_transaction % transaction.id)
                invalid += 1

        if not invalid:
            # Fix any incorrect debit balances
            for debit_id, total in totals.items():
                debit = debits[debit_id]
                if debit.balance != total:
                    debit.update_record(balance = total,
                                        modified_on = dtable.modified_on,
                                        modified_by = dtable.modified_by,
                                        )

        return invalid

    # -------------------------------------------------------------------------
    def generate_claims(self):
        """
            Generate claims for compensation for any unprocessed debits
            under this billing process

            Returns:
                number of claims generated, None on error

            Raises:
                ValueError: if the action is invalid
        """

        # Activate the billing process
        billing = self.__activate()

        # Get the program
        try:
            program = self.program
        except ValueError:
            self.__abort("Program not found")
            raise

        # Abort if there is no unit price (never raise zero-charge claims)
        pdata = program.program
        ppu = pdata.price_per_unit
        if not ppu or ppu <= 0:
            error = "Program has no valid unit price!"
            self.__abort(error)
            raise ValueError(error)

        # Verify all relevant transactions
        invalid = self.verify()
        if invalid:
            error = "%s invalid transactions found!" % invalid
            self.__abort(error)
            raise ValueError(error)

        db = current.db
        s3db = current.s3db

        dtable = s3db.fin_voucher_debit
        ctable = s3db.fin_voucher_claim

        # Customise claim resource
        from core import CRUDRequest
        r = CRUDRequest("fin", "voucher_claim", args=[], get_vars={})
        r.customise_resource("fin_voucher_claim")

        # Base query
        query = (dtable.billing_id == billing.id) & \
                (dtable.claim_id == None) & \
                (dtable.deleted == False)

        # Get totals per provider
        provider_id = dtable.pe_id
        balance_total = dtable.balance.sum()
        num_vouchers = dtable.voucher_id.count()
        rows = db(query).select(provider_id,
                                balance_total,
                                num_vouchers,
                                groupby = provider_id,
                                having = balance_total > 0,
                                )

        # Generate claims
        billing_id = billing.id
        total_claims = 0

        s3db_onaccept = s3db.onaccept
        set_record_owner = current.auth.s3_set_record_owner

        for row in rows:

            # Check provider
            provider = row[provider_id]
            if not provider:
                continue

            # Compute amount receivable
            vouchers = row[num_vouchers]
            quantity = row[balance_total]
            amount = quantity * ppu if ppu else 0

            # Claim details
            data = {"program_id": pdata.id,
                    "billing_id": billing_id,
                    "pe_id": provider,
                    "date": datetime.datetime.utcnow(),
                    "status": "NEW",
                    "vouchers_total": vouchers,
                    "quantity_total": quantity,
                    "price_per_unit": ppu,
                    "amount_receivable": amount,
                    "currency": pdata.currency,
                    }

            data["id"] = claim_id = ctable.insert(**data)
            if claim_id:
                # Post-process the claim
                set_record_owner(ctable, data)
                s3db_onaccept(ctable, data, method="create")

                # Update all debits with claim_id
                q = query & (dtable.pe_id == provider)
                db(q).update(claim_id = claim_id,
                             modified_by = dtable.modified_by,
                             modified_on = dtable.modified_on,
                             )
                total_claims += 1

        # Update totals in billing
        query = (ctable.billing_id == billing_id) & \
                (ctable.deleted == False)
        vouchers_total = ctable.vouchers_total.sum()
        quantity_total = ctable.quantity_total.sum()
        row = db(query).select(vouchers_total,
                               quantity_total,
                               ).first()

        btable = s3db.fin_voucher_billing
        billing.update_record(vouchers_total = row[vouchers_total],
                              quantity_total = row[quantity_total],
                              modified_by = btable.modified_by,
                              modified_on = btable.modified_on,
                              )

        # If no claims have been generated, conclude the billing
        # right away (as there will be no later trigger)
        if total_claims == 0:
            self.check_complete(claims_complete=True)

        return total_claims

    # -------------------------------------------------------------------------
    @classmethod
    def generate_invoice(cls, claim_id):
        """
            Generate an invoice for a claim

            Args:
                claim_id: the claim record ID

            Returns:
                tuple (invoice_id, error)
        """

        db = current.db
        s3db = current.s3db

        ctable = s3db.fin_voucher_claim
        dtable = s3db.fin_voucher_debit
        itable = s3db.fin_voucher_invoice

        invoice_fields = cls.invoice_fields

        # Get the claim
        fields = [ctable.id, ctable.uuid, ctable.date, ctable.status, ctable.invoice_id] + \
                 [ctable[fn] for fn in invoice_fields] + \
                 [ctable.bank_name, ctable.bank_address]
        query = (ctable.id == claim_id) & \
                (ctable.deleted == False)
        claim = db(query).select(limitby=(0, 1), *fields).first()

        # Verify claim status
        if not claim:
            return None, "Claim not found"
        if claim.status != "CONFIRMED":
            return None, "Claim must be confirmed"
        if claim.invoice_id:
            return None, "Claim already invoiced"

        # Verify claim details
        query = (dtable.claim_id == claim.id) & \
                (dtable.deleted == False)
        total = dtable.balance.sum()
        row = db(query).select(total).first()

        quantity_total = claim.quantity_total
        if quantity_total != row[total]:
            return None, "Invalid claim: incorrect quantity"
        ppu = claim.price_per_unit
        if not ppu or ppu <= 0:
            return None, "Invalid claim: no valid unit price"
        amount_receivable = claim.amount_receivable
        if not amount_receivable or amount_receivable != quantity_total * ppu:
            return None, "Invalid claim: incorrect total amount receivable"

        # The claim details
        data = {fn: claim[fn] for fn in invoice_fields}

        # Generate an invoice number
        btable = s3db.fin_voucher_billing
        query = (btable.id == claim.billing_id)
        billing = db(query).select(btable.uuid, limitby=(0, 1)).first()
        try:
            bprefix = (billing.uuid.rsplit(":", 1)[-1][:4]).upper()
        except (TypeError, AttributeError):
            bprefix = ""
        invoice_no = "B%s%02dC%04d" % (bprefix, claim.billing_id, claim.id)

        # Customise invoice resource
        from core import CRUDRequest
        r = CRUDRequest("fin", "voucher_invoice", args=[], get_vars={})
        r.customise_resource("fin_voucher_invoice")

        # Generate invoice
        idata = {"date": datetime.datetime.utcnow().date(),
                 "invoice_no": invoice_no,
                 "status": "NEW",
                 "vhash": cls._hash(claim.uuid, claim.date, data),
                 "bank_name": claim.bank_name,
                 "bank_address": claim.bank_address,
                 }
        idata.update(data)
        invoice_id = idata["id"] = itable.insert(**idata)

        # Postprocess invoice
        current.auth.s3_set_record_owner(itable, idata)
        s3db.onaccept(itable, idata, method="create")

        # Update claim with invoice_id and verification hash
        query = (itable.id == invoice_id)
        invoice = db(query).select(itable.uuid,
                                   itable.billing_id,
                                   itable.date,
                                   itable.quantity_total,
                                   limitby = (0, 1),
                                   ).first()
        claim.update_record(invoice_id = invoice_id,
                            status = "INVOICED",
                            vhash = cls._hash(invoice.uuid, invoice.date, data),
                            modified_on = ctable.modified_on,
                            modified_by = ctable.modified_by,
                            )

        # Update totals in billing
        query = (itable.billing_id == invoice.billing_id) & \
                (itable.deleted == False)
        quantity_total = itable.quantity_total.sum()
        row = db(query).select(quantity_total).first()

        btable = s3db.fin_voucher_billing
        query = (btable.id == invoice.billing_id)
        db(query).update(quantity_invoiced = row[quantity_total],
                         modified_by = btable.modified_by,
                         modified_on = btable.modified_on,
                         )

        return invoice_id, None

    # -------------------------------------------------------------------------
    @classmethod
    def check_invoice(cls, invoice_id):
        """
            Check the integrity of an invoice/claim pair (=check the hashes)

            Args:
                invoice_id: the invoice ID

            Returns:
                True|False
        """

        db = current.db
        s3db = current.s3db

        invoice_fields = cls.invoice_fields

        # Get the invoice
        itable = s3db.fin_voucher_invoice
        fields = [itable.id, itable.uuid, itable.date, itable.vhash]
        fields += [itable[fn] for fn in invoice_fields]
        query = (itable.id == invoice_id) & \
                (itable.deleted == False)
        invoice = db(query).select(limitby=(0, 1), *fields).first()
        if not invoice:
            return False

        # Get the claim
        ctable = s3db.fin_voucher_claim
        fields = [ctable.id, ctable.uuid, ctable.date, ctable.vhash]
        fields += [ctable[fn] for fn in invoice_fields]
        query = (ctable.invoice_id == invoice.id) & \
                (ctable.deleted == False)
        claim = db(query).select(limitby = (0, 1),
                                 orderby = ctable.id,
                                 *fields).first()
        if not claim:
            return False


        # Verify the hashes
        data = {fn: claim[fn] for fn in invoice_fields}
        vhash = cls._hash(claim.uuid, claim.date, data)
        if invoice.vhash != vhash:
            return False

        data = {fn: invoice[fn] for fn in invoice_fields}
        vhash = cls._hash(invoice.uuid, invoice.date, data)
        if claim.vhash != vhash:
            return False

        return True

    # -------------------------------------------------------------------------
    @classmethod
    def settle_invoice(cls, invoice_id, ptoken):

        db = current.db
        s3db = current.s3db

        invoice_fields = cls.invoice_fields

        # Get the invoice
        itable = s3db.fin_voucher_invoice
        fields = [itable.id, itable.uuid, itable.date, itable.status, itable.vhash, itable.ptoken]
        fields += [itable[fn] for fn in invoice_fields]
        query = (itable.id == invoice_id) & \
                (itable.deleted == False)
        invoice = db(query).select(limitby=(0, 1), *fields).first()

        # Verify that the invoice is status=PAID
        if not invoice:
            raise ValueError("Invoice not found")
        if invoice.ptoken != ptoken:
            raise ValueError("Process not authorized")
        if invoice.status != "PAID":
            raise ValueError("Incorrect invoice status")

        # Get the claim
        ctable = s3db.fin_voucher_claim
        fields = [ctable.id, ctable.uuid, ctable.date, ctable.status, ctable.vhash]
        fields += [ctable[fn] for fn in invoice_fields]
        query = (ctable.invoice_id == invoice.id) & \
                (ctable.deleted == False)
        claim = db(query).select(limitby = (0, 1),
                                 orderby = ctable.id,
                                 *fields).first()
        if not claim:
            raise ValueError("Claim not found")
        if claim.status != "INVOICED":
            raise ValueError("Incorrect claim status")

        # Verify the hashes
        data = {fn: claim[fn] for fn in invoice_fields}
        vhash = cls._hash(claim.uuid, claim.date, data)
        if invoice.vhash != vhash:
            raise ValueError("Invoice with invalid verification hash")
        data = {fn: invoice[fn] for fn in invoice_fields}
        vhash = cls._hash(invoice.uuid, invoice.date, data)
        if claim.vhash != vhash:
            raise ValueError("Claim with invalid verification hash")

        # Get all debits linked to the claim, verify the total
        dtable = s3db.fin_voucher_debit
        query = (dtable.claim_id == claim.id) & \
                (dtable.deleted == False)
        debits = db(query).select(dtable.id,
                                  dtable.balance,
                                  )
        balance_total = sum(d.balance for d in debits if d.balance)
        if balance_total != invoice.quantity_total:
            raise ValueError("Invoice quantity does not match debit balance")

        # Compensate all debits
        total = 0
        program = fin_VoucherProgram(claim.program_id)
        for debit in debits:
            credit = program.compensate(debit.id)
            if credit is None:
                raise ValueError("Could not compensate debit %s" % debit.id)
            total += credit

        # Mark the claim as paid
        claim.update_record(status = "PAID",
                            modified_on = ctable.modified_on,
                            modified_by = ctable.modified_by,
                            )

        # Update totals in billing
        query = (ctable.billing_id == invoice.billing_id) & \
                (ctable.status == "PAID") & \
                (ctable.deleted == False)
        quantity_total = ctable.quantity_total.sum()
        row = db(query).select(quantity_total).first()

        btable = s3db.fin_voucher_billing
        query = (btable.id == invoice.billing_id)
        db(query).update(quantity_compensated = row[quantity_total],
                         modified_by = btable.modified_by,
                         modified_on = btable.modified_on,
                         )

        # Customise invoice resource
        from core import CRUDRequest
        r = CRUDRequest("fin", "voucher_invoice", args=[], get_vars={})
        r.customise_resource("fin_voucher_invoice")

        # Trigger onsettled-callback for invoice
        cb = s3db.get_config("fin_voucher_invoice", "onsettled")
        if callable(cb):
            from gluon.tools import callback
            try:
                callback(cb, invoice, tablename="fin_voucher_invoice")
            except Exception:
                import sys
                error = sys.exc_info()[1]
                current.log.error("Callback %s failed: %s" %
                                  (cb, error if error else "unknown error"))

        # Check if billing is complete
        cls(invoice.billing_id).check_complete()

        return total

    # -------------------------------------------------------------------------
    def check_complete(self, claims_complete=False):
        """
            Check whether this billing process is complete (+update status
            if so)

            Args:
                claims_complete: confirm that claim generation is complete

            Returns:
                True|False
        """

        db = current.db
        s3db = current.s3db

        billing = self.billing

        ctable = s3db.fin_voucher_claim
        query = (ctable.billing_id == billing.id) & \
                (ctable.deleted == False)
        existing = db(query).select(ctable.id, limitby=(0, 1)).first()
        if existing:
            # Check if there are any unpaid claims
            query &= (ctable.status != "PAID")
            pending = db(query).select(ctable.id, limitby=(0, 1)).first()
        else:
            # No claims generated yet?
            pending = not claims_complete

        if pending:
            return False

        btable = s3db.fin_voucher_billing
        billing.update_record(status = "COMPLETE",
                              modified_on = btable.modified_on,
                              modified_by = btable.modified_by,
                              )
        return True

    # -------------------------------------------------------------------------
    def has_claims_or_invoices(self):
        """
            Check if this billing process has generated any claims
            or invoices

            Returns:
                True|False
        """

        db = current.db
        s3db = current.s3db

        billing = self.billing

        # Check for existing claims
        ctable = s3db.fin_voucher_claim
        query = (ctable.billing_id == billing.id) & \
                (ctable.deleted == False)
        if db(query).select(ctable.id, limitby=(0, 1)).first():
            return True

        # Check for existing invoices
        itable = s3db.fin_voucher_invoice
        query = (itable.billing_id == billing.id) & \
                (itable.deleted == False)
        if db(query).select(itable.id, limitby=(0, 1)).first():
            return True

        return False

    # -------------------------------------------------------------------------
    @staticmethod
    def _hash(uuid, date, data):
        """
            Generate a verification hash (vhash)

            Args:
                uuid: the uuid of the reference record
                date: the date of the reference record
                data: the data to hash

            Returns:
                the hash as string
        """

        data = {"data": data,
                "date": date.isoformat(),
                "uuid": uuid,
                }
        inp = json.dumps(data, separators=JSONSEPARATORS)

        crypt = CRYPT(key = current.deployment_settings.hmac_key,
                      digest_alg = "sha512",
                      salt = False,
                      )
        return str(crypt(inp)[0])

    # -------------------------------------------------------------------------
    def __activate(self):
        """
            Activate the billing process
                - allocate all relevant debits of the program to the billing
                - set the process status to "in progress"

            Returns:
                the billing record (Row)

            Raises:
                ValueError: if the billing reference is invalid,
                            or when the billing process is already closed
        """

        billing = self.billing

        # Check status
        if billing.status not in ("SCHEDULED", "IN PROGRESS"):
            raise ValueError("Invalid process status")

        db = current.db
        s3db = current.s3db

        # Allocate relevant debits to this billing
        # - all debits under the program effected before the billing date,
        #   which have not yet been allocated to the billing and are not
        #   yet part of any existing claim
        dtable = s3db.fin_voucher_debit
        query = (dtable.program_id == billing.program_id) & \
                (dtable.date <= billing.date) & \
                (dtable.billing_id == None) & \
                (dtable.claim_id == None) & \
                (dtable.deleted == False)
        db(query).update(billing_id = billing.id,
                         modified_on = dtable.modified_on,
                         modified_by = dtable.modified_by,
                         )

        # Update billing process status
        btable = s3db.fin_voucher_billing
        billing.update_record(status = "IN PROGRESS",
                              modified_on = btable.modified_on,
                              modified_by = btable.modified_by,
                              )

        db.commit()
        return billing

    # -------------------------------------------------------------------------
    def __abort(self, reason):
        """
            Abort this billing process
                - release all debits allocated to this process
                - set the process status to "aborted" and record reason

            Args:
                reason: the reason to abort the process

            Raises:
                ValueError: if the billing reference is invalid,
                            or when the billing process is already closed
        """

        db = current.db
        s3db = current.s3db

        billing = self.billing

        # Release all allocated debits that have not been processed yet
        dtable = s3db.fin_voucher_debit
        query = (dtable.billing_id == billing.id) & \
                (dtable.claim_id == None)
        db(query).update(billing_id = None,
                         modified_on = dtable.modified_on,
                         modified_by = dtable.modified_by,
                         )

        # Update billing process status
        if billing.status in ("SCHEDULED", "IN PROGRESS") and \
           not self.has_claims_or_invoices():
            btable = s3db.fin_voucher_billing
            billing.update_record(status = "ABORTED",
                                  verification = reason,
                                  modified_on = btable.modified_on,
                                  modified_by = btable.modified_by,
                                  )
        db.commit()

# =============================================================================
class fin_VoucherCancelDebit(CRUDMethod):
    """ RESTful method to cancel a debit """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Applies the method (controller entry point).

            Args:
                r: the CRUDRequest instance
                attr: controller attributes
        """

        resource = r.resource
        if resource.tablename != "fin_voucher_debit" or not r.record:
            r.error(400, current.ERROR.BAD_RESOURCE)

        output = {}
        if r.http in ("GET", "POST"):
            if r.interactive:
                output = self.cancel(r, **attr)
            else:
                r.error(415, current.ERROR.BAD_FORMAT)
        else:
            r.error(405, current.ERROR.BAD_METHOD)

        current.response.view = self._view(r, "delete.html")
        return output

    # -------------------------------------------------------------------------
    def cancel(self, r, **attr):
        """
            Cancel a voucher debit

            Args:
                r: the CRUDRequest instance
                attr: controller attributes
        """

        # User must be permitted to update the debit
        if not self._permitted("update"):
            r.unauthorised()

        T = current.T

        auth = current.auth

        settings = current.deployment_settings
        request = current.request
        session = current.session
        response = current.response

        debit = r.record
        program = fin_VoucherProgram(debit.program_id)

        # Verify that the debit can be cancelled
        error = program.cancellable(debit.id)[1]
        if error:
            r.error(400, T("Voucher acceptance cannot be cancelled"),
                    next = r.url(id=r.id, method=""),
                    )

        # Form fields and mark-required
        formfields = [Field("reason",
                            label = T("Reason for Cancellation##fin"),
                            requires = IS_NOT_EMPTY(error_message=T("Reason must be specified")),
                            ),
                      Field("do_cancel", "boolean",
                            label = T("Cancel this voucher acceptance"),
                            default = False,
                            ),
                      ]
        labels, has_required = s3_mark_required(formfields,
                                                mark_required = ["do_cancel"],
                                                )
        response.s3.has_required = has_required

        # Form buttons
        CANCEL = T("Cancel Voucher Acceptance")
        buttons = [INPUT(_type="submit", _value=CANCEL)]

        # Construct the form
        response.form_label_separator = ""
        form = SQLFORM.factory(table_name = "fin_voucher_debit",
                               record = None,
                               hidden = {"_next": auth.get_vars_next()},
                               labels = labels,
                               separator = "",
                               showid = False,
                               submit_button = CANCEL,
                               delete_label = auth.messages.delete_label,
                               formstyle = settings.get_ui_formstyle(),
                               buttons = buttons,
                               *formfields)

        # Form validation
        def validate(form):
            try:
                do_cancel = form.vars.do_cancel
            except AttributeError:
                do_cancel = False
            if not do_cancel:
                form.errors.do_cancel = T("Confirm that you want to cancel this voucher acceptance")

        if form.accepts(request.vars,
                        session,
                        formname = "cancel_debit",
                        onvalidation = validate,
                        ):

            # Cancel the debit
            error = program.cancel(debit.id, form.vars.reason)[1]
            if error:
                response.error = T("Voucher acceptance cannot be cancelled: %s") % error
            else:
                response.confirmation = T("Cancellation successful")

            # Redirect to the debit
            self.next = r.url(id=r.id, method="")

        return {"title": get_crud_string("fin_voucher_debit",
                                         "title_display",
                                         ),
                "form": form,
                }

# =============================================================================
def fin_voucher_eligibility_types(program_ids, organisation_ids=None):
    """
        Look up permissible eligibility types for programs

        Args:
            program_ids: voucher program IDs
            organisation_ids: issuer organisation IDs

        Returns:
            dict {program_id: [eligibility_type_ids]}
    """

    db = current.db
    s3db = current.s3db

    if organisation_ids:
        # Look up issuer organisation types
        ltable = s3db.org_organisation_organisation_type
        query = (ltable.organisation_id.belongs(organisation_ids)) & \
                (ltable.deleted == False)
        rows = db(query).select(ltable.organisation_type_id,
                                groupby = ltable.organisation_type_id,
                                )
        issuer_types = [row.organisation_type_id for row in rows]

    ttable = s3db.fin_voucher_eligibility_type
    query = (ttable.program_id.belongs(program_ids)) & \
            (ttable.deleted == False)
    rows = db(query).select(ttable.program_id)

    # Include programs that do not require eligibility types
    unlimited = set(program_ids) - {row.program_id for row in rows}
    eligibility_types = {p: None for p in unlimited}

    if issuer_types:
        # Limit to issuer organisation types
        query &= (ttable.issuer_types.contains(issuer_types, all=False)) | \
                 (ttable.issuer_types == None) | \
                 (ttable.issuer_types == [])
    rows = db(query).select(ttable.id, ttable.program_id)

    for row in rows:
        program_id = row.program_id
        if program_id in eligibility_types:
            eligibility_types[program_id].append(row.id)
        else:
            eligibility_types[program_id] = [row.id]

    return eligibility_types

# =============================================================================
def fin_voucher_permitted_programs(mode = "issuer",
                                   partners_only = False,
                                   c = None,
                                   f = None,
                                   ):
    """
        Get a list of programs and organisations the current user
        is permitted to issue/accept vouchers for

        Args:
            mode: the permission to look for ('issuer'|'provider')
            partners_only: organisations must also be project partners
                           for the project under which a voucher program
                           runs, in order to issue/accept vouchers under
                           that program
            c: override request.controller to look up for a
               different controller context
            f: override request.function to look up for a
               different controller context

        Reutrns:
            tuple of lists (program_ids, org_ids, pe_ids)
    """

    s3db = current.s3db

    otable = s3db.org_organisation
    ptable = s3db.fin_voucher_program
    mtable = s3db.org_group_membership

    permitted_realms = current.auth.permission.permitted_realms
    if mode == "issuer":
        fn = "issuers_id"
        realms = permitted_realms("fin_voucher",
                                  method = "create",
                                  c = c,
                                  f = f,
                                  )
    else:
        fn = "providers_id"
        realms = permitted_realms("fin_voucher_debit",
                                  method = "create",
                                  c = c,
                                  f = f,
                                  )

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
    if partners_only:
        ltable = s3db.project_organisation
        join.append(ltable.on((ltable.project_id == ptable.project_id) & \
                              (ltable.organisation_id == otable.id) & \
                              (ltable.deleted == False)))

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

# =============================================================================
def fin_voucher_start_billing(billing_id=None):
    """
        Scheduler task to start a billing process, to be scheduled
        via s3db_task

        Args:
            billing_id: the billing ID

        Returns:
            success message
    """

    if not billing_id:
        raise TypeError("Argument missing: billing ID")

    billing = fin_VoucherBilling(billing_id)

    claims = billing.generate_claims()
    return "Billing process started (%s claims generated)" % claims

# =============================================================================
def fin_voucher_settle_invoice(invoice_id=None, ptoken=None, user_id=None):
    """
        Scheduler task to settle an invoice, to be scheduled
        via s3db_task

        Args:
            invoice_id: the invoice ID
            ptoken: the processing authorization token

        Returns:
            success message
    """

    auth = current.auth
    if user_id and not auth.s3_logged_in():
        auth.s3_impersonate(user_id)

    if not ptoken:
        raise TypeError("Argument missing: authorization token")
    if not invoice_id:
        raise TypeError("Argument missing: invoice ID")
    if not auth.s3_has_permission("update", "fin_voucher_invoice",
                                  record_id = invoice_id,
                                  c = "fin",
                                  f = "voucher_invoice",
                                  ):
        raise auth.permission.error("Operation not permitted")

    quantity = fin_VoucherBilling.settle_invoice(invoice_id, ptoken)
    return "Invoice settled (%s units compensated)" % quantity

# END =========================================================================
