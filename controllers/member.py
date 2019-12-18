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
    s3_redirect_default(URL(f="membership", args=["summary"]))

# =============================================================================
def membership_type():
    """
        REST Controller
    """

    if not auth.s3_has_role("ADMIN"):
        s3.filter = auth.filter_by_root_org(s3db.member_membership_type)

    output = s3_rest_controller()
    return output

# =============================================================================
def membership():
    """
        REST Controller
    """

    def prep(r):
        if r.interactive:
            if s3.rtl:
                # Ensure that + appears at the beginning of the number
                # - using table alias to only apply to filtered component
                from s3 import s3_phone_represent, S3PhoneWidget
                f = s3db.get_aliased(s3db.pr_contact, "pr_phone_contact").value
                f.represent = s3_phone_represent
                f.widget = S3PhoneWidget()

            if r.id and r.component is None and r.method != "delete":
                # Redirect to person controller
                vars = {"membership.id": r.id}
                redirect(URL(f="person", vars=vars))

            # Assume members under 120
            s3db.pr_person.date_of_birth.widget = \
                                        S3CalendarWidget(past_months=1440)

        elif r.representation == "xls":
            # Split person_id into first/middle/last to make it match Import sheets
            list_fields = s3db.get_config("member_membership",
                                          "list_fields")
            list_fields.remove("person_id")
            list_fields = ["person_id$first_name",
                           "person_id$middle_name",
                           "person_id$last_name",
                           ] + list_fields

            s3db.configure("member_membership",
                           list_fields = list_fields)

        return True
    s3.prep = prep

    return s3_rest_controller(rheader = s3db.member_rheader)

# =============================================================================
def person():
    """
        Person Controller
        - used for Personal Profile & Imports
        - includes components relevant to Membership
    """

    tablename = "pr_person"
    table = s3db.pr_person

    s3db.configure(tablename,
                   deletable = False,
                   )

    s3.crud_strings[tablename].update(
            title_upload = T("Import Members"))

    s3db.configure("member_membership",
                   delete_next = URL("member", "membership"),
                   )

    # Custom Method for Contacts
    set_method = s3db.set_method
    set_method("pr", resourcename,
               method = "contacts",
               action = s3db.pr_Contacts)

    # Custom Method for CV
    set_method("pr", "person",
               method = "cv",
               # @ToDo: Allow Members to have a CV without enabling HRM?
               action = s3db.hrm_CV)

    # Upload for configuration (add replace option)
    s3.importerPrep = lambda: \
        dict(ReplaceOption=T("Remove existing data before import"))

    # Import pre-process
    def import_prep(data):
        """
            Deletes all Member records of the organisation/branch
            before processing a new data import
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
                        # Use cascade=True so that the deletion gets
                        # rolled back if the import fails:
                        resource.delete(format="xml", cascade=True)

    s3.import_prep = import_prep

    # CRUD pre-process
    def prep(r):
        if r.interactive:
            if s3.rtl:
                # Ensure that + appears at the beginning of the number
                # - using table alias to only apply to filtered component
                from s3 import s3_phone_represent, S3PhoneWidget
                f = s3db.get_aliased(s3db.pr_contact, "pr_phone_contact").value
                f.represent = s3_phone_represent
                f.widget = S3PhoneWidget()

            if r.component_name == "membership":
                s3.crud_strings["member_membership"].update(
                    label_delete_button = T("Delete Membership"),
                    label_list_button = T("List Memberships")
                )

            if r.method not in ("import", "search_ac", "validate"):
                if not r.component:
                    # Assume members under 120
                    s3db.pr_person.date_of_birth.widget = \
                                        S3CalendarWidget(past_months=1440)
                resource = r.resource
                if resource.count() == 1:
                    resource.load()
                    r.record = resource.records().first()
                    if r.record:
                        r.id = r.record.id
                if not r.record:
                    session.error = T("Record not found")
                    redirect(URL(f="membership"))
                member_id = get_vars.get("membership.id", None)
                if member_id and r.component_name == "membership":
                    r.component_id = member_id
                s3db.configure("member_membership",
                               insertable = False,
                               )
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
        return output
    s3.postp = postp

    output = s3_rest_controller("pr", resourcename,
                                replace_option = T("Remove existing data before import"),
                                rheader = s3db.member_rheader,
                                )
    return output

# END =========================================================================
