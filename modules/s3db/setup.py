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

from ..s3 import *
from gluon import *

TIME_FORMAT = "%b %d %Y %H:%M:%S"
MSG_FORMAT = "%(now)s - %(category)s - %(data)s\n\n"

WEB_SERVERS = {#1: "apache",
               2: "cherokee",
               }

DB_SERVERS = {#1: "mysql",
              2: "postgresql",
              ##3: "sqlite",
              }

INSTANCE_TYPES = {1: "prod",
                  #2: "test",
                  #3: "demo",
                  }

# =============================================================================
class S3SetupModel(S3Model):

    names = ("setup_deployment",
             "setup_server",
             "setup_instance",
             "setup_setting",
             )

    def model(self):

        T = current.T
        db = current.db

        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        set_method = self.set_method

        folder = current.request.folder
        path_join = os.path.join
        template_path = path_join(folder, "modules", "templates")

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
                     Field("sender",
                           label = T("Email Sender"),
                           requires = IS_EMPTY_OR(
                                        IS_EMAIL()),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Email Sender"),
                                                           T("The Address which you want Outbound Email to be From. Not setting this means that Outbound Email is Disabled.")
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
                                        IS_IN_SET_LAZY(lambda: self.setup_get_countries(template_path),
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
                           requires = IS_IN_SET_LAZY(lambda: self.setup_get_templates(template_path),
                                                     multiple = True,
                                                     zero = None,
                                                     ),
                           ),
                     Field("webserver_type", "integer",
                           default = 2,
                           label = T("Web Server"),
                           represent = S3Represent(options = WEB_SERVERS),
                           requires = IS_IN_SET(WEB_SERVERS),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Web Server"),
                                                           T("Currently only Cherokee is supported by this tool, although Apache should be possible with a little work.")
                                                           )
                                         ),
                           ),
                     Field("db_type", "integer",
                           default = 2,
                           label = T("Database"),
                           represent = S3Represent(options = DB_SERVERS),
                           requires = IS_IN_SET(DB_SERVERS),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Database"),
                                                           T("Currently only PostgreSQL is supported by this tool, although MySQL should be possible with a little work.")
                                                           )
                                         ),
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
                           uploadfolder = path_join(folder, "uploads"),
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
                     #Field("refresh_lock", "integer",
                     #      default = 0,
                     #      readable = False,
                     #      writable = False,
                     #      ),
                     #Field("last_refreshed", "datetime",
                     #      readable = False,
                     #      writable = False,
                     #      ),
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
                            setup_setting = "deployment_id",
                            )

        represent = S3Represent(lookup=tablename)

        deployment_id = S3ReusableField("deployment_id", "reference %s" % tablename,
                                        label = T("Deployment"),
                                        ondelete = "CASCADE",
                                        represent = represent,
                                        requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "setup_deployment.id",
                                                              represent,
                                                              sort=True
                                                              )),
                                        sortby = "name",
                                        )

        # ---------------------------------------------------------------------
        # Servers
        #
        # @ToDo: Should be able to over-ride deployment-default remote_user &
        #        private_key
        #
        SERVER_ROLES = {1: "all",
                        2: "db",
                        3: "webserver",
                        4: "eden",
                        }

        tablename = "setup_server"
        define_table(tablename,
                     deployment_id(),
                     Field("role", "integer",
                           default = 1,
                           label = T("Role"),
                           represent = S3Represent(options = SERVER_ROLES),
                           requires = IS_IN_SET(SERVER_ROLES),
                           writable = False,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Role"),
                                                           T("Currently only 'all' is supported by this tool, although others should be possible with a little work.")
                                                           )
                                         ),
                           ),
                     Field("host_ip", unique = True,
                           default = "127.0.0.1",
                           label = T("IP Address"),
                           requires = IS_IPV4(),
                           writable = False,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("IP Address"),
                                                           T("Currently only 127.0.0.1 is supported by this tool, although others should be possible with a little work.")
                                                           )
                                         ),
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
                     deployment_id(),
                     Field("type", "integer",
                           default = 1,
                           label = T("Type"),
                           represent = S3Represent(options = INSTANCE_TYPES),
                           requires = IS_IN_SET(INSTANCE_TYPES),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Type"),
                                                           T("Currently only Production is supported by this tool, although Demo/Test should be possible with a little work.")
                                                           )
                                         ),
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

        set_method("setup", "deployment",
                   component_name = "instance",
                   method = "deploy",
                   action = self.setup_instance_deploy,
                   )

        set_method("setup", "deployment",
                   component_name = "instance",
                   method = "settings",
                   action = self.setup_instance_settings,
                   )

        represent = S3Represent(lookup=tablename, fields=["type"])

        instance_id = S3ReusableField("instance_id", "reference %s" % tablename,
                                      label = T("Instance"),
                                      ondelete = "CASCADE",
                                      represent = represent,
                                      requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "setup_instance.id",
                                                              represent,
                                                              sort=True
                                                              )),
                                      sortby = "name",
                                      )

        # ---------------------------------------------------------------------
        # Settings in models/000_config.py
        #
        tablename = "setup_setting"
        define_table(tablename,
                     deployment_id(),
                     instance_id(),
                     Field("setting",
                           label = T("Setting"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("current_value",
                           label = T("Current Value"),
                           writable = False,
                           ),
                     Field("new_value",
                           label = T("New Value"),
                           ),
                     *s3_meta_fields()
                     )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Setting"),
            title_display = T("Setting Details"),
            title_list =  T("Settings"),
            title_update = T("Edit Setting"),
            label_list_button =  T("List Settings"),
            label_delete_button = T("Delete Setting"),
            msg_record_created = T("Setting added"),
            msg_record_modified = T("Setting updated"),
            msg_record_deleted = T("Setting deleted"),
            msg_list_empty = T("No Settings currently registered"))

        set_method("setup", "deployment",
                   component_name = "setting",
                   method = "apply",
                   action = self.setup_setting_apply,
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
        # Ensure that " isn't included otherwise we get a syntax error in 000_config.py
        chars = chars.replace('"', "")
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
        """
            Custom S3Method to Deploy an Instance
        """

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
            protocol, sitename = sitename.split("://", 1)
        else:
            protocol = "http"

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
                                                           dtable.sender,
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
                                            deployment.sender,
                                            protocol,
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
                             db_password,
                             web_server,
                             db_type,
                             instance_type,
                             template = "default",
                             sender = None,
                             protocol = "http",
                             sitename = None,
                             private_key = None,
                             remote_user = None,
                             ):
        """
            Write an Ansible Playbook file
            - & Schedule a Task to run it
        """

        try:
            import yaml
        except ImportError:
            error = "PyYAML module needed for Setup"
            current.log.error(error)
            current.response.error = error
            return

        folder = current.request.folder

        playbook_path = os.path.join(folder, "uploads", "playbook")
        if not os.path.isdir(playbook_path):
            os.mkdir(playbook_path)

        roles_path = os.path.join(folder, "private", "eden_deploy", "roles")

        hostname = sitename.split(".", 1)[0]

        if len(hosts) == 1:
            host = hosts[0][1]
            deployment = [
                {
                    "hosts": host,
                    "connection": "local", # @ToDo: Don't assume this
                    "remote_user": remote_user,
                    "vars": {
                        "password": db_password,
                        "template": template,
                        "sender": sender,
                        "web_server": web_server,
                        "type": instance_type,
                        "hostname": hostname,
                        "sitename": sitename,
                        "protocol": protocol,
                        "eden_ip": host,
                        "db_ip": host,
                        "db_type": db_type
                    },
                    "roles": [{ "role": "%s/common" % roles_path },
                              { "role": "%s/%s" % (roles_path, web_server) },
                              { "role": "%s/uwsgi" % roles_path },
                              { "role": "%s/%s" % (roles_path, db_type) },
                              { "role": "%s/configure" % roles_path },
                              ]
                }
            ]
        else:
            deployment = [
                {
                    "hosts": hosts[0][1],
                    "remote_user": remote_user,
                    "vars": {
                        "password": db_password,
                        "type": instance_type
                    },
                    "roles": [{ "role": "%s/%s" % (roles_path, db_type) },
                              ]
                },
                {
                    "hosts": hosts[2][1],
                    "remote_user": remote_user,
                    "vars": {
                        "db_ip": hosts[0][1],
                        "db_type": db_type,
                        "password": db_password,
                        "hostname": hostname,
                        "sitename": sitename,
                        "protocol": protocol,
                        "template": template,
                        "sender": sender,
                        "type": instance_type,
                        "web_server": web_server,
                    },
                    "roles": [{ "role": "%s/common" % roles_path },
                              { "role": "%s/uwsgi" % roles_path },
                              { "role": "%s/configure" % roles_path },
                              ]
                },
                {
                    "hosts": hosts[1][1],
                    "remote_user": remote_user,
                    "vars": {
                        "protocol": protocol,
                        "eden_ip": hosts[2][1],
                        "type": instance_type
                    },
                    "roles": [{ "role": "%s/%s" % (roles_path, web_server) },
                              ]
                }
            ]

        name = "deployment_%d" % int(time.time())
        file_path = os.path.join(playbook_path, "%s.yml" % name)

        with open(file_path, "w") as yaml_file:
            yaml_file.write(yaml.dump(deployment, default_flow_style=False))

        task_vars = {"playbook": file_path,
                     "hosts": [host[1] for host in hosts],
                     }
        if instance_type != "prod":
            # only_tags
            task_vars["tags"] = [instance_type]
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

    # -------------------------------------------------------------------------
    @staticmethod
    def setup_instance_settings_read(instance_id, deployment_id):
        """
            Read the Settings for an instance from models/000_config.py
            - called onaccept from instance creation
            - called by interactive method to read
        """

        from gluon.cfs import getcfs
        from gluon.compileapp import build_environment
        from gluon.restricted import restricted

        # Read current settings from file
        request = current.request
        model = "%s/models/000_config.py" % request.folder
        code = getcfs(model, model, None)
        environment = build_environment(request, current.response, current.session)
        environment["settings"] = Storage2()
        restricted(code, environment, layer=model)
        nested_settings = environment["settings"]

        # Flatten settings
        file_settings = {}
        for section in nested_settings:
            subsection = nested_settings[section]
            for setting in subsection:
                file_settings["%s.%s" % (section, setting)] = subsection[setting]

        # Read current Database Settings
        db = current.db
        stable = current.s3db.setup_setting
        id_field = stable.id
        query = (stable.instance_id == instance_id) & \
                (stable.deleted == False)
        db_settings = db(query).select(id_field,
                                       stable.setting,
                                       #stable.current_value,
                                       stable.new_value,
                                       ).as_dict(key = "setting")
        db_get = db_settings.get

        # Ensure that database looks like file
        checked_settings = []
        cappend = checked_settings.append
        for setting in file_settings:
            s = db_get(setting)
            if s:
                # We update even if not changed so as to update modified_on
                db(id_field == s["id"]).update(current_value = s["current_value"])
            else:
                stable.insert(deployment_id = deployment_id,
                              instance_id = instance_id,
                              setting = setting,
                              current_value = file_settings[setting],
                              )
            cappend(setting)

        # Handle db_settings not in file_settings
        for setting in db_settings:
            if setting in checked_settings:
                continue
            s = db_get(setting)
            if s["new_value"] is not None:
                db(id_field == s["id"]).update(current_value = None)
            else:
                db(id_field == s["id"]).update(deleted = True)

    # -------------------------------------------------------------------------
    def setup_instance_settings(self, r, **attr):
        """
            Custom interactive S3Method to Read the Settings for an instance
            from models/000_config.py
        """

        deployment_id = r.id
        self.setup_instance_settings_read(r.component_id, deployment_id)

        current.session.confirmation = current.T("Settings Read")

        redirect(URL(c="setup", f="deployment",
                     args = [deployment_id, "setting"]),
                     )

    # -------------------------------------------------------------------------
    @staticmethod
    def setup_setting_apply(r, **attr):
        """
            Custom interactive S3Method to Apply a Setting to an instance
            via models/000_config.py
        """

        db = current.db
        s3db = current.s3db

        deployment_id = r.id
        setting_id = r.component_id

        stable = s3db.setup_setting
        setting = db(stable.id == setting_id).select(stable.id,
                                                     stable.instance_id,
                                                     stable.setting,
                                                     stable.new_value,
                                                     limitby = (0, 1)
                                                     ).first()
        new_value = setting.new_value

        dtable = s3db.setup_deployment
        itable = s3db.setup_instance
        query = (itable.id == setting.instance_id) & \
                (dtable.id == itable.deployment_id)
        deployment = db(query).select(dtable.remote_user,
                                      dtable.private_key,
                                      itable.type,
                                      limitby = (0, 1)
                                      ).first()
        remote_user = deployment["setup_deployment.remote_user"]
        private_key = deployment["setup_deployment.private_key"]
        instance_type = deployment["setup_instance.type"]

        # Lookup Server IP
        # @ToDo: Support multiple Eden servers used as Load-balancers
        svtable = s3db.setup_server
        query = (svtable.deployment_id == deployment_id) & \
                (svtable.role.belongs((1, 4)))
        server = db(query).select(svtable.host_ip,
                                  limitby = (0, 1)
                                  ).first()
        host = server.host_ip

        # Build Ansible Playbook to apply the setting
        try:
            import yaml
        except ImportError:
            error = "PyYAML module needed for Setup"
            current.log.error(error)
            current.response.error = error
            return

        folder = current.request.folder

        playbook_path = os.path.join(folder, "uploads", "playbook")
        if not os.path.isdir(playbook_path):
            os.mkdir(playbook_path)

        #roles_path = os.path.join(folder, "private", "eden_deploy", "roles")

        the_setting = setting.setting
        if new_value is True or new_value is False:
            new_line = "settings.%s = %s" % (the_setting, new_value)
        else:
            # @ToDo: Handle lists/dicts (load into JSONS3?)
            new_line = 'settings.%s = "%s"' % (the_setting, new_value)

        playbook = [{"hosts": host,
                     "connection": "local", # @ToDo: Don't assume this
                     "remote_user": remote_user,
                     "tasks": [{"name": "Edit 000_config.py",
                                "lineinfile": {"dest": "/home/%s/applications/eden/models/000_config.py" % instance_type,
                                               "regexp": "^settings.%s =" % the_setting,
                                               "line": new_line,
                                               "state": "present",
                                               },
                                },
                               # @ToDo: handle case where WebServer is on a different host
                               {"name": "Compile & Restart WebServer",
                                #"command": "sudo -H -u web2py python web2py.py -S eden -M -R applications/eden/static/scripts/tools/compile.py",
                                #"args": {"chdir": "/home/%s" % instance_type,
                                #         },
                                "command": "/usr/local/bin/compile",
                                },
                               ]
                     },
                    ]

        name = "apply_%d" % int(time.time())
        file_path = os.path.join(playbook_path, "%s.yml" % name)

        with open(file_path, "w") as yaml_file:
            yaml_file.write(yaml.dump(playbook, default_flow_style=False))

        # Run the Playbook
        task_vars = {"playbook": file_path,
                     "hosts": [host],
                     }
        #if instance_type != "prod":
        #    # only_tags
        #    task_vars["tags"] = [instance_type]
        if private_key:
            task_vars["private_key"] = os.path.join(folder, "uploads", private_key)

        current.s3task.async("deploy",
                             vars = task_vars,
                             timeout = 3600,
                             )

        # Update the DB to show that the setting has been applied
        # @ToDo: Do this as a callback from the async task
        setting.update_record(current_value = new_value,
                              new_value = None,
                              )

        current.session.confirmation = current.T("Setting Applied")

        redirect(URL(c="setup", f="deployment",
                     args = [deployment_id, "setting"]),
                     )

# =============================================================================
def setup_run_playbook(playbook, hosts, tags=None, private_key=None):
    """
        Run an Ansible Playbook & return the result
        - designed to be run as a Scheduled Task
            - 'deploy' a deployment
            - 'apply' a setting

        http://docs.ansible.com/ansible/latest/dev_guide/developing_api.html
        https://serversforhackers.com/c/running-ansible-2-programmatically
    """

    # No try/except here as we want ImportErrors to raise
    from ansible.parsing.dataloader import DataLoader
    from ansible.vars.manager import VariableManager
    from ansible.inventory.manager import InventoryManager
    from ansible.playbook.play import Play
    from ansible.executor.playbook_executor import PlaybookExecutor
    #from ansible.plugins.callback import CallbackBase

    # Copy the current working directory to revert back to later
    cwd = os.getcwd()

    # Change working directory
    roles_path = os.path.join(current.request.folder, "private", "eden_deploy")
    os.chdir(roles_path)

    # Initialize needed objects
    loader = DataLoader()
    options = Storage(connection = "local", # @ToDo: Will need changing when doing multi-host
                      module_path = roles_path,
                      forks = 100,
                      become = None,
                      become_method = None,
                      become_user = None,
                      check = False,
                      diff = False,
                      tags = tags or [],
                      skip_tags = [], # Needs to be an iterable as hasattr(Storage()) is always True
                      private_key_file = private_key, # @ToDo: Needs testing
                      )

    # Instantiate Logging for handling results as they come in
    #results_callback = CallbackModule() # custom subclass of CallbackBase

    # Create Inventory and pass to Var manager
    if len(hosts) == 1:
        # Ensure that we have a comma to tell Ansible that this is a list of hosts not a file to read from
        sources = "%s," % hosts[0]
    else:
        sources = ",".join(hosts)
    inventory = InventoryManager(loader=loader, sources=sources)
    variable_manager = VariableManager(loader=loader, inventory=inventory)
    # https://github.com/ansible/ansible/issues/21562
    tmp_path = os.path.join("/", "tmp")
    variable_manager.extra_vars = {"ansible_local_tmp": tmp_path,
                                   "ansible_remote_tmp": tmp_path,
                                   }

    # Run Playbook
    pbex = PlaybookExecutor(playbooks = [playbook], 
                            inventory = inventory, 
                            variable_manager = variable_manager,
                            loader = loader, 
                            options = options, 
                            passwords = {},
                            )
    pbex.run()

    # Check for Failures
    result = {}
    stats = pbex._tqm._stats
    hosts = sorted(stats.processed.keys())
    for h in hosts:
        t = stats.summarize(h)
        if t["failures"] > 0:
            raise Exception("One of the tasks failed")
        elif t["unreachable"] > 0:
            raise Exception("Host unreachable")
        result[h] = t

    # Change working directory back
    os.chdir(cwd)

    return result

# =============================================================================
def setup_rheader(r, tabs=None):
    """ Resource component page header """

    if r.representation == "html" and r.id:

        T = current.T

        tabs = [(T("Deployment Details"), None),
                (T("Servers"), "server"),
                (T("Instances"), "instance"),
                (T("Settings"), "setting"),
                ]

        rheader_tabs = s3_rheader_tabs(r, tabs)

        rheader = DIV(rheader_tabs)

        return rheader

# =============================================================================
class Storage2(Storage):
    """
        Read settings.x.y without needing to first create settings.x
    """

    def __getattr__(self, key):
        value = dict.get(self, key)
        if value is None:
            self[key] = value = Storage2()
        return value

    def __call__(self):
        """
            settings.import_template()
        """
        return

# END =========================================================================
