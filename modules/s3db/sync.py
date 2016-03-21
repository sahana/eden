# -*- coding: utf-8 -*-

""" Sahana Eden Synchronization

    @copyright: 2009-2016 (c) Sahana Software Foundation
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

__all__ = ("SyncDataModel",
           "sync_rheader",
           "sync_now",
           "sync_job_reset"
           )

from gluon import *
from gluon.storage import Storage

from s3dal import Row
from ..s3 import *
from s3layouts import S3PopupLink

# =============================================================================
class SyncDataModel(S3Model):

    names = ("sync_config",
             "sync_status",
             "sync_repository",
             "sync_repository_id",
             "sync_repository_onaccept",
             "sync_task",
             "sync_resource_filter",
             "sync_job",
             "sync_log"
             )

    def model(self):

        T = current.T
        db = current.db
        request = current.request
        s3 = current.response.s3

        messages = current.messages
        UNKNOWN_OPT = messages.UNKNOWN_OPT
        NONE = messages["NONE"]

        crud_strings = s3.crud_strings
        define_table = self.define_table

        add_components = self.add_components
        configure = self.configure
        set_method = self.set_method

        s3_datetime_represent = lambda dt: \
                                S3DateTime.datetime_represent(dt, utc=True)

        # -------------------------------------------------------------------------
        # Configuration
        # -------------------------------------------------------------------------
        tablename = "sync_config"
        define_table(tablename,
                     Field("proxy",
                           label = T("Proxy Server URL"),
                           requires = IS_EMPTY_OR(IS_URL(mode="generic")),
                           ),
                     *s3_meta_fields())

        # Field configuration
        # @todo: make in-line
        table = db[tablename]
        table.uuid.readable = True
        table.uuid.label = "UUID"

        table.uuid.comment = DIV(_class="tooltip",
                                 _title="%s|%s" % (
                                    T("UUID"),
                                    T("Unique identifier which THIS repository identifies itself with when sending synchronization requests.")))
        table.proxy.comment = DIV(_class="tooltip",
                                  _title="%s|%s" % (
                                    T("Proxy Server URL"),
                                    T("URL of the default proxy server to connect to remote repositories (if required). If only some of the repositories require the use of a proxy server, you can configure this in the respective repository configurations.")))

        # CRUD Strings
        crud_strings[tablename] = Storage(
            title_display = T("Synchronization Settings"),
            title_update = T("Edit Synchronization Settings"),
            msg_record_modified = T("Synchronization settings updated"))

        # Resource Configuration
        configure(tablename,
                  deletable = False,
                  insertable = False,
                  update_next = URL(c="sync", f="config", args=["1", "update"]),
                  )

        # -------------------------------------------------------------------------
        # Status
        # -------------------------------------------------------------------------
        tablename = "sync_status"
        define_table(tablename,
                     Field("running", "boolean",
                           default = False,
                           readable = False,
                           writable = False,
                           ),
                     Field("manual", "boolean",
                           default = False,
                           readable = False,
                           writable = False,
                           ),
                     Field("timestmp", "datetime",
                           readable = False,
                           writable = False),
                           )

        # -------------------------------------------------------------------------
        # Repository
        # -------------------------------------------------------------------------
        sync_repository_types = {
            "adashi": "ADASHI",
            "ccrm": "CiviCRM",
            "eden": "Sahana Eden",
            "filesync": "Local Filesystem",
            "ftp": "FTP",
            "mcb": "Mariner CommandBridge",
            "wrike": "Wrike",
        }

        # Back-ends implementing passive methods (=send and/or receive)
        # so that they can be used for indirect, file-based synchronization
        sync_backend_types = {
            "adashi": "ADASHI",
            "eden": "Sahana Eden",
        }

        password_widget = S3PasswordWidget()
        tablename = "sync_repository"
        define_table(tablename,
                     Field("name", length=64, notnull=True,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (
                                                T("Repository Name"),
                                                T("Name of the repository (for you own reference)"))),
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("apitype",
                           default = "eden",
                           label = T("Repository Type"),
                           represent = S3Represent(options = sync_repository_types),
                           requires = IS_IN_SET(sync_repository_types),
                           ),
                     Field("backend",
                           default = "eden",
                           label = T("Data Format"),
                           represent = S3Represent(options = sync_backend_types),
                           requires = IS_IN_SET(sync_backend_types),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (
                                                T("Data Format"),
                                                T("The data format to use for data import/export"))),
                           ),
                     Field("url",
                           label = "URL",
                           requires = IS_EMPTY_OR(
                                      IS_NOT_IN_DB(db, "sync_repository.url")),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (
                                                T("Repository URL"),
                                                T("URL of the repository including application path, e.g. http://www.example.com/eden"))),
                           ),
                     Field("path",
                           label = T("Path"),
                           requires = IS_EMPTY_OR(
                                      IS_NOT_IN_DB(db, "sync_repository.path")),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (
                                                T("Repository Path"),
                                                T("File system location of the repository, e.g. /var/local/example"))),
                           ),
                     Field("username",
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (
                                                T("Username"),
                                                T("Username to use for authentication at the remote site."))),
                           ),
                     Field("password", "password",
                           widget = password_widget,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (
                                                T("Password"),
                                                T("Password to use for authentication at the remote site."))),
                           ),
                     Field("client_id",
                           label = T("Client ID"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (
                                                T("Client ID"),
                                                T("The client ID to use for authentication at the remote site (if required for this type of repository)."))),
                           ),
                     Field("client_secret", "password",
                           label = T("Client Secret"),
                           widget = password_widget,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (
                                                T("Client Secret"),
                                                T("The client secret to use for authentication at the remote site (if required for this type of repository)."))),
                           ),
                     Field("site_key",
                           label = T("Site Key"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (
                                                T("Site Key"),
                                                T("Site Key which this site uses to authenticate at the remote site (if required for this type of repository)."))),
                           ),
                     Field("refresh_token",
                           readable = False,
                           writable = False,
                           ),
                     Field("proxy",
                           label = T("Proxy Server URL"),
                           requires = IS_EMPTY_OR(IS_URL(mode="generic")),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (
                                                T("Proxy Server URL"),
                                                T("URL of the proxy server to connect to the repository (leave empty for default proxy)"))),
                           ),
                     Field("last_status",
                           label = T("Last status"),
                           readable = False,
                           writable = False,
                           ),
                     Field("accept_push", "boolean",
                           default = False,
                           label = T("Accept Push"),
                           represent = s3_yes_no_represent,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (
                                                T("Accept Push"),
                                                T("Accept unsolicited data transmissions from the repository."))),
                           ),
                     Field("synchronise_uuids", "boolean",
                           default = False,
                           label = T("Synchronize UUIDs"),
                           represent = s3_yes_no_represent,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (
                                                T("Synchronize UUIDs"),
                                                T("Allow records to be synchronized even if the remote record has a different unique identifier (UUID), and update local identifiers. Useful in active repositories when there are known duplicates in the remote database. Must be activated before the first synchronization run to take effect."))),
                           ),
                     Field("keep_source", "boolean",
                           default = False,
                           label = T("Keep Source Data"),
                           represent = s3_yes_no_represent,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (
                                                T("Keep Source Data"),
                                                T("Stores the data sent from the peer in the local file system (if supported by the adapter), for testing purposes. Enable only temporarily if and when required!"))),
                           ),
                     Field.Method("last_pull_time",
                                  self.sync_repository_last_pull_time),
                     Field.Method("last_push_time",
                                  self.sync_repository_last_push_time),
                     *s3_meta_fields())

        # CRUD Strings
        ADD_REPOSITORY = T("Create Repository")
        crud_strings[tablename] = Storage(
            label_create = ADD_REPOSITORY,
            title_display = T("Repository Configuration"),
            title_list = T("Repositories"),
            title_update = T("Edit Repository Configuration"),
            label_list_button = T("List Repositories"),
            msg_record_created = T("Repository configured"),
            msg_record_modified = T("Repository configuration updated"),
            msg_record_deleted = T("Repository configuration deleted"),
            msg_list_empty = T("No repositories configured"))

        # Resource Configuration
        configure(tablename,
                  deduplicate = S3Duplicate(primary=("name",)),
                  list_fields = ["name",
                                 "uuid",
                                 "accept_push",
                                 (T("Last Pull"), "last_pull_time"),
                                 (T("Last Push"), "last_push_time"),
                                 ],
                  onaccept = self.sync_repository_onaccept,
                  ondelete = self.sync_repository_ondelete,
                  create_next = URL(c="sync",
                                    f="repository",
                                    args=["[id]", "task"],
                                    ),
                  update_next = URL(c="sync",
                                    f="repository",
                                    args=["[id]"],
                                    ),
                  )

        set_method("sync", "repository",
                   method="now",
                   action=sync_now)

        # Reusable Fields
        sync_repository_represent = S3Represent(lookup=tablename)
        repository_id = S3ReusableField("repository_id", "reference %s" % tablename,
                                        comment = S3PopupLink(c = "sync",
                                                              f = "repository",
                                                              label = ADD_REPOSITORY,
                                                              title = ADD_REPOSITORY,
                                                              tooltip = ADD_REPOSITORY,
                                                              ),
                                        label = T("Repository"),
                                        represent = sync_repository_represent,
                                        requires = IS_ONE_OF(db,
                                                            "sync_repository.id",
                                                            "%(name)s",
                                                            ),
                                        )

        # Components
        add_components(tablename,
                       sync_task = "repository_id",
                       sync_log = "repository_id",
                       #sync_conflict = "repository_id",

                       **{# Scheduler Jobs
                          S3Task.TASK_TABLENAME: {"name": "job",
                                                  "joinby": "repository_id",
                                                  "link": "sync_job",
                                                  "key": "scheduler_task_id",
                                                  "actuate": "replace",
                                                 },
                         }
                      )

        # -------------------------------------------------------------------------
        # Task
        # -------------------------------------------------------------------------
        # Synchronization mode
        sync_mode = {
            1: T("pull"),           # pull only
            2: T("push"),           # push only
            3: T("pull and push"),  # pull & push
            4: T("none")            # do not synchronize this resource
        }

        # Strategy (allowed import methods)
        sync_strategy = S3ImportItem.METHOD

        sync_strategy_represent = lambda opt: opt and \
                                    ", ".join([o for o in sync_strategy.values()
                                            if o in opt]) or NONE

        # Update method
        sync_update_method = {
            1: T("update"),         # update the existing record
            2: T("replace"),        # replace the existing record
        }

        # Update/conflict resolution policy
        sync_policies = S3ImportItem.POLICY
        sync_policy = {
            sync_policies.OTHER: T("always update"),
            sync_policies.NEWER: T("update if newer"),
            sync_policies.MASTER: T("update if master"),
            sync_policies.THIS: T("never update")
        }

        sync_policy_represent = lambda opt: \
                                opt and sync_policy.get(opt, UNKNOWN_OPT) or NONE

        tablename = "sync_task"
        define_table(tablename,
                     repository_id(),
                     Field("resource_name", notnull = True,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (
                                                T("Resource Name"),
                                                T("Table name of the resource to synchronize"))),
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("infile_pattern",
                           label = T("Input File Name"),
                           readable = False,
                           writable = False,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (
                                                T("Input File Name"),
                                                T("Unix shell-style pattern for the input file name, e.g. 'example*.xml'"))),
                           ),
                     Field("delete_input_files", "boolean",
                           label = T("Delete Input Files?"),
                           default = False,
                           readable = False,
                           writable = False,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (
                                                T("Delete Input Files"),
                                                T("Whether to delete input files after successful import"))),
                           ),
                     Field("outfile_pattern",
                           label = T("Output File Name"),
                           readable = False,
                           writable = False,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (
                                                T("Output File Name"),
                                                T("The output file name. You can use place holders like 'example${minute}.xml'. Supported placeholders are: year, month, day, hour, minute, second"))),
                           ),
                     Field("human_readable", "boolean",
                           label = T("Human-readable Output?"),
                           default = False,
                           readable = False,
                           writable = False,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (
                                                T("Human-readable Output"),
                                                T("Shall XML output be formatted with whitespace and line breaks so that it is more human-readable?"))),
                           ),
                     Field("representation",
                           readable = False,
                           writable = False,
                           ),
                     # Multiple file per sync?
                     Field("multiple_file", "boolean",
                           default = False,
                           readable = False,
                           writable = False,
                           ),
                     Field("last_pull", "datetime",
                           label = T("Last pull on"),
                           readable = True,
                           writable = False,
                           ),
                     Field("last_push", "datetime",
                           label = T("Last push on"),
                           readable = True,
                           writable = False,
                           ),
                     Field("mode", "integer",
                           default = 3,
                           label = T("Mode"),
                           represent = lambda opt: \
                                       sync_mode.get(opt, NONE),
                           requires = IS_IN_SET(sync_mode,
                                                zero=None),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (
                                                T("Synchronization mode"),
                                                T("How data shall be transferred"))),
                           ),
                     Field("strategy", "list:string",
                           default = sync_strategy.values(),
                           label = T("Strategy"),
                           represent = sync_strategy_represent,
                           requires = IS_IN_SET(sync_strategy.values(),
                                                multiple=True,
                                                zero=None),
                           widget = CheckboxesWidgetS3.widget,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (
                                                T("Strategy"),
                                                T("Which methods to apply when importing data to the local repository"))),
                           ),
                     Field("update_method", "integer",
                           default = 1,
                           label = T("Update Method"),
                           represent = lambda opt: \
                                       sync_update_method.get(opt,
                                                              NONE),
                           requires = IS_IN_SET(sync_update_method,
                                                zero=None),
                           # hide while not implemented
                           readable = False,
                           writable = False,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (
                                                T("Update Method"),
                                                T("How local records shall be updated"))),
                           ),
                     Field("update_policy",
                           default = sync_policies.NEWER,
                           label = T("Update Policy"),
                           represent = sync_policy_represent,
                           requires = IS_IN_SET(sync_policies,
                                                zero=None),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (
                                                T("Update Policy"),
                                                T("Under which conditions local records shall be updated"))),
                           ),
                     Field("conflict_policy",
                           default = sync_policies.NEWER,
                           label = T("Conflict Policy"),
                           represent = sync_policy_represent,
                           requires = IS_IN_SET(sync_policies,
                                                zero=None),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (
                                                T("Conflict Policy"),
                                                T("Under which condition a local record shall be updated if it also has been modified locally since the last synchronization"))),
                           ),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Resource"),
            title_display = T("Resource Configuration"),
            title_list = T("Resources"),
            title_update = T("Edit Resource Configuration"),
            label_list_button = T("List Resources"),
            msg_record_created = T("Resource configured"),
            msg_record_modified = T("Resource configuration updated"),
            msg_record_deleted = T("Resource configuration deleted"),
            msg_list_empty = T("No resources configured yet"))

        # Resource Configuration
        configure(tablename,
                  create_onvalidation = self.sync_task_onvalidation,
                  deduplicate = S3Duplicate(primary=("repository_id",
                                                     "resource_name",
                                                     )),
                  )

        # Reusable Field
        task_represent = self.sync_task_represent
        task_id = S3ReusableField("task_id", "reference %s" % tablename,
                                  label = T("Task"),
                                  represent = task_represent,
                                  requires = IS_ONE_OF(db,
                                                       "sync_task.id",
                                                       task_represent),
                                  )

        # Components
        add_components(tablename,
                       sync_resource_filter = "task_id",
                       )

        # -------------------------------------------------------------------------
        # Filters
        # -------------------------------------------------------------------------
        tablename = "sync_resource_filter"
        define_table(tablename,
                     task_id(),
                     Field("tablename",
                           label = T("Table"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("filter_string",
                           label = T("Filter"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     *s3_meta_fields())

        onaccept = self.sync_resource_filter_onaccept
        configure(tablename,
                  list_fields = ["id",
                                 "task_id$repository_id",
                                 "task_id$resource_name",
                                 "tablename",
                                 "filter_string",
                                 ],
                  onaccept = onaccept,
                  ondelete = onaccept,
                  )

        # -------------------------------------------------------------------------
        # Job
        # -------------------------------------------------------------------------
        tablename = "sync_job"
        define_table(tablename,
                     repository_id(),
                     s3.scheduler_task_id(),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Job"),
            title_display = T("Synchronization Job"),
            title_list = T("Synchronization Schedule"),
            title_update = T("Edit Job"),
            label_list_button = T("List Jobs"),
            msg_record_created = T("Job added"),
            msg_record_modified = T("Job updated"),
            msg_record_deleted = T("Job deleted"),
            msg_list_empty = T("No jobs configured yet"),
            msg_no_match = T("No jobs configured"))

        # Resource Configuration
        set_method("sync", "repository",
                   component_name="job",
                   method="reset",
                   action=sync_job_reset)

        # -------------------------------------------------------------------------
        # Log
        # -------------------------------------------------------------------------
        tablename = "sync_log"
        define_table(tablename,
                     Field("timestmp", "datetime",
                           label = T("Date/Time"),
                           represent = s3_datetime_represent,
                           ),
                     repository_id(),
                     Field("resource_name"),
                     # Synchronization mode: PULL/PUSH, IN/OUT
                     Field("mode"),
                     Field("action"),
                     Field("result"),
                     Field("remote", "boolean",
                           default = False,
                           label = T("Remote Error"),
                           represent = s3_yes_no_represent,
                           ),
                     Field("message", "text",
                           represent = s3_strip_markup,
                           ),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
            title_display = T("Log Entry"),
            title_list = T("Synchronization Log"),
            label_list_button = T("List All Entries"),
            msg_record_deleted = T("Log Entry Deleted"),
            msg_list_empty = T("No entries found"),
            msg_no_match = T("No entries found"))

        # Resource Configuration
        configure(tablename,
                  deletable = True,
                  editable = False,
                  insertable = False,
                  orderby = "sync_log.timestmp desc",
                  )

        # ---------------------------------------------------------------------
        # Return global names to s3.*
        #
        return dict(sync_repository_id = repository_id,
                    sync_repository_onaccept = self.sync_repository_onaccept,
                    )

    # -------------------------------------------------------------------------
    def defaults(self):
        """ Safe defaults if module is disabled """

        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def sync_repository_last_pull_time(row):
        """ Last pull synchronization date/time for this repository """

        try:
            repository_id = row["sync_repository.id"]
        except AttributeError:
            return "-"

        table = current.s3db.sync_task
        query = (table.repository_id == repository_id)
        task = current.db(query).select(orderby=~table.last_pull,
                                        limitby=(0,1)).first()
        if task and task.last_pull:
            return S3DateTime.datetime_represent(task.last_pull, utc=True)
        else:
            return current.T("never")

    # -------------------------------------------------------------------------
    @staticmethod
    def sync_repository_last_push_time(row):
        """ Last push synchronization date/time for this repository """

        try:
            repository_id = row["sync_repository.id"]
        except AttributeError:
            return "-"

        table = current.s3db.sync_task
        query = (table.repository_id == repository_id)
        task = current.db(query).select(orderby=~table.last_push,
                                        limitby=(0,1)).first()
        if task and task.last_push:
            return S3DateTime.datetime_represent(task.last_push, utc=True)
        else:
            return current.T("never")

    # -------------------------------------------------------------------------
    @staticmethod
    def sync_task_represent(task_id):
        """
            Task representation

            @ToDo: Migrate to S3Represent
        """

        s3db = current.s3db

        ttable = s3db.sync_task
        rtable = s3db.sync_repository

        query = (ttable.id == task_id) & \
                (rtable.id == ttable.repository_id)

        db = current.db
        task = db(query).select(ttable.resource_name,
                                rtable.name,
                                limitby=(0, 1)).first()

        UNKNOWN_OPT = current.messages.UNKNOWN_OPT
        if task:
            repository = task[rtable.name] or UNKNOWN_OPT
            resource = task[ttable.resource_name] or UNKNOWN_OPT
            return "%s: %s" % (repository, resource)
        else:
            return UNKNOWN_OPT

    # -------------------------------------------------------------------------
    @staticmethod
    def sync_repository_ondelete(row):
        """
            Cleanup after repository deletion

            @todo: use standard delete cascade
        """

        db = current.db
        s3db = current.s3db

        # Remove the URL to allow re-setup of the same repo
        rtable = s3db.sync_repository
        db(rtable.id == row.id).update(url=None)

        # Delete all resources in this repository
        ttable = s3db.sync_task
        db(ttable.repository_id == row.id).update(deleted=True)

        # Delete all jobs for this repository
        # @todo: remove scheduler_task entry as well
        jtable = s3db.sync_job
        db(jtable.repository_id == row.id).update(deleted=True)

        # Delete all pending conflicts of this repository
        #ctable = s3db.sync_conflict
        #db(ctable.repository_id == row.id).delete()

        # Delete all log entries for this repository
        ltable = s3db.sync_log
        db(ltable.repository_id == row.id).delete()

        return

    # -------------------------------------------------------------------------
    @staticmethod
    def sync_repository_onaccept(form):
        """
            Send registration request to the peer
        """

        try:
            repository_id = form.vars.id
        except:
            return

        sync = current.sync

        if repository_id:
            rtable = current.s3db.sync_repository
            query = (rtable.id == repository_id)
            repository = current.db(query).select(limitby=(0, 1)).first()
            if repository and repository.url:
                from s3.s3sync import S3SyncRepository
                connector = S3SyncRepository(repository)
                success = connector.register()
                if not success:
                    current.response.warning = \
                        current.T("Could not auto-register at the repository, please register manually.")
                else:
                    current.response.confirmation = \
                        current.T("Successfully registered at the repository.")
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def sync_task_onvalidation(form):
        """
            Task record validation
        """

        repository_id = form.vars.repository_id or \
                        current.request.post_vars.repository_id
        resource_name = form.vars.resource_name

        if repository_id and resource_name:
            ttable = current.s3db.sync_task
            query = (ttable.repository_id == repository_id) & \
                    (ttable.resource_name == resource_name) & \
                    (ttable.deleted != True)
            row = current.db(query).select(ttable.id,
                                           limitby=(0, 1)).first()
            if row:
                form.errors.resource_name = \
                T("This resource is already configured for this repository")

    # -------------------------------------------------------------------------
    @staticmethod
    def sync_resource_filter_onaccept(form):
        """
            Reset last_push when adding/changing a filter
        """

        db = current.db
        s3db = current.s3db

        ttable = s3db.sync_task
        ftable = s3db.sync_resource_filter

        if isinstance(form, Row):
            filter_id = form.id
        else:
            try:
                filter_id = form.vars.id
            except:
                return

        row = db(ftable.id == filter_id).select(ftable.id,
                                                ftable.deleted,
                                                ftable.task_id,
                                                ftable.deleted_fk,
                                                limitby=(0, 1)).first()

        if row:
            task_id = None
            if row.deleted:
                try:
                    deleted_fk = json.loads(row.deleted_fk)
                except:
                    return
                if "task_id" in deleted_fk:
                    task_id = deleted_fk["task_id"]
            else:
                task_id = row.task_id
            if task_id:
                db(ttable.id == task_id).update(last_push=None)

        return

# =============================================================================
def sync_rheader(r, tabs=[]):
    """
        Synchronization resource headers
    """

    if r.representation == "html":
        if r.tablename == "sync_repository":
            T = current.T
            repository = r.record
            if r.component and r.component_name=="log" and not r.component_id:
                purge_log = A(T("Remove all log entries"),
                              _href=r.url(method="delete"))
            else:
                purge_log = ""
            if repository:
                if repository.url or \
                   repository.apitype == "filesync" and repository.path:
                    tabs.append((T("Manual Synchronization"), "now"))
                rheader_tabs = s3_rheader_tabs(r, tabs)
                rheader = DIV(TABLE(
                    TR(TH("%s: " % T("Name")),
                       repository.name,
                       TH(""),
                       purge_log),
                    TR(TH("URL: "),
                       repository.url,
                       TH(""),
                       ""),
                    ), rheader_tabs)
                return rheader
    return None

# =============================================================================
def sync_job_reset(r, **attr):
    """
        RESTful method to reset a job status from FAILED to QUEUED,
        for "Reset" action button
    """

    if r.interactive:
        if r.component and r.component.alias == "job":
            job_id = r.component_id
            if job_id:
                S3Task.reset(job_id)
                current.session.confirmation = current.T("Job reactivated")
    r.component_id = None
    redirect(r.url(method=""))

# =============================================================================
def sync_now(r, **attr):
    """
        Manual synchronization of a repository

        @param r: the S3Request
        @param attr: controller options for the request
    """

    T = current.T
    auth = current.auth
    response = current.response

    rheader = attr.get("rheader", None)
    if rheader:
        rheader = rheader(r)

    output = dict(title=T("Manual Synchronization"), rheader=rheader)
    s3task = current.s3task

    sync = current.sync

    if not auth.s3_logged_in():
        auth.permission.fail()

    if r.interactive:
        if r.http in ("GET", "POST"):
            repository = r.record
            if not repository:
                r.error(404, current.ERROR.BAD_RECORD)
            form = FORM(TABLE(
                        TR(TD(T("Click 'Start' to synchronize with this repository now:"))),
                        TR(TD(INPUT(_type="submit", _value=T("Start"))))))
            if form.accepts(r.post_vars, current.session):
                task_id = s3task.async("sync_synchronize",
                                       args = [repository.id],
                                       vars = dict(user_id=auth.user.id,
                                                   manual=True))
                if task_id is False:
                    response.error = T("Could not initiate manual synchronization.")
                elif task_id is None:
                    response.flash = T("Manual synchronization completed.")
                else:
                    sync.set_status(manual=True)
                    response.flash = T("Manual synchronization started in the background.")
        else:
            r.error(405, current.ERROR.BAD_METHOD)
    else:
        r.error(415, current.ERROR.BAD_FORMAT)

    status = sync.get_status()
    if status.running:
        output.update(form=T("Synchronization currently active - refresh page to update status."))
    elif not status.manual:
        output.update(form=form)
    else:
        output.update(form=T("Manual synchronization scheduled - refresh page to update status."))

    response.view = "update.html"
    return output

# END =========================================================================
