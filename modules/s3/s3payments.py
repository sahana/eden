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
            current.log.error("Payment Services: '%s' failed due to '%s'" % (action, reason))

    # -------------------------------------------------------------------------
    # Shortcuts
    #
    def info(self, action, reason):
        self.write(action, "INFO", reason)
    def success(self, action, reason):
        self.write(action, "SUCCESS", reason)
    def warning(self, action, reason):
        self.write(action, "WARNING", reason)
    def error(self, action, reason):
        self.write(action, "ERROR", reason)
    def fatal(self, action, reason):
        self.write(action, "FATAL", reason)

# =============================================================================
class S3PaymentService(object):
    """ Online Payment Service (base class) """

    def __init__(self, row):
        """
            Constructor

            @param row: the fin_payment_service Row
        """

        # TODO perhaps not necessary:
        if not row:
            raise SyntaxError("Payment service configuration required")

        # Store service config record ID
        self.service_id = row.id
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

    def get_user_info(self):
        # TODO docstring

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
        req = urllib2.Request(url = url,
                              method = method,
                              )

        # Request data
        if method == "GET":
            request_data = None
        elif data:
            # TODO Py2 compat
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
            error = e.read()
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
                # TODO Py2 compat
                output = f.read().decode("utf-8")
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
            # Add a HTTP-401-handler (if pre-emptive Auth not acceptable)
            # TODO do this only if no pre-emptive Auth
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
    # Factory Method
    # -------------------------------------------------------------------------
    @staticmethod
    def adapter(service_id):
        """
            Instantiate and return a suitable API adapter for a payment
            service

            @param service_id: the fin_payment_service record ID
        """

        # TODO Check permissions
        # Current user must have read-permission for this record
        # - use accessible_query? or just has_permission? or resource.select?

        # Load service configuration
        table = current.s3db.fin_payment_service
        row = current.db(table.id == service_id).select(table.id,
                                                        table.api_type,
                                                        table.base_url,
                                                        table.use_proxy,
                                                        table.proxy,
                                                        table.username,
                                                        table.password,
                                                        table.token_type,
                                                        table.access_token,
                                                        table.token_expiry_date,
                                                        limitby = (0, 1),
                                                        ).first()
        if not row:
            raise KeyError("Payment service configuration #%s not found" % service_id)

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
    def get_user_info(self):
        # TODO implement

        raise NotImplementedError

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

                self.log.success(action, "Access token received")
                return self.access_token
            else:
                self.log.error(action, "No credentials received")
        else:
            self.log.error(action, "Lacking client ID/secret to fetch access token")

        return None

# END =========================================================================
