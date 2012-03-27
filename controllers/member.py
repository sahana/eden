# -*- coding: utf-8 -*-

"""
    Membership Management
"""

module = request.controller
resourcename = request.function

if module not in deployment_settings.modules:
    raise HTTP(404, body="Module disabled: %s" % module)

# =============================================================================
def index():
    """ Dashboard """

    module_name = deployment_settings.modules[module].name_nice
    response.title = module_name

    item = None
    if deployment_settings.has_module("cms"):
        table = s3db.cms_post
        _item = db(table.module == module).select(table.id,
                                                  table.body,
                                                  limitby=(0, 1)).first()
        if _item:
            if s3_has_role(ADMIN):
                item = DIV(XML(_item.body),
                           BR(),
                           A(T("Edit"),
                             _href=URL(c="cms", f="post",
                                       args=[_item.id, "update"],
                                       vars={"module":module}),
                             _class="action-btn"))
            else:
                item = _item.body
        elif s3_has_role(ADMIN):
            item = DIV(H2(module_name),
                       A(T("Edit"),
                         _href=URL(c="cms", f="post", args="create",
                                   vars={"module":module}),
                         _class="action-btn"))

    if not item:
        item = H2(module_name)

    # tbc
    report = ""

    response.view = "index.html"
    return dict(item=item, report=report)

# =============================================================================
# People
# =============================================================================
def membership():
    """
        REST Controller
    """

    tablename = "member_membership"
    table = s3db[tablename]

    def prep(r):
        if r.interactive:
            if r.id and r.component is None:
                # Redirect to person controller
                vars = {"membership.id": r.id}
                redirect(URL(f="person",
                             vars=vars))
        return True
    response.s3.prep = prep

    output = s3_rest_controller(rheader=s3db.member_rheader)
    return output

# -----------------------------------------------------------------------------
def person():
    """
        Person Controller
        - used for Personal Profile & Imports
        - includes components relevant to Membership
    """

    # Custom Method for Contacts
    s3mgr.model.set_method("pr", resourcename,
                           method="contacts",
                           action=s3db.pr_contacts)

    # CRUD pre-process
    def prep(r):
        if r.interactive and r.method != "import":
            resource = r.resource
            if resource.count() == 1:
                resource.load()
                r.record = resource.records().first()
                if r.record:
                    r.id = r.record.id
            if not r.record:
                session.error = T("Record not found")
                redirect(URL(f="membership",
                             #args=["search"]
                             ))
            member_id = request.get_vars.get("membership.id", None)
            if member_id and r.component_name == "membership":
                r.component_id = member_id
            s3mgr.configure("member_membership",
                            insertable = False)
        return True
    response.s3.prep = prep

    output = s3_rest_controller("pr", resourcename,
                                rheader=s3db.member_rheader)
    return output

# END =========================================================================
