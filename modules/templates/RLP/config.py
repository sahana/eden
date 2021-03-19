# -*- coding: utf-8 -*-

"""
    Application Template for Rhineland-Palatinate (RLP) Crisis Management
    - used to manage Volunteer Pools for COVID-19 response

    @license MIT
"""

import datetime

from collections import OrderedDict

from gluon import current, redirect, URL, A, DIV, TABLE, TAG, TR
from gluon.storage import Storage

from s3 import FS, IS_LOCATION, S3DateFilter, S3Represent, s3_fieldmethod, s3_fullname, s3_yes_no_represent
from s3dal import original_tablename

from .helpers import rlp_active_deployments
#from ..RLPPTM.rlpgeonames import rlp_GeoNames

MSAGD = "Ministerium für Soziales, Arbeit, Gesundheit und Demografie"
ALLOWED_FORMATS = ("html", "iframe", "popup", "aadata", "json", "xls", "pdf")

# =============================================================================
def config(settings):

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
    settings.auth.password_retrieval = True

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

    # Use custom geocoder (disabled until production-ready)
    #if rlp_GeoNames.enable:
    #    settings.gis.geocode_service = rlp_GeoNames

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

    settings.pr.availability_json_rules = True

    # -------------------------------------------------------------------------
    settings.hrm.record_tab = False
    settings.hrm.staff_experience = False
    settings.hrm.use_certificates = False
    settings.hrm.use_credentials = False
    settings.hrm.use_description = False
    settings.hrm.use_trainings = False

    # -------------------------------------------------------------------------
    settings.org.projects_tab = False
    settings.org.default_organisation = MSAGD

    # -------------------------------------------------------------------------
    # Custom group types for volunteer pools
    #
    pool_types = {21: T("Open Pool"),
                  22: T("Managed Pool"),
                  }
    pool_type_ids = list(pool_types.keys())

    # Override in models/000_config.py with site-specific file name
    settings.custom.poolrules = "poolrules.default.xml"

    # -------------------------------------------------------------------------
    # UI Settings
    settings.ui.calendar_clear_icon = True

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


        s3db = current.s3db

        from s3 import S3SQLCustomForm, S3SQLInlineComponent, S3SQLInlineLink

        record = r.record
        if r.tablename == "cms_series" and \
           record and record.name == "Announcements":

            table = s3db.cms_post
            field = table.priority
            field.readable = field.writable = True

            crud_fields = ["name",
                           "body",
                           "priority",
                           "date",
                           "expired",
                           S3SQLInlineLink("roles",
                                           label = T("Roles"),
                                           field = "group_id",
                                           ),
                           ]
            list_fields = ["date",
                           "priority",
                           "name",
                           "body",
                           "post_role.group_id",
                           "expired",
                           ]
            orderby = "cms_post.date desc"
        else:
            crud_fields = ["name",
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
                           ]
            list_fields = ["post_module.module",
                           "post_module.resource",
                           "name",
                           "date",
                           "comments",
                           ]
            orderby = "cms_post.name"

        s3db.configure("cms_post",
                       crud_form = S3SQLCustomForm(*crud_fields),
                       list_fields = list_fields,
                       orderby = orderby,
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

        T = current.T

        s3db = current.s3db

        if r.tablename == "org_organisation" and not r.component:

            # Use custom form with email-address
            from s3 import S3SQLCustomForm, \
                           S3SQLInlineComponent, \
                           S3SQLInlineLink

            crud_fields = ["name",
                           "acronym",
                           S3SQLInlineLink(
                                "organisation_type",
                                field = "organisation_type_id",
                                search = False,
                                label = T("Type"),
                                multiple = settings.get_org_organisation_types_multiple(),
                                widget = "multiselect",
                                ),
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
                           "phone",
                           "website",
                           "logo",
                           "comments",
                           ]

            s3db.configure("org_organisation",
                           crud_form = S3SQLCustomForm(*crud_fields),
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
        from .rheaders import rlp_org_rheader
        attr = dict(attr)
        attr["rheader"] = rlp_org_rheader

        return attr

    settings.customise_org_organisation_controller = customise_org_organisation_controller

    # -------------------------------------------------------------------------
    def customise_org_office_resource(r, tablename):

        if r.interactive:

            from s3 import S3SQLCustomForm, S3SQLInlineLink
            crud_fields = ["name",
                            #"code",
                            "organisation_id",
                            "office_type_id",
                            S3SQLInlineLink("facility_type",
                                            field = "facility_type_id",
                                            label = T("Facility Type"),
                                            cols = 3,
                                            ),
                            "location_id",
                            "phone1",
                            "phone2",
                            "email",
                            "fax",
                            "obsolete",
                            "comments",
                            ]

            list_fields = ["id",
                           "name",
                           "office_type_id",
                           "organisation_id",
                           "location_id",
                            "phone1",
                            "phone2",
                            "email",
                            "fax",
                           ]

            current.s3db.configure("org_office",
                                   crud_form = S3SQLCustomForm(*crud_fields),
                                   list_fields = list_fields,
                                   )

    settings.customise_org_office_resource = customise_org_office_resource

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
    def customise_org_facility_type_resource(r, tablename):

        table = current.s3db.org_facility_type
        field = table.vol_deployments
        field.readable = field.writable = True

        current.s3db.configure("org_facility_type",
                               list_fields = ["name",
                                              "vol_deployments",
                                              "comments",
                                              ],
                               )

    settings.customise_org_facility_type_resource = customise_org_facility_type_resource

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
                            # All phone numbers as a single "phonenumber" component
                            pr_contact = {"name": "phonenumber",
                                          "joinby": "pe_id",
                                          "filterby": {
                                            "contact_method": ("SMS", "HOME_PHONE", "WORK_PHONE"),
                                          },
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
    def postprocess_person_select(records, rfields=None, represent=False, as_rows=False):
        """
            Post-process resource.select of pr_person to suppress
            field data the user is not permitted to see

            @param records: list of selected data
            @param rfields: list of S3ResourceFields in the records
            @param represent: records contain represented data
            @param as_rows: records are bare Rows rather than extracted
                            Storage
        """

        auth = current.auth

        if auth.s3_has_role("COORDINATOR"):
            return

        db = current.db
        s3db = current.s3db

        person_ids = set(records.keys())

        # Exclude open pool members
        if person_ids:
            gtable = s3db.pr_group
            mtable = s3db.pr_group_membership
            left = gtable.on(gtable.id == mtable.group_id)
            query = (mtable.person_id.belongs(person_ids)) & \
                    (mtable.deleted == False) & \
                    (gtable.group_type == 21)
            rows = db(query).select(mtable.person_id,
                                    groupby = mtable.person_id,
                                    left = left,
                                    )
            person_ids = person_ids - {row.person_id for row in rows}

        # Exclude volunteers with active deployments that
        # are readable for the current user
        #if person_ids:
        #    today = current.request.utcnow.date()
        #    dtable = s3db.hrm_delegation
        #    query = auth.s3_accessible_query("read", dtable) & \
        #            dtable.person_id.belongs(person_ids) & \
        #            rlp_active_deployments(dtable, from_date=today) & \
        #            (dtable.deleted == False)
        #    rows = db(query).select(dtable.person_id,
        #                            )
        #    person_ids = person_ids - {row.person_id for row in rows}

        # For the remaining volunteers, override personal details
        # and contact information with static values
        HIDDEN = "***"
        static = {"pr_person.first_name": (HIDDEN, HIDDEN),
                  "pr_person.middle_name": (HIDDEN, HIDDEN),
                  "pr_person.last_name": (HIDDEN, HIDDEN),
                  #"pr_person.fullname": (HIDDEN, HIDDEN),
                  "pr_person_details.alias": (HIDDEN, HIDDEN),
                  "pr_phone_contact.value": (None, HIDDEN),
                  "pr_phonenumber_contact.value": (None, HIDDEN),
                  "pr_email_contact.value": (None, HIDDEN),
                  }
        for person_id in person_ids:

            row = records[person_id]

            for colname, values in static.items():
                if colname in row:
                    row[colname] = values[1] if represent else values[0]
                raw = row.get("_row")
                if raw:
                    raw[colname] = values[0]

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

        # Don't show deployment sites as links (pointless for most users)
        field = s3db.pr_person_availability_site.site_id
        field.represent = s3db.org_SiteRepresent(show_link = False)

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

        if r.tablename == "pr_person":
            table = r.table
            if not hasattr(table, "has_account"):
                table.has_account = s3_fieldmethod("has_account", has_account,
                                                   represent = s3_yes_no_represent,
                                                   )
            #if not hasattr(table, "fullname"):
            #    table.fullname = s3_fieldmethod("fullname", s3_fullname)
            if not r.record or r.representation != "html":
                s3db.configure("pr_person",
                               postprocess_select = postprocess_person_select,
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
    def customise_volunteer_availability_fields(r):
        """
            Customise availability fields in volunteer form

            @param r: the current S3Request
        """

        from s3 import S3WeeklyHoursWidget, S3WithIntro, s3_text_represent

        avtable = current.s3db.pr_person_availability
        is_profile = r.controller == "default"

        # Enable hours/week
        field = avtable.hours_per_week
        field.readable = field.writable = True

        # Configure schedule_json
        field = avtable.schedule_json
        field.readable = field.writable = True
        if is_profile:
            # Add intro text for widget
            field.widget = S3WithIntro(field.widget,
                                       intro = ("pr", "person_availability", "HoursMatrixIntro"),
                                       )
        if r.representation == "xls":
            field.represent = lambda v: S3WeeklyHoursWidget.represent(v, html=False)
        else:
            field.represent = S3WeeklyHoursWidget.represent

        # Configure availability comments
        field = avtable.comments
        field.label = T("Availability Comments")
        field.represent = lambda v: s3_text_represent(v,
                                        lines = 8 if r.record else 5,
                                        _class = "avcomments",
                                        )
        if is_profile:
            # Add tooltip for availability comments
            field.comment = DIV(_class = "tooltip",
                                _title = "%s|%s" % (T("Availability Comments"),
                                                    T("Use this field to indicate e.g. vacation dates or other information with regard to your availability to facilitate personnel planning"),
                                                    ),
                                )
        else:
            field.comment = None

    # -------------------------------------------------------------------------
    def volunteer_list_fields(r, coordinator=False, name_fields=None):
        """
            Determine fields for volunteer list

            @param r: the current S3Request
            @param coordinator: user is COORDINATOR
            @param name_fields: name fields in order

            @returns: list of selectors (list_fields)
        """

        if name_fields is None:
            name_fields = []

        list_fields = [(T("Pool"), "pool_membership.group_id"),
                       (T("ID"), "pe_label"),
                       # name
                       "occupation_type_person.occupation_type_id",
                       (T("Hours/Wk"), "availability.hours_per_week"),
                       "availability.schedule_json",
                       "availability.comments",
                       #(T("Mobile Phone"), "phone.value"),
                       (T("Phone"), "phonenumber.value"),
                       # email
                       "current_address.location_id$addr_postcode",
                       (T("Place of Residence"), "current_address.location_id$L3"),
                       # office
                       # status
                       # current deployment
                       # account info
                       ]

        # Name
        if coordinator:
            list_fields[2:2] = name_fields
        else:
            list_fields.insert(2, (T("Name"), "person_details.alias"))

        # Additional fields for XLS/PDF
        if r.representation in ("xls", "pdf"):
            # Email address
            list_fields.insert(-2, (T("Email"), "email.value"))
            if coordinator:
                list_fields.append((T("Skills / Resources"), "competency.skill_id"))
                # Office information
                office = "volunteer_record.site_id$site_id:org_office"
                list_fields.extend([
                    (T("Office##gov"), "%s.name" % office),
                    (T("Office Phone##gov"), "%s.phone1" % office),
                    (T("Office Email##gov"), "%s.email" % office),
                    ])

        # Status, current deployment and account info as last columns
        if coordinator:
            from s3 import S3DateTime
            current.s3db.auth_user.created_on.represent = S3DateTime.datetime_represent

            list_fields.extend([
                "volunteer_record.status",
                (T("Current Deployment"), "ongoing_deployment.organisation_id"),
                (T("Deployed until"), "ongoing_deployment.end_date"),
                (T("has Account"), "has_account"),
                (T("Registered on"), "user.created_on"),
                ])

        return list_fields

    # -------------------------------------------------------------------------
    def volunteer_crud_form(coordinator = False,
                            show_contact_details = False,
                            name_fields = None
                            ):
        """
            Determine fields for volunteer form

            @param coordinator: user is COORDINATOR
            @param show_contact_details: show contact information
            @param name_fields: name fields in order

            @returns: list of form fields
        """

        from s3 import (S3SQLInlineComponent,
                        S3SQLInlineLink,
                        )

        crud_fields = [
                S3SQLInlineLink("pool",
                                field = "group_id",
                                multiple = False,
                                header = False,
                                search = False,
                                ),
                ]

        if coordinator:
            crud_fields.append("volunteer_record.status")

        if show_contact_details and name_fields:
            # Name fields in name-format order
            crud_fields.extend(name_fields)

        # Additional fields for COORDINATORS
        if coordinator:

            # Organisation and Office at the top
            crud_fields[0:0] = [
                "volunteer_record.organisation_id",
                (T("Office##gov"), "volunteer_record.site_id"),
                ]

            # Filter Office selector by Organisation
            script = '''$.filterOptionsS3({
'trigger':'sub_volunteer_record_organisation_id',
'target':'sub_volunteer_record_site_id',
'lookupPrefix':'org',
'lookupResource':'office',
'lookupKey':'organisation_id',
'lookupField':'site_id',
'optional':true
})'''
            s3 = current.response.s3
            if script not in s3.jquery_ready:
                s3.jquery_ready.append(script)

            # Other COORDINATOR-specific fields
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

        # Contact details if permitted
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
        from gluon import IS_IN_SET
        from .helpers import rlp_deployment_sites
        crud_fields.extend([
                S3SQLInlineLink("occupation_type",
                               label = T("Occupation Type"),
                               field = "occupation_type_id",
                               ),
                (T("Occupation / Speciality"), "person_details.occupation"),
                "availability.hours_per_week",
                "availability.schedule_json",
                S3SQLInlineLink("availability_sites",
                                field = "site_id",
                                label = T("Possible Deployment Sites"),
                                requires = IS_IN_SET(rlp_deployment_sites(),
                                                     multiple = True,
                                                     zero = None,
                                                     sort = False,
                                                     ),
                                render_list = True,
                                ),
                "availability.comments",
                "volunteer_record.comments",
                ])

        return crud_fields

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

            controller = r.controller

            from gluon import IS_NOT_EMPTY
            from s3 import (IS_ONE_OF,
                            IS_PERSON_GENDER,
                            S3AgeFilter,
                            S3LocationFilter,
                            S3LocationSelector,
                            S3OptionsFilter,
                            S3RangeFilter,
                            S3SQLCustomForm,
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

            # Availability
            customise_volunteer_availability_fields(r)

            # Configure Location Selector
            atable = s3db.pr_address
            field = atable.location_id
            field.requires = IS_LOCATION() # Mandatory
            field.widget = S3LocationSelector(levels = ("L1", "L2", "L3"),
                                              required_levels = ("L1", "L2", "L3"),
                                              show_address = True,
                                              show_postcode = True,
                                              postcode_required = True,
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

            if controller == "vol":
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
                from .helpers import RLPAvailabilityFilter, \
                                        RLPAvailabilitySiteFilter, \
                                        rlp_deployment_sites
                if not record:
                    # Apply custom filters
                    RLPAvailabilityFilter.apply_filter(resource, get_vars)
                    RLPAvailabilitySiteFilter.apply_filter(resource, get_vars)

                    # Ongoing deployments as component
                    s3db.add_components("pr_person",
                                        hrm_delegation = {"name": "ongoing_deployment",
                                                          "joinby": "person_id",
                                                          "filterby": rlp_active_deployments,
                                                          },
                                        )

                    # Currently-Deployed-Filter
                    deployed_now = get_vars.get("deployed_now") == "1"
                    if deployed_now:
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

                    # Show names and contact details if:
                    # - user is COORDINATOR, or
                    # - volunteer viewed is an open pool member, or
                    # - has an approved deployment the user can access
                    person_id = record.id if record else None
                    if person_id:
                        from .helpers import rlp_deployed_with_org
                        show_contact_details = coordinator or \
                                               open_pool_member(person_id) or \
                                               rlp_deployed_with_org(person_id)
                        if not show_contact_details:
                            name_fields = []
                    else:
                        show_contact_details = True

                    # List fields
                    list_fields = volunteer_list_fields(r,
                                                        coordinator = coordinator,
                                                        name_fields = name_fields,
                                                        )

                    # CRUD fields
                    crud_fields = volunteer_crud_form(coordinator = coordinator,
                                                      show_contact_details = show_contact_details,
                                                      name_fields = name_fields,
                                                      )

                    # Filters
                    if coordinator:
                        # Coordinators can search by ID and names
                        text_search_fields = name_fields + ["pe_label"]
                    else:
                        # Other users can search by ID and Alias
                        text_search_fields = ["person_details.alias",
                                              "pe_label",
                                              ]
                    text_search_fields.append("person_details.occupation")

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
                        S3LocationFilter("current_address.location_id",
                                         label = T("Place of Residence"),
                                         levels = ("L2", "L3"),
                                         ),
                        RLPAvailabilityFilter("delegation.date",
                                              label = T("Available"),
                                              #hide_time = True,
                                              ),
                        S3OptionsFilter("availability.days_of_week",
                                        label = T("On Weekdays"),
                                        options = OrderedDict((
                                                    (1, T("Mon##weekday")),
                                                    (2, T("Tue##weekday")),
                                                    (3, T("Wed##weekday")),
                                                    (4, T("Thu##weekday")),
                                                    (5, T("Fri##weekday")),
                                                    (6, T("Sat##weekday")),
                                                    (0, T("Sun##weekday")),
                                                    )),
                                        cols = 7,
                                        sort = False,
                                        ),
                        RLPAvailabilitySiteFilter("availability_site.site_id",
                                                  label = T("Possible Deployment Sites"),
                                                  options = lambda: rlp_deployment_sites(managed_orgs=True),
                                                  sort = False,
                                                  ),
                        S3RangeFilter("availability.hours_per_week",
                                      ),
                        S3OptionsFilter("competency.skill_id",
                                        label = T("Skills / Resources"),
                                        options = lambda: s3_get_filter_opts("hrm_skill"),
                                        cols = 2,
                                        ),
                        S3AgeFilter("date_of_birth",
                                    label = T("Age"),
                                    minimum = 12,
                                    maximum = 90,
                                    ),
                        ]

                    # Reports
                    axes = [(T("Pool"), "pool_membership.group_id"),
                            (T("Office##gov"), "volunteer_record.site_id"),
                            "occupation_type_person.occupation_type_id",
                            ]
                    facts = [(T("Number of Volunteers"), "count(id)"),
                             (T("Hours per Week"), "sum(availability.hours_per_week)"),
                             ]
                    report_options = {
                        "rows": axes,
                        "cols": axes,
                        "fact": facts,
                        "defaults": {"rows": "pool_membership.group_id",
                                     "cols": None,
                                     "fact": facts[1],
                                     "totals": True,
                                     },
                        }

                    resource.configure(crud_form = S3SQLCustomForm(*crud_fields),
                                       filter_widgets = filter_widgets,
                                       list_fields = list_fields,
                                       # Extra fields for computation of virtual fields
                                       extra_fields = [#"first_name",
                                                       #"last_name",
                                                       "date_of_birth",
                                                       "user.id",
                                                       ],
                                       report_options = report_options,
                                       )

                elif r.component_name == "delegation":

                    # HRMANAGERs and ADMINs see the list
                    if not has_role("HRMANAGER") and \
                       r.interactive and r.method is None and not r.component_id:
                        r.method = "organize"

            elif controller == "default":
                # Personal profile (default/person)
                if not r.component:

                    # Check if volunteer
                    volunteer_id = None
                    if r.id:
                        rows = r.resource.select(["volunteer_record.id"], limit = 1).rows
                        if rows:
                            volunteer_id = rows[0]["hrm_volunteer_record_human_resource.id"]

                    # Custom Form
                    from gluon import IS_IN_SET
                    from s3 import S3SQLInlineLink, S3WithIntro
                    from .helpers import rlp_deployment_sites
                    crud_fields = name_fields
                    if volunteer_id:
                        # Volunteer-specific fields
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
                                            "availability.schedule_json",
                                            S3WithIntro(
                                                S3SQLInlineLink("availability_sites",
                                                        field = "site_id",
                                                        label = T("Possible Deployment Sites"),
                                                        requires = IS_IN_SET(rlp_deployment_sites(),
                                                                            multiple = True,
                                                                            zero = None,
                                                                            sort = False,
                                                                            ),
                                                        render_list = True,
                                                        ),
                                                # Widget intro text from CMS
                                                intro = ("pr", "person_availability_site", "AvailabilitySitesIntro"),
                                                ),
                                            "availability.comments",
                                            "volunteer_record.comments",
                                            ])

                    from .helpers import rlp_update_pool
                    resource.configure(crud_form = S3SQLCustomForm(*crud_fields,
                                                        postprocess = rlp_update_pool if volunteer_id else None,
                                                        ),
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
               not r.component and \
               isinstance(output, dict):
                # Geocoder
                #s3.scripts.append("/%s/static/themes/RLP/js/geocoder.js" % r.application)
                #if r.record:
                #    s3.jquery_ready.append('''S3.rlp_GeoCoder("sub_defaultaddress_defaultaddress_i_location_id_edit_0")''')
                #else:
                #    s3.jquery_ready.append('''S3.rlp_GeoCoder("sub_defaultaddress_defaultaddress_i_location_id_edit_none")''')
                #s3.js_global.append('''i18n.location_found="%s"
#i18n.location_not_found="%s"''' % (T("Location Found"),
                #                   T("Location NOT Found"),
                #                   ))
                if r.record and \
                   r.method in (None, "update", "read"):

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
        from .rheaders import rlp_vol_rheader, rlp_profile_rheader
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
                        "APPR": ("APPR", "CANC", "IMPL", "NVLD"),
                        "IMPL": ("IMPL", "CANC", "NVLD"),
                        }
            if current.auth.s3_has_role("COORDINATOR"):
                workflow["REQ"] = ("REQ", "APPR", "DECL", "NVLD")
            else:
                workflow["REQ"] = ("REQ", "CANC", "NVLD")
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

        return next_status

    # -------------------------------------------------------------------------
    def delegation_free_interval(target, occupied, recurse=False, original=None):
        """
            Determine possible alternative time intervals for
            delegation requests

            @param target: the requested interval (start, end)
            @param occupied: the occupied intervals colliding with the target
            @param recurse: recursive call
            @param original: the original target (in recursive calls)

            @returns: the original target if no conflicts were found, or
                      an interval correction as tuple (start, end)
                      - start is None if only the end date needs correction
                      - end is None if only the start date needs correction
                      ...or None if no alternatives were found
        """

        if not recurse:
            # Sort occupied intervals by their start date
            occupied = sorted(occupied, key=lambda i: i[0] or datetime.date.min)

        # Calculate target and minimum duration
        if target[0] and target[1]:
            duration = (target[1] - target[0]).days
            if duration < 0:
                target = (target[1], target[0])
            duration = abs(duration)
            if not recurse and duration > 6:
                min_duration = 4 * duration // 5
            else:
                min_duration = duration
        else:
            duration = None
            min_duration = None

        deployment, other = occupied[0], occupied[1:]
        if deployment[0] and target[1] and deployment[0] > target[1]:
            # Target interval ends before deployment
            # => accept
            return target

        if deployment[1] and target[0] and deployment[1] < target[0]:
            # Deployment ends before target interval
            # => accept if no other deployments, otherwise check against those
            return target if not other else \
                        delegation_free_interval(target, other,
                                                 recurse = recurse,
                                                 original = original,
                                                 )

        # Try a shorter interval
        # => only if original start date can be kept, i.e. no recursion
        if not recurse and min_duration is not None and \
           deployment[0] and target[0] and deployment[0] > target[0]:
            max_duration = (deployment[0] - target[0]).days
            if max_duration >= min_duration:
                # Minimum duration would be available before
                # earliest deployment => propose new end-date
                return (None, deployment[0] - datetime.timedelta(days=1))

        if not deployment[1]:
            # Deployment has no end-date, so no free interval after that
            return None

        # Compute and validate new start-date
        new_start = deployment[1] + datetime.timedelta(days=1)
        if not original:
            original = target
        if original[1] and new_start > original[1]:
            # Earliest possible start-date lies after original
            # target interval, so no acceptable alternatives
            accept = None
        elif other:
            # Compute new end-date & recurse
            new_end = None if duration is None else \
                        new_start + datetime.timedelta(days=duration)
            accept = delegation_free_interval((new_start, new_end), other,
                                              recurse = True,
                                              original = original,
                                              )
        else:
            # No further deployments => propose new start date
            accept = (new_start, None)

        return accept

    # -------------------------------------------------------------------------
    def delegation_onvalidation(form):
        """
            Custom onvalidation routine for delegations:
            - prevent new request if the volunteer already has an approved
              delegation during the date interval
            - if possible, suggest alternative date interval for new requests
              if the current one would overlap already-approved delegations
            - prevent approval of requests if they overlap another already
              approved delegation
        """

        # Get the record ID
        form_vars = form.vars
        if "id" in form_vars:
            record_id = form_vars.id
        elif hasattr(form, "record_id"):
            record_id = form.record_id
        else:
            record_id = None

        db = current.db
        table = current.s3db.hrm_delegation

        delegation = {"id": record_id}
        missing = []

        # Check if person_id, status, date and end_date are in form
        for fn in ("person_id", "date", "end_date", "status"):
            if fn in form_vars:
                delegation[fn] = form_vars[fn]
            else:
                missing.append(fn)

        # Handle missing fields
        if missing:
            if record_id:
                # Look up from record
                row = db(table.id == record_id).select(*missing,
                                                       limitby=(0, 1),
                                                       ).first()
                if row:
                    for fn in missing:
                        delegation[fn] = row[fn]
            else:
                # Use defaults
                for fn in missing:
                    default = table[fn].default
                    if default:
                        delegation[fn] = default

        # Validate
        person_id = delegation["person_id"]
        if not person_id:
            # Nothing we can check
            return

        status = delegation["status"] or "REQ"
        if status in ("CANC", "NVLD", "DECL", "RJCT"):
            # No check required, just accept
            return

        start = delegation.get("date")
        end = delegation.get("end_date")

        # Look up overlapping delegations
        query = (table.person_id == person_id)
        if start or end:
            query &= rlp_active_deployments(table, start, end)
        else:
            query &= (table.status.belongs(("APPR", "IMPL")))
        if record_id:
            query &= (table.id != record_id)
        query &= (table.deleted == False)

        overlapping = db(query).select(table.id,
                                       limitby = (0, 1),
                                       ).first()
        if overlapping:

            if status == "REQ":
                # Find suitable alternative
                query = (table.person_id == person_id) & \
                        rlp_active_deployments(table, start)
                if record_id:
                    query &= (table.id != record_id)
                query &= (table.deleted == False)
                rows = db(query).select(table.date,
                                        table.end_date,
                                        )
                occupied = [(row.date, row.end_date) for row in rows]
                alternative = delegation_free_interval((start, end), occupied)
                field = None
                if alternative is None:
                    msg = T("Please select another volunteer")
                elif not alternative[1]:
                    msg = T("Earliest possible start date: %(start)s")
                    field = "date"
                elif not alternative[0]:
                    msg = T("Latest possible end date: %(end)s")
                    field = "end_date"
                elif alternative[0] != start or alternative[1] != end:
                    msg = T("Next possible interval for deployment: %(start)s - %(end)s")
                else:
                    msg = None
                if msg:
                    if alternative:
                        dtformat = current.calendar.format_date
                        msg = msg % {"start": dtformat(alternative[0], local=True),
                                     "end": dtformat(alternative[1], local=True),
                                     }
                    if field:
                        form.errors[field] = msg
                    else:
                        form.errors.date = T("Volunteer already deployed in this time intervall")
                        current.response.information = msg
            else:
                form.errors.date = T("Volunteer already deployed in this time intervall")

    # -------------------------------------------------------------------------
    def delegation_onaccept(form):
        """
            Custom onaccept routine for delegations:
            - if a request has been newly approved, close all other pending
              requests overlapping the same date interval
        """

        # Get the record ID
        form_vars = form.vars
        if "id" in form_vars:
            record_id = form_vars.id
        else:
            record_id = None

        db = current.db
        table = current.s3db.hrm_delegation

        delegation = {"id": record_id}
        missing = []

        # Check if person_id, status, date and end_date are in form
        for fn in ("person_id", "date", "end_date", "status"):
            if fn in form_vars:
                delegation[fn] = form_vars[fn]
            else:
                missing.append(fn)

        # Handle missing fields
        if missing and record_id:
            # Look up from record
            row = db(table.id == record_id).select(*missing,
                                                   limitby=(0, 1),
                                                   ).first()
            if row:
                for fn in missing:
                    delegation[fn] = row[fn]

        try:
            record = form.record
        except AttributeError:
            record = None
        person_id = delegation.get("person_id")
        if record and record.status != "APPR" and \
           delegation.get("status") == "APPR" and record_id and person_id:
            query = (table.person_id == person_id) & \
                    (table.status == "REQ")
            start = delegation.get("date")
            if start:
                query &= (table.end_date >= start)
            end = delegation.get("end_date")
            if end:
                query &= (table.date <= end)
            query &= (table.id != record_id) & (table.deleted == False)
            num = db(query).update(status = "DECL")
            if num:
                msg = T("%(num)s other pending request(s) for the same time interval declined")
                current.response.warning = msg % {"num": num}

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

        auth = current.auth
        coordinator = auth.s3_has_role("COORDINATOR")

        # Basic organizer configuration
        organize = {"start": "date",
                    "end": "end_date",
                    "start_editable": coordinator,
                    "color": "status",
                    "colors": {"REQ":  "#d554a2",
                               "APPR": "#408d40",
                               "DECL": "#303030",
                               "CANC": "#d0d0d0",
                               "IMPL": "#40879c",
                               "NVLD": "#333333",
                               },
                    }

        table = s3db.hrm_delegation

        # Custom representation of person_id
        from .helpers import RLPDelegatedPersonRepresent
        field = table.person_id
        field.represent = RLPDelegatedPersonRepresent()

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
                            TR(represent("NVLD"), T("Invalid Record")),
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

            # Can insert on tab
            s3db.configure("hrm_delegation", insertable = bool(volunteer_id))

            # Apply delegation workflow rules, determine earliest start date
            record = r.record
            if record:
                min_date = min(record.date, tomorrow) if record.date else tomorrow
            elif not coordinator:
                min_date = tomorrow
            next_status = delegation_workflow(r.resource.table, record, person_id=volunteer_id)

        elif r.component.tablename == "hrm_delegation":
            # On tab of volunteer file
            if r.component_id:
                r.component.load()
                record = r.component._rows[0]
            else:
                r.component.add_filter(FS("status") != "NVLD")
                record = None

            volunteer_id = r.id
            next_status = delegation_workflow(r.component.table, record, person_id=volunteer_id)

            # Determine earliest start date
            if record:
                min_date = min(record.date, tomorrow) if record.date else tomorrow
            elif not coordinator:
                min_date = tomorrow

            organize["title"] = "organisation_id"
            organize["description"] = ["date",
                                       "end_date",
                                       "requested_on",
                                       "status",
                                       ]
        else:
            next_status = None

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

        # Configure custom forms
        auth = current.auth
        if auth.s3_has_role("COORDINATOR"):
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

        elif auth.s3_has_roles(("HRMANAGER", "VCMANAGER")):
            from s3 import S3SQLCustomForm
            crud_form = S3SQLCustomForm("organisation_id",
                                        "person_id",
                                        "date",
                                        "end_date",
                                        "requested_on",
                                        "status",
                                        "comments",
                                        )
            if not record or record.status != "APPR" and \
               next_status and "APPR" in next_status:
                # Request that can be approved

                # Lookup labels for selectable organisations
                field = table.organisation_id
                requires = field.requires
                if isinstance(requires, (list, tuple)):
                    requires = requires[0]
                if hasattr(requires, "options"):
                    represent = S3Represent(lookup="org_organisation")
                    options = requires.options()
                    organisations = represent.bulk([o[0] for o in options if o[0]])
                else:
                    organisations = None

                # Append inline-notifications
                from s3 import S3WithIntro
                from .notifications import InlineNotifications
                crud_form.append(
                    S3WithIntro(
                        InlineNotifications("notifications",
                                            label = T("Notifications"),
                                            person_id = volunteer_id,
                                            organisations = organisations,
                                            reply_to = "user", #"org",
                                            sender = "org",
                                            ),
                        intro = ("hrm", "delegation", "NotificationIntroOrg"),
                        ))
            s3db.configure("hrm_delegation", crud_form=crud_form)

            # Enable site_id and filter to sites of org
            #field = table.site_id
            #field.readable = field.writable = True
            #field.label = T("Deployment Site")
            #from s3 import IS_ONE_OF
            #field.requires = IS_EMPTY_OR(IS_ONE_OF(current.db, "org_site.site_id",
            #                                       s3db.org_site_represent,
            #                                       ))
            #script = '''$.filterOptionsS3({
            #'trigger':'organisation_id',
            #'target':'site_id',
            #'lookupURL':S3.Ap.concat('/org/sites_for_org/'),
            #})'''
            #current.response.s3.jquery_ready.append(script)

        # Reconfigure
        s3db.add_custom_callback("hrm_delegation",
                                 "onvalidation",
                                 delegation_onvalidation,
                                 )
        s3db.add_custom_callback("hrm_delegation",
                                 "onaccept",
                                 delegation_onaccept,
                                 )
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

        auth = current.auth
        coordinator = auth.s3_has_role("COORDINATOR")

        standard_prep = s3.prep
        def custom_prep(r):

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
                    # Obsolete (past, cancelled, implemented or invalid)
                    query = (FS("end_date") < today) | \
                            (FS("status").belongs(("DECL", "RJCT", "CANC", "IMPL", "NVLD")))
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

            elif r.method != "report":
                status_opts = ("REQ", "APPR", "DECL", "CANC", "IMPL")
                if not r.id:
                    r.resource.add_filter(FS("status") != "NVLD")

            from .helpers import rlp_delegation_read_multiple_orgs
            multiple_orgs = rlp_delegation_read_multiple_orgs()[0]

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
                        #default = ["APPR", "IMPL"] if r.method == "report" else None
                        filter_widgets.insert(0,
                            S3OptionsFilter("status",
                                            options = OrderedDict(status_filter_opts),
                                            #default = default,
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
                                     "person_id$occupation_type_person.occupation_type_id",
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

        standard_postp = s3.postp
        def custom_postp(r, output):

            # Call standard postp
            if callable(standard_postp):
                output = standard_postp(r, output)

            if r.controller == "vol" and volunteer_id and isinstance(output, dict):

                from s3 import S3CustomController

                method = r.method
                if not method:
                    # Add link to organizer
                    output["switch_btn"] = A(T("Switch to organizer"),
                                             _href = r.url(method="organize"),
                                             _class = "action-btn organizer-switch",
                                             _title = T("Manage deployments in a calendar view"),
                                             )

                    # Use custom view to keep organizer-link above form
                    S3CustomController._view("RLP", "delegation.html")

                elif method == "organize":
                    # Add hint how to use the organizer
                    if not coordinator:
                        from .helpers import get_cms_intro
                        intro = get_cms_intro("hrm", "delegation",
                                              "DelegationOrganizerIntro",
                                              cmsxml = True,
                                              )
                        if intro:
                            output["intro"] = intro
                    # Add switch to list view
                    output["switch"] = A(T("Switch to list view"),
                                         _href = r.url(method=""),
                                         _class = "action-btn",
                                         _title = T("Manage deployments in a table view"),
                                         )
                    # Use custom view
                    S3CustomController._view("RLP", "organize.html")

            return output
        s3.postp = custom_postp

        # Custom rheaders
        from .rheaders import rlp_vol_rheader, rlp_delegation_rheader
        attr = dict(attr)
        if volunteer_id:
            attr["rheader"] = rlp_vol_rheader
        else:
            attr["rheader"] = rlp_delegation_rheader

        return attr

    settings.customise_hrm_delegation_controller = customise_hrm_delegation_controller

    # -------------------------------------------------------------------------
    # Custom callbacks for competency changes in user profile
    #
    def hrm_competency_onaccept(form):

        try:
            record_id = form.vars.id
        except AttributeError:
            return

        table = current.s3db.hrm_competency
        query = (table.id == record_id) & (table.person_id != None)
        row = current.db(query).select(table.person_id,
                                       limitby = (0, 1),
                                       ).first()
        if row:
            from .helpers import rlp_update_pool
            rlp_update_pool(Storage(vars = Storage(id=row.person_id)))

    def hrm_competency_ondelete(row):

        person_id = row.person_id
        if person_id:
            from .helpers import rlp_update_pool
            rlp_update_pool(Storage(vars = Storage(id=person_id)))

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

        if r.controller == "default" and r.function == "person":
            volunteer_id = None
            if r.id:
                rows = r.resource.select(["volunteer_record.id"], limit = 1).rows
                if rows:
                    volunteer_id = rows[0]["hrm_volunteer_record_human_resource.id"]

            if volunteer_id:
                # Add custom callbacks to change pool membership if required
                # by pool rules
                s3db.add_custom_callback("hrm_competency", "onaccept",
                                         hrm_competency_onaccept,
                                         )
                s3db.add_custom_callback("hrm_competency", "ondelete",
                                         hrm_competency_ondelete,
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

# END =========================================================================
