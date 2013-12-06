# -*- coding: utf-8 -*-

""" Sahana Eden Content Management System Model

    @copyright: 2012-13 (c) Sahana Software Foundation
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

__all__ = ["S3ContentModel",
           "S3ContentMapModel",
           "S3ContentOrgModel",
           #"S3ContentOrgGroupModel",
           "S3ContentUserModel",
           "cms_index",
           "cms_rheader",
           "cms_customize_post_fields",
           "cms_render_posts",
           "S3CMS",
           ]

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

from gluon import *
from gluon.storage import Storage
from ..s3 import *
from s3layouts import S3AddResourceLink

# =============================================================================
class S3ContentModel(S3Model):
    """
        Content Management System
    """

    names = ["cms_series",
             "cms_post",
             "cms_post_id",
             "cms_post_module",
             #"cms_post_record",
             "cms_tag",
             "cms_tag_post",
             "cms_comment",
             ]

    def model(self):

        T = current.T
        db = current.db
        add_component = self.add_component
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
        table = define_table(tablename,
                             Field("name",
                                   length=255,
                                   notnull=True, unique=True,
                                   label=T("Name")),
                             Field("avatar", "boolean",
                                   default=False,
                                   represent = s3_yes_no_represent,
                                   label=T("Show author picture?")),
                             Field("location", "boolean",
                                   default=False,
                                   represent = s3_yes_no_represent,
                                   label=T("Show Location?")),
                             Field("richtext", "boolean",
                                   default=True,
                                   represent = s3_yes_no_represent,
                                   label=T("Rich Text?")),
                             Field("replies", "boolean",
                                   default=False,
                                   represent = s3_yes_no_represent,
                                   label=T("Comments permitted?")),
                             s3_comments(),
                             # Multiple Roles (@ToDo: Implement the restriction)
                             s3_roles_permitted(readable = False,
                                                writable = False
                                                ),
                             *s3_meta_fields())

        # CRUD Strings
        ADD_SERIES = T("Add Series")
        crud_strings[tablename] = Storage(
            title_create = ADD_SERIES,
            title_display = T("Series Details"),
            title_list = T("Series"),
            title_update = T("Edit Series"),
            title_search = T("Search Series"),
            title_upload = T("Import Series"),
            subtitle_create = T("Add New Series"),
            label_list_button = T("List Series"),
            label_create_button = ADD_SERIES,
            msg_record_created = T("Series added"),
            msg_record_modified = T("Series updated"),
            msg_record_deleted = T("Series deleted"),
            msg_list_empty = T("No series currently defined"))

        # Reusable field
        translate = settings.get_L10n_translate_cms_series()
        represent = S3Represent(lookup=tablename, translate=translate)
        series_id = S3ReusableField("series_id", table,
                                    readable = False,
                                    writable = False,
                                    represent = represent,
                                    requires = IS_NULL_OR(
                                                IS_ONE_OF(db, "cms_series.id",
                                                          represent)),
                                    ondelete = "CASCADE")

        # Resource Configuration
        configure(tablename,
                  onaccept = self.cms_series_onaccept,
                  create_next=URL(f="series", args=["[id]", "post"]))

        # Components
        add_component("cms_post", cms_series="series_id")

        # ---------------------------------------------------------------------
        # Posts
        # - single blocks of rich text which can be embedded into a page,
        #   be viewed as full pages or as part of a Series
        #

        tablename = "cms_post"
        table = define_table(tablename,
                             self.super_link("doc_id", "doc_entity"),
                             series_id(),
                             Field("name", #notnull=True,
                                   comment=T("This isn't visible to the published site, but is used to allow menu items to point to the page"),
                                   label=T("Name")),
                             Field("title",
                                   comment=T("The title of the page, as seen in the browser (optional)"),
                                   label=T("Title")),
                             Field("body", "text", notnull=True,
                                   widget = s3_richtext_widget,
                                   label=T("Body")),
                             # @ToDo: Move this to link table?
                             # - although this makes widget hard!
                             self.gis_location_id(),
                             # @ToDo: Move this to link table?
                             # - although this makes widget hard!
                             self.pr_person_id(label=T("Contact"),
                                               # Enable only in certain conditions
                                               readable = False,
                                               writable = False,
                                               ),
                             Field("avatar", "boolean",
                                   default=False,
                                   represent = s3_yes_no_represent,
                                   label=T("Show author picture?")),
                             Field("replies", "boolean",
                                   default=False,
                                   represent = s3_yes_no_represent,
                                   label=T("Comments permitted?")),
                             s3_datetime(default = "now"),
                             # @ToDo: Also have a datetime for 'Expires On'
                             Field("expired", "boolean",
                                   default=False,
                                   represent = s3_yes_no_represent,
                                   label=T("Expired?")),
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
        ADD_POST = T("Add Post")
        crud_strings[tablename] = Storage(
            title_create = ADD_POST,
            title_display = T("Post Details"),
            title_list = T("Posts"),
            title_update = T("Edit Post"),
            title_search = T("Search Posts"),
            title_upload = T("Import Posts"),
            subtitle_create = T("Add New Post"),
            label_list_button = T("List Posts"),
            label_create_button = ADD_POST,
            msg_record_created = T("Post added"),
            msg_record_modified = T("Post updated"),
            msg_record_deleted = T("Post deleted"),
            msg_list_empty = T("No posts currently available"))

        # Reusable field
        represent = S3Represent(lookup=tablename)
        post_id = S3ReusableField("post_id", table,
                                  label = T("Post"),
                                  sortby="name",
                                  requires = IS_NULL_OR(
                                                IS_ONE_OF(db, "cms_post.id",
                                                          represent)),
                                  represent = represent,
                                  comment = S3AddResourceLink(c="cms", f="post",
                                                              title=ADD_POST,
                                                              tooltip=T("A block of rich text which could be embedded into a page, viewed as a complete page or viewed as a list of news items.")),
                                  ondelete = "CASCADE")

        # Resource Configuration
        configure(tablename,
                  context = {"event": "event.id",
                             "location": "location_id",
                             "organisation": "created_by$organisation_id",
                             },
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
                  list_orderby = ~table.created_on,
                  onaccept = self.cms_post_onaccept,
                  orderby = ~table.created_on,
                  summary = [{"name": "table",
                              "label": "Table",
                              "widgets": [{"method": "datatable"}]
                              },
                             #{"name": "report",
                             # "label": "Report",
                             # "widgets": [{"method": "report2",
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
        add_component("cms_comment", cms_post="post_id")

        add_component("cms_post_module", cms_post="post_id")

        add_component("cms_post_user", cms_post=dict(name="bookmark",
                                                     joinby="post_id"))

        add_component("cms_tag", cms_post=dict(link="cms_tag_post",
                                               joinby="post_id",
                                               key="tag_id",
                                               actuate="hide"))

        # For FilterWidget
        add_component("cms_post_tag", cms_post="post_id")

        add_component("cms_post_organisation",
                      cms_post=dict(joinby="post_id",
                                    # @ToDo: deployment_setting
                                    multiple=False,
                                    ))

        # For InlineForm to tag Posts to Events
        add_component("event_event_post", cms_post="post_id")

        # For Profile to filter appropriately
        add_component("event_event", cms_post=dict(link="event_event_post",
                                                   joinby="post_id",
                                                   key="event_id",
                                                   actuate="hide"))

        # Custom Methods
        set_method("cms", "post",
                   method="add_tag",
                   action=self.cms_add_tag)

        set_method("cms", "post",
                   method="remove_tag",
                   action=self.cms_remove_tag)

        set_method("cms", "post",
                   method="add_bookmark",
                   action=self.cms_add_bookmark)

        set_method("cms", "post",
                   method="remove_bookmark",
                   action=self.cms_remove_bookmark)

        # ---------------------------------------------------------------------
        # Modules/Resources <> Posts link table
        #
        tablename = "cms_post_module"
        table = define_table(tablename,
                             post_id(empty=False),
                             Field("module",
                                   comment=T("If you specify a module then this will be used as the text in that module's index page"),
                                   label=T("Module")
                                   ),
                             Field("resource",
                                   comment=T("If you specify a resource then this will be used as the text in that resource's summary page"),
                                   label=T("Resource")
                                   ),
                             *s3_meta_fields())

        # CRUD Strings
        ADD_POST = T("Add Post")
        crud_strings[tablename] = Storage(
            title_create = ADD_POST,
            title_display = T("Post Details"),
            title_list = T("Posts"),
            title_update = T("Edit Post"),
            subtitle_create = T("Add New Post"),
            label_list_button = T("List Posts"),
            label_create_button = ADD_POST,
            msg_record_created = T("Post set as Module/Resource homepage"),
            msg_record_modified = T("Post updated"),
            msg_record_deleted = T("Post removed"),
            msg_list_empty = T("No posts currently set as module/resource homepages"))

        # ---------------------------------------------------------------------
        # Records <> Posts link table
        # - used to handle record history
        #
        #tablename = "cms_post_record"
        #table = define_table(tablename,
        #                     post_id(empty=False),
        #                     Field("tablename"),
        #                     Field("record", "integer"),
        #                     Field("url"),
        #                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Tags
        #
        tablename = "cms_tag"
        table = define_table(tablename,
                             Field("name",
                                   label=T("Tag")),
                             s3_comments(),
                             # Multiple Roles (@ToDo: Implement the restriction)
                             #s3_roles_permitted(readable = False,
                             #                   writable = False
                             #                   ),
                             *s3_meta_fields())

        # CRUD Strings
        ADD_TAG = T("Add Tag")
        crud_strings[tablename] = Storage(
            title_create = ADD_TAG,
            title_display = T("Tag Details"),
            title_list = T("Tags"),
            title_update = T("Edit Tag"),
            title_search = T("Search Tags"),
            title_upload = T("Import Tags"),
            subtitle_create = T("Add New Tag"),
            label_list_button = T("List Tags"),
            label_create_button = ADD_TAG,
            msg_record_created = T("Tag added"),
            msg_record_modified = T("Tag updated"),
            msg_record_deleted = T("Tag deleted"),
            msg_list_empty = T("No tags currently defined"))

        # ---------------------------------------------------------------------
        # Tags <> Posts link table
        #
        tablename = "cms_tag_post"
        table = define_table(tablename,
                             post_id(empty=False),
                             Field("tag_id", "reference cms_tag"),
                             *s3_meta_fields())

        # CRUD Strings
        ADD_TAG = T("Tag Post")
        crud_strings[tablename] = Storage(
            title_create = ADD_TAG,
            title_display = T("Tag Details"),
            title_list = T("Tags"),
            title_update = T("Edit Tag"),
            title_search = T("Search Tags"),
            title_upload = T("Import Tags"),
            subtitle_create = T("Add New Tag"),
            label_list_button = T("List Tagged Posts"),
            label_create_button = ADD_TAG,
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
        table = define_table(tablename,
                             Field("parent", "reference cms_comment",
                                   requires = IS_NULL_OR(
                                                IS_ONE_OF(db, "cms_comment.id")),
                                   readable=False),
                             post_id(empty=False),
                             Field("body", "text", notnull=True,
                                   label = T("Comment")),
                             *s3_meta_fields())

        # Resource Configuration
        configure(tablename,
                  list_fields=["id",
                               "post_id",
                               "created_by",
                               "modified_on"
                               ])

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict(cms_post_id = post_id,
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def cms_series_onaccept(form):
        """
            Cascade values down to all component Posts
        """

        vars = form.vars

        db = current.db
        table = db.cms_post
        query = (table.series_id == vars.id)
        db(query).update(avatar = vars.avatar,
                         replies = vars.replies,
                         roles_permitted = vars.roles_permitted,
                         )

        return

    # -------------------------------------------------------------------------
    @staticmethod
    def cms_post_onaccept(form):
        """
           Handle the case where the page is for a Module home page,
           Resource Summary page or Map Layer
        """

        db = current.db
        s3db = current.s3db
        form_vars = form.vars
        post_id = form_vars.id
        get_vars = current.request.get_vars
        module = get_vars.get("module", None)
        if module:
            table = db.cms_post_module
            query = (table.module == module)
            resource = get_vars.get("resource", None)
            if resource:
                # Resource Summary page
                query &= (table.resource == resource)
            else:
                # Module home page
                query &= ((table.resource == None) | \
                          (table.resource == "index"))
            result = db(query).update(post_id=post_id)
            if not result:
                table.insert(post_id=post_id,
                             module=module,
                             resource=resource,
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
    def cms_add_tag(r, **attr):
        """
            Add a Tag to a Post

            S3Method for interactive requests
            - designed to be called as an afterTagAdded callback to tag-it.js
        """

        post_id = r.id
        if not post_id or len(r.args) < 3:
            raise HTTP(501, current.messages.BADMETHOD)

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

        output = current.xml.json_message(True, 200, "Tag Added")
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
            raise HTTP(501, current.messages.BADMETHOD)

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
                resource = current.s3db.resource("cms_tag_post", exists.id)
                resource.delete()

        output = current.xml.json_message(True, 200, "Tag Removed")
        current.response.headers["Content-Type"] = "application/json"
        return output

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
            raise HTTP(501, current.messages.BADMETHOD)

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

        output = current.xml.json_message(True, 200, "Bookmark Added")
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
            raise HTTP(501, current.messages.BADMETHOD)

        db = current.db
        ltable = db.cms_post_user
        query = (ltable.post_id == post_id) & \
                (ltable.user_id == user_id)
        exists = db(query).select(ltable.id,
                                  ltable.deleted,
                                  limitby=(0, 1)
                                  ).first()
        if exists and not exists.deleted:
            resource = current.s3db.resource("cms_post_user", exists.id)
            resource.delete()

        output = current.xml.json_message(True, 200, "Bookmark Removed")
        current.response.headers["Content-Type"] = "application/json"
        return output

# =============================================================================
class S3ContentMapModel(S3Model):
    """
        Use of the CMS to provide extra data about Map Layers
    """

    names = ["cms_post_layer",
             ]

    def model(self):

        # ---------------------------------------------------------------------
        # Layers <> Posts link table
        #
        tablename = "cms_post_layer"
        table = self.define_table(tablename,
                                  self.cms_post_id(empty=False),
                                  self.super_link("layer_id", "gis_layer_entity"),
                                  *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict()

# =============================================================================
class S3ContentOrgModel(S3Model):
    """
        Link Posts to Organisations
    """

    names = ["cms_post_organisation",
             ]

    def model(self):

        # ---------------------------------------------------------------------
        # Organisations <> Posts link table
        #
        tablename = "cms_post_organisation"
        table = self.define_table(tablename,
                                  self.cms_post_id(empty=False),
                                  self.org_organisation_id(empty=False),
                                  *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict()

# =============================================================================
class S3ContentOrgGroupModel(S3Model):
    """
        Link Posts to Organisation Groups (Coalitions)
        - currently unused
    """

    names = ["cms_post_organisation_group",
             ]

    def model(self):

        # ---------------------------------------------------------------------
        # Organisation Groups <> Posts link table
        #
        tablename = "cms_post_organisation_group"
        table = self.define_table(tablename,
                                  self.cms_post_id(empty=False),
                                  self.org_group_id(empty=False),
                                  *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict()

# =============================================================================
class S3ContentUserModel(S3Model):
    """
        Link Posts to Users to allow Users to Bookmark posts
    """

    names = ["cms_post_user",
             ]

    def model(self):

        # ---------------------------------------------------------------------
        # Users <> Posts link table
        #
        tablename = "cms_post_user"
        self.define_table(tablename,
                          self.cms_post_id(empty=False),
                          Field("user_id", current.auth.settings.table_user),
                          *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict()

# =============================================================================
def cms_rheader(r, tabs=[]):
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
    if settings.has_module("cms"):
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
            page = run_controller_in(request.controller, alt_function, environment)
            if isinstance(page, dict):
                response._vars = page
                response._view_environment.update(page)
                run_view_in(response._view_environment)
                page = response.body.getvalue()
            # Set default headers if not set
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
        r.error(405, r.ERROR.BAD_METHOD)

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

        # This is currently assuming that we're being used in a Summary page or similar
        request = current.request
        module = request.controller
        resource = request.function
        
        return self.resource_content(module, resource, widget_id)

    # -------------------------------------------------------------------------
    @staticmethod
    def resource_content(module, resource, widget_id=None):
        db = current.db
        table = current.s3db.cms_post
        ltable = db.cms_post_module
        query = (ltable.module == module) & \
                (ltable.resource == resource) & \
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
        if _item:
            if ADMIN:
                if current.response.s3.crud.formstyle == "bootstrap":
                    _class = "btn"
                else:
                    _class = "action-btn"
                item = DIV(XML(_item.body),
                           A(current.T("Edit"),
                             _href=URL(c="cms", f="post",
                                       args=[_item.id, "update"],
                                       vars={"module": module,
                                             "resource": resource
                                             }),
                             _class="%s cms-edit" % _class))
            else:
                item = XML(_item.body)
        elif ADMIN:
            if current.response.s3.crud.formstyle == "bootstrap":
                _class = "btn"
            else:
                _class = "action-btn"
            item = A(current.T("Edit"),
                     _href=URL(c="cms", f="post", args="create",
                               vars={"module": module,
                                     "resource": resource
                                     }),
                     _class="%s cms-edit" % _class)
        else:
            item = ""

        output = DIV(item, _id=widget_id, _class="cms_content")
        return output

# =============================================================================
def cms_customize_post_fields():
    """
        Customize cms_post fields for the Newsfeed / Home Pages
    """

    s3db = current.s3db
    settings = current.deployment_settings

    # Hide Labels when just 1 column in inline form
    s3db.doc_document.file.label = ""
    # @ToDo: deployment_setting for Events
    #s3db.event_event_post.event_id.label = ""

    # @ToDo: deployment_setting
    #org_field = "created_by$organisation_id"
    #current.auth.settings.table_user.organisation_id.represent = \
    #    s3db.org_organisation_represent
    org_field = "post_organisation.organisation_id"
    s3db.cms_post_organisation.organisation_id.label = ""

    table = s3db.cms_post
    table.series_id.requires = table.series_id.requires.other
    # @ToDo: deployment_setting
    #contact_field = "created_by"
    #table.created_by.represent = s3_auth_user_represent_name
    contact_field = "person_id"
    field = table.person_id
    field.readable = True
    field.writable = True
    field.comment = None
    field.requires = IS_ADD_PERSON_WIDGET2()
    field.widget = S3AddPersonWidget2(controller="pr")

    # Which levels of Hierarchy are we using?
    hierarchy = current.gis.get_location_hierarchy()
    levels = hierarchy.keys()
    if len(current.deployment_settings.get_gis_countries()) == 1:
        levels.remove("L0")

    from s3.s3validators import IS_LOCATION_SELECTOR2
    from s3.s3widgets import S3LocationSelectorWidget2
    field = table.location_id
    field.label = ""
    field.represent = s3db.gis_LocationRepresent(sep=" | ")
    field.requires = IS_LOCATION_SELECTOR2(levels=levels)
    field.widget = S3LocationSelectorWidget2(levels=levels)

    if settings.get_cms_richtext():
        table.body.represent = lambda body: XML(body)
    else:
        table.body.represent = lambda body: XML(s3_URLise(body))

    list_fields = ["series_id",
                   "location_id",
                   "date",
                   "body",
                   contact_field,
                   org_field,
                   "document.file",
                   #"event_post.event_id",
                   ]

    if settings.get_cms_show_tags():
        list_fields.append("tag.name")
        s3 = current.response.s3
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
def cms_render_posts(listid, resource, rfields, record, 
                     type = None,
                     **attr):
    """
        Custom dataList item renderer for CMS Posts on the Home & News Feed pages

        @param listid: the HTML ID for this list
        @param resource: the S3Resource to render
        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
        @param attr: additional HTML attributes for the item
    """

    pkey = "cms_post.id"

    # Construct the item ID
    if pkey in record:
        record_id = record[pkey]
        item_id = "%s-%s" % (listid, record_id)
    else:
        # template
        item_id = "%s-[id]" % listid

    item_class = "thumbnail"

    # @ToDo: deployment_setting or introspect based on list_fields
    #org_field = "auth_user.organisation_id"
    org_field = "cms_post_organisation.organisation_id"

    raw = record._row
    series_id = raw["cms_post.series_id"]
    date = record["cms_post.date"]
    body = record["cms_post.body"]

    location_id = raw["cms_post.location_id"]
    if location_id:
        location = record["cms_post.location_id"]
        location_url = URL(c="gis", f="location", args=[location_id, "profile"])
        location = SPAN(A(location,
                          _href=location_url,
                          ),
                        _class="location-title",
                        )
    else:
        location = ""

    person_id = raw["cms_post.person_id"]
    if person_id:
        person = record["cms_post.person_id"]
        person_url = URL(c="pr", f="person", args=[person_id])
        person = A(person,
                   _href=person_url,
                   )
    else:
        person = ""

    avatar = ""
    db = current.db

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
                         _style="padding-right:5px;",
                         _class="media-object")
            avatar = A(avatar,
                       _href=org_url,
                       _class="pull-left",
                       )
    else:
        organisation = ""

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
    elif person:
        card_person = DIV(person,
                          _class="card-person",
                          )
    elif organisation:
        card_person = DIV(organisation,
                          _class="card-person",
                          )

    permit = current.auth.s3_has_permission
    settings = current.deployment_settings
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
            title = T(series)
        else:
            title = series
    else:
        title = series = ""

    # Tool box
    if updateable:
        edit_btn = A(I(" ", _class="icon icon-edit"),
                     _href=URL(c="cms", f="newsfeed",
                               args=[record_id, "update.popup"],
                               vars={"refresh": listid,
                                     "record": record_id}),
                     _class="s3_modal",
                     _title=T("Edit %(type)s") % dict(type=title),
                     )
    else:
        edit_btn = ""
    if permit("delete", table, record_id=record_id):
        delete_btn = A(I(" ", _class="icon icon-trash"),
                       _class="dl-item-delete",
                       )
    else:
        delete_btn = ""
    user = current.auth.user
    if user and settings.get_cms_bookmarks():
        ltable = current.s3db.cms_post_user
        query = (ltable.post_id == record_id) & \
                (ltable.user_id == user.id)
        exists = db(query).select(ltable.id,
                                  limitby=(0, 1)
                                  ).first()
        if exists:
            bookmark_btn = A(I(" ", _class="icon icon-bookmark"),
                             _onclick="$.getS3('%s',function(){$('#%s').datalist('ajaxReloadItem',%s)})" %
                                (URL(c="cms", f="post",
                                     args=[record_id, "remove_bookmark"]),
                                 listid,
                                 record_id),
                             _title=T("Remove Bookmark"),
                             )
        else:
            bookmark_btn = A(I(" ", _class="icon icon-bookmark-empty"),
                             _onclick="$.getS3('%s',function(){$('#%s').datalist('ajaxReloadItem',%s)})" %
                                (URL(c="cms", f="post",
                                     args=[record_id, "add_bookmark"]),
                                 listid,
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
        doc_list = UL(_class="dropdown-menu",
                      _role="menu",
                      )
        retrieve = db.doc_document.file.retrieve
        for doc in documents:
            try:
                doc_name = retrieve(doc)[0]
            except (IOError, TypeError):
                doc_name = messages["NONE"]
            doc_url = URL(c="default", f="download",
                          args=[doc])
            doc_item = LI(A(I(_class="icon-file"),
                            " ",
                            doc_name,
                            _href=doc_url,
                            ),
                          _role="menuitem",
                          )
            doc_list.append(doc_item)
        docs = DIV(A(I(_class="icon-paper-clip"),
                     SPAN(_class="caret"),
                     _class="btn dropdown-toggle",
                     _href="#",
                     **{"_data-toggle": "dropdown"}
                     ),
                   doc_list,
                   _class="btn-group attachments dropdown pull-right",
                   )
    else:
        docs = ""

    request = current.request
    if "profile" in request.args:
        # Single resource list
        card_label = SPAN(" ", _class="card-title")
    else:
        # Mixed resource lists (Home, News Feed)
        icon = series.lower().replace(" ", "_")
        card_label = TAG[""](I(_class="icon icon-%s" % icon),
                             SPAN(" %s" % title,
                                  _class="card-title"))
        # Type cards
        if series == "Alert": 
            # Apply additional highlighting for Alerts
            item_class = "%s disaster" % item_class

    # Render the item
    if series == "Event" and "newsfeed" not in request.args:
        # Events on Homepage have a different header
        header = DIV(SPAN(date,
                          _class="date-title event",
                          ),
                     location,
                     toolbox,
                     _class="card-header",
                     )
    else:
        header = DIV(card_label,
                     location,
                     SPAN(date,
                          _class="date-title",
                          ),
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
               _class=item_class,
               _id=item_id,
               )

    return item

# END =========================================================================
