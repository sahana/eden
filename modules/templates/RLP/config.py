# -*- coding: utf-8 -*-

import datetime

from collections import OrderedDict

from gluon import current, redirect, URL, A, DIV, TABLE, TAG, TR
from gluon.storage import Storage

from s3 import FS, S3DateFilter, S3Represent, s3_fieldmethod, s3_fullname, s3_yes_no_represent
from s3dal import original_tablename

ALLOWED_FORMATS = ("html", "iframe", "popup", "aadata", "json", "xls", "pdf")

def config(settings):
    """
        Settings for Rhineland-Palatinate (RLP) Crisis Management Tool
        - used to manage Volunteer Pools for COVID-19 response
    """

    T = current.T

    purpose = {"event": "COVID-19"}
    settings.base.system_name = T("%(event)s Crisis Management") % purpose
    settings.base.system_name_short = T("%(event)s Crisis Management") % purpose

    # PrePopulate data
    settings.base.prepopulate += ("RLP",)
    settings.base.prepopulate_demo.append("RLP/Demo")

    # Theme (folder to use for views/layout.html)
    settings.base.theme = "RLP"
    # Custom Logo
    #settings.ui.menu_logo = "/%s/static/themes/<templatename>/img/logo.png" % current.request.application

    # Authentication settings
    # No self-registration
    settings.security.self_registration = False
    # Do new users need to verify their email address?
    settings.auth.registration_requires_verification = True
    # Do not send standard welcome emails (using custom function)
    settings.auth.registration_welcome_email = False
    # Do new users need to be approved by an administrator prior to being able to login?
    #settings.auth.registration_requires_approval = True
    settings.auth.registration_requests_organisation = True
    # Required for access to default realm permissions
    settings.auth.registration_link_user_to = ["staff"]
    settings.auth.registration_link_user_to_default = ["staff"]
    # Disable password-retrieval feature
    settings.auth.password_retrieval = False

    settings.auth.realm_entity_types = ("org_organisation", "pr_forum", "pr_group")
    settings.auth.privileged_roles = {"COORDINATOR": "COORDINATOR"}

    settings.auth.password_min_length = 8
    settings.auth.consent_tracking = True

    # Approval emails get sent to all admins
    settings.mail.approver = "ADMIN"

    # Restrict the Location Selector to just certain countries
    # NB This can also be over-ridden for specific contexts later
    # e.g. Activities filtered to those of parent Project
    settings.gis.countries = ("DE",)
    #gis_levels = ("L1", "L2", "L3")
    # Uncomment to display the Map Legend as a floating DIV, so that it is visible on Summary Map
    settings.gis.legend = "float"
    # Uncomment to Disable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False # @ToDo: Vary by country (include in the gis_config!)
    # Uncomment to show the Print control:
    # http://eden.sahanafoundation.org/wiki/UserGuidelines/Admin/MapPrinting
    #settings.gis.print_button = True

    # L10n settings
    # Languages used in the deployment (used for Language Toolbar, GIS Locations, etc)
    # http://www.loc.gov/standards/iso639-2/php/code_list.php
    settings.L10n.languages = OrderedDict([
       ("de", "German"),
       ("en", "English"),
    ])
    # Default language for Language Toolbar (& GIS Locations in future)
    settings.L10n.default_language = "de"
    # Uncomment to Hide the language toolbar
    #settings.L10n.display_toolbar = False
    # Default timezone for users
    settings.L10n.timezone = "Europe/Berlin"
    # Default date/time formats
    settings.L10n.date_format = "%d.%m.%Y"
    settings.L10n.time_format = "%H:%M"
    # Number formats (defaults to ISO 31-0)
    # Decimal separator for numbers (defaults to ,)
    settings.L10n.decimal_separator = "."
    # Thousands separator for numbers (defaults to space)
    settings.L10n.thousands_separator = ","
    # Uncomment this to Translate Layer Names
    #settings.L10n.translate_gis_layer = True
    # Uncomment this to Translate Location Names
    #settings.L10n.translate_gis_location = True
    # Uncomment this to Translate Organisation Names/Acronyms
    #settings.L10n.translate_org_organisation = True
    # Finance settings
    settings.fin.currencies = {
        "EUR" : "Euros",
    #    "GBP" : "Great British Pounds",
    #    "USD" : "United States Dollars",
    }
    settings.fin.currency_default = "EUR"

    # Do not require international phone number format
    settings.msg.require_international_phone_numbers = False

    # Security Policy
    # http://eden.sahanafoundation.org/wiki/S3AAA#System-widePolicy
    # 1: Simple (default): Global as Reader, Authenticated as Editor
    # 2: Editor role required for Update/Delete, unless record owned by session
    # 3: Apply Controller ACLs
    # 4: Apply both Controller & Function ACLs
    # 5: Apply Controller, Function & Table ACLs
    # 6: Apply Controller, Function, Table ACLs and Entity Realm
    # 7: Apply Controller, Function, Table ACLs and Entity Realm + Hierarchy
    # 8: Apply Controller, Function, Table ACLs, Entity Realm + Hierarchy and Delegations
    #
    settings.security.policy = 7

    # -------------------------------------------------------------------------
    settings.pr.hide_third_gender = False
    settings.pr.separate_name_fields = 2
    settings.pr.name_format= "%(last_name)s, %(first_name)s"

    # -------------------------------------------------------------------------
    settings.hrm.record_tab = False
    settings.hrm.staff_experience = False
    settings.hrm.use_certificates = False
    settings.hrm.use_credentials = False
    settings.hrm.use_description = False
    settings.hrm.use_trainings = False

    # -------------------------------------------------------------------------
    settings.org.projects_tab = False
    settings.org.default_organisation = "Ministerium für Soziales, Arbeit, Gesundheit und Demografie"

    # -------------------------------------------------------------------------
    # Custom group types for volunteer pools
    #
    pool_types = {21: T("Open Pool"),
                  22: T("Managed Pool"),
                  }
    pool_type_ids = list(pool_types.keys())

    # -------------------------------------------------------------------------
    # Realm Rules
    #
    def rlp_realm_entity(table, row):
        """
            Assign a Realm Entity to records
        """

        db = current.db
        s3db = current.s3db

        tablename = original_tablename(table)

        realm_entity = 0

        if tablename == "pr_person":

            # Pool volunteers belong to the pool's realm
            mtable = s3db.pr_group_membership
            gtable = s3db.pr_group

            left = gtable.on(gtable.id == mtable.group_id)
            query = (mtable.person_id == row.id) & \
                    (mtable.deleted == False) & \
                    (gtable.group_type.belongs(pool_type_ids))
            pool = db(query).select(gtable.pe_id,
                                    left = left,
                                    limitby = (0, 1),
                                    ).first()
            if pool:
                realm_entity = pool.pe_id
            else:
                # Other human resources belong to their org's realm
                htable = s3db.hrm_human_resource
                otable = s3db.org_organisation

                left = otable.on(otable.id == htable.organisation_id)
                query = (htable.person_id == row.id) & \
                        (htable.deleted == False)
                org = db(query).select(otable.pe_id,
                                       left = left,
                                       limitby = (0, 1),
                                       ).first()
                if org:
                    realm_entity = org.pe_id

        elif tablename in ("pr_person_details",
                           "pr_person_availability",
                           "hrm_human_resource",
                           "hrm_competency",
                           ):

            # Inherit from person via person_id
            table = s3db.table(tablename)
            ptable = s3db.pr_person
            query = (table._id == row.id) & \
                    (ptable.id == table.person_id)
            person = db(query).select(ptable.realm_entity,
                                      limitby = (0, 1),
                                      ).first()
            if person:
                realm_entity = person.realm_entity

        elif tablename in ("pr_address",
                           "pr_contact",
                           "pr_contact_emergency",
                           ):

            # Inherit from person via PE
            table = s3db.table(tablename)
            ptable = s3db.pr_person
            query = (table._id == row.id) & \
                    (ptable.pe_id == table.pe_id)
            person = db(query).select(ptable.realm_entity,
                                      limitby = (0, 1),
                                      ).first()
            if person:
                realm_entity = person.realm_entity

        elif tablename == "hrm_delegation":

            # Delegations are owned by the requesting org => default
            pass

        elif tablename == "hrm_delegation_note":

            organisation_id = None

            # Default to HR Organisation of current user
            hr_id = current.auth.s3_logged_in_human_resource()
            if hr_id:
                htable = s3db.hrm_human_resource
                query = (htable.id == hr_id) & \
                        (htable.deleted == False)
                hr = db(query).select(htable.organisation_id,
                                      limitby = (0, 1),
                                      orderby = htable.created_on,
                                      ).first()
                if hr:
                    organisation_id = hr.organisation_id

            # Fall back to requesting organisation of the delegation
            if not organisation_id:
                dtable = s3db.hrm_delegation
                ntable = s3db.hrm_delegation_note
                query = (ntable.id == row.id) & \
                        (dtable.id == ntable.delegation_id)
                delegation = db(query).select(dtable.organisation_id,
                                              limitby = (0, 1),
                                              ).first()
                if delegation:
                    organisation_id = delegation.organisation_id

            if organisation_id:
                realm_entity = s3db.pr_get_pe_id("org_organisation",
                                                 organisation_id,
                                                 )

        elif tablename == "pr_group":

            # Pools own themselves => default
            pass

        elif tablename == "pr_group_membership":

            # Pool membership is owned by the pool => default
            pass

        return realm_entity

    settings.auth.realm_entity = rlp_realm_entity

    # -------------------------------------------------------------------------
    def customise_auth_user_resource(r, tablename):
        """
            Configure custom register-onaccept
        """

        from .controllers import register
        current.s3db.configure("auth_user",
                               register_onaccept = register.register_onaccept,
                               )

    settings.customise_auth_user_resource = customise_auth_user_resource

    # -------------------------------------------------------------------------
    def customise_cms_post_resource(r, tablename):

        from s3 import S3SQLCustomForm, S3SQLInlineComponent

        crud_form = S3SQLCustomForm("name",
                                    "body",
                                    "date",
                                    S3SQLInlineComponent("document",
                                                         name = "file",
                                                         label = T("Attachments"),
                                                         fields = ["file", "comments"],
                                                         filterby = {"field": "file",
                                                                     "options": "",
                                                                     "invert": True,
                                                                     },
                                                         ),
                                    "comments",
                                    )

        current.s3db.configure("cms_post",
                               crud_form = crud_form,
                               list_fields = ["post_module.module",
                                              "post_module.resource",
                                              "name",
                                              "date",
                                              "comments",
                                              ],
                               )

    settings.customise_cms_post_resource = customise_cms_post_resource

    # -----------------------------------------------------------------------------
    def customise_cms_post_controller(**attr):

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def prep(r):
            # Call standard prep
            result = standard_prep(r) if callable(standard_prep) else True

            table = r.table
            context = r.get_vars.get("resource")
            if context == "Privacy":
                page = URL(c="default", f="index", args=["privacy"])
                r.resource.configure(create_next = page,
                                     update_next = page,
                                     )
                table.name.default = "Privacy Notice"
            elif context == "Legal":
                page = URL(c="default", f="index", args=["legal"])
                r.resource.configure(create_next = page,
                                     update_next = page,
                                     )
                table.name.default = "Legal Notice"
            return result
        s3.prep = prep

        return attr

    settings.customise_cms_post_controller = customise_cms_post_controller
    # -------------------------------------------------------------------------
    def customise_org_organisation_resource(r, tablename):

        s3db = current.s3db

        # TODO is this needed?
        s3db.add_components("org_organisation",
                            pr_group = {"name": "pool",
                                        "link": "org_organisation_team",
                                        "joinby": "organisation_id",
                                        "key": "group_id",
                                        "filterby": {"group_type": pool_type_ids,
                                                     },
                                        "actuate": "replace",
                                        },
                            )

    settings.customise_org_organisation_resource = customise_org_organisation_resource

    # -------------------------------------------------------------------------
    def customise_org_organisation_controller(**attr):

        s3 = current.response.s3

        s3db = current.s3db

        s3db.add_components("org_organisation",
                            pr_group = {"name": "pool",
                                        "link": "org_organisation_team",
                                        "joinby": "organisation_id",
                                        "key": "group_id",
                                        "filterby": {"group_type": pool_type_ids,
                                                     },
                                        "actuate": "replace",
                                        },
                            )

        standard_prep = s3.prep
        def custom_prep(r):

            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if r.component_name == "human_resource":
                # Show staff only (not volunteers)
                r.component.add_filter(FS("type") == 1)

                # TODO adjust list_fields to what is necessary
                # TODO use simplified form


            return result
        s3.prep = custom_prep

        # Custom rheader
        attr = dict(attr)
        attr["rheader"] = rlp_org_rheader

        return attr

    settings.customise_org_organisation_controller = customise_org_organisation_controller

    # -------------------------------------------------------------------------
    def customise_org_office_controller(**attr):

        s3 = current.response.s3

        standard_prep = s3.prep
        def custom_prep(r):

            # Call standard prep
            result = standard_prep(r) if callable(standard_prep) else True

            if r.representation == "json":
                # Include site_id for filterOptionsS3 in vol/person form
                r.resource.configure(list_fields = ["id",
                                                    "site_id",
                                                    "name",
                                                    ],
                                     )

            return result
        s3.prep = custom_prep

        return attr

    settings.customise_org_office_controller = customise_org_office_controller

    # -------------------------------------------------------------------------
    def pr_group_onaccept(form):

        record_id = form.vars.id
        if not record_id:
            return

        db = current.db
        s3db = current.s3db

        table = s3db.pr_group
        query = (table.id == record_id)
        row = db(query).select(table.id,
                               table.pe_id,
                               table.group_type,
                               limitby = (0, 1),
                               ).first()
        if row:
            ftable = s3db.pr_forum
            query = (ftable.uuid == "POOLS")
            all_pools = db(ftable.uuid == "POOLS").select(ftable.id,
                                                          ftable.pe_id,
                                                          limitby = (0, 1),
                                                          ).first()
            if all_pools:
                if row.group_type in pool_type_ids:
                    s3db.pr_add_affiliation(all_pools.pe_id,
                                            row.pe_id,
                                            role = "pools",
                                            )
                else:
                    s3db.pr_remove_affiliation(all_pools.pe_id,
                                               row.pe_id,
                                               role = "pools",
                                               )
            else:
                # Incomplete prepop
                current.log.warning("All-pools forum not found! (Prepop incomplete?)")


    # -------------------------------------------------------------------------
    def customise_pr_group_resource(r, tablename):

        s3db = current.s3db

        s3db.add_custom_callback("pr_group",
                                 "onaccept",
                                 pr_group_onaccept,
                                 )

        if r.tablename == "org_organisation":
            table = r.component.table
        else:
            table = s3db.pr_group

        from gluon import IS_IN_SET
        if not current.auth.user or current.response.s3.bulk:
            valid_types = s3db.pr_group_types
            valid_types.update(pool_types)
        else:
            valid_types = pool_types

        field = table.group_type
        field.label = T("Pool Type")
        field.default = 22
        field.requires = IS_IN_SET(valid_types, zero=None)
        field.represent = S3Represent(options = pool_types)

        field = table.name
        field.label = T("Pool Title")

        field = table.description
        field.readable = field.writable = False

    settings.customise_pr_group_resource = customise_pr_group_resource

    # -------------------------------------------------------------------------
    def open_pool_member(person_id):

        db = current.db
        s3db = current.s3db

        gtable = s3db.pr_group
        mtable = s3db.pr_group_membership

        left = gtable.on(gtable.id == mtable.group_id)
        query = (mtable.person_id == person_id) & \
                (mtable.deleted == False) & \
                (gtable.group_type == 21)
        membership = db(query).select(mtable.id,
                                      left = left,
                                      limitby=(0, 1),
                                      ).first()

        return bool(membership)

    # -------------------------------------------------------------------------
    def vol_update_alias(person_id):
        """
            Update the alias of a person:
            => full name if member of an open volunteer pool
            => placeholder otherwise

            - used to hide the name of managed volunteers, yet make
              the volunteer list searchable by name
        """

        db = current.db
        s3db = current.s3db

        ptable = s3db.pr_person
        person = db(ptable.id == person_id).select(ptable.id,
                                                   ptable.first_name,
                                                   ptable.middle_name,
                                                   ptable.last_name,
                                                   limitby = (0, 1),
                                                   ).first()
        if not person:
            return

        if open_pool_member(person.id):
            alias = s3_fullname(person)
        else:
            alias = "***"

        dtable = s3db.pr_person_details
        query = (dtable.person_id == person.id) & \
                (dtable.deleted == False)
        details = db(query).select(dtable.id, limitby=(0, 1)).first()
        if details:
            details.update_record(alias=alias)
        else:
            data = {"person_id": person.id,
                    "alias": alias,
                    }
            details_id = data["id"] = dtable.insert(**data)
            auth = current.auth
            auth.s3_set_record_owner(dtable, details_id)
            auth.s3_make_session_owner(dtable, details_id)
            s3db.onaccept(dtable, data)

    # -------------------------------------------------------------------------
    def pool_membership_onaccept(form):
        """ Trigger alias update when adding a person to a group """

        db = current.db
        s3db = current.s3db

        record_id = form.vars.id
        mtable = s3db.pr_group_membership
        row = db(mtable.id == record_id).select(mtable.person_id,
                                                limitby = (0, 1),
                                                ).first()
        if row:
            vol_update_alias(row.person_id)

        # Also update realm entity of the person
        ptable = s3db.pr_person
        current.auth.set_realm_entity(ptable,
                                      ptable.id == row.person_id,
                                      force_update = True,
                                      )

    def pool_membership_ondelete(row):
        """ Trigger alias update when removing a person from a group """

        vol_update_alias(row.person_id)

        # Also update realm entity of the person
        ptable = current.s3db.pr_person
        current.auth.set_realm_entity(ptable,
                                      ptable.id == row.person_id,
                                      force_update = True,
                                      )

    # -------------------------------------------------------------------------
    def customise_pr_group_membership_resource(r, tablename):

        s3db = current.s3db
        s3db.add_custom_callback("pr_group_membership",
                                 "onaccept",
                                 pool_membership_onaccept,
                                 )
        s3db.add_custom_callback("pr_group_membership",
                                 "ondelete",
                                 pool_membership_ondelete,
                                 )

        component = r.component

        if component and component.alias == "pool_membership":

            table = component.table

            # Limit group selector to pools the person is not a member of yet
            field = table.group_id
            from s3 import IS_ONE_OF
            gtable = s3db.pr_group
            mtable = s3db.pr_group_membership
            query = (gtable.group_type.belongs(pool_type_ids)) & (mtable.id == None)
            left = mtable.on((mtable.group_id == gtable.id) & \
                             (mtable.person_id == r.id) & \
                             (mtable.deleted == False))
            dbset = current.db(query)
            field.requires = IS_ONE_OF(dbset, "pr_group.id", field.represent,
                                       left = left,
                                       )

            # Hide add-form if already member in all pools
            if len(dbset.select(gtable.id, left=left)) == 0:
                component.configure(insertable=False)

            # Custom label, use drop-down not autocomplete, no add-link
            field.label = T("Pool")
            field.widget = None
            field.comment = None

            # Hide group_head box
            field = table.group_head
            field.readable = field.writable = False

            # Hide comments (not needed here)
            field = table.comments
            field.readable = field.writable = False

            # Custom table configuration for pool membership
            component.configure(list_fields = ["group_id",
                                               # TODO show pool type (needs S3Represent)
                                               #"group_id$group_type",
                                               ],
                                editable = False,
                                )

    settings.customise_pr_group_membership_resource = customise_pr_group_membership_resource

    # -------------------------------------------------------------------------
    def get_pools():
        """
            Get the IDs and names of all current pools
        """

        db = current.db
        s3db = current.s3db

        gtable = s3db.pr_group
        query = (gtable.group_type.belongs(pool_type_ids)) & \
                (gtable.deleted == False)
        rows = db(query).select(gtable.id,
                                gtable.name,
                                cache = s3db.cache,
                                )

        return {row.id: row.name for row in rows}

    # -------------------------------------------------------------------------
    def use_person_custom_components():
        """
            Define custom components of pr_person
            - current address (pr_address)
            - volunteer record (hrm_human_resource)
            - volunteer pool (pr_group)
            - membership in volunteer pool (pr_group_membership)
        """

        s3db = current.s3db

        pools = get_pools()
        pool_ids = list(pools.keys())

        s3db.add_components("pr_pentity",
                            pr_address = {"name": "current_address",
                                          "joinby": "pe_id",
                                          "filterby": {"type": 1},
                                          "multiple": False,
                                          },
                            )

        s3db.add_components("pr_person",
                            hrm_human_resource = {"name": "volunteer_record",
                                                  "joinby": "person_id",
                                                  "filterby": {"type": 2},
                                                  "multiple": False,
                                                  },
                            pr_group = {"name": "pool",
                                        "link": "pr_group_membership",
                                        "joinby": "person_id",
                                        "key": "group_id",
                                        "filterby": {"group_type": pool_type_ids},
                                        "multiple": False,
                                        },
                            pr_group_membership = {"name": "pool_membership",
                                                   "joinby": "person_id",
                                                   "filterby": {"group_id": pool_ids},
                                                   "multiple": False,
                                                   },
                            )

    # -------------------------------------------------------------------------
    def vol_person_onaccept(form):
        """
            Custom-onaccept for person records:
                - auto-generate an ID label
                - update alias (in case name changed)

            @param form: the FORM
        """

        s3db = current.s3db

        record_id = form.vars.get("id")
        if not record_id:
            return

        table = s3db.pr_person
        query = (table.id == record_id) & (table.deleted == False)

        row = current.db(query).select(table.id,
                                       table.pe_label,
                                       limitby = (0, 1),
                                       ).first()
        if row:
            if not row.pe_label:
                pe_label = "R-%07d" % row.id
                row.update_record(pe_label = pe_label)
                s3db.update_super(table, row)
            vol_update_alias(row.id)

    # -------------------------------------------------------------------------
    def has_account(row):
        """
            Field method to check for user ID
        """

        try:
            user_id = row.auth_user.id
        except AttributeError:
            return None
        return bool(user_id)

    # -------------------------------------------------------------------------
    def customise_pr_person_resource(r, tablename):

        s3db = current.s3db

        # Do not update group type in pre-imported pools (for import)
        from s3 import S3Duplicate
        s3db.configure("pr_group",
                       deduplicate = S3Duplicate(ignore_deleted = True,
                                                 noupdate = True,
                                                 ),
                       )

        if r.method == "import" or not current.auth.user:
            # Skip uniqueness validator for occupation types in imports
            # - deduplicate takes care of name matches
            from gluon import IS_NOT_EMPTY, IS_LENGTH
            ottable = s3db.pr_occupation_type
            field = ottable.name
            field.requires = [IS_NOT_EMPTY(),
                              IS_LENGTH(128),
                              ]

        # Custom callbacks for group membership (for import)
        s3db.add_custom_callback("pr_group_membership",
                                 "onaccept",
                                 pool_membership_onaccept,
                                 )
        s3db.add_custom_callback("pr_group_membership",
                                 "ondelete",
                                 pool_membership_ondelete,
                                 )

        # Custom onaccept-callback to set ID label and update alias
        s3db.add_custom_callback("pr_person",
                                 "onaccept",
                                 vol_person_onaccept,
                                 )

        table = r.table
        if r.tablename == "pr_person" and not hasattr(table, "has_account"):
            table.has_account = s3_fieldmethod("has_account", has_account,
                                               represent = s3_yes_no_represent,
                                               )

        # Configure components to inherit realm_entity from person
        s3db.configure("pr_person",
                       realm_components = ("human_resource",
                                           "competency",
                                           "person_details",
                                           "availability",
                                           "contact",
                                           "address",
                                           ),
                       )

    settings.customise_pr_person_resource = customise_pr_person_resource
    # -------------------------------------------------------------------------
    def customise_pr_person_controller(**attr):

        db = current.db
        s3db = current.s3db

        s3 = current.response.s3

        # Enable bigtable features
        settings.base.bigtable = True

        use_person_custom_components()

        standard_prep = s3.prep
        def custom_prep(r):

            result = True
            resource = r.resource
            table = resource.table

            from gluon import IS_NOT_EMPTY
            from s3 import (IS_ONE_OF,
                            IS_PERSON_GENDER,
                            S3AgeFilter,
                            S3LocationFilter,
                            S3LocationSelector,
                            S3OptionsFilter,
                            S3RangeFilter,
                            S3SQLCustomForm,
                            S3SQLInlineComponent,
                            S3SQLInlineLink,
                            S3TextFilter,
                            StringTemplateParser,
                            s3_get_filter_opts,
                            )

            # Make last name mandatory
            field = table.last_name
            field.requires = IS_NOT_EMPTY()

            # Hide comment for first name
            field = table.first_name
            field.comment = None

            # Don't sort genders alphabetically
            genders = sorted(list(s3db.pr_gender_opts.items()),
                             key = lambda item: item[0],
                             )
            field = table.gender
            field.requires = IS_PERSON_GENDER(genders,
                                              sort = False,
                                              zero = None,
                                              )

            # Enable weekly hours
            avtable = s3db.pr_person_availability
            field = avtable.hours_per_week
            field.readable = field.writable = True

            # Hide map selector in address
            atable = s3db.pr_address
            field = atable.location_id
            field.widget = S3LocationSelector(show_address = True,
                                              show_map = False,
                                              )

            hrcomponent = resource.components.get("volunteer_record")
            hrtable = hrcomponent.table

            # Hide comment for comments-field (field re-purposed)
            field = hrtable.comments
            field.comment = None

            # Determine order of name fields
            NAMES = ("first_name", "middle_name", "last_name")
            keys = StringTemplateParser.keys(settings.get_pr_name_format())
            name_fields = [fn for fn in keys if fn in NAMES]

            if r.controller == "vol":
                # Volunteer perspective (vol/person)

                record = r.record

                # Filter to volunteers only
                resource.add_filter(FS("volunteer_record.id") != None)

                has_role = current.auth.s3_has_role
                coordinator = has_role("COORDINATOR")

                # Configure anonymize-method
                from s3 import S3Anonymize
                s3db.set_method("pr", "person",
                                method = "anonymize",
                                action = S3Anonymize,
                                )

                # Configure anonymize-rules
                from .anonymize import rlp_volunteer_anonymize
                s3db.configure("pr_person",
                               anonymize = rlp_volunteer_anonymize(),
                               )

                get_vars = r.get_vars

                if not coordinator:

                    # Restrict data formats
                    settings.ui.export_formats = ("pdf", "xls")
                    if r.representation not in ALLOWED_FORMATS:
                        r.error(403, current.ERROR.NOT_PERMITTED)

                    # Show only active volunteers in pools
                    resource.add_filter(FS("pool_membership.id") > 0)
                    if not record:
                        resource.add_filter(FS("volunteer_record.status") == 1)

                elif not record:

                    # Filter for active/inactive volunteers
                    active = get_vars.get("active")
                    if active == "0":
                        resource.add_filter(FS("volunteer_record.status") != 1)
                    elif active != "both":
                        resource.add_filter(FS("volunteer_record.status") == 1)

                list_title = T("Volunteers")
                if not record:
                    # Availability Filter
                    parse_dt = current.calendar.parse_date
                    from_date = parse_dt(get_vars.get("available__ge"))
                    to_date = parse_dt(get_vars.get("available__le"))
                    if from_date or to_date:
                        # Filter to join active deployments during interval
                        active = lambda ctable: \
                                 rlp_active_deployments(ctable, from_date, to_date)
                        s3db.add_components("pr_person",
                                            hrm_delegation = {"name": "active_deployment",
                                                              "joinby": "person_id",
                                                              "filterby": active,
                                                              },
                                            )
                        resource.add_filter(FS("active_deployment.id") == None)

                    # Currently-Deployed-Filter
                    deployed_now = get_vars.get("deployed_now") == "1"
                    if deployed_now:
                        s3db.add_components("pr_person",
                                            hrm_delegation = {"name": "ongoing_deployment",
                                                              "joinby": "person_id",
                                                              "filterby": rlp_active_deployments,
                                                              },
                                            )
                        resource.add_filter(FS("ongoing_deployment.id") != None)
                        list_title = T("Currently Deployed Volunteers")

                if not r.component:

                    # Hide add-link for organisation
                    field = hrtable.organisation_id
                    field.comment = None

                    # Don't show organisation as link
                    field.represent = s3db.org_OrganisationRepresent(show_link=False)

                    # Limit volunteer organisations to those with volunteer pools
                    gtable = s3db.pr_group
                    otable = s3db.org_organisation
                    ltable = s3db.org_organisation_team
                    left = [ltable.on((ltable.organisation_id == otable.id) & \
                                      (ltable.deleted == False)),
                            gtable.on((gtable.id == ltable.group_id) & \
                                      (gtable.group_type.belongs(pool_type_ids))),
                            ]
                    dbset = db(gtable.id != None)
                    field.requires = IS_ONE_OF(dbset, "org_organisation.id",
                                               field.represent,
                                               left = left,
                                               )

                    # Adapt CRUD-strings => Volunteers
                    s3.crud_strings[resource.tablename] = Storage(
                        label_create = T("Create Volunteer"),
                        title_display = T("Volunteer Details"),
                        title_list = list_title,
                        title_update = T("Edit Volunteer Details"),
                        title_upload = T("Import Volunteers"),
                        label_list_button = T("List Volunteers"),
                        label_delete_button = T("Delete Volunteer"),
                        msg_record_created = T("Volunteer added"),
                        msg_record_modified = T("Volunteer details updated"),
                        msg_record_deleted = T("Volunteer deleted"),
                        msg_list_empty = T("No Volunteers found"),
                        )

                    # Custom list_fields
                    list_fields = [(T("Pool"), "pool_membership.group_id"),
                                   (T("ID"), "pe_label"),
                                   # name-fields
                                   (T("Age"), "age"),
                                   #"occupation_type_person.occupation_type_id",
                                   #"availability.hours_per_week",
                                   #"current_address.location_id$addr_postcode",
                                   #(T("Place of Residence"), "current_address.location_id$L3"),
                                   ]

                    # Custom Form
                    crud_fields = [S3SQLInlineLink("pool",
                                                   field = "group_id",
                                                   multiple = False,
                                                   header = False,
                                                   search = False,
                                                   ),
                                   ]

                    # Only COORDINATOR can see organisation details
                    if coordinator:
                        crud_fields[0:0] = ["volunteer_record.organisation_id",
                                            (T("Office##gov"), "volunteer_record.site_id"),
                                            ]
                        script = '''$.filterOptionsS3({
 'trigger':'sub_volunteer_record_organisation_id',
 'target':'sub_volunteer_record_site_id',
 'lookupPrefix':'org',
 'lookupResource':'office',
 'lookupKey':'organisation_id',
 'lookupField':'site_id',
 'optional':true
})'''
                        if script not in s3.jquery_ready:
                            s3.jquery_ready.append(script)
                        crud_fields.append("volunteer_record.status")

                    # Show names and contact details if:
                    # - user is COORDINATOR, or
                    # - volunteer viewed is an open pool member, or
                    # - has an approved deployment the user can access
                    person_id = record.id if record else None
                    if person_id:
                        show_contact_details = coordinator or \
                                               open_pool_member(person_id) or \
                                               rlp_deployed_with_org(person_id)
                    else:
                        show_contact_details = True

                    if show_contact_details:
                        # Name fields in name-format order
                        crud_fields.extend(name_fields)
                    else:
                        name_fields = []

                    if coordinator:
                        # Coordinators can search names and see names,
                        # personal details and addresses
                        text_search_fields = name_fields + ["pe_label"]
                        list_fields[2:2] = name_fields
                        crud_fields.extend([
                                   "date_of_birth",
                                   "gender",
                                   S3SQLInlineComponent(
                                            "address",
                                            label = T("Current Address"),
                                            fields = [("", "location_id")],
                                            filterby = {"field": "type",
                                                        "options": "1",
                                                        },
                                            link = False,
                                            multiple = False,
                                            ),
                                   ])
                        # Coordinators can export contact details in XLS/PDF
                        if r.representation in ("xls", "pdf"):
                            list_fields.extend([
                                (T("Email"), "email.value"),
                                (T("Mobile Phone"), "phone.value"),
                                ])
                    else:
                        # Other users see ID and Alias
                        text_search_fields = ["person_details.alias", "pe_label"]
                        list_fields.insert(2, (T("Name"), "person_details.alias"))

                    if show_contact_details:
                        crud_fields.extend([
                                   S3SQLInlineComponent(
                                            "contact",
                                            fields = [("", "value")],
                                            filterby = {"field": "contact_method",
                                                        "options": "EMAIL",
                                                        },
                                            label = T("Email"),
                                            multiple = False,
                                            name = "email",
                                            ),
                                   S3SQLInlineComponent(
                                            "contact",
                                            fields = [("", "value")],
                                            filterby = {"field": "contact_method",
                                                        "options": "HOME_PHONE",
                                                        },
                                            label = T("Phone"),
                                            multiple = False,
                                            name = "home_phone",
                                            ),
                                   S3SQLInlineComponent(
                                            "contact",
                                            fields = [("", "value")],
                                            filterby = {"field": "contact_method",
                                                        "options": "SMS",
                                                        },
                                            label = T("Mobile Phone"),
                                            multiple = False,
                                            name = "phone",
                                            ),
                                   S3SQLInlineComponent(
                                            "contact",
                                            fields = [("", "value")],
                                            filterby = {"field": "contact_method",
                                                        "options": "WORK_PHONE",
                                                        },
                                            label = T("Office Phone"),
                                            multiple = False,
                                            name = "work_phone",
                                            ),
                                   ])

                    # Common fields for all cases
                    crud_fields.extend([
                        S3SQLInlineLink("occupation_type",
                                       label = T("Occupation Type"),
                                       field = "occupation_type_id",
                                       ),
                        (T("Occupation / Speciality"), "person_details.occupation"),
                        "availability.hours_per_week",
                        "volunteer_record.comments",
                        ])
                    list_fields.extend([
                        "occupation_type_person.occupation_type_id",
                        "availability.hours_per_week",
                        "current_address.location_id$addr_postcode",
                        (T("Place of Residence"), "current_address.location_id$L3"),
                        ])
                    text_search_fields.append("person_details.occupation")

                    # Status as last column
                    if coordinator:
                        list_fields.append("volunteer_record.status")
                        list_fields.append((T("has Account"), "has_account"))

                    # Filters
                    filter_widgets = [
                        S3TextFilter(text_search_fields,
                                     label = T("Search"),
                                     comment = T("Search by ID or name (Note that records with hidden names can only be found by ID). Can use * or ? as wildcards."),
                                     ),
                        S3OptionsFilter("pool_membership.group_id",
                                        label = T("Pool"),
                                        options = get_pools,
                                        ),
                        S3OptionsFilter("occupation_type_person.occupation_type_id",
                                        options = lambda: s3_get_filter_opts("pr_occupation_type"),
                                        ),
                        RLPAvailabilityFilter("delegation.date",
                                              label = T("Available"),
                                              #hide_time = True,
                                              ),
                        S3LocationFilter("current_address.location_id",
                                         label = T("Place of Residence"),
                                         levels = ("L2", "L3"),
                                         hidden = True,
                                         ),
                        S3RangeFilter("availability.hours_per_week",
                                      hidden = True,
                                      ),
                        S3OptionsFilter("competency.skill_id",
                                        label = T("Skills / Resources"),
                                        options = lambda: s3_get_filter_opts("hrm_skill"),
                                        hidden = True,
                                        cols = 2,
                                        ),
                        S3AgeFilter("date_of_birth",
                                    label = T("Age"),
                                    minimum = 12,
                                    maximum = 90,
                                    hidden = True,
                                    ),
                        ]

                    resource.configure(crud_form = S3SQLCustomForm(*crud_fields),
                                       filter_widgets = filter_widgets,
                                       list_fields = list_fields,
                                       # Extra fields for computation of virtual fields
                                       extra_fields = ["date_of_birth",
                                                       "user.id",
                                                       ],
                                       )

                elif r.component_name == "delegation":

                    # HRMANAGERs and ADMINs see the list
                    if not has_role("HRMANAGER") and \
                       r.interactive and r.method is None and not r.component_id:
                        r.method = "organize"

            elif r.controller == "default":
                # Personal profile (default/person)
                if not r.component:
                    # Custom Form
                    crud_fields = name_fields
                    crud_fields.extend(["date_of_birth",
                                        "gender",
                                        S3SQLInlineLink("occupation_type",
                                                       label = T("Occupation Type"),
                                                       field = "occupation_type_id",
                                                       ),
                                        (T("Occupation / Speciality"), "person_details.occupation"),
                                        "volunteer_record.start_date",
                                        "volunteer_record.end_date",
                                        "volunteer_record.status",
                                        "availability.hours_per_week",
                                        "volunteer_record.comments",
                                        ])

                    resource.configure(crud_form = S3SQLCustomForm(*crud_fields),
                                       deletable = False,
                                       )

                    # Configure anonymize-method
                    from s3 import S3Anonymize
                    s3db.set_method("pr", "person",
                                    method = "anonymize",
                                    action = S3Anonymize,
                                    )
                    from .anonymize import rlp_volunteer_anonymize
                    resource.configure(anonymize = rlp_volunteer_anonymize(),
                                       # We only want to redirect to logout when
                                       # they actually deleted their account, so
                                       # checking on reload before prep (see further down)
                                       #anonymize_next = URL(c = "default",
                                       #                     f = "user",
                                       #                     args = ["logout"],
                                       #                     ),
                                       )

            elif callable(standard_prep):
                result = standard_prep(r)

            return result
        s3.prep = custom_prep

        standard_postp = s3.postp
        def custom_postp(r, output):

            # Call standard postp
            if callable(standard_postp):
                output = standard_postp(r, output)

            if r.controller in ("vol", "default") and \
               not r.component and r.record and \
               r.method in (None, "update", "read") and \
               isinstance(output, dict):

                # Custom CRUD buttons
                if "buttons" not in output:
                    buttons = output["buttons"] = {}
                else:
                    buttons = output["buttons"]

                # Anonymize-button
                from s3 import S3AnonymizeWidget
                anonymize = S3AnonymizeWidget.widget(r,
                                         _class="action-btn anonymize-btn")

                # Render in place of the delete-button
                buttons["delete_btn"] = TAG[""](anonymize,
                                                )
            return output
        s3.postp = custom_postp

        # Custom rheaders
        controller = current.request.controller
        if controller == "vol":
            # Use RLP volunteer rheader
            attr = dict(attr)
            attr["rheader"] = rlp_vol_rheader

        elif controller == "default":
            # Logout post-anonymize if the user has removed their account
            auth = current.auth
            user = auth.user
            if user:
                utable = auth.settings.table_user
                account = db(utable.id == user.id).select(utable.deleted,
                                                          limitby=(0, 1),
                                                          ).first()
                if not account or account.deleted:
                    redirect(URL(c="default", f="user", args=["logout"]))
            else:
                redirect(URL(c="default", f="index"))
            # Use RLP profile rheader
            attr = dict(attr)
            attr["rheader"] = rlp_profile_rheader

        return attr

    settings.customise_pr_person_controller = customise_pr_person_controller

    # -------------------------------------------------------------------------
    def delegation_workflow(table, record, person_id=None):
        """
            Enforce workflow in delegation records

            @param table: the Table used in the request (can be aliased)
            @param record: the delegation record
        """

        field = table.status
        if not record:
            status = None
            if person_id and open_pool_member(person_id):
                next_status = ("APPR", "DECL")
            else:
                next_status = ("REQ")
                field.default = "REQ"
                field.writable = False
        else:
            workflow = {#"REQ": ("REQ", "APPR", "DECL", "CANC"),
                        "APPR": ("APPR", "CANC", "IMPL"),
                        "IMPL": ("IMPL", "CANC",),
                        }
            if current.auth.s3_has_role("COORDINATOR"):
                workflow["REQ"] = ("REQ", "APPR", "DECL")
            else:
                workflow["REQ"] = ("REQ", "CANC")
            status = record.status
            next_status = workflow.get(status)

        if not next_status or len(next_status) == 1:
            # Status can't be changed
            field.writable = False
        else:
            requires = field.requires
            theset = []
            labels = []
            for index, option in enumerate(requires.theset):
                if option in next_status:
                    theset.append(option)
                    labels.append(requires.labels[index])
            requires.theset = theset
            requires.labels = labels
            field.writable = True

        # Can only change dates while not processed yet
        if status and status != "REQ":
            field = table.date
            field.writable = False
            field = table.end_date
            field.writable = False


        if record:
            # Can never change person or organisation
            field = table.person_id
            field.writable = False
            field = table.organisation_id
            field.writable = False

            # Only the requesting org can change dates or comments
            #org_pe_id = current.s3db.pr_get_pe_id("org_organisation",
            #                                      record.organisation_id,
            #                                      )
            #if not org_pe_id or \
            #   not current.auth.s3_has_role("HRMANAGER", for_pe=org_pe_id):
            #    field = table.date
            #    field.writable = False
            #    field = table.end_date
            #    field.writable = False
            #    field = table.comments
            #    field.writable = False
            #    field.comment = None

    # -------------------------------------------------------------------------
    def delegation_read_multiple_orgs():

        realms = current.auth.permission.permitted_realms("hrm_delegation", "read")
        if realms is None:
            multiple_orgs = True
            org_ids = []
        else:
            otable = current.s3db.org_organisation
            query = (otable.pe_id.belongs(realms)) & \
                    (otable.deleted == False)
            rows = current.db(query).select(otable.id)
            multiple_orgs = len(rows) > 1
            org_ids = [row.id for row in rows]

        return multiple_orgs, org_ids

    # -------------------------------------------------------------------------
    def customise_hrm_delegation_resource(r, tablename):

        s3db = current.s3db
        s3 = current.response.s3

        # Adapt terminology to use-case
        s3.crud_strings["hrm_delegation"] = Storage(
            label_create = T("Create Deployment"),
            title_display = T("Deployment Details"),
            title_list = T("Deployments"),
            title_update = T("Edit Deployment"),
            label_list_button = T("List Deployments"),
            label_delete_button = T("Delete Deployment"),
            msg_record_created = T("Deployment added"),
            msg_record_modified = T("Deployment updated"),
            msg_record_deleted = T("Deployment deleted"),
            msg_list_empty = T("No Deployments currently registered"),
            )

        # Basic organizer configuration
        organize = {"start": "date",
                    "end": "end_date",
                    "color": "status",
                    "colors": {"REQ":  "#d554a2",
                               "APPR": "#408d40",
                               "DECL": "#303030",
                               "CANC": "#d0d0d0",
                               "IMPL": "#40879c",
                               },
                    }

        table = s3db.hrm_delegation
        field = table.person_id
        field.represent = rlp_DelegatedPersonRepresent()

        if r.interactive:
            # Add tooltip for status-field to explain statuses
            field = table.status
            represent = field.represent
            status_help = TABLE(
                            TR(represent("REQ"), T("Requested")),
                            TR(represent("APPR"), T("Accepted by coordinator/volunteer")),
                            TR(represent("DECL"), T("Declined by coordinator/volunteer")),
                            TR(represent("CANC"), T("Cancelled by requesting organisation or volunteer")),
                            TR(represent("IMPL"), T("Deployment carried out")),
                            )

            field.comment = DIV(DIV(status_help,
                                    _class = "htmltip-content",
                                    _id = "example",
                                    ),
                                _class = "htmltip",
                                _show = "#example",
                                _title = T("Status"),
                                )

        if r.method == "organize":
            # Cannot change dates with the organizer
            # - but may be possible in the popup
            field = table.date
            field.writable = False
            field = table.end_date
            field.writable = False

            # Cannot create delegations in the organizer
            s3db.configure("hrm_delegation", insertable = False)

        tomorrow = current.request.utcnow.date() + datetime.timedelta(days=1)
        min_date = None
        if r.tablename == "hrm_delegation":
            # Primary controller
            volunteer_id = None
            get_vars = r.get_vars
            if "viewing" in get_vars:
                try:
                    vtablename, record_id = get_vars["viewing"].split(".")
                except ValueError:
                    pass
                else:
                    if r.controller == "vol" and vtablename == "pr_person":
                        volunteer_id = record_id

            if volunteer_id:
                # On tab, viewing volunteer
                organize["title"] = "organisation_id"
                organize["description"] = ["date",
                                           "end_date",
                                           "requested_on",
                                           "status",
                                           ]
            else:
                # Main delegations list
                organize["title"] = "person_id"
                organize["description"] = ["organisation_id",
                                           "date",
                                           "end_date",
                                           "requested_on",
                                           "status",
                                           ]

                # - must not insert here
                s3db.configure("hrm_delegation", insertable = False)

            # Apply delegation workflow rules, determine earliest start date
            record = r.record
            if record:
                min_date = min(record.date, tomorrow) if record.date else tomorrow
            else:
                min_date = tomorrow
            delegation_workflow(r.resource.table, record, person_id=volunteer_id)

        elif r.component.tablename == "hrm_delegation":
            # On tab of volunteer file
            if r.component_id:
                r.component.load()
                record = r.component._rows[0]
            else:
                record = None
            delegation_workflow(r.component.table, record, person_id=r.id)

            # Determine earliest start date
            if record:
                min_date = min(record.date, tomorrow) if record.date else tomorrow
            else:
                min_date = tomorrow

            organize["title"] = "organisation_id"
            organize["description"] = ["date",
                                       "end_date",
                                       "requested_on",
                                       "status",
                                       ]

        # Start and end date are mandatory
        from gluon import IS_EMPTY_OR
        for fname in ("date", "end_date"):
            field = table[fname]
            requires = field.requires
            if isinstance(requires, IS_EMPTY_OR):
                field.requires = requires.other

        # Cannot backdate delegation start
        if min_date:
            from s3 import IS_UTC_DATE, S3CalendarWidget
            field = table.date
            field.requires = IS_UTC_DATE(minimum=min_date)
            field.widget = S3CalendarWidget(minimum = min_date,
                                            set_min = "#hrm_delegation_end_date",
                                            )

        if current.auth.s3_has_role("COORDINATOR"):
            # Coordinators use custom form
            from s3 import S3SQLCustomForm
            crud_form = S3SQLCustomForm("organisation_id",
                                        "person_id",
                                        "date",
                                        "end_date",
                                        "requested_on",
                                        "status",
                                        "comments",
                                        )
            if record and record.status == "REQ" and r.method != "read":
                # Request that can be approved
                # => append inline-notifications
                from .notifications import InlineNotifications
                crud_form.append(
                    InlineNotifications("notifications",
                                        label = T("Notifications"),
                                        ))
            s3db.configure("hrm_delegation", crud_form=crud_form)

        # Reconfigure
        s3db.configure("hrm_delegation",
                       deletable = False,
                       organize = organize,
                       )

    settings.customise_hrm_delegation_resource = customise_hrm_delegation_resource

    # -------------------------------------------------------------------------
    def customise_hrm_delegation_controller(**attr):

        s3db = current.s3db
        s3 = current.response.s3
        request = current.request

        # Enable bigtable features
        settings.base.bigtable = True

        use_person_custom_components()

        # Check if on volunteer tab
        volunteer_id = None
        get_vars = request.get_vars
        if "viewing" in get_vars:
            try:
                vtablename, record_id = get_vars["viewing"].split(".")
            except ValueError:
                return False
            if request.controller == "vol" and vtablename == "pr_person":
                volunteer_id = record_id

        # Must not create or delete delegations from delegation list
        if not volunteer_id:
            s3db.configure("hrm_delegation",
                           insertable = False,
                           )

        standard_prep = s3.prep
        def custom_prep(r):

            auth = current.auth
            coordinator = auth.s3_has_role("COORDINATOR")

            if not coordinator:
                settings.ui.export_formats = ("pdf", "xls")
                if r.representation not in ALLOWED_FORMATS:
                    r.error(403, current.ERROR.NOT_PERMITTED)

            # Call standard prep
            result = standard_prep(r) if callable(standard_prep) else True

            # Subsets to support workflow
            status_opts = None
            orderby = "hrm_delegation.date"
            workflow = r.get_vars.get("workflow")
            if workflow:
                today = current.request.utcnow

                PENDING = ("REQ", "INVT", "APPL")
                DECIDED = ("APPR", "ACPT", "DECL", "RJCT")

                if workflow == "p":
                    # Pending (undecided and relevant)
                    status_opts = PENDING
                    query = (FS("end_date") >= today)
                    title = T("Pending Requests")
                    orderby = "hrm_delegation.requested_on"
                elif workflow == "d":
                    # Decided and relevant
                    status_opts = DECIDED
                    query = (FS("end_date") >= today)
                    title = T("Processed Requests")
                    orderby = "hrm_delegation.requested_on desc"
                #elif workflow == "r":
                #    # Relevant
                #    status_opts = PENDING + DECIDED
                #    query = (FS("date") >= today)
                #    title = T("Current Requests")
                #    orderby = "hrm_delegation.date"
                elif workflow == "o":
                    # Obsolete (past, cancelled or implemented)
                    query = (FS("end_date") < today) | \
                            (FS("status").belongs(("DECL", "RJCT", "CANC", "IMPL")))
                    title = T("Archive")
                    orderby = "hrm_delegation.end_date desc"
                else:
                    # Current delegations (accepted|approved and started)
                    status_opts = (("ACPT", "APPR"))
                    query = (FS("date") <= today)
                    title = T("Deployments")
                s3.crud_strings["hrm_delegation"]["title_list"] = title
                if status_opts:
                    query &= FS("status").belongs(status_opts)
                r.resource.add_filter(query)

            multiple_orgs = delegation_read_multiple_orgs()[0]

            if r.interactive:

                if not volunteer_id:
                    from s3 import S3OptionsFilter, s3_get_filter_opts
                    filter_widgets = [
                        S3OptionsFilter("person_id$pool_membership.group_id",
                                        label = T("Pool"),
                                        options = get_pools(),
                                        ),
                        S3DateFilter("date",
                                     hidden = True,
                                     ),
                        S3DateFilter("end_date",
                                     hidden = True,
                                     ),
                        ]

                    # Status-Filter
                    if not status_opts:
                        status_filter_opts = [opt for opt in s3db.hrm_delegation_status_opts]
                    else:
                        status_filter_opts = [opt for opt in s3db.hrm_delegation_status_opts
                                              if opt[0] in status_opts
                                              ]
                    if len(status_filter_opts) > 1:
                        filter_widgets.insert(0,
                            S3OptionsFilter("status",
                                            options = OrderedDict(status_filter_opts),
                                            sort = False,
                                            cols = 3,
                                            ))

                    # Organisation Filter
                    if coordinator or multiple_orgs:
                        filter_widgets.insert(0,
                            S3OptionsFilter("organisation_id",
                                            options = lambda: s3_get_filter_opts("org_organisation"),
                                            ))

                    r.resource.configure(filter_widgets = filter_widgets,
                                         )

                if r.component_name == "delegation_note":

                    ctable = r.component.table
                    field = ctable.modified_by
                    field.label = T("Author")
                    show_org = auth.s3_has_roles(("ADMIN", "ORG_GROUP_ADMIN"))
                    field.represent = s3db.auth_UserRepresent(show_name = True,
                                                              show_email = False,
                                                              show_link = False,
                                                              show_org = show_org,
                                                              )
                    field.writable = False

            # Adapt list fields to perspective
            list_fields = ["date",
                           "end_date",
                           "requested_on",
                           "status",
                           "comments",
                           ]
            if not volunteer_id:
                list_fields[0:0] =  [(T("Pool"), "person_id$pool_membership.group_id"),
                                     "person_id",
                                     ]
            if multiple_orgs:
                list_fields.insert(0, "organisation_id")

            # Configure reports
            axes = [(T("Pool"), "person_id$pool_membership.group_id"),
                    (T("Deploying Organisation"), "organisation_id"),
                    "status",
                    ]
            facts = [(T("Number of Deployments"), "count(id)"),
                     (T("Number of Volunteers"), "count(person_id)"),
                     ]
            default_rows = "organisation_id" if multiple_orgs else "status"
            report_options = {
                "rows": axes,
                "cols": axes,
                "fact": facts,
                "defaults": {"rows": default_rows,
                             "cols": "person_id$pool_membership.group_id",
                             "fact": facts[0],
                             "totals": True,
                             },
                }

            r.resource.configure(list_fields = list_fields,
                                 orderby = orderby,
                                 report_options = report_options,
                                 )

            # Set method for Ajax-lookup of notification data
            from .notifications import InlineNotificationsData
            s3db.set_method("hrm", "delegation",
                            method = "notifications",
                            action = InlineNotificationsData,
                            )
            return result
        s3.prep = custom_prep

        attr = dict(attr)
        if volunteer_id:
            attr["rheader"] = rlp_vol_rheader
        else:
            attr["rheader"] = rlp_delegation_rheader

        return attr

    settings.customise_hrm_delegation_controller = customise_hrm_delegation_controller
    # -------------------------------------------------------------------------
    def customise_hrm_competency_resource(r, tablename):

        s3db = current.s3db

        table = s3db.hrm_competency
        field = table.skill_id
        field.label = T("Skill / Resource")

        field = table.organisation_id
        field.readable = field.writable = False

        field = table.competency_id
        field.readable = field.writable = False

        s3db.configure("hrm_competency",
                       list_fields = ["person_id",
                                      "skill_id",
                                      "comments",
                                      ],
                       )

    settings.customise_hrm_competency_resource = customise_hrm_competency_resource
    # -------------------------------------------------------------------------
    # Comment/uncomment modules here to disable/enable them
    # Modules menu is defined in modules/eden/menu.py
    settings.modules = OrderedDict([
        # Core modules which shouldn't be disabled
        ("default", Storage(
            name_nice = T("Home"),
            restricted = False, # Use ACLs to control access to this module
            access = None,      # All Users (inc Anonymous) can see this module in the default menu & access the controller
            module_type = None  # This item is not shown in the menu
        )),
        ("admin", Storage(
            name_nice = T("Administration"),
            #description = "Site Administration",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
            module_type = None  # This item is handled separately for the menu
        )),
        ("appadmin", Storage(
            name_nice = T("Administration"),
            #description = "Site Administration",
            restricted = True,
            module_type = None  # No Menu
        )),
        ("errors", Storage(
            name_nice = T("Ticket Viewer"),
            #description = "Needed for Breadcrumbs",
            restricted = False,
            module_type = None  # No Menu
        )),
        #("sync", Storage(
        #    name_nice = T("Synchronization"),
        #    #description = "Synchronization",
        #    restricted = True,
        #    access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
        #    module_type = None  # This item is handled separately for the menu
        #)),
        #("tour", Storage(
        #    name_nice = T("Guided Tour Functionality"),
        #    module_type = None,
        #)),
        #("translate", Storage(
        #    name_nice = T("Translation Functionality"),
        #    #description = "Selective translation of strings based on module.",
        #    module_type = None,
        #)),
        ("gis", Storage(
            name_nice = T("Map"),
            #description = "Situation Awareness & Geospatial Analysis",
            restricted = True,
            module_type = 6,     # 6th item in the menu
        )),
        ("pr", Storage(
            name_nice = T("Person Registry"),
            #description = "Central point to record details on People",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu (access to controller is possible to all still)
            module_type = 10
        )),
        ("org", Storage(
            name_nice = T("Organizations"),
            #description = 'Lists "who is doing what & where". Allows relief agencies to coordinate their activities',
            restricted = True,
            module_type = 1
        )),
        # HRM is required for access to default realm permissions
        ("hrm", Storage(
           name_nice = T("Staff"),
           #description = "Human Resources Management",
           restricted = True,
           module_type = 2,
        )),
        ("vol", Storage(
           name_nice = T("Volunteers"),
           #description = "Human Resources Management",
           restricted = True,
           module_type = 2,
        )),
        ("cms", Storage(
         name_nice = T("Content Management"),
         #description = "Content Management System",
         restricted = True,
         module_type = 10,
        )),
        ("doc", Storage(
            name_nice = T("Documents"),
            #description = "A library of digital resources, such as photos, documents and reports",
            restricted = True,
            module_type = 10,
        )),
        ("msg", Storage(
            name_nice = T("Messaging"),
            #description = "Sends & Receives Alerts via Email & SMS",
            restricted = True,
            # The user-visible functionality of this module isn't normally required. Rather it's main purpose is to be accessed from other modules.
            module_type = None,
        )),
        #("supply", Storage(
        #    name_nice = T("Supply Chain Management"),
        #    #description = "Used within Inventory Management, Request Management and Asset Management",
        #    restricted = True,
        #    module_type = None, # Not displayed
        #)),
        #("inv", Storage(
        #    name_nice = T("Warehouses"),
        #    #description = "Receiving and Sending Items",
        #    restricted = True,
        #    module_type = 4
        #)),
        #("asset", Storage(
        #    name_nice = T("Assets"),
        #    #description = "Recording and Assigning Assets",
        #    restricted = True,
        #    module_type = 5,
        #)),
        # Vehicle depends on Assets
        #("vehicle", Storage(
        #    name_nice = T("Vehicles"),
        #    #description = "Manage Vehicles",
        #    restricted = True,
        #    module_type = 10,
        #)),
        #("req", Storage(
        #   name_nice = T("Requests"),
        #   #description = "Manage requests for supplies, assets, staff or other resources. Matches against Inventories where supplies are requested.",
        #   restricted = True,
        #   module_type = 10,
        #)),
        #("project", Storage(
        #    name_nice = T("Projects"),
        #    #description = "Tracking of Projects, Activities and Tasks",
        #    restricted = True,
        #    module_type = 2
        #)),
        #("cr", Storage(
        #    name_nice = T("Shelters"),
        #    #description = "Tracks the location, capacity and breakdown of victims in Shelters",
        #    restricted = True,
        #    module_type = 10
        #)),
        #("hms", Storage(
        #    name_nice = T("Hospitals"),
        #    #description = "Helps to monitor status of hospitals",
        #    restricted = True,
        #    module_type = 10
        #)),
        #("br", Storage(
        #   name_nice = T("Beneficiary Registry"),
        #   #description = "Allow affected individuals & households to register to receive compensation and distributions",
        #   restricted = True,
        #   module_type = 10,
        #)),
        #("event", Storage(
        #    name_nice = T("Events"),
        #    #description = "Activate Events (e.g. from Scenario templates) for allocation of appropriate Resources (Human, Assets & Facilities).",
        #    restricted = True,
        #    module_type = 10,
        #)),
        #("transport", Storage(
        #   name_nice = T("Transport"),
        #   restricted = True,
        #   module_type = 10,
        #)),
        #("stats", Storage(
        #    name_nice = T("Statistics"),
        #    #description = "Manages statistics",
        #    restricted = True,
        #    module_type = None,
        #)),
    ])

