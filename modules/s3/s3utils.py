# -*- coding: utf-8 -*-

""" Utilities

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @copyright: (c) 2010-2012 Sahana Software Foundation
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

__all__ = ["URL2",
           "URL3",
           "Traceback",
           "getBrowserName",
           "s3_debug",
           "s3_dev_toolbar",
           "s3_mark_required",
           "s3_truncate",
           "s3_split_multi_value",
           "s3_get_db_field_value",
           "s3_filter_staff",
           "s3_fullname",
           "s3_represent_facilities",
           "s3_represent_multiref",
           "s3_comments_represent",
           "s3_url_represent",
           "s3_avatar_represent",
           "s3_auth_user_represent",
           "s3_auth_group_represent",
           "sort_dict_by_values",
           "jaro_winkler",
           "jaro_winkler_distance_row",
           "soundex",
           "search_vars_represent"]

import sys
import os
import hashlib
import md5
import re
import uuid

from gluon import *
from gluon import current
from gluon.storage import Storage

from gluon.contrib.simplejson.ordered_dict import OrderedDict

#try:
#    from xlrd import *
#except ImportError:
#    import sys
#    # On server shows up in Apache error log
#    print >> sys.stderr, "S3 Debug: s3utils: XLRD not installed, Spreadsheet Importer not available."

# =============================================================================
# Modified versions of URL from gluon/html.py
# we need simplified versions for our jquery functions

def URL2(a=None, c=None, r=None):
    """
    example:

    >>> URL(a="a",c="c")
    "/a/c"

    generates a url "/a/c" corresponding to application a & controller c
    If r=request is passed, a & c are set, respectively,
    to r.application, r.controller

    The more typical usage is:

    URL(r=request) that generates a base url with the present application and controller.

    The function (& optionally args/vars) are expected to be added via jquery based on attributes of the item.
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
def URL3(a=None, r=None):
    """
    example:

    >>> URL(a="a")
    "/a"

    generates a url "/a" corresponding to application a
    If r=request is passed, a is set
    to r.application

    The more typical usage is:

    URL(r=request) that generates a base url with the present application.

    The controller & function (& optionally args/vars) are expected to be added via jquery based on attributes of the item.
    """
    application = controller = None
    if r:
        application = r.application
        controller = r.controller
    if a:
        application = a
    if not (application and controller):
        raise SyntaxError, "not enough information to build the url"
    #other = ""
    url = "/%s" % application
    return url

# =============================================================================
class Traceback(object):
    """
        Generate the traceback for viewing error Tickets
    """

    def __init__(self, text):
        """ Traceback constructor """

        self.text = text


    def xml(self):
        """ Returns the xml """

        output = self.make_links(CODE(self.text).xml())
        return output

    def make_link(self, path):
        """ Create a link from a path """
        tryFile = path.replace("\\", "/")

        if os.path.isabs(tryFile) and os.path.isfile(tryFile):
            (folder, filename) = os.path.split(tryFile)
            (base, ext) = os.path.splitext(filename)
            app = current.request.args[0]

            editable = {"controllers": ".py", "models": ".py", "views": ".html"}
            for key in editable.keys():
                check_extension = folder.endswith("%s/%s" % (app, key))
                if ext.lower() == editable[key] and check_extension:
                    return A('"' + tryFile + '"',
                             _href=URL("edit/%s/%s/%s" % \
                                           (app, key, filename))).xml()
        return ""

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
def getBrowserName(userAgent):
    """
        Determine which browser is being used.
        - used by Selenium
    """

    if userAgent.find("MSIE") > -1:
        return "IE"
    elif userAgent.find("Firefox") > -1:
        return "Firefox"
    elif userAgent.find("Gecko") > -1:
        return "Mozilla"
    else:
        return "Unknown"

# =============================================================================
def s3_debug(message, value=None):
    """
       Debug Function (same name/parameters as JavaScript one)

       Provide an easy, safe, systematic way of handling Debug output
       (print to stdout doesn't work with WSGI deployments)

       @ToDo: Should be using python's built-in logging module?
    """

    try:
        output = "S3 Debug: %s" % str(message)
        if value:
            "%s: %s" % (output, str(value))
    except:
        output = u"S3 Debug: %s" % unicode(message)
        if value:
            u"%s: %s" % (output, unicode(value))

    print >> sys.stderr, output

