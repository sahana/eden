# -*- coding: utf-8 -*-

""" Custom UI Widgets

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @copyright: 2009-2013 (c) Sahana Software Foundation
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

    NB Widgets are processed upon form submission (before form validation)
       in addition to when generating new forms (so are often processed twice)
"""

__all__ = ["S3ACLWidget",
           "S3AddObjectWidget",
           "S3AddPersonWidget",
           "S3AddPersonWidget2",
           "S3AutocompleteWidget",
           "S3AutocompleteOrAddWidget",
           "S3BooleanWidget",
           "S3ColorPickerWidget",
           "S3DateWidget",
           "S3DateTimeWidget",
           "S3EmbedComponentWidget",
           "S3HiddenWidget",
           "S3HumanResourceAutocompleteWidget",
           "S3ImageCropWidget",
           "S3InvBinWidget",
           "S3KeyValueWidget",
           #"S3LatLonWidget",
           "S3LocationAutocompleteWidget",
           "S3LocationDropdownWidget",
           "S3LocationSelectorWidget",
           "S3LocationSelectorWidget2",
           "S3MultiSelectWidget",
           "S3OrganisationAutocompleteWidget",
           "S3OrganisationHierarchyWidget",
           "S3PersonAutocompleteWidget",
           "S3PriorityListWidget",
           "S3SiteAutocompleteWidget",
           "S3SiteAddressAutocompleteWidget",
           "S3SliderWidget",
           "S3TimeIntervalWidget",
           #"S3UploadWidget",
           "CheckboxesWidgetS3",
           "s3_checkboxes_widget",
           "s3_comments_widget",
           "s3_grouped_checkboxes_widget",
           "s3_richtext_widget",
           "search_ac",
           ]

import datetime

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

try:
    from lxml import etree
except ImportError:
    import sys
    print >> sys.stderr, "ERROR: lxml module needed for XML handling"
    raise

from gluon import *
# Here are dependencies listed for reference:
#from gluon import current
#from gluon.dal import Field
#from gluon.html import *
#from gluon.http import HTTP
#from gluon.validators import *
from gluon.html import BUTTON
from gluon.sqlhtml import *
from gluon.storage import Storage

from s3export import S3Exporter
from s3utils import *
from s3validators import *

ogetattr = object.__getattribute__
repr_select = lambda l: len(l.name) > 48 and "%s..." % l.name[:44] or l.name

# =============================================================================
class S3ACLWidget(CheckboxesWidget):
    """
        Widget class for ACLs

        @todo: add option dependency logic (JS)
        @todo: configurable vertical/horizontal alignment
    """

    @staticmethod
    def widget(field, value, **attributes):

        requires = field.requires
        if not isinstance(requires, (list, tuple)):
            requires = [requires]
        if requires:
            if hasattr(requires[0], "options"):
                options = requires[0].options()
                values = []
                for k in options:
                    if isinstance(k, (list, tuple)):
                        k = k[0]
                    try:
                        flag = int(k)
                        if flag == 0:
                            if value == 0:
                                values.append(k)
                                break
                            else:
                                continue
                        elif value and value & flag == flag:
                            values.append(k)
                    except ValueError:
                        pass
                value = values

        #return CheckboxesWidget.widget(field, value, **attributes)

        attr = OptionsWidget._attributes(field, {}, **attributes)

        options = [(k, v) for k, v in options if k != ""]
        opts = []
        cols = attributes.get("cols", 1)
        totals = len(options)
        mods = totals%cols
        rows = totals/cols
        if mods:
            rows += 1

        for r_index in range(rows):
            tds = []
            for k, v in options[r_index*cols:(r_index+1)*cols]:
                tds.append(TD(INPUT(_type="checkbox",
                                    _name=attr.get("_name", field.name),
                                    requires=attr.get("requires", None),
                                    hideerror=True, _value=k,
                                    value=(k in value)), v))
            opts.append(TR(tds))

        if opts:
            opts[-1][0][0]["hideerror"] = False
        return TABLE(*opts, **attr)

        # was values = re.compile("[\w\-:]+").findall(str(value))
        #values = not isinstance(value,(list,tuple)) and [value] or value


        #requires = field.requires
        #if not isinstance(requires, (list, tuple)):
            #requires = [requires]
        #if requires:
            #if hasattr(requires[0], "options"):
                #options = requires[0].options()
            #else:
                #raise SyntaxError, "widget cannot determine options of %s" \
                    #% field

# =============================================================================
class S3AddObjectWidget(FormWidget):
    """
        This widget displays an inline form loaded via AJAX on demand.

        In the browser:
            A load request must made to this widget to enable it.
            The load request must include:
                - a URL for the form

            after a successful submission, the response callback is handed the
            response.
    """
    def __init__(self,
                 form_url,
                 table_name,
                 dummy_field_selector,
                 on_show,
                 on_hide
                ):

        self.form_url = form_url
        self.table_name = table_name
        self.dummy_field_selector = dummy_field_selector
        self.on_show = on_show
        self.on_hide = on_hide

    def __call__(self, field, value, **attributes):

        T = current.T
        s3 = current.response.s3

        if s3.debug:
            script_name = "/%s/static/scripts/jquery.ba-resize.js"
        else:
            script_name = "/%s/static/scripts/jquery.ba-resize.min.js"

        if script_name not in s3.scripts:
            s3.scripts.append(script_name)
        return TAG[""](
            # @ToDo: Move to Static
            SCRIPT('''
$(function () {
    var form_field = $('#%(form_field_name)s')
    var throbber = $('<div id="%(form_field_name)s_ajax_throbber" class="ajax_throbber"/>')
    throbber.hide()
    throbber.insertAfter(form_field)

    function request_add_form() {
        throbber.show()
        var dummy_field = $('%(dummy_field_selector)s')
        // create an element for the form
        var form_iframe = document.createElement('iframe')
        var $form_iframe = $(form_iframe)
        $form_iframe.attr('id', '%(form_field_name)s_form_iframe')
        $form_iframe.attr('frameborder', '0')
        $form_iframe.attr('scrolling', 'no')
        $form_iframe.attr('src', '%(form_url)s')

        var initial_iframe_style = {
            width: add_object_link.width(),
            height: add_object_link.height()
        }
        $form_iframe.css(initial_iframe_style)

        function close_iframe() {
            $form_iframe.unload()
            form_iframe.contentWindow.close()
            //iframe_controls.remove()
            $form_iframe.animate(
                initial_iframe_style,
                {
                    complete: function () {
                        $form_iframe.remove()
                        add_object_link.show()
                        %(on_hide)s
                        dummy_field.show()
                    }
                }
            )
        }

        function reload_iframe() {
            form_iframe.contentWindow.location.reload(true)
        }

        function resize_iframe_to_fit_content() {
            var form_iframe_content = $form_iframe.contents().find('body');
            // do first animation smoothly
            $form_iframe.animate(
                {
                    height: form_iframe_content.outerHeight(true),
                    width: 500
                },
                {
                    duration: jQuery.resize.delay,
                    complete: function () {
                        // iframe's own animations should be instant, as they
                        // have their own smoothing (e.g. expanding error labels)
                        function resize_iframe_to_fit_content_immediately() {
                            $form_iframe.css({
                                height: form_iframe_content.outerHeight(true),
                                width:500
                            })
                        }
                        // if the iframe content resizes, resize the iframe
                        // this depends on Ben Alman's resize plugin
                        form_iframe_content.bind(
                            'resize',
                            resize_iframe_to_fit_content_immediately
                        )
                        // when unloading, unbind the resizer (remove poller)
                        $form_iframe.bind(
                            'unload',
                            function () {
                                form_iframe_content.unbind(
                                    'resize',
                                    resize_iframe_to_fit_content_immediately
                                )
                                //iframe_controls.hide()
                            }
                        )
                        // there may have been content changes during animation
                        // so resize to make sure they are shown.
                        form_iframe_content.resize()
                        //iframe_controls.show()
                        %(on_show)s
                    }
                }
            )
        }

        function iframe_loaded() {
            dummy_field.hide()
            resize_iframe_to_fit_content()
            form_iframe.contentWindow.close_iframe = close_iframe
            throbber.hide()
        }

        $form_iframe.bind('load', iframe_loaded)

        function set_object_id() {
            // the server must give the iframe the object
            // id of the created object for the field
            // the iframe must also close itself.
            var created_object_representation = form_iframe.contentWindow.created_object_representation
            if (created_object_representation) {
                dummy_field.val(created_object_representation)
            }
            var created_object_id = form_iframe.contentWindow.created_object_id
            if (created_object_id) {
                form_field.val(created_object_id)
                close_iframe()
            }
        }
        $form_iframe.bind('load', set_object_id)
        add_object_link.hide()

        /*
        var iframe_controls = $('<span class="iframe_controls" style="float:right; text-align:right;"></span>')
        iframe_controls.hide()

        var close_button = $('<a>%(Close)s </a>')
        close_button.click(close_iframe)

        var reload_button = $('<a>%(Reload)s </a>')
        reload_button.click(reload_iframe)

        iframe_controls.append(close_button)
        iframe_controls.append(reload_button)
        iframe_controls.insertBefore(add_object_link)
        */
        $form_iframe.insertAfter(add_object_link)
    }
    var add_object_link = $('<a>%(Add)s</a>')
    add_object_link.click(request_add_form)
    add_object_link.insertAfter(form_field)
})''' % dict(
            field_name = field.name,
            form_field_name = "_".join((self.table_name, field.name)),
            form_url = self.form_url,
            dummy_field_selector = self.dummy_field_selector(self.table_name, field.name),
            on_show = self.on_show,
            on_hide = self.on_hide,
            Add = T("Add..."),
            Reload = T("Reload"),
            Close = T("Close"),
        )
            )
        )

# =============================================================================
class S3AddPersonWidget(FormWidget):
    """
        Renders a person_id field as a Create Person form,
        with an embedded Autocomplete to select existing people.

        It relies on JS code in static/S3/s3.select_person.js
    """

    def __init__(self,
                 controller = None,
                 select_existing = None):

        # Controller to retrieve the person record
        self.controller = controller
        if select_existing is not None:
            self.select_existing = select_existing
        else:
            self.select_existing = current.deployment_settings.get_pr_select_existing()

    def __call__(self, field, value, **attributes):

        T = current.T
        request = current.request
        appname = request.application
        s3 = current.response.s3
        settings = current.deployment_settings

        formstyle = s3.crud.formstyle

        default = dict(_type = "text",
                       value = (value != None and str(value)) or "")
        attr = StringWidget._attributes(field, default, **attributes)
        attr["_class"] = "hide"

        # Main Input
        if "_id" in attr:
            real_input = attr["_id"]
        else:
            real_input = str(field).replace(".", "_")

        if self.controller is None:
            controller = request.controller
        else:
            controller = self.controller

        if self.select_existing:
            # Autocomplete
            select = '''S3.select_person($('#%s').val())''' % real_input
            widget = S3PersonAutocompleteWidget(post_process=select,
                                                hideerror=True)
            ac_row = TR(TD(LABEL("%s: " % T("Name"),
                                 _class="hide",
                                 _id="person_autocomplete_label"),
                           widget(field,
                                  None,
                                  _class="hide")),
                        TD(),
                        _id="person_autocomplete_row",
                        _class="box_top")
            # Select from registry buttons
            _class ="box_top"
            select_row = TR(TD(A(T("Select from registry"),
                                 _href="#",
                                 _id="select_from_registry",
                                 _class="action-btn"),
                               A(T("Remove selection"),
                                 _href="#",
                                 _onclick='''S3.select_person_clear_form();''',
                                 _id="clear_form_link",
                                 _class="action-btn hide",
                                 _style="padding-left:15px;"),
                               A(T("Edit Details"),
                                 _href="#",
                                 _onclick='''S3.select_person_edit_form();''',
                                 _id="edit_selected_person_link",
                                 _class="action-btn hide",
                                 _style="padding-left:15px;"),
                               DIV(_id="person_load_throbber",
                                   _class="throbber hide",
                                   _style="padding-left:85px;"),
                               _class="w2p_fw"),
                            TD(),
                            _id="select_from_registry_row",
                            _class=_class,
                            _controller=controller,
                            _field=real_input,
                            _value=str(value))

        else:
            _class = "hide"
            ac_row = ""
            select_row = TR(TD(A(T("Edit Details"),
                                 _href="#",
                                 _onclick='''S3.select_person_edit_form();''',
                                 _id="edit_selected_person_link",
                                 _class="action-btn hide",
                                 _style="padding-left:15px;"),
                               DIV(_id="person_load_throbber",
                                   _class="throbber hide",
                                   _style="padding-left:85px;"),
                               _class="w2p_fw"),
                            TD(),
                            _id="select_from_registry_row",
                            _class=_class,
                            _controller=controller,
                            _field=real_input,
                            _value=str(value))

        # Embedded Form
        s3db = current.s3db
        ptable = s3db.pr_person
        ctable = s3db.pr_contact
        fields = [ptable.first_name,
                  ptable.middle_name,
                  ptable.last_name,
                  ]
        if settings.get_pr_request_dob():
            fields.append(ptable.date_of_birth)
        if settings.get_pr_request_gender():
            fields.append(ptable.gender)

        if controller == "hrm":
            emailRequired = settings.get_hrm_email_required()
        elif controller == "vol":
            fields.append(s3db.pr_person_details.occupation)
            emailRequired = settings.get_hrm_email_required()
        else:
            emailRequired = False
        if emailRequired:
            validator = IS_EMAIL()
        else:
            validator = IS_NULL_OR(IS_EMAIL())

        fields.extend([Field("email",
                             notnull=emailRequired,
                             requires=validator,
                             label=T("Email Address")),
                       Field("mobile_phone",
                             label=T("Mobile Phone Number"),
                             # requires=None to work around a web2py bug
                             requires=None)
                       ])

        labels, required = s3_mark_required(fields)
        if required:
            s3.has_required = True

        if request.env.request_method == "POST" and not value:
            # Read the POST vars:
            post_vars = request.post_vars
            values = Storage(ptable._filter_fields(post_vars))
            values["email"] = post_vars["email"]
            values["mobile_phone"] = post_vars["mobile_phone"]

            # Use the validators to convert the POST vars into
            # internal format (not validating here):
            data = Storage()
            for f in fields:
                fname = f.name
                if fname in values:
                    v, error = values[fname], None
                    requires = f.requires
                    if requires:
                        if not isinstance(requires, (list, tuple)):
                            requires = [requires]
                        for validator in requires:
                            v, error = validator(v)
                            if error:
                                break
                    if not error:
                        data[fname] = v

            record_id = 0
        else:
            data = None
            record_id = value

        form = SQLFORM.factory(table_name="pr_person",
                               record=data,
                               labels=labels,
                               formstyle=formstyle,
                               upload="default/download",
                               separator = "",
                               record_id = record_id,
                               *fields)
        trs = []
        for tr in form[0]:
            if "_id" in tr.attributes:
                # Standard formstyle
                if tr.attributes["_id"].startswith("submit_record"):
                    # skip submit row
                    continue
            elif "_id" in tr[0][0].attributes:
                # DIV-based formstyle
                if tr[0][0].attributes["_id"].startswith("submit_record"):
                    # skip submit row
                    continue
            if "_class" in tr.attributes:
                tr.attributes["_class"] = "%s box_middle" % \
                                            tr.attributes["_class"]
            else:
                tr.attributes["_class"] = "box_middle"
            trs.append(tr)

        table = DIV(*trs)

        # Divider
        divider = TR(TD(_class="subheading"),
                     TD(),
                     _class="box_bottom")

        # JS
        if s3.debug:
            script = "/%s/static/scripts/S3/s3.select_person.js" % appname
        else:
            script = "/%s/static/scripts/S3/s3.select_person.min.js" % appname
        scripts = s3.scripts
        if script not in scripts:
            scripts.append(script)
        s3.jquery_ready.append('''S3.addPersonWidget()''')

        # Overall layout of components
        return TAG[""](select_row,
                       ac_row,
                       table,
                       divider)