# =============================================================================
def rlp_active_deployments(ctable, from_date=None, to_date=None):
    """
        Helper to construct a component filter expression
        for active deployments within the given interval (or now)

        @param ctable: the (potentially aliased) component table
        @param from_date: start of the interval
        @param to_date: end of the interval

        @note: with no dates, today is assumed as the interval start+end
    """

    start = ctable.date
    end = ctable.end_date

    if not from_date and not to_date:
        from_date = to_date = current.request.utcnow

    if from_date and to_date:
        query = ((start <= to_date) | (start == None)) & \
                ((end >= from_date) | (end == None))
    elif to_date:
        query = (start <= to_date) | (start == None)
    else:
        query = (start >= from_date) | (end >= from_date)

    return query & ctable.status.belongs(("APPR", "IMPL"))

# =============================================================================
def rlp_deployed_with_org(person_id):
    """
        Check whether volunteer has an active or upcoming deployment
        managed by the current user (i.e. where user is either HRMANAGER
        for the deploying organisation, or COORDINATOR)
    """

    s3 = current.response.s3

    # Cache in response.s3 (we may need to check this at several points)
    deployed_with_org = s3.rlp_deployed_with_org
    if not deployed_with_org:
        deployed_with_org = s3.rlp_deployed_with_org = set()
    elif person_id in deployed_with_org:
        return True

    s3db = current.s3db
    now = current.request.utcnow

    deployed = lambda ctable: rlp_active_deployments(ctable, now)
    s3db.add_components("pr_person",
                        hrm_delegation = {"name": "deployment",
                                          "joinby": "person_id",
                                          "filterby": deployed,
                                          },
                        )

    resource = s3db.resource("pr_person",
                             id = person_id,
                             filter = FS("deployment.id") != None,
                             )
    rows = resource.select(["deployment.id"],
                           as_rows = True,
                           limit = 1,
                           )
    if not rows:
        return False

    deployed_with_org.add(person_id)
    return True

