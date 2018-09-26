# -*- coding: utf-8 -*-

""" Sahana Eden Event Model

    @copyright: 2009-2018 (c) Sahana Software Foundation
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

__all__ = ("S3EventModel",
           "S3EventLocationModel",
           "S3EventNameModel",
           "S3EventTagModel",
           "S3IncidentModel",
           "S3IncidentLogModel",
           "S3IncidentReportModel",
           "S3IncidentReportOrganisationGroupModel",
           "S3IncidentTypeModel",
           "S3IncidentTypeTagModel",
           "S3EventActivityModel",
           "S3EventAssetModel",
           "S3EventBookmarkModel",
           "S3EventCMSModel",
           "S3EventCMSTagModel",
           "S3EventDCModel",
           "S3EventForumModel",
           "S3EventHRModel",
           "S3EventTeamModel",
           "S3EventImpactModel",
           "S3EventMapModel",
           "S3EventNeedModel",
           "S3EventNeedResponseModel",
           "S3EventOrganisationModel",
           "S3EventProjectModel",
           "S3EventRequestModel",
           "S3EventResourceModel",
           "S3EventScenarioModel",
           "S3EventScenarioAssetModel",
           "S3EventScenarioHRModel",
           "S3EventScenarioOrganisationModel",
           "S3EventScenarioTaskModel",
           "S3EventSiteModel",
           "S3EventShelterModel",
           "S3EventSitRepModel",
           "S3EventTagModel",
           "S3EventTaskModel",
           #"event_ActionPlan",
           #"event_ScenarioActionPlan",
           #"event_ApplyScenario",
           #"event_EventAssignMethod",
           #"event_IncidentAssignMethod",
           "event_notification_dispatcher",
           "event_event_list_layout",
           "event_incident_list_layout",
           "event_rheader",
           "event_set_event_from_incident",
           )

from gluon import *
from gluon.storage import Storage

from ..s3 import *
from s3layouts import S3PopupLink

# =============================================================================
class S3EventModel(S3Model):
    """
        Event Model

        http://eden.sahanafoundation.org/wiki/BluePrintScenario

        Events are a high-level term, such as a 'Disaster'

        Link tables are in separate classes to increase performance & allow
        the system to be more modular
    """

    names = ("event_event_type",
             "event_type_id",
             "event_event",
             "event_event_id",
             )

    def model(self):

        T = current.T
        db = current.db
        s3 = current.response.s3
        settings = current.deployment_settings

        configure = self.configure
        crud_strings = s3.crud_strings
        define_table = self.define_table
        set_method = self.set_method

        messages = current.messages
        NONE = messages["NONE"]
        #AUTOCOMPLETE_HELP = messages.AUTOCOMPLETE_HELP

        disaster = settings.get_event_label() # If we add more options in future then == "Disaster"
        exercise = settings.get_event_exercise()
        hierarchical_event_types = settings.get_event_types_hierarchical()

        # ---------------------------------------------------------------------
        # Event Types
        #
        tablename = "event_event_type"
        define_table(tablename,
                     Field("name", notnull=True, length=64,
                           label = T("Name"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(64),
                                       ],
                           ),
                     Field("parent", "reference event_event_type", # This form of hierarchy may not work on all Databases
                           label = T("SubType of"),
                           ondelete = "RESTRICT",
                           readable = hierarchical_event_types,
                           writable = hierarchical_event_types,
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        type_represent = S3Represent(lookup=tablename, translate=True)

        if hierarchical_event_types:
            hierarchy = "parent"
            # Can't be defined in-line as otherwise get a circular reference
            table = db[tablename]
            table.parent.represent = type_represent
            table.parent.requires = IS_EMPTY_OR(
                                        IS_ONE_OF(db, "event_event_type.id",
                                                  type_represent,
                                                  # If limiting to just 1 level of parent
                                                  #filterby="parent",
                                                  #filter_opts=(None,),
                                                  orderby="event_event_type.name"))
            event_type_widget = S3HierarchyWidget(lookup = "event_event_type",
                                                  represent = type_represent,
                                                  multiple = False,
                                                  leafonly = True,
                                                  )
            event_type_comment = None
        else:
            hierarchy = None
            event_type_widget = None
            event_type_comment = None
            # Uncomment these to use an Autocomplete & not a Dropdown
            #event_type_widget = S3AutocompleteWidget()
            #event_typecomment = DIV(_class="tooltip",
            #                        _title="%s|%s" % (T("Event Type"),
            #                                          AUTOCOMPLETE_HELP))

        if disaster:
            label = T("Disaster Type")
            crud_strings[tablename] = Storage(
                label_create = T("Create Disaster Type"),
                title_display = T("Disaster Type Details"),
                title_list = T("Disaster Types"),
                title_update = T("Edit Disaster Type"),
                title_upload = T("Import Disaster Types"),
                label_list_button = T("List Disaster Types"),
                label_delete_button = T("Delete Disaster Type"),
                msg_record_created = T("Disaster Type added"),
                msg_record_modified = T("Disaster Type updated"),
                msg_record_deleted = T("Disaster Type removed"),
                msg_list_empty = T("No Disaster Types currently registered")
                )
        else:
            label = T("Event Type")
            crud_strings[tablename] = Storage(
                label_create = T("Create Event Type"),
                title_display = T("Event Type Details"),
                title_list = T("Event Types"),
                title_update = T("Edit Event Type"),
                title_upload = T("Import Event Types"),
                label_list_button = T("List Event Types"),
                label_delete_button = T("Delete Event Type"),
                msg_record_created = T("Event Type added"),
                msg_record_modified = T("Event Type updated"),
                msg_record_deleted = T("Event Type removed"),
                msg_list_empty = T("No Event Types currently registered")
                )

        event_type_id = S3ReusableField("event_type_id", "reference %s" % tablename,
                                        label = label,
                                        ondelete = "RESTRICT",
                                        represent = type_represent,
                                        requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "event_event_type.id",
                                                              type_represent,
                                                              orderby="event_event_type.name",
                                                              sort=True)),
                                        sortby = "name",
                                        widget = event_type_widget,
                                        comment = event_type_comment,
                                        )

        configure(tablename,
                  deduplicate = S3Duplicate(),
                  hierarchy = hierarchy,
                  )

        # ---------------------------------------------------------------------
        # Events / Disasters
        #
        #   Events can be a way of grouping related Incidents or used standalone
        #
        # ---------------------------------------------------------------------
        tablename = "event_event"
        define_table(tablename,
                     self.super_link("doc_id", "doc_entity"),
                     Field("name",      # Name could be a code
                           length = 64,   # Mayon compatibility
                           label = T("Name"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(64),
                                       ],
                           ),
                     event_type_id(),
                     #Field("intensity",
                     #      label = T("Intensity"),
                     #      comment = DIV(_class="tooltip",
                     #                    _title="%s|%s" % (T("Intensity"),
                     #                                      T("e.g. Category for a Typhoon or Magnitude for an Earthquake"))),
                     #      ),
                     self.org_organisation_id(
                        comment = DIV(_class="tooltip",
                                       _title="%s|%s" % (T("Organization"),
                                                         T("The organization managing this event"))),
                        # Enable in the template if-required
                        readable = False,
                        writable = False,
                        ),
                     Field("exercise", "boolean",
                           default = False,
                           label = T("Exercise?"),
                           represent = lambda opt: "√" if opt else NONE,
                           readable = exercise,
                           writable = exercise,
                           #comment = DIV(_class="tooltip",
                           #              _title="%s|%s" % (T("Exercise"),
                                                           # Should!
                           #                                T("Exercises mean all screens have a watermark & all notifications have a prefix."))),
                           ),
                     s3_datetime("start_date",
                                 default = "now",
                                 label = T("Start Date"),
                                 represent = "date",
                                 widget = "date",
                                 set_min = "#event_event_end_date",
                                 ),
                     s3_datetime("end_date",
                                 label = T("End Date"),
                                 represent = "date",
                                 widget = "date",
                                 set_max = "#event_event_start_date",
                                 ),
                     Field.Method("year", self.event_event_year),
                     Field("closed", "boolean",
                           default = False,
                           label = T("Closed"),
                           represent = s3_yes_no_represent,
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        if disaster:
            label = T("Disaster")
            ADD_EVENT = T("New Disaster")
            crud_strings[tablename] = Storage(
                label_create = ADD_EVENT,
                title_display = T("Disaster Details"),
                title_list = T("Disasters"),
                title_update = T("Edit Disaster"),
                label_list_button = T("List Disasters"),
                label_delete_button = T("Delete Disaster"),
                msg_record_created = T("Disaster added"),
                msg_record_modified = T("Disaster updated"),
                msg_record_deleted = T("Disaster deleted"),
                msg_list_empty = T("No Disasters currently registered"))
        else:
            label = T("Event")
            ADD_EVENT = T("New Event")
            crud_strings[tablename] = Storage(
                label_create = ADD_EVENT,
                title_display = T("Event Details"),
                title_list = T("Events"),
                title_update = T("Edit Event"),
                label_list_button = T("List Events"),
                label_delete_button = T("Delete Event"),
                msg_record_created = T("Event added"),
                msg_record_modified = T("Event updated"),
                msg_record_deleted = T("Event deleted"),
                msg_list_empty = T("No Events currently registered"))

        represent = S3Represent(lookup=tablename)
        event_id = S3ReusableField("event_id", "reference %s" % tablename,
                                   sortby="name",
                                   requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "event_event.id",
                                                          represent,
                                                          filterby="closed",
                                                          filter_opts=(False,),
                                                          orderby="event_event.name",
                                                          sort=True)),
                                   represent = represent,
                                   label = label,
                                   ondelete = "CASCADE",
                                   # Uncomment these to use an Autocomplete & not a Dropdown
                                   #widget = S3AutocompleteWidget()
                                   #comment = DIV(_class="tooltip",
                                   #              _title="%s|%s" % (T("Event"),
                                   #                                AUTOCOMPLETE_HELP))
                                   )

        # Which levels of Hierarchy are we using?
        levels = current.gis.get_relevant_hierarchy_levels()

        filter_widgets = [S3LocationFilter("event_location.location_id",
                                           levels = levels,
                                           label = T("Location"),
                                           ),
                          # @ToDo: Filter for events which are open within a date range
                          #S3DateFilter("start_date",
                          #             label = None,
                          #             hide_time = True,
                          #             input_labels = {"ge": "From", "le": "To"}
                          #             ),
                          # Typically we just need to filter by Year
                          S3OptionsFilter("year",
                                          label = T("Year"),
                                          ),
                          S3OptionsFilter("closed",
                                          label = T("Status"),
                                          options = OrderedDict([(False, T("Open")),
                                                                 (True, T("Closed")),
                                                                 ]),
                                          cols = 2,
                                          default = False,
                                          sort = False,
                                          ),
                          ]

        if hierarchical_event_types:
            filter_widgets.insert(0, S3HierarchyFilter("event_type_id",
                                                       label = T("Type"),
                                                       ))
        else:
            filter_widgets.insert(0, S3OptionsFilter("event_type_id",
                                                     label = T("Type"),
                                                     #multiple = False,
                                                     #options = lambda: \
                                                     #  s3_get_filter_opts("event_event_type",
                                                     #                     translate = True)
                                                     ))
        report_fields = ["event_type_id",
                         ]
        rappend = report_fields.append
        for level in levels:
            rappend("event_location.location_id$%s" % level)
        rappend((T("Year"), "year"))

        report_options = Storage(
            rows = report_fields,
            cols = report_fields,
            fact = [(T("Number of Disasters"), "count(id)")],
            defaults = Storage(
                rows = "event_type_id",
                cols = "event_location.location_id$%s" % levels[0], # Highest-level of hierarchy
                fact = "count(id)",
                totals = True,
                chart = "breakdown:rows",
                table = "collapse",
                ),
            )

        # Custom Form
        crud_fields = ["name",
                       "event_type_id",
                       "start_date",
                       "closed",
                       "end_date",
                       S3SQLInlineComponent("event_location",
                                            label = T("Locations"),
                                            #multiple = False,
                                            fields = [("", "location_id")],
                                            ),
                       "comments",
                       ]

        list_fields = ["name",
                       (T("Type"), "event_type_id$name"),
                       (T("Location"), "location.name"),
                       "start_date",
                       "closed",
                       "comments",
                       ]

        if exercise:
            crud_fields.insert(1, "exercise")
            list_fields.insert(4, "exercise")
            filter_widgets.insert(2, S3OptionsFilter("exercise",
                                                     label = T("Exercise"),
                                                     options = OrderedDict([(True, T("Yes")),
                                                                            (False, T("No")),
                                                                            ]),
                                                     cols = 2,
                                                     default = False,
                                                     sort = False,
                                                     ))

        crud_form = S3SQLCustomForm(*crud_fields)

        configure(tablename,
                  context = {"location": "event_location.location_id",
                             },
                  crud_form = crud_form,
                  deduplicate = S3Duplicate(primary = ("name",
                                                       ),
                                            secondary = ("event_type_id",
                                                         "start_date",
                                                         ),
                                            ),
                  extra_fields = ["start_date"],
                  filter_widgets = filter_widgets,
                  list_fields = list_fields,
                  list_layout = event_event_list_layout,
                  list_orderby = "event_event.start_date desc",
                  orderby = "event_event.start_date desc",
                  report_options = report_options,
                  super_entity = "doc_entity",
                  update_onaccept = self.event_update_onaccept,
                  )

        # Components
        self.add_components(tablename,
                            # Should be able to do everything via the link table
                            #event_post = "event_id",
                            cms_post = {"link": "event_post",
                                        "joinby": "event_id",
                                        "key": "post_id",
                                        "actuate": "replace",
                                        },
                            cr_shelter = {"link": "event_shelter",
                                          "joinby": "event_id",
                                          "key": "shelter_id",
                                          "actuate": "replace",
                                          },
                            event_bookmark = "event_id",
                            event_event_name = "event_id",
                            event_tag = "event_id",       # cms_tag
                            event_event_tag = "event_id", # Key-Value Store
                            event_incident = "event_id",
                            event_sitrep = "event_id",
                            dc_response = {"link": "event_response",
                                           "joinby": "event_id",
                                           "key": "response_id",
                                           "actuate": "replace",
                                           },
                            dc_target = {"link": "event_target",
                                         "joinby": "event_id",
                                         "key": "target_id",
                                         "actuate": "replace",
                                         },
                            gis_location = {"link": "event_event_location",
                                            "joinby": "event_id",
                                            "key": "location_id",
                                            "actuate": "hide",
                                            },
                            # Should be able to do everything via the link table
                            #event_activity = {"name": "event_activity",
                            #                  "joinby": "event_id",
                            #                  },
                            project_activity = {"link": "event_activity",
                                                "joinby": "event_id",
                                                "key": "activity_id",
                                                "actuate": "replace",
                                                },
                            # Should be able to do everything via the link table
                            #event_project = {"name": "event_project",
                            #                 "joinby": "event_id",
                            #                 },
                            project_project = {"link": "event_project",
                                               "joinby": "event_id",
                                               "key": "project_id",
                                               "actuate": "replace",
                                               },
                            project_task = {"link": "event_task",
                                            "joinby": "event_id",
                                            "key": "task_id",
                                            "actuate": "replace",
                                            #"autocomplete": "name",
                                            "autodelete": True,
                                            },
                            event_event_location = "event_id",
                            # Should be able to do everything via the link table
                            event_organisation = {"name": "event_organisation",
                                                  "joinby": "event_id",
                                                  },
                            org_organisation = {"link": "event_organisation",
                                                "joinby": "event_id",
                                                "key": "organisation_id",
                                                #"actuate": "embed",
                                                "actuate": "hide",
                                                #"autocomplete": "name",
                                                "autodelete": False,
                                                },
                            # Should be able to do everything via the link table
                            #event_team = "event_id",
                            pr_group = {"link": "event_team",
                                        "joinby": "event_id",
                                        "key": "group_id",
                                        "actuate": "hide",
                                        "autodelete": False,
                                        },
                            event_human_resource = "event_id",
                            pr_person = {"link": "event_human_resource",
                                         "joinby": "event_id",
                                         "key": "person_id",
                                         "actuate": "hide",
                                         "autodelete": False,
                                         },
                            req_need = {"link": "event_event_need",
                                        "joinby": "event_id",
                                        "key": "need_id",
                                        "actuate": "hide",
                                        "autodelete": False,
                                        },
                            req_req = {"link": "event_request",
                                       "joinby": "event_id",
                                       "key": "req_id",
                                       "actuate": "hide",
                                       "autodelete": False,
                                       },
                            stats_impact = {"link": "event_event_impact",
                                            "joinby": "event_id",
                                            "key": "impact_id",
                                            "actuate": "replace",
                                            },
                            event_event_impact = "event_id",
                            )

        # Custom Methods
        set_method("event", "event",
                   method = "dispatch",
                   action = event_notification_dispatcher)

        set_method("event", "event",
                   method = "add_bookmark",
                   action = self.event_add_bookmark)

        set_method("event", "event",
                   method = "remove_bookmark",
                   action = self.event_remove_bookmark)

        set_method("event", "event",
                   method = "add_tag",
                   action = self.event_add_tag)

        set_method("event", "event",
                   method = "remove_tag",
                   action = self.event_remove_tag)

        set_method("event", "event",
                   method = "share",
                   action = self.event_share)

        set_method("event", "event",
                   method = "unshare",
                   action = self.event_unshare)

        # Custom Method to Assign HRs
        set_method("event", "event",
                   method = "assign",
                   action = self.pr_AssignMethod(component="human_resource"))

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"event_type_id": event_type_id,
                "event_event_id": event_id,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """
            Return safe defaults in case the model has been deactivated.
        """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False)

        return {"event_event_id": lambda **attr: dummy("event_id"),
                "event_type_id": lambda **attr: dummy("event_type_id"),
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def event_add_bookmark(r, **attr):
        """
            Bookmark an Event

            S3Method for interactive requests
        """

        event_id = r.id
        user = current.auth.user
        user_id = user and user.id
        if not event_id or not user_id:
            r.error(405, current.ERROR.BAD_METHOD)

        db = current.db
        s3db = current.s3db
        ltable = s3db.event_bookmark
        query = (ltable.event_id == event_id) & \
                (ltable.user_id == user_id)
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
                    data = {"deleted": False}
                db(ltable.id == link_id).update(**data)
        else:
            link_id = ltable.insert(event_id = event_id,
                                    user_id = user_id,
                                    )

        output = current.xml.json_message(True, 200, current.T("Bookmark Added"))
        current.response.headers["Content-Type"] = "application/json"
        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def event_remove_bookmark(r, **attr):
        """
            Remove a Bookmark for an Event

            S3Method for interactive requests
        """

        event_id = r.id
        user = current.auth.user
        user_id = user and user.id
        if not event_id or not user_id:
            r.error(405, current.ERROR.BAD_METHOD)

        s3db = current.s3db
        ltable = s3db.event_bookmark
        query = (ltable.event_id == event_id) & \
                (ltable.user_id == user_id)
        exists = current.db(query).select(ltable.id,
                                          ltable.deleted,
                                          limitby=(0, 1)
                                          ).first()
        if exists and not exists.deleted:
            resource = s3db.resource("event_bookmark", id=exists.id)
            resource.delete()

        output = current.xml.json_message(True, 200, current.T("Bookmark Removed"))
        current.response.headers["Content-Type"] = "application/json"
        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def event_add_tag(r, **attr):
        """
            Add a Tag to an Event

            S3Method for interactive requests
            - designed to be called as an afterTagAdded callback to tag-it.js
        """

        event_id = r.id
        if not event_id or len(r.args) < 3:
            r.error(405, current.ERROR.BAD_METHOD)

        db = current.db
        s3db = current.s3db
        tag = r.args[2]

        ttable = s3db.cms_tag
        ltable = s3db.event_tag
        exists = db(ttable.name == tag).select(ttable.id,
                                               ttable.deleted,
                                               ttable.deleted_fk,
                                               limitby=(0, 1)
                                               ).first()
        if exists:
            tag_id = exists.id
            if exists.deleted:
                if exists.deleted_fk:
                    data = json.loads(exists.deleted_fk)
                    data["deleted"] = False
                else:
                    data = {"deleted": False}
                db(ttable.id == tag_id).update(**data)
        else:
            tag_id = ttable.insert(name=tag)
        query = (ltable.tag_id == tag_id) & \
                (ltable.event_id == event_id)
        exists = db(query).select(ltable.id,
                                  ltable.deleted,
                                  ltable.deleted_fk,
                                  limitby=(0, 1)
                                  ).first()
        if exists:
            if exists.deleted:
                if exists.deleted_fk:
                    data = json.loads(exists.deleted_fk)
                    data["deleted"] = False
                else:
                    data = {"deleted": False}
                db(ltable.id == exists.id).update(**data)
        else:
            ltable.insert(event_id = event_id,
                          tag_id = tag_id,
                          )

        output = current.xml.json_message(True, 200, current.T("Tag Added"))
        current.response.headers["Content-Type"] = "application/json"
        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def event_remove_tag(r, **attr):
        """
            Remove a Tag from an Event

            S3Method for interactive requests
            - designed to be called as an afterTagRemoved callback to tag-it.js
        """

        event_id = r.id
        if not event_id or len(r.args) < 3:
            r.error(405, current.ERROR.BAD_METHOD)

        db = current.db
        s3db = current.s3db
        tag = r.args[2]

        ttable = s3db.cms_tag
        exists = db(ttable.name == tag).select(ttable.id,
                                               ttable.deleted,
                                               limitby=(0, 1)
                                               ).first()
        if exists:
            tag_id = exists.id
            ltable = s3db.event_tag
            query = (ltable.tag_id == tag_id) & \
                    (ltable.event_id == event_id)
            exists = db(query).select(ltable.id,
                                      ltable.deleted,
                                      limitby=(0, 1)
                                      ).first()
            if exists and not exists.deleted:
                resource = s3db.resource("event_tag", id=exists.id)
                resource.delete()

        output = current.xml.json_message(True, 200, current.T("Tag Removed"))
        current.response.headers["Content-Type"] = "application/json"
        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def event_share(r, **attr):
        """
            Share an Event to a Forum

            S3Method for interactive requests
            - designed to be called via AJAX
        """

        event_id = r.id
        if not event_id or len(r.args) < 3:
            r.error(405, current.ERROR.BAD_METHOD)

        db = current.db
        s3db = current.s3db
        auth = current.auth
        forum_id = r.args[2]

        if not auth.s3_has_role("ADMIN"):
            # Check that user is a member of the forum
            mtable = s3db.pr_forum_membership
            ptable = s3db.pr_person
            query = (ptable.pe_id == auth.user.pe_id) & \
                    (mtable.person_id == ptable.id)
            member = db(query).select(mtable.id,
                                      limitby = (0, 1)
                                      ).first()
            if not member:
                output = current.xml.json_message(False, 403, current.T("Cannot Share to a Forum unless you are a Member"))
                current.response.headers["Content-Type"] = "application/json"
                return output

        ltable = s3db.event_forum
        query = (ltable.event_id == event_id) & \
                (ltable.forum_id == forum_id)
        exists = db(query).select(ltable.id,
                                  limitby=(0, 1)
                                  ).first()
        if not exists:
            ltable.insert(event_id = event_id,
                          forum_id = forum_id,
                          )
            # Update modified_on of the forum to allow subscribers to be notified
            db(s3db.pr_forum.id == forum_id).update(modified_on = r.utcnow)

        output = current.xml.json_message(True, 200, current.T("Event Shared"))
        current.response.headers["Content-Type"] = "application/json"
        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def event_unshare(r, **attr):
        """
            Unshare an Event from a Forum

            S3Method for interactive requests
            - designed to be called via AJAX
        """

        event_id = r.id
        if not event_id or len(r.args) < 3:
            r.error(405, current.ERROR.BAD_METHOD)

        db = current.db
        s3db = current.s3db
        forum_id = r.args[2]

        ltable = s3db.event_forum
        query = (ltable.event_id == event_id) & \
                (ltable.forum_id == forum_id)
        exists = db(query).select(ltable.id,
                                  ltable.created_by,
                                  limitby=(0, 1)
                                  ).first()
        if exists:
            auth = current.auth
            if not auth.s3_has_role("ADMIN"):
                # Check that user is the one that shared the Event
                if exists.created_by != auth.user.id:
                    output = current.xml.json_message(False, 403, current.T("Only the Sharer, or Admin, can Unshare"))
                    current.response.headers["Content-Type"] = "application/json"
                    return output

            resource = s3db.resource("event_forum", id=exists.id)
            resource.delete()

        output = current.xml.json_message(True, 200, current.T("Stopped Sharing Event"))
        current.response.headers["Content-Type"] = "application/json"
        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def event_event_year(row):
        """
            Virtual field for event_event - returns the year of this entry
            used for report.

            Requires "start_date" to be in extra_fields

            @param row: the Row

            @ToDo: Extend this to show multiple years if open for multiple?
        """

        try:
            thisdate = row["event_event.start_date"]
        except AttributeError:
            return current.messages["NONE"]
        if not thisdate:
            return current.messages["NONE"]

        return thisdate.year

    # -------------------------------------------------------------------------
    @staticmethod
    def event_update_onaccept(form):
        """
            When an Event is updated, check for closure
        """

        form_vars = form.vars
        if form_vars.closed:
            event = form_vars.id
            # Ensure this event isn't active in the session
            s3 = current.session.s3
            if s3.event == event:
                s3.event = None

            # @ToDo: Hide the Event from the Map menu
            #gis = current.gis
            #config = gis.get_config()
            #if config == config.config_id:
            #    # Reset to the Default Map
            #    gis.set_config(0)

            # Expire all related Posts
            db = current.db
            ltable = current.s3db.event_post
            table = db.cms_post
            rows = db(ltable.event_id == event).select(ltable.post_id)
            for row in rows:
                db(table.id == row.post_id).update(expired=True)

# =============================================================================
class S3EventLocationModel(S3Model):
    """
        Event Locations model
        - locations for Events
    """

    names = ("event_event_location",
             )

    def model(self):

        #T = current.T

        # ---------------------------------------------------------------------
        # Event Locations (link table)
        #
        tablename = "event_event_location"
        self.define_table(tablename,
                          self.event_event_id(empty = False,
                                              ondelete = "CASCADE",
                                              ),
                          self.gis_location_id(
                            widget = S3LocationSelector(show_map=False),
                            #widget = S3LocationAutocompleteWidget(),
                            requires = IS_LOCATION(),
                            represent = self.gis_LocationRepresent(sep=", "),
                            #comment = S3PopupLink(c = "gis",
                            #                      f = "location",
                            #                      label = T("Create Location"),
                            #                      title = T("Location"),
                            #                      tooltip = AUTOCOMPLETE_HELP,
                            #                      ),
                            ),
                          *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("event_id",
                                                            "location_id",
                                                            ),
                                                 ),
                       )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3EventNameModel(S3Model):
    """
        Event Names model
        - local names for Events
    """

    names = ("event_event_name",
             )

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Local Names
        #
        tablename = "event_event_name"
        self.define_table(tablename,
                          self.event_event_id(empty = False,
                                              ondelete = "CASCADE",
                                              ),
                          s3_language(empty = False),
                          Field("name_l10n",
                                label = T("Local Name"),
                                ),
                          s3_comments(),
                          *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("event_id",
                                                            "language",
                                                            ),
                                                 ),
                       )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3EventTagModel(S3Model):
    """
        Event Tags model
        - tags for Events
    """

    names = ("event_event_tag",
             )

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Event Tags
        # - Key-Value extensions
        # - can be used to identify a Source
        # - can be used to add extra attributes (e.g. Area, Population)
        # - can link Events to other Systems, such as:
        #   * GLIDE (http://glidenumber.net/glide/public/about.jsp)
        #   * OCHA Financial Tracking System, for HXL (http://fts.unocha.org/api/v1/emergency/year/2013.xml)
        #   * Mayon
        #   * WebEOC
        # - can be a Triple Store for Semantic Web support
        #
        tablename = "event_event_tag"
        self.define_table(tablename,
                          self.event_event_id(),
                          # key is a reserved word in MySQL
                          Field("tag",
                                label = T("Key"),
                                ),
                          Field("value",
                                label = T("Value"),
                                ),
                          s3_comments(),
                          *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("event_id",
                                                            "tag",
                                                            ),
                                                 ),
                       )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3IncidentModel(S3Model):
    """
        Incidents
         - the primary unit at which things are managed:
            Scenarios are designed
            Resources are assigned
            Situation Reports are made
    """

    names = ("event_incident",
             "event_incident_id",
             )

    def model(self):

        T = current.T
        db = current.db
        settings = current.deployment_settings
        set_method = self.set_method

        if settings.get_event_cascade_delete_incidents():
            ondelete = "CASCADE"
        else:
            ondelete = "SET NULL"

        # ---------------------------------------------------------------------
        # Incidents
        #
        #  Incidents are the unit at which responses are managed.
        #  They can be Exercises or real Incidents.
        #  They can be instantiated from Scenario Templates.
        #

        level_opts = {1 : T("Level 1"),
                      2 : T("Level 2"),
                      3 : T("Level 3"),
                      4 : T("Level 4"),
                      5 : T("Level 5"),
                      }

        severity_opts = {1 : T("1: Low"),
                         2 : T("2: Medium"),
                         3 : T("3: High"),
                         4 : T("4: Severe"),
                         5 : T("5: Catastrophic"),
                         }

        tablename = "event_incident"
        self.define_table(tablename,
                          self.super_link("doc_id", "doc_entity"),
                          # Enable in template if-required
                          self.event_event_id(ondelete = ondelete,
                                              readable = False,
                                              writable = False,
                                              ),
                          self.event_incident_type_id(),
                          Field("name", notnull=True, # Name could be a code
                                length = 64,
                                label = T("Name"),
                                requires = [IS_NOT_EMPTY(),
                                            IS_LENGTH(64),
                                            ],
                                ),
                          Field("exercise", "boolean",
                                label = T("Exercise?"),
                                represent = lambda opt: "√" if opt else None,
                                #comment = DIV(_class="tooltip",
                                #              _title="%s|%s" % (T("Exercise"),
                                                                 # Should!
                                #                                T("Exercises mean all screens have a watermark & all notifications have a prefix."))),
                                ),
                          s3_datetime(default = "now",
                                      comment = DIV(_class="tooltip",
                                                    _title="%s|%s" % (T("Date"),
                                                                      T("The time at which the Incident started."))),
                                      ),
                          s3_datetime(name = "end_date",
                                      label = T("Closed at"),
                                      comment = DIV(_class="tooltip",
                                                    _title="%s|%s" % (T("Closed at"),
                                                                      T("The time when the Incident was closed."))),
                                      ),
                          Field("closed", "boolean",
                                default = False,
                                label = T("Closed"),
                                represent = s3_yes_no_represent,
                                ),
                          self.gis_location_id(),
                          Field("severity", "integer",
                                label = T("Severity"),
                                requires = IS_EMPTY_OR(
                                            IS_IN_SET(severity_opts)
                                            ),
                                represent = S3Represent(options = severity_opts),
                                # Enable this field in templates if-required
                                readable = False,
                                writable = False,
                                ),
                          Field("level", "integer",
                                label = T("Level"),
                                requires = IS_EMPTY_OR(
                                            IS_IN_SET(level_opts)
                                            ),
                                represent = S3Represent(options = level_opts),
                                # Enable this field in templates if-required
                                readable = False,
                                writable = False,
                                ),
                          self.org_organisation_id(label = T("Lead Organization"), # Lead Responder
                                                   # Enable this field in templates if-required
                                                   readable = False,
                                                   writable = False,
                                                   ),
                          self.pr_person_id(label = T("Incident Commander"),
                                            ),
                          s3_comments(),
                          *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Incident"),
            title_display = T("Incident Details"),
            title_list = T("Incidents"),
            title_update = T("Edit Incident"),
            label_list_button = T("List Incidents"),
            label_delete_button = T("Delete Incident"),
            msg_record_created = T("Incident added"),
            msg_record_modified = T("Incident updated"),
            msg_record_deleted = T("Incident removed"),
            msg_list_empty = T("No Incidents currently registered"))

        # Which levels of Hierarchy are we using?
        levels = current.gis.get_relevant_hierarchy_levels()

        text_fields = ["name",
                       "comments",
                       #"organisation_id$name",
                       #"organisation_id$acronym",
                       "location_id$name",
                       ]

        list_fields = ["date",
                       "name",
                       "incident_type_id",
                       "exercise",
                       "closed",
                       "comments",
                       ]

        report_fields = ["date",
                         "name",
                         "incident_type_id",
                         "exercise",
                         "closed",
                         ]

        for level in levels:
            lfield = "location_id$%s" % level
            report_fields.append(lfield)
            text_fields.append(lfield)
            list_fields.append(lfield)

        filter_widgets = [S3TextFilter(text_fields,
                                       label = T("Search"),
                                       ),
                          S3LocationFilter("location_id",
                                           levels = levels,
                                           label = T("Location"),
                                           ),
                          # @ToDo: Filter for events which are open within a date range
                          #S3DateFilter("date",
                          #             label = None,
                          #             hide_time = True,
                          #             input_labels = {"ge": "From", "le": "To"}
                          #             ),
                          S3OptionsFilter("closed",
                                          label = T("Status"),
                                          options = OrderedDict([(False, T("Open")),
                                                                 (True, T("Closed")),
                                                                 ]),
                                          cols = 2,
                                          default = False,
                                          sort = False,
                                          ),
                          ]

        if settings.get_incident_types_hierarchical():
            filter_widgets.insert(1, S3HierarchyFilter("incident_type_id",
                                                       label = T("Type"),
                                                       ))
        else:
            filter_widgets.insert(1, S3OptionsFilter("incident_type_id",
                                                     label = T("Type"),
                                                     #multiple = False,
                                                     #options = lambda: \
                                                     #  s3_get_filter_opts("event_incident_type",
                                                     #                     translate = True)
                                                     ))

        represent = S3Represent(lookup=tablename)
        incident_id = S3ReusableField("incident_id", "reference %s" % tablename,
                                      label = T("Incident"),
                                      ondelete = "RESTRICT",
                                      represent = represent,
                                      requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "event_incident.id",
                                                              represent,
                                                              filterby="closed",
                                                              filter_opts=(False,),
                                                              orderby="event_incident.name",
                                                              sort=True)),
                                      sortby = "name",
                                      # Uncomment these to use an Autocomplete & not a Dropdown
                                      #widget = S3AutocompleteWidget()
                                      #comment = DIV(_class="tooltip",
                                      #              _title="%s|%s" % (T("Incident"),
                                      #                                current.messages.AUTOCOMPLETE_HELP))
                                      )

        # @ToDo: Move this workflow into Templates?
        # - or useful to have good defaults
        if settings.has_module("project"):
            create_next_url = URL(c="event", f="incident",
                                  args=["[id]", "task"])
        elif settings.has_module("hrm"):
            create_next_url = URL(c="event", f="incident",
                                  args=["[id]", "human_resource"])
        elif settings.has_module("asset"):
            create_next_url = URL(c="event", f="incident",
                                  args=["[id]", "asset"])
        else:
            create_next_url = URL(c="event", f="incident",
                                  args=["[id]", "site"])

        self.configure(tablename,
                       create_next = create_next_url,
                       create_onaccept = self.incident_create_onaccept,
                       deduplicate = S3Duplicate(),
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       list_layout = event_incident_list_layout,
                       # Most recent Incident first
                       orderby = "event_incident.date desc",
                       report_options = Storage(rows = report_fields,
                                                cols = report_fields,
                                                fact = report_fields,
                                                defaults = Storage(
                                                    rows = "location_id$%s" % levels[0],
                                                    cols = "closed",
                                                    fact = (T("Number of Incidents"), "count(name)"),
                                                    totals = True,
                                                    ),
                                                ),
                       super_entity = "doc_entity",
                       update_onaccept = self.incident_update_onaccept,
                       )

        # Components
        self.add_components(tablename,
                            # Should be able to do everything via the link table
                            event_asset = {"name": "incident_asset",
                                           "joinby": "incident_id",
                                           },
                            asset_asset = {"link": "event_asset",
                                           "joinby": "incident_id",
                                           "key": "asset_id",
                                           #"actuate": "embed",
                                           "actuate": "hide",
                                           #"autocomplete": "number",
                                           "autodelete": False,
                                           },
                            cms_post = {"link": "event_post",
                                        "joinby": "incident_id",
                                        "key": "post_id",
                                        "actuate": "replace",
                                        },
                            event_bookmark = "incident_id",
                            event_tag = "incident_id",  # cms_tag
                            event_human_resource = "incident_id",
                            event_incident_log = {"name": "log",
                                                  "joinby": "incident_id",
                                                  },
                            event_incident_report = {"link": "event_incident_report_incident",
                                                     "joinby": "incident_id",
                                                     "key": "incident_report_id",
                                                     "actuate": "replace",
                                                     },
                            # Should be able to do everything via the link table
                            #event_organisation = "incident_id",
                            org_organisation = {"link": "event_organisation",
                                                "joinby": "incident_id",
                                                "key": "organisation_id",
                                                #"actuate": "embed",
                                                "actuate": "hide",
                                                #"autocomplete": "name",
                                                "autodelete": False,
                                                },
                            # Should be able to do everything via the link table
                            #event_team = "incident_id",
                            pr_group = {"link": "event_team",
                                        "joinby": "incident_id",
                                        "key": "group_id",
                                        "actuate": "hide",
                                        "autodelete": False,
                                        },
                            # Should be able to do everything via the link table
                            #event_post = "incident_id",
                            event_site = "incident_id",
                            event_sitrep = "incident_id",
                            event_task = {"name": "incident_task",
                                          "joinby": "incident_id",
                                          },
                            project_task = {"link": "event_task",
                                            "joinby": "incident_id",
                                            "key": "task_id",
                                            "actuate": "replace",
                                            #"autocomplete": "name",
                                            "autodelete": True,
                                            },
                            gis_config = {"link": "event_config",
                                          "joinby": "incident_id",
                                          "multiple": False,
                                          "key": "config_id",
                                          "actuate": "replace",
                                          "autocomplete": "name",
                                          "autodelete": True,
                                          },
                            stats_impact = {"link": "event_event_impact",
                                            "joinby": "incident_id",
                                            "key": "impact_id",
                                            "actuate": "replace",
                                            "autodelete": True,
                                            },
                            )

        # Custom Methods
        set_method("event", "incident",
                   method = "add_bookmark",
                   action = self.incident_add_bookmark)

        set_method("event", "incident",
                   method = "remove_bookmark",
                   action = self.incident_remove_bookmark)

        set_method("event", "incident",
                   method = "add_tag",
                   action = self.incident_add_tag)

        set_method("event", "incident",
                   method = "remove_tag",
                   action = self.incident_remove_tag)

        set_method("event", "incident",
                   method = "share",
                   action = self.incident_share)

        set_method("event", "incident",
                   method = "unshare",
                   action = self.incident_unshare)

        set_method("event", "incident",
                   method = "plan",
                   action = event_ActionPlan)

        set_method("event", "incident",
                   method = "scenario",
                   action = event_ApplyScenario)

        set_method("event", "incident",
                   method = "assign",
                   action = self.pr_AssignMethod(component="human_resource"))

        set_method("event", "incident",
                   method = "event",
                   action = event_EventAssignMethod())

        set_method("event", "incident",
                   method = "dispatch",
                   action = event_notification_dispatcher)

        # Pass names back to global scope (s3.*)
        return {"event_incident_id": incident_id,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """
            Return safe defaults in case the model has been deactivated.
        """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False)

        return {"event_incident_id": lambda **attr: dummy("incident_id"),
                }

    # ---------------------------------------------------------------------
    @staticmethod
    def incident_create_onaccept(form):
        """
            When an Incident is instantiated:
             - populate defaults
             - add Log Entry
        """

        s3db = current.s3db

        form_vars = form.vars
        form_vars_get = form_vars.get
        incident_id = form_vars_get("id")
        person_id = form_vars_get("person_id")

        if person_id:
            # Add the Incident Commander as an event_human_resource
            data = {"incident_id": incident_id,
                    "person_id": person_id,
                    "start_date": form_vars_get("date"),
                    }
            jtable = s3db.hrm_job_title
            job_title = current.db(jtable.name == "Incident Commander").select(jtable.id,
                                                                               limitby = (0, 1)
                                                                               ).first()
            if job_title:
                data["job_title_id"] = job_title.id
            s3db.event_human_resource.insert(**data)

        s3db.event_incident_log.insert(incident_id = incident_id,
                                       name = "Incident Created",
                                       )

        #closed = form_vars_get("closed", False)

        #if incident_id and not closed:
        #    # Set the Incident in the session
        #    current.session.s3.incident = incident_id
        #event = form_vars_get("event_id")
        #if event and not closed:
        #    # Set the Event in the session
        #    current.session.s3.event = event

        #s3db = current.s3db
        #db = current.db
        #ctable = s3db.gis_config
        #mapconfig = None
        #scenario = form_vars_get("scenario_id")
        #if scenario:
        #    # We have been instantiated from a Scenario, so
        #    # copy all resources from the Scenario to the Incident

        #    # Read the source resource tables
        #    table = s3db.event_scenario
        #    otable = s3db.event_scenario_organisation
        #    stable = s3db.event_scenario_site
        #    mtable = s3db.event_scenario_config
        #    query = (table.id == scenario)
        #    squery = query & (stable.scenario_id == table.id)
        #    mquery = query & (mtable.scenario_id == table.id) & \
        #                     (ctable.id == mtable.config_id)
        #    facilities = db(squery).select(stable.site_id)
        #    mapconfig = db(mquery).select(ctable.ALL).first()

        #    # Write them to their respective destination tables
        #    stable = s3db.event_site
        #    for row in facilities:
        #        stable.insert(incident_id=incident_id,
        #                      site_id=row.site_id)

        #    # Modules which can be disabled
        #    htable = s3db.table("event_scenario_human_resource", None)
        #    if htable:
        #        hquery = query & (htable.scenario_id == table.id)
        #        hrms = db(hquery).select(htable.job_title_id)
        #        htable = s3db.event_human_resource
        #        for row in hrms:
        #            htable.insert(incident_id=incident_id,
        #                          job_title_id=row.job_title_id)

        #    atable = s3db.table("event_scenario_asset", None)
        #    if atable:
        #        aquery = query & (atable.scenario_id == table.id)
        #        assets = db(aquery).select(atable.asset_id)
        #        atable = s3db.event_asset
        #        for row in assets:
        #            atable.insert(incident_id=incident_id,
        #                          asset_id=row.asset_id)

        #    ttable = s3db.table("event_scenario_task", None)
        #    if ttable:
        #        tquery = query & (ttable.scenario_id == table.id)
        #        tasks = db(tquery).select(ttable.task_id)
        #        ttable = s3db.event_task
        #        for row in tasks:
        #            ttable.insert(incident_id=incident_id,
        #                          task_id=row.task_id)

        #if mapconfig:
        #    # Incident's Map Config is a copy of the Default / Scenario's
        #    # so that it can be changed within the Incident without
        #    # contaminating the base one
        #    del mapconfig["id"]
        #    del mapconfig["uuid"]
        #    mapconfig["name"] = form_vars.name
        #    config = ctable.insert(**mapconfig.as_dict())
        #    mtable = s3db.event_config
        #    mtable.insert(incident_id = incident_id,
        #                  config_id = config,
        #                  )
        #    # Activate this config
        #    if not closed:
        #        current.gis.set_config(config)
        #    # @ToDo: Add to GIS Menu? Separate Menu?

        #else:
        #    # We have been created without a Scenario or from a Scenario without a Map Config
        #    # Create a new Map Config
        #    config = ctable.insert(name = form_vars.name)
        #    mtable = s3db.event_config
        #    mtable.insert(incident_id=incident_id,
        #                  config_id=config)
        #    # Activate this config
        #    if not closed:
        #        current.gis.set_config(config)
        #    # Viewport can be saved from the Map's toolbar
        #    # @ToDo: Add to GIS Menu? Separate Menu?

    # -------------------------------------------------------------------------
    @staticmethod
    def incident_update_onaccept(form):
        """
            When an Incident is updated
             - set correct event_id for all relevant components
             - check for closure
             - add Log Entry
        """

        db = current.db
        s3db = current.s3db

        form_vars = form.vars
        form_vars_get = form_vars.get
        incident_id = form_vars_get("id")

        person_id = form_vars_get("person_id", False)
        closed = form_vars_get("closed", False)
        event_id = form_vars_get("event_id", False)
        if person_id is False or event_id is False or closed is False:
            # Read the record
            itable = s3db.event_incident
            record = db(itable.id == incident_id).select(itable.closed,
                                                         itable.event_id,
                                                         itable.person_id,
                                                         limitby=(0,1)
                                                         ).first()
            closed = record.closed
            event_id = record.event_id
            person_id = record.person_id

        jtable = s3db.hrm_job_title
        job_title = db(jtable.name == "Incident Commander").select(jtable.id,
                                                                   limitby = (0, 1)
                                                                   ).first()

        if job_title:
            job_title_id = job_title.id
            htable = s3db.event_human_resource
            if person_id:
                # Ensure the Incident Commander is current in event_human_resource
                query = (htable.deleted == False) & \
                        (htable.job_title_id == job_title_id) & \
                        (htable.person_id != None) & \
                        (htable.end_date == None)
                hr = db(query).select(htable.id,
                                      htable.person_id,
                                      limitby=(0, 1)
                                      ).first()
                if hr:
                    if hr.person_id == person_id:
                        # All good :)
                        pass
                    else:
                        now = current.request.utcnow
                        hr.update_record(end_date = now)
                        htable.insert(incident_id = incident_id,
                                      job_title_id = job_title_id,
                                      person_id = person_id,
                                      start_date = now,
                                      )
                else:
                    htable.insert(incident_id = incident_id,
                                  job_title_id = job_title_id,
                                  person_id = person_id,
                                  start_date = current.request.utcnow,
                                  )
            else:
                # Ensure no Incident Commander is current in event_human_resource
                query = (htable.deleted == False) & \
                        (htable.job_title_id == job_title_id) & \
                        (htable.person_id != None) & \
                        (htable.end_date == None)
                hr = db(query).select(htable.id,
                                      limitby=(0, 1)
                                      ).first()
                if hr:
                    hr.update_record(end_date = current.request.utcnow)

        if event_id:
            # Cascade to all relevant components
            for tablename in ("event_asset",
                              "event_human_resource",
                              #"event_resource",
                              #"event_site",
                              #"event_incident_report",
                              "event_event_impact",
                              "event_response",
                              "event_target",
                              "event_organisation",
                              "event_post",
                              "event_request",
                              "event_sitrep",
                              "event_task",
                              "event_team",
                              ):
                table = s3db.table(tablename)
                if table:
                    db(table.incident_id == incident_id).update(event_id = event_id)

        if closed:
            # Ensure this incident isn't active in the session
            #s3 = current.session.s3
            #if s3.incident == incident_id:
            #    s3.incident = None

            # @ToDo: Hide the Incident from the Map menu
            #gis = current.gis
            #config = gis.get_config()
            #if config == config.config_id:
            #    # Reset to the Default Map
            #    gis.set_config(0)

            # Expire all related Posts
            db = current.db
            ltable = current.s3db.event_post
            table = db.cms_post
            rows = db(ltable.incident_id == incident_id).select(ltable.post_id)
            for row in rows:
                db(table.id == row.post_id).update(expired=True)

        # Add Log Entry
        record = form.record
        if record: # Not True for a record merger
            changed = {}
            table = db.event_incident
            for var in form_vars:
                vvar = form_vars[var]
                if isinstance(vvar, Field):
                    # modified_by/modified_on
                    continue
                rvar = record.get(var, "NOT_PRESENT")
                if rvar != "NOT_PRESENT" and vvar != rvar:
                    f = table[var]
                    type_ = f.type
                    if type_ == "integer" or \
                       type_.startswith("reference"):
                        if vvar:
                            vvar = int(vvar)
                        if vvar == rvar:
                            continue
                    represent = table[var].represent
                    if represent:
                        if hasattr(represent, "show_link"):
                            represent.show_link = False
                    else:
                        represent = lambda o: o
                    if rvar:
                        changed[var] = "%s changed from %s to %s" % \
                            (f.label, represent(rvar), represent(vvar))
                    else:
                        changed[var] = "%s changed to %s" % \
                            (f.label, represent(vvar))

            if changed:
                table = s3db.event_incident_log
                text = []
                for var in changed:
                    text.append(changed[var])
                text = "\n".join(text)
                table.insert(incident_id = incident_id,
                             name = "Incident Updated",
                             comments = text,
                             )

    # -----------------------------------------------------------------------------
    @staticmethod
    def incident_add_bookmark(r, **attr):
        """
            Bookmark an Incident

            S3Method for interactive requests
        """

        incident_id = r.id
        user = current.auth.user
        user_id = user and user.id
        if not incident_id or not user_id:
            r.error(405, current.ERROR.BAD_METHOD)

        db = current.db
        s3db = current.s3db
        ltable = s3db.event_bookmark
        query = (ltable.incident_id == incident_id) & \
                (ltable.user_id == user_id)
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
                    data = {"deleted": False}
                db(ltable.id == link_id).update(**data)
        else:
            link_id = ltable.insert(incident_id = incident_id,
                                    user_id = user_id,
                                    )

        output = current.xml.json_message(True, 200, current.T("Bookmark Added"))
        current.response.headers["Content-Type"] = "application/json"
        return output

    # -----------------------------------------------------------------------------
    @staticmethod
    def incident_remove_bookmark(r, **attr):
        """
            Remove a Bookmark for an Incident

            S3Method for interactive requests
        """

        incident_id = r.id
        user = current.auth.user
        user_id = user and user.id
        if not incident_id or not user_id:
            r.error(405, current.ERROR.BAD_METHOD)

        s3db = current.s3db
        ltable = s3db.event_bookmark
        query = (ltable.incident_id == incident_id) & \
                (ltable.user_id == user_id)
        exists = current.db(query).select(ltable.id,
                                          ltable.deleted,
                                          limitby=(0, 1)
                                          ).first()
        if exists and not exists.deleted:
            resource = s3db.resource("event_bookmark", id=exists.id)
            resource.delete()

        output = current.xml.json_message(True, 200, current.T("Bookmark Removed"))
        current.response.headers["Content-Type"] = "application/json"
        return output

    # -----------------------------------------------------------------------------
    @staticmethod
    def incident_add_tag(r, **attr):
        """
            Add a Tag to an Incident

            S3Method for interactive requests
            - designed to be called as an afterTagAdded callback to tag-it.js
        """

        incident_id = r.id
        if not incident_id or len(r.args) < 3:
            r.error(405, current.ERROR.BAD_METHOD)

        tag = r.args[2]
        db = current.db
        s3db = current.s3db
        ttable = s3db.cms_tag
        ltable = s3db.event_tag
        exists = db(ttable.name == tag).select(ttable.id,
                                               ttable.deleted,
                                               ttable.deleted_fk,
                                               limitby=(0, 1)
                                               ).first()
        if exists:
            tag_id = exists.id
            if exists.deleted:
                if exists.deleted_fk:
                    data = json.loads(exists.deleted_fk)
                    data["deleted"] = False
                else:
                    data = {"deleted": False}
                db(ttable.id == tag_id).update(**data)
        else:
            tag_id = ttable.insert(name=tag)
        query = (ltable.tag_id == tag_id) & \
                (ltable.incident_id == incident_id)
        exists = db(query).select(ltable.id,
                                  ltable.deleted,
                                  ltable.deleted_fk,
                                  limitby=(0, 1)
                                  ).first()
        if exists:
            if exists.deleted:
                if exists.deleted_fk:
                    data = json.loads(exists.deleted_fk)
                    data["deleted"] = False
                else:
                    data = {"deleted": False}
                db(ltable.id == exists.id).update(**data)
        else:
            ltable.insert(incident_id = incident_id,
                          tag_id = tag_id,
                          )

        output = current.xml.json_message(True, 200, current.T("Tag Added"))
        current.response.headers["Content-Type"] = "application/json"
        return output

    # -----------------------------------------------------------------------------
    @staticmethod
    def incident_remove_tag(r, **attr):
        """
            Remove a Tag from an Incident

            S3Method for interactive requests
            - designed to be called as an afterTagRemoved callback to tag-it.js
        """

        incident_id = r.id
        if not incident_id or len(r.args) < 3:
            r.error(405, current.ERROR.BAD_METHOD)

        tag = r.args[2]
        db = current.db
        s3db = current.s3db
        ttable = s3db.cms_tag
        exists = db(ttable.name == tag).select(ttable.id,
                                               ttable.deleted,
                                               limitby=(0, 1)
                                               ).first()
        if exists:
            tag_id = exists.id
            ltable = s3db.event_tag
            query = (ltable.tag_id == tag_id) & \
                    (ltable.incident_id == incident_id)
            exists = db(query).select(ltable.id,
                                      ltable.deleted,
                                      limitby=(0, 1)
                                      ).first()
            if exists and not exists.deleted:
                resource = s3db.resource("event_tag", id=exists.id)
                resource.delete()

        output = current.xml.json_message(True, 200, current.T("Tag Removed"))
        current.response.headers["Content-Type"] = "application/json"
        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def incident_share(r, **attr):
        """
            Share an Incident to a Forum

            S3Method for interactive requests
            - designed to be called via AJAX
        """

        incident_id = r.id
        if not incident_id or len(r.args) < 3:
            r.error(405, current.ERROR.BAD_METHOD)

        db = current.db
        s3db = current.s3db
        auth = current.auth
        forum_id = r.args[2]

        if not auth.s3_has_role("ADMIN"):
            # Check that user is a member of the forum
            mtable = s3db.pr_forum_membership
            ptable = s3db.pr_person
            query = (ptable.pe_id == auth.user.pe_id) & \
                    (mtable.person_id == ptable.id)
            member = db(query).select(mtable.id,
                                      limitby = (0, 1)
                                      ).first()
            if not member:
                output = current.xml.json_message(False, 403, current.T("Cannot Share to a Forum unless you are a Member"))
                current.response.headers["Content-Type"] = "application/json"
                return output

        ltable = s3db.event_forum
        query = (ltable.incident_id == incident_id) & \
                (ltable.forum_id == forum_id)
        exists = db(query).select(ltable.id,
                                  limitby=(0, 1)
                                  ).first()
        if not exists:
            ltable.insert(incident_id = incident_id,
                          forum_id = forum_id,
                          )
            # Update modified_on of the forum to allow subscribers to be notified
            db(s3db.pr_forum.id == forum_id).update(modified_on = r.utcnow)

        output = current.xml.json_message(True, 200, current.T("Incident Shared"))
        current.response.headers["Content-Type"] = "application/json"
        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def incident_unshare(r, **attr):
        """
            Unshare an Incident from a Forum

            S3Method for interactive requests
            - designed to be called via AJAX
        """

        incident_id = r.id
        if not incident_id or len(r.args) < 3:
            r.error(405, current.ERROR.BAD_METHOD)

        db = current.db
        s3db = current.s3db
        forum_id = r.args[2]

        ltable = s3db.event_forum
        query = (ltable.incident_id == incident_id) & \
                (ltable.forum_id == forum_id)
        exists = db(query).select(ltable.id,
                                  ltable.created_by,
                                  limitby=(0, 1)
                                  ).first()
        if exists:
            auth = current.auth
            if not auth.s3_has_role("ADMIN"):
                # Check that user is the one that shared the Incident
                if exists.created_by != auth.user.id:
                    output = current.xml.json_message(False, 403, current.T("Only the Sharer, or Admin, can Unshare"))
                    current.response.headers["Content-Type"] = "application/json"
                    return output

            resource = s3db.resource("event_forum", id=exists.id)
            resource.delete()

        output = current.xml.json_message(True, 200, current.T("Stopped Sharing Incident"))
        current.response.headers["Content-Type"] = "application/json"
        return output

# =============================================================================
class S3IncidentReportModel(S3Model):
    """
        Incident Reports
         - reports about incidents
         - useful for busy call centres which may receive many reports about a
           single incident and may receive calls which need logging but don't
           get responded to as an Incident (e.g. Out of Scope)

        @ToDo: Deprecate IRS module by porting functionality here
    """

    names = ("event_incident_report",
             "event_incident_report_incident",
             )

    def model(self):

        T = current.T

        #settings = current.deployment_settings
        #if settings.get_event_cascade_delete_incidents():
        #    ondelete = "CASCADE"
        #else:
        #    ondelete = "SET NULL"

        define_table = self.define_table

        # ---------------------------------------------------------------------
        # Incident Reports
        #
        tablename = "event_incident_report"
        define_table(tablename,
                     self.super_link("doc_id", "doc_entity"),
                     # Use link table(s)
                     #self.event_event_id(ondelete = ondelete),
                     #self.event_incident_id(ondelete = "CASCADE"),
                     s3_datetime(default="now"),
                     Field("name", notnull=True,
                           label = T("Short Description"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     self.event_incident_type_id(),
                     #self.pr_person_id(label = T("Reported By"),
                     #                  ),
                     Field("reported_by",
                           label = T("Reported By"),
                           ),
                     Field("contact",
                           label = T("Contact"),
                           ),
                     self.gis_location_id(),
                     Field("contact",
                           label = T("Contact"),
                           ),
                     Field("description", "text",
                           label = T("Long Description"),
                           widget = s3_comments_widget,
                           ),
                     Field("needs", "text",
                           label = T("Immediate Needs"),
                           widget = s3_comments_widget,
                           ),
                     Field("closed", "boolean",
                           default = False,
                           label = T("Closed"),
                           represent = s3_yes_no_represent,
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Incident Report"),
            title_display = T("Incident Report Details"),
            title_list = T("Incident Reports"),
            title_update = T("Edit Incident Report"),
            label_list_button = T("List Incident Reports"),
            #label_delete_button = T("Remove Incident Report from this event"),
            label_delete_button = T("Delete Incident"),
            msg_record_created = T("Incident Report added"),
            msg_record_modified = T("Incident Report updated"),
            msg_record_deleted = T("Incident Report removed"),
            #msg_list_empty = T("No Incident Reports currently registered for this event"),
            msg_list_empty = T("No Incident Reports currently registered"),
            )

        # Which levels of Hierarchy are we using?
        levels = current.gis.get_relevant_hierarchy_levels()

        report_fields = ["name",
                         "incident_type_id",
                         "closed",
                         ]

        text_fields = ["name",
                       "description",
                       "needs",
                       "comments",
                       "location_id$name",
                       ]

        list_fields = ["name",
                       "date",
                       "incident_type_id",
                       "closed",
                       ]

        for level in levels:
            lfield = "location_id$%s" % level
            report_fields.append(lfield)
            text_fields.append(lfield)
            list_fields.append(lfield)

        filter_widgets = [S3TextFilter(text_fields,
                                       label = T("Search"),
                                       ),
                          S3LocationFilter("location_id",
                                           levels = levels,
                                           ),
                          S3OptionsFilter("closed",
                                          label = T("Status"),
                                          options = OrderedDict([(False, T("Open")),
                                                                 (True, T("Closed")),
                                                                 ]),
                                          cols = 2,
                                          default = False,
                                          sort = False,
                                          ),
                          ]

        if current.deployment_settings.get_incident_types_hierarchical():
            filter_widgets.insert(1, S3HierarchyFilter("incident_type_id",
                                                       label = T("Type"),
                                                       ))
        else:
            filter_widgets.insert(1, S3OptionsFilter("incident_type_id",
                                                     label = T("Type"),
                                                     #multiple = False,
                                                     #options = lambda: \
                                                     #  s3_get_filter_opts("event_incident_type",
                                                     #                     translate = True)
                                                     ))

        self.configure(tablename,
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       report_options = Storage(
                        rows=report_fields,
                        cols=report_fields,
                        fact=report_fields,
                        defaults=Storage(rows = "location_id$L1", #lfield, # Lowest-level of hierarchy
                                         cols = "incident_type_id",
                                         fact = "count(name)",
                                         totals = True)
                        ),
                       super_entity = "doc_entity",
                       )

        # Custom Methods
        self.set_method("event", "incident_report",
                        method = "assign",
                        action = event_IncidentAssignMethod(component = "incident_report_incident",
                                                            next_tab = "incident_report"))

        # Components
        self.add_components(tablename,
                            # Incidents
                            event_incident = {"link": "event_incident_report_incident",
                                              "joinby": "incident_report_id",
                                              "key": "incident_id",
                                              "actuate": "hide",
                                              },
                            # Format for event_IncidentAssignMethod
                            event_incident_report_incident = "incident_report_id",
                            # Coalitions
                            org_group = {"link": "event_incident_report_group",
                                         "joinby": "incident_report_id",
                                         "key": "group_id",
                                         "actuate": "hide",
                                         },
                            # Format for InlineComponent/filter_widget
                            event_incident_report_group = "incident_report_id",
                            )

        # ---------------------------------------------------------------------
        # Incident Reports <> Incidents link table
        #
        tablename = "event_incident_report_incident"
        define_table(tablename,
                     Field("incident_report_id", "reference event_incident_report",
                           ondelete = "CASCADE",
                           ),
                     self.event_incident_id(empty = False,
                                            ondelete = "CASCADE",
                                            ),
                     *s3_meta_fields())

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3EventActivityModel(S3Model):
    """
        Link Project Activities to Events
    """

    names = ("event_activity",
             )

    def model(self):

        #if current.deployment_settings.get_event_cascade_delete_incidents():
        #    ondelete = "CASCADE"
        #else:
        #    ondelete = "SET NULL"

        tablename = "event_activity"
        self.define_table(tablename,
                          self.event_event_id(empty = False,
                                              ondelete = "CASCADE",
                                              ),
                          #self.event_incident_id(ondelete = "CASCADE"),
                          self.project_activity_id(#ondelete = "CASCADE", # default anyway
                                                   ),
                          *s3_meta_fields())

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3EventRequestModel(S3Model):
    """
        Link Requests to Incidents &/or Events
    """

    names = ("event_request",
             )

    def model(self):

        if current.deployment_settings.get_event_cascade_delete_incidents():
            ondelete = "CASCADE"
        else:
            ondelete = "SET NULL"

        tablename = "event_request"
        self.define_table(tablename,
                          self.event_event_id(default = current.session.s3.event,
                                              ondelete = ondelete,
                                              ),
                          self.event_incident_id(ondelete = "CASCADE"),
                          self.req_req_id(#ondelete = "CASCADE", # default anyway
                                          ),
                          *s3_meta_fields())

        self.configure(tablename,
                       onaccept = lambda form: \
                        set_event_from_incident(form, "event_request"),
                       )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3EventResourceModel(S3Model):
    """
        Resources Assigned to Events/Incidents
        - depends on Stats module

        Whilst there is a Quantity option, this is envisaged to usually be 1
        - these are typically named, trackable resources

        @UsedBy: MCOP (but not WACOP)

        @ToDo: Optional link to org_resource to e.g. mark resources as assigned
    """

    names = ("event_resource",)

    def model(self):

        if not current.deployment_settings.has_module("stats"):
            current.log.warning("Event Resource Model needs Stats module enabling")
            return {}

        T = current.T
        super_link = self.super_link

        status_opts = {1: T("Available"),
                       2: T("Assigned"),
                       3: T("En Route"),
                       }

        #if current.deployment_settings.get_event_cascade_delete_incidents():
        #    ondelete = "CASCADE"
        #else:
        #    ondelete = "SET NULL"

        # ---------------------------------------------------------------------
        # Resources
        #
        tablename = "event_resource"
        self.define_table(tablename,
                          # Instance
                          super_link("data_id", "stats_data"),
                          super_link("track_id", "sit_trackable"),
                          # Resources are normally managed at the Incident level
                          #self.event_event_id(ondelete = ondelete,
                          #                    # enable in template if-required
                          #                    readable = False,
                          #                    writable = False,
                          #                    ),
                          self.event_incident_id(ondelete = "CASCADE"),
                          # This is a component, so needs to be a super_link
                          # - can't override field name, ondelete or requires
                          super_link("parameter_id", "stats_parameter",
                                     empty = False,
                                     instance_types = ("org_resource_type",),
                                     label = T("Resource Type"),
                                     represent = S3Represent(lookup="stats_parameter",
                                                             translate=True),
                                     readable = True,
                                     writable = True,
                                     comment = S3PopupLink(c = "org",
                                                           f = "resource_type",
                                                           vars = {"child": "parameter_id"},
                                                           title = T("Create Resource Type"),
                                                           ),
                                     ),
                          Field("status", "integer",
                                label = T("Status"),
                                represent = lambda opt: \
                                    status_opts.get(opt) or current.messages.UNKNOWN_OPT,
                                requires = IS_IN_SET(status_opts),
                                ),
                          Field("name",
                                label = T("Name"),
                                ),
                          Field("value", "integer",
                                default = 1,
                                label = T("Quantity"),
                                requires = IS_INT_IN_RANGE(0, None),
                                ),
                          self.org_organisation_id(),
                          self.pr_person_id(label = T("Contact")),
                          # @ToDo: Make use of S3Track:
                          # Base Location: Enable field only in Create form
                          self.gis_location_id(#readable = False,
                                               #writable = False,
                                               ),
                          #Field.Method("location", lambda row: self.sit_location(row, tablename)),
                          # @ToDo: Deprecate once we start using S3Track
                          s3_datetime(default = "now"),
                          s3_comments(),
                          *s3_meta_fields())

        # CRUD strings
        current.response.s3.crud_strings[tablename] = Storage(
            label_create=T("Add Resource"),
            title_display=T("Resource Details"),
            title_list=T("Resources"),
            title_update=T("Edit Resource"),
            title_map=T("Map of Resources"),
            title_upload=T("Import Resources"),
            label_list_button=T("List Resources"),
            label_delete_button=T("Delete Resource"),
            msg_record_created=T("Resource added"),
            msg_record_modified=T("Resource updated"),
            msg_record_deleted=T("Resource deleted"),
            msg_list_empty=T("No Resources assigned to Incident"))

        # Custom Methods
        #self.set_method("event", "resource",
        #                method = "check-in",
        #                action = S3CheckInMethod())

        # List Fields
        #list_fields = ["id",
        #               "incident_id",
        #               "parameter_id",
        #               "status",
        #               "name",
        #               "value",
        #               "organisation_id",
        #               "person_id",
        #               "location_id",
        #               #(T("Location"), "location"),
        #               "comments",
        #               ]

        # Filter Widgets
        filter_widgets = [S3TextFilter(["organisation_id$name",
                                        "location_id",
                                        "parameter_id$name",
                                        "comments",
                                        ],
                                       label = T("Search"),
                                       ),
                          S3OptionsFilter("parameter_id",
                                          label = T("Type"),
                                          ),
                          ]

        # Report options
        report_fields = ["incident_id",
                         "organisation_id",
                         "parameter_id",
                         ]

        report_options = Storage(rows = report_fields,
                                 cols = report_fields,
                                 fact = [(T("Total Number of Resources"), "sum(value)"),
                                         (T("Number of Resources"), "count(value)"),
                                         ],
                                 defaults = Storage(rows = "incident_id",
                                                    cols = "parameter_id",
                                                    fact = "sum(value)",
                                                    totals = True,
                                                    chart = "barchart:rows",
                                                    #table = "collapse",
                                                    )
                                 )

        self.configure(tablename,
                       context = {#"event": "event_id",
                                  "incident": "incident_id",
                                  "location": "location_id",
                                  "organisation": "organisation_id",
                                  },
                       filter_widgets = filter_widgets,
                       #list_fields = list_fields,
                       list_layout = event_resource_list_layout,
                       #onaccept = lambda form: \
                       # set_event_from_incident(form, "event_resource"),
                       orderby = "event_resource.date desc",
                       report_options = report_options,
                       super_entity = ("stats_data", "sit_trackable"),
                       )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3IncidentReportOrganisationGroupModel(S3Model):
    """
        Links between Incident Reports & Organisation Groups
    """

    names = ("event_incident_report_group",
             )

    def model(self):

        represent = S3Represent(lookup="event_incident_report")

        # ---------------------------------------------------------------------
        # Incident Reports <> Coalitions link table
        #
        tablename = "event_incident_report_group"
        self.define_table(tablename,
                          Field("incident_report_id", self.event_incident_report,
                                represent = represent,
                                requires = IS_ONE_OF(current.db, "event_incident_report.id",
                                                     represent,
                                                     sort=True,
                                                     ),
                                ),
                          self.org_group_id(empty=False),
                          *s3_meta_fields())

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3IncidentLogModel(S3Model):
    """
        Incident Logs
            - record of all changes
            - manual updates with ability to notify 
    """

    names = ("event_incident_log",
             )

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Incident Logs
        #
        tablename = "event_incident_log"
        self.define_table(tablename,
                          self.event_incident_id(),
                          Field("name", notnull=True,
                                label = T("Name"),
                                ),
                          self.super_link("pe_id", "pr_pentity",
                                          label = T("Notify"),
                                          filterby = "instance_type",
                                          filter_opts = ("pr_person",),
                                          represent = self.pr_PersonEntityRepresent(show_label = False,
                                                                                    show_type = False),
                                          readable = True,
                                          writable = True,
                                          ),
                          s3_comments(),
                          *s3_meta_fields(),
                          on_define = lambda table: \
                            [table.created_by.set_attributes(represent = s3_auth_user_represent_name),
                             table.created_on.set_attributes(represent = S3DateTime.datetime_represent),
                             ]
                          )

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Log Entry"),
            title_display = T("Log Entry Details"),
            title_list = T("Log Entries"),
            #title_update = T("Edit Log Entry"),
            #title_upload = T("Import Log Entries"),
            label_list_button = T("List Log Entries"),
            #label_delete_button = T("Delete Log Entry"),
            msg_record_created = T("Log Entry added"),
            #msg_record_modified = T("Log Entry updated"),
            #msg_record_deleted = T("Log Entry removed"),
            msg_list_empty = T("No Log Entries currently registered")
            )

        self.configure(tablename,
                       create_onaccept = self.event_incident_log_create_onaccept,
                       deletable = False,
                       editable = False,
                       list_fields = [(T("Date"), "created_on"),
                                      (T("Organization"), "created_by$organisation_id"),
                                      (T("By"), "created_by"),
                                      "name",
                                      "comments",
                                      ],
                       )

        # Pass names back to global scope (s3.*)
        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def event_incident_log_create_onaccept(form):
        """
            Send notification
        """

        # Notify Assignee
        form_vars = form.vars

        pe_id = form_vars.pe_id
        if not pe_id:
            # Not assigned to anyone
            return

        settings = current.deployment_settings

        if settings.has_module("msg"):
            # Notify assignee
            subject = "%s: Incident Log Notification" % settings.get_system_name_short()
            url = "%s%s" % (settings.get_base_public_url(),
                            URL(c="event", f="incident", args=[form_vars.incident_id, "log", form_vars.id]))

            message = "You have been notified of a new Log entry:\n\n%s\n\n%s\n\n%s" % \
                            (url,
                             form_vars.name,
                             form_vars.comments or "")

            current.msg.send_by_pe_id(pe_id, subject, message, contact_method="SMS")

# =============================================================================
class S3IncidentTypeModel(S3Model):
    """
        Incident Types
    """

    names = ("event_incident_type",
             "event_incident_type_id",
             )

    def model(self):

        T = current.T
        db = current.db

        hierarchical_incident_types = \
            current.deployment_settings.get_incident_types_hierarchical()

        # ---------------------------------------------------------------------
        # Incident Types
        #
        tablename = "event_incident_type"
        self.define_table(tablename,
                          Field("name", notnull=True, length=64,
                                label = T("Name"),
                                requires = [IS_NOT_EMPTY(),
                                            IS_LENGTH(64),
                                            ],
                                ),
                          Field("parent", "reference event_incident_type", # This form of hierarchy may not work on all Databases
                                label = T("SubType of"),
                                ondelete = "RESTRICT",
                                readable = hierarchical_incident_types,
                                writable = hierarchical_incident_types,
                                ),
                          s3_comments(),
                          *s3_meta_fields())

        type_represent = S3Represent(lookup=tablename, translate=True)

        if hierarchical_incident_types:
            hierarchy = "parent"
            # Can't be defined in-line as otherwise get a circular reference
            table = db[tablename]
            table.parent.represent = type_represent
            table.parent.requires = IS_EMPTY_OR(
                                        IS_ONE_OF(db, "event_incident_type.id",
                                                  type_represent,
                                                  # If limiting to just 1 level of parent
                                                  #filterby="parent",
                                                  #filter_opts=(None,),
                                                  orderby="event_incident_type.name"))
            incident_type_widget = S3HierarchyWidget(lookup = "event_incident_type",
                                                     represent = type_represent,
                                                     multiple = False,
                                                     leafonly = True,
                                                     )
            incident_type_comment = None
        else:
            hierarchy = None
            incident_type_widget = None
            incident_type_comment = None
            # Uncomment these to use an Autocomplete & not a Dropdown
            #incident_type_widget = S3AutocompleteWidget()
            #incident_type_comment = DIV(_class="tooltip",
            #                             _title="%s|%s" % (T("Event Type"),
            #                                               AUTOCOMPLETE_HELP))

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Incident Type"),
            title_display = T("Incident Type Details"),
            title_list = T("Incident Types"),
            title_update = T("Edit Incident Type"),
            title_upload = T("Import Incident Types"),
            label_list_button = T("List Incident Types"),
            label_delete_button = T("Remove Incident Type from this event"),
            msg_record_created = T("Incident Type added"),
            msg_record_modified = T("Incident Type updated"),
            msg_record_deleted = T("Incident Type removed"),
            #msg_list_empty = T("No Incident Types currently registered in this event")
            msg_list_empty = T("No Incident Types currently registered")
            )

        incident_type_id = S3ReusableField("incident_type_id", "reference %s" % tablename,
                                           label = T("Incident Type"),
                                           ondelete = "RESTRICT",
                                           represent = type_represent,
                                           requires = IS_EMPTY_OR(
                                                        IS_ONE_OF(db, "event_incident_type.id",
                                                                  type_represent,
                                                                  orderby="event_incident_type.name",
                                                                  sort=True)),
                                           sortby = "name",
                                           widget = incident_type_widget,
                                           comment = incident_type_comment,
                                           )
        self.configure(tablename,
                       deduplicate = S3Duplicate(),
                       hierarchy = hierarchy,
                       )

        # Pass names back to global scope (s3.*)
        return {"event_incident_type_id": incident_type_id,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """
            Return safe defaults in case the model has been deactivated.
        """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False)

        return {"event_incident_type_id": lambda **attr: dummy("incident_type_id"),
                }

# =============================================================================
class S3IncidentTypeTagModel(S3Model):
    """
        Incident Type Tags
         - Key-Value extensions
         - can be used to provide conversions to external systems, such as:
           * CAP
           * NIMS
         - can be a Triple Store for Semantic Web support
    """

    names = ("event_incident_type_tag",)

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Incident Type Tags
        #
        tablename = "event_incident_type_tag"
        self.define_table(tablename,
                          self.event_incident_type_id(),
                          # key is a reserved word in MySQL
                          Field("tag", label=T("Key")),
                          Field("value", label=T("Value")),
                          s3_comments(),
                          *s3_meta_fields())

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3EventAlertModel(S3Model):
    """
        Alerts for Events/Incidents

        @ToDo: Optional links to CAP broker & Messaging
               Push: like deploy_alert? via deploy_alert?
               Pull: Subscription/Notification
    """

    names = ("event_alert",
             )

    def model(self):

        T = current.T
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        #if current.deployment_settings.get_event_cascade_delete_incidents():
        #    ondelete = "CASCADE"
        #else:
        #    ondelete = "SET NULL"

        tablename = "event_alert"
        define_table(tablename,
                     # PE representing its Recipients
                     self.super_link("pe_id", "pr_pentity"),
                     self.event_event_id(ondelete = "CASCADE"),
                     #self.event_incident_id(ondelete = "CASCADE"),
                     Field("name",
                           comment = T("This isn't visible to the recipients"),
                           label = T("Name"),
                           ),
                     Field("subject", length=78,    # RFC 2822
                           comment = T("The subject of the alert (optional)"),
                           label = T("Subject"),
                           requires = IS_LENGTH(78),
                           ),
                     Field("body", "text",
                           label = T("Message"),
                           requires = IS_NOT_EMPTY(),
                           represent = lambda v: v or current.messages["NONE"],
                           ),
                     # Link to the Message once sent
                     self.msg_message_id(readable = False),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Alert"),
            title_display = T("Alert Details"),
            title_list = T("Alerts"),
            title_update = T("Edit Alert Details"),
            title_upload = T("Import Recipients"),
            label_list_button = T("List Alerts"),
            label_delete_button = T("Delete Alert"),
            msg_record_created = T("Alert added"),
            msg_record_modified = T("Alert Details updated"),
            msg_record_deleted = T("Alert deleted"),
            msg_list_empty = T("No Alerts currently defined"))

        # Custom method to send alerts
        #self.set_method("event", "alert",
        #                method = "send",
        #                action = self.event_alert_send)

        # Reusable field
        represent = S3Represent(lookup=tablename)
        alert_id = S3ReusableField("alert_id", "reference %s" % tablename,
                                   label = T("Alert"),
                                   ondelete = "CASCADE",
                                   represent = represent,
                                   requires = IS_ONE_OF(db, "event_alert.id",
                                                        represent),
                                   )

        # ---------------------------------------------------------------------
        # Recipients of the Alert
        #
        tablename = "event_alert_recipient"
        define_table(tablename,
                     alert_id(),
                     self.pr_person_id(empty = False,
                                       label = T("Recipient")),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Recipient"),
            title_display = T("Recipient Details"),
            title_list = T("Recipients"),
            title_update = T("Edit Recipient Details"),
            title_upload = T("Import Recipients"),
            label_list_button = T("List Recipients"),
            label_delete_button = T("Delete Recipient"),
            msg_record_created = T("Recipient added"),
            msg_record_modified = T("Recipient Details updated"),
            msg_record_deleted = T("Recipient removed"),
            msg_list_empty = T("No Recipients currently defined"))

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3EventAssetModel(S3Model):
    """
        Link Assets to Incidents
    """

    names = ("event_asset",
             )

    def model(self):

        settings = current.deployment_settings
        if not settings.has_module("supply"):
            # Don't crash
            #return self.defaults()
            return {}

        T = current.T

        # SAFIRE\SC
        status_opts = {1: T("Requested"),
                       2: T("Reserved"),
                       3: T("Checked out"),
                       4: T("Returned"),
                       }

        if settings.get_event_cascade_delete_incidents():
            ondelete = "CASCADE"
        else:
            ondelete = "SET NULL"

        # ---------------------------------------------------------------------
        # Assets

        # @ToDo: make this lookup Lazy (also in asset.py)
        ctable = self.supply_item_category
        itable = self.supply_item
        supply_item_represent = self.supply_item_represent
        asset_items_set = current.db((ctable.can_be_asset == True) & \
                                     (itable.item_category_id == ctable.id))

        tablename = "event_asset"
        self.define_table(tablename,
                          # Instance table
                          self.super_link("cost_item_id", "budget_cost_item"),
                          self.event_event_id(ondelete = ondelete),
                          self.event_incident_id(empty = False,
                                                 ondelete = "CASCADE"),
                          # Mandatory: Define the Item Type
                          self.supply_item_id(represent = supply_item_represent,
                                              requires = IS_ONE_OF(asset_items_set,
                                                                   "supply_item.id",
                                                                   supply_item_represent,
                                                                   sort = True,
                                                                   ),
                                              script = None, # No Item Pack Filter
                                              widget = None,
                                              comment = S3PopupLink(c = "supply",
                                                                    f = "item",
                                                                    # No special controller so need this for an options lookup
                                                                    vars = {"prefix": "asset",
                                                                            "parent": "asset",
                                                                            },
                                                                    label = T("Create Item Type"),
                                                                    title = T("Item"),
                                                                    #tooltip = supply_item_tooltip,
                                                                    ),
                                              ),
                          # Optional: Assign specific Asset
                          # @ToDo: Filter widget based on Type
                          self.asset_asset_id(ondelete = "RESTRICT",
                                              ),
                          Field("status", "integer",
                                label = T("Status"),
                                represent = lambda opt: \
                                    status_opts.get(opt) or current.messages.UNKNOWN_OPT,
                                requires = IS_EMPTY_OR(
                                            IS_IN_SET(status_opts),
                                            ),
                                ),
                          s3_datetime("start_date",
                                      label = T("Start Date"),
                                      widget = "date",
                                      ),
                          s3_datetime("end_date",
                                      label = T("End Date"),
                                      # Not supported by s3_datetime
                                      #start_field = "event_asset_start_date",
                                      #default_interval = 12,
                                      widget = "date",
                                      ),
                          s3_comments(),

                          *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Asset"),
            title_display = T("Asset Details"),
            title_list = T("Assets"),
            title_update = T("Edit Asset"),
            label_list_button = T("List Assets"),
            label_delete_button = T("Remove Asset from this incident"),
            msg_record_created = T("Asset added"),
            msg_record_modified = T("Asset updated"),
            msg_record_deleted = T("Asset removed"),
            msg_list_empty = T("No Assets currently registered for this incident"))

        if current.deployment_settings.has_module("budget"):
            crud_form = S3SQLCustomForm("incident_id",
                                        "item_id",
                                        "asset_id",
                                        S3SQLInlineComponent("allocation",
                                                             label = T("Budget"),
                                                             fields = ["budget_entity_id",
                                                                       "start_date",
                                                                       "end_date",
                                                                       "daily_cost",
                                                                       ],
                                                             ),
                                        )
        else:
            crud_form = None

        self.configure(tablename,
                       context = {"incident": "incident_id",
                                  },
                       create_onaccept = self.event_asset_onaccept,
                       crud_form = crud_form,
                       deduplicate = S3Duplicate(primary = ("incident_id",
                                                            "item_id",
                                                            "asset_id",
                                                            ),
                                                 ),
                       list_fields = ["incident_id",
                                      "item_id",
                                      "asset_id",
                                      "allocation.budget_entity_id",
                                      "allocation.start_date",
                                      "allocation.end_date",
                                      "allocation.daily_cost",
                                      ],
                       update_onaccept = lambda form:
                                            self.event_asset_onaccept(form, create=False),
                       super_entity = "budget_cost_item",
                       )

        # Pass names back to global scope (s3.*)
        return {}

    # ---------------------------------------------------------------------
    @staticmethod
    def event_asset_onaccept(form, create=True):
        """
            When an Asset is assigned to an Incident:
             - set_event_from_incident
             - add Log Entry
        """

        set_event_from_incident(form, "event_asset")

        s3db = current.s3db
        table = s3db.event_asset

        form_vars = form.vars
        form_vars_get = form_vars.get
        incident_id = form_vars_get("incident_id")
        if not incident_id:
            link = current.db(table.id == form_vars_get("id")).select(table.incident_id,
                                                                      limitby = (0, 1)
                                                                      ).first()
            incident_id = link.incident_id

        if create:
            item_id = form_vars_get("item_id")
            if item_id:
                s3db.event_incident_log.insert(incident_id = incident_id,
                                               name = "Item Requested",
                                               comments = s3db.event_asset.item_id.represent(item_id),
                                               )
            return

        # Update
        record = form.record
        if record: # Not True for a record merger
            changed = {}
            for var in form_vars:
                vvar = form_vars[var]
                if isinstance(vvar, Field):
                    # modified_by/modified_on
                    continue
                rvar = record.get(var, "NOT_PRESENT")
                if rvar != "NOT_PRESENT" and vvar != rvar:
                    f = table[var]
                    type_ = f.type
                    if type_ == "integer" or \
                       type_.startswith("reference"):
                        if vvar:
                            vvar = int(vvar)
                        if vvar == rvar:
                            continue
                    represent = table[var].represent
                    if represent:
                        if hasattr(represent, "show_link"):
                            represent.show_link = False
                    else:
                        represent = lambda o: o
                    if rvar:
                        changed[var] = "%s changed from %s to %s" % \
                            (f.label, represent(rvar), represent(vvar))
                    else:
                        changed[var] = "%s changed to %s" % \
                            (f.label, represent(vvar))

            if changed:
                table = s3db.event_incident_log
                text = []
                for var in changed:
                    text.append(changed[var])
                text = "\n".join(text)
                table.insert(incident_id = incident_id,
                             #name = "Item Assigned",
                             name = "Item Request Updated",
                             comments = text,
                             )

# =============================================================================
class S3EventBookmarkModel(S3Model):
    """
        Bookmarks for Events &/or Incidents
        - the Incident bookmarks do NOT populate the Event's
    """

    names = ("event_bookmark",
             )

    def model(self):

        #T = current.T
        auth = current.auth

        # ---------------------------------------------------------------------
        # Bookmarks: Link table between Users & Events/Incidents
        tablename = "event_bookmark"
        self.define_table(tablename,
                          self.event_event_id(ondelete = "CASCADE"),
                          self.event_incident_id(ondelete = "CASCADE"),
                          Field("user_id", auth.settings.table_user,
                                default = auth.user.id if auth.user else None,
                                ),
                          *s3_meta_fields())

        #current.response.s3.crud_strings[tablename] = Storage(
        #    label_create = T("Bookmark Incident"), # or Event
        #    title_display = T("Bookmark Details"),
        #    title_list = T("Bookmarks"),
        #    title_update = T("Edit Bookmark"),
        #    label_list_button = T("List Bookmarks"),
        #    label_delete_button = T("Remove Bookmark for this Incident"),
        #    msg_record_created = T("Bookmark added"),
        #    msg_record_modified = T("Bookmark updated"),
        #    msg_record_deleted = T("Bookmark removed"),
        #    msg_list_empty = T("No Incidents currently bookmarked"))

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3EventCMSModel(S3Model):
    """
        Link CMS Posts to Events &/or Incidents
    """

    names = ("event_post",
             "event_post_incident_type",
             )

    def model(self):

        #T = current.T

        define_table = self.define_table

        post_id = self.cms_post_id

        if current.deployment_settings.get_event_cascade_delete_incidents():
            ondelete = "CASCADE"
        else:
            ondelete = "SET NULL"

        # ---------------------------------------------------------------------
        # Link table between Posts & Events/Incidents
        tablename = "event_post"
        define_table(tablename,
                     self.event_event_id(ondelete = ondelete),
                     self.event_incident_id(ondelete = "CASCADE"),
                     post_id(empty = False,
                             ondelete = "CASCADE",
                             ),
                     *s3_meta_fields())

        #current.response.s3.crud_strings[tablename] = Storage(
        #    label_create = T("Tag Post"),
        #    title_display = T("Tag Details"),
        #    title_list = T("Tags"),
        #    title_update = T("Edit Tag"),
        #    label_list_button = T("List Tags"),
        #    label_delete_button = T("Remove Tag for this Event from this Post"),
        #    msg_record_created = T("Tag added"),
        #    msg_record_modified = T("Tag updated"),
        #    msg_record_deleted = T("Tag removed"),
        #    msg_list_empty = T("No Posts currently tagged to this event"))

        self.configure(tablename,
                       onaccept = lambda form: \
                        set_event_from_incident(form, "event_post"),
                       )

        # ---------------------------------------------------------------------
        # Link table between Posts & Incident Types
        tablename = "event_post_incident_type"
        define_table(tablename,
                     post_id(empty = False,
                             ondelete = "CASCADE",
                             ),
                     self.event_incident_type_id(empty = False,
                                                 ondelete = "CASCADE",
                                                 ),
                     *s3_meta_fields())

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3EventCMSTagModel(S3Model):
    """
        Link (CMS) Tags to Events or Incidents (used in WACOP)
        - the Incident tags do NOT populate the Event's

        TODO rename into event_cms_tag for clarity (event_tag is easily
             confused with event_event_tag)?
    """

    names = ("event_tag",
             )

    def model(self):

        #T = current.T

        # ---------------------------------------------------------------------
        # Tags

        tablename = "event_tag"
        self.define_table(tablename,
                          self.event_event_id(ondelete = "CASCADE",
                                              ),
                          self.event_incident_id(ondelete = "CASCADE",
                                                 ),
                          self.cms_tag_id(empty = False,
                                          ondelete = "CASCADE",
                                          ),
                          *s3_meta_fields())

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3EventDCModel(S3Model):
    """
        Link Data Collections to Events &/or Incidents
    """

    names = ("event_response",
             "event_target",
             )

    def model(self):

        #T = current.T

        configure = self.configure
        define_table = self.define_table

        event_id = self.event_event_id
        incident_id = self.event_incident_id

        if current.deployment_settings.get_event_cascade_delete_incidents():
            ondelete = "CASCADE"
        else:
            ondelete = "SET NULL"

        # ---------------------------------------------------------------------
        # Link table between Assessments & Events/Incidents
        tablename = "event_response"
        define_table(tablename,
                     event_id(ondelete = ondelete),
                     incident_id(ondelete = "CASCADE"),
                     self.dc_response_id(empty = False,
                                         ondelete = "CASCADE",
                                         ),
                     *s3_meta_fields())

        configure(tablename,
                  onaccept = lambda form: \
                    set_event_from_incident(form, "event_response"),
                  )

        # ---------------------------------------------------------------------
        # Link table between Targets & Events/Incidents
        tablename = "event_target"
        define_table(tablename,
                     event_id(ondelete = ondelete),
                     incident_id(ondelete = "CASCADE"),
                     self.dc_target_id(empty = False,
                                       ondelete = "CASCADE",
                                       ),
                     *s3_meta_fields())

        configure(tablename,
                  onaccept = lambda form: \
                    set_event_from_incident(form, "event_target"),
                  )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3EventForumModel(S3Model):
    """
        Shares for Events &/or Incidents
        - the Incident shares do NOT populate the Event's
    """

    names = ("event_forum",
             )

    def model(self):

        #T = current.T

        # ---------------------------------------------------------------------
        # Shares: Link table between Forums & Events/Incidents
        tablename = "event_forum"
        self.define_table(tablename,
                          self.event_event_id(ondelete = "CASCADE"),
                          self.event_incident_id(ondelete = "CASCADE"),
                          self.pr_forum_id(empty = False,
                                           ondelete = "CASCADE",
                                           ),
                          *s3_meta_fields())

        #current.response.s3.crud_strings[tablename] = Storage(
        #    label_create = T("Share Incident"), # or Event
        #    title_display = T(" Shared Incident Details"),
        #    title_list = T("Shared Incidents"),
        #    title_update = T("Edit Shared Incident"),
        #    label_list_button = T("List Shared Incidents"),
        #    label_delete_button = T("Stop Sharing this Incident"),
        #    msg_record_created = T("Incident Shared"),
        #    msg_record_modified = T("Sharing updated"),
        #    msg_record_deleted = T("Incident no longer shared"),
        #    msg_list_empty = T("No Incidents currently shared"))

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3EventHRModel(S3Model):
    """
        Link Human Resources to Events/Incidents
    """

    names = ("event_human_resource",
             )

    def model(self):

        T = current.T

        settings = current.deployment_settings
        sitrep_edxl = settings.get_event_sitrep_edxl()

        if settings.get_event_cascade_delete_incidents():
            ondelete = "CASCADE"
        else:
            ondelete = "SET NULL"

        if settings.has_module("hrm"):
            # Proper field
            job_title_represent = S3Represent(lookup="hrm_job_title")
        else:
            # Dummy field - probably this model not being used but others from Event are
            job_title_represent = None

        # SAFIRE\SC
        status_opts = {1: T("Requested"),
                       2: T("Assigned"),
                       3: T("Standby"),
                       4: T("Mobilized (staged)"),
                       5: T("In Action"),
                       6: T("Demobilize"),
                       7: T("Stand-down"),
                       }

        # ---------------------------------------------------------------------
        # Positions required &, if they are filled, then who is filling them
        # - NB If the Person filling a Role changes then a new record should be created with a new start_date/end_date
        #

        tablename = "event_human_resource"
        self.define_table(tablename,
                          # Instance table
                          self.super_link("cost_item_id", "budget_cost_item"),
                          self.event_event_id(ondelete = ondelete,
                                              # Enable in template if-desired
                                              readable = False,
                                              writable = False,
                                              ),
                          self.event_incident_id(ondelete = "CASCADE"),
                          # Enable in-templates as-required (used by SCPHIMS)
                          self.org_sector_id(readable = False,
                                             writable = False,
                                             ),
                          self.org_organisation_id(label = T("Requesting Organization"),
                                                   readable = sitrep_edxl,
                                                   writable = sitrep_edxl,
                                                   ),
                          self.hrm_job_title_id(label = T("Position"), # T("Role")?
                                                ondelete = "SET NULL",
                                                requires = IS_EMPTY_OR(
                                                            IS_ONE_OF(current.db, "hrm_job_title.id",
                                                                      job_title_represent,
                                                                      filterby="type",
                                                                      filter_opts=(4,), # Type: Deploy
                                                                      )),
                                                comment = S3PopupLink(c = "hrm",
                                                                      f = "job_title",
                                                                      label = T("Create Position"),
                                                                      title = T("Position"),
                                                                      tooltip = T("The person's position in this incident"),
                                                                      ),
                                                ),
                          self.pr_person_id(ondelete = "RESTRICT",
                                            comment = S3PopupLink(c = "pr",
                                                                  f = "person",
                                                                  # No special controller so need this for an options lookup
                                                                  vars = {"prefix": "hrm",
                                                                          "parent": "human_resource",
                                                                          },
                                                                  label = T("Create Person"),
                                                                  title = T("Person"),
                                                                  tooltip = T("The specific individual assigned to this position for this incident. Type the first few characters of one of the Person's names."),
                                                                  ),
                                            ),
                          # reportsToAgency in EDXL-SitRep: person_id$human_resource.organisation_id
                          Field("status", "integer",
                                label = T("Status"),
                                represent = lambda opt: \
                                    status_opts.get(opt) or current.messages.UNKNOWN_OPT,
                                requires = IS_EMPTY_OR(
                                            IS_IN_SET(status_opts),
                                            ),
                                ),
                          s3_datetime("start_date",
                                      label = T("Start Date"),
                                      widget = "date",
                                      ),
                          s3_datetime("end_date",
                                      label = T("End Date"),
                                      # Not supported by s3_datetime
                                      #start_field = "event_human_resource_start_date",
                                      #default_interval = 12,
                                      widget = "date",
                                      ),
                          s3_comments(),
                          *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Assign Human Resource"),
            title_display = T("Human Resource Details"),
            title_list = T("Assigned Human Resources"),
            title_update = T("Edit Human Resource"),
            label_list_button = T("List Assigned Human Resources"),
            label_delete_button = T("Remove Human Resource from this incident"),
            msg_record_created = T("Human Resource assigned"),
            msg_record_modified = T("Human Resource Assignment updated"),
            msg_record_deleted = T("Human Resource unassigned"),
            msg_list_empty = T("No Human Resources currently assigned to this incident"))

        list_fields = [#"incident_id", # Not being dropped in component view
                       "job_title_id",
                       "person_id",
                       "status",
                       "start_date",
                       "end_date",
                       ]

        if current.deployment_settings.has_module("budget"):
            crud_form = S3SQLCustomForm("incident_id",
                                        "job_title_id",
                                        "person_id",
                                        "start_date",
                                        "end_date",
                                        S3SQLInlineComponent("allocation",
                                                             label = T("Budget"),
                                                             fields = ["budget_id",
                                                                       # @ToDo: Populate these automatically from the master record
                                                                       #"start_date",
                                                                       #"end_date",
                                                                       "daily_cost",
                                                                       ],
                                                             ),
                                        )
            list_fields.extend(("allocation.budget_id",
                                #"allocation.start_date",
                                #"allocation.end_date",
                                "allocation.daily_cost",
                                ))
        else:
            crud_form = None

        self.configure(tablename,
                       context = {"incident": "incident_id",
                                  },
                       create_onaccept = self.event_human_resource_onaccept,
                       crud_form = crud_form,
                       deduplicate = S3Duplicate(primary = ("incident_id",
                                                            "job_title_id",
                                                            "person_id",
                                                            "start_date",
                                                            "end_date",
                                                            ),
                                                 ),
                       list_fields = list_fields,
                       update_onaccept = lambda form:
                                            self.event_human_resource_onaccept(form, create=False),
                       super_entity = "budget_cost_item",
                       )

        # Pass names back to global scope (s3.*)
        return {}

    # ---------------------------------------------------------------------
    @staticmethod
    def event_human_resource_onaccept(form, create=True):
        """
            When a Position is assigned to an Incident:
             - set_event_from_incident
             - add Log Entry
        """

        set_event_from_incident(form, "event_human_resource")

        s3db = current.s3db
        table = s3db.event_human_resource

        form_vars = form.vars
        form_vars_get = form_vars.get
        incident_id = form_vars_get("incident_id")
        if not incident_id:
            link = current.db(table.id == form_vars_get("id")).select(table.incident_id,
                                                                      limitby = (0, 1)
                                                                      ).first()
            incident_id = link.incident_id

        if create:
            job_title_id = form_vars_get("job_title_id")
            if job_title_id:
                s3db.event_incident_log.insert(incident_id = incident_id,
                                               name = "Person Requested",
                                               comments = s3db.event_human_resource.job_title_id.represent(job_title_id),
                                               )
            return

        # Update
        record = form.record
        if record: # Not True for a record merger
            changed = {}
            for var in form_vars:
                vvar = form_vars[var]
                if isinstance(vvar, Field):
                    # modified_by/modified_on
                    continue
                rvar = record.get(var, "NOT_PRESENT")
                if rvar != "NOT_PRESENT" and vvar != rvar:
                    f = table[var]
                    type_ = f.type
                    if type_ == "integer" or \
                       type_.startswith("reference"):
                        if vvar:
                            vvar = int(vvar)
                        if vvar == rvar:
                            continue
                    represent = table[var].represent
                    if represent:
                        if hasattr(represent, "show_link"):
                            represent.show_link = False
                    else:
                        represent = lambda o: o
                    if rvar:
                        changed[var] = "%s changed from %s to %s" % \
                            (f.label, represent(rvar), represent(vvar))
                    else:
                        changed[var] = "%s changed to %s" % \
                            (f.label, represent(vvar))

            if changed:
                table = s3db.event_incident_log
                text = []
                for var in changed:
                    text.append(changed[var])
                text = "\n".join(text)
                table.insert(incident_id = incident_id,
                             #name = "Person Assigned",
                             name = "Person Request Updated",
                             comments = text,
                             )

# =============================================================================
class S3EventTeamModel(S3Model):
    """ Link Teams to Events &/or Incidents """

    names = ("event_team_status",
             "event_team",
             )

    def model(self):

        T = current.T
        db = current.db

        define_table = self.define_table
        configure = self.configure
        crud_strings = current.response.s3.crud_strings

        if current.deployment_settings.get_event_cascade_delete_incidents():
            ondelete = "CASCADE"
        else:
            ondelete = "SET NULL"

        # ---------------------------------------------------------------------
        # Event Team Statuses
        #
        # @ToDo: May need to categorise these by Organisation
        #
        tablename = "event_team_status"
        define_table(tablename,
                     Field("name",
                           length = 64,
                           label = T("Name"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(64),
                                       ],
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

        represent = S3Represent(lookup=tablename)
        status_id = S3ReusableField("status_id", "reference %s" % tablename,
                                    label = T("Status"),
                                    ondelete = "RESTRICT",
                                    represent = represent,
                                    requires = IS_ONE_OF(db, "event_team_status.id",
                                                         represent,
                                                         orderby="event_team_status.name",
                                                         sort=True,
                                                         ),
                                    sortby = "name",
                                    )

        configure(tablename,
                  # All name duplicates are updates (=default rule):
                  deduplicate = S3Duplicate(),
                  )

        # ---------------------------------------------------------------------
        # Link table incident<=>team
        #
        tablename = "event_team"
        define_table(tablename,
                     self.event_event_id(ondelete = ondelete),
                     self.event_incident_id(empty = False,
                                            ondelete = "CASCADE",
                                            ),
                     self.pr_group_id(empty = False,
                                      ondelete = "RESTRICT",
                                      # Dropdown, not Autocomplete
                                      widget = None,
                                      ),
                     status_id(),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("Assign Team"),
            title_display = T("Team Details"),
            title_list = T("Assigned Teams"),
            title_update = T("Edit Team"),
            label_list_button = T("List Assigned Teams"),
            label_delete_button = T("Remove Team from this incident"),
            msg_record_created = T("Team assigned"),
            msg_record_modified = T("Team Assignment updated"),
            msg_record_deleted = T("Team Assignment removed"),
            msg_list_empty = T("No Teams currently assigned to this incident"))

        configure(tablename,
                  # Team can be assigned to multiple incidents,
                  # so updates must match both incident_id and group_id:
                  deduplicate = S3Duplicate(primary=("incident_id",
                                                     "group_id",
                                                     )),
                  onaccept = lambda form: \
                        set_event_from_incident(form, "event_team"),
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3EventImpactModel(S3Model):
    """
        Link Events &/or Incidents with Impacts
    """

    names = ("event_event_impact",
             )

    def model(self):

        if not current.deployment_settings.has_module("stats"):
            current.log.warning("Event Impact Model needs Stats module enabling")
            return {}

        #T = current.T

        if current.deployment_settings.get_event_cascade_delete_incidents():
            ondelete = "CASCADE"
        else:
            ondelete = "SET NULL"

        # ---------------------------------------------------------------------
        # Events <> Impacts

        tablename = "event_event_impact"
        self.define_table(tablename,
                          self.event_event_id(ondelete = ondelete),
                          self.event_incident_id(ondelete = "CASCADE"),
                          self.stats_impact_id(empty = False,
                                               ondelete = "CASCADE",
                                               ),
                          *s3_meta_fields())

        # Table configuration
        self.configure(tablename,
                       onaccept = lambda form: \
                        set_event_from_incident(form, "event_event_impact"),
                       )

        # Not accessed directly
        #current.response.s3.crud_strings[tablename] = Storage(
        #    label_create = T("Add Impact"),
        #    title_display = T("Impact Details"),
        #    title_list = T("Impacts"),
        #    title_update = T("Edit Impact"),
        #    label_list_button = T("List Impacts"),
        #    label_delete_button = T("Delete Impact"),
        #    msg_record_created = T("Impact added"),
        #    msg_record_modified = T("Impact updated"),
        #    msg_record_deleted = T("Impact removed"),
        #    msg_list_empty = T("No Impacts currently registered in this Event"))

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3EventMapModel(S3Model):
    """
        Link Map Configs to Incidents
    """

    names = ("event_config",
             )

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Map Config
        tablename = "event_config"
        self.define_table(tablename,
                          self.event_incident_id(empty = False,
                                                 ondelete = "CASCADE",
                                                 ),
                          self.gis_config_id(empty = False,
                                             ondelete = "CASCADE",
                                             ),
                          *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Map Profile"),
            title_display = T("Map Profile Details"),
            title_list = T("Map Profiles"),
            title_update = T("Edit Map Profile"),
            label_list_button = T("List Map Profiles"),
            label_delete_button = T("Remove Map Profile from this incident"),
            msg_record_created = T("Map Profile added"),
            msg_record_modified = T("Map Profile updated"),
            msg_record_deleted = T("Map Profile removed"),
            msg_list_empty = T("No Map Profiles currently registered in this incident"))

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3EventNeedModel(S3Model):
    """
        Link Events &/or Incidents with Needs
    """

    names = ("event_event_need",
             )

    def model(self):

        #T = current.T

        if current.deployment_settings.get_event_cascade_delete_incidents():
            ondelete = "CASCADE"
        else:
            ondelete = "SET NULL"

        # ---------------------------------------------------------------------
        # Events <> Impacts
        #

        tablename = "event_event_need"
        self.define_table(tablename,
                          self.event_event_id(ondelete = ondelete),
                          self.event_incident_id(ondelete = "CASCADE"),
                          self.req_need_id(empty = False,
                                           ondelete = "CASCADE",
                                           ),
                          *s3_meta_fields())

        # Table configuration
        self.configure(tablename,
                       onaccept = lambda form: \
                        set_event_from_incident(form, "event_event_need"),
                       )

        # Not accessed directly
        #current.response.s3.crud_strings[tablename] = Storage(
        #    label_create = T("Add Need"),
        #    title_display = T("Need Details"),
        #    title_list = T("Needs"),
        #    title_update = T("Edit Need"),
        #    label_list_button = T("List Needs"),
        #    label_delete_button = T("Delete Need"),
        #    msg_record_created = T("Need added"),
        #    msg_record_modified = T("Need updated"),
        #    msg_record_deleted = T("Need removed"),
        #    msg_list_empty = T("No Needs currently registered in this Event"))

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3EventNeedResponseModel(S3Model):
    """
        Link Events &/or Incidents with Need Responses (Activity Groups)
    """

    names = ("event_event_need_response",
             )

    def model(self):

        #T = current.T

        if current.deployment_settings.get_event_cascade_delete_incidents():
            ondelete = "CASCADE"
        else:
            ondelete = "SET NULL"

        # ---------------------------------------------------------------------
        # Events <> Impacts
        #

        tablename = "event_event_need_response"
        self.define_table(tablename,
                          self.event_event_id(ondelete = ondelete),
                          self.event_incident_id(ondelete = "CASCADE"),
                          self.req_need_response_id(empty = False,
                                                    ondelete = "CASCADE",
                                                    ),
                          *s3_meta_fields())

        # Table configuration
        self.configure(tablename,
                       onaccept = lambda form: \
                        set_event_from_incident(form, "event_event_need_response"),
                       )

        # Not accessed directly
        #current.response.s3.crud_strings[tablename] = Storage(
        #    label_create = T("Add Activity Group"),
        #    title_display = T("Activity Group Details"),
        #    title_list = T("Activity Groups"),
        #    title_update = T("Edit Activity Group"),
        #    label_list_button = T("List Activity Groups"),
        #    label_delete_button = T("Delete Activity Group"),
        #    msg_record_created = T("Activity Group added"),
        #    msg_record_modified = T("Activity Group updated"),
        #    msg_record_deleted = T("Activity Group removed"),
        #    msg_list_empty = T("No Activity Groups currently registered in this Event"))

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3EventOrganisationModel(S3Model):
    """
        Link Organisations to Events &/or Incidents
    """

    names = ("event_organisation",
             )

    def model(self):

        T = current.T

        status_opts = {1: T("Alerted"),
                       2: T("Standing By"),
                       3: T("Active"),
                       4: T("Deactivated"),
                       5: T("Unable to activate"),
                       }

        if current.deployment_settings.get_event_cascade_delete_incidents():
            ondelete = "CASCADE"
        else:
            ondelete = "SET NULL"

        # ---------------------------------------------------------------------
        # Organisations linked to this Incident / Event
        #

        tablename = "event_organisation"
        self.define_table(tablename,
                          self.event_event_id(ondelete = ondelete,
                                              ),
                          self.event_incident_id(ondelete = "CASCADE",
                                                 ),
                          self.org_organisation_id(empty = False,
                                                   ondelete = "CASCADE",
                                                   ),
                          Field("status", "integer",
                                default = 1,
                                represent = lambda opt: \
                                       status_opts.get(opt, current.messages.UNKNOWN_OPT),
                                requires = IS_IN_SET(status_opts),
                                ),
                          # @ToDo: Role?
                          s3_comments(),
                          *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Organization"),
            title_display = T("Organization Details"),
            title_list = T("Organizations"),
            title_update = T("Edit Organization"),
            label_list_button = T("List Organizations"),
            label_delete_button = T("Remove Organization from this incident"),
            msg_record_created = T("Organization added"),
            msg_record_modified = T("Organization updated"),
            msg_record_deleted = T("Organization removed"),
            msg_list_empty = T("No Organizations currently registered in this incident"))

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("event_id",
                                                            "incident_id",
                                                            "organisation_id",
                                                            ),
                                                 ),
                       onaccept = lambda form: \
                        set_event_from_incident(form, "event_organisation"),
                       )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3EventProjectModel(S3Model):
    """
        Link Projects to Events
    """

    names = ("event_project",
             )

    def model(self):

        #if current.deployment_settings.get_event_cascade_delete_incidents():
        #    ondelete = "CASCADE"
        #else:
        #    ondelete = "SET NULL"

        tablename = "event_project"
        self.define_table(tablename,
                          self.event_event_id(empty = False,
                                              ondelete = "CASCADE"),
                          #self.event_incident_id(ondelete = "CASCADE"),
                          self.project_project_id(#ondelete = "CASCADE", # default anyway
                                                  ),
                          *s3_meta_fields())

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3EventScenarioModel(S3Model):
    """
        Scenario Model

        http://eden.sahanafoundation.org/wiki/BluePrintScenario
    """

    names = ("event_scenario",
             "event_scenario_id",
             )

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Scenarios
        #
        tablename = "event_scenario"
        self.define_table(tablename,
                          Field("name", notnull=True,
                                length=64,    # Mayon compatiblity
                                label = T("Name"),
                                requires = [IS_NOT_EMPTY(),
                                            IS_LENGTH(64)
                                            ],
                                ),
                          # Mandatory Incident Type
                          self.event_incident_type_id(empty = False),
                          # Optional Organisation
                          self.org_organisation_id(),
                          # Optional Location
                          self.gis_location_id(),
                          s3_comments(),
                          *s3_meta_fields())

        # CRUD strings
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Scenario"),
            title_display = T("Scenario Details"),
            title_list = T("Scenarios"),
            title_update = T("Edit Scenario"),
            title_upload = T("Import Scenarios"),
            label_list_button = T("List Scenarios"),
            label_delete_button = T("Delete Scenario"),
            msg_record_created = T("Scenario added"),
            msg_record_modified = T("Scenario updated"),
            msg_record_deleted = T("Scenario deleted"),
            msg_list_empty = T("No Scenarios currently registered"))

        # Components
        self.add_components(tablename,
                            # Tasks
                            project_task = {"link": "event_scenario_task",
                                            "joinby": "scenario_id",
                                            "key": "task_id",
                                            "actuate": "replace",
                                            "autodelete": True,
                                            },
                            event_scenario_task = "scenario_id",
                            # People
                            event_scenario_human_resource = {"name": "human_resource",
                                                             "joinby": "scenario_id",
                                                             },
                            #pr_person = {"link": "event_scenario_human_resource",
                            #             "joinby": "scenario_id",
                            #             "key": "person_id",
                            #             "actuate": "hide",
                            #             "autodelete": False,
                            #             },
                            # Assets
                            event_scenario_asset = "scenario_id",
                            asset_asset = {"link": "event_scenario_asset",
                                           "joinby": "scenario_id",
                                           "key": "asset_id",
                                           "actuate": "hide",
                                           "autodelete": False,
                                           },
                            )

        represent = S3Represent(lookup=tablename)
        scenario_id = S3ReusableField("scenario_id", "reference %s" % tablename,
                                      label = T("Scenario"),
                                      ondelete = "SET NULL",
                                      represent = represent,
                                      requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(current.db, "event_scenario.id",
                                                              represent,
                                                              orderby = "event_scenario.name",
                                                              sort = True,
                                                              )),
                                      sortby = "name",
                                      # Comment these to use a Dropdown & not an Autocomplete
                                      #widget = S3AutocompleteWidget()
                                      #comment = DIV(_class="tooltip",
                                      #              _title="%s|%s" % (T("Scenario"),
                                      #                                current.messages.AUTOCOMPLETE_HELP))
                                    )

        filter_widgets = [S3TextFilter("name",
                                       label = T("Search"),
                                       ),
                          S3OptionsFilter("incident_type_id"),
                          ]

        self.configure(tablename,
                       create_next = URL(args = ["[id]", "plan"]),
                       deduplicate = S3Duplicate(),
                       filter_widgets = filter_widgets,
                       )

        self.set_method("event", "scenario",
                        method = "plan",
                        action = event_ScenarioActionPlan)

        # Pass names back to global scope (s3.*)
        return {"event_scenario_id": scenario_id,
                }

# =============================================================================
class S3EventScenarioAssetModel(S3Model):
    """
        Link Scenarios to Assets
    """

    names = ("event_scenario_asset",
             )

    def model(self):

        settings = current.deployment_settings
        if not settings.has_module("supply"):
            # Don't crash
            #return self.defaults()
            return {}

        T = current.T

        # ---------------------------------------------------------------------
        # Assets

        # @ToDo: make this lookup Lazy (also in asset.py)
        ctable = self.supply_item_category
        itable = self.supply_item
        supply_item_represent = self.supply_item_represent
        asset_items_set = current.db((ctable.can_be_asset == True) & \
                                     (itable.item_category_id == ctable.id))

        tablename = "event_scenario_asset"
        self.define_table(tablename,
                          # Instance table
                          self.event_scenario_id(empty = False,
                                                 ondelete = "CASCADE"),
                          # Mandatory: Define the Item Type
                          self.supply_item_id(represent = supply_item_represent,
                                              requires = IS_ONE_OF(asset_items_set,
                                                                   "supply_item.id",
                                                                   supply_item_represent,
                                                                   sort = True,
                                                                   ),
                                              script = None, # No Item Pack Filter
                                              widget = None,
                                              comment = S3PopupLink(c = "supply",
                                                                    f = "item",
                                                                    # No special controller so need this for an options lookup
                                                                    vars = {"prefix": "asset",
                                                                            "parent": "asset",
                                                                            },
                                                                    label = T("Create Item Type"),
                                                                    title = T("Item"),
                                                                    #tooltip = supply_item_tooltip,
                                                                    ),
                                              ),
                          # Optional: Assign specific Asset
                          # @ToDo: Filter widget based on Type
                          self.asset_asset_id(ondelete = "RESTRICT",
                                              comment = T("Only assign a specific item if there are no alternatives"),
                                              ),
                          # @ToDo: Have a T+x time into Response for Start/End
                          #s3_datetime("start_date",
                          #            label = T("Start Date"),
                          #            widget = "date",
                          #            ),
                          #s3_datetime("end_date",
                          #            label = T("End Date"),
                          #            # Not supported by s3_datetime
                          #            #start_field = "event_scenario_asset_start_date",
                          #            #default_interval = 12,
                          #            widget = "date",
                          #            ),
                          s3_comments(),

                          *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Asset"),
            title_display = T("Asset Details"),
            title_list = T("Assets"),
            title_update = T("Edit Asset"),
            label_list_button = T("List Assets"),
            label_delete_button = T("Remove Asset from this scenario"),
            msg_record_created = T("Asset added"),
            msg_record_modified = T("Asset updated"),
            msg_record_deleted = T("Asset removed"),
            msg_list_empty = T("No Assets currently registered for this scenario"))

        self.configure(tablename,
                       context = {"scenario": "scenario_id",
                                  },
                       deduplicate = S3Duplicate(primary = ("scenario_id",
                                                            "item_id",
                                                            "asset_id",
                                                            ),
                                                 ),
                       )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3EventScenarioHRModel(S3Model):
    """
        Link Scenarios to Human Resources
    """

    names = ("event_scenario_human_resource",
             )

    def model(self):

        T = current.T

        if current.deployment_settings.has_module("hrm"):
            # Proper field
            job_title_represent = S3Represent(lookup="hrm_job_title")
        else:
            # Dummy field - probably this model not being used but others from Event are
            job_title_represent = None

        # ---------------------------------------------------------------------
        # Positions required &, potentially, then who would normally fill them
        #

        tablename = "event_scenario_human_resource"
        self.define_table(tablename,
                          self.event_scenario_id(ondelete = "CASCADE",
                                                 ),
                          self.hrm_job_title_id(label = T("Position"), # T("Role")?
                                                ondelete = "SET NULL",
                                                requires = IS_EMPTY_OR(
                                                            IS_ONE_OF(current.db, "hrm_job_title.id",
                                                                      job_title_represent,
                                                                      filterby="type",
                                                                      filter_opts=(4,), # Type: Deploy
                                                                      )),
                                                comment = S3PopupLink(c = "hrm",
                                                                      f = "job_title",
                                                                      # No special controller so need this for an options lookup
                                                                      vars = {"prefix": "hrm",
                                                                              "parent": "human_resource",
                                                                              },
                                                                      label = T("Create Position"),
                                                                      title = T("Position"),
                                                                      tooltip = T("The person's position in this incident"),
                                                                      ),
                                                ),
                          self.pr_person_id(ondelete = "RESTRICT",
                                            comment = S3PopupLink(c = "pr",
                                                                  f = "person",
                                                                  # No special controller so need this for an options lookup
                                                                  vars = {"prefix": "hrm",
                                                                          "parent": "human_resource",
                                                                          },
                                                                  label = T("Create Person"),
                                                                  title = T("Person"),
                                                                  tooltip = T("The specific individual assigned to this position for this scenario. Not generally used, only use if there are no alternatives. Type the first few characters of one of the Person's names."),
                                                                  ),
                                            ),
                          # @ToDo: Have a T+x time into Response for Start/End
                          #s3_datetime("start_date",
                          #            label = T("Start Date"),
                          #            widget = "date",
                          #            ),
                          #s3_datetime("end_date",
                          #            label = T("End Date"),
                          #            # Not supported by s3_datetime
                          #            #start_field = "event_scenario_human_resource_start_date",
                          #            #default_interval = 12,
                          #            widget = "date",
                          #            ),
                          s3_comments(),
                          *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Assign Human Resource"),
            title_display = T("Human Resource Details"),
            title_list = T("Assigned Human Resources"),
            title_update = T("Edit Human Resource"),
            label_list_button = T("List Assigned Human Resources"),
            label_delete_button = T("Remove Human Resource from this scenario"),
            msg_record_created = T("Human Resource assigned"),
            msg_record_modified = T("Human Resource Assignment updated"),
            msg_record_deleted = T("Human Resource unassigned"),
            msg_list_empty = T("No Human Resources currently assigned to this scenario"))

        self.configure(tablename,
                       context = {"scenario": "scenario_id",
                                  },
                       deduplicate = S3Duplicate(primary = ("scenario_id",
                                                            "job_title_id",
                                                            "person_id",
                                                            ),
                                                 ),
                       )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3EventScenarioOrganisationModel(S3Model):
    """
        Link Scenarios to Organisations
    """

    names = ("event_scenario_organisation",
             )

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Organisations assigned to a Scenario
        #

        tablename = "event_scenario_organisation"
        self.define_table(tablename,
                          self.event_scenario_id(ondelete = "CASCADE",
                                                 ),
                          self.org_organisation_id(ondelete = "RESTRICT",
                                                   empty = False,
                                                   ),
                          s3_comments(),
                          *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Assign Organization"),
            title_display = T("Organization Details"),
            title_list = T("Assigned Organizations"),
            title_update = T("Edit Organization"),
            label_list_button = T("List Assigned Organizations"),
            label_delete_button = T("Remove Organization from this scenario"),
            msg_record_created = T("Organization assigned"),
            msg_record_modified = T("Organization Assignment updated"),
            msg_record_deleted = T("Organization unassigned"),
            msg_list_empty = T("No Organizations currently assigned to this scenario"))

        self.configure(tablename,
                       context = {"scenario": "scenario_id",
                                  },
                       deduplicate = S3Duplicate(primary = ("scenario_id",
                                                            "organisation_id",
                                                            ),
                                                 ),
                       )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3EventScenarioTaskModel(S3Model):
    """
        Link Scenarios to Tasks

        @ToDo: Use Task Templates not Tasks
    """

    names = ("event_scenario_task",
             )

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Tasks
        #

        tablename = "event_scenario_task"
        self.define_table(tablename,
                          self.event_scenario_id(ondelete = "CASCADE",
                                                 ),
                          self.project_task_id(empty = False,
                                               ondelete = "CASCADE",
                                               ),
                          *s3_meta_fields())

        # Not used as we actuate = replace, although the
        # msg_list_empty is used by the ActionPlan
        current.response.s3.crud_strings[tablename] = Storage(
        #    label_create = T("Create Task"),
        #    title_display = T("Task Details"),
        #    title_list = T("Tasks"),
        #    title_update = T("Edit Task"),
        #    label_list_button = T("List Tasks"),
        #    label_delete_button = T("Remove Task from this scenario"),
        #    msg_record_created = T("Task added"),
        #    msg_record_modified = T("Task updated"),
        #    msg_record_deleted = T("Task removed"),
            msg_list_empty = T("No Tasks currently registered for this scenario"))

        self.configure(tablename,
                       context = {"scenario": "scenario_id",
                                  },
                       deduplicate = S3Duplicate(primary = ("scenario_id",
                                                            "task_id",
                                                            ),
                                                 ),
                       )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3EventSiteModel(S3Model):
    """
        Link Sites (Facilities) to Incidents
    """

    names = ("event_site",
             )

    def model(self):

        T = current.T
        super_link = self.super_link
        settings = current.deployment_settings

        status_opts = {1: T("Alerted"),
                       2: T("Standing By"),
                       3: T("Active"),
                       4: T("Deactivated"),
                       5: T("Unable to activate"),
                       }

        SITE_LABEL = settings.get_org_site_label()

        if settings.get_event_cascade_delete_incidents():
            ondelete = "CASCADE"
        else:
            ondelete = "SET NULL"

        # ---------------------------------------------------------------------
        # Facilities
        # @ToDo: Filter Widgets
        tablename = "event_site"
        self.define_table(tablename,
                          # Instance table
                          super_link("cost_item_id", "budget_cost_item"),
                          self.event_event_id(ondelete = ondelete,
                                              ),
                          self.event_incident_id(empty = False,
                                                 ondelete = "CASCADE",
                                                 ),
                          # This is a component, so needs to be a super_link
                          # - can't override field name, ondelete or requires
                          super_link("site_id", "org_site",
                                     #default = auth.user.site_id if auth.is_logged_in() else None,
                                     empty = False,
                                     label = SITE_LABEL,
                                     ondelete = "CASCADE",
                                     represent = self.org_site_represent,
                                     readable = True,
                                     writable = True,
                                     # Comment these to use a Dropdown & not an Autocomplete
                                     #widget = S3SiteAutocompleteWidget(),
                                     #comment = DIV(_class="tooltip",
                                     #              _title="%s|%s" % (SITE_LABEL,
                                     #                                messages.AUTOCOMPLETE_HELP)),
                                     ),
                          Field("status", "integer",
                                default = 1,
                                represent = lambda opt: \
                                       status_opts.get(opt, current.messages.UNKNOWN_OPT),
                                requires = IS_IN_SET(status_opts),
                                ),
                          *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Assign Facility"),
            title_display = T("Facility Details"),
            title_list = T("Facilities"),
            title_update = T("Edit Facility"),
            label_list_button = T("List Facilities"),
            label_delete_button = T("Remove Facility from this incident"),
            msg_record_created = T("Facility added"),
            msg_record_modified = T("Facility updated"),
            msg_record_deleted = T("Facility removed"),
            msg_list_empty = T("No Facilities currently registered in this incident"))

        if current.deployment_settings.has_module("budget"):
            crud_form = S3SQLCustomForm("incident_id",
                                        "site_id",
                                        "status",
                                        S3SQLInlineComponent("allocation",
                                                             label = T("Budget"),
                                                             fields = ["budget_entity_id",
                                                                       "start_date",
                                                                       "end_date",
                                                                       "daily_cost",
                                                                       ],
                                                             ),
                                        )
        else:
            crud_form = None

        self.configure(tablename,
                       crud_form = crud_form,
                       deduplicate = S3Duplicate(primary = ("incident_id",
                                                            "site_id",
                                                            ),
                                                 ),
                       list_fields = ["incident_id",
                                      "site_id",
                                      "status",
                                      "allocation.budget_entity_id",
                                      "allocation.start_date",
                                      "allocation.end_date",
                                      "allocation.daily_cost",
                                      ],
                       onaccept = lambda form: \
                                set_event_from_incident(form, "event_site"),
                       super_entity = "budget_cost_item",
                       )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3EventShelterModel(S3Model):
    """
        Link Shelters to Events
    """

    names = ("event_event_shelter",
             )

    def model(self):

        T = current.T

        ondelete = "CASCADE"
        #if current.deployment_settings.get_event_cascade_delete_incidents():
        #    ondelete = "CASCADE"
        #else:
        #    ondelete = "SET NULL"

        # ---------------------------------------------------------------------
        # Shelters
        #   Link table for cr_shelter <> event_event
        tablename = "event_event_shelter"
        self.define_table(tablename,
                          self.event_event_id(ondelete = ondelete),
                          #self.event_incident_id(ondelete = "CASCADE"),
                          self.cr_shelter_id(empty = False,
                                             ondelete = "CASCADE",
                                             ),
                          *s3_meta_fields()
                          )

        function = current.request.function
        if function == "event":
            current.response.s3.crud_strings[tablename] = Storage(
                label_create = T("Add Shelter"),
                title_display = T("Shelter Details"),
                title_list = T("Shelters"),
                title_update = T("Edit Shelter"),
                label_list_button = T("List Shelters"),
                label_delete_button = T("Remove Shelter for this Event"),
                msg_record_created = T("Shelter added"),
                msg_record_modified = T("Shelter updated"),
                msg_record_deleted = T("Shelter removed"),
                msg_list_empty = T("No Shelters currently tagged to this event")
                )

        elif function == "shelter":
            current.response.s3.crud_strings[tablename] = Storage(
                label_create = T("Associate Event"),
                title_display = T("Event Details"),
                title_list = T("Events"),
                title_update = T("Edit Event"),
                label_list_button = T("List Events"),
                label_delete_button = T("Remove Event for this Shelter"),
                msg_record_created = T("Event added"),
                msg_record_modified = T("Event updated"),
                msg_record_deleted = T("Event removed"),
                msg_list_empty = T("No Events currently tagged to this Shelter")
                )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3EventSitRepModel(S3Model):
    """
        Situation Reports
        - can be simple text/rich text
        - can add documents/photos
        - can add structured components such as Impacts / Staff Assignments
        - can add Tags
        - can add User-controlled Fields (Dynamic Tables)
        - can be compliant with EDXL SitRep 1.0:
        http://docs.oasis-open.org/emergency/edxl-sitrep/v1.0/cs02/edxl-sitrep-v1.0-cs02.html
        messageID 1..1 uuid
        preparedBy 1..1 created_by/modified_by + created_on/modified_on
        authorizedBy 1..1 approved_by + approved_on
        reportPurpose 1..1
        reportNumber 1..1
        reportVersion 1..1
        forTimePeriod 1..1 date/end_date
        reportTitle 0..1 name
        incidentID 1..* incident_id (add separate link table to handle multiple incidents, if-required)
        incidentLifecyclePhase 0..* phase
        originatingMessageID 0..1 uuid (can be itself)
        precedingMessageID 0..* uuid
        urgency 0..1 urgency
        reportConfidence 1..1 confidence
        severity 1..1 severity
        reportingLocation 0..1 location_id
        actionPlan 0..1
        nextContact 0..1 next_contact
        report 0..1 Component: 1 of the 5 Report Types
    """

    names = ("event_sitrep",
             "event_sitrep_id",
             )

    def model(self):

        T = current.T
        settings = current.deployment_settings
        sitrep_dynamic = settings.get_event_sitrep_dynamic()
        sitrep_edxl = settings.get_event_sitrep_edxl()
        use_incidents = settings.get_event_incident()

        # ---------------------------------------------------------------------
        # Situation Reports
        # - @ToDo: aggregate by OU (ARC)
        #

        #version_opts = OrderedDict([
        #    ("Initial", T("Initial")),
        #    ("Update", T("Update")),
        #    ("Final", T("Final")),
        #    ])

        #phase_opts = OrderedDict([
        #    ("Preparedness", T("Preparedness")),
        #    ("Response", T("Response")),
        #    ("Mitigation", T("Mitigation")),
        #    ("Recovery", T("Recovery")),
        #    ])

        #urgency_opts = OrderedDict([
        #    ("Immediate", T("Immediate - Response action should be taken immediately")),
        #    ("Expected", T("Expected - Response action should be taken soon (within next hour)")),
        #    ("Future", T("Future - Responsive action should be taken in the near future")),
        #    ("Past", T("Past - Responsive action is no longer required")),
        #    ("Unknown", T("Unknown")),
        #    ])

        #confidence_opts = OrderedDict([
        #    ("HighlyConfident", T("Highly Confident")),
        #    ("SomewhatConfident", T("Somewhat Confident")),
        #    ("Unsure", T("Unsure")),
        #    ("NoConfidence", T("No Confidence")),
        #    ])

        #severity_opts = OrderedDict([
        #    ("Extreme", T("Extreme - Extraordinary threat to life or property")),
        #    ("Severe", T("Severe - Significant threat to life or property")),
        #    ("Moderate", T("Moderate - Possible threat to life or property")),
        #    ("Minor", T("Minor - Minimal to no known threat to life or property")),
        #    ("Unknown", T("Severity unknown")),
        #    ])

        tablename = "event_sitrep"
        self.define_table(tablename,
                          self.super_link("doc_id", "doc_entity"),
                          self.event_event_id(ondelete = "CASCADE"),
                          self.event_incident_id(ondelete = "CASCADE",
                                                 readable = use_incidents,
                                                 writable = use_incidents,
                                                 ),
                          #Field("phase", "integer",
                          #      label = T("Incident Lifecycle Phase"),
                          #      represent = S3Represent(options = phase_opts),
                          #      requires = IS_EMPTY_OR(
                          #                  IS_IN_SET(phase_opts)
                          #                  ),
                          #      readable = sitrep_edxl,
                          #      writable = sitrep_edxl,
                          #      ),
                          Field("number", "integer",
                                label = T("Number"),
                                requires = IS_INT_IN_RANGE(1, None),
                                ),
                          Field("name", length=128,
                                label = T("Title"),
                                requires = IS_LENGTH(128),
                                ),
                          #Field("version", length=16,
                          #      label = T("Version"),
                          #      represent = S3Represent(options = version_opts),
                          #      requires = IS_IN_SET(version_opts) if sitrep_edxl else IS_EMPTY_OR(IS_IN_SET(version_opts)),
                          #      readable = sitrep_edxl,
                          #      writable = sitrep_edxl,
                          #      ),
                          #Field("purpose", "text",
                          #      label = T("Purpose"),
                          #      #represent = lambda body: XML(body),
                          #      #widget = s3_richtext_widget,
                          #      widget = s3_comments_widget,
                          #      readable = sitrep_edxl,
                          #      writable = sitrep_edxl,
                          #      ),
                          self.org_organisation_id(
                                #readable = not sitrep_edxl,
                                #writable = not sitrep_edxl,
                                ),
                          self.gis_location_id(
                            widget = S3LocationSelector(show_map = False,
                                                        show_postcode = False,
                                                        ),
                            ),
                          #Field("action_plan", "text",
                          #      label = T("Action Plan"),
                          #      #represent = lambda body: XML(body),
                          #      #widget = s3_richtext_widget,
                          #      widget = s3_comments_widget,
                          #      readable = sitrep_edxl,
                          #      writable = sitrep_edxl,
                          #      ),
                          #Field("urgency", length=16,
                          #      label = T("Urgency"),
                          #      represent = S3Represent(options = urgency_opts),
                          #      requires = IS_EMPTY_OR(
                          #                  IS_IN_SET(urgency_opts)
                          #                  ),
                          #      readable = sitrep_edxl,
                          #      writable = sitrep_edxl,
                          #      ),
                          #Field("Confidence", length=16,
                          #      label = T("Confidence"),
                          #      represent = S3Represent(options = confidence_opts),
                          #      requires = IS_IN_SET(confidence_opts) if sitrep_edxl else IS_EMPTY_OR(IS_IN_SET(confidence_opts)),
                          #      readable = sitrep_edxl,
                          #      writable = sitrep_edxl,
                          #      ),
                          #Field("severity", length=16,
                          #      label = T("Severity"),
                          #      represent = S3Represent(options = severity_opts),
                          #      requires = IS_IN_SET(severity_opts) if sitrep_edxl else IS_EMPTY_OR(IS_IN_SET(severity_opts)),
                          #      readable = sitrep_edxl,
                          #      writable = sitrep_edxl,
                          #      ),
                          s3_datetime(default = "now",
                                      represent = "date",
                                      widget = "date",
                                      #set_min = "#event_sitrep_end_date",
                                      ),
                          #s3_datetime("end_date",
                          #            label = T("End Date"),
                          #            represent = "date",
                          #            widget = "date",
                          #            set_max = "#event_sitrep_date",
                          #            readable = sitrep_edxl,
                          #            writable = sitrep_edxl,
                          #            ),
                          #s3_datetime("approved_on",
                          #            readable = sitrep_edxl,
                          #            writable = False,
                          #            ),
                          #s3_datetime("next_contact",
                          #            readable = sitrep_edxl,
                          #            writable = sitrep_edxl,
                          #            ),
                          self.dc_template_id(readable = sitrep_dynamic,
                                              writable = sitrep_dynamic,
                                              ),
                          s3_comments("summary",
                                      comment = None,
                                      label = T("Summary"),
                                      #readable = not sitrep_edxl,
                                      #writable = not sitrep_edxl,
                                      widget = s3_richtext_widget,
                                      ),
                          s3_comments(#readable = not sitrep_edxl,
                                      #writable = not sitrep_edxl,
                                      ),
                          *s3_meta_fields())

        # CRUD strings
        current.response.s3.crud_strings[tablename] = Storage(
                label_create = T("Add Situation Report"),
                title_display = T("Situation Report Details"),
                title_list = T("Situation Reports"),
                title_update = T("Edit Situation Report"),
                title_upload = T("Import Situation Reports"),
                label_list_button = T("List Situation Reports"),
                label_delete_button = T("Delete Situation Report"),
                msg_record_created = T("Situation Report added"),
                msg_record_modified = T("Situation Report updated"),
                msg_record_deleted = T("Situation Report deleted"),
                msg_list_empty = T("No Situation Reports currently registered"))

        if sitrep_edxl:
            # All writable fields
            crud_form = None
        else:
            crud_form = S3SQLCustomForm("event_id",
                                        "incident_id",
                                        "number",
                                        "name",
                                        "organisation_id",
                                        "location_id",
                                        "date",
                                        "summary",
                                        S3SQLInlineComponent(
                                            "document",
                                            name = "document",
                                            label = T("Attachments"),
                                            fields = [("", "file")],
                                        ),
                                        "comments",
                                        )

        list_fields = ["date",
                       "event_id",
                       "location_id$L1",
                       "location_id$L2",
                       "location_id$L3",
                       "organisation_id",
                       "number",
                       "name",
                       "summary",
                       (T("Attachments"), "document.file"),
                       ]
        if use_incidents:
            list_fields.insert(2, "incident_id")

        if sitrep_edxl:
            org_filter = None
        elif settings.get_org_branches():
            org_filter = S3HierarchyFilter("organisation_id",
                                           leafonly = False,
                                           )
        else:
            org_filter = S3OptionsFilter("organisation_id",
                                         #filter = True,
                                         #header = "",
                                         )

        filter_widgets = [S3OptionsFilter("event_id"),
                          org_filter,
                          S3LocationFilter(),
                          S3DateFilter("date"),
                          ]
        if use_incidents:
            filter_widgets.insert(1, S3OptionsFilter("incident_id"))

        self.configure(tablename,
                       crud_form = crud_form,
                       # Question Answers are in a Dynamic Component
                       # - however they all have the same component name so add correct one in controller instead!
                       #dynamic_components = True,
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       orderby = "event_sitrep.date desc",
                       super_entity = "doc_entity",
                       )

        # Components
        #self.add_components(tablename,
        #                    )

        represent = S3Represent(lookup=tablename)

        sitrep_id = S3ReusableField("sitrep_id", "reference %s" % tablename,
                                    label = T("Situation Report"),
                                    ondelete = "RESTRICT",
                                    represent = represent,
                                    requires = IS_EMPTY_OR(
                                                IS_ONE_OF(current.db, "event_sitrep.id",
                                                          represent,
                                                          orderby="event_sitrep.name",
                                                          sort=True,
                                                          )),
                                    sortby = "name",
                                    )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"event_sitrep_id": sitrep_id,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """
            Return safe defaults in case the model has been deactivated.
        """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False)

        return {"event_sitrep_id": lambda **attr: dummy("sitrep_id"),
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def event_sitrep_create_onaccept(form):
        """
            On-accept routine for event_sitrep:
                - Create & link a Dynamic Table to use to store the Questions
        """

        form_vars = form.vars
        try:
            sitrep_id = form_vars.id
        except AttributeError:
            return

        # Create the Dynamic Table
        #settings = current.deployment_settings
        #mobile_data = settings.get_dc_mobile_data()
        #if settings.get_dc_mobile_inserts():
        #    table_settings = "" # Default
        #else:
        #    table_settings = {"insertable": False}

        table_id = current.s3db.s3_table.insert(title = form_vars.get("name"),
                                                mobile_form = False, # Setting for SCPHIMS, deployment_setting if this needs changing for other contexts
                                                #mobile_data = mobile_data, # False by default
                                                #settings = table_settings,
                                                )

        # Add a Field to link Answers together
        db = current.db
        db.s3_field.insert(table_id = table_id,
                           name = "sitrep_id",
                           field_type = "reference event_sitrep",
                           #label = "Response",
                           require_not_empty = True,
                           component_key = True,
                           component_alias = "answer",
                           component_tab = True,
                           master = "dc_response",
                           settings = {"component_multiple": False},
                           )
        # @ToDo: Call onaccept if this starts doing anything other than just setting 'master'
        # @ToDo: Call set_record_owner() once we start restricting these

        # Link this Table to the Template
        db(db.event_sitrep.id == sitrep_id).update(table_id=table_id)

# =============================================================================
class S3EventTaskModel(S3Model):
    """
        Link Tasks to Incidents &/or Events
        - normally linked at the Incident level & just visible at the Event level
    """

    names = ("event_task",
             )

    def model(self):

        T = current.T

        if current.deployment_settings.get_event_cascade_delete_incidents():
            ondelete = "CASCADE"
        else:
            ondelete = "SET NULL"

        # ---------------------------------------------------------------------
        # Tasks
        # Tasks are to be assigned to resources managed by this EOC
        # - we manage in detail
        # @ToDo: Task Templates

        tablename = "event_task"
        self.define_table(tablename,
                          self.event_event_id(ondelete = ondelete,
                                              ),
                          self.event_incident_id(ondelete = "CASCADE",
                                                 ),
                          self.project_task_id(empty = False,
                                               ondelete = "CASCADE",
                                               ),
                          *s3_meta_fields())

        # Not used as we actuate = replace, although the
        # msg_list_empty is used by the ActionPlan
        current.response.s3.crud_strings[tablename] = Storage(
        #    label_create = T("Create Task"),
        #    title_display = T("Task Details"),
        #    title_list = T("Tasks"),
        #    title_update = T("Edit Task"),
        #    label_list_button = T("List Tasks"),
        #    label_delete_button = T("Remove Task from this incident"),
        #    msg_record_created = T("Task added"),
        #    msg_record_modified = T("Task updated"),
        #    msg_record_deleted = T("Task removed"),
            msg_list_empty = T("No Tasks currently registered for this incident"))

        self.configure(tablename,
                       context = {"incident": "incident_id",
                                  },
                       deduplicate = S3Duplicate(primary = ("event_id",
                                                            "incident_id",
                                                            "task_id",
                                                            ),
                                                 ),
                       onaccept = lambda form: \
                                set_event_from_incident(form, "event_task"),
                       )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
def set_event_from_incident(form, tablename):
    """
        Populate event_id from incident if set.
    """

    try:
        form_vars = form.vars
        record_id = form_vars.id
    except KeyError:
        return
    if not record_id:
        return

    db = current.db
    s3db = current.s3db

    table = s3db.table(tablename)

    # Make sure we have the incident_id
    if "incident_id" not in form_vars:
        record = db(table.id == record_id).select(table.id,
                                                  table.incident_id,
                                                  limitby=(0, 1)
                                                  ).first()
        if not record:
            return
    else:
        record = form_vars

    # If incident_id is set then use this to set the event_id
    if record.incident_id:
        itable = s3db.event_incident
        incident = db(itable.id == record.incident_id).select(itable.event_id,
                                                              limitby=(0, 1)
                                                              ).first()
        if incident:
            db(table.id == record_id).update(event_id = incident.event_id)

# Alias
event_set_event_from_incident = set_event_from_incident
# =============================================================================
# Custom Resource Methods

# =============================================================================
class event_ActionPlan(S3Method):
    """
        Custom profile page with multiple DataTables:
            * Tasks
            * People
            * Assets
    """

    def __init__(self, form=None):
        """
            Constructor

            @param form: widget config to inject at the top of the page,
                         or a callable to produce such a widget config
        """

        self.form = form

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Entry point for REST API

            @param r: the S3Request
            @param attr: controller arguments
        """

        if r.name == "incident" and \
           r.id and \
           not r.component and \
           r.representation in ("html", "aadata"):

            T = current.T
            s3db = current.s3db
            get_config = s3db.get_config
            #settings = current.deployment_settings

            def dt_row_actions(component, tablename):
                def row_actions(r, list_id):
                    editable = get_config(tablename, "editable")
                    if editable is None:
                        editable = True
                    deletable = get_config(tablename, "deletable")
                    if deletable is None:
                        deletable = True
                    if editable:
                        actions = [{"label": T("Open"),
                                    "url": r.url(component=component,
                                                 component_id="[id]",
                                                 method="update.popup",
                                                 vars={"refresh": list_id}),
                                    "_class": "action-btn edit s3_modal",
                                    },
                                   ]
                    else:
                        actions = [{"label": T("Open"),
                                    "url": r.url(component=component,
                                                 component_id="[id]",
                                                 method="read.popup",
                                                 vars={"refresh": list_id}),
                                    "_class": "action-btn edit s3_modal",
                                    },
                                   ]
                    if deletable:
                        actions.append({"label": T("Delete"),
                                        "_ajaxurl": r.url(component=component,
                                                          component_id="[id]",
                                                          method="delete.json",
                                                          ),
                                        "_class": "action-btn delete-btn-ajax dt-ajax-delete",
                                        })
                    return actions
                return row_actions

            def dt_row_actions_task():
                def row_actions(r, list_id):
                    editable = get_config("project_task", "editable")
                    if editable is None:
                        editable = True
                    deletable = get_config("event_task", "deletable")
                    if deletable is None:
                        deletable = True
                    if editable:
                        actions = [{"label": T("Open"),
                                    "url": URL(c="project",
                                               f="task",
                                               args="update.popup",
                                               vars={"incident.id": "[id]",
                                                     "refresh": list_id,
                                                     },
                                               ),
                                    "_class": "action-btn edit s3_modal",
                                    },
                                   ]
                    else:
                        actions = [{"label": T("Open"),
                                    "url": URL(c="project",
                                               f="task",
                                               args="read.popup",
                                               vars={"incident.id": "[id]",
                                                     "refresh": list_id,
                                                     },
                                               ),
                                    "_class": "action-btn edit s3_modal",
                                    },
                                   ]
                    if deletable:
                        actions.append({"label": T("Delete"),
                                        "_ajaxurl": r.url(component="incident_task",
                                                          component_id="[id]",
                                                          method="delete.json",
                                                          ),
                                        "_class": "action-btn delete-btn-ajax dt-ajax-delete",
                                        })
                    return actions
                return row_actions

            profile_widgets = []
            form = self.form
            if form:
                if callable(form):
                    form = form(r)
                if form is not None:
                    profile_widgets.append(form)

            tablename = "event_task"
            widget = {"label": "Tasks",
                      "label_create": "Add Task",
                      "type": "datatable",
                      "actions": dt_row_actions_task(),
                      "tablename": tablename,
                      "context": "incident",
                      "create_controller": "event",
                      "create_function": "incident",
                      "create_component": "task",
                      #"pagesize": None, # all records
                      "list_fields": ["task_id$priority",
                                      "task_id$name",
                                      "task_id$pe_id",
                                      "task_id$status",
                                      "task_id$date_due",
                                      ],

                      }
            profile_widgets.append(widget)

            tablename = "event_human_resource"
            s3db.event_human_resource.person_id.represent = s3db.pr_PersonRepresentContact()
            r.customise_resource(tablename)
            widget = {# Use CRUD Strings (easier to customise)
                      #"label": "Human Resources",
                      #"label_create": "Add Human Resource",
                      "type": "datatable",
                      "actions": dt_row_actions("human_resource", tablename),
                      "tablename": tablename,
                      "context": "incident",
                      "create_controller": "event",
                      "create_function": "incident",
                      "create_component": "human_resource",
                      #"pagesize": None, # all records
                      }
            profile_widgets.append(widget)

            tablename = "event_asset"
            r.customise_resource(tablename)
            widget = {# Use CRUD Strings (easier to customise)
                      #"label": "Equipment",
                      #"label_create": "Add Equipment",
                      "type": "datatable",
                      "actions": dt_row_actions("incident_asset", tablename),
                      "tablename": tablename,
                      "context": "incident",
                      "create_controller": "event",
                      "create_function": "incident",
                      "create_component": "asset",
                      #"pagesize": None, # all records
                      "list_fields": ["item_id",
                                      "asset_id",
                                      "status",
                                      "start_date",
                                      "end_date",
                                      ],
                      }
            profile_widgets.append(widget)

            tablename = r.tablename

            if r.representation == "html":
                html = True
                response = current.response
                s3 = response.s3
                # Maintain normal rheader for consistency
                rheader = attr["rheader"]
                profile_header = TAG[""](H2(s3.crud_strings["event_incident"].title_display),
                                         DIV(rheader(r), _id="rheader"),
                                         )
            else:
                html = False
                profile_header = None

            s3db.configure(tablename,
                           profile_cols = 1,
                           profile_header = profile_header,
                           profile_widgets = profile_widgets,
                           )

            profile = S3Profile()
            profile.tablename = tablename
            profile.request = r
            output = profile.profile(r, **attr)
            if html:
                output["title"] = response.title = T("Action Plan")
                # Refresh page every 15 seconds
                s3.jquery_ready.append('''
function timedRefresh(timeoutPeriod){
 setTimeout("location.reload(true);",timeoutPeriod);
}
window.onload = timedRefresh(15000);''')
            return output

        else:
            r.error(405, current.ERROR.BAD_METHOD)

