# -*- coding: utf-8 -*-

""" Finance Tables

    @copyright: 2015-2020 (c) Sahana Software Foundation
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
            cycles = form_vars.cycles
        except AttributeError:
            pass
        else:
            if fixed and not cycles:
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
        if tablename == "fin_payment_service":

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

# END =========================================================================
