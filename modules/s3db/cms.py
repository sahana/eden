# -*- coding: utf-8 -*-

""" Sahana Eden Content Management System Model

    @copyright: 2012-2019 (c) Sahana Software Foundation
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

__all__ = ("S3ContentModel",
           "S3ContentForumModel",
           "S3ContentMapModel",
           "S3ContentOrgModel",
           "S3ContentOrgGroupModel",
           "S3ContentTeamModel",
           "S3ContentUserModel",
           "cms_index",
           "cms_documentation",
           "cms_rheader",
           "cms_configure_newsfeed_post_fields",
           "cms_post_list_layout",
           "S3CMS",
           #"cms_Calendar",
           #"cms_TagList",
           )

import datetime
import json

from gluon import *
from gluon.storage import Storage
from ..s3 import *
from s3layouts import S3PopupLink

# Compact JSON encoding
SEPARATORS = (",", ":")

# =============================================================================
class S3ContentModel(S3Model):
    """
        Content Management System
    """

    names = ("cms_series",
             "cms_status",
             "cms_post",
             "cms_post_id",
             "cms_post_module",
             "cms_tag",
             "cms_tag_id",
             "cms_tag_post",
             "cms_comment",
             )

    def model(self):

        T = current.T
        db = current.db
        add_components = self.add_components
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        set_method = self.set_method
        settings = current.deployment_settings

        # ---------------------------------------------------------------------
        # Series
        # - lists of Posts displaying in recent-first mode
        #

        tablename = "cms_series"
        define_table(tablename,
                     Field("name", length=255, notnull=True, unique=True,
                           label = T("Name"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(255),
                                       IS_NOT_ONE_OF(db,
                                                     "%s.name" % tablename,
                                                     ),
                                       ],
                           ),
                     Field("avatar", "boolean",
                           default = False,
                           label = T("Show author picture?"),
                           represent = s3_yes_no_represent,
                           ),
                     Field("location", "boolean",
                           default = False,
                           label = T("Show Location?"),
                           represent = s3_yes_no_represent,
                           ),
                     Field("richtext", "boolean",
                           default = True,
                           label = T("Rich Text?"),
                           represent = s3_yes_no_represent,
                           ),
                     Field("replies", "boolean",
                           default = False,
                           label = T("Comments permitted?"),
                           represent = s3_yes_no_represent,
                           ),
                     s3_comments(),
                     # Multiple Roles (@ToDo: Implement the restriction)
                     s3_roles_permitted(readable = False,
                                        writable = False
                                        ),
                     *s3_meta_fields())

        # CRUD Strings
        ADD_SERIES = T("Create Series")
        crud_strings[tablename] = Storage(
            label_create = ADD_SERIES,
            title_display = T("Series Details"),
            title_list = T("Series"),
            title_update = T("Edit Series"),
            title_upload = T("Import Series"),
            label_list_button = T("List Series"),
            msg_record_created = T("Series added"),
            msg_record_modified = T("Series updated"),
            msg_record_deleted = T("Series deleted"),
            msg_list_empty = T("No series currently defined"))

        # Reusable field
        translate = settings.get_L10n_translate_cms_series()
        represent = S3Represent(lookup=tablename, translate=translate)
        series_id = S3ReusableField("series_id", "reference %s" % tablename,
                                    label = T("Type"), # Even if this isn't always the use-case
                                    ondelete = "CASCADE",
                                    readable = False,
                                    writable = False,
                                    represent = represent,
                                    requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "cms_series.id",
                                                          represent)),
                                    )

        # Resource Configuration
        configure(tablename,
                  create_next = URL(f="series", args=["[id]", "post"]),
                  onaccept = self.cms_series_onaccept,
                  )

        # Components
        add_components(tablename,
                       cms_post = "series_id",
                       )

        # ---------------------------------------------------------------------
        # Post Statuses
        # - used by WACOP
        #
        tablename = "cms_status"
        define_table(tablename,
                     Field("name", length=128, notnull=True, unique=True,
                           label = T("Name"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(128),
                                       ],
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        ADD_STATUS = T("Create Status")
        crud_strings[tablename] = Storage(
            label_create = ADD_STATUS,
            title_display = T("Status Details"),
            title_list = T("Statuses"),
            title_update = T("Edit Status"),
            #title_upload = T("Import Statuses"),
            label_list_button = T("List Statuses"),
            label_delete_button = T("Delete Status"),
            msg_record_created = T("Status added"),
            msg_record_modified = T("Status updated"),
            msg_record_deleted = T("Status deleted"),
            msg_list_empty = T("No Statuses currently registered"))

        # Reusable Field
        represent = S3Represent(lookup=tablename, translate=True)
                                #none = T("Unknown"))
        status_id = S3ReusableField("status_id", "reference %s" % tablename,
                        comment = S3PopupLink(title = ADD_STATUS,
                                              c = "cms",
                                              f = "status",
                                              ),
                        label = T("Status"),
                        ondelete = "SET NULL",
                        represent = represent,
                        requires = IS_EMPTY_OR(
                                    IS_ONE_OF(db, "cms_status.id",
                                              represent,
                                              sort=True)),
                        sortby = "name",
                        )

        # ---------------------------------------------------------------------
        # Posts
        # - single blocks of [rich] text which can be embedded into a page,
        #   be viewed as full pages or as part of a Series
        #

        if settings.get_cms_richtext():
            body_represent = XML
            body_widget = s3_richtext_widget
        else:
            body_represent = lambda body: XML(s3_URLise(body))
            body_widget = None

        # WACOP Priorities
        # @ToDo: Add deployment_setting if these need to be different in other templates
        post_priority_opts = {1: T("Informational"),
                              2: T("Important"),
                              3: T("Critical"),
                              }

        tablename = "cms_post"
        define_table(tablename,
                     self.super_link("doc_id", "doc_entity"),
                     series_id(),
                     Field("name", #notnull=True,
                           comment = T("This isn't visible to the published site, but is used to allow menu items to point to the page"),
                           label = T("Name"),
                           ),
                     Field("title",
                           comment = T("The title of the page, as seen in the browser (optional)"),
                           label = T("Title"),
                           ),
                     Field("body", "text", notnull=True,
                           label = T("Body"),
                           represent = body_represent,
                           #requires = IS_NOT_EMPTY(),
                           widget = body_widget,
                           ),
                     s3_datetime(default = "now"),
                     # @ToDo: Move this to link table?
                     self.gis_location_id(),
                     # @ToDo: Move this to link table?
                     # - although this makes widget hard!
                     self.pr_person_id(label = T("Contact"),
                                       # Enable only in certain conditions
                                       readable = False,
                                       writable = False,
                                       ),
                     Field("avatar", "boolean",
                           default = False,
                           label = T("Show author picture?"),
                           represent = s3_yes_no_represent,
                           ),
                     Field("replies", "boolean",
                           default = False,
                           label = T("Comments permitted?"),
                           represent = s3_yes_no_represent,
                           ),
                     Field("priority", "integer",
                           default = 1,
                           label = T("Priority"),
                           represent = lambda opt: \
                                       post_priority_opts.get(opt,
                                                              current.messages.UNKNOWN_OPT),
                           requires = IS_IN_SET(post_priority_opts,
                                                zero=None),
                           # Enable in template if-desired
                           readable = False,
                           writable = False,
                           ),
                     status_id(readable = False,
                               writable = False,
                               ),
                     # @ToDo: Also have a datetime for 'Expires On'
                     Field("expired", "boolean",
                           default = False,
                           label = T("Expired?"),
                           represent = s3_yes_no_represent,
                           ),
                     #Field("published", "boolean",
                     #      default=True,
                     #      label=T("Published")),
                     s3_comments(),
                     # Multiple Roles (@ToDo: Implement the restriction)
                     s3_roles_permitted(readable = False,
                                        writable = False
                                        ),
                     *s3_meta_fields())

        # CRUD Strings
        ADD_POST = T("Create Post")
        crud_strings[tablename] = Storage(
            label_create = ADD_POST,
            title_display = T("Post Details"),
            title_list = T("Posts"),
            title_update = T("Edit Post"),
            title_upload = T("Import Posts"),
            label_list_button = T("List Posts"),
            msg_record_created = T("Post added"),
            msg_record_modified = T("Post updated"),
            msg_record_deleted = T("Post deleted"),
            msg_list_empty = T("No posts currently available"))

        # Reusable field
        represent = S3Represent(lookup=tablename)
        post_id = S3ReusableField("post_id", "reference %s" % tablename,
                                  comment = S3PopupLink(c = "cms",
                                                        f = "post",
                                                        title = ADD_POST,
                                                        tooltip = T("A block of rich text which could be embedded into a page, viewed as a complete page or viewed as a list of news items."),
                                                        ),
                                  label = T("Post"),
                                  ondelete = "CASCADE",
                                  represent = represent,
                                  requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "cms_post.id",
                                                          represent)),
                                  sortby = "name",
                                  )

        list_fields = ["post_module.module",
                       "title",
                       "body",
                       "location_id",
                       "date",
                       "expired",
                       "comments"
                       ]

        org_field = settings.get_cms_organisation()
        if org_field == "created_by$organisation_id":
            org_field = "auth_user.organisation_id"
        elif org_field == "post_organisation.organisation_id":
            org_field = "cms_post_organisation.organisation_id"
        if org_field:
            list_fields.append(org_field)

        filter_widgets = [S3TextFilter(["body"],
                                       label = T("Search"),
                                       _class = "filter-search",
                                       #_placeholder = T("Search").upper(),
                                       ),
                          S3OptionsFilter("series_id",
                                          label = T("Type"),
                                          hidden = True,
                                          ),
                          S3LocationFilter("location_id",
                                           label = T("Location"),
                                           hidden = True,
                                           ),
                          S3OptionsFilter("created_by$organisation_id",
                                          label = T("Organization"),
                                          # Can't use this for integers, use field.represent instead
                                          #represent = "%(name)s",
                                          hidden = True,
                                          ),
                          S3DateFilter("created_on",
                                       label = T("Date"),
                                       hide_time = True,
                                       hidden = True,
                                       ),
                          ]

        # Resource Configuration
        configure(tablename,
                  context = {"event": "event.id",
                             "incident": "incident.id",
                             "location": "location_id",
                             "organisation": "created_by$organisation_id",
                             },
                  deduplicate = self.cms_post_duplicate,
                  filter_actions = [{"label": "Open Table",
                                     "icon": "table",
                                     "function": "newsfeed",
                                     "method": "datalist",
                                     },
                                    {"label": "Open Map",
                                     "icon": "globe",
                                     "method": "map",
                                     },
                                    {"label": "Open RSS Feed",
                                     "icon": "rss",
                                     "format": "rss",
                                     },
                                    ],
                  filter_widgets = filter_widgets,
                  list_fields = list_fields,
                  list_layout = cms_post_list_layout,
                  list_orderby = "cms_post.date desc",
                  onaccept = self.cms_post_onaccept,
                  orderby = "cms_post.date desc",
                  summary = [{"name": "table",
                              "label": "Table",
                              "widgets": [{"method": "datatable"}]
                              },
                             #{"name": "report",
                             # "label": "Report",
                             # "widgets": [{"method": "report",
                             #              "ajax_init": True}]
                             # },
                             {"name": "map",
                              "label": "Map",
                              "widgets": [{"method": "map",
                                           "ajax_init": True}],
                              },
                             ],
                  super_entity = "doc_entity",
                  )

        # Components
        add_components(tablename,
                       cms_comment = "post_id",
                       cms_post_layer = "post_id",
                       cms_post_module = "post_id",
                       cms_post_forum = "post_id",
                       cms_post_user = {"name": "bookmark",
                                        "joinby": "post_id",
                                        },
                       cms_tag = {"link": "cms_tag_post",
                                  "joinby": "post_id",
                                  "key": "tag_id",
                                  "actuate": "hide",
                                  },

                       # For filter widget
                       cms_tag_post = "post_id",

                       cms_post_organisation = {"joinby": "post_id",
                                                # @ToDo: deployment_setting
                                                "multiple": False,
                                                },

                       cms_post_organisation_group = {"joinby": "post_id",
                                                      # @ToDo: deployment_setting
                                                      "multiple": False,
                                                      },

                       # For InlineForm to tag Posts to Events/Incidents/Incident Types/Teams
                       event_post = (# Events
                                     {"name": "event_post",
                                      "joinby": "post_id",
                                      },
                                     # Incidents
                                     {"name": "incident_post",
                                      "joinby": "post_id",
                                      }
                                     ),
                       event_post_incident_type = "post_id",

                       pr_group = {"link": "cms_post_team",
                                   "joinby": "group_id",
                                   "key": "incident_type_id",
                                   "actuate": "hide",
                                   },
                       cms_post_team = "post_id",

                       # For Profile to filter appropriately
                       event_event = {"link": "event_post",
                                      "joinby": "post_id",
                                      "key": "event_id",
                                      "actuate": "hide",
                                      },
                       event_incident = {"link": "event_post",
                                         "joinby": "post_id",
                                         "key": "incident_id",
                                         "actuate": "hide",
                                         },
                       event_incident_type = {"link": "event_post_incident_type",
                                              "joinby": "post_id",
                                              "key": "incident_type_id",
                                              "actuate": "hide",
                                              },
                       )

        # Custom Methods
        set_method("cms", "post",
                   method = "add_bookmark",
                   action = self.cms_add_bookmark)

        set_method("cms", "post",
                   method = "remove_bookmark",
                   action = self.cms_remove_bookmark)

        set_method("cms", "post",
                   method = "add_tag",
                   action = self.cms_add_tag)

        set_method("cms", "post",
                   method = "remove_tag",
                   action = self.cms_remove_tag)

        set_method("cms", "post",
                   method = "share",
                   action = self.cms_share)

        set_method("cms", "post",
                   method = "unshare",
                   action = self.cms_unshare)

        set_method("cms", "post",
                   method = "calendar",
                   action = cms_Calendar)

        # ---------------------------------------------------------------------
        # Modules/Resources <> Posts link table
        #
        tablename = "cms_post_module"
        define_table(tablename,
                     post_id(empty = False),
                     Field("module",
                           comment = T("If you specify a module, but no resource, then this will be used as the text in that module's index page"),
                           label = T("Module"),
                           ),
                     Field("resource",
                           comment = T("If you specify a resource, but no record, then this will be used as the text in that resource's summary page"),
                           label = T("Resource"),
                           ),
                     Field("record",
                           comment = T("If you specify a record then this will be used for that record's profile page"),
                           label = T("Record"),
                           ),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Post"),
            title_display = T("Post Details"),
            title_list = T("Posts"),
            title_update = T("Edit Post"),
            label_list_button = T("List Posts"),
            msg_record_created = T("Post set as Module/Resource homepage"),
            msg_record_modified = T("Post updated"),
            msg_record_deleted = T("Post removed"),
            msg_list_empty = T("No posts currently set as module/resource homepages"))

        # ---------------------------------------------------------------------
        # Tags
        #
        tablename = "cms_tag"
        define_table(tablename,
                     Field("name",
                           label = T("Tag"),
                           ),
                     s3_comments(),
                     # Multiple Roles (@ToDo: Implement the restriction)
                     #s3_roles_permitted(readable = False,
                     #                   writable = False
                     #                   ),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Tag"),
            title_display = T("Tag Details"),
            title_list = T("Tags"),
            title_update = T("Edit Tag"),
            title_upload = T("Import Tags"),
            label_list_button = T("List Tags"),
            msg_record_created = T("Tag added"),
            msg_record_modified = T("Tag updated"),
            msg_record_deleted = T("Tag deleted"),
            msg_list_empty = T("No tags currently defined"))

        # Reusable field
        represent = S3Represent(lookup=tablename, translate=True)
        tag_id = S3ReusableField("tag_id", "reference %s" % tablename,
                                 label = T("Tag"),
                                 ondelete = "CASCADE",
                                 represent = represent,
                                 requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "cms_tag.id",
                                                          represent)),
                                 sortby = "name",
                                 )

        # Custom Methods
        set_method("cms", "tag",
                   method = "tag_list",
                   action = cms_TagList)

        # ---------------------------------------------------------------------
        # Tags <> Posts link table
        #
        tablename = "cms_tag_post"
        define_table(tablename,
                     post_id(empty = False),
                     tag_id(empty = False),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Tag Post"),
            title_display = T("Tag Details"),
            title_list = T("Tags"),
            title_update = T("Edit Tag"),
            title_upload = T("Import Tags"),
            label_list_button = T("List Tagged Posts"),
            msg_record_created = T("Post Tagged"),
            msg_record_modified = T("Tag updated"),
            msg_record_deleted = T("Tag removed"),
            msg_list_empty = T("No posts currently tagged"))

        # ---------------------------------------------------------------------
        # Comments
        # - threaded comments on Posts
        #
        # @ToDo: Attachments?
        #
        # Parent field allows us to:
        #  * easily filter for top-level threads
        #  * easily filter for next level of threading
        #  * hook a new reply into the correct location in the hierarchy
        #
        tablename = "cms_comment"
        define_table(tablename,
                     Field("parent", "reference cms_comment",
                           requires = IS_EMPTY_OR(
                                        IS_ONE_OF(db, "cms_comment.id")),
                           readable = False,
                           ),
                     post_id(empty = False),
                     Field("body", "text", notnull=True,
                           label = T("Comment"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     *s3_meta_fields())

        # Resource Configuration
        configure(tablename,
                  list_fields = ["post_id",
                                 "created_by",
                                 "modified_on"
                                 ],
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict(cms_post_id = post_id,
                    cms_tag_id = tag_id,
                    )

    # -------------------------------------------------------------------------
    def defaults(self):
        """
            Safe defaults for model-global names in case module is disabled
        """

        dummy = S3ReusableField("dummy_id", "integer",
                                readable = False,
                                writable = False)

        return dict(cms_post_id = lambda **attr: dummy("post_id"),
                    cms_tag_id = lambda **attr: dummy("tag_id"),
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def cms_series_onaccept(form):
        """
            Cascade values down to all component Posts
        """

        form_vars = form.vars

        db = current.db
        table = db.cms_post
        query = (table.series_id == form_vars.id)
        db(query).update(avatar = form_vars.avatar,
                         replies = form_vars.replies,
                         roles_permitted = form_vars.roles_permitted,
                         )

    # -------------------------------------------------------------------------
    @staticmethod
    def cms_post_duplicate(item):
        """
            CMS Post Import - Update Detection (primarily for non-blog
            contents such as homepage, module index pages, summary pages,
            or online documentation):
                - same name and series => same post

            @param item: the import item

            @todo: if no name present => use cms_post_module component
                   to identify updates (also requires deduplication of
                   cms_post_module component)
        """

        data = item.data

        name = data.get("name")
        series_id = data.get("series_id")

        if not name:
            return

        table = item.table
        query = (table.name == name) & \
                (table.series_id == series_id)
        duplicate = current.db(query).select(table.id,
                                             limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def cms_post_onaccept(form):
        """
           - Set person_id from created_by if not already set
           - Handle the case where the page is for a Module home page,
             Resource Summary page or Map Layer
        """

        db = current.db
        s3db = current.s3db
        post_id = form.vars.id
        get_vars = current.request.get_vars
        module = get_vars.get("module", None)
        if module:
            table = db.cms_post_module
            query = (table.module == module)
            resource = get_vars.get("resource", None)
            if resource:
                query &= (table.resource == resource)
                record = get_vars.get("record", None)
                if record:
                    # Profile page
                    query &= (table.record == record)
                else:
                    # Resource Summary page
                    query &= (table.record == None)
            else:
                # Module home page
                record = None
                query &= ((table.resource == None) | \
                          (table.resource == "index"))
            result = db(query).update(post_id=post_id)
            if not result:
                table.insert(post_id=post_id,
                             module=module,
                             resource=resource,
                             record=record,
                             )

        layer_id = get_vars.get("layer_id", None)
        if layer_id:
            table = s3db.cms_post_layer
            query = (table.layer_id == layer_id)
            result = db(query).update(post_id=post_id)
            if not result:
                table.insert(post_id=post_id,
                             layer_id=layer_id,
                             )

        # Read record
        table = db.cms_post
        record = db(table.id == post_id).select(table.person_id,
                                                table.created_by,
                                                limitby=(0, 1)
                                                ).first()
        if record.created_by and not record.person_id:
            # Set from Author
            ptable = s3db.pr_person
            putable = s3db.pr_person_user
            query = (putable.user_id == record.created_by) & \
                    (putable.pe_id == ptable.pe_id)
            person = db(query).select(ptable.id,
                                      limitby=(0, 1)
                                      ).first()
            if person:
                db(table.id == post_id).update(person_id=person.id)

    # -----------------------------------------------------------------------------
    @staticmethod
    def cms_add_bookmark(r, **attr):
        """
            Bookmark a Post

            S3Method for interactive requests
        """

        post_id = r.id
        user = current.auth.user
        user_id = user and user.id
        if not post_id or not user_id:
            r.error(405, current.ERROR.BAD_METHOD)

        db = current.db
        ltable = db.cms_post_user
        query = (ltable.post_id == post_id) & \
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
                    data = dict(deleted=False)
                db(ltable.id == link_id).update(**data)
        else:
            link_id = ltable.insert(post_id = post_id,
                                    user_id = user_id,
                                    )

        output = current.xml.json_message(True, 200, current.T("Bookmark Added"))
        current.response.headers["Content-Type"] = "application/json"
        return output

    # -----------------------------------------------------------------------------
    @staticmethod
    def cms_remove_bookmark(r, **attr):
        """
            Remove a Bookmark for a Post

            S3Method for interactive requests
        """

        post_id = r.id
        user = current.auth.user
        user_id = user and user.id
        if not post_id or not user_id:
            r.error(405, current.ERROR.BAD_METHOD)

        db = current.db
        ltable = db.cms_post_user
        query = (ltable.post_id == post_id) & \
                (ltable.user_id == user_id)
        exists = db(query).select(ltable.id,
                                  ltable.deleted,
                                  limitby=(0, 1)
                                  ).first()
        if exists and not exists.deleted:
            resource = current.s3db.resource("cms_post_user", id=exists.id)
            resource.delete()

        output = current.xml.json_message(True, 200, current.T("Bookmark Removed"))
        current.response.headers["Content-Type"] = "application/json"
        return output

    # -----------------------------------------------------------------------------
    @staticmethod
    def cms_add_tag(r, **attr):
        """
            Add a Tag to a Post

            S3Method for interactive requests
            - designed to be called as an afterTagAdded callback to tag-it.js
        """

        post_id = r.id
        if not post_id or len(r.args) < 3:
            r.error(405, current.ERROR.BAD_METHOD)

        tag = r.args[2]
        db = current.db
        ttable = db.cms_tag
        ltable = db.cms_tag_post
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
                    data = dict(deleted=False)
                db(ttable.id == tag_id).update(**data)
        else:
            tag_id = ttable.insert(name=tag)
        query = (ltable.tag_id == tag_id) & \
                (ltable.post_id == post_id)
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
                    data = dict(deleted=False)
                db(ltable.id == exists.id).update(**data)
        else:
            ltable.insert(post_id = post_id,
                          tag_id = tag_id,
                          )

        output = current.xml.json_message(True, 200, current.T("Tag Added"))
        current.response.headers["Content-Type"] = "application/json"
        return output

    # -----------------------------------------------------------------------------
    @staticmethod
    def cms_remove_tag(r, **attr):
        """
            Remove a Tag from a Post

            S3Method for interactive requests
            - designed to be called as an afterTagRemoved callback to tag-it.js
        """

        post_id = r.id
        if not post_id or len(r.args) < 3:
            r.error(405, current.ERROR.BAD_METHOD)

        tag = r.args[2]
        db = current.db
        ttable = db.cms_tag
        exists = db(ttable.name == tag).select(ttable.id,
                                               ttable.deleted,
                                               limitby=(0, 1)
                                               ).first()
        if exists:
            tag_id = exists.id
            ltable = db.cms_tag_post
            query = (ltable.tag_id == tag_id) & \
                    (ltable.post_id == post_id)
            exists = db(query).select(ltable.id,
                                      ltable.deleted,
                                      limitby=(0, 1)
                                      ).first()
            if exists and not exists.deleted:
                resource = current.s3db.resource("cms_tag_post", id=exists.id)
                resource.delete()

        output = current.xml.json_message(True, 200, current.T("Tag Removed"))
        current.response.headers["Content-Type"] = "application/json"
        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def cms_share(r, **attr):
        """
            Share a Post to a Forum

            S3Method for interactive requests
            - designed to be called via AJAX
        """

        post_id = r.id
        if not post_id or len(r.args) < 3:
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

        ltable = s3db.cms_post_forum
        query = (ltable.post_id == post_id) & \
                (ltable.forum_id == forum_id)
        exists = db(query).select(ltable.id,
                                  limitby=(0, 1)
                                  ).first()
        if not exists:
            ltable.insert(post_id = post_id,
                          forum_id = forum_id,
                          )
            # Update modified_on of the forum to allow subscribers to be notified
            db(s3db.pr_forum.id == forum_id).update(modified_on = r.utcnow)

        output = current.xml.json_message(True, 200, current.T("Post Shared"))
        current.response.headers["Content-Type"] = "application/json"
        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def cms_unshare(r, **attr):
        """
            Unshare a Post from a Forum

            S3Method for interactive requests
            - designed to be called via AJAX
        """

        post_id = r.id
        if not post_id or len(r.args) < 3:
            r.error(405, current.ERROR.BAD_METHOD)

        db = current.db
        s3db = current.s3db
        forum_id = r.args[2]

        ltable = s3db.cms_post_forum
        query = (ltable.post_id == post_id) & \
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

            resource = s3db.resource("cms_post_forum", id=exists.id)
            resource.delete()

        output = current.xml.json_message(True, 200, current.T("Stopped Sharing Post"))
        current.response.headers["Content-Type"] = "application/json"
        return output

# =============================================================================
class S3ContentForumModel(S3Model):
    """
        Link Posts to Forums to allow Users to Share posts
    """

    names = ("cms_post_forum",)

    def model(self):

        # ---------------------------------------------------------------------
        # Forums <> Posts link table
        #
        tablename = "cms_post_forum"
        self.define_table(tablename,
                          self.cms_post_id(empty = False),
                          self.pr_forum_id(empty = False,
                                           ondelete = "CASCADE",
                                           ),
                          *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class S3ContentMapModel(S3Model):
    """
        Use of the CMS to provide extra data about Map Layers
    """

    names = ("cms_post_layer",)

    def model(self):

        # ---------------------------------------------------------------------
        # Layers <> Posts link table
        #
        tablename = "cms_post_layer"
        self.define_table(tablename,
                          self.cms_post_id(empty = False),
                          self.super_link("layer_id", "gis_layer_entity"),
                          *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class S3ContentOrgModel(S3Model):
    """
        Link Posts to Organisations
    """

    names = ("cms_post_organisation",)

    def model(self):

        # ---------------------------------------------------------------------
        # Organisations <> Posts link table
        #
        tablename = "cms_post_organisation"
        self.define_table(tablename,
                          self.cms_post_id(empty = False,
                                           ondelete = "CASCADE",
                                           ),
                          self.org_organisation_id(empty = False,
                                                   ondelete = "CASCADE",
                                                   ),
                          *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class S3ContentOrgGroupModel(S3Model):
    """
        Link Posts to Organisation Groups (Coalitions/Networks)
    """

    names = ("cms_post_organisation_group",)

    def model(self):

        # ---------------------------------------------------------------------
        # Organisation Groups <> Posts link table
        #
        tablename = "cms_post_organisation_group"
        self.define_table(tablename,
                          self.cms_post_id(empty=False),
                          self.org_group_id(empty=False),
                          *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class S3ContentTeamModel(S3Model):
    """
        Link Posts to Teams
    """

    names = ("cms_post_team",)

    def model(self):

        # ---------------------------------------------------------------------
        # Teams <> Posts link table
        #
        tablename = "cms_post_team"
        self.define_table(tablename,
                          self.cms_post_id(empty = False,
                                           ondelete = "CASCADE",
                                           ),
                          self.pr_group_id(empty = False,
                                           ondelete = "CASCADE",
                                           ),
                          *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class S3ContentUserModel(S3Model):
    """
        Link Posts to Users to allow Users to Bookmark posts
    """

    names = ("cms_post_user",)

    def model(self):

        # ---------------------------------------------------------------------
        # Users <> Posts link table
        #
        tablename = "cms_post_user"
        self.define_table(tablename,
                          self.cms_post_id(empty = False),
                          Field("user_id", current.auth.settings.table_user),
                          *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
def cms_rheader(r, tabs=None):
    """ CMS Resource Headers """

    if r.representation != "html":
        # RHeaders only used in interactive views
        return None
    record = r.record
    if record is None:
        # List or Create form: rheader makes no sense here
        return None

    table = r.table
    resourcename = r.name
    T = current.T

    if resourcename == "series":
        # Tabs
        tabs = [(T("Basic Details"), None),
                (T("Posts"), "post"),
                ]
        rheader_tabs = s3_rheader_tabs(r, tabs)

        rheader = DIV(TABLE(TR(TH("%s: " % table.name.label),
                               record.name
                               ),
                            ), rheader_tabs)

    elif resourcename == "post":
        # Tabs
        tabs = [(T("Basic Details"), None),
                ]
        if record.replies:
            tabs.append((T("Comments"), "discuss"))
        rheader_tabs = s3_rheader_tabs(r, tabs)

        rheader = DIV(TABLE(TR(TH("%s: " % table.name.label),
                               record.name
                               ),
                            ), rheader_tabs)

    return rheader

# =============================================================================
def cms_index(module, resource=None, page_name=None, alt_function=None):
    """
        Return a module index page retrieved from CMS
        - or run an alternate function if not found
    """

    response = current.response
    settings = current.deployment_settings

    if not page_name:
        page_name = settings.modules[module].name_nice

    response.title = page_name

    item = None
    if settings.has_module("cms") and not settings.get_cms_hide_index(module):
        db = current.db
        table = current.s3db.cms_post
        ltable = db.cms_post_module
        query = (ltable.module == module) & \
                (ltable.post_id == table.id) & \
                (table.deleted != True)

        if resource is None:
            query &= ((ltable.resource == None) | \
                     (ltable.resource == "index"))
        else:
            query &= (ltable.resource == resource)

        _item = db(query).select(table.id,
                                 table.body,
                                 table.title,
                                 limitby=(0, 1)).first()
        # @ToDo: Replace this crude check with?
        #if current.auth.s3_has_permission("update", table, record_id=_item.id):
        auth = current.auth
        ADMIN = auth.get_system_roles().ADMIN
        ADMIN = auth.s3_has_role(ADMIN)
        get_vars = {"module": module}
        if resource:
            get_vars["resource"] = resource
        if _item:
            if _item.title:
                response.title = _item.title
            if ADMIN:
                item = DIV(XML(_item.body),
                           BR(),
                           A(current.T("Edit"),
                             _href=URL(c="cms", f="post",
                                       args=[_item.id, "update"],
                                       vars=get_vars),
                             _class="action-btn"))
            else:
                item = XML(_item.body)
        elif ADMIN:
            item = DIV(H2(page_name),
                       A(current.T("Edit"),
                         _href=URL(c="cms", f="post", args="create",
                                   vars=get_vars),
                         _class="action-btn"))

    if not item:
        if alt_function:
            # Serve the alternate controller function
            # Copied from gluon.main serve_controller()
            # (We don't want to re-run models)
            from gluon.compileapp import build_environment, run_controller_in, run_view_in
            request = current.request
            environment = build_environment(request, response, current.session)
            environment["settings"] = settings
            environment["s3db"] = current.s3db
            # Retain certain globals (extend as needed):
            g = globals()
            environment["s3base"] = g.get("s3base")
            environment["s3_redirect_default"] = g.get("s3_redirect_default")
            page = run_controller_in(request.controller, alt_function, environment)
            if isinstance(page, dict):
                response._vars = page
                response._view_environment.update(page)
                run_view_in(response._view_environment)
                page = response.body.getvalue()
            # Set default headers if not set
            from gluon.contenttype import contenttype
            default_headers = [
                ("Content-Type", contenttype("." + request.extension)),
                ("Cache-Control",
                 "no-store, no-cache, must-revalidate, post-check=0, pre-check=0"),
                ("Expires", time.strftime("%a, %d %b %Y %H:%M:%S GMT",
                                          time.gmtime())),
                ("Pragma", "no-cache")]
            for key, value in default_headers:
                response.headers.setdefault(key, value)
            raise HTTP(response.status, page, **response.headers)

        else:
            item = H2(page_name)

    # tbc
    report = ""

    response.view = "index.html"
    return dict(item=item, report=report)

# =============================================================================
def cms_documentation(r, default_page, default_url):
    """
        Render an online documentation page, to be called from prep

        @param r: the S3Request
        @param default_page: the default page name
        @param default_url: the default URL if no contents found
    """

    row = r.record
    if not row:
        # Find the CMS page
        name = r.get_vars.get("name", default_page)
        table = r.resource.table
        query = (table.name == name) & (table.deleted != True)
        row = current.db(query).select(table.id,
                                       table.title,
                                       table.body,
                                       limitby=(0, 1)).first()
    if not row:
        if name != default_page:
            # Error - CMS page not found
            r.error(404, current.T("Page not found"),
                    next=URL(args=current.request.args, vars={}),
                    )
        else:
            # No CMS contents for module homepage found at all
            # => redirect to default page (preserving all errors)
            from s3 import s3_redirect_default
            s3_redirect_default(default_url)

    # Render the page
    from s3 import S3XMLContents
    return {"bypass": True,
            "output": {"title": row.title,
                       "contents": S3XMLContents(row.body),
                       },
            }

# =============================================================================
class S3CMS(S3Method):
    """
        Class to generate a Rich Text widget to embed in a page
    """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Entry point to apply cms method to S3Requests
            - produces a full page with a Richtext widget

            @param r: the S3Request
            @param attr: dictionary of parameters for the method handler

            @return: output object to send to the view
        """

        # Not Implemented
        r.error(405, current.ERROR.BAD_METHOD)

    # -------------------------------------------------------------------------
    def widget(self, r, method="cms", widget_id=None, **attr):
        """
            Render a Rich Text widget suitable for use in a page such as
            S3Summary

            @param method: the widget method
            @param r: the S3Request
            @param attr: controller attributes

            @ToDo: Support comments
        """

        if not current.deployment_settings.has_module("cms"):
            return ""

        return self.resource_content(r.controller,
                                     r.function,
                                     r.id,
                                     widget_id)

    # -------------------------------------------------------------------------
    @staticmethod
    def resource_content(module,
                         resource,
                         record=None,
                         widget_id=None,
                         hide_if_empty=False):
        """
            Render resource-related CMS contents

            @param module: the module prefix
            @param resource: the resource name (without prefix)
            @param record: the record ID (optional)
            @param widget_id: the DOM node ID for the CMS widget
            @param hide_if_empty: return an empty string when there is no
                                  contents rather than a blank DIV
        """

        db = current.db
        table = current.s3db.cms_post
        ltable = db.cms_post_module
        query = (ltable.module == module) & \
                (ltable.resource == resource) & \
                (ltable.record == record) & \
                (ltable.post_id == table.id) & \
                (table.deleted != True)
        _item = db(query).select(table.id,
                                 table.body,
                                 limitby=(0, 1)).first()
        # @ToDo: Replace this crude check with?
        #if current.auth.s3_has_permission("update", r.table, record_id=r.id):
        auth = current.auth
        ADMIN = auth.get_system_roles().ADMIN
        ADMIN = auth.s3_has_role(ADMIN)
        if ADMIN:
            if current.response.s3.crud.formstyle == "bootstrap":
                _class = "btn"
            else:
                _class = "action-btn"
            url_vars = {"module": module,
                        "resource": resource,
                        }
            if record:
                url_vars["record"] = record
            if _item:
                item = DIV(XML(_item.body),
                           A(current.T("Edit"),
                             _href=URL(c="cms", f="post",
                                       args = [_item.id, "update"],
                                       vars = url_vars,
                                       ),
                             _class="%s cms-edit" % _class,
                             ))
            else:
                item = A(current.T("Edit"),
                         _href=URL(c="cms", f="post",
                                   args = "create",
                                   vars = url_vars,
                                   ),
                         _class="%s cms-edit" % _class,
                         )
        elif _item:
            item = XML(_item.body)
        else:
            item = ""

        if item != "" or not hide_if_empty:
            output = DIV(item, _id=widget_id, _class="cms_content")
        else:
            output = item
        return output