# =============================================================================
class S3AddPersonWidget2(FormWidget):
    """
        Renders a person_id field as a Create Person form,
        with an embedded Autocomplete to select existing people.

        It relies on JS code in static/S3/s3.add_person.js
    """

    def __init__(self,
                 controller = None,
                 select_existing = None):

        # Controller to retrieve the person record
        self.controller = controller
        if select_existing is not None:
            self.select_existing = select_existing
        else:
            self.select_existing = current.deployment_settings.get_pr_select_existing()

    def __call__(self, field, value, **attributes):

        T = current.T
        request = current.request
        appname = request.application
        s3 = current.response.s3
        settings = current.deployment_settings

        formstyle = s3.crud.formstyle

        default = dict(_type = "text",
                       value = (value != None and str(value)) or "")
        attr = StringWidget._attributes(field, default, **attributes)
        attr["_class"] = "hide"

        # Main Input
        fieldname = str(field)
        if "_id" in attr:
            real_input = attr["_id"]
        else:
            real_input = fieldname.replace(".", "_")

        if self.controller is None:
            controller = request.controller
        else:
            controller = self.controller

        # Embedded Form
        s3db = current.s3db
        ptable = s3db.pr_person
        ctable = s3db.pr_contact
        fields = [#ptable.first_name,
                  #ptable.middle_name,
                  #ptable.last_name,
                  ]
        if settings.get_pr_request_dob():
            fields.append(ptable.date_of_birth)
        if settings.get_pr_request_gender():
            fields.append(ptable.gender)

        if controller == "hrm":
            emailRequired = settings.get_hrm_email_required()
        elif controller == "vol":
            fields.append(s3db.pr_person_details.occupation)
            emailRequired = settings.get_hrm_email_required()
        else:
            emailRequired = False
        if emailRequired:
            validator = IS_EMAIL()
        else:
            validator = IS_NULL_OR(IS_EMAIL())

        fields.extend([Field("email",
                             notnull=emailRequired,
                             requires=validator,
                             label=T("Email Address")),
                       Field("mobile_phone",
                             label=T("Mobile Phone Number"),
                             # requires=None to work around a web2py bug
                             requires=None)
                       ])

        labels, required = s3_mark_required(fields)
        if required:
            s3.has_required = True

        if request.env.request_method == "POST" and not value:
            # Read the POST vars:
            post_vars = request.post_vars
            values = Storage(ptable._filter_fields(post_vars))
            values["email"] = post_vars["email"]
            values["mobile_phone"] = post_vars["mobile_phone"]

            # Use the validators to convert the POST vars into
            # internal format (not validating here):
            data = Storage()
            for f in fields:
                fname = f.name
                if fname in values:
                    v, error = values[fname], None
                    requires = f.requires
                    if requires:
                        if not isinstance(requires, (list, tuple)):
                            requires = [requires]
                        for validator in requires:
                            v, error = validator(v)
                            if error:
                                break
                    if not error:
                        data[fname] = v

            record_id = 0
        else:
            data = None
            record_id = value

        # Output
        rows = DIV()

        # Fields
        # (id, label, widget)
        fields = [()
                  ]
        
        # Name field
        # - can search for an existing person
        # - can create a new person
        # - multiple names get assigned to first, middle, last
        id = "%s_name" % fieldname
        label = T("Name")
        widget = INPUT(_value="",
                       _id=id,
                       )
        comment = T("Select this Person")
        throbber = DIV(_id="%s__throbber" % id,
                       _class="throbber hide"
                       )
        if formstyle == "bootstrap":
            # We would like to hide the whole original control-group & append rows, but that can't be done directly within a Widget
            # -> Elements moved via JS after page load
            label = LABEL("%s:" % label, _class="control-label",
                                         _for=id)
            # @ToDo: Mark Required
            widget.add_class("input-xlarge")
            # Currently unused, so remove if this remains so
            #from gluon.html import BUTTON
            #comment = BUTTON(comment,
            #                 _class="btn btn-primary hide",
            #                 _id="%s__button" % id
            #                 )
            #_controls = DIV(widget, throbber, comment, _class="controls")
            _controls = DIV(widget, throbber, _class="controls")
            row = DIV(label, _controls, _class="control-group hide", _id="%s__row" % id)
        elif callable(formstyle):
            # @ToDo: Test
            row = formstyle(id, label, widget, comment, hidden=hidden)
        else:
            # Unsupported
            raise
        rows.append(row)
        
        # Divider
        divider = DIV(DIV(_class="subheading"),
                      DIV(),
                      _class="box_bottom")
        rows.append(divider)

        # JS
        if s3.debug:
            script = "/%s/static/scripts/S3/s3.add_person.js" % appname
        else:
            script = "/%s/static/scripts/S3/s3.add_person.min.js" % appname
        scripts = s3.scripts
        if script not in scripts:
            scripts.append(script)
        s3.jquery_ready.append('''S3.addPersonWidget('%s')''' % fieldname)

        # Overall layout of components
        return TAG[""](DIV(INPUT(**attr), # Real input, hidden
                           _classs="hidden"),
                       rows,
                       )

# =============================================================================
class S3AutocompleteWidget(FormWidget):
    """
        Renders a SELECT as an INPUT field with AJAX Autocomplete
    """

    def __init__(self,
                 module,
                 resourcename,
                 fieldname = "name",
                 filter = "",       # REST filter
                 link_filter = "",
                 #new_items = False, # Whether to make this a combo box
                 post_process = "",
                 delay = 450,       # milliseconds
                 min_length = 2):   # Increase this for large deployments

        self.module = module
        self.resourcename = resourcename
        self.fieldname = fieldname
        self.filter = filter
        self.link_filter = link_filter
        #self.new_items = new_items
        self.post_process = post_process
        self.delay = delay
        self.min_length = min_length

        # @ToDo: Refreshes all dropdowns as-necessary
        self.post_process = post_process or ""

    def __call__(self, field, value, **attributes):

        default = dict(
            _type = "text",
            value = (value != None and str(value)) or "",
            )
        attr = StringWidget._attributes(field, default, **attributes)

        # Hide the real field
        attr["_class"] = attr["_class"] + " hide"

        if "_id" in attr:
            real_input = attr["_id"]
        else:
            real_input = str(field).replace(".", "_")
        dummy_input = "dummy_%s" % real_input

        # Script defined in static/scripts/S3/S3.js
        js_autocomplete = '''S3.autocomplete.normal('%s','%s','%s','%s','%s','%s',\"%s\",%s,%s)''' % \
            (self.fieldname, self.module, self.resourcename, real_input, self.filter,
             self.link_filter, self.post_process, self.delay, self.min_length)

        if value:
            try:
                value = long(value)
            except ValueError:
                pass
            text = s3_unicode(field.represent(value))
            if "<" in text:
                text = s3_strip_markup(text)
            represent = text
        else:
            represent = ""

        current.response.s3.jquery_ready.append(js_autocomplete)
        return TAG[""](INPUT(_id=dummy_input,
                             _class="string",
                             _value=represent.encode("utf-8")),
                       DIV(_id="%s_throbber" % dummy_input,
                           _class="throbber hide"),
                       INPUT(**attr),
                       requires = field.requires
                       )

# =============================================================================
class S3AutocompleteOrAddWidget(FormWidget):
    """
        This widget searches for or adds an object. It contains:

        - an autocomplete field which can be used to search for an existing object.
        - an add widget which is used to add an object.
            It fills the field with that object after successful addition
    """
    def __init__(self,
                 autocomplete_widget,
                 add_widget
                ):

        self.autocomplete_widget = autocomplete_widget
        self.add_widget = add_widget

    def __call__(self, field, value, **attributes):
        return TAG[""](# this does the input field
                       self.autocomplete_widget(field, value, **attributes),
                       # this can fill it if it isn't autocompleted
                       self.add_widget(field, value, **attributes)
                       )

# =============================================================================
class S3BooleanWidget(BooleanWidget):
    """
        Standard Boolean widget, with an option to hide/reveal fields conditionally.
    """

    def __init__(self,
                 fields = [],
                 click_to_show = True
                ):

        self.fields = fields
        self.click_to_show = click_to_show

    def __call__(self, field, value, **attributes):

        response = current.response
        fields = self.fields
        click_to_show = self.click_to_show

        default = dict(
                        _type="checkbox",
                        value=value,
                    )

        attr = BooleanWidget._attributes(field, default, **attributes)

        tablename = field.tablename

        hide = ""
        show = ""
        for _field in fields:
            fieldname = "%s_%s" % (tablename, _field)
            hide += '''
$('#%s__row1').hide()
$('#%s__row').hide()
''' % (fieldname, fieldname)
            show += '''
$('#%s__row1').show()
$('#%s__row').show()
''' % (fieldname, fieldname)

        if fields:
            checkbox = "%s_%s" % (tablename, field.name)
            click_start = '''
$('#%s').click(function(){
 if(this.checked){
''' % checkbox
            middle = "} else {\n"
            click_end = "}})"
            if click_to_show:
                # Hide by default
                script = '''%s\n%s\n%s\n%s\n%s\n%s''' % \
                    (hide, click_start, show, middle, hide, click_end)
            else:
                # Show by default
                script = '''%s\n%s\n%s\n%s\n%s\n%s''' % \
                    (show, click_start, hide, middle, show, click_end)
            response.s3.jquery_ready.append(script)

        return TAG[""](INPUT(**attr),
                       requires = field.requires
                       )

# =============================================================================
class S3CheckboxesWidget(OptionsWidget):
    """
        Generates a TABLE tag with <num_column> columns of INPUT
        checkboxes (multiple allowed)

        help_lookup_table_name_field will display tooltip help

        :param lookup_table_name: int -
        :param lookup_field_name: int -
        :param multple: int -

        :param options: list - optional -
        value,text pairs for the Checkboxs -
        If options = None,  use options from requires.options().
        This argument is useful for displaying a sub-set of the requires.options()

        :param num_column: int -

        :param help_lookup_field_name: string - optional -

        :param help_footer: string -

        Currently unused
    """

    def __init__(self,
                 lookup_table_name = None,
                 lookup_field_name = None,
                 multiple = False,
                 options = None,
                 num_column = 1,
                 help_lookup_field_name = None,
                 help_footer = None
                 ):

        self.lookup_table_name = lookup_table_name
        self.lookup_field_name =  lookup_field_name
        self.multiple = multiple
        self.options = options
        self.num_column = num_column
        self.help_lookup_field_name = help_lookup_field_name
        self.help_footer = help_footer

    # -------------------------------------------------------------------------
    def widget(self,
               field,
               value = None
               ):

        if current.db:
            db = current.db
        else:
            db = field._db

        lookup_table_name = self.lookup_table_name
        lookup_field_name = self.lookup_field_name
        if lookup_table_name and lookup_field_name:
            table = db[lookup_table_name]
            requires = IS_NULL_OR(IS_IN_DB(db,
                                   table.id,
                                   "%(" + lookup_field_name + ")s",
                                   multiple = multiple))
        else:
            requires = self.requires

        options = self.options
        if not options:
            if hasattr(requires, "options"):
                options = requires.options()
            else:
                raise SyntaxError, "widget cannot determine options of %s" % field

        values = s3_split_multi_value(value)

        attr = OptionsWidget._attributes(field, {})

        num_column = self.num_column
        num_row  = len(options) / num_column
        # Ensure division  rounds up
        if len(options) % num_column > 0:
             num_row = num_row +1

        t = TABLE(_id = str(field).replace(".", "_"))
        append = t.append
        for i in range(0, num_row):
            table_row = TR()
            for j in range(0, num_column):
                # Check that the index is still within options
                index = num_row * j + i
                if index < len(options):
                    input_options = {}
                    input_options = dict(requires = attr.get("requires", None),
                                         _value = str(options[index][0]),
                                         value = values,
                                         _type = "checkbox",
                                         _name = field.name,
                                         hideerror = True
                                        )
                    tip_attr = {}
                    help_text = ""
                    if self.help_lookup_field_name:
                        help_lookup_field_name = self.help_lookup_field_name
                        row = db(table.id == options[index][0]).select(table[help_lookup_field_name],
                                                                       limitby=(0, 1)).first()
                        if row:
                            help_text = str(P(row[help_lookup_field_name]))
                    if self.help_footer:
                        help_text = help_text + str(self.help_footer)
                    if help_text:
                        tip_attr = dict(_class = "s3_checkbox_label",
                                        #_title = options[index][1] + "|" + help_text
                                        _rel =  help_text
                                        )

                    #table_row.append(TD(A(options[index][1],**option_attr )))
                    table_row.append(TD(INPUT(**input_options),
                                        SPAN(options[index][1], **tip_attr)
                                        )
                                    )
            append(table_row)
        if self.multiple:
            append(TR(I("(Multiple selections allowed)")))
        return t

    # -------------------------------------------------------------------------
    def represent(self, value):

        db = current.db
        table = db[self.lookup_table_name]
        lookup_field_name = self.lookup_field_name
        list = []
        lappend = list.append
        # @ToDo: Optimise if widget ever used! Use belongs
        for id in s3_split_multi_value(value):
            if id:
                row = db(table.id == id).select(table[lookup_field_name],
                                                limitby=(0, 1)).first()
                if row:
                    lappend(row[lookup_field_name])
        if list and not None in list:
            return ", ".join(list)
        else:
            return None

# =============================================================================
class S3ColorPickerWidget(FormWidget):
    """
        Displays an <input type="color"> widget to allow the user to pick a
        color, and falls back to using JSColor or a regular text input if
        necessary.
    """

    DEFAULT_OPTIONS = {
        "showInput": True,
        "showInitial": True,
        "preferredFormat": "hex",
        "showPalette": True,
        "palette": ("red", "yellow", "green", "blue", "white", "black")
    }

    def __init__(self, options=None):
        """
            @param options: options for the JavaScript widget
            @see: http://bgrins.github.com/spectrum/
        """
        self.options = dict(self.DEFAULT_OPTIONS)
        self.options.update(options or {})

    def __call__(self, field, value, **attributes):
        s3 = current.response.s3
        app = current.request.application

        min = "" if s3.debug else ".min"

        script = "/%s/static/scripts/spectrum%s.js" % (app, min)
        style = "spectrum%s.css" % min

        if script not in s3.scripts:
            s3.scripts.append(script)

        if style not in s3.stylesheets:
            s3.stylesheets.append(style)

        s3.jquery_ready.append('''
var sp_options=%s
sp_options.change=function(color){this.value=color.toHex()}
$('.color').spectrum(sp_options)''' % json.dumps(self.options) if self.options else "")

        attr = self._attributes(field, {"_class": "color",
                                        "_value": value
                                        }, **attributes)

        return INPUT(**attr)

# =============================================================================
class S3DateWidget(FormWidget):
    """
        Standard Date widget, but with a modified yearRange to support Birth dates
    """

    def __init__(self,
                 format = None,
                 past=1440,     # how many months into the past the date can be set to
                 future=1440    # how many months into the future the date can be set to
                ):

        self.format = format
        self.past = past
        self.future = future

    def __call__(self, field, value, **attributes):

        # Need to convert value into ISO-format
        # (widget expects ISO, but value comes in custom format)
        _format = current.deployment_settings.get_L10n_date_format()
        v, error = IS_DATE_IN_RANGE(format=_format)(value)
        if not error:
            value = v.isoformat()

        if self.format:
            # default: "yy-mm-dd"
            format = str(self.format)
        else:
            format = _format.replace("%Y", "yy").replace("%y", "y").replace("%m", "mm").replace("%d", "dd").replace("%b", "M")

        default = dict(
                        _type = "text",
                        value = (value != None and str(value)) or "",
                    )
                    
        attr = StringWidget._attributes(field, default, **attributes)
        
        widget = INPUT(**attr)
        widget.add_class("date")

        if "_id" in attr:
            selector = attr["_id"]
        else:
            selector = str(field).replace(".", "_")

        current.response.s3.jquery_ready.append(
'''$('#%(selector)s').datepicker('option',{
 minDate:'-%(past)sm',
 maxDate:'+%(future)sm',
 yearRange:'c-100:c+100',
 dateFormat:'%(format)s'})''' % \
        dict(selector = selector,
             past = self.past,
             future = self.future,
             format = format))

        return TAG[""](widget, requires = field.requires)