# =============================================================================
def rlp_vol_rheader(r, tabs=None):
    """ Custom rheader for vol/person """

    if r.representation != "html":
        # Resource headers only used in interactive views
        return None

    from s3 import s3_rheader_resource, S3ResourceHeader

    tablename, record = s3_rheader_resource(r)
    if tablename != r.tablename:
        resource = current.s3db.resource(tablename, id=record.id)
    else:
        resource = r.resource

    rheader = None
    rheader_fields = []

    if record:

        T = current.T
        db = current.db
        s3db = current.s3db
        auth = current.auth

        coordinator = auth.s3_has_role("COORDINATOR")

        if tablename == "pr_person":

            if coordinator:
                delegation_tab = (T("Recruitment"), "delegation")
            else:
                delegation_tab = (T("Recruitment"), "delegation/")

            if not tabs:
                tabs = [(T("Personal Data"), None),
                        (T("Skills / Resources"), "competency"),
                        delegation_tab,
                        ]

            volunteer = resource.select(["person_details.alias",
                                         "pool_membership.group_id",
                                         "pool_membership.group_id$group_type",
                                         "date_of_birth",
                                         "age",
                                         "occupation_type_person.occupation_type_id",
                                         "volunteer_record.site_id",
                                         ],
                                        represent = True,
                                        raw_data = True,
                                        ).rows
            if volunteer:
                # Extract volunteer details
                volunteer = volunteer[0]
                if coordinator or rlp_deployed_with_org(record.id):
                    name = s3_fullname
                else:
                    name = lambda row: volunteer["pr_person_details.alias"]
                pool = lambda row: volunteer["pr_pool_membership_group_membership.group_id"]
                age = lambda row: volunteer["pr_person.age"]
                occupation_type = lambda row: volunteer["pr_occupation_type_person.occupation_type_id"]
            else:
                # Target record exists, but doesn't match filters
                return None

            rheader_fields = [[(T("ID"), "pe_label"),
                               (T("Pool"), pool),
                               ],
                              [(T("Age"), age),
                               (T("Occupation Type"), occupation_type),
                               ],
                              [("", None),
                               ("", None),
                               ]
                              ]

            if coordinator:
                raw = volunteer["_row"]
                site_id = raw["hrm_volunteer_record_human_resource.site_id"]
                if site_id:
                    # Get site details
                    otable = s3db.org_office
                    query = (otable.site_id == site_id) & \
                            (otable.deleted == False)
                    office = db(query).select(otable.name,
                                              otable.phone1,
                                              otable.email,
                                              limitby = (0, 1),
                                              ).first()
                    if office:
                        rheader_fields[0].append((T("Office##gov"),
                                                  lambda row: office.name,
                                                  ))
                        rheader_fields[1].append((T("Office Phone##gov"),
                                                  lambda row: office.phone1,
                                                  ))
                        rheader_fields[2].append((T("Office Email##gov"),
                                                  lambda row: office.email,
                                                  ))

            open_pool_member = (volunteer["_row"]["pr_group.group_type"] == 21)
            if not coordinator and open_pool_member:
                # Recruitment hint
                from gluon import SPAN
                hint = lambda row: SPAN(T("Please contact the volunteer directly for deployment"),
                                        _class="direct-contact-hint"
                                        )
                rheader_fields.append([(None, hint, 5)])

        rheader = S3ResourceHeader(rheader_fields, tabs, title=name)(r,
                                                         table = resource.table,
                                                         record = record,
                                                         )
    return rheader

