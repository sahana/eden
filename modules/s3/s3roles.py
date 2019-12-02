# -*- coding: utf-8 -*-

""" S3 User Roles Management

    @copyright: 2018-2019 (c) Sahana Software Foundation
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

__all__ = ("S3RoleManager",
           )

import uuid
import json
#import sys

from gluon import current, URL, DIV, SPAN, SQLFORM, INPUT, A, LI, UL

from s3compat import StringIO, long
from s3dal import Field
from .s3crud import S3CRUD
from .s3rest import S3Method
from .s3query import FS
from .s3utils import s3_str, s3_mark_required
from .s3validators import JSONERRORS
from .s3widgets import s3_comments_widget
from .s3xml import SEPARATORS

# =============================================================================
class S3RoleManager(S3Method):
    """ REST Method to manage user roles and permission rules """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Entry point for REST interface.

            @param r: the S3Request instance
            @param attr: controller attributes
        """

        method = self.method
        tablename = self.tablename

        auth = current.auth
        sr = auth.get_system_roles()

        output = {}

        if tablename == "auth_group": # through admin/role controller

            # Only ADMIN can manipulate roles
            if not auth.s3_has_role(sr.ADMIN):
                r.unauthorised()

            if method == "list":
                output = self.role_list(r, **attr)
            elif method in ("read", "create", "update"):
                output = self.role_form(r, **attr)
            elif method == "copy":
                output = self.copy_role(r, **attr)
            elif method == "delete":
                output = self.delete_role(r, **attr)
            elif method == "users":
                output = self.assign_users(r, **attr)
            elif method == "import":
                output = self.import_roles(r, **attr)
            else:
                r.error(405, current.ERROR.BAD_METHOD)

        elif tablename == "auth_user": # through admin/user controller

            # Must have read-permission for the user record
            # (user accounts are filtered to OU by controller)
            if not self._permitted():
                r.unauthorised()

            if method == "roles":
                output = self.assign_roles(r, **attr)
            else:
                r.error(405, current.ERROR.BAD_METHOD)

        # TODO implement per-target perspective
        #elif tablename == "s3_permission": # through admin/permissions controller
        #
        #    # View permissions for a target (page or table)
        #    r.error(501, current.ERROR.NOT_IMPLEMENTED)

        else:
            r.error(401, current.ERROR.BAD_REQUEST)

        return output

    # -------------------------------------------------------------------------
    def role_list(self, r, **attr):
        """
            List or export roles

            @param r: the S3Request instance
            @param attr: controller attributes

            NB this function must be restricted to ADMINs (in apply_method)
        """

        # Check permission to read in this table
        authorised = self._permitted()
        if not authorised:
            r.unauthorised()

        # Validate requested format
        representation = r.representation
        if representation == "csv":
            return self.export_roles(r, **attr)

        T = current.T
        response = current.response
        s3 = response.s3

        get_vars = self.request.get_vars

        # List Config
        list_id = "roles"
        list_fields = ["id",
                       "role",
                       (T("UID"), "uuid"),
                       "description",
                       ]
        default_orderby = "auth_group.role"
        s3.no_formats = True

        # Exclude hidden roles
        resource = self.resource
        resource.add_filter(FS("hidden") == False)

        if r.interactive:

            # Formkey for Ajax-actions
            formkey = str(uuid.uuid4())
            current.session["_formkey[admin/rolelist]"] = formkey

            # Pagination
            display_length = s3.dataTable_pageLength or 25
            start = None
            if s3.no_sspag:
                dt_pagination = "false"
                limit = None
            else:
                dt_pagination = "true"
                limit = 2 * display_length

            # Generate Data Table
            dt, totalrows = resource.datatable(fields = list_fields,
                                               start = start,
                                               limit = limit,
                                               left = [],
                                               orderby = default_orderby,
                                               )

            # Render the Data Table
            datatable = dt.html(totalrows,
                                totalrows,
                                id = list_id,
                                dt_pagination = dt_pagination,
                                dt_pageLength = display_length,
                                dt_base_url = r.url(method="", vars={}),
                                dt_permalink = r.url(),
                                dt_formkey = formkey,
                                )

            # Configure action buttons
            self.role_list_actions(r)

            # View
            response.view = "admin/roles.html"

            # Page actions
            crud_button = S3CRUD.crud_button
            page_actions = DIV(crud_button(T("Create Role"),
                                           _href = r.url(method="create"),
                                           ),
                               # TODO activate when implemented
                               #crud_button(T("Import Roles"),
                               #            _href = r.url(method="import"),
                               #            ),
                               crud_button(T("Export Roles"),
                                           _href = r.url(representation="csv"),
                                           ),
                               )

            # Output
            output = {"title": T("User Roles"),
                      "items": datatable,
                      "page_actions": page_actions,
                      }

        elif representation == "aadata":

            # Page limits
            start, limit = S3CRUD._limits(get_vars)

            # Data Table Filter and Sorting
            searchq, orderby, left = resource.datatable_filter(list_fields,
                                                               get_vars,
                                                               )
            if searchq is not None:
                totalrows = resource.count()
                resource.add_filter(searchq)
            else:
                totalrows = None
            if orderby is None:
                orderby = default_orderby

            # Data Table
            if totalrows != 0:
                dt, displayrows = resource.datatable(fields = list_fields,
                                                     start = start,
                                                     limit = limit,
                                                     left = left,
                                                     orderby = orderby,
                                                     )
            else:
                dt, displayrows = None, 0
            if totalrows is None:
                totalrows = displayrows

            # Echo
            draw = int(get_vars.get("draw", 0))

            # Representation
            if dt is not None:
                output = dt.json(totalrows, displayrows, list_id, draw)
            else:
                output = '{"recordsTotal":%s,' \
                         '"recordsFiltered":0,' \
                         '"dataTable_id":"%s",' \
                         '"draw":%s,' \
                         '"data":[]}' % (totalrows, list_id, draw)

        else:
            r.error(415, current.ERROR.BAD_FORMAT)

        return output

    # -------------------------------------------------------------------------
    def role_list_actions(self, r):
        """
            Configure action buttons for role list

            @param r: the S3Request
        """

        T = current.T
        s3 = current.response.s3
        sr = current.auth.get_system_roles()

        table = self.table

        # Standard actions
        s3.actions = None
        s3.crud_labels.UPDATE = T("Edit")
        S3CRUD.action_buttons(r, editable=True, deletable=False)

        action_button = S3CRUD.action_button

        # Users
        label = T("Users")
        excluded = [str(sr.AUTHENTICATED), str(sr.ANONYMOUS)]
        action_button(label, URL(args=["[id]", "users"]),
                      exclude = excluded,
                      _title = s3_str(T("Assign this role to users")),
                      )
        action_button(label, None,
                      restrict = excluded,
                      _disabled = "disabled",
                      _title = s3_str(T("This role is assigned automatically")),
                      )

        # Copy-button Ajax
        label = T("Copy")
        excluded = [str(sr.ADMIN)]
        action_button(label, None,
                      _ajaxurl = URL(args=["[id]", "copy.json"]),
                      exclude = excluded,
                      _title = s3_str(T("Copy this role to create a new role")),
                      _class = "action-btn copy-role-btn",
                      )
        action_button(label, None,
                      restrict = excluded,
                      _disabled = "disabled",
                      _title = s3_str(T("This role cannot be copied")),
                      )
        question = T("Create a copy of this role?")
        script = '''var dt=$('#roles');dt.on('click','.copy-role-btn',dt.dataTableS3('ajaxAction','%s'));''' % question
        s3.jquery_ready.append(script)

        # Delete-button Ajax
        label = T("Delete")
        query = (table.deleted == False) & \
                ((table.system == True) | (table.protected == True))
        protected_roles = current.db(query).select(table.id)
        excluded = [str(role.id) for role in protected_roles]
        action_button(label, None,
                      _ajaxurl = URL(args=["[id]", "delete.json"]),
                      _class = "delete-btn-ajax action-btn dt-ajax-delete",
                      exclude = excluded,
                      )
        action_button(label, None,
                      restrict = excluded,
                      _disabled = "disabled",
                      _title = s3_str(T("This role cannot be deleted")),
                      )

    # -------------------------------------------------------------------------
    def role_form(self, r, **attr):
        """
            Create, read, update a role

            NB this function must be restricted to ADMINs (in apply_method)
        """

        T = current.T

        s3 = current.response.s3
        settings = current.deployment_settings

        output = {}

        method = r.method
        record = r.record

        # Read-only?
        readonly = False
        if r.record:
            if r.interactive:
                readonly = method == "read"
            elif r.representation == "csv":
                return self.export_roles(r, **attr)
            else:
                r.error(415, current.ERROR.BAD_FORMAT)

        # Form fields
        table = r.table

        # UID
        uid = table.uuid
        uid.label = T("UID")
        uid.readable = True
        uid.writable = False if record and record.system else True

        # Role name
        role = table.role
        role.label = T("Name")

        # Role description
        description = table.description
        description.label = T("Description")
        description.widget = s3_comments_widget

        # Permissions
        PERMISSIONS = T("Permissions")
        permissions = Field("permissions",
                            label = PERMISSIONS,
                            widget = S3PermissionWidget(r.id),
                            )
        if record and record.uuid == "ADMIN":
            # Administrator permissions cannot be edited
            permissions.readable = permissions.writable = False
        elif not current.auth.permission.use_cacls:
            # Security policy does not use configurable permissions
            if record:
                record.permissions = None
            permissions.widget = self.policy_hint
        elif readonly:
            # Read-only view (dummy) - just hide permissions
            permissions.readable = permissions.writable = False
        elif record:
            # Populate the field with current permissions
            record.permissions = self.get_permissions(record)

        # Mark required
        if not readonly:
            labels, s3.has_required = s3_mark_required(table, [])
            labels["permissions"] = "%s:" % s3_str(PERMISSIONS)
        else:
            labels = None

        # Form buttons
        if not readonly:
            submit_button = INPUT(_class = "small primary button",
                                  _type = "submit",
                                  _value = T("Save"),
                                  )
            cancel_button = A(T("Cancel"),
                              _class="cancel-form-btn action-lnk",
                              _href = r.url(id=""),
                              )
            buttons = [submit_button, cancel_button]
        else:
            buttons = ["submit"]

        # Form style
        crudopts = s3.crud
        formstyle = crudopts.formstyle_read if readonly else crudopts.formstyle

        # Render form
        tablename = "auth_group"
        form = SQLFORM.factory(uid,
                               role,
                               description,
                               permissions,
                               record = record,
                               showid = False,
                               labels = labels,
                               formstyle = formstyle,
                               table_name = tablename,
                               upload = s3.download_url,
                               readonly = readonly,
                               separator = "",
                               submit_button = settings.submit_button,
                               buttons = buttons,
                               )
        form.add_class("rm-form")
        output["form"] = form

        # Navigate-away confirmation
        if crudopts.navigate_away_confirm:
            s3.jquery_ready.append("S3EnableNavigateAwayConfirm()")

        # Process form
        response = current.response
        formname = "%s/%s" % (tablename, record.id if record else None)
        if form.accepts(current.request.post_vars,
                        current.session,
                        #onvalidation = self.validate,
                        formname = formname,
                        keepvalues = False,
                        hideerror = False,
                        ):
            role_id, message = self.update_role(record, form)
            if role_id:
                response.confirmation = message
                self.next = r.url(id="", method="")
            else:
                response.error = message

        elif form.errors:
            response.error = T("There are errors in the form, please check your input")

        # Title
        if record:
            if readonly:
                output["title"] = record.role
            else:
                output["title"] = T("Edit Role: %(role)s") % {"role": record.role}
        else:
            output["title"] = T("Create Role")

        # View
        response.view = "admin/role_form.html"

        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def policy_hint(field, value, **attr):
        """
            Show a hint if permissions cannot be edited due to security policy

            @param field: the Field instance
            @param value: the current field value (ignored)
            @param attr: DOM attributes for the widget (ignored)
        """

        T = current.T

        warn = T("The current system configuration uses hard-coded access rules (security policy %(policy)s).") % \
                {"policy": current.deployment_settings.get_security_policy()}
        hint = T("Change to security policy 3 or higher if you want to define permissions for roles.")

        return DIV(SPAN(warn, _class="rm-fixed"),
                   SPAN(hint, _class="rm-hint"),
                   INPUT(_type = "hidden",
                         _name = field.name,
                         _value= "",
                         ),
                   )

    # -------------------------------------------------------------------------
    @staticmethod
    def get_permissions(role):
        """
            Extract the permission rules for a role

            @param role: the role (Row)

            @returns: the permission rules as JSON string
        """

        permissions = current.auth.permission

        rules = []

        table = permissions.table
        if table:
            query = (table.group_id == role.id) & \
                    (table.deleted == False)

            if not permissions.use_facls:
                query &= (table.function == None)
            if not permissions.use_tacls:
                query &= (table.tablename == None)

            rows = current.db(query).select(table.id,
                                            table.controller,
                                            table.function,
                                            table.tablename,
                                            table.uacl,
                                            table.oacl,
                                            table.entity,
                                            table.unrestricted,
                                            )

            for row in rows:
                if row.unrestricted:
                    entity = "any"
                else:
                    entity = row.entity
                rules.append([row.id,
                              row.controller,
                              row.function,
                              row.tablename,
                              row.uacl,
                              row.oacl,
                              entity,
                              False, # delete-flag
                              ])

        return json.dumps(rules, separators=SEPARATORS)

    # -------------------------------------------------------------------------
    def update_role(self, role, form):
        """
            Create or update a role from a role form

            @param role: the role (Row)
            @param form: the form

            @returns: tuple (role ID, confirmation message)
        """

        T = current.T
        auth = current.auth

        formvars = form.vars
        rolename = formvars.role

        uid = formvars.uuid
        if role:
            role_id = role.id
            data = {"role": rolename,
                    "description": formvars.description,
                    }
            if uid is not None:
                data["uuid"] = uid
            role.update_record(**data)
        else:
            data = {"role": rolename}
            role_id = auth.s3_create_role(rolename,
                                          description = formvars.description,
                                          uid = uid,
                                          )

        if role_id:
            # Update permissions
            permissions = formvars.permissions
            if permissions:
                self.update_permissions(role_id, permissions)
            if not role:
                message = T("Role %(role)s created") % data
            else:
                message = T("Role %(role)s updated") % data
        else:
            if not role:
                message = T("Failed to create role %(role)s") % data
            else:
                message = T("Failed to update role %(role)s") % data

        return role_id, message

    # -------------------------------------------------------------------------
    @staticmethod
    def update_permissions(role_id, rules):
        """
            Update the permission rules for a role

            @param role_id: the role record ID (auth_group.id)
            @param rules: the rules as JSON string
        """

        table = current.auth.permission.table
        if table:

            db = current.db

            rules = json.loads(rules)
            for rule in rules:

                rule_id = rule[0]
                deleted = rule[7]

                if rule_id is None:
                    continue
                if not any(rule[i] for i in (1, 2, 3)):
                    continue

                if rule_id and deleted:
                    db(table.id == rule_id).update(deleted=True)

                else:
                    entity = rule[6]
                    if entity == "any":
                        unrestricted = True
                        entity = None
                    else:
                        unrestricted = False
                        try:
                            entity = long(entity) if entity else None
                        except (ValueError, TypeError):
                            entity = None

                    data = {"group_id": role_id,
                            "controller": rule[1],
                            "function": rule[2],
                            "tablename": rule[3],
                            "uacl": rule[4],
                            "oacl": rule[5],
                            "entity": entity,
                            "unrestricted": unrestricted,
                            }

                    if rule_id:
                        # Update the rule
                        db(table.id == rule_id).update(**data)
                    else:
                        # Add the rule
                        table.insert(**data)

    # -------------------------------------------------------------------------
    @staticmethod
    def copy_role(r, **attr):
        """
            Duplicate an existing role

            NB this function must be restricted to ADMINs (in apply_method)
        """

        # CSRF Protection
        key = current.session["_formkey[admin/rolelist]"]
        if not key or r.post_vars.get("_formkey") != key:
            r.error(403, current.ERROR.NOT_PERMITTED)
        elif r.http != "POST":
            r.error(405, current.ERROR.BAD_METHOD)

        db = current.db

        role = r.record
        if not role:
            r.error(400, current.ERROR.BAD_RECORD)

        # Find a suitable uuid and name
        table = r.table
        query = ((table.uuid.like("%s%%" % role.uuid)) | \
                 (table.role.like("%s%%" % role.role)))
        rows = db(query).select(table.uuid,
                                table.role,
                                )
        uids = set(row.uuid for row in rows)
        names = set(row.role for row in rows)
        uid = name = None
        for i in range(2, 1000):
            if not uid:
                uid = "%s%s" % (role.uuid, i)
                if uid in uids:
                    uid = None
            if not name:
                name = "%s-%s" % (role.role, i)
                if name in names:
                    name = None
            if uid and name:
                break
        if not uid:
            uid = str(uuid.uuid4())
        if not name:
            name = str(uuid.uuid4())

        # Create the new role
        role_id = table.insert(uuid = uid,
                               role = name,
                               )

        # Copy permissions
        ptable = current.auth.permission.table
        if ptable:
            query = (ptable.group_id == role.id) & \
                    (ptable.deleted == False)
            rules = db(query).select(ptable.controller,
                                     ptable.function,
                                     ptable.tablename,
                                     ptable.record,
                                     ptable.oacl,
                                     ptable.uacl,
                                     ptable.entity,
                                     ptable.unrestricted,
                                     )
            for rule in rules:
                ptable.insert(group_id = role_id,
                              controller = rule.controller,
                              function = rule.function,
                              tablename = rule.tablename,
                              record = rule.record,
                              oacl = rule.oacl,
                              uacl = rule.uacl,
                              entity = rule.entity,
                              unrestricted = rule.unrestricted,
                              )

        message = current.T("New Role %(role)s created") % {"role": name}
        return current.xml.json_message(message=message)

    # -------------------------------------------------------------------------
    @staticmethod
    def delete_role(r, **attr):
        """
            Delete a role

            NB this function must be restricted to ADMINs (in apply_method)
        """

        # CSRF Protection
        key = current.session["_formkey[admin/rolelist]"]
        if not key or r.post_vars.get("_formkey") != key:
            r.error(403, current.ERROR.NOT_PERMITTED)
        elif r.http not in ("POST", "DELETE"):
            r.error(405, current.ERROR.BAD_METHOD)

        role = r.record
        if not role:
            r.error(400, current.ERROR.BAD_RECORD)

        if role.protected or role.system:
            r.error(403, current.ERROR.NOT_PERMITTED)

        auth = current.auth
        auth.s3_delete_role(role.id)
        auth.s3_set_roles()

        message = current.T("Role %(role)s deleted") % {"role": role.role}

        return current.xml.json_message(message=message)

    # -------------------------------------------------------------------------
    def assign_roles(self, r, **attr):
        """
            Assign/unassign roles to a user

            NB this function is accessible for non-ADMINs (e.g. ORG_ADMIN)
        """

        auth = current.auth

        # Require a primary record
        if not r.record:
            r.error(400, current.ERRORS.BAD_RECORD)

        # Require permission to create or delete group memberships
        mtable = auth.settings.table_membership
        permitted = auth.s3_has_permission
        if not permitted("create", mtable) and not permitted("delete", mtable):
            r.unauthorised()

        # Require that the target user record belongs to a managed organisation
        pe_ids = auth.get_managed_orgs()
        if not pe_ids:
            r.unauthorised()
        elif pe_ids is not True:
            otable = current.s3db.org_organisation
            utable = auth.settings.table_user
            query = (utable.id == r.id) & \
                    (otable.id == utable.organisation_id) & \
                    (otable.pe_id.belongs(pe_ids))
            row = current.db(query).select(utable.id, limitby=(0, 1)).first()
            if not row:
                r.unauthorised()

        # Which roles can the current user manage for this user?
        managed_roles = self.get_managed_roles(r.id)

        output = {}

        if r.http == "GET":

            T = current.T

            # Page Title
            userfield = auth.settings.login_userfield
            user_name = r.record[userfield]
            output["title"] = "%s: %s" % (T("Roles of User"), user_name)

            # Should we use realms?
            use_realms = auth.permission.entity_realm
            if use_realms:
                realm_types, realms = self.get_managed_realms()
            else:
                realm_types, realms = None, None

            # The Ajax URL for role updates
            ajax_url = r.url(id="[id]", representation="json")

            # The form field
            field = mtable.user_id
            field.readable = field.writable = True
            field.widget = S3RolesWidget(mode = "roles",
                                         items = managed_roles,
                                         use_realms = use_realms,
                                         realm_types = realm_types,
                                         realms = realms,
                                         ajax_url = ajax_url,
                                         )

            # Render form
            s3 = current.response.s3
            tablename = str(mtable)
            form = SQLFORM.factory(field,
                                   record = {"id": None, "user_id": r.id},
                                   showid = False,
                                   labels = {field.name: ""},
                                   formstyle = s3.crud.formstyle,
                                   table_name = tablename,
                                   upload = s3.download_url,
                                   #readonly = readonly,
                                   separator = "",
                                   submit_button = False,
                                   buttons = [],
                                   )
            form.add_class("rm-form")
            output["form"] = form

            # Show a back-button since OrgAdmins have no other obvious
            # way to return to the list (no left menu)
            crud_button = S3CRUD.crud_button
            output["list_btn"] = crud_button(T("Back to User List"),
                                             icon = "return",
                                             _href = r.url(id="", method=""),
                                             )

            # View
            response = current.response
            response.view = "admin/role_form.html"

        elif r.http == "POST":
            if r.representation == "json":
                # Read+parse body JSON
                s = r.body
                s.seek(0)
                try:
                    options = json.load(s)
                except JSONERRORS:
                    options = None
                if not isinstance(options, dict):
                    r.error(400, "Invalid request options")

                user_id = r.record.id
                added = options.get("add")
                removed = options.get("remove")

                # Validate
                if added:
                    for group_id, pe_id in added:
                        role = managed_roles.get(group_id)
                        if not role or role.get("a") is False:
                            r.error(403, current.ERROR.NOT_PERMITTED)
                if removed:
                    for group_id, pe_id in removed:
                        role = managed_roles.get(group_id)
                        if not role or role.get("r") is False:
                            r.error(403, current.ERROR.NOT_PERMITTED)

                # Update role assignments
                if added:
                    add_role = auth.s3_assign_role
                    for group_id, pe_id in added:
                        add_role(user_id, group_id, for_pe=pe_id)
                if removed:
                    remove_role = auth.s3_withdraw_role
                    for group_id, pe_id in removed:
                        remove_role(user_id, group_id, for_pe=pe_id)

                output = current.xml.json_message(options=options)

            else:
                r.error(415, current.ERROR.BAD_FORMAT)
        else:
            r.error(405, current.ERROR.BAD_METHOD)

        return output

    # -------------------------------------------------------------------------
    def assign_users(self, r, **attr):
        """
            Assign/unassign users to a role

            NB this function could be accessible for non-ADMINs (e.g. ORG_ADMIN)
        """

        auth = current.auth

        # Require a primary record
        role = r.record
        if not role:
            r.error(400, current.ERRORS.BAD_RECORD)

        # Require permission to create or delete group memberships
        mtable = auth.settings.table_membership
        permitted = auth.s3_has_permission
        if not permitted("create", mtable) and not permitted("delete", mtable):
            r.unauthorised()

        # Require that the target role belongs to managed roles
        managed_roles = self.get_managed_roles(None)
        if role.id not in managed_roles:
            r.unauthorised()

        s3 = current.response.s3

        # Which users can the current user manage?
        managed_users = self.get_managed_users(role.id)

        # Special rules for system roles
        sr = auth.get_system_roles()
        unrestrictable = (sr.ADMIN, sr.AUTHENTICATED, sr.ANONYMOUS)
        unassignable = (sr.AUTHENTICATED, sr.ANONYMOUS)

        output = {}

        if r.http == "GET":

            T = current.T

            # Page Title
            output["title"] = "%s: %s" % (T("Users with Role"), role.role)

            # Should we use realms?
            use_realms = auth.permission.entity_realm and \
                         role.id not in unrestrictable
            if use_realms:
                realm_types, realms = self.get_managed_realms()
            else:
                realm_types, realms = None, None

            # The Ajax URL for role updates
            ajax_url = r.url(id="[id]", representation="json")

            # The form field
            field = mtable.group_id
            field.readable = field.writable = True
            field.widget = S3RolesWidget(mode="users",
                                         items = managed_users,
                                         use_realms = use_realms,
                                         realm_types = realm_types,
                                         realms = realms,
                                         ajax_url = ajax_url,
                                         )

            # Render form
            tablename = str(mtable)
            form = SQLFORM.factory(field,
                                   record = {"id": None, "group_id": role.id},
                                   showid = False,
                                   labels = {field.name: ""},
                                   formstyle = s3.crud.formstyle,
                                   table_name = tablename,
                                   upload = s3.download_url,
                                   #readonly = readonly,
                                   separator = "",
                                   submit_button = False,
                                   buttons = [],
                                   )
            form.add_class("rm-form")
            output["form"] = form

            # Default RHeader and View
            if "rheader" not in attr:
                return_btn = S3CRUD.crud_button("Back to Roles List",
                                                icon = "return",
                                                _href=r.url(id="", method=""),
                                                )
                output["rheader"] = DIV(return_btn,
                                        _class="rheader",
                                        )

            response = current.response
            response.view = "admin/role_form.html"

        elif r.http == "POST":
            if r.representation == "json":
                # Process Ajax-request from S3RolesWidget

                # Read+parse body JSON
                s = r.body
                s.seek(0)
                try:
                    options = json.load(s)
                except JSONERRORS:
                    options = None
                if not isinstance(options, dict):
                    r.error(400, "Invalid request options")

                added = options.get("add")
                removed = options.get("remove")

                # Validate
                group_id = role.id
                if group_id in unassignable:
                    r.error(403, current.ERROR.NOT_PERMITTED)
                if added:
                    for user_id, pe_id in added:
                        user = managed_users.get(user_id)
                        if not user or user.get("a") is False:
                            r.error(403, current.ERROR.NOT_PERMITTED)
                if removed:
                    for user_id, pe_id in removed:
                        user = managed_users.get(user_id)
                        if not user or user.get("r") is False:
                            r.error(403, current.ERROR.NOT_PERMITTED)

                # Update role assignments
                if added:
                    add_role = auth.s3_assign_role
                    for user_id, pe_id in added:
                        add_role(user_id, group_id, for_pe=pe_id)
                if removed:
                    remove_role = auth.s3_withdraw_role
                    for user_id, pe_id in removed:
                        remove_role(user_id, group_id, for_pe=pe_id)

                output = current.xml.json_message(options=options)

            else:
                r.error(415, current.ERROR.BAD_FORMAT)
        else:
            r.error(405, current.ERROR.BAD_METHOD)

        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def get_managed_users(role_id):
        """
            Get a dict of users the current user can assign to roles

            @param role_id: the target role ID

            @returns: a dict {user_id: {l:label,
                                        t:title,
                                        a:assignable,
                                        r:removable,
                                        u:unrestrictable,
                                        }, ...}
                      NB a, r and u attributes only added if non-default
        """

        auth = current.auth
        auth_settings = auth.settings

        sr = auth.get_system_roles()
        admin_role = role_id == sr.ADMIN
        unassignable = role_id in (sr.AUTHENTICATED, sr.ANONYMOUS)
        unrestrictable = role_id in (sr.ADMIN, sr.AUTHENTICATED, sr.ANONYMOUS)

        current_user = auth.user.id if auth.user else None

        users = {}

        pe_ids = auth.get_managed_orgs()
        if pe_ids:
            utable = auth_settings.table_user
            query = (utable.deleted == False)

            if pe_ids is not True:
                otable = current.s3db.org_organisation
                query &= (otable.id == utable.organisation_id) & \
                         (otable.pe_id.belongs(pe_ids))

            userfield = auth_settings.login_userfield

            rows = current.db(query).select(utable.id,
                                            utable.first_name,
                                            utable.last_name,
                                            utable[userfield],
                                            )
            for row in rows:

                user_id = row.id
                user = {"l": row[userfield],
                        "t": "%s %s" % (row.first_name,
                                        row.last_name,
                                        ),
                        }

                if unrestrictable:
                    user["u"] = True
                if admin_role and user_id == current_user:
                    # ADMINs cannot remove their own ADMIN role
                    user["r"] = False
                if unassignable:
                    user["a"] = user["r"] = False

                users[user_id] =  user

        return users

    # -------------------------------------------------------------------------
    @staticmethod
    def get_managed_roles(user_id):
        """
            Get a dict of roles the current user can manage

            @returns: a dict {role_id: {l:label,
                                        a:assignable,
                                        r:removable,
                                        u:unrestrictable,
                                        }, ...},
                      NB a, r and u attributes only added if non-default
        """

        auth = current.auth
        sr = auth.get_system_roles()

        AUTO = (sr.AUTHENTICATED, sr.ANONYMOUS)
        ADMINS = (sr.ADMIN, sr.ORG_ADMIN, sr.ORG_GROUP_ADMIN)
        UNRESTRICTABLE = (sr.ADMIN, sr.AUTHENTICATED, sr.ANONYMOUS)


        table = auth.settings.table_group
        query = (table.hidden == False) & \
                (table.deleted == False)
        rows = current.db(query).select(table.id,
                                        table.uuid,
                                        table.role,
                                        )

        has_role = auth.s3_has_role

        roles = {}
        for row in rows:

            role = {"l": row.role or row.uuid}

            role_id = row.id

            if role_id in ADMINS:
                assignable = has_role(role_id)
            else:
                assignable = role_id not in AUTO

            if role_id == sr.ADMIN and auth.user.id == user_id:
                removable = False
            else:
                removable = assignable

            if not assignable:
                role["a"] = False
            if not removable:
                role["r"] = False
            if role_id in UNRESTRICTABLE:
                role["u"] = True

            roles[role_id] = role

        return roles

    # -------------------------------------------------------------------------
    @staticmethod
    def get_managed_realms():
        """
            Get a dict of realms managed by the current user

            @returns: tuple (realm_types, realms):
                        - realm_types = [(instance_type, label), ...]
                        - realms = {pe_id: {l:label, t:type}, ...}
        """

        T = current.T
        t_ = lambda v: s3_str(T(v))

        realm_types = [(None, t_("Multiple"))]
        realms = {None: {"l": t_("Default Realm"), "t": None},
                  }

        # Look up the realms managed by the current user
        pe_ids = []

        auth = current.auth
        sr = auth.get_system_roles()
        has_role = auth.s3_has_role

        is_admin = has_role(sr.ADMIN)
        if is_admin:
            # Only ADMIN can assign roles site-wide
            realms[0] = {"l": t_("All Entities"), "t": None}
        else:
            if has_role(sr.ORG_GROUP_ADMIN):
                role_realms = auth.user.realms[sr.ORG_GROUP_ADMIN]
                if role_realms:
                    pe_ids.extend(role_realms)
            if has_role(sr.ORG_ADMIN):
                role_realms = auth.user.realms[sr.ORG_ADMIN]
                if role_realms:
                    pe_ids.extend(role_realms)

        # Get entities and types
        s3db = current.s3db
        types = current.deployment_settings.get_auth_realm_entity_types()
        entities = s3db.pr_get_entities(pe_ids = pe_ids,
                                        types = types,
                                        group = True,
                                        show_instance_type = False,
                                        )

        # Add representations for entities and types
        instance_type_nice = s3db.pr_pentity.instance_type.represent
        for instance_type in types:
            entity_group = entities.get(instance_type)
            if not entity_group:
                continue
            realm_types.append((instance_type,
                                s3_str(instance_type_nice(instance_type)),
                                ))
            for pe_id, name in entity_group.items():
                realms[pe_id] = {"l": s3_str(name), "t": instance_type}

        return realm_types, realms

    # -------------------------------------------------------------------------
    def import_roles(self, r, **attr):
        """
            Interactive import of roles (auth_roles.csv format)

            NB this function must be restricted to ADMINs (in apply_method)
        """

        # TODO implement roles importer

        T = current.T

        output = {}

        # Title
        output["title"] = T("Import Roles")

        # View
        response = current.response
        response.view = "admin/import_roles.html"

        return output

        # if GET:
        #   show an import form
        # elif POST:
        #   import the submitted file using Bulk-importer

    # -------------------------------------------------------------------------
    @staticmethod
    def export_roles(r, **attr):
        """
            Export of roles (auth_roles.csv format)

            NB this function must be restricted to ADMINs (in apply_method)
        """

        output = S3RolesExport(r.resource).as_csv()

        # Response headers
        from gluon.contenttype import contenttype

        filename = "auth_roles.csv"
        disposition = "attachment; filename=\"%s\"" % filename

        response = current.response
        response.headers["Content-Type"] = contenttype(".csv")
        response.headers["Content-disposition"] = disposition

        return output.read()

