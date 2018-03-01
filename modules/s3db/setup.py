# -*- coding: utf-8 -*-

""" Sahana Eden Setup Model:
        Assists with Installation of a Deployment
        tbc: Assists with Configuration of a Deployment

@copyright: 2015-2018 (c) Sahana Software Foundation
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
__all__ = ("S3SetupModel",
           "setup_run_playbook",
           "setup_rheader",
           )

import json
import os
import random
import string
import time

from collections import namedtuple

from ..s3 import *
from gluon import *

TIME_FORMAT = "%b %d %Y %H:%M:%S"
MSG_FORMAT = "%(now)s - %(category)s - %(data)s\n\n"

WEB_SERVERS = {1: "apache",
               2: "cherokee",
               }

DB_SERVERS = {1: "mysql",
              2: "postgresql",
              #3: "sqlite",
              }

INSTANCE_TYPES = {1: "prod",
                  2: "test",
                  3: "demo",
                  }

# =============================================================================
class S3SetupModel(S3Model):

    names = ("setup_deployment",
             "setup_server",
             "setup_instance",
             )

    def model(self):

        T = current.T

        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        configure = self.configure
        path = os.path.join(current.request.folder, "modules", "templates")

        # ---------------------------------------------------------------------
        # Deployments
        #
        tablename = "setup_deployment"
        define_table(tablename,
                     Field("name",
                           default = "default",
                           label = T("Name"),
                           requires = IS_NOT_EMPTY(),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Name"),
                                                           T("The name by which you wish to refer to the deployment")
                                                           )
                                         ),
                           ),
                     # @ToDo: Add ability to get a specific hash/tag
                     Field("repo_url",
                           default = "https://github.com/sahana/eden",
                           label = T("Eden Repository"),
                           requires = IS_URL(),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Eden Repository"),
                                                           T("If you wish to use your own Fork, then you can set this here")
                                                           )
                                         ),
                           ),
                     Field("country",
                           label = T("Country"),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET_LAZY(lambda: self.setup_get_countries(path),
                                                       zero = current.messages.SELECT_LOCATION,
                                                       )),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Country"),
                                                           T("Selecting your country means that the appropriate locale settings can be applied. If you need to support multiple countries then you may need to create a custom template.")
                                                           )
                                         ),
                           ),
                     Field("template", "list:string",
                           default = ["default"],
                           label = T("Template"),
                           requires = IS_IN_SET_LAZY(lambda: self.setup_get_templates(path),
                                                     multiple = True,
                                                     zero = None,
                                                     ),
                           ),
                     Field("webserver_type", "integer",
                           default = 2,
                           label = T("Web Server"),
                           represent = S3Represent(options = WEB_SERVERS),
                           requires = IS_IN_SET(WEB_SERVERS),
                           ),
                     Field("db_type", "integer",
                           default = 2,
                           label = T("Database"),
                           represent = S3Represent(options = DB_SERVERS),
                           requires = IS_IN_SET(DB_SERVERS),
                           ),
                     # Set automatically
                     Field("db_password", "password",
                           readable = False,
                           writable = False,
                           ),
                     Field("remote_user",
                           default = "admin",
                           label = T("Remote User"),
                           ),
                     Field("private_key", "upload",
                           label = T("Private Key"),
                           length = current.MAX_FILENAME_LENGTH,
                           requires = IS_EMPTY_OR(IS_UPLOAD_FILENAME()),
                           uploadfolder = os.path.join(current.request.folder, "uploads"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Private Key"),
                                                           T("if you wish to configure servers other than the one hosting the co-app then you need to provide a PEM-encoded SSH private key")
                                                           )
                                         ),
                           ),
                     #Field("secret_key",
                     #      label = T("AWS Secret Key"),
                     #      comment = DIV(_class="tooltip",
                     #                    _title="%s|%s" % (T("AWS Secret Key"),
                     #                                      T("If you wish to add additional servers on AWS then you need this")
                     #                                      )
                     #                    ),
                     #      ),
                     #Field("access_key",
                     #      label = T("AWS Access Key"),
                     #      comment = DIV(_class="tooltip",
                     #                    _title="%s|%s" % (T("AWS Access Key"),
                     #                                      T("If you wish to add additional servers on AWS then you need this")
                     #                                      )
                     #                    ),
                     #      ),
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
        crud_strings[tablename] = Storage(
            label_create = T("Create Deployment"),
            title_display = T("Deployment Details"),
            title_list =  T("Deployments"),
            title_update = T("Edit Deployment"),
            label_list_button =  T("List Deployments"),
            label_delete_button = T("Delete Deployment"),
            msg_record_created = T("Deployment added"),
            msg_record_modified = T("Deployment updated"),
            msg_record_deleted = T("Deployment deleted"),
            msg_list_empty = T("No Deployments currently registered"))

        configure(tablename,
                  #editable = False,
                  listadd = False,
                  create_onaccept = self.setup_deployment_create_onaccept,
                  create_next = URL(c="setup", f="deployment",
                                    args = ["[id]", "instance"],
                                    ),
                  list_fields = ["name",
                                 "country",
                                 "template",
                                 "webserver_type",
                                 "db_type",
                                 "remote_user",
                                 ],
                  )

        self.add_components(tablename,
                            setup_instance = "deployment_id",
                            setup_server = "deployment_id",
                            )

        # ---------------------------------------------------------------------
        # Servers
        #
        SERVER_ROLES = {1: "all",
                        2: "db",
                        3: "webserver",
                        4: "eden",
                        }

        tablename = "setup_server"
        define_table(tablename,
                     Field("deployment_id", "reference setup_deployment"),
                     Field("role", "integer",
                           default = 1,
                           label = T("Role"),
                           represent = S3Represent(options = SERVER_ROLES),
                           requires = IS_IN_SET(SERVER_ROLES),
                           ),
                     Field("host_ip", unique = True,
                           default = "127.0.0.1",
                           label = T("IP Address"),
                           requires = IS_IPV4(),
                           ),
                     #Field("hostname",
                     #      label = T("Hostname"),
                     #      requires = IS_NOT_EMPTY(),
                     #      ),
                     *s3_meta_fields()
                     )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Server"),
            title_display = T("Server Details"),
            title_list =  T("Servers"),
            title_update = T("Edit Server"),
            label_list_button =  T("List Servers"),
            label_delete_button = T("Delete Server"),
            msg_record_created = T("Server added"),
            msg_record_modified = T("Server updated"),
            msg_record_deleted = T("Server deleted"),
            msg_list_empty = T("No Servers currently registered"))

        # ---------------------------------------------------------------------
        # Instances
        #
        tablename = "setup_instance"
        define_table(tablename,
                     Field("deployment_id", "reference setup_deployment"),
                     Field("type", "integer",
                           default = 1,
                           label = T("Type"),
                           represent = S3Represent(options = INSTANCE_TYPES),
                           requires = IS_IN_SET(INSTANCE_TYPES)
                           ),
                     # @ToDo: Add support for SSL Certificates
                     Field("url",
                           label = T("URL"),
                           requires = IS_URL(),
                           represent = lambda opt: A(opt,
                                                     _href = opt,
                                                     _target="_blank",
                                                     ),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("URL"),
                                                           T("The Public URL which will be used to access the instance")
                                                           )
                                         ),
                           ),
                     Field("task_id", "reference scheduler_task",
                           label = T("Scheduled Task"),
                           represent = lambda opt: \
                            A(opt,
                              _href = URL(c="appadmin", f="update",
                                          args = ["db", "scheduler_task", opt]),
                              ) if opt else current.messages["NONE"],
                           writable = False,
                           ),
                     *s3_meta_fields()
                     )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Instance"),
            title_display = T("Instance Details"),
            title_list =  T("Instances"),
            title_update = T("Edit Instance"),
            label_list_button =  T("List Instances"),
            label_delete_button = T("Delete Instance"),
            msg_record_created = T("Instance added"),
            msg_record_modified = T("Instance updated"),
            msg_record_deleted = T("Instance deleted"),
            msg_list_empty = T("No Instances currently registered"))

        self.set_method("setup", "instance",
                        method = "deploy",
                        action = self.setup_instance_deploy,
                        )

        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def setup_deployment_create_onaccept(form):
        """
            New deployments:
                Assign a random DB password
                Configure localhost to have all tiers (for 1st deployment)
        """

        db = current.db
        s3db = current.s3db
        table = s3db.setup_deployment

        deployment_id = form.vars.id

        # Assign a random DB password
        chars = string.ascii_letters + string.digits + string.punctuation
        password = "".join(random.choice(chars) for _ in range(12))
        db(table.id == deployment_id).update(db_password = password)

        if db(table.deleted == False).count() < 2: 
            # Configure localhost to have all tiers (localhost & all tiers are defaults)
            server_id = s3db.setup_server.insert(deployment_id = deployment_id)

        # Configure a Production instance (needs Public URL so has to be done Inline)
        #instance_id = s3db.setup_instance.insert()

        current.session.information = current.T("Press 'Deploy' when you are ready")

    # -------------------------------------------------------------------------
    @staticmethod
    def setup_get_countries(path):
        """
            Return a List of Countries for which we have Locale settings defined

            @ToDo: Read the list of templates from the custom repo URL!
        """

        p = os.path
        basename = p.basename
        isdir = p.isdir
        join = p.join

        path = join(path, "locations")
        available_countries = [basename(c) for c in os.listdir(path) if isdir(join(path, c))]
        all_countries = current.gis.get_countries(key_type="code")
        countries = OrderedDict([(c, all_countries[c]) for c in all_countries if c in available_countries])

        return countries

    # -------------------------------------------------------------------------
    @staticmethod
    def setup_get_templates(path):
        """
            Return a List of Templates for the user to select between

            @ToDo: Read the list of templates from the custom repo URL!
        """

        p = os.path
        basename = p.basename
        join = p.join
        isdir = p.isdir
        listdir = os.listdir
        templates = [basename(t) for t in listdir(path) \
                        if basename(t) not in ("historic",
                                               "locations",
                                               "mobile",
                                               "skeleton",
                                               "skeletontheme",
                                               "__init__.py",
                                               "__init__.pyc",
                                               "000_config.py",
                                               )
                     ]
        subtemplates = []
        sappend = subtemplates.append
        for i in range(0, len(templates)):
            template = templates[i]
            tpath = join(path, template)
            for d in listdir(tpath):
                if isdir(join(tpath, d)):
                    for f in listdir(join(tpath, d)):
                        if f == "config.py":
                            sappend("%s.%s" % (template, d))
                            continue

        templates += subtemplates
        templates.sort()
        return templates

    # -------------------------------------------------------------------------
    def setup_instance_deploy(self, r, **attr):

        db = current.db
        s3db = current.s3db

        # Get Instance details
        instance_id = r.id
        itable = s3db.setup_instance
        instance = db(itable.id == instance_id).select(itable.deployment_id,
                                                       itable.type,
                                                       itable.url,
                                                       limitby = (0, 1)
                                                       ).first()

        sitename = instance.url
        if "://" in sitename:
            sitename = sitename.split("://", 1)[1]

        deployment_id = instance.deployment_id

        # Get Server(s) details
        stable = s3db.setup_server
        query = (stable.deployment_id == deployment_id)
        rows = db(query).select(stable.role,
                                stable.host_ip,
                                )

        hosts = []
        for row in rows:
            hosts.append((row.role, row.host_ip))

        # Get Deployment details
        dtable = s3db.setup_deployment
        deployment = db(dtable.id == deployment_id).select(dtable.webserver_type,
                                                           dtable.db_type,
                                                           dtable.db_password,
                                                           dtable.template,
                                                           dtable.private_key,
                                                           dtable.remote_user,
                                                           limitby=(0, 1)
                                                           ).first()

        # Write Playbook
        task_id = self.setup_write_playbook(hosts,
                                            deployment.db_password,
                                            WEB_SERVERS[deployment.webserver_type],
                                            DB_SERVERS[deployment.db_type],
                                            INSTANCE_TYPES[instance.type],
                                            deployment.template,
                                            sitename,
                                            deployment.private_key,
                                            deployment.remote_user,
                                            )

        # Link scheduled task to current record
        # = allows us to monitor deployment progress
        db(itable.id == instance_id).update(task_id = task_id)

        current.session.confirmation = current.T("Deployment initiated")
        redirect(URL(c="setup", f="deployment",
                     args = [deployment_id, "instance"],
                     ))

    # -------------------------------------------------------------------------
    @staticmethod
    def setup_write_playbook(hosts,
                             password,
                             web_server,
                             database_type,
                             instance_type,
                             template = "default",
                             sitename = None,
                             private_key = None,
                             remote_user = None,
                             ):

        try:
            import yaml
        except ImportError:
            error = "PyYAML module needed for Setup"
            current.log.error(error)
            current.response.error = error
            return

        folder = current.request.folder

        roles_path = "../../private/eden_deploy/roles/" # relative to playbook_path
        playbook_path = os.path.join(folder, "uploads", "playbook")
        if not os.path.isdir(playbook_path):
            os.mkdir(playbook_path)

        if len(hosts) == 1:
            deployment = [
                {
                    "hosts": hosts[0][1],
                    "remote_user": remote_user,
                    "vars": {
                        "password": password,
                        "template": template,
                        "web_server": web_server,
                        "type": instance_type,
                        "sitename": sitename,
                        "eden_ip": hosts[0][1],
                        "db_ip": hosts[0][1],
                        "db_type": database_type
                    },
                    "roles": [
                        "%scommon" % roles_path,
                        "%s%s" % (roles_path, web_server),
                        "%suwsgi" % roles_path,
                        "%s%s" % (roles_path, database_type),
                        "%sconfigure" % roles_path,
                    ]
                }
            ]
        else:
            deployment = [
                {
                    "hosts": hosts[0][1],
                    "remote_user": remote_user,
                    "vars": {
                        "password": password,
                        "type": instance_type
                    },
                    "roles": [
                        "%s%s" % (roles_path, database_type),
                    ]
                },
                {
                    "hosts": hosts[2][1],
                    "remote_user": remote_user,
                    "vars": {
                        "db_ip": hosts[0][1],
                        "db_type": database_type,
                        "password": password,
                        "sitename": sitename,
                        "template": template,
                        "type": instance_type,
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
                    "remote_user": remote_user,
                    "vars": {
                        "eden_ip": hosts[2][1],
                        "type": instance_type
                    },
                    "roles": [
                        "%s%s" % (roles_path, web_server),
                    ]
                }
            ]

        name = "deployment_%d" % int(time.time())
        file_path = os.path.join(playbook_path, "%s.yml" % name)

        with open(file_path, "w") as yaml_file:
            yaml_file.write(yaml.dump(deployment, default_flow_style=False))

        task_vars = {"playbook": file_path,
                     "hosts": [host[1] for host in hosts],
                     "tags": [instance_type],
                     }
        if private_key:
            task_vars["private_key"] = os.path.join(folder, "uploads", private_key)

        task_id = current.s3task.schedule_task(name,
                                               vars = task_vars,
                                               function_name = "deploy",
                                               repeats = 1,
                                               timeout = 3600,
                                               sync_output = 300
                                               )

        return task_id

# =============================================================================
def setup_run_playbook(playbook, hosts, tags, private_key=None):
    """
        Run an Ansible Playbook & return the result
        - designed to be run from the 'deploy' Task

        http://docs.ansible.com/ansible/latest/dev_guide/developing_api.html

        @ToDo: Make use of Tags (needed once adding Test/Demo sites)
    """

    try:
        from ansible.parsing.dataloader import DataLoader
        from ansible.vars.manager import VariableManager
        from ansible.inventory.manager import InventoryManager
        from ansible.playbook.play import Play
        from ansible.executor.task_queue_manager import TaskQueueManager
        #from ansible.plugins.callback import CallbackBase
    except ImportError:
        error = "ansible module needed for Setup"
        current.log.error(error)
        return error

    Options = namedtuple("Options", ["connection", "forks", "become", "become_method", "become_user", "check", "diff"])

    # Initialize needed objects
    loader = DataLoader()
    options = Options(connection="local", forks=100, become=None,
                      become_method=None, become_user=None, check=False,
                      diff=False)
    passwords = dict(#vault_pass = "secret",
                     private_key_file = private_key, # @ToDo: Needs testing
                     )

    # Instantiate our ResultCallback for handling results as they come in
    #results_callback = ResultCallback()

    # Create Inventory and pass to Var manager
    inventory = InventoryManager(loader=loader, sources=hosts)
    variable_manager = VariableManager(loader=loader, inventory=inventory)

    # Load Playbook from file
    play_source = loader.load_from_file(playbook)
    play = Play().load(play_source, variable_manager=variable_manager, loader=loader)

    # Actually run it
    tqm = None
    result = None
    try:
        tqm = TaskQueueManager(inventory = inventory,
                               variable_manager = variable_manager,
                               loader = loader,
                               options = options,
                               passwords = passwords,
                               #stdout_callback=results_callback,
                               )
        result = tqm.run(play)
    finally:
        if tqm is not None:
            tqm.cleanup()

    return result

# =============================================================================
def setup_rheader(r, tabs=None):
    """ Resource component page header """

    if r.representation == "html" and r.id:

        T = current.T

        tabs = [(T("Deployment Details"), None),
                (T("Servers"), "server"),
                (T("Instances"), "instance"),
                ]

        rheader_tabs = s3_rheader_tabs(r, tabs)

        rheader = DIV(rheader_tabs)

        return rheader

# END =========================================================================
