# -*- coding: utf-8 -*-

""" Finance Tables

    @copyright: 2015-2019 (c) Sahana Software Foundation
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
           "FinPaymentServiceModel",
           "FinProductModel",
           "FinSubscriptionModel",
           "fin_rheader",
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

        represent = S3Represent(lookup=tablename)

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
class FinPaymentServiceModel(S3Model):
    """ Model for Payment Services """

    names = ("fin_payment_service",
             "fin_payment_log",
             )

    def model(self):

        T = current.T

        # -------------------------------------------------------------------------
        # Payments Service
        #
        api_types = {"PAYPAL": "PayPal",
                     }

        tablename = "fin_payment_service"
        self.define_table(tablename,
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
                                represent = S3Represent(options = api_types,
                                                        ),
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
                          Field("password",
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

        # TODO Implement represent using API type + org name
        represent = S3Represent(lookup=tablename)
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

        self.add_components(tablename,
                            fin_payment_log = "service_id",
                            )

        # -------------------------------------------------------------------------
        # Payments Log
        #
        tablename = "fin_payment_log"
        self.define_table(tablename,
                          service_id(empty = False,
                                     ondelete = "CASCADE",
                                     ),
                          s3_datetime(default="now",
                                      ),
                          Field("action"),
                          Field("result"),
                          Field("reason"),
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
             )

    def model(self):

        T = current.T

        db = current.db
        s3 = current.response.s3

        define_table = self.define_table
        crud_strings = s3.crud_strings

        # ---------------------------------------------------------------------
        # Products; represent billable products or services
        #
        tablename = "fin_product"
        define_table(tablename,
                     Field("name",
                           requires = IS_NOT_EMPTY(),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

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
                                     requires = IS_ONE_OF(db, "%s.id" % tablename,
                                                          represent,
                                                          ),
                                     sortby = "name",
                                     comment = S3PopupLink(c="fin",
                                                           f="product",
                                                           tooltip=T("Create a new product"),
                                                           ),
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

# =============================================================================
class FinSubscriptionModel(S3Model):
    """ Model to manage subscription-based payments """

    names = (#"fin_subscription_plan",    # TODO
             #"fin_subscription",         # TODO
             )

    def model(self):

        T = current.T

        db = current.db
        s3 = current.response.s3

        define_table = self.define_table
        crud_strings = s3.crud_strings

        # ---------------------------------------------------------------------
        # Subscription Plans
        #
        tablename = "fin_subscription_plan"
        define_table(tablename,
                     Field("name",
                           requires = IS_NOT_EMPTY(),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

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
        represent = S3Represent(lookup=tablename, show_link=True)
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
        # Pass names back to global scope (s3.*)
        #
        return {"fin_subscription_plan_id": plan_id,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """ Safe defaults for names in case the module is disabled """

        return {"fin_subscription_plan_id": S3ReusableField.dummy("plan_id"),
                }

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
        if tablename == "fin_payment_service":

            if not tabs:
                tabs = [(T("Basic Details"), None),
                        (T("Log"), "payment_log"),
                        ]

            rheader_fields = [["organisation_id",
                               "api_type",
                               ],
                              ]

        # Generate rheader XML
        rheader = S3ResourceHeader(rheader_fields, tabs)(
                        r,
                        table = resource.table,
                        record = record,
                        )

    return rheader

# END =========================================================================
