# -*- coding: utf-8 -*-

"""
    Synchronization, Model

    @author: Dominic König <dominic[at]aidiq[dot]com>
"""

def sync_tables():
    """ Synchronization tables loader """

    if "sync_config" in db:
        return

    # -------------------------------------------------------------------------
    # Configuration
    # -------------------------------------------------------------------------
    tablename = "sync_config"
    table = db.define_table(tablename,
                            Field("proxy",
                                  label=T("Proxy Server URL"),
                                  requires=IS_EMPTY_OR(
                                                IS_URL(mode="generic"))),
                            *s3_meta_fields())

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

    # CRUD strings
    s3.crud_strings[tablename] = Storage(
        title_display = T("Synchronization Settings"),
        title_update = T("Edit Synchronization Settings"),
        msg_record_modified = T("Synchronization settings updated"))

    # CRUD configuration
    s3mgr.configure(tablename,
                    insertable=False,
                    deletable=False,
                    update_next=URL(c="sync", f="config",
                                    args=["1", "update"]))

    # -------------------------------------------------------------------------
    # Status
    # -------------------------------------------------------------------------
    tablename = "sync_status"
    table = db.define_table(tablename,
                            Field("running", "boolean",
                                  default=False,
                                  readable=False,
                                  writable=False),
                            Field("manual", "boolean",
                                  default=False,
                                  readable=False,
                                  writable=False),
                            Field("timestmp", "datetime",
                                  readable=False,
                                  writable=False))

    # -------------------------------------------------------------------------
    # Repository
    # -------------------------------------------------------------------------
    tablename = "sync_repository"
    table = db.define_table(tablename,
                            Field("name",
                                  length=64,
                                  notnull=True),
                            Field("url",
                                  label="URL"),
                            Field("username"),
                            Field("password", "password"),
                            Field("proxy",
                                  label=T("Proxy Server URL"),
                                  requires=IS_EMPTY_OR(
                                                IS_URL(mode="generic"))),
                            Field("last_status",
                                  readable=False,
                                  writable=False,
                                  label=T("Last status")),
                            Field("accept_push", "boolean",
                                  default=False,
                                  label=T("Accept Push")),
                            *s3_meta_fields())

    table.uuid.readable = True
    table.uuid.writable = True
    table.uuid.label = "UUID"

    table.url.requires = IS_EMPTY_OR(IS_NOT_IN_DB(db, "sync_repository.url"))

    table.name.comment = DIV(_class="tooltip",
                             _title="%s|%s" % (
                                T("Repository Name"),
                                T("Name of the repository (for you own reference)")))
    table.url.comment = DIV(_class="tooltip",
                            _title="%s|%s" % (
                                T("Repository Base URL"),
                                T("Base URL of the remote Sahana Eden instance including application path, e.g. http://www.example.org/eden")))
    table.proxy.comment = DIV(_class="tooltip",
                              _title="%s|%s" % (
                                T("Proxy Server URL"),
                                T("URL of the proxy server to connect to the repository (leave empty for default proxy)")))
    table.username.comment = DIV(_class="tooltip",
                                 _title="%s|%s" % (
                                    T("Username"),
                                    T("Username to use for authentication at the remote site.")))
    table.password.comment = DIV(_class="tooltip",
                                 _title="%s|%s" % (
                                    T("Password"),
                                    T("Password to use for authentication at the remote site.")))
    table.uuid.comment = DIV(_class="tooltip",
                             _title="%s|%s" % (
                                T("Repository UUID"),
                                T("Identifier which the repository identifies itself with when sending synchronization requests.")))
    table.accept_push.comment = DIV(_class="tooltip",
                                    _title="%s|%s" % (
                                        T("Accept Push"),
                                        T("Accept unsolicited data transmissions from the repository.")))

    # CRUD strings
    ADD_REPOSITORY = T("Add Repository")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_REPOSITORY,
        title_display = T("Repository Configuration"),
        title_list = T("Repositories"),
        title_update = T("Edit Repository Configuration"),
        title_search = T("Search for Repository"),
        subtitle_create = T("Add Repository"),
        subtitle_list = T("Currently Configured Repositories"),
        label_list_button = T("List Repositories"),
        label_create_button = ADD_REPOSITORY,
        msg_record_created = T("Repository configured"),
        msg_record_modified = T("Repository configuration updated"),
        msg_record_deleted = T("Repository configuration deleted"),
        msg_list_empty = T("No repositories configured"))

    # -------------------------------------------------------------------------
    # Repository representation
    def sync_repository_represent(rid):

        rtable = db.sync_repository
        repository = db(rtable.id == rid).select(rtable.name,
                                                 limitby=(0, 1)).first()
        if repository:
            return repository.name
        else:
            return NONE

    # -------------------------------------------------------------------------
    # Reusable repository_id
    repository_id = S3ReusableField("repository_id", db.sync_repository,
                                    requires = IS_ONE_OF(db,
                                                         "sync_repository.id",
                                                         "%(name)s"),
                                    represent = sync_repository_represent,
                                    label = T("Repository"))

    # -------------------------------------------------------------------------
    def sync_repository_ondelete(row):
        """
            Cleanup after repository deletion

            @todo: use standard delete cascade
        """

        # Delete all resources in this repository
        rtable = db.sync_resource
        db(rtable.repository_id == row.id).update(deleted=True)

        # Delete all jobs for this repository
        # @todo: remove scheduler_task entry as well
        jtable = db.sync_job
        db(jtable.repository_id == row.id).update(deleted=True)

        # Delete all pending conflicts of this repository
        ctable = db.sync_conflict
        db(ctable.repository_id == row.id).delete()

        # Delete all log entries for this repository
        ltable = db.sync_log
        db(ltable.repository_id == row.id).delete()

    # -------------------------------------------------------------------------
    def sync_repository_onaccept(form):
        """
            Send registration request to the peer
        """

        try:
            repository_id = form.vars.id
        except:
            return

        if repository_id:
            rtable = db.sync_repository
            query = rtable.id == repository_id
            repository = db(query).select(limitby=(0, 1)).first()
            if repository and repository.url:
                sync = current.manager.sync
                success = sync.request_registration(repository)
                if not success:
                    response.warning = T("Could not auto-register at the repository, please register manually.")
                else:
                    response.confirmation = T("Successfully registered at the repository.")
        return

    # -------------------------------------------------------------------------
    # Repository virtual list fields
    class SyncRepositoryVirtualFields:
        def last_sync_time(self):
            table = db.sync_task
            query = table.repository_id == self.sync_repository.id
            task = db(query).select(orderby=~table.last_sync,
                                    limitby=(0,1)).first()
            if task:
                return s3_datetime_represent(task.last_sync, utc=True)
            else:
                return T("never")
    table.virtualfields.append(SyncRepositoryVirtualFields())

    # -------------------------------------------------------------------------
    # Repository table configuration
    s3mgr.configure(tablename,
                    list_fields=["name",
                                 "uuid",
                                 "accept_push",
                                 (T("Last Synchronization"),
                                        "last_sync_time")],
                    onaccept=sync_repository_onaccept,
                    ondelete=sync_repository_ondelete,
                    create_next=URL(c="sync", f="repository",
                                    args=["[id]", "task"]),
                    update_next=URL(c="sync", f="repository",
                                    args=["[id]"]))

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
    sync_strategy = s3base.S3ImportItem.METHOD

    sync_strategy_represent = lambda opt: opt and \
                                ", ".join([o for o in sync_strategy.values()
                                           if o in opt]) or NONE

    # Update method
    sync_update_method = {
        1: T("update"),         # update the existing record
        2: T("replace"),        # replace the existing record
    }

    # Update/conflict resolution policy
    sync_policies = s3base.S3ImportItem.POLICY
    sync_policy = {
        sync_policies.OTHER: T("always update"),
        sync_policies.NEWER: T("update if newer"),
        sync_policies.MASTER: T("update if master"),
        sync_policies.THIS: T("never update")
    }

    sync_policy_represent = lambda opt: \
                            opt and sync_policy.get(opt, UNKNOWN_OPT) or NONE

    tablename = "sync_task"
    table = db.define_table(tablename,
                            Field("resource_name",
                                  notnull=True),
                            repository_id(),
                            Field("last_sync", "datetime",
                                  readable=True,
                                  writable=False,
                                  update="",
                                  label=T("Last synchronized on")),
                            Field("mode", "integer",
                                  requires = IS_IN_SET(sync_mode,
                                                       zero=None),
                                  default = 3,
                                  label = T("Mode"),
                                  represent = lambda opt: \
                                              sync_mode.get(opt, NONE)),

                            Field("strategy", "list:string",
                                  requires = IS_IN_SET(sync_strategy.values(),
                                                       multiple=True,
                                                       zero=None),
                                  default = sync_strategy.values(),
                                  label = T("Strategy"),
                                  represent = sync_strategy_represent,
                                  widget = CheckboxesWidgetS3.widget),

                            Field("update_method", "integer",
                                  # hide while not implemented
                                  readable=False,
                                  writable=False,
                                  requires = IS_IN_SET(sync_update_method,
                                                       zero=None),
                                  default = 1,
                                  label = T("Update Method"),
                                  represent = lambda opt: \
                                              sync_update_method.get(opt,
                                                                     NONE)),

                            Field("update_policy",
                                  requires = IS_IN_SET(sync_policies,
                                                       zero=None),
                                  default = sync_policies.NEWER,
                                  label = T("Update Policy"),
                                  represent = sync_policy_represent),

                            Field("conflict_policy",
                                  requires = IS_IN_SET(sync_policies,
                                                       zero=None),
                                  default = sync_policies.NEWER,
                                  label = T("Conflict Policy"),
                                  represent = sync_policy_represent),

                            *s3_meta_fields())

    table.resource_name.comment = DIV(_class="tooltip",
                                      _title="%s|%s" % (
                                        T("Resource Name"),
                                        T("Table name of the resource to synchronize")))

    table.mode.comment = DIV(_class="tooltip",
                             _title="%s|%s" % (
                                T("Synchronization mode"),
                                T("How data shall be transferred")))
    table.strategy.comment = DIV(_class="tooltip",
                                 _title="%s|%s" % (
                                    T("Strategy"),
                                    T("Which methods to apply when importing data to the local repository")))
    table.update_method.comment = DIV(_class="tooltip",
                                      _title="%s|%s" % (
                                        T("Update Method"),
                                        T("How local records shall be updated")))
    table.update_policy.comment = DIV(_class="tooltip",
                                      _title="%s|%s" % (
                                        T("Update Policy"),
                                        T("Under which conditions local records shall be updated")))
    table.conflict_policy.comment = DIV(_class="tooltip",
                                        _title="%s|%s" % (
                                            T("Conflict policy"),
                                            T("Under which condition a local record shall be updated if it also has been modified locally since the last synchronization")))

    # CRUD strings
    ADD_TASK = T("Add Resource")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_TASK,
        title_display = T("Resource Configuration"),
        title_list = T("Resources"),
        title_update = T("Edit Resource Configuration"),
        title_search = T("Search for Resource"),
        subtitle_create = ADD_TASK,
        subtitle_list = T("Currently Configured Resources"),
        label_list_button = T("List Resources"),
        label_create_button = ADD_TASK,
        msg_record_created = T("Resource configured"),
        msg_record_modified = T("Resource configuration updated"),
        msg_record_deleted = T("Resource configuration deleted"),
        msg_list_empty = T("No resources configured yet"))

    # -------------------------------------------------------------------------
    def sync_task_onvalidation(form):

        repository_id = form.vars.repository_id or \
                        request.post_vars.repository_id
        resource_name = form.vars.resource_name

        if repository_id and resource_name:
            ttable = db.sync_task
            query = (ttable.repository_id == repository_id) & \
                    (ttable.resource_name == resource_name) & \
                    (ttable.deleted != True)
            row = db(query).select(ttable.id, limitby=(0, 1)).first()
            if row:
                form.errors.resource_name = \
                T("This resource is already configured for this repository")

    s3mgr.configure(tablename,
                    create_onvalidation=sync_task_onvalidation)

    # -------------------------------------------------------------------------
    # Job
    # -------------------------------------------------------------------------
    tablename = "sync_job"
    table = db.define_table(tablename,
                            repository_id(),
                            scheduler_task_id())

    # CRUD strings
    ADD_JOB = T("Add Job")
    s3.crud_strings[tablename] = Storage(
        title_create = ADD_JOB,
        title_display = T("Synchronization Job"),
        title_list = T("Synchronization Schedule"),
        title_update = T("Edit Job"),
        title_search = T("Search for Job"),
        subtitle_create = ADD_JOB,
        subtitle_list = T("Currently Configured Jobs"),
        label_list_button = T("List Jobs"),
        label_create_button = ADD_JOB,
        msg_record_created = T("Job added"),
        msg_record_modified = T("Job updated updated"),
        msg_record_deleted = T("Job deleted"),
        msg_list_empty = T("No jobs configured yet"),
        msg_no_match = T("No jobs configured"))

    # -------------------------------------------------------------------------
    def sync_job_reset(r, **attr):
        """
            RESTful method to reset a job status from FAILED to QUEUED, for
            "Reset" action button
        """

        if r.interactive:
            if r.component and r.component.alias == "job":
                job_id = r.component_id
                if job_id:
                    s3base.S3Task.reset(job_id)
                    session.confirmation = T("Job reactivated")
        r.component_id = None
        redirect(r.url(method=""))

    # Add as method for the "job" component
    s3mgr.model.set_method("sync", "repository",
                           component_name="job",
                           method="reset",
                           action=sync_job_reset)

    # -------------------------------------------------------------------------
    # Conflicts
    # -------------------------------------------------------------------------
    tablename = "sync_conflict"
    table = db.define_table(tablename,
                            repository_id(),
                            Field("dummy"))
    # @todo: implement table
    # @todo: CRUD strings

    s3mgr.configure(tablename,
                    insertable=False,
                    editable=False)

    # -------------------------------------------------------------------------
    # Log
    # -------------------------------------------------------------------------
    tablename = "sync_log"
    table = db.define_table(tablename,
                            Field("timestmp", "datetime",
                                  represent=lambda dt: \
                                        s3_datetime_represent(dt, utc=True),
                                  label=T("Date/Time")),
                            repository_id(),
                            Field("resource_name"),
                            # Synchronization mode: PULL/PUSH, IN/OUT
                            Field("mode"),
                            Field("action"),
                            Field("result"),
                            Field("remote", "boolean",
                                  default=False,
                                  label=T("Remote Error"),
                                  represent=lambda opt: opt and T("yes") or ("no")),
                            Field("message", "text"),
                            *s3_meta_fields())

    # CRUD strings
    s3.crud_strings[tablename] = Storage(
        title_display = T("Log Entry"),
        title_list = T("Synchronization Log"),
        subtitle_list = T("Synchronization Log"),
        label_list_button = T("List All Entries"),
        msg_record_deleted = T("Log Entry Deleted"),
        msg_list_empty = T("No entries found"),
        msg_no_match = T("No entries found"))

    # Configuration
    s3mgr.configure(tablename,
                    editable=False,
                    insertable=False,
                    deletable=True,
                    orderby=~table.timestmp)

    # -------------------------------------------------------------------------