# =============================================================================
class S3DateTimeWidget(FormWidget):
    """
        Date and/or time picker widget based on jquery.ui.datepicker and
        jquery.ui.timepicker.addon.js.
    """

    def __init__(self, **opts):
        """
            Constructor

            @param opts: the widget options

            @keyword date_format: the date format (falls back to
                                  deployment_settings.L10n.date_format)
            @keyword time_format: the time format (falls back to
                                  deployment_settings.L10n.time_format)
            @keyword separator: the date/time separator (falls back to
                                deployment_settings.L10n.datetime_separator)

            @keyword min: the earliest selectable datetime (datetime, overrides "past")
            @keyword max: the latest selectable datetime (datetime, overrides "future")
            @keyword past: the earliest selectable datetime relative to now (hours)
            @keyword future: the latest selectable datetime relative to now (hours)

            @keyword min_year: the earliest year in the drop-down (default: now-10 years)
            @keyword max_year: the latest year in the drop-down (default: now+10 years)

            @keyword hide_time: Hide the time selector (default: False)
            @keyword minute_step: number of minutes per slider step (default: 5)

            @keyword weeknumber: show week number in calendar widget (default: False)
            @keyword month_selector: show drop-down selector for month (default: False)
            @keyword year_selector: show drop-down selector for year (default: True)
            @keyword buttons: show the button panel (default: True)

            @keyword set_min: set a minimum for another datetime widget
            @keyword set_max: set a maximum for another datetime widget
        """

        self.opts = Storage(opts)
        self._class = "datetimepicker"

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):
        """
            Widget builder.

            @param field: the Field
            @param value: the current value
            @param attributes: the HTML attributes for the widget
        """

        self.inject_script(field, value, **attributes)

        default = dict(_type = "text", _class=self._class, value = value)
        attr = StringWidget._attributes(field, default, **attributes)

        if "_id" not in attr:
            attr["_id"] = str(field).replace(".", "_")

        widget = INPUT(**attr)
        widget.add_class(self._class)

        if self.opts.get("hide_time", False):
            widget.add_class("hide-time")

        return TAG[""](widget, requires = field.requires)

    # -------------------------------------------------------------------------
    def inject_script(self, field, value, **attributes):
        """
            Helper function to inject the document-ready-JavaScript for
            this widget.

            @param field: the Field
            @param value: the current value
            @param attributes: the HTML attributes for the widget
        """

        ISO = "%Y-%m-%dT%H:%M:%S"
        opts = self.opts

        if "_id" in attributes:
            selector = attributes["_id"]
        else:
            selector = str(field).replace(".", "_")

        settings = current.deployment_settings
        date_format = opts.get("date_format",
                               settings.get_L10n_date_format())
        time_format = opts.get("time_format",
                               settings.get_L10n_time_format())
        separator = opts.get("separator",
                             settings.get_L10n_datetime_separator())
        datetime_format = "%s%s%s" % (date_format, separator, time_format)

        # Option to hide the time slider
        hide_time = opts.get("hide_time", False)
        if hide_time:
            limit = "Date"
            widget = "datepicker"
            dtformat = date_format
        else:
            limit = "DateTime"
            widget = "datetimepicker"
            dtformat = datetime_format

        # Limits
        now = current.request.utcnow
        timedelta = datetime.timedelta
        offset = S3DateTime.get_offset_value(current.session.s3.utc_offset)

        if "min" in opts:
            earliest = opts["min"]
        else:
            past = opts.get("past", 876000)
            earliest = now - timedelta(hours = past)
        if "max" in opts:
            latest = opts["max"]
        else:
            future = opts.get("future", 876000)
            latest = now + timedelta(hours = future)

        # Closest minute step as default
        minute_step = opts.get("minute_step", 5)
        if not hide_time:
            if earliest <= now and now <= latest:
                start = now
            elif now < earliest:
                start = earliest
            elif now > latest:
                start = latest
            step = minute_step * 60
            seconds = (start - start.min).seconds
            rounding = (seconds + step / 2) // step * step
            rounded = start + timedelta(0, rounding - seconds,
                                            -start.microsecond)
            if rounded < earliest:
                rounded = earliest
            elif rounded > latest:
                rounded = latest
            if offset:
                rounded += timedelta(seconds=offset)
            default = rounded.strftime(dtformat)
        else:
            default = ""

        # Add timezone offset to limits
        if offset:
            earliest += timedelta(seconds=offset)
            latest += timedelta(seconds=offset)

        # Update limits of another widget?
        set_min = opts.get("set_min", None)
        set_max = opts.get("set_max", None)
        onclose = """function(selectedDate) {"""
        onclear = ""
        if set_min:
            onclose += """$('#%s').%s('option', 'minDate', selectedDate);""" % \
                       (set_min, widget)
            onclear += """$('#%s').%s('option', 'minDate', null);""" % \
                       (set_min, widget)
        if set_max:
            onclose += """$('#%s').%s('option', 'maxDate', selectedDate);""" % \
                       (set_max, widget)
            onclear += """$('#%s').%s('option', 'minDate', null);""" % \
                       (set_max, widget)
        onclose += """}"""

        # Translate Python format-strings
        date_format = settings.get_L10n_date_format().replace("%Y", "yy") \
                                                     .replace("%y", "y") \
                                                     .replace("%m", "mm") \
                                                     .replace("%d", "dd") \
                                                     .replace("%b", "M")

        time_format = settings.get_L10n_time_format().replace("%p", "TT") \
                                                     .replace("%I", "hh") \
                                                     .replace("%H", "HH") \
                                                     .replace("%M", "mm") \
                                                     .replace("%S", "ss")

        separator = settings.get_L10n_datetime_separator()

        # Other options
        firstDOW = settings.get_L10n_firstDOW()
        year_range = "%s:%s" % (opts.get("min_year", "-10"),
                                opts.get("max_year", "+10"))

        # Boolean options
        getopt = lambda opt, default: opts.get(opt, default) and "true" or "false"

        current.response.s3.jquery_ready.append(
"""$('#%(selector)s').%(widget)s({
   showSecond: false,
   firstDay: %(firstDOW)s,
   min%(limit)s: new Date(Date.parse('%(earliest)s')),
   max%(limit)s: new Date(Date.parse('%(latest)s')),
   dateFormat: '%(date_format)s',
   timeFormat: '%(time_format)s',
   separator: '%(separator)s',
   stepMinute: %(minute_step)s,
   showWeek: %(weeknumber)s,
   showButtonPanel: %(buttons)s,
   changeMonth: %(month_selector)s,
   changeYear: %(year_selector)s,
   yearRange: '%(year_range)s',
   useLocalTimezone: true,
   defaultValue: '%(default)s',
   onClose: %(onclose)s
});
var clear_button=$('<input id="%(selector)s_clear" type="button" value="clear"/>').click(function(){
 $('#%(selector)s').val('');%(onclear)s
});
if($('#%(selector)s_clear').length == 0){
 $('#%(selector)s').after(clear_button)
}""" % \
            dict(selector=selector,
                 widget=widget,

                 date_format=date_format,
                 time_format=time_format,
                 separator=separator,

                 weeknumber = getopt("weeknumber", False),
                 month_selector = getopt("month_selector", False),
                 year_selector = getopt("year_selector", True),
                 buttons = getopt("buttons", True),

                 firstDOW=firstDOW,
                 year_range=year_range,
                 minute_step=minute_step,

                 limit=limit,
                 earliest=earliest.strftime(ISO),
                 latest=latest.strftime(ISO),
                 default=default,

                 onclose=onclose,
                 onclear=onclear,
            )
        )

        return

# =============================================================================
class S3EmbedComponentWidget(FormWidget):
    """
        Widget used by S3CRUD for link-table components with actuate="embed".
        Uses s3.embed_component.js for client-side processing, and
        S3CRUD._postprocess_embedded to receive the data.
    """

    def __init__(self,
                 link=None,
                 component=None,
                 widget=None,
                 autocomplete=None,
                 link_filter=None,
                 select_existing=True):

        self.link = link
        self.component = component
        self.widget = widget
        self.autocomplete = autocomplete
        self.select_existing = select_existing
        self.link_filter = link_filter

    def __call__(self, field, value, **attributes):

        T = current.T
        db = current.db
        s3db = current.s3db

        request = current.request
        appname = request.application
        s3 = current.response.s3
        appname = current.request.application

        formstyle = s3.crud.formstyle

        link = self.link
        ltable = s3db[link]
        ctable = s3db[self.component]

        prefix, resourcename = self.component.split("_", 1)
        if field.name in request.post_vars:
            selected = request.post_vars[field.name]
        else:
            selected = None

        # Main Input
        default = dict(_type = "text",
                       value = (value != None and str(value)) or "")
        attr = StringWidget._attributes(field, default, **attributes)
        attr["_class"] = "hide"

        if "_id" in attr:
            real_input = attr["_id"]
        else:
            real_input = str(field).replace(".", "_")
        dummy = "dummy_%s" % real_input

        if self.select_existing:
            _class ="box_top"
        else:
            _class = "hide"

        # Post-process selection/deselection
        post_process = s3db.get_config(link, "post_process")
        if post_process is not None:
            try:
                if self.autocomplete:
                    pp = post_process % real_input
                else:
                    pp = post_process % dummy
            except:
                pp = post_process
        else:
            pp = None

        clear = "clear_component_form();"
        if pp is not None:
            clear = "%s%s" % (clear, pp)

        # Select from registry buttons
        url = "/%s/%s/%s/" % (appname, prefix, resourcename)
        select_row = TR(TD(A(T("Select from registry"),
                             _href="#",
                             _id="select_from_registry",
                             _class="action-btn"),
                           A(T("Remove selection"),
                             _href="#",
                             _onclick=clear,
                             _id="clear_form_link",
                             _class="action-btn hide",
                             _style="padding-left:15px;"),
                           A(T("Edit Details"),
                             _href="#",
                             _onclick="edit_selected_form();",
                             _id="edit_selected_link",
                             _class="action-btn hide",
                             _style="padding-left:15px;"),
                           DIV(_id="load_throbber",
                               _class="throbber hide",
                               _style="padding-left:85px;"),
                           _class="w2p_fw"),
                        TD(),
                        _id="select_from_registry_row",
                        _class=_class,
                        _controller=prefix,
                        _component=self.component,
                        _url=url,
                        _field=real_input,
                        _value=str(value))

        # Autocomplete/Selector
        autocomplete = self.autocomplete
        if autocomplete:
            ac_field = ctable[autocomplete]
            select = "select_component($('#%s').val());" % real_input
            if pp is not None:
                select = "%s%s" % (pp, select)
            widget = S3AutocompleteWidget(prefix,
                                          resourcename=resourcename,
                                          fieldname=autocomplete,
                                          link_filter=self.link_filter,
                                          post_process=select)
            ac_row = TR(TD(LABEL("%s: " % ac_field.label,
                                 _class="hide",
                                 _id="component_autocomplete_label"),
                        widget(field, value)),
                        TD(),
                        _id="component_autocomplete_row",
                        _class="box_top")
        else:
            select = "select_component($('#%s').val());" % dummy
            if pp is not None:
                select = "%s%s" % (pp, select)
            # @todo: add link_filter here as well
            widget = OptionsWidget.widget
            ac_row = TR(TD(LABEL("%s: " % field.label,
                                 _class="hide",
                                 _id="component_autocomplete_label"),
                           widget(field, None, _class="hide",
                                  _id=dummy, _onchange=select)),
                        TD(INPUT(_id=real_input, _class="hide")),
                        _id="component_autocomplete_row",
                        _class="box_top")

        # Embedded Form
        fields = [f for f in ctable
                    if (f.writable or f.readable) and not f.compute]
        if selected:
            # Initialize validators with the correct record ID
            for f in fields:
                requires = f.requires or []
                if not isinstance(requires, (list, tuple)):
                    requires = [requires]
                [r.set_self_id(selected) for r in requires
                                         if hasattr(r, "set_self_id")]
        labels, required = s3_mark_required(fields)
        if required:
            s3.has_required = True
        form = SQLFORM.factory(table_name=self.component,
                               labels=labels,
                               formstyle=formstyle,
                               upload="default/download",
                               separator = "",
                               *fields)
        trs = []
        att = "box_middle embedded"
        for tr in form[0]:
            if not tr.attributes["_id"].startswith("submit_record"):
                if "_class" in tr.attributes:
                    tr.attributes["_class"] = "%s %s" % (tr.attributes["_class"], att)
                else:
                    tr.attributes["_class"] = att
                trs.append(tr)
        table = DIV(*trs)

        # Divider
        divider = TR(TD(_class="subheading"), TD(), _class="box_bottom embedded")

        # JavaScript
        if s3.debug:
            script = "s3.embed_component.js"
        else:
            script = "s3.embed_component.min.js"

        s3.scripts.append("/%s/static/scripts/S3/%s" % (appname, script))

        # Overall layout of components
        return TAG[""](select_row,
                       ac_row,
                       table,
                       divider,
                       )

# -----------------------------------------------------------------------------
def S3GenericAutocompleteTemplate(post_process,
                                  delay,
                                  min_length,
                                  field,
                                  value,
                                  attributes,
                                  source,
                                  transform_value = lambda value: value,
                                  new_items = False,    # Allow new items
                                  tablename = None,     # Needed if new_items=True
                                  ):
    """
        Renders a SELECT as an INPUT field with AJAX Autocomplete
    """

    value = transform_value(value)

    default = dict(
        _type = "text",
        value = (value != None and s3_unicode(value)) or "",
        )
    attr = StringWidget._attributes(field, default, **attributes)

    # Hide the real field
    attr["_class"] = attr["_class"] + " hide"

    if "_id" in attr:
        real_input = attr["_id"]
    else:
        real_input = str(field).replace(".", "_")

    dummy_input = "dummy_%s" % real_input

    if value:
        try:
            value = long(value)
        except ValueError:
            pass
        # Provide the representation for the current/default Value
        text = s3_unicode(field.represent(value))
        if "<" in text:
            text = s3_strip_markup(text)
        represent = text.encode("utf-8")
    else:
        represent = ""

    script = '''S3.autocomplete.generic('%(url)s','%(input)s',"%(postprocess)s",%(delay)s,%(min_length)s)''' % \
            dict(url = source,
                 input = real_input,
                 postprocess = post_process,
                 delay = delay,
                 min_length = min_length,
                 )
    current.response.s3.jquery_ready.append(script)
    return TAG[""](INPUT(_id=dummy_input,
                         _class="string",
                         value=represent),
                   DIV(_id="%s_throbber" % dummy_input,
                       _class="throbber hide"),
                   INPUT(**attr),
                   requires = field.requires
                   )

#==============================================================================
class S3GroupedOptionsWidget(FormWidget):
    """ Widget with grouped checkboxes for S3OptionsFilter """

    def __init__(self,
                 options=None,
                 multiple=True,
                 size=None,
                 cols=None,
                 help_field=None,
                 none=None):
        """
            Constructor

            @param options: the options for the SELECT, as list of tuples
                            [(value, label)], or as dict {value: label},
                            or None to auto-detect the options from the
                            Field when called
            @param multiple: multiple options can be selected
            @param size: maximum number of options in merged letter-groups,
                         None to not group options by initial letter
            @param cols: number of columns for the options table
            @param help_field: field in the referenced table to retrieve
                               a tooltip text from (for foreign keys only)
            @param none: True to render "None" as normal option
        """

        self.options = options
        self.multiple = multiple
        self.size = size
        self.cols = cols or 3
        self.help_field = help_field
        self.none = none

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):
        """
            Render this widget

            @param field: the Field
            @param value: the currently selected value(s)
            @param attributes: HTML attributes for the widget
        """

        fieldname = field.name

        attr = Storage(attributes)
        if "_id" in attr:
            _id = attr.pop("_id")
        else:
            _id = "%s-options" % fieldname
        attr["_id"] = _id
        if "_name" not in attr:
            attr["_name"] = fieldname

        options = self._options(field, value)
        if "empty" in options:
            widget = DIV(SPAN(options["empty"],
                              _class="no-options-available"),
                         INPUT(_type="hidden",
                               _name=fieldname,
                               _value=None),
                         **attr)
        else:
            groups = options["groups"]
            if self.multiple:
                attr["_multiple"] = "multiple"
            widget = SELECT(**attr)
            append = widget.append
            render_group = self._render_group
            for group in groups:
                options = render_group(group)
                for option in options:
                    append(option)

            script = '''$('#%s').groupedopts({columns: %s})''' % (_id, self.cols)
            current.response.s3.jquery_ready.append(script)
        
        return widget

    # -------------------------------------------------------------------------
    def _render_group(self, group):
        """
            Helper method to render an options group

            @param group: the group as dict {label:label, items:[items]}
        """

        items = group["items"]
        if items:
            label = group["label"]
            render_item = self._render_item
            options = [render_item(i) for i in items]
            if label:
                return [OPTGROUP(options, _label=label)]
            else:
                return options
        else:
            return None

    # -------------------------------------------------------------------------
    def _render_item(self, item):
        """
            Helper method to render one option

            @param item: the item as tuple (key, label, value, tooltip),
                         value=True indicates that the item is selected
        """

        key, label, value, tooltip = item
        attr = {"_value": key}
        if value:
            attr["_selected"] = "selected"
        if tooltip:
            attr["_title"] = tooltip
        return OPTION(label, **attr)

    # -------------------------------------------------------------------------
    def _options(self, field, value):
        """
            Find, group and sort the options

            @param field: the Field
            @param value: the currently selected value(s)
        """

        options = self.options
        help_field = self.help_field

        # Get the current values as list of unicode
        if not isinstance(value, (list, tuple)):
            values = [value]
        else:
            values = value
        values = [s3_unicode(v) for v in values]

        # Get the options as sorted list of tuples (key, value)
        if options is None:
            requires = field.requires
            if not isinstance(requires, (list, tuple)):
                requires = [requires]
            if hasattr(requires[0], "options"):
                options = requires[0].options()
            else:
                options = []
        elif isinstance(options, dict):
            options = options.items()
        none = self.none
        exclude = ("",) if none is not None else ("", None)
        options = [(s3_unicode(k) if k is not None else none, s3_unicode(v))
                   for k, v in options if k not in exclude]

        # No options available?
        if not options:
            return {"empty": T("no options available")}

        # Get the tooltips as dict {key: tooltip}
        helptext = {}
        if help_field:
            if callable(help_field):
                help_field = help_field(options)
            if isinstance(help_field, dict):
                for key in help_field.keys():
                    helptext[s3_unicode(key)] = help_field[key]
            else:
                ktablename, pkey, multiple = s3_get_foreign_key(field)
                if ktablename is not None:
                    ktable = current.s3db[ktablename]
                    if hasattr(ktable, help_field):
                        keys = [k for k, v in options if k.isdigit()]
                        query = ktable[pkey].belongs(keys)
                        rows = current.db(query).select(ktable[pkey],
                                                        ktable[help_field])
                        for row in rows:
                            helptext[unicode(row[pkey])] = row[help_field]

        # Get all letters and their options
        letter_options = {}
        for key, label in options:
            letter = label
            if letter:
                letter = s3_unicode(label).upper()[0]
                if letter in letter_options:
                    letter_options[letter].append((key, label))
                else:
                    letter_options[letter] = [(key, label)]
        all_letters = letter_options.keys()

        # Sort letters
        import locale
        all_letters.sort(locale.strcoll)
        first_letter = min(u"A", all_letters[0])
        last_letter = max(u"Z", all_letters[-1])

        size = self.size
        cols = self.cols

        close_group = self._close_group

        if size and len(options) > size and len(letter_options) > 1:
            # Multiple groups

            groups = []
            group = {"letters": [first_letter], "items": []}

            for letter in all_letters:

                group_items = group["items"]
                current_size = len(group_items)
                items = letter_options[letter]

                if current_size and current_size + len(items) > size:

                    # Close + append this group
                    close_group(group, values, helptext)
                    groups.append(group)

                    # Start a new group
                    group = {"letters": [letter], "items": items}

                else:

                    # Append current letter
                    if letter != group["letters"][-1]:
                        group["letters"].append(letter)

                    # Append items
                    group["items"].extend(items)

            if len(group["items"]):
                if group["letters"][-1] != last_letter:
                    group["letters"].append(last_letter)
                close_group(group, values, helptext)
                groups.append(group)

        else:
            # Only one group
            group = {"letters": None, "items": options}
            close_group(group, values, helptext)
            groups = [group]

        return {"groups": groups}

    # -------------------------------------------------------------------------
    @staticmethod
    def _close_group(group, values, helptext):
        """
            Helper method to finalize an options group, render its label
            and sort the options

            @param group: the group as dict {letters: [], items: []}
            @param values: the currently selected values as list
            @param helptext: dict of {key: helptext} for the options
        """

        # Construct the group label
        group_letters = group["letters"]
        if group_letters:
            if len(group_letters) > 1:
                group["label"] = "%s - %s" % (group_letters[0],
                                              group_letters[-1])
            else:
                group["label"] = group_letters[0]
        else:
            group["label"] = None
        del group["letters"]

        # Sort the group items
        group_items = sorted(group["items"], key=lambda i: i[1].upper()[0])

        # Add tooltips
        items = []
        for key, label in group_items:
            if helptext and key in helptext:
                tooltip = helptext[key]
            else:
                tooltip = None
            item = (key, label, key in values, tooltip)
            items.append(item)

        group["items"] = items
        return

