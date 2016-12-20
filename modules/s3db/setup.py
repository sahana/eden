# -*- coding: utf-8 -*-

""" Sahana Eden Setup Model

@copyright: 2015-2016 (c) Sahana Software Foundation
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
__all__ = ("S3DeployModel",
           "setup_create_yaml_file",
           "setup_create_playbook",
           "setup_get_templates",
           "setup_get_prepop_options",
           "setup_log",
           "setup_rheader",
           "setup_management_exists",
           "setup_UpgradeMethod",
           "setup_refresh",
           "setup_getupgrades",
           "setup_host_validator",
           "setup_upgrade_status",
           )

from ..s3 import *
from gluon import *
import os
import socket
import shutil
import time

try:
    import ansible.playbook
    import ansible.inventory
    from ansible import callbacks
except ImportError:
    current.log.warning("ansible module needed for Setup")

try:
    import yaml
except ImportError:
    current.log.warning("PyYAML module needed for Setup")

TIME_FORMAT = "%b %d %Y %H:%M:%S"
MSG_FORMAT = "%(now)s - %(category)s - %(data)s\n\n"


class S3DeployModel(S3Model):

    names = ("setup_deployment",
             "setup_server",
             "setup_instance",
             "setup_host",
             "setup_packages",
             "setup_upgrade"
             )

    def model(self):

        T = current.T
        s3 = current.response.s3

        define_table = self.define_table
        configure = self.configure
        add_components = self.add_components
        set_method = self.set_method

        tablename = "setup_deployment"

        define_table(tablename,
                     Field("name",
                           label = T("Name"),
                           required = True,
                           ),
                     Field("distro",
                           label = T("Linux Distribution"),
                           required = True,
                           requires = IS_IN_SET(
                                   [
                                       ("wheezy", "Debian Wheezy"),
                                       ("precise", "Ubuntu 14.04 LTS Precise"),
                                   ])
                           ),
                     Field("remote_user",
                           label = T("Remote User"),
                           required = True,
                           ),
                     Field("secret_key",
                           label = T("AWS Secret Key"),
                           required = True,
                           ),
                     Field("access_key",
                           label = T("AWS Access Key"),
                           required = True,
                           ),
                     Field("private_key", "upload",
                           custom_retrieve = retrieve_file,
                           custom_store = store_file,
                           label = T("Private Key"),
                           length = current.MAX_FILENAME_LENGTH,
                           required = True,
                           requires = IS_LENGTH(current.MAX_FILENAME_LENGTH),
                           ),
                     Field("webserver_type", "integer",
                           label = T("Web Server"),
                           required = True,
                           requires = IS_IN_SET({1:"apache", 2:"cherokee"}),
                           ),
                     Field("db_type", "integer",
                           label = T("Database"),
                           required = True,
                           requires = IS_IN_SET({1:"mysql", 2: "postgresql"}),
                           ),
                     Field("db_password", "password",
                           label = T("Database Password"),
                           required = True,
                           readable = False,
                           ),
                     Field("repo_url",
                           # @ToDo: Add more advanced options
                           default = "https://github.com/flavour/eden",
                           label = T("Eden Repo git URL"),
                           ),
                     # @ToDo: Allow Multiple
                     Field("template",
                           label = T("Template"),
                           required = True,
                           requires = IS_IN_SET(setup_get_templates(), zero=None),
                           ),
                     Field("refresh_lock", "integer",
                           default = 0,
                           readable = False,
                           writable = False,
                           ),
                     Field("last_refreshed", "datetime",
                           readable = False,
                           writable = False,
                           ),
                     *s3_meta_fields()
                    )

        # CRUD Strings
        s3.crud_strings[tablename] = Storage(
            label_create_button = T("Add Deployment"),
            label_list_button = T("View Deployments"),
            label_delete_button = T("Delete Deployment"),
            msg_record_created = T("Deployment Created"),
            msg_record_modified = T("Deployment updated"),
            msg_record_deleted = T("Deployment deleted"),
            msg_list_empty = T("No Deployment Saved yet"),
            subtitle_create = T("Add Deployment"),
            title_create = T("Add Deployment"),
            title_list = T("View Deployments"),
            title_update = T("Edit Deployment"),
        )

        configure(tablename,
                  editable = False,
                  deletable = False,
                  insertable = True,
                  listadd = True
                  )

        tablename = "setup_server"

        define_table(tablename,
                     Field("deployment_id", "reference setup_deployment"),
                     Field("role", "integer",
                           requires = IS_IN_SET({1: "all",
                                                 2: "db",
                                                 3: "webserver",
                                                 4: "eden",
                                                 }),
                           ),
                     Field("host_ip",
                           required = True,
                           ),
                     Field("hostname",
                           label = "Hostname",
                           required = True,
                           ),
                     )

        configure(tablename,
                  onvalidation = server_validation
                  )

        tablename = "setup_instance"

        define_table(tablename,
                     Field("deployment_id", "reference setup_deployment"),
                     Field("type", "integer",
                           requires = IS_IN_SET({1: "prod", 2: "test", 3: "demo", 4: "dev"})
                           ),
                     Field("url",
                           requires = IS_URL(),
                           ),
                     Field("prepop_options",
                           label = "Prepop Options",
                           required = True,
                           requires = IS_IN_SET([], multiple=True),
                           ),
                     Field("scheduler_id", "reference scheduler_task",
                           readable = False,
                           writable = False,
                           ),
                     )

        configure(tablename,
                  deletable = False,
                  editable = False,
                  onaccept = instance_onaccept,
                  )

        add_components("setup_deployment",
                       setup_instance = "deployment_id",
                       setup_server = "deployment_id",
                       )

        tablename = "setup_packages"

        define_table(tablename,
                     Field("name",
                           label = T("Package Name"),
                           ),
                     Field("cv",
                           label = T("Current Version"),
                           ),
                     Field("av",
                           label = T("Available Version"),
                           ),
                     Field("type",
                           label = T("Type of Package"),
                           requires = IS_IN_SET(["os", "pip", "git"]),
                           ),
                     Field("deployment",
                           "reference setup_deployment",
                           ),
                    )

        tablename = "setup_upgrade"

        define_table(tablename,
                     Field("deployment",
                           "reference setup_deployment"
                           ),
                     Field("scheduler",
                           "reference scheduler_task"
                          ),
                     )

        set_method("setup", "deploy",
                   method = "upgrade",
                   action = setup_UpgradeMethod,
                   )

        return {}

    # -------------------------------------------------------------------------
    def defaults(self):
        """
        Safe defaults for model-global names in case module is disabled
        """
        return {}

# -----------------------------------------------------------------------------
def server_validation(form):

    ip = form.vars.host_ip
    table = current.s3db.setup_server
    db = current.db

    rows = db(table.host_ip == ip).select()

    if rows:
        form.errors["host_ip"] = "Server already in use"

# -----------------------------------------------------------------------------
def instance_onaccept(form):

    db = current.db
    s3db = current.s3db
    form_vars = form.vars

    # Get deployment id
    itable = s3db.setup_instance
    instance = db(itable.id == form_vars.id).select(itable.deployment_id,
                                                    limitby = (0, 1)
                                                    ).first()
    deployment_id = instance.deployment_id

    stable = s3db.setup_server
    query = (stable.deployment_id == deployment_id)
    rows = db(query).select(stable.role,
                            stable.host_ip,
                            stable.hostname,
                            orderby = stable.role
                            )

    hosts = []
    for row in rows:
        hosts.append((row.role, row.host_ip))
        if row.role == 1 or row.role == 4:
            hostname = row.hostname


    dtable = s3db.setup_deployment
    deployment = db(dtable.id == deployment_id).select(dtable.db_password,
                                                       dtable.webserver_type,
                                                       dtable.db_type,
                                                       dtable.distro,
                                                       dtable.template,
                                                       dtable.private_key,
                                                       dtable.remote_user,
                                                       limitby=(0, 1)
                                                       ).first()

    prepop_options = str(",".join(form_vars.prepop_options))

    instance_type = int(form_vars.type)
    if instance_type  == 2:
        demo_type = "na"
    elif instance_type == 1 or instance_type == 3:
        # find dtype
        sctable = s3db.scheduler_task
        query = (itable.deployment_id == deployment_id) & \
                (sctable.status == "COMPLETED")
        existing_instances = db(query).select(itable.type,
                                              join = sctable.on(itable.scheduler_id == sctable.id)
                                              )

        if existing_instances:
            demo_type = "afterprod"
        else:
            demo_type = "beforeprod"

    webservers = ("apache", "cherokee")
    dbs = ("mysql", "postgresql")
    prepop = ("prod", "test", "demo")
    scheduler_id = setup_create_yaml_file(hosts,
                                          deployment.db_password,
                                          webservers[deployment.webserver_type - 1],
                                          dbs[deployment.db_type - 1],
                                          prepop[instance_type - 1],
                                          prepop_options,
                                          deployment.distro,
                                          False,
                                          hostname,
                                          deployment.template,
                                          form_vars.url,
                                          deployment.private_key,
                                          deployment.remote_user,
                                          demo_type,
                                          )
    # add scheduler fk in current record
    record = db(itable.id == form_vars.id).select().first()
    record.update_record(scheduler_id=scheduler_id)

# -----------------------------------------------------------------------------
def setup_create_yaml_file(hosts, password, web_server, database_type,
                           prepop, prepop_options, distro, local=False,
                           hostname=None, template="default", sitename=None,
                           private_key=None, remote_user=None, demo_type=None):

    roles_path = "../private/playbook/roles/"

    if len(hosts) == 1:
        deployment = [
            {
                "hosts": hosts[0][1],
                "sudo": True,
                "remote_user": remote_user,
                "vars": {
                    "password": password,
                    "template": template,
                    "web_server": web_server,
                    "type": prepop,
                    "distro": distro,
                    "prepop_options": prepop_options,
                    "sitename": sitename,
                    "hostname": hostname,
                    "dtype": demo_type,
                    "eden_ip": hosts[0][1],
                    "db_ip": hosts[0][1],
                    "db_type": database_type
                },
                "roles": [
                    "%s%s" % (roles_path, database_type),
                    "%scommon" % roles_path,
                    "%suwsgi" % roles_path,
                    "%sconfigure" % roles_path,
                    "%s%s" % (roles_path, web_server),
                ]
            }
        ]
    else:
        deployment = [
            {
                "hosts": hosts[0][1],
                "sudo": True,
                "remote_user": remote_user,
                "vars": {
                    "distro": distro,
                    "dtype": demo_type,
                    "password": password,
                    "type": prepop
                },
                "roles": [
                    "%s%s" % (roles_path, database_type),
                ]
            },
            {
                "hosts": hosts[2][1],
                "sudo": True,
                "remote_user": remote_user,
                "vars": {
                    "dtype": demo_type,
                    "db_ip": hosts[0][1],
                    "db_type": database_type,
                    "hostname": hostname,
                    "password": password,
                    "prepop_options": prepop_options,
                    "sitename": sitename,
                    "template": template,
                    "type": prepop,
                    "web_server": web_server,
                },
                "roles": [
                    "%scommon" % roles_path,
                    "%suwsgi" % roles_path,
                    "%sconfigure" % roles_path,
                ]
            },
            {
                "hosts": hosts[1][1],
                "sudo": True,
                "remote_user": remote_user,
                "vars": {
                    "eden_ip": hosts[2][1],
                    "type": prepop
                },
                "roles": [
                    "%s%s" % (roles_path, web_server),
                ]
            }
        ]

    if demo_type == "afterprod":
        only_tags = ["demo"]
    elif prepop == "test":
        only_tags = ["test",]
    else:
        only_tags = ["all"]

    directory = os.path.join(current.request.folder, "yaml")
    name = "deployment_%d" % int(time.time())
    file_path = os.path.join(directory, "%s.yml" % name)

    if not os.path.isdir(directory):
        os.mkdir(directory)
    with open(file_path, "w") as yaml_file:
        yaml_file.write(yaml.dump(deployment, default_flow_style=False))

    row = current.s3task.schedule_task(
        name,
        vars = {
            "playbook": file_path,
            "private_key": os.path.join(current.request.folder, "uploads", private_key),
            "host": [host[1] for host in hosts],
            "only_tags": only_tags,
        },
        function_name = "deploy",
        repeats = 1,
        timeout = 3600,
        sync_output = 300
    )

    return row


# -----------------------------------------------------------------------------
def setup_create_playbook(playbook, hosts, private_key, only_tags):

    inventory = ansible.inventory.Inventory(hosts)
    #playbook_cb = callbacks.PlaybookCallbacks(verbose=utils.VERBOSITY)
    stats = callbacks.AggregateStats()
    # runner_cb = callbacks.PlaybookRunnerCallbacks(
    #     stats, verbose=utils.VERBOSITY)

    head, tail = os.path.split(playbook)
    deployment_name = tail.rsplit(".")[0]

    cb = CallbackModule(deployment_name)

    pb = ansible.playbook.PlayBook(
        playbook = playbook,
        inventory = inventory,
        callbacks = cb,
        runner_callbacks = cb,
        stats = stats,
        private_key_file = private_key,
        only_tags = only_tags
    )

    return pb

# -----------------------------------------------------------------------------
def setup_get_prepop_options(template):
    module_name = "applications.eden_deployment.modules.templates.%s.config" % template
    __import__(module_name)
    config = sys.modules[module_name]
    prepopulate_options = config.settings.base.get("prepopulate_options")
    if isinstance(prepopulate_options, dict):
        if "mandatory" in prepopulate_options:
            del prepopulate_options["mandatory"]
        return prepopulate_options.keys()
    else:
        return ["mandatory"]

# -----------------------------------------------------------------------------
def setup_log(filename, category, data):
    if type(data) == dict:
        if 'verbose_override' in data:
            # avoid logging extraneous data from facts
            data = 'omitted'
        else:
            data = data.copy()
            invocation = data.pop('invocation', None)
            data = json.dumps(data)
            if invocation is not None:
                data = json.dumps(invocation) + " => %s " % data

    path = os.path.join(current.request.folder, "yaml", "%s.log" % filename)
    now = time.strftime(TIME_FORMAT, time.localtime())
    fd = open(path, "a")
    fd.write(MSG_FORMAT % dict(now=now, category=category, data=data))
    fd.close()

# -----------------------------------------------------------------------------
def setup_get_templates():
    path = os.path.join(current.request.folder, "modules", "templates")
    templates = set(os.path.basename(folder) for folder, subfolders, files in os.walk(path) \
                        for file_ in files if file_ == "config.py"
                    )

    return templates

# -----------------------------------------------------------------------------
def store_file(file, filename=None, path=None):
    path = os.path.join(current.request.folder, "uploads")
    if not os.path.exists(path):
         os.makedirs(path)
    pathfilename = os.path.join(path, filename)
    dest_file = open(pathfilename, 'wb')
    try:
            shutil.copyfileobj(file, dest_file)
    finally:
            dest_file.close()
            os.chmod(pathfilename, 0600)
    return filename

# -----------------------------------------------------------------------------
def retrieve_file(filename, path=None):
    path = os.path.join(current.request.folder, "uploads")
    return (filename, open(os.path.join(path, filename), 'rb'))

# -----------------------------------------------------------------------------
class CallbackModule(object):

    """
    logs playbook results, per deployment in eden/yaml
    """
    def __init__(self, filename):
        self.filename = filename

    def on_any(self, *args, **kwargs):
        pass

    def on_failed(self, host, res, ignore_errors=False):
        setup_log(self.filename, 'FAILED', res)

    def on_ok(self, host, res):
        setup_log(self.filename, 'OK', res)

    def on_error(self, host, msg):
        setup_log(self.filename, 'ERROR', msg)

    def on_skipped(self, host, item=None):
        setup_log(self.filename, 'SKIPPED', '...')

    def on_unreachable(self, host, res):
        setup_log(self.filename, 'UNREACHABLE', res)

    def on_no_hosts(self):
        pass

    def on_async_poll(self, host, res, jid, clock):
        setup_log(self.filename, 'DEBUG', host, res, jid, clock)

    def on_async_ok(self, host, res, jid):
        setup_log(self.filename, 'DEBUG', host, res, jid)

    def on_async_failed(self, host, res, jid):
        setup_log(self.filename, 'ASYNC_FAILED', res)

    def on_start(self):
        setup_log(self.filename, 'DEBUG', 'on_start')

    def on_notify(self, host, handler):
        setup_log(self.filename, 'DEBUG', host)

    def on_no_hosts_matched(self):
        setup_log(self.filename, 'DEBUG', 'no_hosts_matched')

    def on_no_hosts_remaining(self):
        setup_log(self.filename, 'DEBUG', 'no_hosts_remaining')

    def on_task_start(self, name, is_conditional):
        setup_log(self.filename, 'DEBUG', 'Starting %s' % name)

    def on_vars_prompt(self, varname, private=True, prompt=None,
                                encrypt=None, confirm=False, salt_size=None,
                                salt=None, default=None):
        pass

    def on_setup(self):
        setup_log(self.filename, 'DEBUG', 'on_setup')

    def on_import_for_host(self, host, imported_file):
        setup_log(self.filename, 'IMPORTED', imported_file)

    def on_not_import_for_host(self, host, missing_file):
        setup_log(self.filename, 'NOTIMPORTED', missing_file)

    def on_play_start(self, pattern):
        setup_log(self.filename, 'play_start', pattern)

    def on_stats(self, stats):
        setup_log(self.filename, 'DEBUG', stats)

# -----------------------------------------------------------------------------
def setup_rheader(r, tabs=[]):
    """ Resource component page header """

    if r.representation == "html":

        T = current.T

        tabs = [(T("Deployment Details"), None),
                (T("Servers"), "server"),
                (T("Instances"), "instance"),
                ]

        rheader_tabs = s3_rheader_tabs(r, tabs)

        rheader = DIV(rheader_tabs)

        return rheader

# -----------------------------------------------------------------------------
def setup_management_exists(_type, _id, deployment_id):
    """ Returns true/false depending on whether a management task
        exists for an instance
    """

    db = current.db
    ttable = current.s3db.scheduler_task
    args = '["%s", "%s", "%s"]' % (_type, _id, deployment_id)
    query = ((ttable.function_name == "setup_management") & \
             (ttable.args == args) & \
             (ttable.status.belongs(["RUNNING", "QUEUED", "ASSIGNED"])))
    exists = db(query).select(ttable.id,
                              limitby = (0, 1)).first()

    if exists:
        return True

    return False

# -----------------------------------------------------------------------------
class setup_UpgradeMethod(S3Method):

    def apply_method(self, r, **attr):

        s3db = current.s3db
        db = current.db
        T = current.T
        response = current.response

        record = r.record

        dtable = s3db.setup_deploy
        stable = s3db.scheduler_task

        query = (dtable.host == record.host) & \
                (stable.status == "COMPLETED")
        machines = db(query).select(
                                    dtable.id.with_alias("deployment"),
                                    dtable.type.with_alias("type"),
                                    join = [
                                            stable.on(dtable.scheduler_id == stable.id)
                                            ],
                                    distinct = True
                                )

        machine_ids = [machine.deployment for machine in machines]

        validate = s3db.setup_host_validator(machine_ids)

        if r.http == "GET":

            if record.last_refreshed is None:
                redirect(URL(c="setup", f="refresh", args=record.id))

            # Data table
            resource = s3db.resource("setup_packages")

            totalrows = resource.count()
            list_fields = ["id",
                           "name",
                           "cv",
                           "av",
                           ]

            package_filter = (s3db.setup_packages.deployment == record.id) & \
                             (s3db.setup_packages.cv != s3db.setup_packages.av)

            resource.add_filter(package_filter)

            data = resource.select(list_fields,
                                   limit = totalrows,
                                   )

            dt = S3DataTable(data["rfields"], data["rows"])
            dt_id = "datatable"

            if validate is not None:
                dt_bulk_actions = None
                appname = current.request.application
                current.response.s3.scripts.append("/%s/static/scripts/S3/s3.setup.js" % appname)
            else:
                dt_bulk_actions = [(T("Upgrade"), "upgrade")]

            items = dt.html(totalrows,
                            totalrows,
                            dt_pagination = "false",
                            dt_bulk_actions = dt_bulk_actions,
                            )

            output = dict(items=items)
            response.view = "list.html"

        elif r.http == "POST":

            if validate is not None:
                current.session.error = validate
                redirect(URL(c="setup", f="%s_deploy" % record.type, args=[record.id, "upgrade"]))

            post_vars =  r.post_vars

            ptable = s3db.setup_packages
            selected = post_vars.selected
            if selected:
                selected = selected.split(",")
            else:
                selected = []

            # query = ptable.id.belongs(selected)
            # packages = db(query).select()

            query = FS("id").belongs(selected)
            presource = s3db.resource("setup_packages", filter=query)
            packages = presource.select(["name", "type"], as_rows=True)

            system_packages = []
            pip_packages = []
            git_packages = []

            for package in packages:
                if package.type == "os":
                    system_packages.append(package.name)
                elif package.type == "pip":
                    pip_packages.append(package.name)
                elif package.type == "git":
                    if package.name == "web2py":
                        git_packages.append({name: package.name, chdir: "/home/%s" % record.type})


            directory = os.path.join(current.request.folder, "yaml")
            name = "upgrade_%d" % int(time.time())
            file_path = os.path.join(directory, "%s.yml" % name)

            roles_path = "../private/playbook/roles/"

            upgrade = [
                {
                    "hosts": record.host,
                    "sudo": True,
                    "vars": {
                        "system_packages": system_packages,
                        "pip_packages": pip_packages,
                        "git_packages": git_packages,
                    },
                    "roles": [
                        "%supgrades" % roles_path,
                    ]
                }
            ]

            if record.type == "remote":
                upgrade[0]["remote_user"] = record.remote_user
            else:
                upgrade[0]["connection"] = "local"

            if not os.path.isdir(directory):
                os.mkdir(directory)
            with open(file_path, "w") as yaml_file:
                yaml_file.write(yaml.dump(upgrade, default_flow_style=False))

            if record.private_key:
                private_key = os.path.join(current.request.folder, "uploads", record.private_key)
            else:
                private_key = None

            only_tags = ['all']

            row = current.s3task.schedule_task(
                name,
                vars = {
                    "playbook": file_path,
                    "private_key": private_key,
                    "host": [record.host],
                    "only_tags": only_tags,
                },
                function_name = "deploy",
                repeats = 1,
                timeout = 3600,
                sync_output = 300
            )

            # Add record to setup_upgrade
            utable = s3db.setup_upgrade
            utable.insert(deployment=record.id, scheduler=row.id)

            current.session.flash = T("Upgrade Queued. Please wait while it is completed")
            redirect(URL(c="setup", f="%s_deploy" % record.type, args=[record.id, "upgrade"]))

        return output

# -----------------------------------------------------------------------------
def setup_refresh(id):

    T = current.T
    db = current.db
    s3db = current.s3db

    dtable = s3db.setup_deploy
    query = (dtable.id == id)

    record = db(query).select(dtable.id,
                              dtable.host,
                              dtable.type,
                              dtable.prepop,
                              dtable.remote_user,
                              dtable.private_key,
                              ).first()

    if not record:
        return {"success": False,
                "msg": T("Record Not Found"),
                "f": "index",
                "args": None
                }

    # Get machines with the same host as record
    ptable = s3db.setup_packages
    stable = s3db.scheduler_task
    utable = s3db.setup_upgrade

    query = (dtable.host == record.host) & \
            (stable.status == "COMPLETED")
    machines = db(query).select(
                                dtable.id.with_alias("deployment"),
                                dtable.type.with_alias("type"),
                                join = [
                                        stable.on(dtable.scheduler_id == stable.id)
                                        ],
                                distinct = True
                                )

    # Check if machines have a refresh running

    machine_ids = [machine.deployment for machine in machines]

    validate = s3db.setup_host_validator(machine_ids)
    if validate is not None:
        return {"success": False,
                "msg": validate,
                "f": str("%s_deploy" % record.type),
                "args": [record.id, "read"]
                }

    # set the refresh lock
    for machine in machines:
        db(dtable.id == machine.deployment).update(refresh_lock=1)

    # find new packages

    if record.type == "local":
        response = s3db.setup_getupgrades(record.host, record.prepop)
    else:
        response = s3db.setup_getupgrades(record.host,
                                          record.prepop,
                                          record.remote_user,
                                          record.private_key,
                                          )

    if response["dark"]:
        return {"success": False,
                "msg": T("Error contacting the server"),
                "f": str("%s_deploy" % record.type),
                "args": [record.id, "upgrade"]
                }

    # Call ansible runner

    # get a list of current packages
    packages = db(ptable.deployment == record.id).select(ptable.name)

    old_set = set()
    for package in packages:
        old_set.add(package.name)

    new_set = set()
    fetched_packages = response["contacted"][record.host]["packages"]

    for package in fetched_packages:
        new_set.add(package["name"])

    new_packages = new_set.difference(old_set)
    upgrade_packages = new_set.intersection(old_set)
    uptodate_packages = old_set.difference(new_set)

    for package in fetched_packages:
        if package["name"] in new_packages:
            for machine in machines:
                if package["name"] == "web2py" and machine.deployment != record.id:
                    continue
                ptable.insert(name = package["name"],
                              cv = package["cv"],
                              av = package["av"],
                              type = package["type"],
                              deployment = machine.deployment,
                              )
        elif package["name"] in upgrade_packages:
            for machine in machines:
                if package["name"] == "web2py" and machine.deployment != record.id:
                    continue
                query = (ptable.name == package["name"]) & \
                        (ptable.deployment == machine.deployment)
                db(query).update(av=package["av"])

    for package in uptodate_packages:
        for machine in machines:
            if package == "web2py" and machine.deployment != record.id:
                continue
            query = (ptable.name == package) & \
                    (ptable.deployment == machine.deployment)
            row = db(query).select().first()
            row.av = row.cv
            row.update_record()

    # release the refresh lock
    for machine in machines:
        db(dtable.id == machine.deployment).update(refresh_lock=0)

    # update last refreshed
    import datetime
    record.update_record(last_refreshed=datetime.datetime.now())

    return {"success": True,
            "msg": T("Refreshed Packages"),
            "f": str("%s_deploy" % record.type),
            "args": [record.id, "upgrade"]
            }

# -----------------------------------------------------------------------------
def setup_host_validator(machine_ids):
    """ Helper Function that checks whether it's safe to allow
        upgrade/deployments/refresh packages on given instances
    """

    s3db = current.s3db
    db = current.db
    T = current.T
    dtable = s3db.setup_deploy
    ptable = s3db.setup_packages
    stable = s3db.scheduler_task
    utable = s3db.setup_upgrade

    if len(machine_ids) > 1:
        query = (dtable.id.belongs(machine_ids)) & \
                (dtable.refresh_lock != 0)
    else:
        query = (dtable.id == machine_ids[0]) & \
                (dtable.refresh_lock != 0)

    rows = db(query).select(dtable.id)

    if rows:
        return T("A refresh is in progress. Please wait for it to finish")

    # or an upgrade in process

    if len(machine_ids) > 1:
        query = (utable.deployment.belongs(machine_ids)) & \
               ((stable.status != "COMPLETED") & (stable.status != "FAILED"))
    else:
        query = (utable.deployment == machine_ids[0]) & \
               ((stable.status != "COMPLETED") & (stable.status != "FAILED"))

    rows = db(query).select(utable.deployment,
                            join=stable.on(utable.scheduler == stable.id)
                            )

    if rows:
        return T("An upgrade is in progress. Please wait for it to finish")

    # or even a deployment in process

    if len(machine_ids) > 1:
        query = (dtable.id.belongs(machine_ids)) & \
               ((stable.status != "COMPLETED") & (stable.status != "FAILED"))
    else:
        query = (dtable.id == machine_ids[0]) & \
               ((stable.status != "COMPLETED") & (stable.status != "FAILED"))

    rows = db(query).select(dtable.id,
                            join = stable.on(utable.scheduler == stable.id)
                            )

    if rows:
        return T("A deployment is in progress. Please wait for it to finish")

# -----------------------------------------------------------------------------
def setup_getupgrades(host, web2py_path, remote_user=None, private_key=None):
    import ansible.runner

    module_path = os.path.join(current.request.folder, "private", "playbook", "library")
    if private_key:
        private_key = os.path.join(current.request.folder, "uploads", private_key)

    inventory = ansible.inventory.Inventory([host])

    if private_key and remote_user:
        runner = ansible.runner.Runner(module_name = "upgrade",
                                       module_path = module_path,
                                       module_args = "web2py_path=/home/%s" % web2py_path,
                                       remote_user = remote_user,
                                       private_key_file = private_key,
                                       pattern = host,
                                       inventory = inventory,
                                       sudo = True,
                                       )

    else:
        runner = ansible.runner.Runner(module_name = "upgrade",
                                       module_path = module_path,
                                       module_args = "web2py_path=/home/%s" % web2py_path,
                                       pattern = host,
                                       inventory = inventory,
                                       sudo = True,
                                       )

    response = runner.run()

    return response

def setup_upgrade_status(_id):

    s3db = current.s3db
    db = current.db
    T = current.T

    utable = s3db.setup_upgrade
    stable = s3db.scheduler_task
    query = (utable.deployment == _id)

    row = db(query).select(stable.status,
                           join = utable.on(stable.id == utable.scheduler)
                           ).last()

    if row.status == "COMPLETED":
        return T("Upgrade Completed! Refreshing the page in 5 seconds")