# =============================================================================
def cms_configure_newsfeed_post_fields():
    """
        Customize cms_post fields for the Newsfeed / Home Pages
    """

    s3db = current.s3db
    s3 = current.response.s3
    settings = current.deployment_settings

    org_field = settings.get_cms_organisation()
    if org_field == "created_by$organisation_id":
        current.auth.settings.table_user.organisation_id.represent = \
            s3db.org_organisation_represent
    elif org_field == "post_organisation.organisation_id":
        s3db.cms_post_organisation.organisation_id.label = ""

    org_group_field = settings.get_cms_organisation_group()
    if org_group_field == "created_by$org_group_id":
        current.auth.settings.table_user.org_group_id.represent = \
            s3db.org_organisation_group_represent
    elif org_group_field == "post_organisation_group.group_id":
        s3db.cms_post_organisation_group.group_id.label = ""

    table = s3db.cms_post
    table.series_id.requires = table.series_id.requires.other

    contact_field = settings.get_cms_person()
    if contact_field == "created_by":
        table.created_by.represent = s3_auth_user_represent_name
    elif contact_field == "person_id":
        field = table.person_id
        field.readable = True
        field.writable = True
        field.comment = None
        field.widget = S3AddPersonWidget(controller="pr")

    field = table.location_id
    field.label = ""
    field.represent = s3db.gis_LocationRepresent(sep=" | ")
    # Required
    field.requires = IS_LOCATION()

    list_fields = ["series_id",
                   "location_id",
                   "date",
                   ]
    lappend = list_fields.append

    if settings.get_cms_show_titles():
        lappend("title")

    lappend("body")

    if contact_field:
        lappend(contact_field)
    if org_field:
        lappend(org_field)
    if org_group_field:
        lappend(org_group_field)

    if settings.get_cms_show_attachments():
        lappend("document.file")

    if settings.get_cms_show_links():
        lappend("document.url")

    if settings.get_cms_show_events():
        lappend("event_post.event_id")

    if settings.get_cms_location_click_filters():
        script = \