# =============================================================================
class event_ScenarioActionPlan(S3Method):
    """
        Custom profile page with multiple DataTables:
            * Tasks
            * People
            * Assets
    """

    def __init__(self, form=None):
        """
            Constructor

            @param form: widget config to inject at the top of the page,
                         or a callable to produce such a widget config
        """

        self.form = form

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Entry point for REST API

            @param r: the S3Request
            @param attr: controller arguments
        """

        if r.name == "scenario" and \
           r.id and \
           not r.component and \
           r.representation in ("html", "aadata"):

            T = current.T
            s3db = current.s3db
            get_config = s3db.get_config
            #settings = current.deployment_settings

            def dt_row_actions(component, tablename):
                def row_actions(r, list_id):
                    editable = get_config(tablename, "editable")
                    if editable is None:
                        editable = True
                    deletable = get_config(tablename, "deletable")
                    if deletable is None:
                        deletable = True
                    if editable:
                        actions = [{"label": T("Open"),
                                    "url": r.url(component=component,
                                                 component_id="[id]",
                                                 method="update.popup",
                                                 vars={"refresh": list_id}),
                                    "_class": "action-btn edit s3_modal",
                                    },
                                   ]
                    else:
                        actions = [{"label": T("Open"),
                                    "url": r.url(component=component,
                                                 component_id="[id]",
                                                 method="read.popup",
                                                 vars={"refresh": list_id}),
                                    "_class": "action-btn edit s3_modal",
                                    },
                                   ]
                    if deletable:
                        actions.append({"label": T("Delete"),
                                        "_ajaxurl": r.url(component=component,
                                                          component_id="[id]",
                                                          method="delete.json",
                                                          ),
                                        "_class": "action-btn delete-btn-ajax dt-ajax-delete",
                                        })
                    return actions
                return row_actions

            def dt_row_actions_task():
                def row_actions(r, list_id):
                    editable = get_config("project_task", "editable")
                    if editable is None:
                        editable = True
                    deletable = get_config("event_scenario_task", "deletable")
                    if deletable is None:
                        deletable = True
                    if editable:
                        actions = [{"label": T("Open"),
                                    "url": URL(c="project",
                                               f="task",
                                               args="update.popup",
                                               vars={"scenario.id": "[id]",
                                                     "refresh": list_id,
                                                     },
                                               ),
                                    "_class": "action-btn edit s3_modal",
                                    },
                                   ]
                    else:
                        actions = [{"label": T("Open"),
                                    "url": URL(c="project",
                                               f="task",
                                               args="read.popup",
                                               vars={"scenario.id": "[id]",
                                                     "refresh": list_id,
                                                     },
                                               ),
                                    "_class": "action-btn edit s3_modal",
                                    },
                                   ]
                    if deletable:
                        actions.append({"label": T("Delete"),
                                        "_ajaxurl": r.url(component="scenario_task",
                                                          component_id="[id]",
                                                          method="delete.json",
                                                          ),
                                        "_class": "action-btn delete-btn-ajax dt-ajax-delete",
                                        })
                    return actions
                return row_actions

            profile_widgets = []
            form = self.form
            if form:
                if callable(form):
                    form = form(r)
                if form is not None:
                    profile_widgets.append(form)

            tablename = "event_scenario_task"
            widget = {"label": "Tasks",
                      "label_create": "Add Task",
                      "type": "datatable",
                      "actions": dt_row_actions_task(),
                      "tablename": tablename,
                      "context": "scenario",
                      "create_controller": "event",
                      "create_function": "scenario",
                      "create_component": "task",
                      #"pagesize": None, # all records
                      "list_fields": ["task_id$priority",
                                      "task_id$name",
                                      #"task_id$status",
                                      #"task_id$date_due",
                                      "task_id$comments",
                                      ],

                      }
            profile_widgets.append(widget)

            tablename = "event_scenario_human_resource"
            widget = dict(# Use CRUD Strings (easier to customise)
                          #label = "Human Resources",
                          #label_create = "Add Human Resource",
                          type = "datatable",
                          actions = dt_row_actions("human_resource", tablename),
                          tablename = tablename,
                          context = "scenario",
                          create_controller = "event",
                          create_function = "scenario",
                          create_component = "human_resource",
                          #pagesize = None, # all records
                          list_fields = ["job_title_id",
                                         "person_id",
                                         #"start_date",
                                         #"end_date",
                                         "comments",
                                         ],
                          )
            profile_widgets.append(widget)

            tablename = "event_scenario_asset"
            r.customise_resource(tablename)
            widget = dict(# Use CRUD Strings (easier to customise)
                          #label = "Equipment",
                          #label_create = "Add Equipment",
                          type = "datatable",
                          actions = dt_row_actions("scenario_asset", tablename),
                          tablename = tablename,
                          context = "scenario",
                          create_controller = "event",
                          create_function = "scenario",
                          create_component = "asset",
                          #pagesize = None, # all records
                          list_fields = ["item_id",
                                         "asset_id",
                                         #"start_date",
                                         #"end_date",
                                         "comments",
                                         ],
                          )
            profile_widgets.append(widget)

            tablename = r.tablename

            if r.representation == "html":
                response = current.response
                # Maintain normal rheader for consistency
                rheader = attr["rheader"]
                profile_header = TAG[""](H2(response.s3.crud_strings["event_scenario"].title_display),
                                         DIV(rheader(r), _id="rheader"),
                                         )
            else:
                profile_header = None

            s3db.configure(tablename,
                           profile_cols = 1,
                           profile_header = profile_header,
                           profile_widgets = profile_widgets,
                           )

            profile = S3Profile()
            profile.tablename = tablename
            profile.request = r
            output = profile.profile(r, **attr)
            if r.representation == "html":
                output["title"] = response.title = T("Action Plan")
            return output

        else:
            r.error(405, current.ERROR.BAD_METHOD)

# =============================================================================
class event_ApplyScenario(S3Method):
    """
        Populate an Incident with a Scenario's:
            * Tasks
            * People
            * Equipment
    """

    def __init__(self, form=None):
        """
            Constructor

            @param form: widget config to inject at the top of the page,
                         or a callable to produce such a widget config
        """

        self.form = form

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Entry point for REST API

            @param r: the S3Request
            @param attr: controller arguments
        """

        if r.http != "POST":
            r.error(405, current.ERROR.BAD_METHOD)

        incident_id = r.id
        scenario_id = r.post_vars.get("scenario_id")
        if not incident_id or not scenario_id:
            r.error(405, current.ERROR.BAD_METHOD)

        db = current.db
        s3db = current.s3db

        # Tasks
        ttable = s3db.project_task
        sltable = s3db.event_scenario_task
        query = (sltable.scenario_id == scenario_id) & \
                (sltable.task_id == ttable.id)
        tasks = db(query).select(ttable.name,
                                 ttable.pe_id,
                                 ttable.priority,
                                 ttable.comments,
                                 )
        if len(tasks):
            iltable = s3db.event_task
            tinsert = ttable.insert
            linsert = iltable.insert
            r.customise_resource("project_task")
            onaccept = s3db.get_config("project_task", "create_onaccept")
            for t in tasks:
                record = {"name" : t.name,
                          "pe_id" : t.pe_id,
                          "priority" : t.priority,
                          "comments" : t.comments,
                          }
                task_id = tinsert(**record)
                record["id"] = task_id
                linsert(incident_id = incident_id,
                        task_id = task_id,
                        )
                if onaccept:
                    form = Storage(vars = record)
                    # Execute onaccept
                    from gluon.tools import callback
                    try:
                        callback(onaccept, form, tablename="project_task")
                    except:
                        error = "onaccept failed: %s" % str(onaccept)
                        current.log.error(error)
                        raise

        # Human Resources
        sltable = s3db.event_scenario_human_resource
        query = (sltable.scenario_id == scenario_id)
        hrs = db(query).select(sltable.job_title_id,
                               sltable.person_id,
                               sltable.comments,
                               )
        if len(hrs):
            iltable = s3db.event_human_resource
            linsert = iltable.insert
            for h in hrs:
                linsert(incident_id = incident_id,
                        job_title_id = h.job_title_id,
                        person_id = h.person_id,
                        comments = h.comments,
                        )

        # Equipment
        sltable = s3db.event_scenario_asset
        query = (sltable.scenario_id == scenario_id)
        assets = db(query).select(sltable.item_id,
                                  sltable.asset_id,
                                  sltable.comments,
                                  )
        if len(assets):
            iltable = s3db.event_asset
            linsert = iltable.insert
            for a in assets:
                linsert(incident_id = incident_id,
                        item_id = a.item_id,
                        asset_id = a.asset_id,
                        comments = a.comments,
                        )

        output = current.xml.json_message(True, 200, current.T("Scenario Applied"))
        current.response.headers["Content-Type"] = "application/json"
        return output

