# -*- coding: utf-8 -*-

import datetime

from collections import OrderedDict

from gluon import current, URL, A
from gluon.storage import Storage

from s3 import FS, S3Represent, s3_fullname
from s3dal import original_tablename

def config(settings):
    """
        Settings for Rhineland-Palatinate State's Deployment of Volunteers for the COVID-19 response
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
    #settings.auth.registration_requires_verification = True
    # Do new users need to be approved by an administrator prior to being able to login?
    #settings.auth.registration_requires_approval = True
    settings.auth.registration_requests_organisation = True
    # Required for access to default realm permissions
    settings.auth.registration_link_user_to = ["staff"]
    settings.auth.registration_link_user_to_default = ["staff"]
    # Disable password-retrieval feature
    settings.auth.password_retrieval = False

    settings.auth.realm_entity_types = ("org_organisation", "pr_forum", "pr_group")

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
       ("en", "English"),
       ("de", "German"),
    ])
    # Default language for Language Toolbar (& GIS Locations in future)
    settings.L10n.default_language = "de"
    # Uncomment to Hide the language toolbar
    #settings.L10n.display_toolbar = False
    # Default timezone for users
    settings.L10n.timezone = "Europe/Berlin"
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
    settings.org.projects_tab = False

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

        elif tablename == "pr_group":

            # Pools own themselves => default
            pass

        elif tablename == "pr_group_membership":

            # Pool membership is owned by the pool => default
            pass

        return realm_entity

    settings.auth.realm_entity = rlp_realm_entity

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

        # TODO embed contact information for pool

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
            - membership in volunteer pool (group_membership)
            - recruitment request (req_need)
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
                            req_need = {"link": "req_need_person",
                                        "joinby": "person_id",
                                        "key": "need_id",
                                        "actuate": "replace",
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
            # Skip uniqueness validator in imports
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

        # Configure components to inherit realm_entity from person
        s3db.configure("pr_person",
                       realm_components = ("hrm_human_resource",
                                           "hrm_competency",
                                           "pr_person_details",
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

            if r.controller == "vol":

                has_role = current.auth.s3_has_role
                coordinator = has_role("COORDINATOR")

                resource = r.resource

                # Filter to volunteers only
                resource.add_filter(FS("volunteer_record.id") != None)

                # Only COORDINATOR (and ADMIN) can see volunteers outside of pools
                if not coordinator:
                    resource.add_filter(FS("pool_membership.id") > 0)

                # Availability Filter
                get_vars = r.get_vars
                #start_date = get_vars.get("delegation.date__ge")
                start_date = get_vars.get("fake_start_date__ge")
                dfilter = get_vars.get("$filter")
                if start_date or dfilter:
                    if start_date:
                        #del get_vars["delegation.date__ge"]
                        del get_vars["fake_start_date__ge"]
                    if dfilter:
                        del get_vars["$filter"]
                        # Parse out the date from the $filter
                        end_date = dfilter.split('le "')[1].split('")')[0]
                    else:
                        end_date = None
                    # Include people with no delegations yet
                    #query = (FS("delegation.id") == None)
                    #if start_date and end_date:
                    #    # Both Start Date & End Date specified
                    #    query |= ~((FS("delegation.date") <= end_date) & \
                    #               ((FS("delegation.end_date") >= start_date) | \
                    #                (FS("delegation.end_date") == None)) & \
                    #               (FS("delegation.status").belongs(("APPR", "IMPL")))
                    #               )
                    #elif start_date:
                    #    # Just Start Date specified
                    #    # Exclude people with delegations still open at the start date
                    #    query |= ~(((FS("delegation.end_date") >= start_date) | \
                    #                (FS("delegation.end_date") == None)) & \
                    #               (FS("delegation.status").belongs(("APPR", "IMPL")))
                    #               )
                    #else:
                    #    # Just End Date specified
                    #    # Exclude people with delegations that start before the end date
                    #    query |= ~((FS("delegation.date") <= end_date) & \
                    #               (FS("delegation.status").belongs(("APPR", "IMPL")))
                    #               )
                    #resource.add_filter(query)
                    dtable = s3db.hrm_delegation
                    if start_date and end_date:
                        query = (dtable.date <= end_date) & \
                                ((dtable.end_date >= start_date) | \
                                 (dtable.end_date == None)) & \
                                (dtable.status.belongs(("APPR", "IMPL"))) & \
                                (dtable.deleted == False)
                    elif start_date:
                        query = ((dtable.end_date >= start_date) | \
                                 (dtable.end_date == None)) & \
                                (dtable.status.belongs(("APPR", "IMPL"))) & \
                                (dtable.deleted == False)
                    elif end_date:
                        query = (dtable.date <= end_date) & \
                                (dtable.status.belongs(("APPR", "IMPL"))) & \
                                (dtable.deleted == False)
                    busy_persons = db(query).select(dtable.person_id,
                                                    distinct = True)
                    busy_persons = [d.person_id for d in busy_persons]
                    query = ~(FS("id").belongs(busy_persons))
                    resource.add_filter(query)

                # HR type defaults to volunteer (already done in controller)
                #hrtable = s3db.hrm_human_resource
                #hrtable.type.default = 2

                if not r.component:

                    from gluon import IS_NOT_EMPTY
                    from s3 import (IS_ONE_OF,
                                    IS_PERSON_GENDER,
                                    S3AgeFilter,
                                    S3DateFilter,
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

                    # Hide map selector in address
                    atable = s3db.pr_address
                    field = atable.location_id
                    field.widget = S3LocationSelector(show_address = True,
                                                      show_map = False,
                                                      )

                    # Enable weekly hours
                    avtable = s3db.pr_person_availability
                    field = avtable.hours_per_week
                    field.readable = field.writable = True

                    # Hide add-link for organisation
                    hrcomponent = resource.components.get("volunteer_record")
                    hrtable = hrcomponent.table
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

                    # Hide comment for comments-field (field re-purposed)
                    field = hrtable.comments
                    field.comment = None

                    # Make last name mandatory
                    table = resource.table
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

                    # Adapt CRUD-strings => Volunteers
                    s3.crud_strings[resource.tablename] = Storage(
                        label_create = T("Create Volunteer"),
                        title_display = T("Volunteer Details"),
                        title_list = T("Volunteers"),
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
                                   "occupation_type_person.occupation_type_id",
                                   "availability.hours_per_week",
                                   "current_address.location_id$addr_postcode",
                                   (T("Place of Residence"), "current_address.location_id$L3"),
                                   ]

                    # Custom Form
                    crud_fields = [S3SQLInlineLink("pool",
                                                   field = "group_id",
                                                   multiple = False,
                                                   header = False,
                                                   search = False,
                                                   ),
                                   ]

                    # Only COORDINATOR can see personal details
                    if coordinator:
                        crud_fields.insert(0, "volunteer_record.organisation_id")

                        # Name fields in name-format order
                        NAMES = ("first_name", "middle_name", "last_name")
                        keys = StringTemplateParser.keys(settings.get_pr_name_format())
                        name_fields = [fn for fn in keys if fn in NAMES]

                        text_search_fields = name_fields + ["pe_label"]
                        list_fields[2:2] = name_fields

                        crud_fields.extend(name_fields)
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
                    else:
                        text_search_fields = ["person_details.alias", "pe_label"]
                        list_fields.insert(2, (T("Name"), "person_details.alias"))

                    # Show contact details for coordinator, or if open pool member
                    if coordinator or r.record and open_pool_member(r.record.id):
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
                                                        "options": "SMS",
                                                        },
                                            label = T("Mobile Phone"),
                                            multiple = False,
                                            name = "phone",
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
                    text_search_fields.append("person_details.occupation")

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
                        S3DateFilter([#"delegation.end_date",
                                      #"delegation.date",
                                      "fake_start_date",
                                      "fake_end_date",
                                      ],
                                     label = T("Available"),
                                     hide_time = True,
                                     # Using Custom filter in prep for now
                                     #negative = "delegation.id",
                                     #filterby = "delegation.status",
                                     #filter_opts = ["APPR", "IMPL"],
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
                                                       ],
                                       )

                elif r.component_name == "delegation":

                    # HRMANAGERs and ADMINs see the list
                    if not has_role("HRMANAGER") and \
                       r.interactive and r.method is None and not r.component_id:
                        r.method = "organize"
                    if coordinator:
                        s3db.add_custom_callback("hrm_delegation",
                                                 "onaccept",
                                                 hrm_delegation_update_onaccept,
                                                 method = "update",
                                                 )

            elif callable(standard_prep):
                result = standard_prep(r)

            return result
        s3.prep = custom_prep

        # Custom rheader in vol-perspective
        if current.request.controller == "vol":
            attr = dict(attr)
            attr["rheader"] = rlp_vol_rheader

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

        # Can never change person or organisation
        if record:
            field = table.person_id
            field.writable = False
            field = table.organisation_id
            field.writable = False

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
    def hrm_delegation_update_onaccept(form):
        """
            Coordinator has updated a Request
            - if this is an approval then send a notification

            @ToDo: Limit to Managed Pool Members, ignore for open recruitment.
        """

        form_vars_get = form.vars.get

        # Check new Status
        if form_vars_get("status") != "APPR":
            # Take no action
            return

        # Check old Status
        if form.record.status != "REQ":
            # Take no action
            return

        # Send Email to the Org & the Volunteer

        # Lookup Details
        db = current.db
        s3db = current.s3db

        organisation_id = form_vars_get("organisation_id")
        person_id = form_vars_get("person_id")
        start_date = form_vars_get("start_date")
        end_date = form_vars_get("end_date")
        comments = form_vars_get("comments")
        if organisation_id is None or person_id is None:
            # Load the record
            dtable = s3db.hrm_delegation
            record = db(dtable.id == form_vars_get("id")).select(dtable.organisation_id,
                                                                 dtable.person_id,
                                                                 #dtable.date,
                                                                 #dtable.end_date,
                                                                 #dtable.comments,
                                                                 limitby = (0, 1)
                                                                 ).first()
            organisation_id = record.organisation_id
            person_id = record.person_id
            start_date = record.start_date
            end_date = record.end_date
            comments = record.comments

        otable = s3db.org_organisation
        org = db(otable.id == organisation_id).select(otable.name,
                                                      limitby = (0, 1)
                                                      ).first()
        org_name = org.name

        ptable = s3db.pr_person
        person = db(ptable.id == person_id).select(ptable.pe_label,
                                                   limitby = (0, 1)
                                                   ).first()
        pe_label = person.pe_label
        
        # Compose Mail
        # @ToDo: i18n
        subject = "%s: Volunteer Deployment of %s to %s has been Approved" % \
                    (settings.get_system_name_short(),
                     pe_label,
                     org_name,
                     )
        # @ToDo: Read Message Template from CMS or templates/RLP/views/msg/*.txt
        message = "Volunteer %s has been Approved for a Depkloyment to %s from %s to %s." \
                    (pe_label,
                     org_name,
                     start_date,
                     end_date,
                     )
        if comments is not None:
            message = "%s\n%s" % (message, comments)

        # Lookup Email Addresses to send to
        ctable = s3db.pr_contact
        query = (ptable.id == person_id) & \
                (ptable.pe_id == ctable.pe_id) & \
                (ctable.contact_method == "EMAIL") & \
                (ctable.deleted == False)
        emails = db(query).select(ctable.value)
        emails = [e.value for e in emails]

        stable = s3db.org_office
        query = (stable.organisation_id == organisation_id)
        office = db(query).select(stable.email,
                                  limitby = (0, 1),
                                  orderby = stable.created_on
                                  ).first()
        try:
            org_email = office.email
        except AttributeError:
            org_email = None
        if org_email is not None:
            emails.append(org_email)

        send_email = current.msg.send_email
        for email in emails:
            send_email(to = email,
                       subject = subject,
                       message = message,
                       )

        current.session.information = T("Notifications sent")

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
                                           "status",
                                           ]
            else:
                # Main delegations list
                organize["title"] = "person_id"
                organize["description"] = ["organisation_id",
                                           "date",
                                           "end_date",
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

            # Call standard prep
            result = standard_prep(r) if callable(standard_prep) else True

            # Subsets to support workflow
            status_opts = None
            workflow = r.get_vars.get("workflow")
            if workflow:
                # TODO Adjust page title when workflow option chosen
                today = current.request.utcnow

                PENDING = ("REQ", "INVT", "APPL")
                DECIDED = ("APPR", "ACPT", "DECL", "RJCT")

                if workflow == "p":
                    # Pending (undecided and relevant)
                    status_opts = PENDING
                    query = (FS("date") >= today)
                elif workflow == "d":
                    # Decided and relevant
                    status_opts = DECIDED
                    query = (FS("end_date") >= today)
                elif workflow == "r":
                    # Relevant
                    status_opts = PENDING + DECIDED
                    query = (FS("date") >= today)
                elif workflow == "o":
                    # Obsolete (past, cancelled or implemented)
                    query = (FS("end_date") < today) | \
                            (FS("status").belongs(("DECL", "RJCT", "CANC", "IMPL")))
                else:
                    # Current delegations (accepted|approved and started)
                    status_opts = (("ACPT", "APPR"))
                    query = (FS("date") <= today)
                if status_opts:
                    query &= FS("status").belongs(status_opts)
                r.resource.add_filter(query)

            coordinator = current.auth.s3_has_role("COORDINATOR")
            multiple_orgs = delegation_read_multiple_orgs()[0]

            if coordinator:
                s3db.add_custom_callback("hrm_delegation",
                                         "onaccept",
                                         hrm_delegation_update_onaccept,
                                         method = "update",
                                         )

            if r.interactive:

                if not volunteer_id:
                    from s3 import S3DateFilter, S3OptionsFilter, s3_get_filter_opts
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
                    field = r.table.status
                    if not status_opts:
                        status_filter_opts = [opt for opt in field.requires.options()
                                              if opt[0]
                                              ]
                    else:
                        status_filter_opts = [opt for opt in field.requires.options()
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
            list_fields = [(T("Pool"), "person_id$pool_membership.group_id"),
                           "person_id",
                           "date",
                           "end_date",
                           "status",
                           "comments",
                           ]
            if multiple_orgs:
                list_fields.insert(0, "organisation_id")
            r.resource.configure(list_fields = list_fields,
                                 orderby = "hrm_delegation.date",
                                 )
            return result
        s3.prep = custom_prep

        if volunteer_id:
            attr = dict(attr)
            attr["rheader"] = rlp_vol_rheader

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
        #("msg", Storage(
        #    name_nice = T("Messaging"),
        #    #description = "Sends & Receives Alerts via Email & SMS",
        #    restricted = True,
        #    # The user-visible functionality of this module isn't normally required. Rather it's main purpose is to be accessed from other modules.
        #    module_type = None,
        #)),
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
        ("req", Storage(
           name_nice = T("Requests"),
           #description = "Manage requests for supplies, assets, staff or other resources. Matches against Inventories where supplies are requested.",
           restricted = True,
           module_type = 10,
        )),
        ("project", Storage(
            name_nice = T("Projects"),
            #description = "Tracking of Projects, Activities and Tasks",
            restricted = True,
            module_type = 2
        )),
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
        ("event", Storage(
            name_nice = T("Events"),
            #description = "Activate Events (e.g. from Scenario templates) for allocation of appropriate Resources (Human, Assets & Facilities).",
            restricted = True,
            module_type = 10,
        )),
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
                                         ],
                                        represent = True,
                                        raw_data = True,
                                        ).rows
            if volunteer:
                # Extract volunteer details
                volunteer = volunteer[0]
                if coordinator:
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
                              [(T("Name"), name),
                               (T("Occupation Type"), occupation_type),
                               ],
                              [(T("Age"), age),
                               ]
                              ]

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
def rlp_req_rheader(r, tabs=None):
    """ REQ custom resource headers """

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

        if tablename == "req_need":

            if not tabs:
                tabs = [(T("Request Details"), None),
                        ]

            # TODO show requesting organisation, date and status instead?
            rheader_fields = [["name",
                               ],
                              ]

        rheader = S3ResourceHeader(rheader_fields, tabs)(r,
                                                         table=resource.table,
                                                         record=record,
                                                         )
    return rheader
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
    def represent_row(self, row):
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