# =============================================================================
def s3_dev_toolbar():
    """
        Developer Toolbar - ported from gluon.Response.toolbar()
        Shows useful stuff at the bottom of the page in Debug mode
    """
    from gluon.dal import thread
    from gluon.utils import web2py_uuid

    BUTTON = TAG.button

    if hasattr(thread, "instances"):
        dbstats = [TABLE(*[TR(PRE(row[0]),
                           "%.2fms" % (row[1]*1000)) \
                           for row in i.db._timings]) \
                         for i in thread.instances]
    else:
        dbstats = [] # if no db or on GAE
    u = web2py_uuid()
    return DIV(
        BUTTON("request", _onclick="$('#request-%s').slideToggle()" % u),
        DIV(BEAUTIFY(current.request), _class="dbg_hidden", _id="request-%s" % u),
        BUTTON("session", _onclick="$('#session-%s').slideToggle()" % u),
        DIV(BEAUTIFY(current.session), _class="dbg_hidden", _id="session-%s" % u),
        # Disabled response as it breaks S3SearchLocationWidget
        #BUTTON("response", _onclick="$('#response-%s').slideToggle()" % u),
        #DIV(BEAUTIFY(current.response), _class="dbg_hidden", _id="response-%s" % u),
        BUTTON("db stats", _onclick="$('#db-stats-%s').slideToggle()" % u),
        DIV(BEAUTIFY(dbstats), _class="dbg_hidden", _id="db-stats-%s" % u),
        SCRIPT("$('.dbg_hidden').hide()")
        )

# =============================================================================
def s3_mark_required(fields,
                     mark_required=None,
                     label_html=(lambda field_label:
                                 DIV("%s:" % field_label,
                                     SPAN(" *", _class="req")))):
    """
        Add asterisk to field label if a field is required

        @param fields: list of fields (or a table)
        @param mark_required: list of field names which are always required

        @returns: dict of labels
    """

    labels = dict()

    # Do we have any required fields?
    _required = False
    for field in fields:
        if field.writable:
            validators = field.requires
            if isinstance(validators, IS_EMPTY_OR):
                # Allow notnull fields to be marked as not required if we populate them onvalidation
                labels[field.name] = "%s:" % field.label
                continue
            else:
                required = field.required or field.notnull or \
                            mark_required and field.name in mark_required
            if not validators and not required:
                labels[field.name] = "%s:" % field.label
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
                    except TypeError: # default validator takes no args
                        pass
                    else:
                        if error:
                            required = True
                            break
            if required:
                _required = True
                labels[field.name] = label_html(field.label)
            else:
                labels[field.name] = "%s:" % field.label
        else:
            labels[field.name] = "%s:" % field.label

    if labels:
        return (labels, _required)
    else:
        return None

# =============================================================================
def s3_truncate(text, length=48, nice=True):
    """
        Nice truncating of text

        @param text: the text
        @param length: the maximum length
        @param nice: do not truncate words
    """

    if len(text) > length:
        if nice:
            return "%s..." % text[:length].rsplit(" ", 1)[0][:45]
        else:
            return "%s..." % text[:45]
    else:
        return text

# =============================================================================
def s3_split_multi_value(value):
    """
        Converts a series of numbers delimited by |, or already in a
        string into a list. If value = None, returns []

        @author: Michael Howden (michael@aidiq.com)
    """

    if not value:
        return []

    elif isinstance(value, ( str ) ):
        if "[" in value:
            #Remove internal lists
            value = value.replace("[", "")
            value = value.replace("]", "")
            value = value.replace("'", "")
            value = value.replace('"', "")
            return eval("[" + value + "]")
        else:
            return re.compile('[\w\-:]+').findall(str(value))
    else:
        return [str(value)]

