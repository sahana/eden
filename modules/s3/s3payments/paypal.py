# -*- coding: utf-8 -*-

""" PayPal API Adapter

    @copyright: (c) 2020-2020 Sahana Software Foundation
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

__all__ = ("PayPalAdapter",
           )

import datetime

from gluon import current, URL

from .base import S3PaymentService

# =============================================================================
class PayPalAdapter(S3PaymentService):
    """
        API Adapter for PayPal
    """

    # -------------------------------------------------------------------------
    def get_access_token(self):
        """
            Get a new access token

            @returns: the new access token
        """

        action = "Get Access Token"

        username = self.username
        password = self.password

        if username and password:

            now = current.request.utcnow
            credentials, _, error = self.http(method = "POST",
                                              path = "/v1/oauth2/token",
                                              data = "grant_type=client_credentials",
                                              auth = "Basic",
                                              encode = "text",
                                              decode = "json",
                                              )
            if error:
                self.log.error(action, error)
                return None

            if credentials:
                try:
                    access_token = credentials["access_token"]
                except (KeyError, TypeError):
                    self.log.error(action, "No access token received")
                    return None

                ttl = credentials.get("expires_in")
                if ttl:
                    token_expiry_date = now + datetime.timedelta(seconds=ttl)
                else:
                    token_expiry_date = None

                token_type = credentials.get("token_type", "Bearer")

                table = current.s3db.fin_payment_service
                query = table.id == self.service_id
                current.db(query).update(token_type = token_type,
                                         access_token = access_token,
                                         token_expiry_date = token_expiry_date,
                                         )

                self.token_type = token_type
                self.access_token = access_token
                self.token_expiry_date = token_expiry_date

                self.log.success(action)
                return self.access_token
            else:
                self.log.error(action, "No credentials received")
        else:
            self.log.error(action, "Lacking client ID/secret to fetch access token")

        return None

    # -------------------------------------------------------------------------
    def get_user_info(self):
        """
            Retrieve user information (of the config owner)

            @returns: a dict with user details
        """

        action = "Get User Info"

        userinfo, _, error = self.http(method = "GET",
                                       path = "/v1/identity/oauth2/userinfo",
                                       args = {"schema": "paypalv1.1"},
                                       auth = "Token",
                                       decode = "json",
                                       )
        if error:
            self.log.error(action, error)
            return None
        else:
            self.log.success(action)

        return userinfo

    # -------------------------------------------------------------------------
    def register_product(self, product_id):
        """
            Register a product with this payment service

            @param product_id: the fin_product record ID

            @returns: True if successful, or False on error
        """

        success = False

        if self.has_product(product_id):
            # Product is already registered with this service
            # => update it
            success = self.update_product(product_id)

        else:
            action = "Register Product %s" % product_id

            db = current.db
            s3db = current.s3db

            # Get product data
            ptable = s3db.fin_product
            query = (ptable.id == product_id) & \
                    (ptable.deleted == False)
            row = db(query).select(ptable.name,
                                   ptable.description,
                                   ptable.type,
                                   ptable.category,
                                   limitby = (0, 1),
                                   ).first()
            if not row:
                self.log.error(action, "Product not found")
            else:
                # Register Product
                response, status, error = self.http(method = "POST",
                                                    path = "/v1/catalogs/products",
                                                    #args = None,
                                                    data = {
                                                        "name": row.name,
                                                        "description": row.description,
                                                        "type": row.type,
                                                        "category": row.category,
                                                        #"image_url": None,
                                                        #"home_url": None,
                                                        },
                                                    #headers = None,
                                                    auth = "Token",
                                                    #encode = "json",
                                                    #decode = "json",
                                                    )
                if error:
                    reason = ("%s %s" % (status, error)) if status else error
                    self.log.error(action, reason)

                else:
                    success = True
                    self.log.success(action)

                    # Extract registration details from response
                    refno = response["id"]

                    # Create or update product<=>service link
                    # - no onaccept here (onaccept calls this)
                    ltable = s3db.fin_product_service
                    ltable.update_or_insert(
                        (ltable.product_id == product_id) & \
                        (ltable.service_id == self.service_id),
                        product_id = product_id,
                        service_id = self.service_id,
                        is_registered = True,
                        refno = refno,
                        )

        return success

    # -------------------------------------------------------------------------
    def update_product(self, product_id):
        """
            Update a product registration in this payment service

            @param product_id: the fin_product record ID

            @returns: True if successful, or False on error
        """

        action = "Update product %s" % product_id
        success = False

        # TODO Not working
        #      - API refuses to accept patch in documented format
        #      - maybe just a sandbox limitation?
        self.log.info(action, "Not supported by API")
        return True

        db = current.db
        s3db = current.s3db

        # Get product data
        ptable = s3db.fin_product
        ltable = s3db.fin_product_service
        left = ltable.on((ltable.product_id == ptable.id) & \
                         (ltable.service_id == self.service_id) & \
                         (ltable.deleted == False))
        query = (ptable.id == product_id) & \
                (ptable.deleted == False)
        row = db(query).select(ltable.refno,
                               ptable.description,
                               ptable.category,
                               left = left,
                               limitby = (0, 1),
                               ).first()

        if not row or not row.fin_product_service.refno:
            self.log.error(action, "Product registration not found")
        else:
            path = "/v1/catalogs/products/%s" % row.fin_product_service.refno

            # Update Product Details
            updates = [{"op": "replace",
                        "path": "/description",
                        "value": row.fin_product.description,
                        },
                       {"op": "replace",
                        "path": "/category",
                        "value": row.fin_product.category,
                        },
                       #TODO "image_url"
                       #TODO "home_url"
                       ]

            _, status, error = self.http(method = "PATCH",
                                         path = path,
                                         data = updates,
                                         auth = "Token",
                                         )
            if error:
                reason = ("%s %s" % (status, error)) if status else error
                self.log.error(action, reason)
            else:
                success = True
                self.log.success(action)

        return success

    # -------------------------------------------------------------------------
    def retire_product(self, product_id):
        """
            Retire a product from this payment service

            @param product_id: the fin_product record ID

            @returns: True if successful, or False on error
        """

        action = "Retire product %s" % product_id

        # PayPal API does not support deletion of products
        self.log.info(action, "Not supported by API")

        return True

    # -------------------------------------------------------------------------
    def register_subscription_plan(self, plan_id):
        """
            Register a subscription plan with this service

            @param plan_id: the fin_subscription_plan record ID

            @returns: True if successful, or False on error
        """

        if self.has_subscription_plan(plan_id):
            # Plan is already registered with this service
            # => update it
            return self.update_subscription_plan(plan_id)

        action = "Register subscription plan #%s" % plan_id
        error = None

        s3db = current.s3db
        db = current.db

        # Get subscription plan details
        table = s3db.fin_subscription_plan
        query = (table.id == plan_id) & \
                (table.deleted == False)
        plan = db(query).select(table.id,
                                table.name,
                                table.description,
                                table.status,
                                table.product_id,
                                table.interval_unit,
                                table.interval_count,
                                table.fixed,
                                table.total_cycles,
                                table.price,
                                table.currency,
                                limitby = (0, 1),
                                ).first()

        # Verify plan status, and make sure the product is registered
        if not plan:
            error = "Subscription plan not found"
        elif plan.status != "ACTIVE":
            error = "Cannot register inactive subscription plan"
        else:
            product_id = plan.product_id
            if not self.has_product(product_id) and \
               not self.register_product(product_id):
                error = "Could not register product with service"
        if error:
            self.log.error(action, error)
            return False

        # Get product reference number
        ltable = s3db.fin_product_service
        query = (ltable.product_id == product_id) & \
                (ltable.service_id == self.service_id) & \
                (ltable.deleted == False)
        product = db(query).select(ltable.refno,
                                   limitby = (0, 1),
                                   ).first()
        if not product or not product.refno:
            self.log.error(action, "Product reference number missing")
            return False

        # Build data structure

        # Billing Cycles
        billing_cycles = [
            {"frequency": {"interval_unit": plan.interval_unit,
                           "interval_count": plan.interval_count,
                           },
             "tenure_type": "REGULAR",
             "sequence": 1,
             "total_cycles": plan.total_cycles if plan.fixed else 0,
             "pricing_scheme": {"fixed_price": {"value": plan.price,
                                                "currency_code": plan.currency,
                                                },
                                },
             },
            ]

        # Payment Preferences
        payment_preferences = {
            "auto_bill_outstanding": True,
            "payment_failure_threshold": 0,
            #"setup_fee", ?
            }

        # Subscription Plan
        data = {
            "product_id": product.refno,
            "name": plan.name,
            "description": plan.description,

            #"status": "ACTIVE", # default

            "quantity_supported": False,
            "billing_cycles": billing_cycles,
            "payment_preferences": payment_preferences,
            #"taxes": taxes, ?
            }

        response, status, error = self.http(method = "POST",
                                            path = "/v1/billing/plans",
                                            data = data,
                                            auth = "Token",
                                            )

        if error:
            reason = ("%s %s" % (status, error)) if status else error
            self.log.error(action, reason)
            return False
        else:
            self.log.success(action)

            # Get reference number from response
            refno = response["id"]

            # Create or update subscription_plan<=>service link
            # - no onaccept here (onaccept calls this)
            ltable = s3db.fin_subscription_plan_service
            query = (ltable.plan_id == plan_id) & \
                    (ltable.service_id == self.service_id) & \
                    (ltable.deleted == False)
            ltable.update_or_insert(query,
                                    plan_id = plan_id,
                                    service_id = self.service_id,
                                    is_registered = True,
                                    refno = refno,
                                    )

        return True

    # -------------------------------------------------------------------------
    def update_subscription_plan(self, plan_id):
        """
            Update a subscription plan

            @param plan_id: the fin_subscription_plan record ID

            @returns: True if successful, or False on error
        """

        action = "Update subscription plan %s" % plan_id

        # TODO implement
        self.log.info(action, "Not yet implemented")

        return True

    # -------------------------------------------------------------------------
    @staticmethod
    def get_subscriber_info(pe_id):
        """
            Retrieve information about the subscriber from the DB

            @param pe_id: the PE ID of the subscriber

            @returns: a tuple (info, error)
        """

        info, error = S3PaymentService.get_subscriber_info(pe_id)
        if error:
            return None, error
        else:
            # Map info to PayPal-specific structure
            name = {"given_name": info["first_name"],
                    }
            if "last_name" in info:
                name["surname"] = info["last_name"]
            subscriber = {"name": name}
            if "email" in info:
                subscriber["email_address"] = info["email"]

        return subscriber, None

    # -------------------------------------------------------------------------
    def register_subscription(self, plan_id, pe_id):
        """
            Register a subscription with this service

            @param plan_id: the subscription plan ID
            @param pe_id: the subscriber PE ID

            @returns: the record ID of the newly created subscription
        """

        action = "Register subscription for subscriber #%s with plan #%s" % (pe_id, plan_id)

        db = current.db
        s3db = current.s3db

        # Lookup subscription plan
        sptable = s3db.fin_subscription_plan
        query = (sptable.id == plan_id) & \
                (sptable.status != "INACTIVE") & \
                (sptable.deleted == False)
        plan = db(query).select(sptable.id,
                                sptable.product_id,
                                limitby = (0, 1),
                                ).first()
        if not plan:
            self.log.fatal(action, "Subscription plan not found")
            return None

        # Make sure subscription plan is registered with this service
        if not self.has_subscription_plan(plan_id) and \
           not self.register_subscription_plan(plan_id):
            self.log.fatal(action, "Could not register subscription plan #%s" % plan_id)
            return None

        # Look up subscription plan reference number
        ltable = s3db.fin_subscription_plan_service
        query = (ltable.plan_id == plan_id) & \
                (ltable.service_id == self.service_id) & \
                (ltable.deleted == False)
        registration = db(query).select(ltable.refno,
                                        limitby = (0, 1),
                                        ).first()
        refno = registration.refno

        # Look up merchant
        merchant = self.get_merchant_name(plan.product_id)
        if not merchant:
            self.log.warning(action, "Unknown merchant")
            merchant = "Unknown"

        # Look up subscriber
        subscriber, error = self.get_subscriber_info(pe_id)
        if error:
            self.log.fatal(action, error)
            return None

        # Create the subscription record (registration pending),
        stable = s3db.fin_subscription
        subscription_id = stable.insert(plan_id = plan_id,
                                        service_id = self.service_id,
                                        pe_id = pe_id,
                                        #status = "NEW",
                                        )
        if not subscription_id:
            self.log.fatal(action, "Could not create subscription")
            return None

        # The URL to return to upon approval/cancel:
        return_url = URL(c = "fin",
                         f = "subscription",
                         args = [subscription_id, "confirm"],
                         host = True,
                         )
        cancel_url = URL(c = "fin",
                         f = "subscription",
                         args = [subscription_id, "cancel"],
                         host = True,
                         )

        # Subscription application details
        application = {"brand_name": merchant,
                       "locale": "en-US",
                       "shipping_preference": "NO_SHIPPING",
                       # With user_action=="CONTINUE", a separate API request
                       # is required to activate the subscription, whereas
                       # "SUBSCRIBE_NOW" will auto-activate it after the
                       # consensus dialog is completed
                       "user_action": "SUBSCRIBE_NOW",

                       "payment_method": {
                           "payer_selected": "PAYPAL",
                           "payee_preferred": "IMMEDIATE_PAYMENT_REQUIRED"
                           },
                       "return_url": return_url,
                       "cancel_url": cancel_url,
                       }

        data = {"plan_id": refno,
                "subscriber": subscriber,
                "application_context": application,
                }

        response, status, error = self.http(method = "POST",
                                            path = "/v1/billing/subscriptions",
                                            data = data,
                                            auth = "Token",
                                            )

        if error:
            reason = ("%s %s" % (status, error)) if status else error
            self.log.error(action, reason)
            db(stable.id==subscription_id).delete()
            subscription_id = None
        else:
            # Extract the subscription reference (ID)
            ref = response["id"]
            if not ref:
                self.log.error(action, "No subscription reference received")
                db(stable.id==subscription_id).delete()
                return None

            # Get the approval URL
            links = response["links"]
            for link in links:
                if link["rel"] == "approve":
                    approval_url = link["href"]
                    break

            # Store reference and approval URL
            db(stable.id==subscription_id).update(refno = ref,
                                                  approval_url = approval_url,
                                                  )
            self.log.success(action)

        return subscription_id

    # -------------------------------------------------------------------------
    def check_subscription(self, subscription_id):
        """
            Check the current status of a subscription and update it
            in the database; triggers onaccept callback(s) for the
            subscription to prompt automated fulfillment/cancelation
            actions

            @param subscription_id: the subscription record ID

            @returns: the current status of the subscription, or None on error
        """

        action = "Check subscription #%s" % subscription_id

        db = current.db
        s3db = current.s3db

        stable = s3db.fin_subscription
        row = db(stable.id == subscription_id).select(stable.refno,
                                                      stable.status,
                                                      stable.status_date,
                                                      limitby = (0, 1),
                                                      ).first()
        if not row:
            self.log.error(action, "Subscription not found")
            return None

        # Prevent excessive status request rate
        limit = datetime.datetime.utcnow() - datetime.timedelta(minutes=1)
        if row.status != "NEW" and \
           row.status_date and row.status_date > limit:
            return row.status

        status_path = "/v1/billing/subscriptions/%s" % row.refno
        response, status, error = self.http(method = "GET",
                                            path = status_path,
                                            auth = "Token",
                                            )
        if error:
            if status == 404:
                # Subscription does not exist
                self.log.warning(action, "Subscription not found")
                subscription_status = "CANCELLED"
            else:
                # Status-Check failed
                reason = ("%s %s" % (status, error)) if status else error
                self.log.error(action, reason)
                return None
        else:
            # Read subscription status from response
            subscription_status = response.get("status")
            if subscription_status:
                self.log.success(action)
            else:
                subscription_status = None
                self.log.warning(action, "Unclear subscription status")

        # Update status in any case (even if None), so callbacks
        # can take appropriate action
        data = {"status": subscription_status,
                "status_date": datetime.datetime.utcnow()
                }
        db(stable.id==subscription_id).update(**data)
        # Call onaccept to trigger automated fulfillment/cancelation actions
        data["id"] = subscription_id
        s3db.onaccept(stable, data, method="update")

        return subscription_status

    # -------------------------------------------------------------------------
    def activate_subscription(self, subscription_id):
        """
            Activate a subscription (on the service side)

            @param subscription_id: the subscription record ID

            @returns: True if successful, or False on error
        """

        action = "Activate subscription #%s" % subscription_id

        db = current.db
        s3db = current.s3db

        # Get the subscription reference number
        stable = s3db.fin_subscription
        row = db(stable.id == subscription_id).select(stable.refno,
                                                      limitby = (0, 1),
                                                      ).first()
        if not row:
            self.log.error(action, "Subscription not found")
            return False

        path = "/v1/billing/subscriptions/%s/activate" % row.refno
        status, error = self.http(method = "POST",
                                  path = path,
                                  data = {"reason": "(Re)activating the subscription"},
                                  auth = "Token",
                                  )[1:3]
        if error:
            if status == 404:
                # Subscription does not exist
                self.log.warning(action, "Subscription not found")
                subscription_status = "CANCELLED"
            else:
                # Activation failed
                reason = ("%s %s" % (status, error)) if status else error
                self.log.error(action, reason)
                return False
        else:
            subscription_status = "ACTIVE"
            self.log.success(action)

        # Update status
        data = {"status": subscription_status,
                "status_date": datetime.datetime.utcnow()
                }
        db(stable.id==subscription_id).update(**data)

        # Call onaccept to trigger automated fulfillment actions
        data["id"] = subscription_id
        s3db.onaccept(stable, data, method="update")

        return True

    # -------------------------------------------------------------------------
    def cancel_subscription(self, subscription_id):
        """
            Cancel a subscription

            @param subscription_id: the subscription record ID

            @returns: True if successful, or False on error
        """

        action = "Cancel subscription #%s" % subscription_id

        db = current.db
        s3db = current.s3db

        # Get the subscription reference number
        stable = s3db.fin_subscription
        row = db(stable.id == subscription_id).select(stable.refno,
                                                      stable.status,
                                                      limitby = (0, 1),
                                                      ).first()
        if not row:
            self.log.error(action, "Subscription not found")
            return False
        if row.status == "CANCELLED":
            self.log.warning(action, "Subscription was already cancelled")
            return True

        path = "/v1/billing/subscriptions/%s/cancel" % row.refno
        status, error = self.http(method = "POST",
                                  path = path,
                                  data = {"reason": "Client requested cancellation"},
                                  auth = "Token",
                                  decode = "bytes",
                                  )[1:3]
        if error:
            if status == 404:
                # Subscription does not exist
                self.log.warning(action, "Subscription not found")
                subscription_status = "CANCELLED"
            else:
                # Activation failed
                reason = ("%s %s" % (status, error)) if status else error
                self.log.error(action, reason)
                return False
        else:
            subscription_status = "CANCELLED"
            self.log.success(action)

        # Update status
        data = {"status": subscription_status,
                "status_date": datetime.datetime.utcnow()
                }
        db(stable.id==subscription_id).update(**data)

        # Call onaccept to trigger automated cancellation actions
        data["id"] = subscription_id
        s3db.onaccept(stable, data, method="update")

        return True

# END =========================================================================