# =============================================================================
def rlp_profile_rheader(r, tabs=None):
    """ Custom rheader for default/person """

    if r.representation != "html":
        # Resource headers only used in interactive views
        return None

    from s3 import s3_rheader_resource, S3ResourceHeader

    tablename, record = s3_rheader_resource(r)
    if tablename != r.tablename:
        resource = current.s3db.resource(tablename, id=record.id)
    else:
        resource = r.resource

    rheader = None
    rheader_fields = []

    if record:

        T = current.T

        if tablename == "pr_person":

            tabs = [(T("Person Details"), None),
                    (T("User Account"), "user_profile"),
                    (T("Address"), "address"),
                    (T("Contact Information"), "contacts"),
                    (T("Skills"), "competency"),
                    ]

            rheader_fields = [[(T("ID"), "pe_label"),
                               ],
                              [(T("Name"), s3_fullname),
                               ],
                              ["date_of_birth",
                               ]
                              ]

        rheader = S3ResourceHeader(rheader_fields, tabs)(r,
                                                         table = resource.table,
                                                         record = record,
                                                         )
    return rheader

# =============================================================================
def rlp_org_rheader(r, tabs=None):
    """ ORG custom resource headers """

    if r.representation != "html":
        # Resource headers only used in interactive views
        return None

    from s3 import s3_rheader_resource, S3ResourceHeader

    tablename, record = s3_rheader_resource(r)
    if tablename != r.tablename:
        resource = current.s3db.resource(tablename, id=record.id)
    else:
        resource = r.resource

    rheader = None
    rheader_fields = []

    if record:
        T = current.T

        if tablename == "org_organisation":

            if not tabs:
                tabs = [(T("Organisation"), None),
                        (T("Administrative Offices"), "office"),
                        (T("Staff"), "human_resource"),
                        (T("Volunteer Pools"), "pool"),
                        ]

            rheader_fields = [["name",
                               ],
                              ]

        rheader = S3ResourceHeader(rheader_fields, tabs)(r,
                                                         table=resource.table,
                                                         record=record,
                                                         )
    return rheader

