# -*- coding: utf-8 -*-

""" Sahana Eden Person Registry Model

    @copyright: 2009-2019 (c) Sahana Software Foundation
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

__all__ = (# PR Base Entities
           "PRPersonEntityModel",
           "PRPersonModel",
           "PRGroupModel",
           "PRForumModel",

           # Person Entity Components
           "PRAddressModel",
           "PRContactModel",
           "PRImageModel",
           "PRPresenceModel",

           # Person Components
           "PRAvailabilityModel",
           "PRUnavailabilityModel",
           "PRDescriptionModel",
           "PREducationModel",
           "PRIdentityModel",
           "PRLanguageModel",
           "PROccupationModel",
           "PRPersonDetailsModel",
           "PRPersonLocationModel",
           "PRPersonTagModel",

           "PRReligionModel",

           # Group Components
           "PRGroupCompetencyModel",
           "PRGroupLocationModel",
           "PRGroupTagModel",

           # S3 Models
           "S3ImageLibraryModel",
           "S3RoleDelegationModel",
           "S3SavedFilterModel",
           "S3SubscriptionModel",

           # Representation Methods
           "pr_get_entities",
           "pr_RoleRepresent",
           "pr_PersonEntityRepresent",
           "pr_PersonRepresent",
           "pr_PersonRepresentContact",
           "pr_person_comment",
           "pr_image_library_represent",
           "pr_url_represent",
           "pr_rheader",

           # Autocomplete Search Method
           "pr_PersonSearchAutocomplete",

           # REST Methods
           "pr_AssignMethod",
           "pr_compose",
           "pr_Contacts",
           "pr_Template",
           "pr_Templates",

           # PE Hierarchy and Realms
           "pr_update_affiliations",
           "pr_add_affiliation",
           "pr_remove_affiliation",
           "pr_get_pe_id",
           "pr_define_role",
           "pr_delete_role",
           "pr_add_to_role",
           "pr_remove_from_role",
           "pr_instance_type",
           "pr_realm",
           "pr_realm_users",
           "pr_get_role_paths",
           "pr_get_role_branches",
           "pr_get_path",
           "pr_get_ancestors",
           "pr_get_descendants",
           "pr_ancestors",
           "pr_descendants",
           "pr_rebuild_path",
           "pr_role_rebuild_path",

           # Helper for ImageLibrary
           "pr_image_modify",

           # Other functions
           "pr_availability_filter",
           "pr_import_prep",

           # Data List Default Layouts
           #"pr_address_list_layout",
           #"pr_contact_list_layout",
           #"pr_filter_list_layout",
           )

import json
import os

from gluon import current, redirect, URL, \
                  A, DIV, H2, H3, H5, IMG, LABEL, P, SPAN, TABLE, TAG, TH, TR, \
                  IS_LENGTH, IS_EMPTY_OR, IS_IN_SET, IS_NOT_EMPTY, IS_EMAIL, \
                  IS_INT_IN_RANGE, IS_MATCH
from gluon.storage import Storage
from gluon.sqlhtml import RadioWidget

from ..s3 import *
from s3compat import INTEGER_TYPES, basestring, long, urlencode
from s3dal import Field, Row
from s3layouts import S3PopupLink

OU = 1 # role type which indicates hierarchy, see role_types
OTHER_ROLE = 9

# Compact JSON encoding
SEPARATORS = (",", ":")

# =============================================================================
class PRPersonEntityModel(S3Model):
    """ Person Super-Entity """

    names = ("pr_pentity",
             "pr_affiliation",
             "pr_person_user",
             "pr_role",
             "pr_role_types",
             "pr_role_id",
             "pr_pe_label",
             "pr_pe_types",
             "pr_pentity_represent",
             )

    def model(self):

        db = current.db
        T = current.T
        auth_settings = current.auth.settings

        add_components = self.add_components
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        super_entity = self.super_entity
        #super_key = self.super_key
        super_link = self.super_link

        messages = current.messages
        #YES = T("yes") #messages.YES
        #NO = T("no") #messages.NO
        UNKNOWN_OPT = messages.UNKNOWN_OPT

        # ---------------------------------------------------------------------
        # Person Super-Entity
        #
        settings = current.deployment_settings
        if settings.get_ui_label_camp():
            SHELTER = T("Camp")
        else:
            SHELTER = T("Shelter")
        org_group_label = settings.get_org_groups()
        if org_group_label:
            org_group_label = T(org_group_label)
        else:
            org_group_label = T("Organization group")
        pe_types = Storage(cr_shelter = SHELTER,
                           deploy_alert = T("Deployment Alert"),
                           dvi_body = T("Body"),
                           dvi_morgue = T("Morgue"),
                           fire_station = T("Fire Station"),
                           hms_hospital = T("Hospital"),
                           hrm_training_event = T("Training Event"),
                           inv_warehouse = T("Warehouse"),
                           org_organisation = messages.ORGANISATION,
                           org_group = org_group_label,
                           org_facility = T("Facility"),
                           org_office = T("Office"),
                           #po_area = T("Recovery Outreach Area"),
                           po_household = T("Household"),
                           police_station = T("Police Station"),
                           pr_person = T("Person"),
                           pr_forum = T("Forum"),
                           pr_group = T("Group"),
                           )

        pr_pentity_represent = pr_PersonEntityRepresent()

        tablename = "pr_pentity"
        super_entity(tablename, "pe_id", pe_types,
                     #super_link("source_id", "doc_source_entity"),
                     Field("type"),
                     Field("pe_label", length=128),
                     )

        # Resource configuration
        configure(tablename,
                  deletable = False,
                  editable = False,
                  listadd = False,
                  list_fields = ["instance_type",
                                 "type",
                                 "pe_label",
                                 ],
                  onaccept = self.pr_pentity_onaccept,
                  referenced_by = [(auth_settings.table_membership_name, "pe_id")],
                  )

        # Components
        pe_id = "pe_id"
        add_components(tablename,
                       # PR components
                       pr_address = pe_id,
                       pr_contact = (# All contact information:
                                     pe_id,
                                     # Email addresses:
                                     {"name": "email",
                                      "joinby": pe_id,
                                      "filterby": {
                                          "contact_method": "EMAIL",
                                          },
                                      },
                                     # Mobile phone numbers:
                                     {"name": "phone",
                                      "joinby": pe_id,
                                      "filterby": {
                                          "contact_method": "SMS",
                                          },
                                      },
                                     # Home phone numbers:
                                     #{"name": "home_phone",
                                     # "joinby": pe_id,
                                     #"filterby": {
                                     #    "contact_method": "HOME_PHONE",
                                     #    },
                                     # },
                                     # Work phone numbers:
                                     #{"name": "work_phone",
                                     # "joinby": pe_id,
                                     #"filterby": {
                                     #    "contact_method": "WORK_PHONE",
                                     #    },
                                     # },
                                     # Facebook:
                                     {"name": "facebook",
                                      "joinby": pe_id,
                                      "filterby": {
                                          "contact_method": "FACEBOOK",
                                          },
                                      },
                                     # Twitter:
                                     {"name": "twitter",
                                      "joinby": pe_id,
                                      "filterby": {
                                          "contact_method": "TWITTER",
                                          },
                                      },
                                     ),
                       pr_contact_emergency = pe_id,
                       pr_image = ({"name": "image",
                                    "joinby": "pe_id",
                                    },
                                    {"name": "picture",
                                     "joinby": "pe_id",
                                     "filterby": {
                                         "profile": True,
                                         },
                                     },
                                    ),
                       pr_note = pe_id,
                       pr_role = pe_id,
                       pr_physical_description = {"joinby": pe_id,
                                                  "multiple": False,
                                                  },
                       # DVI components
                       dvi_effects = {"joinby": pe_id,
                                      "multiple": False,
                                      },
                       dvi_checklist = {"joinby": pe_id,
                                        "multiple": False,
                                        },
                       dvi_identification = {"joinby": pe_id,
                                             "multiple": False,
                                             },
                       # Tenures
                       stdm_tenure_relationship = pe_id,

                       # Map Configs 'Saved Maps'
                       #   - Personalised configurations
                       #   - OU configurations (Organisation/Branch/Facility/Team)
                       gis_config = pe_id,
                       )

        # Reusable fields
        pr_pe_label = S3ReusableField("pe_label", length=128,
                                      label = T("ID Tag Number"),
                                      requires = IS_EMPTY_OR(
                                                    [IS_LENGTH(128),
                                                     IS_NOT_ONE_OF(db,
                                                        "pr_pentity.pe_label"),
                                                     ]),
                                      )

        # Custom Method for S3AutocompleteWidget
        self.set_method("pr", "pentity",
                        method = "search_ac",
                        action = self.pe_search_ac)

        # ---------------------------------------------------------------------
        # Person <-> User
        #
        tablename = "pr_person_user"
        define_table(tablename,
                     super_link("pe_id", "pr_pentity"),
                     Field("user_id", auth_settings.table_user),
                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Role (Affiliates Group)
        #
        role_types = {
            1: T("Organization Units"),  # business hierarchy (reporting units)
            2: T("Membership"),          # membership role
            3: T("Association"),         # other non-reporting role
            9: T("Other")                # other role type
        }
        tablename = "pr_role"
        define_table(tablename,
                     # The "parent" entity
                     super_link("pe_id", "pr_pentity",
                                label = T("Corporate Entity"),
                                readable = True,
                                writable = True,
                                represent = pr_pentity_represent,
                                sort = True,
                                empty = False,
                                ),
                      # Role type
                      Field("role_type", "integer",
                            requires = IS_IN_SET(role_types, zero=None),
                            represent = lambda opt: \
                                role_types.get(opt, UNKNOWN_OPT),
                            ),
                      # Role name
                      Field("role", notnull=True,
                            requires = IS_NOT_EMPTY(),
                            ),
                      # Path, for faster lookups
                      Field("path",
                            readable = False,
                            writable = False,
                            ),
                      # Type filter, type of entities which can have this role
                      Field("entity_type", "string",
                            requires = IS_EMPTY_OR(IS_IN_SET(pe_types,
                                                             zero=T("ANY"))),
                            represent = lambda opt: \
                                pe_types.get(opt, UNKNOWN_OPT),
                            ),
                      # Subtype filter, if the entity type defines its own type
                      Field("sub_type", "integer",
                            readable = False,
                            writable = False,
                            ),
                      *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Role"),
            title_display = T("Role Details"),
            title_list = T("Roles"),
            title_update = T("Edit Role"),
            label_list_button = T("List Roles"),
            label_delete_button = T("Delete Role"),
            msg_record_created = T("Role added"),
            msg_record_modified = T("Role updated"),
            msg_record_deleted = T("Role deleted"),
            msg_list_empty = T("No Roles defined"))

        # Resource configuration
        configure(tablename,
                  onvalidation = self.pr_role_onvalidation,
                  )

        # Components
        add_components(tablename,
                       pr_affiliation = "role_id",
                       )

        # Reusable fields
        pr_role_represent = pr_RoleRepresent()
        role_id = S3ReusableField("role_id", "reference %s" % tablename,
                                  label = T("Role"),
                                  ondelete = "CASCADE",
                                  represent = pr_role_represent,
                                  requires = IS_ONE_OF(db, "pr_role.id",
                                                       pr_role_represent),
                                  )

        # ---------------------------------------------------------------------
        # Affiliation
        #
        tablename = "pr_affiliation"
        define_table(tablename,
                     role_id(),
                     super_link("pe_id", "pr_pentity",
                                label = T("Entity"),
                                readable = True,
                                writable = True,
                                sort = True,
                                represent = pr_pentity_represent,
                                empty = False,
                                ),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Affiliation"),
            title_display = T("Affiliation Details"),
            title_list = T("Affiliations"),
            title_update = T("Edit Affiliation"),
            label_list_button = T("List Affiliations"),
            label_delete_button = T("Delete Affiliation"),
            msg_record_created = T("Affiliation added"),
            msg_record_modified = T("Affiliation updated"),
            msg_record_deleted = T("Affiliation deleted"),
            msg_list_empty = T("No Affiliations defined"))

        # Resource configuration
        configure(tablename,
                  onaccept = self.pr_affiliation_onaccept,
                  ondelete = self.pr_affiliation_ondelete,
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"pr_pe_types": pe_types,
                "pr_pe_label": pr_pe_label,
                "pr_role_types": role_types,
                "pr_role_id": role_id,
                "pr_pentity_represent": pr_pentity_represent,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def pe_search_ac(r, **attr):
        """
            JSON search method for S3AutocompleteWidget

            @param r: the S3Request
            @param attr: request attributes
        """

        get_vars = current.request.get_vars

        # JQueryUI Autocomplete uses "term"
        # old JQuery Autocomplete uses "q"
        # what uses "value"?
        value = get_vars.term or get_vars.value or get_vars.q or None

        if not value:
            r.error(400, "No search term specified")

        # We want to do case-insensitive searches
        # (default anyway on MySQL/SQLite, but not PostgreSQL)
        value = s3_unicode(value).lower()

        limit = int(get_vars.limit or 0)

        types = get_vars.get("types")
        if types:
            types = types.split(",")
        else:
            # Default to Persons & Groups
            types = ("pr_person", "pr_group")

        response = current.response

        resource = r.resource

        # Representation without PE recognition label
        table = resource.table
        table.pe_id.represent = pr_PersonEntityRepresent(show_label=False)

        # Query comes in pre-filtered to accessible & deletion_status
        # Respect response.s3.filter
        default_filter = response.s3.filter

        items = []

        if "pr_person" in types:

            # Persons
            entity = "pe_id:pr_person"

            first_name = FS("%s.first_name" % entity).lower()
            middle_name = FS("%s.middle_name" % entity).lower()
            last_name = FS("%s.last_name" % entity).lower()

            if " " in value:
                first, last = value.split(" ", 1)
                first = "%s%%" % first
                last = "%s%%" % last.strip()
                query = (first_name.like(first)) & \
                        ((middle_name.like(last)) | \
                         (last_name.like(last)))
            else:
                value = "%s%%" % value.strip()
                query = (first_name.like(value)) | \
                        (middle_name.like(value)) | \
                        (last_name.like(value))

            resource.clear_query()
            resource.add_filter(default_filter)
            resource.add_filter(query)

            data = resource.select(fields=["pe_id"],
                                   limit = limit,
                                   raw_data = True,
                                   represent = True,
                                   show_links = False,
                                   )

            items.extend(data.rows)

        if "pr_group" in types:

            # Add Groups
            entity = "pe_id:pr_group"

            field = FS("%s.name" % entity).lower()
            query = field.like("%%%s%%" % value)

            resource.clear_query()
            resource.add_filter(default_filter)
            resource.add_filter(query)

            data = resource.select(fields=["pe_id"],
                                   limit = limit,
                                   raw_data = True,
                                   represent = True,
                                   show_links = False,
                                   )

            items.extend(data.rows)

        if "org_organisation" in types:

            # Add Organisations
            entity = "pe_id:org_organisation"

            field = FS("%s.name" % entity).lower()
            query = field.like("%%%s%%" % value)

            resource.clear_query()
            resource.add_filter(default_filter)
            resource.add_filter(query)

            data = resource.select(fields=["pe_id"],
                                   limit = limit,
                                   raw_data = True,
                                   represent = True,
                                   show_links = False,
                                   )

            items.extend(data.rows)

        result = []
        append = result.append
        for item in items:
            raw = item["_row"]
            append({"id": raw["pr_pentity.pe_id"],
                    "name": item["pr_pentity.pe_id"],
                    })

        output = json.dumps(result, separators=SEPARATORS)

        response.headers["Content-Type"] = "application/json"
        return output

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
            entity = current.s3db.pr_pentity_represent(role.pe_id)
        except:
            return current.messages.UNKNOWN_OPT
        else:
            return "%s: %s" % (entity, role.role)

    # -------------------------------------------------------------------------
    @staticmethod
    def pr_role_onvalidation(form):
        """
            Clear descendant paths if role type has changed

            @param form: the CRUD form
        """

        form_vars = form.vars
        if not form_vars:
            return
        if "role_type" in form_vars:
            role_id = form.record_id
            if not role_id:
                return
            role_type = form_vars.role_type
            db = current.db
            rtable = db.pr_role
            role = db(rtable.id == role_id).select(rtable.role_type,
                                                   limitby=(0, 1)).first()
            if role and str(role.role_type) != str(role_type):
                # If role type has changed, then clear paths
                if str(role_type) != str(OU):
                    form_vars["path"] = None
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
                    s3db.org_update_affiliations("org_site", instance)
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def pr_affiliation_onaccept(form):
        """
            Remove duplicate affiliations and clear descendant paths
            (to trigger lazy rebuild)

            @param form: the CRUD form
        """

        form_vars = form.vars
        role_id = form_vars["role_id"]
        pe_id = form_vars["pe_id"]
        record_id = form_vars["id"]

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

            @param row: the deleted Row
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
            pe_id = data.get("pe_id")
            if pe_id:
                current.s3db.pr_rebuild_path(pe_id, clear=True)
        return

# =============================================================================
class PRPersonModel(S3Model):
    """ Persons and Groups """

    names = ("pr_person",
             "pr_gender",
             "pr_gender_opts",
             "pr_person_id",
             "pr_person_lookup",
             "pr_person_represent",
             )

    def model(self):

        T = current.T
        db = current.db
        settings = current.deployment_settings

        messages = current.messages
        NONE = messages["NONE"]

        super_link = self.super_link
        add_components = self.add_components

        # ---------------------------------------------------------------------
        # Person
        #
        pr_gender_opts = {1: "",
                          2: T("female"),
                          3: T("male"),
                          }
        if not settings.get_pr_hide_third_gender():
            # Add the third gender option ("other" or "indeterminate",
            # meaning neither female nor male, officially recognized
            # in various countries)
            pr_gender_opts[4] = T("other")

        pr_gender = S3ReusableField("gender", "integer",
                                    default = 1,
                                    label = T("Sex"),
                                    represent = S3Represent(options = pr_gender_opts,
                                                            default = current.messages["NONE"],
                                                            ),
                                    requires = IS_PERSON_GENDER(pr_gender_opts,
                                                                sort = True,
                                                                zero = None,
                                                                ),
                                    )

        if settings.get_L10n_mandatory_lastname():
            last_name_validate = [IS_NOT_EMPTY(error_message = T("Please enter a last name")),
                                  IS_LENGTH(64),
                                  ]
        else:
            last_name_validate = IS_LENGTH(64)

        # Add an opt-in clause to receive emails depending on the
        # deployment settings
        # @ToDo: Replace with Save Search/Subscriptions back-end & simple
        # form-field injection in front-end
        show_opt_in = settings.get_auth_opt_in_to_email()

        tablename = "pr_person"
        self.define_table(
            tablename,
            # Instances
            super_link("pe_id", "pr_pentity"),
            super_link("track_id", "sit_trackable"),
            # Base location
            self.gis_location_id(readable=False,
                                 writable=False),
            self.pr_pe_label(
                comment = DIV(_class="tooltip",
                              _title="%s|%s" % (T("ID Tag Number"),
                                                T("Number or Label on the identification tag this person is wearing (if any)."),
                                                ),
                              ),
                requires = IS_EMPTY_OR([IS_LENGTH(128),
                                        # Uniqueness only required within pr_person:
                                        IS_NOT_ONE_OF(db, "pr_person.pe_label"),
                                        ]),
                ),
            # @ToDo: Remove this field from this core table
            # - remove refs to writing this from this module
            # - update read refs in controllers/dvi.py & controllers/mpr.py
            Field("missing", "boolean",
                  readable=False,
                  writable=False,
                  default=False,
                  represent = lambda missing: \
                              (missing and ["missing"] or [""])[0]),
            Field("first_name", notnull=True,
                  length=64, # Mayon Compatibility
                  #default = "?" if current.auth.permission.format != "html" else "",
                  label = T("First Name"),
                  # NB Not possible to have an IS_NAME() validator here
                  # http://eden.sahanafoundation.org/ticket/834
                  requires = [IS_NOT_EMPTY(error_message = T("Please enter a first name")),
                              IS_LENGTH(64),
                              ],
                  comment =  DIV(_class="tooltip",
                                 _title="%s|%s" % (T("First Name"),
                                                   T("The first or only name of the person (mandatory)."))),
                  ),
            Field("middle_name", length=64, # Mayon Compatibility
                  label = T("Middle Name"),
                  represent = lambda v: v or NONE,
                  requires = IS_LENGTH(64),
                  ),
            Field("last_name", length=64, # Mayon Compatibility
                  label = T("Last Name"),
                  represent = lambda v: v or NONE,
                  requires = last_name_validate,
                  ),
            # @ToDo: Move to person_details & hide by default
            Field("initials", length=8,
                  label = T("Initials"),
                  requires = IS_LENGTH(8),
                  ),
            # @ToDo: Move to person_details & hide by default
            Field("preferred_name", length=64, # Mayon Compatibility
                  label = T("Preferred Name"),
                  comment = DIV(_class="tooltip",
                                _title="%s|%s" % (T("Preferred Name"),
                                                  T("The name to be used when calling for or directly addressing the person (optional)."))),
                  requires = IS_LENGTH(64),
                  ),
            # @ToDo: Move to person_details & hide by default
            Field("local_name",
                  label = T("Local Name"),
                  comment = DIV(_class="tooltip",
                                _title="%s|%s" % (T("Local Name"),
                                                  T("Name of the person in local language and script (optional)."))),
                  ),
            pr_gender(),
            s3_date("date_of_birth",
                    label = T("Date of Birth"),
                    empty = not settings.get_pr_dob_required(),
                    future = 0,
                    past = 1320,  # Months, so 110 years
                    ),
            # @ToDo: Move this field from this core table (should be using Saved Searches/Subscription)
            Field("opt_in", "string", # list of mailing lists which link to teams
                  default=False,
                  readable = show_opt_in,
                  writable = show_opt_in,
                  label = T("Receive updates"),
                  comment = DIV(_class="tooltip",
                                _title="%s|%s" % (T("Mailing list"),
                                                  T("By selecting this you agree that we may contact you."))),
                  ),
            Field.Method("age", self.pr_person_age),
            Field.Method("age_group", self.pr_person_age_group),
            s3_comments(),
            *s3_meta_fields())

        # CRUD Strings
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = messages.ADD_PERSON,
            title_display = T("Person Details"),
            title_list = T("Persons"),
            title_update = T("Edit Person Details"),
            label_list_button = T("List Persons"),
            label_delete_button = T("Delete Person"),
            msg_record_created = T("Person added"),
            msg_record_modified = T("Person details updated"),
            msg_record_deleted = T("Person deleted"),
            msg_list_empty = T("No Persons currently registered"))

        # Filter widgets
        filter_widgets = [
            S3TextFilter(["pe_label",
                          "first_name",
                          "middle_name",
                          "last_name",
                          "local_name",
                          "identity.value"
                         ],
                         label=T("Name and/or ID"),
                         comment=T("To search for a person, enter any of the "
                                   "first, middle or last names and/or an ID "
                                   "number of a person, separated by spaces. "
                                   "You may use % as wildcard."),
                        ),
            ]

        # Custom Form
        crud_form = S3SQLCustomForm("first_name",
                                    "middle_name",
                                    "last_name",
                                    "person_details.year_of_birth",
                                    "date_of_birth",
                                    #"initials",
                                    #"preferred_name",
                                    #"local_name",
                                    "gender",
                                    "person_details.marital_status",
                                    "person_details.nationality",
                                    "person_details.religion",
                                    "person_details.mother_name",
                                    "person_details.father_name",
                                    "person_details.grandfather_name",
                                    "person_details.occupation",
                                    "person_details.company",
                                    "person_details.affiliations",
                                    "comments",
                                    )

        # Resource configuration
        self.configure(tablename,
                       context = {"incident": "incident.id",
                                  "location": "location_id",
                                  "organisation": "human_resource.organisation_id",
                                  },
                       crud_form = crud_form,
                       deduplicate = self.person_duplicate,
                       filter_widgets = filter_widgets,
                       list_fields = ["id",
                                      "first_name",
                                      "middle_name",
                                      "last_name",
                                      #"picture",
                                      "gender",
                                      (T("Age"), "age"),
                                      (messages.ORGANISATION, "human_resource.organisation_id"),
                                      ],
                       list_layout = pr_PersonListLayout(),
                       extra_fields = ["date_of_birth"],
                       main = "first_name",
                       extra = "last_name",
                       onaccept = self.pr_person_onaccept,
                       realm_components = ("address",
                                           "contact",
                                           "contact_emergency",
                                           "identity",
                                           "image",
                                           "person_details",
                                           "person_tag",
                                           "presence",
                                           ),
                       super_entity = ("pr_pentity", "sit_trackable"),
                       )

        person_id_comment = pr_person_comment(
            T("Person"),
            T("Type the first few characters of one of the Person's names."),
            child="person_id")

        person_represent = pr_PersonRepresent()

        # Adapt sorting/ordering to name order
        NAMES = ("first_name", "middle_name", "last_name")
        keys = StringTemplateParser.keys(settings.get_pr_name_format())
        sortby = [fn for fn in keys if fn in NAMES]
        orderby = "pr_person.%s" % (sortby[0] if sortby else NAMES[0])

        person_id = S3ReusableField("person_id", "reference %s" % tablename,
                                    sortby = sortby,
                                    requires = IS_EMPTY_OR(
                                        IS_ONE_OF(db, "pr_person.id",
                                                  person_represent,
                                                  orderby = orderby,
                                                  sort = True,
                                                  error_message = T("Person must be specified!"))
                                                  ),
                                    represent = person_represent,
                                    label = T("Person"),
                                    comment = person_id_comment,
                                    ondelete = "RESTRICT",
                                    widget = S3PersonAutocompleteWidget(),
                                    )

        # Custom Methods for S3PersonAutocompleteWidget and S3AddPersonWidget
        set_method = self.set_method
        set_method("pr", "person",
                   method = "search_ac",
                   action = self.pr_search_ac,
                   )

        set_method("pr", "person",
                   method = "lookup",
                   action = self.pr_person_lookup)

        set_method("pr", "person",
                   method = "check_duplicates",
                   action = self.pr_person_check_duplicates)

        # Enable in templates as-required
        #set_method("pr", "person",
        #           method = "templates",
        #           action = pr_Templates())

        #set_method("pr", "person",
        #           method = "template",
        #           action = pr_Template())

        # Components
        add_components(tablename,
                       # Assets
                       asset_asset = "assigned_to_id",
                       # User account
                       auth_user = {"link": "pr_person_user",
                                    "joinby": "pe_id",
                                    "key": "user_id",
                                    "fkey": "id",
                                    "pkey": "pe_id",
                                    },
                       # Shelter (Camp) Registry
                       cr_shelter_registration = {"joinby": "person_id",
                                                  # A person can be assigned to only one shelter
                                                  # @todo: when fully implemented this needs to allow
                                                  # multiple instances for tracking reasons
                                                  "multiple": False,
                                                  },
                       cr_shelter_registration_history = "person_id",
                       project_activity_person = "person_id",
                       supply_distribution_person = "person_id",
                       event_incident = {"link": "event_human_resource",
                                         "joinby": "person_id",
                                         "key": "incident_id",
                                         "actuate": "hide",
                                         },
                       # HR Records
                       hrm_human_resource = "person_id",
                       # HR Documents
                       doc_document = {"link": "hrm_human_resource",
                                       "joinby": "person_id",
                                       "key": "doc_id",
                                       "fkey": "doc_id",
                                       "pkey": "id",
                                       "actuate": "replace",
                                       },
                       # Skills
                       pr_language = "person_id",
                       hrm_certification = "person_id",
                       hrm_skill = {"link": "hrm_competency",
                                    "joinby": "person_id",
                                    "key": "skill_id",
                                    "actuate": "hide",
                                    },
                       hrm_competency = "person_id",
                       hrm_credential = "person_id",
                       hrm_training = "person_id",
                       hrm_trainings = {"joinby": "person_id",
                                        "multiple": False,
                                        },
                       # Facilitated Trainings (Instructor)
                       hrm_training_event = "person_id",
                       # Experience
                       hrm_experience = "person_id",
                       hrm_programme_hours = {"name": "hours",
                                              "joinby": "person_id",
                                              },
                       vol_activity_hours = "person_id",
                       # Appraisals
                       hrm_appraisal = "person_id",
                       # Availability
                       pr_unavailability = "person_id",
                       pr_person_availability = {"name": "availability",
                                                 "joinby": "person_id",
                                                 # Will need tochange in future
                                                 "multiple": False,
                                                 },
                       # Awards
                       hrm_award = {"name": "staff_award",
                                    "joinby": "person_id",
                                    },
                       vol_volunteer_award = {"name": "award",
                                              "joinby": "person_id",
                                              },
                       # Disciplinary Record
                       hrm_disciplinary_action = "person_id",
                       # Salary Information
                       hrm_salary = "person_id",
                       # Organisation Memberships
                       member_membership = "person_id",
                       # Organisation Group Association
                       org_group_person = "person_id",
                       # Education history
                       pr_education = "person_id",
                       # Occupation Types
                       pr_occupation_type = {"link": "pr_occupation_type_person",
                                             "joinby": "person_id",
                                             "key": "occupation_type_id",
                                             "actuate": "link",
                                             "autodelete": False,
                                             },

                       # Group Memberships
                       pr_group_membership = "person_id",

                       # Identity Documents
                       pr_identity = (# All Identity Documents
                                      {"name": "identity",
                                       "joinby": "person_id",
                                       },
                                      # Passports in particular
                                      {"name": "passport",
                                       "joinby": "person_id",
                                       "filterby": {
                                           "type": 1,
                                           },
                                       },
                                      # National ID in particular
                                      {"name": "national_id",
                                       "joinby": "person_id",
                                       "filterby": {
                                           "type": 2,
                                           },
                                       },
                                      ),
                       # Personal Details
                       pr_person_details = {"joinby": "person_id",
                                            "multiple": False,
                                            },
                       # Locations
                       gis_location = {"link": "pr_person_location",
                                       "joinby": "person_id",
                                       "key": "location_id",
                                       "actuate": "hide",
                                       },
                       pr_person_location = "person_id",

                       # Tags
                       pr_person_tag = "person_id",

                       # Seized Items (owner)
                       security_seized_item = "person_id",

                       # Supply Items (Donor)
                       supply_item = {"link": "supply_person_item",
                                      "joinby": "person_id",
                                      "key": "item_id",
                                      "actuate": "hide",
                                      },
                       supply_person_item = "person_id",
                       )

        # Beneficiary/Case Management
        if settings.has_module("br"):
            # Use BR for case management
            add_components(tablename,
                           # Beneficiary Registry
                           br_case = {"joinby": "person_id",
                                      "multiple": False,
                                      },
                           br_case_language = "person_id",
                           br_case_activity = "person_id",
                           br_assistance_measure = "person_id",
                           br_note = {"name": "br_note",
                                      "joinby": "person_id",
                                      },
                           br_service_contact = "person_id",
                           )
        else:
            # Use DVR for case management
            add_components(tablename,
                           dvr_allowance = "person_id",
                           dvr_case = {"name": "dvr_case",
                                       "joinby": "person_id",
                                       "multiple": False,
                                       },
                           dvr_case_activity = "person_id",
                           dvr_response_action = "person_id",
                           dvr_case_appointment = "person_id",
                           dvr_case_details = {"joinby": "person_id",
                                               "multiple": False,
                                               },
                           dvr_case_effort = "person_id",
                           dvr_case_event = "person_id",
                           dvr_case_flag_case = {"name": "dvr_flag",
                                                 "joinby": "person_id",
                                                 },
                           dvr_case_flag = {"link": "dvr_case_flag_case",
                                            "joinby": "person_id",
                                            "key": "flag_id",
                                            "actuate": "link",
                                            "autodelete": False,
                                            },
                           dvr_case_language = "person_id",
                           dvr_economy = {"joinby": "person_id",
                                          "multiple": False,
                                          },
                           dvr_evaluation = {"joinby": "person_id",
                                             "multiple": False,
                                             },
                           dvr_household = {"joinby": "person_id",
                                            "multiple": False,
                                            },
                           dvr_household_member = "person_id",
                           dvr_note = {"name": "case_note",
                                       "joinby": "person_id",
                                       },
                           dvr_residence_status = "person_id",
                           dvr_service_contact = "person_id",
                           )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"pr_gender": pr_gender,
                "pr_gender_opts": pr_gender_opts,
                "pr_person_id": person_id,
                "pr_person_lookup": self.pr_person_lookup,
                "pr_person_represent": person_represent,
                }

    # -------------------------------------------------------------------------
    @classmethod
    def pr_person_age(cls, row):
        """
            Virtual Field to display the Age of a person

            @param row: a Row containing the person record
        """

        age = cls.pr_age(row)
        if age is None or age < 0:
            return current.messages["NONE"]
        else:
            return age

    # -------------------------------------------------------------------------
    @classmethod
    def pr_person_age_group(cls, row):
        """
            Virtual Field to allow Reporting by Age Group

            @param row: a Row containing the person record

            @ToDo: This formula might need to be different for different Orgs
                   or Usecases
            @ToDo: If we need to be able to Filter based on these then we should
                   create a 'Named Range' widget for an S3DateTimeFilter field
        """

        age = cls.pr_age(row)
        if age is None or age < 0:
            return current.messages["NONE"]
        else:
            return current.deployment_settings.get_pr_age_group(age)

    # -------------------------------------------------------------------------
    @staticmethod
    def pr_age(row):
        """
            Compute the age of a person

            @param row: a Row containing the person record
            @return: age in years (integer)
        """

        if hasattr(row, "pr_person"):
            row = row.pr_person
        if hasattr(row, "date_of_birth"):
            dob = row.date_of_birth
        elif hasattr(row, "id"):
            # date_of_birth not in row: reload the record
            table = current.s3db.pr_person
            person = current.db(table.id == row.id).select(
                                                     table.date_of_birth,
                                                     limitby=(0, 1)).first()
            dob = person.date_of_birth if person else None
        else:
            dob = None
        if dob:
            from dateutil.relativedelta import relativedelta
            return relativedelta(current.request.utcnow.date(), dob).years
        else:
            return None

    # -------------------------------------------------------------------------
    @staticmethod
    def pr_person_onaccept(form):
        """
            Onaccept callback
            Update any User record associated with this person
        """

        db = current.db
        s3db = current.s3db

        form_vars_get = form.vars.get
        person_id = form_vars_get("id")

        ptable = s3db.pr_person
        ltable = s3db.pr_person_user
        utable = current.auth.settings.table_user

        # Check if this person has a User account
        query = (ptable.id == person_id) & \
                (ltable.pe_id == ptable.pe_id) & \
                (utable.id == ltable.user_id)
        user = db(query).select(utable.id,
                                utable.first_name,
                                utable.last_name,
                                limitby=(0, 1)).first()

        if user:
            # Update in case Names have changed
            first_name = form_vars_get("first_name")
            middle_name = form_vars_get("middle_name")
            last_name = form_vars_get("last_name")
            middle_as_last = current.deployment_settings.get_L10n_mandatory_middlename()
            if middle_as_last:
                # RMSAmericas: Map the Person's middle_name to the User's last_name
                if first_name and \
                   (user.first_name != first_name or \
                   user.last_name != middle_name):
                    # Update the user record
                    query = (utable.id == user.id)
                    db(query).update(first_name = first_name,
                                     last_name = middle_name,
                                     )
            else:
                if first_name and \
                   (user.first_name != first_name or \
                   user.last_name != last_name):
                    # Update the user record
                    query = (utable.id == user.id)
                    db(query).update(first_name = first_name,
                                     last_name = last_name,
                                     )

    # -------------------------------------------------------------------------
    @staticmethod
    def person_duplicate(item):
        """ Import item deduplication """

        db = current.db

        data = item.data

        # Master field (if-present)
        pe_label = data.get("pe_label")
        if pe_label:
            # Just look at this
            table = item.table
            duplicate = db(table.pe_label == pe_label).select(table.id,
                                                              limitby=(0, 1)
                                                              ).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE

            return

        settings = current.deployment_settings
        middle_mandatory = settings.get_L10n_mandatory_middlename()

        ptable = db.pr_person
        # Mandatory data
        fname = data.get("first_name")
        mname = data.get("middle_name")
        lname = data.get("last_name")
        if fname:
            fname = s3_unicode(fname).lower()
        if mname:
            mname = s3_unicode(mname).lower()
        if lname:
            lname = s3_unicode(lname).lower()
        initials = data.get("initials")
        if initials:
            initials = s3_unicode(initials).lower()

        # @ToDo: Allow each name to be split into words in a different order
        # - see pr_search_ac
        if middle_mandatory and fname and mname:
            query = (ptable.first_name.lower() == fname) & \
                    (ptable.middle_name.lower() == mname)
        elif fname and lname:
            query = (ptable.first_name.lower() == fname) & \
                    (ptable.last_name.lower() == lname)
        elif fname and mname:
            query = (ptable.first_name.lower() == fname) & \
                    (ptable.middle_name.lower() == mname)
        elif initials:
            query = (ptable.initials.lower() == initials)
        else:
            # Not enough we can use
            return

        # Optional extra data
        dob = data.get("date_of_birth")
        email = sms = None
        hr_code = None
        identities = {}
        for citem in item.components:
            data = citem.data
            if data:
                ctablename = citem.tablename
                if ctablename == "pr_contact":
                    contact_method = data.get("contact_method")
                    if contact_method == "EMAIL":
                        email = data.value
                    elif contact_method == "SMS":
                        sms = data.value
                elif ctablename == "pr_identity":
                    id_type = data.get("type")
                    id_value = data.get("value")
                    if id_type and id_value:
                        identities[id_type] = id_value
                elif ctablename == "hrm_human_resource":
                    # Organisation ID
                    # Note that we cannot see the Organisation here, so need to assume that these are unique across all Organisations
                    # - therefore we make this a low priority additional check
                    hr_code = data.get("code")

        s3db = current.s3db
        ctable = s3db.pr_contact
        etable = ctable.with_alias("pr_email")

        fields = [ptable._id,
                  ptable.first_name,
                  ptable.middle_name,
                  ptable.last_name,
                  ptable.initials,
                  etable.value,
                  ]

        left = [etable.on((etable.pe_id == ptable.pe_id) & \
                          (etable.contact_method == "EMAIL")),
                ]

        if dob:
            fields.append(ptable.date_of_birth)

        if sms:
            stable = ctable.with_alias("pr_sms")
            fields.append(stable.value)
            left.append(stable.on((stable.pe_id == ptable.pe_id) & \
                                  (stable.contact_method == "SMS")))
        if identities:
            itable = s3db.pr_identity
            fields += [itable.type,
                       itable.value,
                       ]
            left.append(itable.on(itable.person_id == ptable.id))

        if hr_code:
            htable = s3db.hrm_human_resource
            fields.append(htable.code)
            left.append(htable.on(htable.person_id == ptable.id))

        candidates = db(query).select(*fields,
                                      left=left,
                                      orderby=["pr_person.created_on ASC"])

        if not candidates:
            return

        duplicates = Storage()

        def rank(a, b, match, mismatch):
            return match if a == b else mismatch

        email_required = settings.get_pr_import_update_requires_email()
        for row in candidates:
            if fname and (lname or mname):
                row_fname = row[ptable.first_name]
                row_mname = row[ptable.middle_name]
                row_lname = row[ptable.last_name]
            if initials:
                row_initials = row[ptable.initials]
            if dob:
                row_dob = row[ptable.date_of_birth]
            row_email = row[etable.value]
            if sms:
                row_sms = row[stable.value]
            if identities:
                row_id_type = row[itable.type]
                row_id_value = row[itable.value]
            if hr_code:
                row_hr_code = row[htable.code]

            check = 0

            if fname and row_fname:
                check += rank(fname, row_fname.lower(), +2, -2)

            if mname:
                if row_mname:
                    check += rank(mname, row_mname.lower(), +2, -2)
                #elif middle_mandatory:
                #    check -= 2
                else:
                    # Don't penalise hard if the new source doesn't include the middle name
                    check -= 1

            if lname:
                if row_lname:
                    check += rank(lname, row_lname.lower(), +2, -2)
                #elif middle_mandatory:
                #    # Don't penalise if the new source doesn't include the last name
                #    pass
                #else:
                #    # Don't penalise hard if the new source doesn't include the last name
                #    check -= 1

            if initials and row_initials:
                check += rank(initials, row_initials.lower(), +4, -1)

            if dob and row_dob:
                check += rank(dob, row_dob, +3, -2)

            if email and row_email:
                check += rank(email.lower(), row_email.lower(), +2, -5)
            elif not email and email_required:
                # Treat missing email as mismatch
                check -= 2 if initials else 3 if not row_email else 4

            if sms and row_sms:
                check += rank(sms.lower(), row_sms.lower(), +1, -1)

            if identities and row_id_type:
                id_value = identities.get(str(row_id_type), None)
                if id_value and row_id_value:
                    check += rank(id_value, row_id_value, +5, -2)

            if hr_code and row_hr_code:
                check += rank(hr_code.lower(), row_hr_code.lower(), +2, -2)

            if check in duplicates:
                continue
            else:
                duplicates[check] = row

        if len(duplicates):
            best_match = max(duplicates.keys())
            if best_match > 0:
                duplicate = duplicates[best_match]
                item.id = duplicate[ptable.id]
                item.method = item.METHOD.UPDATE
                for citem in item.components:
                    citem.method = citem.METHOD.UPDATE

        return

    # -------------------------------------------------------------------------
    @staticmethod
    def pr_search_ac(r, **attr):
        """
            JSON search method for S3PersonAutocompleteWidget and
            S3AddPersonWidget:
            - full name search
        """

        response = current.response
        resource = r.resource

        # Query comes in pre-filtered to accessible & deletion_status
        # Respect response.s3.filter
        resource.add_filter(response.s3.filter)

        get_vars = current.request.get_vars

        # JQueryUI Autocomplete uses "term"
        # old JQuery Autocomplete uses "q"
        # what uses "value"?
        value = get_vars.term or get_vars.value or get_vars.q or None

        if not value:
            r.error(400, "No value provided!")

        # We want to do case-insensitive searches
        # (default anyway on MySQL/SQLite, but not PostgreSQL)
        value = s3_unicode(value).lower()
        value = value.strip()

        settings = current.deployment_settings
        name_format = settings.get_pr_name_format()
        middle_name = "middle_name" in name_format

        # Names could be in the wrong order
        # Multiple Names could be in a single field
        # Each name field could be split into words in a different order
        # @ToDo: deployment_setting for fully loose matching?
        # Single search term
        # Value can be (part of) any of first_name, middle_name or last_name
        query = (FS("first_name").lower().like(value + "%")) | \
                (FS("last_name").lower().like(value + "%"))
        if middle_name:
            query |= (FS("middle_name").lower().like(value + "%"))
        if " " in value:
            # Two search terms
            # Values can be (part of) any of first_name, middle_name or last_name
            # but we must have a (partial) match on both terms
            # We must have a (partial) match on both terms
            value1, value2 = value.split(" ", 1)
            query |= (((FS("first_name").lower().like(value1 + "%")) & \
                       (FS("last_name").lower().like(value2 + "%"))) | \
                      ((FS("first_name").lower().like(value2 + "%")) & \
                       (FS("last_name").lower().like(value1 + "%"))))
            if middle_name:
                query |= (((FS("first_name").lower().like(value1 + "%")) & \
                           (FS("middle_name").lower().like(value2 + "%"))) | \
                          ((FS("first_name").lower().like(value2 + "%")) & \
                           (FS("middle_name").lower().like(value1 + "%"))) | \
                          ((FS("middle_name").lower().like(value1 + "%")) & \
                           (FS("last_name").lower().like(value2 + "%"))) | \
                          ((FS("middle_name").lower().like(value2 + "%")) & \
                           (FS("last_name").lower().like(value1 + "%"))))
            if " " in value2:
                # Three search terms
                # Values can be (part of) any of first_name, middle_name or last_name
                # but we must have a (partial) match on all terms
                value21, value3 = value2.split(" ", 1)
                value12 = "%s %s" % (value1, value21)
                query |= (((FS("first_name").lower().like(value12 + "%")) & \
                           (FS("last_name").lower().like(value3 + "%"))) | \
                          ((FS("first_name").lower().like(value3 + "%")) & \
                           (FS("last_name").lower().like(value12 + "%"))))
                if middle_name:
                    query |= (((FS("first_name").lower().like(value1 + "%")) & \
                               (FS("middle_name").lower().like(value21 + "%")) & \
                               (FS("last_name").lower().like(value3 + "%"))) | \
                              ((FS("first_name").lower().like(value1 + "%")) & \
                               (FS("last_name").lower().like(value21 + "%")) & \
                               (FS("middle_name").lower().like(value3 + "%"))) | \
                              ((FS("last_name").lower().like(value1 + "%")) & \
                               (FS("middle_name").lower().like(value21 + "%")) & \
                               (FS("first_name").lower().like(value3 + "%"))) | \
                              ((FS("last_name").lower().like(value1 + "%")) & \
                               (FS("first_name").lower().like(value21 + "%")) & \
                               (FS("middle_name").lower().like(value3 + "%"))))
                if " " in value3:
                    # Four search terms
                    # Values can be (part of) any of first_name, middle_name or last_name
                    # but we must have a (partial) match on all terms
                    value31, value4 = value3.split(" ", 1)
                    value13 = "%s %s %s" % (value1, value21, value31)
                    value22 = "%s %s" % (value21, value31)
                    query |= (((FS("first_name").lower().like(value13 + "%")) & \
                               (FS("last_name").lower().like(value4 + "%"))) | \
                              ((FS("first_name").lower().like(value4 + "%")) & \
                               (FS("last_name").lower().like(value13 + "%"))))
                    if middle_name:
                        query |= (((FS("first_name").lower().like(value1 + "%")) & \
                                   (FS("middle_name").lower().like(value22 + "%")) & \
                                   (FS("last_name").lower().like(value4 + "%"))) | \
                                  ((FS("first_name").lower().like(value1 + "%")) & \
                                   (FS("last_name").lower().like(value22 + "%")) & \
                                   (FS("middle_name").lower().like(value4 + "%"))) | \
                                  ((FS("last_name").lower().like(value1 + "%")) & \
                                   (FS("middle_name").lower().like(value22 + "%")) & \
                                   (FS("first_name").lower().like(value4 + "%"))) | \
                                  ((FS("last_name").lower().like(value1 + "%")) & \
                                   (FS("first_name").lower().like(value22 + "%")) & \
                                   (FS("middle_name").lower().like(value4 + "%"))) | \
                                  ((FS("first_name").lower().like(value12 + "%")) & \
                                   (FS("middle_name").lower().like(value31 + "%")) & \
                                   (FS("last_name").lower().like(value4 + "%"))) | \
                                  ((FS("first_name").lower().like(value12 + "%")) & \
                                   (FS("last_name").lower().like(value31 + "%")) & \
                                   (FS("middle_name").lower().like(value4 + "%"))) | \
                                  ((FS("last_name").lower().like(value12 + "%")) & \
                                   (FS("middle_name").lower().like(value31 + "%")) & \
                                   (FS("first_name").lower().like(value4 + "%"))) | \
                                  ((FS("last_name").lower().like(value12 + "%")) & \
                                   (FS("first_name").lower().like(value31 + "%")) & \
                                   (FS("middle_name").lower().like(value4 + "%"))))

        resource.add_filter(query)

        limit = int(get_vars.limit or 0)
        MAX_SEARCH_RESULTS = settings.get_search_max_results()
        if (not limit or limit > MAX_SEARCH_RESULTS) and \
           resource.count() > MAX_SEARCH_RESULTS:
            msg = current.T("There are more than %(max)s results, please input more characters.")
            output = [{"label": s3_str(msg % {"max": MAX_SEARCH_RESULTS})}]
        else:
            fields = ["id",
                      "first_name",
                      "middle_name",
                      "last_name",
                      ]

            show_pe_label = get_vars.get("label") == "1"
            if show_pe_label:
                fields.append("pe_label")

            show_hr = settings.get_pr_search_shows_hr_details()
            if show_hr:
                fields.append("human_resource.job_title_id$name")
                show_orgs = settings.get_hrm_show_organisation()
                if show_orgs:
                    fields.append("human_resource.organisation_id$name")

            name_format = settings.get_pr_name_format()
            import re
            match = re.match(r"\s*?%\((?P<fname>.*?)\)s.*", name_format)
            if match:
                orderby = "pr_person.%s" % match.group("fname")
            else:
                orderby = "pr_person.first_name"
            #test = name_format % dict(first_name=1,
                                      #middle_name=2,
                                      #last_name=3,
                                      #)
            #test = "".join(ch for ch in test if ch in ("1", "2", "3"))
            #if test[:1] == "1":
                #orderby = "pr_person.first_name"
            #elif test[:1] == "2":
                #orderby = "pr_person.middle_name"
            #else:
                #orderby = "pr_person.last_name"
            rows = resource.select(fields = fields,
                                   start = 0,
                                   limit = limit,
                                   orderby = orderby,
                                   ).rows

            items = []
            iappend = items.append
            for row in rows:
                name = Storage(first_name=row["pr_person.first_name"],
                               middle_name=row["pr_person.middle_name"],
                               last_name=row["pr_person.last_name"],
                               )

                item = {"id"    : row["pr_person.id"],
                        "name"  : s3_fullname(name),
                        }

                if show_pe_label:
                    item["pe_label"] = row["pr_person.pe_label"]

                if show_hr:
                    job_title = row.get("hrm_job_title.name", None)
                    if job_title:
                        item["job"] = job_title
                    if show_orgs:
                        org = row.get("org_organisation.name", None)
                        if org:
                            item["org"] = org

                iappend(item)

            output = items

        response.headers["Content-Type"] = "application/json"
        return json.dumps(output, separators=SEPARATORS)

    # -------------------------------------------------------------------------
    @staticmethod
    def pr_person_lookup(r, **attr):
        """
            JSON lookup method for S3AddPersonWidget:
            - extract form data for a match in duplicate list
        """

        if r.tablename == "org_site":
            # Coming from site_contact_person
            site_contact_person = True
            record_id = attr.get("person_id")
            resource = current.s3db.resource("pr_person", id=record_id)
        else:
            site_contact_person = False
            record_id = r.id
            resource = r.resource

        current.response.headers["Content-Type"] = "application/json"

        get_vars = r.get_vars
        if not record_id:
            if get_vars.get("search") == "1":
                # Allow other URL filters to identify the record
                # (e.g. pe_id, uuid or pe_label)
                resource.load(start=0, limit=2)
                if len(resource) == 1:
                    # Found exactly one match
                    record_id = resource.records().first().id
                else:
                    # Return blank (no error when search=1)
                    return "{}"
            else:
                r.error(400, "No Record ID provided")

        # NB Requirement to identify a single record also (indirectly)
        #    requires read permission to that record (=>S3Request).
        #
        #    However: that does not imply that the user also has
        #    permission to see person details or contact information,
        #    so sub-queries must apply s3_accessible_query for those
        #    (independently of the widget => URL exploit)

        db = current.db
        s3db = current.s3db
        settings = current.deployment_settings

        auth = current.auth
        accessible_query = auth.s3_accessible_query

        request_dob = settings.get_pr_request_dob()
        request_gender = settings.get_pr_request_gender()
        home_phone = settings.get_pr_request_home_phone()
        get_pe_label = get_vars.get("label") == "1"

        ptable = db.pr_person
        ctable = s3db.pr_contact
        fields = [ptable.pe_id,
                  # We have these already from the search_ac unless we separate_name_fields
                  #ptable.first_name,
                  #ptable.middle_name,
                  #ptable.last_name,
                  ]

        separate_name_fields = settings.get_pr_separate_name_fields()
        get_name = separate_name_fields or get_vars.get("name") == "1"

        if get_name or site_contact_person:
            middle_name = separate_name_fields == 3
            fields.extend((ptable.first_name,
                           ptable.middle_name,
                           ptable.last_name,
                           ))

        left = None
        if get_pe_label:
            fields.append(ptable.pe_label)
        if request_dob:
            fields.append(ptable.date_of_birth)
        if request_gender:
            fields.append(ptable.gender)
        if current.request.controller == "vol":
            dtable = s3db.pr_person_details
            fields.append(dtable.occupation)
            # @ToDo: deployment_settings? Args passed into fn?
            fields += [dtable.father_name,
                       dtable.grandfather_name,
                       dtable.year_of_birth,
                       ]
            left = dtable.on((dtable.person_id == ptable.id) & \
                             (accessible_query("read", dtable)))

        row = db(ptable.id == record_id).select(left=left, *fields).first()

        if left:
            details = row.pr_person_details
            occupation = details.occupation
            father_name = details.father_name
            grandfather_name = details.grandfather_name
            year_of_birth = details.year_of_birth
            row = row.pr_person
        else:
            occupation = None
            father_name = None
            grandfather_name = None
            year_of_birth = None

        if separate_name_fields:
            first_name = row.first_name
            last_name = row.last_name
            if middle_name:
                middle_name = row.middle_name
        elif get_name or site_contact_person:
            name = s3_fullname(row)
        pe_label = row.pe_label if get_pe_label else None
        if request_dob:
            date_of_birth = row.date_of_birth
        else:
            date_of_birth = None
        if request_gender:
            gender = row.gender
        else:
            gender = None

        # Lookup contacts separately as we can't limitby here
        if home_phone:
            contact_methods = ("SMS", "EMAIL", "HOME_PHONE")
        else:
            contact_methods = ("SMS", "EMAIL")
        query = (ctable.pe_id == row.pe_id) & \
                (ctable.contact_method.belongs(contact_methods)) & \
                accessible_query("read", ctable)
        rows = db(query).select(ctable.contact_method,
                                ctable.value,
                                orderby = ctable.priority,
                                )
        email = mobile_phone = None
        if home_phone:
            home_phone = None
            for row in rows:
                if not email and row.contact_method == "EMAIL":
                    email = row.value
                elif not mobile_phone and row.contact_method == "SMS":
                    mobile_phone = row.value
                elif not home_phone and row.contact_method == "HOME_PHONE":
                    home_phone = row.value
                if email and mobile_phone and home_phone:
                    break
        else:
            for row in rows:
                if not email and row.contact_method == "EMAIL":
                    email = row.value
                elif not mobile_phone and row.contact_method == "SMS":
                    mobile_phone = row.value
                if email and mobile_phone:
                    break

        # Minimal flattened structure
        item = {}
        if site_contact_person or not r.id:
            item["id"] = record_id
        if separate_name_fields:
            item["first_name"] = first_name
            item["last_name"] = last_name
            if middle_name:
                item["middle_name"] = middle_name
        elif get_name or site_contact_person:
            item["name"] = name
        if pe_label:
            item["pe_label"] = pe_label
        if email:
            item["email"] = email
        if mobile_phone:
            item["mphone"] = mobile_phone
        if home_phone:
            item["hphone"] = home_phone
        if gender:
            item["sex"] = gender
        if date_of_birth:
            represent = ptable.date_of_birth.represent
            item["dob"] = represent(date_of_birth)
        if occupation:
            item["occupation"] = occupation
        if father_name:
            item["father_name"] = father_name
        if grandfather_name:
            item["grandfather_name"] = grandfather_name
        if year_of_birth:
            item["year_of_birth"] = year_of_birth
        output = json.dumps(item, separators=SEPARATORS)

        current.response.headers["Content-Type"] = "application/json"
        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def pr_person_check_duplicates(r, **attr):
        """
            JSON lookup method for S3AddPersonWidget:
            - find potential duplicates from the current input data
        """

        settings = current.deployment_settings

        # Read Input
        post_vars = current.request.post_vars
        dob = post_vars.get("dob", None)
        if dob:
            # Parse Date
            dob, error = s3_validate(current.s3db.pr_person, "date_of_birth", dob)
            if not error:
                dob = dob.isoformat()
            else:
                dob = None
        gender = post_vars.get("sex")
        father_name = post_vars.get("father_name")
        grandfather_name = post_vars.get("grandfather_name")
        occupation = post_vars.get("occupation")
        mobile_phone = post_vars.get("mphone")
        home_phone = post_vars.get("hphone")
        email = post_vars.get("email")

        # @ToDo: Fuzzy Search
        # We need to use an Index since we can't read all values in do client-side
        # e.g. (Double) Metaphone or Levenshtein
        # Options:
        # * SOLR: http://wiki.apache.org/solr/AnalyzersTokenizersTokenFilters
        #         http://stackoverflow.com/questions/2116832/how-to-use-wildchards-fuzzy-search-with-solr
        #         http://stackoverflow.com/questions/9883151/solr-fuzzy-search-for-similar-words
        # * Whoosh: https://pypi.python.org/pypi/Whoosh/
        # * Postgres (1st is faster on large DBs):
        #    * http://www.postgresql.org/docs/9.3/static/pgtrgm.html
        #    * http://www.postgresql.org/docs/9.3/static/fuzzystrmatch.html
        # * MySQL:
        #    * http://forums.mysql.com/read.php?20,282935,282935#msg-282935

        # Setting can be overridden per-instance, so must
        # introspect the data here rather than looking at the setting:
        #separate_name_fields = settings.get_pr_separate_name_fields()
        separate_name_fields = "first_name" in post_vars

        if separate_name_fields:
            #middle_name_field = separate_name_fields == 3
            middle_name_field = "middle_name" in post_vars

            first_name = post_vars.get("first_name")
            if first_name:
                first_name = s3_unicode(first_name).lower().strip()
            middle_name = post_vars.get("middle_name")
            if middle_name:
                middle_name = s3_unicode(middle_name).lower().strip()
            last_name = post_vars.get("last_name")
            if last_name:
                last_name = s3_unicode(last_name).lower().strip()

            # Names could be in the wrong order
            # @ToDo: Allow each name to be split into words in a different order
            query = (FS("first_name").lower().like(first_name + "%")) | \
                    (FS("middle_name").lower().like(first_name + "%")) | \
                    (FS("last_name").lower().like(first_name + "%"))
            if middle_name:
                query |= (FS("first_name").lower().like(middle_name + "%")) | \
                         (FS("middle_name").lower().like(middle_name + "%")) | \
                         (FS("last_name").lower().like(middle_name + "%"))
            if last_name:
                query |= (FS("first_name").lower().like(last_name + "%")) | \
                         (FS("middle_name").lower().like(last_name + "%")) | \
                         (FS("last_name").lower().like(last_name + "%"))

        else:
            # https://github.com/derek73/python-nameparser
            #from nameparser import HumanName
            #name = HumanName(name.lower())
            #first_name = name.first
            #middle_name = name.middle
            #last_name = name.last
            ##nick_name = name.nickname

            name_format = settings.get_pr_name_format()
            middle_name = "middle_name" in name_format

            # Names could be in the wrong order
            # Multiple Names could be in a single field
            # Each name field could be split into words in a different order
            # @ToDo: deployment_setting for fully loose matching?
            # Single search term
            # Value can be (part of) any of first_name, middle_name or last_name
            value = post_vars.get("name")
            if value:
                value = value.lower()
            query = (FS("first_name").lower().like(value + "%")) | \
                    (FS("last_name").lower().like(value + "%"))
            if middle_name:
                query |= (FS("middle_name").lower().like(value + "%"))
            if " " in value:
                # Two search terms
                # Values can be (part of) any of first_name, middle_name or last_name
                # but we must have a (partial) match on both terms
                # We must have a (partial) match on both terms
                value1, value2 = value.split(" ", 1)
                query |= (((FS("first_name").lower().like(value1 + "%")) & \
                           (FS("last_name").lower().like(value2 + "%"))) | \
                          ((FS("first_name").lower().like(value2 + "%")) & \
                           (FS("last_name").lower().like(value1 + "%"))))
                if middle_name:
                    query |= (((FS("first_name").lower().like(value1 + "%")) & \
                               (FS("middle_name").lower().like(value2 + "%"))) | \
                              ((FS("first_name").lower().like(value2 + "%")) & \
                               (FS("middle_name").lower().like(value1 + "%"))) | \
                              ((FS("middle_name").lower().like(value1 + "%")) & \
                               (FS("last_name").lower().like(value2 + "%"))) | \
                              ((FS("middle_name").lower().like(value2 + "%")) & \
                               (FS("last_name").lower().like(value1 + "%"))))
                if " " in value2:
                    # Three search terms
                    # Values can be (part of) any of first_name, middle_name or last_name
                    # but we must have a (partial) match on all terms
                    value21, value3 = value2.split(" ", 1)
                    value12 = "%s %s" % (value1, value21)
                    query |= (((FS("first_name").lower().like(value12 + "%")) & \
                               (FS("last_name").lower().like(value3 + "%"))) | \
                              ((FS("first_name").lower().like(value3 + "%")) & \
                               (FS("last_name").lower().like(value12 + "%"))))
                    if middle_name:
                        query |= (((FS("first_name").lower().like(value1 + "%")) & \
                                   (FS("middle_name").lower().like(value21 + "%")) & \
                                   (FS("last_name").lower().like(value3 + "%"))) | \
                                  ((FS("first_name").lower().like(value1 + "%")) & \
                                   (FS("last_name").lower().like(value21 + "%")) & \
                                   (FS("middle_name").lower().like(value3 + "%"))) | \
                                  ((FS("last_name").lower().like(value1 + "%")) & \
                                   (FS("middle_name").lower().like(value21 + "%")) & \
                                   (FS("first_name").lower().like(value3 + "%"))) | \
                                  ((FS("last_name").lower().like(value1 + "%")) & \
                                   (FS("first_name").lower().like(value21 + "%")) & \
                                   (FS("middle_name").lower().like(value3 + "%"))))
                    if " " in value3:
                        # Four search terms
                        # Values can be (part of) any of first_name, middle_name or last_name
                        # but we must have a (partial) match on all terms
                        value31, value4 = value3.split(" ", 1)
                        value13 = "%s %s %s" % (value1, value21, value31)
                        value22 = "%s %s" % (value21, value31)
                        query |= (((FS("first_name").lower().like(value13 + "%")) & \
                                   (FS("last_name").lower().like(value4 + "%"))) | \
                                  ((FS("first_name").lower().like(value4 + "%")) & \
                                   (FS("last_name").lower().like(value13 + "%"))))
                        if middle_name:
                            query |= (((FS("first_name").lower().like(value1 + "%")) & \
                                       (FS("middle_name").lower().like(value22 + "%")) & \
                                       (FS("last_name").lower().like(value4 + "%"))) | \
                                      ((FS("first_name").lower().like(value1 + "%")) & \
                                       (FS("last_name").lower().like(value22 + "%")) & \
                                       (FS("middle_name").lower().like(value4 + "%"))) | \
                                      ((FS("last_name").lower().like(value1 + "%")) & \
                                       (FS("middle_name").lower().like(value22 + "%")) & \
                                       (FS("first_name").lower().like(value4 + "%"))) | \
                                      ((FS("last_name").lower().like(value1 + "%")) & \
                                       (FS("first_name").lower().like(value22 + "%")) & \
                                       (FS("middle_name").lower().like(value4 + "%"))) | \
                                      ((FS("first_name").lower().like(value12 + "%")) & \
                                       (FS("middle_name").lower().like(value31 + "%")) & \
                                       (FS("last_name").lower().like(value4 + "%"))) | \
                                      ((FS("first_name").lower().like(value12 + "%")) & \
                                       (FS("last_name").lower().like(value31 + "%")) & \
                                       (FS("middle_name").lower().like(value4 + "%"))) | \
                                      ((FS("last_name").lower().like(value12 + "%")) & \
                                       (FS("middle_name").lower().like(value31 + "%")) & \
                                       (FS("first_name").lower().like(value4 + "%"))) | \
                                      ((FS("last_name").lower().like(value12 + "%")) & \
                                       (FS("first_name").lower().like(value31 + "%")) & \
                                       (FS("middle_name").lower().like(value4 + "%"))))

        resource = r.resource
        resource.add_filter(query)

        fields = ["id",
                  "first_name",
                  "middle_name",
                  "last_name",
                  "date_of_birth",
                  "gender",
                  "person_details.father_name",
                  "person_details.grandfather_name",
                  "person_details.occupation",
                  "image.image",
                  ]

        MAX_SEARCH_RESULTS = settings.get_search_max_results()
        show_hr = settings.get_pr_search_shows_hr_details()
        if show_hr:
            fields.append("human_resource.job_title_id$name")
            show_orgs = settings.get_hrm_show_organisation()
            if show_orgs:
                fields.append("human_resource.organisation_id$name")

        rows = resource.select(fields=fields,
                               start=0,
                               limit=MAX_SEARCH_RESULTS)["rows"]

        # If no results then search other fields
        # @ToDo: Do these searches anyway & merge results together
        if not len(rows):
            rfilter = resource.rfilter
            if dob:
                # Try DoB
                # Remove the name filter (last one in)
                rfilter.filters.pop()
                rfilter.query = None
                rfilter.transformed = None
                query = (FS("date_of_birth") == dob)
                resource.add_filter(query)
                rows = resource.select(fields=fields,
                                       start=0,
                                       limit=MAX_SEARCH_RESULTS)["rows"]
            if not len(rows) and email:
                # Try Email
                # Remove the name or DoB filter (last one in)
                rfilter.filters.pop()
                rfilter.query = None
                rfilter.transformed = None
                query = (FS("contact.value") == email) & (FS("contact.contact_method") == "EMAIL")
                resource.add_filter(query)
                rows = resource.select(fields=fields,
                                       start=0,
                                       limit=MAX_SEARCH_RESULTS)["rows"]
            if not len(rows) and mobile_phone:
                # Try Mobile Phone
                # Remove the name or DoB or email filter (last one in)
                rfilter.filters.pop()
                rfilter.query = None
                rfilter.transformed = None
                query = (FS("contact.value") == mobile_phone) & (FS("contact.contact_method") == "SMS")
                resource.add_filter(query)
                rows = resource.select(fields=fields,
                                       start=0,
                                       limit=MAX_SEARCH_RESULTS)["rows"]
            if not len(rows) and home_phone:
                # Try Home Phone
                # Remove the name or DoB or email or mobile filter (last one in)
                rfilter.filters.pop()
                rfilter.query = None
                rfilter.transformed = None
                query = (FS("contact.value") == home_phone) & (FS("contact.contact_method") == "HOME_PHONE")
                resource.add_filter(query)
                rows = resource.select(fields=fields,
                                       start=0,
                                       limit=MAX_SEARCH_RESULTS)["rows"]

        # @ToDo: Separate lookup for Contacts
        #query = (ctable.pe_id == person.pe_id) & \
        #        (ctable.deleted == False) & \
        #        (ctable.contact_method.belongs(contact_methods))
        #contacts = db(query).select(ctable.contact_method,
        #                            ctable.value,
        #                            orderby=ctable.priority,
        #                            )
        #email = mobile_phone = ""
        #if req_home_phone:
        #    home_phone = ""
        #    for contact in contacts:
        #        if not email and contact.contact_method == "EMAIL":
        #            email = contact.value
        #        elif not mobile_phone and contact.contact_method == "SMS":
        #            mobile_phone = contact.value
        #        elif not home_phone and contact.contact_method == "HOME_PHONE":
        #            home_phone = contact.value
        #        if email and mobile_phone and home_phone:
        #            break
        #    values["home_phone"] = home_phone
        #else:
        #    for contact in contacts:
        #        if not email and contact.contact_method == "EMAIL":
        #            email = contact.value
        #        elif not mobile_phone and contact.contact_method == "SMS":
        #            mobile_phone = contact.value
        #        if email and mobile_phone:
        #            break
        #values["email"] = email
        #values["mobile_phone"] = mobile_phone

        # @ToDo: Rank rows
        # Correct DoB
        # Correct Email
        # Correct Phone
        # Correct Gender
        # Exact Name Match
        # Levenshtein distance on Email
        # Levenshtein distance on Phone
        # Levenshtein distance on Occupation

        items = []
        iappend = items.append
        for row in rows:
            item = {"id" : row["pr_person.id"],
                    }
            if separate_name_fields:
                item["first_name"] = row["pr_person.first_name"]
                item["last_name"] = row["pr_person.last_name"]
                if middle_name_field:
                    middle_name = row["pr_person.middle_name"]
                    if middle_name:
                        item["middle_name"] = middle_name

            name = Storage(first_name=row["pr_person.first_name"],
                           middle_name=row["pr_person.middle_name"],
                           last_name=row["pr_person.last_name"],
                           )
            name = s3_fullname(name)
            item["name"] = name

            date_of_birth = row.get("pr_person.date_of_birth")
            if date_of_birth:
                item["dob"] = date_of_birth.isoformat()
            gender = row.get("pr_person.gender")
            if gender in (2, 3, 4):
                # 1 = unknown
                item["sex"] = gender
            father_name = row.get("pr_person_details.father_name")
            if father_name:
                item["father_name"] = father_name
            grandfather_name = row.get("pr_person_details.grandfather_name")
            if grandfather_name:
                item["grandfather_name"] = grandfather_name
            occupation = row.get("pr_person_details.occupation")
            if occupation:
                item["job"] = occupation
            email = row.get("pr_contact.email")
            if email:
                item["email"] = email
            phone = row.get("pr_contact.phone")
            if phone:
                item["mphone"] = phone
            image = row.get("pr_image.image")
            if image:
                item["image"] = image
            if show_hr:
                job_title = row.get("hrm_job_title.name")
                if job_title:
                    item["job"] = job_title
                if show_orgs:
                    org = row.get("org_organisation.name")
                    if org:
                        item["org"] = org
            iappend(item)
        output = json.dumps(items, separators=SEPARATORS)

        current.response.headers["Content-Type"] = "application/json"
        return output

# =============================================================================
class PRGroupModel(S3Model):
    """ Groups """

    names = ("pr_group_status",
             "pr_group",
             "pr_group_id",
             "pr_group_membership",
             "pr_group_member_role",
             )

    def model(self):

        T = current.T
        db = current.db

        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        NONE = current.messages["NONE"]

        # ---------------------------------------------------------------------
        # Group Statuses
        #
        # @ToDo: May need to categorise these by Group Type &/or Organisation
        #
        tablename = "pr_group_status"
        define_table(tablename,
                     Field("code", length=16,
                           label = T("Code"),
                           # Make mandatory in template if-required
                           requires = IS_LENGTH(16),
                           ),
                     Field("name", length=64,
                           label = T("Name"),
                           # Make mandatory in template if-required
                           requires = IS_LENGTH(64),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        CREATE_STATUS = T("Create Group Status")
        crud_strings[tablename] = Storage(
            label_create = CREATE_STATUS,
            title_display = T("Group Status Details"),
            title_list = T("Group Statuses"),
            title_update = T("Edit Group Status"),
            label_list_button = T("List Group Statuses"),
            label_delete_button = T("Delete Group Status"),
            msg_record_created = T("Group Status added"),
            msg_record_modified = T("Group Status updated"),
            msg_record_deleted = T("Group Status deleted"),
            msg_list_empty = T("No Group Statuses currently defined"),
            )

        # Table configuration
        configure(tablename,
                  # WACOP CAD updates come in with just the Code so need to deduplicate on that
                  # @ToDo: deployment_setting if we need to support other usecases for this model
                  deduplicate = S3Duplicate(primary = ("code",),
                                            ),
                  )

        # Reusable Field
        represent = S3Represent(lookup=tablename, translate=True)
        status_id = S3ReusableField("status_id", "reference %s" % tablename,
                                    comment = S3PopupLink(c = "pr",
                                                          f = "group_status",
                                                          label = CREATE_STATUS,
                                                          title = CREATE_STATUS,
                                                          vars = {"child": "status_id"},
                                                          ),
                                    label = T("Status"),
                                    ondelete = "SET NULL",
                                    represent = represent,
                                    requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "pr_group_status.id",
                                                          represent,
                                                          )),
                                    )

        # ---------------------------------------------------------------------
        # Hard Coded Group types. Add/Comment entries, but don't remove!
        #
        pr_group_types = {1 : T("Family"),
                          2 : T("Tourist Group"),
                          3 : T("Relief Team"),
                          4 : T("other"),
                          5 : T("Mailing Lists"),
                          #6 : T("Society"),
                          7 : T("Case"),
                          }

        tablename = "pr_group"
        define_table(tablename,
                     # Instances
                     super_link("doc_id", "doc_entity"),
                     super_link("pe_id", "pr_pentity"),
                     super_link("track_id", "sit_trackable"),
                     Field("group_type", "integer",
                           default = 4,
                           label = T("Group Type"),
                           represent = S3Represent(options = pr_group_types),
                           requires = IS_IN_SET(pr_group_types, zero=None),
                           ),
                     Field("system", "boolean",
                           default = False,
                           readable = False,
                           writable = False,
                           ),
                     Field("name",
                           label = T("Group Name"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("description", length=2048, # Default is 512
                           label = T("Group Description"),
                           represent = lambda v: v or NONE,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Group description"),
                                                           T("A brief description of the group (optional)")))
                           ),
                     Field("meetings",
                           label = T("Meetings"),
                           represent = lambda v: v or NONE,
                           # Enable in Templates as-required
                           readable = False,
                           writable = False,
                           ),
                     # Base location
                     self.gis_location_id(readable = False,
                                          writable = False,
                                          ),
                     # Enable in templates as-required
                     status_id(readable = False,
                               writable = False,
                               ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Group"),
            title_display = T("Group Details"),
            title_list = T("Groups"),
            title_update = T("Edit Group"),
            label_list_button = T("List Groups"),
            label_delete_button = T("Delete Group"),
            msg_record_created = T("Group added"),
            msg_record_modified = T("Group updated"),
            msg_record_deleted = T("Group deleted"),
            msg_list_empty = T("No Groups currently registered"))

        # CRUD Strings
        mailing_list_crud_strings = Storage(
            label_create = T("Create Mailing List"),
            title_display = T("Mailing List Details"),
            title_list = T("Mailing Lists"),
            title_update = T("Edit Mailing List"),
            label_list_button = T("List Mailing Lists"),
            label_delete_button = T("Delete Mailing List"),
            msg_record_created = T("Mailing list added"),
            msg_record_modified = T("Mailing list updated"),
            msg_record_deleted = T("Mailing list deleted"),
            msg_list_empty = T("No Mailing List currently established"))

        # Resource configuration
        configure(tablename,
                  deduplicate = S3Duplicate(ignore_deleted=True),
                  extra = "description",
                  main = "name",
                  super_entity = ("doc_entity",
                                  "pr_pentity",
                                  "sit_trackable",
                                  ),
                  )

        # Reusable field
        if current.request.controller in ("hrm", "vol") and \
           current.deployment_settings.get_hrm_teams() == "Teams":
            label = T("Team")
            add_label = T("Add Team")
            title = T("Create Team")
            tooltip = T("Create a new Team")
        else:
            label = T("Group")
            add_label = crud_strings.pr_group.label_create
            title = T("Create Group")
            tooltip = T("Create a new Group")

        represent = pr_GroupRepresent()
        group_id = S3ReusableField("group_id", "reference %s" % tablename,
                                   sortby = "name",
                                   comment = S3PopupLink(#c = "pr",
                                                         f = "group",
                                                         label = add_label,
                                                         title = title,
                                                         tooltip = tooltip,
                                                         ),
                                   label = label,
                                   ondelete = "RESTRICT",
                                   represent = represent,
                                   requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "pr_group.id",
                                                          represent,
                                                          filterby="system",
                                                          filter_opts=(False,))),
                                   widget = S3AutocompleteWidget("pr", "group")
                                   )

        # Components
        self.add_components(tablename,
                            pr_person = {"link": "pr_group_membership",
                                         "joinby": "group_id",
                                         "key": "person_id",
                                         # This allows native=True to break members out if tab is 'person'
                                         # - used by CCC
                                         "actuate": "replace",
                                         },
                            pr_group_membership = "group_id",

                            # Tags
                            pr_group_tag = {"name": "tag",
                                            "joinby": "group_id",
                                            },

                            # Locations
                            gis_location = {"link": "pr_group_location",
                                            "joinby": "group_id",
                                            "key": "location_id",
                                            "actuate": "hide",
                                            "autodelete": False,
                                            },
                            pr_group_location = "group_id",

                            # Shelter (Camp) Registry
                            cr_shelter_allocation = {"joinby": "group_id",
                                                     # A group can be assigned to only one shelter
                                                     # @todo: when fully implemented this needs to allow
                                                     # multiple instances for tracking reasons
                                                     "multiple": False,
                                                     },

                            # Events
                            event_event = {"link": "event_team",
                                           "joinby": "group_id",
                                           "key": "event_id",
                                           "actuate": "hide",
                                           "autodelete": False,
                                           },

                            # Incidents
                            event_incident = (# All Incidents
                                              {"name": "incident",
                                               "link": "event_team",
                                               "joinby": "group_id",
                                               "key": "incident_id",
                                               "actuate": "hide",
                                               "autodelete": False,
                                               },
                                              # Active Incidents
                                              {"name": "active_incident",
                                               "link": "event_team",
                                               "joinby": "group_id",
                                               "key": "incident_id",
                                               "actuate": "hide",
                                               "autodelete": False,
                                               "filterby": {"closed": False,
                                                            },
                                               },
                                              ),
                            event_team = "group_id",

                            # Organisations
                            org_organisation = {"link": "org_organisation_team",
                                                "joinby": "group_id",
                                                "key": "organisation_id",
                                                "actuate": "hide",
                                                "autodelete": False,
                                                },
                            org_organisation_team = "group_id",

                            # Skills
                            hrm_skill = {"link": "pr_group_competency",
                                        "joinby": "group_id",
                                        "key": "skill_id",
                                        "actuate": "hide",
                                        "autodelete": False,
                                        },
                            pr_group_competency = "group_id",

                            # Posts
                            cms_post = {"link": "cms_post_team",
                                        "joinby": "group_id",
                                        "key": "post_id",
                                        "actuate": "replace",
                                        "autodelete": False,
                                        },
                            cms_post_team = "group_id",
                            )

        # ---------------------------------------------------------------------
        # Group Member Roles
        #
        tablename = "pr_group_member_role"
        define_table(tablename,
                     Field("name", length=64,
                           label = T("Name"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(64),
                                       ],
                           ),
                     Field("group_type", "integer",
                           default = 4,
                           label = T("Group Type"),
                           represent = S3Represent(options=pr_group_types),
                           requires = IS_IN_SET(pr_group_types, zero=None),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        CREATE_ROLE = T("Create Group Member Role")
        crud_strings[tablename] = Storage(
            label_create = CREATE_ROLE,
            title_display = T("Group Member Role Details"),
            title_list = T("Group Member Roles"),
            title_update = T("Edit Group Member Roles"),
            label_list_button = T("List Group Member Roles"),
            label_delete_button = T("Delete Group Member Role"),
            msg_record_created = T("Group Member Role added"),
            msg_record_modified = T("Group Member Role updated"),
            msg_record_deleted = T("Group Member Role deleted"),
            msg_list_empty = T("No Group Member Roles currently defined"),
            )

        # Table configuration
        configure(tablename,
                  deduplicate = S3Duplicate(primary = ("name",),
                                            secondary = ("group_type",),
                                            ignore_deleted = True,
                                            ),
                  )

        # Reusable Field
        represent = S3Represent(lookup=tablename, translate=True)
        role_id = S3ReusableField("role_id", "reference %s" % tablename,
                                  comment = S3PopupLink(c = "pr",
                                                        f = "group_member_role",
                                                        label = CREATE_ROLE,
                                                        title = CREATE_ROLE,
                                                        tooltip = T("The role of the member in the group"),
                                                        vars = {"child": "role_id"},
                                                        ),
                                  label = T("Group Member Role"),
                                  ondelete = "RESTRICT",
                                  represent = represent,
                                  requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "pr_group_member_role.id",
                                                          represent,
                                                          )),
                                  )

        # ---------------------------------------------------------------------
        # Group membership
        #
        tablename = "pr_group_membership"
        define_table(tablename,
                     group_id(empty = False,
                              label = T("Group"),
                              ondelete = "CASCADE",
                              ),
                     self.pr_person_id(empty = False,
                                       label = T("Person"),
                                       ondelete = "CASCADE",
                                       ),
                     # Enable in template if required
                     role_id(readable = False,
                             writable = False,
                             ondelete = "SET NULL",
                             ),
                     Field("group_head", "boolean",
                           default = False,
                           label = T("Group Head"),
                           represent = lambda group_head: \
                                       (group_head and [T("yes")] or [""])[0]
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        function = current.request.function
        if function == "person":
            crud_strings[tablename] = Storage(
                label_create = T("Add Membership"),
                title_display = T("Membership Details"),
                title_list = T("Memberships"),
                title_update = T("Edit Membership"),
                label_list_button = T("List Memberships"),
                label_delete_button = T("Delete Membership"),
                msg_record_created = T("Added to Group"),
                msg_record_modified = T("Membership updated"),
                msg_record_deleted = T("Removed from Group"),
                msg_list_empty = T("Not yet a Member of any Group"))

        elif function in ("group", "group_membership"):
            crud_strings[tablename] = Storage(
                label_create = T("Add Member"),
                title_display = T("Membership Details"),
                title_list = T("Group Members"),
                title_update = T("Edit Membership"),
                label_list_button = T("List Members"),
                label_delete_button = T("Remove Person from Group"),
                msg_record_created = T("Person added to Group"),
                msg_record_modified = T("Membership updated"),
                msg_record_deleted = T("Person removed from Group"),
                msg_list_empty = T("This Group has no Members yet"))

        # Which levels of Hierarchy are we using?
        levels = current.gis.get_relevant_hierarchy_levels()

        # Filter widgets
        filter_widgets = [
            S3TextFilter(["group_id$name",
                          "person_id$first_name",
                          "person_id$middle_name",
                          "person_id$last_name",
                          ],
                          label = T("Search"),
                          comment = T("To search for a member, enter any portion of the name of the person or group. You may use % as wildcard. Press 'Search' without input to list all members."),
                          _class="filter-search",
                          ),
            S3OptionsFilter("group_id",
                            ),
            S3LocationFilter("person_id$location_id",
                             levels = levels,
                             ),
            ]

        # Table configuration
        configure(tablename,
                  context = {"person": "person_id",
                             },
                  deduplicate = S3Duplicate(primary=("person_id",
                                                     "group_id",
                                                     ),
                                            ),
                  filter_widgets = filter_widgets,
                  list_fields = ["id",
                                 "group_id",
                                 "group_id$description",
                                 "person_id",
                                 "group_head",
                                 ],
                  onvalidation = self.group_membership_onvalidation,
                  onaccept = self.group_membership_onaccept,
                  ondelete = self.group_membership_onaccept,
                  realm_entity = self.group_membership_realm_entity,
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"pr_group_id": group_id,
                "pr_mailing_list_crud_strings": mailing_list_crud_strings,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def group_membership_onvalidation(form):
        """
            Verify that a person isn't added to a group more than once

            @param form: the FORM
        """

        form_vars = form.vars
        if "id" in form_vars:
            record_id = form_vars.id
        elif hasattr(form, "record_id"):
            record_id = form.record_id
        else:
            record_id = None

        person_id = form_vars.get("person_id")
        group_id = form_vars.get("group_id")

        db = current.db
        s3db = current.s3db
        table = s3db.pr_group_membership

        if not record_id:
            # New records - use defaults as required
            if not person_id:
                person_id = table.person_id.default
            if not group_id:
                group_id = table.group_id.default

        elif not person_id or not group_id:
            # Reload the record
            query = (table.id == record_id) & \
                    (table.deleted != True)
            record = db(query).select(table.person_id,
                                      table.group_id,
                                      limitby = (0, 1),
                                      ).first()
            if not record:
                # Nothing we can check
                return
            if not person_id:
                person_id = record.person_id
            if not group_id:
                group_id = record.group_id

        # Try to find a duplicate
        CASE_GROUP = 7
        group_type = None
        query = (table.person_id == person_id) & \
                (table.deleted != True) & \
                (table.group_id == group_id)

        multiple_case_groups = current.deployment_settings \
                                      .get_pr_multiple_case_groups()
        if not multiple_case_groups:
            # Check if group is a case group
            gtable = s3db.pr_group
            gquery = (gtable.id == group_id)
            group = db(gquery).select(gtable.group_type,
                                      limitby=(0, 1),
                                      ).first()
            if group:
                group_type = group.group_type
            if group_type == CASE_GROUP:
                # Alter the query so it checks for any case group
                query = (table.person_id == person_id) & \
                        (table.deleted != True) & \
                        (gtable.id == table.group_id) & \
                        (gtable.group_type == group_type)

        if record_id:
            # Exclude this record during update
            query = (table.id != record_id) & query

        duplicate = db(query).select(table.group_id,
                                     limitby=(0, 1),
                                     ).first()

        # Reject form if duplicate exists
        if duplicate:
            if group_type == CASE_GROUP and \
               str(duplicate.group_id) != str(group_id):
                error = current.T("This person already belongs to another case group")
            else:
                error = current.T("This person already belongs to this group")
            if "person_id" in form_vars:
                # Group perspective
                form.errors["person_id"] = error
            elif "group_id" in form_vars:
                # Person perspective
                form.errors["group_id"] = error

    # -------------------------------------------------------------------------
    @staticmethod
    def group_membership_onaccept(form):
        """
            Remove any duplicate memberships and update affiliations

            @param form: the FORM
        """

        if hasattr(form, "vars"):
            record_id = form.vars.get("id")
        elif isinstance(form, Row) and "id" in form:
            record_id = form.id
        else:
            return

        if not record_id:
            return

        db = current.db
        settings = current.deployment_settings

        table = db.pr_group_membership
        gtable = db.pr_group

        # Use left join for group data
        left = gtable.on(gtable.id == table.group_id)

        row = db(table.id == record_id).select(table.id,
                                               table.person_id,
                                               table.group_id,
                                               table.group_head,
                                               table.deleted,
                                               table.deleted_fk,
                                               gtable.id,
                                               gtable.group_type,
                                               left = left,
                                               limitby = (0, 1),
                                               ).first()
        record = row.pr_group_membership

        if not record:
            return

        # Get person_id and group_id
        group_id = record.group_id
        person_id = record.person_id
        if record.deleted and record.deleted_fk:
            try:
                deleted_fk = json.loads(record.deleted_fk)
            except ValueError:
                pass
            else:
                person_id = deleted_fk.get("person_id", person_id)
                group_id = deleted_fk.get("group_id", group_id)

        # Make sure a person always only belongs once
        # to the same group (delete all other memberships)
        if person_id and group_id and not record.deleted:
            query = (table.person_id == person_id) & \
                    (table.group_id == group_id) & \
                    (table.id != record.id) & \
                    (table.deleted != True)
            deleted_fk = {"person_id": person_id,
                          "group_id": group_id,
                          }
            db(query).update(deleted = True,
                             person_id = None,
                             group_id = None,
                             deleted_fk = json.dumps(deleted_fk),
                             )

        # Update PE hierarchy affiliations
        pr_update_affiliations(table, record)

        # BR extensions
        s3db = current.s3db
        if settings.has_module("br"):
            s3db.br_group_membership_onaccept(record, row.pr_group, group_id, person_id)

        # DVR extensions
        s3db = current.s3db
        ctable = s3db.table("dvr_case")
        if not ctable:
            return
        response = current.response
        s3 = response.s3
        if not s3.purge_case_groups:
            # Get the group
            group = row.pr_group
            if group.id is None and group_id:
                query = (gtable.id == group_id) & \
                        (gtable.deleted != True)
                row = db(query).select(gtable.id,
                                       gtable.group_type,
                                       limitby = (0, 1),
                                       ).first()
                if row:
                    group = row

            if group.group_type == 7:
                # DVR Case Group

                # Case groups should only have one group head
                if not record.deleted and record.group_head:
                    query = (table.group_id == group_id) & \
                            (table.id != record.id) & \
                            (table.group_head == True)
                    db(query).update(group_head=False)

                update_household_size = settings.get_dvr_household_size() == "auto"
                recount = s3db.dvr_case_household_size

                if update_household_size and record.deleted and person_id:
                    # Update the household size for removed group member
                    query = (table.person_id == person_id) & \
                            (table.group_id != group_id) & \
                            (table.deleted != True) & \
                            (gtable.id == table.group_id) & \
                            (gtable.group_type == 7)
                    row = db(query).select(table.group_id,
                                           limitby = (0, 1),
                                           ).first()
                    if row:
                        # Person still belongs to other case groups,
                        # count properly:
                        recount(row.group_id)
                    else:
                        # No further case groups, so household size is 1
                        ctable = s3db.dvr_case
                        cquery = (ctable.person_id == person_id)
                        db(cquery).update(household_size = 1)

                if not s3.bulk:
                    # Get number of (remaining) members in this group
                    query = (table.group_id == group_id) & \
                            (table.deleted != True)
                    rows = db(query).select(table.id, limitby = (0, 2))

                    if len(rows) < 2:
                        # Update the household size for current group members
                        if update_household_size:
                            recount(group_id)
                            update_household_size = False
                        # Remove the case group if it only has one member
                        s3.purge_case_groups = True
                        resource = s3db.resource("pr_group", id=group_id)
                        resource.delete()
                        s3.purge_case_groups = False

                    elif not record.deleted:
                        # Generate a case for new case group member
                        # ...unless we already have one
                        query = (ctable.person_id == person_id) & \
                                (ctable.deleted != True)
                        row = db(query).select(ctable.id, limitby=(0, 1)).first()
                        if not row:
                            # Customise case resource
                            r = S3Request("dvr", "case", current.request)
                            r.customise_resource("dvr_case")

                            # Get the default case status from database
                            s3db.dvr_case_default_status()

                            # Create a case
                            cresource = s3db.resource("dvr_case")
                            try:
                                # Using resource.insert for proper authorization
                                # and post-processing (=audit, ownership, realm,
                                # onaccept)
                                cresource.insert(person_id=person_id)
                            except S3PermissionError:
                                # Unlikely (but possible) that this situation
                                # is deliberate => issue a warning
                                response.warning = current.T("No permission to create a case record for new group member")

                # Update the household size for current group members
                if update_household_size:
                    recount(group_id)

    # -------------------------------------------------------------------------
    @staticmethod
    def group_membership_realm_entity(table, row):
        """
            Set the realm entity of Group Membership records to the same as
            that of the person
        """

        db = current.db
        s3db = current.s3db

        # Find the Group
        gtable = s3db.pr_group
        group = db(gtable.id == row.group_id).select(gtable.realm_entity,
                                                     limitby = (0, 1),
                                                     ).first()
        try:
            return group.realm_entity
        except AttributeError:
            # => Set to default of None
            return None

# =============================================================================
class PRGroupCompetencyModel(S3Model):
    """
        Group Competency Model
        - Skills available in a Group
    """

    names = ("pr_group_competency",)

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Groups <> Skills Link Table
        #
        tablename = "pr_group_competency"
        self.define_table(tablename,
                          self.pr_group_id(),
                          self.hrm_skill_id(),
                          #self.hrm_competency_id(),
                          s3_comments(),
                          *s3_meta_fields()
                          )

        # CRUD Strings
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Skill"),
            title_display = T("Skill"),
            title_list = T("Skills"),
            title_update = T("Edit Skill"),
            title_upload = T("Import Skills"),
            label_list_button = T("List Skills"),
            msg_record_created = T("Skill added to Group"),
            msg_record_modified = T("Skill updated"),
            msg_record_deleted = T("Skill removed from Group"),
            msg_list_empty = T("No Skills found for this Group"))

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("group_id",
                                                            "skill_id",
                                                            ),
                                                 ),
                       )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class PRGroupLocationModel(S3Model):
    """
        Group Location Model
        - Locations served by a Group
    """

    names = ("pr_group_location",)

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Groups <> Locations Link Table
        #
        tablename = "pr_group_location"
        self.define_table(tablename,
                          self.pr_group_id(),
                          self.gis_location_id(
                            #represent = self.gis_LocationRepresent(sep=", "),
                            requires = IS_LOCATION(),
                            widget = S3LocationAutocompleteWidget()
                          ),
                          s3_comments(),
                          *s3_meta_fields()
                          )

        # CRUD Strings
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Location"),
            title_display = T("Location"),
            title_list = T("Locations"),
            title_update = T("Edit Location"),
            title_upload = T("Import Location data"),
            label_list_button = T("List Locations"),
            msg_record_created = T("Location added to Group"),
            msg_record_modified = T("Location updated"),
            msg_record_deleted = T("Location removed from Group"),
            msg_list_empty = T("No Locations found for this Group"))

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("group_id",
                                                            "location_id",
                                                            ),
                                                 ),
                       )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class PRGroupTagModel(S3Model):
    """
        Group Tags
    """

    names = ("pr_group_tag",
             )

    def model(self):

        T = current.T

        tablename = "pr_group_tag"
        self.define_table(tablename,
                          self.pr_group_id(ondelete = "CASCADE"),
                          Field("tag",
                                label = T("Key"),
                                ),
                          Field("value",
                                label = T("Value"),
                                ),
                          #s3_comments(),
                          *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("group_id", "tag"),
                                                 ignore_case = True,
                                                 ),
                       )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class PRForumModel(S3Model):
    """
        Forums - similar to Groups, they are collections of People, however
                 these are restricted to those with User Accounts
        - used to share Information within Realms
        - currently used just by WACOP
    """

    names = ("pr_forum",
             "pr_forum_id",
             "pr_forum_membership",
             )

    def model(self):

        T = current.T
        db = current.db

        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        set_method = self.set_method

        # ---------------------------------------------------------------------
        # Hard Coded Forum types. Add/Comment entries, but don't remove!
        #
        pr_forum_types = {1 : T("Public"),  # Any user can join and post
                          2 : T("Private"), # Anyone in the forum can post & see membership.
                                            # Anyone else can see that the forum exists but not its members or posts.
                          3 : T("Secret"),  # As 'private' but forum's presence is not visible to non-members
                          }

        tablename = "pr_forum"
        define_table(tablename,
                     # Instances
                     self.super_link("pe_id", "pr_pentity"),
                     Field("name",
                           label = T("Name"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("forum_type", "integer",
                           default = 1,
                           label = T("Type"),
                           represent = S3Represent(options = pr_forum_types),
                           requires = IS_IN_SET(pr_forum_types, zero=None),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Forum"),
            title_display = T("Forum Details"),
            title_list = T("Forums"),
            title_update = T("Edit Forum"),
            label_list_button = T("List Forums"),
            label_delete_button = T("Delete Forum"),
            msg_record_created = T("Forum added"),
            msg_record_modified = T("Forum updated"),
            msg_record_deleted = T("Forum deleted"),
            msg_list_empty = T("No Forums currently registered"))

        # Resource configuration
        configure(tablename,
                  deduplicate = S3Duplicate(ignore_deleted=True),
                  super_entity = ("pr_pentity"),
                  )

        # Reusable field
        represent = S3Represent(lookup=tablename)
        forum_id = S3ReusableField("forum_id", "reference %s" % tablename,
                                   sortby = "name",
                                   comment = S3PopupLink(c = "pr",
                                                         f = "forum",
                                                         label = T("Create Forum"),
                                                         title = T("Create Forum"),
                                                         tooltip = T("Create a new Forum"),
                                                         ),
                                   label = T("Forum"),
                                   ondelete = "RESTRICT",
                                   represent = represent,
                                   requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "pr_forum.id",
                                                          represent,
                                                          )),
                                   #widget = S3AutocompleteWidget("pr", "forum")
                                   )

        # Components
        self.add_components(tablename,
                            pr_forum_membership = "forum_id",
                            cms_post = {"link": "cms_post_forum",
                                        "joinby": "forum_id",
                                        "key": "post_id",
                                        "actuate": "replace",
                                        },
                            project_task = {"link": "project_task_forum",
                                            "joinby": "forum_id",
                                            "key": "task_id",
                                            "actuate": "replace",
                                            },
                            )

        # Custom Methods
        set_method("pr", "forum",
                   method = "assign",
                   action = pr_AssignMethod(component = "forum_membership"))

        set_method("pr", "forum",
                   method = "join",
                   action = self.pr_forum_join)

        set_method("pr", "forum",
                   method = "leave",
                   action = self.pr_forum_leave)

        set_method("pr", "forum",
                   method = "request",
                   action = self.pr_forum_request)

        # ---------------------------------------------------------------------
        # Forum membership
        #
        tablename = "pr_forum_membership"
        define_table(tablename,
                     forum_id(empty = False,
                              ondelete = "CASCADE",
                              ),
                     # @ToDo: Filter to just those with User Accounts
                     self.pr_person_id(empty = False,
                                       label = T("Person"),
                                       ondelete = "CASCADE",
                                       ),
                     Field("admin", "boolean",
                           default = False,
                           label = T("Admin"),
                           represent = s3_yes_no_represent,
                           # Enable in Template if-required
                           readable = False,
                           writable = False,
                           ),
                     # If we need more types of role:
                     #role_id(readable = False,
                     #        writable = False,
                     #        ondelete = "SET NULL",
                     #        ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        function = current.request.function
        if function == "person":
            crud_strings[tablename] = Storage(
                label_create = T("Add Membership"),
                title_display = T("Membership Details"),
                title_list = T("Memberships"),
                title_update = T("Edit Membership"),
                label_list_button = T("List Memberships"),
                label_delete_button = T("Delete Membership"),
                msg_record_created = T("Added to Forum"),
                msg_record_modified = T("Membership updated"),
                msg_record_deleted = T("Removed from Forum"),
                msg_list_empty = T("Not yet a Member of any Forum"))

        elif function in ("forum", "forum_membership"):
            crud_strings[tablename] = Storage(
                label_create = T("Add Member"),
                title_display = T("Membership Details"),
                title_list = T("Forum Members"),
                title_update = T("Edit Membership"),
                label_list_button = T("List Members"),
                label_delete_button = T("Remove Person from Forum"),
                msg_record_created = T("Person added to Forum"),
                msg_record_modified = T("Membership updated"),
                msg_record_deleted = T("Person removed from Forum"),
                msg_list_empty = T("This Forum has no Members yet"))

        # Table configuration
        configure(tablename,
                  deduplicate = S3Duplicate(primary=("person_id",
                                                     "forum_id",
                                                     ),
                                            ),
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"pr_forum_id": forum_id,
                }

    # -----------------------------------------------------------------------------
    @staticmethod
    def pr_forum_join(r, **attr):
        """
            Join a (Public) Forum

            S3Method for interactive requests
        """

        forum_id = r.id
        if not forum_id:
            r.error(405, current.ERROR.BAD_METHOD)
        user = current.auth.user
        if not user:
            r.error(405, current.ERROR.BAD_METHOD)

        db = current.db
        s3db = current.s3db
        ptable = s3db.pr_person
        person_id = db(ptable.pe_id == user.pe_id).select(ptable.id,
                                                          limitby = (0, 1)
                                                          ).first().id

        ltable = s3db.pr_forum_membership
        query = (ltable.forum_id == forum_id) & \
                (ltable.person_id == person_id)
        exists = db(query).select(ltable.id,
                                  ltable.deleted,
                                  ltable.deleted_fk,
                                  limitby=(0, 1)
                                  ).first()
        if exists:
            link_id = exists.id
            if exists.deleted:
                if exists.deleted_fk:
                    data = json.loads(exists.deleted_fk)
                    data["deleted"] = False
                else:
                    data = dict(deleted=False)
                db(ltable.id == link_id).update(**data)
        else:
            link_id = ltable.insert(forum_id = forum_id,
                                    person_id = person_id,
                                    )

        #output = current.xml.json_message(True, 200, current.T("Forum Joined"))
        #current.response.headers["Content-Type"] = "application/json"
        #return output
        current.session.confirmation = current.T("Forum Joined")
        redirect(URL(args=[r.id, "forum_membership"]))

    # -----------------------------------------------------------------------------
    @staticmethod
    def pr_forum_leave(r, **attr):
        """
            Leave a Forum

            S3Method for interactive requests
        """

        forum_id = r.id
        if not forum_id:
            r.error(405, current.ERROR.BAD_METHOD)
        user = current.auth.user
        if not user:
            r.error(405, current.ERROR.BAD_METHOD)

        s3db = current.s3db
        ptable = s3db.pr_person
        ltable = s3db.pr_forum_membership
        query = (ltable.forum_id == forum_id) & \
                (ltable.person_id == ptable.id) & \
                (ptable.pe_id == user.pe_id)
        exists = current.db(query).select(ltable.id,
                                          ltable.deleted,
                                          limitby=(0, 1)
                                          ).first()

        if exists and not exists.deleted:
            resource = s3db.resource("pr_forum_membership", id=exists.id)
            success = resource.delete()
            if not success:
                current.session.error = resource.error
                redirect(URL(args=None))

        message = current.T("Forum Left")
        if r.representation == "json":
            output = current.xml.json_message(True, 200, message)
            current.response.headers["Content-Type"] = "application/json"
            return output
        else:
            current.session.confirmation = message
            redirect(URL(args=None))

    # -----------------------------------------------------------------------------
    @staticmethod
    def pr_forum_request(r, **attr):
        """
            Request to Join a (Private) Forum

            S3Method for interactive requests
        """

        forum_id = r.id
        if not forum_id:
            r.error(405, current.ERROR.BAD_METHOD)
        user = current.auth.user
        if not user:
            r.error(405, current.ERROR.BAD_METHOD)

        db = current.db
        s3db = current.s3db
        ptable = s3db.pr_person
        person_id = db(ptable.pe_id == user.pe_id).select(ptable.id,
                                                          limitby = (0, 1)
                                                          ).first().id

        mtable = s3db.pr_forum_membership
        query = (mtable.forum_id == forum_id) & \
                (mtable.person_id == person_id)
        exists = db(query).select(mtable.id,
                                  limitby=(0, 1)
                                  ).first()
        if exists:
            #output = current.xml.json_message(True, 200, current.T("Already a Member"))
            message = current.T("Already a Member")
        else:
            # Send Notification to the Forum Admin(s)
            from s3 import s3_str

            T = current.T

            forum_name = r.record.name
            ltable = s3db.pr_person_user
            utable = db.auth_user
            query = (mtable.forum_id == forum_id) & \
                    (mtable.admin == True) & \
                    (mtable.deleted == False) & \
                    (mtable.person_id == ptable.id) & \
                    (ptable.pe_id == ltable.pe_id) & \
                    (ltable.user_id == utable.id)
            admins = db(query).select(ptable.pe_id,
                                      utable.language,
                                      )
            subject = "User has requested to join Forum %(forum_name)s"
            url = URL(c="pr", f="forum",
                      args=[r.id, "forum_membership", "create"],
                      vars = {"person_id": person_id,
                              }
                      )
            body = "To approve this request, click here: %(url)s"
            translations = {}
            languages = list({a["auth_user.language"] for a in admins})
            for l in languages:
                translations[l] = {"s": s3_str(T(subject, language = l)) % dict(forum_name = forum_name),
                                   "b": s3_str(T(body, language = l)) % dict(url = url),
                                   }
            send_email = current.msg.send_by_pe_id
            for a in admins:
                lang = a.get("auth_user.language")
                translation = translations[lang]
                pe_id = a.get("pr_person.pe_id")
                send_email(pe_id,
                           subject = translation["s"],
                           message = translation["b"],
                           )
            #output = current.xml.json_message(True, 200, T("Invite Requested"))
            message = T("Invite Requested")

        #current.response.headers["Content-Type"] = "application/json"
        #return output
        current.session.confirmation = message
        redirect(URL(args=None))

# =============================================================================
class PRAddressModel(S3Model):
    """ Addresses for Person Entities: Persons and Organisations """

    names = ("pr_address",
             "pr_address_type_opts"
             )

    def model(self):

        T = current.T
        messages = current.messages
        s3 = current.response.s3
        settings = current.deployment_settings

        # ---------------------------------------------------------------------
        # Address
        #
        pr_address_type_opts = {
            1: T("Current Home Address"),
            2: T("Permanent Home Address"),
            3: T("Office Address"),
            #4: T("Holiday Address"),
            9: T("Other Address")
        }

        tablename = "pr_address"
        self.define_table(tablename,
                          # Component not Instance
                          self.super_link("pe_id", "pr_pentity",
                                          orderby = "instance_type",
                                          represent = self.pr_pentity_represent,
                                          ),
                          Field("type", "integer",
                                default = 1,
                                label = T("Address Type"),
                                represent = lambda opt: \
                                            pr_address_type_opts.get(opt,
                                                    messages.UNKNOWN_OPT),
                                requires = IS_IN_SET(pr_address_type_opts,
                                                     zero=None),
                                widget = RadioWidget.widget,
                                ),
                          self.gis_location_id(),
                          # Whether this field has been the source of
                          # the base location of the entity before, and
                          # hence address updates should propagate to
                          # the base location:
                          Field("is_base_location", "boolean",
                                default = False,
                                readable = False,
                                writable = False,
                                ),
                          s3_comments(),
                          *s3_meta_fields())

        # CRUD Strings
        s3.crud_strings[tablename] = Storage(
            label_create = T("Add Address"),
            title_display = T("Address Details"),
            title_list = T("Addresses"),
            title_update = T("Edit Address"),
            label_list_button = T("List Addresses"),
            msg_record_created = T("Address added"),
            msg_record_modified = T("Address updated"),
            msg_record_deleted = T("Address deleted"),
            msg_list_empty = T("There is no address for this person yet. Add new address.")
            )

        list_fields = ["type",
                       (T("Address"), "location_id$addr_street"),
                       ]

        if settings.get_gis_postcode_selector():
            list_fields.append((settings.get_ui_label_postcode(),
                                "location_id$addr_postcode"))

        # Which levels of Hierarchy are we using?
        levels = current.gis.get_relevant_hierarchy_levels()

        # Display in reverse order, like Addresses
        levels.reverse()

        for level in levels:
            list_fields.append("location_id$%s" % level)

        # Resource configuration
        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("pe_id",
                                                            "type",
                                                            "location_id",
                                                            ),
                                                 ignore_deleted = True,
                                                 ),
                       list_fields = list_fields,
                       list_layout = pr_address_list_layout,
                       onaccept = self.pr_address_onaccept,
                       )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"pr_address_type_opts": pr_address_type_opts,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def pr_address_onaccept(form):
        """
            Updates the Base Location to be the same as the Address

            If the base location hasn't yet been set or if this is specifically
            requested
        """

        form_vars = form.vars

        try:
            record_id = form_vars["id"]
        except (TypeError, KeyError):
            # Nothing we can do
            return

        db = current.db
        s3db = current.s3db
        atable = db.pr_address

        row = db(atable.id == record_id).select(atable.id,
                                                atable.location_id,
                                                atable.pe_id,
                                                atable.is_base_location,
                                                limitby = (0, 1),
                                                ).first()
        try:
            location_id = row.location_id
        except AttributeError:
            # Nothing we can do
            return
        pe_id = row.pe_id

        ptable = s3db.pr_person
        person = None
        new_base_location = False
        req_vars = current.request.vars
        if req_vars and "base_location" in req_vars and \
           req_vars.base_location == "on":
            # Specifically requested
            new_base_location = True
            person = db(ptable.pe_id == pe_id).select(ptable.id,
                                                      limitby = (0, 1),
                                                      ).first()
        else:
            # Check if a base location already exists
            person = db(ptable.pe_id == pe_id).select(ptable.id,
                                                      ptable.location_id,
                                                      limitby = (0, 1),
                                                      ).first()

            if person and (row.is_base_location or not person.location_id):
                # This address was the source of the base location
                # (=> update it), or no base location has been set
                # yet (=> set it now)
                new_base_location = True

        if new_base_location:
            # Set new base location
            S3Tracker()(db.pr_pentity, pe_id).set_base_location(location_id)
            row.update_record(is_base_location=True)

            # Reset is_base_location flag in all other addresses
            query = (atable.pe_id == pe_id) & (atable.id != row.id)
            db(query).update(is_base_location=False)

        if not person:
            # Nothing more we can do
            return

        address_type = str(form_vars.get("type"))
        if address_type == "2": # Permanent Home Address
            # Use this for Locating the person *if* they have no Current Address
            query = (atable.pe_id == pe_id) & \
                    (atable.type == 1) & \
                    (atable.deleted != True)
            exists = db(query).select(atable.id,
                                      limitby=(0, 1)
                                      ).first()
            if exists:
                # Do nothing: prefer existing current address
                return
        elif address_type != "1": # Current Home Address
            # Do nothing
            return

        settings = current.deployment_settings
        if settings.has_module("hrm"):
            # Also check for relevant HRM record(s)
            staff_settings = settings.get_hrm_location_staff()
            staff_person = "person_id" in staff_settings
            vol_settings = settings.get_hrm_location_vol()
            vol_person = "person_id" in vol_settings
            if staff_person or vol_person:
                htable = s3db.hrm_human_resource
                query = (htable.person_id == person.id) & \
                        (htable.deleted != True)
                fields = [htable.id]
                if staff_person and vol_person:
                    # Unfiltered in query, need to separate afterwards
                    fields.append(htable.type)
                    vol_site = "site_id" == vol_settings[0]
                    staff_site = "site_id" == staff_settings[0]
                    if staff_site or vol_site:
                        fields.append(htable.site_id)
                elif vol_person:
                    vol_site = "site_id" == vol_settings[0]
                    if vol_site:
                        fields.append(htable.site_id)
                    query &= (htable.type == 2)
                elif staff_person:
                    staff_site = "site_id" == staff_settings[0]
                    if staff_site:
                        fields.append(htable.site_id)
                    query &= (htable.type == 1)
                hrs = db(query).select(*fields)
                for hr in hrs:
                    # @ToDo: Only update if not site_id 1st in list & a site_id exists!
                    if staff_person and vol_person:
                        vol = hr.type == 2
                        if vol and vol_site and hr.site_id:
                            # Volunteer who prioritises getting their location from their site
                            pass
                        elif not vol and staff_site and hr.site_id:
                            # Staff who prioritises getting their location from their site
                            pass
                        else:
                            # Update this HR's location from the Home Address
                            db(htable.id == hr.id).update(location_id=location_id)
                    elif vol_person:
                        if vol_site and hr.site_id:
                            # Volunteer who prioritises getting their location from their site
                            pass
                        else:
                            # Update this HR's location from the Home Address
                            db(htable.id == hr.id).update(location_id=location_id)
                    else:
                        # Staff-only
                        if staff_site and hr.site_id:
                            # Staff who prioritises getting their location from their site
                            pass
                        else:
                            # Update this HR's location from the Home Address
                            db(htable.id == hr.id).update(location_id=location_id)

        if settings.has_module("member"):
            # Also check for any Member record(s)
            mtable = s3db.member_membership
            query = (mtable.person_id == person.id) & \
                    (mtable.deleted != True)
            members = db(query).select(mtable.id)
            for member in members:
                db(mtable.id == member.id).update(location_id=location_id)

# =============================================================================
class PRContactModel(S3Model):
    """
        Person Entity Contacts
        - for Persons, Groups, Organisations and Organisation Groups
    """

    names = ("pr_contact",
             "pr_contact_emergency",
             "pr_contact_represent",
             )

    def model(self):

        T = current.T

        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        messages = current.messages
        super_link = self.super_link

        # ---------------------------------------------------------------------
        # Contact
        #
        # @ToDo: Provide widgets which can be dropped into the main person form to have
        #        the relevant ones for that deployment/context collected on that same
        #        form
        #
        contact_methods = current.msg.CONTACT_OPTS

        access_opts = {1 : T("Private"),
                       2 : T("Public"),
                       }

        tablename = "pr_contact"
        define_table(tablename,
                     # Component not instance
                     super_link("pe_id", "pr_pentity",
                                empty = False,
                                orderby = "instance_type",
                                represent = self.pr_pentity_represent,
                                ),
                     Field("contact_method", length=32,
                           default = "SMS",
                           label = T("Contact Method"),
                           represent = lambda opt: \
                                       contact_methods.get(opt, messages.UNKNOWN_OPT),
                           requires = IS_IN_SET(contact_methods,
                                                zero=None),
                           ),
                     Field("value", notnull=True,
                           label= T("Value"),
                           represent = lambda v: v or messages["NONE"],
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("contact_description",
                           label = T("Contact Description"),
                           ),
                     Field("priority", "integer",
                           default = 1,
                           label = T("Priority"),
                           requires = IS_IN_SET(list(range(1, 10))),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Priority"),
                                                           T("What order to be contacted in."))),
                           ),
                     Field("access", "integer",
                           default = 1, # Contacts default to Private
                           label = T("Access"),
                           represent = lambda opt: \
                                       access_opts.get(opt, messages.UNKNOWN_OPT),
                           requires = IS_IN_SET(access_opts,
                                                zero=None),
                           # Enable in templates as-required
                           readable = False,
                           writable = False,
                           ),
                     # Used to determine whether an RSS/Facebook/Twitter feed should be imported into the main newsfeed
                     # (usually used for Organisational ones)
                     Field("poll", "boolean",
                           default = False,
                           # Enable as-required in templates
                           readable = False,
                           writable = False,
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Contact Information"),
            title_display = T("Contact Details"),
            title_list = T("Contact Information"),
            title_update = T("Edit Contact Information"),
            label_list_button = T("List Contact Information"),
            label_delete_button = T("Delete Contact Information"),
            msg_record_created = T("Contact Information Added"),
            msg_record_modified = T("Contact Information Updated"),
            msg_record_deleted = T("Contact Information Deleted"),
            msg_list_empty = T("No contact information available"))

        configure(tablename,
                  deduplicate = S3Duplicate(primary=("pe_id",
                                                     "contact_method",
                                                     "value",
                                                     ),
                                            ignore_deleted = True,
                                            ),
                  list_fields = ["id",
                                 "contact_method",
                                 "value",
                                 "priority",
                                 # Used by list_layout & anyway it's useful
                                 "comments",
                                 ],
                  list_layout = pr_contact_list_layout,
                  onvalidation = self.pr_contact_onvalidation,
                  )

        contact_represent = pr_ContactRepresent()

        # ---------------------------------------------------------------------
        # Emergency Contact Information
        # - currently only ever 1 of these expected
        #
        tablename = "pr_contact_emergency"
        define_table(tablename,
                     super_link("pe_id", "pr_pentity"),
                     Field("name",
                           label = T("Name"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("relationship",
                           label = T("Relationship"),
                           ),
                     Field("phone",
                           label = T("Phone"),
                           represent = s3_phone_represent,
                           requires = IS_EMPTY_OR(IS_PHONE_NUMBER_MULTI()),
                           widget = S3PhoneWidget(),
                           ),
                     Field("address",
                           label = T("Address"),
                           # Enable as-required in templates
                           readable = False,
                           writable = False,
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Emergency Contact"),
            title_display = T("Emergency Contact Details"),
            title_list = T("Emergency Contacts"),
            title_update = T("Edit Emergency Contact"),
            label_list_button = T("List Emergency Contacts"),
            label_delete_button = T("Delete Emergency Contact"),
            msg_record_created = T("Emergency Contact Added"),
            msg_record_modified = T("Emergency Contact Updated"),
            msg_record_deleted = T("Emergency Contact Deleted"),
            msg_list_empty = T("No emergency contacts registered"))

        configure(tablename,
                  deduplicate = S3Duplicate(primary = ("pe_id",),
                                            ignore_deleted = True,
                                            ),
                  list_layout = pr_EmergencyContactListLayout(),
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"pr_contact_represent": contact_represent,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def pr_contact_onvalidation(form):
        """ Contact form validation """

        form_vars = form.vars

        # Get the contact method
        contact_method = form_vars.contact_method
        if not contact_method and "id" in form_vars:
            ctable = current.s3db.pr_contact
            record = current.db(ctable._id == form_vars.id).select(
                                ctable.contact_method,
                                limitby=(0, 1)).first()
            if record:
                contact_method = record.contact_method

        # Determine the validation rule for the value
        if contact_method == "EMAIL":
            requires = IS_EMAIL(error_message = current.T("Enter a valid email"))
        elif contact_method == "SMS":
            requires = IS_PHONE_NUMBER(international = True)
        elif contact_method in ("HOME_PHONE", "WORK_PHONE"):
            requires = IS_MATCH(multi_phone_number_pattern,
                                error_message = current.T("Enter a valid phone number"))
        else:
            requires = None

        # Validate the value
        if requires:
            value, error = requires(form_vars.value)
            if error:
                form.errors.value = error
            else:
                form_vars.value = value

        return

# =============================================================================
class PRImageModel(S3Model):
    """ Images for Persons """

    names = ("pr_image",)

    def model(self):

        T = current.T
        db = current.db
        request = current.request

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


        def get_file(table):
            """ Decorator to return a table-specific file-callback """

            def cb():
                """ Callback to return the file field for our record """

                if len(request.args) < 3:
                    return None
                query = (table.id == request.args[2])
                record = db(query).select(table.image, limitby = (0, 1)).first()
                return record.image if record else None

            return cb

        tablename = "pr_image"
        self.define_table(tablename,
                          # Component not Instance
                          self.super_link("pe_id", "pr_pentity"),
                          Field("profile", "boolean",
                                default = False,
                                label = T("Profile Picture?"),
                                represent = s3_yes_no_represent,
                                ),
                          Field("image", "upload",
                                autodelete = True,
                                label = T("Image"),
                                length = current.MAX_FILENAME_LENGTH,
                                represent = self.pr_image_represent,
                                widget = S3ImageCropWidget((600, 600)),
                                comment =  DIV(_class = "tooltip",
                                               _title = "%s|%s" % (T("Image"),
                                                                   T("Upload an image file here. If you don't upload an image file, then you must specify its location in the URL field."),
                                                                   ),
                                               ),
                                ),
                          Field("url",
                                label = T("URL"),
                                represent = pr_url_represent,
                                comment = DIV(_class = "tooltip",
                                              _title = "%s|%s" % (T("URL"),
                                                                  T("The URL of the image file. If you don't upload an image file, then you must specify its location here."),
                                                                  ),
                                              ),
                                ),
                          Field("type", "integer",
                                default = 1,
                                label = T("Image Type"),
                                represent = lambda opt: \
                                                pr_image_type_opts.get(opt,
                                                   current.messages.UNKNOWN_OPT),
                                requires = IS_IN_SET(pr_image_type_opts,
                                                     zero = None,
                                                     ),
                                ),
                          s3_comments("description",
                                      label = T("Description"),
                                      comment = DIV(_class = "tooltip",
                                                    _title = "%s|%s" % (T("Description"),
                                                                        T("Give a brief description of the image, e.g. what can be seen where on the picture (optional)."),
                                                                        ),
                                                    ),
                                      ),
                          *s3_meta_fields(),

                          # Image-validator needs the Table instance
                          # => set it on-define to allow the table to be lazy
                          on_define = lambda table: [
                                        table.image.set_attributes(
                                            requires = IS_PROCESSED_IMAGE(
                                                        "image",
                                                        get_file(table),
                                                        upload_path = os.path.join(request.folder,
                                                                                   "uploads",
                                                                                   ),
                                                        ),
                                        ),
                                       ]
                          )

        # CRUD Strings
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Image"),
            title_display = T("Image Details"),
            title_list = T("Images"),
            title_update = T("Edit Image Details"),
            label_list_button = T("List Images"),
            label_delete_button = T("Delete Image"),
            msg_record_created = T("Image added"),
            msg_record_modified = T("Image updated"),
            msg_record_deleted = T("Image deleted"),
            msg_list_empty = T("No Images currently registered"))

        # Resource configuration
        self.configure(tablename,
                       list_fields = ["id",
                                      "profile",
                                      "type",
                                      "image",
                                      "url",
                                      "description"
                                      ],
                       #mark_required = ("url", "image"),
                       onaccept = self.pr_image_onaccept,
                       ondelete = self.pr_image_ondelete,
                       onvalidation = self.pr_image_onvalidation,
                       )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def pr_image_represent(image, size=None):
        """ Representation """

        if not image:
            return current.messages["NONE"]
        url_full = URL(c="default", f="download", args=image)
        if size is None:
            size = (None, 60)
        image = pr_image_library_represent(image, size=size)
        url_small = URL(c="default", f="download", args=image)

        return DIV(A(IMG(_src=url_small,
                         _height=size[1],
                         ),
                     _href=url_full,
                     _class="th",
                     ))

    # -------------------------------------------------------------------------
    @staticmethod
    def pr_image_onaccept(form):
        """
            If this is the profile image then remove this flag from all
            others for this person.
        """

        form_vars = form.vars
        record_id = form_vars.id
        profile = form_vars.profile
        newfilename = form_vars.image_newfilename
        if profile == "False":
            profile = False

        if newfilename:
            _image = form.request_vars.image
            pr_image_modify(_image.file,
                            newfilename,
                            _image.filename,
                            size = (50, 50),
                            )
            pr_image_modify(_image.file,
                            newfilename,
                            _image.filename,
                            size = (None, 60),
                            )
            pr_image_modify(_image.file,
                            newfilename,
                            _image.filename,
                            size = (160, None),
                            )

        if profile:
            # Find the pe_id
            db = current.db
            table = db.pr_image
            pe = db(table.id == record_id).select(table.pe_id,
                                                  limitby = (0, 1),
                                                  ).first()
            if pe:
                pe_id = pe.pe_id
                # Set all others for this person as not the Profile picture
                query  = (table.pe_id == pe_id) & \
                         (table.id != record_id)
                db(query).update(profile = False)

    # -------------------------------------------------------------------------
    @staticmethod
    def pr_image_onvalidation(form):
        """ Image form validation """

        form_vars = form.vars
        image = form_vars.image
        url = form_vars.url

        if not hasattr(image, "file"):
            record_id = current.request.post_vars.id
            if record_id:
                db = current.db
                table = db.pr_image
                record = db(table.id == record_id).select(table.image,
                                                          limitby = (0, 1),
                                                          ).first()
                if record:
                    image = record.image

        if not hasattr(image, "file") and not image and not url:
            form.errors.image = \
            form.errors.url = current.T("Either file upload or image URL required.")

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
class PRPresenceModel(S3Model):
    """
        Presence Log for Persons

        @todo: deprecate
        currently still used by CR?
    """

    names = ("pr_presence",
             "pr_trackable_types",
             "pr_default_trackable",
             "pr_presence_opts",
             "pr_presence_conditions",
             "pr_default_presence"
             )

    def model(self):

        T = current.T

        location_id = self.gis_location_id
        super_link = self.super_link
        messages = current.messages
        ADD_LOCATION = messages.ADD_LOCATION
        UNKNOWN_OPT = messages.UNKNOWN_OPT

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
        self.define_table(tablename,
                          super_link("pe_id", "pr_pentity"),
                          super_link("sit_id", "sit_situation"),
                          self.pr_person_id("observer",
                          label=T("Observer"),
                          default = current.auth.s3_logged_in_person(),
                          comment=pr_person_comment(title=T("Observer"),
                                                    comment=T("Person who has actually seen the person/group."),
                                                    child="observer")),
                          Field("shelter_id", "integer",
                                readable = False,
                                writable = False),
                          location_id(widget=S3LocationAutocompleteWidget(),
                                      comment=S3PopupLink(c = "gis",
                                                          f = "location",
                                                          label = ADD_LOCATION,
                                                          title = T("Current Location"),
                                                          tooltip = T("The Current Location of the Person/Group, which can be general (for Reporting) or precise (for displaying on a Map). Enter a few characters to search from available locations.")),
                                                          ),
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
                                comment = DIV(_class="tooltip",
                                              _title="%s|%s" % (T("Procedure"),
                                                                T("Describe the procedure which this record relates to (e.g. 'medical examination')")))),
                          location_id("orig_id",
                                      label=T("Origin"),
                                      widget = S3LocationAutocompleteWidget(),
                                      comment=S3PopupLink(c = "gis",
                                                          f = "location",
                                                          label = ADD_LOCATION,
                                                          title = T("Origin"),
                                                          tooltip = T("The Location the Person has come from, which can be general (for Reporting) or precise (for displaying on a Map). Enter a few characters to search from available locations."),
                                                          ),
                                      ),
                          location_id("dest_id",
                                      label=T("Destination"),
                                      widget = S3LocationAutocompleteWidget(),
                                      comment=S3PopupLink(c = "gis",
                                                          f = "location",
                                                          label = ADD_LOCATION,
                                                          title = T("Destination"),
                                                          tooltip = T("The Location the Person is going to, which can be general (for Reporting) or precise (for displaying on a Map). Enter a few characters to search from available locations."),
                                                          ),
                                      ),
                          Field("comment"),
                          Field("closed", "boolean",
                                default=False,
                                readable = False,
                                writable = False),
                          *s3_meta_fields())

        # CRUD Strings
        ADD_LOG_ENTRY = T("Add Log Entry")
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = ADD_LOG_ENTRY,
            title_display = T("Log Entry Details"),
            title_list = T("Presence Log"),
            title_update = T("Edit Log Entry"),
            label_list_button = T("List Log Entries"),
            msg_record_created = T("Log entry added"),
            msg_record_modified = T("Log entry updated"),
            msg_record_deleted = T("Log Entry Deleted"),
            msg_list_empty = T("No Presence Log Entries currently registered"))

        # Resource configuration
        self.configure(tablename,
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
                       extra="location_details",
                       super_entity = "sit_situation",
                       )

        # ---------------------------------------------------------------------
        # Return model-global names to response.s3
        #
        return {"pr_trackable_types": pr_trackable_types,
                "pr_default_trackable": pr_default_trackable,
                "pr_presence_opts": pr_presence_opts,
                "pr_presence_conditions": pr_presence_conditions,
                "pr_default_presence": pr_default_presence
                }

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
            dbset = db(shelter_table.id == shelter)
            row = dbset.select(shelter_table.location_id,
                               limitby = (0, 1),
                               ).first()
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
                    record = db(table.id == form.vars.id).select(
                                    table.location_id,
                                    table.shelter_id,
                                    limitby = (0, 1),
                                    ).first()
                    if record and \
                       record.location_id or record.shelter_id:
                        return
            else:
                return
        else:
            return

        form.errors.location_id = \
        form.errors.shelter_id = current.T("Either a shelter or a location must be specified")

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

        if isinstance(form, INTEGER_TYPES + (str,)):
            record_id = form
        elif hasattr(form, "vars"):
            record_id = form.vars.id
        else:
            # e.g. Row like for delete
            record_id = form.id

        presence = db(table.id == record_id).select(table.ALL,
                                                    limitby = (0, 1),
                                                    ).first()
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
                    db(table.id == record_id).update(closed=False)

            elif condition in popts.PERSISTANT_PRESENCE:
                if not presence.closed:
                    query = this_entity & earlier & (is_present | is_missing) & \
                            (table.closed == False)
                    db(query).update(closed=True)

                    query = this_entity & later & \
                            (is_present | (is_absent & same_place))
                    if db(query).count():
                        db(table.id == record_id).update(closed=True)

            elif condition in popts.ABSENCE:
                query = this_entity & earlier & is_present & same_place
                db(query).update(closed=True)

                if not presence.closed:
                    db(table.id == record_id).update(closed=True)

        if not presence.closed:

            # Re-open the last persistent presence if no closing event
            query = this_entity & is_present
            presence = db(query).select(table.ALL,
                                        orderby=~table.datetime,
                                        limitby=(0, 1)).first()
            if presence and presence.closed:
                later = (table.datetime > presence.datetime)
                query = this_entity & later & is_absent & same_place
                if not db(query).count():
                    db(table.id == presence.id).update(closed=False)

            # Re-open the last missing if no later persistent presence
            query = this_entity & is_missing
            presence = db(query).select(table.ALL,
                                        orderby=~table.datetime,
                                        limitby=(0,1)).first()
            if presence and presence.closed:
                later = (table.datetime > presence.datetime)
                query = this_entity & later & is_present
                if not db(query).count():
                    db(table.id == presence.id).update(closed=False)

        pentity = db(db.pr_pentity.pe_id == pe_id).select(db.pr_pentity.instance_type,
                                                          limitby = (0, 1),
                                                          ).first()
        if pentity and pentity.instance_type == "pr_person":
            query = this_entity & is_missing & (table.closed == False)
            if db(query).count():
                db(db.pr_person.pe_id == pe_id).update(missing = True)
            else:
                db(db.pr_person.pe_id == pe_id).update(missing = False)

# =============================================================================
class PRAvailabilityModel(S3Model):
    """
        Availability for Persons, Sites, Services, Assets, etc
        - will allow for automated rostering/matching
    """

    names = ("pr_date_formula",
             "pr_time_formula",
             "pr_slot",
             "pr_person_availability",
             "pr_person_availability_slot",
             )

    def model(self):

        T = current.T

        configure = self.configure
        define_table = self.define_table

        db = current.db

        # ---------------------------------------------------------------------
        # Date Formula
        #
        interval_opts = {1: T("Daily"),
                         2: T("Weekly"),
                         #3: T("Monthly"),
                         #4: T("Yearly"),
                         }

        days_of_week = {0: T("Sunday"),
                        1: T("Monday"),
                        2: T("Tuesday"),
                        3: T("Wednesday"),
                        4: T("Thursday"),
                        5: T("Friday"),
                        6: T("Sunday"),
                        }

        tablename = "pr_date_formula"
        define_table(tablename,
                     Field("name",
                           label = T("Name"),
                           ),
                     # "interval" is a reserved word in MySQL
                     Field("date_interval", "integer",
                           represent = S3Represent(options=interval_opts),
                           #requires = IS_IN_SET(interval_opts),
                           ),
                     Field("rate", "integer"), # Repeat Frequency
                     Field("days_of_week", "list:integer",
                           represent = S3Represent(options=days_of_week),
                           #requires = IS_IN_SET((0, 1, 2, 3, 4, 5, 6),
                           #                     multiple = True,
                           #                     ),
                           ),
                     *s3_meta_fields())

        configure(tablename,
                  deduplicate = S3Duplicate(),
                  )

        # ---------------------------------------------------------------------
        # Time Formula
        #
        tablename = "pr_time_formula"
        define_table(tablename,
                     Field("name",
                           label = T("Name"),
                           ),
                     Field("all_day", "boolean",
                           default = False,
                           represent = s3_yes_no_represent,
                           ),
                     Field("start_time", "time",
                           # @ToDo: s3_time reusablefield?
                           #widget =
                           ),
                     Field("end_time", "time",
                           #widget =
                           ),
                     *s3_meta_fields())

        configure(tablename,
                  deduplicate = S3Duplicate(),
                  )

        # ---------------------------------------------------------------------
        # Slots
        #
        tablename = "pr_slot"
        define_table(tablename,
                     Field("name",
                           label = T("Name"),
                           ),
                     Field("date_formula_id", "reference pr_date_formula"),
                     Field("time_formula_id", "reference pr_time_formula"),
                     *s3_meta_fields())

        configure(tablename,
                  deduplicate = S3Duplicate(),
                  )

        represent = S3Represent(lookup=tablename, translate=True)
        slot_id = S3ReusableField("slot_id", "reference %s" % tablename,
                                  label = T("Slot"),
                                  ondelete = "RESTRICT",
                                  represent = represent,
                                  requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "pr_slot.id",
                                                          represent)),
                                  #comment=S3PopupLink(c = "pr",
                                  #                    f = "slot",
                                  #                    label = ADD_SLOT,
                                  #                    ),
                                  )

        # ---------------------------------------------------------------------
        # Person Availability
        #

        availability_options = \
            current.deployment_settings.get_pr_person_availability_options()
        if availability_options is None:
            options_readable = False
            options_represent = None
            options_requires = None
        else:
            options_readable = True
            options_represent = S3Represent(options=availability_options)
            options_requires = IS_EMPTY_OR(IS_IN_SET(availability_options))

        tablename = "pr_person_availability"
        define_table(tablename,
                     self.pr_person_id(empty = False,
                                       ondelete = "CASCADE",
                                       ),
                     #s3_date("start_date",
                     #        label = T("Start Date"),
                     #        ),
                     #s3_date("end_date",
                     #        label = T("End Date"),
                     #        ),
                     #self.gis_location_id(),
                     # Dropdown of alternate options
                     # - cannot be used for Rostering, but can give additional
                     #   information to the slots or just be a simpler alternative
                     Field("options", "integer",
                           represent = options_represent,
                           requires = options_requires,
                           readable = options_readable,
                           writable = options_readable,
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        configure(tablename,
                  # @todo: adapt deduplicator once we allow multiple
                  #        availability records per person (e.g. include
                  #        start/end dates and location_id)
                  deduplicate = S3Duplicate(primary=("person_id",)),
                  )

        self.add_components(tablename,
                            # Inline Form added in customise to provide a list of slots
                            pr_person_availability_slot = "availability_id",
                            pr_slot = {"link": "pr_person_availability_slot",
                                       "joinby": "availability_id",
                                       "key": "slot_id",
                                       "actuate": "link",
                                       },
                            )

        # ---------------------------------------------------------------------
        # Person Availability <> Slots
        #
        tablename = "pr_person_availability_slot"
        define_table(tablename,
                     Field("availability_id", "reference pr_person_availability"),
                     slot_id(),
                     *s3_meta_fields())

        configure(tablename,
                  deduplicate = S3Duplicate(primary=("availability_id", "slot_id")),
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class PRUnavailabilityModel(S3Model):
    """
        Allow people to mark times when they are unavailable
        - this is generally easier for longer-term volunteers than marking times
          when they are available
        - usually defined using the Organiser method
    """

    names = ("pr_unavailability",
             )

    def model(self):

        T = current.T

        tablename = "pr_unavailability"
        self.define_table(tablename,
                          self.pr_person_id(ondelete = "CASCADE"),
                          s3_datetime("start_date",
                                      label = T("Start Date"),
                                      set_min = "#pr_unavailability_end_date",
                                      ),
                          s3_datetime("end_date",
                                      label = T("End Date"),
                                      set_max = "#pr_unavailability_start_date",
                                      ),
                          s3_comments(),
                          *s3_meta_fields())

        self.configure(tablename,
                       organize = {"start": "start_date",
                                   "end": "end_date",
                                   "title": "comments",
                                   "description": ["start_date",
                                                   "end_date",
                                                   ],
                                   },
                       )

        # CRUD Strings
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Period of Unavailability"),
            title_display = T("Unavailability"),
            title_list = T("Periods of Unavailability"),
            title_update = T("Edit Unavailability"),
            label_list_button = T("List Periods of Unavailability"),
            label_delete_button = T("Delete Unavailability"),
            msg_record_created = T("Unavailability added"),
            msg_record_modified = T("Unavailability updated"),
            msg_record_deleted = T("Unavailability deleted"),
            msg_list_empty = T("No Unavailability currently registered"))

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class PRDescriptionModel(S3Model):
    """
        Additional tables used mostly for DVI/MPR
    """

    names = ("pr_age_group",
             "pr_age_group_opts",
             "pr_note",
             "pr_physical_description",
             )

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
        define_table(tablename,
                     # Component not Instance
                     super_link("pe_id", "pr_pentity"),
                     # Reporter
                     #self.pr_person_id("reporter"),
                     Field("confirmed", "boolean",
                           default = False,
                           readable = False,
                           writable = False,
                           ),
                     Field("closed", "boolean",
                           default = False,
                           readable = False,
                           writable = False,
                           ),
                     Field("status", "integer",
                           default = 9,
                           label = T("Status"),
                           represent = lambda opt: \
                                    person_status.get(opt, UNKNOWN_OPT),
                           requires = IS_IN_SET(person_status,
                                                zero=None),
                           ),
                     s3_datetime("timestmp",
                                 default = "now",
                                 label = T("Date/Time"),
                                 ),
                     Field("note_text", "text",
                           label = T("Text"),
                           ),
                     Field("note_contact", "text",
                           label = T("Contact Info"),
                           readable = False,
                           writable = False,
                           ),
                     self.gis_location_id(label = T("Last known location")),
                     *s3_meta_fields())

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("New Entry"),
            title_display = T("Journal Entry Details"),
            title_list = T("Journal"),
            title_update = T("Edit Entry"),
            label_list_button = T("See All Entries"),
            msg_record_created = T("Journal entry added"),
            msg_record_modified = T("Journal entry updated"),
            msg_record_deleted = T("Journal entry deleted"),
            msg_list_empty = T("No entry available"))

        # Resource configuration
        self.configure(tablename,
                       editable = False,
                       list_fields = ["id",
                                      "timestmp",
                                      "location_id",
                                      "note_text",
                                      "status",
                                      ],
                       onaccept = self.note_onaccept,
                       ondelete = self.note_onaccept,
                       )

        # =====================================================================
        # Physical Description
        #
        pr_age_group_opts = {
            1:T("unknown"),
            2:T("Infant (0-1)"),
            3:T("Child (2-11)"),
            4:T("Adolescent (12-20)"),
            5:T("Adult (21-50)"),
            6:T("Senior (50+)")
        }
        # Also used in DVI
        pr_age_group = S3ReusableField("age_group", "integer",
                                       default = 1,
                                       label = T("Age Group"),
                                       represent = lambda opt: \
                                                   pr_age_group_opts.get(opt,
                                                                         UNKNOWN_OPT),
                                       requires = IS_IN_SET(pr_age_group_opts,
                                                            zero=None),
                                       )

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
        #pr_ethnicity_opts = [
        #    "American Indian",
        #    "Alaskan",
        #    "Asian",
        #    "African American",
        #    "Hispanic or Latino",
        #    "Native Hawaiian",
        #    "Pacific Islander",
        #    "Two or more",
        #    "Unspecified",
        #    "White"
        #]

        tablename = "pr_physical_description"
        define_table(tablename,
                     # Component not Instance
                     super_link("pe_id", "pr_pentity",
                                readable = True,
                                writable = True,
                                ),
                     # Age Group - for use where we don't know the DoB
                     pr_age_group(readable = False,
                                  writable = False,
                                  ),
                     # Race and complexion
                     Field("race", "integer",
                           label = T("Race"),
                           represent = lambda opt: \
                                       pr_race_opts.get(opt, UNKNOWN_OPT),
                           requires = IS_EMPTY_OR(IS_IN_SET(pr_race_opts)),
                           ),
                     Field("complexion", "integer",
                           label = T("Complexion"),
                           represent = lambda opt: \
                                       pr_complexion_opts.get(opt, UNKNOWN_OPT),
                           requires = IS_EMPTY_OR(IS_IN_SET(pr_complexion_opts)),
                           ),
                     Field("ethnicity", length=64, # Mayon Compatibility
                           label = T("Ethnicity"),
                           #requires = IS_EMPTY_OR(IS_IN_SET(pr_ethnicity_opts)),
                           requires = IS_LENGTH(64),
                           ),
                     # Height and weight
                     Field("height", "integer",
                           label = T("Height"),
                           represent = lambda opt: \
                                       pr_height_opts.get(opt, UNKNOWN_OPT),
                           requires = IS_EMPTY_OR(IS_IN_SET(pr_height_opts)),
                           ),
                     Field("height_cm", "integer",
                           label = T("Height (cm)"),
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 300)),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Height"),
                                                           T("The body height (crown to heel) in cm."))),
                           ),
                     Field("weight", "integer",
                           label = T("Weight"),
                           represent = lambda opt: \
                                       pr_weight_opts.get(opt, UNKNOWN_OPT),
                           requires = IS_EMPTY_OR(IS_IN_SET(pr_weight_opts)),
                           ),
                     Field("weight_kg", "integer",
                           label = T("Weight (kg)"),
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, None)),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Weight"),
                                                           T("The weight in kg."))),
                           ),
                     # Blood type, eye color
                     Field("blood_type",
                           label = T("Blood Type (AB0)"),
                           represent = lambda opt: opt or UNKNOWN_OPT,
                           requires = IS_EMPTY_OR(IS_IN_SET(pr_blood_type_opts)),
                           ),
                     Field("eye_color", "integer",
                           label = T("Eye Color"),
                           represent = lambda opt: \
                                       pr_eye_color_opts.get(opt, UNKNOWN_OPT),
                           requires = IS_EMPTY_OR(IS_IN_SET(pr_eye_color_opts)),
                           ),

                     # Hair of the head
                     Field("hair_color", "integer",
                           label = T("Hair Color"),
                           represent = lambda opt: \
                                       pr_hair_color_opts.get(opt, UNKNOWN_OPT),
                           requires = IS_EMPTY_OR(IS_IN_SET(pr_hair_color_opts)),
                           ),
                     Field("hair_style", "integer",
                           label = T("Hair Style"),
                           represent = lambda opt: \
                                       pr_hair_style_opts.get(opt, UNKNOWN_OPT),
                           requires = IS_EMPTY_OR(IS_IN_SET(pr_hair_style_opts)),
                           ),
                     Field("hair_length", "integer",
                           label = T("Hair Length"),
                           represent = lambda opt: \
                                       pr_hair_length_opts.get(opt, UNKNOWN_OPT),
                           requires = IS_EMPTY_OR(IS_IN_SET(pr_hair_length_opts)),
                           ),
                     Field("hair_baldness", "integer",
                           label = T("Baldness"),
                           represent = lambda opt: \
                                       pr_hair_baldness_opts.get(opt, UNKNOWN_OPT),
                           requires = IS_EMPTY_OR(IS_IN_SET(pr_hair_baldness_opts)),
                           ),
                     Field("hair_comment",
                           label = T("Hair Comments"),
                           ),

                     # Facial hair
                     Field("facial_hair_type", "integer",
                           label = T("Facial hair, type"),
                           represent = lambda opt: \
                                       pr_facial_hair_type_opts.get(opt, UNKNOWN_OPT),
                           requires = IS_EMPTY_OR(IS_IN_SET(pr_facial_hair_type_opts)),
                           ),
                     Field("facial_hair_color", "integer",
                           label = T("Facial hair, color"),
                           represent = lambda opt: \
                                       pr_hair_color_opts.get(opt, UNKNOWN_OPT),
                           requires = IS_EMPTY_OR(IS_IN_SET(pr_hair_color_opts)),
                           ),
                     Field("facial_hair_length", "integer",
                           label = T("Facial hair, length"),
                           represent = lambda opt: \
                                       pr_facial_hair_length_opts.get(opt, UNKNOWN_OPT),
                           requires = IS_EMPTY_OR(IS_IN_SET(pr_facial_hair_length_opts)),
                           ),
                     Field("facial_hair_comment",
                           label = T("Facial hair, comment"),
                           ),

                     # Body hair and skin marks
                     Field("body_hair",
                           label = T("Body Hair"),
                           ),
                     Field("skin_marks", "text",
                           label = T("Skin Marks"),
                           ),

                     # Medical Details: scars, amputations, implants
                     Field("medical_conditions", "text",
                           label = T("Medical Conditions"),
                           ),

                     Field("allergic", "boolean",
                           label = T("Allergic"),
                           represent = s3_yes_no_represent,
                           ),
                     Field("allergies", "text",
                           label = T("Allergies"),
                           ),

                     # Other details
                     Field("other_details", "text",
                           label = T("Other Details"),
                           ),

                     s3_comments(),
                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Return model-global names to response.s3
        #
        return {"pr_age_group": pr_age_group,
                "pr_age_group_opts": pr_age_group_opts,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def note_onaccept(form):
        """ Update missing status for person """

        db = current.db
        s3db = current.s3db
        ntable = db.pr_note
        ptable = s3db.pr_person

        if isinstance(form, INTEGER_TYPES + (str,)):
            record_id = form
        elif hasattr(form, "vars"):
            record_id = form.vars.id
        else:
            record_id = form.id

        note = ntable[record_id]
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
            except AttributeError:
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
class PREducationModel(S3Model):
    """ Education details for Persons """

    names = ("pr_education_level",
             "pr_education",
             )

    def model(self):

        T = current.T

        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        messages = current.messages
        NONE = messages["NONE"]

        auth = current.auth
        ADMIN = current.session.s3.system_roles.ADMIN
        is_admin = auth.s3_has_role(ADMIN)
        root_org = auth.root_org()
        if is_admin:
            filter_opts = ()
        elif root_org:
            filter_opts = (root_org, None)
        else:
            filter_opts = (None,)

        # ---------------------------------------------------------------------
        # Education Level
        #
        tablename = "pr_education_level"
        define_table(tablename,
                     Field("name", length=64, notnull=True,
                           label = T("Name"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(64),
                                       ],
                           ),
                     # Only included in order to be able to set
                     # realm_entity to filter appropriately
                     self.org_organisation_id(default = root_org,
                                              readable = is_admin,
                                              writable = is_admin,
                                              ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        ADD_EDUCATION_LEVEL = T("Add Education Level")
        crud_strings[tablename] = Storage(
           label_create = ADD_EDUCATION_LEVEL,
           title_display = T("Education Level"),
           title_list = T("Education Levels"),
           title_update = T("Edit Education Level"),
           label_list_button = T("List Education Levels"),
           msg_record_created = T("Education Level added"),
           msg_record_modified = T("Education Level updated"),
           msg_record_deleted = T("Education Level deleted"),
           msg_list_empty = T("No Education Levels currently registered"))

        represent = S3Represent(lookup=tablename, translate=True)
        level_id = S3ReusableField("level_id", "reference %s" % tablename,
                                   comment = S3PopupLink(c = "pr",
                                                         f = "education_level",
                                                         label = ADD_EDUCATION_LEVEL,
                                                         ),
                                   label = T("Level of Award"),
                                   ondelete = "RESTRICT",
                                   represent = represent,
                                   requires = IS_EMPTY_OR(
                                        IS_ONE_OF(current.db, "pr_education_level.id",
                                                  represent,
                                                  filterby="organisation_id",
                                                  filter_opts=filter_opts
                                                  )),
                                   sortby = "name",
                                   )

        configure(tablename,
                  deduplicate = S3Duplicate(primary = ("name",),
                                            secondary = ("organisation_id",),
                                            ),
                  )

        # ---------------------------------------------------------------------
        # Education
        #
        country_opts = current.gis.get_countries(key_type="code")

        tablename = "pr_education"
        define_table(tablename,
                     self.pr_person_id(label = T("Person"),
                                       ondelete = "CASCADE",
                                       ),
                     level_id(),
                     # Enable this field for backwards-compatibility or to store details of the 'other' level
                     Field("level",
                           #label = T("Level other"),
                           represent = lambda v: v or NONE,
                           readable = False,
                           writable = False,
                           ),
                     Field("award",
                           label = T("Name of Award"),
                           represent = lambda v: v or NONE,
                           ),
                     Field("country",
                           label = T("Country"),
                           represent = S3Represent(options=country_opts),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(country_opts,
                                                  zero=messages.SELECT_LOCATION),
                                        ),
                           # Enable in template as-required
                           readable = False,
                           writable = False,
                           ),
                     Field("institute",
                           label = T("Name of Institute"),
                           represent = lambda v: v or NONE,
                           ),
                     Field("year", "integer",
                           label = T("Year"),
                           represent = lambda v: v or NONE,
                           requires = IS_EMPTY_OR(
                                        IS_INT_IN_RANGE(1900, 2100)
                                        ),
                           ),
                     Field("major",
                           label = T("Major"),
                           represent = lambda v: v or NONE,
                           ),
                     Field("grade",
                           label = T("Grade"),
                           represent = lambda v: v or NONE,
                           ),
                     Field("current", "boolean",
                           default = False,
                           label = T("Current?"),
                           represent = s3_yes_no_represent,
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Education Detail"),
            title_display = T("Education Details"),
            title_list = T("Education Details"),
            title_update = T("Edit Education Details"),
            label_list_button = T("List Education Details"),
            msg_record_created = T("Education details added"),
            msg_record_modified = T("Education details updated"),
            msg_record_deleted = T("Education details deleted"),
            msg_list_empty = T("No entries currently registered"))

        configure("pr_education",
                  context = {"person": "person_id",
                             },
                  deduplicate = S3Duplicate(primary = ("person_id",
                                                       "level",
                                                       "award",
                                                       "year",
                                                       "institute",
                                                       ),
                                            ignore_deleted = True,
                                            ),
                  list_fields = [# Normally accessed via component
                                 #"person_id",
                                 "year",
                                 "level_id",
                                 "award",
                                 "major",
                                 "grade",
                                 "institute",
                                 ],
                  orderby = "pr_education.year desc",
                  sortby = [[1, "desc"]]
                  )

        # ---------------------------------------------------------------------
        # Return model-global names to response.s3
        #
        return {}

# =============================================================================
class PRIdentityModel(S3Model):
    """ Identities for Persons """

    names = ("pr_identity",)

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
        pr_id_type_opts = {1:  T("Passport"),
                           2:  T("National ID Card"),
                           3:  T("Driving License"),
                           #4: T("Credit Card"),
                           5:  T("Residence Permit"),
                           99: T("other")
                           }

        tablename = "pr_identity"
        self.define_table(tablename,
                          self.pr_person_id(label = T("Person"),
                                            ondelete = "CASCADE",
                                            ),
                          Field("type", "integer",
                                default = 1,
                                label = T("ID Type"),
                                represent = S3Represent(options=pr_id_type_opts),
                                requires = IS_IN_SET(pr_id_type_opts,
                                                     zero=None),
                                ),
                          Field("description",
                                label = T("Description"),
                                ),
                          Field("value",
                                label = T("Number"),
                                ),
                          s3_date("valid_from",
                                  label = T("Valid From"),
                                  future = 0,
                                  set_min = "#pr_identity_valid_until",
                                  ),
                          s3_date("valid_until",
                                  label = T("Valid Until"),
                                  set_max = "#pr_identity_valid_from",
                                  start_field = "pr_identity_valid_from",
                                  default_interval = 12,
                                  ),
                          Field("country_code", length=4,
                                label = T("Country Code"),
                                # Enable in template if-required
                                readable = False,
                                writable = False,
                                ),
                          Field("place",
                                label = T("Place of Issue"),
                                #  Enable in template if-required
                                readable = False,
                                writable = False,
                                ),
                          Field("ia_name",
                                label = T("Issuing Authority"),
                                ),
                          #Field("ia_subdivision"), # Name of issuing authority subdivision
                          #Field("ia_code"), # Code of issuing authority (if any)
                          Field("image", "upload",
                                autodelete = True,
                                label = T("Scanned Copy"),
                                length = current.MAX_FILENAME_LENGTH,
                                # upload folder needs to be visible to the download() function as well as the upload
                                uploadfolder = os.path.join(current.request.folder,
                                                            "uploads"),
                               ),
                          s3_comments(),
                          *s3_meta_fields())

        # CRUD Strings
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Identity"),
            title_display = T("Identity Details"),
            title_list = T("Identities"),
            title_update = T("Edit Identity"),
            label_list_button = T("List Identities"),
            msg_record_created = T("Identity added"),
            msg_record_modified = T("Identity updated"),
            msg_record_deleted = T("Identity deleted"),
            msg_list_empty = T("No Identities currently registered"))

        self.configure(tablename,
                       # People can have more than 1 'Other', or even Passport
                       # - so this cannot be used to update the Number, only
                       #   update comments:
                       deduplicate = S3Duplicate(primary = ("person_id",
                                                            "type",
                                                            "value",
                                                            ),
                                                 ignore_deleted = True,
                                                 ),
                       list_fields = ["id",
                                      "type",
                                      "value",
                                      "valid_until",
                                      #"country_code",
                                      #"ia_name"
                                      ],
                       )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class PRLanguageModel(S3Model):
    """
        Languages for Persons
        - alternate model to Skills for alternate UX
        - used by IFRC RDRP AP
    """

    names = ("pr_language",)

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Language
        #
        fluency_opts = {1:  T("Beginner"),
                        2:  T("Intermediate"),
                        3:  T("Advanced"),
                        4:  T("Native language"),
                        }

        tablename = "pr_language"
        self.define_table(tablename,
                          self.pr_person_id(label = T("Person"),
                                            ondelete = "CASCADE",
                                            ),
                          s3_language(),
                          Field("writing", "integer",
                                #default = None,
                                label = T("Writing"),
                                represent = S3Represent(options=fluency_opts),
                                requires = IS_IN_SET(fluency_opts),
                                ),
                          Field("speaking", "integer",
                                #default = None,
                                label = T("Speaking"),
                                represent = S3Represent(options=fluency_opts),
                                requires = IS_IN_SET(fluency_opts),
                                ),
                          Field("understanding", "integer",
                                #default = None,
                                label = T("Understanding"),
                                represent = S3Represent(options=fluency_opts),
                                requires = IS_IN_SET(fluency_opts),
                                ),
                          #s3_comments(),
                          *s3_meta_fields())

        # CRUD Strings
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Language"),
            title_display = T("Language Details"),
            title_list = T("Languages"),
            title_update = T("Edit Language"),
            label_list_button = T("List Languages"),
            msg_record_created = T("Language added"),
            msg_record_modified = T("Language updated"),
            msg_record_deleted = T("Language deleted"),
            msg_list_empty = T("No Languages currently registered for this person"))

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class PROccupationModel(S3Model):
    """
        Model for a person's current occupations, catalog-based
        alternative to the free-text pr_person_details.occupation
    """

    names = ("pr_occupation_type",
             "pr_occupation_type_person",
             )

    def model(self):

        T = current.T

        db = current.db
        s3 = current.response.s3

        define_table = self.define_table
        crud_strings = s3.crud_strings

        # ---------------------------------------------------------------------
        # Occupation Types
        #
        tablename = "pr_occupation_type"
        define_table(tablename,
                     Field("name", length=128, notnull=True,
                           label = T("Name"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(128),
                                       IS_NOT_ONE_OF(db,
                                                     "%s.name" % tablename,
                                                     ),
                                       ],
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # Table Configuration
        self.configure(tablename,
                       deduplicate = S3Duplicate(),
                       )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Occupation Type"),
            title_display = T("Occupation Type Details"),
            title_list = T("Occupation Types"),
            title_update = T("Edit Occupation Type"),
            label_list_button = T("List Occupation Types"),
            label_delete_button = T("Delete Occupation Type"),
            msg_record_created = T("Occupation Type created"),
            msg_record_modified = T("Occupation Type updated"),
            msg_record_deleted = T("Occupation Type deleted"),
            msg_list_empty = T("No Occupation Types currently defined"),
        )

        # Reusable field
        represent = S3Represent(lookup = tablename,
                                translate = True,
                                )
        occupation_type_id = S3ReusableField("occupation_type_id",
                                             "reference %s" % tablename,
                                             label = T("Occupation Type"),
                                             represent = represent,
                                             requires = IS_ONE_OF(db,
                                                          "pr_occupation_type.id",
                                                          represent,
                                                          ),
                                             sortby = "name",
                                             comment = S3PopupLink(c="pr",
                                                                   f="occupation_type",
                                                                   tooltip=T("Create a new occupation type"),
                                                                   ),
                                             )

        # ---------------------------------------------------------------------
        # Occupation Type <=> Person Link
        #
        tablename = "pr_occupation_type_person"
        define_table(tablename,
                     occupation_type_id(ondelete="RESTRICT",
                                        ),
                     self.pr_person_id(ondelete="CASCADE",
                                       ),
                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class PRPersonDetailsModel(S3Model):
    """ Extra optional details for People """

    names = ("pr_person_details",
             "pr_marital_status_opts",
             )

    def model(self):

        T = current.T
        settings = current.deployment_settings
        messages = current.messages

        NONE = messages["NONE"]

        # ---------------------------------------------------------------------
        # Person Details
        #

        # Marital Status Options
        marital_status_opts = {
            1: T("unknown"),
            2: T("single"),
            3: T("married"),
            4: T("separated"),
            5: T("divorced"),
            6: T("widowed"),
            7: T("cohabiting"),
            8: T("married (not legally recognized)"),
            9: T("other"),
        }

        # Literacy Status Options
        literacy_opts = {
            1: T("unknown"),
            2: T("illiterate"),
            3: T("literate"),
        }

        # Nationality Options
        nationality_opts = pr_nationality_opts
        nationality_repr = pr_nationality_prepresent

        # Religion Options
        religion_opts = settings.get_L10n_religions()

        tablename = "pr_person_details"
        self.define_table(tablename,
                          self.pr_person_id(label = T("Person"),
                                            ondelete = "CASCADE",
                                            ),
                          s3_language(default = None),
                          Field("nationality",
                                label = T("Nationality"),
                                represent = nationality_repr,
                                requires = IS_EMPTY_OR(
                                            IS_IN_SET_LAZY(nationality_opts,
                                                           zero = messages.SELECT_LOCATION,
                                                           )),
                                comment = DIV(_class="tooltip",
                                              _title="%s|%s" % (T("Nationality"),
                                                                T("Nationality of the person."))),
                                ),
                          Field("nationality2",
                                label = T("2nd Nationality"),
                                represent = nationality_repr,
                                requires = IS_EMPTY_OR(
                                            IS_IN_SET_LAZY(nationality_opts,
                                                           zero = messages.SELECT_LOCATION,
                                                           )),
                                comment = DIV(_class="tooltip",
                                              _title="%s|%s" % (T("2nd Nationality"),
                                                                T("Second Nationality of the person (if they have one)"))),
                                # Enable in templates as-required
                                readable = False,
                                writable = False,
                                ),
                          Field("place_of_birth",
                                label = T("Place of Birth"),
                                represent = lambda v: v or NONE,
                                # Enable as-required in template
                                readable = False,
                                writable = False,
                                ),
                          Field("age", "integer",
                                label = T("Age"),
                                requires = IS_EMPTY_OR(
                                    IS_INT_IN_RANGE(0, 150)
                                    ),
                                # Enable as-required in template
                                # (used when this is all that is available: normally use Date of Birth)
                                readable = False,
                                writable = False,
                                ),
                          Field("year_of_birth", "integer",
                                label = T("Year of Birth"),
                                requires = IS_EMPTY_OR(
                                    IS_INT_IN_RANGE(1900, current.request.now.year)
                                    ),
                                # Enable as-required in template
                                # (used when this is all that is available: normally use Date of Birth)
                                readable = False,
                                writable = False,
                                ),
                          Field("hometown",
                                label = T("Home Town"),
                                represent = lambda v: v or NONE,
                                # Enable as-required in template
                                readable = False,
                                writable = False,
                                ),
                          Field("marital_status", "integer",
                                default = 1,
                                label = T("Marital Status"),
                                represent = S3Represent(options=marital_status_opts),
                                requires = IS_IN_SET(marital_status_opts,
                                                     zero=None,
                                                     ),
                                ),
                          Field("number_children", "integer",
                                label = T("Number of Children"),
                                ),
                          Field("religion", length=128,
                                label = T("Religion"),
                                represent = S3Represent(options=religion_opts),
                                requires = IS_EMPTY_OR(IS_IN_SET(religion_opts)),
                                ),
                          # This field can either be used as a free-text version of religion, or to provide details of the 'other'
                          Field("religion_other",
                                #label = T("Other Religion"),
                                represent = lambda v: v or NONE,
                                readable = False,
                                writable = False,
                                ),
                          Field("father_name",
                                label = T("Name of Father"),
                                represent = lambda v: v or NONE,
                                ),
                          Field("mother_name",
                                label = T("Name of Mother"),
                                represent = lambda v: v or NONE,
                                ),
                          Field("grandfather_name",
                                label = T("Name of Grandfather"),
                                represent = lambda v: v or NONE,
                                readable = False,
                                writable = False,
                                ),
                          Field("grandmother_name",
                                label = T("Name of Grandmother"),
                                represent = lambda v: v or NONE,
                                readable = False,
                                writable = False,
                                ),
                          Field("occupation", length=128, # Mayon Compatibility
                                label = T("Profession"),
                                represent = lambda v: v or NONE,
                                requires = IS_LENGTH(128),
                                ),
                          Field("education", length=128,
                                label = T("Educational Background"),
                                represent = lambda v: v or NONE,
                                requires = IS_LENGTH(128),
                                ),
                          Field("company",
                                label = T("Company"),
                                represent = lambda v: v or NONE,
                                # @ToDo: Autofill from hrm_human_resource Staff Organisation
                                ),
                          Field("affiliations",
                                label = T("Affiliations"),
                                represent = lambda v: v or NONE,
                                # @ToDo: Autofill from hrm_human_resource Volunteer Organisation
                                ),
                          Field("criminal_record", "boolean",
                                label = T("Criminal Record"),
                                represent = s3_yes_no_represent,
                                ),
                          Field("military_service", "boolean",
                                label = T("Military Service"),
                                represent = s3_yes_no_represent,
                                ),
                          Field("disabled", "boolean",
                                label = T("Disabled"),
                                represent = s3_yes_no_represent,
                                ),
                          Field("literacy", "integer",
                                default = 3,
                                label = T("Literacy"),
                                represent = S3Represent(options = literacy_opts),
                                requires = IS_IN_SET(literacy_opts,
                                                     zero=None,
                                                     ),
                                ),
                          *s3_meta_fields())

        # CRUD Strings
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Person's Details"),
            title_display = T("Person's Details"),
            title_list = T("Persons' Details"),
            title_update = T("Edit Person's Details"),
            label_list_button = T("List Persons' Details"),
            msg_record_created = T("Person's Details added"),
            msg_record_modified = T("Person's Details updated"),
            msg_record_deleted = T("Person's Details deleted"),
            msg_list_empty = T("There are no details for this person yet. Add Person's Details."))

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary=("person_id",),
                                                 ignore_deleted = True,
                                                 ),
                       )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"pr_marital_status_opts": marital_status_opts,
                }

# =============================================================================
class PRPersonLocationModel(S3Model):
    """
        Person Location Model
        - Locations served by a Person
    """

    names = ("pr_person_location",)

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Persons <> Locations Link Table
        #
        tablename = "pr_person_location"
        self.define_table(tablename,
                          self.pr_person_id(),
                          self.gis_location_id(
                            #represent = self.gis_LocationRepresent(sep=", "),
                            requires = IS_LOCATION(),
                            widget = S3LocationAutocompleteWidget()
                          ),
                          s3_comments(),
                          *s3_meta_fields()
                          )

        # CRUD Strings
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Location"),
            title_display = T("Location"),
            title_list = T("Locations"),
            title_update = T("Edit Location"),
            title_upload = T("Import Location data"),
            label_list_button = T("List Locations"),
            msg_record_created = T("Location added to Person"),
            msg_record_modified = T("Location updated"),
            msg_record_deleted = T("Location removed from Person"),
            msg_list_empty = T("No Locations found for this Person"))

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("person_id",
                                                            "location_id",
                                                            ),
                                                 ),
                       )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class PRPersonTagModel(S3Model):
    """
        Person Tags
    """

    names = ("pr_person_tag",
             )

    def model(self):

        T = current.T

        tablename = "pr_person_tag"
        self.define_table(tablename,
                          self.pr_person_id(ondelete = "CASCADE"),
                          Field("tag",
                                label = T("Key"),
                                ),
                          Field("value",
                                label = T("Value"),
                                ),
                          #s3_comments(),
                          *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("person_id", "tag"),
                                                 ignore_case = True,
                                                 ),
                       )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class PRReligionModel(S3Model):
    """
        Model for religions
        - alternative for the simple religion field for when a full hiearchy is
          needed
    """

    names = ("pr_religion",
             "pr_religion_organisation",
             )

    def model(self):

        T = current.T

        db = current.db
        s3 = current.response.s3

        define_table = self.define_table
        crud_strings = s3.crud_strings

        # ---------------------------------------------------------------------
        # Religions
        #
        tablename = "pr_religion"
        define_table(tablename,
                     Field("name", length=128, notnull=True,
                           label = T("Name"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(128),
                                       ],
                           ),
                     Field("parent", "reference pr_religion", # This form of hierarchy may not work on all Databases
                           label = T("SubType of"),
                           ondelete = "RESTRICT",
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # Table Configuration
        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ["name"],
												 secondary = ["parent"],
												 ),
                       hierarchy = "parent",
                       )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Religion"),
            title_display = T("Religion Details"),
            title_list = T("Religions"),
            title_update = T("Edit Religion"),
            label_list_button = T("List Religions"),
            label_delete_button = T("Delete Religion"),
            msg_record_created = T("Religion created"),
            msg_record_modified = T("Religion updated"),
            msg_record_deleted = T("Religion deleted"),
            msg_list_empty = T("No Religions currently defined"),
        )

        # Reusable field
        represent = S3Represent(lookup = tablename,
                                #translate = True,
                                )
        religion_id = S3ReusableField("religion_id",
                                      "reference %s" % tablename,
                                      label = T("Religion"),
                                      represent = represent,
                                      requires = IS_ONE_OF(db,
                                                  "pr_religion.id",
                                                  represent,
                                                  ),
                                      sortby = "name",
                                      comment = S3PopupLink(c="pr",
                                                            f="religion",
                                                            tooltip=T("Create a new religion"),
                                                            ),
                                      widget = S3HierarchyWidget(lookup = "pr_religion",
                                                                 represent = represent,
                                                                 multiple = False,
                                                                 #leafonly = True,
                                                                 )
                                      )

        # Can't be defined in-line as otherwise get a circular reference
        table = db[tablename]
        table.parent.represent = represent
        table.parent.requires = IS_EMPTY_OR(
                                    IS_ONE_OF(db, "pr_religion.id",
                                              represent,
                                              # If limiting to just 1 level of parent
                                              #filterby="parent",
                                              #filter_opts=(None,),
                                              orderby="pr_religion.name"))

        # ---------------------------------------------------------------------
        # Religion <=> Organisation Link
        #
        tablename = "pr_religion_organisation"
        define_table(tablename,
                     religion_id(ondelete="RESTRICT",
                                 ),
                     self.org_organisation_id(empty = False,
                                              ondelete="CASCADE",
                                              ),
                     *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("religion_id",
                                                            "organisation_id",
                                                            ),
                                                 ),
                       )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

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

    names = ("pr_image_library",
             "pr_image_size",
             "pr_image_delete_all",
             )

    def model(self):

        #T = current.T

        # ---------------------------------------------------------------------
        tablename = "pr_image_library"
        self.define_table(tablename,
                          # Original image file name
                          Field("original_name"),
                          # New image file name
                          Field("new_name", "upload",
                                length = current.MAX_FILENAME_LENGTH,
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
        # Pass names back to global scope (s3.*)
        #
        return {"pr_image_size": self.pr_image_size,
                "pr_image_delete_all": self.pr_image_delete_all,
                }

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
        dbset = db(table.original_name == original_image_name)
        dbset.delete_uploaded_files()
        dbset.delete()

# =============================================================================
class S3RoleDelegationModel(S3Model):
    """ Organisation-based Authorization Model """

    names = ("pr_delegation",)

    def model(self):

        # ---------------------------------------------------------------------
        # Delegation: Role <-> Auth Group Link
        # This "delegates" the permissions of a user group for the records
        # owned by a person entity to a group of affiliated entities.
        #
        gtable = current.auth.settings.table_group
        tablename = "pr_delegation"
        self.define_table(tablename,
                          self.pr_role_id(),
                          Field("group_id", gtable,
                                ondelete="CASCADE"),
                          *s3_meta_fields())

        # ---------------------------------------------------------------------
        return {}

# =============================================================================
class S3SavedFilterModel(S3Model):
    """ Saved Filters """

    names = ("pr_filter",
             "pr_filter_id",
             )

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        tablename = "pr_filter"
        self.define_table(tablename,
                          self.super_link("pe_id", "pr_pentity"),
                          Field("title"),
                          # Controller/Function/Resource/URL are used just for Saved Filters
                          Field("controller"),
                          Field("function"),
                          Field("resource"), # tablename
                          Field("url"),
                          Field("description", "text"),
                          # Query is used for both Saved Filters and Subscriptions
                          # Can use a Context to have this work across multiple resources if a simple selector is insufficient
                          Field("query", "text"),
                          s3_comments(),
                          *s3_meta_fields())

        represent = S3Represent(lookup=tablename, fields=["title"])
        filter_id = S3ReusableField("filter_id", "reference %s" % tablename,
                                    label = T("Filter"),
                                    ondelete = "SET NULL",
                                    represent = represent,
                                    requires = IS_EMPTY_OR(
                                                IS_ONE_OF(
                                                    current.db, "pr_filter.id",
                                                    represent,
                                                    orderby="pr_filter.title",
                                                    sort=True,
                                                    )),
                                    )

        self.configure(tablename,
                       listadd = False,
                       list_fields = ["title",
                                      "resource",
                                      "url",
                                      "query",
                                      ],
                       list_layout = pr_filter_list_layout,
                       onvalidation = self.pr_filter_onvalidation,
                       orderby = "pr_filter.resource",
                       )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"pr_filter_id": filter_id,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def pr_filter_onvalidation(form):
        """
            Ensure that JSON can be loaded by json.loads()
        """

        query = form.vars.get("query", None)
        if query:
            query = query.replace("'", "\"")
            try:
                json.loads(query)
            except ValueError as e:
                form.errors.query = "%s: %s" % (current.T("Query invalid"), e)
            form.vars.query = query

# =============================================================================
class S3SubscriptionModel(S3Model):
    """
        Model for Subscriptions & hence Notifications
        http://eden.sahanafoundation.org/wiki/S3/Notifications
    """

    names = ("pr_subscription",
             "pr_subscription_resource",
             "pr_subscription_check_intervals",
             )

    def model(self):

        T = current.T
        UNKNOWN_OPT = current.messages.UNKNOWN_OPT

        trigger_opts = {
            "new": T("New Records"),
            "upd": T("Record Updates"),
        }

        frequency_opts = (
            ("immediately", T("Immediately")),
            ("hourly", T("Hourly")),
            ("daily", T("Daily")),
            ("weekly", T("Weekly")),
            ("never", T("Never")),
        )

        check_intervals = {
            "immediately": 5,
            "hourly": 60,
            "daily": 1440,
            "weekly": 10080,
            "never": 0
        }

        email_format_opts = {
            "text": T("Text"),
            "html": T("HTML")
        }

        MSG_CONTACT_OPTS = current.msg.MSG_CONTACT_OPTS
        FREQUENCY_OPTS = dict(frequency_opts)

        # ---------------------------------------------------------------------
        # Subscription (Settings)
        #
        tablename = "pr_subscription"
        self.define_table(tablename,
                          # Component not Instance
                          self.super_link("pe_id", "pr_pentity",
                                          represent = pr_PersonEntityRepresent(),
                                          ),
                          self.pr_filter_id(),
                          Field("notify_on", "list:string",
                                default = ["new"],
                                represent = S3Represent(options=trigger_opts,
                                                        multiple=True,
                                                        ),
                                requires = IS_IN_SET(trigger_opts,
                                                     multiple=True,
                                                     zero=None,
                                                     ),
                                widget = S3MultiSelectWidget(),
                                ),
                          Field("frequency",
                                default = "daily",
                                represent = lambda opt: \
                                            FREQUENCY_OPTS.get(opt,
                                                               UNKNOWN_OPT),
                                requires = IS_IN_SET(frequency_opts,
                                                     zero=None),
                                ),
                          Field("method", "list:string",
                                default = ["EMAIL"],
                                represent = S3Represent(options=MSG_CONTACT_OPTS,
                                                        multiple=True,
                                                        ),
                                requires = IS_IN_SET(MSG_CONTACT_OPTS,
                                                     multiple=True,
                                                     zero=None,
                                                     ),
                                widget = S3MultiSelectWidget(),
                                ),
                          Field("email_format",
                                represent = S3Represent(options=email_format_opts),
                                requires = IS_EMPTY_OR(
                                            IS_IN_SET(email_format_opts,
                                                      zero=None)),
                                ),
                          Field("attachment", "boolean",
                                default = False,
                                readable = False,
                                writable = False,
                                ),
                          s3_comments(),
                          *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Subscription"),
            title_display = T("Subscription Details"),
            title_list = T("Person Subscriptions"),
            title_update = T("Edit Subscription"),
            label_list_button = T("List Person Subscriptions"),
            label_delete_button = T("Delete Person Subscription"),
            msg_record_created = T("Subscription added"),
            msg_record_modified = T("Subscription updated"),
            msg_record_deleted = T("Subscription removed"),
            msg_list_empty = T("No Subscriptions currently registered")
            )

        list_fields = [(T("Person"), "pe_id"),
                       "notify_on",
                       "frequency",
                       "method",
                       ]

        self.configure(tablename,
                       list_fields = list_fields,
                       )

        self.add_components(tablename,
                            pr_subscription_resource = "subscription_id",
                            )

        # ---------------------------------------------------------------------
        # Subscription Resources (Subscriptions)
        # - a single Subscription Setting covers 1+ Resources
        # - these all share a common Filter, which can be a Context if-required
        #
        tablename = "pr_subscription_resource"
        self.define_table(tablename,
                          Field("subscription_id", "reference pr_subscription",
                                ondelete = "CASCADE",
                                ),
                          Field("resource"), # tablename
                          Field("url"), # "%s/%s" % (controller, function)
                          Field("auth_token", length=40,
                                readable = False,
                                writable = False,
                                ),
                          Field("locked", "boolean",
                                default = False,
                                readable = False,
                                writable = False,
                                ),
                          Field("batch_mode", "boolean",
                                default = True,
                                ),
                          Field("last_check_time", "datetime",
                                default = current.request.utcnow,
                                writable = False,
                                ),
                          Field("next_check_time", "datetime",
                                writable = False,
                                ),
                          *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"pr_subscription_check_intervals": check_intervals,
                }

# =============================================================================
# Representation Methods
# =============================================================================
def pr_get_entities(pe_ids=None,
                    types=None,
                    represent=True,
                    show_instance_type=True,
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
        @param show_instance_type: include instance type in representation
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

    pe_table = s3db.pr_pentity

    if pe_ids is None:
        pe_ids = []
    elif not isinstance(pe_ids, (list, set, tuple)):
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

        if show_instance_type:
            instance_type_nice = " (%s)" % type_repr(instance_type)
        else:
            instance_type_nice = ""

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
                    pe_str = "%s %s%s" % (s3_fullname(row),
                                          label,
                                          instance_type_nice)
                else:
                    pe_str = "%s%s" % (s3_fullname(row),
                                       instance_type_nice)
                repr_g[pe_id] = repr_f[pe_id] = pe_str

        elif "name" in table.fields:
            rows = db(query).select(table.pe_id,
                                    table.name)
            for row in rows:
                pe_id = row.pe_id
                if show_label and "pe_label" in table.fields:
                    label = labels.get(pe_id, None) or default_label
                    pe_str = "%s %s%s" % (row.name,
                                          label,
                                          instance_type_nice)
                else:
                    pe_str = "%s%s" % (row.name,
                                       instance_type_nice)
                repr_g[pe_id] = repr_f[pe_id] = pe_str

        else:
            for pe_id in pe_ids:
                label = labels.get(pe_id, None) or default_label
                pe_str = "[%s]%s" % (label,
                                     instance_type_nice)
                repr_g[pe_id] = repr_f[pe_id] = pe_str

    if represent:
        if group and as_list:
            return Storage([(t, list(repr_grp[t].values())) for t in repr_grp])
        elif group:
            return repr_grp
        elif as_list:
            return list(repr_flt.values())
        else:
            return repr_flt
    else:
        if group:
            return repr_grp
        else:
            return repr_all

# =============================================================================
class pr_RoleRepresent(S3Represent):
    """ Representations of pr_role IDs """

    def __init__(self,
                 show_link=False,
                 multiple=False,
                 translate=True):
        """
            Constructor

            @param show_link: whether to add a URL to representations
            @param multiple: web2py list-type (all values will be lists)
            @param translate: translate all representations (using T)
        """

        self.fields = ["pe_id", "role"]

        super(pr_RoleRepresent, self).__init__(lookup="pr_role",
                                               fields=self.fields,
                                               show_link=show_link,
                                               translate=translate,
                                               multiple=multiple)

    # ---------------------------------------------------------------------
    def represent_row(self,row):
        """
            Represent a Row

            @param row: the Row
        """

        entity = current.s3db.pr_pentity_represent(row.pe_id)
        return "%s: %s" % (entity, row.role)

    # ---------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=None):
        """
            Lookup all rows referenced by values.

            @param key: the key Field
            @param values: the values
            @param fields: the fields to retrieve
        """

        if not fields:
            table = self.table
            fields = [table[f] for f in self.fields]

        rows = super(pr_RoleRepresent, self).lookup_rows(key, values, fields=fields)

        # Bulk represent the pe_ids: this stores the representations
        # in current.s3db.pr_pentity_represent, thereby preventing
        # a row-by-row lookup when calling it from represent_row():
        pe_ids = [row.pe_id for row in rows]
        current.s3db.pr_pentity_represent.bulk(pe_ids)

        return rows

# =============================================================================
class pr_PersonEntityRepresent(S3Represent):

    def __init__(self,
                 # Bad default?
                 show_label=True,
                 default_label="[No ID Tag]",
                 show_type=True,
                 multiple=False,
                 show_link=False,
                 linkto=None,
                 ):
        """
            Constructor

            @param show_label: show the ID tag label for persons
            @param default_label: the default for the ID tag label
            @param show_type: show the instance_type
            @param multiple: assume a value list by default
        """

        self.show_label = show_label
        self.default_label = default_label
        self.show_type = show_type
        self.training_event_represent = None

        super(pr_PersonEntityRepresent, self).__init__(lookup="pr_pentity",
                                                       key="pe_id",
                                                       multiple=multiple,
                                                       show_link=show_link,
                                                       linkto=linkto,
                                                       )

    # -------------------------------------------------------------------------
    def link(self, k, v, row=None):
        """
            Represent a (key, value) as hypertext link.

                - Typically, k is a foreign key value, and v the
                  representation of the referenced record, and the link
                  shall open a read view of the referenced record.

                - The linkto-parameter expects a URL (as string) with "[id]"
                  as placeholder for the key.

            @param k: the key
            @param v: the representation of the key
            @param row: the row with this key
        """

        if not k:
            return v

        if self.linkto == URL(c="pr", f="pentity", args=["[id]"]):
            # Default linkto, so modify this to the instance type-specific URLs
            k = s3_unicode(k)
            db = current.db
            petable = db.pr_pentity
            pe_record = db(petable._id == k).select(petable.instance_type,
                                                    limitby=(0, 1)
                                                    ).first()
            if not pe_record:
                return v
            tablename = pe_record.instance_type
            prefix, name = tablename.split("_", 1)
            url = URL(c=prefix, f=name, args=["read"], vars={"~.pe_id": k})
            # Strip off any .aadata extension!
            url = url.replace(".aadata", "")
            return A(v, _href=url)
        else:
            # Custom linkto
            k = s3_unicode(k)
            return A(v, _href=self.linkto.replace("[id]", k) \
                                         .replace("%5Bid%5D", k))

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=None):
        """
            Custom rows lookup function

            @param key: the key field
            @param values: the values to look up
            @param fields: unused (retained for API compatibility)
        """

        db = current.db
        s3db = current.s3db

        instance_fields = {
            "pr_person": ["first_name", "middle_name", "last_name"],
        }

        # Get all super-entity rows
        etable = s3db.pr_pentity
        rows = db(key.belongs(values)).select(key,
                                              etable.pe_label,
                                              etable.instance_type)
        self.queries += 1

        keyname = key.name
        types = {}
        for row in rows:
            instance_type = row.instance_type
            if instance_type not in types:
                types[instance_type] = {row[keyname]: row}
            else:
                types[instance_type][row[keyname]] = row

        # Get all instance records (per instance type)
        results = []
        append = results.append
        for instance_type in types:

            table = s3db.table(instance_type)
            if not table:
                continue

            if instance_type == "hrm_training_event":
                training_event_represent = s3db.hrm_TrainingEventRepresent()
                training_event_represent._setup()
                rows = training_event_represent.lookup_rows(table[keyname],
                                                            values,
                                                            pe_id=True)
                self.training_event_represent = training_event_represent
            else:
                if instance_type in instance_fields:
                    qfields = [table[f]
                               for f in instance_fields[instance_type]
                               if f in table.fields]
                elif "name" in table.fields:
                    qfields = [table["name"]]
                else:
                    continue
                qfields.insert(0, table[keyname])

                query = (table[keyname].belongs(set(types[instance_type].keys())))
                rows = db(query).select(*qfields)
            self.queries += 1

            sdata = types[instance_type]
            # Construct a new Row which contains both, the super-entity
            # record and the instance record:
            if instance_type == "hrm_training_event":
                for row in rows:
                    append(Row(pr_pentity = sdata[row["hrm_training_event"][keyname]],
                               **{instance_type: row}))
            else:
                for row in rows:
                    append(Row(pr_pentity = sdata[row[keyname]],
                               **{instance_type: row}))

        return results

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a row

            @param row: the Row
        """

        pentity = row.pr_pentity
        instance_type = pentity.instance_type

        show_label = self.show_label
        if show_label:
            label = pentity.pe_label \
                    if pentity.pe_label else self.default_label
        else:
            label = ""

        item = object.__getattribute__(row, instance_type)
        if instance_type == "pr_person":
            pe_str = "%s %s" % (s3_fullname(item), label)
        elif instance_type == "hrm_training_event":
            pe_str = self.training_event_represent.represent_row(item)
        elif "name" in item:
            pe_str = s3_str(item["name"])
        else:
            pe_str = "[%s]" % label

        if self.show_type:
            etable = current.s3db.pr_pentity
            instance_type_nice = etable.instance_type.represent(instance_type)
            pe_str = "%s (%s)" % (pe_str,
                                  s3_str(instance_type_nice),
                                  )

        return pe_str

