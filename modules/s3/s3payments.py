# -*- coding: utf-8 -*-

""" Online Payment Services Integration

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

__all__ = (#"S3Payments",
           "S3PaymentService",
           )

import datetime
import json
import sys

from gluon import current

from s3compat import PY2, HTTPError, URLError, urlencode, urllib2
from .s3rest import S3Method
from .s3utils import s3_str
from .s3validators import JSONERRORS

# =============================================================================
class S3Payments(S3Method):
    """ REST Methods to interact with online payment services """

    # TODO implement

    pass

# =============================================================================
class S3PaymentLog(object):
    """
        Simple log writer for Payment Service Adapters
    """

    def __init__(self, service_id):
        """
            Constructor

            @param service_id: the fin_payment_service record ID
        """
        self.service_id = service_id

    # -------------------------------------------------------------------------
    def write(self, action, result, reason):
        """
            Add a log entry

            @param action: description of the attempted action
            @param result: result of the action
            @param reason: reason for the result (e.g. error message)

            NB: Logging process must either explicitly commit before
                raising an exception, or catch+resolve all exceptions,
                otherwise the log entries will be rolled back
        """

        if not action or not result:
            return

        table = current.s3db.fin_payment_log
        table.insert(date = datetime.datetime.utcnow(),
                     service_id = self.service_id,
                     action = action,
                     result = result,
                     reason = reason,
                     )

        if result in ("ERROR", "FATAL"):
            # Support debugging by additionally logging critical
            # errors in log file (if enabled), in case a subsequent
            # uncaught exception would roll back the DB log entry
            if reason:
                msg = "'%s' failed [%s]" % (action, reason)
            else:
                msg = "'%s' failed" % action
            current.log.error("Payment Service #%s: %s" % (self.service_id, msg))

    # -------------------------------------------------------------------------
    # Shortcuts
    #
    def info(self, action, reason=None):
        self.write(action, "INFO", reason)
    def success(self, action, reason=None):
        self.write(action, "SUCCESS", reason)
    def warning(self, action, reason=None):
        self.write(action, "WARNING", reason)
    def error(self, action, reason=None):
        self.write(action, "ERROR", reason)
    def fatal(self, action, reason=None):
        self.write(action, "FATAL", reason)

# =============================================================================
class S3PaymentService(object):
    """ Online Payment Service (base class) """

    def __init__(self, row):
        """
            Constructor

            @param row: the fin_payment_service Row
        """

        # Store service config record ID
        self.service_id = row.id

        # Instantiate log writer
        self.log = S3PaymentLog(self.service_id)

        # Store attributes
        self.base_url = row.base_url
        self.use_proxy = row.use_proxy
        self.proxy = row.proxy

        self.username = row.username
        self.password = row.password

        self.token_type = row.token_type
        self.access_token = row.access_token
        self.token_expiry_date = row.token_expiry_date

    # -------------------------------------------------------------------------
    # API Functions (to be implemented by subclasses)
    # -------------------------------------------------------------------------
    def get_access_token(self):
        """
            Retrieve and store a new access token for Token-Auth using
            current username (=client_id) and password (=client_secret);
            to be called implicitly by http() if/when required

            @returns: the new access token if successful, otherwise None
        """
        raise NotImplementedError

    # -------------------------------------------------------------------------
    def get_user_info(self):
        """
            Retrieve user information from this service; for account
            verification and API testing (implementation optional)

            @returns: a dict with user details
        """
        raise NotImplementedError

    # -------------------------------------------------------------------------
    def register_product(self, product_id):
        """
            Register a product with this payment service

            @param product_id: the fin_product record ID

            @returns: True if successful, or False on error
        """
        raise NotImplementedError

    # -------------------------------------------------------------------------
    def update_product(self, product_id):
        """
            Update a product registration in this payment service

            @param product_id: the fin_product record ID

            @returns: True if successful, or False on error
        """
        raise NotImplementedError

    # -------------------------------------------------------------------------
    def retire_product(self, product_id):
        """
            Retire a product from this payment service

            @param product_id: the fin_product record ID

            @returns: True if successful, or False on error
        """
        raise NotImplementedError

    # -------------------------------------------------------------------------
    def register_subscription_plan(self, plan_id):
        """
            Register a subscription plan with this service

            @param plan_id: the fin_subscription_plan record ID

            @returns: True if successful, or False on error
        """
        raise NotImplementedError

    # -------------------------------------------------------------------------
    def update_subscription_plan(self, plan_id):
        """
            Update a subscription plan

            @param plan_id: the fin_subscription_plan record ID

            @returns: True if successful, or False on error
        """
        raise NotImplementedError

    # -------------------------------------------------------------------------
    # Utility Functions
    # -------------------------------------------------------------------------
    def http(self,
             method = "GET",
             path = None,
             args = None,
             data = None,
             headers = None,
             auth = False,
             encode = "json",
             decode = "json",
             ):
        """
            Send a HTTP request to the REST API

            @param method: the HTTP method
            @param path: the path relative to the base URL of the service
            @param args: dict of URL parameters
            @param data: data to send (JSON-serializable object)
            @param auth: False - do not send an Auth header
                         "Basic" - send an Auth header with username+password
                         "Token" - send an Auth header with access token
            @param encode: encode the request data as "json"|"text"|"bytes"
            @param decode: decode the response as "json"|"text"|"bytes"
        """

        base_url = self.base_url
        if not base_url:
            return None, None, "No base URL set"

        url = base_url.rstrip("/")
        if path:
            url = "/".join((url, path.lstrip("/")))
        if args:
            url = "?".join((url, urlencode(args)))

        # Generate the Request
        if PY2:
            req = urllib2.Request(url)
            req.get_method = lambda: method
        else:
            req = urllib2.Request(url = url, method = method)

        # Request data
        if method == "GET":
            request_data = None
        elif data:
            if encode == "json":
                request_data = json.dumps(data).encode("utf-8")
                req.add_header("Content-Type", "application/json")
            elif encode == "text":
                request_data = s3_str(data).encode("utf-8")
                req.add_header("Content-Type", "text/plain; charset=UTF-8")
            else:
                request_data = s3_str(data).encode("utf-8")
                req.add_header("Content-Type", "application/octet-stream")
        else:
            request_data = None

        # Acceptable response type
        if decode == "json":
            req.add_header("Accept", "application/json")
        else:
            req.add_header("Accept", "*/*")

        # Run the request
        output = status = error = None

        opener = self._http_opener(req, headers=headers, auth=auth)
        try:
            f = opener.open(req, data=request_data)
        except HTTPError as e:
            # HTTP error status
            status = e.code
            error = s3_str(e.read())
        except URLError as e:
            # Network Error
            error = e.reason
            if not error:
                error = "Unknown network error"
        except Exception:
            # Other Error
            error = sys.exc_info()[1]
        else:
            status = f.code

            # Decode the response
            if decode == "json":
                try:
                    output = json.load(f)
                except JSONERRORS:
                    error = sys.exc_info()[1]
            elif decode == "text":
                output = s3_str(f.read())
            else:
                # return the stream as-is
                output = f

        return output, status, error

    # -------------------------------------------------------------------------
    def _http_opener(self, req, headers=None, auth=True):
        """
            Configure a HTTP opener for API operations

            @param req: the Request
            @param headers: array of HTTP headers
            @param auth: False - do not add Authorization
                         "Basic" - add Auth header using username+password
                         "Token" - add Auth header using access token
                         any tru-ish value - add a 401-handler with username+password

            @returns: OpenerDirector instance
        """

        # Configure opener headers
        addheaders = []
        if headers:
            addheaders.extend(headers)

        # Configure opener handlers
        handlers = []

        # Proxy handling
        proxy = self.proxy
        if proxy and self.use_proxy:
            protocol = req.get_type() if PY2 else req.type
            proxy_handler = urllib2.ProxyHandler({protocol: proxy})
            handlers.append(proxy_handler)

        # Authentication handling
        username = self.username
        password = self.password

        if auth == "Basic":
            if username and password:
                import base64
                base64string = base64.b64encode(('%s:%s' % (username, password)).encode("utf-8"))
                addheaders.append(("Authorization", "Basic %s" % s3_str(base64string)))

        elif auth == "Token":
            token = self.access_token
            token_type = self.token_type or "Bearer"
            expiry_date = self.token_expiry_date
            if not token or \
               expiry_date and expiry_date <= current.request.utcnow:
                try:
                    token = self.get_access_token()
                except NotImplementedError:
                    token = None
            if token:
                addheaders.append(("Authorization", "%s %s" % (token_type, token)))

        else:
            # No pre-emptive auth
            pass

        if auth and username and password:
            # Add a HTTP-401-handler as fallback in case pre-emptive auth fails
            passwd_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
            passwd_manager.add_password(realm = None,
                                        uri = req.get_full_url(),
                                        user = username,
                                        passwd = password,
                                        )
            auth_handler = urllib2.HTTPBasicAuthHandler(passwd_manager)
            handlers.append(auth_handler)

        # Create the opener and add headers
        opener = urllib2.build_opener(*handlers)
        if addheaders:
            opener.addheaders = addheaders

        return opener

    # -------------------------------------------------------------------------
    def has_product(self, product_id):
        """
            Check whether a product is already registered with this service

            @param product_id: the fin_product record ID

            @returns: boolean
        """

        table = current.s3db.fin_product_service
        query = (table.product_id == product_id) & \
                (table.service_id == self.service_id) & \
                (table.deleted == False)

        row = current.db(query).select(table.is_registered,
                                       limitby = (0, 1),
                                       ).first()

        return row.is_registered if row else False

    # -------------------------------------------------------------------------
    def has_subscription_plan(self, plan_id):
        """
            Check whether a subscription_plan is already registered
            with this service

            @param plan_id: the fin_subscription_plan record ID

            @returns: boolean
        """

        table = current.s3db.fin_subscription_plan_service
        query = (table.plan_id == plan_id) & \
                (table.service_id == self.service_id) & \
                (table.deleted == False)

        row = current.db(query).select(table.is_registered,
                                       limitby = (0, 1),
                                       ).first()

        return row.is_registered if row else False

    # -------------------------------------------------------------------------
    # Factory Method
    # -------------------------------------------------------------------------
    @staticmethod
    def adapter(service_id):
        """
            Instantiate and return a suitable API adapter for a payment
            service

            @param service_id: the fin_payment_service record ID
        """

        # Load service configuration
        # - resource.select implies READ permission required,
        #   so access to service config can be restricted to
        #   certain user roles and realms
        resource = current.s3db.resource("fin_payment_service",
                                         id = service_id,
                                         )
        rows = resource.select(["id",
                                "api_type",
                                "base_url",
                                "use_proxy",
                                "proxy",
                                "username",
                                "password",
                                "token_type",
                                "access_token",
                                "token_expiry_date",
                                ],
                                limit = 1,
                                as_rows = True,
                                )
        if not rows:
            raise KeyError("Payment service configuration #%s not found" % service_id)
        row = rows[0]

        # Get adapter for API type
        adapters = {"PAYPAL": PayPalAdapter,
                    }
        adapter = adapters.get(row.api_type)
        if not adapter:
            raise ValueError("Invalid API type: %s" % row.api_type)

        # Instantiate adapter with Row and return it
        return adapter(row)

# =============================================================================
class PayPalAdapter(S3PaymentService):
    """ API Adapter for PayPal """

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

# END =========================================================================