# =============================================================================
def rlp_delegation_rheader(r, tabs=None):
    """ hrm_delegation custom resource header """

    if r.representation != "html":
        # Resource headers only used in interactive views
        return None

    from s3 import s3_rheader_resource, S3ResourceHeader

    tablename, record = s3_rheader_resource(r)
    if tablename != r.tablename:
        resource = current.s3db.resource(tablename, id=record.id)
    else:
        resource = r.resource

    rheader = None
    rheader_fields = []

    if record:
        T = current.T

        if tablename == "hrm_delegation":

            if not tabs:
                tabs = [(T("Basic Details"), None),
                        (T("Notifications"), "delegation_message"),
                        (T("Notes"), "delegation_note"),
                        ]

            rheader_fields = [["organisation_id",
                               "date",
                               "status",
                               ],
                              ["person_id",
                               "end_date",
                               ],
                              ]

        rheader = S3ResourceHeader(rheader_fields, tabs)(r,
                                                         table=resource.table,
                                                         record=record,
                                                         )
    return rheader

# =============================================================================
class RLPAvailabilityFilter(S3DateFilter):
    """
        Date-Range filter with custom variable
        - without this then we parse as a vfilter which clutters error console
          & is inefficient (including preventing a bigtable optimisation)
    """

    @classmethod
    def _variable(cls, selector, operator):

        return super()._variable("available", operator)