# =============================================================================
class event_EventAssignMethod(S3Method):
    """
        Custom Method to allow things to be assigned to an Event
        e.g. Incident
    """

    def __init__(self, component=None, next_tab=None
                 ):
        """
            @param component: the Component in which to create records
            @param next_tab: the component/method to redirect to after assigning
        """

        self.component = component
        if next_tab:
            self.next_tab = next_tab
        else:
            self.next_tab = component

    def apply_method(self, r, **attr):
        """
            Apply method.

            @param r: the S3Request
            @param attr: controller options for this request
        """

        if self.component:
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

        else:
            component = None
            record_id = r.id
            resource = r.resource
            tablename = resource.tablename
            # Requires permission to update record
            authorised = current.auth.s3_has_permission("update", tablename, record_id)
            if not authorised:
                r.unauthorised()

        #settings = current.deployment_settings

        T = current.T
        db = current.db
        s3db = current.s3db

        table = s3db[tablename]
        if component:
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
                    eresource = s3db.resource("event_event",
                                              alias = self.component,
                                              filter=query, vars=filters)
                    rows = eresource.select(["id"], as_rows=True)
                    selected = [str(row.id) for row in rows]

                if component:
                    # Prevent multiple entries in the link table
                    query = (table.event_id.belongs(selected)) & \
                            (table[fkey] == record_id) & \
                            (table.deleted != True)
                    rows = db(query).select(table.id)
                    rows = dict((row.id, row) for row in rows)
                    onaccept = component.get_config("create_onaccept",
                                                    component.get_config("onaccept", None))
                else:
                    onaccept = resource.get_config("update_onaccept",
                                                   resource.get_config("onaccept", None))
                for event_id in selected:
                    try:
                        e_id = int(event_id.strip())
                    except ValueError:
                        continue
                    if component and e_id not in rows:
                        link = Storage(event_id = event_id)
                        link[fkey] = record_id
                        _id = table.insert(**link)
                        if onaccept:
                            link["id"] = _id
                            form = Storage(vars=link)
                            onaccept(form)
                        added += 1
                    else:
                        db(table.id == record_id).update(event_id = event_id)
                        if onaccept:
                            form = Storage(vars = r.record)
                            onaccept(form)
                        added -= 1

            if r.representation == "popup":
                # Don't redirect, so we retain popup extension & so close popup
                response.confirmation = T("%(number)s assigned") % \
                                            {"number": added}
                return {}
            else:
                if added < 0:
                    # No component
                    response.confirmation = T("Assigned")
                    redirect(URL(r.controller, r.function,
                                 args=r.id, vars={}))
                current.session.confirmation = T("%(number)s assigned") % \
                                                    {"number": added}
                if added > 0:
                    redirect(URL(args=[r.id, self.next_tab], vars={}))
                else:
                    redirect(URL(args=r.args, vars={}))

        elif r.http == "GET":

            # Filter widgets
            location_defaults = {}
            if tablename == "event_incident":
                location_id = r.record.location_id
                if location_id:
                    gtable = s3db.gis_location
                    location = db(gtable.id == location_id).select(gtable.level,
                                                                   gtable.name,
                                                                   gtable.parent,
                                                                   limitby = (0, 1),
                                                                   ).first()
                    level = location.level
                    if level:
                        location_defaults["event_location.location_id$%s__belongs" % level] = location.name
                    parent = location.parent
                    if parent:
                        location = db(gtable.id == parent).select(gtable.level,
                                                                  gtable.name,
                                                                  gtable.parent,
                                                                  limitby = (0, 1),
                                                                  ).first()
                        location_defaults["event_location.location_id$%s__belongs" % location.level] = location.name
                        parent = location.parent
                        if parent:
                            location = db(gtable.id == parent).select(gtable.level,
                                                                      gtable.name,
                                                                      gtable.parent,
                                                                      limitby = (0, 1),
                                                                      ).first()
                            location_defaults["event_location.location_id$%s__belongs" % location.level] = location.name
                            parent = location.parent
                            if parent:
                                location = db(gtable.id == parent).select(gtable.level,
                                                                          gtable.name,
                                                                          gtable.parent,
                                                                          limitby = (0, 1),
                                                                          ).first()
                                location_defaults["event_location.location_id$%s__belongs" % location.level] = location.name
                                parent = location.parent
                                if parent:
                                    location = db(gtable.id == parent).select(gtable.level,
                                                                              gtable.name,
                                                                              gtable.parent,
                                                                              limitby = (0, 1),
                                                                              ).first()
                                    location_defaults["event_location.location_id$%s__belongs" % location.level] = location.name
                                    parent = location.parent
                                    if parent:
                                        location = db(gtable.id == parent).select(gtable.level,
                                                                                  gtable.name,
                                                                                  gtable.parent,
                                                                                  limitby = (0, 1),
                                                                                  ).first()
                                        location_defaults["location.location_id$%s__belongs" % location.level] = location.name

            # Which levels of Hierarchy are we using?
            levels = current.gis.get_relevant_hierarchy_levels()

            filter_widgets = [S3LocationFilter("event_location.location_id",
                                               default = location_defaults,
                                               levels = levels,
                                               label = T("Location"),
                                               ),
                              # @ToDo: Filter for events which are open within a date range
                              #S3DateFilter("start_date",
                              #             label = None,
                              #             hide_time = True,
                              #             input_labels = {"ge": "From", "le": "To"}
                              #             ),
                              S3OptionsFilter("closed",
                                              label = T("Status"),
                                              options = OrderedDict([(False, T("Open")),
                                                                     (True, T("Closed")),
                                                                     ]),
                                              cols = 2,
                                              default = False,
                                              sort = False,
                                              ),
                              ]

            # List fields
            list_fields = ["id",
                           "name",
                           "start_date",
                           "event_location.location_id",
                           ]

            # Data table
            resource = s3db.resource("event_event",
                                     alias=r.component.alias if r.component else None,
                                     vars=get_vars)
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

            if component:
                # Hide incidents already in the link table
                etable = db.event_event
                query = (table[fkey] == record_id) & \
                        (table.deleted != True)
                rows = db(query).select(table.event_id)
                already = [row.event_id for row in rows]
                filter_ = (~etable.id.belongs(already))
                resource.add_filter(filter_)

            # Allow customise_ to influence
            #s3 = response.s3
            #if s3.filter:
            #    resource.add_filter(s3.filter)

            dt_id = "datatable"

            # Bulk actions
            dt_bulk_actions = [(T("Assign"), "assign")]

            if r.representation in ("html", "popup"):
                # Page load
                resource.configure(deletable = False)

                profile_url = URL(c = "event",
                                  f = "event",
                                  # @ToDo: Popup (add class="s3_modal"
                                  #args = ["[id]", "profile.popup"])
                                  args = ["[id]", "profile"])
                S3CRUD.action_buttons(r,
                                      deletable = False,
                                      read_url = profile_url,
                                      update_url = profile_url)
                response.s3.no_formats = True

                # Filter form
                if filter_widgets:

                    # Where to retrieve filtered data from:
                    submit_url_vars = resource.crud._remove_filters(r.get_vars)
                    filter_submit_url = r.url(vars=submit_url_vars)

                    # Default Filters (before selecting data!)
                    resource.configure(filter_widgets=filter_widgets)
                    # @ToDo: This is currently not working
                    # - filter shows this option, but the resource isn't filtered
                    #S3FilterForm.apply_filter_defaults(r, resource)

                    # Where to retrieve updated filter options from:
                    filter_ajax_url = URL(c = "event",
                                          f = "event",
                                          args=["filter.options"],
                                          vars={})

                    get_config = resource.get_config
                    filter_clear = get_config("filter_clear", True)
                    filter_formstyle = get_config("filter_formstyle", None)
                    filter_submit = get_config("filter_submit", True)
                    filter_form = S3FilterForm(filter_widgets,
                                               clear=filter_clear,
                                               formstyle=filter_formstyle,
                                               submit=filter_submit,
                                               ajax=True,
                                               url=filter_submit_url,
                                               ajaxurl=filter_ajax_url,
                                               _class="filter-form",
                                               _id="datatable-filter-form",
                                               )
                    fresource = current.s3db.resource(resource.tablename)
                    alias = r.component.alias if r.component else None
                    ff = filter_form.html(fresource,
                                          r.get_vars,
                                          target="datatable",
                                          alias=alias)
                else:
                    ff = ""

                # Data table (items)
                data = resource.select(list_fields,
                                       start=0,
                                       limit=limit,
                                       orderby=orderby,
                                       left=left,
                                       count=True,
                                       represent=True)
                filteredrows = data["numrows"]
                dt = S3DataTable(data["rfields"], data["rows"])

                items = dt.html(totalrows,
                                filteredrows,
                                dt_id,
                                dt_ajax_url=r.url(representation="aadata"),
                                dt_bulk_actions=dt_bulk_actions,
                                dt_pageLength=display_length,
                                dt_pagination="true",
                                dt_searching="false",
                                )

                response.view = "list_filter.html"

                return {"items": items,
                        "title": T("Assign to Event"),
                        "list_filter_form": ff,
                        }

            elif r.representation == "aadata":
                # Ajax refresh
                if "draw" in get_vars:
                    echo = int(get_vars.draw)
                else:
                    echo = None

                data = resource.select(list_fields,
                                       start=0,
                                       limit=limit,
                                       orderby=orderby,
                                       left=left,
                                       count=True,
                                       represent=True)
                filteredrows = data["numrows"]
                dt = S3DataTable(data["rfields"], data["rows"])

                items = dt.json(totalrows,
                                filteredrows,
                                dt_id,
                                echo,
                                dt_bulk_actions=dt_bulk_actions)
                response.headers["Content-Type"] = "application/json"
                return items

            else:
                r.error(415, current.ERROR.BAD_FORMAT)
        else:
            r.error(405, current.ERROR.BAD_METHOD)