# =============================================================================
class S3PermissionWidget(object):
    """
        Form widget to modify permissions of a role
    """

    def __init__(self, role_id=None):
        """
            Constructor
        """

        sr = current.auth.get_system_roles()

        if role_id == sr.ANONYMOUS:
            default_roles = ()
        elif role_id == sr.AUTHENTICATED:
            default_roles = (sr.ANONYMOUS,)
        else:
            default_roles = (sr.ANONYMOUS, sr.AUTHENTICATED)

        self.default_roles = default_roles

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):
        """
            Form builder entry point

            @param field: the Field
            @param value: the current (or default) value of the field
            @param attributes: HTML attributes for the widget
        """

        T = current.T

        # Widget ID
        widget_id = attributes.get("_id") or str(field).replace(".", "_")

        # Field name
        name = attributes.get("_name") or field.name

        # Page access rules tab+pane
        prules_id = "%s-prules" % widget_id
        prules_tab = LI(A(T("Page Access"),
                          _href = "#" + prules_id,
                          )
                        )
        prules_pane = DIV(_id = prules_id,
                          _class = "rm-page-rules",
                          )

        # Table access rules tab+page
        rules = current.auth.permission
        use_tacls = rules.use_tacls
        if use_tacls:
            trules_id = "%s-trules" % widget_id
            trules_tab = LI(A(T("Table Access"),
                              _href = "#" + trules_id,
                              ),
                            )
            trules_pane = DIV(_id = trules_id,
                              _class = "rm-table-rules",
                              )
        else:
            trules_pane = ""
            trules_tab = ""

        # Construct the widget
        widget = DIV(INPUT(_type = "hidden",
                           _name = name,
                           _value = value,
                           _id = widget_id + "-input",
                           ),
                     DIV(UL(trules_tab,
                            prules_tab,
                            ),
                         trules_pane,
                         prules_pane,
                         _class = "rm-rules hide"
                         ),
                     _id = widget_id,
                     )

        # Module header icons
        rtl = current.response.s3.rtl
        icons = {"expanded": "fa fa-caret-down",
                 "collapsed": "fa fa-caret-left" if rtl else "fa fa-caret-right",
                 }

        # Client-side widget options
        widget_opts = {"fRules": rules.use_facls,
                       "tRules": use_tacls,
                       "useRealms": rules.entity_realm,
                       "permissions": self.get_permissions(),
                       "defaultPermissions": self.get_default_permissions(),
                       "modules": self.get_active_modules(),
                       "icons": icons,
                       }

        if use_tacls:
            widget_opts["models"] = self.get_active_models()

        # Localized strings for client-side widget
        i18n = {"rm_Add": T("Add"),
                "rm_AddRule": T("Add Rule"),
                "rm_AllEntities": T("All Entities"),
                "rm_AllRecords": T("All Records"),
                "rm_AssignedEntities": T("Assigned Entities"),
                "rm_Cancel": T("Cancel"),
                "rm_CollapseAll": T("Collapse All"),
                "rm_ConfirmDeleteRule": T("Do you want to delete this rule?"),
                "rm_Default": T("default"),
                "rm_DeleteRule": T("Delete"),
                "rm_ExpandAll": T("Expand All"),
                "rm_NoAccess": T("No access"),
                "rm_NoRestrictions": T("No restrictions"),
                "rm_Others": T("Others"),
                "rm_OwnedRecords": T("Owned Records"),
                "rm_Page": T("Page"),
                "rm_RestrictedTables": T("Restricted Tables"),
                "rm_Scope": T("Scope"),
                "rm_SystemTables": T("System Tables"),
                "rm_Table": T("Table"),
                "rm_UnrestrictedTables": T("Unrestricted Tables"),
                }

        # Inject the client-side script
        self.inject_script(widget_id, widget_opts, i18n)

        return widget

    # -------------------------------------------------------------------------
    @staticmethod
    def get_active_modules():
        """
            Get a JSON-serializable dict of active modules

            @returns: a dict {prefix: (name_nice, restricted)}
        """

        # Modules where access rules do not apply (or are hard-coded)
        exclude = ("appadmin", "errors")

        # Active modules
        modules = current.deployment_settings.modules
        active= {k: (s3_str(modules[k].name_nice), modules[k].restricted)
                 for k in modules if k not in exclude
                 }

        # Special controllers for dynamic models
        if current.auth.permission.use_facls:
            active["default/dt"] = (s3_str(current.T("Dynamic Models")), True)

        return active

    # -------------------------------------------------------------------------
    def get_active_models(self):
        """
            Get a JSON-serializable dict of active data models

            @returns: a dict {prefix: {tablename: restricted}}
        """

        # Get all table names
        db_tables = current.cache.ram("permission_widget_all_tables",
                                      self.get_db_tables,
                                      time_expire = 14400,
                                      )

        # Count the number of restricting roles per table
        # @see: S3Permission.table_restricted()
        rtable = current.auth.permission.table
        query = (rtable.tablename != None) & \
                (rtable.controller == None) & \
                (rtable.function == None) & \
                (rtable.deleted == False)
        numroles = rtable.group_id.count()
        tablename = rtable.tablename
        rows = current.db(query).select(tablename,
                                        numroles,
                                        groupby = tablename,
                                        )
        restrictions = {row[tablename]: row[numroles] for row in rows}

        # Sort tablenames after module and mark number of restrictions
        models = {}
        for tablename in db_tables:

            prefix = tablename.split("_", 1)[0]

            if prefix in ("auth", "sync", "s3", "scheduler"):
                prefix = "_system"

            if prefix not in models:
                models[prefix] = {}

            models[prefix][tablename] = restrictions.get(tablename, 0)

        return models

    # -------------------------------------------------------------------------
    @staticmethod
    def get_db_tables():
        """
            Return all table names in the database; in separate function
            to allow caching because it requires to load all models once

            @returns: db.tables
        """

        db = current.db
        s3db = current.s3db

        # Load all static models
        s3db.load_all_models()

        # Load all dynamic tables (TODO: how does this make sense?)
        #ttable = s3db.s3_table
        #rows = db(ttable.deleted != True).select(ttable.name)
        #for row in rows:
        #    s3db.table(row.name)

        return db.tables

    # -------------------------------------------------------------------------
    @staticmethod
    def get_permissions():
        """
            Get a JSON-serializable list of permissions

            @returns: an ordered list of dicts:
                     [{l: label,
                       b: bit,
                       o: relevant for owned records,
                       },
                       ...
                       ]
        """

        permission = current.auth.permission

        opts = permission.PERMISSION_OPTS
        skip = 0x0000

        # Hide approval-related permissions if record approval is disabled
        if not current.deployment_settings.get_auth_record_approval():
            skip |= permission.REVIEW | permission.APPROVE

        output = []
        for bit, label in opts.items():

            if bit & skip:
                continue

            output.append({"l": s3_str(label),
                           "b": bit,
                           "o": bit != permission.CREATE,
                           })
        return output

    # -------------------------------------------------------------------------
    def get_default_permissions(self):
        """
            Get default permissions, i.e. those granted by roles the user
            has by default

            @returns: a dict {tablename: (uACL, oACL)}
        """

        permissions = current.auth.permission
        table = permissions.table

        default_roles = self.default_roles
        default_permissions = {}

        if table and default_roles:
            query = (table.group_id.belongs(default_roles))
            if not permissions.use_facls:
                query &= (table.function == None)
            if not permissions.use_tacls:
                query &= (table.tablename == None)
            query &= (table.deleted == False)
            rows = current.db(query).select(table.controller,
                                            table.function,
                                            table.tablename,
                                            table.uacl,
                                            table.oacl,
                                            )
            for row in rows:
                target = row.tablename
                if not target:
                    c = row.controller
                    if c:
                        target = "%s/%s" % (c, row.function or "*")
                    else:
                        continue
                rules = default_permissions.get(target)
                if rules:
                    default_permissions[target] = (rules[0] | row.uacl,
                                                   rules[1] | row.oacl,
                                                   )
                else:
                    default_permissions[target] = (row.uacl, row.oacl)

        return default_permissions

    # -------------------------------------------------------------------------
    def inject_script(self, widget_id, options, i18n):
        """
            Inject the necessary JavaScript for the widget

            @param widget_id: the widget ID
                              (=element ID of the person_id field)
            @param options: JSON-serializable dict of widget options
            @param i18n: translations of screen messages rendered by
                         the client-side script,
                         a dict {messageKey: translation}
        """

        s3 = current.response.s3

        # Static script
        if s3.debug:
            script = "/%s/static/scripts/S3/s3.ui.permissions.js" % \
                     current.request.application
        else:
            script = "/%s/static/scripts/S3/s3.ui.permissions.min.js" % \
                     current.request.application
        scripts = s3.scripts
        if script not in scripts:
            scripts.append(script)
            self.inject_i18n(i18n)

        # Widget options
        opts = {}
        if options:
            opts.update(options)

        # Widget instantiation
        script = '''$('#%(widget_id)s').permissionEdit(%(options)s)''' % \
                 {"widget_id": widget_id,
                  "options": json.dumps(opts, separators=SEPARATORS),
                  }
        jquery_ready = s3.jquery_ready
        if script not in jquery_ready:
            jquery_ready.append(script)

    # -------------------------------------------------------------------------
    @staticmethod
    def inject_i18n(labels):
        """
            Inject translations for screen messages rendered by the
            client-side script

            @param labels: dict of translations {messageKey: translation}
        """

        strings = ['''i18n.%s="%s"''' % (k, s3_str(v))
                                        for k, v in labels.items()]
        current.response.s3.js_global.append("\n".join(strings))

