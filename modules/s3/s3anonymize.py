# -*- coding: utf-8 -*-

""" S3 Person Record Anonymizing

    @copyright: 2018-2020 (c) Sahana Software Foundation
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

import json
from uuid import uuid4

from gluon import current, A, BUTTON, DIV, FORM, INPUT, LABEL, P

from s3dal import original_tablename
from .s3rest import S3Method
from .s3query import FS, S3Joins
from .s3validators import JSONERRORS
from .s3utils import s3_str

__all__ = ("S3Anonymize",
           "S3AnonymizeWidget",
           )

# =============================================================================
class S3Anonymize(S3Method):
    """ REST Method to Anonymize Person Records """

    def apply_method(self, r, **attr):
        """
            Entry point for REST API

            @param r: the S3Request instance
            @param attr: controller parameters

            @return: output data (JSON)
        """

        output = {}

        table, record_id = self.get_target_id()
        if not table:
            r.error(405, "Anonymizing not configured for resource")
        if not record_id:
            r.error(400, "No target record specified")
        if not self.permitted(table, record_id):
            r.unauthorised()

        if r.representation == "json":
            if r.http == "POST":
                output = self.anonymize(r, table, record_id)
            else:
                r.error(405, current.ERROR.BAD_METHOD)
        else:
            r.error(415, current.ERROR.BAD_FORMAT)

        # Set Content Type
        current.response.headers["Content-Type"] = "application/json"

        return output

    # -------------------------------------------------------------------------
    @classmethod
    def anonymize(cls, r, table, record_id):
        """
            Handle POST (anonymize-request), i.e. anonymize the target record

            @param r: the S3Request
            @param table: the target Table
            @param record_id: the target record ID

            @returns: JSON message
        """

        # Read+parse body JSON
        s = r.body
        s.seek(0)
        try:
            options = json.load(s)
        except JSONERRORS:
            options = None
        if not isinstance(options, dict):
            r.error(400, "Invalid request options")

        # Verify submitted action key against session (CSRF protection)
        widget_id = "%s-%s-anonymize" % (table, record_id)
        session_s3 = current.session.s3
        keys = session_s3.anonymize
        if keys is None or \
           widget_id not in keys or \
           options.get("key") != keys[widget_id]:
            r.error(400, "Invalid action key (form reopened in another tab?)")

        # Get the available rules from settings
        rules = current.s3db.get_config(table, "anonymize")
        if isinstance(rules, (tuple, list)):
            names = set(rule.get("name") for rule in rules)
            names.discard(None)
        else:
            # Single rule
            rules["name"] = "default"
            names = (rules["name"],)
            rules = [rules]

        # Get selected rules from options
        selected = options.get("apply")
        if not isinstance(selected, list):
            r.error(400, "Invalid request options")

        # Validate selected rules
        for name in selected:
            if name not in names:
                r.error(400, "Invalid rule: %s" % name)

        # Merge selected rules
        cleanup = {}
        cascade = []
        for rule in rules:
            name = rule.get("name")
            if not name or name not in selected:
                continue
            field_rules = rule.get("fields")
            if field_rules:
                cleanup.update(field_rules)
            cascade_rules = rule.get("cascade")
            if cascade_rules:
                cascade.extend(cascade_rules)

        # Apply selected rules
        if cleanup or cascade:
            rules = {"fields": cleanup, "cascade": cascade}

            # NB will raise (+roll back) if configuration is invalid
            cls.cascade(table, (record_id,), rules)

            # Audit anonymize
            prefix, name = original_tablename(table).split("_", 1)
            current.audit("anonymize", prefix, name,
                          record = record_id,
                          representation = "html",
                          )

            output = current.xml.json_message(updated=record_id)
        else:
            output = current.xml.json_message(msg="No applicable rules found")

        return output

    # -------------------------------------------------------------------------
    def get_target_id(self):
        """
            Determine the target table and record ID

            @return: tuple (table, record_id)
        """

        resource = self.resource

        rules = resource.get_config("anonymize")
        if not rules:
            return None, None

        return resource.table, self.record_id

    # -------------------------------------------------------------------------
    @staticmethod
    def permitted(table, record_id):
        """
            Check permissions to anonymize the target record

            @param table: the target Table
            @param record_id: the target record ID

            @return: True|False
        """

        has_permission = current.auth.s3_has_permission

        return has_permission("update", table, record_id=record_id) and \
               has_permission("delete", table, record_id=record_id)

    # -------------------------------------------------------------------------
    @classmethod
    def cascade(cls, table, record_ids, rules):
        """
            Apply cascade of rules to anonymize records

            @param table: the Table
            @param record_ids: a set of record IDs
            @param rules: the rules for this Table

            @raises Exception: if the cascade failed due to DB constraints
                               or invalid rules; callers should roll back
                               the transaction if an exception is raised
        """

        s3db = current.s3db

        pkey = table._id.name

        cascade = rules.get("cascade")
        if cascade:

            fieldnames = set(rule.get("match", pkey) for _, rule in cascade)
            if pkey not in fieldnames:
                fieldnames.add(pkey)
            fields = [table[fn] for fn in fieldnames]

            db = current.db
            rows = db(table._id.belongs(record_ids)).select(*fields)

            for tablename, rule in cascade:

                lookup = rule.get("lookup")
                if lookup:
                    # Explicit look-up function, call with master table+rows,
                    # as well as the name of the related table; should return
                    # a set/tuple/list of record ids in the related table
                    ids = lookup(table, rows, tablename)
                else:
                    key = rule.get("key")
                    if not key:
                        continue

                    field = rule.get("match", pkey)
                    match = set(row[field] for row in rows)

                    # Resolve key and construct query
                    resource = s3db.resource(tablename, components=[])
                    rq = FS(key).belongs(match)
                    query = rq.query(resource)

                    # Construct necessary joins
                    joins = S3Joins(tablename)
                    joins.extend(rq._joins(resource)[0])
                    joins = joins.as_list()

                    # Extract the target table IDs
                    target_rows = db(query).select(resource._id,
                                                   join = joins,
                                                   )
                    ids = set(row[resource._id.name] for row in target_rows)

                # Recurse into related table
                if ids:
                    cls.cascade(resource.table, ids, rule)

        # Apply field rules
        field_rules = rules.get("fields")
        if field_rules:
            cls.apply_field_rules(table, record_ids, field_rules)

        # Apply deletion rules
        if rules.get("delete"):
            resource = s3db.resource(table, id=list(record_ids))
            resource.delete(cascade=True)

    # -------------------------------------------------------------------------
    @staticmethod
    def apply_field_rules(table, record_ids, rules):
        """
            Apply field rules on a set of records in a table

            @param table: the Table
            @param record_ids: the record IDs
            @param rules: the rules

            @raises Exception: if the field rules could not be applied
                               due to DB constraints or invalid rules;
                               callers should roll back the transaction
                               if an exception is raised
        """

        fields = [table[fn] for fn in rules if fn in table.fields]
        if table._id.name not in rules:
            fields.insert(0, table._id)

        # Select the records
        query = table._id.belongs(record_ids)
        rows = current.db(query).select(*fields)

        pkey = table._id.name

        s3db = current.s3db
        update_super = s3db.update_super
        onaccept = s3db.onaccept

        for row in rows:
            data = {}
            for fieldname, rule in rules.items():

                if fieldname in table.fields:
                    field = table[fieldname]
                else:
                    continue

                if rule == "remove":
                    # Set to None
                    if field.notnull:
                        raise ValueError("Cannot remove %s - must not be NULL" % field)
                    else:
                        data[fieldname] = None

                elif rule == "reset":
                    # Reset to the field's default value
                    default = field.default
                    if default is None and field.notnull:
                        raise ValueError("Cannot reset %s - default value None violates notnull-constraint")
                    data[fieldname] = default

                elif callable(rule):
                    # Callable rule to procude a new value
                    new_value = rule(row[pkey], field, row[field])
                    if fieldname != table._id.name:
                        data[fieldname] = new_value

                elif type(rule) is tuple:
                    method, value = rule
                    if method == "set":
                        # Set a fixed value
                        data[fieldname] = value

            if data:
                success = row.update_record(**data)
                if not success:
                    raise ValueError("Could not clean %s record" % table)

                update_super(table, row)

                data[pkey] = row[pkey]
                onaccept(table, data, method="update")

# =============================================================================
class S3AnonymizeWidget(object):
    """ GUI widget for S3Anonymize """

    # -------------------------------------------------------------------------
    @classmethod
    def widget(cls,
               r,
               _class = "action-lnk",
               label = "Anonymize",
               ajaxURL = None
               ):
        """
            Render an action item (link or button) to anonymize the
            target record of an S3Request, which can be embedded in
            the record view

            @param r: the S3Request
            @param _class: HTML class for the action item
            @param label: The label for the action item
            @param ajaxURL: The URL for the AJAX request

            @returns: the action item (a HTML helper instance), or an empty
                      string if no anonymize-rules are configured for the
                      target table, no target record was specified or the
                      user is not permitted to anonymize it
        """

        T = current.T

        default = ""

        # Determine target table
        if r.component:
            resource = r.component
            if resource.link and not r.actuate_link():
                resource = resource.link
        else:
            resource = r.resource
        table = resource.table

        # Determine target record
        record_id = S3Anonymize._record_id(r)
        if not record_id:
            return default

        # Check if target is configured for anonymize
        rules = resource.get_config("anonymize")
        if not rules:
            return default
        if not isinstance(rules, (tuple, list)):
            # Single rule
            rules["name"] = "default"
            rules = [rules]

        # Check permissions to anonymize
        if not S3Anonymize.permitted(table, record_id):
            return default

        # Determine widget ID
        widget_id = "%s-%s-anonymize" % (table, record_id)

        # Inject script
        if ajaxURL is None:
            ajaxURL = r.url(method = "anonymize",
                            representation = "json",
                            )
        script_options = {"ajaxURL": ajaxURL,
                          }
        cls.inject_script(widget_id, script_options)

        # Action button
        label_T = T(label)
        action_button = A(label_T, _class="anonymize-btn")
        if _class:
            action_button.add_class(_class)

        # Dialog and Form
        INFO = T("The following information will be deleted from the record")
        CONFIRM = T("Are you sure you want to delete the selected details?")
        SUCCESS = T("Action successful - please wait...")

        form = FORM(P("%s:" % INFO),
                    cls.selector(rules),
                    P(CONFIRM),
                    DIV(INPUT(value = "anonymize_confirm",
                              _name = "anonymize_confirm",
                              _type = "checkbox",
                              ),
                    LABEL(T("Yes, delete the selected details")),
                          _class = "anonymize-confirm",
                          ),
                    cls.buttons(),
                    _class = "anonymize-form",
                    # Store action key in form
                    hidden = {"action-key": cls.action_key(widget_id)},
                    )

        dialog = DIV(form,
                     DIV(P(SUCCESS),
                         _class = "hide anonymize-success",
                         ),
                     _class = "anonymize-dialog hide",
                     _title = label_T,
                     )

        # Assemble widget
        widget = DIV(action_button,
                     dialog,
                     _class = "s3-anonymize",
                     _id = widget_id,
                     )

        return widget

    # -------------------------------------------------------------------------
    @staticmethod
    def action_key(widget_id):
        """
            Generate a unique STP token for the widget (CSRF protection) and
            store it in session

            @param widget_id: the widget ID (which includes the target
                              table name and record ID)
            @return: a unique identifier (as string)
        """

        session_s3 = current.session.s3

        keys = session_s3.anonymize
        if keys is None:
            session_s3.anonymize = keys = {}
        key = keys[widget_id] = str(uuid4())

        return key

    # -------------------------------------------------------------------------
    @staticmethod
    def selector(rules):
        """
            Generate the rule selector for anonymize-form

            @param rules: the list of configured rules

            @return: the selector (DIV)
        """

        T = current.T

        selector = DIV(_class="anonymize-select")

        for rule in rules:

            name = rule.get("name")
            if not name:
                continue

            title = T(rule.get("title", name))

            selector.append(DIV(INPUT(value = "on",
                                      _name = s3_str(name),
                                      _type = "checkbox",
                                      _class = "anonymize-rule",
                                      ),
                                LABEL(title),
                                _class = "anonymize-option",
                                ))

        return selector

    # -------------------------------------------------------------------------
    @staticmethod
    def buttons():
        """
            Generate the submit/cancel buttons for the anonymize-form

            @return: the buttons row (DIV)
        """

        T = current.T

        return DIV(BUTTON(T("Submit"),
                          _class = "small alert button anonymize-submit",
                          _disabled = "disabled",
                          _type = "button",
                          ),
                   A(T("Cancel"),
                     _class = "cancel-form-btn action-lnk anonymize-cancel",
                     _href = "javascript:void(0)",
                     ),
                   _class = "anonymize-buttons",
                   )

    # -------------------------------------------------------------------------
    @staticmethod
    def inject_script(widget_id, options):
        """
            Inject the necessary JavaScript for the UI dialog

            @param widget_id: the widget ID
            @param options: JSON-serializable dict of widget options
        """

        request = current.request
        s3 = current.response.s3

        # Static script
        if s3.debug:
            script = "/%s/static/scripts/S3/s3.ui.anonymize.js" % \
                     request.application
        else:
            script = "/%s/static/scripts/S3/s3.ui.anonymize.min.js" % \
                     request.application
        scripts = s3.scripts
        if script not in scripts:
            scripts.append(script)

        # Widget options
        opts = {}
        if options:
            opts.update(options)

        # Widget instantiation
        script = '''$('#%(widget_id)s').anonymize(%(options)s)''' % \
                 {"widget_id": widget_id,
                  "options": json.dumps(opts),
                  }
        jquery_ready = s3.jquery_ready
        if script not in jquery_ready:
            jquery_ready.append(script)

# END =========================================================================