# Component definitions
s3mgr.model.add_component("sync_task",
                          sync_repository="repository_id")

s3mgr.model.add_component(s3base.S3Task.TASK_TABLENAME,
                          sync_repository=dict(name="job",
                                               joinby="repository_id",
                                               link="sync_job",
                                               key="scheduler_task_id",
                                               actuate="replace"))

s3mgr.model.add_component("sync_log",
                          sync_repository="repository_id")

s3mgr.model.add_component("sync_conflict",
                          sync_repository="repository_id")

# Loader configuration
s3mgr.model.loader(sync_tables,
                   "sync_config",
                   "sync_status",
                   "sync_repository",
                   "sync_resource",
                   "sync_job",
                   "sync_conflict",
                   "sync_log")

# -----------------------------------------------------------------------------
def sync_rheader(r, tabs=[]):
    """
        Synchronization resource headers
    """

    T = current.T

    if r.representation == "html":

        if r.tablename == "sync_repository":
            repository = r.record
            if r.component and r.component_name=="log" and not r.component_id:
                purge_log = A(T("Remove all log entries"),
                              _href=r.url(method="delete"))
            else:
                purge_log = ""
            if repository:
                if repository.url:
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

# -----------------------------------------------------------------------------
def sync_now(r, **attr):
    """
        Manual synchronization of a repository
    """

    manager = current.manager

    rheader = attr.get("rheader", None)
    if rheader:
        rheader = rheader(r)

    output = dict(title=T("Manual Synchronization"), rheader=rheader)
    s3task = current.s3task

    sync = s3base.S3Sync()

    if r.interactive:
        if r.http in ("GET", "POST"):
            repository = r.record
            if not repository:
                r.error(404, manager.ERROR.BAD_RECORD)
            form = FORM(TABLE(
                        TR(TD(T("Click 'Start' to synchronize with this repository now:"))),
                        TR(TD(INPUT(_type="submit", _value=T("Start"))))))
            if form.accepts(r.post_vars, session):
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
            r.error(405, manager.ERROR.BAD_METHOD)
    else:
        r.error(501, manager.ERROR.BAD_FORMAT)

    status = sync.get_status()
    if status.running:
        output.update(form=T("Synchronization currently active - refresh page to update status."))
    elif not status.manual:
        output.update(form=form)
    else:
        output.update(form=T("Manual synchronization scheduled - refresh page to update status."))

    response.view = "update.html"
    return output

s3mgr.model.set_method("sync", "repository", method="now", action=sync_now)

# END =========================================================================
