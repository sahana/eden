# -*- coding: utf-8 -*-

""" Sahana Eden Person Registry Model

    @author: Dominic König <dominic[at]aidiq.com>

    @copyright: 2009-2012 (c) Sahana Software Foundation
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

__all__ = ["S3PersonEntity",
           "S3OrgAuthModel",
           "S3PersonModel",
           "S3GroupModel",
           "S3ContactModel",
           "S3PersonAddressModel",
           "S3PersonImageModel",
           "S3PersonIdentityModel",
           "S3SavedSearch",
           "S3PersonPresence",
           "S3PersonDescription",
            # Representation Methods
           "pr_pentity_represent",
           "pr_person_represent",
           "pr_person_comment",
           "pr_rheader",
            # Custom Resource Methods
           "pr_contacts",
           "pr_profile",
            # Hierarchy Manipulation
           "pr_update_affiliations",
           "pr_add_affiliation",
           "pr_remove_affiliation",
            # PE Helpers
           "pr_get_pe_id",
            # Back-end Role Tools
           "pr_define_role",
           "pr_delete_role",
           "pr_add_to_role",
           "pr_remove_from_role",
            # Hierarchy Lookup
           "pr_get_role_paths",
           "pr_get_role_branches",
           "pr_get_path",
           "pr_get_ancestors",
           "pr_get_descendants",
            # Internal Path Tools
           "pr_rebuild_path",
           "pr_role_rebuild_path"]

import gluon.contrib.simplejson as json

from gluon import *
from gluon.dal import Row
from gluon.storage import Storage
from gluon.sqlhtml import RadioWidget
from ..s3 import *
from layouts import *

OU = 1 # role type which indicates hierarchy, see role_types
OTHER_ROLE = 9

# =============================================================================
class S3PersonEntity(S3Model):
    """ Person Super-Entity """

    names = ["pr_pentity",
             "pr_affiliation",
             "pr_role",
             "pr_role_types",
             "pr_role_id",
             "pr_pe_label",
             "pr_pe_types"]

    def model(self):

        db = current.db
        T = current.T
        s3 = current.response.s3

        add_component = self.add_component
        configure = self.configure
        crud_strings = s3.crud_strings
        define_table = self.define_table
        meta_fields= s3.meta_fields
        super_entity = self.super_entity
        super_key = self.super_key
        super_link = self.super_link

        YES = T("yes") #current.messages.YES
        NO = T("no") #current.messages.NO
        UNKNOWN_OPT = current.messages.UNKNOWN_OPT

        # ---------------------------------------------------------------------
        # Person Super-Entity
        #
        #if current.deployment_settings.get_ui_camp():
        #    shelter = T("Camp")
        #else:
        #    shelter = T("Shelter")
        pe_types = Storage(pr_person = T("Person"),
                           pr_group = T("Group"),
                           org_organisation = T("Organization"),
                           org_office = T("Office"),
                           # If we want these, then pe_id needs adding to their
                           # tables & configuring as a super-entity
                           #cr_shelter = shelter,
                           #fire_station = T("Fire Station"),
                           #hms_hospital = T("Hospital"),
                           dvi_body = T("Body"))

        tablename = "pr_pentity"
        table = super_entity(tablename, "pe_id", pe_types,
                             Field("type"),
                             Field("pe_label", length=128))

        # Search method
        pentity_search = S3PentitySearch(name = "pentity_search_simple",
                                         label = T("Name and/or ID"),
                                         comment = T(""),
                                         field = ["pe_label"])

        pentity_search.pentity_represent = pr_pentity_represent

        # Resource configuration
        configure(tablename,
                  editable=False,
                  deletable=False,
                  listadd=False,
                  onaccept=self.pr_pentity_onaccept,
                  search_method=pentity_search)

        # Reusable fields
        pr_pe_label = S3ReusableField("pe_label", length=128,
                                      label = T("ID Tag Number"),
                                      requires = IS_NULL_OR(IS_NOT_ONE_OF(db,
                                                            "pr_pentity.pe_label")))

        # Components
        pe_id = super_key(table)
        add_component("pr_contact_emergency", pr_pentity=pe_id)
        add_component("pr_address", pr_pentity=pe_id)
        add_component("pr_image", pr_pentity=pe_id)
        add_component("pr_contact", pr_pentity=pe_id)
        add_component("pr_note", pr_pentity=pe_id)
        add_component("pr_physical_description",
                      pr_pentity=dict(joinby=pe_id,
                                      multiple=False))
        add_component("dvi_identification",
                      pr_pentity=dict(joinby=pe_id,
                                      multiple=False))
        add_component("dvi_effects",
                      pr_pentity=dict(joinby=pe_id,
                                      multiple=False))
        add_component("dvi_checklist",
                      pr_pentity=dict(joinby=pe_id,
                                      multiple=False))
        # Map Configs
        #   - Personalised configurations
        #   - OU configurations (Organisation/Branch/Facility/Team)
        add_component("gis_config",
                      pr_pentity=dict(joinby=pe_id,
                                      multiple=False))

        # ---------------------------------------------------------------------
        # Person <-> User
        #
        utable = current.auth.settings.table_user
        tablename = "pr_person_user"
        table = define_table(tablename,
                             super_link("pe_id", "pr_pentity"),
                             Field("user_id", utable),
                             *meta_fields())

        # ---------------------------------------------------------------------
        # Role (Affiliates Group)
        #
        role_types = {
            1:T("Organizational Units"),  # business hierarchy (reporting units)
            2:T("Membership"),            # membership role
            3:T("Association"),           # other non-reporting role
            9:T("Other")                  # other role type
        }
        tablename = "pr_role"
        table = define_table(tablename,
                             # The "parent" entity
                             super_link("pe_id", "pr_pentity",
                                        label=T("Corporate Entity"),
                                        readable=True,
                                        writable=True),
                             # Role type
                             Field("role_type", "integer",
                                   requires = IS_IN_SET(role_types, zero=None),
                                   represent = lambda opt: \
                                               role_types.get(opt, UNKNOWN_OPT)),
                             # Role name
                             Field("role", notnull=True),
                             # Path, for faster lookups
                             Field("path",
                                   readable = False,
                                   writable = False),
                             # Type filter, type of entities which can have this role
                             Field("entity_type", "string",
                                   requires = IS_EMPTY_OR(IS_IN_SET(pe_types, zero=T("ANY"))),
                                   represent = lambda opt: pe_types.get(opt, UNKNOWN_OPT)),
                             # Subtype filter, if the entity type defines its own type
                             Field("sub_type", "integer",
                                   readable = False,
                                   writable = False),
                             *meta_fields())

        # Field configuration
        table.pe_id.requires = IS_ONE_OF(db, "pr_pentity.pe_id",
                                         pr_pentity_represent, sort=True)
        table.pe_id.represent = pr_pentity_represent

        # CRUD Strings
        crud_strings[tablename] = Storage(
            title_create = T("Add Role"),
            title_display = T("Role Details"),
            title_list = T("Roles"),
            title_update = T("Edit Role"),
            title_search = T("Search Roles"),
            subtitle_create = T("Add New Role"),
            subtitle_list = T("List of Roles"),
            label_list_button = T("List Roles"),
            label_create_button = T("Add Role"),
            label_delete_button = T("Delete Role"),
            msg_record_created = T("Role added"),
            msg_record_modified = T("Role updated"),
            msg_record_deleted = T("Role deleted"),
            msg_list_empty = T("No Roles defined"))

        # Resource configuration
        configure(tablename,
                  onvalidation=self.pr_role_onvalidation)

        # Reusable fields
        role_id = S3ReusableField("role_id", db.pr_role,
                                  requires = IS_ONE_OF(db, "pr_role.id",
                                                       self.pr_role_represent),
                                  represent = self.pr_role_represent,
                                  label = T("Role"),
                                  ondelete = "CASCADE")

        # ---------------------------------------------------------------------
        # Affiliation
        #
        tablename = "pr_affiliation"
        table = define_table(tablename,
                             role_id(),
                             super_link("pe_id", "pr_pentity",
                                        label=T("Entity"),
                                        readable=True,
                                        writable=True),
                             *meta_fields())

        table.pe_id.requires = IS_ONE_OF(db, "pr_pentity.pe_id",
                                         pr_pentity_represent, sort=True)
        table.pe_id.represent = pr_pentity_represent

        # CRUD Strings
        crud_strings[tablename] = Storage(
            title_create = T("Add Affiliation"),
            title_display = T("Affiliation Details"),
            title_list = T("Affiliations"),
            title_update = T("Edit Affiliation"),
            title_search = T("Search Affiliations"),
            subtitle_create = T("Add New Affiliation"),
            subtitle_list = T("List of Affiliations"),
            label_list_button = T("List Affiliations"),
            label_create_button = T("Add Affiliation"),
            label_delete_button = T("Delete Affiliation"),
            msg_record_created = T("Affiliation added"),
            msg_record_modified = T("Affiliation updated"),
            msg_record_deleted = T("Affiliation deleted"),
            msg_list_empty = T("No Affiliations defined"))

        # Resource configuration
        configure(tablename,
                  onaccept=self.pr_affiliation_onaccept,
                  ondelete=self.pr_affiliation_ondelete)

        # ---------------------------------------------------------------------
        # Return model-global names to response.s3
        #
        return Storage(
            pr_pe_types=pe_types,
            pr_pe_label=pr_pe_label,
            pr_role_types=role_types,
            pr_role_id=role_id,
        )

    # -------------------------------------------------------------------------
    @staticmethod
    def pr_role_represent(role_id):
        """
            Represent an entity role

            @param role_id: the pr_role record ID
        """

        db = current.db
        s3db = current.s3db

        table = s3db.pr_role
        role = db(table.id == role_id).select(table.role,
                                              table.pe_id,
                                              limitby=(0, 1)).first()
        if role:
            entity = pr_pentity_represent(role.pe_id)
            return "%s: %s" % (entity, role.role)
        else:
            return current.messages.NONE

    # -------------------------------------------------------------------------
    @staticmethod
    def pr_role_onvalidation(form):
        """
            Clear descendant paths if role type has changed

            @param form: the CRUD form
        """

        db = current.db
        s3db = current.s3db

        formvars = form.vars
        if not formvars:
            return
        if "role_type" in formvars:
            role_id = form.record_id
            if not role_id:
                return
            role_type = formvars.role_type
            rtable = s3db.pr_role
            role = db(rtable.id == role_id).select(rtable.role_type,
                                                   limitby=(0, 1)).first()
            if role and str(role.role_type) != str(role_type):
                # If role type has changed, then clear paths
                if str(role_type) != str(OU):
                    formvars["path"] = None
                s3db.pr_role_rebuild_path(role_id, clear=True)
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def pr_pentity_onaccept(form):
        """
            Update organisation affiliations for org_site instances.
        """

        db = current.db
        s3db = current.s3db

        ptable = s3db.pr_pentity

        pe_id = form.vars.pe_id
        pe = db(ptable.pe_id == pe_id).select(ptable.instance_type,
                                              limitby=(0, 1)).first()
        if pe:
            itable = s3db.table(pe.instance_type, None)
            if itable and \
               "site_id" in itable.fields and \
               "organisation_id" in itable.fields:
                q = itable.pe_id == pe_id
                instance = db(q).select(itable.pe_id,
                                        itable.organisation_id,
                                        limitby=(0, 1)).first()
                if instance:
                    s3db.pr_update_affiliations("org_site", instance)
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def pr_affiliation_onaccept(form):
        """
            Remove duplicate affiliations and clear descendant paths (to
            trigger lazy rebuild)

            @param form: the CRUD form
        """

        db = current.db
        s3db = current.s3db
        manager = current.manager

        atable = s3db.pr_affiliation

        formvars = form.vars
        role_id = formvars["role_id"]
        pe_id = formvars["pe_id"]
        record_id = formvars["id"]

        if role_id and pe_id and record_id:
            # Remove duplicates
            query = (atable.id != record_id) & \
                    (atable.role_id == role_id) & \
                    (atable.pe_id == pe_id)
            deleted_fk = {"role_id": role_id, "pe_id": pe_id}
            data = {"deleted": True,
                    "role_id": None,
                    "pe_id": None,
                    "deleted_fk": json.dumps(deleted_fk)}
            db(query).update(**data)
            # Clear descendant paths
            s3db.pr_rebuild_path(pe_id, clear=True)
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def pr_affiliation_ondelete(row):
        """
            Clear descendant paths, also called indirectly via
            ondelete-CASCADE when a role gets deleted.

            @param row: the deleted row
        """

        db = current.db
        s3db = current.s3db

        atable = s3db.pr_affiliation

        if row and row.id:
            query = atable.id == row.id
            record = db(query).select(atable.deleted_fk,
                                      limitby=(0, 1)).first()
        else:
            return
        if record:
            data = json.loads(record.deleted_fk)
            pe_id = data.get("pe_id", None)
            if pe_id:
                s3db.pr_rebuild_path(pe_id, clear=True)
        return

# =============================================================================
class S3OrgAuthModel(S3Model):
    """ Organisation-based Authorization Model """

    names = ["pr_restriction", "pr_delegation"]

    def model(self):

        auth = current.auth
        s3 = current.response.s3
        role_id = current.s3db.pr_role_id

        define_table = self.define_table
        super_link = self.super_link
        meta_fields = s3.meta_fields

        # ---------------------------------------------------------------------
        # Restriction: Person Entity <-> Auth Membership Link
        # This restricts the permissions assigned by an auth-group membership
        # to the records owned by this person entity.
        #
        mtable = auth.settings.table_membership
        tablename = "pr_restriction"
        table = define_table(tablename,
                             super_link("pe_id", "pr_pentity"),
                             Field("membership_id", mtable,
                                   ondelete="CASCADE"),
                             *meta_fields())

        # ---------------------------------------------------------------------
        # Delegation: Role <-> Auth Group Link
        # This "delegates" the permissions of a user group for the records
        # owned by a person entity to a group of affiliated entities.
        #
        gtable = auth.settings.table_group
        tablename = "pr_delegation"
        table = define_table(tablename,
                             role_id(),
                             Field("group_id", gtable,
                                   ondelete="CASCADE"),
                             *meta_fields())

        # ---------------------------------------------------------------------
        return Storage()

# =============================================================================
class S3PersonModel(S3Model):
    """ Persons and Groups """

    names = ["pr_person",
             "pr_person_user",
             "pr_gender",
             "pr_gender_opts",
             "pr_age_group",
             "pr_age_group_opts",
             "pr_person_id",
            ]

    def model(self):

        T = current.T
        db = current.db
        request = current.request
        s3 = current.response.s3
        gis = current.gis
        settings = current.deployment_settings

        pe_label = self.pr_pe_label

        location_id = self.gis_location_id

        messages = current.messages
        UNKNOWN_OPT = messages.UNKNOWN_OPT
        SELECT_LOCATION = messages.SELECT_LOCATION

        define_table = self.define_table
        super_link = self.super_link
        add_component = self.add_component

        # ---------------------------------------------------------------------
        # Person
        #
        pr_gender_opts = {
            1:"",
            2:T("female"),
            3:T("male")
        }
        pr_gender = S3ReusableField("gender", "integer",
                                    requires = IS_IN_SET(pr_gender_opts, zero=None),
                                    default = 1,
                                    label = T("Gender"),
                                    represent = lambda opt: \
                                                pr_gender_opts.get(opt, UNKNOWN_OPT))

        pr_age_group_opts = {
            1:T("unknown"),
            2:T("Infant (0-1)"),
            3:T("Child (2-11)"),
            4:T("Adolescent (12-20)"),
            5:T("Adult (21-50)"),
            6:T("Senior (50+)")
        }
        pr_age_group = S3ReusableField("age_group", "integer",
                                       requires = IS_IN_SET(pr_age_group_opts,
                                                            zero=None),
                                       default = 1,
                                       label = T("Age Group"),
                                       represent = lambda opt: \
                                                   pr_age_group_opts.get(opt,
                                                                         UNKNOWN_OPT))

        pr_marital_status_opts = {
            1:T("unknown"),
            2:T("single"),
            3:T("married"),
            4:T("separated"),
            5:T("divorced"),
            6:T("widowed"),
            9:T("other")
        }

        pr_religion_opts = settings.get_L10n_religions()

        pr_impact_tags = {
            1: T("injured"),
            4: T("diseased"),
            2: T("displaced"),
            5: T("separated from family"),
            3: T("suffered financial losses")
        }

        if settings.get_L10n_mandatory_lastname():
            last_name_validate = IS_NOT_EMPTY(error_message = T("Please enter a last name"))
        else:
            last_name_validate = None

        s3_date_format = settings.get_L10n_date_format()

        tablename = "pr_person"
        table = define_table(tablename,
                             super_link("pe_id", "pr_pentity"),
                             super_link("track_id", "sit_trackable"),
                             location_id(readable=False,
                                         writable=False),       # base location
                             pe_label(comment = DIV(DIV(_class="tooltip",
                                                        _title="%s|%s" % (T("ID Tag Number"),
                                                                          T("Number or Label on the identification tag this person is wearing (if any)."))))),
                             Field("missing", "boolean",
                                   readable=False,
                                   writable=False,
                                   default=False,
                                   represent = lambda missing: \
                                               (missing and ["missing"] or [""])[0]),
                             Field("volunteer", "boolean",
                                   readable=False,
                                   writable=False,
                                   default=False),
                             Field("first_name",
                                   notnull=True,
                                   default = "?" if current.auth.permission.format != "html" else "",
                                   length=64, # Mayon Compatibility
                                   # NB Not possible to have an IS_NAME() validator here
                                   # http://eden.sahanafoundation.org/ticket/834
                                   requires = IS_NOT_EMPTY(error_message = T("Please enter a first name")),
                                   comment =  DIV(_class="tooltip",
                                                  _title="%s|%s" % (T("First name"),
                                                                    T("The first or only name of the person (mandatory)."))),
                                   label = T("First Name")),
                             Field("middle_name",
                                   length=64, # Mayon Compatibility
                                   label = T("Middle Name")),
                             Field("last_name",
                                   length=64, # Mayon Compatibility
                                   label = T("Last Name"),
                                   requires = last_name_validate),
                             Field("initials",
                                   length=8,
                                   label = T("Initials")),
                             Field("preferred_name",
                                   label = T("Preferred Name"),
                                   comment = DIV(DIV(_class="tooltip",
                                                     _title="%s|%s" % (T("Preferred Name"),
                                                                       T("The name to be used when calling for or directly addressing the person (optional).")))),
                                   length=64), # Mayon Compatibility
                             Field("local_name",
                                   label = T("Local Name"),
                                    comment = DIV(DIV(_class="tooltip",
                                                        _title="%s|%s" % (T("Local Name"),
                                                                        T("Name of the person in local language and script (optional)."))))),
                             pr_gender(label = T("Gender")),
                             Field("date_of_birth", "date",
                                   label = T("Date of Birth"),
                                   requires = [IS_EMPTY_OR(IS_DATE_IN_RANGE(
                                                format = s3_date_format,
                                                maximum=request.utcnow.date(),
                                                error_message="%s %%(max)s!" %
                                                              T("Enter a valid date before")))],
                                   widget = S3DateWidget(past=1320,  # Months, so 110 years
                                                         future=0)),
                             pr_age_group(label = T("Age group")),
                             Field("nationality",
                                   requires = IS_NULL_OR(IS_IN_SET_LAZY(
                                                lambda: gis.get_countries(key_type="code"),
                                                zero = SELECT_LOCATION)),
                                   label = T("Nationality"),
                                   comment = DIV(DIV(_class="tooltip",
                                                     _title="%s|%s" % (T("Nationality"),
                                                                       T("Nationality of the person.")))),
                                   represent = lambda code: \
                                               gis.get_country(code, key_type="code") or UNKNOWN_OPT),
                             Field("occupation",
                                   label = T("Profession"),
                                   length=128), # Mayon Compatibility
                             # Field("picture", "upload",
                                   # autodelete=True,
                                   # label = T("Picture"),
                                   # requires = IS_EMPTY_OR(IS_IMAGE(maxsize=(800, 800),
                                                                   # error_message=T("Upload an image file (bmp, gif, jpeg or png), max. 800x800 pixels!"))),
                                   # represent = lambda image: image and \
                                                        # DIV(A(IMG(_src=URL(c="default", f="download",
                                                                           # args=image),
                                                                  # _height=60,
                                                                  # _alt=T("View Picture")),
                                                                  # _href=URL(c="default", f="download",
                                                                            # args=image))) or
                                                            # T("No Picture"),
                                   # comment = DIV(_class="tooltip",
                                                 # _title="%s|%s" % (T("Picture"),
                                                                   # T("Upload an image file here.")))),
                             Field("opt_in",
                                   "string", # list of mailing lists which link to teams
                                   default=False,
                                   label = T("Receive updates"),
                                   comment = DIV(DIV(_class="tooltip",
                                                     _title="%s|%s" % (T("Mailing list"),
                                                                       T("By selecting this you agree that we may contact you.")))),
                                   ),
                             s3.comments(),
                             *(s3.lx_fields() + s3.meta_fields()))

        # CRUD Strings
        ADD_PERSON = current.messages.ADD_PERSON
        LIST_PERSONS = T("List Persons")
        s3.crud_strings[tablename] = Storage(
            title_create = T("Add a Person"),
            title_display = T("Person Details"),
            title_list = LIST_PERSONS,
            title_update = T("Edit Person Details"),
            title_search = T("Search Persons"),
            subtitle_create = ADD_PERSON,
            subtitle_list = T("Persons"),
            label_list_button = LIST_PERSONS,
            label_create_button = ADD_PERSON,
            label_delete_button = T("Delete Person"),
            msg_record_created = T("Person added"),
            msg_record_modified = T("Person details updated"),
            msg_record_deleted = T("Person deleted"),
            msg_list_empty = T("No Persons currently registered"))

        # add an opt in clause to receive emails depending on the deployment settings
        if current.deployment_settings.get_auth_opt_in_to_email():
            table.opt_in.readable = True
            table.opt_in.writable = True
        else:
            table.opt_in.readable = False
            table.opt_in.writable = False

        # Search method
        pr_person_search = S3PersonSearch(
                                name="person_search_simple",
                                label=T("Name and/or ID"),
                                comment=T("To search for a person, enter any of the first, middle or last names and/or an ID number of a person, separated by spaces. You may use % as wildcard. Press 'Search' without input to list all persons."),
                                field=["pe_label",
                                       "first_name",
                                       "middle_name",
                                       "last_name",
                                       "local_name",
                                       #"identity.value"
                                      ])

        # Resource configuration
        self.configure(tablename,
                       super_entity=("pr_pentity", "sit_trackable"),
                       list_fields = ["id",
                                      "first_name",
                                      "middle_name",
                                      "last_name",
                                      #"picture",
                                      "gender",
                                      "age_group",
                                      (T("Organization"), "hrm_human_resource:organisation_id$name")
                                     ],
                       onvalidation=self.pr_person_onvalidation,
                       search_method=pr_person_search,
                       deduplicate=self.person_deduplicate,
                       main="first_name",
                       extra="last_name")

        person_id_comment = pr_person_comment(
                                    T("Person"),
                                    T("Type the first few characters of one of the Person's names."),
                                    child="person_id")

        person_id = S3ReusableField("person_id", db.pr_person,
                                    sortby = ["first_name", "middle_name", "last_name"],
                                    requires = IS_NULL_OR(IS_ONE_OF(db, "pr_person.id",
                                                                    pr_person_represent,
                                                                    orderby="pr_person.first_name",
                                                                    sort=True,
                                                                    error_message=T("Person must be specified!"))),
                                    represent = pr_person_represent,
                                    label = T("Person"),
                                    comment = person_id_comment,
                                    ondelete = "RESTRICT",
                                    widget = S3PersonAutocompleteWidget())

        # Components
        add_component("pr_group_membership", pr_person="person_id")
        add_component("pr_identity", pr_person="person_id")
        add_component("pr_save_search", pr_person="person_id")
        add_component("msg_subscription", pr_person="person_id")

        # HR Record as component of Persons
        add_component("hrm_human_resource", pr_person="person_id")
        add_component("member_membership", pr_person="person_id")

        # Skills as components of Persons
        add_component("hrm_certification", pr_person="person_id")
        add_component("hrm_competency", pr_person="person_id")
        add_component("hrm_credential", pr_person="person_id")
        add_component("hrm_experience", pr_person="person_id")
        # @ToDo: Double link table to show the Courses attended?
        add_component("hrm_training", pr_person="person_id")

        # Assets as component of persons
        add_component("asset_asset", pr_person="assigned_to_id")

        # ---------------------------------------------------------------------
        # Return model-global names to response.s3
        #
        return Storage(
            pr_gender = pr_gender,
            pr_gender_opts = pr_gender_opts,
            pr_age_group = pr_age_group,
            pr_age_group_opts = pr_age_group_opts,
            pr_person_id = person_id,
        )

    # -------------------------------------------------------------------------
    @staticmethod
    def pr_person_onvalidation(form):
        """ Onvalidation callback """

        try:
            age = int(form.vars.get("age_group", None))
        except (ValueError, TypeError):
            age = None
        dob = form.vars.get("date_of_birth", None)

        if age and age != 1 and dob:
            now = request.utcnow
            dy = int((now.date() - dob).days / 365.25)
            if dy < 0:
                ag = 1
            elif dy < 2:
                ag = 2
            elif dy < 12:
                ag = 3
            elif dy < 21:
                ag = 4
            elif dy < 51:
                ag = 5
            else:
                ag = 6

            if age != ag:
                form.errors.age_group = T("Age group does not match actual age.")
                return False

        return True

    # -------------------------------------------------------------------------
    @staticmethod
    def person_deduplicate(item):
        """ Import item deduplication """

        db = current.db
        s3db = current.s3db

        # Ignore this processing if the id is set
        if item.id:
            return
        if item.tablename == "pr_person":
            ptable = s3db.pr_person
            ctable = s3db.pr_contact

            # Match by first name and last name, and if given, by email address
            fname = "first_name" in item.data and item.data.first_name
            lname = "last_name" in item.data and item.data.last_name
            if fname and lname:
                # "LIKE" is inappropriate here:
                # E.g. "Fran Boon" would overwrite "Frank Boones"
                #query = (ptable.first_name.lower().like('%%%s%%' % fname.lower())) & \
                        #(ptable.last_name.lower().like('%%%s%%' % lname.lower()))

                # But even an exact name match does not necessarily indicate a
                # duplicate: depending on the scope of the deployment, you could
                # have thousands of people with exactly the same names (or just
                # two of them - and it can already go wrong).
                # We take the email address as additional criterion, however, where
                # person data do not usually contain email addresses you might need
                # to add more/other criteria here
                query = (ptable.first_name.lower() == fname.lower()) & \
                        (ptable.last_name.lower() == lname.lower())
                email = False
                for citem in item.components:
                    if citem.tablename == "pr_contact":
                        if "contact_method" in citem.data and \
                        citem.data.contact_method == "EMAIL":
                            email = citem.data.value
                if email != False:
                    query = query & \
                            (ptable.pe_id == ctable.pe_id) & \
                            (ctable.value.lower() == email.lower())

            else:
                # Try Initials (this is a weak test but works well in small teams)
                initials = "initials" in item.data and item.data.initials
                if not initials:
                    # Nothing we can do
                    return
                query = (ptable.initials.lower() == initials.lower())

            # Look for details on the database
            _duplicate = db(query).select(ptable.id,
                                          limitby=(0, 1)).first()
            if _duplicate:
                item.id = _duplicate.id
                item.data.id = _duplicate.id
                item.method = item.METHOD.UPDATE
                for citem in item.components:
                    citem.method = citem.METHOD.UPDATE

# =============================================================================
class S3GroupModel(S3Model):
    """ Groups """

    names = ["pr_group",
             "pr_group_id",
             "pr_group_represent",
             "pr_group_membership"]

    def model(self):

        T = current.T
        db = current.db
        request = current.request
        s3 = current.response.s3

        person_id = self.pr_person_id

        messages = current.messages
        NONE = messages.NONE
        UNKNOWN_OPT = messages.UNKNOWN_OPT

        comments = s3.comments
        configure = self.configure
        crud_strings = s3.crud_strings
        define_table = self.define_table
        meta_fields = s3.meta_fields

        # ---------------------------------------------------------------------
        # Group
        #
        pr_group_types = {
            1:T("Family"),
            2:T("Tourist Group"),
            3:T("Relief Team"),
            4:T("other"),
            5:T("Mailing Lists"),
        }

        tablename = "pr_group"
        table = define_table(tablename,
                             self.super_link("pe_id", "pr_pentity"),
                             Field("group_type", "integer",
                                   requires = IS_IN_SET(pr_group_types, zero=None),
                                   default = 4,
                                   label = T("Group Type"),
                                   represent = lambda opt: \
                                               pr_group_types.get(opt, UNKNOWN_OPT)),
                             Field("system", "boolean",
                                   default=False,
                                   readable=False,
                                   writable=False),
                             Field("name",
                                   label=T("Group Name"),
                                   requires = IS_NOT_EMPTY()),
                             Field("description",
                                   label=T("Group Description")),
                             comments(),
                             *meta_fields())

        # Field configuration
        table.description.comment = DIV(DIV(_class="tooltip",
                                            _title="%s|%s" % (T("Group description"),
                                                              T("A brief description of the group (optional)"))))

        # CRUD Strings
        ADD_GROUP = T("Add Group")
        LIST_GROUPS = T("List Groups")
        crud_strings[tablename] = Storage(
            title_create = ADD_GROUP,
            title_display = T("Group Details"),
            title_list = LIST_GROUPS,
            title_update = T("Edit Group"),
            title_search = T("Search Groups"),
            subtitle_create = T("Add New Group"),
            subtitle_list = T("Groups"),
            label_list_button = LIST_GROUPS,
            label_create_button = ADD_GROUP,
            label_delete_button = T("Delete Group"),
            msg_record_created = T("Group added"),
            msg_record_modified = T("Group updated"),
            msg_record_deleted = T("Group deleted"),
            msg_list_empty = T("No Groups currently registered"))

        # CRUD Strings
        ADD_GROUP = T("Add Mailing List")
        LIST_GROUPS = T("Mailing List")
        mailing_list_crud_strings = Storage(
            title_create = ADD_GROUP,
            title_display = T("Mailing List Details"),
            title_list = LIST_GROUPS,
            title_update = T("Edit Mailing List"),
            title_search = T("Search Mailing Lists"),
            subtitle_create = T("Add New Mailing List"),
            subtitle_list = T("Mailing Lists"),
            label_list_button = LIST_GROUPS,
            label_create_button = ADD_GROUP,
            label_delete_button = T("Delete Mailing List"),
            msg_record_created = T("Mailing list added"),
            msg_record_modified = T("Mailing list updated"),
            msg_record_deleted = T("Mailing list deleted"),
            msg_list_empty = T("No Mailing List currently established"))

        # Resource configuration
        configure(tablename,
                  super_entity="pr_pentity",
                  deduplicate=self.group_deduplicate,
                  main="name",
                  extra="description")

        # Reusable fields
        group_represent = lambda id: (id and [db.pr_group[id].name] or [NONE])[0]
        group_id = S3ReusableField("group_id", db.pr_group,
                                   sortby="name",
                                   requires = IS_NULL_OR(IS_ONE_OF(db, "pr_group.id",
                                                                   "%(id)s: %(name)s",
                                                                   filterby="system",
                                                                   filter_opts=(False,))),
                                   represent = group_represent,
                                    comment = \
                                        DIV(A(s3.crud_strings.pr_group.label_create_button,
                                              _class="colorbox",
                                              _href=URL(c="pr", f="group", args="create",
                                                        vars=dict(format="popup")),
                                              _target="top",
                                              _title=s3.crud_strings.pr_group.label_create_button),
                                            DIV(DIV(_class="tooltip",
                                                    _title="%s|%s" % (T("Create Group Entry"),
                                                                      T("Create a group entry in the registry."))))),
                                   ondelete = "RESTRICT")

        # Components
        self.add_component("pr_group_membership", pr_group="group_id")

        # ---------------------------------------------------------------------
        # Group membership
        #
        resourcename = "group_membership"
        tablename = "pr_group_membership"
        table = define_table(tablename,
                             group_id(label = T("Group"),
                                      ondelete="CASCADE"),
                             person_id(label = T("Person"),
                                       ondelete="CASCADE"),
                             Field("group_head", "boolean",
                                   label = T("Group Head"),
                                   default=False),
                             Field("description",
                                   label = T("Description")),
                             comments(),
                             *meta_fields())

        # Field configuration
        table.group_head.represent = lambda group_head: \
                                        (group_head and [T("yes")] or [""])[0]

        # CRUD strings
        request = current.request
        if request.function in ("person", "group_membership"):
            crud_strings[tablename] = Storage(
                title_create = T("Add Membership"),
                title_display = T("Membership Details"),
                title_list = T("Memberships"),
                title_update = T("Edit Membership"),
                title_search = T("Search Membership"),
                subtitle_create = T("Add New Membership"),
                subtitle_list = T("Current Memberships"),
                label_list_button = T("List All Memberships"),
                label_create_button = T("Add Membership"),
                label_delete_button = T("Delete Membership"),
                msg_record_created = T("Membership added"),
                msg_record_modified = T("Membership updated"),
                msg_record_deleted = T("Membership deleted"),
                msg_list_empty = T("No Memberships currently registered"))

        elif request.function == "group":
            crud_strings[tablename] = Storage(
                title_create = T("Add Member"),
                title_display = T("Membership Details"),
                title_list = T("Group Members"),
                title_update = T("Edit Membership"),
                title_search = T("Search Member"),
                subtitle_create = T("Add New Member"),
                subtitle_list = T("Current Group Members"),
                label_list_button = T("List Members"),
                label_create_button = T("Add Group Member"),
                label_delete_button = T("Delete Membership"),
                msg_record_created = T("Group Member added"),
                msg_record_modified = T("Membership updated"),
                msg_record_deleted = T("Membership deleted"),
                msg_list_empty = T("No Members currently registered"))

        # Resource configuration
        configure(tablename,
                  onaccept = self.group_membership_onaccept,
                  ondelete = self.group_membership_onaccept,
                  list_fields=["id",
                               "group_id",
                               "person_id",
                               "group_head",
                               "description"
                              ])

        # ---------------------------------------------------------------------
        # Return model-global names to response.s3
        #
        return Storage(
            pr_group_id = group_id,
            pr_group_represent = group_represent,
            pr_mailing_list_crud_strings = mailing_list_crud_strings
        )

    # -------------------------------------------------------------------------
    @staticmethod
    def group_deduplicate(item):
        """ Group de-duplication """

        if item.id:
            return
        if item.tablename == "pr_group":
            table = item.table
            name = item.data.get("name", None)

            query = (table.name == name) & \
                    (table.deleted != True)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def group_membership_onaccept(form):
        """
            Remove any duplicate memberships and update affiliations
        """

        db = current.db
        s3db = current.s3db

        mtable = s3db.pr_group_membership

        if hasattr(form, "vars"):
            _id = form.vars.id
        elif isinstance(form, Row) and "id" in form:
            _id = form.id
        else:
            return
        if _id:
            record = db(mtable.id == _id).select(limitby=(0, 1)).first()
        else:
            return
        if record:
            person_id = record.person_id
            group_id = record.group_id
            if person_id and group_id and not record.deleted:
                query = (mtable.person_id == person_id) & \
                        (mtable.group_id == group_id) & \
                        (mtable.id != record.id) & \
                        (mtable.deleted != True)
                deleted_fk = {"person_id": person_id,
                              "group_id": group_id}
                db(query).update(deleted = True,
                                 person_id = None,
                                 group_id = None,
                                 deleted_fk = json.dumps(deleted_fk))
            pr_update_affiliations(mtable, record)
        return

# =============================================================================
class S3ContactModel(S3Model):
    """ Person Contacts """

    names = ["pr_contact",
             "pr_contact_emergency"
             ]

    def model(self):

        T = current.T
        db = current.db
        msg = current.msg
        request = current.request
        s3 = current.response.s3

        UNKNOWN_OPT = current.messages.UNKNOWN_OPT

        comments = s3.comments
        define_table = self.define_table
        meta_fields = s3.meta_fields
        super_link = self.super_link

        # ---------------------------------------------------------------------
        # Contact
        #
        # @ToDo: Provide widgets which can be dropped into the main person form to have
        #        the relevant ones for that deployment/context collected on that same
        #        form
        #
        contact_methods = msg.CONTACT_OPTS

        tablename = "pr_contact"
        table = define_table(tablename,
                             super_link("pe_id", "pr_pentity"),
                             Field("contact_method",
                                   length=32,
                                   requires = IS_IN_SET(contact_methods,
                                                        zero=None),
                                   default = "SMS",
                                   label = T("Contact Method"),
                                   represent = lambda opt: \
                                               contact_methods.get(opt, UNKNOWN_OPT)),
                             Field("value",
                                   label= T("Value"),
                                   notnull=True,
                                   requires = IS_NOT_EMPTY()),
                             Field("priority", "integer",
                                   label= T("Priority"),
                                   comment = DIV(_class="tooltip",
                                                 _title="%s|%s" % (T("Priority"),
                                                                   T("What order to be contacted in."))),
                                   requires = IS_IN_SET(range(1, 10), zero=None)),
                             comments(),
                             *meta_fields())

        # Field configuration
        table.pe_id.requires = IS_ONE_OF(db, "pr_pentity.pe_id",
                                         pr_pentity_represent,
                                         orderby="instance_type",
                                         filterby="instance_type",
                                         filter_opts=("pr_person", "pr_group"))

        # CRUD Strings
        s3.crud_strings[tablename] = Storage(
            title_create = T("Add Contact Information"),
            title_display = T("Contact Details"),
            title_list = T("Contact Information"),
            title_update = T("Edit Contact Information"),
            title_search = T("Search Contact Information"),
            subtitle_create = T("Add Contact Information"),
            subtitle_list = T("Contact Information"),
            label_list_button = T("List Contact Information"),
            label_create_button = T("Add Contact Information"),
            label_delete_button = T("Delete Contact Information"),
            msg_record_created = T("Contact Information Added"),
            msg_record_modified = T("Contact Information Updated"),
            msg_record_deleted = T("Contact Information Deleted"),
            msg_list_empty = T("No contact information available"))

        # Resource configuration
        self.configure(tablename,
                       onvalidation=self.contact_onvalidation,
                       deduplicate=self.contact_deduplicate,
                       list_fields=["id",
                                    "contact_method",
                                    "value",
                                    "priority",
                                   ])

        # ---------------------------------------------------------------------
        # Emergency Contact Information
        #
        tablename = "pr_contact_emergency"
        table = define_table(tablename,
                             super_link("pe_id", "pr_pentity"),
                             Field("name",
                                   label= T("Name")),
                             Field("relationship",
                                   label= T("Relationship")),
                             Field("phone",
                                   label = T("Phone"),
                                   requires = IS_NULL_OR(s3_phone_requires)),
                             comments(),
                             *meta_fields())

        # ---------------------------------------------------------------------
        # Return model-global names to response.s3
        #
        return Storage(
        )

    # -------------------------------------------------------------------------
    @staticmethod
    def contact_onvalidation(form):
        """ Contact form validation """

        if form.vars.contact_method == "EMAIL":
            email, error = IS_EMAIL()(form.vars.value)
            if error:
                form.errors.value = T("Enter a valid email")
        return False

    # -------------------------------------------------------------------------
    @staticmethod
    def contact_deduplicate(item):
        """ Contact information de-duplication """

        if item.id:
            return
        if item.tablename == "pr_contact":
            table = item.table
            pe_id = item.data.get("pe_id", None)
            contact_method = item.data.get("contact_method", None)
            value = item.data.get("value", None)

            if pe_id is None:
                return

            query = (table.pe_id == pe_id) & \
                    (table.contact_method == contact_method) & \
                    (table.value == value) & \
                    (table.deleted != True)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE
        return

# =============================================================================
class S3PersonAddressModel(S3Model):
    """ Addresses for Persons """

    names = ["pr_address",
             "pr_address_type_opts"
            ]

    def model(self):

        T = current.T
        db = current.db
        request = current.request
        s3 = current.response.s3

        location_id = self.gis_location_id

        UNKNOWN_OPT = current.messages.UNKNOWN_OPT

        # ---------------------------------------------------------------------
        # Address
        #
        pr_address_type_opts = {
            1:T("Home Address"),
            2:T("Office Address"),
            3:T("Holiday Address"),
            9:T("other")
        }

        tablename = "pr_address"
        table = self.define_table(tablename,
                                  self.super_link("pe_id", "pr_pentity"),
                                  Field("type", "integer",
                                        requires = IS_IN_SET(pr_address_type_opts, zero=None),
                                        widget = RadioWidget.widget,
                                        default = 1,
                                        label = T("Address Type"),
                                        represent = lambda opt: \
                                                    pr_address_type_opts.get(opt, UNKNOWN_OPT)),
                                  location_id(),
                                  s3.comments(),
                                  *(s3.address_fields() + s3.meta_fields()))

        table.pe_id.requires = IS_ONE_OF(db, "pr_pentity.pe_id",
                                         pr_pentity_represent,
                                         orderby="instance_type",
                                         filterby="instance_type",
                                         filter_opts=("pr_person", "pr_group"))

        # Field configuration
        if not self.settings.get_gis_building_name():
            table.building_name.readable = False

        # CRUD Strings
        ADD_ADDRESS = T("Add Address")
        LIST_ADDRESS = T("List of addresses")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_ADDRESS,
            title_display = T("Address Details"),
            title_list = LIST_ADDRESS,
            title_update = T("Edit Address"),
            title_search = T("Search Addresses"),
            subtitle_create = T("Add New Address"),
            subtitle_list = T("Addresses"),
            label_list_button = LIST_ADDRESS,
            label_create_button = ADD_ADDRESS,
            msg_record_created = T("Address added"),
            msg_record_modified = T("Address updated"),
            msg_record_deleted = T("Address deleted"),
            msg_list_empty = T("There is no address for this person yet. Add new address."))

        # Resource configuration
        self.configure(tablename,
                       onaccept=self.address_onaccept,
                       onvalidation=s3.address_onvalidation,
                       deduplicate=self.address_deduplicate,
                       list_fields = ["id",
                                      "type",
                                      "address",
                                      "postcode",
                                      #"L4",
                                      "L3",
                                      "L2",
                                      "L1",
                                      "L0"
                                    ])

        # ---------------------------------------------------------------------
        # Return model-global names to response.s3
        #
        return Storage(
                pr_address_type_opts = pr_address_type_opts
            )

    # -------------------------------------------------------------------------
    @staticmethod
    def address_onaccept(form):
        """
            Updates the Base Location to be the same as the Address

            If the base location hasn't yet been set or if this is specifically
            requested
        """

        db = current.db
        s3db = current.s3db
        request = current.request
        lx_update = current.response.s3.lx_update

        vars = form.vars
        location_id = vars.location_id
        pe_id = vars.pe_id

        if location_id:
            person = None
            table = s3db.pr_person
            if "base_location" in request.vars and \
               request.vars.base_location == "on":
                # Specifically requested
                S3Tracker()(s3db.pr_pentity, pe_id).set_base_location(location_id)
                person = db(table.pe_id == pe_id).select(table.id,
                                                         limitby=(0, 1)).first()
                if person:
                    # Update the Lx fields
                    lx_update(table, person.id)
            else:
                # Check if a base location already exists
                query = (table.pe_id == pe_id)
                person = db(query).select(table.id,
                                          table.location_id).first()
                if person and not person.location_id:
                    # Hasn't yet been set so use this
                    S3Tracker()(s3db.pr_pentity, pe_id).set_base_location(location_id)
                    # Update the Lx fields
                    lx_update(table, person.id)

            if person and str(vars.type) == "1": # Home Address
                # Also check for any Volunteer HRM record(s)
                htable = s3db.hrm_human_resource
                query = (htable.person_id == person.id) & \
                        (htable.type == 2) & \
                        (htable.deleted != True)
                hrs = db(query).select(htable.id)
                for hr in hrs:
                    db(htable.id == hr.id).update(location_id=location_id)
                    # Update the Lx fields
                    lx_update(htable, hr.id)
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def address_deduplicate(item):
        """ Address de-duplication """

        if item.id:
            return
        if item.tablename == "pr_address":
            table = item.table
            pe_id = item.data.get("pe_id", None)
            address = item.data.get("address", None)

            if pe_id is None:
                return

            query = (table.pe_id == pe_id) & \
                    (table.address == address) & \
                    (table.deleted != True)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE
        return

# =============================================================================
class S3PersonImageModel(S3Model):
    """ Images for Persons """

    names = ["pr_image"]

    def model(self):

        T = current.T
        db = current.db
        request = current.request
        s3 = current.response.s3

        UNKNOWN_OPT = current.messages.UNKNOWN_OPT

        # ---------------------------------------------------------------------
        # Image
        #
        pr_image_type_opts = {
            1:T("Photograph"),
            2:T("Sketch"),
            3:T("Fingerprint"),
            4:T("X-Ray"),
            5:T("Document Scan"),
            9:T("other")
        }

        tablename = "pr_image"
        table = self.define_table(tablename,
                                  self.super_link("pe_id", "pr_pentity"),
                                  Field("profile", "boolean",
                                        default = False,
                                        label = T("Profile Picture?")
                                        ),
                                  Field("type", "integer",
                                        requires = IS_IN_SET(pr_image_type_opts, zero=None),
                                        default = 1,
                                        label = T("Image Type"),
                                        represent = lambda opt: pr_image_type_opts.get(opt,
                                                                                        UNKNOWN_OPT)),
                                  Field("title", label=T("Title"),
                                        requires = IS_NOT_EMPTY(),
                                        comment = DIV(_class="tooltip",
                                                      _title="%s|%s" % (T("Title"),
                                                                        T("Specify a descriptive title for the image.")))),
                                  Field("image", "upload", autodelete=True,
                                        represent = lambda image: image and \
                                                   DIV(A(IMG(_src=URL(c="default", f="download",
                                                                       args=image),
                                                              _height=60, _alt=T("View Image")),
                                                              _href=URL(c="default", f="download",
                                                                        args=image))) or T("No Image"),
                                        comment =  DIV(_class="tooltip",
                                                       _title="%s|%s" % (T("Image"),
                                                                         T("Upload an image file here. If you don't upload an image file, then you must specify its location in the URL field.")))),
                                  Field("url",
                                        label = T("URL"),
                                        represent = lambda url: url and \
                                                                DIV(A(IMG(_src=url, _height=60), _href=url)) or T("None"),
                                        comment = DIV(_class="tooltip",
                                                      _title="%s|%s" % (T("URL"),
                                                                       T("The URL of the image file. If you don't upload an image file, then you must specify its location here.")))),
                                   Field("description",
                                        label=T("Description"),
                                        comment = DIV(_class="tooltip",
                                                      _title="%s|%s" % (T("Description"),
                                                                        T("Give a brief description of the image, e.g. what can be seen where on the picture (optional).")))),
                                  s3.comments(),
                                  *s3.meta_fields())

        # CRUD Strings
        LIST_IMAGES = T("List Images")
        s3.crud_strings[tablename] = Storage(
            title_create = T("Image"),
            title_display = T("Image Details"),
            title_list = LIST_IMAGES,
            title_update = T("Edit Image Details"),
            title_search = T("Search Images"),
            subtitle_create = T("Add New Image"),
            subtitle_list = T("Images"),
            label_list_button = LIST_IMAGES,
            label_create_button = T("Add Image"),
            label_delete_button = T("Delete Image"),
            msg_record_created = T("Image added"),
            msg_record_modified = T("Image updated"),
            msg_record_deleted = T("Image deleted"),
            msg_list_empty = T("No Images currently registered"))

        # Resource configuration
        self.configure(tablename,
                       onaccept = self.pr_image_onaccept,
                       onvalidation = self.pr_image_onvalidation,
                       mark_required = ["url", "image"],
                       list_fields=["id",
                                    "title",
                                    "profile",
                                    "type",
                                    "image",
                                    "url",
                                    "description"
                                   ])

        # ---------------------------------------------------------------------
        # Return model-global names to response.s3
        #
        return Storage()

    # -------------------------------------------------------------------------
    @staticmethod
    def pr_image_onaccept(form):
        """
            If this is the profile image then remove this flag from all
            others for this person.
        """

        db = current.db
        s3db = current.s3db
        table = s3db.pr_image

        vars = form.vars
        id = vars.id
        profile = vars.profile
        url = vars.url
        newfilename = vars.image_newfilename
        if profile == 'False':
            profile = False

        if newfilename and not url:
            # Provide the link to the file in the URL field
            url = URL(c="default", f="download", args=newfilename)
            query = (table.id == id)
            db(query).update(url = url)

        if profile:
            # Find the pe_id
            query = (table.id == id)
            pe = db(query).select(table.pe_id,
                                  limitby=(0, 1)).first()
            if pe:
                pe_id = pe.pe_id
                # Set all others for this person as not the Profile picture
                query  = (table.pe_id == pe_id) & \
                         (table.id != id)
                db(query).update(profile = False)

    # -------------------------------------------------------------------------
    @staticmethod
    def pr_image_onvalidation(form):
        """ Image form validation """

        db = current.db
        s3db = current.s3db
        request = current.request

        vars = form.vars
        table = s3db.pr_image
        image = vars.image
        url = vars.url

        if not hasattr(image, "file"):
            id = request.post_vars.id
            if id:
                record = db(table.id == id).select(table.image,
                                                   limitby=(0, 1)).first()
                if record:
                    image = record.image

        if not hasattr(image, "file") and not image and not url:
            form.errors.image = \
            form.errors.url = T("Either file upload or image URL required.")
        return

# =============================================================================
class S3PersonIdentityModel(S3Model):
    """ Identities for Persons """

    names = ["pr_identity"]

    def model(self):

        T = current.T
        db = current.db
        request = current.request
        s3 = current.response.s3

        person_id = self.pr_person_id

        UNKNOWN_OPT = current.messages.UNKNOWN_OPT

        # ---------------------------------------------------------------------
        # Identity
        #
        # http://docs.oasis-open.org/emergency/edxl-have/cs01/xPIL-types.xsd
        # <xs:simpleType name="DocumentTypeList">
        #  <xs:enumeration value="Passport"/>
        #  <xs:enumeration value="DriverLicense"/>
        #  <xs:enumeration value="CreditCard"/>
        #  <xs:enumeration value="BankCard"/>
        #  <xs:enumeration value="KeyCard"/>
        #  <xs:enumeration value="AccessCard"/>
        #  <xs:enumeration value="IdentificationCard"/>
        #  <xs:enumeration value="Certificate"/>
        #  <xs:enumeration value="MileageProgram"/>
        #
        pr_id_type_opts = {
            1:T("Passport"),
            2:T("National ID Card"),
            3:T("Driving License"),
            #4:T("Credit Card"),
            99:T("other")
        }

        tablename = "pr_identity"
        table = self.define_table(tablename,
                                  person_id(label = T("Person"),
                                            ondelete="CASCADE"),
                                  Field("type", "integer",
                                        requires = IS_IN_SET(pr_id_type_opts, zero=None),
                                        default = 1,
                                        label = T("ID type"),
                                        represent = lambda opt: \
                                                    pr_id_type_opts.get(opt,
                                                                        UNKNOWN_OPT)),
                                  Field("value"),
                                  Field("description"),
                                  Field("country_code", length=4),
                                  Field("ia_name", label = T("Issuing Authority")),
                                  #Field("ia_subdivision"), # Name of issuing authority subdivision
                                  #Field("ia_code"), # Code of issuing authority (if any)
                                  s3.comments(),
                                  *s3.meta_fields())

        # Field configuration
        table.value.requires = [IS_NOT_EMPTY(),
                                IS_NOT_ONE_OF(db, "%s.value" % tablename)]

        # CRUD Strings
        ADD_IDENTITY = T("Add Identity")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_IDENTITY,
            title_display = T("Identity Details"),
            title_list = T("Known Identities"),
            title_update = T("Edit Identity"),
            title_search = T("Search Identity"),
            subtitle_create = T("Add New Identity"),
            subtitle_list = T("Current Identities"),
            label_list_button = T("List Identities"),
            label_create_button = ADD_IDENTITY,
            msg_record_created = T("Identity added"),
            msg_record_modified = T("Identity updated"),
            msg_record_deleted = T("Identity deleted"),
            msg_list_empty = T("No Identities currently registered"))

        # Resource configuration
        self.configure(tablename,
                       list_fields=["id",
                                    "type",
                                    "type",
                                    "value",
                                    "country_code",
                                    "ia_name"
                                   ])

        # ---------------------------------------------------------------------
        # Return model-global names to response.s3
        #
        return Storage()


# =============================================================================
class S3SavedSearch(S3Model):
    """ Saved Searches """

    names = ["pr_save_search"]

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth
        request = current.request
        s3 = current.response.s3

        pr_person = self.table("pr_person")
        person_id = s3.pr_person_id

        # ---------------------------------------------------------------------
        # Saved Searches
        #
        tablename = "pr_save_search"
        table = self.define_table(tablename,
                                  Field("user_id", "integer",
                                        readable = False,
                                        writable = False,
                                        default = auth.user_id),
                                  Field("search_vars","text",
                                        label = T("Search Criteria"),
                                        represent=lambda id:self.search_vars_represent(id)),
                                  Field("subscribed","boolean",
                                        default=False),
                                  person_id(label = T("Person"),
                                            ondelete="CASCADE",
                                            default = auth.s3_logged_in_person()),
                                  *s3.meta_fields())


        # CRUD Strings
        s3.crud_strings[tablename] = Storage(
            title_create = T("Save Search"),
            title_display = T("Saved Search Details"),
            title_list = T("Saved Searches"),
            title_update = T("Edit Saved Search"),
            title_search = T("Search Saved Searches"),
            subtitle_create = T("Add Saved Search"),
            subtitle_list = T("Saved Searches"),
            label_list_button = T("List Saved Searches"),
            label_create_button = T("Save Search"),
            label_delete_button = T("Delete Saved Search"),
            msg_record_created = T("Saved Search added"),
            msg_record_modified = T("Saved Search updated"),
            msg_record_deleted = T("Saved Search deleted"),
            msg_list_empty = T("No Search saved"))

        # Resource configuration
        self.configure(tablename,
                       insertable = False,
                       editable = False,
                       listadd = False,
                       deletable = True,
                       list_fields=["search_vars"])

        # ---------------------------------------------------------------------
        # Return model-global names to response.s3
        #
        return Storage()

    # -------------------------------------------------------------------------
    @staticmethod

    def search_vars_represent(search_vars):
        """
        Represent the search criteria
        @param search_vars: the pr_save_search record ID

        @ToDo: Modify this function so that it displays a Human Readable representation of the criteria
               Move this function to modules/s3/s3search
               Use this function in controllers/msg instead of re-defining it there
        """
        import cPickle
        import re
        s = ""
        search_vars = search_vars.replace("&apos;", "'")
        try:
            search_vars = cPickle.loads(str(search_vars))
        except:
            raise HTTP(500,"ERROR RETRIEVING THE SEARCH CRITERIA")
            s = "<p>"
            pat = '_'
            for var in search_vars.iterkeys():
                if var == "criteria" :
                    c_dict = search_vars[var]
                    #s = s + crud_string("pr_save_search", "Search Criteria")
                    for j in c_dict.iterkeys():
                        if not re.match(pat,j):
                            st = str(j)
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
            return XML(s)

# =============================================================================
class S3PersonPresence(S3Model):
    """
        Presence Log for Persons

        @todo: deprecate
        currently still used by CR
    """

    names = ["pr_presence",
             "pr_trackable_types",
             "pr_default_trackable",
             "pr_presence_opts",
             "pr_presence_conditions",
             "pr_default_presence"]

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth
        request = current.request
        s3 = current.response.s3

        person_id = self.pr_person_id
        location_id = self.gis_location_id

        ADD_LOCATION = current.messages.ADD_LOCATION
        UNKNOWN_OPT = current.messages.UNKNOWN_OPT

        datetime_represent = S3DateTime.datetime_represent

        # Trackable types
        pr_trackable_types = {
            1:current.T("Person"),          # an individual
            2:current.T("Group"),           # a group
            3:current.T("Body"),            # a dead body or body part
            4:current.T("Object"),          # other objects belonging to persons
            5:current.T("Organization"),    # an organisation
            6:current.T("Office"),          # an office
        }
        pr_default_trackable = 1

        # Presence conditions
        pr_presence_opts = Storage(
            SEEN = 1,
            TRANSIT = 2,
            PROCEDURE = 3,
            TRANSITIONAL_PRESENCE = (1, 2, 3),
            CHECK_IN = 11,
            CONFIRMED = 12,
            DECEASED = 13,
            LOST = 14,
            PERSISTANT_PRESENCE = (11, 12, 13, 14),
            TRANSFER = 21,
            CHECK_OUT = 22,
            ABSENCE = (21, 22),
            MISSING = 99
        )
        opts = pr_presence_opts
        pr_presence_conditions = Storage({
            # Transitional presence conditions:
            opts.SEEN: current.T("Seen"),           # seen (formerly "found") at location
            opts.TRANSIT: current.T("Transit"),     # seen at location, between two transfers
            opts.PROCEDURE: current.T("Procedure"), # seen at location, undergoing procedure ("Checkpoint")

            # Persistant presence conditions:
            opts.CHECK_IN: current.T("Check-In"),   # arrived at location for accomodation/storage
            opts.CONFIRMED: current.T("Confirmed"), # confirmation of stay/storage at location
            opts.DECEASED: current.T("Deceased"),   # deceased
            opts.LOST: current.T("Lost"),           # destroyed/disposed at location

            # Absence conditions:
            opts.TRANSFER: current.T("Transfer"),   # Send to another location
            opts.CHECK_OUT: current.T("Check-Out"), # Left location for unknown destination

            # Missing condition:
            opts.MISSING: current.T("Missing"),     # Missing (from a "last-seen"-location)
        })
        pr_default_presence = 1

        resourcename = "presence"
        tablename = "pr_presence"
        table = self.define_table(tablename,
                                  self.super_link("pe_id", "pr_pentity"),
                                  self.super_link("sit_id", "sit_situation"),
                                  person_id("observer",
                                            label=T("Observer"),
                                            default = auth.s3_logged_in_person(),
                                            comment=pr_person_comment(title=T("Observer"),
                                                                      comment=T("Person who has actually seen the person/group."),
                                                                      child="observer")),
                                  Field("shelter_id", "integer",
                                        readable = False,
                                        writable = False),
                                  location_id(widget = S3LocationAutocompleteWidget(),
                                              comment = DIV(A(ADD_LOCATION,
                                                              _class="colorbox",
                                                              _target="top",
                                                              _title=ADD_LOCATION,
                                                              _href=URL(c="gis", f="location",
                                                                        args="create",
                                                                        vars=dict(format="popup"))),
                                                            DIV(_class="tooltip",
                                                                _title="%s|%s" % (T("Current Location"),
                                                                                  T("The Current Location of the Person/Group, which can be general (for Reporting) or precise (for displaying on a Map). Enter a few characters to search from available locations."))))),
                                  Field("location_details",
                                        comment = DIV(_class="tooltip",
                                                      _title="%s|%s" % (T("Location Details"),
                                                                        T("Specific Area (e.g. Building/Room) within the Location that this Person/Group is seen.")))),
                                  Field("datetime", "datetime",
                                        label = T("Date/Time"),
                                        default = request.utcnow,
                                        requires = IS_UTC_DATETIME(allow_future=False),
                                        widget = S3DateTimeWidget(future=0),
                                        represent = lambda val: datetime_represent(val, utc=True)),
                                  Field("presence_condition", "integer",
                                        requires = IS_IN_SET(pr_presence_conditions,
                                                             zero=None),
                                        default = pr_default_presence,
                                        label = T("Presence Condition"),
                                        represent = lambda opt: \
                                                    pr_presence_conditions.get(opt, UNKNOWN_OPT)),
                                   Field("proc_desc",
                                         label = T("Procedure"),
                                         comment = DIV(DIV(_class="tooltip",
                                                           _title="%s|%s" % (T("Procedure"),
                                                                             T('Describe the procedure which this record relates to (e.g. "medical examination")'))))),
                                   location_id("orig_id",
                                               label=T("Origin"),
                                               widget = S3LocationAutocompleteWidget(),
                                               comment = DIV(A(ADD_LOCATION,
                                                               _class="colorbox",
                                                               _target="top",
                                                               _title=ADD_LOCATION,
                                                               _href=URL(c="gis", f="location",
                                                                         args="create",
                                                                         vars=dict(format="popup"))),
                                                             DIV(_class="tooltip",
                                                                 _title="%s|%s" % (T("Origin"),
                                                                                   T("The Location the Person has come from, which can be general (for Reporting) or precise (for displaying on a Map). Enter a few characters to search from available locations."))))),
                                   location_id("dest_id",
                                               label=T("Destination"),
                                               widget = S3LocationAutocompleteWidget(),
                                               comment = DIV(A(ADD_LOCATION,
                                                               _class="colorbox",
                                                               _target="top",
                                                               _title=ADD_LOCATION,
                                                               _href=URL(c="gis", f="location",
                                                                         args="create",
                                                                         vars=dict(format="popup"))),
                                                             DIV(_class="tooltip",
                                                                 _title="%s|%s" % (T("Destination"),
                                                                                   T("The Location the Person is going to, which can be general (for Reporting) or precise (for displaying on a Map). Enter a few characters to search from available locations."))))),
                                   Field("comment"),
                                   Field("closed", "boolean",
                                         default=False,
                                         readable = False,
                                         writable = False),
                                   *s3.meta_fields())

        # CRUD Strings
        ADD_LOG_ENTRY = T("Add Log Entry")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_LOG_ENTRY,
            title_display = T("Log Entry Details"),
            title_list = T("Presence Log"),
            title_update = T("Edit Log Entry"),
            title_search = T("Search Log Entry"),
            subtitle_create = T("Add New Log Entry"),
            subtitle_list = T("Current Log Entries"),
            label_list_button = T("List Log Entries"),
            label_create_button = ADD_LOG_ENTRY,
            msg_record_created = T("Log entry added"),
            msg_record_modified = T("Log entry updated"),
            msg_record_deleted = T("Log entry deleted"),
            msg_list_empty = T("No Presence Log Entries currently registered"))

        # Resource configuration
        self.configure(tablename,
                       super_entity = "sit_situation",
                       onvalidation = self.presence_onvalidation,
                       onaccept = self.presence_onaccept,
                       delete_onaccept = self.presence_onaccept,
                       list_fields = ["id",
                                      "datetime",
                                      "location_id",
                                      "shelter_id",
                                      "presence_condition",
                                      "orig_id",
                                      "dest_id"
                                     ],
                       main="time",
                       extra="location_details")

        # ---------------------------------------------------------------------
        # Return model-global names to response.s3
        #
        return Storage(
             pr_trackable_types=pr_trackable_types,
             pr_default_trackable=pr_default_trackable,
             pr_presence_opts=pr_presence_opts,
             pr_presence_conditions=pr_presence_conditions,
             pr_default_presence=pr_default_presence
        )

    # -------------------------------------------------------------------------
    @staticmethod
    def presence_onvalidation(form):
        """ Presence record validation """

        db = current.db
        s3db = current.s3db
        s3 = current.response.s3

        table = s3db.pr_presence
        popts = s3.pr_presence_opts
        shelter_table = s3db.cr_shelter

        location = form.vars.location_id
        shelter = form.vars.shelter_id

        if shelter and shelter_table is not None:
            set = db(shelter_table.id == shelter)
            row = set.select(shelter_table.location_id, limitby=(0, 1)).first()
            if row:
                location = form.vars.location_id = row.location_id
            else:
                shelter = None

        if location or shelter:
            return

        condition = form.vars.presence_condition
        if condition:
            try:
                condition = int(condition)
            except ValueError:
                condition = None
        else:
            condition = table.presence_condition.default
            form.vars.presence_condition = condition

        if condition:
            if condition in popts.PERSISTANT_PRESENCE or \
               condition in popts.ABSENCE:
                if not form.vars.id:
                    if table.location_id.default or \
                       table.shelter_id.default:
                        return
                else:
                    record = db(table.id == form.vars.id).select(table.location_id,
                                                                 table.shelter_id,
                                                                 limitby=(0, 1)).first()
                    if record and \
                       record.location_id or record.shelter_id:
                        return
            else:
                return
        else:
            return

        form.errors.location_id = \
        form.errors.shelter_id = T("Either a shelter or a location must be specified")
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def presence_onaccept(form):
        """
            Update the presence log of a person entity

            - mandatory to be called as onaccept routine at any modification
              of pr_presence records

        """

        db = current.db
        s3db = current.s3db
        s3 = current.response.s3

        table = s3db.pr_presence
        popts = s3.pr_presence_opts

        if isinstance(form, (int, long, str)):
            id = form
        elif hasattr(form, "vars"):
            id = form.vars.id
        else:
            id = form.id

        presence = db(table.id == id).select(table.ALL, limitby=(0,1)).first()
        if not presence:
            return
        else:
            condition = presence.presence_condition

        pe_id = presence.pe_id
        datetime = presence.datetime
        if not datetime or not pe_id:
            return

        this_entity = ((table.pe_id == pe_id) & (table.deleted == False))
        earlier = (table.datetime < datetime)
        later = (table.datetime > datetime)
        same_place = ((table.location_id == presence.location_id) |
                      (table.shelter_id == presence.shelter_id))
        is_present = (table.presence_condition.belongs(popts.PERSISTANT_PRESENCE))
        is_absent = (table.presence_condition.belongs(popts.ABSENCE))
        is_missing = (table.presence_condition == popts.MISSING)

        if not presence.deleted:

            if condition in popts.TRANSITIONAL_PRESENCE:
                if presence.closed:
                    db(table.id == id).update(closed=False)

            elif condition in popts.PERSISTANT_PRESENCE:
                if not presence.closed:
                    query = this_entity & earlier & (is_present | is_missing) & \
                            (table.closed == False)
                    db(query).update(closed=True)

                    query = this_entity & later & \
                            (is_present | (is_absent & same_place))
                    if db(query).count():
                        db(table.id == id).update(closed=True)

            elif condition in popts.ABSENCE:
                query = this_entity & earlier & is_present & same_place
                db(query).update(closed=True)

                if not presence.closed:
                    db(table.id == id).update(closed=True)

        if not presence.closed:

            # Re-open the last persistant presence if no closing event
            query = this_entity & is_present
            presence = db(query).select(table.ALL, orderby=~table.datetime, limitby=(0,1)).first()
            if presence and presence.closed:
                later = (table.datetime > presence.datetime)
                query = this_entity & later & is_absent & same_place
                if not db(query).count():
                    db(table.id == presence.id).update(closed=False)

            # Re-open the last missing if no later persistant presence
            query = this_entity & is_missing
            presence = db(query).select(table.ALL, orderby=~table.datetime, limitby=(0,1)).first()
            if presence and presence.closed:
                later = (table.datetime > presence.datetime)
                query = this_entity & later & is_present
                if not db(query).count():
                    db(table.id == presence.id).update(closed=False)

        pentity = db(db.pr_pentity.pe_id == pe_id).select(db.pr_pentity.instance_type,
                                                          limitby=(0,1)).first()
        if pentity and pentity.instance_type == "pr_person":
            query = this_entity & is_missing & (table.closed == False)
            if db(query).count():
                db(db.pr_person.pe_id == pe_id).update(missing = True)
            else:
                db(db.pr_person.pe_id == pe_id).update(missing = False)

        return

# =============================================================================
class S3PersonDescription(S3Model):
    """ Additional tables for DVI/MPR """

    names = ["pr_note", "pr_physical_description"]

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth
        request = current.request
        s3 = current.response.s3

        person_id = self.pr_person_id
        location_id = self.gis_location_id

        UNKNOWN_OPT = current.messages.UNKNOWN_OPT
        #if deployment_settings.has_module("dvi") or \
           #deployment_settings.has_module("mpr"):

        # ---------------------------------------------------------------------
        # Note
        #
        person_status = {
            1: T("missing"),
            2: T("found"),
            3: T("deceased"),
            9: T("none")
        }

        resourcename = "note"
        tablename = "pr_note"
        table = self.define_table(tablename,
                                  self.super_link("pe_id", "pr_pentity"),
                                  # Reporter
                                  #person_id("reporter"),
                                  Field("confirmed", "boolean",
                                        default=False,
                                        readable=False,
                                        writable=False),
                                  Field("closed", "boolean",
                                        default=False,
                                        readable=False,
                                        writable=False),
                                  Field("status", "integer",
                                        requires=IS_IN_SET(person_status,
                                                           zero=None),
                                        default=9,
                                        label=T("Status"),
                                        represent=lambda opt: \
                                                  person_status.get(opt, UNKNOWN_OPT)),
                                  Field("timestmp", "datetime",
                                        label=T("Date/Time"),
                                        requires=[IS_EMPTY_OR(IS_UTC_DATETIME_IN_RANGE())],
                                        widget = S3DateTimeWidget(),
                                        default=request.utcnow),
                                  Field("note_text", "text",
                                        label=T("Text")),
                                  Field("note_contact", "text",
                                        label=T("Contact Info"),
                                        readable=False,
                                        writable=False),
                                  location_id(label=T("Last known location")),
                                  *s3.meta_fields())

        # CRUD strings
        ADD_NOTE = T("New Entry")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_NOTE,
            title_display = T("Journal Entry Details"),
            title_list = T("Journal"),
            title_update = T("Edit Entry"),
            title_search = T("Search Entries"),
            subtitle_create = T("Add New Entry"),
            subtitle_list = T("Current Entries"),
            label_list_button = T("See All Entries"),
            label_create_button = ADD_NOTE,
            msg_record_created = T("Journal entry added"),
            msg_record_modified = T("Journal entry updated"),
            msg_record_deleted = T("Journal entry deleted"),
            msg_list_empty = T("No entry available"))

        # Resource configuration
        self.configure(tablename,
                       list_fields=["id",
                                    "timestmp",
                                    "location_id",
                                    "note_text",
                                    "status"],
                       editable=False,
                       onaccept=self.note_onaccept,
                       ondelete=self.note_onaccept)

        # =====================================================================
        # Physical Description
        #
        pr_race_opts = {
            1: T("caucasoid"),
            2: T("mongoloid"),
            3: T("negroid"),
            99: T("other")
        }

        pr_complexion_opts = {
            1: T("light"),
            2: T("medium"),
            3: T("dark"),
            99: T("other")
        }

        pr_height_opts = {
            1: T("short"),
            2: T("average"),
            3: T("tall")
        }

        pr_weight_opts = {
            1: T("slim"),
            2: T("average"),
            3: T("fat")
        }

        # http://docs.oasis-open.org/emergency/edxl-have/cs01/xPIL-types.xsd
        pr_blood_type_opts = ("A+", "A-", "B+", "B-", "AB+", "AB-", "0+", "0-")

        pr_eye_color_opts = {
            1: T("blue"),
            2: T("grey"),
            3: T("green"),
            4: T("brown"),
            5: T("black"),
            99: T("other")
        }

        pr_hair_color_opts = {
            1: T("blond"),
            2: T("brown"),
            3: T("black"),
            4: T("red"),
            5: T("grey"),
            6: T("white"),
            99: T("see comment")
        }

        pr_hair_style_opts = {
            1: T("straight"),
            2: T("wavy"),
            3: T("curly"),
            99: T("see comment")
        }

        pr_hair_length_opts = {
            1: T("short<6cm"),
            2: T("medium<12cm"),
            3: T("long>12cm"),
            4: T("shaved"),
            99: T("see comment")
        }

        pr_hair_baldness_opts = {
            1: T("forehead"),
            2: T("sides"),
            3: T("tonsure"),
            4: T("total"),
            99: T("see comment")
        }

        pr_facial_hair_type_opts = {
            1: T("none"),
            2: T("Moustache"),
            3: T("Goatee"),
            4: T("Whiskers"),
            5: T("Full beard"),
            99: T("see comment")
        }

        pr_facial_hair_length_opts = {
            1: T("short"),
            2: T("medium"),
            3: T("long"),
            4: T("shaved")
        }

        # This set is suitable for use in the US
        pr_ethnicity_opts = [
            "American Indian",
            "Alaskan",
            "Asian",
            "African American",
            "Hispanic or Latino",
            "Native Hawaiian",
            "Pacific Islander",
            "Two or more",
            "Unspecified",
            "White"
        ]

        resourcename = "physical_description"
        tablename = "pr_physical_description"
        table = self.define_table(tablename,
                                  self.super_link("pe_id", "pr_pentity"),
                                  # Race and complexion
                                  Field("race", "integer",
                                        requires = IS_EMPTY_OR(IS_IN_SET(pr_race_opts)),
                                        label = T("Race"),
                                        represent = lambda opt: \
                                                    pr_race_opts.get(opt, UNKNOWN_OPT)),
                                  Field("complexion", "integer",
                                        requires = IS_EMPTY_OR(IS_IN_SET(pr_complexion_opts)),
                                        label = T("Complexion"),
                                        represent = lambda opt: \
                                                    pr_complexion_opts.get(opt, UNKNOWN_OPT)),
                                  Field("ethnicity",
                                        #requires=IS_NULL_OR(IS_IN_SET(pr_ethnicity_opts)),
                                        length=64),   # Mayon Compatibility

                                  # Height and weight
                                  Field("height", "integer",
                                        requires = IS_EMPTY_OR(IS_IN_SET(pr_height_opts)),
                                        label = T("Height"),
                                        represent = lambda opt: \
                                                    pr_height_opts.get(opt, UNKNOWN_OPT)),
                                  Field("height_cm", "integer",
                                        requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 300)),
                                        label = T("Height (cm)")),
                                  Field("weight", "integer",
                                        requires = IS_EMPTY_OR(IS_IN_SET(pr_weight_opts)),
                                        label = T("Weight"),
                                        represent = lambda opt: \
                                                    pr_weight_opts.get(opt, UNKNOWN_OPT)),
                                  Field("weight_kg", "integer",
                                        requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 500)),
                                        label = T("Weight (kg)")),

                                  # Blood type, eye color
                                  Field("blood_type",
                                        requires = IS_EMPTY_OR(IS_IN_SET(pr_blood_type_opts)),
                                        label = T("Blood Type (AB0)"),
                                        represent = lambda opt: opt or UNKNOWN_OPT),
                                  Field("eye_color", "integer",
                                        requires = IS_EMPTY_OR(IS_IN_SET(pr_eye_color_opts)),
                                        label = T("Eye Color"),
                                        represent = lambda opt: \
                                                    pr_eye_color_opts.get(opt, UNKNOWN_OPT)),

                                  # Hair of the head
                                  Field("hair_color", "integer",
                                        requires = IS_EMPTY_OR(IS_IN_SET(pr_hair_color_opts)),
                                        label = T("Hair Color"),
                                        represent = lambda opt: \
                                                    pr_hair_color_opts.get(opt, UNKNOWN_OPT)),
                                  Field("hair_style", "integer",
                                        requires = IS_EMPTY_OR(IS_IN_SET(pr_hair_style_opts)),
                                        label = T("Hair Style"),
                                        represent = lambda opt: \
                                                    pr_hair_style_opts.get(opt, UNKNOWN_OPT)),
                                  Field("hair_length", "integer",
                                        requires = IS_EMPTY_OR(IS_IN_SET(pr_hair_length_opts)),
                                        label = T("Hair Length"),
                                        represent = lambda opt: \
                                                    pr_hair_length_opts.get(opt, UNKNOWN_OPT)),
                                  Field("hair_baldness", "integer",
                                        requires = IS_EMPTY_OR(IS_IN_SET(pr_hair_baldness_opts)),
                                        label = T("Baldness"),
                                        represent = lambda opt: \
                                                    pr_hair_baldness_opts.get(opt, UNKNOWN_OPT)),
                                  Field("hair_comment"),

                                  # Facial hair
                                  Field("facial_hair_type", "integer",
                                        requires = IS_EMPTY_OR(IS_IN_SET(pr_facial_hair_type_opts)),
                                        label = T("Facial hair, type"),
                                        represent = lambda opt: \
                                                    pr_facial_hair_type_opts.get(opt, UNKNOWN_OPT)),
                                  Field("facial_hair_color", "integer",
                                        requires = IS_EMPTY_OR(IS_IN_SET(pr_hair_color_opts)),
                                        label = T("Facial hair, color"),
                                        represent = lambda opt: \
                                                    pr_hair_color_opts.get(opt, UNKNOWN_OPT)),
                                  Field("facial_hair_length", "integer",
                                        requires = IS_EMPTY_OR(IS_IN_SET(pr_facial_hair_length_opts)),
                                        label = T("Facial hear, length"),
                                        represent = lambda opt: \
                                                    pr_facial_hair_length_opts.get(opt, UNKNOWN_OPT)),
                                  Field("facial_hair_comment"),

                                  # Body hair and skin marks
                                  Field("body_hair"),
                                  Field("skin_marks", "text"),

                                  # Medical Details: scars, amputations, implants
                                  Field("medical_conditions", "text"),

                                  # Other details
                                  Field("other_details", "text"),

                                  s3.comments(),
                                  *s3.meta_fields())

        # Field configuration
        table.height_cm.comment = DIV(DIV(_class="tooltip",
                                          _title="%s|%s" % (T("Height"),
                                                            T("The body height (crown to heel) in cm."))))
        table.weight_kg.comment = DIV(DIV(_class="tooltip",
                                          _title="%s|%s" % (T("Weight"),
                                                            T("The weight in kg."))))

        table.pe_id.readable = False
        table.pe_id.writable = False

        # CRUD Strings
        # ?

        # Resource Configuration
        # ?

    # -------------------------------------------------------------------------
    @staticmethod
    def note_onaccept(form):
        """ Update missing status for person """

        db = current.db
        s3db = current.s3db

        pe_table = s3db.pr_pentity
        ntable = s3db.pr_note
        ptable = s3db.pr_person

        if isinstance(form, (int, long, str)):
            _id = form
        elif hasattr(form, "vars"):
            _id = form.vars.id
        else:
            _id = form.id

        note = ntable[_id]
        if not note:
            return

        query = (ntable.pe_id == note.pe_id) & \
                (ntable.deleted != True)
        mq = query & ntable.status == 1
        fq = query & ntable.status.belongs((2, 3))
        mr = db(mq).select(ntable.id,
                           ntable.timestmp,
                           orderby=~ntable.timestmp,
                           limitby=(0, 1)).first()
        fr = db(fq).select(ntable.id,
                           ntable.timestmp,
                           orderby=~ntable.timestmp,
                           limitby=(0, 1)).first()
        missing = False
        if mr and not fr or fr.timestmp < mr.timestmp:
            missing = True
        query = ptable.pe_id == note.pe_id
        db(query).update(missing=missing)
        if note.deleted:
            try:
                location_id = form.location_id
            except:
                pass
            else:
                ttable = s3db.sit_presence
                query = (ptable.pe_id == note.pe_id) & \
                        (ttable.uuid == ptable.uuid) & \
                        (ttable.location_id == location_id) & \
                        (ttable.timestmp == note.timestmp)
        if note.location_id:
            tracker = S3Tracker()
            tracker(query).set_location(note.location_id,
                                        timestmp=note.timestmp)
        return

# =============================================================================
# Representation Methods
# =============================================================================
#
def pr_pentity_represent(id, show_label=True, default_label="[No ID Tag]"):
    """ Represent a Person Entity in option fields or list views """

    T = current.T
    db = current.db
    s3db = current.s3db

    if not id:
        return current.messages.NONE

    pe_str = T("None (no such record)")

    pe_table = s3db.pr_pentity
    pe = db(pe_table.pe_id == id).select(pe_table.instance_type,
                                         pe_table.pe_label,
                                         limitby=(0, 1)).first()
    if not pe:
        return pe_str

    instance_type = pe.instance_type
    instance_type_nice = pe_table.instance_type.represent(instance_type)

    table = s3db.table(instance_type, None)
    if not table:
        return pe_str

    label = pe.pe_label or default_label

    if instance_type == "pr_person":
        person = db(table.pe_id == id).select(
                    table.first_name, table.middle_name, table.last_name,
                    limitby=(0, 1)).first()
        if person:
            if show_label:
                pe_str = "%s %s (%s)" % (s3_fullname(person),
                                         label, instance_type_nice)
            else:
                pe_str = "%s (%s)" % (s3_fullname(person),
                                      instance_type_nice)
    elif instance_type == "pr_group":
        group = db(table.pe_id == id).select(table.name,
                                             limitby=(0, 1)).first()
        if group:
            pe_str = "%s (%s)" % (group.name, instance_type_nice)
    elif instance_type == "org_organisation":
        organisation = db(table.pe_id == id).select(table.name,
                                                    limitby=(0, 1)).first()
        if organisation:
            pe_str = "%s (%s)" % (organisation.name, instance_type_nice)
    elif instance_type == "org_office":
        office = db(table.pe_id == id).select(table.name,
                                              limitby=(0, 1)).first()
        if office:
            pe_str = "%s (%s)" % (office.name, instance_type_nice)
    else:
        pe_str = "[%s] (%s)" % (label,
                                instance_type_nice)
    return pe_str

# =============================================================================
def pr_person_represent(id):
    """ Representation """

    if not id:
        return current.messages.NONE

    db = current.db
    s3db = current.s3db
    cache = current.cache

    table = s3db.pr_person

    def _represent(id):
        if isinstance(id, Row):
            person = id
            id = person.id
        else:
            person = db(table.id == id).select(table.first_name,
                                               table.middle_name,
                                               table.last_name,
                                               limitby=(0, 1)).first()
        if person:
            return s3_fullname(person)
        else:
            return None

    name = cache.ram("pr_person_%s" % id,
                     lambda: _represent(id), time_expire=10)
    return name

# =============================================================================
def pr_person_comment(title=None, comment=None, caller=None, child=None):

    T = current.T
    if title is None:
        title = T("Person")
    if comment is None:
        comment = T("Type the first few characters of one of the Person's names.")
    if child is None:
        child = "person_id"
    return S3AddResourceLink(c="pr", f="person",
                             vars=dict(caller=caller, child=child),
                             title=current.messages.ADD_PERSON,
                             tooltip="%s|%s" % (title, comment))

# =============================================================================
def pr_rheader(r, tabs=[]):
    """
        Person Registry resource headers
        - used in PR, HRM, DVI, MPR, MSG, VOL
    """

    T = current.T
    db = current.db
    s3db = current.s3db
    gis = current.gis
    s3 = current.response.s3

    tablename, record = s3_rheader_resource(r)

    if r.representation == "html":
        rheader_tabs = s3_rheader_tabs(r, tabs)

        if tablename == "pr_person":
            person = record
            if person:
                s3 = current.response.s3
                ptable = r.table
                itable = s3db.pr_image
                query = (itable.pe_id == record.pe_id) & \
                        (itable.profile == True)
                image = db(query).select(itable.image,
                                         limitby=(0, 1)).first()
                if image:
                    image = TD(itable.image.represent(image.image),
                               _rowspan=3)
                else:
                    image = ""
                rheader = DIV(TABLE(
                    TR(TH("%s: " % T("Name")),
                       s3_fullname(person),
                       TH("%s: " % T("ID Tag Number")),
                       "%(pe_label)s" % person,
                       image),
                    TR(TH("%s: " % T("Date of Birth")),
                       "%s" % (person.date_of_birth or T("unknown")),
                       TH("%s: " % T("Gender")),
                       "%s" % s3.pr_gender_opts.get(person.gender, T("unknown"))),

                    TR(TH("%s: " % T("Nationality")),
                       "%s" % (gis.get_country(person.nationality, key_type="code") or T("unknown")),
                       TH("%s: " % T("Age Group")),
                       "%s" % s3.pr_age_group_opts.get(person.age_group, T("unknown"))),

                    ), rheader_tabs)
                return rheader

        elif tablename == "pr_group":
            group = record
            if group:
                table = s3db.pr_group_membership
                query = (table.group_id == record.id) & \
                        (table.group_head == True)
                leader = db(query).select(table.person_id,
                                          limitby=(0, 1)).first()
                if leader:
                    leader = s3_fullname(leader.person_id)
                else:
                    leader = ""
                rheader = DIV(TABLE(
                                TR(TH("%s: " % T("Name")),
                                   group.name,
                                   TH("%s: " % T("Leader")) if leader else "",
                                   leader),
                                TR(TH("%s: " % T("Description")),
                                   group.description or "",
                                   TH(""),
                                   "")
                                ), rheader_tabs)
                return rheader

    return None

# =============================================================================
# Custom Resource Methods
# =============================================================================
#
def pr_contacts(r, **attr):
    """
        Custom Method to provide the details for the Person's Contacts Tab:
        - provides a single view on:
            Addresses (pr_address)
            Contacts (pr_contact)
            Emergency Contacts

        @ToDo: Fix Map in Address' LocationSelector
        @ToDo: Allow Address Create's LocationSelector to work in Debug mode
    """

    from itertools import groupby

    if r.http != "GET":
        r.error(405, current.manager.ERROR.BAD_METHOD)

    T = current.T
    db = current.db
    s3db = current.s3db

    person = r.record

    # Addresses
    atable = s3db.pr_address
    query = (atable.pe_id == person.pe_id)
    addresses = db(query).select(atable.id,
                                 atable.type,
                                 atable.building_name,
                                 atable.address,
                                 atable.postcode,
                                 orderby=atable.type)

    address_groups = {}
    for key, group in groupby(addresses, lambda a: a.type):
        address_groups[key] = list(group)

    address_wrapper = DIV(H2(T("Addresses")),
                          DIV(A(T("Add"), _class="addBtn", _id="address-add"),
                              _class="margin"))

    items = address_groups.items()
    opts = s3db.pr_address_type_opts
    for address_type, details in items:
        address_wrapper.append(H3(opts[address_type]))
        for detail in details:
            building_name = detail.building_name or ""
            if building_name:
                building_name = "%s, " % building_name
            address = detail.address or ""
            if address:
                address = "%s, " % address
            postcode = detail.postcode or ""
            address_wrapper.append(P(
                SPAN("%s%s%s" % (building_name,
                                 address,
                                 postcode)),
                A(T("Edit"), _class="editBtn fright"),
                _id="address-%s" % detail.id,
                _class="address",
                ))

    # Contacts
    ctable = s3db.pr_contact
    query = (ctable.pe_id == person.pe_id)
    contacts = db(query).select(ctable.id,
                                ctable.value,
                                ctable.contact_method,
                                orderby=ctable.contact_method)

    contact_groups = {}
    for key, group in groupby(contacts, lambda c: c.contact_method):
        contact_groups[key] = list(group)

    contacts_wrapper = DIV(H2(T("Contacts")),
                           DIV(A(T("Add"), _class="addBtn", _id="contact-add"),
                               _class="margin"))


    items = contact_groups.items()
    opts = current.msg.CONTACT_OPTS
    for contact_type, details in items:
        contacts_wrapper.append(H3(opts[contact_type]))
        for detail in details:
            contacts_wrapper.append(P(
                SPAN(detail.value),
                A(T("Edit"), _class="editBtn fright"),
                _id="contact-%s" % detail.id,
                _class="contact",
                ))

    # Emergency Contacts
    etable = s3db.pr_contact_emergency
    query = (etable.pe_id == person.pe_id) & \
            (etable.deleted == False)
    emergency = db(query).select(etable.id,
                                 etable.name,
                                 etable.relationship,
                                 etable.phone)

    emergency_wrapper = DIV(H2(T("Emergency Contacts")),
                            DIV(A(T("Add"), _class="addBtn", _id="emergency-add"),
                                _class="margin"))

    for contact in emergency:
        name = contact.name or ""
        if name:
            name = "%s, "% name
        relationship = contact.relationship or ""
        if relationship:
            relationship = "%s, "% relationship
        emergency_wrapper.append(P(
            SPAN("%s%s%s" % (name, relationship, contact.phone)),
            A(T("Edit"), _class="editBtn fright"),
            _id="emergency-%s" % contact.id,
            _class="emergency",
            ))

    # Overall content
    content = DIV(address_wrapper,
                  contacts_wrapper,
                  emergency_wrapper,
                  _class="contacts-wrapper")

    # Add the javascript
    response = current.response
    s3 = response.s3
    s3.scripts.append(URL(c="static", f="scripts",
                          args=["S3", "s3.contacts.js"]))
    s3.js_global.append("personId = %s;" % person.id);

    # Custom View
    response.view = "pr/contacts.html"

    # RHeader for consistency
    controller = current.request.controller
    if controller == "hrm":
        rheader = s3db.hrm_rheader(r)
    elif controller == "member":
        rheader = s3db.member_rheader(r)
    elif controller == "pr":
        rheader = s3db.pr_rheader(r)

    return dict(
            title = T("Contacts"),
            rheader = rheader,
            content = content,
        )

# =============================================================================
def pr_profile(r, **attr):
    """
        Custom Method to provide the auth_user profile as a Tab of the Person
        @ToDo: Complete this (currently unfinished)
    """

    if r.http != "GET":
        r.error(405, current.manager.ERROR.BAD_METHOD)

    T = current.T
    db = current.db
    s3db = current.s3db

    person = r.record

    # Profile
    ltable = s3db.pr_person_user
    query = (ltable.pe_id == person.pe_id)
    profile = db(query).select(limitby=(0, 1)).first()

    form = current.auth()

    # Custom View
    response.view = "pr/profile.html"

    # RHeader for consistency
    rheader = s3db.hrm_rheader(r)

    return dict(
            title = T("Profile"),
            rheader = rheader,
            form = form,
        )

# =============================================================================
# Hierarchy Manipulation
# =============================================================================
#
def pr_update_affiliations(table, record):
    """
        Update OU affiliations related to this record

        @param table: the table
        @param record: the record
    """

    if hasattr(table, "_tablename"):
        rtype = table._tablename
    else:
        rtype = table

    db = current.db
    s3db = current.s3db

    if rtype == "hrm_human_resource":

        # Get the HR record
        htable = s3db.hrm_human_resource
        if not isinstance(record, Row):
            record = db(htable.id == record).select(htable.ALL,
                                                    limitby=(0, 1)).first()
        if not record:
            return

        # Find the person_ids to update
        update = pr_human_resource_update_affiliations
        person_id = None
        if record.deleted_fk:
            try:
                person_id = json.loads(record.deleted_fk)["person_id"]
            except:
                pass
        if person_id:
            update(person_id)
        if person_id != record.person_id:
            person_id = record.person_id
            if person_id:
                update(person_id)

    elif rtype == "pr_group_membership":

        mtable = s3db.pr_group_membership
        if not isinstance(record, Row):
            record = db(mtable.id == record).select(mtable.ALL,
                                                    limitby=(0, 1)).first()
        if not record:
            return
        pr_group_update_affiliations(record)

    elif rtype == "org_organisation_branch":

        ltable = s3db.org_organisation_branch
        if not isinstance(record, Row):
            record = db(ltable.id == record).select(ltable.ALL,
                                                    limitby=(0, 1)).first()
        if not record:
            return
        pr_organisation_update_affiliations(record)

    elif rtype == "org_site":

        pr_site_update_affiliations(record)

    return

# =============================================================================
def pr_organisation_update_affiliations(record):
    """
        Update affiliations for a branch organisation

        @param record: the org_organisation_branch record
    """

    db = current.db
    s3db = current.s3db

    if record.deleted and record.deleted_fk:
        try:
            fk = json.loads(record.deleted_fk)
            branch_id = fk["branch_id"]
        except:
            return
    else:
        branch_id = record.branch_id

    BRANCHES = "Branches"

    otable = s3db.org_organisation
    btable = otable.with_alias("branch")
    ltable = s3db.org_organisation_branch
    rtable = s3db.pr_role
    atable = s3db.pr_affiliation
    etable = s3db.pr_pentity

    o = otable._tablename
    b = btable._tablename
    r = rtable._tablename

    # Get current memberships
    query = (ltable.branch_id == branch_id) & \
            (ltable.deleted != True)
    left = [otable.on(ltable.organisation_id == otable.id),
            btable.on(ltable.branch_id == btable.id)]
    rows = db(query).select(otable.pe_id, btable.pe_id, left=left)
    current_memberships = [(row[o].pe_id, row[b].pe_id) for row in rows]

    # Get current affiliations
    query = (rtable.deleted != True) & \
            (rtable.role == BRANCHES) & \
            (rtable.pe_id == etable.pe_id) & \
            (etable.instance_type == o) & \
            (atable.deleted != True) & \
            (atable.role_id == rtable.id) & \
            (atable.pe_id == btable.pe_id) & \
            (btable.id == branch_id)
    rows = db(query).select(rtable.pe_id, btable.pe_id)
    current_affiliations = [(row[r].pe_id, row[b].pe_id) for row in rows]

    # Remove all affiliations which are not current memberships
    for a in current_affiliations:
        org, branch = a
        if a not in current_memberships:
            pr_remove_affiliation(org, branch, role=BRANCHES)
        else:
            current_memberships.remove(a)
    # Add affiliations for all new memberships
    for m in current_memberships:
        org, branch = m
        pr_add_affiliation(org, branch, role=BRANCHES, role_type=OU)
    return

# =============================================================================
def pr_group_update_affiliations(record):
    """
        Update affiliations for group memberships, currently this makes
        all members of a group organisational units of the group.

        @param record: the pr_membership record
    """

    db = current.db
    s3db = current.s3db

    MEMBERS = "Members"

    if record.deleted and record.deleted_fk:
        try:
            fk = json.loads(record.deleted_fk)
            person_id = fk["person_id"]
        except:
            return
    else:
        person_id = record.person_id

    ptable = s3db.pr_person
    gtable = s3db.pr_group
    mtable = s3db.pr_group_membership
    rtable = s3db.pr_role
    atable = s3db.pr_affiliation
    etable = s3db.pr_pentity

    g = gtable._tablename
    r = rtable._tablename
    p = ptable._tablename

    # Get current memberships
    query = (mtable.person_id == person_id) & \
            (mtable.deleted != True)
    left = [ptable.on(mtable.person_id == ptable.id),
            gtable.on(mtable.group_id == gtable.id)]
    rows = db(query).select(ptable.pe_id, gtable.pe_id, left=left)
    current_memberships = [(row[g].pe_id, row[p].pe_id) for row in rows]

    # Get current affiliations
    query = (rtable.deleted != True) & \
            (rtable.role == MEMBERS) & \
            (rtable.pe_id == etable.pe_id) & \
            (etable.instance_type == g) & \
            (atable.deleted != True) & \
            (atable.role_id == rtable.id) & \
            (atable.pe_id == ptable.pe_id) & \
            (ptable.id == person_id)
    rows = db(query).select(ptable.pe_id, rtable.pe_id)
    current_affiliations = [(row[r].pe_id, row[p].pe_id) for row in rows]

    # Remove all affiliations which are not current memberships
    for a in current_affiliations:
        group, person = a
        if a not in current_memberships:
            pr_remove_affiliation(group, person, role=MEMBERS)
        else:
            current_memberships.remove(a)
    # Add affiliations for all new memberships
    for m in current_memberships:
        group, person = m
        pr_add_affiliation(group, person, role=MEMBERS, role_type=OU)
    return

# =============================================================================
def pr_site_update_affiliations(record):
    """
        Update the affiliations of an org_site instance

        @param record: the org_site instance record
    """

    db = current.db
    s3db = current.s3db

    SITES = "Sites"

    otable = s3db.org_organisation
    stable = s3db.org_site
    rtable = s3db.pr_role
    ptable = s3db.pr_pentity
    atable = s3db.pr_affiliation

    o_pe_id = None
    s_pe_id = record.pe_id

    organisation_id = record.organisation_id
    if organisation_id:
        org = db(otable.id == organisation_id).select(otable.pe_id,
                                                      limitby=(0, 1)).first()
        if org:
            o_pe_id = org.pe_id
    if s_pe_id:
        query = (atable.deleted != True) & \
                (atable.pe_id == s_pe_id) & \
                (rtable.deleted != True) & \
                (rtable.id == atable.role_id) & \
                (rtable.role == SITES) & \
                (ptable.pe_id == rtable.pe_id) & \
                (ptable.instance_type == str(otable))
        rows = db(query).select(rtable.pe_id)
        seen = False
        for row in rows:
            if o_pe_id == None or o_pe_id != row.pe_id:
                pr_remove_affiliation(row.pe_id, s_pe_id, role=SITES)
            elif o_pe_id == row.pe_id:
                seen = True
        if o_pe_id and not seen:
            pr_add_affiliation(o_pe_id, s_pe_id, role=SITES, role_type=OU)
    return

# =============================================================================
def pr_human_resource_update_affiliations(person_id):
    """
        Update all affiliations related to the HR records of a person

        @param person_id: the person record ID
    """

    db = current.db
    s3db = current.s3db

    STAFF = "Staff"
    VOLUNTEER = "Volunteer"

    update = pr_human_resource_update_affiliations

    etable = s3db.pr_pentity
    ptable = s3db.pr_person
    rtable = s3db.pr_role
    atable = s3db.pr_affiliation
    htable = s3db.hrm_human_resource
    otable = s3db.org_organisation
    stable = s3db.org_site

    h = htable._tablename
    s = stable._tablename
    o = otable._tablename
    r = rtable._tablename
    e = etable._tablename

    # Get the PE-ID for this person
    pe_id = s3db.pr_get_pe_id("pr_person", person_id)

    # Get all current HR records
    query = (htable.person_id == person_id) & \
            (htable.status == 1) & \
            (htable.type.belongs((1,2))) & \
            (htable.deleted != True)
    left = [otable.on(htable.organisation_id == otable.id),
            stable.on(htable.site_id == stable.site_id)]
    rows = db(query).select(htable.site_id,
                            htable.type,
                            otable.pe_id,
                            stable.uuid,
                            stable.instance_type,
                            left=left)

    # Extract all master PE's
    masters = {STAFF:[], VOLUNTEER:[]}
    sites = Storage()
    for row in rows:
        if row[h].type == 1:
            role = STAFF
            site_id = row[h].site_id
            site_pe_id = None
            if site_id and site_id not in sites:
                itable = s3db.table(row[s].instance_type, None)
                if itable and "pe_id" in itable.fields:
                    q = itable.site_id == site_id
                    site = db(q).select(itable.pe_id,
                                        limitby=(0, 1)).first()
                    if site:
                        site_pe_id = sites[site_id] = site.pe_id
            else:
                site_pe_id = sites[site_id]
            if site_pe_id and site_pe_id not in masters[role]:
                masters[role].append(site_pe_id)
        elif row[h].type == 2:
            role = VOLUNTEER
        else:
            continue
        org_pe_id = row[o].pe_id
        if org_pe_id and org_pe_id not in masters[role]:
            masters[role].append(org_pe_id)

    # Get all current affiliations
    query = (ptable.id == person_id) & \
            (atable.deleted != True) & \
            (atable.pe_id == ptable.pe_id) & \
            (rtable.deleted != True) & \
            (rtable.id == atable.role_id) & \
            (rtable.role.belongs((STAFF, VOLUNTEER))) & \
            (etable.pe_id == rtable.pe_id) & \
            (etable.instance_type.belongs((o, s)))
    affiliations = db(query).select(rtable.id,
                                    rtable.pe_id,
                                    rtable.role,
                                    etable.instance_type)

    # Remove all affiliations which are not in masters
    for a in affiliations:
        pe = a[r].pe_id
        role = a[r].role
        if role in masters:
            if pe not in masters[role]:
                pr_remove_affiliation(pe, pe_id, role=role)
            else:
                masters[role].remove(pe)

    # Add affiliations to all masters which are not in current affiliations
    for role in masters:
        if role == VOLUNTEER:
            role_type = OTHER_ROLE
        else:
            role_type = OU
        for m in masters[role]:
            pr_add_affiliation(m, pe_id, role=role, role_type=role_type)

    return

# =============================================================================
def pr_add_affiliation(master, affiliate, role=None, role_type=OU):
    """
        Add a new affiliation record

        @param master: the master entity, either as PE-ID or as tuple
                       (instance_type, instance_id)
        @param affiliate: the affiliated entity, either as PE-ID or as tuple
                          (instance_type, instance_id)
        @param role: the role to add the affiliate to (will be created if it
                     doesn't yet exist)
        @param role_type: the type of the role, defaults to OU
    """

    db = current.db
    s3db = current.s3db

    if not role:
        return

    master_pe = pr_get_pe_id(master)
    affiliate_pe = pr_get_pe_id(affiliate)

    if master_pe and affiliate_pe:
        rtable = s3db.pr_role
        query = (rtable.pe_id == master_pe) & \
                (rtable.role == role) & \
                (rtable.deleted != True)
        row = db(query).select(limitby=(0, 1)).first()
        if not row:
            data = {"pe_id": master_pe,
                    "role": role,
                    "role_type": role_type}
            role_id = rtable.insert(**data)
        else:
            role_id = row.id
        if role_id:
            pr_add_to_role(role_id, affiliate_pe)
    return

# =============================================================================
def pr_remove_affiliation(master, affiliate, role=None):
    """
        Remove affiliation records

        @param master: the master entity, either as PE-ID or as tuple
                       (instance_type, instance_id), if this is None, then
                       all affiliations with all entities will be removed
        @param affiliate: the affiliated entity, either as PE-ID or as tuple
                          (instance_type, instance_id)
        @param affiliate: the affiliated PE, either as pe_id or as tuple
                          (instance_type, instance_id)
        @param role: name of the role to remove the affiliate from, if None,
                     the affiliate will be removed from all roles
    """

    db = current.db
    s3db = current.s3db

    master_pe = pr_get_pe_id(master)
    affiliate_pe = pr_get_pe_id(affiliate)

    if affiliate_pe:
        atable = s3db.pr_affiliation
        rtable = s3db.pr_role
        query = (atable.pe_id == affiliate_pe) & \
                (atable.role_id == rtable.id)
        if master_pe:
            query &= (rtable.pe_id == master_pe)
        if role:
            query &= (rtable.role == role)
        rows = db(query).select(rtable.id)
        for row in rows:
            pr_remove_from_role(row.id, affiliate_pe)
    return

# =============================================================================
# PE Helpers
# =============================================================================
#
def pr_get_pe_id(entity, record_id=None):
    """
        Get the PE-ID of an instance record

        @param entity: the entity, either a tablename, a tuple (tablename,
                       record_id), a Row of the instance type, or a PE-ID
        @param record_id: the record ID, if entity is a tablename

        @returns: the PE-ID
    """

    db = current.db
    s3db = current.s3db
    if record_id is not None:
        table, _id = entity, record_id
    elif isinstance(entity, (tuple, list)):
        table, _id = entity
    elif isinstance(entity, Row):
        if "pe_id" in entity:
            return entity["pe_id"]
        else:
            for f in entity.values():
                if isinstance(f, Row) and "pe_id" in f:
                    return f["pe_id"]
            return None
    else:
        return entity
    if not hasattr(table, "_tablename"):
        table = s3db.table(table, None)
    record = None
    if table:
        if "pe_id" in table.fields and _id:
            record = db(table._id==_id).select(table.pe_id,
                                               limitby=(0, 1)).first()
        elif _id:
            key = table._id.name
            if key == "pe_id":
                return _id
            if key != "id" and "instance_type" in table.fields:
                s = db(table._id==_id).select(table.instance_type,
                                              limitby=(0, 1)).first()
            else:
                return None
            if not s:
                return None
            table = s3db.table(s.instance_type, None)
            if table and "pe_id" in table.fields:
                record = db(table[key] == _id).select(table.pe_id,
                                                      limitby=(0, 1)).first()
            else:
                return None
    if record:
        return record.pe_id
    return None

# =============================================================================
# Back-end Role Tools
# =============================================================================
#
def pr_define_role(pe_id,
                   role=None,
                   role_type=None,
                   entity_type=None,
                   sub_type=None):
    """
        Back-end method to define a new affiliates-role for a person entity

        @param pe_id: the person entity ID
        @param role: the role name
        @param role_type: the role type (from pr_role_types), default 9
        @param entity_type: limit selection in CRUD forms to this entity type
        @param sub_type: limit selection in CRUD forms to this entity sub-type

        @returns: the role ID
    """

    db = current.db
    s3db = current.s3db

    if not pe_id:
        return
    if role_type not in s3db.pr_role_types:
        role_type = 9 # Other

    data = {"pe_id": pe_id,
            "role": role,
            "role_type": role_type,
            "entity_type": entity_type,
            "sub_type": sub_type}

    rtable = s3db.pr_role
    if role:
        query = (rtable.pe_id == pe_id) & \
                (rtable.role == role)
        duplicate = db(query).select(rtable.id,
                                     rtable.role_type,
                                     limitby=(0, 1)).first()
    else:
        duplicate = None
    if duplicate:
        if duplicate.role_type != role_type:
            # Clear paths if this changes the role type
            if str(role_type) != str(OU):
                data["path"] = None
            s3db.pr_role_rebuild_path(duplicate.id, clear=True)
        duplicate.update_record(**data)
        record_id = duplicate.id
    else:
        record_id = rtable.insert(**data)
    return record_id

# =============================================================================
def pr_delete_role(role_id):
    """
        Back-end method to delete a role

        @param role_id: the role ID
    """

    manager = current.manager
    resource = manager.define_resource("pr", "role", id=role_id)
    return resource.delete()

# =============================================================================
def pr_add_to_role(role_id, pe_id):
    """
        Back-end method to add a person entity to a role.

        @param role_id: the role ID
        @param pe_id: the person entity ID

        @todo: update descendant paths only if the role is a OU role
    """

    db = current.db
    s3db = current.s3db

    atable = s3db.pr_affiliation

    # Check for duplicate
    query = (atable.role_id == role_id) & (atable.pe_id == pe_id)
    affiliation = db(query).select(limitby=(0, 1)).first()
    if affiliation is None:
        # Insert affiliation record
        atable.insert(role_id=role_id, pe_id=pe_id)
        # Clear descendant paths (triggers lazy rebuild)
        pr_rebuild_path(pe_id, clear=True)
    return

# =============================================================================
def pr_remove_from_role(role_id, pe_id):
    """
        Back-end method to remove a person entity from a role.

        @param role_id: the role ID
        @param pe_id: the person entity ID

        @todo: update descendant paths only if the role is a OU role
    """

    db = current.db
    s3db = current.s3db

    atable = s3db.pr_affiliation

    query = (atable.role_id == role_id) & (atable.pe_id == pe_id)
    affiliation = db(query).select(limitby=(0, 1)).first()
    if affiliation is not None:
        # Soft-delete the record, clear foreign keys
        deleted_fk = {"role_id": role_id, "pe_id": pe_id}
        data = {"deleted": True,
                "role_id": None,
                "pe_id": None,
                "deleted_fk": json.dumps(deleted_fk)}
        affiliation.update_record(**data)
        # Clear descendant paths
        pr_rebuild_path(pe_id, clear=True)
    return

# =============================================================================
# Hierarchy Lookup
# =============================================================================
#
def pr_get_role_paths(pe_id, roles=None, role_types=None):
    """
        Get the ancestor paths of the ancestor OUs this person entity
        is affiliated with, sorted by roles.

        Used by gis.set_config()

        @param pe_id: the person entity ID
        @param roles: list of roles to limit the search
        @param role_types: list of role types to limit the search

        @returns: a Storage() of S3MultiPaths with the role names as keys

        @note: role_types is ignored if roles gets specified
    """

    db = current.db
    s3db = current.s3db

    atable = s3db.pr_affiliation
    rtable = s3db.pr_role

    query = (atable.deleted != True) & \
            (atable.role_id == rtable.id) & \
            (atable.pe_id == pe_id) & \
            (rtable.deleted != True)

    if roles is not None:
        # Limit the lookup to these roles
        if not isinstance(roles, (list, tuple)):
            roles = [roles]
        query &= (rtable.role.belongs(roles))
    elif role_types is not None:
        # Limit the lookup to these types of roles
        if not isinstance(role_types, (list, tuple)):
            role_types = [role_types]
        query &= (rtable.role_type.belongs(role_types))

    rows = db(query).select(rtable.role, rtable.path, rtable.pe_id)

    role_paths = Storage()
    for role in rows:
        name = role.role
        if name in role_paths:
            multipath = role_paths[name]
            multipath.append([role.pe_id])
        else:
            multipath = S3MultiPath([role.pe_id])
        path = pr_get_path(role.pe_id)
        multipath.extend(role.pe_id, path, cut=pe_id)
        role_paths[name] = multipath.clean()

    return role_paths

# =============================================================================
def pr_get_role_branches(pe_id,
                         roles=None,
                         role_types=None,
                         entity_type=None):
    """
        Get all descendants of the immediate ancestors of the entity
        within these roles/role types

        @param pe_id: the person entity ID
        @param roles: list of roles to limit the search
        @param role_types: list of role types to limit the search
        @param entity_type: limit the result to this entity type

        @returns: a list of PE-IDs

        @note: role_types is ignored if roles gets specified
    """

    db = current.db
    s3db = current.s3db

    rtable = s3db.pr_role
    atable = s3db.pr_affiliation
    etable = s3db.pr_pentity

    query = (atable.deleted != True) & \
            (atable.pe_id == pe_id) & \
            (atable.role_id == rtable.id) & \
            (rtable.pe_id == etable.pe_id)

    if roles is not None:
        # Limit the search to these roles
        if not isinstance(roles, (list, tuple)):
            roles = [roles]
        query &= (rtable.role.belongs(roles))

    elif role_types is not None:
        # Limit the search to these types of roles
        if not isinstance(role_types, (list, tuple)):
            role_types = [role_types]
        query &= (rtable.role_type.belongs(role_types))

    rows = db(query).select(rtable.pe_id, etable.instance_type)

    # Table names to retrieve the data from the rows
    rtn = rtable._tablename
    etn = etable._tablename

    # Get the immediate ancestors
    nodes = [r[rtn].pe_id for r in rows]

    # Filter the result by entity type
    result = [r[rtn].pe_id for r in rows
              if entity_type is None or r[etn].instance_type == entity_type]

    # Get the branches
    branches = pr_get_descendants(nodes, entity_type=entity_type)

    return result + branches

# =============================================================================
def pr_get_path(pe_id):
    """
        Get all ancestor paths of a person entity

        @param pe_id: the person entity ID

        @returns: an S3MultiPath instance
    """

    db = current.db
    s3db = current.s3db

    atable = s3db.pr_affiliation
    rtable = s3db.pr_role

    query = (atable.deleted != True) & \
            (atable.role_id == rtable.id) & \
            (atable.pe_id == pe_id) & \
            (rtable.deleted != True) & \
            (rtable.role_type == OU)
    roles = db(query).select(rtable.ALL)
    multipath = S3MultiPath()
    append = multipath.append
    for role in roles:
        path = S3MultiPath([role.pe_id])
        if role.path is None:
            ppath = pr_role_rebuild_path(role)
        else:
            ppath = S3MultiPath(role.path)
        path.extend(role.pe_id, ppath, cut=pe_id)
        for p in path.paths:
            append(p)
    return multipath.clean()

# =============================================================================
def pr_get_ancestors(pe_id):
    """
        Find all ancestor entities of a person entity in the OU hierarchy
        (performs a path lookup where paths are available, otherwise rebuilds
        paths).

        @param pe_id: the person entity ID
        @param roles: list of roles to limit the search

        @returns: a list of PE-IDs

        @todo: be able to filter by entity_type and subtype
    """

    db = current.db
    s3db = current.s3db

    atable = s3db.pr_affiliation
    rtable = s3db.pr_role

    query = (atable.deleted != True) & \
            (atable.role_id == rtable.id) & \
            (atable.pe_id == pe_id) & \
            (rtable.deleted != True) & \
            (rtable.role_type == OU)

    roles = db(query).select(rtable.ALL)

    paths = []
    append = paths.append
    for role in roles:
        path = S3MultiPath([role.pe_id])
        if role.path is None:
            ppath = pr_role_rebuild_path(role)
        else:
            ppath = S3MultiPath(role.path)
        path.extend(role.pe_id, ppath, cut=pe_id)
        append(path)
    ancestors = S3MultiPath.all_nodes(paths)

    return ancestors

# =============================================================================
def pr_get_descendants(pe_ids, skip=[], entity_type=None, ids=True):
    """
        Find descendant entities of a person entity in the OU hierarchy
        (performs a real search, not a path lookup).

        @param pe_ids: person entity ID or list of IDs
        @param skip: list of person entity IDs to skip during descending

        @returns: a list of PE-IDs
    """

    db = current.db
    s3db = current.s3db

    etable = s3db.pr_pentity
    rtable = s3db.pr_role
    atable = s3db.pr_affiliation

    en = etable._tablename
    an = atable._tablename

    if type(pe_ids) is not list:
        pe_ids = [pe_ids]
    pe_ids = [i for i in pe_ids if i not in skip]
    if not pe_ids:
        return []
    query = (rtable.deleted != True) & \
            (rtable.pe_id.belongs(pe_ids)) & \
            (~(rtable.pe_id.belongs(skip))) &\
            (rtable.role_type == OU) & \
            (atable.deleted != True) & \
            (atable.role_id == rtable.id) & \
            (etable.pe_id == atable.pe_id)
    skip = skip + pe_ids
    rows = db(query).select(atable.pe_id,
                            etable.instance_type)
    nodes = [(r[an].pe_id, r[en].instance_type) for r in rows]
    result = []
    append = result.append
    for n in nodes:
        if n not in result:
            append(n)
    node_ids = [n[0] for n in result]
    descendants = pr_get_descendants(node_ids, skip=skip, ids=False)
    for d in descendants:
        if d not in result:
            append(d)

    if ids:
        return [n[0]
                for n in result
                if entity_type is None or n[1] == entity_type]
    else:
        return result

# =============================================================================
# Internal Path Tools
# =============================================================================
#
def pr_rebuild_path(pe_id, clear=False):
    """
        Rebuild the ancestor path of all roles in the OU hierarchy a person
        entity defines.

        @param pe_id: the person entity ID
        @param clear: clear paths in descendant roles (triggers lazy rebuild)
    """

    db = current.db
    s3db = current.s3db

    if isinstance(pe_id, Row):
        pe_id = row.pe_id

    rtable = s3db.pr_role
    query = (rtable.deleted != True) & \
            (rtable.pe_id == pe_id) & \
            (rtable.role_type == OU)
    db(query).update(path=None)
    roles = db(query).select()
    for role in roles:
        if role.path is None:
            pr_role_rebuild_path(role, clear=clear)
    return

# =============================================================================
def pr_role_rebuild_path(role_id, skip=[], clear=False):
    """
        Rebuild the ancestor path of a role within the OU hierarchy

        @param role_id: the role ID
        @param skip: list of role IDs to skip during recursion
        @param clear: clear paths in descendant roles (triggers lazy rebuild)
    """

    db = current.db
    s3db = current.s3db

    rtable = s3db.pr_role
    atable = s3db.pr_affiliation

    if isinstance(role_id, Row):
        role = role_id
        role_id = role.id
    else:
        query = (rtable.deleted != True) & \
                (rtable.id == role_id)
        role = db(query).select(limitby=(0, 1)).first()
    if not role:
        return None
    pe_id = role.pe_id

    if role_id in skip:
        return role.path
    skip = skip + [role_id]

    if role.role_type != OU:
        path = None
    else:
        # Get all parent roles
        query = (atable.deleted != True) & \
                (atable.pe_id == pe_id) & \
                (rtable.deleted != True) & \
                (rtable.id == atable.role_id) & \
                (rtable.role_type == OU)
        parent_roles = db(query).select(rtable.ALL)

        # Update ancestor path
        path = S3MultiPath()
        for prole in parent_roles:
            path.append([prole.pe_id])
            if prole.path is None:
                ppath = pr_role_rebuild_path(prole, skip=skip)
            else:
                ppath = S3MultiPath(prole.path)
            if ppath is not None:
                path.extend(prole.pe_id, ppath, cut=pe_id)
        db(rtable.id == role_id).update(path=str(path))

    # Clear descendant paths, if requested (only necessary for writes)
    if clear:
        query = (rtable.deleted != True) & \
                (rtable.path.like("%%|%s|%%" % pe_id)) & \
                (~(rtable.id.belongs(skip)))
        db(query).update(path=None)

    return path

# END =========================================================================