# =============================================================================
class S3HiddenWidget(StringWidget):
    """
        Standard String widget, but with a class of hide
        - used by CAP
    """

    def __call__(self, field, value, **attributes):

        default = dict(
            _type = "text",
            value = (value != None and str(value)) or "",
            )
        attr = StringWidget._attributes(field, default, **attributes)
        attr["_class"] = "hide %s" % attr["_class"]

        return TAG[""](INPUT(**attr),
                       requires = field.requires
                       )

# =============================================================================
class S3HumanResourceAutocompleteWidget(FormWidget):
    """
        Renders an hrm_human_resource SELECT as an INPUT field with
        AJAX Autocomplete.

        Differs from the S3AutocompleteWidget in that it uses:
            3 name fields
            Organisation
            Job Role
   """

    def __init__(self,
                 post_process = "",
                 delay = 450,   # milliseconds
                 min_length=2,  # Increase this for large deployments
                 group = "",    # Filter to staff/volunteers
                 ):

        self.post_process = post_process
        self.delay = delay
        self.min_length = min_length
        self.group = group

    def __call__(self, field, value, **attributes):

        default = dict(
            _type = "text",
            value = (value != None and str(value)) or "",
            )
        attr = StringWidget._attributes(field, default, **attributes)

        # Hide the real field
        attr["_class"] = "%s hide" % attr["_class"]

        if "_id" in attr:
            real_input = attr["_id"]
        else:
            real_input = str(field).replace(".", "_")
        dummy_input = "dummy_%s" % real_input

        if value:
            try:
                value = long(value)
            except ValueError:
                pass
            # Provide the representation for the current/default Value
            text = s3_unicode(field.represent(value))
            if "<" in text:
                text = s3_strip_markup(text)
            represent = text
        else:
            represent = ""

        script = '''S3.autocomplete.hrm('%(group)s','%(input)s',"%(postprocess)s",%(delay)s,%(min_length)s)''' % \
            dict(group = self.group,
                 input = real_input,
                 postprocess = self.post_process,
                 delay = self.delay,
                 min_length = self.min_length,
                 )
        current.response.s3.jquery_ready.append(script)
        return TAG[""](INPUT(_id=dummy_input,
                             _class="string",
                             _value=represent.encode("utf-8")),
                       DIV(_id="%s_throbber" % dummy_input,
                           _class="throbber hide"),
                       INPUT(**attr),
                       requires = field.requires
                       )

# =============================================================================
class S3ImageCropWidget(FormWidget):
    """
        Allows the user to crop an image and uploads it.
        Cropping is done client-side where supported, otherwise using PIL.

        @ToDo: Doesn't currently work with Inline Component Forms
    """

    DEFAULT_WIDTH = 300

    def __init__(self, image_bounds=None):
        self.image_bounds = image_bounds

    def __call__(self, field, value, download_url=None, **attributes):

        T = current.T
        CROP_IMAGE = T("Crop Image")

        script_dir = "/%s/static/scripts" % current.request.application

        s3 = current.response.s3
        debug = s3.debug
        scripts = s3.scripts

        if debug:
            script = "%s/jquery.color.js" % script_dir
            if script not in scripts:
                scripts.append(script)
            script = "%s/jquery.Jcrop.js" % script_dir
            if script not in scripts:
                scripts.append(script)
            script = "%s/S3/s3.imagecrop.widget.js" % script_dir
            if script not in scripts:
                scripts.append(script)
                s3.js_global.append('''
i18n.invalid_image='%s'
i18n.crop_image='%s'
i18n.cancel_crop="%s"''' % (T("Please select a valid image!"),
                            CROP_IMAGE,
                            T("Cancel Crop")))
        else:
            script = "%s/S3/s3.imagecrop.widget.min.js" % script_dir
            if script not in scripts:
                scripts.append(script)
                s3.js_global.append('''
i18n.invalid_image='%s'
i18n.crop_image='%s'
i18n.cancel_crop="%s"''' % (T("Please select a valid image!"),
                            CROP_IMAGE,
                            T("Cancel Crop")))

        stylesheets = s3.stylesheets
        sheet = "plugins/jquery.Jcrop.css"
        if sheet not in stylesheets:
            stylesheets.append(sheet)

        attr = self._attributes(field, {
                "_type": "file",
                "_class": "imagecrop-upload"
            }, **attributes)

        elements = [INPUT(_type="hidden", _name="imagecrop-points")]
        append = elements.append

        if value and download_url:
            if callable(download_url):
                download_url = download_url()

            url = "%s/%s" % (download_url ,value)

            append(IMG(_src=url,
                       _class="imagecrop-preview",
                       _style="display:hidden;",
                       _width="%spx" % self.DEFAULT_WIDTH))
            append(P(T("You can select an area on the image and save to crop it."),
                     _class="imagecrop-help",
                     _style="display:none;"))
            append(INPUT(_value=CROP_IMAGE,
                         _type="button",
                         _class="imagecrop-toggle"))
            append(INPUT(**attr))
            # Set up the canvas
            canvas = TAG["canvas"](_class="imagecrop-canvas",
                                   _style="display:none;")
            append(canvas)

        else:
            append(DIV(_class="tooltip",
                       _title="%s|%s" % \
                (CROP_IMAGE,
                 T("Select an image to upload. You can crop this later by opening this record."))))
            # Set up the canvas
            canvas = TAG["canvas"](_class="imagecrop-canvas",
                                   _style="display:none;")
            image_bounds = self.image_bounds
            if image_bounds:
                canvas.attributes["_width"] = image_bounds[0]
                canvas.attributes["_height"] = image_bounds[1]
                canvas.attributes["_style"] = "background:black;"
            append(INPUT(**attr))
            append(INPUT(_type="hidden",
                         _name="imagecrop-data",
                         _class="imagecrop-data"))
            append(P(T("Drag an image below to crop and scale it before uploading it:")))
            append(canvas)

        # Prevent multiple widgets on the same page from interfering with each
        # other.
        import uuid
        uid = "cropwidget-%s" % uuid.uuid4().hex
        for element in elements:
            element.attributes["_data-uid"] = uid

        return DIV(elements)

# =============================================================================
class S3InvBinWidget(FormWidget):
    """
        Widget used by S3CRUD to offer the user matching bins where
        stock items can be placed
    """

    def __init__(self,
                 tablename,):
        self.tablename = tablename

    def __call__(self, field, value, **attributes):

        T = current.T
        request = current.request
        s3db = current.s3db
        tracktable = s3db.inv_track_item
        stocktable = s3db.inv_inv_item

        new_div = INPUT(value = value or "",
                        requires = field.requires,
                        _id = "i_%s_%s" % (self.tablename, field.name),
                        _name = field.name,
                       )
        id = None
        function = self.tablename[4:]
        if len(request.args) > 2:
            if request.args[1] == function:
                id = request.args[2]

        if id == None or tracktable[id] == None:
            return TAG[""](
                           new_div
                          )

        record = tracktable[id]
        site_id = s3db.inv_recv[record.recv_id].site_id
        query = (stocktable.site_id == site_id) & \
                (stocktable.item_id == record.item_id) & \
                (stocktable.item_source_no == record.item_source_no) & \
                (stocktable.item_pack_id == record.item_pack_id) & \
                (stocktable.currency == record.currency) & \
                (stocktable.pack_value == record.pack_value) & \
                (stocktable.expiry_date == record.expiry_date) & \
                (stocktable.supply_org_id == record.supply_org_id)
        rows = current.db(query).select(stocktable.bin,
                                        stocktable.id)
        if len(rows) == 0:
            return TAG[""](
                           new_div
                          )
        bins = []
        for row in rows:
            bins.append(OPTION(row.bin))

        match_lbl = LABEL(T("Select an existing bin"))
        match_div = SELECT(bins,
                          _id = "%s_%s" % (self.tablename, field.name),
                          _name = field.name,
                         )
        new_lbl = LABEL(T("...or add a new bin"))
        return TAG[""](match_lbl,
                       match_div,
                       new_lbl,
                       new_div
                       )

# =============================================================================
class S3KeyValueWidget(ListWidget):
    """
        Allows for input of key-value pairs and stores them as list:string
    """

    def __init__(self, key_label=None, value_label=None):
        """
            Returns a widget with key-value fields
        """
        self._class = "key-value-pairs"
        T = current.T

        self.key_label = key_label or T("Key")
        self.value_label = value_label or T("Value")

    def __call__(self, field, value, **attributes):
        T = current.T
        s3 = current.response.s3

        _id = "%s_%s" % (field._tablename, field.name)
        _name = field.name
        _class = "text hide"

        attributes["_id"] = _id
        attributes["_name"] = _name
        attributes["_class"] = _class

        script = SCRIPT(
'''jQuery(document).ready(function(){jQuery('#%s').kv_pairs('%s','%s')})''' % \
    (_id, self.key_label, self.value_label))

        if not value: value = "[]"
        if not isinstance(value, str):
            try:
                value = json.dumps(value)
            except:
                raise("Bad value for key-value pair field")
        appname = current.request.application
        jsfile = "/%s/static/scripts/S3/%s" % (appname, "s3.keyvalue.widget.js")

        if jsfile not in s3.scripts:
            s3.scripts.append(jsfile)

        return TAG[""](
                    TEXTAREA(value, **attributes),
                    script
               )

    @staticmethod
    def represent(value):
        if isinstance(value, str):
            try:
                value = json.loads(value)
                if isinstance(value, str):
                    raise ValueError("key-value JSON is wrong.")
            except:
                # XXX: log this!
                #raise ValueError("Bad json was found as value for a key-value field: %s" % value)
                return ""

        rep = []
        if isinstance(value, (tuple, list)):
            for kv in value:
                rep += ["%s: %s" % (kv["key"], kv["value"])]
        return ", ".join(rep)

# =============================================================================
class S3LatLonWidget(DoubleWidget):
    """
        Widget for latitude or longitude input, gives option to input in terms
        of degrees, minutes and seconds
    """

    def __init__(self, type, switch_button=False, disabled=False):
        self._id = "gis_location_%s" % type
        self._name = self._id
        self.disabled = disabled
        self.switch_button = switch_button

    def widget(self, field=None, value=None):

        T = current.T
        s3 = current.response.s3

        attr = dict(value=value,
                    _class="decimal %s" % self._class,
                    _id=self._id,
                    _name=self._name)

        attr_dms = dict()

        if self.disabled:
            attr["_disabled"] = "disabled"
            attr_dms["_disabled"] = "disabled"

        dms_boxes = SPAN(
                        INPUT(_class="degrees", **attr_dms), "° ",
                        INPUT(_class="minutes", **attr_dms), "' ",
                        INPUT(_class="seconds", **attr_dms), "\" ",
                        ["",
                            DIV(A(T("Use decimal"),
                                    _class="action-btn gis_coord_switch_decimal"))
                        ][self.switch_button],
                        _style="display: none;",
                        _class="gis_coord_dms"
                    )

        decimal = SPAN(
                        INPUT(**attr),
                        ["",
                            DIV(A(T("Use deg, min, sec"),
                                    _class="action-btn gis_coord_switch_dms"))
                        ][self.switch_button],
                        _class="gis_coord_decimal"
                  )

        if not s3.lat_lon_i18n_appended:
            s3.js_global.append('''
i18n.gis_only_numbers={degrees:'%s',minutes:'%s',seconds:'%s',decimal:'%s'}
i18n.gis_range_error={degrees:{lat:'%s',lon:'%s'},minutes:'%s',seconds:'%s',decimal:{lat:'%s',lon:'%s'}}
''' %  (T("Degrees must be a number."),
        T("Minutes must be a number."),
        T("Seconds must be a number."),
        T("Degrees must be a number."),
        T("Degrees in a latitude must be between -90 to 90."),
        T("Degrees in a longitude must be between -180 to 180."),
        T("Minutes must be less than 60."),
        T("Seconds must be less than 60."),
        T("Latitude must be between -90 and 90."),
        T("Longitude must be between -180 and 180.")))

            s3.lat_lon_i18n_appended = True

        if (field == None):
            return SPAN(decimal,
                        dms_boxes,
                        _class="gis_coord_wrap")
        else:
            return SPAN(decimal,
                        dms_boxes,
                        *controls,
                        requires = field.requires,
                        _class="gis_coord_wrap"
                        )

# =============================================================================
class S3LocationAutocompleteWidget(FormWidget):
    """
        Renders a gis_location SELECT as an INPUT field with AJAX Autocomplete

        Appropriate when the location has been previously created (as is the
        case for location groups or other specialized locations that need
        the location create form).
        S3LocationSelectorWidget is generally more appropriate for specific locations.

        Currently used for selecting the region location in gis_config
        and for project/location.
    """

    def __init__(self,
                 prefix="gis",
                 resourcename="location",
                 fieldname="name",
                 level="",
                 hidden = False,
                 post_process = "",
                 delay = 450,     # milliseconds
                 min_length = 2): # Increase this for large deployments

        self.prefix = prefix
        self.resourcename = resourcename
        self.fieldname = fieldname
        self.level = level
        self.hidden = hidden
        self.post_process = post_process
        self.delay = delay
        self.min_length = min_length

    def __call__(self, field, value, **attributes):
        fieldname = self.fieldname
        level = self.level
        if level:
            if isinstance(level, list):
                levels = ""
                counter = 0
                for _level in level:
                    levels += _level
                    if counter < len(level):
                        levels += "|"
                    counter += 1
                url = URL(c=self.prefix,
                          f=self.resourcename,
                          args="search_ac",
                          vars={"filter":"~",
                                "field":fieldname,
                                "level":levels,
                                })
            else:
                url = URL(c=self.prefix,
                          f=self.resourcename,
                          args="search_ac",
                          vars={"filter":"~",
                                "field":fieldname,
                                "level":level,
                                })
        else:
            url = URL(c=self.prefix,
                      f=self.resourcename,
                      args="search_ac",
                      vars={"filter":"~",
                            "field":fieldname,
                            })

        return S3GenericAutocompleteTemplate(
            self.post_process,
            self.delay,
            self.min_length,
            field,
            value,
            attributes,
            source = url,
        )

# =============================================================================
class S3LocationDropdownWidget(FormWidget):
    """
        Renders a dropdown for an Lx level of location hierarchy

    """

    def __init__(self, level="L0", default=None, empty=False):
        """ Set Defaults """
        self.level = level
        self.default = default
        self.empty = empty

    def __call__(self, field, value, **attributes):

        level = self.level
        default = self.default
        empty = self.empty

        s3db = current.s3db
        table = s3db.gis_location
        if level:
            query = (table.deleted != True) & \
                    (table.level == level)
        else:
            # Workaround for merge form
            query = (table.id == value)
        locations = current.db(query).select(table.name,
                                             table.id,
                                             cache=s3db.cache)
        opts = []
        for location in locations:
            opts.append(OPTION(location.name, _value=location.id))
            if not value and default and location.name == default:
                value = location.id
        locations = locations.as_dict()
        attr = dict(attributes)
        attr["_type"] = "int"
        attr["value"] = value
        attr_dropdown = OptionsWidget._attributes(field, attr)
        requires = IS_IN_SET(locations)
        if empty:
            requires = IS_NULL_OR(requires)
        attr_dropdown["requires"] = requires

        attr_dropdown["represent"] = \
            lambda id: locations["id"]["name"] or UNKNOWN_OPT

        return TAG[""](SELECT(*opts, **attr_dropdown),
                       requires=field.requires
                       )

