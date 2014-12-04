# -*- coding: utf-8 -*-

""" Sahana Eden Delphi Decision Maker Model

    @copyright: 2009-2014 (c) Sahana Software Foundation
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

__all__ = ("S3DelphiModel",
           "S3DelphiUser",
           )

from gluon import *
from gluon.storage import Storage
from ..s3 import *

# =============================================================================
class S3DelphiModel(S3Model):
    """
        Delphi Decision Maker
    """

    names = ("delphi_group",
             "delphi_membership",
             "delphi_problem",
             "delphi_solution",
             "delphi_vote",
             "delphi_comment",
             "delphi_solution_represent",
             "delphi_DelphiUser",
             )

    def model(self):

        T = current.T
        db = current.db

        messages = current.messages
        NONE = messages["NONE"]
        UNKNOWN_OPT = messages.UNKNOWN_OPT

        add_components = self.add_components
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        # ---------------------------------------------------------------------
        # Groups
        # ---------------------------------------------------------------------
        tablename = "delphi_group"
        define_table(tablename,
                     Field("name", length=255, notnull=True, unique=True,
                           label = T("Group Title"),
                           ),
                     Field("description", "text",
                           label = T("Description"),
                           ),
                     Field("active", "boolean", default=True,
                           label = T("Active"),
                           represent = s3_yes_no_represent,
                           ),
                     *s3_meta_fields()
                     )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Group"),
            title_display = T("Group Details"),
            title_list = T("Groups"),
            title_update = T("Edit Group"),
            label_list_button = T("List Groups"),
            label_delete_button = T("Delete Group"),
            msg_record_created = T("Group added"),
            msg_record_modified = T("Group updated"),
            msg_record_deleted = T("Group deleted"),
            msg_list_empty = T("No Groups currently defined"))

        configure(tablename,
                  deduplicate = self.group_duplicate,
                  list_fields = ["id",
                                 "name",
                                 "description",
                                 ],
                  )

        # Components
        add_components(tablename,
                       delphi_membership = "group_id",
                       delphi_problem = "group_id",
                       )

        group_id = S3ReusableField("group_id", "reference %s" % tablename,
                                   notnull=True,
                                   label = T("Problem Group"),
                                   represent = self.delphi_group_represent,
                                   requires = IS_ONE_OF(db, "delphi_group.id",
                                                        self.delphi_group_represent
                                                        ),
                                   )

        user_id = S3ReusableField("user_id", current.auth.settings.table_user,
                                  notnull=True,
                                  label = T("User"),
                                  represent = s3_auth_user_represent,
                                  requires = IS_ONE_OF(db, "auth_user.id",
                                                       s3_auth_user_represent),
                                  )

        # ---------------------------------------------------------------------
        # Group Membership
        # ---------------------------------------------------------------------
        delphi_role_opts = {
            1:T("Guest"),
            2:T("Contributor"),
            3:T("Participant"),
            4:T("Moderator")
        }
        tablename = "delphi_membership"
        define_table(tablename,
                     group_id(),
                     user_id(),
                     Field("description",
                           label = T("Description"),
                           ),
                     # @ToDo: Change how Membership Requests work
                     Field("req", "boolean",
                           default = False,
                           label = T("Request"),    # Membership Request
                           represent = s3_yes_no_represent,
                           ),
                     Field("status", "integer",
                           default = 3,
                           label = T("Status"),
                           represent = lambda opt: \
                                       delphi_role_opts.get(opt, UNKNOWN_OPT),
                           requires = IS_IN_SET(delphi_role_opts,
                                                zero=None),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s|%s|%s|%s" % (T("Status"),
                                                                    T("Guests can view all details"),
                                                                    T("A Contributor can additionally Post comments to the proposed Solutions & add alternative Solutions"),
                                                                    T("A Participant can additionally Vote"),
                                                                    T("A Moderator can additionally create Problems & control Memberships")))
                           ),
                     *s3_meta_fields()
                     )

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Member"),
            title_display = T("Membership Details"),
            title_list = T("Group Members"),
            title_update = T("Edit Membership"),
            label_list_button = T("List Members"),
            label_delete_button = T("Remove Person from Group"),
            msg_record_created = T("Person added to Group"),
            msg_record_modified = T("Membership updated"),
            msg_record_deleted = T("Person removed from Group"),
            msg_list_empty = T("This Group has no Members yet"))

        configure(tablename,
                  list_fields = ["id",
                                 "group_id",
                                 "user_id",
                                 "status",
                                 "req",
                                 ],
                  )

        # ---------------------------------------------------------------------
        # Problems
        # ---------------------------------------------------------------------
        tablename = "delphi_problem"
        define_table(tablename,
                     group_id(),
                     Field("code", length=8,
                           label = T("Problem Code"),
                           represent = lambda v: v or NONE,
                           ),
                     Field("name", length=255, notnull=True, unique=True,
                           label = T("Problem Title"),
                           ),
                     Field("description", "text",
                           label = T("Description"),
                           represent = s3_comments_represent,
                           ),
                     Field("criteria", "text", notnull=True,
                           label = T("Criteria"),
                           ),
                     Field("active", "boolean",
                           default = True,
                           label = T("Active"),
                           represent = s3_yes_no_represent,
                           ),
                     *s3_meta_fields()
                     )

        # @todo: make lazy_table
        table = db[tablename]
        table.modified_on.label = T("Last Modification")

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Problem"),
            title_display = T("Problem Details"),
            title_list = T("Problems"),
            title_update = T("Edit Problem"),
            label_list_button = T("List Problems"),
            label_delete_button = T("Delete Problem"),
            msg_record_created = T("Problem added"),
            msg_record_modified = T("Problem updated"),
            msg_record_deleted = T("Problem deleted"),
            msg_list_empty = T("No Problems currently defined"))

        configure(tablename,
                  deduplicate = self.problem_duplicate,
                  list_fields = ["id",
                                 "group_id",
                                 "code",
                                 "name",
                                 "description",
                                 "created_by",
                                 "modified_on",
                                 ],
                  orderby = table.code,
                  )

        # Components
        add_components(tablename,
                       delphi_solution = "problem_id",
                       )

        problem_id = S3ReusableField("problem_id", "reference %s" % tablename,
                                     notnull=True,
                                     label = T("Problem"),
                                     represent = self.delphi_problem_represent,
                                     requires = IS_ONE_OF(db, "delphi_problem.id",
                                                          self.delphi_problem_represent
                                                          ),
                                     )

        # ---------------------------------------------------------------------
        # Solutions
        # ---------------------------------------------------------------------
        tablename = "delphi_solution"
        define_table(tablename,
                     problem_id(),
                     Field("name",
                           label = T("Title"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("description", "text",
                           label = T("Description"),
                           represent = s3_comments_represent,
                           ),
                     Field("changes", "integer",
                           default = 0,
                           label = T("Changes"),
                           writable = False,
                           ),
                     Field.Method("comments",
                                  delphi_solution_comments),
                     Field.Method("votes",
                                  delphi_solution_votes),
                     *s3_meta_fields()
                     )

        # @todo: make lazy_table
        table = db[tablename]
        table.created_by.label = T("Suggested By")
        table.modified_on.label = T("Last Modification")

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Solution"),
            title_display = T("Solution Details"),
            title_list = T("Solutions"),
            title_update = T("Edit Solution"),
            label_list_button = T("List Solutions"),
            label_delete_button = T("Delete Solution"),
            msg_record_created = T("Solution added"),
            msg_record_modified = T("Solution updated"),
            msg_record_deleted = T("Solution deleted"),
            msg_list_empty = T("No Solutions currently defined"))


        configure(tablename,
                  extra_fields = ["problem_id"],
                  list_fields = ["id",
                                 #"problem_id",
                                 "name",
                                 "description",
                                 "created_by",
                                 "modified_on",
                                 (T("Voted on"), "votes"),
                                 (T("Comments"), "comments"),
                                 ],
                  )

        solution_represent = S3Represent(lookup=tablename)
        solution_id = S3ReusableField("solution_id", "reference %s" % tablename,
                                      label = T("Solution"),
                                      represent = solution_represent,
                                      requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "delphi_solution.id",
                                                              solution_represent
                                                              )),
                                      )

        # ---------------------------------------------------------------------
        # Votes
        # ---------------------------------------------------------------------
        tablename = "delphi_vote"
        define_table(tablename,
                     problem_id(),
                     solution_id(empty = False),
                     Field("rank", "integer",
                           label = T("Rank"),
                           ),
                     *s3_meta_fields()
                     )

        # ---------------------------------------------------------------------
        # Comments
        # @ToDo: Attachments?
        #
        # Parent field allows us to:
        #  * easily filter for top-level threads
        #  * easily filter for next level of threading
        #  * hook a new reply into the correct location in the hierarchy
        #
        # ---------------------------------------------------------------------
        tablename = "delphi_comment"
        define_table(tablename,
                     Field("parent", "reference delphi_comment",
                           requires = IS_EMPTY_OR(
                                        IS_ONE_OF_EMPTY(db, "delphi_comment.id")),
                           readable=False,
                           ),
                     problem_id(),
                     # @ToDo: Tag to 1+ Solutions
                     #solution_multi_id(),
                     solution_id(),
                     Field("body", "text", notnull=True,
                           label = T("Comment"),
                           ),
                     *s3_meta_fields()
                     )

        configure(tablename,
                  list_fields = ["id",
                                 "problem_id",
                                 "solution_id",
                                 "created_by",
                                 "modified_on",
                                 ],
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        return dict(delphi_solution_represent = solution_represent,
                    delphi_DelphiUser = S3DelphiUser,
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def delphi_group_represent(id, row=None):
        """ FK representation """

        if not row:
            db = current.db
            table = db.delphi_group
            row = db(table.id == id).select(table.id,
                                            table.name,
                                            limitby = (0, 1)).first()
        elif not id:
            return current.messages["NONE"]

        try:
            return A(row.name,
                     _href=URL(c="delphi",
                               f="group",
                               args=[row.id]))
        except:
            return current.messages.UNKNOWN_OPT

    # ---------------------------------------------------------------------
    @staticmethod
    def delphi_problem_represent(id, row=None, show_link=False,
                                 solutions=True):
        """ FK representation """

        if not row:
            db = current.db
            table = db.delphi_problem
            row = db(table.id == id).select(table.id,
                                            table.name,
                                            limitby = (0, 1)).first()
        elif not id:
            return current.messages["NONE"]

        try:
            if show_link:
                if solutions:
                    url = URL(c="delphi", f="problem", args=[row.id, "solution"])
                else:
                    url = URL(c="delphi", f="problem", args=[row.id])
                return A(row.name, _href=url)
            else:
                return row.name
        except:
            return current.messages.UNKNOWN_OPT

    # ---------------------------------------------------------------------
    @staticmethod
    def group_duplicate(item):
        """
          This callback will be called when importing records
          it will look to see if the record being imported is a duplicate.

          @param item: An S3ImportItem object which includes all the details
                       of the record being imported

          If the record is a duplicate then it will set the item method to update

          Rules for finding a duplicate:
           - Look for a record with the same name, ignoring case
        """

        table = item.table
        data = item.data
        name = "name" in data and data.name

        query = (table.name.lower() == name.lower())
        duplicate = current.db(query).select(table.id,
                                             limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

    # ---------------------------------------------------------------------
    @staticmethod
    def problem_duplicate(item):
        """
          This callback will be called when importing records
          it will look to see if the record being imported is a duplicate.

          @param item: An S3ImportItem object which includes all the details
                       of the record being imported

          If the record is a duplicate then it will set the item method to update

          Rules for finding a duplicate:
           - Look for a record with the same name, ignoring case
        """

        table = item.table
        name = "name" in item.data and item.data.name

        query = (table.name.lower() == name.lower())
        duplicate = current.db(query).select(table.id,
                                             limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

# =============================================================================
def delphi_solution_comments(row):
    """ Clickable number of comments for a solution, virtual field """

    if hasattr(row, "delphi_solution"):
        row = row.delphi_solution
    try:
        solution_id = row.id
        problem_id = row.problem_id
    except AttributeError:
        return None

    ctable = current.s3db.delphi_comment
    query = (ctable.solution_id == solution_id)
    comments = current.db(query).count()

    url = URL(c="delphi", f="problem",
              args=[problem_id, "solution", solution_id, "discuss"])
    return A(comments, _href=url)

def delphi_solution_votes(row):
    """ Clickable number of solutions for a problem, virtual field """

    if hasattr(row, "delphi_solution"):
        row = row.delphi_solution
    try:
        solution_id = row.id
        problem_id = row.problem_id
    except AttributeError:
        return None

    vtable = current.s3db.delphi_vote
    query = (vtable.solution_id == solution_id)
    votes = current.db(query).count()
    url = URL(c="delphi", f="problem",
              args=[problem_id, "results"])
    return A(votes, _href=url)

# =============================================================================
class S3DelphiUser:
    """ Delphi User class """

    def user(self):
        """  Used by Discuss() (& summary()) """

        return current.s3db.auth_user[self.user_id]

    def __init__(self, group_id=None):

        auth = current.auth
        user_id = auth.user.id if auth.is_logged_in() else None
        status = 1 # guest
        membership = None
        if auth.s3_has_role("DelphiAdmin"):
            # DelphiAdmin is Moderator for every Group
            status = 4
        elif user_id != None and group_id != None:
            table = current.s3db.delphi_membership
            query = (table.group_id == group_id) & \
                    (table.user_id == user_id)
            membership = current.db(query).select()
            if membership:
                membership = membership[0]
                status = membership.status

        self.authorised = (status == 4)

        # Only Moderators & Participants can Vote
        self.can_vote = status in (3, 4)
        # All but Guests can add Solutions & Discuss
        self.can_add_item = status != 1
        self.can_post = status != 1

        self.membership = membership
        self.status = status
        self.user_id = user_id

# END =========================================================================