# =============================================================================
class event_IncidentAssignMethod(S3Method):
    """
        Custom Method to allow things to be assigned to an Incident
        e.g. Incident Report
    """

    def __init__(self, component, next_tab=None
                 ):
        """
            @param component: the Component in which to create records
            @param next_tab: the component/method to redirect to after assigning
        """

        self.component = component
        if next_tab:
            self.next_tab = next_tab
        else:
            self.next_tab = component

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
                    iresource = s3db.resource("event_incident",
                                              alias = self.component,
                                              filter=query, vars=filters)
                    rows = iresource.select(["id"], as_rows=True)
                    selected = [str(row.id) for row in rows]

                # Prevent multiple entries in the link table
                query = (table.incident_id.belongs(selected)) & \
                        (table[fkey] == record_id) & \
                        (table.deleted != True)
                rows = db(query).select(table.id)
                rows = dict((row.id, row) for row in rows)
                onaccept = component.get_config("create_onaccept",
                                                component.get_config("onaccept", None))
                for incident_id in selected:
                    try:
                        i_id = int(incident_id.strip())
                    except ValueError:
                        continue
                    if i_id not in rows:
                        link = Storage(incident_id = incident_id)
                        link[fkey] = record_id
                        _id = table.insert(**link)
                        if onaccept:
                            link["id"] = _id
                            form = Storage(vars=link)
                            onaccept(form)
                        added += 1

            if r.representation == "popup":
                # Don't redirect, so we retain popup extension & so close popup
                response.confirmation = T("%(number)s assigned") % \
                                            {"number": added}
                return {}
            else:
                current.session.confirmation = T("%(number)s assigned") % \
                                                    {"number": added}
                if added > 0:
                    redirect(URL(c="event", f="incident",
                                 args=[incident_id, self.next_tab],
                                 vars={},
                                 ))
                else:
                    redirect(URL(args=r.args, vars={}))

        elif r.http == "GET":

            # Filter widgets
            location_defaults = {}
            if tablename == "event_incident_report_incident":
                location_id = r.record.location_id
                if location_id:
                    gtable = s3db.gis_location
                    location = db(gtable.id == location_id).select(gtable.level,
                                                                   gtable.name,
                                                                   gtable.parent,
                                                                   limitby = (0, 1),
                                                                   ).first()
                    level = location.level
                    if level:
                        location_defaults["~.location_id$%s__belongs" % level] = location.name
                    parent = location.parent
                    if parent:
                        location = db(gtable.id == parent).select(gtable.level,
                                                                  gtable.name,
                                                                  gtable.parent,
                                                                  limitby = (0, 1),
                                                                  ).first()
                        location_defaults["~.location_id$%s__belongs" % location.level] = location.name
                        parent = location.parent
                        if parent:
                            location = db(gtable.id == parent).select(gtable.level,
                                                                      gtable.name,
                                                                      gtable.parent,
                                                                      limitby = (0, 1),
                                                                      ).first()
                            location_defaults["~.location_id$%s__belongs" % location.level] = location.name
                            parent = location.parent
                            if parent:
                                location = db(gtable.id == parent).select(gtable.level,
                                                                          gtable.name,
                                                                          gtable.parent,
                                                                          limitby = (0, 1),
                                                                          ).first()
                                location_defaults["~.location_id$%s__belongs" % location.level] = location.name
                                parent = location.parent
                                if parent:
                                    location = db(gtable.id == parent).select(gtable.level,
                                                                              gtable.name,
                                                                              gtable.parent,
                                                                              limitby = (0, 1),
                                                                              ).first()
                                    location_defaults["~.location_id$%s__belongs" % location.level] = location.name
                                    parent = location.parent
                                    if parent:
                                        location = db(gtable.id == parent).select(gtable.level,
                                                                                  gtable.name,
                                                                                  gtable.parent,
                                                                                  limitby = (0, 1),
                                                                                  ).first()
                                        location_defaults["~.location_id$%s__belongs" % location.level] = location.name

            # Which levels of Hierarchy are we using?
            levels = current.gis.get_relevant_hierarchy_levels()

            filter_widgets = [S3LocationFilter("location_id",
                                               default = location_defaults,
                                               levels = levels,
                                               label = T("Location"),
                                               ),
                              # @ToDo: Filter for events which are open within a date range
                              #S3DateFilter("start_date",
                              #             label = None,
                              #             hide_time = True,
                              #             input_labels = {"ge": "From", "le": "To"}
                              #             ),
                              S3OptionsFilter("closed",
                                              label = T("Status"),
                                              options = OrderedDict([(False, T("Open")),
                                                                     (True, T("Closed")),
                                                                     ]),
                                              cols = 2,
                                              default = False,
                                              sort = False,
                                              ),
                              ]

            # List fields
            list_fields = ["id",
                           "name",
                           "date",
                           "location_id",
                           ]

            # Data table
            resource = s3db.resource("event_incident",
                                     alias=r.component.alias if r.component else None,
                                     vars=get_vars)
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

            # Hide incidents already in the link table
            itable = db.event_incident
            query = (table[fkey] == record_id) & \
                    (table.deleted != True)
            rows = db(query).select(table.incident_id)
            already = [row.incident_id for row in rows]
            filter_ = (~itable.id.belongs(already))
            resource.add_filter(filter_)

            # Allow customise_ to influence
            #s3 = response.s3
            #if s3.filter:
            #    resource.add_filter(s3.filter)

            dt_id = "datatable"

            # Bulk actions
            dt_bulk_actions = [(T("Assign"), "assign")]

            if r.representation in ("html", "popup"):
                # Page load
                resource.configure(deletable = False)

                profile_url = URL(c = "event",
                                  f = "incident",
                                  # @ToDo: Popup (add class="s3_modal"
                                  #args = ["[id]", "profile.popup"])
                                  args = ["[id]", "profile"])
                S3CRUD.action_buttons(r,
                                      deletable = False,
                                      read_url = profile_url,
                                      update_url = profile_url)
                response.s3.no_formats = True

                # Filter form
                if filter_widgets:

                    # Where to retrieve filtered data from:
                    submit_url_vars = resource.crud._remove_filters(r.get_vars)
                    filter_submit_url = r.url(vars=submit_url_vars)

                    # Default Filters (before selecting data!)
                    resource.configure(filter_widgets=filter_widgets)
                    S3FilterForm.apply_filter_defaults(r, resource)

                    # Where to retrieve updated filter options from:
                    filter_ajax_url = URL(c = "event",
                                          f = "incident",
                                          args=["filter.options"],
                                          vars={})

                    get_config = resource.get_config
                    filter_clear = get_config("filter_clear", True)
                    filter_formstyle = get_config("filter_formstyle", None)
                    filter_submit = get_config("filter_submit", True)
                    filter_form = S3FilterForm(filter_widgets,
                                               clear=filter_clear,
                                               formstyle=filter_formstyle,
                                               submit=filter_submit,
                                               ajax=True,
                                               url=filter_submit_url,
                                               ajaxurl=filter_ajax_url,
                                               _class="filter-form",
                                               _id="datatable-filter-form",
                                               )
                    fresource = current.s3db.resource(resource.tablename)
                    alias = r.component.alias if r.component else None
                    ff = filter_form.html(fresource,
                                          r.get_vars,
                                          target="datatable",
                                          alias=alias)
                else:
                    ff = ""

                # Data table (items)
                data = resource.select(list_fields,
                                       start=0,
                                       limit=limit,
                                       orderby=orderby,
                                       left=left,
                                       count=True,
                                       represent=True)
                filteredrows = data["numrows"]
                dt = S3DataTable(data["rfields"], data["rows"])

                items = dt.html(totalrows,
                                filteredrows,
                                dt_id,
                                dt_ajax_url=r.url(representation="aadata"),
                                dt_bulk_actions=dt_bulk_actions,
                                dt_pageLength=display_length,
                                dt_pagination="true",
                                dt_searching="false",
                                )

                response.view = "list_filter.html"

                return {"items": items,
                        "title": T("Assign to Incident"),
                        "list_filter_form": ff,
                        }

            elif r.representation == "aadata":
                # Ajax refresh
                if "draw" in get_vars:
                    echo = int(get_vars.draw)
                else:
                    echo = None

                data = resource.select(list_fields,
                                       start=0,
                                       limit=limit,
                                       orderby=orderby,
                                       left=left,
                                       count=True,
                                       represent=True)
                filteredrows = data["numrows"]
                dt = S3DataTable(data["rfields"], data["rows"])

                items = dt.json(totalrows,
                                filteredrows,
                                dt_id,
                                echo,
                                dt_bulk_actions=dt_bulk_actions)
                response.headers["Content-Type"] = "application/json"
                return items

            else:
                r.error(415, current.ERROR.BAD_FORMAT)
        else:
            r.error(405, current.ERROR.BAD_METHOD)