# =============================================================================
class pr_PersonRepresent(S3Represent):
    """
        Extends S3Represent to change the link method to access the person via
                            either HRM, Vol or PR controllers
    """

    def __init__(self,
                 lookup = "pr_person",
                 key = None,
                 fields = None,
                 labels = None,
                 options = None,
                 translate = False,
                 linkto = None,
                 show_link = False,
                 multiple = False,
                 default = None,
                 none = None):

        if show_link and not linkto:
            request = current.request
            group = request.get_vars.get("group", None)
            if group == "staff":
                controller = "hrm"
            elif group == "volunteer":
                controller = "vol"
            else:
                c = request.controller
                if c == "hrm":
                    controller = "hrm"
                elif c == "vol":
                    controller = "vol"
                elif c == "br":
                    controller = "br"
                elif c == "dvr":
                    controller = "dvr"
                else:
                    controller = "pr"
            linkto = URL(c=controller, f="person", args=["[id]"], extension="")

        if not fields:
            fields = ["first_name", "middle_name", "last_name"]

        if not labels:
            labels = s3_fullname

        super(pr_PersonRepresent, self).__init__(lookup,
                                                 key,
                                                 fields,
                                                 labels,
                                                 options,
                                                 translate,
                                                 linkto,
                                                 show_link,
                                                 multiple,
                                                 default,
                                                 none)

