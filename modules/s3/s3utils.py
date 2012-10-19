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

import datetime
import os
import re
import sys
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
from gluon.storage import Storage
from gluon.dal import Row
from gluon.sqlhtml import SQLTABLE
from gluon.tools import Crud
from gluon.contrib.simplejson.ordered_dict import OrderedDict

from s3validators import IS_UTC_OFFSET

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
                                     SPAN(" *", _class="req")))):
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
        if field.writable:
            validators = field.requires
            if isinstance(validators, IS_EMPTY_OR) and field.name not in mark_required:
                # Allow notnull fields to be marked as not required
                # if we populate them onvalidation
                labels[field.name] = "%s:" % field.label
                continue
            else:
                required = field.required or field.notnull or \
                            field.name in mark_required
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
                    except TypeError:
                        # default validator takes no args
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
def s3_get_db_field_value(tablename=None,
                          fieldname=None,
                          look_up_value=None,
                          look_up_field="id",
                          match_case=True):
    """
        Returns the value of <field> from the first record in <table_name>
        with <look_up_field> = <look_up>

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

        @todo: update parameter description
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

    if not record and not rows and query is not None:
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
        if record.middle_name:
            mname = record.middle_name.strip()
        if record.last_name:
            lname = record.last_name.strip()
        return s3_format_fullname(fname, mname, lname, truncate)

    elif rows:
        represents = {}
        for row in rows:
            fname, mname, lname = "", "", ""
            if "pr_person" in row:
                record = row["pr_person"]
            else:
                record = row
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
    """
        Represent Facilities
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
    for instance_type in instance_types:
        represent = db.org_site.instance_type.represent
        instance_type_nice = represent(instance_type)
        c, f = instance_type.split("_")
        site_ids = instance_ids[instance_type]
        table = db[instance_type]
        query = table.site_id.belongs(site_ids)
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

        @todo: parameter description?
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
                            _class="hide popup",
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

        @todo: parameter description?
    """

    if not url:
        return ""
    return A(url, _href=url, _target="blank")

# =============================================================================
def s3_avatar_represent(id, tablename="auth_user", _class="avatar"):
    """
        Represent a User as their profile picture or Gravatar

        @todo: parameter description?
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

    return IMG(_src=url,
               _class=_class,
               _width=size[0],
               _height=size[1],
              )

# =============================================================================
def s3_auth_user_represent(id):
    """
        Represent a user as their email address

        @todo: parameter description?
    """

    if not id:
        return current.messages.NONE

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
def s3_auth_group_represent(opt):
    """
        Represent user groups by their role names

        @todo: parameter description?
    """

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
def s3_represent_name(table):
    """
        Returns a represent function for the common case where we return
        the name of the record.
    """

    def represent(id, row=None):
        if row:
            return row.name
        elif not id:
            return current.messages.NONE

        r = current.db(table._id == id).select(table.name,
                                               limitby=(0, 1)
                                               ).first()
        try:
            return r.name
        except:
            return current.messages.UNKNOWN_OPT

    return represent

