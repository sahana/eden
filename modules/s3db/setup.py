# -*- coding: utf-8 -*-

""" Sahana Eden Setup Model:
        * Installation of a Deployment
        * Configuration of a Deployment
        * Managing a Deployment (Start/Stop/Clean instances)
        * Monitoring of a Deployment
        * Upgrading a Deployment (tbc)

    @copyright: 2015-2019 (c) Sahana Software Foundation
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
           "S3SetupMonitorModel",
           #"Storage2",
           #"setup_DeploymentRepresent",
           "setup_monitor_run_task",
           "setup_monitor_check_email_reply",
           "setup_instance_settings_read",
           #"setup_write_playbook",
           "setup_run_playbook",
           "setup_rheader",
           )

import json
import os
import random
import string
import time

from gluon import *

from ..s3 import *
from s3compat import basestring

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
                  2: "setup",
                  3: "test",
                  4: "demo",
                  }

# =============================================================================
class S3SetupModel(S3Model):

    names = ("setup_deployment",
             "setup_deployment_id",
             "setup_server",
             "setup_server_id",
             "setup_instance",
             "setup_setting",
             )

    def model(self):

        T = current.T
        db = current.db

        add_components = self.add_components
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
                     # @ToDo: Allow use of Custom repo
                     # @ToDo: Add ability to get a specific hash/tag
                     Field("repo_url",
                           default = "https://github.com/sahana/eden",
                           label = T("Eden Repository"),
                           requires = IS_URL(),
                           readable = False,
                           writable = False,
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
                  list_fields = ["production.url",
                                 "country",
                                 "template",
                                 "webserver_type",
                                 "db_type",
                                 ],
                  )

        add_components(tablename,
                       setup_instance = (# All instances:
                                         "deployment_id",
                                         # Production instance:
                                         {"name": "production",
                                          "joinby": "deployment_id",
                                          "filterby": {
                                              "type": 1,
                                              },
                                          "multiple": False,
                                          },
                                         ),
                       setup_monitor_task = "deployment_id",
                       setup_server = (# All instances:
                                       "deployment_id",
                                       # Production instance:
                                       {"name": "production_server",
                                        "joinby": "deployment_id",
                                        "filterby": {
                                            "role": 1,
                                            },
                                        "multiple": False,
                                        },
                                       ),
                       setup_setting = "deployment_id",
                       )

        set_method("setup", "deployment",
                   method = "wizard",
                   action = self.setup_server_wizard)

        represent = setup_DeploymentRepresent()

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
        SERVER_ROLES = {1: "all",
                        2: "db",
                        #3: "webserver",
                        #4: "eden",
                        }

        tablename = "setup_server"
        define_table(tablename,
                     # @ToDo: Server Groups
                     #group_id(),
                     deployment_id(),
                     Field("host_ip", unique=True, length=24,
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
                     #Field("hostname",
                     #      label = T("Hostname"),
                     #      requires = IS_NOT_EMPTY(),
                     #      ),
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
                     *s3_meta_fields()
                     )

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

        crud_form = S3SQLCustomForm("deployment_id",
                                    "host_ip",
                                    "role",
                                    "remote_user",
                                    "private_key",
                                    (T("Monitor"), "monitor_server.enabled"),
                                    "monitor_server.status",
                                    )

        configure(tablename,
                  crud_form = crud_form,
                  list_fields = ["deployment_id",
                                 "host_ip",
                                 "role",
                                 "monitor_server.enabled",
                                 "monitor_server.status",
                                 ],
                  )

        add_components(tablename,
                       setup_monitor_run = {"name": "monitor_log",
                                            "joinby": "server_id",
                                            },
                       setup_monitor_server = {"joinby": "server_id",
                                               "multiple": False,
                                               },
                       setup_monitor_task = "server_id",
                       )

        # @ToDo: Add represented Deployment/Role
        represent = S3Represent(lookup=tablename, fields=["host_ip"])

        server_id = S3ReusableField("server_id", "reference %s" % tablename,
                                    label = T("Server"),
                                    ondelete = "CASCADE",
                                    represent = represent,
                                    requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "setup_server.id",
                                                          represent,
                                                          sort=True
                                                          )),
                                    sortby = "host_ip",
                                    )

        set_method("setup", "server",
                   method = "enable",
                   action = setup_monitor_server_enable_interactive)

        set_method("setup", "server",
                   method = "disable",
                   action = setup_monitor_server_disable_interactive)

        set_method("setup", "server",
                   method = "check",
                   action = setup_monitor_server_check)

        # ---------------------------------------------------------------------
        # Instances
        #
        type_represent = S3Represent(options = INSTANCE_TYPES)

        tablename = "setup_instance"
        define_table(tablename,
                     deployment_id(),
                     Field("type", "integer",
                           default = 1,
                           label = T("Type"),
                           represent = type_represent,
                           requires = IS_IN_SET(INSTANCE_TYPES),
                           ),
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
                     #Field("ssl_cert", "upload",
                     #      label = T("SSL Certificate"),
                     #      length = current.MAX_FILENAME_LENGTH,
                     #      requires = IS_EMPTY_OR(IS_UPLOAD_FILENAME()),
                     #      uploadfolder = path_join(folder, "uploads"),
                     #      comment = DIV(_class="tooltip",
                     #                    _title="%s|%s" % (T("SSL Certificate"),
                     #                                      T("If not using Let's Encrypt e.g. you wish to use an OV or EV certificate")
                     #                                      )
                     #                    ),
                     #      ),
                     #Field("ssl_key", "upload",
                     #      label = T("SSL Key"),
                     #      length = current.MAX_FILENAME_LENGTH,
                     #      requires = IS_EMPTY_OR(IS_UPLOAD_FILENAME()),
                     #      uploadfolder = path_join(folder, "uploads"),
                     #      comment = DIV(_class="tooltip",
                     #                    _title="%s|%s" % (T("SSL Key"),
                     #                                      T("If not using Let's Encrypt e.g. you wish to use an OV or EV certificate")
                     #                                      )
                     #                    ),
                     #      ),
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
                     # @ToDo: Action post-deployment changes
                     Field("start", "boolean",
                           default = True, # default = False in Controller for additional instances
                           label = T("Start at Boot"),
                           represent = s3_yes_no_represent,
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
                     # Has the Configuration Wizard been run?
                     Field("configured", "boolean",
                           default = False,
                           #represent = s3_yes_no_represent,
                           readable = False,
                           writable = False,
                           ),
                     *s3_meta_fields()
                     )

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

        configure(tablename,
                  list_fields = ["type",
                                 "url",
                                 "start",
                                 "task_id",
                                 ],
                  )

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

        set_method("setup", "deployment",
                   component_name = "instance",
                   method = "start",
                   action = self.setup_instance_start,
                   )

        set_method("setup", "deployment",
                   component_name = "instance",
                   method = "stop",
                   action = self.setup_instance_stop,
                   )

        set_method("setup", "deployment",
                   component_name = "instance",
                   method = "clean",
                   action = self.setup_instance_clean,
                   )

        set_method("setup", "deployment",
                   component_name = "instance",
                   method = "wizard",
                   action = self.setup_instance_wizard,
                   )

        represent = S3Represent(lookup = tablename,
                                fields = ["type"],
                                labels = lambda row: type_represent(row.type))

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

        return {"setup_deployment_id": deployment_id,
                "setup_server_id": server_id,
                }

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
        # Ensure that ' isn't included otherwise we get a syntax error in pgpass.sql
        chars = chars.replace("'", "")
        # Ensure that @ isn't included as Web2Py doesn't like this
        chars = chars.replace("@", "")
        password = "".join(random.choice(chars) for _ in range(12))
        db(table.id == deployment_id).update(db_password = password)

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

        # All subdirectories in the path that contain a config.py are
        # templates - except skeleton/skeletontheme
        dirs = next(os.walk(path))[1]
        templates = [d for d in dirs
                         if d[:8] != "skeleton" and
                         os.path.isfile(os.path.join(path, d, "config.py"))
                         ]

        subtemplates = []
        sappend = subtemplates.append
        for template in templates:
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
    def setup_server_wizard(self, r, **attr):
        """
            Custom S3Method to select an Instance to Configure
        """

        db = current.db
        deployment_id = r.id
        itable = db.setup_instance

        instances = db(itable.deployment_id == deployment_id).select(itable.id,
                                                                     itable.type,
                                                                     )

        if len(instances) == 1:
            # Redirect to the Instance Wizard
            redirect(URL(c="setup", f="deployment",
                         args = [deployment_id, "instance", instances.first().id, "wizard"],
                         ))

        # Provide a Dropdown of Instances for the user to select
        dropdown = SELECT(OPTION(_value=""),
                          _id = "instances",
                          )
        for instance in instances:
            dropdown.append(OPTION(INSTANCE_TYPES[instance.type],
                                   _value="%s" % instance.id))

        script = '''
var dropdown = $('#instances');
dropdown.change(function() {
 var url = S3.Ap.concat('/setup/deployment/%s/instance/' + this.value + '/wizard');
 $(location).prop('href', url);
})''' % deployment_id
        response = current.response
        response.s3.jquery_ready.append(script)
        response.view = "simple.html"
        output = {"item": DIV(P(current.T("Select the instance you wish to configure")),
                              dropdown),
                  }
        return output

    # -------------------------------------------------------------------------
    def setup_instance_wizard(self, r, **attr):
        """
            Custom S3Method to Configure an Instance

            @ToDo: Option to Propagate settings from Prod to Demo &/or Test
                   - on by default
        """

        from gluon import IS_IN_SET, SQLFORM
        from gluon.sqlhtml import RadioWidget
        from s3 import s3_mark_required
        from s3dal import Field

        T = current.T
        response = current.response
        settings = current.deployment_settings

        questions = settings.get_setup_wizard_questions()

        fields = []
        fappend = fields.append
        for q in questions:
            setting = q["setting"]
            fname = setting.replace(".", "_")
            fappend(Field(fname,
                          label = T(q["question"]),
                          requires = IS_IN_SET(q["options"]),
                          widget = RadioWidget.widget,
                          #widget = lambda f, v: RadioWidget.widget(f, v, style="divs"),
                          _id = "setting",
                          ))

        labels, required = s3_mark_required(fields)
        response.s3.has_required = required
        response.form_label_separator = ""

        form = SQLFORM.factory(#formstyle = settings.get_ui_formstyle(),
                               submit_button = T("Submit"),
                               labels = labels,
                               separator = "",
                               table_name = "options", # Dummy table name
                               _id = "options",
                               *fields
                               )

        if form.accepts(r.post_vars, current.session):
            # Processs Form
            result = self.setup_settings_apply(r.id, form.vars)
            if result:
                response.confirmation = T("Settings Applied")

        current.response.view = "simple.html"
        output = {"item": form,
                  "title": T("Configuration Wizard"),
                  }
        return output

    # -------------------------------------------------------------------------
    def setup_instance_deploy(self, r, **attr):
        """
            Custom S3Method to Deploy an Instance
        """

        db = current.db
        s3db = current.s3db

        deployment_id = r.id

        # Get Instance details
        # - we read all instances for Certbot configuration
        instance_id = r.component_id
        itable = s3db.setup_instance
        query = (itable.deployment_id == deployment_id) & \
                (itable.deleted == False)
        instances = db(query).select(itable.id,
                                     itable.type,
                                     itable.url,
                                     itable.sender,
                                     itable.start,
                                     )
        all_sites = []
        all_append = all_sites.append
        for instance in instances:
            url = instance.url
            if "://" in url:
                protocol, url = url.split("://", 1)
            all_append(url)
            if str(instance.id) == instance_id:
                sitename = url
                sender = instance.sender
                start = instance.start
                instance_type = instance.type

        # Default to SSL
        # (plain http requests will still work as automatically redirected to https)
        protocol = "https"

        # Get Server(s) details
        stable = s3db.setup_server
        query = (stable.deployment_id == deployment_id)
        servers = db(query).select(stable.role,
                                   stable.host_ip,
                                   stable.remote_user,
                                   stable.private_key,
                                   )

        # Get Deployment details
        dtable = s3db.setup_deployment
        deployment = db(dtable.id == deployment_id).select(dtable.webserver_type,
                                                           dtable.db_type,
                                                           dtable.db_password,
                                                           dtable.template,
                                                           limitby=(0, 1)
                                                           ).first()

        # Build Playbook data structure
        roles_path = os.path.join(r.folder, "private", "eden_deploy", "roles")

        appname = "eden" # @ToDo: Allow this to be configurable
        hostname = sitename.split(".", 1)[0]
        db_password = deployment.db_password
        web_server = WEB_SERVERS[deployment.webserver_type]
        db_type = DB_SERVERS[deployment.db_type]
        instance_type = INSTANCE_TYPES[instance_type]
        template = deployment.template

        if len(servers) == 1:
            # All-in-one deployment
            server = servers.first()
            host_ip = server.host_ip
            hosts = [host_ip]
            private_key = server.private_key
            playbook = [{"hosts": host_ip,
                         "connection": "local", # @ToDo: Don't assume this
                         "remote_user": server.remote_user,
                         "become_method": "sudo",
                         "become_user": "root",
                         "vars": {"appname": appname,
                                  "all_sites": ",".join(all_sites),
                                  "db_ip": host_ip,
                                  "db_type": db_type,
                                  "hostname": hostname,
                                  "password": db_password,
                                  "protocol": protocol,
                                  "sender": sender,
                                  "sitename": sitename,
                                  "start": start,
                                  "template": template,
                                  "type": instance_type,
                                  "web_server": web_server,
                                  },
                         "roles": [{ "role": "%s/common" % roles_path },
                                   { "role": "%s/%s" % (roles_path, web_server) },
                                   { "role": "%s/uwsgi" % roles_path },
                                   { "role": "%s/%s" % (roles_path, db_type) },
                                   { "role": "%s/final" % roles_path },
                                   ]
                         },
                        ]
        else:
            # Separate Database
            # @ToDo: Needs testing/completion
            for server in servers:
                if server.role == 2:
                    db_ip = server.host_ip
                    private_key = server.private.key
                    remote_user = server.remote_user
                else:
                    webserver_ip = server.host_ip
            hosts = [db_ip, webserver_ip]
            playbook = [{"hosts": db_ip,
                         "remote_user": remote_user,
                         "become_method": "sudo",
                         "become_user": "root",
                         "vars": {"db_type": db_type,
                                  "password": db_password,
                                  "type": instance_type
                                  },
                         "roles": [{ "role": "%s/%s" % (roles_path, db_type) },
                                   ]
                         },
                        {"hosts": webserver_ip,
                         #"remote_user": remote_user,
                         "become_method": "sudo",
                         "become_user": "root",
                         "vars": {"appname": appname,
                                  "all_sites": ",".join(all_sites),
                                  "db_ip": db_ip,
                                  "db_type": db_type,
                                  "hostname": hostname,
                                  "password": db_password,
                                  "protocol": protocol,
                                  "sitename": sitename,
                                  "sender": sender,
                                  "start": start,
                                  "template": template,
                                  "type": instance_type,
                                  "web_server": web_server,
                                  },
                         "roles": [{ "role": "%s/common" % roles_path },
                                   { "role": "%s/%s" % (roles_path, web_server) },
                                   { "role": "%s/uwsgi" % roles_path },
                                   { "role": "%s/final" % roles_path },
                                   ],
                         },
                        ]

        # Write Playbook
        name = "deployment_%d" % int(time.time())
        if instance_type == "prod":
            tags = []
        else:
            tags = [instance_type]
        task_vars = setup_write_playbook("%s.yml" % name,
                                         playbook,
                                         hosts,
                                         tags,
                                         private_key,
                                         )

        # Run Playbook
        task_id = current.s3task.schedule_task(name,
                                               vars = task_vars,
                                               function_name = "setup_run_playbook",
                                               repeats = None,
                                               timeout = 6000,
                                               #sync_output = 300
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
    def setup_instance_settings(r, **attr):
        """
            Custom interactive S3Method to Read the Settings for an instance
            from models/000_config.py
        """

        deployment_id = r.id

        setup_instance_settings_read(r.component_id, deployment_id)

        current.session.confirmation = current.T("Settings Read")

        redirect(URL(c="setup", f="deployment",
                     args = [deployment_id, "setting"]),
                     )

    # -------------------------------------------------------------------------
    @staticmethod
    def setup_instance_start(r, **attr):
        """
            Custom interactive S3Method to Start an Instance
        """

        setup_instance_method(r.component_id)

        current.session.confirmation = current.T("Instance Started")

        redirect(URL(c="setup", f="deployment",
                     args = [r.id, "instance"]),
                     )

    # -------------------------------------------------------------------------
    @staticmethod
    def setup_instance_stop(r, **attr):
        """
            Custom interactive S3Method to Stop an Instance
        """

        setup_instance_method(r.component_id, "stop")

        current.session.confirmation = current.T("Instance Stopped")

        redirect(URL(c="setup", f="deployment",
                     args = [r.id, "instance"]),
                     )

    # -------------------------------------------------------------------------
    @staticmethod
    def setup_instance_clean(r, **attr):
        """
            Custom interactive S3Method to Clean an Instance
        """

        setup_instance_method(r.component_id, "clean")

        current.session.confirmation = current.T("Instance Clean Started")

        redirect(URL(c="setup", f="deployment",
                     args = [r.id, "instance"]),
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

        itable = s3db.setup_instance
        instance = db(itable.id == setting.instance_id).select(itable.type,
                                                               limitby = (0, 1)
                                                               ).first()
        instance_type = INSTANCE_TYPES[instance.type]

        # Lookup Server Details
        # @ToDo: Support multiple Eden servers used as Load-balancers
        svtable = s3db.setup_server
        query = (svtable.deployment_id == deployment_id) & \
                (svtable.role.belongs((1, 4)))
        server = db(query).select(svtable.host_ip,
                                  svtable.remote_user,
                                  svtable.private_key,
                                  limitby = (0, 1)
                                  ).first()
        host = server.host_ip
        remote_user = server.remote_user
        private_key = server.private_key

        # Build Playbook data structure:
        the_setting = setting.setting
        if new_value is True or new_value is False:
            new_line = "settings.%s = %s" % (the_setting, new_value)
        else:
            # @ToDo: Handle lists/dicts (load into JSONS3?)
            new_line = 'settings.%s = "%s"' % (the_setting, new_value)

        appname = r.application

        playbook = [{"hosts": host,
                     "connection": "local", # @ToDo: Don't assume this
                     "remote_user": remote_user,
                     "become_method": "sudo",
                     "become_user": "root",
                     "tasks": [{"name": "Edit 000_config.py",
                                "lineinfile": {"dest": "/home/%s/applications/%s/models/000_config.py" % (instance_type, appname),
                                               "regexp": "^settings.%s =" % the_setting,
                                               "line": new_line,
                                               "state": "present",
                                               },
                                },
                               # @ToDo: Handle case where need to restart multiple webservers
                               {"name": "Compile & Restart WebServer",
                                #"command": "sudo -H -u web2py python web2py.py -S %(appname)s -M -R applications/%(appname)s/static/scripts/tools/compile.py" % {"appname": appname},
                                #"args": {"chdir": "/home/%s" % instance_type,
                                #         },
                                # We don't want to restart the UWSGI process running the Task until after the Task has completed
                                "command": 'echo "/usr/local/bin/compile %s" | at now + 1 minutes' % instance_type,
                                "become": "yes",
                                },
                               ]
                     },
                    ]

        # Write Playbook
        name = "apply_%d" % int(time.time())
        task_vars = setup_write_playbook("%s.yml" % name,
                                         playbook,
                                         [host],
                                         tags = None,
                                         private_key = private_key,
                                         )

        # Run the Playbook
        current.s3task.schedule_task(name,
                                     vars = task_vars,
                                     function_name = "setup_run_playbook",
                                     repeats = None,
                                     timeout = 6000,
                                     #sync_output = 300
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

    # -------------------------------------------------------------------------
    @staticmethod
    def setup_settings_apply(instance_id, settings):
        """
            Method to Apply Settings to an instance
            via models/000_config.py
        """

        db = current.db
        s3db = current.s3db
        appname = current.request.application

        itable = s3db.setup_instance
        instance = db(itable.id == instance_id).select(itable.id,
                                                       itable.deployment_id,
                                                       itable.type,
                                                       limitby = (0, 1)
                                                       ).first()
        deployment_id = instance.deployment_id
        instance_type = INSTANCE_TYPES[instance.type]

        # Lookup Server Details
        # @ToDo: Support multiple Eden servers used as Load-balancers
        svtable = s3db.setup_server
        query = (svtable.deployment_id == deployment_id) & \
                (svtable.role.belongs((1, 4)))
        server = db(query).select(svtable.host_ip,
                                  svtable.remote_user,
                                  svtable.private_key,
                                  limitby = (0, 1)
                                  ).first()
        host = server.host_ip
        remote_user = server.remote_user
        private_key = server.private_key

        # Build Playbook data structure:
        tasks = []
        tappend = tasks.append
        for setting in settings:
            the_setting = setting.replace("_", ".", 1)
            new_value = settings[setting]
            if new_value == "True" or new_value == "False":
                new_line = "settings.%s = %s" % (the_setting, new_value)
            else:
                # @ToDo: Handle lists/dicts (load into JSONS3?)
                new_line = 'settings.%s = "%s"' % (the_setting, new_value)
            tappend({"name": "Edit 000_config.py",
                     "lineinfile": {"dest": "/home/%s/applications/%s/models/000_config.py" % (instance_type, appname),
                                    "regexp": "^settings.%s =" % the_setting,
                                    "line": new_line,
                                    "state": "present",
                                    },
                     })

        # @ToDo: Handle case where need to restart multiple webservers
        tappend({"name": "Compile & Restart WebServer",
                 #"command": "sudo -H -u web2py python web2py.py -S %(appname)s -M -R applications/%(appname)s/static/scripts/tools/compile.py" % {"appname": appname},
                 #"args": {"chdir": "/home/%s" % instance_type,
                 #         },
                 # We don't want to restart the UWSGI process running the Task until after the Task has completed
                 "command": 'echo "/usr/local/bin/compile %s" | at now + 1 minutes' % instance_type,
                 "become": "yes",
                 })

        playbook = [{"hosts": host,
                     "connection": "local", # @ToDo: Don't assume this
                     "remote_user": remote_user,
                     "become_method": "sudo",
                     "become_user": "root",
                     "tasks": tasks,
                     },
                    ]

        # Write Playbook
        name = "apply_%d" % int(time.time())
        task_vars = setup_write_playbook("%s.yml" % name,
                                         playbook,
                                         [host],
                                         tags = None,
                                         private_key = private_key,
                                         )

        # Run the Playbook
        current.s3task.schedule_task(name,
                                     vars = task_vars,
                                     function_name = "setup_run_playbook",
                                     repeats = None,
                                     timeout = 6000,
                                     #sync_output = 300
                                     )

        # Update the DB to show that the settings have been applied
        # @ToDo: Do this as a callback from the async task
        instance.update_record(configured = True)
        stable = s3db.setup_setting
        q = (stable.instance_id == instance_id)
        for setting in settings:
            the_setting = setting.replace("_", ".", 1)
            new_value = settings[setting]
            db(q & (stable.setting == the_setting)).update(current_value = new_value,
                                                           new_value = None)

        return True

# =============================================================================
class S3SetupMonitorModel(S3Model):

    names = ("setup_monitor_server",
             "setup_monitor_check",
             "setup_monitor_check_option",
             "setup_monitor_task",
             "setup_monitor_task_option",
             "setup_monitor_run",
             #"setup_monitor_alert",
             )

    def model(self):

        T = current.T
        db = current.db

        add_components = self.add_components
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        set_method = self.set_method
        server_id = self.setup_server_id

        UNKNOWN_OPT = current.messages.UNKNOWN_OPT

        STATUS_OPTS = {1 : T("OK"),
                       2 : T("Warning"),
                       3 : T("Critical"),
                       4 : T("Unknown"),
                       }

        status_id = S3ReusableField("status", "integer", notnull=True,
                                    default = 4,
                                    label = T("Status"),
                                    represent = lambda opt: \
                                                    STATUS_OPTS.get(opt,
                                                                    UNKNOWN_OPT),
                                    requires = IS_IN_SET(STATUS_OPTS,
                                                         zero=None),
                                    writable = False,
                                    )

        # =====================================================================
        # Servers
        # - extensions for Monitoring
        #
        tablename = "setup_monitor_server"
        define_table(tablename,
                     #Field("name", unique=True, length=255,
                     #      label = T("Name"),
                     #      ),
                     server_id(),
                     Field("enabled", "boolean",
                           default = True,
                           label = T("Enabled?"),
                           represent = s3_yes_no_represent,
                           ),
                     status_id(),
                     s3_comments(),
                     *s3_meta_fields())

        configure(tablename,
                  onaccept = self.setup_monitor_server_onaccept,
                  )

        # =====================================================================
        # Checks
        #
        tablename = "setup_monitor_check"
        define_table(tablename,
                     Field("name", unique=True, length=255,
                           label = T("Name"),
                           ),
                     Field("function_name",
                           label = T("Script"),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
                label_create = T("Create Check"),
                title_display = T("Check Details"),
                title_list =  T("Checks"),
                title_update = T("Edit Check"),
                title_upload = T("Import Checks"),
                label_list_button =  T("List Checks"),
                label_delete_button = T("Delete Check"),
                msg_record_created = T("Check added"),
                msg_record_modified = T("Check updated"),
                msg_record_deleted = T("Check deleted"),
                msg_list_empty = T("No Checks currently registered"))

        represent = S3Represent(lookup=tablename)
        check_id = S3ReusableField("check_id", "reference %s" % tablename,
                                   label = T("Check"),
                                   ondelete = "CASCADE",
                                   represent = represent,
                                   requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "setup_monitor_check.id",
                                                          represent)),
                                   )

        add_components(tablename,
                       setup_monitor_check_option = {"name": "option",
                                                     "joinby": "check_id",
                                                     },
                       setup_monitor_task = "check_id",
                       )

        # =====================================================================
        # Check Options
        # - default configuration of the Check
        #
        tablename = "setup_monitor_check_option"
        define_table(tablename,
                     check_id(),
                     # option is a reserved word in MySQL
                     Field("tag",
                           label = T("Option"),
                           ),
                     Field("value",
                           label = T("Value"),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # =====================================================================
        # Tasks
        #
        tablename = "setup_monitor_task"
        define_table(tablename,
                     self.setup_deployment_id(readable = False,
                                              writable = False,
                                              ),
                     server_id(),
                     check_id(),
                     Field("enabled", "boolean",
                           default = True,
                           label = T("Enabled?"),
                           represent = s3_yes_no_represent,
                           ),
                     status_id(),
                     s3_comments(),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("Create Task"),
            title_display = T("Task Details"),
            title_list =  T("Tasks"),
            title_update = T("Edit Task"),
            title_upload = T("Import Tasks"),
            label_list_button =  T("List Tasks"),
            label_delete_button = T("Delete Task"),
            msg_record_created = T("Task added"),
            msg_record_modified = T("Task updated"),
            msg_record_deleted = T("Task deleted"),
            msg_list_empty = T("No Tasks currently registered"))

        configure(tablename,
                  # Open the Options after creation
                  create_next = URL(c="setup", f="monitor_task", args=["[id]", "option"]),
                  onaccept = self.setup_monitor_task_onaccept,
                  )

        # @ToDo: Fix represent
        represent = S3Represent(lookup=tablename, fields=["server_id", "check_id"])
        task_id = S3ReusableField("task_id", "reference %s" % tablename,
                                  label = T("Task"),
                                  ondelete = "CASCADE",
                                  represent = represent,
                                  requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "setup_monitor_task.id",
                                                          represent)),
                                  )

        add_components(tablename,
                       setup_monitor_alert = "task_id",
                       setup_monitor_run = "task_id",
                       setup_monitor_task_option = {"name": "option",
                                                    "joinby": "task_id",
                                                    },
                       )

        set_method("monitor", "task",
                   method = "enable",
                   action = self.setup_monitor_task_enable_interactive)

        set_method("monitor", "task",
                   method = "disable",
                   action = self.setup_monitor_task_disable_interactive)

        set_method("monitor", "task",
                   method = "check",
                   action = self.setup_monitor_task_run)

        # =====================================================================
        # Task Options
        # - configuration of the Task
        #
        tablename = "setup_monitor_task_option"
        define_table(tablename,
                     task_id(),
                     # option is a reserved word in MySQL
                     Field("tag",
                           label = T("Option"),
                           ),
                     Field("value",
                           label = T("Value"),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # =====================================================================
        # Runs
        #
        tablename = "setup_monitor_run"
        define_table(tablename,
                     server_id(writable = False),
                     task_id(writable = False),
                     status_id(),
                     s3_comments(),
                     *s3_meta_fields()#,
                     #on_define = lambda table: \
                     #   [table.created_on.set_attributes(represent = \
                     #       lambda dt: S3DateTime.datetime_represent(dt, utc=True)),
                     #   ]
                     )

        crud_strings[tablename] = Storage(
            #label_create = T("Create Log Entry"),
            title_display = T("Log Entry Details"),
            title_list =  T("Log Entries"),
            title_update = T("Edit Log Entry"),
            #title_upload = T("Import Log Entries"),
            label_list_button =  T("List Log Entries"),
            label_delete_button = T("Delete Log Entry"),
            #msg_record_created = T("Log Entry added"),
            msg_record_modified = T("Log Entry updated"),
            msg_record_deleted = T("Log Entry deleted"),
            msg_list_empty = T("No Log Entries currently registered"))

        configure(tablename,
                  # Logs inserted automatically
                  insertable = False,
                  list_fields = ["created_on",
                                 "server_id",
                                 "task_id",
                                 "status",
                                 "comments",
                                 ],
                  orderby = "setup_monitor_run.created_on desc",
                  )

        # =============================================================================
        # Alerts
        #  - what threshold to raise an alert on
        #
        # @ToDo: UI to wrap normal Subscription / Notifications

        #tablename = "setup_monitor_alert"
        #define_table(tablename,
        #             task_id(),
        #             self.pr_person_id(),
        #             # @ToDo: Threshold
        #             s3_comments(),
        #             *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def setup_monitor_server_onaccept(form):
        """
            Process the Enabled Flag
        """

        form_vars = form.vars
        if form.record:
            # Update form
            # process of changed
            if form.record.enabled and not form_vars.enabled:
                setup_monitor_server_disable(form_vars.id)
            elif form_vars.enabled and not form.record.enabled:
                setup_monitor_server_enable(form_vars.id)
        else:
            # Create form
            # Process only if enabled
            if form_vars.enabled:
                setup_monitor_server_enable(form_vars.id)

    # -------------------------------------------------------------------------
    @staticmethod
    def setup_monitor_task_enable(task_id):
        """
            Enable a Task
            - Schedule Check

            CLI API for shell scripts & to be called by S3Method
        """

        db = current.db
        table = current.s3db.setup_monitor_task

        record = db(table.id == task_id).select(table.id,
                                                table.enabled,
                                                limitby=(0, 1),
                                                ).first()

        if not record.enabled:
            # Flag it as enabled
            record.update_record(enabled = True)

        # Is the task already Scheduled?
        ttable = db.scheduler_task
        args = "[%s]" % task_id
        query = ((ttable.function_name == "setup_monitor_run_task") & \
                 (ttable.args == args) & \
                 (ttable.status.belongs(["RUNNING", "QUEUED", "ALLOCATED"])))
        exists = db(query).select(ttable.id,
                                  limitby=(0, 1)).first()
        if exists:
            return "Task already enabled"
        else:
            current.s3task.schedule_task("setup_monitor_run_task",
                                         args = [task_id],
                                         period = 300,  # seconds
                                         timeout = 300, # seconds
                                         repeats = 0    # unlimited
                                         )
            return "Task enabled"

    # -------------------------------------------------------------------------
    @staticmethod
    def setup_monitor_task_enable_interactive(r, **attr):
        """
            Enable a Task
            - Schedule Check

            S3Method for interactive requests
        """

        result = S3SetupMonitorModel.setup_monitor_task_enable(r.id)
        current.session.confirmation = result
        redirect(URL(f="task"))

    # -------------------------------------------------------------------------
    @staticmethod
    def setup_monitor_task_disable(task_id):
        """
            Disable a Check
            - Remove Schedule for Check

            CLI API for shell scripts & to be called by S3Method
        """

        db = current.db
        table = current.s3db.setup_monitor_task

        record = db(table.id == task_id).select(table.id, # needed for update_record
                                                table.enabled,
                                                limitby=(0, 1),
                                                ).first()

        if record.enabled:
            # Flag it as disabled
            record.update_record(enabled = False)

        # Is the task already Scheduled?
        ttable = db.scheduler_task
        args = "[%s]" % task_id
        query = ((ttable.function_name == "setup_monitor_run_task") & \
                 (ttable.args == args) & \
                 (ttable.status.belongs(["RUNNING", "QUEUED", "ALLOCATED"])))
        exists = db(query).select(ttable.id,
                                  limitby=(0, 1)).first()
        if exists:
            # Disable all
            db(query).update(status="STOPPED")
            return "Task disabled"
        else:
            return "Task already disabled"

    # -------------------------------------------------------------------------
    @staticmethod
    def setup_monitor_task_disable_interactive(r, **attr):
        """
            Disable a Task
            - Remove Schedule for Check

            S3Method for interactive requests
        """

        result = S3SetupMonitorModel.setup_monitor_task_disable(r.id)
        current.session.confirmation = result
        redirect(URL(f="monitor_task"))

    # -------------------------------------------------------------------------
    @staticmethod
    def setup_monitor_task_onaccept(form):
        """
            Process the Enabled Flag
            Create Form:
                Set deployment_id
                PrePopulate Task Options from Check Options
        """

        form_vars = form.vars
        if form.record:
            # Update form
            # process if changed
            if form.record.enabled and not form_vars.enabled:
                S3SetupMonitorModel.setup_monitor_task_disable(form_vars.id)
            elif form_vars.enabled and not form.record.enabled:
                S3SetupMonitorModel.setup_monitor_task_enable(form_vars.id)
        else:
            # Create form
            db = current.db
            record_id = form_vars.id
            if form_vars.enabled:
                # Process only if enabled
                S3SetupMonitorModel.setup_monitor_task_enable(record_id)

            # Set deployment_id
            ttable = db.setup_monitor_task
            server_id = form_vars.server_id
            if server_id:
                task = None
            else:
                # Read record
                task = db(ttable.id == record_id).select(ttable.id,
                                                         ttable.server_id,
                                                         limitby = (0, 1)
                                                         ).first()
                server_id = task.server_id
            stable = db.setup_server
            server = db(stable.id == server_id).select(stable.deployment_id,
                                                       limitby = (0, 1)
                                                       ).first()
            deployment_id = server.deployment_id
            if task:
                task.update_record(deployment_id = deployment_id)
            else:
                db(ttable.id == record_id).update(deployment_id = deployment_id)

            # Pre-populate task options
            check_id = form_vars.check_id
            cotable = db.setup_monitor_check_option
            query = (cotable.check_id == check_id) & \
                    (cotable.deleted == False)
            options = db(query).select(cotable.tag,
                                       cotable.value,
                                       )
            if not options:
                return
            totable = db.setup_monitor_task_option
            for option in options:
                totable.insert(tag = option.tag,
                               value = option.value,
                               )

    # -------------------------------------------------------------------------
    @staticmethod
    def setup_monitor_task_run(r, **attr):
        """
            Run a Task

            S3Method for interactive requests
        """

        task_id = r.id
        current.s3task.run_async("setup_monitor_task_run", args=[task_id])
        current.session.confirmation = \
            current.T("The check request has been submitted, so results should appear shortly - refresh to see them")

        redirect(URL(c="setup", f="monitor_task",
                     args = [task_id, "log"],
                     ))

# =============================================================================
def setup_monitor_server_enable(server_id):
    """
        Enable Monitoring for a Server
        - Schedule all enabled Tasks

        CLI API for shell scripts & to be called by S3Method
    """

    db = current.db

    stable = current.s3db.setup_monitor_server
    record = db(stable.server_id == server_id).select(stable.id,
                                                      stable.enabled,
                                                      limitby=(0, 1),
                                                      ).first()

    if not record.enabled:
        # Flag it as enabled
        record.update_record(enabled = True)

    table = db.setup_monitor_task
    query = (table.server_id == server_id) & \
            (table.enabled == True) & \
            (table.deleted == False)
    tasks = db(query).select(table.id)

    # Do we have any Tasks already Scheduled?
    args = []
    for task in tasks:
        args.append("[%s]" % task.id)
    ttable = db.scheduler_task
    query = ((ttable.function_name == "setup_monitor_run_task") & \
             (ttable.args.belongs(args)) & \
             (ttable.status.belongs(["RUNNING", "QUEUED", "ALLOCATED"])))
    exists = db(query).select(ttable.id)
    exists = [r.id for r in exists]
    for task in tasks:
        task_id = task.id
        if task_id not in exists:
            current.s3task.schedule_task("setup_monitor_run_task",
                                         args = [task_id],
                                         period = 300,  # seconds
                                         timeout = 300, # seconds
                                         repeats = 0    # unlimited
                                         )
    return "Server Monitoring enabled"

# =============================================================================
def setup_monitor_server_enable_interactive(r, **attr):
    """
        Enable Monitoring for a Server
        - Schedule all enabled Tasks

        S3Method for interactive requests
    """

    result = setup_monitor_server_enable(r.id)
    current.session.confirmation = result
    redirect(URL(f="server"))

# =============================================================================
def setup_monitor_server_disable(server_id):
    """
        Disable Monitoring for a Server
        - Remove all related Tasks

        CLI API for shell scripts & to be called by S3Method
    """

    db = current.db

    stable = current.s3db.setup_monitor_server
    record = db(stable.server_id == server_id).select(stable.id,
                                                      stable.enabled,
                                                      limitby=(0, 1),
                                                      ).first()

    if record.enabled:
        # Flag it as disabled
        record.update_record(enabled = False)

    table = db.setup_monitor_task
    query = (table.server_id == server_id) & \
            (table.enabled == True) & \
            (table.deleted == False)
    tasks = db(query).select(table.id)

    # Do we have any Tasks already Scheduled?
    args = []
    for task in tasks:
        args.append("[%s]" % task.id)
    ttable = db.scheduler_task
    query = ((ttable.function_name == "setup_monitor_run_task") & \
             (ttable.args.belongs(args)) & \
             (ttable.status.belongs(["RUNNING", "QUEUED", "ALLOCATED"])))
    exists = db(query).select(ttable.id,
                              limitby=(0, 1)).first()
    if exists:
        # Disable all
        db(query).update(status="STOPPED")
        return "Server Monitoring disabled"
    else:
        return "Server Monitoring already disabled"

# =============================================================================
def setup_monitor_server_disable_interactive(r, **attr):
    """
        Disable Monitoring for a Server
        - Remove all related Tasks

        S3Method for interactive requests
    """

    result = setup_monitor_server_disable(r.id)
    current.session.confirmation = result
    redirect(URL(f="server"))

# =============================================================================
def setup_monitor_server_check(r, **attr):
    """
        Run all enabled Tasks for this server

        S3Method for interactive requests
    """

    server_id = r.id
    table = current.s3db.setup_monitor_task
    query = (table.server_id == server_id) & \
            (table.enabled == True) & \
            (table.deleted == False)
    tasks = current.db(query).select(table.id)
    run_async = current.s3task.run_async
    for task in tasks:
        run_async("setup_monitor_run_task", args=[task.id])
    current.session.confirmation = \
        current.T("The check requests have been submitted, so results should appear shortly - refresh to see them")

    redirect(URL(c="setup", f="server",
                 args = [server_id, "monitor_log"],
                 ))

# =============================================================================
def setup_monitor_run_task(task_id):
    """
        Check a Service
    """

    db = current.db
    table = current.s3db.setup_monitor_task
    ctable = db.setup_monitor_check

    query = (table.id == task_id) & \
            (table.check_id == ctable.id)
    row = db(query).select(table.server_id,
                           ctable.function_name,
                           limitby=(0, 1)
                           ).first()
    server_id = row["setup_monitor_task.server_id"]
    function_name = row["setup_monitor_check.function_name"]

    # Load the Monitor template for this deployment
    template = current.deployment_settings.get_setup_monitor_template()
    module_name = "applications.%s.modules.templates.%s.monitor" \
        % (current.request.application, template)
    __import__(module_name)
    mymodule = sys.modules[module_name]
    S3Monitor = mymodule.S3Monitor()

    # Get the Check Script
    try:
        fn = getattr(S3Monitor, function_name)
    except:
        current.log.error("Check Script not found: %s" % function_name)
        return None

    # Create an entry in the monitor_run table
    rtable = db.setup_monitor_run
    run_id = rtable.insert(server_id = server_id,
                           task_id = task_id,
                           )
    # Ensure the entry is made even if the script crashes
    db.commit()

    # Run the script
    result = fn(task_id, run_id)

    # Update the entry with the result
    if result:
        status = result
    else:
        # No result
        status = 2 # Warning

    db(rtable.id == run_id).update(status=status)

    # @ToDo: Cascade status to Host

    return result

# =============================================================================
def setup_monitor_check_email_reply(run_id):
    """
        Check whether we have received a reply to an Email check
    """

    rtable = current.s3db.setup_monitor_run
    record = current.db(rtable.id == run_id).select(rtable.id,
                                                    rtable.status,
                                                    limitby=(0, 1)).first()
    try:
        status = record.status
    except:
        # Can't find run record!
        # @ToDo: Send Alert
        pass
    else:
        if status == 2:
            # Still in Warning State: Make it go Critical
            record.update_record(status=3)
            # @ToDo: Send Alert

# =============================================================================
def setup_write_playbook(playbook_name,
                         playbook_data,
                         hosts,
                         tags = None,
                         private_key = None,
                         ):
    """
        Write an Ansible Playbook file
    """

    try:
        import yaml
    except ImportError:
        error = "PyYAML module needed for Setup"
        current.log.error(error)
        current.response.error = error
        return

    folder = current.request.folder
    os_path = os.path
    os_path_join = os_path.join

    playbook_folder = os_path_join(folder, "uploads", "playbook")
    if not os_path.isdir(playbook_folder):
        os.mkdir(playbook_folder)

    playbook_path = os_path_join(playbook_folder, playbook_name)

    with open(playbook_path, "w") as yaml_file:
        yaml_file.write(yaml.dump(playbook_data, default_flow_style=False))

    task_vars = {"playbook": playbook_path,
                 "hosts": hosts,
                 }
    if tags:
        # only_tags
        task_vars["tags"] = tags
    if private_key:
        task_vars["private_key"] = os_path_join(folder, "uploads", private_key)

    return task_vars

# =============================================================================
def setup_run_playbook(playbook, hosts, tags=None, private_key=None):
    """
        Run an Ansible Playbook & return the result
        - designed to be run as a Scheduled Task
            - 'deploy' a deployment
            - 'apply' a setting
            - 'start' an instance
            - 'stop' an instance
            @ToDo: Clean an instance, Upgrade an Instance

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

    # Broken with Ansible 2.8
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
                            # Not supported in Ansible 2.8
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
def setup_instance_settings_read(instance_id, deployment_id):
    """
        Read the Settings for an instance from models/000_config.py
        - called onaccept from instance creation
        - called by interactive method to read
    """

    from gluon.cfs import getcfs
    from gluon.compileapp import build_environment
    from gluon.globals import Request, Response, Session
    from gluon.restricted import restricted

    # Read current settings from file
    folder = current.request.folder
    model = "%s/models/000_config.py" % folder
    code = getcfs(model, model, None)
    request = Request({})
    request.controller = "dontrunany"
    request.folder = folder
    response = Response()
    session = Session()
    #session.connect(request, response)
    environment = build_environment(request, response, session, store_current=False)
    environment["settings"] = Storage2()
    restricted(code, environment, layer=model)
    nested_settings = environment["settings"]

    # Flatten settings
    file_settings = {}
    for section in nested_settings:
        if section == "database":
            # Filter out DB settings as these need special handling
            continue
        subsection = nested_settings[section]
        for setting in subsection:
            if setting in ("hmac_key", "template"):
                # Filter out settings which need special handling
                continue
            file_settings["%s.%s" % (section, setting)] = subsection[setting]

    # Read Settings currently in Database
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
    from gluon.serializers import json as jsons # Need support for T()
    for setting in file_settings:
        current_value = file_settings[setting]
        if not isinstance(current_value, basestring):
            # NB Storage & OrderedDict will come out as dict
            current_value = jsons(current_value)
        s = db_get(setting)
        if s:
            # We update even if not changed so as to update modified_on
            db(id_field == s["id"]).update(current_value = current_value)
        else:
            stable.insert(deployment_id = deployment_id,
                          instance_id = instance_id,
                          setting = setting,
                          current_value = current_value,
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

# =============================================================================
def setup_instance_method(instance_id, method="start"):
    """
        Run individual Ansible Roles ('methods')
            e.g. Start, Stop or Clean an Instance
            - called by interactive method to start/stop
    """

    # Read Data
    db = current.db
    s3db = current.s3db
    itable = s3db.setup_instance
    instance = db(itable.id == instance_id).select(itable.deployment_id,
                                                   itable.type,
                                                   limitby = (0, 1)
                                                   ).first()

    deployment_id = instance.deployment_id

    # Get Server(s) details
    stable = s3db.setup_server
    query = (stable.deployment_id == deployment_id) & \
            (stable.role == 1)
    server = db(query).select(stable.host_ip,
                              stable.private_key,
                              stable.remote_user,
                              limitby = (0, 1)
                              ).first()
    host = server.host_ip

    # Get Deployment details
    dtable = s3db.setup_deployment
    deployment = db(dtable.id == deployment_id).select(dtable.db_type,
                                                       dtable.webserver_type,
                                                       limitby=(0, 1)
                                                       ).first()

    # Build Playbook data structure
    roles_path = os.path.join(current.request.folder, "private", "eden_deploy", "roles")

    playbook = [{"hosts": host,
                 "connection": "local", # @ToDo: Don't assume this
                 "remote_user": server.remote_user,
                 "become_method": "sudo",
                 "become_user": "root",
                 "vars": {"db_type": DB_SERVERS[deployment.db_type],
                          "web_server": WEB_SERVERS[deployment.webserver_type],
                          "type": INSTANCE_TYPES[instance.type],
                          },
                 "roles": [{ "role": "%s/%s" % (roles_path, method) },
                           ]
                 },
                ]

    # Write Playbook
    name = "%s_%d" % (method, int(time.time()))
    task_vars = setup_write_playbook("%s.yml" % name,
                                     playbook,
                                     [host],
                                     tags = None,
                                     private_key = server.private_key,
                                     )

    # Run the Playbook
    current.s3task.schedule_task(name,
                                 vars = task_vars,
                                 function_name = "setup_run_playbook",
                                 repeats = None,
                                 timeout = 6000,
                                 #sync_output = 300
                                 )

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

# =============================================================================
class setup_DeploymentRepresent(S3Represent):

    def __init__(self):
        """
            Constructor
        """

        super(setup_DeploymentRepresent, self).__init__(lookup = "setup_deployment",
                                                        )

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=None):
        """
            Custom look-up of rows

            @param key: the key field
            @param values: the values to look up
            @param fields: unused (retained for API compatibility)
        """

        dtable = self.table
        itable = current.s3db.setup_instance

        count = len(values)
        if count == 1:
            query = (dtable.id == values[0])
        else:
            query = (dtable.id.belongs(values))

        left = itable.on((itable.deployment_id == dtable.id) & (itable.type == 1))
        rows = current.db(query).select(dtable.id,
                                        itable.url,
                                        left = left,
                                        limitby = (0, count),
                                        )
        self.queries += 1
        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a row

            @param row: the Row
        """

        if not hasattr(row, "setup_instance"):
            return str(row.id)

        return row.setup_instance.url

# =============================================================================
def setup_rheader(r, tabs=None):
    """ Resource component page header """

    rheader = None
    if r.representation == "html" and r.id:

        T = current.T
        r_name = r.name

        if r_name == "deployment":
            tabs = [(T("Deployment Details"), None),
                    (T("Servers"), "server"),
                    (T("Instances"), "instance"),
                    (T("Settings"), "setting"),
                    (T("Monitoring"), "monitor_task"),
                    ]

            rheader_tabs = s3_rheader_tabs(r, tabs)

            button = A(T("Configuration Wizard"),
                       _class="action-btn",
                       _href=URL(c="setup", f="deployment",
                                 args=[r.id, "wizard"],
                                 ),
                       )

            rheader = DIV(button,
                          rheader_tabs)

        if r_name == "server":
            tabs = [(T("Server Details"), None),
                    # Inline form instead of Tab
                    #(T("Monitoring"), "monitor_server"),
                    (T("Monitor Tasks"), "monitor_task"),
                    (T("Monitor Logs"), "monitor_log"),
                    ]

            rheader_tabs = s3_rheader_tabs(r, tabs)

            rheader = DIV(rheader_tabs)

        elif r_name == "monitor_check":
            tabs = [(T("Check Details"), None),
                    # @ToDo: Move Inline
                    (T("Options"), "option"),
                    ]
            rheader_tabs = s3_rheader_tabs(r, tabs)

            record = r.record
            table = r.table
            rheader = DIV(TABLE(TR(TH("%s: " % table.name.label),
                                   record.name),
                                TR(TH("%s: " % table.function_name.label),
                                   record.function_name),
                                TR(TH("%s: " % table.comments.label),
                                   record.comments or ""),
                                ), rheader_tabs)

        elif r_name == "monitor_task":
            tabs = [(T("Task Details"), None),
                    # @ToDo: Move Inline
                    (T("Options"), "option"),
                    (T("Logs"), "log"),
                    ]
            rheader_tabs = s3_rheader_tabs(r, tabs)

            record = r.record
            table = r.table
            rheader = DIV(TABLE(TR(TH("%s: " % table.server_id.label),
                                   table.server_id.represent(record.server_id)),
                                TR(TH("%s: " % table.check_id.label),
                                   table.check_id.represent(record.check_id)),
                                TR(TH("%s: " % table.status.label),
                                   table.status.represent(record.status)),
                                TR(TH("%s: " % table.enabled.label),
                                   record.enabled),
                                TR(TH("%s: " % table.comments.label),
                                   record.comments or ""),
                                ), rheader_tabs)

        return rheader

# END =========================================================================