'''S3.filter_location=function(d){var cb
for(var p in d){cb=$('input[name="multiselect_post-cms_post_location_id-location-filter-L'+p+'"][value="'+d[p]+'"]')
if(!cb.prop('checked')){cb.click()}}}'''
        s3.jquery_ready.append(script)
        # Which levels of Hierarchy are we using?
        levels = current.gis.get_relevant_hierarchy_levels()

        for level in levels:
            lappend("location_id$%s" % level)

    if settings.get_cms_show_tags():
        lappend("tag.name")
        if s3.debug:
            s3.scripts.append("/%s/static/scripts/tag-it.js" % current.request.application)
        else:
            s3.scripts.append("/%s/static/scripts/tag-it.min.js" % current.request.application)
        if current.auth.s3_has_permission("update", current.db.cms_tag_post):
            readonly = '''afterTagAdded:function(event,ui){
 if(ui.duringInitialization){return}
 var post_id=$(this).attr('data-post_id')
 var url=S3.Ap.concat('/cms/post/',post_id,'/add_tag/',ui.tagLabel)
 $.getS3(url)
},afterTagRemoved:function(event,ui){
 var post_id=$(this).attr('data-post_id')
 var url=S3.Ap.concat('/cms/post/',post_id,'/remove_tag/',ui.tagLabel)
 $.getS3(url)
},'''
        else:
            readonly = '''readOnly:true'''
        script = \