# =============================================================================
def event_notification_dispatcher(r, **attr):
    """
        Send a Dispatch notice from an Incident Report
            - this will be formatted as an OpenGeoSMS
    """

    if r.representation == "html" and \
        r.id and not r.component:

        T = current.T
        msg = current.msg
        s3db = current.s3db

        #ctable = s3db.pr_contact
        itable = s3db.event_incident
        etable = s3db.event_event

        message = ""
        text = ""

        if r.name == "event":

            record = r.record
            record_id = record.id
            eventName = record.start_name
            startDate = record.date
            exercise = record.exercise

            text += "************************************************"
            text += "\n%s " % T("Automatic Message")
            text += "\n%s: %s, " % (T("Event ID"), record_id)
            text += " %s: %s" % (T("Event name"), eventName)
            text += "\n%s: %s " % (T("Event started"), startDate)
            text += "\n%s= %s, " % (T("Exercise"), exercise)
            text += "%s= %s" % (T("Status open"), exercise)
            text += "\n************************************************\n"

            # URL to redirect to after message sent
            url = URL(c="event", f="event", args=r.id)

        if r.name == "incident":

            record = r.record
            record_id = record.id
            incName = record.name
            zeroHour = record.date
            exercise = record.exercise
            event_id = record.event_id
            closed = record.closed

            if event_id != None:
                event = current.db(itable.id == event_id).select(etable.name,
                                                                 limitby=(0, 1),
                                                                 ).first()
                eventName = event.name
            else:
                eventName = T("Not Defined")

            text += "************************************************"
            text += "\n%s " % T("Automatic Message")
            text += "\n%s: %s,  " % (T("Incident ID"), record_id)
            text += " %s: %s" % (T("Incident name"), incName)
            text += "\n%s: %s " % (T("Related event"), eventName)
            text += "\n%s: %s " % (T("Incident started"), zeroHour)
            text += "\n%s %s, " % (T("Exercise?"), exercise)
            text += "%s %s" % (T("Closed?"), closed)
            text += "\n************************************************\n"

            url = URL(c="event", f="incident", args=r.id)

        # Create the form
        opts = {"type": "SMS",
                # @ToDo: deployment_setting
                "subject": T("Deployment Request"),
                "message": message + text,
                "url": url,
                }

        #query = (ctable.pe_id == id)
        #recipients = current.db(query).select(ctable.pe_id)

        #if not recipients:
        #    # Provide an Autocomplete the select the person to send the notice to
        #    opts["recipient_type"] = "pr_person"

        #elif len(recipients) == 1:
        #    # Send to this person
        #    opts["recipient"] = recipients.first()["pr_person"].pe_id
        #else:
        #    # Send to the Incident Commander
        #    ic = False
        #    for row in recipients:
        #        if row["irs_ireport_human_resource"].incident_commander == True:
        #            opts["recipient"] = row["pr_person"].pe_id
        #            ic = True
        #            break
        #        if not ic:
        #            # Provide an Autocomplete to select the person to send the notice to
        #            opts["recipient_type"] = "pr_person"

        output = msg.compose(**opts)

        # Maintain RHeader for consistency
        if attr.get("rheader"):
            rheader = attr["rheader"](r)
            if rheader:
                output["rheader"] = rheader

        output["title"] = T("Send Event Update")
        current.response.view = "msg/compose.html"
        return output

    else:
        r.error(405, current.messages.BAD_METHOD)