# =============================================================================
def s3_get_db_field_value(tablename=None,
                          fieldname=None,
                          look_up_value=None,
                          look_up_field="id",
                          match_case=True):
    """
        Returns the value of <field> from the first record in <table_name>
        with <look_up_field> = <look_up>

        @author: Michael Howden (michael@aidiq.com)

        @param table: The name of the table
        @param field: the field to find the value from
        @param look_up: the value to find
        @param look_up_field: the field to find <look_up> in
        @type match_case: boolean

        @returns:
            - Field Value if there is a record
            - None - if there is no matching record

        Example::
            s3_get_db_field_value("or_organisation", "id",
                                   look_up = "UNDP",
                                   look_up_field = "name" )
    """
    db = current.db
    lt = db[tablename]
    lf = lt[look_up_field]
    if match_case or str(lf.type) != "string":
        query = (lf == look_up_value)
    else:
        query = (lf.lower() == str.lower(look_up_value))
    if "deleted" in lt:
        query = (lt.deleted == False) & query
    row = db(query).select(lt[fieldname], limitby=(0, 1)).first()
    return row and row[fieldname] or None

# =============================================================================
def s3_filter_staff(r):
    """
        Filter out people which are already staff for this facility

        @todo: make the Person-AC pick up the filter options from
               the person_id field (currently not implemented)
    """

    db = current.db
    try:
        hrtable = db.hrm_human_resource
    except:
        return
    try:
        site_id = r.record.site_id
        person_id_field = r.target()[2].person_id
    except:
        return
    query = (hrtable.site_id == site_id) & \
            (hrtable.deleted == False)

    staff = db(query).select(hrtable.person_id)
    person_ids = [row.person_id for row in staff]
    try:
        person_id_field.requires.set_filter(not_filterby = "id",
                                            not_filter_opts = person_ids)
    except:
        pass

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
        if not mname or mname.isspace():
            name = ("%s %s" % (fname, lname)).rstrip()
        else:
            name = ("%s %s %s" % (fname, mname, lname)).rstrip()
        if truncate:
            name = s3_truncate(name, 24, nice = False)
    return name

# =============================================================================
def s3_fullname(person=None, pe_id=None, truncate=True):
    """
        Returns the full name of a person

        @param person: the pr_person record or record_id or a list of record_ids
                       (last used by gis.get_representation())
        @param pe_id: alternatively, the person entity ID
        @param truncate: truncate the name to max 24 characters
    """

    DEFAULT = ""

    db = current.db
    ptable = db.pr_person

    record = None
    query = None
    rows = None
    if isinstance(person, (int, long)) or str(person).isdigit():
        query = (ptable.id == person) & (ptable.deleted != True)
    elif isinstance(person, list):
        query = (ptable.id.belongs(person)) & (ptable.deleted != True)
        rows = db(query).select(ptable.id,
                                ptable.first_name,
                                ptable.middle_name,
                                ptable.last_name)
    elif person is not None:
        record = person
    elif pe_id is not None:
        query = (ptable.pe_id == pe_id) & (ptable.deleted != True)

    if not record and not rows and query:
        record = db(query).select(ptable.first_name,
                                  ptable.middle_name,
                                  ptable.last_name,
                                  limitby=(0, 1)).first()
    if record:
        fname, mname, lname = "", "", ""
        try:
            # plain query
            if record.first_name:
                fname = record.first_name.strip()
            if record.middle_name:
                mname = record.middle_name.strip()
            if record.last_name:
                lname = record.last_name.strip()
        except KeyError:
            # result of a JOIN
            if record.pr_person.first_name:
                fname = record.pr_person.first_name.strip()
            if record.pr_person.middle_name:
                mname = record.pr_person.middle_name.strip()
            if record.pr_person.last_name:
                lname = record.pr_person.last_name.strip()
        return s3_format_fullname(fname, mname, lname, truncate)

    elif rows:
        represents = {}
        for record in rows:
            fname, mname, lname = "", "", ""
            if record.first_name:
                fname = record.first_name.strip()
            if record.middle_name:
                mname = record.middle_name.strip()
            if record.last_name:
                lname = record.last_name.strip()
            represent = s3_format_fullname(fname, mname, lname, truncate)
            represents[record.id] = represent
        return represents

    else:
        return DEFAULT