# =============================================================================
class pr_PersonRepresentContact(pr_PersonRepresent):
    """
        Extended representation of person IDs to include phone number
        and/or email address, using the highest-priority contact info
        available (and permitted)
    """

    def __init__(self,
                 labels = None,
                 linkto = None,
                 show_email = False,
                 show_phone = True,
                 access = None,
                 show_link = True,
                 ):
        """
            Constructor

            @param labels: callable to render the name part
                           (defaults to s3_fullname)
            @param linkto: a URL (as string) to link representations to,
                           with "[id]" as placeholder for the key
                           (defaults see pr_PersonRepresent)

            @param show_email: include email address in representation
            @param show_phone: include phone number in representation

            @param access: access level for contact details,
                           None = ignore access level
                           1 = show private only
                           2 = show public only

            @param show_link: render as HTML hyperlink
        """

        super(pr_PersonRepresentContact, self).__init__(
                                                 lookup = "pr_person",
                                                 labels = labels,
                                                 linkto = linkto,
                                                 show_link = show_link,
                                                 )

        self.show_email = show_email
        self.show_phone = show_phone
        self.access = access

        self._email = {}
        self._phone = {}

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a row

            @param row: the Row
        """

        reprstr = super(pr_PersonRepresentContact, self).represent_row(row)

        try:
            pe_id = row.pe_id
        except AttributeError:
            pass
        else:
            if self.show_email:
                email = self._email.get(pe_id)
                if email:
                    reprstr = "%s <%s>" % (reprstr, email)

            if self.show_phone:
                phone = self._phone.get(pe_id)
                if phone:
                    reprstr = "%s %s" % (reprstr, s3_phone_represent(phone))

        return reprstr

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=None):
        """
            Custom rows lookup

            @param key: the key Field
            @param values: the values
            @param fields: unused (retained for API compatibility)
        """

        # Lookup pe_ids and name fields
        db = current.db
        s3db = current.s3db

        table = self.table
        count = len(values)
        if count == 1:
            query = (key == values[0])
        else:
            query = key.belongs(values)

        rows = db(query).select(table.id,
                                table.pe_id,
                                table.first_name,
                                table.middle_name,
                                table.last_name,
                                limitby = (0, count),
                                )
        self.queries += 1

        lookup_phone = set()
        lookup_email = set()
        phone = self._phone
        email = self._email
        for row in rows:
            pe_id = row.pe_id
            if pe_id not in phone:
                lookup_phone.add(pe_id)
            if pe_id not in email:
                lookup_email.add(pe_id)

        ctable = s3db.pr_contact
        base = current.auth.s3_accessible_query("read", ctable)
        access = self.access
        if lookup_phone:
            join_on = base & \
                      (ctable.pe_id == table.pe_id) & \
                      (ctable.contact_method == "SMS") & \
                      (ctable.deleted == False)
            if access:
                join_on &= (ctable.access == access)
            left = ctable.on(join_on)
            query = (table.pe_id.belongs(lookup_phone))
            contacts = db(query).select(table.pe_id,
                                        ctable.value,
                                        left = left,
                                        orderby = ctable.priority,
                                        )
            self.queries += 1
            for contact in contacts:
                pe_id = contact.pr_person.pe_id
                if not phone.get(pe_id):
                    phone[pe_id] = contact.pr_contact.value

        if lookup_email:
            join_on = base & \
                      (ctable.pe_id == table.pe_id) & \
                      (ctable.contact_method == "EMAIL") & \
                      (ctable.deleted == False)
            if access:
                join_on &= (ctable.access == access)
            left = ctable.on(join_on)
            query = (table.pe_id.belongs(lookup_email))
            contacts = db(query).select(table.pe_id,
                                        ctable.value,
                                        left = left,
                                        orderby = ctable.priority,
                                        )
            self.queries += 1
            for contact in contacts:
                pe_id = contact.pr_person.pe_id
                if not email.get(pe_id):
                    email[pe_id] = contact.pr_contact.value

        return rows

# =============================================================================
class pr_GroupRepresent(S3Represent):
    """ Representation of person groups """

    def __init__(self):
        """ Constructor """

        super(pr_GroupRepresent, self).__init__("pr_group",
                                                fields = ["name"],
                                                )

        self.show_org_groups = current.deployment_settings \
                                      .get_org_group_team_represent()
        self.org_groups = {}

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=None):
        """
            Custom rows lookup

            @param key: the key Field
            @param values: the values
            @param fields: unused (retained for API compatibility)
        """

        db = current.db

        table = self.table
        count = len(values)
        if count == 1:
            query = (key == values[0])
        else:
            query = key.belongs(values)
        rows = db(query).select(table.id,
                                table.name,
                                limitby=(0, count),
                                )
        self.queries += 1

        if self.show_org_groups:
            # Look up all org_groups linked to these groups (second query
            # because it's a m2m link but the returned rows must not contain
            # duplicates)
            s3db = current.s3db
            ltable = s3db.org_group_team
            gtable = s3db.org_group

            left = gtable.on(ltable.org_group_id == gtable.id)
            group_id = ltable.group_id

            if count == 1:
                query = (group_id == values[0])
            else:
                query = group_id.belongs(values)
            query &= (ltable.deleted != True)

            org_group_name = gtable.name
            links = db(query).select(group_id,
                                     org_group_name,
                                     left=left,
                                     )
            self.queries += 1

            groups = self.org_groups
            for link in links:
                group = link[group_id]
                name = link[org_group_name]
                if name:
                    if group not in groups:
                        groups[group] = [name]
                    else:
                        groups[group].append(name)

        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a row

            @param row: the Row
        """

        representation = "%s" % row.name

        if self.show_org_groups:
            # Append the org_group names in parantheses
            names = self.org_groups.get(row.id)
            if names:
                representation = "%s (%s)" % (representation, ", ".join(names))

        return representation

