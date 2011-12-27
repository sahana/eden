# -*- coding: utf-8 -*-

"""
    VITA Disaster Victim Identification, Models

    @author: nursix
    @author: khushbu
    @see: U{http://eden.sahanafoundation.org/wiki/BluePrintVITA}
"""

module = "dvi"
if deployment_settings.has_module(module):

    def dvi_tables():
        """ Load the DVI Tables when needed """

        pr_gender = s3db.pr_gender
        pr_age_group = s3db.pr_age_group

        # Recovery Request ====================================================
        #
        task_status = {
            1:T("Not Started"),
            2:T("Assigned"),
            3:T("In Progress"),
            4:T("Completed"),
            5:T("Not Applicable"),
            6:T("Not Possible")
        }

        resourcename = "recreq"
        tablename = "dvi_recreq"
        table = db.define_table(tablename,
                                Field("date", "datetime"),
                                Field("marker", length=64),
                                person_id(),
                                Field("bodies_found", "integer"),
                                Field("bodies_recovered", "integer"),
                                Field("description", "text"),
                                location_id(),
                                Field("status", "integer",
                                      requires = IS_IN_SET(task_status,
                                                           zero=None),
                                      default = 1,
                                      label = T("Task Status"),
                                      represent = lambda opt: \
                                        task_status.get(opt, UNKNOWN_OPT)),
                                *s3_meta_fields())

        # Settings and Restrictions
        table.date.label = T("Date/Time of Find")
        table.date.default = request.utcnow
        table.date.requires = IS_UTC_DATETIME(allow_future=False)
        table.date.represent = lambda val: s3_datetime_represent(val, utc=True)
        table.date.widget = S3DateTimeWidget(future=0)

        table.marker.label = T("Marker")
        table.marker.comment = DIV(_class="tooltip",
                                    _title="%s|%s" % (
                                           T("Marker"),
                                           T("Number or code used to mark the place of find, e.g. flag code, grid coordinates, site reference number or similar (if available)")))

        table.location_id.label = T("Location")
        table.person_id.label = T("Finder")

        table.bodies_found.label = T("Bodies found")
        table.bodies_found.requires = IS_INT_IN_RANGE(1, 99999)
        table.bodies_found.default = 0
        table.bodies_found.comment = DIV(_class="tooltip",
                                    _title="%s|%s" % (
                                           T("Number of bodies found"),
                                           T("Please give an estimated figure about how many bodies have been found.")))

        table.bodies_recovered.label = T("Bodies recovered")
        table.bodies_recovered.requires = IS_NULL_OR(
                                            IS_INT_IN_RANGE(0, 99999))
        table.bodies_recovered.default = 0

        # CRUD Strings
        s3.crud_strings[tablename] = Storage(
            title_create = T("Body Recovery Request"),
            title_display = T("Request Details"),
            title_list = T("Body Recovery Requests"),
            title_update = T("Update Request"),
            title_search = T("Search Request"),
            subtitle_create = T("Add New Request"),
            subtitle_list = T("List of Requests"),
            label_list_button = T("List of Requests"),
            label_create_button = T("Add Request"),
            label_delete_button = T("Delete Request"),
            msg_record_created = T("Recovery Request added"),
            msg_record_modified = T("Recovery Request updated"),
            msg_record_deleted = T("Recovery Request deleted"),
            msg_list_empty = T("No requests found"))


        dvi_recreq_id = S3ReusableField("dvi_recreq_id", table,
                                        requires = IS_NULL_OR(IS_ONE_OF(db,
                                                   "dvi_recreq.id",
                                                   "[%(marker)s] %(date)s: %(bodies_found)s bodies")),
                                        represent = lambda id: id,
                                        label=T("Recovery Request"),
                                        ondelete = "RESTRICT")

        s3mgr.configure(tablename,
                        list_fields = ["id",
                                       "date",
                                       "marker",
                                       "location_id",
                                       "bodies_found",
                                       "bodies_recovered",
                                       "status"])

        # Morgue ==================================================================
        #
        resourcename = "morgue"
        tablename = "dvi_morgue"
        table = db.define_table(tablename,
                                Field("name",
                                      unique=True,
                                      notnull=True),
                                Field("description"),
                                location_id(),
                                *s3_meta_fields())

        def dvi_morgue_represent(id):
            table = db.dvi_morgue
            row = db(table.id == id).select(table.name,
                                            limitby=(0, 1)).first()
            if row:
                return row.name
            else:
                return "-"

        morgue_id = S3ReusableField("morgue_id", table,
                                    requires = IS_NULL_OR(IS_ONE_OF(db,
                                               "dvi_morgue.id", "%(name)s")),
                                    represent = dvi_morgue_represent,
                                    ondelete = "RESTRICT")

        # Body ====================================================================
        #
        resourcename = "body"
        tablename = "dvi_body"
        table = db.define_table(tablename,
                                super_link(db.pr_pentity), # pe_id
                                super_link(s3db.sit_trackable), # track_id
                                pe_label(),
                                morgue_id(),
                                dvi_recreq_id(),
                                Field("date_of_recovery", "datetime"),
                                Field("recovery_details","text"),
                                Field("incomplete","boolean"),
                                Field("major_outward_damage","boolean"),
                                Field("burned_or_charred","boolean"),
                                Field("decomposed","boolean"),
                                pr_gender(),
                                pr_age_group(),
                                location_id(),
                                *s3_meta_fields())

        s3mgr.model.add_component(table, dvi_morgue="morgue_id")

        table.pe_label.requires = [IS_NOT_EMPTY(
                                    error_message=T("Enter a unique label!")),
                                   IS_NOT_ONE_OF(db, "dvi_body.pe_label")]

        table.date_of_recovery.default = request.utcnow
        table.date_of_recovery.requires = IS_UTC_DATETIME(allow_future=False)
        table.date_of_recovery.represent = lambda val: s3_datetime_represent(val, utc=True)

        # Labels
        table.dvi_recreq_id.label = T("Recovery Request")
        table.gender.label=T("Apparent Gender")
        table.age_group.label=T("Apparent Age")
        table.location_id.label=T("Place of Recovery")

        table.incomplete.label = T("Incomplete")
        table.major_outward_damage.label = T("Major outward damage")
        table.burned_or_charred.label = T("Burned/charred")
        table.decomposed.label = T("Decomposed")

        # Representations
        table.major_outward_damage.represent = lambda opt: (opt and ["yes"] or [""])[0]
        table.burned_or_charred.represent =  lambda opt: (opt and ["yes"] or [""])[0]
        table.decomposed.represent =  lambda opt: (opt and ["yes"] or [""])[0]
        table.incomplete.represent =  lambda opt: (opt and ["yes"] or [""])[0]

        # CRUD Strings
        s3.crud_strings[tablename] = Storage(
            title_create = T("Add Dead Body Report"),
            title_display = T("Dead Body Details"),
            title_list = T("Dead Body Reports"),
            title_update = T("Edit Dead Body Details"),
            title_search = T("Find Dead Body Report"),
            subtitle_create = T("Add New Report"),
            subtitle_list = T("List of Reports"),
            label_list_button = T("List Reports"),
            label_create_button = T("Add Report"),
            label_delete_button = T("Delete Report"),
            msg_record_created = T("Dead body report added"),
            msg_record_modified = T("Dead body report updated"),
            msg_record_deleted = T("Dead body report deleted"),
            msg_list_empty = T("No dead body reports available"))

        def dvi_body_onaccept(form):
            """ Update body presence log """
            try:
                body = db.dvi_body[form.vars.id]
            except:
                return
            if body and body.location_id:
                s3tracker(body).set_location(body.location_id,
                                             timestmp=body.date_of_recovery)

        dvi_body_search = s3base.S3Search(
                name = "body_search_simple",
                label = T("ID Tag"),
                comment = T("To search for a body, enter the ID tag number of the body. You may use % as wildcard. Press 'Search' without input to list all bodies."),
                field = ["pe_label"])

        s3mgr.configure(tablename,
                        super_entity=(db.pr_pentity, s3db.sit_trackable),
                        create_onaccept=dvi_body_onaccept,
                        create_next=URL(f="body", args=["[id]", "checklist"]),
                        search_method=dvi_body_search,
                        list_fields=["id",
                                     "pe_label",
                                     "gender",
                                     "age_group",
                                     "incomplete",
                                     "date_of_recovery",
                                     "location_id"])

        # Checklist of operations =============================================
        #
        resourcename = "checklist"
        tablename = "dvi_checklist"
        table = db.define_table(tablename,
                    super_link(db.pr_pentity), # pe_id
                    Field("personal_effects","integer",
                            requires = IS_IN_SET(task_status, zero=None),
                            default = 1,
                            label = T("Inventory of Effects"),
                            represent = lambda opt: \
                                        task_status.get(opt, UNKNOWN_OPT)),
                    Field("body_radiology","integer",
                            requires = IS_IN_SET(task_status, zero=None),
                            default = 1,
                            label = T("Radiology"),
                            represent = lambda opt: \
                                        task_status.get(opt, UNKNOWN_OPT)),
                    Field("fingerprints","integer",
                            requires = IS_IN_SET(task_status, zero=None),
                            default = 1,
                            label = T("Fingerprinting"),
                            represent = lambda opt: \
                                        task_status.get(opt, UNKNOWN_OPT)),
                    Field("anthropology","integer",
                            requires = IS_IN_SET(task_status, zero=None),
                            default = 1,
                            label = T("Anthropolgy"),
                            represent = lambda opt: \
                                        task_status.get(opt, UNKNOWN_OPT)),
                    Field("pathology","integer",
                            requires = IS_IN_SET(task_status, zero=None),
                            default = 1,
                            label = T("Pathology"),
                            represent = lambda opt: \
                                        task_status.get(opt, UNKNOWN_OPT)),
                    Field("embalming","integer",
                            requires = IS_IN_SET(task_status, zero=None),
                            default = 1,
                            label = T("Embalming"),
                            represent = lambda opt: \
                                        task_status.get(opt, UNKNOWN_OPT)),
                    Field("dna","integer",
                            requires = IS_IN_SET(task_status, zero=None),
                            default = 1,
                            label = T("DNA Profiling"),
                            represent = lambda opt: \
                                        task_status.get(opt, UNKNOWN_OPT)),
                    Field("dental","integer",
                            requires = IS_IN_SET(task_status, zero=None),
                            default = 1,
                            label = T("Dental Examination"),
                            represent = lambda opt: \
                                        task_status.get(opt, UNKNOWN_OPT)),
                    *s3_meta_fields())

        # CRUD Strings
        CREATE_CHECKLIST = T("Create Checklist")
        s3.crud_strings[tablename] = Storage(
            title_create = CREATE_CHECKLIST,
            title_display = T("Checklist of Operations"),
            title_list = T("List Checklists"),
            title_update = T("Update Task Status"),
            title_search = T("Search Checklists"),
            subtitle_create = T("New Checklist"),
            subtitle_list = T("Checklist of Operations"),
            label_list_button = T("Show Checklist"),
            label_create_button = CREATE_CHECKLIST,
            msg_record_created = T("Checklist created"),
            msg_record_modified = T("Checklist updated"),
            msg_record_deleted = T("Checklist deleted"),
            msg_list_empty = T("No Checklist available"))

        s3mgr.model.add_component(table,
                                  pr_pentity=dict(joinby=super_key(db.pr_pentity),
                                                  multiple=False))

        s3mgr.configure(tablename, list_fields=["id"])

        # Effects Inventory ===================================================
        #
        resourcename = "effects"
        tablename = "dvi_effects"
        table = db.define_table(tablename,
                    super_link(db.pr_pentity),  # pe_id
                    Field("clothing", "text"),  # TODO: elaborate
                    Field("jewellery", "text"), # TODO: elaborate
                    Field("footwear", "text"),  # TODO: elaborate
                    Field("watch", "text"),     # TODO: elaborate
                    Field("other", "text"),
                    *s3_meta_fields())

        # CRUD Strings
        ADD_PERSONAL_EFFECTS = T("Add Personal Effects")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_PERSONAL_EFFECTS,
            title_display = T("Personal Effects Details"),
            title_list = T("List Personal Effects"),
            title_update = T("Edit Personal Effects Details"),
            title_search = T("Search Personal Effects"),
            subtitle_create = T("Add New Entry"),
            subtitle_list = T("Personal Effects"),
            label_list_button = T("List Records"),
            label_create_button = ADD_PERSONAL_EFFECTS,
            msg_record_created = T("Record added"),
            msg_record_modified = T("Record updated"),
            msg_record_deleted = T("Record deleted"),
            msg_list_empty = T("No Details currently registered"))

        s3mgr.model.add_component(table,
                                  pr_pentity=dict(joinby=super_key(db.pr_pentity),
                                                  multiple=False))

        s3mgr.configure(tablename, list_fields=["id"])

        # Identification Report ===============================================
        #
        dvi_id_status = {
            1:T("Unidentified"),
            2:T("Preliminary"),
            3:T("Confirmed"),
        }

        dvi_id_methods = {
            1:T("Visual Recognition"),
            2:T("Physical Description"),
            3:T("Fingerprints"),
            4:T("Dental Profile"),
            5:T("DNA Profile"),
            6:T("Combined Method"),
            9:T("Other Evidence")
        }

        def dvi_person_id_comment(fieldname):

            c_title = T("Person.")
            c_comment = T("Type the first few characters of one of the Person's names.")

            ADD_PERSON = T("Add Person")
            return DIV(A(ADD_PERSON,
                         _class="colorbox",
                         _href=URL(c="pr", f="person", args="create",
                                   vars=dict(format="popup", child=fieldname)),
                         _target="top",
                         _title=ADD_PERSON),
                       DIV(DIV(_class="tooltip",
                               _title="%s|%s" % (c_title, c_comment))))

        resourcename = "identification"
        tablename = "dvi_identification"
        table = db.define_table(tablename,
                    super_link(db.pr_pentity), # pe_id
                    Field("status", "integer",
                          requires = IS_IN_SET(dvi_id_status, zero=None),
                          default = 1,
                          label = T("Identification Status"),
                          represent = lambda opt: \
                                      dvi_id_status.get(opt, UNKNOWN_OPT)),
                    person_id("identity",
                                label=T("Identified as"),
                                comment = dvi_person_id_comment("identity"),
                                empty=False),
                    person_id("identified_by",
                                label=T("Identified by"),
                                comment = dvi_person_id_comment("identified_by"),
                                empty=False),
                    Field("method", "integer",
                          requires = IS_IN_SET(dvi_id_methods, zero=None),
                          default = 1,
                          label = T("Method used"),
                          represent = lambda opt: \
                                      dvi_id_methods.get(opt, UNKNOWN_OPT)),
                    Field("comment", "text"),
                    *s3_meta_fields())

        # CRUD Strings
        s3.crud_strings[tablename] = Storage(
            title_create = T("Add Identification Report"),
            title_display = T("Identification Report"),
            title_list = T("List Reports"),
            title_update = T("Edit Identification Report"),
            title_search = T("Search Report"),
            subtitle_create = T("Add New Report"),
            subtitle_list = T("Identification Reports"),
            label_list_button = T("List Reports"),
            label_create_button = T("Add Identification Report"),
            msg_record_created = T("Report added"),
            msg_record_modified = T("Report updated"),
            msg_record_deleted = T("Report deleted"),
            msg_list_empty = T("No Identification Report Available"))

        # Identification reports as component of person entities
        s3mgr.model.add_component(table,
                                  pr_pentity=dict(joinby=super_key(db.pr_pentity),
                                                  multiple=False))

        s3mgr.configure(tablename,
                        mark_required = ["identity", "identified_by"],
                        list_fields = ["id"])

        # -----------------------------------------------------------------------------
        def dvi_rheader(r, tabs=[]):

            """ Page header for component pages """

            if r.name == "morgue":
                rheader_tabs = s3_rheader_tabs(r, tabs)
                morgue = r.record
                if morgue:
                    rheader = DIV(TABLE(

                        TR(TH("%s: " % T("Morgue")),
                            "%(name)s" % morgue)

                        ), rheader_tabs
                    )
                    return rheader

            elif r.name == "body":
                rheader_tabs = s3_rheader_tabs(r, tabs)
                body = r.record
                if body:
                    rheader = DIV(TABLE(
                        TR(TH("%s: " % T("ID Tag Number")),
                            "%(pe_label)s" % body,
                            TH(""),
                            ""),
                        TR(TH("%s: " % T("Gender")),
                            "%s" % pr_gender_opts[body.gender],
                            TH(""),
                            ""),
                        TR(TH("%s: " % T("Age Group")),
                            "%s" % pr_age_group_opts[body.age_group],
                            TH(""),
                            ""),
                        ), rheader_tabs
                    )
                    return rheader

            return None

        return dict(dvi_rheader=dvi_rheader)

    # Provide a handle to this load function
    s3mgr.loader(dvi_tables, "dvi_recreq",
                             "dvi_morgue",
                             "dvi_body",
                             "dvi_checklist",
                             "dvi_effects",
                             "dvi_identification")

# END =========================================================================

