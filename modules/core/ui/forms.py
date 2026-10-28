"""
    CRUD Forms with built-in Database I/O

    Copyright: 2012-2023 (c) Sahana Software Foundation

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

__all__ = ("CRUDForm",
           "CustomForm",
           "DefaultForm",
           "DummyFormField",
           "FormField",
           "InlineInstruction",
           "SectionBreak",
           "VirtualFormField",
           "WithAdvice",
           )

import json

from gluon import current, A, DIV, INPUT, TAG, TD, TR, IS_LIST_OF, SQLFORM
from gluon.storage import Storage
from gluon.tools import callback

from s3dal import Field, filter_fields

from ..tools import s3_mark_required, set_last_record_id, s3_str, SKIP_VALIDATION

DEFAULT = lambda: None

# =============================================================================
class CRUDForm:
    """ CRUD Form Base Class"""

    # -------------------------------------------------------------------------
    def __init__(self, *elements, **attributes):
        """
            Args:
                elements: the form elements
                attributes: form attributes
        """

        self.elements = []
        append = self.elements.append

        debug = current.deployment_settings.get_base_debug()
        for element in elements:
            if not element:
                continue
            if isinstance(element, CRUDFormElement):
                append(element)
            elif isinstance(element, str):
                append(FormField(element))
            elif isinstance(element, tuple):
                l = len(element)
                if l > 1:
                    label, selector = element[:2]
                    widget = element[2] if l > 2 else DEFAULT
                else:
                    selector = element[0]
                    label = widget = DEFAULT
                append(FormField(selector, label=label, widget=widget))
            else:
                msg = "Invalid form element: %s" % str(element)
                if debug:
                    raise SyntaxError(msg)
                current.log.error(msg)

        opts = {}
        attr = {}
        for k in attributes:
            value = attributes[k]
            if k[:1] == "_":
                attr[k] = value
            else:
                opts[k] = value

        self.attr = attr
        self.opts = opts

        self.prefix = None
        self.name = None
        self.resource = None

        self.tablename = None
        self.table = None
        self.record_id = None

        self.subtables = None
        self.subrows = None
        self.components = None

    # -------------------------------------------------------------------------
    # Rendering/Processing
    # -------------------------------------------------------------------------
    def __call__(self,
                 request = None,
                 resource = None,
                 record_id = None,
                 readonly = False,
                 message = "Record created/updated",
                 format = None,
                 **options):
        """
            Render/process the form. To be implemented in subclass.

            Args:
                request: the CRUDRequest
                resource: the target CRUDResource
                record_id: the record ID
                readonly: render the form read-only
                message: message upon successful form submission
                format: data format extension (for audit)
                options: keyword options for the form

            Returns:
                a FORM instance
        """

        return None

    # -------------------------------------------------------------------------
    # Utility functions
    # -------------------------------------------------------------------------
    def __len__(self):
        """ Support len(crud_form) """

        return len(self.elements)

    # -------------------------------------------------------------------------
    def _config(self, key, default=None):
        """
            Get a configuration setting for the current table

            Args:
                key: the setting key
                default: fallback value if the setting is not available
        """

        tablename = self.tablename
        if tablename:
            return current.s3db.get_config(tablename, key, default)
        else:
            return default

    # -------------------------------------------------------------------------
    @staticmethod
    def _submit_buttons(readonly=False):
        """
            Render submit buttons

            Args:
                readonly: render the form read-only

            Returns:
                list of submit buttons
        """

        T = current.T
        s3 = current.response.s3
        settings = s3.crud

        if settings.custom_submit:
            submit = [(None,
                       settings.submit_button,
                       settings.submit_style)]
            submit.extend(settings.custom_submit)
            buttons = []
            for name, label, _class in submit:
                if isinstance(label, str):
                    label = T(label)
                button = INPUT(_type = "submit",
                               _class = "btn crud-submit-button",
                               _name = name,
                               _value = label,
                               )
                if _class:
                    button.add_class(_class)
                buttons.append(button)
        else:
            buttons = ["submit"]

        # Cancel button
        if not readonly and s3.cancel:
            if not settings.custom_submit:
                if settings.submit_button:
                    submit_label = T(settings.submit_button)
                else:
                    submit_label = T("Save")
                submit_button = INPUT(_type = "submit",
                                      _value = submit_label,
                                      )
                if settings.submit_style:
                    submit_button.add_class(settings.submit_style)
                buttons = [submit_button]

            cancel = s3.cancel
            if isinstance(cancel, DIV):
                cancel_button = cancel
            else:
                cancel_button = A(T("Cancel"),
                                  _class = "cancel-form-btn action-lnk",
                                  )
                if isinstance(cancel, dict):
                    # Script-controlled cancel button (embedded form)
                    if "script" in cancel:
                        # Custom script
                        script = cancel["script"]
                    else:
                        # Default script: hide form, show add-button
                        script = \
'''$('.cancel-form-btn').on('click',function(){$('#%(hide)s').slideUp('medium',function(){$('#%(show)s').show()})})'''
                    s3.jquery_ready.append(script % cancel)
                elif s3.cancel is True:
                    cancel_button.add_class("s3-cancel")
                else:
                    cancel_button.update(_href = s3.cancel)
            buttons.append(cancel_button)

        return buttons

    # -------------------------------------------------------------------------
    @staticmethod
    def _insert_subheadings(form, tablename, formstyle, subheadings):
        """
            Insert subheadings into forms

            Args:
                form: the form
                tablename: the tablename
                formstyle: the formstyle
                subheadings: - {"fieldname": "Heading"}, or
                             - {"fieldname": ["Heading1", "Heading2"]}
        """

        if not subheadings:
            return
        if tablename in subheadings:
            subheadings = subheadings.get(tablename)

        form_rows = iter(form[0])
        tr = next(form_rows)
        i = 0
        while tr:
            # @ToDo: We need a better way of working than this!
            f = tr.attributes.get("_id", None)
            if not f:
                try:
                    # DIV-based form-style
                    f = tr[0][0].attributes.get("_id", None)
                    if not f:
                        # DRRPP formstyle
                        f = tr[0][0][1][0].attributes.get("_id", None)
                        if not f:
                            # Date fields are inside an extra TAG()
                            f = tr[0][0][1][0][0].attributes.get("_id", None)
                except:
                    # Something else
                    f = None
            if f:
                if f.endswith("__row"):
                    f = f[:-5]
                if f.startswith(tablename):
                    f = f[len(tablename) + 1:] # : -6

                for prefix in ("sub_default", "sub_", "link_default", "link_"):
                    if f.startswith(prefix):
                        f = f[len(prefix):]
                        break

                headings = subheadings.get(f)
                if not headings:
                    try:
                        tr = next(form_rows)
                    except StopIteration:
                        break
                    else:
                        i += 1
                    continue
                if not isinstance(headings, list):
                    headings = [headings]
                inserted = 0
                for heading in headings:
                    subheading = CRUDForm._create_subheading(
                        formstyle.__name__,
                        heading,
                        tablename,
                        f,
                        inserted if inserted else "",
                    )
                    form[0].insert(i, subheading)
                    i += 1
                    inserted += 1
                if inserted:
                    tr.attributes.update(_class="%s after_subheading" % tr.attributes["_class"])
                    for _i in range(0, inserted):
                        # Iterate over the rows we just created
                        tr = next(form_rows)
            try:
                tr = next(form_rows)
            except StopIteration:
                break
            else:
                i += 1

    # -------------------------------------------------------------------------
    @staticmethod
    def _create_subheading(formstyle_name, represent, tablename, field_id, level=""):
        """
            Generates the HTML for the sub heading in relation to the current
            form style name

            Args:
                formstyle_name: the name of the form style
                represent: dictionary with the attributes
                tablename: the table name
                field_id: the id of the field
                level: the level index
        """

        if formstyle_name in ("formstyle_table", "formstyle_table_inline"):
            return TR(
                TD(
                    represent,
                    _colspan=3,
                    _class="subheading",
                ),
                _class = "subheading",
                _id = "%s_%s__subheading%s" % (tablename, field_id, level),
            )

        return DIV(
            represent,
            _class = "subheading",
            _id = "%s_%s__subheading%s" % (tablename, field_id, level),
        )

    # -------------------------------------------------------------------------
    def _populate(self,
                  from_table = None,
                  from_record = None,
                  map_fields = None,
                  data = None,
                  formfields = None,
                  format = None,
                  ):
        """
            Pre-populate the form with values from a previous record or
            controller-submitted data

            Args:
                from_table: the table to copy the data from
                from_record: the record to copy the data from
                map_fields: field selection/mapping
                data: the data to prepopulate the form with
                format: the request format extension
        """

        table = self.table
        record = None

        # Pre-populate from a previous record?
        if from_table is not None:

            # Field mapping
            if map_fields:
                if isinstance(map_fields, dict):
                    # Map fields with other names
                    fields = [from_table[map_fields[f]]
                              for f in map_fields
                                if f in table.fields and
                                   map_fields[f] in from_table.fields and
                                   table[f].writable]

                elif isinstance(map_fields, (list, tuple)):
                    # Only use a subset of the fields
                    fields = [from_table[f]
                              for f in map_fields
                                if f in table.fields and
                                   f in from_table.fields and
                                   table[f].writable]
                else:
                    raise TypeError
            else:
                # Use all writable fields
                fields = [from_table[f]
                          for f in table.fields
                            if f in from_table.fields and
                            table[f].writable]

            # Audit read => this is a read method, after all
            prefix, name = from_table._tablename.split("_", 1)
            current.audit("read", prefix, name,
                          record=from_record, representation=format)

            # Get original record
            query = (from_table.id == from_record)
            row = current.db(query).select(limitby=(0, 1), *fields).first()
            if row:
                if isinstance(map_fields, dict):
                    record = {f: row[map_fields[f]] for f in map_fields}
                else:
                    record = row.as_dict()

        # Pre-populate from call?
        elif isinstance(data, dict):
            record = {f: data[f] for f in data
                                 if f in table.fields and table[f].writable}

        # Add missing fields to pre-populated record
        if record:
            missing_fields = {}
            if formfields:
                for f in formfields:
                    fname = f.name
                    if fname not in record:
                        missing_fields[fname] = f.default
            else:
                for f in table.fields:
                    if f not in record and table[f].writable:
                        missing_fields[f] = table[f].default
            record.update(missing_fields)
            record[table._id.name] = None

        return record

# =============================================================================
class DefaultForm(CRUDForm):
    """ Standard CRUD form """

    # -------------------------------------------------------------------------
    # Rendering/Processing
    # -------------------------------------------------------------------------
    def __call__(self,
                 request = None,
                 resource = None,
                 record_id = None,
                 readonly = False,
                 message = "Record created/updated",
                 format = None,
                 **options):
        """
            Render/process the form.

            Args:
                request: the CRUDRequest
                resource: the target CRUDResource
                record_id: the record ID
                readonly: render the form read-only
                message: message upon successful form submission
                format: data format extension (for audit)
                options: keyword options for the form

            TODO describe keyword arguments

            Returns:
                a FORM instance
        """

        if resource is None:
            self.resource = request.resource
            self.prefix, self.name, self.table, self.tablename = \
                request.target()
        else:
            self.resource = resource
            self.prefix = resource.prefix
            self.name = resource.name

            self.tablename = resource.tablename
            self.table = resource.table

        response = current.response
        s3 = response.s3
        settings = s3.crud

        prefix = self.prefix
        name = self.name
        tablename = self.tablename
        table = self.table

        record = None
        labels = None

        self.record_id = record_id

        if not readonly:
            get_option = options.get

            # Populate create-form from another record?
            if record_id is None:
                data = get_option("data")
                from_table = get_option("from_table")
                from_record = get_option("from_record")
                map_fields = get_option("map_fields")
                record = self._populate(from_table = from_table,
                                        from_record = from_record,
                                        map_fields = map_fields,
                                        data = data,
                                        format = format,
                                        )

            # De-duplicate link table entries
            self.record_id = record_id = self.deduplicate_link(request, record_id)

            # Add asterisk to labels of required fields
            mark_required = self._config("mark_required", default=[])
            labels, required = s3_mark_required(table, mark_required)

            # Show required-hint if there are any required fields.
            s3.has_required = required

        # Determine form style
        if format == "plain":
            # Default formstyle works best when we have no formatting
            formstyle = "table3cols"
        elif readonly:
            formstyle = settings.formstyle_read
        else:
            formstyle = settings.formstyle

        # Submit buttons
        buttons = self._submit_buttons(readonly)

        # Generate the form
        if record is None:
            record = record_id
        response.form_label_separator = ""
        form = SQLFORM(table,
                       record = record,
                       record_id = record_id,
                       readonly = readonly,
                       comments = not readonly,
                       deletable = False,
                       showid = False,
                       upload = s3.download_url,
                       labels = labels,
                       formstyle = formstyle,
                       separator = "",
                       submit_button = settings.submit_button,
                       buttons = buttons)

        # Style the Submit button, if-requested
        if settings.submit_style and not settings.custom_submit:
            try:
                form[0][-1][0][0]["_class"] = settings.submit_style
            except:
                # Submit button has been removed or a different formstyle
                pass

        # Subheadings
        subheadings = options.get("subheadings", None)
        if subheadings:
            self._insert_subheadings(form, tablename, formstyle, subheadings)

        # Process the form
        logged = False
        if not readonly:
            link = get_option("link")
            hierarchy = get_option("hierarchy")
            onvalidation = get_option("onvalidation")
            onaccept = get_option("onaccept")
            success, error = self.process(form,
                                          request.post_vars,
                                          onvalidation = onvalidation,
                                          onaccept = onaccept,
                                          hierarchy = hierarchy,
                                          link = link,
                                          http = request.http,
                                          format = format,
                                          )
            if success:
                response.confirmation = message
                logged = True
            elif error:
                response.error = error

        # Audit read
        if not logged and not form.errors:
            current.audit("read", prefix, name,
                          record=record_id, representation=format)

        return form

    # -------------------------------------------------------------------------
    def deduplicate_link(self, request, record_id):
        """
            Change to update if this request attempts to create a
            duplicate entry in a link table

            Args:
                request: the request
                record_id: the record ID
        """

        linked = self.resource.linked
        table = self.table

        session = current.session

        if request.env.request_method == "POST" and linked is not None:
            pkey = table._id.name
            post_vars = request.post_vars
            if not post_vars[pkey]:

                lkey = linked.lkey
                rkey = linked.rkey

                def parse_key(value):
                    key = s3_str(value)
                    if key.startswith("{"):
                        # JSON-based selector (e.g. LocationSelector)
                        return json.loads(key).get("id")
                    else:
                        # Normal selector (e.g. OptionsWidget)
                        return value

                try:
                    lkey_ = parse_key(post_vars[lkey])
                    rkey_ = parse_key(post_vars[rkey])
                except Exception:
                    return record_id

                query = (table[lkey] == lkey_) & (table[rkey] == rkey_)
                row = current.db(query).select(table._id, limitby=(0, 1)).first()
                if row is not None:
                    tablename = self.tablename
                    record_id = row[pkey]
                    formkey = session.get("_formkey[%s/None]" % tablename)
                    formname = "%s/%s" % (tablename, record_id)
                    session["_formkey[%s]" % formname] = formkey
                    post_vars["_formname"] = formname
                    post_vars[pkey] = record_id

        return record_id

    # -------------------------------------------------------------------------
    def process(self, form, vars,
                onvalidation = None,
                onaccept = None,
                hierarchy = None,
                link = None,
                http = "POST",
                format = None,
                ):
        """
            Process the form

            Args:
                form: FORM instance
                vars: request POST variables
                onvalidation: callback(function) upon successful form validation
                onaccept: callback(function) upon successful form acceptance
                hierarchy: the data for the hierarchy link to create
                link: component link
                http: HTTP method
                format: request extension

        """

        table = self.table
        tablename = self.tablename

        # Get the proper onvalidation routine
        if isinstance(onvalidation, dict):
            onvalidation = onvalidation.get(tablename, [])

        # Append link.postprocess to onvalidation
        if link and link.postprocess:
            postprocess = link.postprocess
            if isinstance(onvalidation, list):
                onvalidation.insert(0, postprocess)
            elif onvalidation is not None:
                onvalidation = [postprocess, onvalidation]
            else:
                onvalidation = [postprocess]

        success = True
        error = None

        record_id = self.record_id
        formname = "%s/%s" % (tablename, record_id)
        if form.accepts(vars,
                        current.session,
                        formname = formname,
                        onvalidation = onvalidation,
                        keepvalues = False,
                        hideerror = False
                        ):

            # Undelete?
            if vars.get("_undelete"):
                undelete = form.vars.get("deleted") is False
            else:
                undelete = False

            # Audit
            prefix = self.prefix
            name = self.name
            if record_id is None or undelete:
                current.audit("create", prefix, name, form=form,
                              representation=format)
            else:
                current.audit("update", prefix, name, form=form,
                              record=record_id, representation=format)

            form_vars = form.vars

            # Update super entity links
            s3db = current.s3db
            s3db.update_super(table, form_vars)

            # Update component link
            if link and link.postprocess is None:
                resource = link.resource
                master = link.master
                resource.update_link(master, form_vars)

            if form_vars.id:
                if record_id is None or undelete:
                    # Create hierarchy link
                    if hierarchy:
                        from ..tools import S3Hierarchy
                        h = S3Hierarchy(tablename)
                        if h.config:
                            h.postprocess_create_node(hierarchy, form_vars)
                    # Set record owner
                    auth = current.auth
                    auth.s3_set_record_owner(table, form_vars.id)
                    auth.s3_make_session_owner(table, form_vars.id)
                else:
                    # Update realm
                    update_realm = s3db.get_config(table, "update_realm")
                    if update_realm:
                        current.auth.set_realm_entity(table, form_vars,
                                                      force_update=True)
                # Store session vars
                self.resource.lastid = str(form_vars.id)
                set_last_record_id(tablename, form_vars.id)

            # Execute onaccept
            try:
                callback(onaccept, form, tablename=tablename)
            except:
                error = "onaccept failed: %s" % str(onaccept)
                current.log.error(error)
                # This is getting swallowed
                raise

        else:
            success = False

            if form.errors:
                # Indicate form error in response
                # - so an otherwise hidden form can be made visible
                current.response.s3.form_error = True

                # Revert any records created within widgets/validators
                current.db.rollback()

                # IS_LIST_OF validation errors need special handling
                errors = []
                for fieldname in form.errors:
                    if fieldname in table:
                        if isinstance(table[fieldname].requires, IS_LIST_OF):
                            errors.append("%s: %s" % (fieldname,
                                                      form.errors[fieldname]))
                        else:
                            errors.append(str(form.errors[fieldname]))
                if errors:
                    error = "\n".join(errors)

            elif http == "POST":

                # Invalid form
                error = current.T("Invalid form (re-opened in another window?)")

        return success, error

# =============================================================================
class CustomForm(CRUDForm):
    """ Custom CRUD Form """

    # -------------------------------------------------------------------------
    # Rendering/Processing
    # -------------------------------------------------------------------------
    def __call__(self,
                 request = None,
                 resource = None,
                 record_id = None,
                 readonly = False,
                 message = "Record created/updated",
                 format = None,
                 **options):
        """
            Render/process the form.

            Args:
                request: the CRUDRequest
                resource: the target CRUDResource
                record_id: the record ID
                readonly: render the form read-only
                message: message upon successful form submission
                format: data format extension (for audit)
                options: keyword options for the form

            Returns:
                a FORM instance
        """

        db = current.db
        response = current.response
        s3 = response.s3

        # Determine the target resource
        if resource is None:
            resource = request.resource
            self.prefix, self.name, self.table, self.tablename = \
                request.target()
        else:
            self.prefix = resource.prefix
            self.name = resource.name
            self.tablename = resource.tablename
            self.table = resource.table
        self.resource = resource

        # Resolve all form elements against the resource
        subtables = set()
        subtable_fields = {}
        fields = []
        components = []

        for element in self.elements:
            alias, name, field = element.resolve(resource)

            if isinstance(alias, str):
                subtables.add(alias)

                if field is not None:
                    fields_ = subtable_fields.get(alias)
                    if fields_ is None:
                        fields_ = []
                    fields_.append((name, field))
                    subtable_fields[alias] = fields_

            elif isinstance(alias, CRUDFormElement):
                components.append(alias)

            if field is not None:
                fields.append((alias, name, field))

        self.subtables = subtables
        self.components = components

        rcomponents = resource.components

        # Customise subtables
        if subtables:
            if not request:
                # Create dummy CRUDRequest
                from ..controller import CRUDRequest
                r = CRUDRequest(resource.prefix,
                                resource.name,
                                # Current request args/vars could be in a different
                                # resource context, so must override them here:
                                args = [],
                                get_vars = {},
                                )
            else:
                r = request

            customise_resource = current.deployment_settings.customise_resource
            for alias in subtables:

                # Get tablename
                component = rcomponents.get(alias)
                if not component:
                    continue
                tablename = component.tablename

                # Run customise_resource
                customise = customise_resource(tablename)
                if customise:
                    customise(r, tablename)

                # Apply customised attributes to renamed fields
                # => except default, label, requires and widget, which can be overridden
                #    in FormField.resolve instead
                renamed_fields = subtable_fields.get(alias)
                if renamed_fields:
                    table = component.table
                    for name, renamed_field in renamed_fields:
                        original_field = table[name]
                        for attr in ("comment",
                                     "default",
                                     "readable",
                                     "represent",
                                     "requires",
                                     "update",
                                     "writable",
                                     ):
                            setattr(renamed_field,
                                    attr,
                                    getattr(original_field, attr),
                                    )

        # Mark required fields with asterisk
        if not readonly:
            mark_required = self._config("mark_required", default=[])
            labels, required = s3_mark_required(self.table, mark_required)
            # Show the required-hint if there are any required fields.
            s3.has_required = required
        else:
            labels = None

        # Choose formstyle
        crud_settings = s3.crud
        if format == "plain":
            # Simple formstyle works best when we have no formatting
            formstyle = "table3cols"
        elif readonly:
            formstyle = crud_settings.formstyle_read
        else:
            formstyle = crud_settings.formstyle

        # Retrieve the record
        record = None
        if record_id is not None:
            query = (self.table._id == record_id)
            # @ToDo: limit fields (at least not meta)
            record = db(query).select(limitby=(0, 1)).first()
        self.record_id = record_id
        self.subrows = Storage()

        # Populate the form
        data = None
        noupdate = []
        forbidden = []
        has_permission = current.auth.s3_has_permission

        if record is not None:

            # Retrieve the subrows
            subrows = self.subrows
            for alias in subtables:

                # Get the component
                component = rcomponents.get(alias)
                if not component or component.multiple:
                    continue

                # Get the subtable row from the DB
                subfields = subtable_fields.get(alias)
                if subfields:
                    subfields = [f[0] for f in subfields]
                row = self._subrow(query, component, fields=subfields)

                # Check permission for this subtable row
                ctname = component.tablename
                if not row:
                    permitted = has_permission("create", ctname)
                    if not permitted:
                        forbidden.append(alias)
                    continue

                cid = row[component.table._id]
                permitted = has_permission("read", ctname, cid)
                if not permitted:
                    forbidden.append(alias)
                    continue

                permitted = has_permission("update", ctname, cid)
                if not permitted:
                    noupdate.append(alias)

                # Add the row to the subrows
                subrows[alias] = row

            # Build the data Storage for the form
            pkey = self.table._id
            data = Storage({pkey.name:record[pkey]})
            for alias, name, field in fields:

                if alias is None:
                    # Field in the master table
                    if name in record:
                        value = record[name]
                        # Field Method?
                        if callable(value):
                            value = value()
                        data[field.name] = value

                elif alias in subtables:
                    # Field in a subtable
                    if alias in subrows and \
                       subrows[alias] is not None and \
                       name in subrows[alias]:
                        data[field.name] = subrows[alias][name]

                elif hasattr(alias, "extract"):
                    # Form element with custom extraction method
                    data[field.name] = alias.extract(resource, record_id)

        else:
            # Record does not exist
            self.record_id = record_id = None

            # Check create-permission for subtables
            for alias in subtables:
                component = rcomponents.get(alias)
                if not component:
                    continue
                permitted = has_permission("create", component.tablename)
                if not permitted:
                    forbidden.append(alias)

        # Apply permissions for subtables
        fields = [f for f in fields if f[0] not in forbidden]
        for a, n, f in fields:
            if a:
                if a in noupdate:
                    f.writable = False
                if labels is not None and f.name not in labels:
                    if f.required:
                        flabels = s3_mark_required([f], mark_required=[f])[0]
                        labels[f.name] = flabels[f.name]
                    elif f.label:
                        labels[f.name] = "%s:" % f.label
                    else:
                        labels[f.name] = ""

        if readonly:
            # Strip all comments
            for a, n, f in fields:
                f.comment = None
        else:
            # Mark required subtable-fields (retaining override-labels)
            for alias in subtables:
                component = rcomponents.get(alias)
                if not component:
                    continue
                mark_required = component.get_config("mark_required", [])
                ctable = component.table
                sfields = dict((n, (f.name, f.label))
                               for a, n, f in fields
                               if a == alias and n in ctable)
                slabels = s3_mark_required([ctable[n] for n in sfields],
                                           mark_required=mark_required,
                                           map_names=sfields)[0]
                if labels:
                    labels.update(slabels)
                else:
                    labels = slabels

        self.subtables = [s for s in self.subtables if s not in forbidden]

        # Aggregate the form fields
        formfields = [f[-1] for f in fields]

        # Prepopulate from another record?
        get_option = options.get
        if not record_id and request.http == "GET":
            data = self._populate(from_table = get_option("from_table"),
                                  from_record = get_option("from_record"),
                                  map_fields = get_option("map_fields"),
                                  data = get_option("data"),
                                  format = format,
                                  formfields = formfields
                                  )

        # Submit buttons
        buttons = self._submit_buttons(readonly)

        # Render the form
        tablename = self.tablename
        response.form_label_separator = ""
        form = SQLFORM.factory(record = data,
                               showid = False,
                               labels = labels,
                               formstyle = formstyle,
                               table_name = tablename,
                               upload = s3.download_url,
                               readonly = readonly,
                               separator = "",
                               submit_button = crud_settings.submit_button,
                               buttons = buttons,
                               *formfields)

        # Style the Submit button, if-requested
        if crud_settings.submit_style and not crud_settings.custom_submit:
            try:
                form[0][-1][0][0]["_class"] = crud_settings.submit_style
            except (KeyError, IndexError, TypeError):
                # Submit button has been removed or a different formstyle
                pass

        # Subheadings
        subheadings = get_option("subheadings", None)
        if subheadings:
            self._insert_subheadings(form, tablename, formstyle, subheadings)

        # Process the form
        formname = "%s/%s" % (tablename, record_id)
        post_vars = request.post_vars
        if form.accepts(post_vars,
                        current.session,
                        onvalidation = self.validate,
                        formname = formname,
                        keepvalues = False,
                        hideerror = False,
                        ):

            # Undelete?
            if post_vars.get("_undelete"):
                undelete = post_vars.get("deleted") is False
            else:
                undelete = False

            self.accept(form,
                        format = format,
                        link = get_option("link"),
                        hierarchy = get_option("hierarchy"),
                        undelete = undelete,
                        )
            # Post-process the form submission after all records have
            # been accepted and linked together (self.accept() has
            # already updated the form data with any new keys here):
            postprocess = self.opts.get("postprocess", None)
            if postprocess:
                try:
                    callback(postprocess, form, tablename=tablename)
                except:
                    error = "postprocess failed: %s" % postprocess
                    current.log.error(error)
                    raise
            response.confirmation = message

        if form.errors:
            # Indicate form error in response
            # - so an otherwise hidden form can be made visible
            current.response.s3.form_error = True

            # Revert any records created within widgets/validators
            db.rollback()

            response.error = current.T("There are errors in the form, please check your input")

        return form

    # -------------------------------------------------------------------------
    def validate(self, form):
        """
            Run the onvalidation callbacks for the master table
            and all subtables in the form, and store any errors
            in the form.

            Args:
                form: the form
        """

        s3db = current.s3db
        config = self._config

        # Validate against the main table
        if self.record_id:
            onvalidation = config("update_onvalidation",
                           config("onvalidation", None))
        else:
            onvalidation = config("create_onvalidation",
                           config("onvalidation", None))
        if onvalidation is not None:
            try:
                callback(onvalidation, form, tablename=self.tablename)
            except:
                error = "onvalidation failed: %s" % str(onvalidation)
                current.log.error(error)
                raise

        # Validate against all subtables
        get_config = s3db.get_config
        for alias in self.subtables:

            # Extract the subtable data
            subdata = self._extract(form, alias)
            if not subdata:
                continue

            # Get the onvalidation callback for this subtable
            subtable = self.resource.components[alias].table
            subform = Storage(vars=subdata, errors=Storage())

            rows = self.subrows
            if alias in rows and rows[alias] is not None:
                # Add the record ID for update-onvalidation
                pkey = subtable._id
                subform.vars[pkey.name] = rows[alias][pkey]
                subonvalidation = get_config(subtable._tablename,
                                             "update_onvalidation",
                                  get_config(subtable._tablename,
                                             "onvalidation", None))
            else:
                subonvalidation = get_config(subtable._tablename,
                                             "create_onvalidation",
                                  get_config(subtable._tablename,
                                             "onvalidation", None))

            # Validate against the subtable, store errors in form
            if subonvalidation is not None:
                try:
                    callback(subonvalidation, subform,
                             tablename = subtable._tablename)
                except:
                    error = "onvalidation failed: %s" % str(subonvalidation)
                    current.log.error(error)
                    raise
                for fn in subform.errors:
                    dummy = "sub_%s_%s" % (alias, fn)
                    form.errors[dummy] = subform.errors[fn]

        # Validate components (e.g. Inline-Forms)
        for component in self.components:
            if hasattr(component, "validate"):
                component.validate(form)

    # -------------------------------------------------------------------------
    def accept(self,
               form,
               format = None,
               link = None,
               hierarchy = None,
               undelete = False,
               ):
        """
            Create/update all records from the form.

            Args:
                form: the form
                format: data format extension (for audit)
                link: resource.link for linktable components
                hierarchy: the data for the hierarchy link to create
                undelete: reinstate a previously deleted record
        """

        db = current.db

        resource = self.resource
        table = self.table

        accept_row = self._accept
        input_data = self._extract

        # Create/update the main record
        main_data = input_data(form)
        master_id, master_form_vars = accept_row(self.record_id,
                                                 main_data,
                                                 format = format,
                                                 link = link,
                                                 hierarchy = hierarchy,
                                                 undelete = undelete,
                                                 )
        if not master_id:
            return
        else:
            master_query = (table._id == master_id)
            main_data[table._id.name] = master_id
            # Make sure lastid is set even if master has no data
            # (otherwise *_next redirection will fail)
            resource.lastid = str(master_id)

        # Create or update the subtables
        get_subrow = self._subrow
        for alias in self.subtables:

            # Get the data for this subtable from the form
            subdata = input_data(form, alias=alias)
            if not subdata:
                continue

            component = resource.components[alias]
            if not component or component.multiple:
                return
            subtable = component.table

            # Get the key (pkey) of the master record to link the
            # subtable record to, and update the subdata with it
            pkey = component.pkey
            if pkey != table._id.name and pkey not in main_data:
                row = db(table._id == master_id).select(table[pkey],
                                                        limitby = (0, 1),
                                                        ).first()
                if not row:
                    return
                main_data[pkey] = row[table[pkey]]
            if component.link:
                link = Storage(resource = component.link,
                               master = main_data,
                               )
            else:
                link = None
                subdata[component.fkey] = main_data[pkey]

            # Do we already have a record for this component?
            subrow = get_subrow(master_query, component, fields=[subtable._id.name])
            if subrow:
                # Yes => get the subrecord ID
                subid = subrow[subtable._id]
            else:
                # No => apply component defaults
                subid = None
                subdata = component.get_defaults(main_data, data=subdata)

            # Accept the subrecord
            accept_row(subid,
                       subdata,
                       alias = alias,
                       link = link,
                       format = format,
                       )

        # Accept components (e.g. Inline-Forms)
        for item in self.components:
            if hasattr(item, "accept"):
                item.accept(form, master_id=master_id, format=format)

        # Update form with master form_vars
        form_vars = form.vars
        form_vars[table._id.name] = master_id

        # Super entities (& anything added manually in table's onaccept)
        for var in master_form_vars:
            if var not in form_vars:
                form_vars[var] = master_form_vars[var]

    # -------------------------------------------------------------------------
    @staticmethod
    def _subrow(master_query, component, fields=None):
        """
            Extract the current row from a single-component

            Args:
                master_query: query for the master record
                component: the single-component (CRUDResource)
                fields: list of field names to extract
        """

        # Get the join for this subtable
        if not component or component.multiple:
            return None
        query = master_query & component.get_join()

        table = component.table
        if fields:
            # Map field names to component table
            try:
                fields = [table[f] for f in fields]
            except (KeyError, AttributeError):
                fields = None
            else:
                fields.insert(0, table._id)
        if not fields:
            fields = [table.ALL]

        # Retrieve the row
        return current.db(query).select(*fields,
                                        limitby = (0, 1)
                                        ).first()

    # -------------------------------------------------------------------------
    # Utility functions
    # -------------------------------------------------------------------------
    def insert(self, index, element):
        """
            S.insert(index, object) -- insert object before index
        """

        if not element:
            return
        if isinstance(element, CRUDFormElement):
            self.elements.insert(index, element)
        elif isinstance(element, str):
            self.elements.insert(index, FormField(element))
        elif isinstance(element, tuple):
            l = len(element)
            if l > 1:
                label, selector = element[:2]
                widget = element[2] if l > 2 else DEFAULT
            else:
                selector = element[0]
                label = widget = DEFAULT
            self.elements.insert(index, FormField(selector, label=label, widget=widget))
        else:
            msg = "Invalid form element: %s" % str(element)
            if current.deployment_settings.get_base_debug():
                raise SyntaxError(msg)
            current.log.error(msg)

    # -------------------------------------------------------------------------
    def append(self, element):
        """
            S.append(object) -- append object to the end of the sequence
        """

        self.insert(len(self), element)

    # -------------------------------------------------------------------------
    def _extract(self, form, alias=None):
        """
            Extract data for a subtable from the form

            Args:
                form: the form
                alias: the component alias of the subtable
        """

        if alias is None:
            return filter_fields(self.table, form.vars)
        else:
            subform = Storage()
            alias_length = len(alias)
            form_vars = form.vars
            for k in form_vars:
                if k[:4] == "sub_" and \
                   k[4:4 + alias_length + 1] == "%s_" % alias:
                    fn = k[4 + alias_length + 1:]
                    subform[fn] = form_vars[k]
            return subform

    # -------------------------------------------------------------------------
    def _accept(self,
                record_id,
                data,
                alias = None,
                format = None,
                hierarchy = None,
                link = None,
                undelete = False
                ):
        """
            Creates or updates a record

            Args:
                record_id: the record ID
                data: the data
                alias: the component alias
                format: the request format (for audit)
                hierarchy: the data for the hierarchy link to create
                link: resource.link for linktable components
                undelete: reinstate a previously deleted record

            Returns:
                tuple (accept_id, master_form_vars)
                - accept_id: the ID of the new/updated record
                - master_form_vars: the updated form vars (master record only)

            Raises:
                - RuntimeError if the record could not be created
        """

        empty = Storage()

        if alias is not None:
            # Subtable
            if not data or \
               not record_id and all(value is None for value in data.values()):
                # No data => skip
                return None, empty
        elif record_id and not data:
            # Existing master record, no data => skip, but return
            # record_id to allow update of inline-components:
            return record_id, empty

        s3db = current.s3db

        if alias is None:
            component = self.resource
        else:
            component = self.resource.components[alias]

        # Get the DB table (without alias)
        table = component.table
        tablename = component.tablename
        if component._alias != tablename:
            unaliased = s3db.table(component.tablename)
            # Must retain custom defaults of the aliased component:
            for field in table:
                field_ = unaliased[field.name]
                field_.default = field.default
                field_.update = field.update
            table = unaliased

        get_config = s3db.get_config

        oldrecord = None
        if record_id:
            # Update existing record
            accept_id = record_id
            db = current.db
            onaccept = get_config(tablename, "update_onaccept",
                       get_config(tablename, "onaccept", None))

            table_fields = table.fields
            query = (table._id == record_id)
            if onaccept:
                # Get oldrecord in full to save in form
                oldrecord = db(query).select(limitby=(0, 1)).first()
            elif "deleted" in table_fields:
                oldrecord = db(query).select(table.deleted,
                                             limitby=(0, 1)).first()
            else:
                oldrecord = None

            if undelete:
                # Restoring a previously deleted record
                if "deleted" in table_fields:
                    data["deleted"] = False
                if "created_by" in table_fields and current.auth.user:
                    data["created_by"] = current.auth.user.id
                if "created_on" in table_fields:
                    data["created_on"] = current.request.utcnow
            elif oldrecord and "deleted" in oldrecord and oldrecord.deleted:
                # Do not (ever) update a deleted record that we don't
                # want to restore, otherwise this may set foreign keys
                # in a deleted record!
                return accept_id, empty
            db(table._id == record_id).update(**data)
        else:
            # Insert new record
            accept_id = table.insert(**data)
            if not accept_id:
                raise RuntimeError("Could not create record")
            onaccept = get_config(tablename, "create_onaccept",
                       get_config(tablename, "onaccept", None))

        data[table._id.name] = accept_id
        prefix, name = tablename.split("_", 1)

        # Pseudo-form for post-processing
        form_vars = Storage(data)
        form = Storage(vars=form_vars, record=oldrecord)

        # Audit
        if record_id is None or undelete:
            current.audit("create", prefix, name, form=form,
                          representation=format)
        else:
            current.audit("update", prefix, name, form=form,
                          record=accept_id, representation=format)

        # Update super entity links
        s3db.update_super(table, form_vars)

        # Update component link
        if link and link.postprocess is None:
            resource = link.resource
            master = link.master
            resource.update_link(master, form_vars)

        if accept_id:
            if record_id is None or undelete:
                # Create hierarchy link
                if hierarchy:
                    from ..tools import S3Hierarchy
                    h = S3Hierarchy(tablename)
                    if h.config:
                        h.postprocess_create_node(hierarchy, form_vars)
                # Set record owner
                auth = current.auth
                auth.s3_set_record_owner(table, accept_id)
                auth.s3_make_session_owner(table, accept_id)
            else:
                # Update realm
                update_realm = get_config(table, "update_realm")
                if update_realm:
                    current.auth.set_realm_entity(table, form_vars,
                                                  force_update = True,
                                                  )

            # Store session vars
            component.lastid = str(accept_id)
            set_last_record_id(tablename, accept_id)

            # Execute onaccept
            try:
                callback(onaccept, form, tablename=tablename)
            except:
                error = "onaccept failed: %s" % str(onaccept)
                current.log.error(error)
                raise

        # Master form vars
        # - to update the original form with any values added during
        #   post-process, e.g. super-IDs
        master_form_vars = empty if alias else form.vars

        return accept_id, master_form_vars

# =============================================================================
class CRUDFormElement:
    """ SQL Form Element Base Class """

    # -------------------------------------------------------------------------
    def __init__(self, selector, **options):
        """
            Args:
                selector: the data object selector
                options: options for the form element
        """

        self.selector = selector
        self.options = Storage(options)

    # -------------------------------------------------------------------------
    def resolve(self, resource):
        """
            Method to resolve this form element against the calling resource.
            To be implemented in subclass.

            Args:
                resource: the resource

            Returns:
                a tuple (form element,
                         original field name,
                         Field instance for the form renderer
                         )

            Note:
                The form element can be None for the main table, the component
                alias for a subtable, or this form element instance for a
                subform.

                If None is returned as Field instance, this form element will
                not be rendered at all. Besides setting readable/writable
                in the Field instance, this can be another mechanism to
                control access to form elements.
        """

        return None, None, None

    # -------------------------------------------------------------------------
    # Utility methods
    # -------------------------------------------------------------------------
    @staticmethod
    def _rename_field(field, name,
                      comments = True,
                      label = DEFAULT,
                      popup = None,
                      skip_validation = False,
                      widget = DEFAULT
                      ):
        """
            Rename a field (actually: create a new Field instance with the
            same attributes as the given Field, but a different field name).

            Args:
                field: the original Field instance
                name: the new name
                comments: render comments - if set to False, only
                          navigation items with an inline() renderer
                          method will be rendered (unless popup is None)
                label: override option for the original field label
                popup: only if comments=False, additional vars for comment
                       navigation items (e.g. PopupLink), None prevents
                       rendering of navigation items
                skip_validation: skip field validation during POST, useful
                                 for client-side processed dummy fields.
                widget: override option for the original field widget
        """

        if label is DEFAULT:
            label = field.label
        if widget is DEFAULT:
            # Some widgets may need disabling during POST
            widget = field.widget

        if not hasattr(field, "type"):
            # Virtual Field
            field = Storage(comment = None,
                            type = "string",
                            length = 255,
                            unique = False,
                            uploadfolder = None,
                            autodelete = False,
                            label = "",
                            writable = False,
                            readable = True,
                            default = None,
                            update = None,
                            compute = None,
                            represent = lambda v: v or "",
                            )
            requires = None
            required = False
            notnull = False
        elif skip_validation and current.request.env.request_method == "POST":
            requires = SKIP_VALIDATION(field.requires)
            required = False
            notnull = False
        else:
            requires = field.requires
            required = field.required
            notnull = field.notnull

        if not comments:
            if popup:
                comment = field.comment
                if hasattr(comment, "clone"):
                    comment = comment.clone()
                if hasattr(comment, "renderer") and \
                   hasattr(comment, "inline") and \
                   isinstance(popup, dict):
                    comment.vars.update(popup)
                    comment.renderer = comment.inline
                else:
                    comment = None
            else:
                comment = None
        else:
            comment = field.comment

        f = Field(str(name),
                  type = field.type,
                  length = field.length,

                  required = required,
                  notnull = notnull,
                  unique = field.unique,

                  uploadfolder = field.uploadfolder,
                  autodelete = field.autodelete,

                  comment = comment,
                  label = label,
                  widget = widget,

                  default = field.default,

                  writable = field.writable,
                  readable = field.readable,

                  update = field.update,
                  compute = field.compute,

                  represent = field.represent,
                  requires = requires)

        return f

# =============================================================================
class FormField(CRUDFormElement):
    """
        Base class for regular form fields

        A regular form field is a field in the main form, which can be
        fields in the main record or in a subtable (single-record-component).
    """

    # -------------------------------------------------------------------------
    def resolve(self, resource):
        """
            Method to resolve this form element against the calling resource.

            Args:
                resource: the resource

            Returns:
                a tuple (subtable alias (or None for main table),
                         original field name,
                         Field instance for the form renderer
                         )
        """

        # Import S3ResourceField only here, to avoid circular dependency
        from ..resource import S3ResourceField

        rfield = S3ResourceField(resource, self.selector)

        field = rfield.field
        if field is None:
            raise SyntaxError("Invalid selector: %s" % self.selector)

        tname = rfield.tname

        options_get = self.options.get
        label = options_get("label", DEFAULT)
        widget = options_get("widget", DEFAULT)

        if resource._alias:
            tablename = resource._alias
        else:
            tablename = resource.tablename

        if tname == tablename:
            # Field in the main table

            if label is not DEFAULT:
                field.label = label
            if widget is not DEFAULT:
                field.widget = widget

            return None, field.name, field

        else:
            for alias, component in resource.components.loaded.items():
                if component.multiple:
                    continue
                if component._alias:
                    tablename = component._alias
                else:
                    tablename = component.tablename
                if tablename == tname:
                    name = "sub_%s_%s" % (alias, rfield.fname)
                    renamed_field = self._rename_field(field,
                                                       name,
                                                       label = label,
                                                       widget = widget,
                                                       )
                    return alias, field.name, renamed_field

            raise SyntaxError("Invalid subtable: %s" % tname)

# =============================================================================
class VirtualFormField(CRUDFormElement):
    """
        A form element to embed values of field methods (virtual fields),
        always read-only
    """

    # -------------------------------------------------------------------------
    def resolve(self, resource):
        """
            Method to resolve this form element against the calling resource.

            Args:
                resource: the resource

            Returns:
                a tuple (subtable alias (or None for main table),
                         original field name,
                         Field instance for the form renderer
                         )
        """

        table = resource.table
        selector = self.selector

        if not hasattr(table, selector):
            raise SyntaxError("Undefined virtual field: %s" % selector)

        label = self.options.label
        if not label:
            label = " ".join(s.capitalize() for s in selector.split("_"))

        # Apply represent if defined
        method = table[selector]
        if hasattr(method, "handler") and \
           hasattr(method.handler, "represent"):
            represent = method.handler.represent
        else:
            represent = None

        field = Field(selector,
                      label = label,
                      represent = represent,
                      widget = self,
                      )

        return None, selector, field

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):
        """
            Widget renderer for field method values
                - renders a simple DIV with the (represented) value
                - includes the (raw) value as hidden input, so it is
                  available in POST vars after form submission
        """

        v = field.represent(value) if field.represent else value

        inp = INPUT(_type="hidden", _name=field.name, _value=s3_str(value))

        widget = DIV(v, inp, **attributes)
        widget.add_class("s3-virtual-field")

        return widget

# =============================================================================
class DummyFormField(CRUDFormElement):
    """
        A Dummy Field

        A simple DIV which can then be acted upon with JavaScript
    """

    # -------------------------------------------------------------------------
    def resolve(self, resource):
        """
            Method to resolve this form element against the calling resource.

            Args:
                resource: the resource

            Returns:
                a tuple (subtable alias (or None for main table),
                         original field name,
                         Field instance for the form renderer
                         )
        """

        selector = self.selector

        field = Field(selector,
                      default = "",
                      label = "",
                      widget = self,
                      )

        return None, selector, field

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):
        """
            Widget renderer for the input field. To be implemented in
            subclass (if required) and to be set as widget=self for the
            field returned by the resolve()-method of this form element.

            Args:
                field: the input field
                value: the value to populate the widget
                attributes: attributes for the widget

            Returns:
                the widget for this form element as HTML helper
        """

        return DIV(_class = "s3-dummy-field")

# =============================================================================
class SectionBreak(CRUDFormElement):
    """
        A Section Break

        A simple DIV which can then be acted upon with JavaScript &/or Styled
    """

    # -------------------------------------------------------------------------
    def resolve(self, resource):
        """
            Method to resolve this form element against the calling resource.

            Args:
                resource: the resource

            Returns:
                a tuple (subtable alias (or None for main table),
                         original field name,
                         Field instance for the form renderer
                         )
        """

        selector = ""

        field = Field(selector,
                      default = "",
                      label = "",
                      widget = self,
                      )

        return None, selector, field

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):
        """
            Widget renderer for the input field. To be implemented in
            subclass (if required) and to be set as widget=self for the
            field returned by the resolve()-method of this form element.

            Args:
                field: the input field
                value: the value to populate the widget
                attributes: attributes for the widget

            Returns:
                the widget for this form element as HTML helper
        """

        return DIV(_class = "s3-section-break")

# =============================================================================
class InlineInstruction(CRUDFormElement):
    """
        Inline Instructions

        A simple DIV which can then be acted upon with JavaScript &/or Styled
    """

    # -------------------------------------------------------------------------
    def __init__(self, do, say, **options):
        """
            Args:
                do: What to Do
                say: What to Say
        """

        super().__init__(None)

        self.do = do
        self.say = say

    # -------------------------------------------------------------------------
    def resolve(self, resource):
        """
            Method to resolve this form element against the calling resource.

            Args:
                resource: the resource

            Returns:
                a tuple (subtable alias (or None for main table),
                         original field name,
                         Field instance for the form renderer
                         )
        """

        selector = ""

        field = Field(selector,
                      default = "",
                      label = "",
                      widget = self,
                      )

        return None, selector, field

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):
        """
            Widget renderer for the input field. To be implemented in
            subclass (if required) and to be set as widget=self for the
            field returned by the resolve()-method of this form element.

            Args:
                field: the input field
                value: the value to populate the widget
                attributes: attributes for the widget

            Returns:
                the widget for this form element as HTML helper
        """

        element = DIV(data = {"do": self.do,
                              "say": self.say,
                              },
                      _class = "s3-inline-instructions",
                      )

        return element

# =============================================================================
class WithAdvice(CRUDFormElement):
    """
        Wrapper for form elements (or field widgets) to add an
        introductory/advisory text above or below them
    """

    def __init__(self, widget, text=None, below=False, cmsxml=False):
        """
            Args:
                widget: the widget
                text: the text, string|DIV|tuple,
                      if specified as tuple (module, resource, name),
                      the text will be looked up from CMS
                below: render the advice below rather than above the widget
                cmsxml: do not XML-escape CMS contents, should only
                        be used with safe origin content (=normally never)
        """

        super().__init__(None)

        self.widget = widget

        self.text = text
        self.cmsxml = cmsxml
        self.below = below

    # -------------------------------------------------------------------------
    def resolve(self, resource):
        """
            Override CRUDFormElement.resolve() to map to widget

            Args:
                resource: the CRUDResource to resolve this form element
                          against
        """

        widget = self.widget

        if isinstance(widget, str):
            widget = FormField(widget)

        resolved = widget.resolve(resource)

        field = resolved[2]
        if field:
            if isinstance(widget, FormField):
                if field.widget:
                    self.widget = field.widget
                else:
                    self.widget = self.default_widget
            field.widget = self
        return resolved

    # -------------------------------------------------------------------------
    def __getattr__(self, key):
        """
            Attribute access => map to widget

            Args:
                key: the attribute key
        """

        if key in self.__dict__:
            return self.__dict__[key]

        sentinel = object()
        value = getattr(self.widget, key, sentinel)
        if value is sentinel:
            raise AttributeError
        return value

    # -------------------------------------------------------------------------
    def __call__(self, *args, **kwargs):
        """
            Widget renderer => map to widget, then add advice
        """

        w = self.widget(*args, **kwargs)

        text = self.text
        if isinstance(text, tuple):
            if len(text) == 3 and current.deployment_settings.has_module("cms"):
                text = current.s3db.cms_get_content(text[2],
                                                    module = text[0],
                                                    resource = text[1],
                                                    cmsxml = self.cmsxml,
                                                    )
            else:
                text = None

        if text:
            elements = (DIV(text, _class="widget-advice"), w)
            if self.below:
                elements = elements[::-1]
            return TAG[""](*elements)
        else:
            return w

    # -------------------------------------------------------------------------
    @staticmethod
    def default_widget(*args, **kwargs):
        """
            Default widget if enclosed field has no widget
        """

        from s3dal import SQLCustomType
        from gluon.sqlhtml import REGEX_WIDGET_CLASS, OptionsWidget

        widgets = SQLFORM.widgets

        field = args[0]
        ftype = field.type

        if ftype == 'upload':
            widget = widgets.upload.widget(*args, **kwargs)
        elif ftype == 'boolean':
            widget = widgets.boolean.widget(*args, **kwargs)
        elif OptionsWidget.has_options(field):
            if not field.requires.multiple:
                widget = OptionsWidget.widget(*args, **kwargs)
            else:
                widget = widgets.multiple.widget(*args, **kwargs)
        elif str(ftype).startswith('list:'):
            widget = widgets.list.widget(*args, **kwargs)
        elif ftype == 'text':
            widget = widgets.text.widget(*args, **kwargs)
        elif ftype == 'password':
            widget = widgets.password.widget(*args, **kwargs)
        elif ftype == 'blob':
            raise TypeError('WithAdvice: unsupported field type %s' % ftype)
        elif isinstance(ftype, SQLCustomType) and callable(ftype.widget):
            widget = ftype.widget(*args, **kwargs)
        else:
            field_type = REGEX_WIDGET_CLASS.match(str(ftype)).group()
            if not field_type or field_type not in widgets:
                field_type = "string"
            widget = widgets[field_type].widget(*args, **kwargs)

        return widget

# END =========================================================================