# =============================================================================
class pr_ContactRepresent(S3Represent):

    def __init__(self,
                 show_link = True,
                 ):
        """
            Show a Contact with appropriate hyperlinks if Facebook or Twitter

            @param: see super
        """

        super(pr_ContactRepresent, self).__init__(lookup = "pr_contact",
                                                  fields = ["contact_method",
                                                            "value",
                                                            ],
                                                  show_link = show_link,
                                                  )

    # -------------------------------------------------------------------------
    def link(self, k, v, row=None):
        """
            Represent a (key, value) as hypertext link.

                - Typically, k is a foreign key value, and v the
                  representation of the referenced record, and the link
                  shall open a read view of the referenced record.

                - The linkto-parameter expects a URL (as string) with "[id]"
                  as placeholder for the key.

            @param k: the key
            @param v: the representation of the key
            @param row: the row with this key
        """

        if not k:
            return v

        if v.startswith("http"):
            return A(v, _href=v)

        contact_method = row.contact_method
        if contact_method == "TWITTER":
            url = "http://twitter.com/%s" % v
            return A(v, _href=url)
        elif contact_method == "FACEBOOK":
            url = "http://%s" % v
            return A(v, _href=url)
        else:
            # No link
            return v

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a row

            @param row: the Row
        """

        value = row["pr_contact.value"]
        if not value:
            return self.default

        return s3_str(value)

# =============================================================================
def pr_image_library_represent(image_name, format=None, size=None):
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
        return current.messages["NONE"]
    parts = url.split("/")
    image = parts[-1]
    size = (None, 60)
    image = pr_image_library_represent(image, size=size)
    url_small = URL(c="default", f="download", args=image)

    return DIV(A(IMG(_src=url_small, _height=60), _href=url))

# =============================================================================
def pr_person_comment(title=None, comment=None, caller=None, child=None):

    T = current.T
    if title is None:
        title = T("Person")
    if comment is None:
        comment = T("Type the first few characters of one of the Person's names.")
    if child is None:
        child = "person_id"
    get_vars = {"child": child}
    if caller:
        get_vars["caller"] = caller
    return S3PopupLink(c = "pr",
                       f = "person",
                       vars = get_vars,
                       title = current.messages.ADD_PERSON,
                       tooltip = "%s|%s" % (title, comment),
                       )

# =============================================================================
def pr_rheader(r, tabs=None):
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

                record_id = record.id
                pdtable = s3db.pr_person_details
                query = (pdtable.person_id == record_id)
                details = db(query).select(pdtable.nationality,
                                           limitby=(0, 1)).first()
                if details:
                    nationality = details.nationality
                else:
                    nationality = None

                rheader = DIV(
                    A(s3_avatar_represent(record_id,
                                          "pr_person",
                                          _class="rheader-avatar"),
                      _href=URL(f="person", args=[record_id, "image"],
                                vars = r.get_vars),
                      ),
                    TABLE(
                        TR(TH("%s: " % T("Name")),
                           s3_fullname(record),
                           TH("%s: " % T("ID Tag Number")),
                           "%(pe_label)s" % record
                           ),
                        TR(TH("%s: " % T("Date of Birth")),
                           "%s" % (record.date_of_birth or T("unknown")),
                           TH("%s: " % T("Gender")),
                           "%s" % s3db.pr_gender_opts.get(record.gender,
                                                          T("unknown"))
                           ),

                        TR(TH("%s: " % T("Nationality")),
                           "%s" % (pdtable.nationality.represent(nationality)),
                           TH("%s: " % T("Age")),
                           record.age()
                           ),
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
                                   leader,
                                   ),
                                TR(TH("%s: " % T("Description")),
                                   record.description or "",
                                   TH(""),
                                   "",
                                   )
                                ), rheader_tabs)

                return rheader

            elif tablename == "pr_forum":
                if not tabs:
                    title_display = current.response.s3.crud_strings["pr_forum"].title_display
                    tabs = [(title_display, None),
                            (T("Members"), "forum_membership"),
                            (T("Assign"), "assign"),
                            ]
                    rheader_tabs = s3_rheader_tabs(r, tabs)
                action = ""
                if current.deployment_settings.has_module("msg"):
                    permit = current.auth.permission.has_permission
                    if permit("update", c="pr", f="compose") and permit("update", c="msg"):
                        # @ToDo: Be able to see who has been messaged, whether messages bounced, receive confirmation responses, etc
                        action = A(T("Message Members"),
                                   _href = URL(f = "compose",
                                               vars = {"forum.id": record.id,
                                                       "pe_id": record.pe_id,
                                                       },
                                               ),
                                   _class = "action-btn send"
                                   )
                rheader = DIV(TABLE(
                                TR(TH("%s: " % T("Name")),
                                   record.name,
                                   ),
                                TR(TH("%s: " % T("Comments")),
                                   record.comments or "",
                                   TH(""),
                                   "",
                                   ),
                                TR(TH(action, _colspan=2)),
                                ), rheader_tabs)

                return rheader

    return None

# =============================================================================
def pr_nationality_opts():
    """
        Nationality options

        @returns: a sorted list of nationality options
    """

    T = current.T

    countries = current.gis.get_countries(key_type="code")
    opts = sorted(((k, T(countries[k])) for k in countries.keys()),
                  # NB applies server locale's sorting rules, not
                  #    the user's chosen language (not easily doable
                  #    in Python, would require pyICU or similar)
                  key=lambda x: s3_str(x[1]),
                  )

    # Stateless always last
    opts.append(("XX", T("Stateless")))

    # Allow to explicitly specify an "unclear" nationality?
    if current.deployment_settings.get_pr_nationality_explicit_unclear():
        opts.append(("??", T("unclear")))

    return opts

def pr_nationality_prepresent(code):
    """
        Representation of Nationality

        @param code: ISO2 country code

        @returns: T-translated name of the country
    """

    if code == "XX":
        return current.T("Stateless")
    elif code == "??":
        return current.T("unclear")
    else:
        country_name = current.gis.get_country(code, key_type="code")
        if country_name:
            return current.T(country_name)

    return current.messages.UNKNOWN_OPT

# =============================================================================
# Custom Resource Methods
# =============================================================================
#
class pr_AssignMethod(S3Method):
    """
        Custom Method to allow people to be assigned to something
        e.g. Team, Forum
    """

    def __init__(self,
                 component,
                 next_tab = None,
                 #types = None,
                 actions = None,
                 filter_widgets = None,
                 list_fields = None,
                 postprocess = None,
                 #rheader = None,
                 title = None,
                 ):
        """
            @param component: the Component in which to create records
            @param next_tab: the component/method to redirect to after assigning
            @param types: a list of types to pick from: Users
                          (Staff/Vols/Members to come as-required)
            @param actions: a custom list of Actions for the dataTable
            @param filter_widgets: a custom list of FilterWidgets to show
            @param list_fields: a custom list of Fields to show
            @param postprocess: name of a settings.tasks.<function> postprocess function to act on all assigned person_ids at once
            @param rheader: an rheader to show
            @param title: an alternative page title
        """

        self.component = component
        if next_tab:
            self.next_tab = next_tab
        else:
            self.next_tab = component
        #self.types = types
        self.actions = actions
        self.filter_widgets = filter_widgets
        self.list_fields = list_fields
        self.postprocess = postprocess
        #self.rheader = rheader
        self.title = title

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Apply method.

            @param r: the S3Request
            @param attr: controller options for this request
        """

        try:
            component = r.resource.components[self.component]
        except KeyError:
            current.log.error("Invalid Component!")
            raise

        if component.link:
            component = component.link

        tablename = component.tablename

        # Requires permission to create component
        authorised = current.auth.s3_has_permission("create", tablename)
        if not authorised:
            r.unauthorised()

        #settings = current.deployment_settings
        #types = self.types
        #if not types:
        #    if settings.has_module("vol"):
        #        types = (1, 2)
        #    else:
        #        # Staff
        #        types = (1,)
        #if types == (2,):
        #    controller = "vol"
        #else:
        #    controller = "hrm"
        USERS = tablename == "pr_forum_membership"
        controller = "pr"

        T = current.T
        db = current.db
        s3db = current.s3db

        table = s3db[tablename]
        fkey = component.fkey
        record = r.record
        if fkey in record:
            # SuperKey
            record_id = record[fkey]
        else:
            record_id = r.id

        get_vars = r.get_vars
        response = current.response

        if r.http == "POST":
            added = 0
            post_vars = r.post_vars
            if all([n in post_vars for n in ("assign", "selected", "mode")]):

                selected = post_vars.selected
                if selected:
                    selected = selected.split(",")
                else:
                    selected = []

                # Handle exclusion filter
                if post_vars.mode == "Exclusive":
                    if "filterURL" in post_vars:
                        filters = S3URLQuery.parse_url(post_vars.filterURL)
                    else:
                        filters = None
                    query = ~(FS("id").belongs(selected))
                    presource = s3db.resource("pr_person",
                                              alias = self.component,
                                              filter=query, vars=filters)
                    rows = presource.select(["id"], as_rows=True)
                    selected = [str(row.id) for row in rows]

                # Prevent multiple entries in the link table
                query = (table.person_id.belongs(selected)) & \
                        (table[fkey] == record_id) & \
                        (table.deleted != True)
                rows = db(query).select(table.id)
                rows = dict((row.id, row) for row in rows)
                onaccept = component.get_config("create_onaccept",
                                                component.get_config("onaccept", None))
                for person_id in selected:
                    try:
                        pr_id = int(person_id.strip())
                    except ValueError:
                        continue
                    if pr_id not in rows:
                        link = Storage(person_id = person_id)
                        link[fkey] = record_id
                        _id = table.insert(**link)
                        if onaccept:
                            link["id"] = _id
                            form = Storage(vars = link)
                            if not isinstance(onaccept, list):
                                onaccept = [onaccept]
                            for callback in onaccept:
                                callback(form)
                        added += 1
                if self.postprocess is not None:
                    # Run postprocess async as it may take some time to run
                    current.s3task.run_async("settings_task",
                                             args = [self.postprocess],
                                             vars = {"record": record.as_json(),
                                                     "selected": json.dumps(selected),
                                                     })

            if r.representation == "popup":
                # Don't redirect, so we retain popup extension & so close popup
                response.confirmation = T("%(number)s assigned") % \
                                            {"number": added}
                return {}
            else:
                current.session.confirmation = T("%(number)s assigned") % \
                                                    {"number": added}
                if added > 0:
                    redirect(URL(args=[r.id, self.next_tab], vars={}))
                else:
                    redirect(URL(args=r.args, vars={}))

        elif r.http == "GET":

            filter_widgets = self.filter_widgets
            #if filter_widgets is None: # provide a default

            # List fields
            list_fields = self.list_fields
            if list_fields is None:
                list_fields = ["id",
                               "first_name",
                               "middle_name",
                               "last_name",
                               ]
                if USERS:
                    db.auth_user.organisation_id.represent = s3db.org_OrganisationRepresent()
                    list_fields.append((current.messages.ORGANISATION, "user.organisation_id"))
                elif tablename == "event_human_resource":
                    list_fields.append((current.messages.ORGANISATION, "human_resource.organisation_id"))
                # @ToDo: be able to configure additional fields here, like:
                #if len(types) == 2:
                #    list_fields.append((T("Type"), "human_resource.type"))
                #list_fields.append("human_resource.job_title_id")
                #if settings.get_hrm_use_certificates():
                #    list_fields.append((T("Certificates"), "certification.certificate_id"))
                #if settings.get_hrm_use_skills():
                #    list_fields.append((T("Skills"), "competency.skill_id"))
                #if settings.get_hrm_use_trainings():
                #    list_fields.append((T("Trainings"), "training.course_id"))

            # Data table
            resource = s3db.resource("pr_person",
                                     alias = r.component.alias if r.component else None,
                                     vars = get_vars)
            totalrows = resource.count()
            if "pageLength" in get_vars:
                display_length = get_vars["pageLength"]
                if display_length == "None":
                    display_length = None
                else:
                    display_length = int(display_length)
            else:
                display_length = 25
            if display_length:
                limit = 4 * display_length
            else:
                limit = None
            filter_, orderby, left = resource.datatable_filter(list_fields,
                                                               get_vars)
            resource.add_filter(filter_)

            # Hide people already in the link table
            ptable = db.pr_person
            query = (table[fkey] == record_id) & \
                    (table.deleted != True)
            rows = db(query).select(table.person_id)
            already = [row.person_id for row in rows]
            filter_ = (~ptable.id.belongs(already))
            resource.add_filter(filter_)

            if USERS:
                # Restrict to just Users
                ltable = s3db.pr_person_user
                filter_ = (ptable.pe_id == ltable.pe_id)
                resource.add_filter(filter_)

            s3 = response.s3
            if s3.filter:
                resource.add_filter(s3.filter)

            dt_id = "datatable"

            # Bulk actions
            label = s3.crud.get("assign_button", "Assign")
            dt_bulk_actions = [(T(label), "assign")]

            if r.representation in ("html", "popup"):
                # Page load
                resource.configure(deletable = False)

                # Actions
                actions = self.actions
                if actions is None:
                    profile_url = URL(c = controller,
                                      f = "person",
                                      args = ["[id]", "profile"])
                    S3CRUD.action_buttons(r,
                                          deletable = False,
                                          read_url = profile_url,
                                          update_url = profile_url)
                    actions = s3.actions

                s3.no_formats = True

                # Filter form
                if filter_widgets:

                    # Where to retrieve filtered data from:
                    submit_url_vars = resource.crud._remove_filters(r.get_vars)
                    filter_submit_url = r.url(vars = submit_url_vars)

                    # Default Filters (before selecting data!)
                    resource.configure(filter_widgets = filter_widgets)
                    S3FilterForm.apply_filter_defaults(r, resource)

                    # Where to retrieve updated filter options from:
                    filter_ajax_url = URL(f="person",
                                          args = ["filter.options"],
                                          vars = {})

                    get_config = resource.get_config
                    filter_clear = get_config("filter_clear", True)
                    filter_formstyle = get_config("filter_formstyle", None)
                    filter_submit = get_config("filter_submit", True)
                    filter_form = S3FilterForm(filter_widgets,
                                               clear = filter_clear,
                                               formstyle = filter_formstyle,
                                               submit = filter_submit,
                                               ajax = True,
                                               url = filter_submit_url,
                                               ajaxurl = filter_ajax_url,
                                               _class = "filter-form",
                                               _id = "datatable-filter-form",
                                               )
                    fresource = current.s3db.resource(resource.tablename)
                    alias = r.component.alias if r.component else None
                    ff = filter_form.html(fresource,
                                          r.get_vars,
                                          target = "datatable",
                                          alias = alias)
                else:
                    ff = ""

                # Data table (items)
                data = resource.select(list_fields,
                                       start = 0,
                                       limit = limit,
                                       orderby = orderby,
                                       left = left,
                                       count = True,
                                       represent = True)
                filteredrows = data["numrows"]
                dt = S3DataTable(data["rfields"], data["rows"])
                items = dt.html(totalrows,
                                filteredrows,
                                dt_id,
                                dt_ajax_url = r.url(representation="aadata"),
                                dt_bulk_actions = dt_bulk_actions,
                                dt_pageLength = display_length,
                                dt_pagination = "true",
                                dt_row_actions = actions,
                                dt_searching = "false",
                                )

                response.view = "list_filter.html"

                return {"items": items,
                        "title": self.title or T("Assign People"),
                        "list_filter_form": ff,
                        }

            elif r.representation == "aadata":
                # Ajax refresh
                if "draw" in get_vars:
                    echo = int(get_vars.draw)
                else:
                    echo = None

                data = resource.select(list_fields,
                                       start = 0,
                                       limit = limit,
                                       orderby = orderby,
                                       left = left,
                                       count = True,
                                       represent = True)
                filteredrows = data["numrows"]
                dt = S3DataTable(data["rfields"], data["rows"])
                items = dt.json(totalrows,
                                filteredrows,
                                dt_id,
                                echo,
                                dt_bulk_actions = dt_bulk_actions)
                response.headers["Content-Type"] = "application/json"
                return items

            else:
                r.error(415, current.ERROR.BAD_FORMAT)
        else:
            r.error(405, current.ERROR.BAD_METHOD)