# =============================================================================
def s3_represent_facilities(db, site_ids, link=True):

    table = db.org_site
    sites = db(table._id.belongs(site_ids)).select(table._id,
                                                    table.instance_type)
    if not sites:
        return []

    instance_ids = Storage()
    instance_types = []
    for site in sites:
        site_id = site[table._id.name]
        instance_type = site.instance_type
        if instance_type not in instance_types:
            instance_types.append(instance_type)
            instance_ids[instance_type] = [site_id]
        else:
            instance_ids[instance_type].append(site_id)

    results = []
    for instance_type in instance_types:
        table = db[instance_type]
        site_ids = instance_ids[instance_type]

        query = table.site_id.belongs(site_ids)

        if instance_type == "org_office":
            records = db(query).select(table.id,
                                        table.site_id,
                                        table.type,
                                        table.name)
        else:
            records = db(query).select(table.id,
                                        table.site_id,
                                        table.name)

        for record in records:
            if instance_type == "org_office" and record.type == 5:
                instance_type_nice = current.T("Warehouse")
            else:
                represent = db.org_site.instance_type.represent
                instance_type_nice = represent(instance_type)

            site_str = "%s (%s)" % (record.name, instance_type_nice)

            if link:
                c, f = instance_type.split("_")
                site_str = A(site_str, _href=URL(c=c,
                                                 f=f,
                                                 args=[record.id],
                                                 extension=""))

            results.append((record.site_id, site_str))

    return results

# =============================================================================
def s3_represent_multiref(table, opt, represent=None, separator=", "):
    """
        Produce a representation for a list:reference field.
        Used by: gis.location.members
    """

    db = current.db

    if represent is None:
        if "name" in table.fields:
            represent = lambda r: r and r.name or UNKNOWN_OPT

    if isinstance(opt, (int, long, str)):
        query = (table.id == opt)
    else:
        query = (table.id.belongs(opt))
    if "deleted" in table.fields:
        query = query & (table.deleted == False)

    records = db(query).select()

    if records:
        try:
            first = represent(records[0])
            rep_function = represent
        except TypeError:
            first = represent % records[0]
            rep_function = lambda r: represent % r

        # NB join only operates on strings, and some callers provide A().
        results = [first]
        for record in records[1:]:
            results.append(separator)
            results.append(rep_function(record))

        # Wrap in XML to allow showing anchors on read-only pages, else
        # Web2py will escape the angle brackets, etc. The single-record
        # location represent produces A() (unless told not to), and we
        # want to show links if we can.
        return XML(DIV(*results))

    else:
        return current.messages.UNKNOWN_OPT

# =============================================================================
def s3_comments_represent(text, showlink=True):
    """ Represent Comments Fields """
    if len(text) < 80:
        return text
    elif not showlink:
        return "%s..." % text[:76]
    else:
        unique =  uuid.uuid4()
        represent = DIV(
                        DIV(text,
                            _id=unique,
                            _class="hidden popup",
                            _onmouseout="$('#%s').hide();" % unique
                           ),
                        A("%s..." % text[:76],
                          _onmouseover="$('#%s').removeClass('hidden').show();" % unique,
                         ),
                       )
        return represent

# =============================================================================
def s3_url_represent(url):
    """ Make URLs clickable """

    if not url:
        return ""

    return A(url, _href=url, _target="blank")

# =============================================================================
def s3_avatar_represent(id, tablename="auth_user", _class="avatar"):
    """ Represent a User as their profile picture or Gravatar """

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

    if image:
        url = URL(c="default", f="download",
                  args=image)
    elif email:
        # If no Image uploaded, try Gravatar, which also provides a nice fallback identicon
        hash = md5.new(email).hexdigest()
        url = "http://www.gravatar.com/avatar/%s?s=50&d=identicon" % hash

    else:
        url = "http://www.gravatar.com/avatar/00000000000000000000000000000000?d=mm"

    return IMG(_src=url,
               _class=_class,
               _height=50, _width=50)

# =============================================================================
def s3_auth_user_represent(id):
    """ Represent a user as their email address """

    db = current.db
    s3db = current.s3db

    table = s3db.auth_user
    user = db(table.id == id).select(table.email,
                                     limitby=(0, 1),
                                     cache=s3db.cache).first()
    if user:
        return user.email
    return None