# =============================================================================
def s3_represent_name_translate(table):
    """
        Returns a represent function for the common case where we return
        a translated version of the name of the record.
    """

    def represent(id, row=None):
        if row:
            return current.T(row.name)
        elif not id:
            return current.messages.NONE

        r = current.db(table._id == id).select(table.name,
                                               limitby=(0, 1)
                                               ).first()
        try:
            return current.T(r.name)
        except:
            return current.messages.UNKNOWN_OPT

    return represent

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

        @todo: parameter description?
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

        @todo: parameter description?
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
        - needed to check for passwords being same
        @ToDo: Move this to JS. Internationalisation (T()) can be provided in
               views/l10n.js
    """

    T = current.T
    request = current.request
    settings = current.deployment_settings
    s3 = current.response.s3
    appname = current.request.application
    auth = current.auth

    if s3.debug:
        s3.scripts.append("/%s/static/scripts/jquery.validate.js" % appname)
        s3.scripts.append("/%s/static/scripts/jquery.pstrength.2.1.0.js" % appname)
    else:
        s3.scripts.append("/%s/static/scripts/jquery.validate.min.js" % appname)
        s3.scripts.append("/%s/static/scripts/jquery.pstrength.2.1.0.min.js" % appname)

    if request.cookies.has_key("registered"):
        password_position = '''last'''
    else:
        password_position = '''first'''

    if settings.get_auth_registration_mobile_phone_mandatory():
        mobile = '''
  mobile:{
   required:true
  },'''
    else:
        mobile = ""

    if settings.get_auth_registration_organisation_required():
        org1 = '''
  organisation_id:{
   required: true
  },'''
        org2 = "".join((''',
  organisation_id:"''', str(T("Enter your organization")), '''"'''))
    else:
        org1 = ""
        org2 = ""

    domains = ""
    if settings.get_auth_registration_organisation_hidden() and \
       request.controller != "admin":
        table = current.auth.settings.table_user
        table.organisation_id

        table = current.s3db.auth_organisation
        query = (table.organisation_id != None) & \
                (table.domain != None)
        whitelists = db(query).select(table.organisation_id,
                                      table.domain)
        if whitelists:
            domains = '''$('#auth_user_organisation_id__row').hide()
S3.whitelists={
'''
            count = 0
            for whitelist in whitelists:
                count += 1
                domains += "'%s':%s" % (whitelist.domain,
                                         whitelist.organisation_id)
                if count < len(whitelists):
                    domains += ",\n"
                else:
                    domains += "\n"
            domains += '''}
$('#regform #auth_user_email').blur(function(){
 var email=$('#regform #auth_user_email').val()
 var domain=email.split('@')[1]
 if(undefined!=S3.whitelists[domain]){
  $('#auth_user_organisation_id').val(S3.whitelists[domain])
 }else{
  $('#auth_user_organisation_id__row').show()
 }
})'''

    # validate signup form on keyup and submit
    # @ToDo: //remote:'emailsurl'
    script = "".join(( domains, '''
$('#regform').validate({
 errorClass:'req',
 rules:{
  first_name:{
   required:true
  },''', mobile, '''
  email:{
   required:true,
   email:true
  },''', org1, '''
  password:{
   required:true
  },
  password_two:{
   required:true,
   equalTo:".password:''', password_position, '''"
  }
 },
 messages:{
  first_name:"''', str(T("Enter your first name")), '''",
  password:{
   required:"''', str(T("Provide a password")), '''"
  },
  password_two:{
   required:"''', str(T("Repeat your password")), '''",
   equalTo:"''', str(T("Enter the same password as above")), '''"
  },
  email:{
   required:"''', str(T("Please enter a valid email address")), '''",
   email:"''', str(T("Please enter a valid email address")), '''"
  }''', org2, '''
 },
 errorPlacement:function(error,element){
  error.appendTo(element.parent().next())
 },
 submitHandler:function(form){
  form.submit()
 }
})
var MinPasswordChar = ''', str(auth.settings.password_min_length), ''';
   $('.password:''', password_position, '''').pstrength({ minchar: MinPasswordChar, minchar_label: null } );
''' ))
    s3.jquery_ready.append(script)

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

    if isinstance(s, unicode):
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
class S3BulkImporter(object):
    """
        Import CSV files of data to pre-populate the database.
        Suitable for use in Testing, Demos & Simulations
    """

    def __init__(self):
        """ Constructor """

        import csv
        from xml.sax.saxutils import unescape

        self.csv = csv
        self.unescape = unescape
        self.importTasks = []
        self.specialTasks = []
        self.tasks = []
        self.alternateTables = {"hrm_person": {"tablename":"pr_person",
                                               "prefix":"pr",
                                               "name":"person"},
                                "member_person": {"tablename":"pr_person",
                                                  "prefix":"pr",
                                                  "name":"person"},
                               }
        self.errorList = []
        self.resultList = []

    # -------------------------------------------------------------------------
    def load_descriptor(self, path):
        """ Method that will load the descriptor file and then all the
            import tasks in that file into the importTasks property.
            The descriptor file is the file called tasks.txt in path.
            The file consists of a comma separated list of:
            application, resource name, csv filename, xsl filename.
        """

        source = open(os.path.join(path, "tasks.cfg"), "r")
        values = self.csv.reader(source)
        for details in values:
            if details == []:
                continue
            prefix = details[0][0].strip('" ')
            if prefix == "#": # comment
                continue
            if prefix == "*": # specialist function
                self.extractSpecialistLine(path, details)
            else: # standard importer
                self.extractImporterLine(path, details)

    # -------------------------------------------------------------------------
    def extractImporterLine(self, path, details):
        """
            Method that extract the details for an import Task
        """
        argCnt = len(details)
        if argCnt == 4 or argCnt == 5:
             # remove any spaces and enclosing double quote
            app = details[0].strip('" ')
            res = details[1].strip('" ')
            request = current.request

            csvFileName = details[2].strip('" ')
            if csvFileName[:7] == "http://":
                csv = csvFileName
            else:
                (csvPath, csvFile) = os.path.split(csvFileName)
                if csvPath != "":
                    path = os.path.join(request.folder,
                                        "private",
                                        "templates",
                                        csvPath)
                csv = os.path.join(path, csvFile)

            xslFileName = details[3].strip('" ')
            templateDir = os.path.join(request.folder,
                                       "static",
                                       "formats",
                                       "s3csv",
                                      )
            # try the app directory in the templates directory first
            xsl = os.path.join(templateDir, app, xslFileName)
            _debug("%s %s" % (xslFileName, xsl))
            if os.path.exists(xsl) == False:
                # now try the templates directory
                xsl = os.path.join(templateDir, xslFileName)
                _debug ("%s %s" % (xslFileName, xsl))
                if os.path.exists(xsl) == False:
                    # use the same directory as the csv file
                    xsl = os.path.join(path, xslFileName)
                    _debug ("%s %s" % (xslFileName, xsl))
                    if os.path.exists(xsl) == False:
                        self.errorList.append(
                        "Failed to find a transform file %s, Giving up." % xslFileName)
                        return
            vars = None
            if argCnt == 5:
                vars = details[4]
            self.tasks.append([1, app, res, csv, xsl, vars])
            self.importTasks.append([app, res, csv, xsl, vars])
        else:
            self.errorList.append(
            "prepopulate error: job not of length 4. %s job ignored" % task)

    # -------------------------------------------------------------------------
    def extractSpecialistLine(self, path, details):
        """ Method that will store a single import job into
            the importTasks property.
        """
        function = details[1].strip('" ')
        csv = None
        if len(details) == 3:
            fileName = details[2].strip('" ')
            (csvPath, csvFile) = os.path.split(fileName)
            if csvPath != "":
                path = os.path.join(current.request.folder,
                                    "private",
                                    "templates",
                                    csvPath)
            csv = os.path.join(path, csvFile)
        extraArgs = None
        if len(details) == 4:
            extraArgs = details[3].strip('" ')
        self.tasks.append([2, function, csv, extraArgs])
        self.specialTasks.append([function, csv, extraArgs])

    # -------------------------------------------------------------------------
    def load_import(self, controller, csv, xsl):
        """ Method that will store a single import job into
            the importTasks property.
        """
        self.importTasks.append([controller, csv, xsl])

    # -------------------------------------------------------------------------
    def execute_import_task(self, task):
        """ Method that will execute each import job, in order """
        start = datetime.datetime.now()
        if task[0] == 1:
            db = current.db
            request = current.request
            response = current.response
            errorString = "prepopulate error: file %s missing"
            # Store the view
            view = response.view

            _debug ("Running job %s %s (filename=%s transform=%s)" % (task[1], task[2], task[3], task[4]))
            prefix = task[1]
            name = task[2]
            tablename = "%s_%s" % (prefix, name)
            if tablename in self.alternateTables:
                details = self.alternateTables[tablename]
                if "tablename" in details:
                    tablename = details["tablename"]
                current.s3db.table(tablename)
                if "loader" in details:
                    loader = details["loader"]
                    if loader is not None:
                        loader()
                if "prefix" in details:
                    prefix = details["prefix"]
                if "name" in details:
                    name = details["name"]

            try:
                resource = current.s3db.resource(tablename)
            except AttributeError:
                # Table cannot be loaded
                self.errorList.append("WARNING: Unable to find table %s import job skipped" % tablename)
                return

            # Check if the source file is accessible
            filename = task[3]
            if filename[:7] == "http://":
                import urllib2
                req = urllib2.Request(url=filename)
                try:
                    f = urllib2.urlopen(req)
                except urllib2.HTTPError, e:
                    self.errorList.append("Could not access %s: %s" % (filename, e.read()))
                    return
                except:
                    self.errorList.append(errorString % filename)
                    return
                else:
                    csv = f
            else:
                try:
                    csv = open(filename, "r")
                except IOError:
                    self.errorList.append(errorString % filename)
                    return

            # Check if the stylesheet is accessible
            try:
                open(task[4], "r")
            except IOError:
                self.errorList.append(errorString % task[4])
                return

            extra_data = None
            if task[5]:
                try:
                    extradata = self.unescape(task[5], {"'": '"'})
                    extradata = json.loads(extradata)
                    extra_data = extradata
                except:
                    self.errorList.append("WARNING:5th parameter invalid, parameter %s ignored" % task[5])
            try:
                # @todo: add extra_data and file attachments
                result = resource.import_xml(csv,
                                             format="csv",
                                             stylesheet=task[4],
                                             extra_data=extra_data)
            except SyntaxError, e:
                self.errorList.append("WARNING: import error - %s" % e)
                return

            if not resource.error:
                db.commit()
            else:
                # Must roll back if there was an error!
                error = resource.error
                self.errorList.append("%s - %s: %s" % (
                                      task[3], resource.tablename, error))
                errors = current.xml.collect_errors(resource)
                if errors:
                    self.errorList.extend(errors)
                db.rollback()

            # Restore the view
            response.view = view
            end = datetime.datetime.now()
            duration = end - start
            csvName = task[3][task[3].rfind("/")+1:]
            try:
                # Python-2.7
                duration = '{:.2f}'.format(duration.total_seconds()/60)
                msg = "%s import job completed in %s mins" % (csvName, duration)
            except AttributeError:
                # older Python
                msg = "%s import job completed in %s" % (csvName, duration)
            self.resultList.append(msg)
            if response.s3.debug:
                s3_debug(msg)

    # -------------------------------------------------------------------------
    def execute_special_task(self, task):
        """
        """

        start = datetime.datetime.now()
        s3 = current.response.s3
        if task[0] == 2:
            fun = task[1]
            csv = task[2]
            extraArgs = task[3]
            if csv is None:
                if extraArgs is None:
                    error = s3[fun]()
                else:
                    error = s3[fun](extraArgs)
            elif extraArgs is None:
                error = s3[fun](csv)
            else:
                error = s3[fun](csv, extraArgs)
            if error:
                self.errorList.append(error)
            end = datetime.datetime.now()
            duration = end - start
            try:
                # Python-2.7
                duration = '{:.2f}'.format(duration.total_seconds()/60)
                msg = "%s import job completed in %s mins" % (fun, duration)
            except AttributeError:
                # older Python
                msg = "%s import job completed in %s" % (fun, duration)
            self.resultList.append(msg)
            if s3.debug:
                s3_debug(msg)

    # -------------------------------------------------------------------------
    def import_role(self, filename):
        """ Import Roles from CSV """

        # Check if the source file is accessible
        try:
            openFile = open(filename, "r")
        except IOError:
            return "Unable to open file %s" % filename

        auth = current.auth
        acl = auth.permission
        create_role = auth.s3_create_role

        def parseACL(_acl):
            permissions = _acl.split("|")
            aclValue = 0
            for permission in permissions:
                if permission == "READ":
                    aclValue = aclValue | acl.READ
                if permission == "CREATE":
                    aclValue = aclValue | acl.CREATE
                if permission == "UPDATE":
                    aclValue = aclValue | acl.UPDATE
                if permission == "DELETE":
                    aclValue = aclValue | acl.DELETE
                if permission == "ALL":
                    aclValue = aclValue | acl.ALL
            return aclValue

        reader = self.csv.DictReader(openFile)
        roles = {}
        acls = {}
        args = {}
        for row in reader:
            if row != None:
                role = row["role"]
                if "description" in row:
                    desc = row["description"]
                else:
                    desc = ""
                rules = {}
                extra_param = {}
                if "controller" in row and row["controller"]:
                    rules["c"] = row["controller"]
                if "function" in row and row["function"]:
                    rules["f"] = row["function"]
                if "table" in row and row["table"]:
                    rules["t"] = row["table"]
                if row["oacl"]:
                    rules["oacl"] = parseACL(row["oacl"])
                if row["uacl"]:
                    rules["uacl"] = parseACL(row["uacl"])
                #if "org" in row and row["org"]:
                    #rules["organisation"] = row["org"]
                #if "facility" in row and row["facility"]:
                    #rules["facility"] = row["facility"]
                if "entity" in row and row["entity"]:
                    rules["entity"] = row["entity"]
                if "hidden" in row and row["hidden"]:
                    extra_param["hidden"] = row["hidden"]
                if "system" in row and row["system"]:
                    extra_param["system"] = row["system"]
                if "protected" in row and row["protected"]:
                    extra_param["protected"] = row["protected"]
                if "uid" in row and row["uid"]:
                    extra_param["uid"] = row["uid"]
            if role in roles:
                acls[role].append(rules)
            else:
                roles[role] = [role,desc]
                acls[role] = [rules]
            if len(extra_param) > 0 and role not in args:
                args[role] = extra_param
        for rulelist in roles.values():
            if rulelist[0] in args:
                create_role(rulelist[0],
                            rulelist[1],
                            *acls[rulelist[0]],
                            **args[rulelist[0]])
            else:
                create_role(rulelist[0],
                            rulelist[1],
                            *acls[rulelist[0]])

    # -------------------------------------------------------------------------
    def clear_tasks(self):
        """ Clear the importTask list """
        self.tasks = []

    # -------------------------------------------------------------------------
    def perform_tasks(self, path):
        """ convenience method that will load and then execute the import jobs
            that are listed in the descriptor file
        """
        self.load_descriptor(path)
        for task in self.tasks:
            if task[0] == 1:
                self.execute_import_task(task)
            elif task[0] == 2:
                self.execute_special_task(task)

# =============================================================================
class S3DateTime(object):
    """
        Toolkit for date+time parsing/representation
    """

    # -------------------------------------------------------------------------
    @staticmethod
    def date_represent(date, utc=False):
        """
            Represent the date according to deployment settings &/or T()

            @param date: the date
            @param utc: the date is given in UTC
        """

        session = current.session
        settings = current.deployment_settings

        format = settings.get_L10n_date_format()

        if date and isinstance(date, datetime.datetime) and utc:
            offset = IS_UTC_OFFSET.get_offset_value(session.s3.utc_offset)
            if offset:
                date = date + datetime.timedelta(seconds=offset)

        if date:
            return date.strftime(str(format))
        else:
            return current.messages.NONE

    # -----------------------------------------------------------------------------
    @staticmethod
    def time_represent(time, utc=False):
        """
            Represent the date according to deployment settings &/or T()

            @param time: the time
            @param utc: the time is given in UTC
        """

        session = current.session
        settings = current.deployment_settings
        format = settings.get_L10n_time_format()

        if time and utc:
            offset = IS_UTC_OFFSET.get_offset_value(session.s3.utc_offset)
            if offset:
                time = time + datetime.timedelta(seconds=offset)

        if time:
            return time.strftime(str(format))
        else:
            return current.messages.NONE

    # -----------------------------------------------------------------------------
    @staticmethod
    def datetime_represent(dt, utc=False):
        """
            Represent the datetime according to deployment settings &/or T()

            @param dt: the datetime
            @param utc: the datetime is given in UTC
        """

        session = current.session
        xml = current.xml

        if dt and utc:
            offset = IS_UTC_OFFSET.get_offset_value(session.s3.utc_offset)
            if offset:
                dt = dt + datetime.timedelta(seconds=offset)

        if dt:
            return xml.encode_local_datetime(dt)
        else:
            return current.messages.NONE

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
class Traceback(object):
    """ Generate the traceback for viewing error Tickets """

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
class S3MarkupStripper(HTMLParser.HTMLParser):
    """ Simple markup stripper """

    def __init__(self):
        self.reset()
        self.result = []

    def handle_data(self, d):
        self.result.append(d)

    def stripped(self):
        return "".join(self.result)

# =============================================================================
class S3DataTable(object):
    """
        Generate a datatable from a list of Storages and a list of fields
    """

    # The dataTable id if no explicit value has been provided
    id_counter = 1

    def __init__(self,
                 rfields,
                 data,
                 start=0,
                 limit=None,
                 filterString=None,
                 orderby=None,
                 ):
        """
            S3DataTable constructor

            @param rfields: A list of S3Resourcefield
            @param data: A list of Storages the key is of the form table.field
                         The value is the data to be displayed in the dataTable
            @param start: the first row to return from the data
            @param limit: the (maximum) number of records to return
            @param filterString: The string that was used in filtering the records
            @param orderby: the DAL orderby construct
        """

        from gluon.dal import Expression

        self.data = data
        self.rfields = rfields
        lfields = []
        append = lfields.append
        heading = {}
        for field in rfields:
            selector = "%s.%s" % (field.tname, field.fname)
            append(selector)
            heading[selector] = (field.label)
        self.lfields = lfields
        self.heading = heading
        max = len(data)
        if start < 0:
            start == 0
        if start > max:
            start = max
        if limit == None:
            end = max
        else:
            end = start + limit
            if end > max:
                end = max
        self.start = start
        self.end = end
        self.filterString = filterString

        def selectAction(orderby):
            if isinstance(orderby, tuple):
                for el in orderby:
                    selectAction(el)
            if isinstance(orderby, Field):
                extractField(orderby)
            elif isinstance(orderby, Expression):
                extractExpression(orderby)
            else:
                self.orderby.append([1, "asc"])

        def extractField(field):
            cnt = 0
            for rfield in rfields:
                if str(field) == rfield.colname:
                    self.orderby.append([cnt, "asc"])
                    break
                cnt += 1

        def extractExpression(exp):
            cnt = 0
            if isinstance(exp.first, Field):
                for rfield in rfields:
                    if str(exp.first) == rfield.colname:
                        if exp.op == exp.db._adapter.INVERT:
                            self.orderby.append([cnt, "desc"])
                        else:
                            self.orderby.append([cnt, "asc"])
                        break
                    cnt += 1
            else:
                extractExpression(exp.first)
            if exp.second:
                selectAction(exp.second)

        self.orderby = []
        selectAction(orderby)

    # -------------------------------------------------------------------------
    @staticmethod
    def getConfigData():
        """
            Method to extract the configuration data from S3 globals and
            store them as an attr variable

            @return: dictionary of attributes which can be passed into html()

            @param attr: dictionary of attributes which can be passed in
                   dt_displayLength : The default number of records that will be shown
                   dt_pagination: Enable pagination
                   dt_pagination_type: type of pagination, either:
                                        (default) full_numbers
                                        OR two_button
                   dt_bFilter: Enable or disable filtering of data.
                   dt_group: The colum that is used to group the data
                   dt_ajax_url: The URL to be used for the Ajax call
                   dt_action_col: The column where the action buttons will be placed
                   dt_bulk_actions: list of labels for the bulk actions.
                   dt_bulk_col: The column in which the checkboxes will appear,
                                by default it will be the column immediately
                                before the first data item
                   dt_bulk_selected: A list of selected items
                   dt_actions: dictionary of actions
                   dt_styles: dictionary of styles to be applied to a list of ids
                              for example:
                              {"warning" : [1,3,6,7,9],
                               "alert" : [2,10,13]}
        """

        request = current.request
        s3 = current.response.s3

        attr = Storage()
        if s3.datatable_ajax_source:
            attr.dt_ajax_url = s3.datatable_ajax_source
        if s3.actions:
            attr.dt_actions = s3.actions
        if s3.dataTableBulkActions:
            attr.dt_bulk_actions = s3.dataTableBulkActions
        if s3.dataTable_iDisplayLength:
            attr.dt_displayLength = s3.dataTable_iDisplayLength
        attr.dt_pagination = "false" if s3.no_sspag else "true"
        if s3.dataTable_sPaginationType:
            attr.dt_pagination_type = s3.dataTable_sPaginationType
        if s3.dataTable_group:
            attr.dt_group = s3.dataTable_group
        if s3.dataTable_NobFilter:
            attr.dt_bFilter = not s3.dataTable_NobFilter
        if s3.dataTable_sDom:
            attr.dt_sDom = s3.dataTable_sDom
        if s3.dataTableDisplay:
            attr.dt_display = s3.dataTableDisplay
        if s3.dataTableStyleDisabled or s3.dataTableStyleWarning or s3.dataTableStyleAlert:
            attr.dt_styles = {}
            if s3.dataTableStyleDisabled:
                attr.dt_styles["dtdisable"] = s3.dataTableStyleDisabled
            if s3.dataTableStyleWarning:
                attr.dt_styles["dtwarning"] = s3.dataTableStyleWarning
            if s3.dataTableStyleAlert:
                attr.dt_styles["dtalert"] = s3.dataTableStyleAlert
        return attr

    # -------------------------------------------------------------------------
    @staticmethod
    def getControlData(rfields, vars):
        """
            Method that will return the orderby and filter from the vars
            returned by the browser, from an ajax call.

            @param rfields: A list of S3Resourcefield
            @param vars: A list of variables sent from the dataTable
        """

        # @todo: does not sort properly in option fields nor FK references
        if not vars.iSortingCols:
            return (False, "")

        sort_cols = int(vars.iSortingCols)
        orderby = False
        for x in range(sort_cols):
            index = int(vars["iSortCol_%s" % x])
            f = rfields[index].field
            if vars["sSortDir_%s" % x] == "desc":
                f = ~f
            if not orderby:
                orderby = f
            else:
                orderby |= f
        # @todo: does not search properly in option fields nor FK references
        words = vars.sSearch
        if not words:
            return (orderby, "")
        words = words.split()
        query = None
        for rf in rfields:
            if rf.ftype in ("string", "text") :
                if not query:
                    query = rf.field.contains(words)
                else:
                    query |= (rf.field.contains(words))

        return (orderby, query)

    # ---------------------------------------------------------------------
    @staticmethod
    def listFormats(id, rfields=None, permalink=None):
        """
            Calculate the export formats that can be added to the table

            @param id: The unique dataTabel ID
            @param rfields: optional list of rfields
        """

        T = current.T
        s3 = current.response.s3
        application = current.request.application

        # @todo: this needs rework
        #        - s3FormatRequest must retain any URL filters
        #        - s3FormatRequest must remove the "search" method
        #        - other data formats could have other list_fields,
        #          hence applying the datatable sorting/filters is
        #          not transparent
        if s3.datatable_ajax_source:
            end = s3.datatable_ajax_source.find(".aadata")
            default_url = s3.datatable_ajax_source[:end] # strip '.aadata' extension
        else:
            default_url = current.request.url
        iconList = []
        url = s3.formats.pdf if s3.formats.pdf else default_url
        iconList.append(IMG(_src="/%s/static/img/pdficon_small.gif" % application,
                            _onclick="s3FormatRequest('pdf','%s','%s');" % (id, url),
                            _alt=T("Export in PDF format"),
                            ))
        url = s3.formats.xls if s3.formats.xls else default_url
        iconList.append(IMG(_src="/%s/static/img/icon-xls.png" % application,
                            _onclick="s3FormatRequest('xls','%s','%s');" % (id, url),
                            _alt=T("Export in XLS format"),
                            ))
        url = s3.formats.rss if s3.formats.rss else default_url
        iconList.append(IMG(_src="/%s/static/img/RSS_16.png" % application,
                            _onclick="s3FormatRequest('rss','%s','%s');" % (id, url),
                            _alt=T("Export in RSS format"),
                            ))
        div = DIV(_class='list_formats')
        if permalink is not None:
            link = A(T("Link to this result"),
                     _href=permalink,
                     _class="permalink")
            div.append(link)
            div.append(" | ")

        div.append(current.T("Export to:"))
        if "have" in s3.formats:
            iconList.append(IMG(_src="/%s/static/img/have_16.png" % application,
                                _onclick="s3FormatRequest('have','%s','%s');" % (id, s3.formats.have),
                                _alt=T("Export in HAVE format"),
                                ))
        if "kml" in s3.formats:
            iconList.append(IMG(_src="/%s/static/img/kml_icon.png" % application,
                                _onclick="s3FormatRequest('kml','%s','%s');" % (id, s3.formats.kml),
                                _alt=T("Export in KML format"),
                                ))
        elif rfields:
            kml_list = ["location_id",
                        "site_id",
                        ]
            for r in rfields:
                if r.fname in kml_list:
                    iconList.append(IMG(_src="/%s/static/img/kml_icon.png" % application,
                                        _onclick="s3FormatRequest('kml','%s','%s');" % (id, default_url),
                                        _alt=T("Export in KML format"),
                                        ))
        if "map" in s3.formats:
            iconList.append(IMG(_src="/%s/static/img/map_icon.png" % application,
                                _onclick="s3FormatRequest('map','%s','%s');" % (id, s3.formats.map),
                                _alt=T("Show on map"),
                                ))

        for icon in iconList:
            div.append(icon)
        return div

    # ---------------------------------------------------------------------
    @staticmethod
    def defaultActionButtons(resource,
                             custom_actions=None,
                             r=None
                             ):
        """
            Configure default action buttons

            @param resource: the resource
            @param r: the request, if specified, all action buttons will
                      be linked to the controller/function of this request
                      rather than to prefix/name of the resource
            @param custom_actions: custom actions as list of dicts like
                                   {"label":label, "url":url, "_class":class},
                                   will be appended to the default actions
        """

        from s3crud import S3CRUD

        auth = current.auth
        s3 = current.response.s3

        table = resource.table
        s3.actions = None
        has_permission = auth.s3_has_permission
        ownership_required = auth.permission.ownership_required

        labels = current.manager.LABEL
        args = ["[id]"]

        # Choose controller/function to link to
        if r is not None:
            c = r.controller
            f = r.function
        else:
            c = resource.prefix
            f = resource.name

        # "Open" button
        if has_permission("update", table) and \
           not ownership_required("update", table):
            update_url = URL(c=c, f=f, args=args + ["update"])
            S3CRUD.action_button(labels.UPDATE, update_url)
        else:
            read_url = URL(c=c, f=f, args=args)
            S3CRUD.action_button(labels.READ, read_url)
        # Delete action
        # @todo: does not apply selective action (renders DELETE for
        #        all items even if the user is only permitted to delete
        #        some of them) => should implement "restrict", see
        #        S3CRUD.action_buttons
        deletable = current.s3db.get_config(resource.tablename, "deletable",
                                            True)
        if deletable and \
           has_permission("delete", table) and \
           not ownership_required("delete", table):
            delete_url = URL(c=c, f=f, args = args + ["delete"])
            S3CRUD.action_button(labels.DELETE, delete_url)

        # Append custom actions
        if custom_actions:
            s3.actions = s3.actions + custom_actions

    # ---------------------------------------------------------------------
    @staticmethod
    def htmlConfig(html,
                   id,
                   orderby,
                   rfields = None,
                   cache = None,
                   filteredrows = None,
                   **attr
                   ):
        """
            Method to wrap the html for a dataTable in a form, the list of formats
            used for data export and add the config details required by dataTables,

            @param html: The html table
            @param id: The id of the table
            @param orderby: the sort details see aaSort at http://datatables.net/ref
            @param rfields: The list of resource fields
            @param attr: dictionary of attributes which can be passed in
                   dt_displayLength : The default number of records that will be shown
                   dt_sDom : The Datatable DOM initialisation variable, describing
                             the order in which elements are displayed.
                             See http://datatables.net/ref for more details.
                   dt_pagination : Is pagination enabled, dafault 'true'
                   dt_pagination_type : How the pagination buttons are displayed
                   dt_bFilter: Enable or disable filtering of data.
                   dt_ajax_url: The URL to be used for the Ajax call
                   dt_action_col: The column where the action buttons will be placed
                   dt_bulk_actions: list of labels for the bulk actions.
                   dt_bulk_col: The column in which the checkboxes will appear,
                                by default it will be the column immediately
                                before the first data item
                   dt_group: The column(s) that is(are) used to group the data
                   dt_group_totals: The number of record in each group.
                                    This will be displayed in parenthesis
                                    after the group title.
                   dt_group_titles: The titles to be used for each group.
                                    These are a list of lists with the inner list
                                    consisting of two values, the repr from the
                                    db and the label to display. This can be more than
                                    the actual number of groups (giving an empty group).
                   dt_group_space: Insert a space between the group heading and the next group
                   dt_bulk_selected: A list of selected items
                   dt_actions: dictionary of actions
                   dt_styles: dictionary of styles to be applied to a list of ids
                              for example:
                              {"warning" : [1,3,6,7,9],
                               "alert" : [2,10,13]}
                   dt_text_maximum_len: The maximum length of text before it is condensed
                   dt_text_condense_len: The length displayed text is condensed down to
                   dt_shrink_groups: If set then the rows within a group will be hidden
                                     two types are supported, 'individulal' and 'accordion'
                   dt_group_types: The type of indicator for groups that can be 'shrunk'
                                   Permitted valies are: 'icon' (the default) 'text' and 'none'
            @global current.response.s3.actions used to get the RowActions
        """

        from gluon.serializers import json
        from gluon.storage import Storage

        request = current.request
        s3 = current.response.s3

        if not s3.dataTableID or not isinstance(s3.dataTableID, list):
            s3.dataTableID = [id]
        elif id not in s3.dataTableID:
            s3.dataTableID.append(id)
        # The configuration parameter from the server to the client will be
        # sent in a json object stored in an hidden input field. This object
        # will then be parsed by s3.dataTable.js and the values used.
        config = Storage()
        config.id = id
        displayLength = attr.get("dt_displayLength", current.manager.ROWSPERPAGE)
        # Make sure that the displayed length is not greater than the number of filtered records
        if filteredrows and displayLength > filteredrows:
            displayLength = filteredrows
        config.displayLength = displayLength
        config.sDom = attr.get("dt_sDom", 'fril<"dataTable_table"t>pi')
        config.pagination = attr.get("dt_pagination", "true")
        config.paginationType = attr.get("dt_pagination_type", "full_numbers")
        config.bFilter = attr.get("dt_bFilter", "true")
        config.ajaxUrl = attr.get("dt_ajax_url", URL(c=request.controller,
                                                     f=request.function,
                                                     extension="aadata",
                                                     args=request.args,
                                                     vars=request.get_vars,
                                                     ))
        config.rowStyles = attr.get("dt_styles", [])


        rowActions = s3.actions
        if rowActions:
            config.rowActions = rowActions
        else:
            config.rowActions = []
        bulkActions = attr.get("dt_bulk_actions", None)
        if bulkActions and not isinstance(bulkActions, list):
            bulkActions = [bulkActions]
        config.bulkActions = bulkActions
        config.bulkCol = attr.get("dt_bulk_col", 0)
        action_col = attr.get("dt_action_col", 0)
        if bulkActions and config.bulkCol <= action_col:
            action_col += 1
        config.actionCol = action_col
        group_list = attr.get("dt_group", [])
        if not isinstance(group_list, list):
            group_list = [group_list]
        dt_group = []
        for group in group_list:
            if bulkActions and config.bulkCol <= group:
                group += 1
            if action_col >= group:
                group -= 1
            dt_group.append([group, "asc"])
        config.group = dt_group
        config.groupTotals = attr.get("dt_group_totals", [])
        config.groupTitles = attr.get("dt_group_titles", [])
        config.groupSpacing = attr.get("dt_group_space", "false")
        for order in orderby:
            if bulkActions:
                if config.bulkCol <= order[0]:
                    order[0] += 1
            if action_col >= order[0]:
                order[0] -= 1
        config.aaSort = orderby
        config.textMaxLength = attr.get("dt_text_maximum_len", 80)
        config.textShrinkLength = attr.get("dt_text_condense_len", 75)
        config.shrinkGroupedRows = attr.get("dt_shrink_groups", "false")
        config.groupIcon = attr.get("dt_group_types", [])
        # Wrap the table in a form and add some data in hidden fields
        form = FORM()
        if not s3.no_formats and len(html) > 0:
            permalink = attr.get("dt_permalink", None)
            form.append(S3DataTable.listFormats(id, rfields,
                                                permalink=permalink))
        form.append(html)
        # Add the configuration details for this dataTable
        form.append(INPUT(_type="hidden",
                          _id="%s_configurations" % id,
                          _name="config",
                          _value=json(config)))
        # If we have a cache set up then pass it in
        if cache:
            form.append(INPUT(_type="hidden",
                              _id="%s_dataTable_cache" %id,
                              _name="cache",
                              _value=json(cache)))
        # If we have bulk actions then add the hidden fields
        if config.bulkActions:
            form.append(INPUT(_type="hidden",
                              _id="%s_dataTable_bulkMode" % id,
                              _name="mode",
                              _value="Inclusive"))
            bulk_selected = attr.get("dt_bulk_selected", "")
            if isinstance(bulk_selected, list):
                bulk_selected = ",".join(bulk_selected)
            form.append(INPUT(_type="hidden",
                              _id="%s_dataTable_bulkSelection" % id,
                              _name="selected",
                              _value="[%s]" % bulk_selected))
        return form

    # ---------------------------------------------------------------------
    def table(self, id, flist=None, action_col=0):
        """
            Method to render the data as an html table. This is of use if
            and html table is required without the dataTable goodness. However
            if you want html for a dataTable then use the html() method

            @param id: The id of the table
            @param flist: The list of fields
            @param action_col: The column where action columns will be displayed
                               (this is required by dataTables)
        """

        data = self.data
        heading = self.heading
        start = self.start
        end = self.end
        if not flist:
            flist = self.lfields

        # Build the header row
        header = THEAD()
        tr = TR()
        for field in flist:
            if field == "BULK":
                tr.append(TH(""))
            else:
                tr.append(TH(heading[field]))
        header.append(tr)

        body = TBODY()
        if data:
            # Build the body rows (the actual data)
            rc = 0
            for i in xrange(start, end):
                row = data[i]
                if rc % 2 == 0:
                    _class = "even"
                else:
                    _class = "odd"
                rc += 1
                tr = TR(_class=_class)
                for field in flist:
                    # Insert a checkbox for bulk select
                    if field == "BULK":
                        tr.append(TD(INPUT(_id="select%s" % row[flist[action_col]],
                                           _type="checkbox",
                                           _class="bulkcheckbox",
                                           )))
                    else:
                        tr.append(TD(row[field]))
                body.append(tr)
        table = TABLE([header, body], _id=id, _class="dataTable display")
        return table

    # ---------------------------------------------------------------------
    def html(self,
             totalrows,
             filteredrows,
             id = None,
             sEcho = 1,
             **attr
             ):
        """
            Method to render the data into html

            @param totalrows: The total rows in the unfiltered query.
            @param filteredrows: The total rows in the filtered query.
            @param id: The id of the table these need to be unique if more
                       than one dataTable is to be rendered on the same page.
                           If this is not passed in then a unique id will be
                           generated. Regardless the id is stored in self.id
                           so it can be easily accessed after rendering.
            @param sEcho: An unaltered copy of sEcho sent from the client used
                          by dataTables as a draw count.
            @param attr: dictionary of attributes which can be passed in
        """

        flist = self.lfields

        if not id:
            id = "list_%s" % self.id_counter
            self.id_counter += 1
        self.id = id

        bulkActions = attr.get("dt_bulk_actions", None)
        bulkCol = attr.get("dt_bulk_col", 0)
        if bulkCol > len(flist):
            bulkCol = len(flist)
        action_col = attr.get("dt_action_col", 0)
        if action_col != 0:
            if action_col == -1 or action_col >= len(flist):
                action_col = len(flist) -1
                attr["dt_action_col"] = action_col
            flist = flist[1:action_col+1] + [flist[0]] + flist[action_col+1:]

        # Get the details for any bulk actions. If we have at least one bulk
        # action then a column will be added, either at the start or in the
        # column identified by dt_bulk_col
        if bulkActions:
            flist.insert(bulkCol, "BULK")
            if bulkCol <= action_col:
                action_col += 1

        pagination = attr.get("dt_pagination", "true") == "true"
        if pagination:
            real_end = self.end
            self.end = self.start + 1
        table = self.table(id, flist, action_col)
        cache = None
        if pagination:
            s3 = current.response.s3
            self.end = real_end
            aadata = self.aadata(totalrows, filteredrows, id, sEcho,
                                 flist, stringify=False, **attr)
            cache = {"iCacheLower": self.start,
                     "iCacheUpper": self.end if filteredrows > self.end else filteredrows,
                     "lastJson": aadata}

        html = self.htmlConfig(table,
                               id,
                               self.orderby,
                               self.rfields,
                               cache,
                               filteredrows,
                               **attr
                               )
        return html

    # ---------------------------------------------------------------------
    def aadata(self,
               totalrows,
               displayrows,
               id,
               sEcho,
               flist,
               stringify=True,
               **attr
               ):
        """
            Method to render the data into a json object

            @param totalrows: The total rows in the unfiltered query.
            @param displayrows: The total rows in the filtered query.
            @param id: The id of the table for which this ajax call will
                       respond to.
            @param sEcho: An unaltered copy of sEcho sent from the client used
                          by dataTables as a draw count.
            @param flist: The list of fields
            @param attr: dictionary of attributes which can be passed in
                   dt_action_col: The column where the action buttons will be placed
                   dt_bulk_actions: list of labels for the bulk actions.
                   dt_bulk_col: The column in which the checkboxes will appear,
                                by default it will be the column immediately
                                before the first data item
                   dt_group_totals: The number of record in each group.
                                    This will be displayed in parenthesis
                                    after the group title.
        """

        from gluon.serializers import json

        data = self.data
        if not flist:
            flist = self.lfields
        start = self.start
        end = self.end
        action_col = attr.get("dt_action_col", 0)
        structure = {}
        aadata = []
        for i in xrange(start, end):
            row = data[i]
            details = []
            for field in flist:
                if field == "BULK":
                    details.append("<INPUT id='select%s' type='checkbox' class='bulkcheckbox'>" % \
                        row[flist[action_col]])
                else:
                    details.append(s3_unicode(row[field]))
            aadata.append(details)
        structure["dataTable_id"] = id
        structure["dataTable_filter"] = self.filterString
        structure["dataTable_groupTotals"] = attr.get("dt_group_totals", [])
        structure["dataTable_sort"] = self.orderby
        structure["aaData"] = aadata
        structure["iTotalRecords"] = totalrows
        structure["iTotalDisplayRecords"] = displayrows
        structure["sEcho"] = sEcho
        if stringify:
            return json(structure)
        else:
            return structure

    # ---------------------------------------------------------------------
    def json(self,
             totalrows,
             displayrows,
             id,
             sEcho,
             stringify=True,
             **attr
             ):
        """
            Method to render the data into a json object

            @param totalrows: The total rows in the unfiltered query.
            @param displayrows: The total rows in the filtered query.
            @param id: The id of the table for which this ajax call will
                       respond to.
            @param sEcho: An unaltered copy of sEcho sent from the client used
                          by dataTables as a draw count.
            @param attr: dictionary of attributes which can be passed in
                   dt_action_col: The column where the action buttons will be placed
                   dt_bulk_actions: list of labels for the bulk actions.
                   dt_bulk_col: The column in which the checkboxes will appear,
                                by default it will be the column immediately
                                before the first data item
                   dt_group_totals: The number of record in each group.
                                    This will be displayed in parenthesis
                                    after the group title.
        """
        flist = self.lfields
        action_col = attr.get("dt_action_col", 0)
        if action_col != 0:
            if action_col == -1 or action_col >= len(flist):
                action_col = len(flist) - 1
            flist = flist[1:action_col+1] + [flist[0]] + flist[action_col+1:]
        # Get the details for any bulk actions. If we have at least one bulk
        # action then a column will be added, either at the start or in the
        # column identified by dt_bulk_col
        bulkActions = attr.get("dt_bulk_actions", None)
        bulkCol = attr.get("dt_bulk_col", 0)
        if bulkActions:
            if bulkCol > len(flist):
                bulkCol = len(flist)
            flist.insert(bulkCol, "BULK")
            if bulkCol <= action_col:
                action_col += 1

        return self.aadata(totalrows, displayrows, id, sEcho, flist,
                           stringify, **attr)

# END =========================================================================
