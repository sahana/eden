# -*- coding: utf-8 -*-

""" Sahana Eden Person Registry Model

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
           "S3PersonEducationModel",
           "S3PersonDetailsModel",
           "S3SavedSearch",
           "S3PersonPresence",
           "S3PersonDescription",
           "S3ImageLibraryModel",
           # Representation Methods
           "pr_get_entities",
           "pr_pentity_represent",
           "pr_person_represent",
           "pr_person_comment",
           "pr_image_represent",
           "pr_url_represent",
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
           "pr_realm",
           "pr_realm_users",
           "pr_get_role_paths",
           "pr_get_role_branches",
           "pr_get_path",
           "pr_get_ancestors",
           "pr_get_descendants",
           "pr_ancestors",
           "pr_descendants",
           # Internal Path Tools
           "pr_rebuild_path",
           "pr_role_rebuild_path",
           # Helpers for ImageLibrary
           "pr_image_modify",
           "pr_image_resize",
           "pr_image_format",
           ]

import os
import re

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

from gluon import *
from gluon.dal import Row
from gluon.storage import Storage
from gluon.sqlhtml import RadioWidget

from ..s3 import *
from layouts import *
from eden.layouts import S3AddResourceLink

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
             "pr_pe_types"
             ]

    def model(self):

        db = current.db
        T = current.T

        add_component = self.add_component
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        super_entity = self.super_entity
        super_key = self.super_key
        super_link = self.super_link

        messages = current.messages
        YES = T("yes") #messages.YES
        NO = T("no") #messages.NO
        UNKNOWN_OPT = messages.UNKNOWN_OPT

        # ---------------------------------------------------------------------
        # Person Super-Entity
        #
        #if current.deployment_settings.get_ui_camp():
        #    shelter = T("Camp")
        #else:
        #    shelter = T("Shelter")
        pe_types = Storage(pr_person = T("Person"),
                           pr_group = T("Group"),
                           org_organisation = messages.ORGANISATION,
                           org_office = T("Office"),
                           inv_warehouse = T("Warehouse"),
                           # If we want these, then pe_id needs adding to their
                           # tables & configuring as a super-entity
                           #cr_shelter = shelter,
                           #fire_station = T("Fire Station"),
                           dvi_morgue = T("Morgue"),
                           hms_hospital = T("Hospital"),
                           dvi_body = T("Body"))

        tablename = "pr_pentity"
        table = super_entity(tablename, "pe_id", pe_types,
                             #super_link("source_id", "doc_source_entity"),
                             Field("type"),
                             Field("pe_label", length=128))

        # Search method
        pentity_search = S3PentitySearch(name = "pentity_search_simple",
                                         label = T("Name and/or ID"),
                                         comment = "",
                                         field = ["pe_label"])

        pentity_search.pentity_represent = pr_pentity_represent

        # Resource configuration
        configure(tablename,
                  list_fields = ["instance_type", "type", "pe_label"],
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
        add_component("pr_role", pr_pentity=pe_id)
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

        add_component("pr_saved_search", pr_pentity=pe_id)

        # ---------------------------------------------------------------------
        # Person <-> User
        #
        utable = current.auth.settings.table_user
        tablename = "pr_person_user"
        table = define_table(tablename,
                             super_link("pe_id", "pr_pentity"),
                             Field("user_id", utable),
                             *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Role (Affiliates Group)
        #
        role_types = {
            1:T("Organization Units"),    # business hierarchy (reporting units)
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
                             *s3_meta_fields())

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
        role_id = S3ReusableField("role_id", table,
                                  requires = IS_ONE_OF(db, "pr_role.id",
                                                       self.pr_role_represent),
                                  represent = self.pr_role_represent,
                                  label = T("Role"),
                                  ondelete = "CASCADE")

        add_component("pr_affiliation", pr_role="role_id")

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
                             *s3_meta_fields())

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
        # Return model-global names to s3db.*
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
        table = db.pr_role
        role = db(table.id == role_id).select(table.role,
                                              table.pe_id,
                                              limitby=(0, 1)).first()
        try:
            entity = pr_pentity_represent(role.pe_id)
            return "%s: %s" % (entity, role.role)
        except:
            return current.messages.UNKNOWN_OPT

    # -------------------------------------------------------------------------
    @staticmethod
    def pr_role_onvalidation(form):
        """
            Clear descendant paths if role type has changed

            @param form: the CRUD form
        """

        formvars = form.vars
        if not formvars:
            return
        if "role_type" in formvars:
            role_id = form.record_id
            if not role_id:
                return
            role_type = formvars.role_type
            db = current.db
            rtable = db.pr_role
            role = db(rtable.id == role_id).select(rtable.role_type,
                                                   limitby=(0, 1)).first()
            if role and str(role.role_type) != str(role_type):
                # If role type has changed, then clear paths
                if str(role_type) != str(OU):
                    formvars["path"] = None
                current.s3db.pr_role_rebuild_path(role_id, clear=True)
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

        formvars = form.vars
        role_id = formvars["role_id"]
        pe_id = formvars["pe_id"]
        record_id = formvars["id"]

        if role_id and pe_id and record_id:
            # Remove duplicates
            db = current.db
            atable = db.pr_affiliation
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
            current.s3db.pr_rebuild_path(pe_id, clear=True)
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def pr_affiliation_ondelete(row):
        """
            Clear descendant paths, also called indirectly via
            ondelete-CASCADE when a role gets deleted.

            @param row: the deleted row
        """

        if row and row.id:
            db = current.db
            atable = db.pr_affiliation
            query = (atable.id == row.id)
            record = db(query).select(atable.deleted_fk,
                                      limitby=(0, 1)).first()
        else:
            return
        if record and record.deleted_fk:
            data = json.loads(record.deleted_fk)
            pe_id = data.get("pe_id", None)
            if pe_id:
                current.s3db.pr_rebuild_path(pe_id, clear=True)
        return

# =============================================================================
class S3OrgAuthModel(S3Model):
    """ Organisation-based Authorization Model """

    names = ["pr_delegation"]

    def model(self):

        # ---------------------------------------------------------------------
        # Delegation: Role <-> Auth Group Link
        # This "delegates" the permissions of a user group for the records
        # owned by a person entity to a group of affiliated entities.
        #
        gtable = current.auth.settings.table_group
        tablename = "pr_delegation"
        table = self.define_table(tablename,
                                  current.s3db.pr_role_id(),
                                  Field("group_id", gtable,
                                        ondelete="CASCADE"),
                                  *s3_meta_fields())

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
        gis = current.gis
        settings = current.deployment_settings

        messages = current.messages
        UNKNOWN_OPT = messages.UNKNOWN_OPT

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
                                    label = T("Sex"),
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

        tablename = "pr_person"
        table = define_table(tablename,
                             super_link("pe_id", "pr_pentity"),
                             super_link("track_id", "sit_trackable"),
                             # Base location
                             self.gis_location_id(readable=False,
                                                  writable=False),
                             self.pr_pe_label(
                                comment = DIV(_class="tooltip",
                                              _title="%s|%s" % (T("ID Tag Number"),
                                                                T("Number or Label on the identification tag this person is wearing (if any).")))),
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
                             Field("first_name", notnull=True,
                                   default = "?" if current.auth.permission.format != "html" else "",
                                   length=64, # Mayon Compatibility
                                   # NB Not possible to have an IS_NAME() validator here
                                   # http://eden.sahanafoundation.org/ticket/834
                                   requires = IS_NOT_EMPTY(error_message = T("Please enter a first name")),
                                   comment =  DIV(_class="tooltip",
                                                  _title="%s|%s" % (T("First Name"),
                                                                    T("The first or only name of the person (mandatory)."))),
                                   label = T("First Name")),
                             Field("middle_name", length=64, # Mayon Compatibility
                                   label = T("Middle Name")),
                             Field("last_name", length=64, # Mayon Compatibility
                                   label = T("Last Name"),
                                   requires = last_name_validate),
                             Field("initials", length=8,
                                   label = T("Initials")),
                             Field("preferred_name", length=64, # Mayon Compatibility
                                   label = T("Preferred Name"),
                                   comment = DIV(DIV(_class="tooltip",
                                                     _title="%s|%s" % (T("Preferred Name"),
                                                                       T("The name to be used when calling for or directly addressing the person (optional).")))),
                                   ),
                             # @ToDo: Move these fields to a component to keep the main heavily-used table as clean as possible
                             Field("local_name",
                                   label = T("Local Name"),
                                    comment = DIV(DIV(_class="tooltip",
                                                        _title="%s|%s" % (T("Local Name"),
                                                                        T("Name of the person in local language and script (optional)."))))),
                             pr_gender(label = T("Sex")),
                             s3_date("date_of_birth",
                                     label = T("Date of Birth"),
                                     past = 1320,  # Months, so 110 years
                                     ),
                             pr_age_group(
                                    readable = False,
                                    writable = False,
                                    ),
                             Field("opt_in", "string", # list of mailing lists which link to teams
                                   default=False,
                                   label = T("Receive updates"),
                                   comment = DIV(DIV(_class="tooltip",
                                                     _title="%s|%s" % (T("Mailing list"),
                                                                       T("By selecting this you agree that we may contact you.")))),
                                   ),
                             s3_comments(),
                             # @ToDo: Remove the lx_fields when we can Search person_id$location_id$Lx
                             *(s3_lx_fields() + s3_meta_fields()))

        # CRUD Strings
        ADD_PERSON = messages.ADD_PERSON
        current.response.s3.crud_strings[tablename] = Storage(
            title_create = T("Add a Person"),
            title_display = T("Person Details"),
            title_list = T("Persons"),
            title_update = T("Edit Person Details"),
            title_search = T("Search Persons"),
            subtitle_create = ADD_PERSON,
            label_list_button = T("List Persons"),
            label_create_button = ADD_PERSON,
            label_delete_button = T("Delete Person"),
            msg_record_created = T("Person added"),
            msg_record_modified = T("Person details updated"),
            msg_record_deleted = T("Person deleted"),
            msg_list_empty = T("No Persons currently registered"))

        # add an opt in clause to receive emails depending on the deployment settings
        if settings.get_auth_opt_in_to_email():
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
                                       "identity.value"
                                      ])

        # Custom Form
        crud_form = s3forms.S3SQLCustomForm("first_name",
                                            "last_name",
                                            "age_group",
                                            "date_of_birth",
                                            "initials",
                                            "preferred_name",
                                            "local_name",
                                            "gender",
                                            "person_details.marital_status",
                                            "age_group",
                                            "person_details.nationality",
                                            "person_details.religion",
                                            "person_details.mother_name",
                                            "person_details.father_name",
                                            "person_details.occupation",
                                            "person_details.company",
                                            "person_details.affiliations",
                                            "comments",
                                            )

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
                                       (messages.ORGANISATION, "hrm_human_resource:organisation_id$name")
                                       ],
                        crud_form = crud_form,
                        onvalidation=self.pr_person_onvalidation,
                        onaccept=self.pr_person_onaccept,
                        search_method=pr_person_search,
                        deduplicate=self.person_deduplicate,
                        main="first_name",
                        extra="last_name",
                        realm_components = ["presence"],
                        )

        person_id_comment = pr_person_comment(
                                    T("Person"),
                                    T("Type the first few characters of one of the Person's names."),
                                    child="person_id")

        person_id = S3ReusableField("person_id", table,
                                    sortby = ["first_name", "middle_name", "last_name"],
                                    requires = IS_NULL_OR(
                                                IS_ONE_OF(db, "pr_person.id",
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
        add_component("pr_education", pr_person="person_id")
        add_component("pr_person_details", pr_person=dict(joinby="person_id",
                                                          multiple=False))
        add_component("pr_save_search", pr_person="person_id")
        add_component("msg_subscription", pr_person="person_id")

        add_component("member_membership", pr_person="person_id")

        # HR Record
        add_component("hrm_human_resource", pr_person="person_id")

        # Skills
        add_component("hrm_certification", pr_person="person_id")
        add_component("hrm_competency", pr_person="person_id")
        add_component("hrm_credential", pr_person="person_id")
        # @ToDo: Double link table to show the Courses attended?
        add_component("hrm_training", pr_person="person_id")

        # Experience
        add_component("hrm_experience", pr_person="person_id")
        add_component("hrm_programme_hours", pr_person=Storage(
                                                name="hours",
                                                joinby="person_id"))

        # Assets
        add_component("asset_asset", pr_person="assigned_to_id")

        # ---------------------------------------------------------------------
        # Return model-global names to s3db.*
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
            now = current.request.utcnow
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
                form.errors.age_group = current.T("Age group does not match actual age.")

    # -------------------------------------------------------------------------
    @staticmethod
    def pr_person_onaccept(form):
        """
            Onaccept callback
            Update any user associated with this person
        """

        db = current.db
        s3db = current.s3db

        vars = form.vars
        person_id = vars.id

        ptable = s3db.pr_person
        ltable = s3db.pr_person_user
        utable = current.auth.settings.table_user

        # Find a user for this person
        query = (ptable.id == person_id) & \
                (ltable.pe_id == ptable.pe_id) & \
                (utable.id == ltable.user_id)
        user = db(query).select(utable.id,
                                utable.first_name,
                                utable.last_name,
                                limitby=(0, 1)).first()

        # If there is a user and their first or last name have changed
        if user and vars.first_name and \
           (user.first_name != vars.first_name or \
            user.last_name != vars.last_name):
            # Update the user record
            query = (utable.id == user.id)
            db(query).update(first_name = vars.first_name,
                             last_name = vars.last_name,
                             )

    # -------------------------------------------------------------------------
    @staticmethod
    def person_deduplicate(item):
        """ Import item deduplication """

        db = current.db
        ptable = db.pr_person
        s3db = current.s3db
        etable = s3db.pr_contact.with_alias("pr_email")
        stable = s3db.pr_contact.with_alias("pr_sms")

        left = [etable.on((etable.pe_id == ptable.pe_id) & \
                          (etable.contact_method == "EMAIL")),
                stable.on((stable.pe_id == ptable.pe_id) & \
                          (stable.contact_method == "SMS"))]

        data = item.data
        fname = lname = None
        if "first_name" in data:
            fname = data["first_name"]
        if "last_name" in data:
            lname = data["last_name"]
        initials = dob = None
        if "initials" in data:
            initials = data["initials"]
        if "date_of_birth" in data:
            dob = data["date_of_birth"]
        email = sms = None
        for citem in item.components:
            if citem.tablename == "pr_contact":
                data = citem.data
                if "contact_method" in data and \
                    data.contact_method == "EMAIL":
                    email = data.value
                elif "contact_method" in data and \
                        data.contact_method == "SMS":
                    sms = data.value

        if fname and lname:
            query = (ptable.first_name.lower() == fname.lower()) & \
                    (ptable.last_name.lower() == lname.lower())
        elif initials:
            query = (ptable.initials.lower() == initials.lower())
        else:
            return
        candidates = db(query).select(ptable._id,
                                      ptable.first_name,
                                      ptable.last_name,
                                      ptable.initials,
                                      ptable.date_of_birth,
                                      etable.value,
                                      stable.value,
                                      left=left,
                                      orderby=["pr_person.created_on ASC"])

        duplicates = Storage()

        def rank(a, b, match, mismatch):
            if a and b:
                return match if a == b else mismatch
            else:
                return untested

        for row in candidates:
            row_fname = row[ptable.first_name]
            row_lname = row[ptable.last_name]
            row_initials = row[ptable.initials]
            row_dob = row[ptable.date_of_birth]
            row_email = row[etable.value]
            row_sms = row[stable.value]

            check = 0

            if fname and row_fname:
                check += rank(fname.lower(), row_fname.lower(), +2, -2)

            if lname and row_lname:
                check += rank(lname.lower(), row_lname.lower(), +2, -2)

            if dob and row_dob:
                check += rank(dob, row_dob, +3, -2)

            if email and row_email:
                check += rank(email.lower(), row_email.lower(), +2, -5)
            elif not email:
                # Treat missing email as mismatch
                check -= 2 if initials else 3 if not row_email else 4

            if initials and row_initials:
                check += rank(initials.lower(), row_initials.lower(), +4, -1)

            if sms and row_sms:
                check += rank(sms.lower(), row_sms.lower(), +1, -1)

            if check in duplicates:
                continue
            else:
                duplicates[check] = row

        duplicate = None
        if len(duplicates):
            best_match = max(duplicates.keys())
            if best_match > 0:
                duplicate = duplicates[best_match]
                item.id = duplicate[ptable.id]
                item.method = item.METHOD.UPDATE
                for citem in item.components:
                    citem.method = citem.METHOD.UPDATE
        return

# =============================================================================
class S3GroupModel(S3Model):
    """ Groups """

    names = ["pr_group",
             "pr_group_id",
             "pr_group_represent",
             "pr_group_membership"
             ]

    def model(self):

        T = current.T
        db = current.db

        messages = current.messages
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

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
                                        pr_group_types.get(opt, messages.UNKNOWN_OPT)),
                             Field("system", "boolean",
                                   default=False,
                                   readable=False,
                                   writable=False),
                             Field("name",
                                   label=T("Group Name"),
                                   requires = IS_NOT_EMPTY()),
                             Field("description",
                                   label=T("Group Description"),
                                   comment = DIV(_class="tooltip",
                                                 _title="%s|%s" % (T("Group description"),
                                                                   T("A brief description of the group (optional)")))
                                   ),
                             s3_comments(),
                             *s3_meta_fields())

        # CRUD Strings
        ADD_GROUP = T("Add Group")
        crud_strings[tablename] = Storage(
            title_create = ADD_GROUP,
            title_display = T("Group Details"),
            title_list = T("Groups"),
            title_update = T("Edit Group"),
            title_search = T("Search Groups"),
            subtitle_create = T("Add New Group"),
            label_list_button = T("List Groups"),
            label_create_button = ADD_GROUP,
            label_delete_button = T("Delete Group"),
            msg_record_created = T("Group added"),
            msg_record_modified = T("Group updated"),
            msg_record_deleted = T("Group deleted"),
            msg_list_empty = T("No Groups currently registered"))

        # CRUD Strings
        ADD_GROUP = T("Add Mailing List")
        mailing_list_crud_strings = Storage(
            title_create = ADD_GROUP,
            title_display = T("Mailing List Details"),
            title_list = T("Mailing Lists"),
            title_update = T("Edit Mailing List"),
            title_search = T("Search Mailing Lists"),
            subtitle_create = T("Add New Mailing List"),
            label_list_button = T("List Mailing Lists"),
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
        group_id = S3ReusableField("group_id", table,
                                   sortby="name",
                                   requires = IS_NULL_OR(
                                                IS_ONE_OF(db, "pr_group.id",
                                                          self.group_represent,
                                                          filterby="system",
                                                          filter_opts=(False,))),
                                   represent = self.group_represent,
                                   comment=S3AddResourceLink(c="pr",
                                                             f="group",
                                                             label=crud_strings.pr_group.label_create_button,
                                                             title=T("Create Group Entry"),
                                                             tooltip=T("Create a group entry in the registry.")),
                                   ondelete = "RESTRICT")

        # Components
        self.add_component("pr_group_membership", pr_group="group_id")

        # ---------------------------------------------------------------------
        # Group membership
        #
        tablename = "pr_group_membership"
        table = define_table(tablename,
                             group_id(label = T("Group"),
                                      ondelete="CASCADE"),
                             self.pr_person_id(label = T("Person"),
                                               ondelete="CASCADE"),
                             Field("group_head", "boolean",
                                   label = T("Group Head"),
                                   default=False,
                                   represent = lambda group_head: \
                                    (group_head and [T("yes")] or [""])[0]),
                             Field("description",
                                   label = T("Description")),
                             s3_comments(),
                             *s3_meta_fields())

        # CRUD strings
        function = current.request.function
        if function in ("person", "group_membership"):
            crud_strings[tablename] = Storage(
                title_create = T("Add Membership"),
                title_display = T("Membership Details"),
                title_list = T("Memberships"),
                title_update = T("Edit Membership"),
                title_search = T("Search Membership"),
                subtitle_create = T("Add New Membership"),
                label_list_button = T("List Memberships"),
                label_create_button = T("Add Membership"),
                label_delete_button = T("Delete Membership"),
                msg_record_created = T("Membership added"),
                msg_record_modified = T("Membership updated"),
                msg_record_deleted = T("Membership deleted"),
                msg_list_empty = T("No Memberships currently registered"))

        elif function == "group":
            crud_strings[tablename] = Storage(
                title_create = T("Add Member"),
                title_display = T("Membership Details"),
                title_list = T("Group Members"),
                title_update = T("Edit Membership"),
                title_search = T("Search Member"),
                subtitle_create = T("Add New Member"),
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
        # Return model-global names to s3db.*
        #
        return Storage(
            pr_group_id = group_id,
            pr_group_represent = self.group_represent,
            pr_mailing_list_crud_strings = mailing_list_crud_strings
        )

    # -------------------------------------------------------------------------
    @staticmethod
    def group_represent(id, row=None):
        """ FK representation """

        if row:
            return row.name
        elif not id:
            return current.messages.NONE

        db = current.db
        table = db.pr_group
        r = db(table.id == id).select(table.name,
                                      limitby = (0, 1)).first()
        try:
            return r.name
        except:
            return current.messages.UNKNOWN_OPT

    # -------------------------------------------------------------------------
    @staticmethod
    def group_deduplicate(item):
        """ Group de-duplication """

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

        if hasattr(form, "vars"):
            _id = form.vars.id
        elif isinstance(form, Row) and "id" in form:
            _id = form.id
        else:
            return

        db = current.db
        mtable = db.pr_group_membership

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

        define_table = self.define_table
        super_link = self.super_link

        # ---------------------------------------------------------------------
        # Contact
        #
        # @ToDo: Provide widgets which can be dropped into the main person form to have
        #        the relevant ones for that deployment/context collected on that same
        #        form
        #
        contact_methods = current.msg.CONTACT_OPTS

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
                                        contact_methods.get(opt, current.messages.UNKNOWN_OPT)),
                             Field("value",
                                   label= T("Value"),
                                   notnull=True,
                                   requires = IS_NOT_EMPTY(),
                                  ),
                             Field("priority", "integer",
                                   label= T("Priority"),
                                   comment = DIV(_class="tooltip",
                                                 _title="%s|%s" % (T("Priority"),
                                                                   T("What order to be contacted in."))),
                                   requires = IS_IN_SET(range(1, 10), zero=None)),
                             s3_comments(),
                             *s3_meta_fields())

        # Field configuration
        table.pe_id.requires = IS_ONE_OF(current.db, "pr_pentity.pe_id",
                                         pr_pentity_represent,
                                         orderby="instance_type",
                                         filterby="instance_type",
                                         filter_opts=("pr_person", "pr_group"))

        # CRUD Strings
        current.response.s3.crud_strings[tablename] = Storage(
            title_create = T("Add Contact Information"),
            title_display = T("Contact Details"),
            title_list = T("Contact Information"),
            title_update = T("Edit Contact Information"),
            title_search = T("Search Contact Information"),
            subtitle_create = T("Add Contact Information"),
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
                             s3_comments(),
                             *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Return model-global names to s3db.*
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
                form.errors.value = current.T("Enter a valid email")
        return False

    # -------------------------------------------------------------------------
    @staticmethod
    def contact_deduplicate(item):
        """ Contact information de-duplication """

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
        messages = current.messages
        settings = current.deployment_settings

        # ---------------------------------------------------------------------
        # Address
        #
        pr_address_type_opts = {
            1:T("Current Home Address"),
            2:T("Permanent Home Address"),
            3:T("Office Address"),
            #4:T("Holiday Address"),
            9:T("Other Address")
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
                                                    pr_address_type_opts.get(opt,
                                                        messages.UNKNOWN_OPT)),
                                  self.gis_location_id(),
                                  s3_comments(),
                                  *s3_meta_fields())

        table.pe_id.requires = IS_ONE_OF(current.db, "pr_pentity.pe_id",
                                         pr_pentity_represent,
                                         orderby="instance_type",
                                         filterby="instance_type",
                                         filter_opts=("pr_person", "pr_group"))

        # CRUD Strings
        ADD_ADDRESS = T("Add Address")
        current.response.s3.crud_strings[tablename] = Storage(
            title_create = ADD_ADDRESS,
            title_display = T("Address Details"),
            title_list = T("Addresses"),
            title_update = T("Edit Address"),
            title_search = T("Search Addresses"),
            subtitle_create = T("Add New Address"),
            label_list_button = T("List Addresses"),
            label_create_button = ADD_ADDRESS,
            msg_record_created = T("Address added"),
            msg_record_modified = T("Address updated"),
            msg_record_deleted = T("Address deleted"),
            msg_list_empty = T("There is no address for this person yet. Add new address."))

        # Resource configuration
        self.configure(tablename,
                       onaccept=self.address_onaccept,
                       onvalidation=s3_address_onvalidation,
                       deduplicate=self.address_deduplicate,
                       list_fields = ["id",
                                      "type",
                                      (T("Address"), "location_id$addr_street"),
                                      (settings.get_ui_label_postcode(), "location_id$addr_postcode"),
                                      #"location_id$L4",
                                      "location_id$L3",
                                      "location_id$L2",
                                      "location_id$L1",
                                      (messages.COUNTRY, "location_id$L0"),
                                      ])

        # ---------------------------------------------------------------------
        # Return model-global names to s3db.*
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

        vars = form.vars
        location_id = vars.location_id
        if not location_id:
            return

        db = current.db
        s3db = current.s3db
        atable = db.pr_address
        pe_id = db(atable.id == vars.id).select(atable.pe_id,
                                                limitby=(0, 1)).first().pe_id
        requestvars = current.request.vars
        settings = current.deployment_settings
        person = None
        table = s3db.pr_person
        if "base_location" in requestvars and \
           requestvars.base_location == "on":
            # Specifically requested
            S3Tracker()(s3db.pr_pentity, pe_id).set_base_location(location_id)
            person = db(table.pe_id == pe_id).select(table.id,
                                                     limitby=(0, 1)).first()
            if person:
                # Update the Lx fields
                s3_lx_update(table, person.id)
        else:
            # Check if a base location already exists
            query = (table.pe_id == pe_id)
            person = db(query).select(table.id,
                                      table.location_id).first()
            if person and not person.location_id:
                # Hasn't yet been set so use this
                S3Tracker()(s3db.pr_pentity, pe_id).set_base_location(location_id)
                # Update the Lx fields
                s3_lx_update(table, person.id)

        if person and str(vars.type) == "1": # Home Address
            if settings.has_module("hrm"):
                # Also check for any Volunteer HRM record(s)
                htable = s3db.hrm_human_resource
                query = (htable.person_id == person.id) & \
                        (htable.type == 2) & \
                        (htable.deleted != True)
                hrs = db(query).select(htable.id)
                for hr in hrs:
                    db(htable.id == hr.id).update(location_id=location_id)
                    # Update the Lx fields
                    #s3_lx_update(htable, hr.id)
            if settings.has_module("member"):
                # Also check for any Member record(s)
                mtable = s3db.member_membership
                query = (mtable.person_id == person.id) & \
                        (mtable.deleted != True)
                members = db(query).select(mtable.id)
                for member in members:
                    db(mtable.id == member.id).update(location_id=location_id)
                    # Update the Lx fields
                    #s3_lx_update(mtable, member.id)

    # -------------------------------------------------------------------------
    @staticmethod
    def address_deduplicate(item):
        """ Address de-duplication """

        if item.tablename == "pr_address":
            data = item.data
            pe_id = data.get("pe_id", None)
            address = data.get("address", None)

            if pe_id is None:
                return

            table = item.table
            db = current.db
            ltable = db.gis_location
            query = (table.pe_id == pe_id) & \
                    (ltable.id == table.location_id) & \
                    (ltable.addr_street == address) & \
                    (table.deleted != True)
            duplicate = db(query).select(table.id,
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
                                  Field("image", "upload", autodelete=True,
                                        represent = self.pr_image_represent,
                                        comment =  DIV(_class="tooltip",
                                                       _title="%s|%s" % (T("Image"),
                                                                         T("Upload an image file here. If you don't upload an image file, then you must specify its location in the URL field.")))),
                                  Field("url",
                                        label = T("URL"),
                                        represent = pr_url_represent,
                                        comment = DIV(_class="tooltip",
                                                      _title="%s|%s" % (T("URL"),
                                                                       T("The URL of the image file. If you don't upload an image file, then you must specify its location here.")))),
                                  Field("type", "integer",
                                        requires = IS_IN_SET(pr_image_type_opts, zero=None),
                                        default = 1,
                                        label = T("Image Type"),
                                        represent = lambda opt: \
                                            pr_image_type_opts.get(opt,
                                                                   current.messages.UNKNOWN_OPT)),
                                  s3_comments("description",
                                              label=T("Description"),
                                              comment = DIV(_class="tooltip",
                                                            _title="%s|%s" % (T("Description"),
                                                                              T("Give a brief description of the image, e.g. what can be seen where on the picture (optional).")))),
                                  *s3_meta_fields())

        # CRUD Strings
        current.response.s3.crud_strings[tablename] = Storage(
            title_create = T("Image"),
            title_display = T("Image Details"),
            title_list = T("Images"),
            title_update = T("Edit Image Details"),
            title_search = T("Search Images"),
            subtitle_create = T("Add New Image"),
            label_list_button = T("List Images"),
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
                       ondelete = self.pr_image_ondelete,
                       #mark_required = ["url", "image"],
                       list_fields=["id",
                                    "title",
                                    "profile",
                                    "type",
                                    "image",
                                    "url",
                                    "description"
                                    ])

        # ---------------------------------------------------------------------
        # Return model-global names to s3db.*
        #
        return Storage()

    # -------------------------------------------------------------------------
    @staticmethod
    def pr_image_represent(image, size=None):
        """ Representation """

        if not image:
            return current.messages.NONE
        url_full = URL(c="default", f="download", args=image)
        if size is None:
            size = (None, 60)
        image = pr_image_represent(image, size=size)
        url_small = URL(c="default", f="download", args=image)

        return DIV(A(IMG(_src=url_small, _height=size[1]), _href=url_full))

    # -------------------------------------------------------------------------
    @staticmethod
    def pr_image_onaccept(form):
        """
            If this is the profile image then remove this flag from all
            others for this person.
        """

        vars = form.vars
        id = vars.id
        profile = vars.profile
        url = vars.url
        newfilename = vars.image_newfilename
        if profile == "False":
            profile = False

        if newfilename:
            _image = form.request_vars.image
            pr_image_resize(_image.file,
                            newfilename,
                            _image.filename,
                            (50, 50)
                            )
            pr_image_resize(_image.file,
                            newfilename,
                            _image.filename,
                            (None, 60)
                            )

            pr_image_resize(_image.file,
                            newfilename,
                            _image.filename,
                            (160, None)
                            )

        if profile:
            # Find the pe_id
            db = current.db
            table = db.pr_image
            pe = db(table.id == id).select(table.pe_id,
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

        vars = form.vars
        image = vars.image
        url = vars.url

        if not hasattr(image, "file"):
            id = current.request.post_vars.id
            if id:
                db = current.db
                table = db.pr_image
                record = db(table.id == id).select(table.image,
                                                   limitby=(0, 1)).first()
                if record:
                    image = record.image

        if not hasattr(image, "file") and not image and not url:
            form.errors.image = \
            form.errors.url = current.T("Either file upload or image URL required.")
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def pr_image_ondelete(row):
        """
            If a PR Image is deleted, delete the thumbnails too
        """

        db = current.db
        table = db.pr_image
        row = db(table.id == row.id).select(table.image,
                                            limitby=(0, 1)).first()
        current.s3db.pr_image_delete_all(row.image)

# =============================================================================
class S3ImageLibraryModel(S3Model):
    """
        Image Model

        This is used to store modified copies of images held in other tables.
        The modifications can be:
         * different file type (bmp, jpeg, gif, png etc)
         * different size (thumbnails)

        This has been included in the pr module because:
        pr uses it (but so do other modules), pr is a compulsory module
        and this should also be compulsory but didn't want to create a
        new compulsory module just for this.
    """

    names = ["pr_image_library",
             "pr_image_size",
             "pr_image_delete_all",
             ]

    def model(self):

        #T = current.T

        # ---------------------------------------------------------------------
        tablename = "pr_image_library"
        table = self.define_table(tablename,
                                  # Original image file name
                                  Field("original_name"),
                                  # New image file name
                                  Field("new_name", "upload",
                                        autodelete=True,
                                        ),
                                  # New file format name
                                  Field("format"),
                                  # New requested file dimensions
                                  Field("width", "integer"),
                                  Field("height", "integer"),
                                  # New actual file dimensions
                                  Field("actual_width", "integer"),
                                  Field("actual_height", "integer")
                                )

        # ---------------------------------------------------------------------
        # Return model-global names to s3db.*
        #
        return Storage(
            pr_image_size = self.pr_image_size,
            pr_image_delete_all = self.pr_image_delete_all,
        )

    # -----------------------------------------------------------------------------
    @staticmethod
    def pr_image_size(image_name, size):
        """
            Used by s3_avatar_represent()
        """

        db = current.db
        table = db.pr_image_library
        image = db(table.new_name == image_name).select(table.actual_height,
                                                        table.actual_width,
                                                        limitby=(0, 1)).first()
        if image:
            return (image.actual_width, image.actual_height)
        else:
            return size

    # -----------------------------------------------------------------------------
    @staticmethod
    def pr_image_delete_all(original_image_name):
        """
            Method to delete all the images that belong to
            the original file.
        """

        if current.deployment_settings.get_security_archive_not_delete():
            return
        db = current.db
        table = db.pr_image_library
        set = db(table.original_name == original_image_name)
        set.delete_uploaded_files()
        set.delete()

# =============================================================================
class S3PersonIdentityModel(S3Model):
    """ Identities for Persons """

    names = ["pr_identity"]

    def model(self):

        T = current.T

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
                                  self.pr_person_id(label = T("Person"),
                                                    ondelete="CASCADE"),
                                  Field("type", "integer",
                                        label = T("ID type"),
                                        requires = IS_IN_SET(pr_id_type_opts, zero=None),
                                        default = 1,
                                        represent = lambda opt: \
                                             pr_id_type_opts.get(opt,
                                                                 current.messages.UNKNOWN_OPT)),
                                  Field("value",
                                        label = T("Number")),
                                  s3_date("valid_from",
                                          label = T("Valid From"),
                                          future = 0,
                                          ),
                                  s3_date("valid_until",
                                          label = T("Valid Until"),
                                          ),
                                  Field("description",
                                        label = T("Description")),
                                  Field("country_code", length=4,
                                        label=T("Country Code")),
                                  Field("ia_name",
                                        label = T("Issuing Authority")),
                                  #Field("ia_subdivision"), # Name of issuing authority subdivision
                                  #Field("ia_code"), # Code of issuing authority (if any)
                                  s3_comments(),
                                  *s3_meta_fields())

        # CRUD Strings
        ADD_IDENTITY = T("Add Identity")
        current.response.s3.crud_strings[tablename] = Storage(
            title_create = ADD_IDENTITY,
            title_display = T("Identity Details"),
            title_list = T("Identities"),
            title_update = T("Edit Identity"),
            title_search = T("Search Identity"),
            subtitle_create = T("Add New Identity"),
            label_list_button = T("List Identities"),
            label_create_button = ADD_IDENTITY,
            msg_record_created = T("Identity added"),
            msg_record_modified = T("Identity updated"),
            msg_record_deleted = T("Identity deleted"),
            msg_list_empty = T("No Identities currently registered"))

        # Resource configuration
        self.configure(tablename,
                       deduplicate=self.identity_deduplicate,
                       list_fields=["id",
                                    "type",
                                    "value",
                                    "country_code",
                                    "ia_name"
                                    ])

        # ---------------------------------------------------------------------
        # Return model-global names to s3db.*
        #
        return Storage()

    # -------------------------------------------------------------------------
    @staticmethod
    def identity_deduplicate(item):
        """ Identity de-duplication """

        if item.tablename == "pr_identity":
            table = item.table
            person_id = item.data.get("person_id", None)
            id_type = item.data.get("type", None)
            id_value = item.data.get("value", None)

            if person_id is None:
                return

            query = (table.person_id == person_id) & \
                    (table.type == id_type) & \
                    (table.value == id_value) & \
                    (table.deleted != True)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE
        return

# =============================================================================
class S3PersonEducationModel(S3Model):
    """ Education details for Persons """

    names = ["pr_education"]

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        tablename = "pr_education"
        table = self.define_table(tablename,
                                  self.pr_person_id(label = T("Person"),
                                                    ondelete="CASCADE"),
                                  Field("level",
                                        label=T("Level of Award")),
                                  Field("award",
                                        label=T("Name of Award")),
                                  Field("institute",
                                        label=T("Name of Institute")),
                                  Field("year",
                                        label=T("Year")),
                                  Field("major",
                                        label=T("Major")),
                                  Field("grade",
                                        label=T("Grade")),
                                  s3_comments(),
                                  *s3_meta_fields())

        # CRUD Strings
        ADD_IDENTITY = T("Add Educational Achievements")
        current.response.s3.crud_strings[tablename] = Storage(
            title_create = ADD_IDENTITY,
            title_display = T("Education Details"),
            title_list = T("Education Details"),
            title_update = T("Edit Education Details"),
            title_search = T("Search Education Details"),
            subtitle_create = T("Add Education Detail"),
            label_list_button = T("List Education Details"),
            label_create_button = ADD_IDENTITY,
            msg_record_created = T("Education details added"),
            msg_record_modified = T("Education details updated"),
            msg_record_deleted = T("Education details deleted"),
            msg_list_empty = T("No education details currently registered"))

        # Resource configuration
        self.configure("pr_education",
                       list_fields=["id",
                                    "year",
                                    "level",
                                    "award",
                                    "major",
                                    "grade",
                                    "institute",
                                   ],
                       orderby = ~table.year,
                       sortby = [[1, "desc"]]
                       )

        # ---------------------------------------------------------------------
        # Return model-global names to response.s3
        #
        return Storage()

# =============================================================================
class S3PersonDetailsModel(S3Model):
    """ Extra details for People """

    names = ["pr_person_details",
             ]

    def model(self):

        T = current.T
        gis = current.gis
        messages = current.messages
        UNKNOWN_OPT = messages.UNKNOWN_OPT

        pr_marital_status_opts = {
            1:T("unknown"),
            2:T("single"),
            3:T("married"),
            4:T("separated"),
            5:T("divorced"),
            6:T("widowed"),
            9:T("other")
        }

        pr_marital_status = S3ReusableField("marital_status", "integer",
                                            requires = IS_IN_SET(pr_marital_status_opts,
                                                                 zero=None),
                                            default = 1,
                                            label = T("Marital Status"),
                                            represent = lambda opt: \
                                                pr_marital_status_opts.get(opt, UNKNOWN_OPT))

        pr_religion_opts = current.deployment_settings.get_L10n_religions()

        # ---------------------------------------------------------------------
        # Details
        tablename = "pr_person_details"
        table = self.define_table(tablename,
                                  self.pr_person_id(label = T("Person"),
                                                    ondelete="CASCADE"),
                                  Field("nationality",
                                        requires = IS_NULL_OR(
                                                    IS_IN_SET_LAZY(lambda: \
                                                        gis.get_countries(key_type="code"),
                                                        zero = messages.SELECT_LOCATION)),
                                        label = T("Nationality"),
                                        comment = DIV(_class="tooltip",
                                                      _title="%s|%s" % (T("Nationality"),
                                                                        T("Nationality of the person."))),
                                        represent = lambda code: \
                                            gis.get_country(code, key_type="code") or UNKNOWN_OPT),
                                  pr_marital_status(),
                                  Field("religion", length=128,
                                        label = T("Religion"),
                                        requires = IS_NULL_OR(IS_IN_SET(pr_religion_opts)),
                                        represent = lambda opt: \
                                            pr_religion_opts.get(opt, UNKNOWN_OPT),
                                        ),
                                  Field("father_name",
                                        label = T("Name of Father"),
                                        ),
                                  Field("mother_name",
                                        label = T("Name of Mother"),
                                        ),
                                  Field("occupation", length=128, # Mayon Compatibility
                                        label = T("Profession"),
                                       ),
                                  Field("company",
                                        label = T("Company"),
                                        # @ToDo: Autofill from hrm_human_resource Staff Organisation
                                        ),
                                  Field("affiliations",
                                        label = T("Affiliations"),
                                        # @ToDo: Autofill from hrm_human_resource Volunteer Organisation
                                        ),
                                  *s3_meta_fields())

        # CRUD Strings
        ADD_ADDRESS = T("Add Person's Details")
        current.response.s3.crud_strings[tablename] = Storage(
            title_create = ADD_ADDRESS,
            title_display = T("Person's Details"),
            title_list = T("Persons' Details"),
            title_update = T("Edit Person's Details"),
            title_search = T("Search Person's Details"),
            subtitle_create = T("Add New Person's Details"),
            label_list_button = T("List Persons' Details"),
            label_create_button = ADD_ADDRESS,
            msg_record_created = T("Person's Details added"),
            msg_record_modified = T("Person's Details updated"),
            msg_record_deleted = T("Person's Details deleted"),
            msg_list_empty = T("There are no details for this person yet. Add Person's Details."))

        # Resource configuration
        #self.configure(tablename,
        #               )

        # ---------------------------------------------------------------------
        # Return model-global names to s3db.*
        #
        return Storage()

# =============================================================================
class S3SavedSearch(S3Model):
    """ Saved Searches """

    names = ["pr_saved_search"]

    def model(self):

        T = current.T

        CONTACT_OPTS = current.msg.CONTACT_OPTS
        UNKNOWN_OPT = current.messages.UNKNOWN_OPT

        # ---------------------------------------------------------------------
        pr_saved_search_notification_format = {
            1: T("List"),
            2: T("Report"),
            3: T("Map"),
            4: T("Graph"),
        }

        pr_saved_search_notification_frequency = {
            "never": T("Never"),
            "hourly": T("Hourly"),
            "daily": T("Daily"),
            "weekly": T("Weekly"),
            "monthly": T("Monthly"),
        }

        tablename = "pr_saved_search"
        table = self.define_table(tablename,
                                  Field("name",
                                        requires=IS_NOT_EMPTY(),
                                        comment=DIV(_class="tooltip",
                                                    _title="%s|%s" % (T("Name"),
                                                                      T("Your name for this search. Notifications will use this name."))),
                                        ),
                                  self.super_link("pe_id", "pr_pentity",
                                                  #label=T("Person Entity"),
                                                  readable=True,
                                                  writable=True,
                                                  #represent=pr_pentity_represent,
                                                  ),
                                  Field("controller",
                                        #label=T("Controller"),
                                        readable=False,
                                        writable=False),
                                  Field("function",
                                        #label=T("Function"),
                                        readable=False,
                                        writable=False),
                                  Field("prefix",
                                        #label=T("Module prefix"),
                                        readable=False,
                                        writable=False),
                                  Field("resource_name",
                                        #label=T("Resource name"),
                                        readable=False,
                                        writable=False),
                                  Field("url",
                                        #label=T("URL"),
                                        readable=False,
                                        writable=False,
                                        #comment=DIV(_class="tooltip",
                                        #            _title="%s|%s" % (T("URL"),
                                        #                              T("The URL with field query. Used to fetch the search results."))),
                                        ),
                                  # Friendly representation of the search URL
                                  Field("query", "text",
                                        label=T("Query"),
                                        writable=False,
                                        comment=DIV(_class="tooltip",
                                                    _title="%s|%s" % (T("Query"),
                                                                      T("These are the filters being used by the search."))),
                                        ),
                                  Field("filters",
                                        #label=T("Search Filters"),
                                        readable=False,
                                        writable=False),
                                  Field("notification_format", "integer",
                                        #label=T("Format"),
                                        readable=False,
                                        writable=False,
                                        requires=IS_IN_SET(pr_saved_search_notification_format,
                                                           zero=None),
                                        default=1,
                                        represent=lambda opt: \
                                            pr_saved_search_notification_format.get(opt, UNKNOWN_OPT),
                                        ),
                                  Field("notification_method",
                                        label=T("Notification method"),
                                        readable=False,
                                        writable=False,
                                        requires=IS_IN_SET(CONTACT_OPTS,
                                                           zero=None),
                                        represent=lambda opt: \
                                            CONTACT_OPTS.get(opt, UNKNOWN_OPT),
                                        default="EMAIL",
                                        comment=DIV(_class="tooltip",
                                                    _title="%s|%s" % (T("Notification method"),
                                                                      T("How you want to be notified."))),
                                        ),
                                  Field("notification_frequency",
                                        label=T("Frequency"),
                                        requires=IS_IN_SET(pr_saved_search_notification_frequency,
                                                           zero=None),
                                        default="never",
                                        represent=lambda opt: \
                                            pr_saved_search_notification_frequency.get(opt, UNKNOWN_OPT),
                                        comment=DIV(_class="tooltip",
                                                    _title="%s|%s" % (T("Notification frequency"),
                                                                      T("How often you want to be notified. If there are no changes, no notification will be sent."))),
                                        ),
                                  Field("notification_batch", "boolean",
                                        label=T("Send batch"),
                                        comment=DIV(_class="tooltip",
                                                    _title="%s|%s" % (T("Send batch"),
                                                                      T("If checked, the notification will contain all modified records. If not checked, a notification will be send for each modified record."))),
                                        default=True,
                                        represent=lambda v: T("Yes") if v else T("No"),
                                        ),
                                  Field("last_checked", "datetime",
                                        default=current.request.utcnow,
                                        writable=False,
                                        comment=DIV(_class="tooltip",
                                                    _title="%s|%s" % (T("Last Checked"),
                                                                      T("When this search was last checked for changes."))),
                                        ),
                                  Field("public", "boolean",
                                        default=False,
                                        represent=lambda v: T("Yes") if v else T("No"),
                                        comment=DIV(_class="tooltip",
                                                    _title="%s|%s" % (T("Public"),
                                                                      T("Check this to make your search viewable by others."))),
                                        ),
                                  Field("auth_token",
                                        readable=False,
                                        writable=False),
                                  s3_comments(),
                                  *s3_meta_fields()
                                  )

        # CRUD Strings
        current.response.s3.crud_strings[tablename] = Storage(
            title_create=T("Add search"),
            title_display=T("Saved search details"),
            title_list=T("Saved searches"),
            title_update=T("Edit saved search"),
            title_search=T("Search saved searches"),
            subtitle_create=T("Add saved search"),
            label_list_button=T("List saved searches"),
            label_create_button=T("Save search"),
            label_delete_button=T("Delete saved search"),
            msg_record_created=T("Saved search added"),
            msg_record_modified=T("Saved search updated"),
            msg_record_deleted=T("Saved search deleted"),
            msg_list_empty=T("No Search saved")
        )

        # Resource configuration
        self.configure(tablename,
                       onvalidation=self.pr_saved_search_onvalidation,
                       listadd=False,
                       list_fields=["name",
                                    "notification_format",
                                    "notification_method",
                                    "notification_frequency",
                                    "notification_batch",
                                    "public",
                                    ]
                       )

        # ---------------------------------------------------------------------
        # Return model-global names to s3db.*
        #
        return Storage()

    # -------------------------------------------------------------------------
    @staticmethod
    def pr_saved_search_onvalidation(form):
        """
            Set values for some fields if left empty
        """

        vars = form.vars
        # If the pe_id is empty, populate it with the current user pe_id
        if not vars.pe_id:
            vars.pe_id = current.auth.s3_user_pe_id(current.auth.user_id)

        # Set the friendly query string from the url
        if vars.url:
            vars.query = S3SavedSearch.friendly_string_from_field_query(
                vars.prefix,
                vars.resource_name,
                vars.url
            )

        # By default we set the name to match the friendly query string
        if not vars.name and vars.query:
            vars.name = vars.query

    # -------------------------------------------------------------------------
    @staticmethod
    def friendly_string_from_field_query(prefix, resource_name, url):
        """
            Takes a field query URL
            Returns a string of nice labels and represent-ed values
        """

        from s3.s3resource import S3Resource, S3ResourceField, S3ResourceFilter
        from s3.s3xml import S3XML
        import urlparse

        represent = current.manager.represent
        resource = S3Resource(prefix, resource_name)

        parsed_url = urlparse.urlparse(url)
        filters = urlparse.parse_qs(parsed_url.query)

        field_labels = []
        nice_values = []

        for field_filter, values in filters.items():
            field_selector, filter = field_filter.split("__")
            lf = S3FieldSelector(field_selector).resolve(resource)

            # Parse the values back out
            values = S3ResourceFilter._parse_value(values)

            if not isinstance(values, list):
                values = [values]

            # Field names are sometimes concatenated with pipes if they
            # cover multiple fields, e.g., simple search
            if "|" in field_selector:
                selectors = field_selector.split("|")

                labels = []
                for selector in selectors:
                    field = S3ResourceField(resource, selector)

                    labels.append(s3_unicode(field.label))

                # Represent the value as a unicode string
                for index, value in enumerate(values):
                    values[index] = s3_unicode(value)
            else:
                field = S3ResourceField(resource, field_selector)
                labels = [s3_unicode(field.label)]

                for index, value in enumerate(values):
                    # Some represents need ints
                    if s3_has_foreign_key(field.field):
                        try:
                            value = int(value)
                        except:
                            pass

                    rep_value = represent(lf.field,
                                          value,
                                          strip_markup=True,
                                          )
                    values[index] = rep_value

            # Join the nice labels back together
            field_labels.append("|".join(labels))
            nice_values.append(",".join(values))

        query_list = []
        for index, label in enumerate(field_labels):
            query_list.append("%s=%s" % (label, nice_values[index]))

        query_list = " AND ".join(query_list)

        return query_list

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
             "pr_default_presence"
             ]

    def model(self):

        T = current.T
        auth = current.auth

        person_id = self.pr_person_id
        location_id = self.gis_location_id

        messages = current.messages
        ADD_LOCATION = messages.ADD_LOCATION
        UNKNOWN_OPT = messages.UNKNOWN_OPT

        crud_strings = current.response.s3.crud_strings

        # Trackable types
        pr_trackable_types = {
            1: T("Person"),           # an individual
            2: T("Group"),            # a group
            3: T("Body"),             # a dead body or body part
            4: T("Object"),           # other objects belonging to persons
            5: messages.ORGANISATION, # an organisation
            6: T("Office"),           # an office
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
            opts.SEEN: T("Seen"),           # seen (formerly "found") at location
            opts.TRANSIT: T("Transit"),     # seen at location, between two transfers
            opts.PROCEDURE: T("Procedure"), # seen at location, undergoing procedure ("Checkpoint")

            # Persistant presence conditions:
            opts.CHECK_IN: T("Check-In"),   # arrived at location for accomodation/storage
            opts.CONFIRMED: T("Confirmed"), # confirmation of stay/storage at location
            opts.DECEASED: T("Deceased"),   # deceased
            opts.LOST: T("Lost"),           # destroyed/disposed at location

            # Absence conditions:
            opts.TRANSFER: T("Transfer"),   # Send to another location
            opts.CHECK_OUT: T("Check-Out"), # Left location for unknown destination

            # Missing condition:
            opts.MISSING: T("Missing"),     # Missing (from a "last-seen"-location)
        })
        pr_default_presence = 1

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
                                  location_id(widget=S3LocationAutocompleteWidget(),
                                              comment=S3AddResourceLink(c="gis",
                                                                        f="location",
                                                                        label=ADD_LOCATION,
                                                                        title=T("Current Location"),
                                                                        tooltip=T("The Current Location of the Person/Group, which can be general (for Reporting) or precise (for displaying on a Map). Enter a few characters to search from available locations."))),
                                  Field("location_details",
                                        comment = DIV(_class="tooltip",
                                                      _title="%s|%s" % (T("Location Details"),
                                                                        T("Specific Area (e.g. Building/Room) within the Location that this Person/Group is seen.")))),
                                  s3_datetime("datetime",
                                              label = T("Date/Time"),
                                              empty=False,
                                              default="now",
                                              future=0
                                              ),
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
                                               comment=S3AddResourceLink(c="gis",
                                                                         f="location",
                                                                         label=ADD_LOCATION,
                                                                         title=T("Origin"),
                                                                         tooltip=T("The Location the Person has come from, which can be general (for Reporting) or precise (for displaying on a Map). Enter a few characters to search from available locations."))
                                               ),

                                   location_id("dest_id",
                                               label=T("Destination"),
                                               widget = S3LocationAutocompleteWidget(),
                                               comment=S3AddResourceLink(c="gis",
                                                                         f="location",
                                                                         label=ADD_LOCATION,
                                                                         title=T("Destination"),
                                                                         tooltip=T("The Location the Person is going to, which can be general (for Reporting) or precise (for displaying on a Map). Enter a few characters to search from available locations."))
                                               ),

                                   Field("comment"),
                                   Field("closed", "boolean",
                                         default=False,
                                         readable = False,
                                         writable = False),
                                   *s3_meta_fields())

        # CRUD Strings
        ADD_LOG_ENTRY = T("Add Log Entry")
        crud_strings[tablename] = Storage(
            title_create = ADD_LOG_ENTRY,
            title_display = T("Log Entry Details"),
            title_list = T("Presence Log"),
            title_update = T("Edit Log Entry"),
            title_search = T("Search Log Entry"),
            subtitle_create = T("Add New Log Entry"),
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
                       ondelete = self.presence_onaccept,
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
        table = db.pr_presence
        s3db = current.s3db
        popts = s3db.pr_presence_opts
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
        table = db.pr_presence
        popts = current.s3db.pr_presence_opts

        if isinstance(form, (int, long, str)):
            id = form
        elif hasattr(form, "vars"):
            id = form.vars.id
        else:
            # e.g. Row like for delete
            id = form.id

        presence = db(table.id == id).select(table.ALL,
                                             limitby=(0, 1)).first()
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

            # Re-open the last persistent presence if no closing event
            query = this_entity & is_present
            presence = db(query).select(table.ALL, orderby=~table.datetime, limitby=(0,1)).first()
            if presence and presence.closed:
                later = (table.datetime > presence.datetime)
                query = this_entity & later & is_absent & same_place
                if not db(query).count():
                    db(table.id == presence.id).update(closed=False)

            # Re-open the last missing if no later persistent presence
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

    names = ["pr_note",
             "pr_physical_description"
             ]

    def model(self):

        T = current.T

        UNKNOWN_OPT = current.messages.UNKNOWN_OPT

        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        # ---------------------------------------------------------------------
        # Note
        #
        person_status = {
            1: T("missing"),
            2: T("found"),
            3: T("deceased"),
            9: T("none")
        }

        tablename = "pr_note"
        table = define_table(tablename,
                             super_link("pe_id", "pr_pentity"),
                             # Reporter
                             #self.pr_person_id("reporter"),
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
                             s3_datetime("timestmp",
                                         label=T("Date/Time"),
                                         default="now"
                                         ),
                             Field("note_text", "text",
                                   label=T("Text")),
                             Field("note_contact", "text",
                                   label=T("Contact Info"),
                                   readable=False,
                                   writable=False),
                             self.gis_location_id(label=T("Last known location")),
                             *s3_meta_fields())

        # CRUD strings
        ADD_NOTE = T("New Entry")
        crud_strings[tablename] = Storage(
            title_create = ADD_NOTE,
            title_display = T("Journal Entry Details"),
            title_list = T("Journal"),
            title_update = T("Edit Entry"),
            title_search = T("Search Entries"),
            subtitle_create = T("Add New Entry"),
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
        pr_blood_type_opts = ("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-")

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

        tablename = "pr_physical_description"
        table = define_table(tablename,
                             super_link("pe_id", "pr_pentity"),
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
                             Field("ethnicity", length=64,
                                   #requires=IS_NULL_OR(IS_IN_SET(pr_ethnicity_opts)),
                                   #readable=False,
                                   #writable=False,
                                  ),   # Mayon Compatibility

                             # Height and weight
                             Field("height", "integer",
                                   requires = IS_EMPTY_OR(IS_IN_SET(pr_height_opts)),
                                   label = T("Height"),
                                   represent = lambda opt: \
                                                pr_height_opts.get(opt, UNKNOWN_OPT)),
                             Field("height_cm", "integer",
                                   requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 300)),
                                   label = T("Height (cm)"),
                                   comment = DIV(_class="tooltip",
                                                 _title="%s|%s" % (T("Height"),
                                                                   T("The body height (crown to heel) in cm.")))
                                   ),
                             Field("weight", "integer",
                                   requires = IS_EMPTY_OR(IS_IN_SET(pr_weight_opts)),
                                   label = T("Weight"),
                                   represent = lambda opt: \
                                                pr_weight_opts.get(opt, UNKNOWN_OPT)),
                             Field("weight_kg", "integer",
                                   requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 500)),
                                   label = T("Weight (kg)"),
                                   comment = DIV(_class="tooltip",
                                                 _title="%s|%s" % (T("Weight"),
                                                                   T("The weight in kg.")))
                                   ),
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
                                   label = T("Facial hair, length"),
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

                             s3_comments(),
                             *s3_meta_fields())

        # Field configuration
        table.pe_id.readable = False
        table.pe_id.writable = False

        # CRUD Strings
        # ?

        # ---------------------------------------------------------------------
        # Return model-global names to response.s3
        #
        return Storage(
        )


    # -------------------------------------------------------------------------
    @staticmethod
    def note_onaccept(form):
        """ Update missing status for person """

        db = current.db
        s3db = current.s3db
        pe_table = s3db.pr_pentity
        ntable = db.pr_note
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
            tracker(query=query).set_location(note.location_id,
                                              timestmp=note.timestmp)
        return

# =============================================================================
# Representation Methods
# =============================================================================
def pr_get_entities(pe_ids=None,
                    types=None,
                    represent=True,
                    group=False,
                    as_list=False,
                    show_label=False,
                    default_label="[No ID Tag]"):
    """
        Get representations of person entities. Depending on the group
        and as_list parameters, this function returns a list or Storage
        of entity representations (either pe_ids or string representations).

        @param pe_ids: a list of pe_ids (filters the results)
        @param types: a list of instance types (filters the results)
        @param represent: provide string representations
        @param group: group results by instance type (returns a Storage
                      with the instance types as keys)
        @param as_list: return flat lists instead of dicts (ignored if
                        represent=False because that would return a flat
                        list of pe_ids anyway)
        @param show_label: show the PE label
        @param default_label: the default label
    """

    db = current.db
    s3db = current.s3db

    DEFAULT = current.T("None (no such record)")

    pe_table = s3db.pr_pentity

    if pe_ids is None:
        pe_ids = []
    elif not isinstance(pe_ids, (list, tuple)):
        pe_ids = [pe_ids]
    pe_ids = [long(pe_id) for pe_id in set(pe_ids)]
    query = (pe_table.deleted != True)
    if types:
        if not isinstance(types, (list, tuple)):
            types = [types]
        query &= (pe_table.instance_type.belongs(types))
    if pe_ids:
        query &= (pe_table.pe_id.belongs(pe_ids))
    rows = db(query).select(pe_table.pe_id,
                            pe_table.pe_label,
                            pe_table.instance_type)

    entities = Storage()
    labels = Storage()

    for row in rows:
        pe_id = row.pe_id
        instance_type = row.instance_type
        if instance_type not in entities:
            entities[instance_type] = []
        entities[instance_type].append(pe_id)
        labels[pe_id] = row.pe_label

    type_repr = pe_table.instance_type.represent

    repr_grp = Storage()
    repr_flt = Storage()
    repr_all = []

    for instance_type in entities:
        if types and instance_type not in types:
            continue
        repr_all.extend(entities[instance_type])
        if not represent:
            repr_grp[instance_type] = entities[instance_type]
            continue
        table = s3db.table(instance_type)
        if not table:
            continue

        instance_type_nice = type_repr(instance_type)

        ids = entities[instance_type]
        query = (table.deleted != True) & \
                (table.pe_id.belongs(ids))

        if instance_type not in repr_grp:
            repr_grp[instance_type] = Storage()
        repr_g = repr_grp[instance_type]
        repr_f = repr_flt

        if instance_type == "pr_person":
            rows = db(query).select(table.pe_id,
                                    table.first_name,
                                    table.middle_name,
                                    table.last_name)

            for row in rows:
                pe_id = row.pe_id
                if show_label:
                    label = labels.get(pe_id, None) or default_label
                    pe_str = "%s %s (%s)" % (s3_fullname(row),
                                             label,
                                             instance_type_nice)
                else:
                    pe_str = "%s (%s)" % (s3_fullname(row),
                                          instance_type_nice)
                repr_g[pe_id] = repr_f[pe_id] = pe_str

        elif "name" in table.fields:
            rows = db(query).select(table.pe_id,
                                    table.name)
            for row in rows:
                pe_id = row.pe_id
                if show_label and "pe_label" in table.fields:
                    label = labels.get(pe_id, None) or default_label
                    pe_str = "%s %s (%s)" % (row.name,
                                             label,
                                             instance_type_nice)
                else:
                    pe_str = "%s (%s)" % (row.name,
                                          instance_type_nice)
                repr_g[pe_id] = repr_f[pe_id] = pe_str

        else:
            for pe_id in pe_ids:
                label = labels.get(pe_id, None) or default_label
                pe_str = "[%s] (%s)" % (label,
                                        instance_type_nice)
                repr_g[pe_id] = repr_f[pe_id] = pe_str

    if represent:
        if group and as_list:
            return Storage([(t, repr_grp[t].values()) for t in repr_grp])
        elif group:
            return repr_grp
        elif as_list:
            return repr_flt.values()
        else:
            return repr_flt
    else:
        if group:
            return repr_grp
        else:
            return repr_all

# =============================================================================
def pr_pentity_represent(id, show_label=True, default_label="[No ID Tag]"):
    """ Represent a Person Entity in option fields or list views """

    if not id:
        return current.messages.NONE

    db = current.db
    s3db = current.s3db

    pe_str = current.T("None (no such record)")

    pe_table = s3db.pr_pentity
    if isinstance(id, Row):
        pe = id
        id = pe.pe_id
    else:
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
    elif instance_type == "inv_warehouse":
        warehouse = db(table.pe_id == id).select(table.name,
                                                 limitby=(0, 1)).first()
        if warehouse:
            pe_str = "%s (%s)" % (warehouse.name, instance_type_nice)
    else:
        pe_str = "[%s] (%s)" % (label,
                                instance_type_nice)
    return pe_str

# =============================================================================
def pr_person_represent(person_id, show_link=False):
    """
        Represent a Person in option fields or list views

        @param show_link: whether to make the output into a hyperlink
    """

    if not person_id:
        return current.messages.NONE
    if isinstance(person_id, dict):
        name = s3_fullname(person_id.keys())
    else:
        name = current.cache.ram("pr_person_%s" % person_id,
                                 lambda: s3_fullname(person_id),
                                 time_expire=60)
    if show_link:
        request = current.request
        group = request.get_vars.get("group", None)
        c = request.controller
        if group == "staff" or \
           c == "hrm":
            controller = "hrm"
        elif group == "volunteer" or \
             c == "vol":
            controller = "vol"
        else:
            controller = "pr"
        name = A(name,
                 _href = URL(c=controller, f="person", args=[person_id]))
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
    vars = dict(child = child)
    if caller:
        vars["caller"] = caller
    return S3AddResourceLink(c="pr", f="person",
                             vars=vars,
                             title=current.messages.ADD_PERSON,
                             tooltip="%s|%s" % (title, comment))

# =============================================================================
def pr_rheader(r, tabs=[]):
    """
        Person Registry resource headers
        - used in PR, HRM, DVI, MPR, MSG, VOL
    """

    if r.representation == "html":
        tablename, record = s3_rheader_resource(r)
        if record:
            rheader_tabs = s3_rheader_tabs(r, tabs)
            T = current.T
            db = current.db
            s3db = current.s3db

            if tablename == "pr_person":
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

                pdtable = s3db.pr_person_details
                query = (pdtable.person_id == record.id)
                details = db(query).select(pdtable.nationality,
                                           limitby=(0, 1)).first()
                if details:
                    nationality = details.nationality
                else:
                    nationality = None

                rheader = DIV(TABLE(
                    TR(TH("%s: " % T("Name")),
                       s3_fullname(record),
                       TH("%s: " % T("ID Tag Number")),
                       "%(pe_label)s" % record,
                       image),
                    TR(TH("%s: " % T("Date of Birth")),
                       "%s" % (record.date_of_birth or T("unknown")),
                       TH("%s: " % T("Gender")),
                       "%s" % s3db.pr_gender_opts.get(record.gender,
                                                      T("unknown"))),

                    TR(TH("%s: " % T("Nationality")),
                       "%s" % (pdtable.nationality.represent(nationality)),
                       TH("%s: " % T("Age Group")),
                       "%s" % s3db.pr_age_group_opts.get(record.age_group,
                                                         T("unknown"))),
                    ), rheader_tabs)
                return rheader

            elif tablename == "pr_group":
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
                                   record.name,
                                   TH("%s: " % T("Leader")) if leader else "",
                                   leader),
                                TR(TH("%s: " % T("Description")),
                                   record.description or "",
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
    """

    from itertools import groupby

    if r.http != "GET":
        r.error(405, current.manager.ERROR.BAD_METHOD)

    T = current.T
    #auth = current.auth
    db = current.db
    s3db = current.s3db
    crud = r.resource.crud

    person = r.record

    # Addresses
    # - removed since can't get Google Maps displaying in Location Selector when loaded async
    # - even when loaded into page before async load of map
    # atable = s3db.pr_address
    # query = (atable.pe_id == person.pe_id)
    # addresses = db(query).select(atable.id,
                                 # atable.type,
                                 # atable.building_name,
                                 # atable.address,
                                 # atable.L3,
                                 # atable.postcode,
                                 # atable.L0,
                                 # orderby=atable.type)

    # address_groups = {}
    # for key, group in groupby(addresses, lambda a: a.type):
        # address_groups[key] = list(group)

    # address_wrapper = DIV(H2(T("Addresses")),
                          # DIV(A(T("Add"), _class="action-btn", _id="address-add"),
                              # IMG(_src=URL(c="static", f="img", args="ajax-loader.gif"),
                                  # _height=32, _width=32,
                                  # _id="address-add_throbber",
                                  # _class="throbber hide"),
                              # _class="margin"))

    # items = address_groups.items()
    # opts = s3db.pr_address_type_opts
    # for address_type, details in items:
        # address_wrapper.append(H3(opts[address_type]))
        # for detail in details:
            # text = ",".join((detail.building_name or "",
                             # detail.address or "",
                             # detail.L3 or "",
                             # detail.postcode or "",
                             # detail.L0 or "",
                            # ))
            # text = re.sub(",+", ",", text)
            # if text[0] == ",":
                # text = text[1:]
            # address_wrapper.append(P(
                # SPAN(text),
                # A(T("Edit"), _class="editBtn action-btn fright"),
                # _id="address-%s" % detail.id,
                # _class="address",
                # ))

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

    contacts_wrapper = DIV(H2(T("Contacts")))

    r.component = Storage()
    r.component.table = ctable
    r.component_id = None
    if crud._permitted(method="create"):
        add_btn = DIV(A(T("Add"), _class="action-btn", _id="contact-add"),
                      IMG(_src=URL(c="static", f="img", args="ajax-loader.gif"),
                          _height=32, _width=32,
                          _id="contact-add_throbber",
                          _class="throbber hide"),
                      _class="margin")
        contacts_wrapper.append(add_btn)

    items = contact_groups.items()
    def mysort(key):
        """ Sort Contact Types by Priority"""
        keys = {
                "SMS": 1,
                "EMAIL": 2,
                "WORK_PHONE": 3,
                "HOME_PHONE": 4,
                "SKYPE": 5,
                "RADIO": 6,
                "TWITTER": 7,
                "FACEBOOK": 8,
                "FAX": 9,
                "OTHER": 10
            }
        return keys[key[0]]
    items.sort(key=mysort)
    opts = current.msg.CONTACT_OPTS

    def action_buttons(id):
        r.component_id = id
        if crud._permitted(method="update"):
            edit_btn = A(T("Edit"), _class="editBtn action-btn fright")
        else:
            edit_btn = DIV()
        if crud._permitted(method="delete"):
            delete_btn = A(T("Delete"), _class="deleteBtn delete-btn fright")
        else:
            delete_btn = DIV()
        return (edit_btn, delete_btn)

    for contact_type, details in items:
        contacts_wrapper.append(H3(opts[contact_type]))
        for detail in details:
            id = detail.id
            (edit_btn, delete_btn) = action_buttons(id)
            contacts_wrapper.append(
                P(
                  SPAN(detail.value),
                  edit_btn,
                  delete_btn,
                  _id="contact-%s" % id,
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

    emergency_wrapper = DIV(H2(T("Emergency Contacts")))

    r.component.table = etable
    r.component_id = None
    if crud._permitted(method="create"):
        add_btn = DIV(A(T("Add"), _class="action-btn", _id="emergency-add"),
                      IMG(_src=URL(c="static", f="img", args="ajax-loader.gif"),
                          _height=32, _width=32,
                          _id="emergency-add_throbber",
                          _class="throbber hide"),
                      _class="margin")
        emergency_wrapper.append(add_btn)

    for contact in emergency:
        name = contact.name or ""
        if name:
            name = "%s, "% name
        relationship = contact.relationship or ""
        if relationship:
            relationship = "%s, "% relationship
        id = contact.id
        (edit_btn, delete_btn) = action_buttons(id)
        emergency_wrapper.append(
            P(
              SPAN("%s%s%s" % (name, relationship, contact.phone)),
              edit_btn,
              delete_btn,
              _id="emergency-%s" % id,
              _class="emergency",
            ))

    # Overall content
    content = DIV(#address_wrapper,
                  contacts_wrapper,
                  emergency_wrapper,
                  _class="contacts-wrapper")

    # Add the javascript
    response = current.response
    s3 = response.s3
    if s3.debug:
        s3.scripts.append(URL(c="static", f="scripts",
                              args=["S3", "s3.contacts.js"]))
    else:
        s3.scripts.append(URL(c="static", f="scripts",
                              args=["S3", "s3.contacts.min.js"]))

    s3.js_global.append("controller='%s'" % current.request.controller)
    s3.js_global.append("personId=%s" % person.id);

    # Load the Google JS now as can't load it async
    # @ToDo: Is this worth making conditional on this being their default base layer?
    #apikey = current.deployment_settings.get_gis_api_google()
    #if apikey:
    #    s3.scripts.append("http://www.google.com/jsapi?key=%s" % apikey)
    #s3.scripts.append("http://maps.google.com/maps/api/js?v=3.6&sensor=false")

    # Custom View
    response.view = "pr/contacts.html"

    # RHeader for consistency
    rheader = attr.get("rheader", None)
    if callable(rheader):
        rheader = rheader(r)

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

    person = r.record

    # Profile
    s3db = current.s3db
    ltable = s3db.pr_person_user
    query = (ltable.pe_id == person.pe_id)
    profile = current.db(query).select(limitby=(0, 1)).first()

    form = current.auth()

    # Custom View
    response.view = "pr/profile.html"

    # RHeader for consistency
    rheader = s3db.hrm_rheader(r)

    return dict(
            title = current.T("Profile"),
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

    if record.deleted and record.deleted_fk:
        try:
            fk = json.loads(record.deleted_fk)
            branch_id = fk["branch_id"]
        except:
            return
    else:
        branch_id = record.branch_id

    BRANCHES = "Branches"

    db = current.db
    s3db = current.s3db
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

    if record.deleted and record.deleted_fk:
        try:
            fk = json.loads(record.deleted_fk)
            person_id = fk["person_id"]
        except:
            return
    else:
        person_id = record.person_id

    MEMBERS = "Members"

    db = current.db
    s3db = current.s3db
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

    STAFF = "Staff"
    VOLUNTEER = "Volunteer"

    update = pr_human_resource_update_affiliations

    db = current.db
    s3db = current.s3db
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

    if not role:
        return None

    master_pe = pr_get_pe_id(master)
    affiliate_pe = pr_get_pe_id(affiliate)

    role_id = None
    if master_pe and affiliate_pe:
        rtable = current.s3db.pr_role
        query = (rtable.pe_id == master_pe) & \
                (rtable.role == role) & \
                (rtable.deleted != True)
        row = current.db(query).select(limitby=(0, 1)).first()
        if not row:
            data = {"pe_id": master_pe,
                    "role": role,
                    "role_type": role_type}
            role_id = rtable.insert(**data)
        else:
            role_id = row.id
        if role_id:
            pr_add_to_role(role_id, affiliate_pe)
    return role_id

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

    master_pe = pr_get_pe_id(master)
    affiliate_pe = pr_get_pe_id(affiliate)

    if affiliate_pe:
        s3db = current.s3db
        atable = s3db.pr_affiliation
        rtable = s3db.pr_role
        query = (atable.pe_id == affiliate_pe) & \
                (atable.role_id == rtable.id)
        if master_pe:
            query &= (rtable.pe_id == master_pe)
        if role:
            query &= (rtable.role == role)
        rows = current.db(query).select(rtable.id)
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
    elif isinstance(entity, (long, int)) or \
         isinstance(entity, basestring) and entity.isdigit():
        return entity
    else:
        return None
    if not hasattr(table, "_tablename"):
        table = s3db.table(table, None)
    record = None
    if table:
        db = current.db
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

    if not pe_id:
        return

    s3db = current.s3db
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
        duplicate = current.db(query).select(rtable.id,
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

    resource = s3db.resource("pr_role", role_id)
    return resource.delete()

# =============================================================================
def pr_add_to_role(role_id, pe_id):
    """
        Back-end method to add a person entity to a role.

        @param role_id: the role ID
        @param pe_id: the person entity ID

        @todo: update descendant paths only if the role is a OU role
    """

    # Check for duplicate
    atable = current.s3db.pr_affiliation
    query = (atable.role_id == role_id) & \
            (atable.pe_id == pe_id)
    affiliation = current.db(query).select(limitby=(0, 1)).first()
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

    atable = current.s3db.pr_affiliation
    query = (atable.role_id == role_id) & \
            (atable.pe_id == pe_id)
    affiliation = current.db(query).select(limitby=(0, 1)).first()
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

    rows = current.db(query).select(rtable.role, rtable.path, rtable.pe_id)

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

    rows = current.db(query).select(rtable.pe_id, etable.instance_type)

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

    s3db = current.s3db
    atable = s3db.pr_affiliation
    rtable = s3db.pr_role
    query = (atable.deleted != True) & \
            (atable.role_id == rtable.id) & \
            (atable.pe_id == pe_id) & \
            (rtable.deleted != True) & \
            (rtable.role_type == OU)
    roles = current.db(query).select(rtable.ALL)
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

        @returns: a list of PE-IDs
    """

    s3db = current.s3db
    atable = s3db.pr_affiliation
    rtable = s3db.pr_role
    query = (atable.deleted != True) & \
            (atable.role_id == rtable.id) & \
            (atable.pe_id == pe_id) & \
            (rtable.deleted != True) & \
            (rtable.role_type == OU)

    roles = current.db(query).select(rtable.ALL)

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
def pr_realm(entity):
    """
        Get the default realm (=the immediate OU ancestors) of an entity

        @param entity: the entity (pe_id)
    """

    if not entity:
        return []

    s3db = current.s3db
    atable = s3db.pr_affiliation
    rtable = s3db.pr_role
    query = (atable.deleted != True) & \
            (atable.role_id == rtable.id) & \
            (atable.pe_id == entity) & \
            (rtable.deleted != True) & \
            (rtable.role_type == OU)
    rows = current.db(query).select(rtable.pe_id)
    realm = [row.pe_id for row in rows]
    return realm

# =============================================================================
def pr_realm_users(realm, roles=None, role_types=OU):
    """
        Get all users in a realm

        @param realm: the realm (list of pe_ids)
        @param roles: list of pr_role names to limit the lookup to
        @param role_types: list of pr_role role types to limit the lookup to

        @note: role_types overrides roles
    """

    auth = current.auth
    s3db = current.s3db
    atable = s3db.pr_affiliation
    rtable = s3db.pr_role
    ltable = s3db.pr_person_user
    utable = auth.settings.table_user

    if realm is None:
        query = (utable.deleted != True)
    else:
        if not isinstance(realm, (list, tuple)):
            realm = [realm]
        query = (rtable.deleted != True) & \
                (rtable.pe_id.belongs(realm))
        if roles is not None:
            if not isinstance(roles, (list, tuple)):
                roles = [roles]
            query &= (rtable.role.belongs(roles))
        elif role_types is not None:
            if not isinstance(role_types, (list, tuple)):
                role_types = [role_types]
            query &= (rtable.role_type.belongs(role_types))
        query &= (atable.deleted != True) & \
                (atable.role_id == rtable.id) & \
                (atable.pe_id == ltable.pe_id) & \
                (ltable.deleted != True) & \
                (ltable.user_id == utable.id) & \
                (utable.deleted != True)
    rows = current.db(query).select(utable.id, utable.email)
    if rows:
        if auth.settings.username_field:
            return Storage([(row.id, row.username) for row in rows])
        else:
            return Storage([(row.id, row.email) for row in rows])
    else:
        return Storage()

# =============================================================================
def pr_ancestors(entities):
    """
        Find all ancestor entities of the given entities in the
        OU hierarchy.

        @param entities:

        @returns: Storage of lists of PE-IDs
    """

    if not entities:
        return Storage()

    s3db = current.s3db
    atable = s3db.pr_affiliation
    rtable = s3db.pr_role
    query = (atable.deleted != True) & \
            (atable.role_id == rtable.id) & \
            (atable.pe_id.belongs(entities)) & \
            (rtable.deleted != True) & \
            (rtable.role_type == OU)
    rows = current.db(query).select(rtable.ALL, atable.pe_id)

    ancestors = Storage([(pe_id, []) for pe_id in entities])
    r = rtable._tablename
    a = atable._tablename
    for row in rows:
        pe_id = row[a].pe_id
        paths = ancestors[pe_id]
        role = row[r]
        path = S3MultiPath([role.pe_id])
        if role.path is None:
            ppath = pr_role_rebuild_path(role)
        else:
            ppath = S3MultiPath(role.path)
        path.extend(role.pe_id, ppath, cut=pe_id)
        paths.append(path)
    for pe_id in ancestors:
        ancestors[pe_id] = S3MultiPath.all_nodes(ancestors[pe_id])
    return ancestors

# =============================================================================
def pr_descendants(pe_ids, skip=[]):
    """
    """

    pe_ids = [i for i in pe_ids if i not in skip]
    if not pe_ids:
        return []

    s3db = current.s3db
    etable = s3db.pr_pentity
    rtable = s3db.pr_role
    atable = s3db.pr_affiliation

    query = (rtable.deleted != True) & \
            (rtable.pe_id.belongs(pe_ids)) & \
            (rtable.role_type == OU) & \
            (atable.role_id == rtable.id) & \
            (atable.deleted != True) & \
            (etable.pe_id == atable.pe_id)

    rows = current.db(query).select(rtable.pe_id,
                                    atable.pe_id,
                                    etable.instance_type)
    r = rtable._tablename
    e = etable._tablename
    a = atable._tablename

    nodes = []
    result = Storage()
    for row in rows:
        parent = row[r].pe_id
        child = row[a].pe_id
        if row[e].instance_type != "pr_person":
            if parent not in result:
                result[parent] = [child]
            else:
                result[parent].append(child)
        if child not in nodes:
            nodes.append(child)

    skip = skip + pe_ids
    descendants = pr_descendants(nodes, skip=skip)

    for child in descendants:
        for parent in result:
            if child in result[parent]:
                for node in descendants[child]:
                    if node not in result[parent]:
                        result[parent].append(node)
    for x in result:
        for y in result:
            if x in result[y]:
                result[y].extend([i for i in result[x] if i not in result[y] and i != y])

    return result

# =============================================================================
def pr_get_descendants(pe_ids, skip=[], entity_type=None, ids=True):
    """
        Find descendant entities of a person entity in the OU hierarchy
        (performs a real search, not a path lookup).

        @param pe_ids: person entity ID or list of IDs
        @param skip: list of person entity IDs to skip during descending

        @returns: a list of PE-IDs
    """

    if type(pe_ids) is not list:
        pe_ids = [pe_ids]
    pe_ids = [i for i in pe_ids if i not in skip]
    if not pe_ids:
        return []

    s3db = current.s3db
    etable = s3db.pr_pentity
    rtable = s3db.pr_role
    atable = s3db.pr_affiliation
    en = etable._tablename
    an = atable._tablename
    query = (rtable.deleted != True) & \
            (rtable.pe_id.belongs(pe_ids)) & \
            (~(rtable.pe_id.belongs(skip))) &\
            (rtable.role_type == OU) & \
            (atable.deleted != True) & \
            (atable.role_id == rtable.id) & \
            (etable.pe_id == atable.pe_id)
    skip = skip + pe_ids
    rows = current.db(query).select(atable.pe_id,
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

    if isinstance(pe_id, Row):
        pe_id = row.pe_id

    rtable = current.s3db.pr_role
    query = (rtable.deleted != True) & \
            (rtable.pe_id == pe_id) & \
            (rtable.role_type == OU)
    db = current.db
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

# =============================================================================
def pr_image_represent(image_name,
                       format = None,
                       size = (),
                      ):
    """
        Get the image that matches the required image type

        @param image_name: the name of the original image
        @param format:     the file format required
        @param size:       the size of the image (width, height)
    """

    table = current.s3db.pr_image_library
    query = (table.original_name == image_name)
    if format:
        query = query & (table.format == format)
    if size:
        query = query & (table.width == size[0]) & \
                        (table.height == size[1])
    image = current.db(query).select(table.new_name,
                                     limitby=(0, 1)).first()
    if image:
        return image.new_name
    else:
        return image_name

# ---------------------------------------------------------------------
def pr_url_represent(url):
    """ Representation """

    if not url:
        return current.messages.NONE
    parts = url.split("/")
    image = parts[-1]
    size = (None, 60)
    image = current.s3db.pr_image_represent(image, size=size)
    url_small = URL(c="default", f="download", args=image)

    return DIV(A(IMG(_src=url_small, _height=60), _href=url))

# -----------------------------------------------------------------------------
def pr_image_modify(image_file,
                    image_name,
                    original_name,
                    size = (None, None),
                    to_format = None,
                    ):
    """
        Resize the image passed in and store on the table

        @param image_file:    the image stored in a file object
        @param image_name:    the name of the original image
        @param original_name: the original name of the file
        @param size:          the required size of the image (width, height)
        @param to_format:     the format of the image (jpeg, bmp, png, gif, etc.)
    """

    # Import the specialist libraries
    try:
        from PIL import Image
        from PIL import ImageOps
        from PIL import ImageStat
        PILImported = True
    except(ImportError):
        try:
            import Image
            import ImageOps
            import ImageStat
            PILImported = True
        except(ImportError):
            PILImported = False
    if PILImported:
        from tempfile import TemporaryFile
        s3db = current.s3db
        table = s3db.pr_image_library

        fileName, fileExtension = os.path.splitext(original_name)

        image_file.seek(0)
        im = Image.open(image_file)
        thumb_size = []
        if size[0] == None:
            thumb_size.append(im.size[0])
        else:
            thumb_size.append(size[0])
        if size[1] == None:
            thumb_size.append(im.size[1])
        else:
            thumb_size.append(size[1])
        im.thumbnail(thumb_size, Image.ANTIALIAS)

        if not to_format:
            to_format = fileExtension[1:]
        if to_format.upper() == "JPG":
            to_format = "JPEG"
        elif to_format.upper() == "BMP":
            im = im.convert("RGB")
        save_im_name = "%s.%s" % (fileName, to_format)
        tempFile = TemporaryFile()
        im.save(tempFile,to_format)
        tempFile.seek(0)
        newfile = table.new_name.store(tempFile,
                                       save_im_name,
                                       table.new_name.uploadfolder)
        # rewind the original file so it can be read, if required
        image_file.seek(0)
        image_id = table.insert(original_name = image_name,
                                new_name = newfile,
                                format = to_format,
                                width = size[0],
                                height = size[1],
                                actual_width = im.size[0],
                                actual_height = im.size[1],
                               )
        return True
    else:
        return False

# -----------------------------------------------------------------------------
def pr_image_resize(image_file,
                    image_name,
                    original_name,
                    size,
                    ):
    """
        Resize the image passed in and store on the table

        @param image_file:    the image stored in a file object
        @param image_name:    the name of the original image
        @param original_name: the original name of the file
        @param size:          the required size of the image (width, height)
    """

    return pr_image_modify(image_file,
                           image_name,
                           original_name,
                           size = size)

# -----------------------------------------------------------------------------
def pr_image_format(image_file,
                    image_name,
                    original_name,
                    to_format,
                    ):
    """
        Change the file format of the image passed in and store on the table

        @param image_file:    the image stored in a file object
        @param image_name:    the name of the original image
        @param original_name: the original name of the file
        @param to_format:     the format of the image (jpeg, bmp, png, gif, etc.)
    """

    return pr_image_modify(image_file,
                           image_name,
                           original_name,
                           to_format = to_format)

# END =========================================================================
