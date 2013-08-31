# -*- coding: utf-8 -*-

""" S3 Notifications

    @copyright: 2011-13 (c) Sahana Software Foundation
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

import datetime
import os
import sys
import urlparse
import urllib2
from urllib import urlencode
from uuid import uuid4

try:
    from cStringIO import StringIO # Faster, where available
except:
    from StringIO import StringIO

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module
        
from gluon import *
from gluon.storage import Storage
from gluon.tools import fetch

from s3utils import s3_truncate, s3_unicode

DEBUG = False
if DEBUG:
    print >> sys.stderr, "S3NOTIFY: DEBUG MODE"

    def _debug(m):
        print >> sys.stderr, m
else:
    _debug = lambda m: None

# =============================================================================
class S3Notifications(object):
    """ Framework to send notifications about subscribed events """

    # -------------------------------------------------------------------------
    @classmethod
    def check_subscriptions(cls):
        """
            Scheduler entry point, creates notification tasks for all
            active subscriptions which (may) have updates.
        """

        now = datetime.utcnow()

        _debug("S3Notifications.check_subscriptions(now=%s)" % now)

        subscriptions = cls._subscriptions(now)
        if subscriptions:
            async = current.s3task.async
            for row in subscriptions:
                # Create asynchronous notification task.
                row.update_record(locked=True)
                async("notify_notify", args=[row.id])
            message = "%s notifications scheduled." % len(subscriptions)
            current.db.commit()
        else:
            message = "No notifications to schedule."

        _debug(message)
        return message

    # -------------------------------------------------------------------------
    @classmethod
    def notify(cls, resource_id):
        """
            Asynchronous task to notify a subscriber about updates,
            runs a POST?format=msg request against the subscribed
            controller which extracts the data and renders and sends
            the notification message (see send()).

            @param resource_id: the pr_subscription_resource record ID
        """

        _debug("S3Notifications.notify(resource_id=%s)" % resource_id)

        db = current.db
        s3db = current.s3db

        stable = s3db.pr_subscription
        rtable = db.pr_subscription_resource
        ftable = s3db.pr_filter

        # Extract the subscription data
        join = stable.on(rtable.subscription_id == stable.id)
        left = ftable.on(ftable.id == stable.filter_id)

        # @todo: should not need rtable.resource here
        row = db(rtable.id == resource_id).select(stable.id,
                                                  stable.pe_id,
                                                  stable.frequency,
                                                  stable.notify_on,
                                                  stable.method,
                                                  stable.email_format,
                                                  rtable.id,
                                                  rtable.resource,
                                                  rtable.url,
                                                  rtable.last_check_time,
                                                  ftable.query,
                                                  join=join,
                                                  left=left).first()
        if not row:
            return True

        s = getattr(row, "pr_subscription")
        r = getattr(row, "pr_subscription_resource")
        f = getattr(row, "pr_filter")

        # Create a temporary token to authorize the lookup request
        auth_token = str(uuid4())

        # Store the auth_token in the subscription record
        r.update_record(auth_token=auth_token)
        db.commit()

        # Construct the send-URL
        settings = current.deployment_settings
        public_url = settings.get_base_public_url()
        lookup_url = "%s/%s/%s" % (public_url,
                                   current.request.application,
                                   r.url.lstrip("/"))
                                   
        # Break up the URL into its components
        purl = list(urlparse.urlparse(lookup_url))

        # Subscription parameters
        last_check_time = current.xml.encode_iso_datetime(r.last_check_time)
        query = {"subscription": auth_token, "format": "msg"}
        if "upd" in s.notify_on:
            query["~.modified_on__ge"] = last_check_time
        else:
            query["~.created_on__ge"] = last_check_time

        # Filters
        if f.query:
            from s3filter import S3FilterString
            resource = s3db.resource(r.resource)
            fstring = S3FilterString(resource, f.query)
            for k, v in fstring.get_vars.iteritems():
                if v is not None:
                    if k in query:
                        value = query[k]
                        if type(value) is list:
                            value.append(v)
                        else:
                            query[k] = [value, v]
                    else:
                        query[k] = v
            query_nice = s3_unicode(fstring.represent())
        else:
            query_nice = None

        # Add subscription parameters and filters to the URL query, and
        # put the URL back together
        query = urlencode(query)
        if purl[4]:
            query = "&".join((purl[4], query))
        page_url = urlparse.urlunparse([purl[0], # scheme
                                        purl[1], # netloc
                                        purl[2], # path
                                        purl[3], # params
                                        query,   # query
                                        purl[5], # fragment
                                        ])
                                       
        # Serialize data for send (avoid second lookup in send)
        data = json.dumps({"pe_id": s.pe_id,
                           "notify_on": s.notify_on,
                           "method": s.method,
                           "email_format": s.email_format,
                           "resource": r.resource,
                           "last_check_time": last_check_time,
                           "filter_query": query_nice,
                           })

        # Send the request
        _debug("Requesting %s" % page_url)
        req = urllib2.Request(page_url, data=data)
        req.add_header('Content-Type', "application/json")
        success = False
        try:
            response = json.loads(urllib2.urlopen(req).read())
            message = response["message"]
            if response["status"] == "success":
                success = True
        except urllib2.HTTPError, e:
            message = ("HTTP %s: %s" % (e.code, e.read()))
        except:
            exc_info = sys.exc_info()[:2]
            message = ("%s: %s" % (exc_info[0].__name__, exc_info[1]))
        _debug(message)

        # Update time stamps and unlock, invalidate auth token
        intervals = s3db.pr_subscription_check_intervals
        interval = datetime.timedelta(minutes=intervals.get(s.frequency, 0))
        if success:
            last_check_time = datetime.datetime.utcnow()
            next_check_time = last_check_time + interval
            r.update_record(auth_token=None,
                            locked=False,
                            last_check_time=last_check_time,
                            next_check_time=next_check_time)
        else:
            r.update_record(auth_token=None,
                            locked=False)
        db.commit()

        # Done
        return message

    # -------------------------------------------------------------------------
    @classmethod
    def send(cls, r, resource):
        """
            Method to retrieve updates for a subscription, render the
            notification message and send it - responds to POST?format=msg
            requests to the respective resource.

            @param r: the S3Request
            @param resource: the S3Resource
        """

        _debug("S3Notifications.send()")

        json_message = current.xml.json_message

        # Read subscription data
        source = r.body
        source.seek(0)
        data = source.read()
        subscription = json.loads(data)

        #_debug("Notify PE #%s by %s on %s of %s since %s" % (
                    #subscription["pe_id"],
                    #str(subscription["method"]),
                    #str(subscription["notify_on"]),
                    #subscription["resource"],
                    #subscription["last_check_time"]))

        notify_on = subscription["notify_on"]
        methods = subscription["method"]
        if not notify_on or not methods:
            return json_message(message="No notifications configured "
                                        "for this subscription")

        # Authorization (subscriber must be logged in)
        auth = current.auth
        pe_id = subscription["pe_id"]
        if not auth.s3_logged_in() or auth.user.pe_id != pe_id:
            r.unauthorised()

        # Last check time
        last_check_time = current.xml.decode_iso_datetime(
                                subscription["last_check_time"])

        # Fields to report
        fields = resource.list_fields(key="notify_fields")
        if "created_on" not in fields:
            fields.append("created_on")

        # Extract the data
        data = resource.select(fields,
                               represent=True,
                               raw_data=True)
        rows = data["rows"]

        # How many records do we have?
        numrows = len(rows)
        if not numrows:
            return json_message(message="No records found")

        #_debug("%s rows:" % numrows)

        # Render and send the messages
        settings = current.deployment_settings
        
        join = lambda *f: os.path.join(current.request.folder, *f)
        theme = settings.get_template()
        send = current.msg.send_by_pe_id

        success = False
        errors = []

        # Email format
        email_format = subscription["email_format"]
        if not email_format:
            email_format = settings.get_msg_notification_email_format()

        # Pre-render the contents for the view
        contents = {}
        if email_format == "html" and "EMAIL" in methods:
            contents["html"] = cls._pre_render(resource,
                                               data,
                                               notify_on,
                                               last_check_time,
                                               "html")
            contents["default"] = contents["html"]
        if email_format != "html" or "EMAIL" not in methods or len(methods) > 1:
            contents["text"] = cls._pre_render(resource,
                                               data,
                                               notify_on,
                                               last_check_time,
                                               "text")
            contents["default"] = contents["text"]
        
        # Add human-readable representation of the filter query
        filter_query = subscription.get("filter_query")
        for f, c in contents.iteritems():
            c["filter_query"] = filter_query

        # Subject line
        get_config = resource.get_config
        subject = get_config("notification_subject",
                             settings.get_msg_notification_subject())
        from string import Template
        subject = Template(subject).safe_substitute(s="%(system)s",
                                                    r="%(resource)s")
        subject = subject % contents["default"]

        # Helper function to find templates from a priority list
        def get_template(path, filenames):

            for fn in filenames:
                filepath = join(path, fn)
                if os.path.exists(filepath):
                    try:
                        return open(filepath, "rb")
                    except:
                        pass
            return None
            
        prefix = resource.get_config("notification_prefix", "notify")
        for method in methods:

            error = None
            
            # Get the message template
            template = None
            filenames = ["%s_%s.html" % (prefix, method.lower())]
            if method == "EMAIL" and email_format:
                filenames.insert(0, "%s_email_%s.html" % (prefix, email_format))
            if theme != "default":
                path = join("private", "templates", theme, "views", "msg")
                template = get_template(path, filenames)
            if template is None:
                path = join("views", "msg")
                template = get_template(path, filenames)
            if template is None:
                template = StringIO(T("New updates are available."))

            # Select contents format
            if method == "EMAIL" and email_format == "html":
                output = contents["html"]
            else:
                output = contents["text"]
                
            # Render the message
            try:
                message = current.response.render(template, output)
            except:
                exc_info = sys.exc_info()[:2]
                error = ("%s: %s" % (exc_info[0].__name__, exc_info[1]))
                errors.append(error)
                continue

            # Send the message
            #_debug("Sending message per %s" % method)
            #_debug(message)
            try:
                sent = send(pe_id,
                            subject=s3_truncate(subject, 64),
                            message=message,
                            pr_message_method=method,
                            system_generated=True)
            except:
                exc_info = sys.exc_info()[:2]
                error = ("%s: %s" % (exc_info[0].__name__, exc_info[1]))
                sent = False
                
            if sent:
                # Successful if at least one notification went out
                success = True
            else:
                if not error:
                    error = current.session.error
                    if isinstance(error, list):
                        error = "/".join(error)
                if error:
                    errors.append(error)

        # Done
        if errors:
            message = ", ".join(errors)
        else:
            message = "Success"
        return json_message(success=success,
                            statuscode=200 if success else 403,
                            message=message)

    # -------------------------------------------------------------------------
    @classmethod
    def _subscriptions(cls, now):
        """
            Helper method to find all subscriptions which need to be
            notified now.

            @param now: current datetime (UTC)
            @return: joined Rows pr_subscription/pr_subscription_resource,
                     or None if no due subscriptions could be found

            @todo: take notify_on into account when checking
        """

        db = current.db
        s3db = current.s3db

        stable = s3db.pr_subscription
        rtable = db.pr_subscription_resource
        ftable = s3db.pr_filter

        # Find all resources with due suscriptions
        query = ((rtable.next_check_time == None) |
                 (rtable.next_check_time <= now)) & \
                (rtable.locked != True) & \
                (rtable.deleted != True)

        tname = rtable.resource
        mtime = rtable.last_check_time.min()
        rows = db(query).select(tname,
                                mtime,
                                groupby=tname)

        # Select those which have updates
        resources = set()
        radd = resources.add
        for row in rows:
            tablename = row[tname]
            table = s3db.table(tablename)
            if not table or not "modified_on" in table.fields:
                # Can't notify updates in resources without modified_on
                continue
            else:
                modified_on = table.modified_on
            msince = row[mtime]
            if msince is None:
                query = (table.id > 0)
            else:
                query = (modified_on >= msince)
            update = db(query).select(modified_on,
                                      orderby=~(modified_on),
                                      limitby=(0, 1)).first()
            if update:
                radd((tablename, update.modified_on))

        # Get all active subscriptions to these resources which
        # may need to be notified now:
        if resources:
            join = rtable.on((rtable.subscription_id == stable.id) & \
                             (rtable.locked != True) & \
                             (rtable.deleted != True))
            query = None
            for rname, modified_on in resources:
                q = (rtable.resource == rname) & \
                    ((rtable.last_check_time == None) |
                     (rtable.last_check_time <= modified_on))
                if query is None:
                    query = q
                else:
                    query |= q
            query = (stable.frequency != "never") & \
                    (stable.deleted != True) & \
                    ((rtable.next_check_time == None) | \
                     (rtable.next_check_time <= now)) & \
                    query
            return db(query).select(rtable.id, join=join)
        else:
            return None

    # -------------------------------------------------------------------------
    @classmethod
    def _pre_render(cls,
                    resource,
                    data,
                    notify_on,
                    last_check_time,
                    format=None):
        """
            Method to pre-render the contents for the message template

            @param resource: the S3Resource
            @param data: the data returned from S3Resource.select
            @param notify_on: the notification trigger(s)
            @param last_check_time: the last check time (datetime)
            @param format: the contents format ("text" or "html")

            @todo: make this configurable per resource and/or controller
        """

        prefix = resource.prefix_selector

        created_on_selector = prefix("created_on")
        created_on_colname = None

        rfields = data["rfields"]

        as_utc = current.xml.as_utc

        rows = data["rows"]
        new, upd = [], []

        # Common contents
        crud_strings = current.response.s3.crud_strings[resource.tablename]
        if crud_strings:
            resource_name = crud_strings.title_list
        else:
            resource_name = string.capwords(resource.name, "_")

        output = {"system": current.deployment_settings.get_system_name_short(),
                  "resource": resource_name
                  }

        if format == "html":
            # Pre-formatted HTML
            colnames = []
            
            new_headers = TR()
            mod_headers = TR()
            for rfield in rfields:
                if rfield.selector == created_on_selector:
                    created_on_colname = rfield.colname
                elif rfield.ftype != "id":
                    colnames.append(rfield.colname)
                    label = rfield.label
                    new_headers.append(TH(label))
                    mod_headers.append(TH(label))
            for row in rows:
                append_record = upd.append
                if created_on_colname:
                    try:
                        created_on = row["_row"][created_on_colname]
                    except KeyError, AttributeError:
                        pass
                    else:
                        if as_utc(created_on) >= last_check_time:
                            append_record = new.append
                tr = TR([TD(XML(row[colname])) for colname in colnames])
                append_record(tr)
            if "new" in notify_on and len(new):
                output["new"] = len(new)
                output["new_records"] = TABLE(THEAD(new_headers), TBODY(new))
            else:
                output["new"] = None
            if "upd" in notify_on and len(upd):
                output["upd"] = len(upd)
                output["upd_records"] = TABLE(THEAD(new_headers), TBODY(upd))
            else:
                output["upd"] = None

        else:
            # Standard text format
            labels = []
            append = labels.append

            for rfield in rfields:
                if rfield.selector == created_on_selector:
                    created_on_colname = rfield.colname
                elif rfield.ftype != "id":
                    append((rfield.colname, rfield.label))

            for row in rows:
                append_record = upd.append
                if created_on_colname:
                    try:
                        created_on = row["_row"][created_on_colname]
                    except KeyError, AttributeError:
                        pass
                    else:
                        if as_utc(created_on) >= last_check_time:
                            append_record = new.append

                record = []
                append_column = record.append
                for colname, label in labels:
                    append_column((label, row[colname]))
                append_record(record)

            crud_strings = current.response.s3.crud_strings[resource.tablename]
            if crud_strings:
                resource_name = crud_strings.title_list
            else:
                resource_name = string.capwords(resource.name, "_")

            output = {"system": current.deployment_settings \
                                       .get_system_name_short(),
                      "resource": resource_name,
                      }
            if "new" in notify_on and len(new):
                output["new"] = len(new)
                output["new_records"] = new
            else:
                output["new"] = None
            if "upd" in notify_on and len(upd):
                output["upd"] = len(upd)
                output["upd_records"] = upd
            else:
                output["upd"] = None

        return output

# END =========================================================================
