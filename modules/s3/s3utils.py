# -*- coding: utf-8 -*-

""" Utilities

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @copyright: (c) 2010-2013 Sahana Software Foundation
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
import datetime
import os
import re
import sys
import time
import urllib
import HTMLParser

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

from gluon import *
from gluon.dal import Row
from gluon.sqlhtml import SQLTABLE
from gluon.storage import Storage
from gluon.tools import Crud
from gluon.languages import lazyT

from gluon.contrib.simplejson.ordered_dict import OrderedDict

DEBUG = False
if DEBUG:
    print >> sys.stderr, "S3Utils: DEBUG MODE"
    def _debug(m):
        print >> sys.stderr, m
else:
    _debug = lambda m: None

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
def s3_dev_toolbar():
    """
        Developer Toolbar - ported from gluon.Response.toolbar()
        Shows useful stuff at the bottom of the page in Debug mode
    """

    try:
        # New web2py
        from gluon.dal import THREAD_LOCAL
    except:
        # Old web2py
        from gluon.dal import thread as THREAD_LOCAL
    from gluon.utils import web2py_uuid

    BUTTON = TAG.button

    if hasattr(THREAD_LOCAL, "instances"):
        dbstats = [TABLE(*[TR(PRE(row[0]),
                           "%.2fms" % (row[1]*1000)) \
                           for row in i.db._timings]) \
                         for i in THREAD_LOCAL.instances]
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
                     mark_required=[],
                     label_html=(lambda field_label:
                                 DIV("%s:" % field_label,
                                     SPAN(" *", _class="req"))),
                     map_names=None):
    """
        Add asterisk to field label if a field is required

        @param fields: list of fields (or a table)
        @param mark_required: list of field names which are always required

        @returns: dict of labels

        @todo: complete parameter description?
    """

    labels = dict()

    # Do we have any required fields?
    _required = False
    for field in fields:
        if map_names:
            fname, flabel = map_names[field.name]
        else:
            fname, flabel = field.name, field.label
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

        @todo: parameter description
        @todo: is this still used?
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
def s3_filter_staff(r):
    """
        Filter out people which are already staff for this facility

        @todo: make the Person-AC pick up the filter options from
               the person_id field (currently not implemented)
    """

    db = current.db
    try:
        hrtable = db.hrm_human_resource
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

        @param person: the pr_person record or record_id
        @param pe_id: alternatively, the person entity ID
        @param truncate: truncate the name to max 24 characters
    """

    db = current.db
    ptable = db.pr_person

    record = None
    query = None
    if isinstance(person, (int, long)) or str(person).isdigit():
        query = (ptable.id == person) & (ptable.deleted != True)
    elif person is not None:
        record = person
    elif pe_id is not None:
        query = (ptable.pe_id == pe_id) & (ptable.deleted != True)

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
        - used by GIS.get_representation()

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
def s3_represent_facilities(db, site_ids, link=True):
    """
        Bulk lookup for Facility Representations
        - used by Home page
    """

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
    represent = db.org_site.instance_type.represent
    for instance_type in instance_types:
        site_ids = instance_ids[instance_type]
        table = db[instance_type]
        c, f = instance_type.split("_")
        query = table.site_id.belongs(site_ids)
        if instance_type == "org_facility":
            instance_type_nice = represent(instance_type)
            records = db(query).select(table.id,
                                       table.facility_type_id,
                                       table.site_id,
                                       table.name)
            type_represent = table.facility_type_id.represent
            for record in records:
                if record.facility_type_id:
                    facility_type = type_represent(record.facility_type_id[:1])
                    site_str = "%s (%s)" % (record.name, facility_type)
                else:
                    site_str = "%s (%s)" % (record.name, instance_type_nice)
                if link:
                    site_str = A(site_str, _href=URL(c=c,
                                                     f=f,
                                                     args=[record.id],
                                                     extension=""))

                results.append((record.site_id, site_str))

        else:
            instance_type_nice = represent(instance_type)
            records = db(query).select(table.id,
                                       table.site_id,
                                       table.name)
            for record in records:
                site_str = "%s (%s)" % (record.name, instance_type_nice)
                if link:
                    site_str = A(site_str, _href=URL(c=c,
                                                     f=f,
                                                     args=[record.id],
                                                     extension=""))

                results.append((record.site_id, site_str))

    return results