# =============================================================================
def pr_compose():
    """
        Send message to people/teams/forums

        @ToDo: Better rewritten as an S3Method
    """

    get_vars = current.request.get_vars
    #pe_id = None

    #if "person.id" in get_vars:
    #    # CCC uses a custom version for messaging Donors re: Donations
    #    fieldname = "person.id"
    #    record_id = get_vars.get(fieldname)
    #    table = current.s3db.pr_person
    #    title = current.T("Message Person")
    #    query = (table.id == record_id)
    #    # URL to redirect to after message sent
    #    url = URL(f="person", args=record_id)

    #elif "forum.id" in get_vars:
    if "forum.id" in get_vars:
        # Used by? WACOP?
        fieldname = "forum.id"
        record_id = get_vars.get(fieldname)
        pe_id = get_vars.pe_id
        title = current.T("Message Members")
        # URL to redirect to after message sent
        url = URL(f="forum", args=record_id)

    #elif "group.id" in get_vars:
    #    fieldname = "group.id"
    #    record_id = get_vars.get(fieldname)
    #    pe_id = get_vars.pe_id
    #    title = current.T("Message Members")
    #    # URL to redirect to after message sent
    #    url = URL(f="group", args=record_id)

    else:
        current.session.error = current.T("Record not found")
        redirect(URL(f="index"))

    #if not pe_id:
    #    db = current.db
    #    pe = db(query).select(table.pe_id,
    #                          limitby=(0, 1)).first()
    #    try:
    #        pe_id = pe.pe_id
    #    except:
    #        current.session.error = current.T("Record not found")
    #        redirect(URL(f="index"))

    # Create the form
    output = current.msg.compose(recipient = pe_id,
                                 url = url)

    output["title"] = title

    response = current.response
    representation = s3_get_extension()
    response.headers["Content-Type"] = \
        response.s3.content_type.get(representation, "text/html")
    response.view = "msg/compose.html"

    return output