# =============================================================================
def event_event_list_layout(list_id, item_id, resource, rfields, record,
                            icon="event"):
    """
        Default dataList item renderer for Incidents on Profile pages

        @param list_id: the HTML ID of the list
        @param item_id: the HTML ID of the item
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
    """

    record_id = record["event_event.id"]
    item_class = "thumbnail"

    author = record["event_event.modified_by"]

    name = record["event_event.name"]
    event_type = record["event_event.event_type_id"] or ""
    description = record["event_event.comments"]
    start_date = record["event_event.start_date"]

    location = record["event_event_location.location_id"] or ""

    # Edit Bar
    # @ToDo: Consider using S3NavigationItem to hide the auth-related parts
    permit = current.auth.s3_has_permission
    table = current.db.event_event
    if permit("update", table, record_id=record_id):
        edit_btn = A(ICON("edit"),
                     _href=URL(c="event", f="event",
                               args=[record_id, "update.popup"],
                               vars={"refresh": list_id,
                                     "record": record_id},
                               ),
                     _class="s3_modal",
                     _title=S3CRUD.crud_string(resource.tablename,
                                               "title_update"),
                     )
    else:
        edit_btn = ""
    if permit("delete", table, record_id=record_id):
        delete_btn = A(ICON("delete"),
                       _class="dl-item-delete",
                       _title=S3CRUD.crud_string(resource.tablename,
                                                 "label_delete_button"),
                       )
    else:
        delete_btn = ""
    edit_bar = DIV(edit_btn,
                   delete_btn,
                   _class="edit-bar fright",
                   )

    # Render the item
    item = DIV(DIV(ICON(icon),
                   SPAN(event_type, _class="type-title"),
                   SPAN(location, _class="location-title"),
                   SPAN(start_date, _class="date-title"),
                   edit_bar,
                   _class="card-header",
                   ),
               DIV(DIV(A(name,
                          _href=URL(c="event", f="event",
                                    args=[record_id, "profile"])),
                        _class="card-title"),
                   DIV(DIV((description or ""),
                           DIV(author or "",
                               _class="card-person",
                               ),
                           _class="media",
                           ),
                       _class="media-body",
                       ),
                   _class="media",
                   ),
               #docs,
               _class=item_class,
               _id=item_id,
               )

    return item

