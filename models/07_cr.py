# -*- coding: utf-8 -*-

"""
    Shelter (Camp) Registry, model
"""

if deployment_settings.has_module("cr"):

    # Add Shelters as component of Services, Types as a simple way
    # to get reports showing shelters per type, etc.
    s3mgr.model.add_component("cr_shelter",
                              cr_shelter_type="shelter_type_id",
                              cr_shelter_service="shelter_service_id")

    def shelter_tables():
        """ Load the Shelter Tables when needed """

        module = "cr"

        person_id = s3db.pr_person_id
        location_id = s3db.gis_location_id
        organisation_id = s3db.org_organisation_id

        # -------------------------------------------------------------------------
        # Shelter types
        # e.g. NGO-operated, Government evacuation center, School, Hospital -- see Agasti opt_camp_type.)
        tablename = "cr_shelter_type"
        table = db.define_table(tablename,
                                Field("name", notnull=True,
                                      requires = IS_NOT_ONE_OF(db,
                                                               "%s.name" % tablename)),
                                s3_comments(),

                                *(s3_timestamp() + s3_uid() + s3_deletion_status()))

        # CRUD strings
        if deployment_settings.get_ui_camp():
            ADD_SHELTER_TYPE = T("Add Camp Type")
            LIST_SHELTER_TYPES = T("List Camp Types")
            SHELTER_TYPE_LABEL = T("Camp Type")
            s3.crud_strings[tablename] = Storage(
                title_create = ADD_SHELTER_TYPE,
                title_display = T("Camp Type Details"),
                title_list = LIST_SHELTER_TYPES,
                title_update = T("Edit Camp Type"),
                title_search = T("Search Camp Types"),
                subtitle_create = T("Add New Camp Type"),
                subtitle_list = T("Camp Types"),
                label_list_button = LIST_SHELTER_TYPES,
                label_create_button = ADD_SHELTER_TYPE,
                msg_record_created = T("Camp Type added"),
                msg_record_modified = T("Camp Type updated"),
                msg_record_deleted = T("Camp Type deleted"),
                msg_list_empty = T("No Camp Types currently registered"),
                name_nice = T("Camp"),
                name_nice_plural = T("Camps"))
        else:
            ADD_SHELTER_TYPE = T("Add Shelter Type")
            LIST_SHELTER_TYPES = T("List Shelter Types")
            SHELTER_TYPE_LABEL = T("Shelter Type")
            s3.crud_strings[tablename] = Storage(
                title_create = ADD_SHELTER_TYPE,
                title_display = T("Shelter Type Details"),
                title_list = LIST_SHELTER_TYPES,
                title_update = T("Edit Shelter Type"),
                title_search = T("Search Shelter Types"),
                subtitle_create = T("Add New Shelter Type"),
                subtitle_list = T("Shelter Types"),
                label_list_button = LIST_SHELTER_TYPES,
                label_create_button = ADD_SHELTER_TYPE,
                msg_record_created = T("Shelter Type added"),
                msg_record_modified = T("Shelter Type updated"),
                msg_record_deleted = T("Shelter Type deleted"),
                msg_list_empty = T("No Shelter Types currently registered"),
                name_nice = T("Shelter"),
                name_nice_plural = T("Shelters"))

        shelter_type_id = S3ReusableField("shelter_type_id", db.cr_shelter_type,
                                          requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                          "cr_shelter_type.id",
                                                                          "%(name)s")),
                                          represent = lambda id: (id and [db.cr_shelter_type[id].name] or ["None"])[0],
                                          comment = S3Comment(desc=None,
                                                              title=None,
                                                              anchor_link=\
                                                                  URL(c="cr", f="shelter_type",
                                                                      args="create",
                                                                      vars=dict(format="popup")
                                                                      ),
                                                              anchor_title=ADD_SHELTER_TYPE,
                                                              ),
                                          # A(ADD_SHELTER_TYPE,
                                          #             _class="colorbox",
                                          #             _href=URL(c="cr",
                                          #                       f="shelter_type",
                                          #                       args="create",
                                          #                       vars=dict(format="popup")),
                                          #             _target="top",
                                          #             _title=ADD_SHELTER_TYPE),
                                          ondelete = "RESTRICT",
                                          label = SHELTER_TYPE_LABEL)

        # -------------------------------------------------------------------------
        # Shelter services
        # e.g. medical, housing, food, ...
        tablename = "cr_shelter_service"
        table = db.define_table(tablename,
                                Field("name", notnull=True),
                                s3_comments(),

                                *(s3_timestamp() + s3_uid() + s3_deletion_status()))

        # CRUD strings
        if deployment_settings.get_ui_camp():
            ADD_SHELTER_SERVICE = T("Add Camp Service")
            LIST_SHELTER_SERVICES = T("List Camp Services")
            SHELTER_SERVICE_LABEL = T("Camp Service")
            s3.crud_strings[tablename] = Storage(
                title_create = ADD_SHELTER_SERVICE,
                title_display = T("Camp Service Details"),
                title_list = LIST_SHELTER_SERVICES,
                title_update = T("Edit Camp Service"),
                title_search = T("Search Camp Services"),
                subtitle_create = T("Add New Camp Service"),
                subtitle_list = T("Camp Services"),
                label_list_button = LIST_SHELTER_SERVICES,
                label_create_button = ADD_SHELTER_SERVICE,
                msg_record_created = T("Camp Service added"),
                msg_record_modified = T("Camp Service updated"),
                msg_record_deleted = T("Camp Service deleted"),
                msg_list_empty = T("No Camp Services currently registered"),
                name_nice = T("Camp Service"),
                name_nice_plural = T("Camp Services"))
        else:
            ADD_SHELTER_SERVICE = T("Add Shelter Service")
            LIST_SHELTER_SERVICES = T("List Shelter Services")
            SHELTER_SERVICE_LABEL = T("Shelter Service")
            s3.crud_strings[tablename] = Storage(
                title_create = ADD_SHELTER_SERVICE,
                title_display = T("Shelter Service Details"),
                title_list = LIST_SHELTER_SERVICES,
                title_update = T("Edit Shelter Service"),
                title_search = T("Search Shelter Services"),
                subtitle_create = T("Add New Shelter Service"),
                subtitle_list = T("Shelter Services"),
                label_list_button = LIST_SHELTER_SERVICES,
                label_create_button = ADD_SHELTER_SERVICE,
                msg_record_created = T("Shelter Service added"),
                msg_record_modified = T("Shelter Service updated"),
                msg_record_deleted = T("Shelter Service deleted"),
                msg_list_empty = T("No Shelter Services currently registered"),
                name_nice = T("Shelter Service"),
                name_nice_plural = T("Shelter Services"))

        def cr_shelter_service_represent(shelter_service_ids):
            table = db.cr_shelter_service
            if not shelter_service_ids:
                return NONE
            elif isinstance(shelter_service_ids, (list, tuple)):
                query = (table.id.belongs(shelter_service_ids))
                shelter_services = db(query).select(table.name)
                return ", ".join([s.name for s in shelter_services])
            else:
                query = (table.id == shelter_service_ids)
                shelter_service = db(query).select(table.name,
                                                   limitby=(0, 1)).first()
                return shelter_service and shelter_service.name or NONE

        shelter_service_id = S3ReusableField("shelter_service_id",
                                             "list:reference cr_shelter_service",
                                             sortby="name",
                                             requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                             "cr_shelter_service.id",
                                                                             "%(name)s", multiple=True)),
                                             represent = cr_shelter_service_represent,
                                             label = SHELTER_SERVICE_LABEL,
                                             comment = A(ADD_SHELTER_SERVICE,
                                                         _class="colorbox",
                                                         _href=URL(c="cr", f="shelter_service",
                                                                   args="create",
                                                                   vars=dict(format="popup")),
                                                         _target="top",
                                                         _title=ADD_SHELTER_SERVICE),
                                             ondelete = "RESTRICT",
                                             #widget = SQLFORM.widgets.checkboxes.widget
                                             )

        # -------------------------------------------------------------------------
        resourcename = "shelter"
        tablename = "cr_shelter"
        table = db.define_table(tablename,
                                super_link("site_id", "org_site"),
                                #Field("code",
                                #      length=10,           # Mayon compatibility
                                #      notnull=True,
                                #      unique=True, label=T("Code")),
                                Field("name", notnull=True,
                                      length=64,            # Mayon compatibility
                                      requires = IS_NOT_EMPTY(),
                                      label = T("Shelter Name")),
                                organisation_id(widget = S3OrganisationAutocompleteWidget(default_from_profile = True)),
                                shelter_type_id(),          # e.g. NGO-operated, Government evacuation center, School, Hospital -- see Agasti opt_camp_type.)
                                shelter_service_id(),       # e.g. medical, housing, food, ...
                                location_id(),
                                Field("phone", label = T("Phone"),
                                      requires = IS_NULL_OR(s3_phone_requires)),
                                person_id(label = T("Contact Person")),
                                Field("capacity", "integer",
                                      label = T("Capacity (Max Persons)"),
                                      requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 999999))),
                                Field("population", "integer",
                                      label = T("Population"),
                                      requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 999999))),
                                Field("source",
                                      label = T("Source")),
                                #document_id(), # Better to have multiple Documents on a Tab
                                s3_comments(),
                                *(address_fields() + s3_meta_fields()))

        # CRUD strings
        if deployment_settings.get_ui_camp():
            ADD_SHELTER = T("Add Camp")
            LIST_SHELTERS = T("List Camps")
            SHELTER_LABEL = T("Camp Service")
            SHELTER_HELP = T("The Camp this Request is from")
            s3.crud_strings[tablename] = Storage(
                title_create = ADD_SHELTER,
                title_display = T("Camp Details"),
                title_list = LIST_SHELTERS,
                title_update = T("Edit Camp"),
                title_search = T("Search Camps"),
                subtitle_create = T("Add New Camp"),
                subtitle_list = T("Camps"),
                label_list_button = LIST_SHELTERS,
                label_create_button = ADD_SHELTER,
                msg_record_created = T("Camp added"),
                msg_record_modified = T("Camp updated"),
                msg_record_deleted = T("Camp deleted"),
                msg_list_empty = T("No Camps currently registered"),
                name_nice = T("Camp Service"),
                name_nice_plural = T("Camp Services"))

        else:
            ADD_SHELTER = T("Add Shelter")
            LIST_SHELTERS = T("List Shelters")
            SHELTER_LABEL = T("Shelter Service")
            SHELTER_HELP = T("The Shelter this Request is from")
            s3.crud_strings[tablename] = Storage(
                title_create = ADD_SHELTER,
                title_display = T("Shelter Details"),
                title_list = LIST_SHELTERS,
                title_update = T("Edit Shelter"),
                title_search = T("Search Shelters"),
                subtitle_create = T("Add New Shelter"),
                subtitle_list = T("Shelters"),
                label_list_button = LIST_SHELTERS,
                label_create_button = ADD_SHELTER,
                msg_record_created = T("Shelter added"),
                msg_record_modified = T("Shelter updated"),
                msg_record_deleted = T("Shelter deleted"),
                msg_list_empty = T("No Shelters currently registered"),
                name_nice = T("Shelter"),
                name_nice_plural = T("Shelters"))

        # Reusable field
        shelter_id = S3ReusableField("shelter_id", db.cr_shelter,
                                     requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                     "cr_shelter.id",
                                                                     "%(name)s",
                                                                     sort=True)),
                                     represent = lambda id: (id and [db.cr_shelter[id].name] or ["None"])[0],
                                     ondelete = "RESTRICT",
                                     comment = DIV(A(ADD_SHELTER,
                                                     _class="colorbox",
                                                     _href=URL(c="cr", f="shelter",
                                                               args="create",
                                                               vars=dict(format="popup")),
                                                     _target="top",
                                                     _title=ADD_SHELTER),
                                               DIV( _class="tooltip",
                                                    _title="%s|%s" % (SHELTER_LABEL,
                                                                      "%s (%s)." % (SHELTER_HELP,
                                                                                    T("optional"))))),
                                     label = SHELTER_LABEL,
                                     widget = S3AutocompleteWidget("cr", "shelter")
                                     )

        s3mgr.configure(tablename,
                        super_entity="org_site",
                        # Update the Address Fields
                        onvalidation=address_onvalidation,
                        list_fields=["id",
                                     "name",
                                     "shelter_type_id",
                                     "shelter_service_id",
                                     "capacity",
                                     "population",
                                     "location_id",
                                     "L1",
                                     "L2",
                                     "L3",
                                     "person_id",
                                    ])

        # -----------------------------------------------------------------------------
        def shelter_rheader(r, tabs=[]):

            """ Resource Headers """

            if r.representation == "html":
                tablename, record = s3_rheader_resource(r)
                if tablename == "cr_shelter" and record:
                    if not tabs:
                        tabs = [(T("Basic Details"), None),
                                (T("People"), "presence"),
                                (T("Staff"), "human_resource"),
                            ]
                        if deployment_settings.has_module("assess"):
                            tabs.append((T("Assessments"), "rat"))

                        try:
                            tabs = tabs + response.s3.req_tabs(r)
                        except:
                            pass
                        try:
                            tabs = tabs + s3db.inv_tabs(r)
                        except:
                            pass

                    rheader_tabs = s3_rheader_tabs(r, tabs)

                    if r.name == "shelter":
                        location = s3db.gis_location_represent(record.location_id)

                        rheader = DIV(TABLE(
                                            TR(
                                                TH("%s: " % T("Name")), record.name
                                              ),
                                            TR(
                                                TH("%s: " % T("Location")), location
                                              ),
                                            ),
                                      rheader_tabs)
                    else:
                        rheader = DIV(TABLE(
                                            TR(
                                                TH("%s: " % T("Name")), record.name
                                              ),
                                            ),
                                      rheader_tabs)

                    if r.component and r.component.name == "req":
                        # Inject the helptext script
                        rheader.append(response.s3.req_helptext_script)

                    return rheader
            return None
        # Pass variables back to global scope (response.s3.*)
        return dict(
            shelter_id = shelter_id,
            shelter_rheader = shelter_rheader,
            ADD_SHELTER = ADD_SHELTER,
            SHELTER_LABEL = SHELTER_LABEL
            )

    # Provide a handle to this load function
    s3mgr.loader(shelter_tables,
                 "cr_shelter_type",
                 "cr_shelter_service",
                 "cr_shelter")

else:
    def shelter_id(**arguments):
        """ Allow FKs to be added safely to other models in case module disabled """
        return Field("shelter_id", "integer", readable=False, writable=False)

# END =========================================================================

