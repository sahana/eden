# -*- coding: utf-8 -*-

""" Sahana Eden Delphi Decision Maker Model

    @copyright: 2009-2012 (c) Sahana Software Foundation
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

__all__ = ["S3DelphiModel",
           "S3DelphiUser"]

from gluon import *
from gluon.storage import Storage
from ..s3 import *

# =============================================================================
class S3DelphiModel(S3Model):
    """
        Delphi Decision Maker
    """

    names = ["delphi_group",
             "delphi_membership",
             "delphi_problem",
             "delphi_solution",
             "delphi_vote",
             "delphi_comment",
             "delphi_solution_represent",
            ]

    def model(self):

        T = current.T
        db = current.db
        s3 = current.response.s3

        UNKNOWN_OPT = current.messages.UNKNOWN_OPT

        # ---------------------------------------------------------------------
        # Groups
        # ---------------------------------------------------------------------
        tablename = "delphi_group"
        table = self.define_table(tablename,
                                  Field("name", notnull=True, unique=True,
                                        label = T("Group Title")),
                                  Field("description", "text",
                                        label = T("Description")),
                                  Field("active", "boolean", default=True,
                                        label = T("Active")),
                                  *s3_meta_fields()
                                )

        # CRUD Strings
        ADD_GROUP = T("Add Group")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_GROUP,
            title_display = T("Group Details"),
            title_list = T("Groups"),
            title_update = T("Edit Group"),
            title_search = T("Search Groups"),
            subtitle_create = T("Add New Group"),
            label_list_button = T("List Groups"),
            label_create_button = ADD_GROUP,
            label_delete_button = T("Delete Group"),
            msg_record_created = T("Group added"),
            msg_record_modified = T("Group updated"),
            msg_record_deleted = T("Group deleted"),
            msg_list_empty = T("No Groups currently defined"))

        self.configure(tablename,
                       list_fields=["id",
                                    "name",
                                    "description"])

        group_id = S3ReusableField("group_id", db.delphi_group, notnull=True,
                                   label = T("Problem Group"),
                                   requires = IS_ONE_OF(db, "delphi_group.id",
                                                        "%(name)s"),
                                   represent = self.group_represent)

        user_id = S3ReusableField("user_id", db.auth_user, notnull=True,
                                  label = T("User"),
                                  requires = IS_ONE_OF(db, "auth_user.id",
                                                       s3_auth_user_represent),
                                  represent = s3_auth_user_represent)

        # Memberships as component of Groups
        self.add_component("delphi_membership",
                           delphi_group="group_id")

        # Problems as component of Groups
        self.add_component("delphi_problem",
                           delphi_group="group_id")

        self.configure("delphi_group", deduplicate=self.group_duplicate)

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
        table = self.define_table(tablename,
                                  group_id(),
                                  user_id(),
                                  Field("description",
                                        label = T("Description")),
                                  # @ToDo: Change how Membership Requests work
                                  Field("req", "boolean", default=False,
                                        label = T("Request")), # Membership Request
                                  Field("status", "integer", default=3,
                                        label = T("Status"),
                                        requires = IS_IN_SET(delphi_role_opts,
                                                             zero=None),
                                        represent = lambda opt: \
                                            delphi_role_opts.get(opt, UNKNOWN_OPT),
                                        comment = DIV( _class="tooltip",
                                                       _title="%s|%s|%s|%s|%s" % (T("Status"),
                                                                                  T("Guests can view all details"),
                                                                                  T("A Contributor can additionally Post comments to the proposed Solutions & add alternative Solutions"),
                                                                                  T("A Participant can additionally Vote"),
                                                                                  T("A Moderator can additionally create Problems & control Memberships")))
                                        ),
                                  *s3_meta_fields()
                                )

        # CRUD Strings
        ADD_MEMBERSHIP = T("Add Membership")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_MEMBERSHIP,
            title_display = T("Membership Details"),
            title_list = T("Memberships"),
            title_update = T("Edit Membership"),
            title_search = T("Search Memberships"),
            subtitle_create = T("Add New Membership"),
            label_list_button = T("List Memberships"),
            label_create_button = ADD_MEMBERSHIP,
            label_delete_button = T("Remove Membership"),
            msg_record_created = T("Membership added"),
            msg_record_modified = T("Membership updated"),
            msg_record_deleted = T("Membership deleted"),
            msg_list_empty = T("No Memberships currently defined"))

        self.configure(tablename,
                       list_fields=["id",
                                    "group_id",
                                    "user_id",
                                    "status",
                                    "req"])

        # ---------------------------------------------------------------------
        # Problems
        # ---------------------------------------------------------------------
        tablename = "delphi_problem"
        table = self.define_table(tablename,
                                  group_id(),
                                  Field("name", notnull=True, unique=True,
                                        label = T("Problem Title")),
                                  Field("description", "text",
                                        represent = s3_comments_represent,
                                        label = T("Description")),
                                  Field("criteria", "text", notnull=True,
                                        label = T("Criteria")),
                                  Field("active", "boolean", default=True,
                                        label = T("Active")),
                                  *s3_meta_fields()
                                )

        table.modified_on.label = T("Last Modification")

        # CRUD Strings
        ADD_PROBLEM = T("Add Problem")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_PROBLEM,
            title_display = T("Problem Details"),
            title_list = T("Problems"),
            title_update = T("Edit Problem"),
            title_search = T("Search Problems"),
            subtitle_create = T("Add New Problem"),
            label_list_button = T("List Problems"),
            label_create_button = ADD_PROBLEM,
            label_delete_button = T("Delete Problem"),
            msg_record_created = T("Problem added"),
            msg_record_modified = T("Problem updated"),
            msg_record_deleted = T("Problem deleted"),
            msg_list_empty = T("No Problems currently defined"))

        self.configure(tablename,
                       list_fields=["id",
                                    "group_id",
                                    "name",
                                    "description",
                                    "created_by",
                                    "modified_on"])

        problem_id = S3ReusableField("problem_id", db.delphi_problem, notnull=True,
                                     label = T("Problem"),
                                     requires = IS_ONE_OF(db, "delphi_problem.id",
                                                          "%(name)s"),
                                     represent = self.problem_represent)

        # Solutions as component of Problems
        self.add_component("delphi_solution",
                           delphi_problem="problem_id")

        self.configure("delphi_problem", deduplicate=self.problem_duplicate)

        # ---------------------------------------------------------------------
        # Solutions
        # ---------------------------------------------------------------------
        tablename = "delphi_solution"
        table = self.define_table(tablename,
                                  problem_id(),
                                  Field("name",
                                        label = T("Title"),
                                        requires = IS_NOT_EMPTY()),
                                  Field("description", "text",
                                        represent = s3_comments_represent,
                                        label = T("Description")),
                                  Field("changes", "integer",
                                        default = 0,
                                        writable = False,
                                        label = T("Changes")),
                                  *s3_meta_fields()
                                )

        table.created_by.label = T("Suggested By")
        table.modified_on.label = T("Last Modification")

        # CRUD Strings
        ADD_SOLUTION = T("Add Solution")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_SOLUTION,
            title_display = T("Solution Details"),
            title_list = T("Solutions"),
            title_update = T("Edit Solution"),
            title_search = T("Search Solutions"),
            subtitle_create = T("Add New Solution"),
            label_list_button = T("List Solutions"),
            label_create_button = ADD_SOLUTION,
            label_delete_button = T("Delete Solution"),
            msg_record_created = T("Solution added"),
            msg_record_modified = T("Solution updated"),
            msg_record_deleted = T("Solution deleted"),
            msg_list_empty = T("No Solutions currently defined"))


        table.virtualfields.append(solution_virtualfields())

        self.configure(tablename,
                       list_fields=["id",
                                    #"problem_id",
                                    "name",
                                    "description",
                                    "created_by",
                                    "modified_on",
                                    (T("Voted on"), "votes"),
                                    (T("Comments"), "comments"),
                                    ])

        solution_id = S3ReusableField("solution_id", db.delphi_solution,
                                      label = T("Solution"),
                                      requires = IS_EMPTY_OR(IS_ONE_OF(db,
                                                                       "delphi_solution.id",
                                                                       "%(name)s")),
                                      represent = self.solution_represent)

        # ---------------------------------------------------------------------
        # Votes
        # ---------------------------------------------------------------------
        tablename = "delphi_vote"
        table = self.define_table(tablename,
                                  problem_id(),
                                  solution_id(empty=False),
                                  Field("rank", "integer",
                                        label = T("Rank")),
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
        table = self.define_table(tablename,
                                  Field("parent", "reference delphi_comment",
                                        requires = IS_EMPTY_OR(IS_ONE_OF(db,
                                                                         "delphi_comment.id")),
                                        readable=False),
                                  problem_id(),
                                  # @ToDo: Tag to 1+ Solutions
                                  #solution_multi_id(),
                                  solution_id(),
                                  Field("body", "text", notnull=True,
                                        label = T("Comment")),
                                  *s3_meta_fields()
                                )

        self.configure(tablename,
                       list_fields=["id",
                                    "problem_id",
                                    "solution_id",
                                    "created_by",
                                    "modified_on"])

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (response.s3.*)
        return Storage(
                        delphi_solution_represent = self.solution_represent
                    )

    # ---------------------------------------------------------------------
    @staticmethod
    def group_represent(id):

        db = current.db
        s3db = current.s3db
        messages = current.messages
        NONE = messages.NONE
        UNKNOWN_OPT = messages.UNKNOWN_OPT

        if not id:
            return NONE
        table = s3db.delphi_group
        query = (table.id == id)
        record = db(query).select(table.name,
                                  limitby=(0, 1)).first()
        if not record:
            return UNKNOWN_OPT
        return A(record.name,
                 _href=URL(c="delphi",
                           f="group",
                           args=[id]))

    # ---------------------------------------------------------------------
    @staticmethod
    def problem_represent(id, showlink=False, solutions=True):

        db = current.db
        s3db = current.s3db
        messages = current.messages
        NONE = messages.NONE
        UNKNOWN_OPT = messages.UNKNOWN_OPT

        if not id:
            return NONE
        table = s3db.delphi_problem
        query = (table.id == id)
        record = db(query).select(table.name,
                                  limitby=(0, 1)).first()
        if not record:
            return UNKNOWN_OPT
        if showlink:
            if solutions:
                url = URL(c="delphi", f="problem", args=[id, "solution"])
            else:
                url = URL(c="delphi", f="problem", args=[id])
            output = A(record.name, _href=url)
            return output
        else:
            return record.name

    # ---------------------------------------------------------------------
    @staticmethod
    def solution_represent(id):

        db = current.db
        s3db = current.s3db
        messages = current.messages
        NONE = messages.NONE
        UNKNOWN_OPT = messages.UNKNOWN_OPT

        if not id:
            return NONE
        table = s3db.delphi_solution
        query = (table.id == id)
        record = db(query).select(table.name,
                                  limitby=(0, 1)).first()
        if not record:
            return UNKNOWN_OPT
        return record.name

    # ---------------------------------------------------------------------
    @staticmethod
    def group_duplicate(job):
        """
          This callback will be called when importing records
          it will look to see if the record being imported is a duplicate.

          @param job: An S3ImportJob object which includes all the details
                      of the record being imported

          If the record is a duplicate then it will set the job method to update

          Rules for finding a duplicate:
           - Look for a record with the same name, ignoring case
        """

        if job.tablename == "delphi_group":
            table = job.table
            name = "name" in job.data and job.data.name

            query = (table.name.lower().like('%%%s%%' % name.lower()))
            _duplicate = current.db(query).select(table.id,
                                                  limitby=(0, 1)).first()
            if _duplicate:
                job.id = _duplicate.id
                job.data.id = _duplicate.id
                job.method = job.METHOD.UPDATE

    # ---------------------------------------------------------------------
    @staticmethod
    def problem_duplicate(job):
        """
          This callback will be called when importing records
          it will look to see if the record being imported is a duplicate.

          @param job: An S3ImportJob object which includes all the details
                      of the record being imported

          If the record is a duplicate then it will set the job method to update

          Rules for finding a duplicate:
           - Look for a record with the same name, ignoring case
        """

        if job.tablename == "delphi_problem":
            table = job.table
            name = "name" in job.data and job.data.name

            query = (table.name.lower().like('%%%s%%' % name.lower()))
            _duplicate = current.db(query).select(table.id,
                                                  limitby=(0, 1)).first()
            if _duplicate:
                job.id = _duplicate.id
                job.data.id = _duplicate.id
                job.method = job.METHOD.UPDATE

# =============================================================================
class solution_virtualfields(dict, object):
    """ Virtual Fields for Solutions """

    # Fields to be loaded by sqltable as qfields
    # without them being list_fields
    # (These cannot contain VirtualFields)
    extra_fields = [
                "problem_id"
            ]

    def comments(self):
        db = current.db
        s3db = current.s3db
        ctable = s3db.delphi_comment
        # Prevent recursive queries
        try:
            query = (ctable.solution_id == self.delphi_solution.id)
        except AttributeError:
            # We are being instantiated inside one of the other methods
            return None
        comments = db(query).count()
        url = URL(c="delphi", f="problem",
                  args=["solution", self.delphi_solution.id, "discuss"])
        output = A(comments,
                   _href=url)
        return output

    def votes(self):
        db = current.db
        s3db = current.s3db
        vtable = s3db.delphi_vote
        # Prevent recursive queries
        try:
            query = (vtable.solution_id == self.delphi_solution.id)
        except AttributeError:
            # We are being instantiated inside one of the other methods
            return None
        votes = db(query).count()
        url = URL(c="delphi", f="problem",
                  args=[self.delphi_solution.problem_id, "results"])
        output = A(votes,
                   _href=url)
        return output

# -----------------------------------------------------------------------------
class S3DelphiUser:
    """ Delphi User class """

    def user(self):
        """  Used by Discuss() (& summary()) """
        s3db = current.s3db
        return s3db.auth_user[self.user_id]

    def __init__(self, group_id=None):

        db = current.db
        s3db = current.s3db
        auth = current.auth
        session = current.session

        self.user_id = auth.user.id if (auth.is_logged_in() and session.auth) else None
        self.status = 1 # guest
        self.membership = None
        if auth.s3_has_role("DelphiAdmin"):
            # DelphiAdmin is Moderator for every Group
            self.status = 4
        elif self.user_id != None and group_id != None:
            table = s3db.delphi_membership
            query = (table.group_id == group_id) & \
                    (table.user_id == self.user_id)
            self.membership = db(query).select()
            if self.membership:
                self.membership = self.membership[0]
                self.status = self.membership.status

        self.authorised = (self.status == 4)

        # Only Moderators & Participants can Vote
        self.can_vote = self.status in (3, 4)
        # All but Guests can add Solutions & Discuss
        self.can_add_item = self.status != 1
        self.can_post = self.status != 1

# END =========================================================================