'''S3.tagit=function(){$('.s3-tags').tagit({autocomplete:{source:'%s'},%s})}
S3.tagit()
S3.redraw_fns.push('tagit')''' % (URL(c="cms", f="tag",
                                      args="search_ac.json"),
                                  readonly)
        s3.jquery_ready.append(script)

    s3db.configure("cms_post",
                   list_fields = list_fields,
                   )

    return table

# =============================================================================
def cms_post_list_layout(list_id, item_id, resource, rfields, record):
    """
        Default dataList item renderer for CMS Posts on the
        Home & News Feed pages.

        @param list_id: the HTML ID of the list
        @param item_id: the HTML ID of the item
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
    """

    record_id = record["cms_post.id"]
    item_class = "thumbnail"

    db = current.db
    s3db = current.s3db
    settings = current.deployment_settings
    NONE = current.messages["NONE"]

    org_field = settings.get_cms_organisation()
    # Convert to the right format for this context
    if org_field == "created_by$organisation_id":
        org_field = "auth_user.organisation_id"
    elif org_field == "post_organisation.organisation_id":
        org_field = "cms_post_organisation.organisation_id"

    org_group_field = settings.get_cms_organisation_group()
    # Convert to the right format for this context
    if org_group_field == "created_by$org_group_id":
        org_group_field = "auth_user.org_group_id"
    elif org_group_field == "post_organisation_group.group_id":
        org_group_field = "cms_post_organisation_group.group_id"

    raw = record._row
    body = record["cms_post.body"]
    series_id = raw["cms_post.series_id"]

    title  = record["cms_post.title"]
    if title and title != NONE:
        subtitle = [DIV(title,
                        _class="card-subtitle"
                        )
                    ]
    else:
        subtitle = []

    for event_resource in ["event", "incident"]:
        label = record["event_post.%s_id" % event_resource]
        if label and label != NONE:
            link=URL(c="event", f=event_resource,
                     args=[raw["event_post.%s_id" % event_resource],
                          "profile"]
                     )
            subtitle.append(DIV(A(ICON(event_resource),
                                  label,
                                  _href=link,
                                  _target="_blank",
                                  ),
                                _class="card-subtitle"
                                ))
    if subtitle:
        subtitle.append(body)
        body = TAG[""](*subtitle)

    # Allow records to be truncated
    # (not yet working for HTML)
    body = DIV(body,
               _class="s3-truncate",
               )

    date = record["cms_post.date"]
    date = SPAN(date,
                _class="date-title",
                )

    location_id = raw["cms_post.location_id"]
    if location_id:
        location = record["cms_post.location_id"]
        if settings.get_cms_location_click_filters():
            # Which levels of Hierarchy are we using?
            levels = current.gis.get_relevant_hierarchy_levels()

            data = {}
            for level in levels:
                data[level[1:]] = raw["gis_location.%s" % level]
            onclick = '''S3.filter_location(%s)''' % json.dumps(data, separators=SEPARATORS)
            location = SPAN(A(location,
                              _href="#",
                              _onclick=onclick,
                              ),
                            _class="location-title",
                            )
        else:
            location_url = URL(c="gis", f="location", args=[location_id, "profile"])
            location = SPAN(A(location,
                              _href=location_url,
                              ),
                            _class="location-title",
                            )
    else:
        location = ""

    person = ""
    contact_field = settings.get_cms_person()
    if contact_field == "created_by":
        author_id = raw["cms_post.created_by"]
        person = record["cms_post.created_by"]

        # @ToDo: Bulk lookup
        ltable = s3db.pr_person_user
        ptable = db.pr_person
        query = (ltable.user_id == author_id) & \
                (ltable.pe_id == ptable.pe_id)
        row = db(query).select(ptable.id,
                               limitby=(0, 1)
                               ).first()
        if row:
            person_id = row.id
        else:
            person_id = None
    elif contact_field == "person_id":
        person_id = raw["cms_post.person_id"]
        if person_id:
            person = record["cms_post.person_id"]
    else:
        person_id = None

    if person:
        if person_id:
            # @ToDo: deployment_setting for controller to use?
            person_url = URL(c="pr", f="person", args=[person_id])
        else:
            person_url = "#"
        person = A(person,
                   _href=person_url,
                   )

    avatar = ""

    organisation = ""
    if org_field:
        organisation_id = raw[org_field]
        if organisation_id:
            organisation = record[org_field]
            org_url = URL(c="org", f="organisation", args=[organisation_id, "profile"])
            organisation = A(organisation,
                             _href=org_url,
                             _class="card-organisation",
                             )

            # Avatar
            # Try Organisation Logo
            otable = db.org_organisation
            row = db(otable.id == organisation_id).select(otable.logo,
                                                          limitby=(0, 1)
                                                          ).first()
            if row and row.logo:
                logo = URL(c="default", f="download", args=[row.logo])
                avatar = IMG(_src=logo,
                             _height=50,
                             _width=50,
                             _style="padding-right:5px",
                             _class="media-object")
            else:
                avatar = organisation
            avatar = A(avatar,
                       _href=org_url,
                       _class="pull-left",
                       )

    org_group = ""
    if org_group_field:
        org_group_id = raw[org_group_field]
        if org_group_id:
            org_group = record[org_group_field]
            org_group_url = URL(c="org", f="group", args=[org_group_id, "profile"])
            org_group = A(org_group,
                          _href=org_group_url,
                          _class="card-org-group",
                          )

    if not avatar and person_id:
        # Personal Avatar
        avatar = s3_avatar_represent(person_id,
                                     tablename="pr_person",
                                     _class="media-object")

        avatar = A(avatar,
                   _href=person_url,
                   _class="pull-left",
                   )

    if person and organisation:
        card_person = DIV(person,
                          " - ",
                          organisation,
                          _class="card-person",
                          )
    elif person and org_group:
        card_person = DIV(person,
                          " - ",
                          org_group,
                          _class="card-person",
                          )
    elif person:
        card_person = DIV(person,
                          _class="card-person",
                          )
    #elif organisation:
    #    card_person = DIV(organisation,
    #                      _class="card-person",
    #                      )
    elif org_group:
        card_person = DIV(org_group,
                          _class="card-person",
                          )
    else:
        card_person = DIV(_class="card-person",
                          )

    permit = current.auth.s3_has_permission
    table = db.cms_post
    updateable = permit("update", table, record_id=record_id)

    if settings.get_cms_show_tags():
        tags = raw["cms_tag.name"]
        if tags or updateable:
            tag_list = UL(_class="s3-tags",
                          )
            tag_list["_data-post_id"] = record_id
        else:
            tag_list = ""
        if tags:
            if not isinstance(tags, list):
                tags = [tags]#.split(", ")
            for tag in tags:
                tag_item = LI(tag)
                tag_list.append(tag_item)
        tags = tag_list
    else:
        tags = ""

    T = current.T
    if series_id:
        series = record["cms_post.series_id"]
        translate = settings.get_L10n_translate_cms_series()
        if translate:
            series_title = T(series)
        else:
            series_title = series
    else:
        series_title = series = ""

    request = current.request

    # Tool box
    if updateable:
        if request.function == "newsfeed":
            fn = "newsfeed"
        else:
            fn = "post"
        edit_btn = A(ICON("edit"),
                     _href=URL(c="cms", f=fn,
                               args=[record_id, "update.popup"],
                               vars={"refresh": list_id,
                                     "record": record_id}
                               ),
                     _class="s3_modal",
                     _title=T("Edit %(type)s") % dict(type=series_title),
                     )
    else:
        edit_btn = ""
    if permit("delete", table, record_id=record_id):
        delete_btn = A(ICON("delete"),
                       _class="dl-item-delete",
                       )
    else:
        delete_btn = ""
    user = current.auth.user
    if user and settings.get_cms_bookmarks():
        ltable = s3db.cms_post_user
        query = (ltable.post_id == record_id) & \
                (ltable.user_id == user.id)
        exists = db(query).select(ltable.id,
                                  limitby=(0, 1)
                                  ).first()
        if exists:
            bookmark_btn = A(ICON("bookmark"),
                             _onclick="$.getS3('%s',function(){$('#%s').datalist('ajaxReloadItem',%s)})" %
                                (URL(c="cms", f="post",
                                     args=[record_id, "remove_bookmark"]),
                                 list_id,
                                 record_id),
                             _title=T("Remove Bookmark"),
                             )
        else:
            bookmark_btn = A(ICON("bookmark-empty"),
                             _onclick="$.getS3('%s',function(){$('#%s').datalist('ajaxReloadItem',%s)})" %
                                (URL(c="cms", f="post",
                                     args=[record_id, "add_bookmark"]),
                                 list_id,
                                 record_id),
                             _title=T("Add Bookmark"),
                             )
    else:
        bookmark_btn = ""
    toolbox = DIV(bookmark_btn,
                  edit_btn,
                  delete_btn,
                  _class="edit-bar fright",
                  )

    # Dropdown of available documents
    documents = raw["doc_document.file"]
    if documents:
        if not isinstance(documents, list):
            documents = [documents]
        doc_list_id = "attachments-%s" % item_id
        doc_list = UL(_class="f-dropdown dropdown-menu",
                      _role="menu",
                      _id=doc_list_id,
                      data={"dropdown-content": ""},
                      )
        retrieve = db.doc_document.file.retrieve
        for doc in documents:
            try:
                doc_name = retrieve(doc)[0]
            except (IOError, TypeError):
                doc_name = NONE
            doc_url = URL(c="default", f="download",
                          args=[doc])
            doc_item = LI(A(ICON("file"),
                            " ",
                            doc_name,
                            _href=doc_url,
                            ),
                          _role="menuitem",
                          )
            doc_list.append(doc_item)
        docs = DIV(A(ICON("attachment"),
                     SPAN(_class="caret"),
                     _class="btn dropdown-toggle dropdown",
                     _href="#",
                     data={"toggle": "dropdown",
                           "dropdown": doc_list_id,
                           },
                     ),
                   doc_list,
                   _class="btn-group attachments dropdown pull-right",
                   )
    else:
        docs = ""

    links = raw["doc_document.url"]
    if links:
        if not isinstance(links, list):
            links = [links]
        link_list = DIV(_class="media card-links")
        for link in links:
            link_item = A(ICON("link"),
                          " ",
                          link,
                          _href=link,
                          _target="_blank",
                          _class="card-link",
                          )
            link_list.append(link_item)
    else:
        link_list = ""

    if "profile" in request.args:
        # Single resource list
        # - don't show series_title
        if settings.get_cms_show_titles():
            title = raw["cms_post.title"] or ""
        else:
            title = ""
        card_label = SPAN(" %s" % title,
                          _class="card-title")
    else:
        # Mixed resource lists (Home, News Feed)
        icon = series.lower().replace(" ", "_")
        series_title = SPAN(" %s" % series_title,
                            _class="card-title")
        raw_title = raw["cms_post.title"]
        if settings.get_cms_show_titles() and raw_title:
            title = SPAN(s3_truncate(raw_title), _class="card-title2")
            card_label = TAG[""](ICON(icon),
                                 series_title,
                                 title,
                                 )
        else:
            card_label = TAG[""](ICON(icon),
                                 series_title,
                                 )
        # Type cards
        if series == "Alert":
            # Apply additional highlighting for Alerts
            item_class = "%s disaster" % item_class

    # Render the item
    if series == "Event" and "newsfeed" not in request.args: # and request.function != "newsfeed"
        # Events on Homepage have a different header
        date.add_class("event")
        header = DIV(date,
                     location,
                     toolbox,
                     _class="card-header",
                     )
    else:
        header = DIV(card_label,
                     location,
                     date,
                     toolbox,
                     _class="card-header",
                     )

    item = DIV(header,
               DIV(avatar,
                   DIV(DIV(body,
                           card_person,
                           _class="media",
                           ),
                       _class="media-body",
                       ),
                   _class="media",
                   ),
               tags,
               docs,
               link_list,
               _class=item_class,
               _id=item_id,
               )

    return item