# =============================================================================
def s3_comments_represent(text, show_link=True):
    """
        Represent Comments Fields
    """

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
                            _onmouseout="$('#%s').hide();" % unique
                           ),
                        A("%s..." % text[:76],
                          _onmouseover="$('#%s').removeClass('hide').show();" % unique,
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
    return A(url, _href=url, _target="blank")

# =============================================================================
def s3_avatar_represent(id, tablename="auth_user", **attr):
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
    elif email:
        # If no Image uploaded, try Gravatar, which also provides a nice fallback identicon
        import hashlib
        hash = hashlib.md5(email).hexdigest()
        url = "http://www.gravatar.com/avatar/%s?s=50&d=identicon" % hash
    else:
        url = "http://www.gravatar.com/avatar/00000000000000000000000000000000?d=mm"

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
def s3_auth_group_represent(opt):
    """
        Represent user groups by their role names
    """

    if not opt:
        return current.messages["NONE"]

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
        return current.messages["NONE"]
    return ", ".join(roles)

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
        s3_debug("pywurfl python module has not been installed, browser compatibility listing will not be populated. Download pywurfl from http://pypi.python.org/pypi/pywurfl/")
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
def s3_register_validation():
    """
        JavaScript client-side validation for Register form
        - needed to check for passwords being same, etc
    """

    T = current.T
    request = current.request
    settings = current.deployment_settings
    s3 = current.response.s3
    appname = current.request.application
    auth = current.auth

    # Static Scripts
    scripts_append = s3.scripts.append
    if s3.debug:
        scripts_append("/%s/static/scripts/jquery.validate.js" % appname)
        scripts_append("/%s/static/scripts/jquery.pstrength.2.1.0.js" % appname)
        scripts_append("/%s/static/scripts/S3/s3.register_validation.js" % appname)
    else:
        scripts_append("/%s/static/scripts/jquery.validate.min.js" % appname)
        scripts_append("/%s/static/scripts/jquery.pstrength.2.1.0.min.js" % appname)
        scripts_append("/%s/static/scripts/S3/s3.register_validation.min.js" % appname)

    # Configuration
    js_global = []
    js_append = js_global.append
    if request.cookies.has_key("registered"):
        # .password:first
        js_append('''S3.password_position=1''')
    else:
        # .password:last
        js_append('''S3.password_position=2''')

    if settings.get_auth_registration_mobile_phone_mandatory():
        js_append('''S3.auth_registration_mobile_phone_mandatory=1''')

    if settings.get_auth_registration_organisation_required():
        js_append('''S3.get_auth_registration_organisation_required=1''')
        js_append('''i18n.enter_your_organisation="%s"''' % T("Enter your organization"))

    if request.controller != "admin":
        if settings.get_auth_registration_organisation_hidden():
            js_append('''S3.get_auth_registration_hide_organisation=1''')

        # Check for Whitelists
        table = current.s3db.auth_organisation
        query = (table.organisation_id != None) & \
                (table.domain != None)
        whitelists = current.db(query).select(table.organisation_id,
                                              table.domain)
        if whitelists:
            domains = []
            domains_append = domains.append
            for whitelist in whitelists:
                domains_append("'%s':%s" % (whitelist.domain,
                                            whitelist.organisation_id))
            domains = ''','''.join(domains)
            domains = '''S3.whitelists={%s}''' % domains
            js_append(domains)

    js_append('''i18n.enter_first_name="%s"''' % T("Enter your first name"))
    js_append('''i18n.provide_password="%s"''' % T("Provide a password"))
    js_append('''i18n.repeat_your_password="%s"''' % T("Repeat your password"))
    js_append('''i18n.enter_same_password="%s"''' % T("Enter the same password as above"))
    js_append('''i18n.please_enter_valid_email="%s"''' % T("Please enter a valid email address"))

    js_append('''S3.password_min_length=%i''' % settings.get_auth_password_min_length())

    script = '''\n'''.join(js_global)
    s3.js_global.append(script)

    # Call script after Global config done
    s3.jquery_ready.append('''s3_register_validation()''')

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

        @returns: tuple (tablename, key, multiple), where tablename is
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
def search_vars_represent(search_vars):
    """
        Unpickle and convert saved search form variables into
        a human-readable HTML.

        @param search_vars: the (c)pickled search form variables

        @returns: HTML as string
    """

    import cPickle

    s = ""
    search_vars = search_vars.replace("&apos;", "'")

    try:
        search_vars = cPickle.loads(str(search_vars))
    except:
        raise HTTP(500,"ERROR RETRIEVING THE SEARCH CRITERIA")
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
class CrudS3(Crud):
    """
        S3 extension of the gluon.tools.Crud class
        - select() uses SQLTABLES3 (to allow different linkto construction)

        @todo: is this still used anywhere?
    """

    def __init__(self):
        """ Initialise parent class & make any necessary modifications """
        Crud.__init__(self, current.db)


    def select(
        self,
        table,
        query=None,
        fields=None,
        orderby=None,
        limitby=None,
        headers={},
        **attr):

        db = current.db
        request = current.request
        if not (isinstance(table, db.Table) or table in db.tables):
            raise HTTP(404)
        if not self.has_permission("select", table):
            redirect(current.auth.settings.on_failed_authorization)
        #if record_id and not self.has_permission("select", table):
        #    redirect(current.auth.settings.on_failed_authorization)
        if not isinstance(table, db.Table):
            table = db[table]
        if not query:
            query = table.id > 0
        if not fields:
            fields = [table.ALL]
        rows = db(query).select(*fields, **dict(orderby=orderby,
            limitby=limitby))
        if not rows:
            return None # Nicer than an empty table.
        if not "linkto" in attr:
            attr["linkto"] = self.url(args="read")
        if not "upload" in attr:
            attr["upload"] = self.url("download")
        if request.extension != "html":
            return rows.as_list()
        return SQLTABLES3(rows, headers=headers, **attr)

# =============================================================================
class SQLTABLES3(SQLTABLE):
    """
        S3 custom version of gluon.sqlhtml.SQLTABLE

        Given a SQLRows object, as returned by a db().select(), generates
        an html table with the rows.

            - we need a different linkto construction for our CRUD controller
            - we need to specify a different ID field to direct to for the M2M controller
            - used by S3Resource.sqltable

        Optional arguments:

        @keyword linkto: URL (or lambda to generate a URL) to edit individual records
        @keyword upload: URL to download uploaded files
        @keyword orderby: Add an orderby link to column headers.
        @keyword headers: dictionary of headers to headers redefinions
        @keyword truncate: length at which to truncate text in table cells.
            Defaults to 16 characters.

        Optional names attributes for passed to the <table> tag

        Simple linkto example::

            rows = db.select(db.sometable.ALL)
            table = SQLTABLES3(rows, linkto="someurl")

        This will link rows[id] to .../sometable/value_of_id

        More advanced linkto example::

            def mylink(field):
                return URL(args=[field])

            rows = db.select(db.sometable.ALL)
            table = SQLTABLES3(rows, linkto=mylink)

        This will link rows[id] to::

            current_app/current_controller/current_function/value_of_id
    """

    def __init__(self, sqlrows,
                 linkto=None,
                 upload=None,
                 orderby=None,
                 headers={},
                 truncate=16,
                 columns=None,
                 th_link="",
                 **attributes):

        # reverted since it causes errors (admin/user & manual importing of req/req/import)
        # super(SQLTABLES3, self).__init__(**attributes)
        TABLE.__init__(self, **attributes)

        self.components = []
        self.attributes = attributes
        self.sqlrows = sqlrows
        (components, row) = (self.components, [])
        if not columns:
            columns = sqlrows.colnames
        if headers=="fieldname:capitalize":
            headers = {}
            for c in columns:
                headers[c] = " ".join([w.capitalize() for w in c.split(".")[-1].split("_")])
        elif headers=="labels":
            headers = {}
            for c in columns:
                (t, f) = c.split(".")
                field = sqlrows.db[t][f]
                headers[c] = field.label

        if headers!=None:
            for c in columns:
                if orderby:
                    row.append(TH(A(headers.get(c, c),
                                    _href=th_link+"?orderby=" + c)))
                else:
                    row.append(TH(headers.get(c, c)))
            components.append(THEAD(TR(*row)))

        tbody = []
        table_field = re.compile("[\w_]+\.[\w_]+")
        for (rc, record) in enumerate(sqlrows):
            row = []
            if rc % 2 == 0:
                _class = "even"
            else:
                _class = "odd"
            for colname in columns:
                if not table_field.match(colname):
                    if "_extra" in record and colname in record._extra:
                        r = record._extra[colname]
                        row.append(TD(r))
                        continue
                    else:
                        raise KeyError("Column %s not found (SQLTABLE)" % colname)
                (tablename, fieldname) = colname.split(".")
                try:
                    field = sqlrows.db[tablename][fieldname]
                except (KeyError, AttributeError):
                    field = None
                if tablename in record \
                        and isinstance(record, Row) \
                        and isinstance(record[tablename], Row):
                    r = record[tablename][fieldname]
                elif fieldname in record:
                    r = record[fieldname]
                else:
                    raise SyntaxError("something wrong in Rows object")
                r_old = r
                if not field:
                    pass
                elif linkto and field.type == "id":
                    #try:
                        #href = linkto(r, "table", tablename)
                    #except TypeError:
                        #href = "%s/%s/%s" % (linkto, tablename, r_old)
                    #r = A(r, _href=href)
                    try:
                        href = linkto(r)
                    except TypeError:
                        href = "%s/%s" % (linkto, r)
                    r = A(r, _href=href)
                #elif linkto and field.type.startswith("reference"):
                    #ref = field.type[10:]
                    #try:
                        #href = linkto(r, "reference", ref)
                    #except TypeError:
                        #href = "%s/%s/%s" % (linkto, ref, r_old)
                        #if ref.find(".") >= 0:
                            #tref,fref = ref.split(".")
                            #if hasattr(sqlrows.db[tref],"_primarykey"):
                                #href = "%s/%s?%s" % (linkto, tref, urllib.urlencode({fref:r}))
                    #r = A(str(r), _href=str(href))
                elif linkto \
                     and hasattr(field._table, "_primarykey") \
                     and fieldname in field._table._primarykey:
                    # have to test this with multi-key tables
                    key = urllib.urlencode(dict([ \
                                ((tablename in record \
                                      and isinstance(record, Row) \
                                      and isinstance(record[tablename], Row)) \
                                      and (k, record[tablename][k])) \
                                      or (k, record[k]) \
                                    for k in field._table._primarykey]))
                    r = A(r, _href="%s/%s?%s" % (linkto, tablename, key))
                elif field.type.startswith("list:"):
                    r = field.represent(r or [])
                elif field.represent:
                    r = field.represent(r)
                elif field.type.startswith("reference"):
                    pass
                elif field.type == "blob" and r:
                    r = "DATA"
                elif field.type == "upload":
                    if upload and r:
                        r = A("file", _href="%s/%s" % (upload, r))
                    elif r:
                        r = "file"
                    else:
                        r = ""
                elif field.type in ["string", "text"]:
                    r = str(field.formatter(r))
                    ur = unicode(r, "utf8")
                    if truncate!=None and len(ur) > truncate:
                        r = ur[:truncate - 3].encode("utf8") + "..."
                row.append(TD(r))
            tbody.append(TR(_class=_class, *row))
        components.append(TBODY(*tbody))

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
class S3DateTime(object):
    """
        Toolkit for date+time parsing/representation
    """

    # -------------------------------------------------------------------------
    @classmethod
    def date_represent(cls, date, utc=False):
        """
            Represent the date according to deployment settings &/or T()

            @param date: the date
            @param utc: the date is given in UTC
        """

        session = current.session
        settings = current.deployment_settings

        format = settings.get_L10n_date_format()

        if date and isinstance(date, datetime.datetime) and utc:
            offset = cls.get_offset_value(session.s3.utc_offset)
            if offset:
                date = date + datetime.timedelta(seconds=offset)

        if date:
            try:
                return date.strftime(str(format))
            except:
                # e.g. dates < 1900
                date = date.isoformat()
                s3_debug("Date cannot be formatted - using isoformat", date)
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
        if isinstance(a, (list, tuple)):
            if isinstance(b, (list, tuple)):
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
        if isinstance(b, (list, tuple)):
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
                @returns: position of the sequence (index+1), 0 if the path
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
