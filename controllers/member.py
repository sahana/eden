# -*- coding: utf-8 -*-

"""
    Membership Management
"""

module = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# =============================================================================
def index():
    """ Dashboard """

    return s3db.cms_index(module, alt_function="index_alt")

# -----------------------------------------------------------------------------
def index_alt():
    """
        Module homepage for non-Admin users when no CMS content found
    """

    # Just redirect to the list of Members
    redirect(URL(f="membership"))

# =============================================================================
def membership_type():
    """
        REST Controller
    """

    if not auth.s3_has_role(ADMIN):
        s3.filter = auth.filter_by_root_org(s3db.member_membership_type)

    output = s3_rest_controller()
    return output

# =============================================================================
def membership():
    """
        REST Controller
    """

    tablename = "member_membership"
    table = s3db[tablename]

    def prep(r):
        if r.interactive:
            if r.id and r.component is None and r.method != "delete":
                # Redirect to person controller
                vars = {"membership.id": r.id}
                redirect(URL(f="person", vars=vars))
            else:
                # Assume members under 120
                s3db.pr_person.date_of_birth.widget = S3DateWidget(past=1440)
        return True
    s3.prep = prep

    def postp(r, output):
        if r.interactive and r.component is None:
            # Set the minimum end_date to the same as the start_date
            s3.jquery_ready.append(
'''S3.start_end_date('member_membership_start_date','member_membership_end_date')''')
        return output
    s3.postp = postp

    output = s3_rest_controller(rheader=s3db.member_rheader)
    return output

# =============================================================================
def person():
    """
        Person Controller
        - used for Personal Profile & Imports
        - includes components relevant to Membership
    """

    tablename = "pr_person"
    table = s3db.pr_person

    s3db.configure(tablename, deletable=False)
    s3.crud_strings[tablename].update(
            title_upload = T("Import Members"))

    s3db.configure("member_membership",
                   delete_next=URL("member", "membership"))

    # Custom Method for Contacts
    s3db.set_method("pr", resourcename,
                    method="contacts",
                    action=s3db.pr_contacts)

    # Upload for configuration (add replace option)
    s3.importerPrep = lambda: \
        dict(ReplaceOption=T("Remove existing data before import"))

    # Import pre-process
    def import_prep(data):
        """
            Deletes all Member records of the organisation
            before processing a new data import, used for the import_prep
            hook in s3mgr
        """
        resource, tree = data
        xml = current.xml
        tag = xml.TAG
        att = xml.ATTRIBUTE
        if s3.import_replace:
            if tree is not None:
                root = tree.getroot()
                expr = "/%s/%s[@%s='org_organisation']/%s[@%s='name']" % \
                       (tag.root, tag.resource, att.name, tag.data, att.field)
                orgs = root.xpath(expr)
                for org in orgs:
                    org_name = org.get("value", None) or org.text
                    if org_name:
                        try:
                            org_name = json.loads(xml.xml_decode(org_name))
                        except:
                            pass
                    if org_name:
                        mtable = s3db.member_membership
                        otable = s3db.org_organisation
                        query = (otable.name == org_name) & \
                                (mtable.organisation_id == otable.id)
                        resource = s3db.resource("member_membership", filter=query)
                        ondelete = s3db.get_config("member_membership", "ondelete")
                        resource.delete(ondelete=ondelete, format="xml", cascade=True)

    s3mgr.import_prep = import_prep

    # CRUD pre-process
    def prep(r):
        if r.interactive:
            if r.component_name == "membership":
                s3.crud_strings["member_membership"].update(
                    label_delete_button = T("Delete Membership"),
                    label_list_button = T("List Memberships")
                )

            if r.method != "import":
                if not r.component:
                    # Assume members under 120
                    s3db.pr_person.date_of_birth.widget = S3DateWidget(past=1440)
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
                s3db.configure("member_membership",
                                insertable = False)
        return True
    s3.prep = prep

    def postp(r, output):
        if r.interactive:
            if not r.component and "buttons" in output:
                # Provide correct list-button (non-native controller)
                buttons = output["buttons"]
                if "list_btn" in buttons:
                    crud_button = r.resource.crud.crud_button
                    buttons["list_btn"] = crud_button(None,
                                                tablename="member_membership",
                                                name="label_list_button",
                                                _href=URL(c="member", f="membership"),
                                                _id="list-btn")
            elif r.component_name == "membership":
                # Set the minimum end_date to the same as the start_date
                s3.jquery_ready.append(
'''S3.start_end_date('member_membership_start_date','member_membership_end_date')''')
        return output
    s3.postp = postp

    output = s3_rest_controller("pr", resourcename,
                                rheader=s3db.member_rheader,
                                replace_option=T("Remove existing data before import"))
    return output

# END =========================================================================
