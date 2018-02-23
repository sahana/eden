# -*- coding: utf-8 -*-

from collections import OrderedDict

from gluon import current
from gluon.storage import Storage

def config(settings):
    """
        New Zealand Red Cross
        - designed to be used with locations.NZ & VM templates
    """

    T = current.T

    #settings.base.system_name = T("Sahana Skeleton")
    #settings.base.system_name_short = T("Sahana")

    # PrePopulate data
    settings.base.prepopulate+= ("historic/NZRC", "historic/NZRC/Demo")

    # Theme (folder to use for views/layout.html)
    settings.base.theme = "historic.NZRC"

    # Authentication settings
    # Do new users need to verify their email address?
    settings.auth.registration_requires_verification = True
    # Do new users need to be approved by an administrator prior to being able to login?
    settings.auth.registration_requires_approval = True
    # Need an Org in order to link to Volunteer/Member records
    settings.auth.registration_requests_organisation = True
    settings.auth.registration_organisation_required = True

    settings.auth.registration_link_user_to = {"staff": T("Staff"),
                                               "volunteer": T("Volunteer"),
                                               "member": T("Member")
                                               }

    # Approval emails get sent to all admins
    settings.mail.approver = "ADMIN"

    # Uncomment to display the Map Legend as a floating DIV
    settings.gis.legend = "float"
    # Uncomment to show the Print control:
    # http://eden.sahanafoundation.org/wiki/UserGuidelines/Admin/MapPrinting
    #settings.gis.print_button = True

    # Number formats (defaults to ISO 31-0)
    # Decimal separator for numbers (defaults to ,)
    settings.L10n.decimal_separator = "."
    # Thousands separator for numbers (defaults to space)
    settings.L10n.thousands_separator = ","

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

    settings.security.policy = 7 # Organisation-ACLs + Hierarchy

    # -------------------------------------------------------------------------
    # Org
    settings.org.branches = True

    # -------------------------------------------------------------------------
    # PR
    # Uncomment to do a search for duplicates in AddPersonWidget2
    settings.pr.lookup_duplicates = True

    # -------------------------------------------------------------------------
    # HRM
    settings.hrm.email_required = False

    settings.hrm.use_credentials = False

    # -------------------------------------------------------------------------
    # Projects
    settings.project.mode_task = True

    # -------------------------------------------------------------------------
    # Req
    settings.req.req_type = ["People"]

    # Uncomment to Commit Named People rather than simply Anonymous Skills
    settings.req.commit_people = True

    # Disable Inline Forms, unless we enable separate controllers
    # (otherwise Create form cannot redirect to next tab correctly)
    settings.req.inline_forms = False

    settings.req.show_quantity_transit = False

    # -------------------------------------------------------------------------
    def ns_only(tablename,
                fieldname = "organisation_id",
                required = True,
                branches = True,
                updateable = True,
                limit_filter_opts = True,
                hierarchy = True,
                ):
        """
            Function to configure an organisation_id field to be restricted to just
            NS/Branch

            @param required: Field is mandatory
            @param branches: Include Branches
            @param updateable: Limit to Orgs which the user can update
            @param limit_filter_opts: Also limit the Filter options
            @param hierarchy: Use the hierarchy widget (unsuitable for use in Inline Components)

            NB If limit_filter_opts=True, apply in customise_xx_controller inside prep,
               after standard_prep is run
        """

        # Lookup organisation_type_id for Red Cross
        db = current.db
        s3db = current.s3db
        ttable = s3db.org_organisation_type
        try:
            type_id = db(ttable.name == "Red Cross / Red Crescent").select(ttable.id,
                                                                           limitby=(0, 1),
                                                                           cache = s3db.cache,
                                                                           ).first().id
        except:
            # No IFRC prepop done - skip (e.g. testing impacts of CSS changes in this theme)
            return

        # Load standard model
        f = s3db[tablename][fieldname]

        if limit_filter_opts:
            # Find the relevant filter widget & limit it's options
            filter_widgets = s3db.get_config(tablename, "filter_widgets")
            filter_widget = None
            if filter_widgets:
                from s3 import FS, S3HierarchyFilter
                for w in filter_widgets:
                    if isinstance(w, S3HierarchyFilter) and \
                       w.field == "organisation_id":
                        filter_widget = w
                        break
            if filter_widget is not None:
                selector = FS("organisation_organisation_type.organisation_type_id")
                filter_widget.opts["filter"] = (selector == type_id)

        # Label
        if branches:
            f.label = T("National Society / Branch")
            #f.label = T("Branch")
        else:
            f.label = T("National Society")

        # Requires

        # Filter by type
        ltable = db.org_organisation_organisation_type
        rows = db(ltable.organisation_type_id == type_id).select(ltable.organisation_id)
        filter_opts = [row.organisation_id for row in rows]

        auth = current.auth
        s3_has_role = auth.s3_has_role
        Admin = s3_has_role("ADMIN")
        if branches:
            if Admin:
                parent = True
            else:
                # @ToDo: Set the represent according to whether the user can see resources of just a single NS or multiple
                # @ToDo: Consider porting this into core
                user = auth.user
                if user:
                    realms = user.realms
                    #delegations = user.delegations
                    if realms:
                        parent = True
                    else:
                        parent = False
                else:
                    parent = True

        else:
            # Keep the represent function as simple as possible
            parent = False
            # Exclude branches
            btable = s3db.org_organisation_branch
            rows = db((btable.deleted != True) &
                      (btable.branch_id.belongs(filter_opts))).select(btable.branch_id)
            filter_opts = list(set(filter_opts) - set(row.branch_id for row in rows))

        organisation_represent = s3db.org_OrganisationRepresent
        represent = organisation_represent(parent=parent)
        f.represent = represent

        from s3 import IS_ONE_OF
        requires = IS_ONE_OF(db, "org_organisation.id",
                             represent,
                             filterby = "id",
                             filter_opts = filter_opts,
                             updateable = updateable,
                             orderby = "org_organisation.name",
                             sort = True)
        if not required:
            from gluon import IS_EMPTY_OR
            requires = IS_EMPTY_OR(requires)
        f.requires = requires

        if parent and hierarchy:
            # Use hierarchy-widget
            from s3 import FS, S3HierarchyWidget
            # No need for parent in represent (it's a hierarchy view)
            node_represent = organisation_represent(parent=False)
            # Filter by type
            # (no need to exclude branches - we wouldn't be here if we didn't use branches)
            selector = FS("organisation_organisation_type.organisation_type_id")
            f.widget = S3HierarchyWidget(lookup="org_organisation",
                                         filter=(selector == type_id),
                                         represent=node_represent,
                                         multiple=False,
                                         leafonly=False,
                                         )
        else:
            # Dropdown not Autocomplete
            f.widget = None

        # Comment
        if (Admin or s3_has_role("ORG_ADMIN")):
            # Need to do import after setting Theme
            from s3layouts import S3PopupLink
            from s3 import S3ScriptItem
            add_link = S3PopupLink(c = "org",
                                   f = "organisation",
                                   vars = {"organisation_type.name":"Red Cross / Red Crescent"},
                                   label = T("Create National Society"),
                                   title = T("National Society"),
                                   )
            comment = f.comment
            if not comment or isinstance(comment, S3PopupLink):
                f.comment = add_link
            elif isinstance(comment[1], S3ScriptItem):
                # Don't overwrite scripts
                f.comment[0] = add_link
            else:
                f.comment = add_link
        else:
            # Not allowed to add NS/Branch
            f.comment = ""

    # -----------------------------------------------------------------------------
    def customise_auth_user_controller(**attr):
        """
            Customise admin/user() and default/user() controllers
        """

        if current.auth.is_logged_in():
            # Organisation needs to be an NS/Branch
            ns_only("auth_user",
                    required = True,
                    branches = True,
                    updateable = False, # Need to see all Orgs in Registration screens
                    )
        else:
            # Registration page
            db = current.db
            s3db = current.s3db
            field = db.auth_user.organisation_id

            # Limit to just Branches
            field.label = T("Branch")
            # Simplify Represent
            field.represent = represent = s3db.org_OrganisationRepresent(parent=False)
            otable = s3db.org_organisation
            btable = s3db.org_organisation_branch
            query = (btable.deleted != True) & \
                    (btable.organisation_id == otable.id) & \
                    (otable.name == "New Zealand Red Cross")
            rows = db(query).select(btable.branch_id)
            filter_opts = [row.branch_id for row in rows]
            from s3 import IS_ONE_OF
            field.requires = IS_ONE_OF(db, "org_organisation.id",
                                       represent,
                                       filterby = "id",
                                       filter_opts = filter_opts,
                                       orderby = "org_organisation.name",
                                       sort = True,
                                       )
            # Don't create new branches here
            field.comment = None

        return attr

    settings.customise_auth_user_controller = customise_auth_user_controller

    # -----------------------------------------------------------------------------
    def customise_deploy_alert_resource(r, tablename):

        current.s3db.deploy_alert_recipient.human_resource_id.label = T("Member")

    settings.customise_deploy_alert_resource = customise_deploy_alert_resource

    # -----------------------------------------------------------------------------
    def customise_deploy_application_resource(r, tablename):

        r.table.human_resource_id.label = T("Member")

    settings.customise_deploy_application_resource = customise_deploy_application_resource

    # -----------------------------------------------------------------------------
    def _customise_assignment_fields(**attr):

        MEMBER = T("Member")
        from gluon.html import DIV
        hr_comment =  \
            DIV(_class="tooltip",
                _title="%s|%s" % (MEMBER,
                                  current.messages.AUTOCOMPLETE_HELP))

        from s3 import IS_ONE_OF
        s3db = current.s3db
        atable = s3db.deploy_assignment
        atable.human_resource_id.label = MEMBER
        atable.human_resource_id.comment = hr_comment
        field = atable.job_title_id
        field.comment = None
        field.label = T("Sector")
        field.requires = IS_ONE_OF(current.db, "hrm_job_title.id",
                                   field.represent,
                                   filterby = "type",
                                   filter_opts = (4,),
                                   )

        # Default activity_type when creating experience records from assignments
        activity_type = s3db.hrm_experience.activity_type
        activity_type.default = activity_type.update = "rdrt"

        return

    # -----------------------------------------------------------------------------
    def customise_deploy_assignment_controller(**attr):

        s3db = current.s3db
        table = s3db.deploy_assignment

        # Labels
        table.job_title_id.label = T("RDRT Type")
        table.start_date.label = T("Deployment Date")
        #table.end_date.label = T("EOM")

        # List fields
        list_fields = [(T("Mission"), "mission_id$name"),
                       (T("Appeal Code"), "mission_id$code"),
                       (T("Country"), "mission_id$location_id"),
                       (T("Disaster Type"), "mission_id$event_type_id"),
                       # @todo: replace by date of first alert?
                       (T("Date"), "mission_id$created_on"),
                       "job_title_id",
                       (T("Member"), "human_resource_id$person_id"),
                       (T("Deploying NS"), "human_resource_id$organisation_id"),
                       "start_date",
                       "end_date",
                       "appraisal.rating",
                       # @todo: Comments of the mission (=>XLS only)
                      ]

        # Report options
        report_fact = [(T("Number of Deployments"), "count(human_resource_id)"),
                       (T("Average Rating"), "avg(appraisal.rating)"),
                       ]
        report_axis = [(T("Appeal Code"), "mission_id$code"),
                       (T("Country"), "mission_id$location_id"),
                       (T("Disaster Type"), "mission_id$event_type_id"),
                       (T("RDRT Type"), "job_title_id"),
                       (T("Deploying NS"), "human_resource_id$organisation_id"),
                      ]
        report_options = Storage(
            rows=report_axis,
            cols=report_axis,
            fact=report_fact,
            defaults=Storage(rows="mission_id$location_id",
                             cols="mission_id$event_type_id",
                             fact="count(human_resource_id)",
                             totals=True
                             )
            )

        s3db.configure("deploy_assignment",
                       list_fields = list_fields,
                       report_options = report_options,
                       )


        # CRUD Strings
        current.response.s3.crud_strings["deploy_assignment"] = Storage(
            label_create = T("Add Deployment"),
            title_display = T("Deployment Details"),
            title_list = T("Deployments"),
            title_update = T("Edit Deployment Details"),
            title_upload = T("Import Deployments"),
            label_list_button = T("List Deployments"),
            label_delete_button = T("Delete Deployment"),
            msg_record_created = T("Deployment added"),
            msg_record_modified = T("Deployment Details updated"),
            msg_record_deleted = T("Deployment deleted"),
            msg_list_empty = T("No Deployments currently registered"))

        _customise_assignment_fields()

        # Restrict Location to just Countries
        from s3 import S3Represent
        field = s3db.deploy_mission.location_id
        field.represent = S3Represent(lookup="gis_location", translate=True)

        return attr

    settings.customise_deploy_assignment_controller = customise_deploy_assignment_controller

    # -----------------------------------------------------------------------------
    def customise_deploy_mission_controller(**attr):

        db = current.db
        s3db = current.s3db
        s3 = current.response.s3
        MEMBER = T("Member")
        from gluon.html import DIV
        hr_comment =  \
            DIV(_class="tooltip",
                _title="%s|%s" % (MEMBER,
                                  current.messages.AUTOCOMPLETE_HELP))

        table = s3db.deploy_mission
        table.code.label = T("Appeal Code")
        table.event_type_id.label = T("Disaster Type")
        table.organisation_id.readable = table.organisation_id.writable = False

        # Restrict Location to just Countries
        from s3 import S3Represent, S3MultiSelectWidget
        field = table.location_id
        field.label = current.messages.COUNTRY
        field.requires = s3db.gis_country_requires
        field.widget = S3MultiSelectWidget(multiple=False)
        field.represent = S3Represent(lookup="gis_location", translate=True)

        rtable = s3db.deploy_response
        rtable.human_resource_id.label = MEMBER
        rtable.human_resource_id.comment = hr_comment

        _customise_assignment_fields()

        # Report options
        report_fact = [(T("Number of Missions"), "count(id)"),
                       (T("Number of Countries"), "count(location_id)"),
                       (T("Number of Disaster Types"), "count(event_type_id)"),
                       (T("Number of Responses"), "sum(response_count)"),
                       (T("Number of Deployments"), "sum(hrquantity)"),
                      ]
        report_axis = ["code",
                       "location_id",
                       "event_type_id",
                       "status",
                       ]
        report_options = Storage(rows = report_axis,
                                 cols = report_axis,
                                 fact = report_fact,
                                 defaults = Storage(rows = "location_id",
                                                    cols = "event_type_id",
                                                    fact = "sum(hrquantity)",
                                                    totals = True,
                                                    ),
                                 )

        s3db.configure("deploy_mission",
                       report_options = report_options,
                       )

        # CRUD Strings
        s3.crud_strings["deploy_assignment"] = Storage(
            label_create = T("New Deployment"),
            title_display = T("Deployment Details"),
            title_list = T("Deployments"),
            title_update = T("Edit Deployment Details"),
            title_upload = T("Import Deployments"),
            label_list_button = T("List Deployments"),
            label_delete_button = T("Delete Deployment"),
            msg_record_created = T("Deployment added"),
            msg_record_modified = T("Deployment Details updated"),
            msg_record_deleted = T("Deployment deleted"),
            msg_list_empty = T("No Deployments currently registered"))

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if r.interactive and not current.auth.s3_has_role("RDRT_ADMIN"):
                # Limit write-access to these fields to RDRT Admins:
                fields = ("name",
                          "event_type_id",
                          "location_id",
                          "code",
                          "status",
                          )
                table = r.resource.table
                for f in fields:
                    if f in table:
                        table[f].writable = False

            #if not r.component and r.method == "create":
            #    # Org is always IFRC
            #    otable = s3db.org_organisation
            #    query = (otable.name == "International Federation of Red Cross and Red Crescent Societies")
            #    organisation = db(query).select(otable.id,
            #                                    limitby = (0, 1),
            #                                    ).first()
            #    if organisation:
            #        r.table.organisation_id.default = organisation.id

            return result
        s3.prep = custom_prep

        return attr

    settings.customise_deploy_mission_controller = customise_deploy_mission_controller

    # -----------------------------------------------------------------------------
    def customise_hrm_certificate_resource(r, tablename):

        field = current.s3db.hrm_certificate.organisation_id
        field.readable = field.writable = False

    settings.customise_hrm_certificate_resource = customise_hrm_certificate_resource

    # -----------------------------------------------------------------------------
    def customise_hrm_course_resource(r, tablename):

        field = current.s3db.hrm_course.organisation_id
        field.readable = field.writable = False

    settings.customise_hrm_course_resource = customise_hrm_course_resource

    # -----------------------------------------------------------------------------
    def customise_hrm_credential_controller(**attr):

        # Currently just used by RDRT
        table = current.s3db.hrm_credential
        field = table.job_title_id
        field.comment = None
        field.label = T("Sector")
        from s3 import IS_ONE_OF
        field.requires = IS_ONE_OF(current.db, "hrm_job_title.id",
                                   field.represent,
                                   filterby = "type",
                                   filter_opts = (4,),
                                   )
        table.organisation_id.readable = table.organisation_id.writable = False
        table.performance_rating.readable = table.performance_rating.writable = False
        table.start_date.readable = table.start_date.writable = False
        table.end_date.readable = table.end_date.writable = False

        return attr

    settings.customise_hrm_credential_controller = customise_hrm_credential_controller

    # -----------------------------------------------------------------------------
    def customise_hrm_department_resource(r, tablename):

        field = current.s3db.hrm_department.organisation_id
        field.readable = field.writable = False

    settings.customise_hrm_department_resource = customise_hrm_department_resource

    # -----------------------------------------------------------------------------
    def hrm_human_resource_create_onaccept(form):

        s3db = current.s3db

        # Make Volunteer deployable
        s3db.deploy_application.insert(human_resource_id=form.vars.id)

        # Fire nromal onaccept
        s3db.hrm_human_resource_onaccept(form)


    # -----------------------------------------------------------------------------
    def customise_hrm_human_resource_resource(r, tablename):

        db = current.db
        s3db = current.s3db
        field = s3db.hrm_human_resource.organisation_id

        # Limit to just Branches
        field.label = T("Branch")
        # Simplify Represent
        field.represent = represent = s3db.org_OrganisationRepresent(parent=False)
        otable = s3db.org_organisation
        btable = s3db.org_organisation_branch
        query = (btable.deleted != True) & \
                (btable.organisation_id == otable.id) & \
                (otable.name == "New Zealand Red Cross")
        rows = db(query).select(btable.branch_id)
        filter_opts = [row.branch_id for row in rows]
        from s3 import IS_ONE_OF
        field.requires = IS_ONE_OF(db, "org_organisation.id",
                                   represent,
                                   filterby = "id",
                                   filter_opts = filter_opts,
                                   updateable = True,
                                   orderby = "org_organisation.name",
                                   sort = True,
                                   )
        # Don't create new branches here
        field.comment = None

        s3db.configure("hrm_human_resource",
                       create_onaccept = hrm_human_resource_create_onaccept,
                       )

    settings.customise_hrm_human_resource_resource = customise_hrm_human_resource_resource

    # -----------------------------------------------------------------------------
    def customise_hrm_experience_controller(**attr):

        s3 = current.response.s3

        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                if not standard_prep(r):
                    return False

            if r.controller == "deploy":
                # Popups in RDRT Member Profile

                table = r.table

                job_title_id = table.job_title_id
                job_title_id.label = T("Sector / Area of Expertise")
                job_title_id.comment = None
                jtable = current.s3db.hrm_job_title
                query = (jtable.type == 4)
                if r.method == "update" and r.record.job_title_id:
                    # Allow to keep the current value
                    query |= (jtable.id == r.record.job_title_id)
                from s3 import IS_ONE_OF
                job_title_id.requires = IS_ONE_OF(current.db(query),
                                                  "hrm_job_title.id",
                                                  job_title_id.represent,
                                                  )
                job_title = table.job_title
                job_title.readable = job_title.writable = True
            return True
        s3.prep = custom_prep

        return attr

    settings.customise_hrm_experience_controller = customise_hrm_experience_controller

    # =============================================================================
    def vol_programme_active(person_id):
        """
            Whether a Volunteer counts as 'Active' based on the number of hours
            they've done (both Trainings & Programmes) per month, averaged over
            the last year.
            If nothing recorded for the last 3 months, don't penalise as assume
            that data entry hasn't yet been done.

            @ToDo: This should be based on the HRM record, not Person record
                   - could be active with Org1 but not with Org2
            @ToDo: allow to be calculated differently per-Org
        """

        now = current.request.utcnow

        # Time spent on Programme work
        htable = current.s3db.hrm_programme_hours
        query = (htable.deleted == False) & \
                (htable.person_id == person_id) & \
                (htable.date != None)
        programmes = current.db(query).select(htable.hours,
                                              htable.date,
                                              orderby=htable.date)
        if programmes:
            # Ignore up to 3 months of records
            import datetime
            three_months_prior = (now - datetime.timedelta(days=92))
            end = max(programmes.last().date, three_months_prior.date())
            last_year = end - datetime.timedelta(days=365)
            # Is this the Volunteer's first year?
            if programmes.first().date > last_year:
                # Only start counting from their first month
                start = programmes.first().date
            else:
                # Start from a year before the latest record
                start = last_year

            # Total hours between start and end
            programme_hours = 0
            for programme in programmes:
                if programme.date >= start and programme.date <= end and programme.hours:
                    programme_hours += programme.hours

            # Average hours per month
            months = max(1, (end - start).days / 30.5)
            average = programme_hours / months

            # Active?
            if average >= 8:
                return True

        return False

    def hrm_vol_active(default):
        """ Whether & How to track Volunteers as Active """

        # Use formula based on hrm_programme
        return vol_programme_active

    settings.hrm.vol_active = hrm_vol_active

    # -----------------------------------------------------------------------------
    def rdrt_member_profile_header(r):
        """ Custom profile header to allow update of RDRT roster status """

        record = r.record
        if not record:
            return ""

        person_id = record.person_id
        from s3 import s3_fullname, s3_avatar_represent
        name = s3_fullname(person_id)

        table = r.table

        # Organisation
        comments = table.organisation_id.represent(record.organisation_id)

        from s3 import s3_unicode
        from gluon.html import A, DIV, H2, LABEL, P, SPAN

        # Add job title if present
        job_title_id = record.job_title_id
        if job_title_id:
            comments = (SPAN("%s, " % \
                             s3_unicode(table.job_title_id.represent(job_title_id))),
                             comments)

        # Determine the current roster membership status (active/inactive)
        atable = current.s3db.deploy_application
        status = atable.active
        query = atable.human_resource_id == r.id
        row = current.db(query).select(atable.id,
                                       atable.active,
                                       limitby=(0, 1)).first()
        if row:
            active = 1 if row.active else 0
            status_id = row.id
            roster_status = status.represent(row.active)
        else:
            active = None
            status_id = None
            roster_status = current.messages.UNKNOWN_OPT

        if status_id and \
           current.auth.s3_has_permission("update",
                                          "deploy_application",
                                          record_id=status_id):
            # Make inline-editable
            roster_status = A(roster_status,
                              data = {"status": active},
                              _id = "rdrt-roster-status",
                              _title = T("Click to edit"),
                              )
            s3 = current.response.s3
            script = "/%s/static/themes/IFRC/js/rdrt.js" % r.application
            if script not in s3.scripts:
                s3.scripts.append(script)
            script = '''$.rdrtStatus('%(url)s','%(active)s','%(inactive)s','%(submit)s')'''
            from gluon import URL
            options = {"url": URL(c="deploy", f="application",
                                  args=["%s.s3json" % status_id]),
                       "active": status.represent(True),
                       "inactive": status.represent(False),
                       "submit": T("Save"),
                       }
            s3.jquery_ready.append(script % options)
        else:
            # Read-only
            roster_status = SPAN(roster_status)

        # Render profile header
        return DIV(A(s3_avatar_represent(person_id,
                                         tablename="pr_person",
                                         _class="media-object",
                                         ),
                     _class="pull-left",
                     ),
                   H2(name),
                   P(comments),
                   DIV(LABEL(status.label + ": "), roster_status),
                   _class="profile-header",
                   )

    # -----------------------------------------------------------------------------
    def emergency_contact_represent(row):
        """
            Representation of Emergency Contacts (S3Represent label renderer)

            @param row: the row
        """

        items = [row["pr_contact_emergency.name"]]
        relationship = row["pr_contact_emergency.relationship"]
        if relationship:
            items.append(" (%s)" % relationship)
        phone_number = row["pr_contact_emergency.phone"]
        if phone_number:
            items.append(": %s" % phone_number)
        return "".join(items)

    # -----------------------------------------------------------------------------
    def customise_member_membership_resource(r, tablename):

        db = current.db
        s3db = current.s3db
        field = s3db.member_membership.organisation_id

        # Limit to just Branches
        field.label = T("Branch")
        # Simplify Represent
        field.represent = represent = s3db.org_OrganisationRepresent(parent=False)
        otable = s3db.org_organisation
        btable = s3db.org_organisation_branch
        query = (btable.deleted != True) & \
                (btable.organisation_id == otable.id) & \
                (otable.name == "New Zealand Red Cross")
        rows = db(query).select(btable.branch_id)
        filter_opts = [row.branch_id for row in rows]
        from s3 import IS_ONE_OF
        field.requires = IS_ONE_OF(db, "org_organisation.id",
                                   represent,
                                   filterby = "id",
                                   filter_opts = filter_opts,
                                   updateable = True,
                                   orderby = "org_organisation.name",
                                   sort = True,
                                   )
        # Don't create new branches here
        field.comment = None

    settings.customise_member_membership_resource = customise_member_membership_resource

    # -----------------------------------------------------------------------------
    def customise_member_membership_type_resource(r, tablename):

        field = current.s3db.member_membership_type.organisation_id
        field.readable = field.writable = False

    settings.customise_member_membership_type_resource = customise_member_membership_type_resource

    # -----------------------------------------------------------------------------
    def customise_vol_award_resource(r, tablename):

        field = current.s3db.vol_award.organisation_id
        field.readable = field.writable = False

    settings.customise_vol_award_resource = customise_vol_award_resource

    # -----------------------------------------------------------------------------
    def customise_dvr_case_resource(r, tablename):

        db = current.db
        s3db = current.s3db
        field = s3db.dvr_case.organisation_id

        # Limit to just Branches
        field.label = T("Branch")
        # Simplify Represent
        field.represent = represent = s3db.org_OrganisationRepresent(parent=False)
        otable = s3db.org_organisation
        btable = s3db.org_organisation_branch
        query = (btable.deleted != True) & \
                (btable.organisation_id == otable.id) & \
                (otable.name == "New Zealand Red Cross")
        rows = db(query).select(btable.branch_id)
        filter_opts = [row.branch_id for row in rows]
        from s3 import IS_ONE_OF
        field.requires = IS_ONE_OF(db, "org_organisation.id",
                                   represent,
                                   filterby = "id",
                                   filter_opts = filter_opts,
                                   updateable = True,
                                   orderby = "org_organisation.name",
                                   sort = True,
                                   )
        # Don't create new branches here
        field.comment = None

    settings.customise_dvr_case_resource = customise_dvr_case_resource

    # -------------------------------------------------------------------------
    # Comment/uncomment modules here to disable/enable them
    # Modules menu is defined in modules/eden/menu.py
    settings.modules = OrderedDict([
        # Core modules which shouldn't be disabled
        ("default", Storage(
            name_nice = T("Home"),
            restricted = False, # Use ACLs to control access to this module
            access = None,      # All Users (inc Anonymous) can see this module in the default menu & access the controller
        )),
        ("admin", Storage(
            name_nice = T("Administration"),
            #description = "Site Administration",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
        )),
        ("appadmin", Storage(
            name_nice = T("Administration"),
            #description = "Site Administration",
            restricted = True,
        )),
        ("errors", Storage(
            name_nice = T("Ticket Viewer"),
            #description = "Needed for Breadcrumbs",
            restricted = False,
        )),
        ("gis", Storage(
            name_nice = T("Map"),
            #description = "Situation Awareness & Geospatial Analysis",
            restricted = True,
        )),
        ("pr", Storage(
            name_nice = T("Person Registry"),
            #description = "Central point to record details on People",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu (access to controller is possible to all still)
        )),
        ("org", Storage(
            name_nice = T("Organizations"),
            #description = 'Lists "who is doing what & where". Allows relief agencies to coordinate their activities',
            restricted = True,
        )),
        ("hrm", Storage(
            name_nice = T("Staff"),
            #description = "Human Resources Management",
            restricted = True,
        )),
        ("vol", Storage(
            name_nice = T("Volunteers"),
            #description = "Human Resources Management",
            restricted = True,
        )),
        ("cms", Storage(
          name_nice = T("Content Management"),
          #description = "Content Management System",
          restricted = True,
        )),
        ("doc", Storage(
            name_nice = T("Documents"),
            #description = "A library of digital resources, such as photos, documents and reports",
            restricted = True,
        )),
        ("msg", Storage(
            name_nice = T("Messaging"),
            #description = "Sends & Receives Alerts via Email & SMS",
            restricted = True,
            # The user-visible functionality of this module isn't normally required. Rather it's main purpose is to be accessed from other modules.
        )),
        ("member", Storage(
               name_nice = T("Members"),
               #description = "Membership Management System",
               restricted = True,
        )),
        ("deploy", Storage(
               name_nice = T("Delegates"),
               #description = "Alerting and Deployment of Disaster Response Teams",
               restricted = True,
        )),
        ("project", Storage(
               name_nice = T("Tasks"),
               restricted = True,
        )),
        ("req", Storage(
           name_nice = T("Opportunities"),
           restricted = True,
        )),
        #("dvr", Storage(
        #   name_nice = T("Case Management"),
        #   #description = "Allow affected individuals & households to register to receive compensation and distributions",
        #   restricted = True,
        #)),
        ("po", Storage(
           name_nice = T("Project Outreach"),
           #description = "Allow affected individuals & households to register to receive compensation and distributions",
           restricted = True,
        )),
    ])

# END =========================================================================