# =============================================================================
def event_incident_list_layout(list_id, item_id, resource, rfields, record,
                               icon="incident"):
    """
        Default dataList item renderer for Incidents on Profile pages

        @param list_id: the HTML ID of the list
        @param item_id: the HTML ID of the item
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
    """

    raw = record._row
    record_id = raw["event_incident.id"]
    item_class = "thumbnail"

    author = record["event_incident.modified_by"]
    #date = record["event_incident.modified_on"]

    name = record["event_incident.name"]
    description = record["event_incident.comments"]
    start_date = record["event_incident.start_date"]

    organisation = record["event_incident.organisation_id"]
    organisation_id = raw["event_incident.organisation_id"]
    location = record["event_incident.location_id"]

    org_url = URL(c="org", f="organisation", args=[organisation_id, "profile"])
    org_logo = raw["org_organisation.logo"]
    if org_logo:
        org_logo = A(IMG(_src=URL(c="default", f="download", args=[org_logo]),
                         _class="media-object",
                         ),
                     _href=org_url,
                     _class="pull-left",
                     )
    else:
        # @ToDo: use a dummy logo image
        org_logo = A(IMG(_class="media-object"),
                     _href=org_url,
                     _class="pull-left",
                     )

    # Edit Bar
    # @ToDo: Consider using S3NavigationItem to hide the auth-related parts
    permit = current.auth.s3_has_permission
    table = current.db.event_incident
    if permit("update", table, record_id=record_id):
        edit_btn = A(ICON("edit"),
                     _href=URL(c="event", f="incident",
                               args=[record_id, "update.popup"],
                               vars={"refresh": list_id,
                                     "record": record_id},
                               ),
                     _class="s3_modal",
                     _title=S3CRUD.crud_string(resource.tablename,
                                               "title_update"),
                     )
    else:
        edit_btn = ""
    if permit("delete", table, record_id=record_id):
        delete_btn = A(ICON("delete"),
                       _class="dl-item-delete",
                       _title=S3CRUD.crud_string(resource.tablename,
                                                 "label_delete_button"),
                       )
    else:
        delete_btn = ""
    edit_bar = DIV(edit_btn,
                   delete_btn,
                   _class="edit-bar fright",
                   )

    # Render the item
    item = DIV(DIV(ICON(icon),
                   SPAN(location, _class="location-title"),
                   SPAN(start_date, _class="date-title"),
                   edit_bar,
                   _class="card-header",
                   ),
               DIV(DIV(A(name,
                          _href=URL(c="event", f="incident",
                                    args=[record_id, "profile"])),
                        _class="card-title"),
                   DIV(DIV((description or ""),
                           DIV(author or "",
                               " - ",
                               A(organisation,
                                 _href=org_url,
                                 _class="card-organisation",
                                 ),
                               _class="card-person",
                               ),
                           _class="media",
                           ),
                       _class="media-body",
                       ),
                   _class="media",
                   ),
               #docs,
               _class=item_class,
               _id=item_id,
               )

    return item

