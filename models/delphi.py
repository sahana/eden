# coding: utf8

"""
    Delphi decision maker
"""

module = "delphi"
if deployment_settings.has_module(module):

    # Memberships as component of Groups
    s3mgr.model.add_component("delphi_membership",
                              delphi_group="group_id")

    # Problems as component of Groups
    s3mgr.model.add_component("delphi_problem",
                              delphi_group="group_id")

    # Solutions as component of Problems
    s3mgr.model.add_component("delphi_solution",
                              delphi_problem="problem_id")

    def delphi_tables():
        """ Load the Delphi Tables when needed """

        # ---------------------------------------------------------------------
        # Groups
        # ---------------------------------------------------------------------
        tablename = "delphi_group"
        table = db.define_table(tablename,
                                Field("name", notnull=True, unique=True,
                                      label = T("Group Title")),
                                Field("description", "text",
                                      label = T("Description")),
                                Field("active", "boolean", default=True,
                                      label = T("Active")),
                                *s3_meta_fields())

        # CRUD Strings
        ADD_GROUP = T("Add Group")
        LIST_GROUPS = T("List Groups")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_GROUP,
            title_display = T("Group Details"),
            title_list = LIST_GROUPS,
            title_update = T("Edit Group"),
            title_search = T("Search Groups"),
            subtitle_create = T("Add New Group"),
            subtitle_list = T("Groups"),
            label_list_button = LIST_GROUPS,
            label_create_button = ADD_GROUP,
            label_delete_button = T("Delete Group"),
            msg_record_created = T("Group added"),
            msg_record_modified = T("Group updated"),
            msg_record_deleted = T("Group deleted"),
            msg_list_empty = T("No Groups currently defined"))

        s3mgr.configure(tablename,
                        list_fields=["id",
                                     "name",
                                     "description"])

        def delphi_group_represent(id):
            if not id:
                return NONE
            table = db.delphi_group
            query = (table.id == id)
            record = db(query).select(table.name,
                                      limitby=(0, 1)).first()
            if not record:
                return UNKNOWN_OPT
            return A(record.name,
                     _href=URL(c="delphi",
                               f="group",
                               args=[id]))

        group_id = S3ReusableField("group_id", db.delphi_group, notnull=True,
                                   label = T("Problem Group"),
                                   requires = IS_ONE_OF(db, "delphi_group.id",
                                                        "%(name)s"),
                                   represent = delphi_group_represent)

        user_id = S3ReusableField("user_id", db.auth_user, notnull=True,
                                  label = T("User"),
                                  requires = IS_ONE_OF(db, "auth_user.id",
                                                       s3_user_represent),
                                  represent = s3_user_represent)

        def delphi_group_duplicate(job):
            """
              This callback will be called when importing records
              it will look to see if the record being imported is a duplicate.

              @param job: An S3ImportJob object which includes all the details
                          of the record being imported

              If the record is a duplicate then it will set the job method to update

              Rules for finding a duplicate:
               - Look for a record with the same name, ignoring case
            """
            # ignore this processing if the id is set
            if job.id:
                return
            if job.tablename == "delphi_group":
                table = job.table
                name = "name" in job.data and job.data.name

                query = (table.name.lower().like('%%%s%%' % name.lower()))
                _duplicate = db(query).select(table.id,
                                              limitby=(0, 1)).first()
                if _duplicate:
                    job.id = _duplicate.id
                    job.data.id = _duplicate.id
                    job.method = job.METHOD.UPDATE

        s3mgr.configure("delphi_group", deduplicate=delphi_group_duplicate)

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
        table = db.define_table(tablename,
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
        LIST_MEMBERSHIPS = T("List Memberships")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_MEMBERSHIP,
            title_display = T("Membership Details"),
            title_list = LIST_MEMBERSHIPS,
            title_update = T("Edit Membership"),
            title_search = T("Search Memberships"),
            subtitle_create = T("Add New Membership"),
            subtitle_list = T("Memberships"),
            label_list_button = LIST_MEMBERSHIPS,
            label_create_button = ADD_MEMBERSHIP,
            label_delete_button = T("Remove Membership"),
            msg_record_created = T("Membership added"),
            msg_record_modified = T("Membership updated"),
            msg_record_deleted = T("Membership deleted"),
            msg_list_empty = T("No Memberships currently defined"))

        s3mgr.configure(tablename,
                        list_fields=["id",
                                     "group_id",
                                     "user_id",
                                     "status",
                                     "req"])

        # ---------------------------------------------------------------------
        # Problems
        # ---------------------------------------------------------------------
        tablename = "delphi_problem"
        table = db.define_table(tablename,
                                group_id(),
                                Field("name", notnull=True, unique=True,
                                      label = T("Problem Title")),
                                Field("description", "text",
                                      represent = comments_represent,
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
        LIST_PROBLEMS = T("List Problems")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_PROBLEM,
            title_display = T("Problem Details"),
            title_list = LIST_PROBLEMS,
            title_update = T("Edit Problem"),
            title_search = T("Search Problems"),
            subtitle_create = T("Add New Problem"),
            subtitle_list = T("Problems"),
            label_list_button = LIST_PROBLEMS,
            label_create_button = ADD_PROBLEM,
            label_delete_button = T("Delete Problem"),
            msg_record_created = T("Problem added"),
            msg_record_modified = T("Problem updated"),
            msg_record_deleted = T("Problem deleted"),
            msg_list_empty = T("No Problems currently defined"))

        s3mgr.configure(tablename,
                        list_fields=["id",
                                     "group_id",
                                     "name",
                                     "description",
                                     "created_by",
                                     "modified_on"])

        def delphi_problem_represent(id, showlink=False, solutions=True):
            if not id:
                return NONE
            table = db.delphi_problem
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

        problem_id = S3ReusableField("problem_id", db.delphi_problem, notnull=True,
                                     label = T("Problem"),
                                     requires = IS_ONE_OF(db, "delphi_problem.id",
                                                          "%(name)s"),
                                     represent = delphi_problem_represent)

        def delphi_problem_duplicate(job):
            """
              This callback will be called when importing records
              it will look to see if the record being imported is a duplicate.

              @param job: An S3ImportJob object which includes all the details
                          of the record being imported

              If the record is a duplicate then it will set the job method to update

              Rules for finding a duplicate:
               - Look for a record with the same name, ignoring case
            """
            # ignore this processing if the id is set
            if job.id:
                return
            if job.tablename == "delphi_problem":
                table = job.table
                name = "name" in job.data and job.data.name

                query = (table.name.lower().like('%%%s%%' % name.lower()))
                _duplicate = db(query).select(table.id,
                                              limitby=(0, 1)).first()
                if _duplicate:
                    job.id = _duplicate.id
                    job.data.id = _duplicate.id
                    job.method = job.METHOD.UPDATE

        s3mgr.configure("delphi_problem", deduplicate=delphi_problem_duplicate)

        # ---------------------------------------------------------------------
        # Solutions
        # ---------------------------------------------------------------------
        tablename = "delphi_solution"
        table = db.define_table(tablename,
                                problem_id(),
                                Field("name",
                                      label = T("Title"),
                                      requires = IS_NOT_EMPTY()),
                                Field("description", "text",
                                      represent = comments_represent,
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
        LIST_SOLUTIONS = T("List Solutions")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_SOLUTION,
            title_display = T("Solution Details"),
            title_list = LIST_SOLUTIONS,
            title_update = T("Edit Solution"),
            title_search = T("Search Solutions"),
            subtitle_create = T("Add New Solution"),
            subtitle_list = T("Solutions"),
            label_list_button = LIST_SOLUTIONS,
            label_create_button = ADD_SOLUTION,
            label_delete_button = T("Delete Solution"),
            msg_record_created = T("Solution added"),
            msg_record_modified = T("Solution updated"),
            msg_record_deleted = T("Solution deleted"),
            msg_list_empty = T("No Solutions currently defined"))

        # Virtual Fields
        class solution_virtualfields(dict, object):
            # Fields to be loaded by sqltable as qfields
            # without them being list_fields
            # (These cannot contain VirtualFields)
            extra_fields = [
                        "problem_id"
                    ]

            def s3_comments(self):
                ctable = db.delphi_comment
                # Prevent recursive queries
                try:
                    query = (ctable.solution_id == self.delphi_solution.id)
                except AttributeError:
                    # We are being instantiated inside one of the other methods
                    return None
                comments = db(query).count()
                url = URL(c="delphi", f="problem", args=["solution", self.delphi_solution.id, "discuss"])
                output = A(comments,
                           _href=url)
                return output

            def votes(self):
                vtable = db.delphi_vote
                # Prevent recursive queries
                try:
                    query = (vtable.solution_id == self.delphi_solution.id)
                except AttributeError:
                    # We are being instantiated inside one of the other methods
                    return None
                votes = db(query).count()
                url = URL(c="delphi", f="problem", args=[self.delphi_solution.problem_id, "results"])
                output = A(votes,
                           _href=url)
                return output

        table.virtualfields.append(solution_virtualfields())

        s3mgr.configure(tablename,
                        list_fields=["id",
                                     #"problem_id",
                                     "name",
                                     "description",
                                     "created_by",
                                     "modified_on",
                                     (T("Voted on"), "votes"),
                                     (T("Comments"), "comments"),
                                     ])

        def delphi_solution_represent(id):
            if not id:
                return NONE
            table = db.delphi_solution
            query = (table.id == id)
            record = db(query).select(table.name,
                                      limitby=(0, 1)).first()
            if not record:
                return UNKNOWN_OPT
            return record.name

        solution_id = S3ReusableField("solution_id", db.delphi_solution,
                                      label = T("Solution"),
                                      requires = IS_EMPTY_OR(IS_ONE_OF(db,
                                                                       "delphi_solution.id",
                                                                       "%(name)s")),
                                      represent = delphi_solution_represent)

        # ---------------------------------------------------------------------
        # Votes
        # ---------------------------------------------------------------------
        tablename = "delphi_vote"
        table = db.define_table(tablename,
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
        table = db.define_table(tablename,
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

        s3mgr.configure(tablename,
                        list_fields=["id",
                                     "problem_id",
                                     "solution_id",
                                     "created_by",
                                     "modified_on"])

        # =====================================================================
        # Pass variables back to global scope (response.s3.*)
        return dict (
                delphi_problem_represent = delphi_problem_represent,
                delphi_solution_represent = delphi_solution_represent
            )

    # Provide a handle to this load function
    s3mgr.loader(delphi_tables,
                 "delphi_group",
                 "delphi_membership",
                 "delphi_problem",
                 "delphi_solution",
                 "delphi_vote",
                 "delphi_comment",
                 )

# END =========================================================================
