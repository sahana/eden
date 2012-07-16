# -*- coding: utf-8 -*-

""" Sahana Eden Content Management System Model

    @copyright: 2012 (c) Sahana Software Foundation
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
           "cms_rheader",
          ]

from gluon import *
from gluon.storage import Storage
from ..s3 import *
from layouts import S3AddResourceLink

# =============================================================================
class S3ContentModel(S3Model):
    """
        Content Management System
    """

    names = ["cms_series",
             "cms_post",
             "cms_comment",
             ]

    def model(self):

        T = current.T
        db = current.db
        add_component = self.add_component
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        # ---------------------------------------------------------------------
        # Series
        # - lists of Posts displaying in recent-first mode
        #

        tablename = "cms_series"
        table = define_table(tablename,
                             Field("name", notnull=True,
                                   label=T("Name")),
                             Field("avatar", "boolean",
                                   default=False,
                                   label=T("Show author picture?")),
                             Field("replies", "boolean",
                                   default=False,
                                   label=T("Comments permitted?")),
                             s3_comments(),
                             # Multiple Roles (@ToDo: Implement the restriction)
                             s3_roles_permitted(
                                                readable = False,
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
        series_id = S3ReusableField("series_id", table,
                                    readable=False,
                                    writable=False,
                                    requires = IS_NULL_OR(
                                                IS_ONE_OF(db, "cms_series.id",
                                                          "%(name)s")),
                                    ondelete = "CASCADE")

        # Resource Configuration
        configure(tablename,
                  onaccept = self.series_onaccept,
                  create_next=URL(f="series", args=["[id]", "post"]))

        # Components
        add_component("cms_post", cms_series="series_id")

        # ---------------------------------------------------------------------
        # Posts
        # - single blocks of rich text which can be embedded into a page,
        #   be viewed as full pages or as part of a Series
        #

        modules = {}
        _modules = current.deployment_settings.modules
        for module in _modules:
            if module in ["appadmin", "errors", "sync"]:
                continue
            modules[module] = _modules[module].name_nice

        tablename = "cms_post"
        table = define_table(tablename,
                             series_id(),
                             Field("module",
                                   requires=IS_NULL_OR(
                                                IS_IN_SET_LAZY(lambda: \
                                            sort_dict_by_values(modules))),
                                   comment=T("If you specify a module then this will be used as the text in that module's index page"),
                                   label=T("Module")),
                             Field("name", notnull=True,
                                   comment=T("This isn't visible to the published site, but is used to allow menu items to point to the page"),
                                   label=T("Name")),
                             Field("title",
                                   comment=T("The title of the page, as seen in the browser (optional)"),
                                   label=T("Title")),
                             Field("body", "text", notnull=True,
                                   widget = s3_richtext_widget,
                                   label=T("Body")),
                             Field("avatar", "boolean",
                                   default=False,
                                   label=T("Show author picture?")),
                             Field("replies", "boolean",
                                   default=False,
                                   label=T("Comments permitted?")),
                             #Field("published", "boolean",
                             #      default=True,
                             #      label=T("Published")),
                             s3_comments(),
                             # Multiple Roles (@ToDo: Implement the restriction)
                             s3_roles_permitted(
                                                readable = False,
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
            msg_list_empty = T("No posts currently defined"))

        # Reusable field
        post_id = S3ReusableField("post_id", table,
                                  label = T("Post"),
                                  sortby="name",
                                  requires = IS_NULL_OR(
                                                IS_ONE_OF(db, "cms_post.id",
                                                          "%(name)s")),
                                  represent = lambda id, row=None: \
                                                (id and [db.cms_post[id].name] or [NONE])[0],
                                  comment = S3AddResourceLink(c="cms",
                                                              f="post",
                                                              title=ADD_POST,
                                                              tooltip=T("A block of rich text which could be embedded into a page, viewed as a complete page or viewed as a list of news items.")),
                                  ondelete = "CASCADE")

        # Resource Configuration
        configure(tablename,
                  onaccept = self.post_onaccept)

        # Components
        add_component("cms_comment", cms_post="post_id")

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
                                   requires = IS_EMPTY_OR(IS_ONE_OF(db,
                                                                    "cms_comment.id")),
                                   readable=False),
                             post_id(),
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
        # Pass variables back to global scope (s3db.*)
        #
        return Storage()

    # -------------------------------------------------------------------------
    @staticmethod
    def series_onaccept(form):
        """
            cascade values down to all component Posts
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
    def post_onaccept(form):
        """
        """

        vars = form.vars

        module = vars.get("module", None)
        if module:
            # Ensure that no other record is set as the one for this module
            db = current.db
            table = db.cms_post
            query = (table.module == module) & \
                    (table.id != vars.id)
            db(query).update(module=None)

        return

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

        rheader = DIV(TABLE(
            TR(
               TH("%s: " % table.name.label),
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

        rheader = DIV(TABLE(
            TR(
               TH("%s: " % table.name.label),
               record.name
              ),
            ), rheader_tabs)

    return rheader

# END =========================================================================