# =============================================================================
class S3RolesWidget(object):
    """
        Form widget to assign roles to users
    """

    def __init__(self,
                 mode="roles",
                 items=None,
                 use_realms=False,
                 realm_types=None,
                 realms=None,
                 ajax_url=None,
                 ):
        """
            Constructor

            @param mode: what to assign ("roles"|"users")
            @param items: the assignable items (roles or users), dict,
                          structure see get_managed_roles/get_managed_users
            @param use_realms: boolean, whether to use realms
            @param realm_types: the realm types and their labels, tuple,
                                format see get_managed_realms
            @param realms: the realms, dict, structure see get_managed_realms
            @param ajax_url: the URL for Ajax modification of assignments
        """

        self.mode = mode

        self.items = items

        self.use_realms = use_realms
        self.realm_types = realm_types
        self.realms = realms

        self.ajax_url = ajax_url

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):
        """
            Form builder entry point

            @param field: the Field
            @param value: the current (or default) value of the field
            @param attributes: HTML attributes for the widget
        """

        T = current.T

        # Widget ID
        widget_id = attributes.get("_id") or str(field).replace(".", "_")

        # Field name
        name = attributes.get("_name") or field.name

        # Extract the current assignments
        if value:
            assignments = self.get_current_assignments(value)
        else:
            assignments = []

        # Construct the widget
        widget = DIV(INPUT(_type = "hidden",
                           _name = name,
                           _value = value,
                           _id = widget_id + "-id",
                           ),
                     INPUT(_type = "hidden",
                           _name = "assigned",
                           _value = json.dumps(assignments, separators=SEPARATORS),
                           _id = widget_id + "-data",
                           ),
                     _id = widget_id,
                     _class = "rm-assign-widget",
                     )

        # Client-side widget options
        widget_opts = {"mode": self.mode,
                       "ajaxURL": self.ajax_url,
                       "items": self.items,
                       "useRealms": self.use_realms,
                       "realms": self.realms,
                       "realmTypes": self.realm_types,
                       }

        # Localized strings for client-side widget
        if self.mode == "roles":
            CONFIRM = T("Do you want to remove the %(role)s role?")
        else:
            CONFIRM = T("Do you want to remove %(user)s from this role?")
        i18n = {"rm_Add": T("Add"),
                "rm_Cancel": T("Cancel"),
                "rm_ConfirmDeleteAssignment": CONFIRM,
                "rm_Delete": T("Delete"),
                "rm_DeletionFailed": T("Deletion Failed"),
                "rm_ForEntity": T("For Entity"),
                "rm_Roles": T("Roles"),
                "rm_SubmissionFailed": T("Submission Failed"),
                "rm_Users": T("Users"),
                }

        # Inject the client-side script
        self.inject_script(widget_id, widget_opts, i18n)

        return widget

    # -------------------------------------------------------------------------
    def get_current_assignments(self, record_id):
        """
            Get the current assignments for the user/role

            @param record_id: the user or role ID

            @returns: a list of tuples (roleID|userID, realmID)
        """

        auth = current.auth
        table = auth.settings.table_membership

        if self.mode == "roles":
            query = (table.user_id == record_id) & \
                    (table.group_id.belongs(set(self.items.keys())))
            field = table.group_id
        else:
            query = (table.group_id == record_id) & \
                    (table.user_id.belongs(set(self.items.keys())))
            field = table.user_id

        use_realms = self.use_realms
        if use_realms and \
           not auth.s3_has_role(auth.get_system_roles().ADMIN):
            managed_realms = set(self.realms.keys())
            none = None in managed_realms
            managed_realms.discard(None)
            q = (table.pe_id.belongs(managed_realms)) if managed_realms else None
            if none:
                n = (table.pe_id == None)
                q = q | n if q else n
            if q:
                query &= q

        query &= (table.deleted == False)
        rows = current.db(query).select(field, table.pe_id)

        assignments = set()
        for row in rows:
            pe_id = row.pe_id if use_realms else None
            assignments.add((row[field], pe_id))

        return list(assignments)

    # -------------------------------------------------------------------------
    def inject_script(self, widget_id, options, i18n):
        """
            Inject the necessary JavaScript for the widget

            @param widget_id: the widget ID
                              (=element ID of the person_id field)
            @param options: JSON-serializable dict of widget options
            @param i18n: translations of screen messages rendered by
                         the client-side script,
                         a dict {messageKey: translation}
        """

        s3 = current.response.s3

        # Static script
        if s3.debug:
            script = "/%s/static/scripts/S3/s3.ui.roles.js" % \
                     current.request.application
        else:
            script = "/%s/static/scripts/S3/s3.ui.roles.min.js" % \
                     current.request.application
        scripts = s3.scripts
        if script not in scripts:
            scripts.append(script)
            self.inject_i18n(i18n)

        # Widget options
        opts = {}
        if options:
            opts.update(options)

        # Widget instantiation
        script = '''$('#%(widget_id)s').roleManager(%(options)s)''' % \
                 {"widget_id": widget_id,
                  "options": json.dumps(opts, separators=SEPARATORS),
                  }
        jquery_ready = s3.jquery_ready
        if script not in jquery_ready:
            jquery_ready.append(script)

    # -------------------------------------------------------------------------
    @staticmethod
    def inject_i18n(labels):
        """
            Inject translations for screen messages rendered by the
            client-side script

            @param labels: dict of translations {messageKey: translation}
        """

        strings = ['''i18n.%s="%s"''' % (k, s3_str(v))
                                        for k, v in labels.items()]
        current.response.s3.js_global.append("\n".join(strings))

