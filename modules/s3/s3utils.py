# -*- coding: utf-8 -*-

""" Utilities

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @copyright: (c) 2010-2014 Sahana Software Foundation
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

import collections
import copy
import datetime
import os
import re
import sys
import time
import urlparse
import HTMLParser
from threading import Timer

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

try:
    # Python 2.7
    from collections import OrderedDict
except:
    # Python 2.6
    from gluon.contrib.simplejson.ordered_dict import OrderedDict

from gluon import *
try:
    from gluon import Field
    from gluon.dal.objects import Expression, Row
except ImportError:
    # old web2py
    from gluon.dal import Expression, Field, Row
from gluon.storage import Storage
from gluon.languages import lazyT
from gluon.tools import addrow

DEBUG = False
if DEBUG:
    print >> sys.stderr, "S3Utils: DEBUG MODE"
    def _debug(m):
        print >> sys.stderr, m
else:
    _debug = lambda m: None

URLSCHEMA = re.compile("((?:(())(www\.([^/?#\s]*))|((http(s)?|ftp):)"
                       "(//([^/?#\s]*)))([^?#\s]*)(\?([^#\s]*))?(#([^\s]*))?)")

RCVARS = "rcvars"

# =============================================================================
def s3_debug(message, value=None):
    """
       Debug Function (same name/parameters as JavaScript one)

       Provide an easy, safe, systematic way of handling Debug output
       (print to stdout doesn't work with WSGI deployments)

       @ToDo: Should be using python's built-in logging module?
    """

    output = "S3 Debug: %s" % s3_unicode(message)
    if value:
        output = "%s: %s" % (output, s3_unicode(value))

    try:
        print >> sys.stderr, output
    except:
        # Unicode string
        print >> sys.stderr, "Debug crashed"

# =============================================================================
def s3_get_last_record_id(tablename):
    """
        Reads the last record ID for a resource from a session

        @param table: the the tablename
    """

    session = current.session

    if RCVARS in session and tablename in session[RCVARS]:
        return session[RCVARS][tablename]
    else:
        return None

# =============================================================================
def s3_store_last_record_id(tablename, record_id):
    """
        Stores a record ID for a resource in a session

        @param tablename: the tablename
        @param record_id: the record ID to store
    """

    session = current.session

    # Web2py type "Reference" can't be pickled in session (no crash,
    # but renders the server unresponsive) => always convert into long
    try:
        record_id = long(record_id)
    except ValueError:
        return False

    if RCVARS not in session:
        session[RCVARS] = Storage({tablename: record_id})
    else:
        session[RCVARS][tablename] = record_id
    return True

# =============================================================================
def s3_remove_last_record_id(tablename=None):
    """
        Clears one or all last record IDs stored in a session

        @param tablename: the tablename, None to remove all last record IDs
    """

    session = current.session

    if tablename:
        if RCVARS in session and tablename in session[RCVARS]:
            del session[RCVARS][tablename]
    else:
        if RCVARS in session:
            del session[RCVARS]
    return True

# =============================================================================
def s3_validate(table, field, value, record=None):
    """
        Validates a value for a field

        @param table: Table
        @param field: Field or name of the field
        @param value: value to validate
        @param record: the existing database record, if available

        @return: tuple (value, error)
    """

    default = (value, None)

    if isinstance(field, basestring):
        fieldname = field
        if fieldname in table.fields:
            field = table[fieldname]
        else:
            return default
    else:
        fieldname = field.name

    self_id = None

    if record is not None:

        try:
            v = record[field]
        except: # KeyError is now AttributeError
            v = None
        if v and v == value:
            return default

        try:
            self_id = record[table._id]
        except: # KeyError is now AttributeError
            pass

    requires = field.requires

    if field.unique and not requires:
        # Prevent unique-constraint violations
        field.requires = IS_NOT_IN_DB(current.db, str(field))
        if self_id:
            field.requires.set_self_id(self_id)

    elif self_id:

        # Initialize all validators for self_id
        if not isinstance(requires, (list, tuple)):
            requires = [requires]
        for r in requires:
            if hasattr(r, "set_self_id"):
                r.set_self_id(self_id)
            if hasattr(r, "other") and \
               hasattr(r.other, "set_self_id"):
                r.other.set_self_id(self_id)

    try:
        value, error = field.validate(value)
    except:
        # Oops - something went wrong in the validator:
        # write out a debug message, and continue anyway
        current.log.error("Validate %s: %s (ignored)" %
                          (field, sys.exc_info()[1]))
        return (None, None)
    else:
        return (value, error)

# =============================================================================
def s3_represent_value(field,
                       value=None,
                       record=None,
                       linkto=None,
                       strip_markup=False,
                       xml_escape=False,
                       non_xml_output=False,
                       extended_comments=False):
    """
        Represent a field value

        @param field: the field (Field)
        @param value: the value
        @param record: record to retrieve the value from
        @param linkto: function or format string to link an ID column
        @param strip_markup: strip away markup from representation
        @param xml_escape: XML-escape the output
        @param non_xml_output: Needed for output such as pdf or xls
        @param extended_comments: Typically the comments are abbreviated
    """

    xml_encode = current.xml.xml_encode

    NONE = current.response.s3.crud_labels["NONE"]
    cache = current.cache
    fname = field.name

    # Get the value
    if record is not None:
        tablename = str(field.table)
        if tablename in record and isinstance(record[tablename], Row):
            text = val = record[tablename][field.name]
        else:
            text = val = record[field.name]
    else:
        text = val = value

    ftype = str(field.type)
    if ftype[:5] == "list:" and not isinstance(val, list):
        # Default list representation can't handle single values
        val = [val]

    # Always XML-escape content markup if it is intended for xml output
    # This code is needed (for example) for a data table that includes a link
    # Such a table can be seen at inv/inv_item
    # where the table displays a link to the warehouse
    if not non_xml_output:
        if not xml_escape and val is not None:
            if ftype in ("string", "text"):
                val = text = xml_encode(s3_unicode(val))
            elif ftype == "list:string":
                val = text = [xml_encode(s3_unicode(v)) for v in val]

    # Get text representation
    if field.represent:
        try:
            key = "%s_repr_%s" % (field, val)
            unicode(key)
        except (UnicodeEncodeError, UnicodeDecodeError):
            text = field.represent(val)
        else:
            text = cache.ram(key,
                             lambda: field.represent(val),
                             time_expire=60)
            if isinstance(text, DIV):
                text = str(text)
            elif not isinstance(text, basestring):
                text = s3_unicode(text)
    else:
        if val is None:
            text = NONE
        elif fname == "comments" and not extended_comments:
            ur = s3_unicode(text)
            if len(ur) > 48:
                text = "%s..." % ur[:45].encode("utf8")
        else:
            text = s3_unicode(text)

    # Strip away markup from text
    if strip_markup and "<" in text:
        try:
            stripper = S3MarkupStripper()
            stripper.feed(text)
            text = stripper.stripped()
        except:
            pass

    # Link ID field
    if fname == "id" and linkto:
        id = str(val)
        try:
            href = linkto(id)
        except TypeError:
            href = linkto % id
        href = str(href).replace(".aadata", "")
        return A(text, _href=href).xml()

    # XML-escape text
    elif xml_escape:
        text = xml_encode(text)

    try:
        text = text.decode("utf-8")
    except:
        pass

    return text

# =============================================================================
def s3_set_default_filter(selector, value, tablename=None):
    """
        Set a default filter for selector.

        @param selector: the field selector
        @param value: the value, can be a dict {operator: value},
                      a list of values, or a single value, or a
                      callable that returns any of these
        @param tablename: the tablename
    """

    s3 = current.response.s3

    filter_defaults = s3
    for level in ("filter_defaults", tablename):
        if level not in filter_defaults:
            filter_defaults[level] = {}
        filter_defaults = filter_defaults[level]
    filter_defaults[selector] = value
    return

# =============================================================================
def s3_dev_toolbar():
    """
        Developer Toolbar - ported from gluon.Response.toolbar()
        Shows useful stuff at the bottom of the page in Debug mode
    """

    from gluon.dal import DAL
    from gluon.utils import web2py_uuid

    #admin = URL("admin", "default", "design", extension="html",
    #            args=current.request.application)
    BUTTON = TAG.button

    dbstats = []
    dbtables = {}
    infos = DAL.get_instances()
    for k, v in infos.iteritems():
        dbstats.append(TABLE(*[TR(PRE(row[0]), "%.2fms" %
                                      (row[1] * 1000))
                                       for row in v["dbstats"]]))
        dbtables[k] = dict(defined=v["dbtables"]["defined"] or "[no defined tables]",
                           lazy=v["dbtables"]["lazy"] or "[no lazy tables]")

    u = web2py_uuid()
    backtotop = A("Back to top", _href="#totop-%s" % u)
    # Convert lazy request.vars from property to Storage so they
    # will be displayed in the toolbar.
    request = copy.copy(current.request)
    request.update(vars=current.request.vars,
                   get_vars=current.request.get_vars,
                   post_vars=current.request.post_vars)
    return DIV(
        #BUTTON("design", _onclick="document.location='%s'" % admin),
        BUTTON("request",
               _onclick="$('#request-%s').slideToggle().removeClass('hide')" % u),
        #BUTTON("response",
        #       _onclick="$('#response-%s').slideToggle().removeClass('hide')" % u),
        BUTTON("session",
               _onclick="$('#session-%s').slideToggle().removeClass('hide')" % u),
        BUTTON("db tables",
               _onclick="$('#db-tables-%s').slideToggle().removeClass('hide')" % u),
        BUTTON("db stats",
               _onclick="$('#db-stats-%s').slideToggle().removeClass('hide')" % u),
        DIV(BEAUTIFY(request), backtotop,
            _class="hide", _id="request-%s" % u),
        #DIV(BEAUTIFY(current.response), backtotop,
        #    _class="hide", _id="response-%s" % u),
        DIV(BEAUTIFY(current.session), backtotop,
            _class="hide", _id="session-%s" % u),
        DIV(BEAUTIFY(dbtables), backtotop,
            _class="hide", _id="db-tables-%s" % u),
        DIV(BEAUTIFY(dbstats), backtotop,
            _class="hide", _id="db-stats-%s" % u),
        _id="totop-%s" % u
    )

# =============================================================================
def s3_required_label(field_label):
    """ Default HTML for labels of required form fields """

    return TAG[""]("%s:" % field_label, SPAN(" *", _class="req"))

# =============================================================================
def s3_mark_required(fields,
                     mark_required=None,
                     label_html=None,
                     map_names=None):
    """
        Add asterisk to field label if a field is required

        @param fields: list of fields (or a table)
        @param mark_required: list of field names which are always required
        @param label_html: function to render labels of requried fields
        @param map_names: dict of alternative field names and labels
                          {fname: (name, label)}, used for inline components
        @return: tuple, (dict of form labels, has_required) with has_required
                 indicating whether there are required fields in this form
    """

    if not mark_required:
        mark_required = ()

    if label_html is None:
        # @ToDo: DRY this setting with s3.locationselector.widget2.js
        label_html = s3_required_label

    labels = dict()

    # Do we have any required fields?
    _required = False
    for field in fields:
        if map_names:
            fname, flabel = map_names[field.name]
        else:
            fname, flabel = field.name, field.label
        if not flabel:
            labels[fname] = ""
            continue
        if field.writable:
            validators = field.requires
            if isinstance(validators, IS_EMPTY_OR) and field.name not in mark_required:
                # Allow notnull fields to be marked as not required
                # if we populate them onvalidation
                labels[fname] = "%s:" % flabel
                continue
            else:
                required = field.required or field.notnull or \
                            field.name in mark_required
            if not validators and not required:
                labels[fname] = "%s:" % flabel
                continue
            if not required:
                if not isinstance(validators, (list, tuple)):
                    validators = [validators]
                for v in validators:
                    if hasattr(v, "options"):
                        if hasattr(v, "zero") and v.zero is None:
                            continue
                    if hasattr(v, "mark_required"):
                        if v.mark_required:
                            required = True
                            break
                        else:
                            continue
                    try:
                        val, error = v("")
                    except TypeError:
                        # default validator takes no args
                        pass
                    else:
                        if error:
                            required = True
                            break
            if required:
                _required = True
                labels[fname] = label_html(flabel)
            else:
                labels[fname] = "%s:" % flabel
        else:
            labels[fname] = "%s:" % flabel

    # Callers expect an iterable
    #if labels:
    return (labels, _required)
    #else:
    #    return None

# =============================================================================
def s3_addrow(form, label, widget, comment, formstyle, row_id, position=-1):
    """
        Add a row to a form, applying formstyle

        @param form: the FORM
        @param label: the label
        @param widget: the widget
        @param comment: the comment
        @param formstyle: the formstyle
        @param row_id: the form row HTML id
        @param position: position where to insert the row
    """

    if callable(formstyle):
        row = formstyle(row_id, label, widget, comment)
        if isinstance(row, (tuple, list)):
            for subrow in row:
                form[0].insert(position, subrow)
                if position >= 0:
                    position += 1
        else:
            form[0].insert(position, row)
    else:
        addrow(form, label, widget, comment, formstyle, row_id,
               position = position)
    return

# =============================================================================
def s3_truncate(text, length=48, nice=True):
    """
        Nice truncating of text

        @param text: the text
        @param length: the maximum length
        @param nice: do not truncate words
    """

    text = s3_unicode(text)
    if len(text) > length:
        if nice:
            return "%s..." % text[:length].rsplit(" ", 1)[0][:45]
        else:
            return "%s..." % text[:45]
    else:
        return text

# =============================================================================
def s3_datatable_truncate(string, maxlength=40):
    """
        Representation method to override the dataTables-internal truncation
        of strings per field, like:

        if not r.id and not r.method:
            table.field.represent = lambda string: \
                                    s3_datatable_truncate(string, maxlength=40)

        @param string: the string
        @param maxlength: the maximum string length

        @note: the JS click-event will be attached by S3.datatables.js
    """

    string = s3_unicode(string)
    if string and len(string) > maxlength:
        _class = "dt-truncate"
        return TAG[""](
                DIV(SPAN(_class="ui-icon ui-icon-zoomin",
                         _style="float:right",
                         ),
                    string[:maxlength-3] + "...",
                    _class=_class),
                DIV(SPAN(_class="ui-icon ui-icon-zoomout",
                            _style="float:right"),
                    string,
                    _style="display:none",
                    _class=_class),
                )
    else:
        return string if string else ""

# =============================================================================
def s3_trunk8(selector=None, lines=None, less=None, more=None):
    """
        Intelligent client-side text truncation

        @param selector: the jQuery selector (default: .s3-truncate)
        @param lines: maximum number of lines (default: 1)
    """

    T = current.T

    s3 = current.response.s3
    scripts = s3.scripts
    script = "/%s/static/scripts/trunk8.js" % current.request.application
    if script not in scripts:
        scripts.append(script)

        # Toggle-script
        # - only required once per page
        script = \
"""$(document).on('click','.s3-truncate-more',function(event){
 $(this).parent()
        .trunk8('revert')
        .append(' <a class="s3-truncate-less" href="#">%(less)s</a>')
 return false
})
$(document).on('click','.s3-truncate-less',function(event){
 $(this).parent().trunk8()
 return false
})""" % dict(less=T("less") if less is None else less)
        s3.jquery_ready.append(script)

    # Init-script
    # - required separately for each selector
    script = """S3.trunk8('%(selector)s', %(lines)s, '%(more)s')""" % \
             dict(selector = ".s3-truncate" if selector is None else selector,
                  lines = "null" if lines is None else lines,
                  more=T("more") if more is None else more,
                 )

    s3.jquery_ready.append(script)
    return

# =============================================================================
def s3_format_fullname(fname=None, mname=None, lname=None, truncate=True):
    """
        Formats the full name of a person

        @param fname: the person's pr_person.first_name value
        @param mname: the person's pr_person.middle_name value
        @param lname: the person's pr_person.last_name value
        @param truncate: truncate the name to max 24 characters
    """

    name = ""
    if fname or mname or lname:
        if not fname:
            fname = ""
        if not mname:
            mname = ""
        if not lname:
            lname = ""
        if truncate:
            fname = "%s" % s3_truncate(fname, 24)
            mname = "%s" % s3_truncate(mname, 24)
            lname = "%s" % s3_truncate(lname, 24, nice = False)
        name_format = current.deployment_settings.get_pr_name_format()
        name = name_format % dict(first_name=fname,
                                  middle_name=mname,
                                  last_name=lname,
                                  )
        name = name.replace("  ", " ").rstrip()
        if truncate:
            name = s3_truncate(name, 24, nice = False)
    return name

# =============================================================================
def s3_fullname(person=None, pe_id=None, truncate=True):
    """
        Returns the full name of a person

        @param person: the pr_person record or record_id
        @param pe_id: alternatively, the person entity ID
        @param truncate: truncate the name to max 24 characters
    """

    db = current.db
    ptable = db.pr_person

    record = None
    query = None
    if isinstance(person, (int, long)) or str(person).isdigit():
        query = (ptable.id == person)# & (ptable.deleted != True)
    elif person is not None:
        record = person
    elif pe_id is not None:
        query = (ptable.pe_id == pe_id)# & (ptable.deleted != True)

    if not record and query is not None:
        record = db(query).select(ptable.first_name,
                                  ptable.middle_name,
                                  ptable.last_name,
                                  limitby=(0, 1)).first()
    if record:
        fname, mname, lname = "", "", ""
        if "pr_person" in record:
            record = record["pr_person"]
        if record.first_name:
            fname = record.first_name.strip()
        if "middle_name" in record and record.middle_name:
            mname = record.middle_name.strip()
        if record.last_name:
            lname = record.last_name.strip()
        return s3_format_fullname(fname, mname, lname, truncate)

    else:
        return ""

# =============================================================================
def s3_fullname_bulk(record_ids=[], truncate=True):
    """
        Returns the full name for a set of Persons
        - currently unused

        @param record_ids: a list of record_ids
        @param truncate: truncate the name to max 24 characters
    """

    db = current.db
    ptable = db.pr_person
    query = (ptable.id.belongs(record_ids))
    rows = db(query).select(ptable.id,
                            ptable.first_name,
                            ptable.middle_name,
                            ptable.last_name)

    represents = {}
    for row in rows:
        fname, mname, lname = "", "", ""
        if row.first_name:
            fname = row.first_name.strip()
        if row.middle_name:
            mname = row.middle_name.strip()
        if row.last_name:
            lname = row.last_name.strip()
        represent = s3_format_fullname(fname, mname, lname, truncate)
        represents[row.id] = represent
    return represents

# =============================================================================
def s3_comments_represent(text, show_link=True):
    """
        Represent Comments Fields
    """

    # Make sure text is multi-byte-aware before truncating it
    text = s3_unicode(text)
    if len(text) < 80:
        return text
    elif not show_link:
        return "%s..." % text[:76]
    else:
        import uuid
        unique =  uuid.uuid4()
        represent = DIV(
                DIV(text,
                    _id=unique,
                    _class="hide showall",
                    _onmouseout="$('#%s').hide()" % unique
                   ),
                A("%s..." % text[:76],
                  _onmouseover="$('#%s').removeClass('hide').show()" % unique,
                 ),
                )
        return represent

# =============================================================================
def s3_url_represent(url):
    """
        Make URLs clickable
    """

    if not url:
        return ""
    return A(url, _href=url, _target="_blank")

# =============================================================================
def s3_URLise(text):
    """
        Convert all URLs in a text into an HTML <A> tag.

        @param text: the text
    """

    output = URLSCHEMA.sub(lambda m: '<a href="%s" target="_blank">%s</a>' %
                          (m.group(0), m.group(0)), text)
    return output

# =============================================================================
def s3_avatar_represent(id, tablename="auth_user", gravatar=False, **attr):
    """
        Represent a User as their profile picture or Gravatar

        @param tablename: either "auth_user" or "pr_person" depending on which
                          table the 'id' refers to
        @param attr: additional HTML attributes for the IMG(), such as _class
    """

    db = current.db
    s3db = current.s3db
    cache = s3db.cache

    table = s3db[tablename]

    email = None
    image = None

    if tablename == "auth_user":
        user = db(table.id == id).select(table.email,
                                         limitby=(0, 1),
                                         cache=cache).first()
        if user:
            email = user.email.strip().lower()
        ltable = s3db.pr_person_user
        itable = s3db.pr_image
        query = (ltable.user_id == id) & \
                (ltable.pe_id == itable.pe_id) & \
                (itable.profile == True)
        image = db(query).select(itable.image,
                                 limitby=(0, 1)).first()
        if image:
            image = image.image
    elif tablename == "pr_person":
        user = db(table.id == id).select(table.pe_id,
                                         limitby=(0, 1),
                                         cache=cache).first()
        if user:
            ctable = s3db.pr_contact
            query = (ctable.pe_id == user.pe_id) & \
                    (ctable.contact_method == "EMAIL")
            email = db(query).select(ctable.value,
                                     limitby=(0, 1),
                                     cache=cache).first()
            if email:
                email = email.value
            itable = s3db.pr_image
            query = (itable.pe_id == user.pe_id) & \
                    (itable.profile == True)
            image = db(query).select(itable.image,
                                     limitby=(0, 1)).first()
            if image:
                image = image.image

    size = (50, 50)
    if image:
        image = s3db.pr_image_represent(image, size=size)
        size = s3db.pr_image_size(image, size)
        url = URL(c="default", f="download",
                  args=image)
    elif gravatar:
        if email:
            # If no Image uploaded, try Gravatar, which also provides a nice fallback identicon
            import hashlib
            hash = hashlib.md5(email).hexdigest()
            url = "http://www.gravatar.com/avatar/%s?s=50&d=identicon" % hash
        else:
            url = "http://www.gravatar.com/avatar/00000000000000000000000000000000?d=mm"
    else:
        url = URL(c="static", f="img", args="blank-user.gif")

    if "_class" not in attr:
        attr["_class"] = "avatar"
    if "_width" not in attr:
        attr["_width"] = size[0]
    if "_height" not in attr:
        attr["_height"] = size[1]
    return IMG(_src=url, **attr)

# =============================================================================
def s3_auth_user_represent(id, row=None):
    """
        Represent a user as their email address
    """

    if row:
        return row.email
    elif not id:
        return current.messages["NONE"]

    db = current.db
    table = db.auth_user
    user = db(table.id == id).select(table.email,
                                     limitby=(0, 1),
                                     cache=current.s3db.cache).first()
    try:
        return user.email
    except:
        return current.messages.UNKNOWN_OPT

# =============================================================================
def s3_auth_user_represent_name(id, row=None):
    """
        Represent users by their names
    """

    if not row:
        if not id:
            return current.messages["NONE"]
        db = current.db
        table = db.auth_user
        row = db(table.id == id).select(table.first_name,
                                        table.last_name,
                                        limitby=(0, 1)).first()
    try:
        return s3_format_fullname(row.first_name.strip(),
                                  None,
                                  row.last_name.strip())
    except:
        return current.messages.UNKNOWN_OPT

# =============================================================================
def s3_yes_no_represent(value):
    " Represent a Boolean field as Yes/No instead of True/False "

    if value:
        return current.T("Yes")
    else:
        return current.T("No")

# =============================================================================
def s3_include_debug_css():
    """
        Generates html to include the css listed in
            /private/templates/<template>/css.cfg
    """

    request = current.request
    folder = request.folder
    appname = request.application
    theme = current.deployment_settings.get_theme()

    css_cfg = "%s/private/templates/%s/css.cfg" % (folder, theme)
    try:
        f = open(css_cfg, "r")
    except:
        raise HTTP(500, "Theme configuration file missing: private/templates/%s/css.cfg" % theme)
    files = f.readlines()
    files = files[:-1]
    include = ""
    for file in files:
        if file[0] != "#":
            include = '%s\n<link href="/%s/static/styles/%s" rel="stylesheet" type="text/css" />' \
                % (include, appname, file[:-1])
    f.close()

    return XML(include)

# =============================================================================
def s3_include_debug_js():
    """
        Generates html to include the js scripts listed in
            /static/scripts/tools/sahana.js.cfg
    """

    request = current.request
    folder = request.folder
    appname = request.application
    theme = current.deployment_settings.get_theme()

    scripts_dir = os.path.join(folder, "static", "scripts")
    sys.path.append(os.path.join(scripts_dir, "tools"))

    import mergejsmf

    configDictCore = {
        ".": scripts_dir,
        "ui": scripts_dir,
        "web2py": scripts_dir,
        "S3":     scripts_dir
    }
    configFilename = "%s/tools/sahana.js.cfg"  % scripts_dir
    (fs, files) = mergejsmf.getFiles(configDictCore, configFilename)

    include = ""
    for file in files:
        include = '%s\n<script src="/%s/static/scripts/%s" type="text/javascript"></script>' \
            % (include, appname, file)

    return XML(include)

# =============================================================================
def s3_include_ext():
    """
        Add ExtJS CSS & JS into a page for a Map
        - since this is normally run from MAP.xml() it is too late to insert into
          s3.[external_]stylesheets, so must inject sheets into correct order
    """

    s3 = current.response.s3
    if s3.ext_included:
        # Ext already included
        return
    request = current.request
    appname = request.application

    xtheme = current.deployment_settings.get_base_xtheme()
    if xtheme:
        xtheme = "%smin.css" % xtheme[:-3]
        xtheme = \
    "<link href='/%s/static/themes/%s' rel='stylesheet' type='text/css' media='screen' charset='utf-8' />" % \
        (appname, xtheme)

    if s3.cdn:
        # For Sites Hosted on the Public Internet, using a CDN may provide better performance
        PATH = "http://cdn.sencha.com/ext/gpl/3.4.1.1"
    else:
        PATH = "/%s/static/scripts/ext" % appname

    if s3.debug:
        # Provide debug versions of CSS / JS
        adapter = "%s/adapter/jquery/ext-jquery-adapter-debug.js" % PATH
        main_js = "%s/ext-all-debug.js" % PATH
        main_css = \
    "<link href='%s/resources/css/ext-all-notheme.css' rel='stylesheet' type='text/css' media='screen' charset='utf-8' />" % PATH
        if not xtheme:
            xtheme = \
    "<link href='%s/resources/css/xtheme-gray.css' rel='stylesheet' type='text/css' media='screen' charset='utf-8' />" % PATH
    else:
        adapter = "%s/adapter/jquery/ext-jquery-adapter.js" % PATH
        main_js = "%s/ext-all.js" % PATH
        if xtheme:
            main_css = \
    "<link href='/%s/static/scripts/ext/resources/css/ext-notheme.min.css' rel='stylesheet' type='text/css' media='screen' charset='utf-8' />" % appname
        else:
            main_css = \
    "<link href='/%s/static/scripts/ext/resources/css/ext-gray.min.css' rel='stylesheet' type='text/css' media='screen' charset='utf-8' />" % appname

    scripts = s3.scripts
    scripts_append = scripts.append
    scripts_append(adapter)
    scripts_append(main_js)

    langfile = "ext-lang-%s.js" % s3.language
    if os.path.exists(os.path.join(request.folder, "static", "scripts", "ext", "src", "locale", langfile)):
        locale = "%s/src/locale/%s" % (PATH, langfile)
        scripts_append(locale)

    if xtheme:
        s3.jquery_ready.append('''$('link:first').after("%s").after("%s")''' % (xtheme, main_css))
    else:
        s3.jquery_ready.append('''$('link:first').after("%s")''' % main_css)
    s3.ext_included = True

# =============================================================================
def s3_is_mobile_client(request):
    """
        Simple UA Test whether client is a mobile device
    """

    env = request.env
    if env.http_x_wap_profile or env.http_profile:
        return True
    if env.http_accept and \
       env.http_accept.find("text/vnd.wap.wml") > 0:
        return True
    keys = ["iphone", "ipod", "android", "opera mini", "blackberry", "palm",
            "windows ce", "iemobile", "smartphone", "medi", "sk-0", "vk-v",
            "aptu", "xda-", "mtv ", "v750", "p800", "opwv", "send", "xda2",
            "sage", "t618", "qwap", "veri", "t610", "tcl-", "vx60", "vx61",
            "lg-k", "lg-l", "lg-m", "lg-o", "lg-a", "lg-b", "lg-c", "xdag",
            "lg-f", "lg-g", "sl45", "emul", "lg-p", "lg-s", "lg-t", "lg-u",
            "lg-w", "6590", "t250", "qc21", "ig01", "port", "m1-w", "770s",
            "n710", "ez60", "mt50", "g1 u", "vk40", "bird", "tagt", "pose",
            "jemu", "beck", "go.w", "jata", "gene", "smar", "g-mo", "o2-x",
            "htc_", "hei-", "fake", "qc-7", "smal", "htcp", "htcs", "craw",
            "htct", "aste", "htca", "htcg", "teli", "telm", "kgt", "mwbp",
            "kwc-", "owg1", "htc ", "kgt/", "htc-", "benq", "slid", "qc60",
            "dmob", "blac", "smt5", "nec-", "sec-", "sec1", "sec0", "fetc",
            "spv ", "mcca", "nem-", "spv-", "o2im", "m50/", "ts70", "arch",
            "qtek", "opti", "devi", "winw", "rove", "winc", "talk", "pant",
            "netf", "pana", "esl8", "pand", "vite", "v400", "whit", "scoo",
            "good", "nzph", "mtp1", "doco", "raks", "wonu", "cmd-", "cell",
            "mode", "im1k", "modo", "lg-d", "idea", "jigs", "bumb", "sany",
            "vulc", "vx70", "psio", "fly_", "mate", "pock", "cdm-", "fly-",
            "i230", "lge-", "lge/", "argo", "qc32", "n701", "n700", "mc21",
            "n500", "midp", "t-mo", "airn", "bw-u", "iac", "bw-n", "lg g",
            "erk0", "sony", "alav", "503i", "pt-g", "au-m", "treo", "ipaq",
            "dang", "seri", "mywa", "eml2", "smb3", "brvw", "sgh-", "maxo",
            "pg-c", "qci-", "vx85", "vx83", "vx80", "vx81", "pg-8", "pg-6",
            "phil", "pg-1", "pg-2", "pg-3", "ds12", "scp-", "dc-s", "brew",
            "hipt", "kddi", "qc07", "elai", "802s", "506i", "dica", "mo01",
            "mo02", "avan", "kyoc", "ikom", "siem", "kyok", "dopo", "g560",
            "i-ma", "6310", "sie-", "grad", "ibro", "sy01", "nok6", "el49",
            "rim9", "upsi", "inno", "wap-", "sc01", "ds-d", "aur ", "comp",
            "wapp", "wapr", "waps", "wapt", "wapu", "wapv", "wapy", "newg",
            "wapa", "wapi", "wapj", "wapm", "hutc", "lg/u", "yas-", "hita",
            "lg/l", "lg/k", "i-go", "4thp", "bell", "502i", "zeto", "ez40",
            "java", "n300", "n302", "mmef", "pn-2", "newt", "1207", "sdk/",
            "gf-5", "bilb", "zte-", "maui", "qc-3", "qc-2", "blaz", "r600",
            "hp i", "qc-5", "moto", "cond", "motv", "virg", "ccwa", "audi",
            "shar", "i-20", "samm", "sama", "sams", "sch-", "mot ", "http",
            "505i", "mot-", "n502", "topl", "n505", "mobi", "3gso", "wmlb",
            "ezwa", "qc12", "abac", "tdg-", "neon", "mio8", "sp01", "rozo",
            "vx98", "dait", "t600", "anyw", "tx-9", "sava", "m-cr", "tsm-",
            "mioa", "tsm5", "klon", "capi", "tsm3", "hcit", "libw", "lg50",
            "mc01", "amoi", "lg54", "ez70", "se47", "n203", "vk52", "vk53",
            "vk50", "webc", "haie", "semc", "grun", "play", "palm", "a wa",
            "anny", "prox", "o2 x", "ezze", "symb", "hs-c", "pg13", "mits",
            "kpt ", "qa-a", "501i", "pdxg", "iris", "pluc", "acoo", "soft",
            "hpip", "iac/", "iac-", "aus ", "s55/", "vx53", "vx52", "chtm",
            "meri", "merc", "your", "huaw", "cldc", "voda", "smit", "x700",
            "mozz", "lexi", "up.b", "sph-", "keji", "jbro", "wig ", "attw",
            "pire", "r380", "lynx", "anex", "vm40", "hd-m", "504i", "w3c ",
            "c55/", "w3c-", "upg1", "t218", "tosh", "acer", "hd-t", "eric",
            "hd-p", "noki", "acs-", "dbte", "n202", "tim-", "alco", "ezos",
            "dall", "leno", "alca", "asus", "m3ga", "utst", "aiko", "n102",
            "n101", "n100", "oran"]
    ua = (env.http_user_agent or "").lower()
    if [key for key in keys if key in ua]:
        return True
    return False

# =============================================================================
def s3_populate_browser_compatibility(request):
    """
        Use WURFL for browser compatibility detection

        @ToDo: define a list of features to store
    """

    features = Storage(
        #category = ["list","of","features","to","store"]
    )

    try:
        from pywurfl.algorithms import TwoStepAnalysis
    except ImportError:
        current.log.warning("pywurfl python module has not been installed, browser compatibility listing will not be populated. Download pywurfl from http://pypi.python.org/pypi/pywurfl/")
        return False
    import wurfl
    device = wurfl.devices.select_ua(unicode(request.env.http_user_agent),
                                     search=TwoStepAnalysis(wurfl.devices))

    browser = Storage()
    #for feature in device:
        #if feature[0] not in category_list:
            #category_list.append(feature[0])
    #for category in features:
        #if category in
        #browser[category] = Storage()
    for feature in device:
        if feature[0] in features and \
           feature[1] in features[feature[0]]:
            browser[feature[0]][feature[1]] = feature[2]

    return browser

# =============================================================================
def s3_filename(filename):
    """
        Convert a string into a valid filename on all OS
        http://stackoverflow.com/questions/295135/turn-a-string-into-a-valid-filename-in-python/698714#698714

        - currently unused
    """

    import string
    import unicodedata

    validFilenameChars = "-_.() %s%s" % (string.ascii_letters, string.digits)

    filename = unicode(filename)
    cleanedFilename = unicodedata.normalize("NFKD",
                                            filename).encode("ASCII", "ignore")

    return "".join(c for c in cleanedFilename if c in validFilenameChars)

# =============================================================================
def s3_has_foreign_key(field, m2m=True):
    """
        Check whether a field contains a foreign key constraint

        @param field: the field (Field instance)
        @param m2m: also detect many-to-many links

        @note: many-to-many references (list:reference) are no DB constraints,
               but pseudo-references implemented by the DAL. If you only want
               to find real foreign key constraints, then set m2m=False.
    """

    try:
        ftype = str(field.type)
    except:
        # Virtual Field
        return False
    if ftype[:9] == "reference":
        return True
    if m2m and ftype[:14] == "list:reference":
        return True
    return False

# =============================================================================
def s3_get_foreign_key(field, m2m=True):
    """
        Resolve a field type into the name of the referenced table,
        the referenced key and the reference type (M:1 or M:N)

        @param field: the field (Field instance)
        @param m2m: also detect many-to-many references

        @return: tuple (tablename, key, multiple), where tablename is
                  the name of the referenced table (or None if this field
                  has no foreign key constraint), key is the field name of
                  the referenced key, and multiple indicates whether this is
                  a many-to-many reference (list:reference) or not.

        @note: many-to-many references (list:reference) are no DB constraints,
               but pseudo-references implemented by the DAL. If you only want
               to find real foreign key constraints, then set m2m=False.
    """

    ftype = str(field.type)
    if ftype[:9] == "reference":
        key = ftype[10:]
        multiple = False
    elif m2m and ftype[:14] == "list:reference":
        key = ftype[15:]
        multiple = True
    else:
        return (None, None, None)
    if "." in key:
        rtablename, key = key.split(".")
    else:
        rtablename = key
        rtable = current.s3db.table(rtablename)
        if rtable:
            key = rtable._id.name
        else:
            key = None
    return (rtablename, key, multiple)

# =============================================================================
def s3_unicode(s, encoding="utf-8"):
    """
        Convert an object into an unicode instance, to be used instead of
        unicode(s) (Note: user data should never be converted into str).

        @param s: the object
        @param encoding: the character encoding
    """

    if type(s) is unicode:
        return s
    try:
        if not isinstance(s, basestring):
            if hasattr(s, "__unicode__"):
                s = unicode(s)
            else:
                try:
                    s = unicode(str(s), encoding, "strict")
                except UnicodeEncodeError:
                    if not isinstance(s, Exception):
                        raise
                    s = " ".join([s3_unicode(arg, encoding) for arg in s])
        else:
            s = s.decode(encoding)
    except UnicodeDecodeError:
        if not isinstance(s, Exception):
            raise
        else:
            s = " ".join([s3_unicode(arg, encoding) for arg in s])
    return s

# =============================================================================
def s3_flatlist(nested):
    """ Iterator to flatten mixed iterables of arbitrary depth """
    for item in nested:
        if isinstance(item, collections.Iterable) and \
           not isinstance(item, basestring):
            for sub in s3_flatlist(item):
                yield sub
        else:
            yield item

# =============================================================================
def s3_orderby_fields(table, orderby, expr=False):
    """
        Introspect and yield all fields involved in a DAL orderby
        expression.

        @param table: the Table
        @param orderby: the orderby expression
        @param expr: True to yield asc/desc expressions as they are,
                     False to yield only Fields
    """

    if not orderby:
        return

    db = current.db
    COMMA = db._adapter.COMMA
    INVERT = db._adapter.INVERT

    if isinstance(orderby, str):
        items = orderby.split(",")
    elif type(orderby) is Expression:
        def expand(e):
            if isinstance(e, Field):
                return [e]
            if e.op == COMMA:
                return expand(e.first) + expand(e.second)
            elif e.op == INVERT:
                return [e] if expr else [e.first]
            return []
        items = expand(orderby)
    elif not isinstance(orderby, (list, tuple)):
        items = [orderby]
    else:
        items = orderby

    s3db = current.s3db
    tablename = table._tablename if table else None
    for item in items:
        if type(item) is Expression:
            if not isinstance(item.first, Field):
                continue
            f = item if expr else item.first
        elif isinstance(item, Field):
            f = item
        elif isinstance(item, str):
            fn, direction = (item.strip().split() + ["asc"])[:2]
            tn, fn = ([tablename] + fn.split(".", 1))[-2:]
            if tn:
                try:
                    f = s3db.table(tn, db_only=True)[fn]
                except (AttributeError, KeyError):
                    continue
            else:
                if current.response.s3.debug:
                    raise SyntaxError('Tablename prefix required for orderby="%s"' % item)
                else:
                    # Ignore
                    continue
            if expr and direction[:3] == "des":
                f = ~f
        else:
            continue
        yield f

# =============================================================================
def s3_get_extension(request=None):
    """
        Get the file extension in the path of the request

        @param request: the request object (web2py request or S3Request),
                        defaults to current.request
    """


    if request is None:
        request = current.request

    extension = request.extension
    if request.function == "ticket" and request.controller == "admin":
        extension = "html"
    elif "format" in request.get_vars:
        ext = request.get_vars.format
        if isinstance(ext, list):
            ext = ext[-1]
        extension = ext.lower() or extension
    else:
        ext = None
        for arg in request.args[::-1]:
            if "." in arg:
                ext = arg.rsplit(".", 1)[1].lower()
                break
        if ext:
            extension = ext
    return extension

# =============================================================================
def s3_set_extension(url, extension=None):
    """
        Add a file extension to the path of a url, replacing all
        other extensions in the path.

        @param url: the URL (as string)
        @param extension: the extension, defaults to the extension
                          of current. request
    """

    if extension == None:
        extension = s3_get_extension()
    #if extension == "html":
        #extension = ""

    u = urlparse.urlparse(url)

    path = u.path
    if path:
        if "." in path:
            elements = [p.split(".")[0] for p in path.split("/")]
        else:
            elements = path.split("/")
        if extension and elements[-1]:
            elements[-1] += ".%s" % extension
        path = "/".join(elements)
    return urlparse.urlunparse((u.scheme,
                                u.netloc,
                                path,
                                u.params,
                                u.query,
                                u.fragment))

# =============================================================================
def search_vars_represent(search_vars):
    """
        Unpickle and convert saved search form variables into
        a human-readable HTML.

        @param search_vars: the (c)pickled search form variables

        @return: HTML as string
    """

    import cPickle

    s = ""
    search_vars = search_vars.replace("&apos;", "'")

    try:
        search_vars = cPickle.loads(str(search_vars))
    except:
        raise HTTP(500, "ERROR RETRIEVING THE SEARCH CRITERIA")
    else:
        s = "<p>"
        pat = '_'
        for var in search_vars.iterkeys():
            if var == "criteria" :
                c_dict = search_vars[var]
                #s = s + crud_string("pr_save_search", "Search Criteria")
                for j in c_dict.iterkeys():
                    st = str(j)
                    if st[0] == '_':
                        continue
                    else:
                        st = st.replace("_search_", " ")
                        st = st.replace("_advanced", "")
                        st = st.replace("_simple", "")
                        st = st.replace("text", "text matching")
                        """st = st.replace(search_vars["function"], "")
                        st = st.replace(search_vars["prefix"], "")"""
                        st = st.replace("_", " ")
                        s = "%s <b> %s </b>: %s <br />" % \
                            (s, st.capitalize(), str(c_dict[j]))
            elif var == "simple" or var == "advanced":
                continue
            else:
                if var == "function":
                    v1 = "Resource Name"
                elif var == "prefix":
                    v1 = "Module"
                s = "%s<b>%s</b>: %s<br />" %(s, v1, str(search_vars[var]))
        s = s + "</p>"

    return XML(s)

# =============================================================================
def s3_jaro_winkler(str1, str2):
    """
        Return Jaro_Winkler distance of two strings (between 0.0 and 1.0)

        Used as a measure of similarity between two strings

        @see http://en.wikipedia.org/wiki/Jaro-Winkler_distance

        @param str1: the first string
        @param str2: the second string
        @status: currently unused
    """

    jaro_winkler_marker_char = chr(1)

    if (str1 == str2):
        return 1.0

    if str1 == None:
        return 0

    if str2 == None:
        return 0

    len1 = len(str1)
    len2 = len(str2)
    halflen = max(len1, len2) / 2 - 1

    ass1  = ""  # Characters assigned in str1
    ass2  = ""  # Characters assigned in str2
    workstr1 = str1
    workstr2 = str2

    common1 = 0    # Number of common characters
    common2 = 0

    # If the type is list  then check for each item in
    # the list and find out final common value
    if isinstance(workstr2, list):
        for item1 in workstr1:
            for item2 in workstr2:
                for i in range(len1):
                    start = max(0, i - halflen)
                    end = min(i + halflen + 1, len2)
                    index = item2.find(item1[i], start, end)
                    if (index > -1):
                        # Found common character
                        common1 += 1
                    ass1 = ass1 + item1[i]
                    item2 = item2[:index] + \
                            jaro_winkler_marker_char + \
                            item2[index + 1:]
    else:
        for i in range(len1):
            start = max(0, i - halflen)
            end   = min(i + halflen + 1, len2)
            index = workstr2.find(str1[i], start, end)
            if (index > -1):
                # Found common character
                common1 += 1
            ass1 = ass1 + str1[i]
            workstr2 = workstr2[:index] + \
                       jaro_winkler_marker_char + \
                       workstr2[index + 1:]

    # If the type is list
    if isinstance(workstr1, list):
        for item1 in workstr2:
            for item2 in workstr1:
                for i in range(len2):
                    start = max(0, i - halflen)
                    end = min(i + halflen + 1, len1)
                    index = item2.find(item1[i], start, end)
                    if (index > -1):
                        # Found common character
                        common2 += 1
                    ass2 = ass2 + item1[i]
                    item1 = item1[:index] + \
                            jaro_winkler_marker_char + \
                            item1[index + 1:]
    else:
        for i in range(len2):
            start = max(0, i - halflen)
            end   = min(i + halflen + 1, len1)
            index = workstr1.find(str2[i], start, end)
            if (index > -1):
                # Found common character
                common2 += 1
            ass2 = ass2 + str2[i]
            workstr1 = workstr1[:index] + \
                       jaro_winkler_marker_char + \
                       workstr1[index + 1:]

    if (common1 != common2):
        common1 = float(common1 + common2) / 2.0

    if (common1 == 0):
        return 0.0

    # Compute number of transpositions
    if (len1 == len2):
        transposition = 0
        for i in range(len(ass1)):
            if (ass1[i] != ass2[i]):
                transposition += 1
        transposition = transposition / 2.0
    elif (len1 > len2):
        transposition = 0
        for i in range(len(ass2)): #smaller length one
            if (ass1[i] != ass2[i]):
                transposition += 1
        while (i < len1):
            transposition += 1
            i += 1
        transposition = transposition / 2.0
    elif (len1 < len2):
        transposition = 0
        for i in range(len(ass1)): #smaller length one
            if (ass1[i] != ass2[i]):
                transposition += 1
        while (i < len2):
            transposition += 1
            i += 1
        transposition = transposition / 2.0

    # Compute number of characters common to beginning of both strings,
    # for Jaro-Winkler distance
    minlen = min(len1, len2)
    for same in range(minlen + 1):
        if (str1[:same] != str2[:same]):
            break
    same -= 1
    if (same > 4):
        same = 4

    common1 = float(common1)
    w = 1. / 3. * (common1 / float(len1) + \
                   common1 / float(len2) + \
                   (common1 - transposition) / common1)

    wn = w + same * 0.1 * (1.0 - w)
    if (wn < 0.0):
        wn = 0.0
    elif (wn > 1.0):
        wn = 1.0
    return wn

# =============================================================================
def s3_jaro_winkler_distance_row(row1, row2):
    """
        Calculate the percentage match for two db records

        @todo: parameter description?
        @status: currently unused
    """

    dw = 0
    num_similar = 0
    if len(row1) != len(row2):
            #print "The records columns does not match."
            return
    for x in range(0, len(row1)):
        str1 = row1[x]    # get row fields
        str2 = row2[x]    # get row fields
        dw += s3_jaro_winkler(str1, str2) #Calculate match value for two column values

    dw = dw / len(row1) # Average of all column match value.
    dw = dw * 100       # Convert to percentage
    return dw

# =============================================================================
def soundex(name, len=4):
    """
        Code referenced from http://code.activestate.com/recipes/52213-soundex-algorithm/

        @todo: parameter description?
    """

    # digits holds the soundex values for the alphabet
    digits = "01230120022455012623010202"
    sndx = ""
    fc = ""

    # Translate alpha chars in name to soundex digits
    for c in name.upper():
        if c.isalpha():
            if not fc:
                # remember first letter
                fc = c
            d = digits[ord(c)-ord("A")]
            # duplicate consecutive soundex digits are skipped
            if not sndx or (d != sndx[-1]):
                sndx += d

    # replace first digit with first alpha character
    sndx = fc + sndx[1:]

    # remove all 0s from the soundex code
    sndx = sndx.replace("0", "")

    # return soundex code padded to len characters
    return (sndx + (len * "0"))[:len]

# =============================================================================
def sort_dict_by_values(adict):
    """
        Sort a dict by value and return an OrderedDict
        - used by modules/eden/irs.py
    """

    return OrderedDict(sorted(adict.items(), key = lambda item: item[1]))

# =============================================================================
class Traceback(object):
    """ Generate the traceback for viewing error Tickets """

    def __init__(self, text):
        """ Traceback constructor """

        self.text = text

    # -------------------------------------------------------------------------
    def xml(self):
        """ Returns the xml """

        output = self.make_links(CODE(self.text).xml())
        return output

    # -------------------------------------------------------------------------
    def make_link(self, path):
        """ Create a link from a path """

        tryFile = path.replace("\\", "/")

        if os.path.isabs(tryFile) and os.path.isfile(tryFile):
            (folder, filename) = os.path.split(tryFile)
            (base, ext) = os.path.splitext(filename)
            app = current.request.args[0]

            editable = {"controllers": ".py", "models": ".py", "views": ".html"}
            l_ext = ext.lower()
            f_endswith = folder.endswith
            for key in editable.keys():
                check_extension = f_endswith("%s/%s" % (app, key))
                if l_ext == editable[key] and check_extension:
                    return A('"' + tryFile + '"',
                             _href=URL("edit/%s/%s/%s" % \
                                           (app, key, filename))).xml()
        return ""

    # -------------------------------------------------------------------------
    def make_links(self, traceback):
        """ Make links using the given traceback """

        lwords = traceback.split('"')

        # Make the short circuit compatible with <= python2.4
        result = (len(lwords) != 0) and lwords[0] or ""

        i = 1

        while i < len(lwords):
            link = self.make_link(lwords[i])

            if link == "":
                result += '"' + lwords[i]
            else:
                result += link

                if i + 1 < len(lwords):
                    result += lwords[i + 1]
                    i = i + 1

            i = i + 1

        return result

# =============================================================================
def URL2(a=None, c=None, r=None):
    """
        Modified version of URL from gluon/html.py
            - used by views/layout_iframe.html for our jquery function

        @example:

        >>> URL(a="a",c="c")
        "/a/c"

        generates a url "/a/c" corresponding to application a & controller c
        If r=request is passed, a & c are set, respectively,
        to r.application, r.controller

        The more typical usage is:

        URL(r=request) that generates a base url with the present
        application and controller.

        The function (& optionally args/vars) are expected to be added
        via jquery based on attributes of the item.
    """
    application = controller = None
    if r:
        application = r.application
        controller = r.controller
    if a:
        application = a
    if c:
        controller = c
    if not (application and controller):
        raise SyntaxError, "not enough information to build the url"
    #other = ""
    url = "/%s/%s" % (application, controller)
    return url

# =============================================================================
class S3CustomController(object):

    @classmethod
    def _view(cls, theme, name):

        view = os.path.join(current.request.folder,
                            "private", "templates", theme, "views", name)
        try:
            # Pass view as file not str to work in compiled mode
            current.response.view = open(view, "rb")
        except IOError:
            from gluon.http import HTTP
            raise HTTP(404, "Unable to open Custom View: %s" % view)
        return

# =============================================================================
class S3DateTime(object):
    """
        Toolkit for date+time parsing/representation
    """

    # -------------------------------------------------------------------------
    @classmethod
    def date_represent(cls, date, format=None, utc=False):
        """
            Represent the date according to deployment settings &/or T()

            @param date: the date
            @param format: the format if wishing to override deployment_settings
            @param utc: the date is given in UTC
        """

        if not format:
            format = current.deployment_settings.get_L10n_date_format()

        if date and isinstance(date, datetime.datetime) and utc:
            offset = cls.get_offset_value(current.session.s3.utc_offset)
            if offset:
                date = date + datetime.timedelta(seconds=offset)

        if date:
            try:
                return date.strftime(str(format))
            except:
                # e.g. dates < 1900
                date = date.isoformat()
                current.log.warning("Date cannot be formatted - using isoformat", date)
                return date
        else:
            return current.messages["NONE"]

    # -----------------------------------------------------------------------------
    @classmethod
    def time_represent(cls, time, utc=False):
        """
            Represent the date according to deployment settings &/or T()

            @param time: the time
            @param utc: the time is given in UTC
        """

        session = current.session
        settings = current.deployment_settings
        format = settings.get_L10n_time_format()

        if time and utc:
            offset = cls.get_offset_value(session.s3.utc_offset)
            if offset:
                time = time + datetime.timedelta(seconds=offset)

        if time:
            return time.strftime(str(format))
        else:
            return current.messages["NONE"]

    # -----------------------------------------------------------------------------
    @classmethod
    def datetime_represent(cls, dt, utc=False):
        """
            Represent the datetime according to deployment settings &/or T()

            @param dt: the datetime
            @param utc: the datetime is given in UTC
        """

        if dt and utc:
            offset = cls.get_offset_value(current.session.s3.utc_offset)
            if offset:
                dt = dt + datetime.timedelta(seconds=offset)

        if dt:
            return current.xml.encode_local_datetime(dt)
        else:
            return current.messages["NONE"]

    # -----------------------------------------------------------------------------
    @staticmethod
    def get_offset_value(offset_str):
        """
            Convert an UTC offset string into a UTC offset value in seconds

            @param offset_str: the UTC offset as string
        """
        if offset_str and len(offset_str) >= 5 and \
            (offset_str[-5] == "+" or offset_str[-5] == "-") and \
            offset_str[-4:].isdigit():
            offset_hrs = int(offset_str[-5] + offset_str[-4:-2])
            offset_min = int(offset_str[-5] + offset_str[-2:])
            offset = 3600 * offset_hrs + 60 * offset_min
            return offset
        else:
            return None
# =============================================================================
# From http://stackoverflow.com/questions/3393612/run-certain-code-every-n-seconds
class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer = None
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False
# =============================================================================
class S3TypeConverter(object):
    """ Universal data type converter """

    @classmethod
    def convert(cls, a, b):
        """
            Convert b into the data type of a

            @raise TypeError: if any of the data types are not supported
                              or the types are incompatible
            @raise ValueError: if the value conversion fails
        """

        if isinstance(a, lazyT):
            a = str(a)
        if b is None:
            return None
        if type(a) is type:
            if a in (str, unicode):
                return cls._str(b)
            if a is int:
                return cls._int(b)
            if a is bool:
                return cls._bool(b)
            if a is long:
                return cls._long(b)
            if a is float:
                return cls._float(b)
            if a is datetime.datetime:
                return cls._datetime(b)
            if a is datetime.date:
                return cls._date(b)
            if a is datetime.time:
                return cls._time(b)
            raise TypeError
        if type(b) is type(a) or isinstance(b, type(a)):
            return b
        if isinstance(a, (list, tuple, set)):
            if isinstance(b, (list, tuple, set)):
                return b
            elif isinstance(b, basestring):
                if "," in b:
                    b = b.split(",")
                else:
                    b = [b]
            else:
                b = [b]
            if len(a):
                cnv = cls.convert
                return [cnv(a[0], item) for item in b]
            else:
                return b
        if isinstance(b, (list, tuple, set)):
            cnv = cls.convert
            return [cnv(a, item) for item in b]
        if isinstance(a, basestring):
            return cls._str(b)
        if isinstance(a, bool):
            return cls._bool(b)
        if isinstance(a, int):
            return cls._int(b)
        if isinstance(a, long):
            return cls._long(b)
        if isinstance(a, float):
            return cls._float(b)
        if isinstance(a, datetime.datetime):
            return cls._datetime(b)
        if isinstance(a, datetime.date):
            return cls._date(b)
        if isinstance(a, datetime.time):
            return cls._time(b)
        raise TypeError

    # -------------------------------------------------------------------------
    @staticmethod
    def _bool(b):
        """ Convert into bool """

        if isinstance(b, bool):
            return b
        if isinstance(b, basestring):
            if b.lower() in ("true", "1"):
                return True
            elif b.lower() in ("false", "0"):
                return False
        if isinstance(b, (int, long)):
            if b == 0:
                return False
            else:
                return True
        raise TypeError

    # -------------------------------------------------------------------------
    @staticmethod
    def _str(b):
        """ Convert into string """

        if isinstance(b, basestring):
            return b
        if isinstance(b, datetime.date):
            raise TypeError # @todo: implement
        if isinstance(b, datetime.datetime):
            raise TypeError # @todo: implement
        if isinstance(b, datetime.time):
            raise TypeError # @todo: implement
        return str(b)

    # -------------------------------------------------------------------------
    @staticmethod
    def _int(b):
        """ Convert into int """

        if isinstance(b, int):
            return b
        return int(b)

    # -------------------------------------------------------------------------
    @staticmethod
    def _long(b):
        """ Convert into long """

        if isinstance(b, long):
            return b
        return long(b)

    # -------------------------------------------------------------------------
    @staticmethod
    def _float(b):
        """ Convert into float """

        if isinstance(b, long):
            return b
        return float(b)

    # -------------------------------------------------------------------------
    @staticmethod
    def _datetime(b):
        """ Convert into datetime.datetime """

        if isinstance(b, datetime.datetime):
            return b
        elif isinstance(b, basestring):
            try:
                # ISO Format is standard (e.g. in URLs)
                tfmt = current.xml.ISOFORMAT
                (y, m, d, hh, mm, ss, t0, t1, t2) = time.strptime(b, tfmt)
            except ValueError:
                try:
                    # Try localized datetime format
                    tfmt = str(current.deployment_settings.get_L10n_datetime_format())
                    (y, m, d, hh, mm, ss, t0, t1, t2) = time.strptime(b, tfmt)
                except ValueError:
                    # dateutil as last resort
                    try:
                        dt = current.xml.decode_iso_datetime(b)
                    except:
                        raise ValueError
                    else:
                        return dt
            return datetime.datetime(y, m, d, hh, mm, ss)
        else:
            raise TypeError

    # -------------------------------------------------------------------------
    @classmethod
    def _date(cls, b):
        """ Convert into datetime.date """

        if isinstance(b, datetime.date):
            return b
        elif isinstance(b, basestring):
            format = current.deployment_settings.get_L10n_date_format()
            validator = IS_DATE(format=format)
            value, error = validator(b)
            if error:
                # May be specified as datetime-string?
                value = cls._datetime(b).date()
            return value
        else:
            raise TypeError

    # -------------------------------------------------------------------------
    @staticmethod
    def _time(b):
        """ Convert into datetime.time """

        if isinstance(b, datetime.time):
            return b
        elif isinstance(b, basestring):
            validator = IS_TIME()
            value, error = validator(v)
            if error:
                raise ValueError
            return value
        else:
            raise TypeError

# =============================================================================
class S3MultiPath:
    """
        Simplified path toolkit for managing multi-ancestor-hypergraphs
        in a relational database.

        MultiPaths allow single-query searches for all ancestors and
        descendants of a node, as well as single-query affiliation
        testing - whereas they require multiple writes on update (one
        per each descendant node), so they should only be used for
        hypergraphs which rarely change.

        Every node of the hypergraph contains a path attribute, with the
        following MultiPath-syntax:

        MultiPath: <SimplePath>,<SimplePath>,...
        SimplePath: [|<Node>|<Node>|...|]
        Node: ID of the ancestor node

        SimplePaths contain only ancestors, not the node itself.

        SimplePaths contain the ancestors in reverse order, i.e. the nearest
        ancestor first (this is important because removing a vertex from the
        path will cut off the tail, not the head)

        A path like A<-B<-C can be constructed like:

            path = S3MultiPath([["C", "B", "A"]])
            [|C|B|A|]

        Extending this path by a vertex E<-B will result in a multipath like:

            path.extend("B", "E")
            [|C|B|A|],[|C|B|E|]

        Cutting the vertex A<-B reduces the multipath to:

            path.cut("B", "A")
            [|C|B|E|]

        Note the reverse notation (nearest ancestor first)!

        MultiPaths will be normalized automatically, i.e.:

            path = S3MultiPath([["C", "B", "A", "D", "F", "B", "E", "G"]])
            [|C|B|A|D|F|],[|C|B|E|G|]
    """

    # -------------------------------------------------------------------------
    # Construction
    #
    def __init__(self, paths=None):
        """ Constructor """
        self.paths = []
        if isinstance(paths, S3MultiPath):
            self.paths = list(paths.paths)
        else:
            if paths is None:
                paths = []
            elif type(paths) is str:
                paths = self.__parse(paths)
            elif not isinstance(paths, (list, tuple)):
                paths = [paths]
            append = self.append
            for p in paths:
                append(p)

    # -------------------------------------------------------------------------
    def append(self, path):
        """
            Append a new ancestor path to this multi-path

            @param path: the ancestor path
        """
        Path = self.Path

        if isinstance(path, Path):
            path = path.nodes
        else:
            path = Path(path).nodes
        multipath = None

        # Normalize any recurrent paths
        paths = self.__normalize(path)

        append = self.paths.append
        for p in paths:
            p = Path(p)
            if not self & p:
                append(p)
                multipath = self
        return multipath

    # -------------------------------------------------------------------------
    def extend(self, head, ancestors=None, cut=None):
        """
            Extend this multi-path with a new vertex ancestors<-head

            @param head: the head node
            @param ancestors: the ancestor (multi-)path of the head node
        """

        # If ancestors is a multi-path, extend recursively with all paths
        if isinstance(ancestors, S3MultiPath):
            extend = self.extend
            for p in ancestors.paths:
                extend(head, p, cut=cut)
            return self

        # Split-extend all paths which contain the head node
        extensions = []
        Path = self.Path
        append = extensions.append
        for p in self.paths:
            if cut:
                pos = p.find(cut)
                if pos > 0:
                    p.nodes = p.nodes[:pos-1]
            i = p.find(head)
            if i > 0:
                path = Path(p.nodes[:i]).extend(head, ancestors)
                detour = None
                for tail in self.paths:
                    j = tail.find(path.last())
                    if j > 0:
                        # append original tail
                        detour = Path(path)
                        detour.extend(path.last(), tail[j:])
                        append(detour)
                if not detour:
                    append(path)
        self.paths.extend(extensions)

        # Finally, cleanup for duplicate and empty paths
        return self.clean()

    # -------------------------------------------------------------------------
    def cut(self, head, ancestor=None):
        """
            Cut off the vertex ancestor<-head in this multi-path

            @param head: the head node
            @param ancestor: the ancestor node to cut off
        """
        for p in self.paths:
            p.cut(head, ancestor)
        # Must cleanup for duplicates
        return self.clean()

    # -------------------------------------------------------------------------
    def clean(self):
        """
            Remove any duplicate and empty paths from this multi-path
        """
        mp = S3MultiPath(self)
        pop = mp.paths.pop
        self.paths = []
        append = self.paths.append
        while len(mp):
            item = pop(0)
            if len(item) and not mp & item and not self & item:
                append(item)
        return self

    # -------------------------------------------------------------------------
    # Serialization/Deserialization
    #
    def __parse(self, value):
        """ Parse a multi-path-string into nodes """
        return value.split(",")

    def __repr__(self):
        """ Serialize this multi-path as string """
        return ",".join([str(p) for p in self.paths])

    def as_list(self):
        """ Return this multi-path as list of node lists """
        return [p.as_list() for p in self.paths if len(p)]

    # -------------------------------------------------------------------------
    # Introspection
    #
    def __len__(self):
        """ The number of paths in this multi-path """
        return len(self.paths)

    # -------------------------------------------------------------------------
    def __and__(self, sequence):
        """
            Check whether sequence is the start sequence of any of
            the paths in this multi-path (for de-duplication)

            @param sequence: sequence of node IDs (or path)
        """
        for p in self.paths:
            if p.startswith(sequence):
                return 1
        return 0

    # -------------------------------------------------------------------------
    def __contains__(self, sequence):
        """
            Check whether sequence is contained in any of the paths (can
            also be used to check whether this multi-path contains a path
            to a particular node)

            @param sequence: the sequence (or node ID)
        """
        for p in self.paths:
            if sequence in p:
                return 1
        return 0

    # -------------------------------------------------------------------------
    def nodes(self):
        """ Get all nodes from this path """
        nodes = []
        for p in self.paths:
            n = [i for i in p.nodes if i not in nodes]
            nodes.extend(n)
        return nodes

    # -------------------------------------------------------------------------
    @staticmethod
    def all_nodes(paths):
        """
            Get all nodes from all paths

            @param paths: list of multi-paths
        """
        nodes = []
        for p in paths:
            n = [i for i in p.nodes() if i not in nodes]
            nodes.extend(n)
        return nodes

    # -------------------------------------------------------------------------
    # Normalization
    #
    @staticmethod
    def __normalize(path):
        """
            Normalize a path into a sequence of non-recurrent paths

            @param path: the path as a list of node IDs
        """
        seq = map(str, path)
        l = zip(seq, seq[1:])
        if not l:
            return [path]
        seq = S3MultiPath.__resolve(seq)
        pop = seq.pop
        paths = []
        append = paths.append
        while len(seq):
            p = pop(0)
            s = paths + seq
            contained = False
            lp = len(p)
            for i in s:
                if i[:lp] == p:
                    contained = True
                    break
            if not contained:
                append(p)
        return paths

    # -------------------------------------------------------------------------
    @staticmethod
    def __resolve(seq):
        """
            Resolve a sequence of vertices (=pairs of node IDs) into a
            sequence of non-recurrent paths

            @param seq: the vertex sequence
        """
        resolve = S3MultiPath.__resolve
        if seq:
            head = seq[0]
            tail = seq[1:]
            tails = []
            index = tail.index
            append = tails.append
            while head in tail:
                pos = index(head)
                append(tail[:pos])
                tail = tail[pos + 1:]
            append(tail)
            r = []
            append = r.append
            for tail in tails:
                nt = resolve(tail)
                for t in nt:
                    append([head] + t)
            return r
        else:
            return [seq]

    # -------------------------------------------------------------------------
    # Helper class for simple ancestor paths
    #
    class Path:

        # ---------------------------------------------------------------------
        # Construction methods
        #
        def __init__(self, nodes=None):
            """ Constructor """
            self.nodes = []
            if isinstance(nodes, S3MultiPath.Path):
                self.nodes = list(nodes.nodes)
            else:
                if nodes is None:
                    nodes = []
                elif type(nodes) is str:
                    nodes = self.__parse(nodes)
                elif not isinstance(nodes, (list, tuple)):
                    nodes = [nodes]
                append = self.append
                for n in nodes:
                    if not append(n):
                        break

        # ---------------------------------------------------------------------
        def append(self, node=None):
            """
                Append a node to this path

                @param node: the node
            """
            if node is None:
                return True
            n = str(node)
            if not n:
                return True
            if n not in self.nodes:
                self.nodes.append(n)
                return True
            return False

        # ---------------------------------------------------------------------
        def extend(self, head, ancestors=None):
            """
                Extend this path with a new vertex ancestors<-head, if this
                path ends at the head node

                @param head: the head node
                @param ancestors: the ancestor sequence
            """
            if ancestors is None:
                # If no head node is specified, use the first ancestor node
                path = S3MultiPath.Path(head)
                head = path.first()
                ancestors = path.nodes[1:]
            last = self.last()
            if last is None or last == str(head):
                append = self.append
                path = S3MultiPath.Path(ancestors)
                for i in path.nodes:
                    if not append(i):
                        break
                return self
            else:
                return None

        # ---------------------------------------------------------------------
        def cut(self, head, ancestor=None):
            """
                Cut off the ancestor<-head vertex from this path, retaining
                the head node

                @param head: the head node
                @param ancestor: the ancestor node

            """
            if ancestor is not None:
                sequence = [str(head), str(ancestor)]
                pos = self.find(sequence)
                if pos > 0:
                    self.nodes = self.nodes[:pos]
            else:
                # if ancestor is None and the path starts with head,
                # then remove the entire path
                if str(head) == self.first():
                    self.nodes = []
            return self

        # ---------------------------------------------------------------------
        # Serialize/Deserialize
        #
        def __repr__(self):
            """ Represent this path as a string """
            return "[|%s|]" % "|".join(self.nodes)

        def __parse(self, value):
            """ Parse a string into nodes """
            return value.strip().strip("[").strip("]").strip("|").split("|")

        def as_list(self):
            """ Return the list of nodes """
            return list(self.nodes)

        # ---------------------------------------------------------------------
        # Item access
        #
        def __getitem__(self, i):
            """ Get the node at position i """
            try:
                return self.nodes.__getitem__(i)
            except IndexError:
                return None

        # ---------------------------------------------------------------------
        def first(self):
            """ Get the first node in this path (the nearest ancestor) """
            return self[0]

        # ---------------------------------------------------------------------
        def last(self):
            """ Get the last node in this path (the most distant ancestor) """
            return self[-1]

        # ---------------------------------------------------------------------
        # Tests
        #
        def __contains__(self, sequence):
            """
                Check whether this path contains sequence

                @param sequence: sequence of node IDs
            """
            if self.find(sequence) != -1:
                return 1
            else:
                return 0

        # ---------------------------------------------------------------------
        def __len__(self):
            """
                Get the number of nodes in this path
            """
            return len(self.nodes)

        # ---------------------------------------------------------------------
        def find(self, sequence):
            """
                Find a sequence of node IDs in this path

                @param sequence: sequence of node IDs (or path)
                @return: position of the sequence (index+1), 0 if the path
                          is empty, -1 if the sequence wasn't found
            """
            path = S3MultiPath.Path(sequence)
            sequence = path.nodes
            nodes = self.nodes
            if not sequence:
                return -1
            if not nodes:
                return 0
            head, tail = sequence[0], sequence[1:]
            pos = 0
            l = len(tail)
            index = nodes.index
            while head in nodes[pos:]:
                pos = index(head, pos) + 1
                if not tail or nodes[pos:pos+l] == tail:
                    return pos
            return -1

        # ---------------------------------------------------------------------
        def startswith(self, sequence):
            """
                Check whether this path starts with sequence

                @param sequence: sequence of node IDs (or path)
            """
            sequence = S3MultiPath.Path(sequence).nodes
            if self.nodes[0:len(sequence)] == sequence:
                return True
            else:
                return False

# =============================================================================
class S3MarkupStripper(HTMLParser.HTMLParser):
    """ Simple markup stripper """

    def __init__(self):
        self.reset()
        self.result = []

    def handle_data(self, d):
        self.result.append(d)

    def stripped(self):
        return "".join(self.result)

def s3_strip_markup(text):

    try:
        stripper = S3MarkupStripper()
        stripper.feed(text)
        text = stripper.stripped()
    except Exception, e:
        pass
    return text

# END =========================================================================
