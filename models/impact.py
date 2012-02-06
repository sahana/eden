# -*- coding: utf-8 -*-

"""
    Impact

    Impact resources used by the old Assessment module
"""


if deployment_settings.has_module("assess"):

    # Impact as component of incident reports
    s3mgr.model.add_component("impact_impact", irs_ireport="ireport_id")

    def impact_tables():
        """ Load the Impact tables as-needed """

        sector_id = s3db.org_sector_id
        ireport_id = s3db.ireport_id

        # Load the models we depend on
        if deployment_settings.has_module("assess"):
            s3mgr.load("assess_assess")
        assess_id = response.s3.assess_id

        module = "impact"

        # -------------------------------------------------------------------------
        # Impact Type
        resourcename = "type"
        tablename = "%s_%s" % (module, resourcename)
        table = db.define_table(tablename,
                                Field("name", length=128, notnull=True, unique=True),
                                sector_id(),
                                *s3_meta_fields())

        # CRUD strings
        ADD_IMPACT_TYPE = T("Add Impact Type")
        LIST_IMPACT_TYPE = T("List Impact Types")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_IMPACT_TYPE,
            title_display = T("Impact Type Details"),
            title_list = LIST_IMPACT_TYPE,
            title_update = T("Edit Impact Type"),
            title_search = T("Search Impact Type"),
            subtitle_create = T("Add New Impact Type"),
            subtitle_list = T("Impact Types"),
            label_list_button = LIST_IMPACT_TYPE,
            label_create_button = ADD_IMPACT_TYPE,
            label_delete_button = T("Delete Impact Type"),
            msg_record_created = T("Impact Type added"),
            msg_record_modified = T("Impact Type updated"),
            msg_record_deleted = T("Impact Type deleted"),
            msg_list_empty = T("No Impact Types currently registered"))

        def impact_type_comment():
            if auth.has_membership(auth.id_group("'Administrator'")):
                return DIV(A(ADD_IMPACT_TYPE,
                             _class="colorbox",
                             _href=URL(c="impact", f="type",
                                       args="create",
                                       vars=dict(format="popup",
                                                 child="impact_type_id")),
                             _target="top",
                             _title=ADD_IMPACT_TYPE
                             )
                           )
            else:
                return None

        impact_type_id = S3ReusableField("impact_type_id", db.impact_type,
                                         sortby="name",
                                         requires = IS_NULL_OR(IS_ONE_OF(db, "impact_type.id","%(name)s", sort=True)),
                                         represent = lambda id: s3_get_db_field_value(tablename = "impact_type",
                                                                                      fieldname = "name",
                                                                                      look_up_value = id),
                                         label = T("Impact Type"),
                                         comment = impact_type_comment(),
                                         ondelete = "RESTRICT")

        # =====================================================================
        # Impact
        # Load model
        s3mgr.load("irs_ireport")
        ireport_id = response.s3.ireport_id

        resourcename = "impact"
        tablename = "%s_%s" % (module, resourcename)
        table = db.define_table(tablename,
                                ireport_id(readable=False, writable=False),
                                assess_id(readable=False, writable=False),
                                impact_type_id(),
                                Field("value", "double"),
                                Field("severity", "integer",
                                      default = 0),
                                s3_comments(),
                                *s3_meta_fields())

        table.severity.requires = IS_EMPTY_OR(IS_IN_SET(assess_severity_opts))
        table.severity.widget=SQLFORM.widgets.radio.widget
        table.severity.represent = s3_assess_severity_represent

        # CRUD strings
        ADD_IMPACT = T("Add Impact")
        LIST_IMPACT = T("List Impacts")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_IMPACT,
            title_display = T("Impact Details"),
            title_list = LIST_IMPACT,
            title_update = T("Edit Impact"),
            title_search = T("Search Impacts"),
            subtitle_create = T("Add New Impact"),
            subtitle_list = T("Impacts"),
            label_list_button = LIST_IMPACT,
            label_create_button = ADD_IMPACT,
            label_delete_button = T("Delete Impact"),
            msg_record_created = T("Impact added"),
            msg_record_modified = T("Impact updated"),
            msg_record_deleted = T("Impact deleted"),
            msg_list_empty = T("No Impacts currently registered"))

    # Provide a handle to this load function
    s3mgr.loader(impact_tables,
                 "impact_impact",
                 "impact_type")

# END =========================================================================