# =============================================================================
class S3LocationSelectorWidget(FormWidget):
    """
        Renders a gis_location Foreign Key to allow inline display/editing of linked fields.

        Designed for use for Resources which require a Specific Location, such as Sites, Persons, Assets, Incidents, etc
        Not currently suitable for Resources which require a Hierarchical Location, such as Projects, Assessments, Plans, etc
        - S3LocationAutocompleteWidget is more appropriate for these.

        Can also be used to transparently wrap simple sites (such as project_site) using the IS_SITE_SELECTOR() validator

        It uses s3.locationselector.widget.js to do all client-side functionality.
        It requires the IS_LOCATION_SELECTOR() validator to process Location details upon form submission.

        Create form
            Active Tab: 'Create New Location'
                Country Dropdown (to set the Number & Labels of Hierarchy)
                Building Name (deployment_setting to hide)
                Street Address (Line1/Line2?)
                    @ToDo: Trigger a geocoder lookup onblur
                Postcode
                @ToDo: Mode Strict:
                    Lx as dropdowns. Default label is 'Select previous to populate this dropdown' (Fixme!)
                Mode not Strict (default):
                    L2-L5 as Autocompletes which create missing locations automatically
                    @ToDo: Lx as Dropdown (where the 'Edit Lx' is set)
                Map:
                    @ToDo: Inline or Popup? (Deployment Option?)
                    Set Map Viewport to default on best currently selected Hierarchy
                        @ToDo: L1+
                Lat Lon
            Inactive Tab: 'Select Existing Location'
                Needs 2 modes:
                    Specific Locations only - for Sites/Incidents
                    @ToDo: Hierarchies ok (can specify which) - for Projects/Documents
                @ToDo: Hierarchical Filters above the Search Box
                    Search is filtered to values shown
                    Filters default to any hierarchy selected on the Create tab?
                Button to explicitly say 'Select this Location' which sets all the fields (inc hidden ID) & the UUID var
                    Tabs then change to View/Edit

        Update form
            Update form has uuid set server-side & hence S3.gis.uuid set client-side
            Assume location is shared by other resources
                Active Tab: 'View Location Details' (Fields are read-only)
                Inactive Tab: 'Edit Location Details' (Fields are writable)
                @ToDo: Inactive Tab: 'Move Location': Defaults to Searching for an Existing Location, with a button to 'Create New Location'

        @see: http://eden.sahanafoundation.org/wiki/BluePrintGISLocationSelector

        @ToDo: Support multiple in a page:
               http://eden.sahanafoundation.org/ticket/1223
    """

    def __init__(self,
                 catalog_layers=False,
                 hide_address=False,
                 site_type=None,
                 polygon=False):

        self.catalog_layers = catalog_layers
        self.hide_address = hide_address
        self.site_type = site_type
        self.polygon = polygon

    def __call__(self, field, value, **attributes):

        T = current.T
        db = current.db
        s3db = current.s3db
        gis = current.gis

        auth = current.auth
        settings = current.deployment_settings
        response = current.response
        s3 = current.response.s3
        location_selector_loaded = s3.gis.location_selector_loaded
        # @ToDo: Don't insert JS snippets when location_selector already loaded

        appname = current.request.application

        locations = s3db.gis_location
        ctable = s3db.gis_config

        requires = field.requires

        # Main Input
        defaults = dict(_type = "text",
                        value = (value != None and str(value)) or "")
        attr = StringWidget._attributes(field, defaults, **attributes)
        # Hide the real field
        attr["_class"] = "hide"

        # Is this a Site?
        site = ""
        if self.site_type:
            # We are acting on a site_id not location_id
            # Store the real variables
            #site_value = value
            #site_field = field
            # Ensure that we have a name for the Location visible
            settings.gis.building_name = True
            # Set the variables to what they would be for a Location
            stable = s3db[self.site_type]
            field = stable.location_id
            if value:
                query = (stable.id == value)
                record = db(query).select(stable.location_id,
                                          limitby=(0, 1)).first()
                if record:
                    value = record.location_id
                    defaults = dict(_type = "text",
                                    value = str(value))
                else:
                    raise HTTP(404)
        else:
            # Check for being a location_id on a site type
            # If so, then the JS defaults the Building Name to Site Name
            tablename = field.tablename
            if tablename in auth.org_site_types:
                site = tablename

        # Full list of countries (by ID)
        countries = gis.get_countries()

        # Countries we should select from
        _countries = settings.get_gis_countries()
        if _countries:
            __countries = gis.get_countries(key_type="code")
            countrynames = []
            append = countrynames.append
            for k, v in __countries.iteritems():
                if k in _countries:
                    append(v)
            for k, v in countries.iteritems():
                if v not in countrynames:
                    del countries[k]

        # Read Options
        config = gis.get_config()
        default_L0 = Storage()
        country_snippet = ""
        if value:
            default_L0.id = gis.get_parent_country(value)
        elif config.default_location_id:
            # Populate defaults with IDs & Names of ancestors at each level
            defaults = gis.get_parent_per_level(defaults,
                                                config.default_location_id,
                                                feature=None,
                                                ids=True,
                                                names=True)
            query = (locations.id == config.default_location_id)
            default_location = db(query).select(locations.level,
                                                locations.name).first()
            if default_location.level:
                # Add this one to the defaults too
                defaults[default_location.level] = Storage(name=default_location.name,
                                                           id=config.default_location_id)
            if "L0" in defaults:
                default_L0 = defaults["L0"]
                if default_L0:
                    id = default_L0.id
                    if id not in countries:
                        # Add the default country to the list of possibles
                        countries[id] = defaults["L0"].name
                country_snippet = '''S3.gis.country="%s"\n''' % \
                    gis.get_default_country(key_type="code")
        elif len(_countries) == 1:
            default_L0.id = countries.keys()[0]
            country_snippet = '''S3.gis.country="%s"\n''' % _countries[0]
        elif len(countries) == 1:
            default_L0.id = countries.keys()[0]

        # Should we use a Map-based selector?
        map_selector = settings.get_gis_map_selector()
        if map_selector:
            no_map = ""
        else:
            no_map = '''S3.gis.no_map = true;\n'''
        # Should we display LatLon boxes?
        latlon_selector = settings.get_gis_latlon_selector()
        # Show we display Polygons?
        polygon = self.polygon
        # Navigate Away Confirm?
        if settings.get_ui_navigate_away_confirm():
            navigate_away_confirm = '''
S3.navigate_away_confirm=true'''
        else:
            navigate_away_confirm = ""

        # Which tab should the widget open to by default?
        # @ToDo: Act on this server-side instead of client-side
        if s3.gis.tab:
            tab = '''
S3.gis.tab="%s"''' % s3.gis.tab
        else:
            # Default to Create
            tab = ""

        # Which Levels do we have in our hierarchy & what are their initial Labels?
        # If we have a default country or one from the value then we can lookup
        # the labels we should use for that location
        country = None
        if default_L0:
            country = default_L0.id
        location_hierarchy = gis.get_location_hierarchy(location=country)
        # This is all levels to start, but L0 will be dropped later.
        levels = gis.hierarchy_level_keys

        map_popup = ""
        if value:
            # Read current record
            if auth.s3_has_permission("update", locations, record_id=value):
                # Update mode
                # - we assume this location could be shared by other resources
                create = "hide"   # Hide sections which are meant for create forms
                update = ""
                query = (locations.id == value)
                this_location = db(query).select(locations.uuid,
                                                 locations.name,
                                                 locations.level,
                                                 locations.inherited,
                                                 locations.lat,
                                                 locations.lon,
                                                 locations.addr_street,
                                                 locations.addr_postcode,
                                                 locations.parent,
                                                 locations.path,
                                                 locations.wkt,
                                                 limitby=(0, 1)).first()
                if this_location:
                    uid = this_location.uuid
                    level = this_location.level
                    defaults[level] = Storage()
                    defaults[level].id = value
                    if this_location.inherited:
                        lat = None
                        lon = None
                        wkt = None
                    else:
                        lat = this_location.lat
                        lon = this_location.lon
                        wkt = this_location.wkt
                    addr_street = this_location.addr_street or ""
                    #addr_street_encoded = ""
                    #if addr_street:
                    #    addr_street_encoded = addr_street.replace("\r\n",
                    #                                              "%0d").replace("\r",
                    #                                                             "%0d").replace("\n",
                    #                                                                            "%0d")
                    postcode = this_location.addr_postcode
                    parent = this_location.parent
                    path = this_location.path

                    # Populate defaults with IDs & Names of ancestors at each level
                    defaults = gis.get_parent_per_level(defaults,
                                                        value,
                                                        feature=this_location,
                                                        ids=True,
                                                        names=True)
                    # If we have a non-specific location then not all keys will be populated.
                    # Populate these now:
                    for l in levels:
                        try:
                            defaults[l]
                        except:
                            defaults[l] = None

                    if level and not level == "XX":
                        # If within the locations hierarchy then don't populate the visible name box
                        represent = ""
                    else:
                        represent = this_location.name

                    if map_selector:
                        zoom = config.zoom
                        if zoom == None:
                            zoom = 1
                        if lat is None or lon is None:
                            map_lat = config.lat
                            map_lon = config.lon
                        else:
                            map_lat = lat
                            map_lon = lon

                        query = (locations.id == value)
                        row = db(query).select(locations.wkt,
                                               limitby=(0, 1)).first()
                        if row:
                            features = [row.wkt]
                        else:
                            features = []
                        map_popup = gis.show_map(lat = map_lat,
                                                 lon = map_lon,
                                                 # Same as a single zoom on a cluster
                                                 zoom = zoom + 2,
                                                 features = features,
                                                 catalogue_layers = self.catalog_layers,
                                                 add_feature = True,
                                                 add_feature_active = not polygon,
                                                 add_polygon = polygon,
                                                 add_polygon_active = polygon,
                                                 toolbar = True,
                                                 nav = False,
                                                 area = False,
                                                 save = False,
                                                 collapsed = True,
                                                 search = True,
                                                 window = True,
                                                 window_hide = True,
                                                 )
                else:
                    # Bad location_id
                    response.error = T("Invalid Location!")
                    value = None

            elif auth.s3_has_permission("read", locations, record_id=value):
                # Read mode
                # @ToDo
                return ""
            else:
                # No Permission to read location, so don't render a row
                return ""

        if not value:
            # No default value
            # Check that we're allowed to create records
            if auth.s3_has_permission("update", locations):
                # Create mode
                create = ""
                update = "hide"   # Hide sections which are meant for update forms
                uuid = ""
                represent = ""
                level = None
                lat = None
                lon = None
                wkt = None
                addr_street = ""
                #addr_street_encoded = ""
                postcode = ""
                if map_selector:
                    map_popup = gis.show_map(add_feature = True,
                                             add_feature_active = not polygon,
                                             add_polygon = polygon,
                                             add_polygon_active = polygon,
                                             catalogue_layers = self.catalog_layers,
                                             toolbar = True,
                                             nav = False,
                                             area = False,
                                             save = False,
                                             collapsed = True,
                                             search = True,
                                             window = True,
                                             window_hide = True,
                                             )
            else:
                # No Permission to create a location, so don't render a row
                return ""

        # JS snippets of config
        # (we only include items with data)
        s3_gis_lat_lon = ""

        # Components to inject into Form
        divider = TR(TD(_class="subheading"),
                     _class="box_bottom locselect")
        expand_button = DIV(_id="gis_location_expand", _class="expand")
        label_row = TR(TD(expand_button, B("%s:" % field.label)),
                       _id="gis_location_label_row",
                       _class="box_top")

        # Tabs to select between the modes
        # @ToDo: Move Location tab
        view_button = A(T("View Location Details"),
                        _style="cursor:pointer; cursor:hand",
                        _id="gis_location_view-btn")

        edit_button = A(T("Edit Location Details"),
                        _style="cursor:pointer; cursor:hand",
                        _id="gis_location_edit-btn")

        add_button = A(T("Create New Location"),
                       _style="cursor:pointer; cursor:hand",
                       _id="gis_location_add-btn")

        search_button = A(T("Select Existing Location"),
                          _style="cursor:pointer; cursor:hand",
                          _id="gis_location_search-btn")

        tabs = DIV(SPAN(add_button, _id="gis_loc_add_tab",
                        _class="tab_here %s" % create),
                   SPAN(search_button, _id="gis_loc_search_tab",
                        _class="tab_last %s" % create),
                   SPAN(view_button, _id="gis_loc_view_tab",
                        _class="tab_here %s" % update),
                   SPAN(edit_button, _id="gis_loc_edit_tab",
                        _class="tab_last %s" % update),
                   _class="tabs")

        tab_rows = TR(TD(tabs), TD(),
                      _id="gis_location_tabs_row",
                      _class="locselect box_middle")

        # L0 selector
        SELECT_COUNTRY = T("Choose country")
        level = "L0"
        L0_rows = ""
        if len(countries) == 1:
            # Hard-coded country
            id = countries.items()[0][0]
            L0_rows = INPUT(value = id,
                            _id="gis_location_%s" % level,
                            _name="gis_location_%s" % level,
                            _class="hide box_middle")
        else:
            if default_L0:
                attr_dropdown = OptionsWidget._attributes(field,
                                                          dict(_type = "int",
                                                               value = default_L0.id),
                                                          **attributes)
            else:
                attr_dropdown = OptionsWidget._attributes(field,
                                                          dict(_type = "int",
                                                               value = ""),
                                                          **attributes)
            attr_dropdown["requires"] = \
                IS_NULL_OR(IS_IN_SET(countries,
                                     zero = SELECT_COUNTRY))
            attr_dropdown["represent"] = \
                lambda id: gis.get_country(id) or UNKNOWN_OPT
            opts = [OPTION(SELECT_COUNTRY, _value="")]
            if countries:
                for (id, name) in countries.iteritems():
                    opts.append(OPTION(name, _value=id))
            attr_dropdown["_id"] = "gis_location_%s" % level
            ## Old: Need to blank the name to prevent it from appearing in form.vars & requiring validation
            #attr_dropdown["_name"] = ""
            attr_dropdown["_name"] = "gis_location_%s" % level
            if value:
                # Update form => read-only
                attr_dropdown["_disabled"] = "disabled"
                try:
                    attr_dropdown["value"] = defaults[level].id
                except:
                    pass
            widget = SELECT(*opts, **attr_dropdown)
            label = LABEL("%s:" % location_hierarchy[level])
            L0_rows = DIV(TR(TD(label), TD(),
                             _class="locselect box_middle",
                             _id="gis_location_%s_label__row" % level),
                          TR(TD(widget), TD(),
                             _class="locselect box_middle",
                             _id="gis_location_%s__row" % level))
        row = TR(INPUT(_id="gis_location_%s_search" % level,
                       _disabled="disabled"), TD(),
                 _class="hide locselect box_middle",
                 _id="gis_location_%s_search__row" % level)
        L0_rows.append(row)

        if self.site_type:
            NAME_LABEL = T("Site Name")
        else:
            NAME_LABEL = T("Building Name")
        STREET_LABEL = T("Street Address")
        POSTCODE_LABEL = settings.get_ui_label_postcode()
        LAT_LABEL = T("Latitude")
        LON_LABEL = T("Longitude")
        AUTOCOMPLETE_HELP = T("Enter some characters to bring up a list of possible matches")
        NEW_HELP = T("If not found, you can have a new location created.")
        def ac_help_widget(level):
            try:
                label = location_hierarchy[level]
            except:
                label = level
            return DIV(_class="tooltip",
                       _title="%s|%s|%s" % (label, AUTOCOMPLETE_HELP, NEW_HELP))

        hidden = ""
        Lx_rows = DIV()
        if value:
            # Display Read-only Fields
            name_widget = INPUT(value=represent,
                                _id="gis_location_name",
                                _name="gis_location_name",
                                _disabled="disabled")
            street_widget = TEXTAREA(value=addr_street,
                                     _id="gis_location_street",
                                     _class="text",
                                     _name="gis_location_street",
                                     _disabled="disabled")
            postcode_widget = INPUT(value=postcode,
                                    _id="gis_location_postcode",
                                    _name="gis_location_postcode",
                                    _disabled="disabled")

            lat_widget = S3LatLonWidget("lat",
                                        disabled=True).widget(value=lat)
            lon_widget = S3LatLonWidget("lon",
                                        switch_button=True,
                                        disabled=True).widget(value=lon)

            for level in levels:
                if level == "L0":
                    # L0 has been handled as special case earlier
                    continue
                elif level not in location_hierarchy:
                    # Skip levels not in hierarchy
                    continue
                if defaults[level]:
                    id = defaults[level].id
                    name = defaults[level].name
                else:
                    # Hide empty levels
                    hidden = "hide"
                    id = ""
                    name = ""
                try:
                    label = LABEL("%s:" % location_hierarchy[level])
                except:
                    label = LABEL("%s:" % level)
                row = TR(TD(label), TD(),
                         _id="gis_location_%s_label__row" % level,
                         _class="%s locselect box_middle" % hidden)
                Lx_rows.append(row)
                widget = DIV(INPUT(value=id,
                                   _id="gis_location_%s" % level,
                                   _name="gis_location_%s" % level,
                                   _class="hide"),
                             INPUT(value=name,
                                   _id="gis_location_%s_ac" % level,
                                   _disabled="disabled"),
                             DIV(_id="gis_location_%s_throbber" % level,
                                 _class="throbber hide"))
                row = TR(TD(widget), TD(),
                         _id="gis_location_%s__row" % level,
                         _class="%s locselect box_middle" % hidden)
                Lx_rows.append(row)

        else:
            name_widget = INPUT(_id="gis_location_name",
                                _name="gis_location_name")
            street_widget = TEXTAREA(_id="gis_location_street",
                                     _class="text",
                                     _name="gis_location_street")
            postcode_widget = INPUT(_id="gis_location_postcode",
                                    _name="gis_location_postcode")
            lat_widget = S3LatLonWidget("lat").widget()
            lon_widget = S3LatLonWidget("lon", switch_button=True).widget()

            for level in levels:
                hidden = ""
                if level == "L0":
                    # L0 has been handled as special case earlier
                    continue
                elif level not in location_hierarchy:
                    # Hide unused levels
                    # (these can then be enabled for other regions)
                    hidden = "hide"
                try:
                    label = LABEL("%s:" % location_hierarchy[level])
                except:
                    label = LABEL("%s:" % level)
                row = TR(TD(label), TD(),
                         _class="%s locselect box_middle" % hidden,
                         _id="gis_location_%s_label__row" % level)
                Lx_rows.append(row)
                if level in defaults and defaults[level]:
                    default = defaults[level]
                    default_id = default.id
                    default_name = default.name
                else:
                    default_id = ""
                    default_name = ""
                widget = DIV(INPUT(value=default_id,
                                   _id="gis_location_%s" % level,
                                   _name="gis_location_%s" % level,
                                   _class="hide"),
                                INPUT(value=default_name,
                                      _id="gis_location_%s_ac" % level,
                                      _class="%s" % hidden),
                                DIV(_id="gis_location_%s_throbber" % level,
                                    _class="throbber hide"))
                row = TR(TD(widget),
                         TD(ac_help_widget(level)),
                         _class="%s locselect box_middle" % hidden,
                         _id="gis_location_%s__row" % level)
                Lx_rows.append(row)
                row = TR(INPUT(_id="gis_location_%s_search" % level,
                               _disabled="disabled"), TD(),
                         _class="hide locselect box_middle",
                         _id="gis_location_%s_search__row" % level)
                Lx_rows.append(row)

        hide_address = self.hide_address
        if settings.get_gis_building_name():
            hidden = ""
            if hide_address:
                hidden = "hide"
            elif value and not represent:
                hidden = "hide"
            name_rows = DIV(TR(LABEL("%s:" % NAME_LABEL), TD(),
                               _id="gis_location_name_label__row",
                               _class="%s locselect box_middle" % hidden),
                            TR(name_widget, TD(),
                               _id="gis_location_name__row",
                               _class="%s locselect box_middle" % hidden),
                            TR(INPUT(_id="gis_location_name_search",
                                     _disabled="disabled"), TD(),
                               _id="gis_location_name_search__row",
                               _class="hide locselect box_middle"))
        else:
            name_rows = ""

        hidden = ""
        if hide_address:
            hidden = "hide"
        elif value and not addr_street:
            hidden = "hide"
        street_rows = DIV(TR(LABEL("%s:" % STREET_LABEL), TD(),
                             _id="gis_location_street_label__row",
                             _class="%s locselect box_middle" % hidden),
                          TR(street_widget, TD(),
                             _id="gis_location_street__row",
                             _class="%s locselect box_middle" % hidden),
                          TR(INPUT(_id="gis_location_street_search",
                                   _disabled="disabled"), TD(),
                             _id="gis_location_street_search__row",
                             _class="hide locselect box_middle"))
        if config.geocoder:
            geocoder = '''
S3.gis.geocoder=true'''
        else:
            geocoder = ""

        hidden = ""
        if hide_address:
            hidden = "hide"
        elif value and not postcode:
            hidden = "hide"
        postcode_rows = DIV(TR(LABEL("%s:" % POSTCODE_LABEL), TD(),
                               _id="gis_location_postcode_label__row",
                               _class="%s locselect box_middle" % hidden),
                            TR(postcode_widget, TD(),
                               _id="gis_location_postcode__row",
                               _class="%s locselect box_middle" % hidden),
                            TR(INPUT(_id="gis_location_postcode_search",
                                     _disabled="disabled"), TD(),
                               _id="gis_location_postcode_search__row",
                               _class="hide locselect box_middle"))

        hidden = ""
        no_latlon = ""
        if not latlon_selector:
            hidden = "hide"
            no_latlon = '''S3.gis.no_latlon=true\n'''
        elif value and lat is None:
            hidden = "hide"
        latlon_help = locations.lat.comment
        converter_button = locations.lon.comment
        converter_button = ""
        latlon_rows = DIV(TR(LABEL("%s:" % LAT_LABEL), TD(),
                             _id="gis_location_lat_label__row",
                             _class="%s locselect box_middle" % hidden),
                          TR(TD(lat_widget), TD(latlon_help),
                             _id="gis_location_lat__row",
                             _class="%s locselect box_middle" % hidden),
                          TR(INPUT(_id="gis_location_lat_search",
                                   _disabled="disabled"), TD(),
                             _id="gis_location_lat_search__row",
                             _class="hide locselect box_middle"),
                          TR(LABEL("%s:" % LON_LABEL), TD(),
                             _id="gis_location_lon_label__row",
                             _class="%s locselect box_middle" % hidden),
                          TR(TD(lon_widget), TD(converter_button),
                             _id="gis_location_lon__row",
                             _class="%s locselect box_middle" % hidden),
                          TR(INPUT(_id="gis_location_lon_search",
                                   _disabled="disabled"), TD(),
                             _id="gis_location_lon_search__row",
                             _class="hide locselect box_middle"))

        # Map Selector
        PLACE_ON_MAP = T("Place on Map")
        VIEW_ON_MAP = T("View on Map")
        if map_selector:
            if value:
                map_button = A(VIEW_ON_MAP,
                               _style="cursor:pointer; cursor:hand",
                               _id="gis_location_map-btn",
                               _class="action-btn")
            else:
                map_button = A(PLACE_ON_MAP,
                               _style="cursor:pointer; cursor:hand",
                               _id="gis_location_map-btn",
                               _class="action-btn")
            if geocoder:
                if value:
                    _class = "action-btn hide"
                else:
                    _class = "action-btn"
                geocoder_button = A(T("Geocode"),
                                    _style="cursor:pointer; cursor:hand",
                                    _id="gis_location_geocoder-btn",
                                    _class=_class)
            else:
                geocoder_button = ""
            map_button_row = TR(TD(geocoder_button, map_button),
                                _id="gis_location_map_button_row",
                                _class="locselect box_middle")
        else:
            map_button_row = ""

        # Search
        widget = DIV(INPUT(_id="gis_location_search_ac"),
                           DIV(_id="gis_location_search_throbber",
                               _class="throbber hide"),
                           _id="gis_location_search_div")

        label = LABEL("%s:" % AUTOCOMPLETE_HELP)

        select_button = A(T("Select This Location"),
                          _style="cursor:pointer; cursor:hand",
                          _id="gis_location_search_select-btn",
                          _class="hide action-btn")

        search_rows = DIV(TR(label, TD(),
                             _id="gis_location_search_label__row",
                             _class="hide locselect box_middle"),
                          TR(TD(widget),
                             TD(select_button),
                             _id="gis_location_search__row",
                             _class="hide locselect box_middle"))
        # @ToDo: Hierarchical Filter
        Lx_search_rows = ""

        # Error Messages
        NAME_REQUIRED = T("Name field is required!")
        COUNTRY_REQUIRED = T("Country is required!")

        # Settings to be read by static/scripts/S3/s3.locationselector.widget.js
        # Note: Currently we're limited to a single location selector per page
        js_location_selector = '''
%s%s%s%s%s%s
S3.gis.location_id='%s'
S3.gis.site='%s'
i18n.gis_place_on_map='%s'
i18n.gis_view_on_map='%s'
i18n.gis_name_required='%s'
i18n.gis_country_required="%s"''' % (country_snippet,
                                     geocoder,
                                     navigate_away_confirm,
                                     no_latlon,
                                     no_map,
                                     tab,
                                     attr["_id"],    # Name of the real location or site field
                                     site,
                                     PLACE_ON_MAP,
                                     VIEW_ON_MAP,
                                     NAME_REQUIRED,
                                     COUNTRY_REQUIRED
                                     )

        s3.js_global.append(js_location_selector)
        if s3.debug:
            script = "s3.locationselector.widget.js"
        else:
            script = "s3.locationselector.widget.min.js"

        s3.scripts.append("/%s/static/scripts/S3/%s" % (appname, script))

        if self.polygon:
            hidden = ""
            if value:
                # Display read-only view
                wkt_widget = TEXTAREA(value = wkt,
                                      _class="wkt-input",
                                      _id="gis_location_wkt",
                                      _name="gis_location_wkt",
                                      _disabled="disabled")
                if not wkt:
                    hidden = "hide"
            else:
                wkt_widget = TEXTAREA(_class="wkt-input",
                                      _id="gis_location_wkt",
                                      _name="gis_location_wkt")
            wkt_input_row = TAG[""](
                                TR(TD(LABEL(T("Polygon"))),
                                   TD(),
                                   _id="gis_location_wkt_label__row",
                                   _class="box_middle %s" % hidden),
                                TR(
                                   TD(wkt_widget),
                                   TD(),
                                   _id="gis_location_wkt__row",
                                   _class="box_middle %s" % hidden)
                                )
        else:
            wkt_input_row = ""

         # Ensure that we don't insert duplicate scripts on validation errors
        s3.gis.location_selector_loaded = True

        # The overall layout of the components
        return TAG[""](TR(INPUT(**attr)),  # Real input, which is hidden
                       label_row,
                       tab_rows,
                       Lx_search_rows,
                       search_rows,
                       L0_rows,
                       name_rows,
                       street_rows,
                       postcode_rows,
                       Lx_rows,
                       wkt_input_row,
                       map_button_row,
                       latlon_rows,
                       divider,
                       TR(map_popup, TD(), _class="box_middle"),
                       requires=requires
                       )