# =============================================================================
class pr_Contacts(S3Method):
    """ Custom Method to edit person contacts """

    # Priority Order of Contact Methods
    PRIORITY = {"SMS": 1,
                "EMAIL": 2,
                "WORK_PHONE": 3,
                "HOME_PHONE": 4,
                "SKYPE": 5,
                "RADIO": 6,
                "TWITTER": 7,
                "FACEBOOK": 8,
                "WHATSAPP": 9,
                "FAX": 10,
                "OTHER": 11,
                "IRC": 12,
                "GITHUB": 13,
                "LINKEDIN": 14,
                "BLOG": 15,
                }

    def apply_method(self, r, **attr):
        """
            Entry point for REST API

            @param r: the S3Request
            @param attr: controller parameters for the request
        """

        if r.http != "GET":
            r.error(405, current.ERROR.BAD_METHOD)

        record = r.record
        if not record:
            r.error(404, current.ERROR.BAD_RECORD)

        # Permission to create new contacts?
        allow_create = current.auth.s3_has_permission("update", "pr_person",
                                                      record_id = record.id,
                                                      )

        # Single widget - hardcode the ID
        widget_id = "pr-contacts"

        # Render the subforms
        pe_id = record.pe_id
        contents = DIV(_id = widget_id,
                       _class = "pr-contacts-wrapper medium-8 small-12 columns",
                       )
        contacts = self.contacts(r,
                                 pe_id,
                                 allow_create=allow_create,
                                 method=r.method,
                                 )
        if contacts:
            contents.append(contacts)
        emergency = self.emergency(pe_id,
                                   allow_create=allow_create,
                                   )
        if emergency:
            contents.append(emergency)

        # Add the javascript
        response = current.response
        s3 = response.s3
        if s3.debug:
            s3.scripts.append(URL(c="static", f="scripts",
                                  args=["S3", "s3.ui.contacts.js"]))
        else:
            s3.scripts.append(URL(c="static", f="scripts",
                                  args=["S3", "s3.ui.contacts.min.js"]))

        # Widget options
        T = current.T
        if r.method == "private_contacts":
            access = 1
        elif r.method == "public_contacts":
            access = 2
        else:
            access = None
        widget_opts = {"controller": r.controller,
                       "personID": record.id,
                       "access": access,
                       "cancelButtonText": str(T("Cancel")),
                       }

        # Apply widget
        script = '''$("#%s").personcontacts(%s)''' % \
                 (widget_id, json.dumps(widget_opts))
        s3.jquery_ready.append(script)

        # Custom View
        response.view = "pr/contacts.html"

        title = self.crud_string(r.tablename, "title_display")

        return {"contents": contents, "title": title}

    # -------------------------------------------------------------------------
    @staticmethod
    def action_buttons(table, record_id):
        """ Action buttons for contact rows """

        T = current.T
        has_permission = current.auth.s3_has_permission

        if has_permission("update", table, record_id=record_id):
            edit_btn = A(T("Edit"), _class="edit-btn action-btn fright")
        else:
            edit_btn = SPAN()
        if has_permission("delete", table, record_id=record_id):
            delete_btn = A(T("Delete"), _class="delete-btn-ajax fright")
        else:
            delete_btn = SPAN()
        return DIV(delete_btn,
                   edit_btn,
                   DIV(_class="inline-throbber", _style="display:none"),
                   _class="pr-contact-actions medium-3 columns",
                   )

    # -------------------------------------------------------------------------
    def contacts(self, r, pe_id, allow_create=False, method="contacts"):
        """
            Contact Information Subform

            @param r: the S3Request
            @param pe_id: the pe_id
            @param allow_create: allow adding of new contacts
            @param method: the request method ("contacts", "private_contacts"
                           or "public_contacts")
        """

        T = current.T
        s3db = current.s3db

        tablename = "pr_contact"
        resource = s3db.resource(tablename,
                                 filter = FS("pe_id") == pe_id)

        # Filter by access
        if method != "contacts":
            if method == "private_contacts":
                access = FS("access") == 1
            else:
                access = FS("access") == 2
            resource.add_filter(access)

        # Retrieve the rows
        fields = ["id",
                  "priority",
                  "contact_description",
                  "value",
                  "contact_method",
                  "comments",
                  ]
        rows = resource.select(fields, orderby="pr_contact.priority").rows

        # Group by contact method and sort by priority
        from itertools import groupby
        groups = []
        gappend = groups.append
        method = lambda row: row["pr_contact.contact_method"]
        for key, group in groupby(rows, method):
            gappend((key, list(group)))
        PRIORITY = self.PRIORITY
        groups.sort(key = lambda item: PRIORITY.get(item[0], 99))

        # Start the form
        form = DIV(H2(T("Contacts")), _class="pr-contacts")

        # Add-button
        table = resource.table
        if allow_create and current.auth.s3_has_permission("create", table):
            add_btn = DIV(A(T("Add"),
                            _class="contact-add-btn action-btn",
                            ),
                          DIV(_class="throbber hide"),
                          )
            form.append(add_btn)

        # Use field.readable to hide fields if-required
        r.customise_resource(tablename)
        comments_readable = table.comments.readable
        description_readable = table.contact_description.readable
        priority_readable = table.priority.readable

        # Contact information by contact method
        opts = current.msg.CONTACT_OPTS
        action_buttons = self.action_buttons
        inline_edit_hint = T("Click to edit")
        for contact_method, contacts in groups:

            # Subtitle
            form.append(H3(opts[contact_method]))

            # Individual Rows
            for contact in contacts:

                contact_id = contact["pr_contact.id"]
                value = contact["pr_contact.value"]

                data = {"id": contact_id,
                        "value": value,
                        }

                if priority_readable:
                    priority = contact["pr_contact.priority"]
                    if priority:
                        data["priority"] = priority
                        priority_title = "%s - %s" % (T("Priority"), inline_edit_hint)
                        priority_field = SPAN(priority,
                                              _class = "pr-contact-priority",
                                              _title = priority_title,
                                              )
                    else:
                        priority_field = ""
                else:
                    priority_field = ""

                title = SPAN(value,
                             _title = inline_edit_hint,
                             _class = "pr-contact-value",
                             )

                if description_readable:
                    description = contact["pr_contact.contact_description"] or ""
                    if description:
                        data["description"] = description
                        title = TAG[""](SPAN(description,
                                             _title = inline_edit_hint,
                                             _class = "pr-contact-description",
                                             ),
                                        ", ",
                                        title,
                                        )

                if comments_readable:
                    comments = contact["pr_contact.comments"] or ""
                    data["comments"] = comments
                    comments = DIV(SPAN(comments,
                                        _title = inline_edit_hint,
                                        _class = "pr-contact-comments",
                                        ),
                                   _class = "pr-contact-subtitle",
                                   )
                else:
                    comments = DIV()

                actions = action_buttons(table, contact_id)
                form.append(DIV(DIV(priority_field,
                                    DIV(DIV(title,
                                            _class="pr-contact-title",
                                            ),
                                        comments,
                                        _class = "pr-contact-details",
                                        ),
                                    _class = "pr-contact-data medium-9 columns",
                                    ),

                                actions,
                                data = data,
                                _class="pr-contact row",
                                ))
        return form

    # -------------------------------------------------------------------------
    def emergency(self, pe_id, allow_create=False):
        """
            Emergency Contact Information SubForm

            @param pe_id: the pe_id
            @param allow_create: allow adding of new contacts

            @todo: make inline-editable this one too
        """

        if not current.deployment_settings.get_pr_show_emergency_contacts():
            return None

        T = current.T
        s3db = current.s3db

        # Retrieve the rows
        resource = s3db.resource("pr_contact_emergency",
                                 filter = FS("pe_id") == pe_id)
        table = resource.table
        fields = [f for f in ("name",
                              "relationship",
                              "address",
                              "phone",
                              "comments",
                              )
                    if table[f].readable]
        fields.insert(0, "id")
        rows = resource.select(fields).rows

        # Start the form
        form = DIV(H2(T("Emergency Contacts")),
                   _class="pr-emergency-contacts",
                   )

        # Add-button
        if allow_create and current.auth.s3_has_permission("create", table):
            add_btn = DIV(A(T("Add"),
                            _class="contact-add-btn action-btn",
                            ),
                          DIV(_class="throbber hide"),
                          )
            form.append(add_btn)

        # Individual rows
        readable_fields = fields[1:]
        action_buttons = self.action_buttons
        inline_edit_hint = T("Click to edit")
        for row in rows:
            contact_id = row["pr_contact_emergency.id"]

            # Render description and data
            data = {"id": contact_id}
            description = TAG[""](SPAN(row["pr_contact_emergency.name"],
                                       _title = inline_edit_hint,
                                       _class = "pr-emergency-name",
                                       ),
                                  )
            append = description.append
            for fieldname in ("relationship", "address", "phone"):
                if fieldname in readable_fields:
                    value = row["pr_contact_emergency.%s" % fieldname]
                    if value:
                        data[fieldname] = s3_unicode(value)
                        editable = SPAN(value,
                                        _title = inline_edit_hint,
                                        _class = "pr-emergency-%s" % fieldname,
                                        )
                        if fieldname == "relationship":
                            append(" (")
                            append(editable)
                            append(")")
                        else:
                            append(", ")
                            append(editable)

            # Render comments
            if "comments" in readable_fields:
                comments = row["pr_contact_emergency.comments"] or ""
                if comments:
                    data["comments"] = s3_unicode(comments)
            else:
                comments = ""

            actions = action_buttons(table, contact_id)
            form.append(DIV(DIV(DIV(description,
                                    _class="pr-contact-title",
                                    ),
                                DIV(SPAN(comments,
                                         _title = inline_edit_hint,
                                         _class = "pr-emergency-comments"),
                                    _class = "pr-contact-subtitle",
                                    ),
                                _class = "pr-emergency-data medium-9 columns",
                                ),
                            actions,
                            data = data,
                            _class="pr-emergency-contact row",
                            ))

        return form