# =============================================================================
class cms_Calendar(S3Method):
    """
        Display Posts on a Calendar format

       @ToDo: Customisable Date Range
                - currently hardcoded to 1 day in past, today & 5 days ahead
       @ToDo: Interactive version
                - drag/drop entries
                - edit entries
       @ToDo: PDF/XLS representations
    """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Entry point for REST API

            @param r: the S3Request
            @param attr: controller arguments
        """

        if r.name == "post":
            if r.representation == "html":
                output = self.html(r, **attr)
                return output
            #elif r.representation == "pdf":
            #    output = self.pdf(r, **attr)
            #    return output
            #elif r.representation == "xls":
            #    output = self.xls(r, **attr)
            #    return output
        r.error(405, current.ERROR.BAD_METHOD)

    # -------------------------------------------------------------------------
    def _extract(self, days, r, **attr):
        """
            Extract the Data
        """

        # Respect any filters present
        resource = r.resource

        # Provide additional Filter based on days
        resource.add_filter((FS("date") > days[0].replace(hour = 0, minute=0, second=0, microsecond=0)) & \
                            (FS("date") < days[-1].replace(hour = 23, minute=59, second=59)))

        # @ToDo: Configurable fields (location_id not always relevant, but e.g. Author may be)
        fields = ["body",
                  "date",
                  "location_id",
                  "post_module.module",
                  "post_module.resource",
                  "post_module.record",
                  ]

        data = resource.select(fields, represent=True, raw_data=True)

        # Reformat posts into Array of rows and columns (days)
        # Need to start with the columns as we don't yet know how many rows we need
        cols = []
        cappend = cols.append
        max_rows = []
        mappend = max_rows.append
        # Initialise arrays
        for _ in days:
            cappend([])
            mappend(0)

        # Place each record into the correct day's column
        len_days = len(days)
        for record in data.rows:
            date = record._row["cms_post.date"]
            for i in range(len_days):
                if date < days[i + 1]:
                    cols[i].append(record)
                    max_rows[i] += 1
                    break

        # Now convert to rows
        rows = []
        rappend = rows.append
        len_rows = max(max_rows)
        # Initialise array
        for i in range(len_rows):
            rappend([])

        for row in rows:
            rappend = row.append
            for col in cols:
                if len(col):
                    rappend(col.pop())
                else:
                    rappend(Storage())

        return rows

    # -------------------------------------------------------------------------
    def html(self, r, **attr):
        """
            HTML Representation
        """

        T = current.T

        now = current.request.now
        timedelta = datetime.timedelta

        # @ToDo: Make this configurable
        days = (now - timedelta(days = 1), # Yesterday
                now,                       # Today
                now + timedelta(days = 1), # Tomorrow
                now + timedelta(days = 2),
                now + timedelta(days = 3),
                now + timedelta(days = 4),
                now + timedelta(days = 5),
                )

        posts = self._extract(days, r, **attr)

        item = TABLE()
        title_row = TR()
        rappend = title_row.append
        for day in days:
            rappend(TD(day.strftime("%A")))
        item.append(title_row)

        for row in posts:
            data_row = TR()
            rappend = data_row.append
            row.reverse()
            for day in days:
                post = row.pop()
                if post:
                    rappend(TD(self.post_layout(post)))
                else:
                    rappend(TD())
            item.append(data_row)

        output = dict(item=item)
        output["title"] = T("Weekly Schedule")

        # Maintain RHeader for consistency
        if "rheader" in attr:
            rheader = attr["rheader"](r)
            if rheader:
                output["rheader"] = rheader

        current.response.view = "simple.html"
        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def post_layout(post):
        """
            Format a calendar entry
        """

        title = post["cms_post.body"]
        record_id = post["cms_post_module.record"]
        if record_id:
            title = A(title,
                      _href = URL(c = str(post["cms_post_module.module"]),
                                  f = str(post["cms_post_module.resource"]), # gluon does an isinstance(str)
                                  args = record_id,
                                  ),
                      _target = "_blank",
                      )

        location = post["cms_post.location_id"]

        return DIV(title,
                   BR(),
                   location,
                   )

# =============================================================================
class cms_TagList(S3Method):
    """
        Return a list of available Tags
        - suitable for use in Tag-It's AutoComplete
    """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Entry point for REST API

            @param r: the S3Request
            @param attr: controller arguments
        """

        if r.representation == "json":
            table = current.s3db.cms_tag
            tags = current.db(table.deleted == False).select(table.name)
            tag_list = [tag.name for tag in tags]
            output = json.dumps(tag_list, separators=SEPARATORS)
            current.response.headers["Content-Type"] = "application/json"
            return output

        r.error(405, current.ERROR.BAD_METHOD)

# END =========================================================================