# =============================================================================
class S3LocationSelectorWidget2(FormWidget):
    """
        Renders a gis_location Foreign Key to allow inline display/editing of linked fields

        Differences to the original LocationSelectorWidget:
        * Allows selection of either an Lx or creation of a new Point within the lowest Lx level
        * Uses dropdowns not autocompletes
        * Selection of lower Lx levels only happens when higher-level have been done

        Limitations:
        * Currently assumes use within just 1 country
        * Doesn't allow creation of new Lx Locations
        * Doesn't allow selection of existing Locations
        * Doesn't support manual entry of LatLons
        * Doesn't support Geocoding

        May evolve into a replacement in-time if missing features get migrated here.

        Implementation Notes:
        * Should support formstyles (Bootstrap currenty supported)
        * Should support use in an InlineComponent (not urgent)
        * Should support multiple on a page (not urgent)
        * Performance: Create JSON for the hierarchy, along with bboxes for the map zoom
                       - load progressively rather than all as 1 big download
        h = {id : {'n' : name,
                   'l' : level,
                   'f' : parent
                   }}
    """

    def __init__(self,
                 levels = ["L1", "L2", "L3"],   # Which levels of the hierarchy to expose?
                 hide_lx = True,                # Whether to hide lower Lx fields until higher level selected
                 reverse_lx = False,            # Whether to show Lx fields in the order usually used by Street Addresses
                 show_address = False,          # Whether to show a field for Street Address
                 show_postcode = False,         # Whether to show a field for Postcode
                 show_map = True,               # Whether to show a Map to select specific points
                 polygons = False,              # Whether the Map uses a Polygon draw tool instead of Point
                 ):

        self.levels = levels
        self.hide_lx = hide_lx
        self.reverse_lx = reverse_lx
        self.show_address = show_address
        self.show_postcode = show_postcode
        self.show_map = show_map
        self.polygons = polygons

    def __call__(self, field, value, **attributes):

        levels = self.levels
        show_address = self.show_address
        show_postcode = self.show_postcode
        show_map = self.show_map
        polygons = self.polygons

        T = current.T
        db = current.db
        s3db = current.s3db
        gis = current.gis
        settings = current.deployment_settings
        s3 = current.response.s3
        location_selector_loaded = s3.gis.location_selector_loaded
        formstyle = s3.crud.formstyle # Currently only Bootstrap has been tested
        request = current.request

        default = field.default
        if not default:
            # Check for a default location in the active gis_config
            config = gis.get_config()
            default = config.default_location_id

        gtable = s3db.gis_location

        countries = settings.get_gis_countries()
        if len(countries) == 1:
            ttable = s3db.gis_location_tag
            query = (ttable.tag == "ISO2") & \
                    (ttable.value == countries[0]) & \
                    (ttable.location_id == gtable.id)
            country = db(query).select(gtable.id,
                                       gtable.lat_min,
                                       gtable.lon_min,
                                       gtable.lat_max,
                                       gtable.lon_max,
                                       limitby=(0, 1)).first()
            default_L0 = country.id
            default_bounds = [country.lon_min,
                              country.lat_min,
                              country.lon_max,
                              country.lat_max
                              ]
        else:
            default_L0 = 0
            config = gis.get_config()
            default_bounds = [config.lon_min,
                              config.lat_min,
                              config.lon_max,
                              config.lat_max
                              ]
            # @ToDo: Lookup Labels dynamically when L0 changes
            raise NotImplementedError

        # @ToDo: Which geocoder(s) should we use?
        # Lookup country in gis_config
        geocoder = False

        values = dict(L0 = default_L0,
                      L1 = 0,
                      L2 = 0,
                      L3 = 0,
                      L4 = 0,
                      L5 = 0,
                      specific = 0,
                      )
        parent = ""
        # Keep the selected Lat/Lon/Address/Postcode during validation errors
        post_vars = request.post_vars
        lat = post_vars.lat
        lon = post_vars.lon
        wkt = post_vars.wkt
        address = post_vars.address
        postcode = post_vars.postcode
        if value == "dummy":
            # Validation Error when Creating a specific point
            # Revert to Parent
            value = post_vars.parent
        if not value:
            value = default
        if value:
            record = db(gtable.id == value).select(gtable.path,
                                                   gtable.parent,
                                                   gtable.level,
                                                   gtable.inherited,
                                                   gtable.lat,
                                                   gtable.lon,
                                                   gtable.wkt,
                                                   gtable.addr_street,
                                                   gtable.addr_postcode,
                                                   limitby=(0, 1)).first()
            if not record:
                raise ValueError
            parent = record.parent
            level = record.level
            path = record.path.split("/")
            path_ok = True
            if level:
                if len(path) != (int(level[1:]) + 1):
                    # We don't have a full path
                    path_ok = False
            else:
                # Specific location
                # Only use a specific Lat/Lon when they are not inherited
                if not record.inherited:
                    lat = record.lat
                    lon = record.lon
                    wkt = record.wkt if polygons else ""
                address = record.addr_street
                postcode = record.addr_postcode
                values["specific"] = value
                if len(path) < (len(levels) + 1):
                    # We don't have a full path
                    path_ok = False

            if path_ok:
                for l in levels:
                    try:
                        values[l] = path[int(l[1:])]
                    except:
                        pass
            else:
                # Retrieve all records in the path to match them up to their Lx
                rows = db(gtable.id.belongs(path)).select(gtable.id,
                                                          gtable.level)
                for row in rows:
                    values[row.level] = row.id

        fieldname = str(field).replace(".", "_")

        # Main INPUT, will be hidden
        defaults = dict(_type = "text",
                        value = (value != None and str(value)) or "")
        attr = StringWidget._attributes(field, defaults, **attributes)

        # Parent INPUT field, will be hidden
        parent_input = INPUT(_name="parent",
                             _id="%s_parent" % fieldname,
                             value=parent,
                             )
        if show_map:
            if polygons:
                # WKT INPUT field, will be hidden
                wkt_input = INPUT(_name="wkt",
                                  _id="%s_wkt" % fieldname,
                                  value=wkt,
                                  )
                lat_input = ""
                lon_input = ""
            else:
                # Lat/Lon INPUT fields, will be hidden
                lat_input = INPUT(_name="lat",
                                  _id="%s_lat" % fieldname,
                                  value=lat,
                                  )
                lon_input = INPUT(_name="lon",
                                  _id="%s_lon" % fieldname,
                                  value=lon,
                                  )
                wkt_input = ""
        else:
            lat_input = ""
            lon_input = ""
            wkt_input = ""

        if "L0" in levels:
            L0_input = ""
        else:
            # Have a hidden L0 input
            # - used for Geocoder
            L0_input = INPUT(_name="L0",
                             _id="%s_L0" % fieldname,
                             value=default_L0,
                             )
        Lx_inputs = TAG[""](L0_input)

        if show_address:
            # Street Address
            id = "%s_address" % fieldname
            label = T("Street Address")
            widget = INPUT(_name="address",
                           _id=id,
                           value=address,
                           )
            hidden = not address
            if formstyle == "bootstrap":
                # We would like to hide the whole original control-group & append rows, but that can't be done directly within a Widget
                # -> Elements moved via JS after page load
                label = LABEL("%s:" % label, _class="control-label",
                                             _for=id)
                widget.add_class("input-xlarge")
                _controls = DIV(widget, _class="controls")
                # Will unhide if dropdowns open accordingly
                _class = "control-group hide"
                address_row = DIV(label, _controls, _class=_class, _id="%s__row" % id)
            elif callable(formstyle):
                # @ToDo: Test
                comment = ""
                address_row = formstyle(id, label, widget, comment, hidden=True)
            else:
                # Unsupported
                raise
        else:
            address_row = ""

        if show_postcode:
            # Postcode
            id = "%s_postcode" % fieldname
            label = settings.get_ui_label_postcode()
            widget = INPUT(_name="postcode",
                           _id=id,
                           value=postcode,
                           )
            hidden = not postcode
            if formstyle == "bootstrap":
                # We would like to hide the whole original control-group & append rows, but that can't be done directly within a Widget
                # -> Elements moved via JS after page load
                label = LABEL("%s:" % label, _class="control-label",
                                             _for=id)
                widget.add_class("input-xlarge")
                _controls = DIV(widget, _class="controls")
                # Will unhide if dropdowns open accordingly
                _class = "control-group hide"
                postcode_row = DIV(label, _controls, _class=_class, _id="%s__row" % id)
            elif callable(formstyle):
                # @ToDo: Test
                comment = ""
                postcode_row = formstyle(id, label, widget, comment, hidden=True)
            else:
                # Unsupported
                raise
        else:
            postcode_row = ""

        # Hierarchy Labels
        htable = s3db.gis_hierarchy
        fields = [htable[level] for level in levels]
        labels = db(htable.location_id == default_L0).select(*fields,
                                                             limitby=(0, 1)).first()

        # Lx Dropdowns
        Lx_rows = DIV()
        # 1st level is always visible (except in Bootstrap)
        hidden = False
        for level in levels:
            id = "%s_%s" % (fieldname, level)
            label = labels[level]
            widget = SELECT(OPTION(T("Select %(location)s") % dict(location = label),
                                   _value=""),
                            _id=id)
            #comment = T("Select this %(location)s") % dict(location = label)
            throbber = DIV(_id="%s__throbber" % id,
                           _class="throbber hide"
                           )
            if formstyle == "bootstrap":
                # We would like to hide the whole original control-group & append rows, but that can't be done directly within a Widget
                # -> Elements moved via JS after page load
                label = LABEL("%s:" % label, _class="control-label",
                                             _for=id)
                widget.add_class("input-xlarge")
                # Currently unused, so remove if this remains so
                #from gluon.html import BUTTON
                #comment = BUTTON(comment,
                #                 _class="btn btn-primary hide",
                #                 _id="%s__button" % id
                #                 )
                #_controls = DIV(widget, throbber, comment, _class="controls")
                _controls = DIV(widget, throbber, _class="controls")
                row = DIV(label, _controls, _class="control-group hide", _id="%s__row" % id)
            elif callable(formstyle):
                # @ToDo
                row = formstyle(id, label, widget, comment, hidden=hidden)
            else:
                # Unsupported
                raise
            Lx_rows.append(row)
            # Subsequent levels are hidden by default
            # (client-side JS will open when-needed)
            hidden = True

        # @ToDo: Don't assume we start at L1
        query = (gtable.deleted == False) & \
                (gtable.level == "L1") & \
                (gtable.parent == default_L0)
        locations = db(query).select(gtable.id,
                                     gtable.name,
                                     gtable.level,
                                     gtable.parent,
                                     gtable.inherited,
                                     gtable.lat_min,
                                     gtable.lon_min,
                                     gtable.lat_max,
                                     gtable.lon_max,
                                     )
        top = dict(id = default_L0,
                   b = default_bounds)
        location_dict = dict(d=top)
        for location in locations:
            if location.inherited:
                location_dict[int(location.id)] = dict(n=location.name,
                                                       l=int(location.level[1]),
                                                       f=int(location.parent),
                                                       )
            else:
                location_dict[int(location.id)] = dict(n=location.name,
                                                       l=int(location.level[1]),
                                                       f=int(location.parent),
                                                       b=[location.lon_min,
                                                          location.lat_min,
                                                          location.lon_max,
                                                          location.lat_max,
                                                          ],
                                                       )
        if default_L0 and default_L0 not in location_dict:
            location_dict[default_L0] = dict(l=0,
                                             b=default_bounds)

        if not location_selector_loaded:
            script = '''l=%s''' % json.dumps(location_dict)
            s3.js_global.append(script)

        # If we need to show the map since we have an existing lat/lon
        # then we need to launch the client-side JS as a callback to the MapJS loader
        if lat is not None or lon is not None:
            use_callback = True
        else:
            use_callback = False

        max_level = levels[len(levels) - 1]
        L1 = values["L1"]
        specific = values["specific"]
        args = [default_L0]
        if specific:
            # We need to proivde all args
            args += [L1, values["L2"], values["L3"], values["L4"], values["L5"], specific]
        elif L1:
            # Add only required args
            args.append(L1)
            L2 = values["L2"]
            if L2:
                args.append(L2)
                L3 = values["L3"]
                if L3:
                    args.append(L3)
                    L4 = values["L4"]
                    if L4:
                        args.append(L4)
                        L5 = values["L5"]
                        if L5:
                            args.append(L5)

        args = [str(arg) for arg in args]
        args = ''','''.join(args)
        script = '''S3.gis.locationselector('%s',%s,%s,%s)''' % \
                    (fieldname,
                     "true" if self.hide_lx else "false",
                     "true" if self.reverse_lx else "false",
                     args)
        if show_map and use_callback:
            callback = script
        elif not location_selector_loaded:
            s3.jquery_ready.append(script)

        if s3.debug:
            script = "s3.locationselector.widget2.js"
        else:
            script = "s3.locationselector.widget2.min.js"

        script = "/%s/static/scripts/S3/%s" % (request.application, script)
        scripts = s3.scripts
        if script not in scripts:
            scripts.append(script)

        if show_map:
            # @ToDo: handle multiple LocationSelectors in 1 page
            # (=> multiple callbacks, as well as the need to migrate options from globals to a parameter)
            map = gis.show_map(id = "location_selector_%s" % fieldname,
                               collapsed = True,
                               height = 320,
                               width = 480,
                               add_feature = not polygons,
                               add_feature_active = not polygons,
                               add_polygon = polygons,
                               add_polygon_active = polygons,
                               # Hide controls from toolbar
                               nav = False,
                               area = False,
                               save = False,
                               # Don't use normal callback (since we postpone rendering Map until DIV unhidden)
                               # but use our one if we need to display a map by default
                               callback = callback if use_callback else None,
                               )
            icon_id = "%s_map_icon" % fieldname
            row_id = "%s_map_icon__row" % fieldname
            if formstyle == "bootstrap":
                map_icon = DIV(LABEL(I(_class="icon-map",
                                       _id=icon_id,
                                       ),
                                     _class="control-label",
                                     ),
                               _id = row_id,
                               _class = "control-group hide",
                               )
                if geocoder:
                    geocode_button = BUTTON(T("Geocode"),
                                            _id="%s_geocode" % fieldname,
                                            _class="hide",
                                            )
                else:
                    geocode_button = None
            else:
                # @ToDo: Icon in default CSS
                # @ToDo: Test
                label = LABEL(I(_class="icon-map",
                                _id=icon_id,
                                ))
                widget = ""
                comment = ""
                map_icon = formstyle(row_id, label, widget, comment)
                if geocoder:
                    geocode_button = BUTTON(T("Geocode"),
                                            _id="%s_geocode" % fieldname,
                                            _class="hide",
                                            )
                else:
                    geocode_button = None
            map = TAG[""](map, map_icon, geocode_button)
        else:
            map = ""

        # Ensure that we don't insert duplicate scripts on validation errors
        s3.gis.location_selector_loaded = True

        # The overall layout of the components
        return TAG[""](DIV(INPUT(**attr), # Real input, hidden
                           Lx_inputs,
                           lat_input,
                           lon_input,
                           wkt_input,
                           parent_input,
                           _class="hide"),
                       Lx_rows,
                       address_row,
                       postcode_row,
                       map,
                       requires=field.requires
                       )