# =============================================================================
class S3RolesExport(object):
    """
        Roles Exporter
    """

    def __init__(self, resource):
        """
            Constructor

            @param resource: the role resource (auth_group) with REST
                             filters; or None to export all groups
        """

        db = current.db
        auth = current.auth

        # Optional columns
        self.col_hidden = False
        self.col_protected = False
        self.col_entity = False

        # Look up the roles
        gtable = auth.settings.table_group
        fields = ("id",
                  "uuid",
                  "role",
                  "description",
                  "hidden",
                  "protected",
                  "system",
                  )
        if resource and resource.tablename == str(gtable):
            roles = resource.select(fields, as_rows=True)
        else:
            query = (gtable.deleted == False)
            roles = db(query).select(*fields)

        # Generate roles dict
        role_dicts = {}
        for role in roles:
            role_dict = {"uid": role.uuid,
                         "role": role.role,
                         "description": role.description,
                         }
            if role.hidden:
                self.col_hidden = True
                role_dict["hidden"] = "true"
            if role.protected and not role.system:
                self.col_protected = True
                role_dict["protected"] = "true"
            role_dicts[role.id] = role_dict
        self.roles = role_dicts

        # Look up all rules, ordered by UID, controller, function, table
        rtable = auth.permission.table
        query = (rtable.group_id.belongs(set(role_dicts.keys()))) & \
                (rtable.deleted == False)
        rules = db(query).select(rtable.id,
                                 rtable.group_id,
                                 rtable.controller,
                                 rtable.function,
                                 rtable.tablename,
                                 rtable.uacl,
                                 rtable.oacl,
                                 rtable.entity,
                                 )
        self.rules = rules

        # Look up all org entities
        entities = set()
        for rule in rules:
            entity = rule.entity
            if entity is not None:
                self.col_entity = True
                entities.add(entity)

        otable = current.s3db.org_organisation
        query = (otable.pe_id.belongs(entities)) & \
                (otable.deleted == False)
        self.orgs = db(query).select(otable.pe_id,
                                     otable.name,
                                     ).as_dict(key="pe_id")

    # -------------------------------------------------------------------------
    def as_csv(self):
        """
            Export the current roles and permissions as CSV,
            suitable for prepop (see S3BulkImporter.import_role)

            @returns: a StringIO containing the CSV
        """

        import csv

        # Optional columns
        col_protected = self.col_protected
        col_hidden = self.col_hidden
        col_entity = self.col_entity

        # Role fields
        fieldnames = ["uid", "role", "description"]
        if col_hidden:
            fieldnames.append("hidden")
        if col_protected:
            fieldnames.append("protected")

        # Rule fields
        fieldnames.extend(["controller", "function", "table", "uacl", "oacl"])
        if col_entity:
            fieldnames.extend("entity")

        # Helper to get the role UID for a rule
        role_dicts = self.roles
        def get_uid(group_id):
            role_dict = role_dicts.get(group_id)
            return role_dict.get("uid") if role_dict else None

        # Sort the rules
        rules = sorted(self.rules,
                       key = lambda rule: (get_uid(rule.group_id),
                                           rule.controller or "zzzzzz",
                                           rule.function or "",
                                           rule.tablename or "",
                                           ))

        # Create the CSV
        f = StringIO()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        # Write the rules to the CSV
        orgs = self.orgs
        encode_permissions = self.encode_permissions
        for rule in rules:

            role_dict = role_dicts.get(rule.group_id)
            if not role_dict:
                continue

            rule_dict = {}

            # The entity column (optional)
            if col_entity:
                entity = rule.entity
                if entity is not None:
                    if entity == 0:
                        rule_dict["entity"] = "any"
                    else:
                        org = orgs.get(entity)
                        if org:
                            rule_dict["entity"] = org
                        else:
                            continue

            # The target columns (controller, function, table)
            if rule.tablename:
                rule_dict["table"] = rule.tablename
            else:
                if rule.controller:
                    rule_dict["controller"] = rule.controller
                if rule.function:
                    rule_dict["function"] = rule.function

            # The permission columns (uacl, oacl)
            uacl = encode_permissions(rule.uacl, explicit_none=True)
            if uacl:
                rule_dict["uacl"] = uacl
            oacl = encode_permissions(rule.oacl & ~(rule.uacl))
            if oacl:
                rule_dict["oacl"] = oacl

            # Add role columns
            rule_dict.update(role_dict)

            # Write the rule
            writer.writerow(rule_dict)

        f.seek(0)
        return f

    # -------------------------------------------------------------------------
    @staticmethod
    def encode_permissions(permissions, explicit_none=False):
        """
            Encodes a permission bitmap as string, using the permission
            labels from S3Permission.PERMISSION_OPTS

            @param permissions: the permission bitmap
            @param explicit_none: return "NONE" if no permission bit set
                                  (otherwise returns None)
        """

        if not permissions:
            if explicit_none:
                return "NONE"
            else:
                return None

        opts = current.auth.permission.PERMISSION_OPTS
        labels = []
        for bit in opts:
            if permissions & bit:
                labels.append(opts[bit])

        return "|".join(labels)

# END =========================================================================