# =============================================================================
class pr_Templates(S3Method):
    """
        Custom Method to select a Word Template to merge Person data into

        - used by DRKCM
    """

    def apply_method(self, r, **attr):
        """
            Apply method.

            @param r: the S3Request
            @param attr: controller options for this request
        """

        if r.http == "GET":
            if r.representation == "html":

                T = current.T
                s3db = current.s3db

                person_id = r.id

                root_org = s3db.org_root_organisation(current.auth.user.organisation_id)
                table = s3db.doc_document
                query = (table.organisation_id == root_org) & \
                        (table.is_template == True) & \
                        (table.deleted == False)
                templates = current.db(query).select(table.id,
                                                     table.name,
                                                     )
                if not templates:
                    buttons = P(T("No document templates found."))
                else:
                    buttons = UL()
                    bappend = buttons.append
                    for t in templates:
                        bappend(LI(A(t.name,
                                     #_class = "action-btn",
                                     _href = URL(args = [person_id, "template.docx"],
                                                 vars = {"template": t.id},
                                                 ),
                                     _target = "_top",
                                     )))

                output = {"title": "", #"%s:" % current.T("Select Template"),
                          "item": buttons,
                          }
                current.response.view = "plain.html"
                return output

            else:
                r.error(415, current.ERROR.BAD_FORMAT)
        else:
            r.error(405, current.ERROR.BAD_METHOD)

# =============================================================================
class pr_Template(S3Method):
    """
        Custom Method to merge Person data into a Word Template

        - used by DRKCM
    """

    def apply_method(self, r, **attr):
        """
            Apply method.

            @param r: the S3Request
            @param attr: controller options for this request
        """

        if r.http == "GET":
            if r.representation == "docx":

                T = current.T

                person_id = r.id
                if not person_id:
                    current.session.error = T("No Person selected")
                    redirect(URL(args = None))

                try:
                    from mailmerge import MailMerge
                except ImportError:
                    current.session.error = T("Need to install docx-mailmerge")
                    redirect(URL(args = person_id))

                # Find Template
                document_id = r.get_vars.get("template")
                if not document_id:
                    r.error(400, current.ERROR.BAD_REQUEST)

                table = current.s3db.doc_document
                template = current.db(table.id == document_id).select(table.file,
                                                                      table.name,
                                                                      limitby = (0, 1)
                                                                      ).first()

                template_path = os.path.join(r.folder, "uploads", template.file)

                # Extract Data
                resource = r.resource
                mailmerge_fields = current.deployment_settings.get_doc_mailmerge_fields()
                data = resource.select(list(mailmerge_fields.values()),
                                       represent = True,
                                       show_links = False,
                                       )
                record = data.rows[0]
                rfields = {rfield.selector: rfield for rfield in data.rfields}

                # Format Data
                NONE = current.messages["NONE"]
                prefix = resource.prefix_selector

                doc_data = {}
                for key, selector in mailmerge_fields.items():
                    if selector == "current_user.name":
                        user = current.auth.user
                        if user:
                            username = s3_format_fullname(fname = user.first_name,
                                                          lname = user.last_name,
                                                          )
                        else:
                            username = current.T("Unknown User")
                        doc_data[key] = s3_unicode(username)
                    else:
                        rfield = rfields.get(prefix(selector))
                        if rfield:
                            value = record[rfield.colname]
                            doc_data[key] = s3_unicode(value)
                        else:
                            doc_data[key] = NONE

                # Merge
                filename = "%s_%s.docx" % (template.name, person_id)
                with MailMerge(template_path) as document:
                    document.merge(**doc_data)
                    document.write(filename)

                # Output
                from gluon.contenttype import contenttype
                from gluon.streamer import DEFAULT_CHUNK_SIZE

                # Response headers
                disposition = "attachment; filename=\"%s\"" % filename
                response = current.response
                response.headers["Content-Type"] = contenttype(".docx")
                response.headers["Content-disposition"] = disposition

                stream = open(filename, "rb")
                return response.stream(stream, chunk_size=DEFAULT_CHUNK_SIZE,
                                       request=r)

            else:
                r.error(415, current.ERROR.BAD_FORMAT)
        else:
            r.error(405, current.ERROR.BAD_METHOD)

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

    if rtype == "hrm_human_resource":

        # Get the HR record
        htable = current.s3db.hrm_human_resource
        if not isinstance(record, Row):
            record = current.db(htable.id == record).select(htable.deleted_fk,
                                                            htable.person_id,
                                                            limitby=(0, 1)
                                                            ).first()
        if not record:
            return

        # Find the person_id to update
        person_id = record.person_id
        if person_id:
            pr_human_resource_update_affiliations(person_id)
        elif hasattr(record, "deleted_fk"):
            deleted_fk = record.deleted_fk
            if deleted_fk:
                try:
                    deleted_fk = json.loads(deleted_fk)
                except JSONERRORS:
                    pass
                else:
                    person_id = deleted_fk.get("person_id")
            if person_id:
                pr_human_resource_update_affiliations(person_id)

    elif rtype == "pr_group_membership":

        mtable = current.s3db.pr_group_membership
        if not isinstance(record, Row):
            record = current.db(mtable.id == record).select(mtable.deleted,
                                                            mtable.deleted_fk,
                                                            mtable.person_id,
                                                            limitby=(0, 1)
                                                            ).first()
        if not record:
            return
        pr_group_update_affiliations(record)

    elif rtype in ("org_group_membership",
                   "org_organisation_branch",
                   "org_organisation_team",
                   "org_site") or \
         rtype in current.auth.org_site_types:
        # Hierarchy methods in org.py:
        current.s3db.org_update_affiliations(table, record)

    # @ToDo
    #elif rtype == "member_membership":

    #    mtable = current.s3db.member_membership
    #    if not isinstance(record, Row):
    #        record = current.db(mtable.id == record).select(mtable.ALL,
    #                                                        limitby=(0, 1)
    #                                                        ).first()
    #    if not record:
    #        return
    #    pr_member_update_affiliations(record)

    return

# =============================================================================
def pr_group_update_affiliations(record):
    """
        Update affiliations for group memberships, currently this makes
        all members of a group organisational units of the group.

        @param record: the pr_group_membership record
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
    gtable = s3db.pr_group
    mtable = db.pr_group_membership
    ptable = db.pr_person
    etable = s3db.pr_pentity
    rtable = db.pr_role
    atable = db.pr_affiliation

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
def pr_human_resource_update_affiliations(person_id):
    """
        Update all affiliations related to the HR records of a person

        @param person_id: the person record ID
    """

    STAFF = "Staff"
    VOLUNTEER = "Volunteer"

    db = current.db
    s3db = current.s3db
    etable = s3db.pr_pentity
    rtable = db.pr_role
    atable = db.pr_affiliation
    htable = s3db.hrm_human_resource
    ptable = db.pr_person
    stable = s3db.org_site
    otable = db.org_organisation

    h = htable._tablename
    s = stable._tablename
    o = otable._tablename
    r = rtable._tablename
    #e = etable._tablename

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
    #vol_role = current.deployment_settings.get_hrm_vol_affiliation() or OTHER_ROLE
    role_type = OU
    for role in masters:
        #if role == VOLUNTEER:
        #    #role_type = vol_role
        #    role_type = OTHER_ROLE
        #else:
        #    role_type = OU
        for m in masters[role]:
            pr_add_affiliation(m, pe_id, role=role, role_type=role_type)

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
        row = current.db(query).select(rtable.id,
                                       limitby=(0, 1)).first()
        if not row:
            data = {"pe_id": master_pe,
                    "role": role,
                    "role_type": role_type,
                    }
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

        @return: the PE-ID
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
    elif isinstance(entity, INTEGER_TYPES) or \
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

        @return: the role ID
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

    resource = current.s3db.resource("pr_role", id=role_id)
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
    affiliation = current.db(query).select(atable.id,
                                           limitby=(0, 1)).first()
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
    affiliation = current.db(query).select(atable.id,
                                           limitby=(0, 1)).first()
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

        @return: a Storage() of S3MultiPaths with the role names as keys

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

    rows = current.db(query).select(rtable.role,
                                    rtable.path,
                                    rtable.pe_id)

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

        @return: a list of PE-IDs

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
    branches = pr_get_descendants(nodes, entity_types=entity_type)

    return result + branches

# =============================================================================
def pr_get_path(pe_id):
    """
        Get all ancestor paths of a person entity

        @param pe_id: the person entity ID

        @return: an S3MultiPath instance
    """

    s3db = current.s3db
    atable = s3db.pr_affiliation
    rtable = s3db.pr_role
    query = (atable.deleted != True) & \
            (atable.role_id == rtable.id) & \
            (atable.pe_id == pe_id) & \
            (rtable.deleted != True) & \
            (rtable.role_type == OU)
    roles = current.db(query).select(rtable.id,
                                     rtable.pe_id,
                                     rtable.path,
                                     rtable.role_type)
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

        @return: a list of PE-IDs
    """

    s3db = current.s3db
    atable = s3db.pr_affiliation
    rtable = s3db.pr_role
    query = (atable.deleted != True) & \
            (atable.role_id == rtable.id) & \
            (atable.pe_id == pe_id) & \
            (rtable.deleted != True) & \
            (rtable.role_type == OU)

    roles = current.db(query).select(rtable.id,
                                     rtable.pe_id,
                                     rtable.path,
                                     rtable.role_type)
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
def pr_instance_type(pe_id):
    """
        Get the instance type for a PE

        @param pe_id: the PE ID
    """

    if pe_id:
        etable = current.s3db.pr_pentity
        row = current.db(etable.pe_id == pe_id).select(etable.instance_type,
                                                       limitby=(0, 1)).first()
        if row:
            return row.instance_type
    return None

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

    s3db = current.s3db
    atable = s3db.pr_affiliation
    rtable = s3db.pr_role
    ltable = s3db.pr_person_user

    auth_settings = current.auth.settings
    utable = auth_settings.table_user
    userfield = auth_settings.login_userfield

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
    rows = current.db(query).select(utable.id, utable[userfield])
    if rows:
        return Storage([(row.id, row[userfield]) for row in rows])
    else:
        return Storage()