# =============================================================================
class S3MultiSelectWidget(MultipleOptionsWidget):
    """
        Standard MultipleOptionsWidget, but using the jQuery UI:
        http://www.erichynds.com/jquery/jquery-ui-multiselect-widget/
        static/scripts/jquery.ui.multiselect.js
    """

    def __init__(self,
                 filter = True,
                 header = True,
                 selectedList = 4,
                 noneSelectedText = "Select"
                 ):
        self.filter = filter
        self.header = header
        self.selectedList = selectedList
        self.noneSelectedText = noneSelectedText

    def __call__(self, field, value, **attr):

        T = current.T

        if isinstance(field, Field):
            selector = str(field).replace(".", "_")
        else:
            selector = field.name.replace(".", "_")

        # Options:
        # * Show Selected List
        if self.header is True:
            header = '''checkAllText:'%s',uncheckAllText:"%s"''' % \
                (T("Check all"),
                 T("Uncheck all"))
        elif self.header is False:
            header = '''header:false'''
        else:
            header = '''header:"%s"''' % self.header
        script = '''$('#%s').multiselect({selectedText:'%s',%s,height:300,minWidth:0,selectedList:%s,noneSelectedText:'%s'})''' % \
            (selector,
             T("# selected"),
             header,
             self.selectedList,
             T(self.noneSelectedText))
        if self.filter:
            script = '''%s.multiselectfilter()''' % script
        current.response.s3.jquery_ready.append(script)

        _class = attr.get("_class", None)
        if _class:
            if "multiselect-widget" not in _class:
                attr["_class"] = "%s multiselect-widget" % _class
        else:
            attr["_class"] = "multiselect-widget"

        return TAG[""](MultipleOptionsWidget.widget(field, value, **attr),
                       requires = field.requires
                       )

# =============================================================================
class S3OptionsMatrixWidget(FormWidget):
    """
        Constructs a two dimensional array/grid of checkboxes
        with row and column headers.
    """

    def __init__(self, rows, cols):
        """
            @type rows: tuple
            @param rows:
                A tuple of tuples.
                The nested tuples will have the row label followed by a value
                for each checkbox in that row.

            @type cols: tuple
            @param cols:
                A tuple containing the labels to use in the column headers
        """
        self.rows = rows
        self.cols = cols

    def __call__(self, field, value, **attributes):
        """
            Returns the grid/matrix of checkboxes as a web2py TABLE object and
            adds references to required Javascript files.

            @type field: Field
            @param field:
                This gets passed in when the widget is rendered or used.

            @type value: list
            @param value:
                A list of the values matching those of the checkboxes.

            @param attributes:
                HTML attributes to assign to the table.
        """

        if isinstance(value, (list, tuple)):
            values = [str(v) for v in value]
        else:
            values = [str(value)]

        # Create the table header
        header_cells = []
        for col in self.cols:
            header_cells.append(TH(col, _scope="col"))
        header = THEAD(TR(header_cells))

        # Create the table body cells
        grid_rows = []
        for row in self.rows:
            # Create a list to hold our table cells
            # the first cell will hold the row label
            row_cells = [TH(row[0], _scope="row")]
            for option in row[1:]:
                # This determines if the checkbox should be checked
                if option in values:
                    checked = True
                else:
                    checked = False

                row_cells.append(TD(
                                    INPUT(_type="checkbox",
                                          _name=field.name,
                                          _value=option,
                                          value=checked
                                          )
                                    ))
            grid_rows.append(TR(row_cells))

        s3 = current.response.s3
        s3.scripts.append("/%s/static/scripts/S3/s3.optionsmatrix.js" % current.request.application)

        # If the table has an id attribute, activate the jQuery plugin for it.
        if "_id" in attributes:
            s3.jquery_ready.append('''$('#{0}').s3optionsmatrix()'''.format(attributes.get("_id")))

        return TABLE(header, TBODY(grid_rows), **attributes)

# =============================================================================
class S3OrganisationAutocompleteWidget(FormWidget):
    """
        Renders an org_organisation SELECT as an INPUT field with AJAX Autocomplete.
        Differs from the S3AutocompleteWidget in that it can default to the setting in the profile.

        @ToDo: Add an option to hide the widget completely when using the Org from the Profile
               - i.e. prevent user overrides
    """

    def __init__(self,
                 post_process = "",
                 default_from_profile = False,
                 new_items = False, # Whether to make this a combo box
                 delay = 450,       # milliseconds
                 min_length = 2):   # Increase this for large deployments

        self.post_process = post_process
        self.delay = delay
        self.min_length = min_length
        self.new_items = new_items
        self.default_from_profile = default_from_profile

    def __call__(self, field, value, **attributes):

        def transform_value(value):
            if not value and self.default_from_profile:
                auth = current.session.auth
                if auth and auth.user:
                    value = auth.user.organisation_id
            return value

        return S3GenericAutocompleteTemplate(
            self.post_process,
            self.delay,
            self.min_length,
            field,
            value,
            attributes,
            transform_value = transform_value,
            new_items = self.new_items,
            tablename = "org_organisation",
            source = URL(c="org", f="org_search",
                         args="search_ac",
                         vars={"filter":"~"})
        )

# =============================================================================
class S3OrganisationHierarchyWidget(OptionsWidget):
    """ Renders an organisation_id SELECT as a menu """

    _class = "widget-org-hierarchy"

    def __init__(self, primary_options=None):
        """
            [{"id":12, "pe_id":4, "name":"Organisation Name"}]
        """
        self.primary_options = primary_options

    def __call__(self, field, value, **attributes):

        options = self.primary_options
        name = attributes.get("_name", field.name)

        if options is None:
            requires = field.requires
            if isinstance(requires, (list, tuple)) and \
               len(requires):
                requires = requires[0]
            if requires is not None:
                if isinstance(requires, IS_EMPTY_OR):
                    requires = requires.other
                if hasattr(requires, "options"):
                    table = current.s3db.org_organisation
                    options = requires.options()
                    ids = [option[0] for option in options if option[0]]
                    rows = current.db(table.id.belongs(ids)).select(table.id,
                                                                    table.pe_id,
                                                                    table.name,
                                                                    orderby=table.name)
                    options = []
                    for row in rows:
                        options.append(row.as_dict())
                else:
                    raise SyntaxError, "widget cannot determine options of %s" % field

        javascript_array = '''%s_options=%s''' % (name,
                                                  json.dumps(options))
        s3 = current.response.s3
        s3.js_global.append(javascript_array)
        s3.scripts.append("/%s/static/scripts/S3/s3.orghierarchy.js" % \
            current.request.application)
        s3.stylesheets.append("jquery-ui/jquery.ui.menu.css")

        return self.widget(field, value, **attributes)

# =============================================================================
class S3PersonAutocompleteWidget(FormWidget):
    """
        Renders a pr_person SELECT as an INPUT field with AJAX Autocomplete.
        Differs from the S3AutocompleteWidget in that it uses 3 name fields

        To make this widget use the HR table, set the controller to "hrm"

        @ToDo: Migrate to template (initial attempt failed)
   """

    def __init__(self,
                 controller = "pr",
                 function = "person_search",
                 post_process = "",
                 hideerror = False,
                 delay = 450,   # milliseconds
                 min_length=2): # Increase this for large deployments

        self.post_process = post_process
        self.delay = delay
        self.min_length = min_length
        self.c = controller
        self.f = function
        self.hideerror = hideerror

    def __call__(self, field, value, **attributes):

        default = dict(
            _type = "text",
            value = (value != None and str(value)) or "",
            )
        attr = StringWidget._attributes(field, default, **attributes)

        # Hide the real field
        attr["_class"] = "%s hide" % attr["_class"]

        if "_id" in attr:
            real_input = attr["_id"]
        else:
            real_input = str(field).replace(".", "_")

        dummy_input = "dummy_%s" % real_input

        if value:
            try:
                value = long(value)
            except ValueError:
                pass
            # Provide the representation for the current/default Value
            text = s3_unicode(field.represent(value))
            if "<" in text:
                text = s3_strip_markup(text)
            represent = text.encode("utf-8")
        else:
            represent = ""

        script = '''S3.autocomplete.person('%(module)s','%(resourcename)s','%(input)s',"%(postprocess)s",%(delay)s,%(min_length)s)''' % \
            dict(module = self.c,
                 resourcename = self.f,
                 input = real_input,
                 postprocess = self.post_process,
                 delay = self.delay,
                 min_length = self.min_length,
                 )
        current.response.s3.jquery_ready.append(script)
        return TAG[""](INPUT(_id=dummy_input,
                             _class="string",
                             _value=represent),
                       DIV(_id="%s_throbber" % dummy_input,
                           _class="throbber hide"),
                       INPUT(hideerror=self.hideerror, **attr),
                       requires = field.requires
                       )

# =============================================================================
class S3PriorityListWidget(StringWidget):
    """
        Widget to broadcast facility needs
    """

    def __call__(self, field, value, **attributes):

        s3 = current.response.s3

        default = dict(
            _type = "text",
            value = (value != None and str(value)) or "",
            )
        attr = StringWidget._attributes(field, default, **attributes)

        # @ToDo: i18n strings in JS
        #T = current.T

        selector = str(field).replace(".", "_")
        s3.jquery_ready.append('''
$('#%s').removeClass('list').addClass('prioritylist').prioritylist()''' % \
            (selector))

        # @ToDo: minify
        s3.scripts.append("/%s/static/scripts/S3/s3.prioritylist.js" % current.request.application)
        s3.stylesheets.append("S3/s3.prioritylist.css")

        return TAG[""](INPUT(**attr),
                       requires = field.requires
                       )

# =============================================================================
class S3SiteAutocompleteWidget(FormWidget):
    """
        Renders an org_site SELECT as an INPUT field with AJAX Autocomplete.
        Differs from the S3AutocompleteWidget in that it uses name & type fields
        in the represent
    """

    def __init__(self,
                 post_process = "",
                 delay = 450, # milliseconds
                 min_length = 2,
                 ):

        self.auth = current.auth
        self.post_process = post_process
        self.delay = delay
        self.min_length = min_length

    def __call__(self, field, value, **attributes):

        default = dict(
            _type = "text",
            value = (value != None and str(value)) or "",
            )
        attr = StringWidget._attributes(field, default, **attributes)

        # Hide the real field
        attr["_class"] = "%s hide" % attr["_class"]

        if "_id" in attr:
            real_input = attr["_id"]
        else:
            real_input = str(field).replace(".", "_")
        dummy_input = "dummy_%s" % real_input

        if value:
            try:
                value = long(value)
            except ValueError:
                pass
            # Provide the representation for the current/default Value
            text = s3_unicode(field.represent(value))
            if "<" in text:
                text = s3_strip_markup(text)
            represent = text.encode("utf-8")
        else:
            represent = ""

        s3 = current.response.s3
        site_types = current.auth.org_site_types
        for instance_type in site_types:
            # Change from T()
            site_types[instance_type] = s3_unicode(site_types[instance_type])
        site_types = '''S3.org_site_types=%s''' % json.dumps(site_types)
        js_global = s3.js_global
        if site_types not in js_global:
            js_global.append(site_types)
        script = '''S3.autocomplete.site('%(input)s',"%(postprocess)s",%(delay)s,%(min_length)s)''' % \
            dict(input = real_input,
                 postprocess = self.post_process,
                 delay = self.delay,
                 min_length = self.min_length,
                 )
        s3.jquery_ready.append(script)
        return TAG[""](INPUT(_id=dummy_input,
                             _class="string",
                             _value=represent),
                       DIV(_id="%s_throbber" % dummy_input,
                           _class="throbber hide"),
                       INPUT(**attr),
                       requires = field.requires
                       )

# =============================================================================
class S3SiteAddressAutocompleteWidget(FormWidget):
    """
        Renders an org_site SELECT as an INPUT field with AJAX Autocomplete.
        Differs from the S3AutocompleteWidget in that it searches both name & address fields
        & uses these in the represent
    """

    def __init__(self,
                 post_process = "",
                 delay = 450, # milliseconds
                 min_length = 2):

        self.auth = current.auth
        self.post_process = post_process
        self.delay = delay
        self.min_length = min_length

    def __call__(self, field, value, **attributes):

        default = dict(
            _type = "text",
            value = (value != None and str(value)) or "",
            )
        attr = StringWidget._attributes(field, default, **attributes)

        # Hide the real field
        attr["_class"] = "%s hide" % attr["_class"]

        if "_id" in attr:
            real_input = attr["_id"]
        else:
            real_input = str(field).replace(".", "_")
        dummy_input = "dummy_%s" % real_input

        if value:
            try:
                value = long(value)
            except ValueError:
                pass
            # Provide the representation for the current/default Value
            text = s3_unicode(field.represent(value))
            if "<" in text:
                text = s3_strip_markup(text)
            represent = text.encode("utf-8")
        else:
            represent = ""

        script = '''S3.autocomplete.site_address('%(input)s',"%(postprocess)s",%(delay)s,%(min_length)s)''' % \
            dict(input = real_input,
                 postprocess = self.post_process,
                 delay = self.delay,
                 min_length = self.min_length,
                 )
        current.response.s3.jquery_ready.append(script)
        return TAG[""](INPUT(_id=dummy_input,
                             _class="string",
                             _value=represent),
                       DIV(_id="%s_throbber" % dummy_input,
                           _class="throbber hide"),
                       INPUT(**attr),
                       requires = field.requires
                       )