# =============================================================================
class rlp_DelegatedPersonRepresent(S3Represent):

    def __init__(self, show_link=True, linkto=None):
        """
            Constructor

            @param show_link: show representation as clickable link
            @param linkto: URL for the link, using "[id]" as placeholder
                           for the record ID
        """

        super(rlp_DelegatedPersonRepresent, self).__init__(
                                                lookup = "pr_person",
                                                show_link = show_link,
                                                linkto = linkto,
                                                )

        self.coordinator = current.auth.s3_has_role("COORDINATOR")

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=None):
        """
            Custom rows lookup

            @param key: the key Field
            @param values: the values
            @param fields: unused (retained for API compatibility)
        """

        db = current.db
        s3db = current.s3db

        table = self.table

        count = len(values)
        if count == 1:
            query = (key == values[0])
        else:
            query = key.belongs(values)

        # Get the person names
        rows = db(query).select(table.id,
                                table.pe_label,
                                table.first_name,
                                table.middle_name,
                                table.last_name,
                                limitby = (0, count),
                                )
        self.queries += 1
        person_ids = {row.id for row in rows}

        # For all persons found, get the alias
        dtable = s3db.pr_person_details
        query = (dtable.person_id.belongs(person_ids)) & \
                (dtable.deleted == False)
        details = db(query).select(dtable.person_id, dtable.alias)
        aliases = {item.person_id: item.alias for item in details}
        self.queries += 1

        for row in rows:
            alias = aliases.get(row.id, "***")
            row.alias = alias if alias else "-"

        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row, prefix=None):
        """
            Represent a row

            @param row: the Row
        """

        if self.coordinator:
            repr_str = "[%s] %s" % (row.pe_label, s3_fullname(row))
        else:
            repr_str = "[%s] %s" % (row.pe_label, row.alias)

        return repr_str

    # -------------------------------------------------------------------------
    def link(self, k, v, row=None):
        """
            Represent a (key, value) as hypertext link

            @param k: the key (br_case_activity.id)
            @param v: the representation of the key
            @param row: the row with this key
        """

        url = URL(c = "vol", f = "person", args = [row.id], extension = "")

        return A(v, _href = url)

# END =========================================================================