# =============================================================================
def s3_auth_group_represent(opt):
    """ Represent user groups by their role names """

    if not opt:
        return current.messages.NONE

    auth = current.auth
    s3db = current.s3db

    table = auth.settings.table_group
    groups = current.db(table.id > 0).select(table.id,
                                             table.role,
                                             cache=s3db.cache).as_dict()
    if not isinstance(opt, (list, tuple)):
        opt = [opt]
    roles = []
    for o in opt:
        try:
            key = int(o)
        except ValueError:
            continue
        if key in groups:
            roles.append(groups[key]["role"])
    if not roles:
        return current.messages.NONE
    return ", ".join(roles)

# =============================================================================
def sort_dict_by_values(adict):
    """
        Sort a dict by value and return an OrderedDict
        - used by modules/eden/irs.py
    """

    return OrderedDict(sorted(adict.items(), key = lambda item: item[1]))

# =============================================================================
def jaro_winkler(str1, str2):
    """
        Return Jaro_Winkler distance of two strings (between 0.0 and 1.0)

        Used as a measure of similarity between two strings

        @see http://en.wikipedia.org/wiki/Jaro-Winkler_distance

        @param str1: the first string
        @param str2: the second string

        @author: Pradnya Kulkarni
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

    # If the type is list  then check for each item in the list and find out final common value
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
                    item2 = item2[:index] + jaro_winkler_marker_char + item2[index + 1:]
    else:
        for i in range(len1):
            start = max(0, i - halflen)
            end   = min(i + halflen + 1, len2)
            index = workstr2.find(str1[i], start, end)
            if (index > -1):
                # Found common character
                common1 += 1
            ass1 = ass1 + str1[i]
            workstr2 = workstr2[:index] + jaro_winkler_marker_char + workstr2[index + 1:]

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
                    item1 = item1[:index] + jaro_winkler_marker_char + item1[index + 1:]
    else:
        for i in range(len2):
            start = max(0, i - halflen)
            end   = min(i + halflen + 1, len1)
            index = workstr1.find(str2[i], start, end)
            if (index > -1):
                # Found common character
                common2 += 1
            ass2 = ass2 + str2[i]
            workstr1 = workstr1[:index] + jaro_winkler_marker_char + workstr1[index + 1:]

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

    # Compute number of characters common to beginning of both strings, for Jaro-Winkler distance
    minlen = min(len1, len2)
    for same in range(minlen + 1):
        if (str1[:same] != str2[:same]):
            break
    same -= 1
    if (same > 4):
        same = 4

    common1 = float(common1)
    w = 1. / 3. * (common1 / float(len1) + common1 / float(len2) + (common1 - transposition) / common1)

    wn = w + same * 0.1 * (1.0 - w)
    if (wn < 0.0):
        wn = 0.0
    elif (wn > 1.0):
        wn = 1.0
    return wn

# =============================================================================
def jaro_winkler_distance_row(row1, row2):
    """
        Calculate the percentage match for two db records

        @author: Pradnya Kulkarni
    """

    dw = 0
    num_similar = 0
    if len(row1) != len(row2):
            #print "The records columns does not match."
            return
    for x in range(0, len(row1)):
        str1 = row1[x]    # get row fields
        str2 = row2[x]    # get row fields
        dw += jaro_winkler(str1, str2) #Calculate match value for two column values

    dw = dw / len(row1) # Average of all column match value.
    dw = dw * 100       # Convert to percentage
    return dw

# =============================================================================
def soundex(name, len=4):
    """
        Code referenced from http://code.activestate.com/recipes/52213-soundex-algorithm/

        @author: Pradnya Kulkarni
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
def search_vars_represent(search_vars):
        """
            Returns Search Criteria in a Human Readable Form

            @author: Pratyush Nigam
        """

        import cPickle
        import re
        s = ""
        search_vars = search_vars.replace("&apos;", "'")
        try:
            search_vars = cPickle.loads(str(search_vars))
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
                            s = "%s <b> %s </b>: %s <br />" %(s, st.capitalize(), str(c_dict[j]))
                elif var == "simple" or var == "advanced":
                    continue
                else:
                    if var == "function":
                        v1 = "Resource Name"
                    elif var == "prefix":
                        v1 = "Module"
                    s = "%s<b>%s</b>: %s<br />" %(s, v1, str(search_vars[var]))
            s = s + "</p>"
        except:
            raise HTTP(500,"ERROR RETRIEVING THE SEARCH CRITERIA")

        return XML(s)

# END =========================================================================