# =============================================================================
class S3SliderWidget(FormWidget):
    """
        Standard Slider Widget

        @author: Daniel Klischies (daniel.klischies@freenet.de)

        @ToDo: The range of the slider should ideally be picked up from the Validator
        @ToDo: Show the value of the slider numerically as well as simply a position
    """

    def __init__(self,
                 minval,
                 maxval,
                 steprange,
                 value):
        self.minval = minval
        self.maxval = maxval
        self.steprange = steprange
        self.value = value

    def __call__(self, field, value, **attributes):

        response = current.response

        fieldname = str(field).replace(".", "_")
        sliderdiv = DIV(_id=fieldname, **attributes)
        inputid = "%s_input" % fieldname
        localfield = str(field).split(".")
        sliderinput = INPUT(_name=localfield[1],
                            _id=inputid,
                            _class="hide",
                            _value=self.value)

        response.s3.jquery_ready.append('''S3.slider('%s','%f','%f','%f','%f')''' % \
          (fieldname,
           self.minval,
           self.maxval,
           self.steprange,
           self.value))

        return TAG[""](sliderdiv, sliderinput)

# =============================================================================
class S3TimeIntervalWidget(FormWidget):
    """
        Simple time interval widget for the scheduler task table
    """

    multipliers = (("weeks", 604800),
                   ("days", 86400),
                   ("hours", 3600),
                   ("minutes", 60),
                   ("seconds", 1))

    # -------------------------------------------------------------------------
    @staticmethod
    def widget(field, value, **attributes):

        multipliers = S3TimeIntervalWidget.multipliers

        if value is None:
            value = 0

        if value == 0:
            multiplier = 1
        else:
            for m in multipliers:
                multiplier = m[1]
                if int(value) % multiplier == 0:
                    break

        options = []
        for i in xrange(1, len(multipliers) + 1):
            title, opt = multipliers[-i]
            if opt == multiplier:
                option = OPTION(title, _value=opt, _selected="selected")
            else:
                option = OPTION(title, _value=opt)
            options.append(option)

        val = value / multiplier
        inp = DIV(INPUT(value = val,
                        requires = field.requires,
                        _id = ("%s" % field).replace(".", "_"),
                        _name = field.name),
                  SELECT(options,
                         _name=("%s_multiplier" % field).replace(".", "_")))
        return inp

    # -------------------------------------------------------------------------
    @staticmethod
    def represent(value):

        multipliers = S3TimeIntervalWidget.multipliers

        try:
            val = int(value)
        except:
            val = 0

        if val == 0:
            multiplier = multipliers[-1]
        else:
            for m in multipliers:
                if val % m[1] == 0:
                    multiplier = m
                    break

        val = val / multiplier[1]
        return "%s %s" % (val, current.T(multiplier[0]))

# =============================================================================
class S3UploadWidget(UploadWidget):
    """
        Subclassed to not show the delete checkbox when field is mandatory
            - This now been included as standard within Web2Py from r2867
            - Leaving this unused example in the codebase so that we can easily
              amend this if we wish to later
    """

    @staticmethod
    def widget(field, value, download_url=None, **attributes):
        """
        generates a INPUT file tag.

        Optionally provides an A link to the file, including a checkbox so
        the file can be deleted.
        All is wrapped in a DIV.

        @see: :meth:`FormWidget.widget`
        @param download_url: Optional URL to link to the file (default = None)

        """

        default=dict(
            _type="file",
            )
        attr = UploadWidget._attributes(field, default, **attributes)

        inp = INPUT(**attr)

        if download_url and value:
            url = "%s/%s" % (download_url, value)
            (br, image) = ("", "")
            if UploadWidget.is_image(value):
                br = BR()
                image = IMG(_src = url, _width = UploadWidget.DEFAULT_WIDTH)

            requires = attr["requires"]
            if requires == [] or isinstance(requires, IS_EMPTY_OR):
                inp = DIV(inp, "[",
                          A(UploadWidget.GENERIC_DESCRIPTION, _href = url),
                          "|",
                          INPUT(_type="checkbox",
                                _name=field.name + UploadWidget.ID_DELETE_SUFFIX),
                          UploadWidget.DELETE_FILE,
                          "]", br, image)
            else:
                inp = DIV(inp, "[",
                          A(UploadWidget.GENERIC_DESCRIPTION, _href = url),
                          "]", br, image)
        return inp

# =============================================================================
class CheckboxesWidgetS3(OptionsWidget):
    """
        S3 version of gluon.sqlhtml.CheckboxesWidget:
        - configurable number of columns
        - supports also integer-type keys in option sets
        - has an identifiable class for styling

        Used in Sync, Projects, Assess, Facilities
    """

    @classmethod
    def widget(cls, field, value, **attributes):
        """
            generates a TABLE tag, including INPUT checkboxes (multiple allowed)

            see also: :meth:`FormWidget.widget`
        """

        #values = re.compile("[\w\-:]+").findall(str(value))
        values = not isinstance(value, (list, tuple)) and [value] or value
        values = [str(v) for v in values]

        attr = OptionsWidget._attributes(field, {}, **attributes)
        attr["_class"] = "checkboxes-widget-s3"

        requires = field.requires
        if not isinstance(requires, (list, tuple)):
            requires = [requires]

        if hasattr(requires[0], "options"):
            options = requires[0].options()
        else:
            raise SyntaxError, "widget cannot determine options of %s" \
                % field

        options = [(k, v) for k, v in options if k != ""]

        options_help = attributes.get("options_help", {})
        input_index = attributes.get("start_at", 0)

        opts = []
        cols = attributes.get("cols", 1)

        totals = len(options)
        mods = totals % cols
        rows = totals / cols
        if mods:
            rows += 1

        if totals == 0:
            T = current.T
            opts.append(TR(TD(SPAN(T("no options available"),
                                   _class="no-options-available"),
                              INPUT(_name=field.name,
                                    _class="hide",
                                    _value=None))))

        for r_index in range(rows):
            tds = []

            for k, v in options[r_index * cols:(r_index + 1) * cols]:
                input_id = "id-%s-%s" % (field.name, input_index)
                option_help = options_help.get(str(k), "")
                if option_help:
                    label = LABEL(v, _for=input_id, _title=option_help)
                else:
                    # Don't provide empty client-side popups
                    label = LABEL(v, _for=input_id)

                tds.append(TD(INPUT(_type="checkbox",
                                    _name=field.name,
                                    _id=input_id,
                                    # Hide checkboxes without a label
                                    _class="" if v else "hide",
                                    requires=attr.get("requires", None),
                                    hideerror=True,
                                    _value=k,
                                    value=(str(k) in values)),
                              label))

                input_index += 1
            opts.append(TR(tds))

        if opts:
            opts[-1][0][0]["hideerror"] = False
        return TABLE(*opts, **attr)

# =============================================================================
def s3_checkboxes_widget(field,
                         value,
                         options = None,
                         cols = 1,
                         start_at_id = 0,
                         help_field = None,
                         **attributes):
    """
        Display checkboxes for each value in the table column "field".

        @type cols: int
        @param cols: spread the input elements into "cols" columns

        @type start_at_id: int
        @param start_at_id: start input element ids at this number

        @type help_text: string
        @param help_text: field name string pointing to the field
                          containing help text for each option
    """

    values = not isinstance(value, (list, tuple)) and [value] or value
    values = [str(v) for v in values]

    field_name = field.name
    attributes["_name"] = "%s_widget" % field_name
    if "_id" not in attributes:
        attributes["_id"] = field_name
    if "_class" not in attributes:
        attributes["_class"] = "s3-checkboxes-widget"

    if options is None:
        requires = field.requires
        if not isinstance(requires, (list, tuple)):
            requires = [requires]

        if hasattr(requires[0], "options"):
            options = requires[0].options()
        else:
            raise SyntaxError, "widget cannot determine options of %s" % field

    help_text = Storage()
    if help_field:

        ktablename, pkey, multiple = s3_get_foreign_key(field)

        if isinstance(help_field, dict):
            # Convert the keys to strings (that's what the options are)
            for key in help_field.keys():
                help_text[str(key)] = help_field[key]

        elif hasattr(help_field, "__call__"):
            # Execute the callable
            help_field = help_field()
            # Convert the keys to strings (that's what the options are)
            for key in help_field.keys():
                help_text[str(key)] = help_field[key]

        elif ktablename is not None:

            ktable = current.s3db[ktablename]
            if hasattr(ktable, help_field):
                keys = [k for k, v in options if str(k).isdigit()]
                query = ktable[pkey].belongs(keys)
                rows = current.db(query).select(ktable[pkey],
                                                ktable[help_field])
                for row in rows:
                    help_text[str(row[pkey])] = row[help_field]
            else:
                # Error => no comments available
                pass
        else:
            # No lookup table => no comments available
            pass

    options = [(k, v) for k, v in options if k != ""]
    options = sorted(options, key=lambda option: s3_unicode(option[1]))

    input_index = start_at_id
    rows = []
    rappend = rows.append
    count = len(options)
    if count == 0:
        rows = TR(TD(SPAN(current.T("no options available"),
                          _class="no-options-available"),
                     INPUT(_type="hidden",
                           _name=field.name,
                           _value=None)))
    else:
        mods = count % cols
        num_of_rows = count / cols
        if mods:
            num_of_rows += 1

        for r in range(num_of_rows):
            cells = []
            cappend = cells.append

            for k, v in options[r * cols:(r + 1) * cols]:
                input_id = "id-%s-%s" % (field_name, input_index)

                title = help_text.get(str(k), None)
                if title:
                    label_attr = dict(_title=title)
                else:
                    label_attr = {}

                cappend(TD(INPUT(_type="checkbox",
                                _name=field_name,
                                _id=input_id,
                                hideerror=True,
                                _value=s3_unicode(k).encode("utf-8"),
                                value=(k in values)),
                        LABEL(v,
                                _for=input_id,
                                **label_attr)))

                input_index += 1

            rappend(TR(cells))

        if rows:
            rows[-1][0][0]["hideerror"] = False

    return TABLE(*rows, **attributes)

# =============================================================================
def s3_comments_widget(field, value, **attr):
    """
        A smaller-than-normal textarea
        to be used by the s3.comments() & gis.desc_field Reusable fields
    """

    if "_id" not in attr:
        _id = "%s_%s" % (field._tablename, field.name)
    else:
        _id = attr["_id"]
    if "_name" not in attr:
        _name = field.name
    else:
        _name = attr["_name"]

    return TEXTAREA(_name=_name,
                    _id=_id,
                    _class="comments %s" % (field.type),
                    value=value,
                    requires=field.requires)

# =============================================================================
def s3_grouped_checkboxes_widget(field,
                                 value,
                                 size = 24,
                                 **attributes):
    """
        Displays checkboxes for each value in the table column "field".
        If there are more than "size" options, they are grouped by the
        first letter of their label.

        @type field: Field
        @param field: Field (or Storage) object

        @type value: dict
        @param value: current value from the form field

        @type size: int
        @param size: number of input elements for each group

        Used by S3SearchOptionsWidget
    """

    requires = field.requires
    if not isinstance(requires, (list, tuple)):
        requires = [requires]

    if hasattr(requires[0], "options"):
        options = requires[0].options()
    else:
        raise SyntaxError, "widget cannot determine options of %s" \
            % field

    options = [(k, v) for k, v in options if k != ""]

    total = len(options)

    if total == 0:
        T = current.T
        options.append(TR(TD(SPAN(T("no options available"),
                                  _class="no-options-available"),
                             INPUT(_type="hide",
                                   _name=field.name,
                                   _value=None))))

    if total > size:
        # Options are put into groups of "size"

        import locale

        letters = []
        letters_options = {}

        append = letters.append
        for val, label in options:
            letter = label

            if letter:
                letter = s3_unicode(letter).upper()[0]
                if letter not in letters_options:
                    append(letter)
                    letters_options[letter] = [(val, label)]
                else:
                    letters_options[letter].append((val, label))

        widget = DIV(_class=attributes.pop("_class",
                                           "s3-grouped-checkboxes-widget"),
                     _name = "%s_widget" % field.name)

        input_index = 0
        group_index = 0
        group_options = []

        from_letter = u"A"
        to_letter = letters[0]
        letters.sort(locale.strcoll)

        lget = letters_options.get
        for letter in letters:
            if from_letter is None:
                from_letter = letter

            group_options += lget(letter, [])

            count = len(group_options)

            if count >= size or letter == letters[-1]:
                if letter == letters[-1]:
                    to_letter = u"Z"
                else:
                    to_letter = letter

                # Are these options for a single letter or a range?
                if to_letter != from_letter:
                    group_label = "%s - %s" % (from_letter, to_letter)
                else:
                    group_label = from_letter

                widget.append(DIV(group_label,
                                  _id="%s-group-label-%s" % (field.name,
                                                             group_index),
                                  _class="s3-grouped-checkboxes-widget-label expanded"))

                group_field = field
                # Can give Unicode issues:
                #group_field.requires = IS_IN_SET(group_options,
                #                                 multiple=True)

                letter_widget = s3_checkboxes_widget(group_field,
                                                     value,
                                                     options = group_options,
                                                     start_at_id=input_index,
                                                     **attributes)

                widget.append(letter_widget)

                input_index += count
                group_index += 1
                group_options = []
                from_letter = None

    else:
        # not enough options to form groups

        try:
            widget = s3_checkboxes_widget(field, value, **attributes)
        except:
            # some versions of gluon/sqlhtml.py don't support non-integer keys
            if s3_debug:
                raise
            else:
                return None

    return widget

# =============================================================================
def s3_richtext_widget(field, value):
    """
        A larger-than-normal textarea to be used by the CMS Post Body field
    """

    s3 = current.response.s3
    id = "%s_%s" % (field._tablename, field.name)

    # Load the scripts
    ckeditor = URL(c="static", f="ckeditor", args="ckeditor.js")
    s3.scripts.append(ckeditor)
    adapter = URL(c="static", f="ckeditor", args=["adapters",
                                                  "jquery.js"])
    s3.scripts.append(adapter)

    # Toolbar options: http://docs.cksource.com/CKEditor_3.x/Developers_Guide/Toolbar
    js = '''var ck_config={toolbar:[['Format','Bold','Italic','-','NumberedList','BulletedList','-','Link','Unlink','-','Image','Table','-','PasteFromWord','-','Source','Maximize']],toolbarCanCollapse:false,removePlugins:'elementspath'}'''
    s3.js_global.append(js)

    js = '''$('#%s').ckeditor(ck_config)''' % id
    s3.jquery_ready.append(js)

    return TEXTAREA(_name=field.name,
                    _id=id,
                    _class="richtext %s" % (field.type),
                    value=value,
                    requires=field.requires)

# =============================================================================
def search_ac(r, **attr):
    """
        JSON search method for S3AutocompleteWidget

        @param r: the S3Request
        @param attr: request attributes
    """

    output = None

    _vars = current.request.get_vars

    # JQueryUI Autocomplete uses "term" instead of "value"
    # (old JQuery Autocomplete uses "q" instead of "value")
    value = _vars.value or _vars.term or _vars.q or None

    # We want to do case-insensitive searches
    # (default anyway on MySQL/SQLite, but not PostgreSQL)
    value = value.lower().strip()

    if _vars.field and _vars.filter and value:
        s3db = current.s3db
        resource = r.resource
        table = resource.table

        limit = int(_vars.limit or 0)

        fieldname = str.lower(_vars.field)
        field = table[fieldname]

        # Default fields to return
        fields = [table.id, field]
        if resource.tablename == "org_site":
            # Simpler to provide an exception case than write a whole new class
            table = s3db.org_site
            fields.append(table.instance_type)

        filter = _vars.filter
        if filter == "~":
            # Normal single-field Autocomplete
            query = (field.lower().like(value + "%"))

        elif filter == "=":
            if field.type.split(" ")[0] in \
                ["reference", "id", "float", "integer"]:
                # Numeric, e.g. Organizations' offices_by_org
                query = (field == value)
            else:
                # Text
                query = (field.lower() == value)

        elif filter == "<":
            query = (field < value)

        elif filter == ">":
            query = (field > value)

        else:
            output = current.xml.json_message(
                        False,
                        400,
                        "Unsupported filter! Supported filters: ~, =, <, >")
            raise HTTP(400, body=output)

        # Exclude records which are already linked:
        #      ?link=<linktablename>.<leftkey>.<id>.<rkey>.<fkey>
        # e.g. ?link=project_organisation.organisation_id.5.project_id.id
        if "link" in _vars:
            try:
                link, lkey, _id, rkey, fkey = _vars.link.split(".")
                linktable = s3db[link]
                fq = (linktable[rkey] == table[fkey]) & \
                     (linktable[lkey] == _id)
                linked = current.db(fq).select(table._id)
                exclude = (~(table._id.belongs([r[table._id.name]
                                                for r in linked])))
            except Exception, e:
                pass # ignore
            else:
                query &= exclude

        # Select only or exclude template records:
        # to only select templates:
        #           ?template=<fieldname>.<value>,
        #      e.g. ?template=template.true
        # to exclude templates:
        #           ?template=~<fieldname>.<value>
        #      e.g. ?template=~template.true
        if "template" in _vars:
            try:
                flag, val = _vars.template.split(".", 1)
                if flag[0] == "~":
                    exclude = True
                    flag = flag[1:]
                else:
                    exclude = False
                ffield = table[flag]
            except:
                pass # ignore
            else:
                if str(ffield.type) == "boolean":
                    if val.lower() == "true":
                        val = True
                    else:
                        val = False
                if exclude:
                    templates = (ffield != val)
                else:
                    templates = (ffield == val)
                resource.add_filter(templates)

        resource.add_filter(query)

        if filter == "~":
            MAX_SEARCH_RESULTS = current.deployment_settings.get_search_max_results()
            if (not limit or limit > MAX_SEARCH_RESULTS) and \
               resource.count() > MAX_SEARCH_RESULTS:
                output = jsons([dict(id="",
                                     name="Search results are over %d. Please input more characters." \
                                     % MAX_SEARCH_RESULTS)])

        if output is None:
            output = S3Exporter().json(resource,
                                            start=0,
                                            limit=limit,
                                            fields=fields,
                                            orderby=field)
        current.response.headers["Content-Type"] = "application/json"

    else:
        output = current.xml.json_message(
                    False,
                    400,
                    "Missing options! Require: field, filter & value")
        raise HTTP(400, body=output)

    return output

# END =========================================================================