# =============================================================================
def pr_ancestors(entities):
    """
        Find all ancestor entities of the given entities in the
        OU hierarchy.

        @param entities:

        @return: Storage of lists of PE-IDs
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
    rows = current.db(query).select(rtable.id,
                                    rtable.pe_id,
                                    rtable.path,
                                    rtable.role_type,
                                    atable.pe_id)
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
def pr_descendants(pe_ids, skip=None, root=True):
    """
        Find descendant entities of a person entity in the OU hierarchy
        (performs a real search, not a path lookup), grouped by root PE

        @param pe_ids: set/list of pe_ids
        @param skip: list of person entity IDs to skip during
                     descending (internal)
        @param root: this is the top-node (internal)

        @return: a dict of lists of descendant PEs per root PE
    """

    if skip is None:
        skip = set()

    # We still need to support Py 2.6
    #pe_ids = {i for i in pe_ids if i not in skip}
    pe_ids = set(i for i in pe_ids if i not in skip)
    if not pe_ids:
        return {}

    s3db = current.s3db
    etable = s3db.pr_pentity
    rtable = s3db.pr_role
    atable = s3db.pr_affiliation

    q = (rtable.pe_id.belongs(pe_ids)) \
        if len(pe_ids) > 1 else (rtable.pe_id == list(pe_ids)[0])

    query = (q & (rtable.role_type == OU) & (rtable.deleted != True)) & \
            ((atable.role_id == rtable.id) & (atable.deleted != True)) & \
            (etable.pe_id == atable.pe_id)

    rows = current.db(query).select(rtable.pe_id,
                                    atable.pe_id,
                                    etable.instance_type)
    r = rtable._tablename
    e = etable._tablename
    a = atable._tablename

    nodes = set()
    ogetattr = object.__getattribute__

    result = {}

    skip.update(pe_ids)
    for row in rows:

        parent = ogetattr(ogetattr(row, r), "pe_id")
        child = ogetattr(ogetattr(row, a), "pe_id")
        instance_type = ogetattr(ogetattr(row, e), "instance_type")
        if instance_type != "pr_person":
            if parent not in result:
                result[parent] = []
            result[parent].append(child)
        if child not in skip:
            nodes.add(child)

    if nodes:
        descendants = pr_descendants(nodes, skip=skip, root=False)
        for child, nodes in descendants.items():
            for parent, children in result.items():
                if child in children:
                    for node in nodes:
                        if node not in children:
                            children.append(node)
    if root:
        for child, nodes in result.items():
            for parent, children in result.items():
                if child in children:
                    for node in nodes:
                        if node not in children and node != parent:
                            children.append(node)

    return result

# =============================================================================
def pr_get_descendants(pe_ids, entity_types=None, skip=None, ids=True):
    """
        Find descendant entities of a person entity in the OU hierarchy
        (performs a real search, not a path lookup).

        @param pe_ids: person entity ID or list of IDs
        @param entity_types: optional filter to a specific entity_type
        @param ids: whether to return a list of ids or nodes (internal)
        @param skip: list of person entity IDs to skip during
                     descending (internal)

        @return: a list of PE-IDs
    """

    if not pe_ids:
        return []
    if type(pe_ids) is not set:
        pe_ids = set(pe_ids) \
                 if isinstance(pe_ids, (list, tuple)) else {pe_ids}

    db = current.db
    s3db = current.s3db
    etable = s3db.pr_pentity
    rtable = db.pr_role
    atable = db.pr_affiliation

    if skip is None:
        skip = set()
    skip.update(pe_ids)

    if len(pe_ids) > 1:
        q = (rtable.pe_id.belongs(pe_ids))
    else:
        q = (rtable.pe_id == list(pe_ids)[0])

    query = ((rtable.deleted != True) & q & (rtable.role_type == OU)) & \
            ((atable.deleted != True) & (atable.role_id == rtable.id))

    if entity_types is not None:
        query &= (etable.pe_id == atable.pe_id)
        rows = db(query).select(etable.pe_id, etable.instance_type)
        # We still need to support Py 2.6
        #result = {(r.pe_id, r.instance_type) for r in rows}
        result = set((r.pe_id, r.instance_type) for r in rows)
        # We still need to support Py 2.6
        #node_ids = {i for i, t in result if i not in skip}
        node_ids = set(i for i, t in result if i not in skip)
    else:
        rows = db(query).select(atable.pe_id)
        # We still need to support Py 2.6
        #result = {r.pe_id for r in rows}
        result = set(r.pe_id for r in rows)
        # We still need to support Py 2.6
        #node_ids = {i for i in result if i not in skip}
        node_ids = set(i for i in result if i not in skip)
    # Recurse
    if node_ids:
        descendants = pr_get_descendants(node_ids,
                                         skip=skip,
                                         entity_types=entity_types,
                                         ids=False)
        result.update(descendants)

    if ids:
        if entity_types is not None:
            if type(entity_types) is not set:
                if not isinstance(entity_types, (tuple, list)):
                    entity_types = {entity_types}
                else:
                    entity_types = set(entity_types)
            return [n[0] for n in result if n[1] in entity_types]
        else:
            return list(result)
    else:
        return result

# =============================================================================
# Internal Path Tools
# =============================================================================
def pr_rebuild_path(pe_id, clear=False):
    """
        Rebuild the ancestor path of all roles in the OU hierarchy a person
        entity defines.

        @param pe_id: the person entity ID
        @param clear: clear paths in descendant roles (triggers lazy rebuild)
    """

    if isinstance(pe_id, Row):
        pe_id = pe_id.pe_id

    rtable = current.s3db.pr_role
    query = (rtable.pe_id == pe_id) & \
            (rtable.role_type == OU) & \
            (rtable.deleted != True)
    db = current.db
    db(query).update(path=None)
    roles = db(query).select(rtable.id,
                             rtable.pe_id,
                             rtable.path,
                             rtable.role_type)
    for role in roles:
        if role.path is None:
            pr_role_rebuild_path(role, clear=clear)

# =============================================================================
def pr_role_rebuild_path(role_id, skip=None, clear=False):
    """
        Rebuild the ancestor path of a role within the OU hierarchy

        @param role_id: the role ID
        @param skip: list of role IDs to skip during recursion
        @param clear: clear paths in descendant roles (triggers lazy rebuild)
    """

    if skip is None:
        skip = set()

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
    skip.add(role_id)

    if role.role_type != OU:
        path = None
    else:
        # Get all parent roles
        query = (atable.pe_id == pe_id) & \
                (atable.deleted != True) & \
                (rtable.deleted != True) & \
                (rtable.id == atable.role_id) & \
                (rtable.role_type == OU)
        parent_roles = db(query).select(rtable.id,
                                        rtable.pe_id,
                                        rtable.path,
                                        rtable.role_type)

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

        @ToDo: Move this function to Doc? (however - operates on a PR table)
    """

    # Import the specialist libraries
    try:
        from PIL import Image
        PILImported = True
    except ImportError:
        try:
            import Image
            PILImported = True
        except ImportError:
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
        try:
            im.thumbnail(thumb_size, Image.ANTIALIAS)
        except IOError:
            # Maybe need to reinstall pillow:
            #pip uninstall pillow
            #apt-get install libjpeg-dev
            #pip install pillow
            import sys
            msg = sys.exc_info()[1]
            current.log.error(msg)
            current.session.error = msg
            return

        if not to_format:
            to_format = fileExtension[1:]
        if to_format.upper() == "JPG":
            to_format = "JPEG"
        elif to_format.upper() == "BMP":
            im = im.convert("RGB")
        save_im_name = "%s.%s" % (fileName, to_format)
        tempFile = TemporaryFile()
        im.save(tempFile, to_format)
        tempFile.seek(0)
        newfile = table.new_name.store(tempFile,
                                       save_im_name,
                                       table.new_name.uploadfolder)
        # rewind the original file so it can be read, if required
        image_file.seek(0)
        table.insert(original_name = image_name,
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

# =============================================================================
def pr_availability_filter(r):
    """
        Filter requested resource (hrm_human_resource or pr_person) for
        availability during a selected interval
            - uses special filter selector "available" from GET vars
            - called from prep of the respective controller
            - adds resource filter for r.resource

        @param r: the S3Request
    """

    get_vars = r.get_vars

    # Parse start/end date
    calendar = current.calendar
    start = get_vars.pop("available__ge", None)
    if start:
        start = calendar.parse_datetime(start)
    end = get_vars.pop("available__le", None)
    if end:
        end = calendar.parse_datetime(end)

    utable = current.s3db.pr_unavailability

    # Construct query for unavailability
    query = (utable.deleted == False)
    if start and end:
        query &= ((utable.start_date >= start) & (utable.start_date <= end)) | \
                 ((utable.end_date >= start) & (utable.end_date <= end)) | \
                 ((utable.start_date < start) & (utable.end_date > end))
    elif start:
        query &= (utable.end_date >= start) | (utable.start_date >= start)
    elif end:
        query &= (utable.start_date <= end) | (utable.end_date <= end)
    else:
        return

    # Get person_ids of unavailability-entries
    rows = current.db(query).select(utable.person_id,
                                    groupby = utable.person_id,
                                    )
    if rows:
        person_ids = set(row.person_id for row in rows)

        # Filter r.resource for non-match
        if r.tablename == "hrm_human_resource":
            r.resource.add_filter(~(FS("person_id").belongs(person_ids)))
        elif r.tablename == "pr_person":
            r.resource.add_filter(~(FS("id").belongs(person_ids)))

# =============================================================================
def pr_import_prep(data):
    """
        Called when contacts are imported from CSV

        Lookups Pseudo-reference Integer fields from Names
        i.e. pr_contact.pe_id from <Org Name>

        Based on auth.s3_import_prep

        @ToDo: Add support for Sites
    """

    db = current.db
    s3db = current.s3db
    set_record_owner = current.auth.s3_set_record_owner
    update_super = s3db.update_super
    table = s3db.org_organisation

    tree = data[1]

    # Memberships
    elements = tree.getroot().xpath("/s3xml//resource[@name='pr_contact']/data[@field='pe_id']")
    looked_up = {}
    for element in elements:
        org = element.text

        if not org:
            continue

        if org in looked_up:
            # Replace string with pe_id
            element.text = looked_up[org]
            # Don't check again
            continue

        record = db(table.name == org).select(table.pe_id,
                                              limitby=(0, 1)
                                              ).first()
        if not record:
            # Add a new record
            record_id = table.insert(**{"name": org})
            update_super(table, Storage(id=record_id))
            set_record_owner(table, record_id)
            record = db(table.id == record_id).select(table.pe_id,
                                                      limitby=(0, 1)).first()
        pe_id = record.pe_id
        # Replace string with pe_id
        element.text = str(pe_id)
        # Store in case we get called again with same value
        looked_up[org] = pe_id

# =============================================================================
def pr_address_list_layout(list_id, item_id, resource, rfields, record):
    """
        Default dataList item renderer for Addresses on the HRM Profile

        @param list_id: the HTML ID of the list
        @param item_id: the HTML ID of the item
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
    """

    record_id = record["pr_address.id"]
    item_class = "thumbnail"

    raw = record._row
    title = record["pr_address.type"]
    comments = raw["pr_address.comments"] or ""

    addr_street = raw["gis_location.addr_street"] or ""
    if addr_street:
        addr_street = P(ICON("home"),
                        " ",
                        SPAN(addr_street),
                        " ",
                        _class="card_1_line",
                        )

    addr_postcode = raw["gis_location.addr_postcode"] or ""
    if addr_postcode:
        addr_postcode = P(ICON("mail"),
                          " ",
                          SPAN(addr_postcode),
                          " ",
                          _class="card_1_line",
                          )
    locations = []
    for level in ("L5", "L4", "L3", "L2", "L1", "L0"):
        l = raw.get("gis_location.%s" % level, None)
        if l:
            locations.append(l)
    if len(locations):
        location = " | ".join(locations)
        location = P(ICON("globe"),
                     " ",
                     SPAN(location),
                     " ",
                     _class="card_1_line",
                     )
    else:
        location = ""

    # Edit Bar
    permit = current.auth.s3_has_permission
    table = current.s3db.pr_address
    if permit("update", table, record_id=record_id):
        edit_btn = A(ICON("edit"),
                     _href=URL(c="pr", f="address",
                               args=[record_id, "update.popup"],
                               vars={"refresh": list_id,
                                     "record": record_id}),
                     _class="s3_modal",
                     _title=current.T("Edit Address"),
                     )
    else:
        edit_btn = ""
    if permit("delete", table, record_id=record_id):
        delete_btn = A(ICON("delete"),
                       _class="dl-item-delete",
                       )
    else:
        delete_btn = ""
    edit_bar = DIV(edit_btn,
                   delete_btn,
                   _class="edit-bar fright",
                   )

    # Render the item
    item = DIV(DIV(ICON("icon"), # Placeholder only
                   SPAN(" %s" % title,
                        _class="card-title"),
                   edit_bar,
                   _class="card-header",
                   ),
               DIV(DIV(DIV(addr_street,
                           addr_postcode,
                           location,
                           P(SPAN(comments),
                             " ",
                             _class="card_manylines",
                             ),
                           _class="media",
                           ),
                       _class="media-body",
                       ),
                   _class="media",
                   ),
               _class=item_class,
               _id=item_id,
               )

    return item

# =============================================================================
def pr_contact_list_layout(list_id, item_id, resource, rfields, record):
    """
        Default dataList item renderer for Contacts on the HRM Profile

        @param list_id: the HTML ID of the list
        @param item_id: the HTML ID of the item
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
    """

    record_id = record["pr_contact.id"]
    item_class = "thumbnail"

    raw = record._row
    title = record["pr_contact.contact_method"]
    contact_method = raw["pr_contact.contact_method"]
    value = record["pr_contact.value"]
    comments = raw["pr_contact.comments"] or ""

    # Edit Bar
    permit = current.auth.s3_has_permission
    table = current.s3db.pr_contact
    if permit("update", table, record_id=record_id):
        edit_btn = A(ICON("edit"),
                     _href=URL(c="pr", f="contact",
                               args=[record_id, "update.popup"],
                               vars={"refresh": list_id,
                                     "record": record_id}),
                     _class="s3_modal",
                     _title=current.T("Edit Contact"),
                     )
    else:
        edit_btn = ""
    if permit("delete", table, record_id=record_id):
        delete_btn = A(ICON("delete"),
                       _class="dl-item-delete",
                       )
    else:
        delete_btn = ""
    edit_bar = DIV(edit_btn,
                   delete_btn,
                   _class="edit-bar fright",
                   )

    if contact_method in("SMS", "HOME_PHONE", "WORK_PHONE"):
        icon = "phone"
    elif contact_method == "EMAIL":
        icon = "mail"
    elif contact_method == "SKYPE":
        icon = "skype"
    elif contact_method == "FACEBOOK":
        icon = "facebook"
    elif contact_method == "TWITTER":
        icon = "twitter"
    elif contact_method == "RADIO":
        icon = "microphone"
    elif contact_method == "RSS":
        icon = "rss"
    else:
        icon = "other"
    # Render the item
    item = DIV(DIV(ICON("icon"), # Placeholder only
                   SPAN(" %s" % title,
                        _class="card-title"),
                   edit_bar,
                   _class="card-header",
                   ),
               DIV(DIV(DIV(P(ICON(icon),
                             " ",
                             SPAN(value),
                             " ",
                             _class="card_1_line",
                             ),
                           P(SPAN(comments),
                             " ",
                             _class="card_manylines",
                             ),
                           _class="media",
                           ),
                       _class="media-body",
                       ),
                   _class="media",
                   ),
               _class=item_class,
               _id=item_id,
               )

    return item

# =============================================================================
class pr_EmergencyContactListLayout(S3DataListLayout):
    """ Datalist layout for emergency contacts """

    ICONS = {"phone": "phone",
             "address": "home",
             "relationship": "user",
             }

    # -------------------------------------------------------------------------
    def render_header(self, list_id, item_id, resource, rfields, record):
        """
            Render the card header

            @param list_id: the HTML ID of the list
            @param item_id: the HTML ID of the item
            @param resource: the S3Resource to render
            @param rfields: the S3ResourceFields to render
            @param record: the record as dict
        """

        header = DIV(ICON("icon"),
                     SPAN(record["pr_contact_emergency.name"],
                          _class="card-title",
                          ),
                     _class="card-header",
                     )

        toolbox = self.render_toolbox(list_id, resource, record)
        if toolbox:
            header.append(toolbox)

        return header

    # -------------------------------------------------------------------------
    def render_body(self, list_id, item_id, resource, rfields, record):
        """
            Render the card body

            @param list_id: the HTML ID of the list
            @param item_id: the HTML ID of the item
            @param resource: the S3Resource to render
            @param rfields: the S3ResourceFields to render
            @param record: the record as dict
        """

        body = DIV(_class="media")
        append = body.append

        fields = ("pr_contact_emergency.relationship",
                  "pr_contact_emergency.phone",
                  "pr_contact_emergency.address",
                  "pr_contact_emergency.comments",
                  )

        render_column = self.render_column
        for rfield in rfields:
            if rfield.colname in fields:
                column = render_column(item_id, rfield, record)
                if column:
                    append(column)
        return DIV(DIV(body, _class="media-body"), _class="media")

    # -------------------------------------------------------------------------
    def render_column(self, item_id, rfield, record):
        """
            Render a column of the record

            @param list_id: the HTML ID of the list
            @param rfield: the S3ResourceField
            @param record: the record as dict
        """

        value = record[rfield.colname]
        if value:
            if rfield.ftype == "text":
                _class = "card_manylines"
            else:
                _class = "card_1_line"
            return P(ICON(self.ICONS.get(rfield.fname, "icon")),
                     SPAN(value),
                     _class=_class,
                     )
        else:
            return None

    # -------------------------------------------------------------------------
    def render_toolbox(self, list_id, resource, record):
        """
            Render the toolbox

            @param list_id: the HTML ID of the list
            @param resource: the S3Resource to render
            @param record: the record as dict
        """

        table = resource.table
        tablename = resource.tablename
        record_id = record[str(resource._id)]

        toolbox = DIV(_class="edit-bar fright")

        update_url = URL(c="pr",
                         f="contact_emergency",
                         args=[record_id, "update.popup"],
                         vars={"refresh": list_id,
                               "record": record_id,
                               "profile": self.profile,
                               },
                         )

        has_permission = current.auth.s3_has_permission
        crud_string = S3Method.crud_string

        if has_permission("update", table, record_id=record_id):
            btn = A(ICON("edit"),
                    _href=update_url,
                    _class="s3_modal",
                    _title=crud_string(tablename, "title_update"))
            toolbox.append(btn)

        if has_permission("delete", table, record_id=record_id):
            btn = A(ICON("delete"),
                    _class="dl-item-delete",
                    _title=crud_string(tablename, "label_delete_button"))
            toolbox.append(btn)

        return toolbox

# =============================================================================
class pr_PersonListLayout(S3DataListLayout):
    """ Datalist layout for emergency contacts """

    ICONS = {"date_of_birth": "calendar",
             "male": "male",
             "female": "female",
             "nationality": "globe",
             "blood_type": "medical",
             }

    # -------------------------------------------------------------------------
    def render_header(self, list_id, item_id, resource, rfields, record):
        """
            Render the card header

            @param list_id: the HTML ID of the list
            @param item_id: the HTML ID of the item
            @param resource: the S3Resource to render
            @param rfields: the S3ResourceFields to render
            @param record: the record as dict
        """

        raw = record._row
        fullname = s3_format_fullname(raw["pr_person.first_name"],
                                      raw["pr_person.middle_name"],
                                      raw["pr_person.last_name"],
                                      )
        header = DIV(ICON("icon"),
                     SPAN(fullname,
                          _class="card-title",
                          ),
                     _class="card-header",
                     )

        toolbox = self.render_toolbox(list_id, resource, record)
        if toolbox:
            header.append(toolbox)

        return header

    # -------------------------------------------------------------------------
    def render_body(self, list_id, item_id, resource, rfields, record):
        """
            Render the card body

            @param list_id: the HTML ID of the list
            @param item_id: the HTML ID of the item
            @param resource: the S3Resource to render
            @param rfields: the S3ResourceFields to render
            @param record: the record as dict
        """

        body = DIV(_class="media")
        append = body.append

        fields = ("pr_person_details.nationality",
                  "pr_person.date_of_birth",
                  "pr_person.gender",
                  "pr_physical_description.blood_type",
                  )

        render_column = self.render_column
        for rfield in rfields:
            if rfield.colname in fields:
                column = render_column(item_id, rfield, record)
                if column:
                    append(column)
        return DIV(DIV(body, _class="media-body"), _class="media")

    # -------------------------------------------------------------------------
    def render_column(self, item_id, rfield, record):
        """
            Render a column of the record

            @param list_id: the HTML ID of the list
            @param rfield: the S3ResourceField
            @param record: the record as dict
        """

        value = record._row[rfield.colname]
        if value:
            if rfield.ftype == "text":
                _class = "card_manylines"
            else:
                _class = "card_1_line"
            if rfield.colname == "pr_person.gender":
                gender = record._row[rfield.colname]
                if gender == 2:
                    icon = "female"
                elif gender == 3:
                    icon = "male"
                # @todo: support "other" gender
                #elif gender == 4:
                    #icon = ?
                else:
                    return None # don't render if unknown
            else:
                icon = rfield.fname
            return P(ICON(self.ICONS.get(icon, "icon")),
                     LABEL("%s: " % rfield.label),
                     SPAN(record[rfield.colname]),
                     _class=_class,
                     )
        else:
            return None

    # -------------------------------------------------------------------------
    def render_toolbox(self, list_id, resource, record):
        """
            Render the toolbox

            @param list_id: the HTML ID of the list
            @param resource: the S3Resource to render
            @param record: the record as dict
        """

        record_id = record[str(resource._id)]

        toolbox = DIV(_class="edit-bar fright")

        if current.auth.s3_has_permission("update",
                                          resource.table,
                                          record_id=record_id):

            controller = current.request.controller
            if controller not in ("deploy", "hrm", "member", "vol"):
                controller = "pr"

            update_url = URL(c = controller,
                             f = "person",
                             args = [record_id, "update.popup"],
                             vars = {"refresh": list_id,
                                     "record": record_id,
                                     "profile": self.profile,
                                     },
                             )

            btn = A(ICON("edit"),
                    _href=update_url,
                    _class="s3_modal",
                    _title=S3Method.crud_string(resource.tablename,
                                                "title_update"))
            toolbox.append(btn)

        return toolbox

# =============================================================================
class pr_PersonSearchAutocomplete(S3Method):
    """
        Alternative search method for S3PersonAutocompleteWidget with
        configurable search fields (thus allowing e.g. pe_label to be
        included)

        To apply selectively, override the "search_ac" method of pr_person
        in the respective controller (or in customise_pr_person_controller,
        respectively)

        Search rule (differs from pr_search_ac): every search field can
        contain multiple words (separated by blanks), and every partial
        of the search string must match the beginning of a word in any of
        the fields (i.e. the field value must match either "partial%" or
        "% partial%")
    """

    def __init__(self, search_fields=None):
        """
            Constructor

            @param search_fields: tuple|list of field selectors
        """

        if search_fields is None:
            self.search_fields = ("first_name",
                                  "middle_name",
                                  "last_name",
                                  )
        else:
            self.search_fields = search_fields

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Entry point for REST controller

            @param r: the S3Request
            @param attr: controller parameters for the request
        """

        response = current.response
        settings = current.deployment_settings

        # Apply response.s3.filter
        resource = r.resource
        resource.add_filter(response.s3.filter)

        # Get the search string
        get_vars = r.get_vars
        value = get_vars.term or get_vars.value or get_vars.q or None
        if not value:
            r.error(400, "No value provided!")
        value = s3_unicode(value).lower().strip()

        # Limit to max 8 partials (prevent excessively long search queries)
        partials = value.split()[:8]

        # Build query
        search_fields = set(self.search_fields)
        pe_label_separate = "pe_label" not in search_fields
        if get_vars.get("label") == "1":
            search_fields.add("pe_label")
        query = None
        for partial in partials:
            pquery = None
            for field in search_fields:
                selector = FS(field).lower()
                fquery = selector.like("%s%%" % partial) | \
                         selector.like("%% %s%%" % partial)
                if pquery:
                    pquery |= fquery
                else:
                    pquery = fquery
            if query:
                query &= pquery
            else:
                query = pquery
        if query is not None:
            resource.add_filter(query)

        # Limit the search
        limit = int(get_vars.limit or 0)
        MAX_SEARCH_RESULTS = settings.get_search_max_results()
        if (not limit or limit > MAX_SEARCH_RESULTS) and \
           resource.count() > MAX_SEARCH_RESULTS:
            msg = current.T("There are more than %(max)s results, please input more characters.")
            output = [{"label": s3_str(msg % {"max": MAX_SEARCH_RESULTS})}]
        else:
            fields = ["id"]
            fields.extend(search_fields)

            # Include HR fields?
            show_hr = settings.get_pr_search_shows_hr_details()
            if show_hr:
                fields.append("human_resource.job_title_id$name")
                show_orgs = settings.get_hrm_show_organisation()
                if show_orgs:
                    fields.append("human_resource.organisation_id$name")

            # Sort results alphabetically (according to name format)
            name_format = settings.get_pr_name_format()
            import re
            match = re.match(r"\s*?%\((?P<fname>.*?)\)s.*", name_format)
            if match:
                orderby = "pr_person.%s" % match.group("fname")
            else:
                orderby = "pr_person.first_name"

            # Extract results
            rows = resource.select(fields=fields,
                                   start=0,
                                   limit=limit,
                                   orderby=orderby,
                                   ).rows

            # Build output
            items = []
            iappend = items.append
            for row in rows:
                name = Storage(first_name=row["pr_person.first_name"],
                               middle_name=row["pr_person.middle_name"],
                               last_name=row["pr_person.last_name"],
                               )
                name = s3_fullname(name)
                item = {"id": row["pr_person.id"],
                        "name": name,
                        }

                # Include pe_label?
                if "pe_label" in search_fields:
                    pe_label = row["pr_person.pe_label"]
                    if pe_label:
                        if pe_label_separate:
                            # Send pe_label separate (dealt with client-side)
                            item["pe_label"] = pe_label
                        else:
                            # Prepend pe_label to name
                            item["name"] = "%s %s" % (pe_label, name)
                if show_hr:
                    job_title = row.get("hrm_job_title.name", None)
                    if job_title:
                        item["job"] = job_title
                    if show_orgs:
                        org = row.get("org_organisation.name", None)
                        if org:
                            item["org"] = org
                iappend(item)
            output = items

        response.headers["Content-Type"] = "application/json"
        return json.dumps(output, separators=SEPARATORS)

# =============================================================================
def pr_filter_list_layout(list_id, item_id, resource, rfields, record):
    """
        Default dataList item renderer for Saved Filters

        @param list_id: the HTML ID of the list
        @param item_id: the HTML ID of the item
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
    """

    record_id = record["pr_filter.id"]
    item_class = "thumbnail"

    raw = record._row

    T = current.T
    resource_name = raw["pr_filter.resource"]
    resource = current.s3db.resource(resource_name)

    # Resource title
    crud_strings = current.response.s3.crud_strings.get(resource.tablename)
    if crud_strings:
        resource_name = crud_strings.title_list
    else:
        resource_name = " ".join(s.capitalize() for s in resource.name.split("_"))

    # Filter title
    title = record["pr_filter.title"]

    # Filter Query
    fstring = S3FilterString(resource, raw["pr_filter.query"])
    query = fstring.represent()

    # Actions
    actions = filter_actions(resource,
                             raw["pr_filter.url"],
                             fstring.get_vars)

    # Render the item
    item = DIV(DIV(DIV(actions,
                       _class="action-bar fleft"),
                   SPAN(T("%(resource)s Filter") % \
                        dict(resource=resource_name),
                        _class="card-title"),
                    DIV(A(ICON("delete"),
                          _title=T("Delete this Filter"),
                          _class="dl-item-delete"),
                        _class="edit-bar fright"),
                   _class="card-header"),
               DIV(DIV(H5(title,
                          _id="filter-title-%s" % record_id,
                          _class="media-heading jeditable"),
                       DIV(query),
                       _class="media-body"),
                   _class="media"),
               _class=item_class,
               _id=item_id,
               )

    return item

# -----------------------------------------------------------------------------
def filter_actions(resource, url, filters):
    """
        Helper to construct the actions for a saved filter.

        @param resource: the S3Resource
        @param url: the filter page URL
        @param filters: the filter GET vars
    """

    if not url:
        return ""

    T = current.T
    actions = []
    append = actions.append
    tablename = resource.tablename
    filter_actions = current.s3db.get_config(tablename, "filter_actions")
    if filter_actions:
        controller, fn = tablename.split("_", 1)
        for action in filter_actions:
            c = action.get("controller", controller)
            f = action.get("function", fn)
            m = action.get("method", None)
            if m:
                args = [m]
            else:
                args = []
            e = action.get("format", None)
            link = URL(c=c, f=f, args=args, extension=e,
                       vars=filters)
            append(A(ICON(action.get("icon", "other")),
                     _title=T(action.get("label", "Open")),
                     _href=link))
    else:
        # Default to using Summary Tabs
        links = summary_urls(resource, url, filters)
        if links:
            if "map" in links:
                append(A(ICON("globe"),
                         _title=T("Open Map"),
                         _href=links["map"]))
            if "table" in links:
                append(A(ICON("table"),
                         _title=T("Open Table"),
                         _href=links["table"]))
            if "chart" in links:
                append(A(ICON("bar-chart"),
                         _title=T("Open Chart"),
                         _href=links["chart"]))
            if "report" in links:
                append(A(ICON("bar-chart"),
                         _title=T("Open Report"),
                         _href=links["report"]))

    return actions

# -----------------------------------------------------------------------------
def summary_urls(resource, url, filters):
    """
        Helper to get URLs for summary tabs to use as Actions for a Saved Filter

        @param resource: the S3Resource
        @param url: the filter page URL
        @param filters: the filter GET vars
    """

    links = {}

    get_vars = S3URLQuery.parse_url(url)
    get_vars.pop("t", None)
    get_vars.pop("w", None)
    get_vars.update(filters)

    list_vars = []
    for (k, v) in get_vars.items():
        if v is None:
            continue
        values = v if type(v) is list else [v]
        for value in values:
            if value is not None:
                list_vars.append((k, value))
    base_url = url.split("?", 1)[0]

    summary_config = S3Summary._get_config(resource)
    tab_idx = 0
    for section in summary_config:

        if section.get("common"):
            continue
        #section_id = section["name"]

        tab_vars = list_vars + [("t", str(tab_idx))]
        links[section["name"]] = "%s?%s" % (base_url, urlencode(tab_vars))
        tab_idx += 1

    return links

# END =========================================================================
