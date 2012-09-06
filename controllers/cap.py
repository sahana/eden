# -*- coding: utf-8 -*-

"""
    CAP Module - Controllers
"""

module = request.controller
resourcename = request.function

if module not in settings.modules:
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    module_name = settings.modules[module].name_nice
    response.title = module_name
    return dict(module_name=module_name)

# -----------------------------------------------------------------------------
def info_prep(r):
    template_info_id = None

    if r.representation == "html":
        item = r.record
        if (item and r.resource.tablename == "cap_info" and s3db.cap_alert_is_template(item.alert_id)):
            for f in ["urgency", "certainty",
                      "effective", "onset", "expires",
                      "priority", "severity"]:
                s3db.cap_info[f].writable = False
                s3db.cap_info[f].readable = False
                s3db.cap_info[f].required = False
            for f in ["category", "event"]:
                s3db.cap_info[f].required = False

    if request.post_vars.get("language", False):
        if (r.tablename == "cap_info"):
            try:
                template_info_id = s3db.cap_info(s3db.cap_info.id == request.resource._ids[0]) \
                                    .template_info_id
            except AttributeError, KeyError:
                pass
        elif (r.component and r.component.tablename == "cap_info"):
            try:
                template_info_id = r.component.get_id()
                # this will error out if component is not yet saved
            except:
                pass

    if template_info_id:

        # read template and copy locked fields to post_vars
        template = s3db.cap_info(s3db.cap_info.id == template_info_id)
        settings = json.loads(template.template_settings)
        if isinstance(settings.get('locked', False), dict):
            locked_fields = [lf for lf in settings["locked"] if settings["locked"]]
            for lf in locked_fields:
                request.post_vars[lf] = template[lf]
    return True

# -----------------------------------------------------------------------------
def alert():
    """ REST controller for CAP alerts """

    def prep(r):
        if "_ids" in dir(r.resource) and len(r.resource._ids) == 1 and \
            s3db.cap_alert_is_template(r.resource._ids[0]):
            redirect(URL(c="cap", f="template", args=request.args, vars=request.vars))

        if r.tablename == "cap_alert":
            if request.post_vars.get("edit_info", False):
                tid = str(request.post_vars["template_id"])
                if tid:
                    # read template and copy locked fields to post_vars
                    template = s3db.cap_alert(s3db.cap_alert.id == tid)
                    try:
                        settings = json.loads(template.template_settings)
                    except ValueError:
                        settings = dict()
                    if isinstance(settings.get('locked', False), dict):
                        locked_fields = [lf for lf in settings["locked"] if settings["locked"]]
                        for lf in locked_fields:
                            request.post_vars[lf] = template[lf]
        info_prep(r)
        return True

    s3.prep = prep

    def postp(r, output):
        """
            Common REST post-processor:
             - check to see if "Save and add information" was pressed
        """

        if r.tablename == "cap_alert":
            if request.post_vars.get("edit_info", False) and r.resource.lastid:
                table = current.s3db.cap_alert
                alert = current.db(table.id == r.resource.lastid) \
                                .select(table.template_id, limitby=(0, 1)).first()

                if alert:
                    template_id = alert.template_id
                    alert_id = r.resource.lastid
                    template_info = current.db(
                                        current.s3db.cap_info.alert_id == template_id
                                    ).select()
                    for row in template_info:
                        row_clone = row.as_dict()
                        unwanted_fields = ['deleted_rb',
                                           'owned_by_user',
                                           'approved_by',
                                           'mci',
                                           'deleted',
                                           'modified_on',
                                           'owned_by_entity',
                                           'uuid',
                                           'created_on',
                                           'deleted_fk',
                                           # Don't copy this: make an
                                           # Ajax call instead
                                           'template_settings',
                                           'id'
                                          ]
                        for key in unwanted_fields:
                            try:
                                row_clone.pop(key)
                            except KeyError:
                                pass

                        row_clone["alert_id"] = alert_id
                        row_clone["template_info_id"] = row.id
                        row_clone["is_template"] = False

                        current.s3db.cap_info.insert(**row_clone)

                r.next = URL(c="cap", f="alert",
                             args=[r.resource.lastid, "info"])
        return output

    s3.postp = postp

    s3.scripts.append("/%s/static/scripts/S3/s3.cap.js" % appname)
    s3.stylesheets.append("S3/cap.css")
    return s3db.cap_alert_controller()

# -----------------------------------------------------------------------------
def info():
    """ REST controller for CAP info segments """


    s3.prep = info_prep

    s3.scripts.append("/%s/static/scripts/S3/s3.cap.js" % appname)
    s3.stylesheets.append("S3/cap.css")
    return s3db.cap_info_controller()

def template():
    """ REST controller for CAP templates """

    #vars = request.vars
    #vars["as_template"] = 1
    #redirect(URL(c="cap", f="alert", args=request.args, vars=vars))
    #return True
    #s3.prep = info_prep

    viewing = request.vars['viewing']
    if viewing:
        table, id = viewing.strip().split(".")
        if table == "cap_alert":
            redirect(URL(c="cap", f="template", args=[id]))
            return False
    s3.scripts.append("/%s/static/scripts/json2.min.js" % appname)
    s3.scripts.append("/%s/static/scripts/S3/s3.cap.js" % appname)
    s3.stylesheets.append("S3/cap.css")
    return s3db.cap_template_controller()

# END =========================================================================