# =============================================================================
def event_resource_list_layout(list_id, item_id, resource, rfields, record):
    """
        Default dataList item renderer for Resources on Profile pages

        @param list_id: the HTML ID of the list
        @param item_id: the HTML ID of the item
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
    """

    raw = record._row
    record_id = raw["event_resource.id"]
    item_class = "thumbnail"

    author = record["event_resource.modified_by"]
    date = record["event_resource.date"]
    quantity = record["event_resource.value"]
    resource_type = record["event_resource.parameter_id"]
    comments = raw["event_resource.comments"]
    organisation = record["event_resource.organisation_id"]
    organisation_id = raw["event_resource.organisation_id"]
    location = record["event_resource.location_id"]
    location_id = raw["event_resource.location_id"]
    location_url = URL(c = "gis",
                       f = "location",
                       args = [location_id, "profile"],
                       )

    org_url = URL(c = "event",
                  f = "organisation",
                  args = [organisation_id, "profile"],
                  )
    logo = raw["org_organisation.logo"]
    if logo:
        logo = A(IMG(_src = URL(c="default", f="download", args=[logo]),
                     _class = "media-object",
                     ),
                 _href = org_url,
                 _class = "pull-left",
                 )
    else:
        # @ToDo: use a dummy logo image
        logo = A(IMG(_class="media-object"),
                 _href = org_url,
                 _class = "pull-left",
                 )

    # Edit Bar
    permit = current.auth.s3_has_permission
    table = current.db.event_resource
    if permit("update", table, record_id=record_id):
        urlvars = {"refresh": list_id,
                   "record": record_id,
                   }
        f = current.request.function
        if f == "organisation" and organisation_id:
            urlvars["(organisation)"] = organisation_id
        elif f == "location" and location_id:
            urlvars["(location)"] = location_id
        edit_btn = A(ICON("edit"),
                     _href = URL(c = "event",
                                 f = "resource",
                                 args = [record_id, "update.popup"],
                                 vars = urlvars,
                                 ),
                     _class = "s3_modal",
                     _title = S3CRUD.crud_string(resource.tablename,
                                                 "title_update",
                                                 ),
                     )
    else:
        edit_btn = ""
    if permit("delete", table, record_id=record_id):
        delete_btn = A(ICON("delete"),
                       _class = "dl-item-delete",
                       _title = S3CRUD.crud_string(resource.tablename,
                                                   "label_delete_button",
                                                   ),
                       )
    else:
        delete_btn = ""
    edit_bar = DIV(edit_btn,
                   delete_btn,
                   _class = "edit-bar fright",
                   )

    # Render the item
    #avatar = logo

    item = DIV(DIV(SPAN(A(location,
                          _href = location_url,
                          ),
                        _class = "location-title",
                        ),
                   SPAN(date,
                        _class = "date-title",
                        ),
                   edit_bar,
                   _class = "card-header",
                   ),
               DIV(#avatar,
                   DIV("%s %s" % (quantity,
                                  current.T(resource_type)
                                  ),
                       _class = "card-title",
                       ),
                   DIV(DIV(comments,
                           DIV(author or "" ,
                               " - ",
                               A(organisation,
                                 _href = org_url,
                                 _class = "card-organisation",
                                 ),
                               _class = "card-person",
                               ),
                           _class = "media",
                           ),
                       _class = "media-body",
                       ),
                   _class = "media",
                   ),
               #docs,
               _class = item_class,
               _id = item_id,
               )

    return item

# =============================================================================
def event_rheader(r):
    """ Resource headers for component views """

    rheader = None

    record = r.record
    if record and r.representation == "html":

        T = current.T
        settings = current.deployment_settings

        name = r.name
        if name == "event":
            # Event Controller
            if settings.get_event_label(): # == "Disaster"
                label = T("Disaster Details")
            else:
                label = T("Event Details")
            tabs = [(label, None),
                    ]
            if settings.has_module("doc"):
                tabs += [(T("Documents"), "document"),
                         (T("Photos"), "image"),
                         ]
            if settings.get_event_impact_tab():
                tabs.append((T("Impact"), "impact"))
            if settings.get_event_dc_target_tab():
                tabs.append((T("Assessment Targets"), "target"))
            if settings.get_event_dc_response_tab():
                tabs.append((T("Assessments"), "response"))
            if settings.get_project_event_projects():
                tabs.append((T("Projects"), "project"))
            if settings.get_project_event_activities():
                tabs.append((T("Activities"), "activity"))
            if settings.has_module("cr"):
                tabs.append((T("Shelters"), "shelter"))
            #if settings.has_module("req"):
            #    tabs.append((T("Requests"), "req"))
            if settings.get_event_dispatch_tab():
                tabs.append((T("Send Notification"), "dispatch"))

            rheader_tabs = s3_rheader_tabs(r, tabs)

            if record.exercise:
                exercise = TH(T("EXERCISE"))
            else:
                exercise = TH()
            if record.closed:
                closed = TH(T("CLOSED"))
            else:
                closed = TH()
            table = r.table
            rheader = DIV(TABLE(TR(exercise),
                                TR(TH("%s: " % table.name.label),
                                   record.name,
                                   ),
                                TR(TH("%s: " % table.comments.label),
                                   record.comments,
                                   ),
                                TR(TH("%s: " % table.start_date.label),
                                   table.start_date.represent(record.start_date),
                                   ),
                                TR(closed),
                                ), rheader_tabs)

        elif name == "incident":
            # Incident Controller
            tabs = [(T("Incident Details"), None)]
            append = tabs.append

            # Impact tab
            if settings.get_incident_impact_tab():
                append((T("Impact"), "impact"))

            # Tasks tab
            if settings.has_module("project"):
                append((T("Tasks"), "task"))

            # Staff tab
            if settings.has_module("hrm"):
                STAFF = settings.get_hrm_staff_label()
                append((STAFF, "human_resource"))
                if current.auth.s3_has_permission("create", "event_human_resource"):
                    append((T("Assign %(staff)s") % {"staff": STAFF}, "assign"))

            # Teams tab:
            teams_tab = settings.get_incident_teams_tab()
            if teams_tab:
                tab_label = T("Teams") if teams_tab is True else T(teams_tab)
                append((tab_label, "group"))

            # Asset tab
            if settings.has_module("asset"):
                append((T("Assets"), "asset"))

            # Other tabs
            tabs.extend(((T("Facilities"), "site"), # Inc Shelters
                         (T("Organizations"), "organisation"),
                         (T("SitReps"), "sitrep"),
                         (T("Map Profile"), "config"),
                         ))

            # Messaging tab
            if settings.get_incident_dispatch_tab():
                append((T("Send Notification"), "dispatch"))

            rheader_tabs = s3_rheader_tabs(r, tabs)

            if record.exercise:
                exercise = TH(T("EXERCISE"))
            else:
                exercise = TH()
            if record.closed:
                closed = TH(T("CLOSED"))
            else:
                closed = TH()
            table = r.table
            rheader = DIV(TABLE(TR(exercise),
                                TR(TH("%s: " % table.name.label),
                                   record.name,
                                   ),
                                TR(TH("%s: " % table.location_id.label),
                                  table.location_id.represent(record.location_id),
                                  ),
                                TR(TH("%s: " % table.comments.label),
                                   record.comments,
                                   ),
                                TR(TH("%s: " % table.date.label),
                                   table.date.represent(record.date),
                                   ),
                                TR(closed),
                                ), rheader_tabs)

        elif name == "scenario":
            # Scenarios Controller
            tabs = [(T("Scenario Details"), None)]
            append = tabs.append

            # Tasks tab
            if settings.has_module("project"):
                append((T("Tasks"), "task"))

            # Staff tab
            if settings.has_module("hrm"):
                STAFF = settings.get_hrm_staff_label()
                append((STAFF, "human_resource"))
                if current.auth.s3_has_permission("create", "event_human_resource"):
                    append((T("Assign %(staff)s") % {"staff": STAFF}, "assign"))

            # Asset tab
            if settings.has_module("asset"):
                append((T("Assets"), "asset"))

            # Other tabs
            #tabs.extend(((T("Facilities"), "site"), # Inc Shelters
            #             (T("Organizations"), "organisation"),
            #             (T("Map Profile"), "config"),
            #             ))

            rheader_tabs = s3_rheader_tabs(r, tabs)

            table = r.table
            rheader = DIV(TABLE(TR(TH("%s: " % table.incident_type_id.label),
                                   table.incident_type_id.represent(record.incident_type_id),
                                   ),
                                TR(TH("%s: " % table.name.label),
                                   record.name,
                                   ),
                                TR(TH("%s: " % table.comments.label),
                                   record.comments,
                                   ),
                                ), rheader_tabs)

        elif name == "sitrep":
            # SitRep Controller
            tabs = [(T("Header"), None)]

            # Dynamic Answers tab
            if settings.get_event_sitrep_dynamic():
                tabs.append((T("Details"), "answer"))

            # EDXL tabs
            #if settings.get_event_sitrep_edxl():
            #    tabs.extend(((T("Field Observation Report"), "field_observation"),
            #                 (T("Situation Information"), "situation_information"),
            #                 (T("Response Resources Totals"), "response_resources"),
            #                 (T("Casualty And Illness Summary"), "casualty_illness"),
            #                 (T("Management Reporting Summary"), "management"),
            #                 ))

            rheader_tabs = s3_rheader_tabs(r, tabs)

            table = r.table
            rheader = DIV(TABLE(TR(TH("%s: " % table.event_id.label),
                                   table.event_id.represent(record.event_id),
                                   ),
                                TR(TH("%s: " % table.number.label),
                                   record.number,
                                   ),
                                TR(TH("%s: " % table.date.label),
                                   table.date.represent(record.date),
                                   ),
                                ), rheader_tabs)

    return rheader

# END =========================================================================
