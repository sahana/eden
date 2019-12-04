# -*- coding: utf-8 -*-

""" Custom UI Widgets

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @copyright: 2009-2019 (c) Sahana Software Foundation
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

__all__ = ("S3ACLWidget",
           "S3AddObjectWidget",
           "S3AddPersonWidget",
           "S3AgeWidget",
           "S3AutocompleteWidget",
           "S3BooleanWidget",
           "S3CascadeSelectWidget",
           "S3ColorPickerWidget",
           "S3CalendarWidget",
           "S3DateWidget",
           "S3DateTimeWidget",
           "S3HoursWidget",
           "S3EmbeddedComponentWidget",
           "S3GroupedOptionsWidget",
           #"S3RadioOptionsWidget",
           "S3HiddenWidget",
           "S3HierarchyWidget",
           "S3HumanResourceAutocompleteWidget",
           "S3ImageCropWidget",
           "S3InvBinWidget",
           "S3KeyValueWidget",
           # Only used inside this module
           #"S3LatLonWidget",
           "S3LocationAutocompleteWidget",
           "S3LocationDropdownWidget",
           "S3LocationLatLonWidget",
           "S3PasswordWidget",
           "S3PhoneWidget",
           "S3Selector",
           "S3LocationSelector",
           "S3MultiSelectWidget",
           "S3OrganisationAutocompleteWidget",
           "S3OrganisationHierarchyWidget",
           "S3PersonAutocompleteWidget",
           "S3PentityAutocompleteWidget",
           "S3PriorityListWidget",
           "S3SelectWidget",
           "S3SiteAutocompleteWidget",
           "S3SliderWidget",
           "S3StringWidget",
           "S3TimeIntervalWidget",
           #"S3UploadWidget",
           "S3FixedOptionsWidget",
           "S3QuestionEditorWidget",
           "CheckboxesWidgetS3",
           "s3_comments_widget",
           "s3_richtext_widget",
           "search_ac",
           "S3XMLContents",
           "S3TagCheckboxWidget",
           "ICON",
           )

import datetime
import json
import os
import re

try:
    from dateutil.relativedelta import relativedelta
except ImportError:
    import sys
    sys.stderr.write("ERROR: dateutil module needed for Date handling\n")
    raise

from gluon import *
# Here are dependencies listed for reference:
#from gluon import current
#from gluon.html import *
#from gluon.http import HTTP
#from gluon.validators import *
from gluon.html import BUTTON
from gluon.languages import lazyT
from gluon.sqlhtml import *
from gluon.storage import Storage

from s3compat import INTEGER_TYPES, basestring, long, sorted_locale, unicodeT, xrange
from .s3datetime import S3Calendar, S3DateTime
from .s3utils import *
from .s3validators import *

DEFAULT = lambda:None
ogetattr = object.__getattribute__
repr_select = lambda l: len(l.name) > 48 and "%s..." % l.name[:44] or l.name

# Compact JSON encoding
SEPARATORS = (",", ":")

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

        UNUSED

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
    var throbber = $('<div id="%(form_field_name)s_ajax_throbber" class="throbber"/>')
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
})''' % {"field_name": field.name,
         "form_field_name": "_".join((self.table_name, field.name)),
         "form_url": self.form_url,
         "dummy_field_selector": self.dummy_field_selector(self.table_name, field.name),
         "on_show": self.on_show,
         "on_hide": self.on_hide,
         "Add": T("Add..."),
         "Reload": T("Reload"),
         "Close": T("Close"),
         }
            )
        )

# =============================================================================
class S3AddPersonWidget(FormWidget):
    """
        Widget for person_id (future also: human_resource_id) fields that
        allows to either select an existing person (autocomplete), or to
        create a new person record inline

        Features:
        - embedded fields configurable in deployment settings
        - can use single name field (with on-submit name splitting),
          alternatively separate fields for first/middle/last names
        - can check for possible duplicates during data entry
        - fully encapsulated, works with regular validators (IS_ONE_OF)

        => Uses client-side script s3.ui.addperson.js (injected)
    """

    def __init__(self,
                 controller = None,
                 separate_name_fields = None,
                 father_name = None,
                 grandfather_name = None,
                 year_of_birth = None,
                 first_name_only = None,
                 pe_label = False,
                 ):
        """
            Constructor

            @param controller: controller for autocomplete
            @param separate_name_fields: use separate name fields, overrides
                                         deployment setting

            @param father_name: expose father name field, overrides
                                deployment setting
            @param grandfather_name: expose grandfather name field, overrides
                                     deployment setting

            @param year_of_birth: use just year-of-birth field instead of full
                                  date-of-birth, overrides deployment setting

            @param first_name_only: treat single name field entirely as
                                    first name (=do not split into name parts),
                                    overrides auto-detection, otherwise default
                                    for right-to-left written languages

            @param pe_label: expose ID label field
        """

        self.controller = controller
        self.separate_name_fields = separate_name_fields
        self.father_name = father_name
        self.grandfather_name = grandfather_name
        self.year_of_birth = year_of_birth
        self.first_name_only = first_name_only
        self.pe_label = pe_label

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):
        """
            Widget builder

            @param field: the Field
            @param value: the current or default value
            @param attributes: additional HTML attributes for the widget
        """

        s3db = current.s3db
        T = current.T

        # Attributes for the main input
        default = {"_type": "text",
                   "value": (value is not None and str(value)) or "",
                   }
        attr = StringWidget._attributes(field, default, **attributes)

        # Translations
        i18n = {"none_of_the_above": T("None of the above"),
                "loading": T("loading")
                }

        # Determine reference type
        reference_type = str(field.type)[10:]
        if reference_type == "pr_person":
            hrm = False
            fn = "person"
        # Currently not supported + no active use-case
        # @todo: implement in create_person()
        #elif reference_type == "hrm_human_resource":
        #    hrm = True
        #    fn = "human_resource"
        else:
            raise TypeError("S3AddPersonWidget: unsupported field type %s" % field.type)

        settings = current.deployment_settings

        # Field label overrides
        # (all other labels are looked up from the corresponding Field)
        self.labels = {
            "full_name": T(settings.get_pr_label_fullname()),
            "email": T("Email"),
            "mobile_phone": settings.get_ui_label_mobile_phone(),
            "home_phone": T("Home Phone"),
            }

        # Fields which, if enabled, are required
        # (all other fields are assumed to not be required)
        self.required = {
            "organisation_id": settings.get_hrm_org_required(),
            "full_name": True,
            "first_name": True,
            "middle_name": settings.get_L10n_mandatory_middlename(),
            "last_name": settings.get_L10n_mandatory_lastname(),
            "date_of_birth": settings.get_pr_dob_required(),
            "email": settings.get_hrm_email_required() if hrm else False,
        }

        # Determine controller for autocomplete
        controller = self.controller
        if not controller:
            controller = current.request.controller
            if controller not in ("pr", "dvr", "hrm", "vol"):
                controller = "hrm" if hrm else "pr"

        # Fields to extract and fields in form
        ptable = s3db.pr_person
        dtable = s3db.pr_person_details

        fields = {}
        details = False

        trigger = None
        formfields = []
        fappend = formfields.append

        values = {}

        # Organisation ID
        if hrm:
            htable = s3db.hrm_human_resource
            f = htable.organisation_id
            if f.default:
                values["organisation_id"] = s3_str(f.default)
            fields["organisation_id"] = f
            fappend("organisation_id")

        # ID Label
        pe_label = self.pe_label
        if pe_label:
            fields["pe_label"] = ptable.pe_label
            fappend("pe_label")

        # Name fields (always extract all)
        fields["first_name"] = ptable.first_name
        fields["last_name"] = ptable.last_name
        fields["middle_name"] = ptable.middle_name

        separate_name_fields = self.separate_name_fields
        if separate_name_fields is None:
            separate_name_fields = settings.get_pr_separate_name_fields()

        if separate_name_fields:

            # Detect order of name fields
            name_format = settings.get_pr_name_format()
            keys = StringTemplateParser.keys(name_format)

            if keys and keys[0] == "last_name":
                # Last name first
                trigger = "last_name"
                fappend("last_name")
                fappend("first_name")
            else:
                # First name first
                trigger = "first_name"
                fappend("first_name")
                fappend("last_name")

            if separate_name_fields == 3:
                if keys and keys[-1] == "middle_name":
                    fappend("middle_name")
                else:
                    formfields.insert(-1, "middle_name")

        else:

            # Single combined name field
            fields["full_name"] = True
            fappend("full_name")

        # Additional name fields
        father_name = self.father_name
        if father_name is None:
            # Not specified => apply deployment setting
            father_name = settings.get_pr_request_father_name()
        if father_name:
            f = dtable.father_name
            i18n["father_name_label"] = f.label
            fields["father_name"] = f
            details = True
            fappend("father_name")

        grandfather_name = self.grandfather_name
        if grandfather_name is None:
            # Not specified => apply deployment setting
            grandfather_name  = settings.get_pr_request_grandfather_name()
        if grandfather_name:
            f = dtable.grandfather_name
            i18n["grandfather_name_label"] = f.label
            fields["grandfather_name"] = f
            details = True
            fappend("grandfather_name")

        # Date of Birth / Year of birth
        year_of_birth = self.year_of_birth
        if year_of_birth is None:
            # Use Global deployment_setting
            year_of_birth = settings.get_pr_request_year_of_birth()
        if year_of_birth:
            fields["year_of_birth"] = dtable.year_of_birth
            details = True
            fappend("year_of_birth")
        elif settings.get_pr_request_dob():
            fields["date_of_birth"] = ptable.date_of_birth
            fappend("date_of_birth")

        # Gender
        if settings.get_pr_request_gender():
            f = ptable.gender
            if f.default:
                values["gender"] = s3_str(f.default)
            fields["gender"] = f
            fappend("gender")

        # Occupation
        if controller == "vol":
            fields["occupation"] = dtable.occupation
            details = True
            fappend("occupation")

        # Contact Details
        if settings.get_pr_request_email():
            fields["email"] = True
            fappend("email")
        if settings.get_pr_request_mobile_phone():
            fields["mobile_phone"] = True
            fappend("mobile_phone")
        if settings.get_pr_request_home_phone():
            fields["home_phone"] = True
            fappend("home_phone")

        self.fields = fields

        # Extract existing values
        if value:
            record_id = None
            if isinstance(value, basestring) and not value.isdigit():
                data, error = self.parse(value)
                if not error:
                    if all(k in data for k in formfields):
                        values = data
                    else:
                        record_id = data.get("id")
            else:
                record_id = value
            if record_id:
                values = self.extract(record_id, fields, hrm=hrm, details=details)

        # Generate the embedded rows
        widget_id = str(field).replace(".", "_")
        formrows = self.embedded_form(field.label, widget_id, formfields, values)

        # Widget Options (pass only non-default options)
        widget_options = {}

        # Duplicate checking?
        lookup_duplicates = settings.get_pr_lookup_duplicates()
        if lookup_duplicates:
            # Add translations for duplicates-review
            i18n.update({"Yes": T("Yes"),
                         "No": T("No"),
                         "dupes_found": T("_NUM_ duplicates found"),
                         })
            widget_options["lookupDuplicates"] = True

        if settings.get_ui_icons() != "font-awesome":
            # Non-default icon theme => pass icon classes
            widget_options["downIcon"] = ICON("down").attributes.get("_class")
            widget_options["yesIcon"] = ICON("deployed").attributes.get("_class")
            widget_options["noIcon"] = ICON("remove").attributes.get("_class")

        # Use separate name fields?
        if separate_name_fields:
            widget_options["separateNameFields"] = True
            if trigger:
                widget_options["trigger"] = trigger

        # Non default AC controller/function?
        if controller != "pr":
            widget_options["c"] = controller
        if fn != "person":
            widget_options["f"] = fn

        # Non-default AC trigger parameters?
        delay = settings.get_ui_autocomplete_delay()
        if delay != 800:
            widget_options["delay"] = delay
        chars = settings.get_ui_autocomplete_min_chars()
        if chars != 2:
            widget_options["chars"] = chars

        # Inject the scripts
        self.inject_script(widget_id, widget_options, i18n)

        # Create and return the main input
        attr["_class"] = "hide"

        # Prepend internal validation
        requires = field.requires
        if requires:
            requires = (self.validate, requires)
        else:
            requires = self.validate
        attr["requires"] = requires

        return TAG[""](DIV(INPUT(**attr), _class = "hide"), formrows)

    # -------------------------------------------------------------------------
    def extract(self, record_id, fields, details=False, hrm=False):
        """
            Extract the data for a record ID

            @param record_id: the record ID
            @param fields: the fields to extract, dict {propName: Field}
            @param details: includes person details
            @param hrm: record ID is a hrm_human_resource ID rather
                        than person ID

            @return: dict of {propName: value}
        """

        db = current.db

        s3db = current.s3db
        ptable = s3db.pr_person
        dtable = s3db.pr_person_details

        qfields = [f for f in fields.values() if type(f) is not bool]
        qfields.append(ptable.pe_id)

        if hrm:
            htable = s3db.hrm_human_resource
            query = (htable.id == record_id)
            join = ptable.on(ptable.id == htable.person_id)
        else:
            query = (ptable.id == record_id)
            join = None

        if details:
            left = dtable.on(dtable.person_id == ptable.id)
        else:
            left = None

        row = db(query).select(join = join,
                               left = left,
                               limitby = (0, 1),
                               *qfields).first()
        if not row:
            # Raise?
            return {}


        person = row.pr_person if join or left else row
        values = dict((k, person[k]) for k in person)

        if fields.get("full_name"):
            values["full_name"] = s3_fullname(person)

        if details:
            details = row.pr_person_details
            for k in details:
                values[k] = details[k]

        if hrm:
            human_resource = row.hrm_human_resource
            for k in human_resource:
                values[k] = human_resource[k]

        values.update(self.get_contact_data(row.pe_id))

        return values

    # -------------------------------------------------------------------------
    def get_contact_data(self, pe_id):
        """
            Extract the contact data for a pe_id; extracts only the first
            value per contact method

            @param pe_id: the pe_id

            @return: a dict {fieldname: value}, where field names
                     correspond to the contact method (field map)
        """

        # Map contact method <=> form field name
        names = {"EMAIL": "email",
                 "HOME_PHONE": "home_phone",
                 "SMS": "mobile_phone",
                 }

        # Determine relevant contact methods
        fields = self.fields
        methods = set(m for m in names if fields.get(names[m]))

        # Initialize values with relevant fields
        values = dict.fromkeys((names[m] for m in methods), "")

        if methods:

            # Retrieve the contact data
            ctable = current.s3db.pr_contact
            query = (ctable.pe_id == pe_id) & \
                    (ctable.deleted == False) & \
                    (ctable.contact_method.belongs(methods))

            rows = current.db(query).select(ctable.contact_method,
                                            ctable.value,
                                            orderby=ctable.priority,
                                            )

            # Extract the values
            for row in rows:
                method = row.contact_method
                if method in methods:
                    values[names[method]] = row.value
                    methods.discard(method)
                if not methods:
                    break

        return values

    # -------------------------------------------------------------------------
    def embedded_form(self, label, widget_id, formfields, values):
        """
            Construct the embedded form

            @param label: the label for the embedded form
                          (= field label for the person_id)
            @param widget_id: the widget ID
                              (=element ID of the person_id field)
            @param formfields: list of field names indicating which
                               fields to render and in which order
            @param values: dict with values to populate the embedded
                           form

            @return: a DIV containing the embedded form rows
        """

        T = current.T
        s3 = current.response.s3
        settings = current.deployment_settings

        # Test the formstyle
        formstyle = s3.crud.formstyle
        tuple_rows = isinstance(formstyle("", "", "", ""), tuple)

        rows = DIV()

        # Section Title + Actions
        title_id = "%s_title" % widget_id
        label = LABEL(label, _for=title_id)

        widget = DIV(A(ICON("edit"),
                       _class="edit-action",
                       _title=T("Edit Entry"),
                       ),
                     A(ICON("remove"),
                       _class="cancel-action",
                       _title=T("Revert Entry"),
                       ),
                     _class="add_person_edit_bar hide",
                     _id="%s_edit_bar" % widget_id,
                     )

        if tuple_rows:
            row = TR(TD(DIV(label, widget, _class="box_top_inner"),
                        _class="box_top_td",
                        _colspan=2,
                        ),
                     _id="%s__row" % title_id,
                     )
        else:
            row = formstyle("%s__row" % title_id, label, widget, "")
            row.add_class("box_top hide")

        rows.append(row)

        # Input rows
        for fname in formfields:

            field = self.fields.get(fname)
            if not field:
                continue # Field is disabled

            field_id = "%s_%s" % (widget_id, fname)

            label = self.get_label(fname)
            required = self.required.get(fname, False)
            if required:
                label = DIV("%s:" % label, SPAN(" *", _class="req"))
            else:
                label = "%s:" % label
            label = LABEL(label, _for=field_id)

            widget = self.get_widget(fname, field)
            value = values.get(fname, "")
            if not widget:
                value = s3_str(value)
                widget = INPUT(_id = field_id,
                               _name = fname,
                               _value = value,
                               old_value = value,
                               )
            else:
                widget = widget(field,
                                value,
                                requires = None,
                                _id = field_id,
                                old_value = value,
                                )


            row = formstyle("%s__row" % field_id, label, widget, "")
            if tuple_rows:
                row[0].add_class("box_middle")
                row[1].add_class("box_middle")
                rows.append(row[0])
                rows.append(row[1])
            else:
                row.add_class("box_middle hide")
                rows.append(row)

        # Divider (bottom box)
        if tuple_rows:
            row = formstyle("%s_box_bottom" % widget_id, "", "", "")
            row = row[0]
            row.add_class("box_bottom")
        else:
            row = DIV(_id="%s_box_bottom" % widget_id,
                      _class="box_bottom hide",
                      )
            if settings.ui.formstyle == "bootstrap":
                # Need to add custom classes to core HTML markup
                row.add_class("control-group")
        rows.append(row)

        return rows

    # -------------------------------------------------------------------------
    def get_label(self, fieldname):
        """
            Get a label for an embedded field

            @param fieldname: the name of the embedded form field

            @return: the label
        """

        label = self.labels.get(fieldname)
        if label is None:
            # use self.fields
            field = self.fields.get(fieldname)
            if not field or field is True:
                label = ""
            else:
                label = field.label

        return label

    # -------------------------------------------------------------------------
    def get_widget(self, fieldname, field):
        """
            Get a widget for an embedded field; only when the field needs
            a specific widget => otherwise return None here, so the form
            builder will render a standard INPUT

            @param fieldname: the name of the embedded form field
            @param field: the Field corresponding to the form field

            @return: the widget; or None if no specific widget is required
        """

        # Fields which require a specific widget
        widget = None

        if fieldname in ("organisation_id", "gender"):
            widget = OptionsWidget.widget

        elif fieldname == "date_of_birth":
            if hasattr(field, "widget"):
                widget = field.widget

        return widget

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

        request = current.request
        s3 = current.response.s3

        # Static script
        if s3.debug:
            script = "/%s/static/scripts/S3/s3.ui.addperson.js" % \
                     request.application
        else:
            script = "/%s/static/scripts/S3/s3.ui.addperson.min.js" % \
                     request.application
        scripts = s3.scripts
        if script not in scripts:
            scripts.append(script)
            self.inject_i18n(i18n)

        # Widget options
        opts = {}
        if options:
            opts.update(options)

        # Widget instantiation
        script = '''$('#%(widget_id)s').addPerson(%(options)s)''' % \
                 {"widget_id": widget_id,
                  "options": json.dumps(opts),
                  }
        jquery_ready = s3.jquery_ready
        if script not in jquery_ready:
            jquery_ready.append(script)

    # -------------------------------------------------------------------------
    def inject_i18n(self, labels):
        """
            Inject translations for screen messages rendered by the
            client-side script

            @param labels: dict of translations {messageKey: translation}
        """

        strings = ['''i18n.%s="%s"''' % (k, s3_str(v))
                                        for k, v in labels.items()]
        current.response.s3.js_global.append("\n".join(strings))

    # -------------------------------------------------------------------------
    def validate(self, value):
        """
            Validate main input value

            @param value: the main input value (JSON)

            @return: tuple (id, error), where "id" is the record ID of the
                     selected or newly created record
        """

        if not isinstance(value, basestring) or value.isdigit():
            # Not a JSON object => return as-is
            return value, None

        data, error = self.parse(value)
        if (error):
            return value, error

        person_id = data.get("id")
        if person_id:
            # Existing record selected => return ID as-is
            return person_id, None

        # Establish the name(s)
        names = self.get_names(data)
        if not names:
            # Treat as empty
            return None, None
        else:
            data.update(names)

        # Validate phone numbers
        mobile = data.get("mobile_phone")
        if mobile:
            validator = IS_PHONE_NUMBER(international=True)
            mobile, error = validator(mobile)
            if error:
                return (None, error)

        home_phone = data.get("home_phone")
        if home_phone:
            validator = IS_PHONE_NUMBER()
            home_phone, error = validator(home_phone)
            if error:
                return (None, error)

        # Validate date of birth
        dob = data.get("date_of_birth")
        if not dob and \
           self.fields.get("date_of_birth") and \
           self.required.get("date_of_birth"):
            return (None, T("Date of Birth is Required"))

        # Validate the email
        error = self.validate_email(data.get("email"))[1]
        if error:
            return (None, error)

        # Try to create the person records (and related records)
        return self.create_person(data)

    # -------------------------------------------------------------------------
    def parse(self, value):
        """
            Parse the main input JSON when the form gets submitted

            @param value: the main input value (JSON)

            @return: tuple (data, error), where data is a dict with the
                     submitted data like: {fieldname: value, ...}
        """

        from .s3validators import JSONERRORS
        try:
            data = json.loads(value)
        except JSONERRORS:
            return value, "invalid JSON"

        if type(data) is not dict:
            return value, "invalid JSON"

        return data, None

    # -------------------------------------------------------------------------
    def get_names(self, data):
        """
            Get first, middle and last names from the input data

            @param data: the input data dict

            @return: dict with the name parts found
        """

        settings = current.deployment_settings

        separate_name_fields = self.separate_name_fields
        if separate_name_fields is None:
            separate_name_fields = settings.get_pr_separate_name_fields()

        keys = ["first_name", "middle_name", "last_name"]

        if separate_name_fields:

            names = {}

            for key in keys:
                value = data.get(key)
                if value:
                    names[key] = value

        else:

            fullname = data.get("full_name")

            if fullname:

                # Shall all name parts go into first_name?
                first_name_only = self.first_name_only
                if first_name_only is None:
                    # Activate by default if using RTL
                    first_name_only = current.response.s3.rtl

                if first_name_only:

                    # Put all name parts into first_name
                    names = {"first_name": fullname}

                else:

                    # Separate the name parts
                    name_format = settings.get_pr_name_format()
                    parts = StringTemplateParser.keys(name_format)
                    if parts and parts[0] == "last_name":
                        keys.reverse()
                    names = dict(zip(keys, self.split_names(fullname)))

            else:

                names = {}

        return names

    # -------------------------------------------------------------------------
    @staticmethod
    def split_names(name):
        """
            Split a full name into first/middle/last

            @param name: the full name

            @return: tuple (first, middle, last)
        """

        # https://github.com/derek73/python-nameparser
        from nameparser import HumanName
        name = HumanName(name)

        return name.first, name.middle, name.last

    # -------------------------------------------------------------------------
    def validate_email(self, value, person_id=None):
        """
            Validate the email address; checks whether the email address
            is valid and unique

            @param value: the email address
            @param person_id: the person ID, if known

            @return: tuple (value, error), where error is None if the
                     email address is valid, otherwise contains the
                     error message
        """

        T = current.T

        error_message = T("Please enter a valid email address")

        if value is not None:
            value = value.strip()

        # No email?
        if not value:
            # @todo: may not need to check whether email is enabled?
            email_required = self.fields.get("email") and \
                             self.required.get("email")
            if email_required:
                return (value, error_message)
            return (value, None)

        # Valid email?
        value, error = IS_EMAIL()(value)
        if error:
            return value, error_message

        # Unique email?
        s3db = current.s3db
        ctable = s3db.pr_contact
        query = (ctable.deleted != True) & \
                (ctable.contact_method == "EMAIL") & \
                (ctable.value == value)
        if person_id:
            ptable = s3db.pr_person
            query &= (ctable.pe_id == ptable.pe_id) & \
                     (ptable.id != person_id)
        email = current.db(query).select(ctable.id, limitby=(0, 1)).first()
        if email:
            error_message = T("This email-address is already registered.")
            return value, error_message

        # Ok!
        return value, None

    # -------------------------------------------------------------------------
    def create_person(self, data):
        """
            Create a new record from form data

            @param data - the submitted data
            @return: tuple (id, error), where "id" is the record ID of the
                     newly created record
        """

        s3db = current.s3db

        # Validate the person fields
        ptable = s3db.pr_person
        person = {}
        for f in ptable._filter_fields(data):
            if f == "id":
                continue
            value, error = s3_validate(ptable, f, data[f])
            if error:
                label = ptable[f].label or f
                return (None, "%s: %s" % (label, error))
            else:
                person[f] = value

        # Onvalidation? (doesn't currently exist)

        # Create new person record
        person_id = ptable.insert(**person)

        if not person_id:
            return (None, T("Could not add person record"))

        # Update the super-entities
        record = {"id": person_id}
        s3db.update_super(ptable, record)

        # Update ownership & realm
        current.auth.s3_set_record_owner(ptable, person_id)

        # Onaccept? (not relevant for this case)

        # Read the created pe_id
        pe_id = record.get("pe_id")
        if not pe_id:
            return (None, T("Could not add person details"))

        # Add contact information as provided
        ctable = s3db.pr_contact
        contacts = {"email": "EMAIL",
                    "home_phone": "HOME_PHONE",
                    "mobile_phone": "SMS",
                    }
        for fname, contact_method in contacts.items():
            value = data.get(fname)
            if value:
                ctable.insert(pe_id = pe_id,
                              contact_method = contact_method,
                              value = value,
                              )

        # Add details as provided
        details = {}
        for fname in ("occupation",
                      "father_name",
                      "grandfather_name",
                      "year_of_birth",
                      ):
            value = data.get(fname)
            if value:
                details[fname] = value
        if details:
            details["person_id"] = person_id
            s3db.pr_person_details.insert(**details)

        return person_id, None

# =============================================================================
class S3AgeWidget(FormWidget):
    """
        Widget to accept and represent date of birth as age in years,
        mapping the age to a pseudo date-of-birth internally so that
        it progresses over time; contains both widget and representation
        method

        @example:
            s3_date("date_of_birth",
                    label = T("Age"),
                    widget = S3AgeWidget.widget,
                    represent = lambda v: S3AgeWidget.date_as_age(v) \
                                          if v else current.messages["NONE"],
                    ...
                    )
    """

    @classmethod
    def widget(cls, field, value, **attributes):
        """
            The widget method, renders a simple integer-input

            @param field: the Field
            @param value: the current or default value
            @param attributes: additional HTML attributes for the widget
        """

        if isinstance(value, basestring) and value and not value.isdigit():
            # ISO String
            value = current.calendar.parse_date(value)

        age = cls.date_as_age(value)

        attr = IntegerWidget._attributes(field, {"value": age}, **attributes)

        # Inner validation
        requires = (IS_INT_IN_RANGE(0, 150), cls.age_as_date)

        # Accept empty if field accepts empty
        if isinstance(field.requires, IS_EMPTY_OR):
            requires = IS_EMPTY_OR(requires)
        attr["requires"] = requires

        return INPUT(**attr)

    # -------------------------------------------------------------------------
    @staticmethod
    def date_as_age(value, row=None):
        """
            Convert a date value into age in years, can be used as
            representation method

            @param value: the date

            @return: the age in years (integer)
        """

        if value and isinstance(value, datetime.date):
            from dateutil.relativedelta import relativedelta
            age = relativedelta(current.request.utcnow, value).years
        else:
            age = value
        return age

    # -------------------------------------------------------------------------
    @staticmethod
    def age_as_date(value, error_message="invalid age"):
        """
            Convert age in years into an approximate date of birth, acts
            as inner validator of the widget

            @param value: age value
            @param error_message: error message (override)

            @returns: tuple (date, error)
        """

        try:
            age = int(value)
        except ValueError:
            return None, error_message

        from dateutil.relativedelta import relativedelta
        date = (current.request.utcnow - relativedelta(years=age)).date()

        # Map back to January 1st of the year of birth
        # => common practice, but needs validation as requirement
        date = date.replace(month=1, day=1)

        return date, None

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
                 post_process = "",
                 ):

        self.module = module
        self.resourcename = resourcename
        self.fieldname = fieldname
        self.filter = filter
        self.link_filter = link_filter
        self.post_process = post_process

        # @ToDo: Refreshes all dropdowns as-necessary
        self.post_process = post_process or ""

    def __call__(self, field, value, **attributes):

        s3 = current.response.s3
        settings = current.deployment_settings

        default = {"_type": "text",
                   "value": (value is not None and str(value)) or "",
                   }
        attr = StringWidget._attributes(field, default, **attributes)

        # Hide the real field
        attr["_class"] = attr["_class"] + " hide"

        if "_id" in attr:
            real_input = attr["_id"]
        else:
            real_input = str(field).replace(".", "_")
        dummy_input = "dummy_%s" % real_input

        # JS Function defined in static/scripts/S3/S3.js
        script = '''S3.autocomplete.normal('%s','%s','%s','%s','%s',"%s"''' % \
            (self.fieldname,
             self.module,
             self.resourcename,
             real_input,
             self.filter,
             self.link_filter,
             )

        options = ""
        post_process = self.post_process
        delay = settings.get_ui_autocomplete_delay()
        min_length = settings.get_ui_autocomplete_min_chars()
        if min_length != 2:
            options = ''',"%(postprocess)s",%(delay)s,%(min_length)s''' % \
                {"postprocess": post_process,
                 "delay": delay,
                 "min_length": min_length,
                 }
        elif delay != 800:
            options = ''',"%(postprocess)s",%(delay)s''' % \
                {"postprocess": post_process,
                 "delay": delay,
                 }
        elif post_process:
            options = ''',"%(postprocess)s"''' % \
                {"postprocess": post_process,
                 }

        script = '''%s%s)''' % (script, options)
        s3.jquery_ready.append(script)

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

        s3.js_global.append('''i18n.none_of_the_above="%s"''' % current.T("None of the above"))

        return TAG[""](INPUT(_id=dummy_input,
                             _class="string",
                             _value=represent.encode("utf-8")),
                       DIV(_id="%s_throbber" % dummy_input,
                           _class="throbber input_throbber hide"),
                       INPUT(**attr),
                       requires = field.requires
                       )

# =============================================================================
class S3BooleanWidget(BooleanWidget):
    """
        Standard Boolean widget, with an option to hide/reveal fields conditionally.
    """

    def __init__(self, fields=None, click_to_show=True):

        if fields is None:
            self.fields = ()
        else:
            self.fields = fields
        self.click_to_show = click_to_show

    def __call__(self, field, value, **attributes):

        response = current.response
        fields = self.fields
        click_to_show = self.click_to_show

        default = {"_type": "checkbox",
                   "value": value,
                   }

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
class S3ColorPickerWidget(FormWidget):
    """
        Displays a widget to allow the user to pick a
        color, and falls back to using JSColor or a regular text input if
        necessary.
    """

    DEFAULT_OPTIONS = {
        "showInput": True,
        "showInitial": True,
        "preferredFormat": "hex",
        #"showPalette": True,
        "showPaletteOnly": True,
        "togglePaletteOnly": True,
        "palette": ("red", "orange", "yellow", "green", "blue", "white", "black")
    }

    def __init__(self, options=None):
        """
            @param options: options for the JavaScript widget
            @see: http://bgrins.github.com/spectrum/
        """

        self.options = dict(self.DEFAULT_OPTIONS)
        self.options.update(options or {})

    def __call__(self, field, value, **attributes):

        default = {#"_type": "color", # We don't want to use native HTML5 widget as it doesn't support our options & is worse for documentation
                   "_type": "text",
                   "value": (value is not None and str(value)) or "",
                   }

        attr = StringWidget._attributes(field, default, **attributes)

        widget = INPUT(**attr)

        if "_id" in attr:
            selector = attr["_id"]
        else:
            selector = str(field).replace(".", "_")

        s3 = current.response.s3

        _min = "" if s3.debug else ".min"

        script = "/%s/static/scripts/spectrum%s.js" % \
            (current.request.application, _min)
        style = "plugins/spectrum%s.css" % _min

        if script not in s3.scripts:
            s3.scripts.append(script)

        if style not in s3.stylesheets:
            s3.stylesheets.append(style)

        # i18n of Strings
        T = current.T
        options = self.options
        options.update(cancelText = s3_unicode(T("cancel")),
                       chooseText = s3_unicode(T("choose")),
                       togglePaletteMoreText = s3_unicode(T("more")),
                       togglePaletteLessText = s3_unicode(T("less")),
                       clearText = s3_unicode(T("Clear Color Selection")),
                       noColorSelectedText = s3_unicode(T("No Color Selected")),
                       )

        options = json.dumps(options, separators=SEPARATORS)
        # Ensure we save in rrggbb format not #rrggbb (IS_HTML_COLOUR)
        options = "%s,change:function(c){this.value=c.toHex()}}" % options[:-1]
        script = \
'''$('#%(selector)s').spectrum(%(options)s)''' % {"selector": selector,
                                                  "options": options,
                                                  }
        s3.jquery_ready.append(script)

        return widget

# =============================================================================
class S3CalendarWidget(FormWidget):
    """
        Widget to select a date from a popup calendar, with
        optional time input

        @note: this widget must be combined with the IS_UTC_DATE or
               IS_UTC_DATETIME validators to have the value properly
               converted from/to local timezone and format.

        - control script is s3.ui.calendar.js
        - uses jQuery UI DatePicker for Gregorian calendars: https://jqueryui.com/datepicker/
        - uses jQuery UI Timepicker-addon if using times: http://trentrichardson.com/examples/timepicker
        - uses Calendars for non-Gregorian calendars: http://keith-wood.name/calendars.html
            (for this, ensure that css.cfg includes calendars/ui.calendars.picker.css and
                                                    calendars/ui-smoothness.calendars.picker.css)
    """

    def __init__(self,
                 calendar=None,
                 date_format=None,
                 time_format=None,
                 separator=None,
                 minimum=None,
                 maximum=None,
                 past=None,
                 future=None,
                 past_months=None,
                 future_months=None,
                 month_selector=False,
                 year_selector=True,
                 min_year=None,
                 max_year=None,
                 week_number=False,
                 buttons=None,
                 timepicker=False,
                 minute_step=5,
                 set_min=None,
                 set_max=None,
                 clear_text=None,
                 ):
        """
            Constructor

            @param calendar: which calendar to use (override default)

            @param date_format: the date format (override default)
            @param time_format: the time format (override default)
            @param separator: date-time separator (override default)

            @param minimum: the minimum selectable date/time (overrides past)
            @param maximum: the maximum selectable date/time (overrides future)
            @param past: how many hours into the past are selectable (overrides past_months)
            @param future: how many hours into the future are selectable (overrides future_months)
            @param past_months: how many months into the past are selectable
            @param future_months: how many months into the future are selectable

            @param month_selector: show a months drop-down
            @param year_selector: show a years drop-down
            @param min_year: the minimum selectable year (can be relative to now like "-10")
            @param max_year: the maximum selectable year (can be relative to now like "+10")

            @param week_number: show the week number in the calendar
            @param buttons: show the button panel (defaults to True if
                            the widget has a timepicker, else False)

            @param timepicker: show a timepicker
            @param minute_step: minute-step for the timepicker slider

            @param set_min: CSS selector for another S3Calendar widget for which to
                            dynamically update the minimum selectable date/time from
                            the selected date/time of this widget
            @param set_max: CSS selector for another S3Calendar widget for which to
                            dynamically update the maximum selectable date/time from
                            the selected date/time of this widget
        """

        self.calendar = calendar

        self.date_format = date_format
        self.time_format = time_format
        self.separator = separator

        self.minimum = minimum
        self.maximum = maximum
        self.past = past
        self.future = future
        self.past_months = past_months
        self.future_months = future_months

        self.month_selector = month_selector
        self.year_selector = year_selector
        self.min_year = min_year
        self.max_year = max_year

        self.week_number = week_number
        self.buttons = buttons if buttons is not None else timepicker

        self.timepicker = timepicker
        self.minute_step = minute_step

        self.set_min = set_min
        self.set_max = set_max

        self.clear_text = clear_text

        self._class = "s3-calendar-widget datetimepicker"

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):
        """
            Widget builder

            @param field: the Field
            @param value: the current value
            @param attributes: the HTML attributes for the widget
        """

        # Modify class as required
        _class = self._class

        # Default attributes
        defaults = {"_type": "text",
                    "_class": _class,
                    "value": value,
                    "requires": field.requires,
                    }
        attr = self._attributes(field, defaults, **attributes)

        # Real input ID
        input_id = attr.get("_id")
        if not input_id:
            if isinstance(field, Field):
                input_id = str(field).replace(".", "_")
            else:
                input_id = field.name.replace(".", "_")
            attr["_id"] = input_id


        # Real input name attribute
        input_name = attr.get("_name")
        if not input_name:
            input_name = field.name.replace(".", "_")
            attr["_name"] = input_name

        # Container ID
        container_id = "%s-calendar-widget" % input_id

        # Script options
        settings = current.deployment_settings

        calendar = self.calendar or current.calendar.name
        calendar = calendar if calendar and calendar != "Gregorian" else "gregorian"

        date_format = self.date_format or \
                      settings.get_L10n_date_format()
        time_format = self.time_format or \
                      settings.get_L10n_time_format()
        separator = self.separator or \
                    settings.get_L10n_datetime_separator()

        c = current.calendar if not self.calendar else S3Calendar(self.calendar)
        firstDOW = c.first_dow

        dtformat = separator.join([date_format, time_format])
        extremes = self.extremes(dtformat=dtformat)

        T = current.T

        clear_text = self.clear_text
        if clear_text is None:
            clear_text = s3_str(T("Clear"))
        else:
            clear_text = s3_str(T(clear_text))

        options = {"calendar": calendar,
                   "dateFormat": str(date_format),
                   "timeFormat": str(time_format),
                   "separator": separator,
                   "firstDOW": firstDOW,
                   "monthSelector": self.month_selector,
                   "yearSelector": self.year_selector,
                   "showButtons": self.buttons,
                   "weekNumber": self.week_number,
                   "timepicker": self.timepicker,
                   "minuteStep": self.minute_step,
                   "todayText": s3_str(T("Today")),
                   "nowText": s3_str(T("Now")),
                   "closeText": s3_str(T("Done")),
                   "clearText": clear_text,
                   "setMin": self.set_min,
                   "setMax": self.set_max,
                   }
        options.update(extremes)

        if settings.get_ui_calendar_clear_icon():
            options["clearButton"] = "icon"

        # Inject JS
        self.inject_script(input_id, options)

        # Construct real input
        real_input = INPUT(**attr)

        # Construct and return the widget
        return TAG[""](DIV(real_input,
                           _id=container_id,
                           _class="calendar-widget-container",
                           ),
                       )

    # -------------------------------------------------------------------------
    def extremes(self, dtformat=None):
        """
            Compute the minimum/maximum selectable date/time, as well as
            the default time (=the minute-step closest to now)

            @param dtformat: the user datetime format

            @return: a dict {minDateTime, maxDateTime, defaultValue, yearRange}
                     with the min/max options as ISO-formatted strings, and the
                     defaultValue in user-format (all in local time), to be
                     passed as-is to s3.calendarwidget
        """

        extremes = {}
        now = current.request.utcnow

        # RAD : default to something quite generous
        pyears, fyears = 80, 80

        # Minimum
        earliest = None
        fallback = False
        if self.minimum:
            earliest = self.minimum
            if type(earliest) is datetime.date:
                # Consistency with S3Calendar
                earliest = datetime.datetime.combine(earliest, datetime.time(8, 0, 0))
        elif self.past is not None:
            earliest = now - datetime.timedelta(hours=self.past)
        elif self.past_months is not None:
            earliest = now - relativedelta(months=self.past_months)
        else:
            fallback = True
            earliest = now - datetime.timedelta(hours=876000)
        if earliest is not None:
            if not fallback:
                pyears = abs(earliest.year - now.year)
            earliest = S3DateTime.to_local(earliest.replace(microsecond=0))
            extremes["minDateTime"] = earliest.isoformat()

        # Maximum
        latest = None
        fallback = False
        if self.maximum:
            latest = self.maximum
            if type(latest) is datetime.date:
                # Consistency with S3Calendar
                latest = datetime.datetime.combine(latest, datetime.time(8, 0, 0))
        elif self.future is not None:
            latest = now + datetime.timedelta(hours=self.future)
        elif self.future_months is not None:
            latest = now + relativedelta(months=self.future_months)
        else:
            fallback = True
            latest = now + datetime.timedelta(hours=876000)
        if latest is not None:
            if not fallback:
                fyears = abs(latest.year - now.year)
            latest = S3DateTime.to_local(latest.replace(microsecond=0))
            extremes["maxDateTime"] = latest.isoformat()

        # Default date/time
        if self.timepicker and dtformat:
            # Pick a start date/time
            if earliest <= now <= latest:
                start = now
            elif now < earliest:
                start = earliest
            elif now > latest:
                start = latest
            # Round to the closest minute-step
            step = self.minute_step * 60
            seconds = (start - start.min).seconds
            rounding = (seconds + step / 2) // step * step
            rounded = start + datetime.timedelta(0,
                                                 rounding - seconds,
                                                 -start.microsecond,
                                                 )
            # Limits
            if rounded < earliest:
                rounded = earliest
            elif rounded > latest:
                rounded = latest
            # Translate into local time
            rounded = S3DateTime.to_local(rounded)
            # Convert into user format
            default = rounded.strftime(dtformat)
            extremes["defaultValue"] = default

        # Year range
        min_year = self.min_year
        if not min_year:
            min_year = "-%s" % pyears
        max_year = self.max_year
        if not max_year:
            max_year = "+%s" % fyears
        extremes["yearRange"] = "%s:%s" % (min_year, max_year)

        return extremes

    # -------------------------------------------------------------------------
    def inject_script(self, selector, options):
        """
            Helper function to inject the document-ready-JavaScript for
            this widget.

            @param field: the Field
            @param value: the current value
            @param attr: the HTML attributes for the widget
        """

        if not selector:
            return

        s3 = current.response.s3
        appname = current.request.application

        request = current.request
        s3 = current.response.s3

        datepicker_l10n = None
        timepicker_l10n = None
        calendars_type = None
        calendars_l10n = None
        calendars_picker_l10n = None

        # Paths to localization files
        datepicker_l10n_path = os.path.join(request.folder, "static", "scripts", "ui", "i18n")
        timepicker_l10n_path = os.path.join(request.folder, "static", "scripts", "ui", "i18n")
        calendars_l10n_path = os.path.join(request.folder, "static", "scripts", "calendars", "i18n")

        calendar = options["calendar"].lower()
        if calendar != "gregorian":
            # Include the right calendar script
            filename = "jquery.calendars.%s.js" % calendar
            lscript = os.path.join(calendars_l10n_path, filename)
            if os.path.exists(lscript):
                calendars_type = "calendars/i18n/%s" % filename

        language = current.session.s3.language
        if language in current.deployment_settings.date_formats:
            # Localise if we have configured a Date Format and we have a jQueryUI options file

            # Do we have a suitable locale file?
            #if language in ("prs", "ps"):
            #    # Dari & Pashto use Farsi
            #    language = "fa"
            #elif language == "ur":
            #    # Urdu uses Arabic
            #    language = "ar"
            if "-" in language:
                parts = language.split("-", 1)
                language = "%s-%s" % (parts[0], parts[1].upper())

            # datePicker regional
            filename = "datepicker-%s.js" % language
            path = os.path.join(timepicker_l10n_path, filename)
            if os.path.exists(path):
                timepicker_l10n = "ui/i18n/%s" % filename

            # timePicker regional
            filename = "jquery-ui-timepicker-%s.js" % language
            path = os.path.join(datepicker_l10n_path, filename)
            if os.path.exists(path):
                datepicker_l10n = "ui/i18n/%s" % filename

            if calendar != "gregorian" and language:
                # calendars regional
                filename = "jquery.calendars.%s-%s.js" % (calendar, language)
                path = os.path.join(calendars_l10n_path, filename)
                if os.path.exists(path):
                    calendars_l10n = "calendars/i18n/%s" % filename
                # calendarsPicker regional
                filename = "jquery.calendars.picker-%s.js" % language
                path = os.path.join(calendars_l10n_path, filename)
                if os.path.exists(path):
                    calendars_picker_l10n = "calendars/i18n/%s" % filename
        else:
            language = ""

        options["language"] = language

        # Global scripts
        if s3.debug:
            scripts = ("jquery.plugin.js",
                       "calendars/jquery.calendars.all.js",
                       "calendars/jquery.calendars.picker.ext.js",
                       "S3/s3.ui.calendar.js",
                       datepicker_l10n,
                       timepicker_l10n,
                       calendars_type,
                       calendars_l10n,
                       calendars_picker_l10n,
                       )
        else:
            scripts = ("jquery.plugin.min.js",
                       "S3/s3.ui.calendar.min.js",
                       datepicker_l10n,
                       timepicker_l10n,
                       calendars_type,
                       calendars_l10n,
                       calendars_picker_l10n,
                       )
        for script in scripts:
            if not script:
                continue
            path = "/%s/static/scripts/%s" % (appname, script)
            if path not in s3.scripts:
                s3.scripts.append(path)

        # jQuery-ready script
        script = '''$('#%(selector)s').calendarWidget(%(options)s);''' % \
                 {"selector": selector, "options": json.dumps(options)}
        s3.jquery_ready.append(script)

# =============================================================================
class S3DateWidget(FormWidget):
    """
        Standard Date widget
    """

    def __init__(self,
                 format = None,
                 #past=1440,
                 #future=1440,
                 past=None,
                 future=None,
                 start_field = None,
                 default_interval = None,
                 default_explicit = False,
                 ):
        """
            Constructor

            @param format: format of date
            @param past: how many months into the past the date can be set to
            @param future: how many months into the future the date can be set to
            @param start_field: "selector" for start date field
            @param default_interval: x months from start date
            @param default_explicit: bool for explicit default
        """

        self.format = format
        self.past = past
        self.future = future
        self.start_field = start_field
        self.default_interval = default_interval
        self.default_explicit = default_explicit

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):
        """
            Widget builder

            @param field: the Field
            @param value: the current value
            @param attributes: the HTML attributes for the widget
        """

        # Need to convert value into ISO-format
        # (widget expects ISO, but value comes in custom format)
        dt = current.calendar.parse_date(value, local=True)
        if dt:
            value = dt.isoformat()

        request = current.request
        settings = current.deployment_settings

        s3 = current.response.s3

        jquery_ready = s3.jquery_ready
        language = current.session.s3.language

        if language in settings.date_formats:
            # Localise if we have configured a Date Format and we have a jQueryUI options file
            # Do we have a suitable locale file?
            if language in ("prs", "ps"):
                # Dari & Pashto use Farsi
                language = "fa"
            #elif language == "ur":
            #    # Urdu uses Arabic
            #    language = "ar"
            elif "-" in language:
                parts = language.split("-", 1)
                language = "%s-%s" % (parts[0], parts[1].upper())
            path = os.path.join(request.folder, "static", "scripts", "ui", "i18n", "datepicker-%s.js" % language)
            if os.path.exists(path):
                lscript = "/%s/static/scripts/ui/i18n/datepicker-%s.js" % (request.application, language)
                if lscript not in s3.scripts:
                    # 1st Datepicker
                    s3.scripts.append(lscript)
                    script = '''$.datepicker.setDefaults($.datepicker.regional["%s"])''' % language
                    jquery_ready.append(script)

        if self.format:
            # default: "yy-mm-dd"
            format = str(self.format)
        else:
            dtfmt = settings.get_L10n_date_format()
            format = dtfmt.replace("%Y", "yy") \
                          .replace("%y", "y") \
                          .replace("%m", "mm") \
                          .replace("%d", "dd") \
                          .replace("%b", "M")

        default = {"_type": "text",
                   "value": (value is not None and str(value)) or "",
                   }

        attr = StringWidget._attributes(field, default, **attributes)

        widget = INPUT(**attr)
        widget.add_class("date")

        if "_id" in attr:
            selector = attr["_id"]
        else:
            selector = str(field).replace(".", "_")

        # Convert to Days
        now = current.request.utcnow
        past = self.past
        if past is None:
            past = ""
        else:
            if past:
                past = now - relativedelta(months=past)
                if now > past:
                    days = (now - past).days
                    minDate = "-%s" % days
                else:
                    days = (past - now).days
                    minDate = "+%s" % days
            else:
                minDate = "-0"
            past = ",minDate:%s" % minDate

        future = self.future
        if future is None:
            future = ""
        else:
            if future:
                future = now + relativedelta(months=future)
                if future > now:
                    days = (future - now).days
                    maxDate = "+%s" % days
                else:
                    days = (now - future).days
                    maxDate = "-%s" % days
            else:
                maxDate = "+0"
            future = ",maxDate:%s" % maxDate

        # Set auto updation of end_date based on start_date if start_field attr are set
        start_field = self.start_field
        default_interval = self.default_interval

        script = \
'''$('#%(selector)s').datepicker('option',{yearRange:'c-100:c+100',dateFormat:'%(format)s'%(past)s%(future)s}).one('click',function(){$(this).focus()})''' % \
            {"selector": selector,
             "format": format,
             "past": past,
             "future": future,
             }

        if script not in jquery_ready: # Prevents loading twice when form has errors
            jquery_ready.append(script)

        if start_field and default_interval:

            T = current.T

            # Setting i18n for labels
            i18n = '''
i18n.interval="%(interval_label)s"
i18n.btn_1_label="%(btn_first_label)s"
i18n.btn_2_label="%(btn_second_label)s"
i18n.btn_3_label="%(btn_third_label)s"
i18n.btn_4_label="%(btn_fourth_label)s"
i18n.btn_clear="%(btn_clear)s"
''' % {"interval_label": T("Interval"),
       "btn_first_label": T("+6 MO"),
       "btn_second_label": T("+1 YR"),
       "btn_third_label": T("+2 YR"),
       "btn_fourth_label": T("+5 YR"),
       "btn_clear": T("Clear"),
       }

            s3.js_global.append(i18n)

            script = '''
$('#%(end_selector)s').end_date_interval({
start_date_selector:"#%(start_selector)s",
interval:%(interval)d
%(default_explicit)s
})
''' % {"end_selector": selector,
       "start_selector": start_field,
       "interval": default_interval,
       "default_explicit": ",default_explicit:true" if self.default_explicit else "",
       }

            if script not in jquery_ready:
                jquery_ready.append(script)

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

        default = {"_type": "text",
                   "_class": self._class,
                   "value": value,
                   }
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
        opts_get = opts.get

        if "_id" in attributes:
            selector = attributes["_id"]
        else:
            selector = str(field).replace(".", "_")

        settings = current.deployment_settings
        date_format = opts_get("date_format",
                               settings.get_L10n_date_format())
        time_format = opts_get("time_format",
                               settings.get_L10n_time_format())
        separator = opts_get("separator",
                             settings.get_L10n_datetime_separator())
        datetime_format = "%s%s%s" % (date_format, separator, time_format)

        request = current.request
        s3 = current.response.s3
        jquery_ready = s3.jquery_ready
        language = current.session.s3.language
        if language in settings.date_formats:
            # Localise if we have configured a Date Format and we have a jQueryUI options file
            # Do we have a suitable locale file?
            if language in ("prs", "ps"):
                # Dari & Pashto use Farsi
                language = "fa"
            #elif language == "ur":
            #    # Urdu uses Arabic
            #    language = "ar"
            elif "-" in language:
                parts = language.split("_", 1)
                language = "%s-%s" % (parts[0], parts[1].upper())
            path = os.path.join(request.folder, "static", "scripts", "ui", "i18n", "datepicker-%s.js" % language)
            if os.path.exists(path):
                lscript = "/%s/static/scripts/ui/i18n/datepicker-%s.js" % (request.application, language)
                if lscript not in s3.scripts:
                    # 1st Datepicker
                    s3.scripts.append(lscript)
                    script = '''$.datepicker.setDefaults($.datepicker.regional["%s"])''' % language
                    jquery_ready.append(script)

        # Option to hide the time slider
        hide_time = opts_get("hide_time", False)
        if hide_time:
            limit = "Date"
            widget = "datepicker"
            dtformat = date_format
        else:
            limit = "DateTime"
            widget = "datetimepicker"
            dtformat = datetime_format

        # Limits
        now = request.utcnow
        timedelta = datetime.timedelta

        if "min" in opts:
            earliest = opts["min"]
        else:
            past = opts_get("past", 876000)
            earliest = now - timedelta(hours = past)
        if "max" in opts:
            latest = opts["max"]
        else:
            future = opts_get("future", 876000)
            latest = now + timedelta(hours = future)

        # Closest minute step as default
        minute_step = opts_get("minute_step", 5)
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
            rounded = S3DateTime.to_local(rounded)
            default = rounded.strftime(dtformat)
        else:
            default = ""

        # Convert extremes to local time
        earliest = S3DateTime.to_local(earliest)
        latest = S3DateTime.to_local(latest)

        # Update limits of another widget?
        set_min = opts_get("set_min", None)
        set_max = opts_get("set_max", None)
        onclose = '''function(selectedDate){'''
        onclear = ""
        if set_min:
            onclose += '''$('#%s').%s('option','minDate',selectedDate)\n''' % \
                       (set_min, widget)
            onclear += '''$('#%s').%s('option','minDate',null)\n''' % \
                       (set_min, widget)
        if set_max:
            onclose += '''$('#%s').%s('option','maxDate',selectedDate)''' % \
                       (set_max, widget)
            onclear += '''$('#%s').%s('option','minDate',null)''' % \
                       (set_max, widget)
        onclose += '''}'''

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

        # Year range
        pyears, fyears = 10, 10
        if "min" in opts or "past" in opts:
            pyears = abs(earliest.year - now.year)
        if "max" in opts or "future" in opts:
            fyears = abs(latest.year - now.year)
        year_range = "%s:%s" % (opts_get("min_year", "-%s" % pyears),
                                opts_get("max_year", "+%s" % fyears))

        # Other options
        firstDOW = settings.get_L10n_firstDOW()

        # Boolean options
        getopt = lambda opt, default: opts_get(opt, default) and "true" or "false"

        script = \
'''$('#%(selector)s').%(widget)s({
 showSecond:false,
 firstDay:%(firstDOW)s,
 min%(limit)s:new Date(Date.parse('%(earliest)s')),
 max%(limit)s:new Date(Date.parse('%(latest)s')),
 dateFormat:'%(date_format)s',
 timeFormat:'%(time_format)s',
 separator:'%(separator)s',
 stepMinute:%(minute_step)s,
 showWeek:%(weeknumber)s,
 showButtonPanel:%(buttons)s,
 changeMonth:%(month_selector)s,
 changeYear:%(year_selector)s,
 yearRange:'%(year_range)s',
 useLocalTimezone:true,
 defaultValue:'%(default)s',
 onClose:%(onclose)s
}).one('click',function(){$(this).focus()})
var clear_button=$('<button id="%(selector)s_clear" class="btn date-clear-btn" type="button">%(clear)s</button>').click(function(){
 $('#%(selector)s').val('');%(onclear)s;$('#%(selector)s').closest('.filter-form').trigger('optionChanged')
})
if($('#%(selector)s_clear').length==0){
 $('#%(selector)s').after(clear_button)
}''' %  {"selector": selector,
         "widget": widget,
         "date_format": date_format,
         "time_format": time_format,
         "separator": separator,
         "weeknumber": getopt("weeknumber", False),
         "month_selector": getopt("month_selector", False),
         "year_selector": getopt("year_selector", True),
         "buttons": getopt("buttons", True),
         "firstDOW": firstDOW,
         "year_range": year_range,
         "minute_step": minute_step,
         "limit": limit,
         "earliest": earliest.strftime(ISO),
         "latest": latest.strftime(ISO),
         "default": default,
         "clear": current.T("clear"),
         "onclose": onclose,
         "onclear": onclear,
         }

        if script not in jquery_ready: # Prevents loading twice when form has errors
            jquery_ready.append(script)

        return

# =============================================================================
class S3HoursWidget(FormWidget):
    """
        Widget to enter a duration in hours (e.g. of a task), supporting
        flexible input format (e.g. "1h 15min", "1.75", "2:10")

        NB users who frequently enter minutes-fragments sometimes forget
           that the field expects hours, e.g. input of "15" interpreted
           as 15 hours while the user actually meant 15 minutes. To avoid
           this, use the explicit_above parameter to require an explicit
           time unit or colon notation for implausible numbers (e.g. >10)
           - so the user must enter "15h", "15m", "15:00" or "0:15" explicitly.
    """

    PARTS = re.compile(r"((?:[+-]{0,1}\s*)(?:[0-9,.:]+)\s*(?:[^0-9,.:+-]*))")
    TOKEN = re.compile(r"([+-]{0,1}\s*)([0-9,.:]+)([^0-9,.:+-]*)")

    def __init__(self, interval=None, precision=2, explicit_above=None):
        """
            Constructor

            @param interval: standard interval to round up to (minutes),
                             None to disable rounding
            @param precision: number of decimal places to keep
            @param explicit_above: require explicit time unit or colon notation
                                   for value fragments above this limit
        """

        self.interval = interval
        self.precision = precision

        self.explicit_above = explicit_above

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):
        """
            Entry point for form processing

            @param field: the Field
            @param value: the current/default value
            @param attributes: HTML attributes for the widget
        """

        default = {"value": (value != None and str(value)) or ""}
        attr = StringWidget._attributes(field, default, **attributes)

        attr["requires"] = self.validate

        widget = INPUT(**attr)
        widget.add_class("hours")

        return widget

    # -------------------------------------------------------------------------
    def validate(self, value):
        """
            Pre-validator to parse the input value before validating it

            @param value: the input value

            @returns: tuple (parsed, error)
        """

        try:
            return self.s3_parse(value), None
        except SyntaxError as e:
            # Input format violation
            return value, str(e)
        except:
            return value, "invalid value"

    # -------------------------------------------------------------------------
    def s3_parse(self, value):
        """
            Function to parse the input value (if it is a string)

            @param value: the value
            @returns: the value as float (hours)
        """

        hours = 0.0

        if value is None or value == "":
            return None
        elif not value:
            return hours

        explicit_above = self.explicit_above

        parts = self.PARTS.split(value)
        for part in parts:

            token = part.strip()
            if not token:
                continue

            m = self.TOKEN.match(token)
            if not m:
                continue

            sign = m.group(1).strip()
            num = m.group(2)

            unit = m.group(3).lower()
            unit, implicit = (unit[0], False) if unit else ("h", ":" not in num)
            if unit == "s":
                length = 1
                factor = 3600.0
            elif unit == "m":
                length = 2
                factor = 60.0
            else:
                length = 3
                factor = 1.0

            segments = (num.replace(",", ".").split(":") + ["0", "0", "0"])[:length]
            total = 0.0
            for segment in segments:
                try:
                    v = float(segment)
                except ValueError:
                    v = 0.0
                total += v / factor
                factor *= 60

            if explicit_above is not None and total > explicit_above and implicit:
                msg = current.T("Specify a time unit or use HH:MM format")
                raise SyntaxError(s3_str(msg))
            if sign == "-":
                hours -= total
            else:
                hours += total

        interval = self.interval
        if interval:
            import math
            interval = float(interval)
            hours = math.ceil(hours * 60.0 / interval) * interval / 60.0

        precision = self.precision
        return round(hours, precision) if precision is not None else hours

# =============================================================================
class S3EmbeddedComponentWidget(FormWidget):
    """
        Widget used by S3CRUD for link-table components with actuate="embed".
        Uses s3.embed_component.js for client-side processing, and
        S3CRUD._postprocess_embedded to receive the data.
    """

    def __init__(self,
                 link=None,
                 component=None,
                 autocomplete=None,
                 link_filter=None,
                 select_existing=True):
        """
            Constructor

            @param link: the name of the link table
            @param component: the name of the component table
            @param autocomplete: name of the autocomplete field
            @param link_filter: filter expression to filter out records
                                in the component that are already linked
                                to the main record
            @param select_existing: allow the selection of existing
                                    component records from the registry
        """

        self.link = link
        self.component = component
        self.autocomplete = autocomplete
        self.select_existing = select_existing
        self.link_filter = link_filter

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):
        """
            Widget renderer

            @param field: the Field
            @param value: the current value
            @param attributes: the HTML attributes for the widget
        """

        T = current.T

        # Input ID
        if "_id" in attributes:
            input_id = attributes["_id"]
        else:
            input_id = str(field).replace(".", "_")

        # Form style and widget style
        s3 = current.response.s3
        formstyle = s3.crud.formstyle
        if not callable(formstyle) or \
           isinstance(formstyle("","","",""), tuple):
            widgetstyle = self._formstyle
        else:
            widgetstyle = formstyle

        # Subform controls
        controls = TAG[""](A(T("Select from Registry"),
                             _id="%s-select" % input_id,
                             _class="action-btn",
                             ),
                           A(T("Remove Selection"),
                             _id="%s-clear" % input_id,
                             _class="action-btn hide",
                             _style="padding-left:15px;",
                             ),
                           A(T("Edit Details"),
                             _id="%s-edit" % input_id,
                             _class="action-btn hide",
                             _style="padding-left:15px;",
                             ),
                           DIV(_class="throbber hide",
                               _style="padding-left:85px;",
                               ),
                           )
        controls = widgetstyle("%s-select-row" % input_id,
                               "",
                               controls,
                               "",
                               )
        controls.add_class("box_top" if self.select_existing else "hide")

        s3db = current.s3db
        ctable = s3db[self.component]
        prefix, resourcename = self.component.split("_", 1)

        # Selector
        autocomplete = self.autocomplete
        if autocomplete:
            # Autocomplete widget
            ac_field = ctable[autocomplete]

            widget = S3AutocompleteWidget(prefix,
                                          resourcename=resourcename,
                                          fieldname=autocomplete,
                                          link_filter=self.link_filter,
                                          )
            selector = widgetstyle("%s-autocomplete-row" % input_id,
                                   LABEL("%s: " % ac_field.label,
                                         _class="hide",
                                         _id="%s-autocomplete-label" % input_id),
                                   widget(field, value),
                                   "",
                                   )
            selector.add_class("box_top")
        else:
            # Options widget
            # @todo: add link_filter here as well
            widget = OptionsWidget.widget(field, None,
                                          _class="hide",
                                          _id="dummy_%s" % input_id,
                                          )
            label = LABEL("%s: " % field.label,
                          _class="hide",
                          _id="%s-autocomplete-label" % input_id,
                          )
            hidden_input = INPUT(_id=input_id, _class="hide")

            selector = widgetstyle("%s-autocomplete-row" % input_id,
                                   label,
                                   TAG[""](widget, hidden_input),
                                   "",
                                   )
            selector.add_class("box_top")

        # Initialize field validators with the correct record ID
        fields = [f for f in ctable
                    if (f.writable or f.readable) and not f.compute]
        request = current.request
        if field.name in request.post_vars:
            selected = request.post_vars[field.name]
        else:
            selected = None
        if selected:
            for f in fields:
                requires = f.requires or []
                if not isinstance(requires, (list, tuple)):
                    requires = [requires]
                [r.set_self_id(selected) for r in requires
                                         if hasattr(r, "set_self_id")]

        # Mark required
        labels, required = s3_mark_required(fields)
        if required:
            s3.has_required = True

        # Generate embedded form
        form = SQLFORM.factory(table_name=self.component,
                               labels=labels,
                               formstyle=formstyle,
                               upload="default/download",
                               separator = "",
                               *fields)

        # Re-wrap the embedded form rows in an empty TAG
        formrows = []
        append = formrows.append
        for formrow in form[0]:
            if not formrow.attributes["_id"].startswith("submit_record"):
                if hasattr(formrow, "add_class"):
                    formrow.add_class("box_middle embedded-%s" % input_id)
                append(formrow)
        formrows = TAG[""](formrows)

        # Divider
        divider = widgetstyle("", "", DIV(_class="subheading"), "")
        divider.add_class("box_bottom embedded")

        # Widget script
        appname = request.application
        if s3.debug:
            script = "s3.ui.embeddedcomponent.js"
        else:
            script = "s3.ui.embeddedcomponent.min.js"
        script = "/%s/static/scripts/S3/%s" % (appname, script)
        if script not in s3.scripts:
            s3.scripts.append(script)

        # Script options
        url = "/%s/%s/%s/" % (appname, prefix, resourcename)
        options = {"ajaxURL": url,
                   "fieldname": input_id,
                   "component": self.component,
                   "recordID": str(value),
                   "autocomplete": True if autocomplete else False,
                   }

        # Post-process after Selection/Deselection
        post_process = s3db.get_config(self.link, "post_process")
        if post_process:
            try:
                pp = post_process % input_id
            except TypeError:
                pp = post_process
            options["postprocess"] = pp

        # Initialize UI Widget
        script = '''$('#%(input)s').embeddedComponent(%(options)s)''' % \
                 {"input": input_id, "options": json.dumps(options)}
        s3.jquery_ready.append(script)

        # Overall layout of components
        return TAG[""](controls, selector, formrows, divider)

    # -------------------------------------------------------------------------
    @staticmethod
    def _formstyle(row_id, label, widget, comments):
        """
            Fallback for legacy formstyles (i.e. not callable or tuple-rows)
        """

        return TR(TD(label, widget, _class="w2p_fw"),
                  TD(comments),
                  _id=row_id,
                  )

    # -------------------------------------------------------------------------
    @staticmethod
    def link_filter_query(table, expression):
        """
            Parse a link filter expression and convert it into an
            S3ResourceQuery that can be added to the search_ac resource.

            Link filter expressions are used to exclude records from
            the (autocomplete-)search that are already linked to the master
            record.

            General format:
                ?link=<linktablename>.<leftkey>.<id>.<rkey>.<fkey>

            Example:
                ?link=project_organisation.organisation_id.5.project_id.id

            @param expression: the link filter expression
        """

        try:
            link, lkey, _id, rkey, fkey = expression.split(".")
        except ValueError:
            # Invalid expression
            return None
        linktable = current.s3db.table(link)
        if linktable:
            fq = (linktable[rkey] == table[fkey]) & \
                 (linktable[lkey] == _id)
            if "deleted" in linktable:
                fq &= (linktable.deleted != True)
            linked = current.db(fq).select(table._id)
            from .s3query import FS
            pkey = FS("id")
            exclude = (~(pkey.belongs([r[table._id.name] for r in linked])))
            return exclude
        return None

# -----------------------------------------------------------------------------
def S3GenericAutocompleteTemplate(post_process,
                                  delay,
                                  min_length,
                                  field,
                                  value,
                                  attributes,
                                  source = None,
                                  transform_value = lambda value: value,
                                  tablename = None, # Allow variations
                                  ):
    """
        Renders a SELECT as an INPUT field with AJAX Autocomplete
    """

    value = transform_value(value)

    default = {"_type": "text",
               "value": (value is not None and s3_unicode(value)) or "",
               }
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

    if tablename == "org_organisation":
        # S3OrganisationAutocompleteWidget
        script = \
'''S3.autocomplete.org('%(input)s',"%(postprocess)s",%(delay)s,%(min_length)s)''' % \
            {"input": real_input,
             "postprocess": post_process,
             "delay": delay,
             "min_length": min_length,
             }
    else:
        # Currently unused
        script = \
'''S3.autocomplete.generic('%(url)s','%(input)s',"%(postprocess)s",%(delay)s,%(min_length)s)''' % \
            {"url": source,
             "input": real_input,
             "postprocess": post_process,
             "delay": delay,
             "min_length": min_length,
             }
    current.response.s3.jquery_ready.append(script)
    return TAG[""](INPUT(_id=dummy_input,
                         _class="string",
                         value=represent),
                   DIV(_id="%s_throbber" % dummy_input,
                       _class="throbber input_throbber hide"),
                   INPUT(**attr),
                   requires = field.requires
                   )

#==============================================================================
class S3GroupedOptionsWidget(FormWidget):
    """
        Widget with checkboxes or radio buttons for S3OptionsFilter
        - checkboxes can be optionally grouped by letter
    """

    def __init__(self,
                 options=None,
                 multiple=True,
                 size=None,
                 cols=None,
                 help_field=None,
                 none=None,
                 sort=True,
                 orientation=None,
                 table=True,
                 no_opts=None,
                 option_comment=None,
                 ):
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
            @param sort: sort the options (only effective if size==None)
            @param orientation: the ordering orientation, "columns"|"rows"
            @param table: whether to render options inside a table or not
            @param no_opts: text to show if no options available
            @param comment: HTML template to render after the LABELs
        """

        self.options = options
        self.multiple = multiple
        self.size = size
        self.cols = cols or 3
        self.help_field = help_field
        self.none = none
        self.sort = sort
        self.orientation = orientation
        self.table = table
        self.no_opts = no_opts
        self.option_comment = option_comment

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
        if self.multiple:
            attr["_multiple"] = "multiple"
        widget = SELECT(**attr)
        if "empty" not in options:
            groups = options["groups"]
            append = widget.append
            render_group = self._render_group
            for group in groups:
                options = render_group(group)
                for option in options:
                    append(option)

        no_opts = self.no_opts
        if no_opts is None:
            no_opts = s3_str(current.T("No options available"))
        widget.add_class("groupedopts-widget")
        widget_opts = {"columns": self.cols,
                       "emptyText": no_opts,
                       "orientation": self.orientation or "columns",
                       "sort": self.sort,
                       "table": self.table,
                       }

        if self.option_comment:
            widget_opts["comment"] = self.option_comment
            s3_include_underscore()

        script = '''$('#%s').groupedopts(%s)''' % \
                 (_id, json.dumps(widget_opts, separators=SEPARATORS))
        jquery_ready = current.response.s3.jquery_ready
        if script not in jquery_ready:
            jquery_ready.append(script)

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
    @staticmethod
    def _render_item(item):
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

        # Get the options as sorted list of tuples (key, value)
        options = self.options
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

        options = [(s3_unicode(k) if k is not None else none,
                    # Not working with multi-byte str components:
                    #v.flatten()
                    #    if hasattr(v, "flatten") else s3_unicode(v))
                    s3_unicode(s3_strip_markup(v.xml()))
                        if isinstance(v, DIV) else s3_unicode(v))
                   for k, v in options if k not in exclude]

        # No options available?
        if not options:
            return {"empty": current.T("no options available")}

        # Get the current values as list of unicode
        if not isinstance(value, (list, tuple)):
            values = [value]
        else:
            values = value
        values = [s3_unicode(v) for v in values]

        # Get the tooltips as dict {key: tooltip}
        helptext = {}
        help_field = self.help_field
        if help_field:
            if callable(help_field):
                help_field = help_field(options)
            if isinstance(help_field, dict):
                for key in help_field.keys():
                    helptext[s3_unicode(key)] = help_field[key]
            else:
                ktablename, pkey = s3_get_foreign_key(field)[:2]
                if ktablename is not None:
                    ktable = current.s3db[ktablename]
                    if hasattr(ktable, help_field):
                        keys = [k for k, v in options if k.isdigit()]
                        query = ktable[pkey].belongs(keys)
                        rows = current.db(query).select(ktable[pkey],
                                                        ktable[help_field])
                        for row in rows:
                            helptext[s3_unicode(row[pkey])] = row[help_field]

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

        # Sort letters
        if letter_options:
            all_letters = sorted_locale(letter_options.keys())
            first_letter = min(u"A", all_letters[0])
            last_letter = max(u"Z", all_letters[-1])
        else:
            # No point with grouping if we don't have any labels
            all_letters = []
            size = 0

        size = self.size

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
            close_group(group, values, helptext, sort=self.sort)
            groups = [group]

        return {"groups": groups}

    # -------------------------------------------------------------------------
    @staticmethod
    def _close_group(group, values, helptext, sort=True):
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
        if sort:
            group_items = sorted(group["items"],
                                 key = lambda i: i[1].upper()[0] \
                                       if i[1] else None,
                                 )
        else:
            group_items = group["items"]

        # Add tooltips
        items = []
        T = current.T
        for key, label in group_items:
            tooltip = helptext.get(key)
            if tooltip:
                tooltip = s3_str(T(tooltip))
            item = (key, label, key in values, tooltip)
            items.append(item)

        group["items"] = items
        return

#==============================================================================
class S3RadioOptionsWidget(FormWidget):
    """
        Widget with radio buttons for S3OptionsFilter
        - unused: can just use S3GroupedOptionsWidget with multiple=False
    """

    def __init__(self,
                 options=None,
                 cols=None,
                 help_field=None,
                 none=None,
                 sort=True):
        """
            Constructor

            @param options: the options for the SELECT, as list of tuples
                            [(value, label)], or as dict {value: label},
                            or None to auto-detect the options from the
                            Field when called
            @param cols: number of columns for the options table
            @param help_field: field in the referenced table to retrieve
                               a tooltip text from (for foreign keys only)
            @param none: True to render "None" as normal option
            @param sort: sort the options
        """

        self.options = options
        self.cols = cols or 3
        self.help_field = help_field
        self.none = none
        self.sort = sort

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
            widget = DIV(**attr)
            append = widget.append
            render_item = self._render_item
            for option in options:
                item = render_item(fieldname, option)
                append(item)

        return widget

    # -------------------------------------------------------------------------
    @staticmethod
    def _render_item(fieldname, item):
        """
            Helper method to render one option

            @param item: the item as tuple (key, label, value, tooltip),
                         value=True indicates that the item is selected
        """

        key, label, value, tooltip = item
        item_id = "%s%s" % (fieldname, key)
        attr = {"_type": "radio",
                "_name": fieldname,
                "_id": item_id,
                "_class": "s3-radioopts-option",
                "_value": key,
                }
        if value:
            attr["_checked"] = "checked"
        if tooltip:
            attr["_title"] = tooltip
        return DIV(INPUT(**attr),
                   LABEL(label, _for=item_id),
                   )

    # -------------------------------------------------------------------------
    def _options(self, field, value):
        """
            Find and sort the options

            @param field: the Field
            @param value: the currently selected value(s)
        """

        # Get the options as sorted list of tuples (key, value)
        options = self.options
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
            return {"empty": current.T("no options available")}

        # Get the current values as list of unicode
        if not isinstance(value, (list, tuple)):
            values = [value]
        else:
            values = value
        values = [s3_unicode(v) for v in values]

        # Get the tooltips as dict {key: tooltip}
        helptext = {}
        help_field = self.help_field
        if help_field:
            if callable(help_field):
                help_field = help_field(options)
            if isinstance(help_field, dict):
                for k, v in help_field.items():
                    helptext[s3_unicode(k)] = v
            else:
                ktablename, pkey = s3_get_foreign_key(field)[:2]
                if ktablename is not None:
                    ktable = current.s3db[ktablename]
                    if hasattr(ktable, help_field):
                        keys = [k for k, v in options if k.isdigit()]
                        query = ktable[pkey].belongs(keys)
                        rows = current.db(query).select(ktable[pkey],
                                                        ktable[help_field])
                        for row in rows:
                            helptext[s3_unicode(row[pkey])] = row[help_field]

        # Prepare output for _render_item()
        _options = []
        oappend = _options.append
        for k, v in options:
            tooltip = helptext.get(k, None)
            item = (k, v, k in values, tooltip)
            oappend(item)

        if self.sort:
            # Sort options
            _options = sorted(_options, key=lambda i: i[1].upper()[0])

        return _options

# =============================================================================
class S3HiddenWidget(StringWidget):
    """
        Standard String widget, but with a class of hide
        - used by CAP
    """

    def __call__(self, field, value, **attributes):

        default = {"_type": "text",
                   "value": (value is not None and str(value)) or "",
                   }
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
                 group = "",    # Filter to staff/volunteers/deployables
                 ):

        self.post_process = post_process
        self.group = group

    def __call__(self, field, value, **attributes):

        settings = current.deployment_settings

        group = self.group
        if not group and current.request.controller == "deploy":
            group = "deploy"

        default = {"_type": "text",
                   "value": (value is not None and str(value)) or "",
                   }
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

        delay = settings.get_ui_autocomplete_delay()
        min_length = settings.get_ui_autocomplete_min_chars()

        script = '''S3.autocomplete.hrm('%(group)s','%(input)s',"%(postprocess)s"''' % \
            {"group": group,
             "input": real_input,
             "postprocess": self.post_process,
             }
        if delay != 800:
            script = "%s,%s" % (script, delay)
            if min_length != 2:
                script = "%s,%s" % (script, min_length)
        elif min_length != 2:
            script = "%s,,%s" % (script, min_length)
        script = "%s)" % script

        current.response.s3.jquery_ready.append(script)

        return TAG[""](INPUT(_id=dummy_input,
                             _class="string",
                             _value=represent.encode("utf-8")),
                       DIV(_id="%s_throbber" % dummy_input,
                           _class="throbber input_throbber hide"),
                       INPUT(**attr),
                       requires = field.requires
                       )

# =============================================================================
class S3ImageCropWidget(FormWidget):
    """
        Allows the user to crop an image and uploads it.
        Cropping & Scaling (if necessary) done client-side
        - currently using JCrop (https://jcrop.com)
        - @ToDo: Replace with https://blueimp.github.io/jQuery-File-Upload/ ?
        Uses the IS_PROCESSED_IMAGE validator

        @ToDo: Doesn't currently work with Inline Component Forms
    """

    def __init__(self, image_bounds=None):
        """
            @param image_bounds: Limits the Size of the Image that can be
                                 uploaded.
                                 Tuple/List - (MaxWidth, MaxHeight)
        """
        self.image_bounds = image_bounds

    def __call__(self, field, value, download_url=None, **attributes):
        """
            @param field: Field using this widget
            @param value: value if any
            @param download_url: Download URL for saved Image
        """

        T = current.T

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
        else:
            script = "%s/S3/s3.imagecrop.widget.min.js" % script_dir
            if script not in scripts:
                scripts.append(script)

        s3.js_global.append('''
i18n.invalid_image='%s'
i18n.supported_image_formats='%s'
i18n.upload_new_image='%s'
i18n.upload_image='%s' ''' % (T("Please select a valid image!"),
                              T("Supported formats"),
                              T("Upload different Image"),
                              T("Upload Image")))

        stylesheets = s3.stylesheets
        sheet = "plugins/jquery.Jcrop.css"
        if sheet not in stylesheets:
            stylesheets.append(sheet)

        attr = self._attributes(field, {"_type": "file",
                                        "_class": "imagecrop-upload"
                                        }, **attributes)

        elements = [INPUT(_type="hidden", _name="imagecrop-points")]
        append = elements.append

        append(DIV(_class="tooltip",
                   _title="%s|%s" % \
                 (T("Crop Image"),
                 T("Select an image to upload. You can crop this later by opening this record."))))

        # Set up the canvas
        # Canvas is used to scale and crop the Image on the client side
        canvas = TAG["canvas"](_class="imagecrop-canvas",
                               _style="display:none",
                               )
        image_bounds = self.image_bounds

        if image_bounds:
            canvas.attributes["_width"] = image_bounds[0]
            canvas.attributes["_height"] = image_bounds[1]
        else:
            # Images are not scaled and are uploaded as it is
            canvas.attributes["_width"] = 0

        append(canvas)

        btn_class = "imagecrop-btn button"
        if current.deployment_settings.ui.formstyle == "bootstrap":
            btn_class = "imagecrop-btn"

        buttons = [ A(T("Enable Crop"),
                      _id="select-crop-btn",
                      _class=btn_class,
                      _role="button"),
                    A(T("Crop Image"),
                      _id="crop-btn",
                      _class=btn_class,
                      _role="button"),
                    A(T("Cancel"),
                      _id="remove-btn",
                      _class="imagecrop-btn")
                    ]

        parts = [LEGEND(T("Uploaded Image"))] + buttons + \
                [HR(_style="display:none"),
                 IMG(_id="uploaded-image",
                     _style="display:none")
                 ]

        display_div = FIELDSET(parts,
                               _class="image-container")

        crop_data_attr = {"_type": "hidden",
                          "_name": "imagecrop-data",
                          "_class": "imagecrop-data"
                          }

        if value and download_url:
            if callable(download_url):
                download_url = download_url()

            url = "%s/%s" % (download_url, value)
            # Add Image
            crop_data_attr["_value"] = url
            append(FIELDSET(LEGEND(A(T("Upload different Image")),
                                   _id="upload-title"),
                            DIV(INPUT(**attr),
                                DIV(T("or Drop here"),
                                    _class="imagecrop-drag"),
                                _id="upload-container",
                                _style="display:none")))
        else:
            append(FIELDSET(LEGEND(T("Upload Image"),
                                   _id="upload-title"),
                            DIV(INPUT(**attr),
                                DIV(T("or Drop here"),
                                    _class="imagecrop-drag"),
                                _id="upload-container")))

        append(INPUT(**crop_data_attr))
        append(display_div)
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

        if not value:
            value = "[]"
        if not isinstance(value, str):
            try:
                value = json.dumps(value, separators=SEPARATORS)
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

    def __init__(self, type, switch=False, disabled=False):
        self.type = type
        self.disabled = disabled
        self.switch = switch

    def widget(self, field, value, **attributes):

        T = current.T
        s3 = current.response.s3
        switch = self.switch

        if field:
            # LocationLatLonWidget
            id = name = "%s_%s" % (str(field).replace(".", "_"), self.type)
        else:
            # LocationSelectorWidget[2]
            id = name = "gis_location_%s" % self.type
        attr = {"value": value,
                "_class": "decimal %s" % self._class,
                "_id": id,
                "_name": name,
                }

        attr_dms = {}

        if self.disabled:
            attr["_disabled"] = "disabled"
            attr_dms["_disabled"] = "disabled"

        dms_boxes = SPAN(INPUT(_class="degrees", **attr_dms), "° ",
                         INPUT(_class="minutes", **attr_dms), "' ",
                         INPUT(_class="seconds", **attr_dms), "\" ",
                         ["",
                          DIV(A(T("Use decimal"),
                                _class="action-btn gis_coord_switch_decimal"))
                          ][switch],
                         _style="display:none",
                         _class="gis_coord_dms",
                         )

        decimal = SPAN(INPUT(**attr),
                       ["",
                        DIV(A(T("Use deg, min, sec"),
                              _class="action-btn gis_coord_switch_dms"))
                        ][switch],
                       _class="gis_coord_decimal",
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

            if s3.debug:
                script = "/%s/static/scripts/S3/s3.gis.latlon.js" % \
                            current.request.application
            else:
                script = "/%s/static/scripts/S3/s3.gis.latlon.min.js" % \
                            current.request.application
            s3.scripts.append(script)
            s3.lat_lon_i18n_appended = True

        return SPAN(decimal,
                    dms_boxes,
                    _class="gis_coord_wrap",
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
                 level = "",
                 post_process = "",
                 ):

        self.level = level
        self.post_process = post_process

    def __call__(self, field, value, **attributes):

        settings = current.deployment_settings

        level = self.level
        if isinstance(level, list):
            levels = ""
            counter = 0
            for _level in level:
                levels += _level
                if counter < len(level):
                    levels += "|"
                counter += 1

        default = {"_type": "text",
                   "value": (value is not None and s3_unicode(value)) or "",
                   }
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

        delay = settings.get_ui_autocomplete_delay()
        min_length = settings.get_ui_autocomplete_min_chars()

        # Mandatory part
        script = '''S3.autocomplete.location("%s"''' % real_input
        # Optional parts
        if self.post_process:
            # We need all
            script = '''%s,'%s',%s,%s,"%s"''' % (script, level, min_length, delay, self.post_process)
        elif delay != 800:
            script = '''%s,"%s",%s,%s''' % (script, level, min_length, delay)
        elif min_length != 2:
            script = '''%s,"%s",%s''' % (script, level, min_length)
        elif level:
            script = '''%s,"%s"''' % (script, level)
        # Close
        script = "%s)" % script
        current.response.s3.jquery_ready.append(script)
        return TAG[""](INPUT(_id=dummy_input,
                             _class="string",
                             value=represent),
                       DIV(_id="%s_throbber" % dummy_input,
                           _class="throbber input_throbber hide"),
                       INPUT(**attr),
                       requires = field.requires
                       )

# =============================================================================
class S3LocationDropdownWidget(FormWidget):
    """
        Renders a dropdown for an Lx level of location hierarchy
    """

    def __init__(self, level="L0", default=None, validate=False, empty=DEFAULT, blank=False):
        """
            Constructor

            @param level: the Lx-level (as string)
            @param default: the default location name
            @param validate: validate input in-widget (special purpose)
            @param empty: allow selection to be empty
            @param blank: start without options (e.g. when options are
                          Ajax-added later by filterOptionsS3)
        """

        self.level = level
        self.default = default
        self.validate = validate
        self.empty = empty
        self.blank = blank

    def __call__(self, field, value, **attributes):

        level = self.level
        default = self.default
        empty = self.empty

        opts = []
        # Get locations
        s3db = current.s3db
        table = s3db.gis_location
        if self.blank:
            query = (table.id == value)
        elif level:
            query = (table.deleted != True) & \
                    (table.level == level)
        else:
            # Workaround for merge form
            query = (table.id == value)
        locations = current.db(query).select(table.name,
                                             table.id,
                                             cache=s3db.cache)

        # Build OPTIONs
        for location in locations:
            opts.append(OPTION(location.name, _value=location.id))
            if not value and default and location.name == default:
                value = location.id

        # Widget attributes
        attr = dict(attributes)
        attr["_type"] = "int"
        attr["value"] = value
        attr = OptionsWidget._attributes(field, attr)

        if self.validate:
            # Validate widget input to enforce Lx subset
            # - not normally needed (Field validation should suffice)
            requires = IS_IN_SET(locations.as_dict())
            if empty is DEFAULT:
                # Introspect the field
                empty = isinstance(field.requires, IS_EMPTY_OR)
            if empty:
                requires = IS_EMPTY_OR(requires)

            # Skip in-widget validation on POST if inline
            widget_id = attr.get("_id")
            if widget_id and widget_id[:4] == "sub_":
                from .s3forms import SKIP_POST_VALIDATION
                requires = SKIP_POST_VALIDATION(requires)

            widget = TAG[""](SELECT(*opts, **attr), requires = requires)
        else:
            widget = SELECT(*opts, **attr)

        return widget

# =============================================================================
class S3LocationLatLonWidget(FormWidget):
    """
        Renders a Lat & Lon input for a Location
    """

    def __init__(self, empty=False):
        """ Set Defaults """
        self.empty = empty

    def __call__(self, field, value, **attributes):

        T = current.T
        empty = self.empty
        requires = IS_LAT_LON(field)
        if empty:
            requires = IS_EMPTY_OR(requires)

        defaults = {"_type": "text",
                    "value": (value is not None and str(value)) or "",
                    }
        attr = StringWidget._attributes(field, defaults, **attributes)
        # Hide the real field
        attr["_class"] = "hide"

        if value:
            db = current.db
            table = db.gis_location
            record = db(table.id == value).select(table.lat,
                                                  table.lon,
                                                  limitby=(0, 1)
                                                  ).first()
            try:
                lat = record.lat
                lon = record.lon
            except AttributeError:
                lat = None
                lon = None
        else:
            lat = None
            lon = None

        rows = TAG[""]()

        formstyle = current.response.s3.crud.formstyle

        comment = ""
        selector = str(field).replace(".", "_")
        row_id = "%s_lat" % selector
        label = T("Latitude")
        widget = S3LatLonWidget("lat").widget(field, lat)
        label = "%s:" % label
        if not empty:
            label = DIV(label,
                        SPAN(" *", _class="req"))

        row = formstyle(row_id, label, widget, comment)
        if isinstance(row, tuple):
            for r in row:
                rows.append(r)
        else:
            rows.append(row)

        row_id = "%s_lon" % selector
        label = T("Longitude")
        widget = S3LatLonWidget("lon", switch=True).widget(field, lon)
        label = "%s:" % label
        if not empty:
            label = DIV(label,
                        SPAN(" *", _class="req"))
        row = formstyle(row_id, label, widget, comment)
        if isinstance(row, tuple):
            for r in row:
                rows.append(r)
        else:
            rows.append(row)

        return TAG[""](INPUT(**attr),
                       *rows,
                       requires = requires
                       )

# =============================================================================
class S3Selector(FormWidget):
    """
        Base class for JSON-based complex selectors (e.g. S3LocationSelector),
        used to detect this widget class during form processing, and to apply
        a common API.

        Subclasses must implement:
            - __call__().........widget renderer
            - extract()..........extract the values dict from the database
            - represent()........representation method for new/updated value
                                 dicts (before DB commit)
            - validate().........validator for the JSON input
            - postprocess()......post-process to create/update records

        Subclasses should use:
            - inputfield()......to generate the hidden input field
            - parse()...........to parse the JSON from the hidden input field
    """

    def __call__(self, field, value, **attributes):
        """
            Widget renderer.

            To be implemented in subclass.

            @param field: the Field
            @param value: the current value(s)
            @param attr: additional HTML attributes for the widget

            @return: the widget HTML
        """

        values = self.parse(value)

        return self.inputfield(field, values, "s3-selector", **attributes)

    # -------------------------------------------------------------------------
    def extract(self, record_id, values=None):
        """
            Extract the record from the database and update values.

            To be implemented in subclass.

            @param record_id: the record ID
            @param values: the values dict

            @return: the (updated) values dict
        """

        if values is None:
            values = {}
        values["id"] = record_id

        return values

    # -------------------------------------------------------------------------
    def represent(self, value):
        """
            Representation method for new or updated value dicts.

            IMPORTANT: This method *must not* change DB status because it
                       is called from inline forms before the the row is
                       committed to the DB, so any DB status change would
                       be invalid at this point.

            To be implemented in subclass.

            @param values: the values dict

            @return: string representation for the values dict
        """

        return s3_unicode(value)

    # -------------------------------------------------------------------------
    def validate(self, value, requires=None):
        """
            Parse and validate the input value, but don't create or update
            any records. This will be called by S3CRUD.validate to validate
            inline-form values.

            To be implemented in subclass.

            @param value: the value from the form
            @param requires: the field validator
            @returns: tuple (values, error) with values being the parsed
                      value dict, and error any validation errors
        """

        values = self.parse(value)

        return values, None

    # -------------------------------------------------------------------------
    def postprocess(self, value):
        """
            Post-process to create or update records. Called during POST
            before validation of the outer form.

            To be implemented in subclass.

            @param value: the value from the form (as JSON)
            @return: tuple (record_id, error)
        """

        # Convert value into dict and validate
        values, error = self.validate(value)
        if values:
            record_id = values.get("id")
        else:
            record_id = None

        # Return on validation error
        if error:
            # Make sure to return None to not override the field values
            return None, error

        # Post-process goes here (no post-process in base class)

        # Make sure to return the record ID, no the values dict
        return record_id, None

    # -------------------------------------------------------------------------
    def inputfield(self, field, values, classes, **attributes):
        """
            Generate the (hidden) input field. Should be used in __call__.

            @param field: the Field
            @param values: the parsed value (as dict)
            @param classes: standard HTML classes
            @param attributes: the widget attributes as passed in to the widget

            @return: the INPUT field
        """

        if isinstance(classes, (tuple, list)):
            _class = " ".join(classes)
        else:
            _class = classes

        requires = self.postprocess

        fieldname = str(field).replace(".", "_")
        if fieldname.startswith("sub_"):
            from .s3forms import SKIP_POST_VALIDATION
            requires = SKIP_POST_VALIDATION(requires)

        defaults = {"requires": requires,
                    "_type": "hidden",
                    "_class": _class,
                    }
        attr = FormWidget._attributes(field, defaults, **attributes)

        return INPUT(_value = self.serialize(values), **attr)

    # -------------------------------------------------------------------------
    def serialize(self, values):
        """
            Serialize the values (as JSON string). Called from inputfield().

            @param values: the values (as dict)
            @return: the serialized values
        """

        return json.dumps(values, separators=SEPARATORS)

    # -------------------------------------------------------------------------
    def parse(self, value):
        """
            Parse the form value into a dict. The value would be a record
            id if coming from the database, or a JSON string when coming
            from a form. Should be called from validate(), doesn't need to
            be re-implemented in subclass.

            @param value: the value
            @return: the parsed data as dict
        """

        record_id = None
        values = None

        if value:
            if isinstance(value, basestring):
                if value.isdigit():
                    record_id = long(value)
                else:
                    try:
                        values = json.loads(value)
                    except ValueError:
                        pass
            else:
                record_id = value
        else:
            record_id = None

        if values is None:
            values = {"id": record_id}

        return values

# =============================================================================
class S3LocationSelector(S3Selector):
    """
        Form widget to select a location_id that can also
        create/update the location

        Differences to the original S3LocationSelectorWidget:
        * Allows selection of either an Lx or creation of a new Point
          within the lowest Lx level
        * Uses dropdowns not autocompletes
        * Selection of lower Lx levels only happens when higher-level
          have been done

        Implementation Notes:
        * Performance: Create JSON for the hierarchy, along with bboxes for
                       the map zoom - loaded progressively rather than all as
                       one big download
        h = {id : {'n' : name,
                   'l' : level,
                   'f' : parent
                   }}

        Limitations (@todo):
        * Doesn't allow creation of new Lx Locations
        * Doesn't support manual entry of LatLons
        * Doesn't allow selection of existing specific Locations
        * Doesn't support variable Levels by Country
        * Use in an InlineComponent with multiple=False needs completing:
            - Validation errors cause issues
            - Needs more testing
        * Should support use in an InlineComponent with multiple=True
        * Should support multiple on a page
    """

    keys = ("L0", "L1", "L2", "L3", "L4", "L5",
            "address", "postcode", "lat", "lon", "wkt", "specific", "id", "radius")

    def __init__(self,
                 levels = None,
                 required_levels = None,
                 hide_lx = True,
                 reverse_lx = False,
                 show_address = False,
                 show_postcode = None,
                 show_latlon = None,
                 latlon_mode = "decimal",
                 latlon_mode_toggle = True,
                 show_map = None,
                 open_map_on_load = False,
                 feature_required = False,
                 lines = False,
                 points = True,
                 polygons = False,
                 circles = False,
                 color_picker = False,
                 catalog_layers = False,
                 min_bbox = None,
                 labels = True,
                 placeholders = False,
                 error_message = None,
                 represent = None,
                 prevent_duplicate_addresses = False,
                 outside = None,
                 ):
        """
            Constructor

            @param levels: list or tuple of hierarchy levels (names) to expose,
                           in order (e.g. ("L0", "L1", "L2"))
                           or False to disable completely
            @param required_levels: list or tuple of required hierarchy levels (if empty,
                                    only the highest selectable Lx will be required)
            @param hide_lx: hide Lx selectors until higher level has been selected
            @param reverse_lx: render Lx selectors in the order usually used by
                               street Addresses (lowest level first), and below the
                               address line
            @param show_address: show a field for street address.
                                 If the parameter is set to a string then this is used as the label.
            @param show_postcode: show a field for postcode
            @param show_latlon: show fields for manual Lat/Lon input
            @param latlon_mode: (initial) lat/lon input mode ("decimal" or "dms")
            @param latlon_mode_toggle: allow user to toggle lat/lon input mode
            @param show_map: show a map to select specific points
            @param open_map_on_load: show map on load
            @param feature_required: map feature is required
            @param lines: use a line draw tool
            @param points: use a point draw tool
            @param polygons: use a polygon draw tool
            @param circles: use a circle draw tool
            @param color_picker: display a color-picker to set per-feature styling
                                 (also need to enable in the feature layer to show on map)
            @param catalog_layers: display catalogue layers or just the default base layer
            @param min_bbox: minimum BBOX in map selector, used to determine automatic
                             zoom level for single-point locations
            @param labels: show labels on inputs
            @param placeholders: show placeholder text in inputs
            @param error_message: default error message for server-side validation
            @param represent: an S3Represent instance that can represent non-DB rows
            @param prevent_duplicate_addresses: do a check for duplicate addresses & prevent
                                                creation of record if a dupe is found
        """

        settings = current.deployment_settings

        self._initlx = True
        self._levels = levels
        self._required_levels = required_levels
        self._load_levels = None

        self.hide_lx = hide_lx
        self.reverse_lx = reverse_lx
        self.show_address = show_address
        self.show_postcode = show_postcode
        self.prevent_duplicate_addresses = prevent_duplicate_addresses

        if show_latlon is None:
            show_latlon = settings.get_gis_latlon_selector()
        self.show_latlon = show_latlon
        self.latlon_mode = latlon_mode
        if show_latlon:
            # @todo: latlon_toggle_mode should default to a deployment setting
            self.latlon_mode_toggle = latlon_mode_toggle
        else:
            self.latlon_mode_toggle = False

        if feature_required:
            show_map = True
            if not any((points, lines, polygons, circles)):
                points = True
            if lines or polygons or circles:
                required = "wkt" if not points else "any"
            else:
                required = "latlon"
            self.feature_required = required
        else:
            self.feature_required = None
        if show_map is None:
            show_map = settings.get_gis_map_selector()
        self.show_map = show_map
        self.open_map_on_load = show_map and open_map_on_load

        self.lines = lines
        self.points = points
        self.polygons = polygons
        self.circles = circles

        self.color_picker = color_picker
        self.catalog_layers = catalog_layers

        self.min_bbox = min_bbox or settings.get_gis_bbox_min_size()

        self.labels = labels
        self.placeholders = placeholders

        self.error_message = error_message
        self._represent = represent

    # -------------------------------------------------------------------------
    @property
    def levels(self):
        """ Lx-levels to expose as dropdowns """

        levels = self._levels
        if self._initlx:
            lx = []
            if levels is False:
                levels = []
            elif not levels:
                # Which levels of Hierarchy are we using?
                levels = current.gis.get_relevant_hierarchy_levels()
                if levels is None:
                    levels = []
            if not isinstance(levels, (tuple, list)):
                levels = [levels]
            for level in levels:
                if level not in lx:
                    lx.append(level)
            for level in self.required_levels:
                if level not in lx:
                    lx.append(level)
            levels = self._levels = lx
            self._initlx = False
        return levels

    # -------------------------------------------------------------------------
    @property
    def required_levels(self):
        """ Lx-levels to treat as required """

        levels = self._required_levels
        if self._initlx:
            if levels is None:
                levels = set()
            elif not isinstance(levels, (list, tuple)):
                levels = [levels]
            self._required_levels = levels
        return levels

    # -------------------------------------------------------------------------
    @property
    def load_levels(self):
        """
            Lx-levels to load from the database = all levels down to the
            lowest exposed level (L0=highest, L5=lowest)
        """

        load_levels = self._load_levels

        if load_levels is None:
            load_levels = ("L0", "L1", "L2", "L3", "L4", "L5")
            while load_levels:
                if load_levels[-1] in self.levels:
                    break
                else:
                    load_levels = load_levels[:-1]
            self._load_levels = load_levels

        return load_levels

    # -------------------------------------------------------------------------
    @property
    def mobile(self):
        """
            Mobile widget settings

            @ToDo: Expose configuration options
        """

        widget = {"type": "location",
                  }

        return widget

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):
        """
            Widget renderer

            @param field: the Field
            @param value: the current value(s)
            @param attr: additional HTML attributes for the widget
        """

        # Environment
        T = current.T
        db = current.db

        s3db = current.s3db

        request = current.request
        s3 = current.response.s3

        # Is the location input required?
        requires = field.requires
        if requires:
            required = not hasattr(requires, "other")
        else:
            required = False

        # Don't use this widget/validator in appadmin
        if request.controller == "appadmin":
            attr = FormWidget._attributes(field, {}, **attributes)
            if required:
                requires = IS_LOCATION()
            else:
                requires = IS_EMPTY_OR(IS_LOCATION())
            return TAG[""](INPUT(**attr), requires=requires)

        # Settings
        settings = current.deployment_settings
        countries = settings.get_gis_countries()

        # Read the currently active GIS config
        gis = current.gis
        config = gis.get_config()

        # Parse the current value
        values = self.parse(value)
        location_id = values.get("id")

        # Determine the default location and bounds
        gtable = s3db.gis_location

        default = field.default
        default_bounds = None

        if not default:
            # Check for a default location in the active gis_config
            default = config.default_location_id

        if not default:
            # Fall back to default country (if only one)
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
                                           cache=s3db.cache,
                                           limitby=(0, 1)).first()
                try:
                    default = country.id
                    default_bounds = [country.lon_min,
                                      country.lat_min,
                                      country.lon_max,
                                      country.lat_max,
                                      ]
                except AttributeError:
                    error = "Default country data not in database (incorrect prepop setting?)"
                    current.log.critical(error)
                    if s3.debug:
                        raise RuntimeError(error)

        if not location_id and list(values.keys()) == ["id"]:
            location_id = values["id"] = default

        # Update the values dict from the database
        values = self.extract(location_id, values=values)

        # The lowest level we have a value for, but no selector exposed
        levels = self.levels
        load_levels = self.load_levels
        lowest_lx = None
        for level in load_levels[::-1]:
            if level not in levels and values.get(level):
                lowest_lx = level
                break

        # Field name for ID construction
        fieldname = attributes.get("_name")
        if not fieldname:
            fieldname = str(field).replace(".", "_")

        # Load initial Hierarchy Labels (for Lx dropdowns)
        labels, labels_compact = self._labels(levels,
                                              country=values.get("L0"),
                                              )

        # Load initial Hierarchy Locations (to populate Lx dropdowns)
        location_dict = self._locations(levels,
                                        values,
                                        default_bounds = default_bounds,
                                        lowest_lx = lowest_lx,
                                        config = config,
                                        )

        # Render visual components
        components = {}
        manual_input = self._input

        # Street Address INPUT
        show_address = self.show_address
        if show_address:
            address = values.get("address")
            if show_address is True:
                label = gtable.addr_street.label
            else:
                label = show_address
            components["address"] = manual_input(fieldname,
                                                 "address",
                                                 address,
                                                 label,
                                                 hidden = not address,
                                                 )

        # Postcode INPUT
        show_postcode = self.show_postcode
        if show_postcode is None:
            # Use global setting
            show_postcode = settings.get_gis_postcode_selector()
        if show_postcode:
            postcode = values.get("postcode")
            components["postcode"] = manual_input(fieldname,
                                                  "postcode",
                                                  postcode,
                                                  settings.get_ui_label_postcode(),
                                                  hidden = not postcode,
                                                  )

        # Lat/Lon INPUTs
        lat = values.get("lat")
        lon = values.get("lon")
        if self.show_latlon:
            hidden = not lat and not lon
            components["lat"] = manual_input(fieldname,
                                             "lat",
                                             lat,
                                             T("Latitude"),
                                             hidden = hidden,
                                             _class = "double",
                                             )
            components["lon"] = manual_input(fieldname,
                                             "lon",
                                             lon,
                                             T("Longitude"),
                                             hidden = hidden,
                                             _class = "double",
                                             )

        # Lx Dropdowns
        multiselect = settings.get_ui_multiselect_widget()
        lx_rows = self._lx_selectors(field,
                                     fieldname,
                                     levels,
                                     labels,
                                     multiselect=multiselect,
                                     required=required,
                                     )
        components.update(lx_rows)

        # Lat/Lon Input Mode Toggle
        if self.latlon_mode_toggle:
            latlon_labels = {"decimal": T("Use decimal"),
                             "dms": T("Use deg, min, sec"),
                             }
            if self.latlon_mode == "dms":
                latlon_label = latlon_labels["decimal"]
            else:
                latlon_label = latlon_labels["dms"]
            toggle_id = fieldname + "_latlon_toggle"
            components["latlon_toggle"] = ("",
                                           A(latlon_label,
                                             _id=toggle_id,
                                             _class="action-lnk",
                                             ),
                                           toggle_id,
                                           False,
                                           )
        else:
            latlon_labels = None

        # Already loaded? (to prevent duplicate JS injection)
        location_selector_loaded = s3.gis.location_selector_loaded

        # Action labels i18n
        if not location_selector_loaded:
            global_append = s3.js_global.append
            global_append('''i18n.select="%s"''' % T("Select"))
            if multiselect == "search":
                global_append('''i18n.search="%s"''' % T("Search"))
            if latlon_labels:
                global_append('''i18n.latlon_mode='''
                              '''{decimal:"%(decimal)s",dms:"%(dms)s"}''' %
                              latlon_labels)
                global_append('''i18n.latlon_error='''
                              '''{lat:"%s",lon:"%s",min:"%s",sec:"%s",format:"%s"}''' %
                              (T("Latitude must be -90..90"),
                               T("Longitude must be -180..180"),
                               T("Minutes must be 0..59"),
                               T("Seconds must be 0..59"),
                               T("Unrecognized format"),
                               ))

        # If we need to show the map since we have an existing lat/lon/wkt
        # then we need to launch the client-side JS as a callback to the
        # MapJS loader
        wkt = values.get("wkt")
        radius = values.get("radius")
        if lat is not None or lon is not None or wkt is not None:
            use_callback = True
        else:
            use_callback = False

        # Widget JS options
        options = {"hideLx": self.hide_lx,
                   "reverseLx": self.reverse_lx,
                   "locations": location_dict,
                   "labels": labels_compact,
                   "showLabels": self.labels,
                   "featureRequired": self.feature_required,
                   "latlonMode": self.latlon_mode,
                   "latlonModeToggle": self.latlon_mode_toggle,
                   }
        if self.min_bbox:
            options["minBBOX"] = self.min_bbox
        if self.open_map_on_load:
            options["openMapOnLoad"] = True
        script = '''$('#%s').locationselector(%s)''' % \
                 (fieldname, json.dumps(options, separators=SEPARATORS))

        show_map = self.show_map
        callback = None
        if show_map and use_callback:
            callback = script
        elif not location_selector_loaded or \
             not location_selector_loaded.get(fieldname):
            s3.jquery_ready.append(script)

        # Inject LocationSelector JS
        if s3.debug:
            script = "s3.ui.locationselector.js"
        else:
            script = "s3.ui.locationselector.min.js"
        script = "/%s/static/scripts/S3/%s" % (request.application, script)

        scripts = s3.scripts
        if script not in scripts:
            scripts.append(script)

        # Should we use the Geocoder?
        geocoder = config.geocoder and show_address

        # Inject map
        if show_map:
            map_icon = self._map(field,
                                 fieldname,
                                 lat,
                                 lon,
                                 wkt,
                                 radius,
                                 callback = callback,
                                 geocoder = geocoder,
                                 tablename = field.tablename,
                                 )
        else:
            map_icon = None

        # LocationSelector is now loaded! (=prevent duplicate JS injection)
        if location_selector_loaded:
            location_selector_loaded[fieldname] = True
        else:
            s3.gis.location_selector_loaded = {fieldname: True}

        # Real input
        classes = ["location-selector"]
        if fieldname.startswith("sub_"):
            is_inline = True
            classes.append("inline-locationselector-widget")
        else:
            is_inline = False
        real_input = self.inputfield(field, values, classes, **attributes)

        # The overall layout of the components
        visible_components = self._layout(components,
                                          map_icon=map_icon,
                                          inline=is_inline,
                                          )

        return TAG[""](DIV(_class="throbber"),
                       real_input,
                       visible_components,
                       )

    # -------------------------------------------------------------------------
    @staticmethod
    def _labels(levels, country=None):
        """
            Extract the hierarchy labels

            @param levels: the exposed hierarchy levels
            @param country: the country (gis_location record ID) for which
                            to read the hierarchy labels

            @return: tuple (labels, compact) where labels is for
                     internal use with _lx_selectors, and compact
                     the version ready for JSON output

            @ToDo: Country-specific Translations of Labels
        """

        T = current.T
        table = current.s3db.gis_hierarchy

        fields = [table[level] for level in levels if level != "L0"]

        query = (table.uuid == "SITE_DEFAULT")
        if country:
            # Read both country-specific and default
            fields.append(table.uuid)
            query |= (table.location_id == country)
            limit = 2
        else:
            # Default only
            limit = 1

        rows = current.db(query).select(*fields, limitby=(0, limit))

        labels = {}
        compact = {}

        if "L0" in levels:
            labels["L0"] = current.messages.COUNTRY

        if country:
            for row in rows:
                if row.uuid == "SITE_DEFAULT":
                    d = compact["d"] = {}
                    for level in levels:
                        if level == "L0":
                            continue
                        d[int(level[1:])] = row[level]
                else:
                    d = compact[country] = {}
                    for level in levels:
                        if level == "L0":
                            continue
                        label = row[level]
                        label = s3_str(T(label)) if label else level
                        labels[level] = d[int(level[1:])] = label
        else:
            row = rows.first()
            d = compact["d"] = {}
            for level in levels:
                if level == "L0":
                    continue
                d[int(level[1:])] = s3_str(T(row[level]))

        return labels, compact

    # -------------------------------------------------------------------------
    @staticmethod
    def _locations(levels,
                   values,
                   default_bounds = None,
                   lowest_lx = None,
                   config = None,
                   ):
        """
            Build initial location dict (to populate Lx dropdowns)

            @param levels: the exposed levels
            @param values: the current values
            @param default_bounds: the default bounds (if already known, e.g.
                                   single-country deployment)
            @param lowest_lx: the lowest un-selectable Lx level (to determine
                              default bounds if not passed in)
            @param config: the current GIS config

            @return: dict of location data, ready for JSON output

            @ToDo: DRY with controllers/gis.py ldata()
        """

        db = current.db
        s3db = current.s3db
        settings = current.deployment_settings

        L0 = values.get("L0")
        L1 = values.get("L1")
        L2 = values.get("L2")
        L3 = values.get("L3")
        L4 = values.get("L4")
        #L5 = values.get("L5")

        # Read all visible levels
        # NB (level != None) is to handle Missing Levels
        gtable = s3db.gis_location

        # @todo: DRY this:
        if "L0" in levels:
            query = (gtable.level == "L0")
            countries = settings.get_gis_countries()
            if len(countries):
                ttable = s3db.gis_location_tag
                query &= ((ttable.tag == "ISO2") & \
                          (ttable.value.belongs(countries)) & \
                          (ttable.location_id == gtable.id))
            if L0 and "L1" in levels:
                query |= (gtable.level != None) & \
                         (gtable.parent == L0)
            if L1 and "L2" in levels:
                query |= (gtable.level != None) & \
                         (gtable.parent == L1)
            if L2 and "L3" in levels:
                query |= (gtable.level != None) & \
                         (gtable.parent == L2)
            if L3 and "L4" in levels:
                query |= (gtable.level != None) & \
                         (gtable.parent == L3)
            if L4 and "L5" in levels:
                query |= (gtable.level != None) & \
                         (gtable.parent == L4)
        elif L0 and "L1" in levels:
            query = (gtable.level != None) & \
                    (gtable.parent == L0)
            if L1 and "L2" in levels:
                query |= (gtable.level != None) & \
                         (gtable.parent == L1)
            if L2 and "L3" in levels:
                query |= (gtable.level != None) & \
                         (gtable.parent == L2)
            if L3 and "L4" in levels:
                query |= (gtable.level != None) & \
                         (gtable.parent == L3)
            if L4 and "L5" in levels:
                query |= (gtable.level != None) & \
                         (gtable.parent == L4)
        elif L1 and "L2" in levels:
            query = (gtable.level != None) & \
                    (gtable.parent == L1)
            if L2 and "L3" in levels:
                query |= (gtable.level != None) & \
                         (gtable.parent == L2)
            if L3 and "L4" in levels:
                query |= (gtable.level != None) & \
                         (gtable.parent == L3)
            if L4 and "L5" in levels:
                query |= (gtable.level != None) & \
                         (gtable.parent == L4)
        elif L2 and "L3" in levels:
            query = (gtable.level != None) & \
                    (gtable.parent == L2)
            if L3 and "L4" in levels:
                query |= (gtable.level != None) & \
                         (gtable.parent == L3)
            if L4 and "L5" in levels:
                query |= (gtable.level != None) & \
                         (gtable.parent == L4)
        elif L3 and "L4" in levels:
            query = (gtable.level != None) & \
                    (gtable.parent == L3)
            if L4 and "L5" in levels:
                query |= (gtable.level != None) & \
                         (gtable.parent == L4)
        elif L4 and "L5" in levels:
            query = (gtable.level != None) & \
                    (gtable.parent == L4)
        else:
            query = None

        # Translate options using gis_location_name?
        language = current.session.s3.language
        if language in ("en", "en-gb"):
            # We assume that Location names default to the English version
            translate = False
        else:
            translate = settings.get_L10n_translate_gis_location()

        if query is None:
            locations = []
            if levels != []:
                # Misconfigured (e.g. no default for a hidden Lx level)
                current.log.warning("S3LocationSelector: no default for hidden Lx level?")
        else:
            query &= (gtable.deleted == False) & \
                     (gtable.end_date == None)
            fields = [gtable.id,
                      gtable.name,
                      gtable.level,
                      gtable.parent,
                      gtable.inherited,
                      gtable.lat_min,
                      gtable.lon_min,
                      gtable.lat_max,
                      gtable.lon_max,
                      ]

            if translate:
                ntable = s3db.gis_location_name
                fields.append(ntable.name_l10n)
                left = ntable.on((ntable.deleted == False) & \
                                 (ntable.language == language) & \
                                 (ntable.location_id == gtable.id))
            else:
                left = None
            locations = db(query).select(*fields, left=left)

        location_dict = {}
        if default_bounds:

            # Only L0s get set before here
            location_dict["d"] = {"id": L0,
                                  "b": default_bounds,
                                  }
            location_dict[L0] = {"b": default_bounds,
                                 "l": 0,
                                 }

        elif lowest_lx:
            # What is the lowest-level un-selectable Lx?
            lx = values.get(lowest_lx)
            record = db(gtable.id == lx).select(gtable.lat_min,
                                                gtable.lon_min,
                                                gtable.lat_max,
                                                gtable.lon_max,
                                                cache=s3db.cache,
                                                limitby=(0, 1)).first()
            try:
                bounds = [record.lon_min,
                          record.lat_min,
                          record.lon_max,
                          record.lat_max
                          ]
            except:
                # Record not found!
                raise ValueError

            location_dict["d"] = {"id": lx,
                                  "b": bounds,
                                  }
            location_dict[lx] = {"b": bounds,
                                 "l": int(lowest_lx[1:]),
                                 }
        else:
            fallback = None
            default_location = config.default_location_id
            if default_location:
                query = (gtable.id == default_location)
                record = db(query).select(gtable.level,
                                          gtable.lat_min,
                                          gtable.lon_min,
                                          gtable.lat_max,
                                          gtable.lon_max,
                                          cache=s3db.cache,
                                          limitby=(0, 1)).first()
                if record and record.level:
                    bounds = [record.lon_min,
                              record.lat_min,
                              record.lon_max,
                              record.lat_max,
                              ]
                    if any(bounds):
                        fallback = {"id": default_location, "b": bounds}
            if fallback is None:
                fallback = {"b": [config.lon_min,
                                  config.lat_min,
                                  config.lon_max,
                                  config.lat_max,
                                  ]
                            }
            location_dict["d"] = fallback

        if translate:
            for location in locations:
                l = location["gis_location"]
                name = location["gis_location_name.name_l10n"] or l.name
                data = {"n": name,
                        "l": int(l.level[1]),
                        }
                if l.parent:
                    data["f"] = int(l.parent)
                if not l.inherited:
                    data["b"] = [l.lon_min,
                                 l.lat_min,
                                 l.lon_max,
                                 l.lat_max,
                                 ]
                location_dict[int(l.id)] = data
        else:
            for l in locations:
                level = l.level
                if level:
                    level = int(level[1])
                else:
                    current.log.warning("S3LocationSelector",
                                        "Location Hierarchy not setup properly")
                    continue
                data = {"n": l.name,
                        "l": level,
                        }
                if l.parent:
                    data["f"] = int(l.parent)
                if not l.inherited:
                    data["b"] = [l.lon_min,
                                 l.lat_min,
                                 l.lon_max,
                                 l.lat_max,
                                 ]
                location_dict[int(l.id)] = data

        return location_dict

    # -------------------------------------------------------------------------
    @staticmethod
    def _layout(components, map_icon=None, formstyle=None, inline=False):
        """
            Overall layout for visible components

            @param components: the components as dict
                               {name: (label, widget, id, hidden)}
            @param map icon: the map icon
            @param formstyle: the formstyle (falls back to CRUD formstyle)
        """

        if formstyle is None:
            formstyle = current.response.s3.crud.formstyle

        # Test the formstyle
        row = formstyle("test", "test", "test", "test")
        if isinstance(row, tuple):
            # Formstyle with separate row for label
            # (e.g. old default Eden formstyle)
            tuple_rows = True
            table_style = inline and row[0].tag == "tr"
        else:
            # Formstyle with just a single row
            # (e.g. Bootstrap, Foundation or DRRPP)
            tuple_rows = False
            table_style = False

        selectors = DIV() if not table_style else TABLE()
        for name in ("L0", "L1", "L2", "L3", "L4", "L5"):
            if name in components:
                label, widget, input_id, hidden = components[name]
                formrow = formstyle("%s__row" % input_id,
                                    label,
                                    widget,
                                    "",
                                    hidden=hidden,
                                    )
                if tuple_rows:
                    selectors.append(formrow[0])
                    selectors.append(formrow[1])
                else:
                    selectors.append(formrow)

        inputs = TAG[""]() if not table_style else TABLE()
        for name in ("address", "postcode", "lat", "lon", "latlon_toggle"):
            if name in components:
                label, widget, input_id, hidden = components[name]
                formrow = formstyle("%s__row" % input_id,
                                    label,
                                    widget,
                                    "",
                                    hidden=hidden,
                                    )
                if tuple_rows:
                    inputs.append(formrow[0])
                    inputs.append(formrow[1])
                else:
                    inputs.append(formrow)

        output = TAG[""](selectors, inputs)
        if map_icon:
            output.append(map_icon)
        return output

    # -------------------------------------------------------------------------
    def _lx_selectors(self,
                      field,
                      fieldname,
                      levels,
                      labels,
                      multiselect=False,
                      required=False):
        """
            Render the Lx-dropdowns

            @param field: the field (to construct the HTML Names)
            @param fieldname: the fieldname (to construct the HTML IDs)
            @param levels: tuple of levels in order, like ("L0", "L1", ...)
            @param labels: the labels for the hierarchy levels as dict {level:label}
            @param multiselect: Use multiselect-dropdowns (specify "search" to
                                make the dropdowns searchable)
            @param required: whether selection is required

            @return: a dict of components
                     {name: (label, widget, id, hidden)}
        """

        # Use multiselect widget?
        if multiselect == "search":
            _class = "lx-select multiselect search"
        elif multiselect:
            _class = "lx-select multiselect"
        else:
            _class = None

        # Initialize output
        selectors = {}

        # 1st level is always hidden until populated
        hidden = True

        _fieldname = fieldname.split("%s_" % field.tablename)[1]

        #T = current.T
        required_levels = self.required_levels
        for level in levels:

            _name = "%s_%s" % (_fieldname, level)

            _id = "%s_%s" % (fieldname, level)

            label = labels.get(level, level)

            # Widget (options to be populated client-side)
            #placeholder = T("Select %(level)s") % {"level": label}
            placeholder = ""
            widget = SELECT(OPTION(placeholder, _value=""),
                            _name = _name,
                            _id = _id,
                            _class = _class,
                            )

            # Mark as required?
            if required or level in required_levels:
                widget.add_class("required")
                label = s3_required_label(label)

                if required and ("L%s" % (int(level[1:]) - 1)) not in levels:
                    # This is the highest level, treat subsequent levels
                    # as optional unless they are explicitly configured
                    # as required
                    required = False

            # Throbber
            throbber = DIV(_id="%s__throbber" % _id,
                           _class="throbber hide",
                           )

            if self.labels:
                label = LABEL(label, _for=_id)
            else:
                label = ""
            selectors[level] = (label, TAG[""](widget, throbber), _id, hidden)

            # Follow hide-setting for all subsequent levels (default: True),
            # client-side JS will open when-needed
            hidden = self.hide_lx

        return selectors

    # -------------------------------------------------------------------------
    def _input(self,
               fieldname,
               name,
               value,
               label,
               hidden=False,
               _class="string"):
        """
            Render a text input (e.g. address or postcode field)

            @param fieldname: the field name (for ID construction)
            @param name: the name for the input field
            @param value: the initial value for the input
            @param label: the label for the input
            @param hidden: render hidden

            @return: a tuple (label, widget, id, hidden)
        """

        input_id = "%s_%s" % (fieldname, name)

        if label and self.labels:
            _label = LABEL("%s:" % label, _for=input_id)
        else:
            _label = ""
        if label and self.placeholders:
            _placeholder = label
        else:
            _placeholder = None
        widget = INPUT(_name = name,
                       _id = input_id,
                       _class = _class,
                       _placeholder = _placeholder,
                       value = s3_str(value),
                       )

        return (_label, widget, input_id, hidden)

    # -------------------------------------------------------------------------
    def _map(self,
             field,
             fieldname,
             lat,
             lon,
             wkt,
             radius,
             callback = None,
             geocoder = False,
             tablename = None):
        """
            Initialize the map

            @param field: the field
            @param fieldname: the field name (to construct HTML IDs)
            @param lat: the Latitude of the current point location
            @param lon: the Longitude of the current point location
            @param wkt: the WKT
            @param radius: the radius of the location
            @param callback: the script to initialize the widget, if to be
                             initialized as callback of the MapJS loader
            @param geocoder: use a geocoder
            @param tablename: tablename to determine the controller/function
                              for custom colorpicker style

            @return: the HTML components for the map (including the map icon row)

            @ToDo: handle multiple LocationSelectors in 1 page
                   (=> multiple callbacks, as well as the need to
                       migrate options from globals to a parameter)
        """

        lines = self.lines
        points = self.points
        polygons = self.polygons
        circles = self.circles

        # Toolbar options
        add_points_active = add_polygon_active = add_line_active = add_circle_active = False
        if points and lines:
            # Allow selection between drawing a point or a line
            toolbar = True
            if wkt:
                if not polygons or wkt.startswith("LINE"):
                    add_line_active = True
                elif polygons:
                    add_polygon_active = True
                else:
                    add_line_active = True
            else:
                add_points_active = True
        elif points and polygons:
            # Allow selection between drawing a point or a polygon
            toolbar = True
            if wkt:
                add_polygon_active = True
            else:
                add_points_active = True
        elif points and circles:
            # Allow selection between drawing a point or a circle
            toolbar = True
            if wkt:
                add_circle_active = True
            else:
                add_points_active = True
        elif points:
            # No toolbar needed => always drawing points
            toolbar = False
            add_points_active = True
        elif lines and polygons:
            # Allow selection between drawing a line or a polygon
            toolbar = True
            if wkt:
                if wkt.startswith("LINE"):
                    add_line_active = True
                else:
                    add_polygon_active = True
            else:
                add_polygon_active = True
        elif lines and circles:
            # Allow selection between drawing a line or a circle
            toolbar = True
            if wkt:
                if wkt.startswith("LINE"):
                    add_line_active = True
                else:
                    add_circle_active = True
            else:
                add_circle_active = True
        elif lines:
            # No toolbar needed => always drawing lines
            toolbar = False
            add_line_active = True
        elif polygons and circles:
            # Allow selection between drawing a polygon or a circle
            toolbar = True
            if wkt:
                if radius is not None:
                    add_circle_active = True
                else:
                    add_polygon_active = True
            else:
                add_polygon_active = True
        elif polygons:
            # No toolbar needed => always drawing polygons
            toolbar = False
            add_polygon_active = True
        elif circles:
            # No toolbar needed => always drawing circles
            toolbar = False
            add_circle_active = True
        else:
            # No Valid options!
            raise SyntaxError

        s3 = current.response.s3

        # ColorPicker options
        color_picker = self.color_picker
        if color_picker:
            toolbar = True
            # Requires the custom controller to store this before calling the widget
            # - a bit hacky, but can't think of a better option currently without
            # rewriting completely as an S3SQLSubForm
            record_id = s3.record_id
            if not record_id:
                # Show Color Picker with default Style
                color_picker = True
            else:
                # Do we have a style defined for this record?
                # @ToDo: Support Layers using alternate controllers/functions
                db = current.db
                s3db = current.s3db
                c, f = field.tablename.split("_", 1)
                ftable = s3db.gis_layer_feature
                query = (ftable.deleted == False) & \
                        (ftable.controller == c) & \
                        (ftable.function == f) & \
                        (ftable.individual == True)
                rows = db(query).select(ftable.layer_id)
                if not rows:
                    # Show Color Picker with default Style
                    color_picker = True
                else:
                    # @ToDo: Handle multiple rows?
                    layer_id = rows.first().layer_id
                    stable = s3db.gis_style
                    query = (stable.deleted == False) & \
                            (stable.layer_id == layer_id) & \
                            (stable.record_id == record_id)
                    rows = db(query).select(stable.style)
                    row = rows.first()
                    if row:
                        color_picker = row.style
                    else:
                        # Show Color Picker with default Style
                        color_picker = True
        else:
            color_picker = False

        settings = current.deployment_settings

        # Create the map
        _map = current.gis.show_map(id = "location_selector_%s" % fieldname,
                                    collapsed = True,
                                    height = settings.get_gis_map_selector_height(),
                                    width = settings.get_gis_map_selector_width(),
                                    add_feature = points,
                                    add_feature_active = add_points_active,
                                    add_line = lines,
                                    add_line_active = add_line_active,
                                    add_polygon = polygons,
                                    add_polygon_active = add_polygon_active,
                                    add_circle = circles,
                                    add_circle_active = add_circle_active,
                                    catalogue_layers = self.catalog_layers,
                                    color_picker = color_picker,
                                    toolbar = toolbar,
                                    # Hide controls from toolbar
                                    clear_layers = False,
                                    nav = False,
                                    print_control = False,
                                    area = False,
                                    zoomWheelEnabled = False,
                                    # Don't use normal callback (since we postpone rendering Map until DIV unhidden)
                                    # but use our one if we need to display a map by default
                                    callback = callback,
                                    )

        # Inject map icon labels
        if polygons or lines:
            show_map_add = settings.get_ui_label_locationselector_map_polygon_add()
            show_map_view = settings.get_ui_label_locationselector_map_polygon_view()
            if wkt is not None:
                label = show_map_view
            else:
                label = show_map_add
        else:
            show_map_add = settings.get_ui_label_locationselector_map_point_add()
            show_map_view = settings.get_ui_label_locationselector_map_point_view()
            if lat is not None or lon is not None:
                label = show_map_view
            else:
                label = show_map_add

        T = current.T
        global_append = s3.js_global.append
        location_selector_loaded = s3.gis.location_selector_loaded

        if not location_selector_loaded:
            global_append('''i18n.show_map_add="%s"
i18n.show_map_view="%s"
i18n.hide_map="%s"
i18n.map_feature_required="%s"''' % (show_map_add,
                                     show_map_view,
                                     T("Hide Map"),
                                     T("Map Input Required"),
                                     ))

        # Generate map icon
        icon_id = "%s_map_icon" % fieldname
        row_id = "%s_map_icon__row" % fieldname
        _formstyle = settings.ui.formstyle
        if not _formstyle or \
           isinstance(_formstyle, basestring) and "foundation" in _formstyle:
            # Default: Foundation
            # Need to add custom classes to core HTML markup
            map_icon = DIV(DIV(BUTTON(ICON("globe"),
                                      SPAN(label),
                                      _type="button", # defaults to 'submit' otherwise!
                                      _id=icon_id,
                                      _class="btn tiny button gis_loc_select_btn",
                                      ),
                               _class="small-12 columns",
                               ),
                           _id = row_id,
                           _class = "form-row row hide",
                           )
        elif _formstyle == "bootstrap":
            # Need to add custom classes to core HTML markup
            map_icon = DIV(DIV(BUTTON(ICON("icon-map"),
                                      SPAN(label),
                                      _type="button", # defaults to 'submit' otherwise!
                                      _id=icon_id,
                                      _class="btn gis_loc_select_btn",
                                      ),
                               _class="controls",
                               ),
                           _id = row_id,
                           _class = "control-group hide",
                           )
        else:
            # Old default
            map_icon = DIV(DIV(BUTTON(ICON("globe"),
                                      SPAN(label),
                                      _type="button", # defaults to 'submit' otherwise!
                                      _id=icon_id,
                                      _class="btn gis_loc_select_btn",
                                      ),
                               _class="w2p_fl",
                               ),
                           _id = row_id,
                           _class = "hide",
                           )

        # Geocoder?
        if geocoder:

            if not location_selector_loaded:
                global_append('''i18n.address_mapped="%s"
i18n.address_not_mapped="%s"
i18n.location_found="%s"
i18n.location_not_found="%s"''' % (T("Address Mapped"),
                                   T("Address NOT Mapped"),
                                   T("Address Found"),
                                   T("Address NOT Found"),
                                   ))

            map_icon.append(DIV(DIV(_class="throbber hide"),
                                DIV(_class="geocode_success hide"),
                                DIV(_class="geocode_fail hide"),
                                BUTTON(T("Geocode"),
                                       _type="button", # defaults to 'submit' otherwise!
                                       _class="hide",
                                       ),
                                _id="%s_geocode" % fieldname,
                                _class="controls geocode",
                                ))

        # Inject map directly behind map icon
        map_icon.append(_map)

        return map_icon

    # -------------------------------------------------------------------------
    def extract(self, record_id, values=None):
        """
            Load record data from database and update the values dict

            @param record_id: the location record ID
            @param values: the values dict
        """

        # Initialize the values dict
        if values is None:
            values = {}
        for key in ("L0", "L1", "L2", "L3", "L4", "L5", "specific", "parent", "radius"):
            if key not in values:
                values[key] = None

        values["id"] = record_id

        if not record_id:
            return values

        db = current.db
        table = current.s3db.gis_location

        levels = self.load_levels

        lat = values.get("lat")
        lon = values.get("lon")
        wkt = values.get("wkt")
        radius = values.get("radius")
        address = values.get("address")
        postcode = values.get("postcode")

        # Load the record
        record = db(table.id == record_id).select(table.id,
                                                  table.path,
                                                  table.parent,
                                                  table.level,
                                                  table.gis_feature_type,
                                                  table.inherited,
                                                  table.lat,
                                                  table.lon,
                                                  table.wkt,
                                                  table.radius,
                                                  table.addr_street,
                                                  table.addr_postcode,
                                                  limitby=(0, 1)).first()
        if not record:
            raise ValueError

        level = record.level

        # Parse the path
        path = record.path
        if path is None:
            # Not updated yet? => do it now
            try:
                path = current.gis.update_location_tree({"id": record_id})
            except ValueError:
                pass
        path = [] if path is None else path.split("/")

        path_ok = True
        if level:
            # Lx location
            values["level"] = level
            values["specific"] = None

            if len(path) != (int(level[1:]) + 1):
                # We don't have a full path
                path_ok = False

        else:
            # Specific location
            values["parent"] = record.parent
            values["specific"] = record.id

            if len(path) < (len(levels) + 1):
                # We don't have a full path
                path_ok = False

            # Only use a specific Lat/Lon when they are not inherited
            if not record.inherited:
                if self.points:
                    if lat is None or lat == "":
                        if record.gis_feature_type == 1:
                            # Only use Lat for Points
                            lat = record.lat
                        else:
                            lat = None
                    if lon is None or lon == "":
                        if record.gis_feature_type == 1:
                            # Only use Lat for Points
                            lon = record.lon
                        else:
                            lon = None
                else:
                    lat = None
                    lon = None
                if self.lines or self.polygons or self.circles:
                    if not wkt:
                        if record.gis_feature_type != 1:
                            # Only use WKT for non-Points
                            wkt = record.wkt
                            if record.radius is not None:
                                radius = record.radius
                        else:
                            wkt = None
                else:
                    wkt = None
            if address is None:
                address = record.addr_street
            if postcode is None:
                postcode = record.addr_postcode

        # Path
        if path_ok:
            for level in levels:
                idx = int(level[1:])
                if len(path) > idx:
                    values[level] = int(path[idx])
        else:
            # Retrieve all records in the path to match them up to their Lx
            rows = db(table.id.belongs(path)).select(table.id, table.level)
            for row in rows:
                if row.level:
                    values[row.level] = row.id

        # Address data
        values["address"] = address
        values["postcode"] = postcode

        # Lat/Lon/WKT/Radius
        values["lat"] = lat
        values["lon"] = lon
        values["wkt"] = wkt
        values["radius"] = radius

        return values

    # -------------------------------------------------------------------------
    def represent(self, value):
        """
            Representation of a new/updated location row (before DB commit).

            NB: Using a fake path here in order to prevent
                gis_LocationRepresent.represent_row() from running
                update_location_tree as that would change DB status which
                is an invalid action at this point (row not committed yet).

            This method is called during S3CRUD.validate for inline components

            @param values: the values dict

            @return: string representation for the values dict
        """

        if not value or not any(value.get(key) for key in self.keys):
            # No data
            return current.messages["NONE"]

        lat = value.get("lat")
        lon = value.get("lon")
        wkt = value.get("wkt")
        #radius = value.get("radius")
        address = value.get("address")
        postcode = value.get("postcode")

        record = Storage(name = value.get("name"),
                         lat = lat,
                         lon = lon,
                         addr_street = address,
                         addr_postcode = postcode,
                         parent = value.get("parent"),
                         )

        # Is this a specific location?
        specific = value.get("specific")
        if specific:
            record_id = specific
        elif address or postcode or lat or lon or wkt:
            specific = True
            record_id = value.get("id")
        else:
            record_id = None
        if not record_id:
            record_id = 0
        record.id = record_id

        lx_ids = {}

        # Construct the path (must have a path to prevent update_location_tree)
        path = [str(record_id)]
        level = None
        append = None
        for l in xrange(5, -1, -1):
            lx = value.get("L%s" % l)
            if lx:
                if not level and not specific and l < 5:
                    level = l
                elif level and not record.parent:
                    record.parent = lx
                lx_ids[l] = lx
                if append is None:
                    append = path.append
            if append:
                append(str(lx))
        path.reverse()
        record.path = "/".join(path)

        # Determine the Lx level
        if specific or level is None:
            record.level = None
        else:
            record.level = "L%s" % level

        # Get the Lx names
        s3db = current.s3db
        ltable = s3db.gis_location

        if lx_ids:
            query = ltable.id.belongs(set(lx_ids.values()))
            limitby = (0, len(lx_ids))
            lx_names = current.db(query).select(ltable.id,
                                                ltable.name,
                                                limitby=limitby).as_dict()
            for l in xrange(0, 6):
                if l in lx_ids:
                    lx_name = lx_names.get(lx_ids[l])["name"]
                else:
                    lx_name = None
                if not lx_name:
                    lx_name = ""
                record["L%s" % l] = lx_name
                if level == l:
                    record["name"] = lx_name

        # Call standard location represent
        represent = self._represent
        if represent is None:
            # Fall back to default
            represent = s3db.gis_location_id().represent

        if hasattr(represent, "alt_represent_row"):
            text = represent.alt_represent_row(record)
        else:
            text = represent(record)

        return s3_str(text)

    # -------------------------------------------------------------------------
    def validate(self, value, requires=None):
        """
            Parse and validate the input value, but don't create or update
            any location data

            @param value: the value from the form
            @param requires: the field validator
            @returns: tuple (values, error) with values being the parsed
                      value dict, and error any validation errors
        """

        values = self.parse(value)

        if not values or not any(values.get(key) for key in self.keys):
            # No data
            if requires and not isinstance(requires, IS_EMPTY_OR):
                return values, current.T("Location data required")
            return values, None

        table = current.s3db.gis_location
        errors = {}
        feature = None
        onvalidation = None

        msg = self.error_message

        # Check for valid Lat/Lon/WKT/Radius (if any)
        lat = values.get("lat")
        if lat:
            try:
                lat = float(lat)
            except ValueError:
                errors["lat"] = current.T("Latitude is Invalid!")
        elif lat == "":
            lat = None

        lon = values.get("lon")
        if lon:
            try:
                lon = float(lon)
            except ValueError:
                errors["lon"] = current.T("Longitude is Invalid!")
        elif lon == "":
            lon = None

        wkt = values.get("wkt")
        if wkt:
            try:
                from shapely.wkt import loads as wkt_loads
                wkt_loads(wkt)
            except:
                errors["wkt"] = current.T("WKT is Invalid!")
        elif wkt == "":
            wkt = None

        radius = values.get("radius")
        if radius:
            try:
                radius = float(radius)
            except ValueError:
                errors["radius"] = current.T("Radius is Invalid!")
        elif radius == "":
            radius = None

        if errors:
            error = "\n".join(s3_str(errors[fn]) for fn in errors)
            return (values, error)

        specific = values.get("specific")
        location_id = values.get("id")

        if specific and location_id and location_id != specific:
            # Reset from a specific location to an Lx
            # Currently not possible
            #   => widget always retains specific
            #   => must take care of orphaned specific locations otherwise
            lat = lon = wkt = radius = None
        else:
            # Read other details
            parent = values.get("parent")
            address = values.get("address")
            postcode = values.get("postcode")

        if parent or address or postcode or \
           wkt is not None or \
           lat is not None or \
           lon is not None or \
           radius is not None:

            # Specific location with details
            if specific:
                values["id"] = specific

                # Would-be update => get original record
                query = (table.id == specific) & \
                        (table.deleted == False) & \
                        (table.level == None) # specific Locations only
                location = current.db(query).select(table.lat,
                                                    table.lon,
                                                    table.wkt,
                                                    table.addr_street,
                                                    table.addr_postcode,
                                                    table.parent,
                                                    limitby=(0, 1)).first()
                if not location:
                    return (values, msg or current.T("Invalid Location!"))

                # Check for changes
                changed = False
                lparent = location.parent
                if parent and lparent:
                    if int(parent) != int(lparent):
                        changed = True
                elif parent or lparent:
                    changed = True
                if not changed:
                    laddress = location.addr_street
                    if (address or laddress) and \
                        address != laddress:
                        changed = True
                    else:
                        lpostcode = location.addr_postcode
                        if (postcode or lpostcode) and \
                            postcode != lpostcode:
                            changed = True
                        else:
                            lwkt = location.wkt
                            if (wkt or lwkt) and \
                               wkt != lwkt:
                                changed = True
                            else:
                                # Float comparisons need care
                                # - just check the 1st 5 decimal points, as
                                #   that's all we care about
                                llat = location.lat
                                if lat is not None and llat is not None:
                                    if round(lat, 5) != round(llat, 5):
                                        changed = True
                                elif lat is not None or llat is not None:
                                    changed = True
                                if not changed:
                                    llon = location.lon
                                    if lon is not None and llon is not None:
                                        if round(lon, 5) != round(llon, 5):
                                            changed = True
                                    elif lon is not None or llon is not None:
                                        changed = True

                if changed:
                    # Update specific location (indicated by id=specific)

                    # Permission to update?
                    if not current.auth.s3_has_permission("update", table,
                                                          record_id=specific):
                        return (values, current.auth.messages.access_denied)

                    # Schedule for onvalidation
                    feature = Storage(addr_street = address,
                                      addr_postcode = postcode,
                                      parent = parent,
                                      )
                    if any(detail is not None for detail in (lat, lon, wkt, radius)):
                        feature.lat = lat
                        feature.lon = lon
                        feature.wkt = wkt
                        feature.radius = radius
                        feature.inherited = False
                    onvalidation = current.s3db.gis_location_onvalidation

                else:
                    # No changes => skip (indicated by specific=0)
                    values["specific"] = 0

            else:
                # Create new specific location (indicate by id=0)
                values["id"] = 0

                # Permission to create?
                if not current.auth.s3_has_permission("create", table):
                    return (values, current.auth.messages.access_denied)

                # Check for duplicate address
                if self.prevent_duplicate_addresses:
                    query = (table.addr_street == address) & \
                            (table.parent == parent) & \
                            (table.deleted != True)
                    duplicate = current.db(query).select(table.id,
                                                         limitby=(0, 1)
                                                         ).first()
                    if duplicate:
                        return (values, current.T("Duplicate Address"))

                # Schedule for onvalidation
                feature = Storage(addr_street = address,
                                  addr_postcode = postcode,
                                  parent = parent,
                                  inherited = True,
                                  )
                if any(detail is not None for detail in (lat, lon, wkt, radius)):
                    feature.lat = lat
                    feature.lon = lon
                    feature.wkt = wkt
                    feature.radius = radius
                    feature.inherited = False
                onvalidation = current.s3db.gis_location_onvalidation

        elif specific:
            # Update specific location (indicated by id=specific)
            values["id"] = specific

            # Permission to update?
            if not current.auth.s3_has_permission("update", table,
                                                  record_id=specific):
                return (values, current.auth.messages.access_denied)

            # Make sure parent/address are properly removed
            values["parent"] = None
            values["address"] = None
            values["postcode"] = None

        else:
            # Lx location => check level
            ## @todo:
            #if not location_id:
                ## Get lowest selected Lx

            if location_id:
                levels = self.levels
                if levels == []:
                    # Widget set to levels=False
                    # No Street Address specified, so skip
                    return (None, None)
                query = (table.id == location_id) & \
                        (table.deleted == False)
                location = current.db(query).select(table.level,
                                                    limitby=(0, 1)).first()
                if not location:
                    return (values, msg or current.T("Invalid Location!"))

                level = location.level
                if level:
                    # Accept all levels above and including the lowest selectable level
                    for i in xrange(5,-1,-1):
                        if "L%s" % i in levels:
                            accepted_levels = set("L%s" % l for l in xrange(i,-1,-1))
                            break
                    if level not in accepted_levels:
                        return (values, msg or \
                                        current.T("Location is of incorrect level!"))
            # Do not update (indicate by specific = None)
            values["specific"] = None

        if feature and onvalidation:

            form = Storage(errors = errors,
                           vars = feature,
                           )
            try:
                # @todo: should use callback()
                onvalidation(form)
            except:
                if current.response.s3.debug:
                    raise
                else:
                    error = "onvalidation failed: %s (%s)" % (
                                onvalidation, sys.exc_info()[1])
                    current.log.error(error)
            if form.errors:
                errors = form.errors
                error = "\n".join(s3_str(errors[fn]) for fn in errors)
                return (values, error)
            elif feature:
                # gis_location_onvalidation adds/updates form vars (e.g.
                # gis_feature_type, the_geom) => must also update values
                values.update(feature)

        # Success
        return (values, None)

    # -------------------------------------------------------------------------
    def postprocess(self, value):
        """
            Takes the JSON from the real input and returns a location ID
            for it. Creates or updates the location if necessary.

            @param value: the JSON from the real input
            @return: tuple (location_id, error)

            @ToDo: Audit
        """

        # Convert and validate
        values, error = self.validate(value)
        if values:
            location_id = values.get("id")
        else:
            location_id = None

        # Return on validation error
        if error:
            # Make sure to return None to not override the field values
            # @todo: consider a custom INPUT subclass without
            #        _postprocessing() to prevent _value override
            #        after successful POST
            return None, error

        # Skip if location_id is None
        if location_id is None:
            return location_id, None

        db = current.db
        table = current.s3db.gis_location

        # Read the values
        lat = values.get("lat")
        lon = values.get("lon")
        lat_min = values.get("lat_min") # Values brought in by onvalidation
        lon_min = values.get("lon_min")
        lat_max = values.get("lat_max")
        lon_max = values.get("lon_max")
        wkt = values.get("wkt")
        radius = values.get("radius")
        the_geom = values.get("the_geom")
        address = values.get("address")
        postcode = values.get("postcode")
        parent = values.get("parent")
        gis_feature_type = values.get("gis_feature_type")

        if location_id == 0:
            # Create new location
            if wkt is not None or (lat is not None and lon is not None):
                inherited = False
            else:
                inherited = True

            feature = Storage(lat = lat,
                              lon = lon,
                              lat_min = lat_min,
                              lon_min = lon_min,
                              lat_max = lat_max,
                              lon_max = lon_max,
                              wkt = wkt,
                              radius = radius,
                              inherited = inherited,
                              addr_street = address,
                              addr_postcode = postcode,
                              parent = parent,
                              )

            # These could have been added during validate:
            if gis_feature_type:
                feature.gis_feature_type = gis_feature_type
            if the_geom:
                feature.the_geom = the_geom

            location_id = table.insert(**feature)
            feature.id = location_id
            current.gis.update_location_tree(feature)

        else:
            specific = values.get("specific")
            # specific is 0 to skip update (unchanged)
            # specific is None for Lx locations
            if specific and specific == location_id:
                # Update specific location
                feature = Storage(addr_street=address,
                                  addr_postcode=postcode,
                                  parent=parent,
                                  )
                if any(detail is not None for detail in (lat, lon, wkt, radius)):
                    feature.lat = lat
                    feature.lon = lon
                    feature.lat_min = lat_min
                    feature.lon_min = lon_min
                    feature.lat_max = lat_max
                    feature.lon_max = lon_max
                    feature.wkt = wkt
                    feature.radius = radius
                    feature.inherited = False

                # These could have been added during validate:
                if gis_feature_type:
                    feature.gis_feature_type = gis_feature_type
                if the_geom:
                    feature.the_geom = the_geom

                db(table.id == location_id).update(**feature)
                feature.id = location_id
                current.gis.update_location_tree(feature)

        return location_id, None

# =============================================================================
class S3SelectWidget(OptionsWidget):
    """
        Standard OptionsWidget, but using the jQuery UI SelectMenu:
            http://jqueryui.com/selectmenu/

        Useful for showing Icons against the Options.
    """

    def __init__(self,
                 icons = False
                 ):
        """
            Constructor

            @param icons: show icons next to options,
                           can be:
                                - False (don't show icons)
                                - function (function to call add Icon URLs, height and width to the options)
        """

        self.icons = icons

    def __call__(self, field, value, **attr):

        if isinstance(field, Field):
            selector = str(field).replace(".", "_")
        else:
            selector = field.name.replace(".", "_")

        # Widget
        _class = attr.get("_class", None)
        if _class:
            if "select-widget" not in _class:
                attr["_class"] = "%s select-widget" % _class
        else:
            attr["_class"] = "select-widget"

        widget = TAG[""](self.widget(field, value, **attr),
                         requires = field.requires)

        if self.icons:
            # Use custom subclass in S3.js
            fn = "iconselectmenu().iconselectmenu('menuWidget').addClass('customicons')"
        else:
            # Use default
            fn = "selectmenu()"
        script = '''$('#%s').%s''' % (selector, fn)

        jquery_ready = current.response.s3.jquery_ready
        if script not in jquery_ready: # Prevents loading twice when form has errors
            jquery_ready.append(script)

        return widget

    # -------------------------------------------------------------------------
    def widget(self, field, value, **attributes):
        """
            Generates a SELECT tag, including OPTIONs (only 1 option allowed)
            see also: `FormWidget.widget`
        """

        default = {"value": value,
                   }
        attr = self._attributes(field, default,
                               **attributes)
        requires = field.requires
        if not isinstance(requires, (list, tuple)):
            requires = [requires]
        if requires:
            if hasattr(requires[0], "options"):
                options = requires[0].options()
            else:
                raise SyntaxError(
                    "widget cannot determine options of %s" % field)
        icons = self.icons
        if icons:
            # Options including Icons
            # Add the Icons to the Options
            options = icons(options)
            opts = []
            oappend = opts.append
            for (k, v, i) in options:
                oattr = {"_value": k,
                         #"_data-class": "select-widget-icon",
                         }
                if i:
                    oattr["_data-style"] = "background-image:url('%s');height:%spx;width:%spx" % \
                        (i[0], i[1], i[2])
                opt = OPTION(v, **oattr)
                oappend(opt)
        else:
            # Standard Options
            opts = [OPTION(v, _value=k) for (k, v) in options]

        return SELECT(*opts, **attr)

# =============================================================================
class S3MultiSelectWidget(MultipleOptionsWidget):
    """
        Standard MultipleOptionsWidget, but using the jQuery UI:
            http://www.erichynds.com/jquery/jquery-ui-multiselect-widget/
            static/scripts/ui/multiselect.js
    """

    def __init__(self,
                 search = "auto",
                 header = True,
                 multiple = True,
                 selectedList = 3,
                 noneSelectedText = "Select",
                 columns = None,
                 create = None,
                 ):
        """
            Constructor

            @param search: show an input field in the widget to search for options,
                           can be:
                                - True (always show search field)
                                - False (never show the search field)
                                - "auto" (show search if more than 10 options)
                                - <number> (show search if more than <number> options)
            @param header: show a header for the options list, can be:
                                - True (show the default Select All/Deselect All header)
                                - False (don't show a header unless required for search field)
            @param selectedList: maximum number of individual selected options to show
                                 on the widget button (before collapsing into "<number>
                                 selected")
            @param noneSelectedText: text to show on the widget button when no option is
                                     selected (automatic l10n, no T() required)
            @param columns: set the columns width class for Foundation forms
            @param create: options to create a new record {"c": "controller",
                                                           "f": "function",
                                                           "label": "label",
                                                           "parent": "parent", (optional: which function to lookup options from)
                                                           "child": "child", (optional: which field to lookup options for)
                                                           }
            @ToDo: Complete the 'create' feature:
                * Ensure the Create option doesn't get filtered out when searching for items
                * Style option to make it clearer that it's an Action item
        """

        self.search = search
        self.header = header
        self.multiple = multiple
        self.selectedList = selectedList
        self.noneSelectedText = noneSelectedText
        self.columns = columns
        self.create = create

    def __call__(self, field, value, **attr):

        T = current.T

        if isinstance(field, Field):
            selector = str(field).replace(".", "_")
        else:
            selector = field.name.replace(".", "_")

        # Widget
        _class = attr.get("_class", None)
        if _class:
            if "multiselect-widget" not in _class:
                attr["_class"] = "%s multiselect-widget" % _class
        else:
            attr["_class"] = "multiselect-widget"

        multiple_opt = self.multiple
        if multiple_opt:
            w = MultipleOptionsWidget
        else:
            w = OptionsWidget
            if value:
                # Base widget requires single value, so enforce that
                # if necessary, and convert to string to match options
                value = str(value[0] if type(value) is list else value)

        # Set explicit columns width for the formstyle
        if self.columns:
            attr["s3cols"] = self.columns

        widget = w.widget(field, value, **attr)
        options_len = len(widget)

        # Search field and header for multiselect options list
        search_opt = self.search
        header_opt = self.header
        if not multiple_opt and header_opt is True:
            # Select All / Unselect All doesn't make sense if multiple == False
            header_opt = False
        if not isinstance(search_opt, bool) and \
           (search_opt == "auto" or isinstance(search_opt, INTEGER_TYPES)):
            max_options = 10 if search_opt == "auto" else search_opt
            if options_len > max_options:
                search_opt = True
            else:
                search_opt = False
        if search_opt is True and header_opt is False:
            # Must have at least "" as header to show the search field
            header_opt = ""

        # Other options:
        # * Show Selected List
        if header_opt is True:
            header = '''checkAllText:'%s',uncheckAllText:"%s"''' % \
                     (T("Select All"),
                      T("Clear All"))
        elif header_opt is False:
            header = '''header:false'''
        else:
            header = '''header:"%s"''' % header_opt
        noneSelectedText = self.noneSelectedText
        if not isinstance(noneSelectedText, lazyT):
            noneSelectedText = T(noneSelectedText)
        create = self.create or ""
        if create:
            tablename = "%s_%s" % (create["c"], create["f"])
            if current.auth.s3_has_permission("create", tablename):
                create = ",create:%s" % json.dumps(create, separators=SEPARATORS)
            else:
                create = ""
        script = '''$('#%s').multiselect({allSelectedText:'%s',selectedText:'%s',%s,height:300,minWidth:0,selectedList:%s,noneSelectedText:'%s',multiple:%s%s})''' % \
                 (selector,
                  T("All selected"),
                  T("# selected"),
                  header,
                  self.selectedList,
                  noneSelectedText,
                  "true" if multiple_opt else "false",
                  create
                  )

        if search_opt:
            script = '''%s.multiselectfilter({label:'',placeholder:'%s'})''' % \
                (script, T("Search"))
        jquery_ready = current.response.s3.jquery_ready
        if script not in jquery_ready: # Prevents loading twice when form has errors
            jquery_ready.append(script)

        return widget

# =============================================================================
class S3CascadeSelectWidget(FormWidget):
    """ Cascade Selector for Hierarchies """

    def __init__(self,
                 lookup=None,
                 formstyle=None,
                 levels=None,
                 multiple=False,
                 filter=None,
                 leafonly=True,
                 cascade=None,
                 represent=None,
                 inline=False,
                 ):
        """
            Constructor

            @param lookup: the name of the hierarchical lookup-table
            @param formstyle: the formstyle to use for the inline-selectors
                              (defaults to s3.crud.formstyle)
            @param levels: list of labels for the hierarchy levels, in
                           top-down order
            @param multiple: allow selection of multiple options
            @param filter: resource filter expression to filter the
                           selectable options
            @param leafonly: allow only leaf-nodes to be selected
            @param cascade: automatically select child-nodes when a
                            parent node is selected (override option,
                            implied by leafonly if not set explicitly)
            @param represent: representation function for the nodes
                              (defaults to the represent of the field)
            @param inline: formstyle uses inline-labels, so add a colon
        """

        self.lookup = lookup
        self.formstyle = formstyle

        self.levels = levels
        self.multiple = multiple

        self.filter = filter
        self.leafonly = leafonly
        self.cascade = cascade

        self.represent = represent
        self.inline = inline

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attr):
        """
            Widget renderer

            @param field: the Field
            @param value: the current value(s)
            @param attr: additional HTML attributes for the widget
        """

        # Get the lookup table
        lookup = self.lookup
        if not lookup:
            lookup = s3_get_foreign_key(field)[0]
            if not lookup:
                raise SyntaxError("No lookup table known for %s" % field)

        # Get the representation
        represent = self.represent
        if not represent:
            represent = field.represent

        # Get the hierarchy
        leafonly = self.leafonly
        from .s3hierarchy import S3Hierarchy
        h = S3Hierarchy(tablename = lookup,
                        represent = represent,
                        filter = self.filter,
                        leafonly = leafonly,
                        )
        if not h.config:
            raise AttributeError("No hierarchy configured for %s" % lookup)

        # Get the cascade levels
        levels = self.levels
        if not levels:
            levels = current.s3db.get_config(lookup, "hierarchy_levels")
        if not levels:
            levels = [field.label]

        # Get the hierarchy nodes
        nodes = h.json(max_depth=len(levels)-1)

        # Intended DOM-ID of the input field
        if isinstance(field, Field):
            input_id = str(field).replace(".", "_")
        else:
            input_id = field.name.replace(".", "_")

        # Prepare labels and selectors
        selectors = []
        multiple = "multiple" if self.multiple else None
        T = current.T
        for depth, level in enumerate(levels):
            # The selector for this level
            selector = SELECT(data = {"level": depth},
                              _class = "s3-cascade-select",
                              _disabled = "disabled",
                              _multiple = multiple,
                              )

            # The label for the selector
            row_id = "%s_level_%s" % (input_id, depth)
            label = T(level) if isinstance(level, basestring) else level
            if self.inline:
                label = "%s:" % label
            label = LABEL(label, _for=row_id, _id="%s__label" % row_id)
            selectors.append((row_id, label, selector, None))

        # Build inline-rows from labels+selectors
        formstyle = self.formstyle
        if not formstyle:
            formstyle = current.response.s3.crud.formstyle
        selector_rows = formstyle(None, selectors)

        # Construct the widget
        widget_id = attr.get("_id")
        if not widget_id:
            widget_id = "%s-cascade" % input_id
        widget = DIV(self.hidden_input(input_id, field, value, **attr),
                     INPUT(_type = "hidden",
                           _class = "s3-cascade",
                           _value = json.dumps(nodes),
                           ),
                     selector_rows,
                     _class = "s3-cascade-select",
                     _id = widget_id,
                     )

        # Inject static JS and instantiate UI widget
        cascade = self.cascade
        if leafonly and cascade is not False:
            cascade = True

        widget_opts = {"multiple": True if multiple else False,
                       "leafonly": leafonly,
                       "cascade": cascade,
                       }
        self.inject_script(widget_id, widget_opts)

        return widget

    # -------------------------------------------------------------------------
    def hidden_input(self, input_id, field, value, **attr):
        """
            Construct the hidden (real) input and populate it with the
            current field value

            @param input_id: the DOM-ID for the input
            @param field: the Field
            @param value: the current value
            @param attr: widget attributes from caller
        """

        # Currently selected values
        selected = []
        append = selected.append
        if isinstance(value, basestring) and value and not value.isdigit():
            value = self.parse(value)[0]
        if not isinstance(value, (list, tuple, set)):
            values = [value]
        else:
            values = value
        for v in values:
            if isinstance(v, INTEGER_TYPES) or str(v).isdigit():
                append(v)

        # Prepend value parser to field validator
        requires = field.requires
        if isinstance(requires, (list, tuple)):
            requires = [self.parse] + requires
        elif requires is not None:
            requires = [self.parse, requires]
        else:
            requires = self.parse

        # The hidden input field
        hidden_input = INPUT(_type = "hidden",
                             _name = attr.get("_name") or field.name,
                             _id = input_id,
                             _class = "s3-cascade-input",
                             requires = requires,
                             value = json.dumps(selected),
                             )

        return hidden_input

    # -------------------------------------------------------------------------
    @staticmethod
    def inject_script(widget_id, options):
        """
            Inject static JS and instantiate client-side UI widget

            @param widget_id: the widget ID
            @param options: JSON-serializable dict with UI widget options
        """

        request = current.request
        s3 = current.response.s3

        # Static script
        if s3.debug:
            script = "/%s/static/scripts/S3/s3.ui.cascadeselect.js" % \
                     request.application
        else:
            script = "/%s/static/scripts/S3/s3.ui.cascadeselect.min.js" % \
                     request.application
        scripts = s3.scripts
        if script not in scripts:
            scripts.append(script)

        # Widget options
        opts = {}
        if options:
            opts.update(options)

        # Widget instantiation
        script = '''$('#%(widget_id)s').cascadeSelect(%(options)s)''' % \
                 {"widget_id": widget_id,
                  "options": json.dumps(opts),
                  }
        jquery_ready = s3.jquery_ready
        if script not in jquery_ready:
            jquery_ready.append(script)

    # -------------------------------------------------------------------------
    def parse(self, value):
        """
            Value parser for the hidden input field of the widget

            @param value: the value received from the client, JSON string

            @return: a list (if multiple=True) or the value
        """

        default = [] if self.multiple else None

        if value is None:
            return None, None
        try:
            value = json.loads(value)
        except ValueError:
            return default, None
        if not self.multiple and isinstance(value, list):
            value = value[0] if value else None

        return value, None

# =============================================================================
class S3HierarchyWidget(FormWidget):
    """ Selector Widget for Hierarchies """

    def __init__(self,
                 lookup = None,
                 represent = None,
                 multiple = True,
                 leafonly = True,
                 cascade = False,
                 bulk_select = False,
                 filter = None,
                 columns = None,
                 none = None,
                 ):
        """
            Constructor

            @param lookup: name of the lookup table (must have a hierarchy
                           configured)
            @param represent: alternative representation method (falls back
                              to the field's represent-method)
            @param multiple: allow selection of multiple options
            @param leafonly: True = only leaf nodes can be selected (with
                             multiple=True: selection of a parent node will
                             automatically select all leaf nodes of that
                             branch)
                             False = any nodes can be selected independently
            @param cascade: automatic selection of children when selecting
                            a parent node (if leafonly=False, otherwise
                            this is the standard behavior!), requires
                            multiple=True
            @param bulk_select: provide option to select/deselect all nodes
            @param filter: filter query for the lookup table
            @param columns: set the columns width class for Foundation forms
            @param none: label for an option that delivers "None" as value
                         (useful for HierarchyFilters with explicit none-selection)
        """

        self.lookup = lookup
        self.represent = represent
        self.filter = filter

        self.multiple = multiple
        self.leafonly = leafonly
        self.cascade = cascade

        self.columns = columns
        self.bulk_select = bulk_select

        self.none = none

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attr):
        """
            Widget renderer

            @param field: the Field
            @param value: the current value(s)
            @param attr: additional HTML attributes for the widget
        """

        if isinstance(field, Field):
            selector = str(field).replace(".", "_")
        else:
            selector = field.name.replace(".", "_")

        # Widget ID
        widget_id = attr.get("_id")
        if widget_id == None:
            widget_id = attr["_id"] = "%s-hierarchy" % selector

        # Field name
        name = attr.get("_name")
        if not name:
            name = field.name

        # Get the lookup table
        lookup = self.lookup
        if not lookup:
            lookup = s3_get_foreign_key(field)[0]
            if not lookup:
                raise SyntaxError("No lookup table known for %s" % field)

        # Get the representation
        represent = self.represent
        if not represent:
            represent = field.represent

        # Instantiate the hierarchy
        leafonly = self.leafonly
        from .s3hierarchy import S3Hierarchy
        h = S3Hierarchy(tablename = lookup,
                        represent = represent,
                        leafonly = leafonly,
                        filter = self.filter,
                        )
        if not h.config:
            raise AttributeError("No hierarchy configured for %s" % lookup)

        # Set explicit columns width for the formstyle
        if self.columns:
            attr["s3cols"] = self.columns

        # Generate the widget
        settings = current.deployment_settings
        cascade_option_in_tree = settings.get_ui_hierarchy_cascade_option_in_tree()

        if self.multiple and self.bulk_select and \
           not cascade_option_in_tree:
            # Render bulk-select options as separate header
            header = DIV(SPAN(A("Select All",
                                _class="s3-hierarchy-select-all",
                                ),
                              " | ",
                              A("Deselect All",
                                _class="s3-hierarchy-deselect-all",
                                ),
                              _class="s3-hierarchy-bulkselect",
                              ),
                         _class="s3-hierarchy-header",
                         )
        else:
            header = ""

        # Currently selected values
        selected = []
        append = selected.append
        if isinstance(value, basestring) and value and not value.isdigit():
            value = self.parse(value)[0]
        if not isinstance(value, (list, tuple, set)):
            values = [value]
        else:
            values = value
        for v in values:
            if isinstance(v, INTEGER_TYPES) or str(v).isdigit():
                append(v)

        # Prepend value parser to field validator
        requires = field.requires
        if isinstance(requires, (list, tuple)):
            requires = [self.parse] + requires
        elif requires is not None:
            requires = [self.parse, requires]
        else:
            requires = self.parse

        # The hidden input field
        hidden_input = INPUT(_type = "hidden",
                             _multiple = "multiple",
                             _name = name,
                             _id = selector,
                             _class = "s3-hierarchy-input",
                             requires = requires,
                             value = json.dumps(selected),
                             )

        # The widget
        widget = DIV(hidden_input,
                     DIV(header,
                         DIV(h.html("%s-tree" % widget_id,
                                    none=self.none,
                                    ),
                             _class = "s3-hierarchy-tree",
                             ),
                         _class = "s3-hierarchy-wrapper",
                         ),
                     **attr)
        widget.add_class("s3-hierarchy-widget")

        s3 = current.response.s3
        scripts = s3.scripts
        script_dir = "/%s/static/scripts" % current.request.application

        # Custom theme
        theme = settings.get_ui_hierarchy_theme()

        if s3.debug:
            script = "%s/jstree.js" % script_dir
            if script not in scripts:
                scripts.append(script)
            script = "%s/S3/s3.ui.hierarchicalopts.js" % script_dir
            if script not in scripts:
                scripts.append(script)
            style = "%s/jstree.css" % theme.get("css", "plugins")
            if style not in s3.stylesheets:
                s3.stylesheets.append(style)
        else:
            script = "%s/S3/s3.jstree.min.js" % script_dir
            if script not in scripts:
                scripts.append(script)
            style = "%s/jstree.min.css" % theme.get("css", "plugins")
            if style not in s3.stylesheets:
                s3.stylesheets.append(style)

        T = current.T

        widget_opts = {"selected": selected,
                       "selectedText": str(T("# selected")),
                       "noneSelectedText": str(T("Select")),
                       "noOptionsText": str(T("No options available")),
                       "selectAllText": str(T("Select All")),
                       "deselectAllText": str(T("Deselect All")),
                       }

        # Only include non-default options
        if not self.multiple:
            widget_opts["multiple"] = False
        if not leafonly:
            widget_opts["leafonly"] = False
        if self.cascade:
            widget_opts["cascade"] = True
        if self.bulk_select:
            widget_opts["bulkSelect"] = True
        if not cascade_option_in_tree:
            widget_opts["cascadeOptionInTree"] = False
        icons = theme.get("icons", False)
        if icons:
            widget_opts["icons"] = icons
        stripes = theme.get("stripes", True)
        if not stripes:
            widget_opts["stripes"] = stripes


        script = '''$('#%(widget_id)s').hierarchicalopts(%(widget_opts)s)''' % \
                 {"widget_id": widget_id,
                  "widget_opts": json.dumps(widget_opts, separators=SEPARATORS),
                  }

        s3.jquery_ready.append(script)

        return widget

    # -------------------------------------------------------------------------
    def parse(self, value):
        """
            Value parser for the hidden input field of the widget

            @param value: the value received from the client, JSON string

            @return: a list (if multiple=True) or the value
        """

        default = [] if self.multiple else None

        if value is None:
            return None, None
        try:
            value = json.loads(value)
        except ValueError:
            return default, None
        if not self.multiple and isinstance(value, list):
            value = value[0] if value else None

        return value, None

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
                 ):

        self.post_process = post_process
        self.tablename = "org_organisation"
        self.default_from_profile = default_from_profile

    def __call__(self, field, value, **attributes):

        def transform_value(value):
            if not value and self.default_from_profile:
                auth = current.session.auth
                if auth and auth.user:
                    value = auth.user.organisation_id
            return value

        settings = current.deployment_settings
        delay = settings.get_ui_autocomplete_delay()
        min_length = settings.get_ui_autocomplete_min_chars()

        return S3GenericAutocompleteTemplate(self.post_process,
                                             delay,
                                             min_length,
                                             field,
                                             value,
                                             attributes,
                                             transform_value = transform_value,
                                             tablename = "org_organisation",
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
                    raise SyntaxError("widget cannot determine options of %s" % field)

        javascript_array = '''%s_options=%s''' % (name,
                                                  json.dumps(options, separators=SEPARATORS))
        s3 = current.response.s3
        s3.js_global.append(javascript_array)
        s3.scripts.append("/%s/static/scripts/S3/s3.orghierarchy.js" % \
            current.request.application)

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
                 ajax_filter = "",
                 ):

        self.post_process = post_process
        self.c = controller
        self.f = function
        self.hideerror = hideerror
        self.ajax_filter = ajax_filter

    def __call__(self, field, value, **attributes):

        default = {"_type": "text",
                   "value": (value is not None and str(value)) or "",
                   }
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

        script = '''S3.autocomplete.person('%(controller)s','%(fn)s',"%(input)s"''' % \
            {"controller": self.c,
             "fn": self.f,
             "input": real_input,
             }
        options = ""
        post_process = self.post_process

        settings = current.deployment_settings
        delay = settings.get_ui_autocomplete_delay()
        min_length = settings.get_ui_autocomplete_min_chars()

        if self.ajax_filter:
            options = ''',"%(ajax_filter)s"''' % \
                {"ajax_filter": self.ajax_filter}

        if min_length != 2:
            options += ''',"%(postprocess)s",%(delay)s,%(min_length)s''' % \
                {"postprocess": post_process,
                 "delay": delay,
                 "min_length": min_length,
                 }
        elif delay != 800:
            options += ''',"%(postprocess)s",%(delay)s''' % \
                {"postprocess": post_process,
                 "delay": delay,
                 }
        elif post_process:
            options += ''',"%(postprocess)s"''' % \
                {"postprocess": post_process}

        script = '''%s%s)''' % (script, options)
        current.response.s3.jquery_ready.append(script)

        return TAG[""](INPUT(_id=dummy_input,
                             _class="string",
                             _value=represent),
                       DIV(_id="%s_throbber" % dummy_input,
                           _class="throbber input_throbber hide"),
                       INPUT(hideerror=self.hideerror, **attr),
                       requires = field.requires
                       )

# =============================================================================
class S3PentityAutocompleteWidget(FormWidget):
    """
        Renders a pr_pentity SELECT as an INPUT field with AJAX Autocomplete.
        Differs from the S3AutocompleteWidget in that it can filter by type &
        also represents results with the type
    """

    def __init__(self,
                 controller = "pr",
                 function = "pentity",
                 types = None,
                 post_process = "",
                 hideerror = False,
                 ):

        self.post_process = post_process
        self.c = controller
        self.f = function
        self.types = types
        self.hideerror = hideerror

    def __call__(self, field, value, **attributes):

        default = {"_type": "text",
                   "value": (value is not None and str(value)) or "",
                   }
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

        T = current.T
        s3 = current.response.s3
        script = \
'''i18n.person="%s"\ni18n.group="%s"\ni18n.none_of_the_above="%s"''' % \
            (T("Person"), T("Group"), T("None of the above"))
        s3.js_global.append(script)

        if self.types:
            # Something other than default: ("pr_person", "pr_group")
            types = json.dumps(self.types, separators=SEPARATORS)
        else:
            types = ""

        script = '''S3.autocomplete.pentity('%(controller)s','%(fn)s',"%(input)s"''' % \
            {"controller": self.c,
             "fn": self.f,
             "input": real_input,
             }

        options = ""
        post_process = self.post_process

        settings = current.deployment_settings
        delay = settings.get_ui_autocomplete_delay()
        min_length = settings.get_ui_autocomplete_min_chars()

        if types:
            options = ''',"%(postprocess)s",%(delay)s,%(min_length)s,%(types)s''' % \
                {"postprocess": post_process,
                 "delay": delay,
                 "min_length": min_length,
                 "types": types,
                 }
        elif min_length != 2:
            options = ''',"%(postprocess)s",%(delay)s,%(min_length)s''' % \
                {"postprocess": post_process,
                 "delay": delay,
                 "min_length": min_length,
                 }
        elif delay != 800:
            options = ''',"%(postprocess)s",%(delay)s''' % \
                {"postprocess": post_process,
                 "delay": delay,
                 }
        elif post_process:
            options = ''',"%(postprocess)s"''' % \
                {"postprocess": post_process,
                 }

        script = '''%s%s)''' % (script, options)
        s3.jquery_ready.append(script)
        return TAG[""](INPUT(_id=dummy_input,
                             _class="string",
                             _value=represent),
                       DIV(_id="%s_throbber" % dummy_input,
                           _class="throbber input_throbber hide"),
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

        default = {"_type": "text",
                   "value": (value is not None and str(value)) or "",
                   }
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
                 ):

        self.auth = current.auth
        self.post_process = post_process

    def __call__(self, field, value, **attributes):

        default = {"_type": "text",
                   "value": (value is not None and str(value)) or "",
                   }
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
            represent = field.represent
            if hasattr(represent, "link"):
                # S3Represent, so don't generate HTML
                text = s3_unicode(represent(value, show_link=False))
            else:
                # Custom represent, so filter out HTML later
                text = s3_unicode(represent(value))
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
        site_types = '''S3.org_site_types=%s''' % json.dumps(site_types, separators=SEPARATORS)

        settings = current.deployment_settings
        delay = settings.get_ui_autocomplete_delay()
        min_length = settings.get_ui_autocomplete_min_chars()

        js_global = s3.js_global
        if site_types not in js_global:
            js_global.append(site_types)
        script = '''S3.autocomplete.site('%(input)s',"%(postprocess)s"''' % \
            {"input": real_input,
             "postprocess": self.post_process,
             }
        if delay != 800:
            script = "%s,%s" % (script, delay)
            if min_length != 2:
                script = "%s,%s" % (script, min_length)
        elif min_length != 2:
            script = "%s,,%s" % (script, min_length)
        script = "%s)" % script

        s3.jquery_ready.append(script)
        return TAG[""](INPUT(_id=dummy_input,
                             _class="string",
                             _value=represent),
                       DIV(_id="%s_throbber" % dummy_input,
                           _class="throbber input_throbber hide"),
                       INPUT(**attr),
                       requires = field.requires
                       )

# =============================================================================
class S3SliderWidget(FormWidget):
    """
        Standard Slider Widget

        The range of the Slider is derived from the Validator
    """

    def __init__(self,
                 step = 1,
                 type = "int",
                 ):
        self.step = step
        self.type = type

    def __call__(self, field, value, **attributes):

        validator = field.requires
        field = str(field)
        fieldname = field.replace(".", "_")
        input_field = INPUT(_name = field.split(".")[1],
                            _disabled = True,
                            _id = fieldname,
                            _style = "border:0",
                            _value = value,
                            )
        slider = DIV(_id="%s_slider" % fieldname, **attributes)

        s3 = current.response.s3

        if isinstance(validator, IS_EMPTY_OR):
            validator = validator.other

        self.min = validator.minimum

        # Max Value depends upon validator type
        if isinstance(validator, IS_INT_IN_RANGE):
            self.max = validator.maximum - 1
        elif isinstance(validator, IS_FLOAT_IN_RANGE):
            self.max = validator.maximum

        if value is None:
            # JSONify
            value = "null"
            script = '''i18n.slider_help="%s"''' % \
                current.T("Click on the slider to choose a value")
            s3.js_global.append(script)

        if self.type == "int":
            script = '''S3.slider('%s',%i,%i,%i,%s)''' % (fieldname,
                                                          self.min,
                                                          self.max,
                                                          self.step,
                                                          value)
        else:
            # Float
            script = '''S3.slider('%s',%f,%f,%f,%s)''' % (fieldname,
                                                          self.min,
                                                          self.max,
                                                          self.step,
                                                          value)
        s3.jquery_ready.append(script)

        return TAG[""](input_field, slider)

# =============================================================================
class S3StringWidget(StringWidget):
    """
        Extend the default Web2Py widget to include a Placeholder
    """

    def __init__(self,
                 columns = 10,
                 placeholder = None,
                 prefix = None,
                 textarea = False,
                 ):
        """
            Constructor

            @param columns: number of grid columns to span (Foundation-themes)
            @param placeholder: placeholder text for the input field
            @param prefix: text for prefix button (Foundation-themes)
            @param textarea: render as textarea rather than string input
        """

        self.columns = columns
        self.placeholder = placeholder
        self.prefix = prefix
        self.textarea = textarea

    def __call__(self, field, value, **attributes):

        default = {"value": (value is not None and str(value)) or "",
                   }

        if self.textarea:
            attr = TextWidget._attributes(field, default, **attributes)
        else:
            attr = StringWidget._attributes(field, default, **attributes)

        placeholder = self.placeholder
        if placeholder:
            attr["_placeholder"] = placeholder

        if self.textarea:
            widget = TEXTAREA(**attr)
        else:
            widget = INPUT(**attr)

        # NB These classes target Foundation Themes
        prefix = self.prefix
        if prefix:
            widget = DIV(DIV(SPAN(prefix, _class="prefix"),
                             _class="small-1 columns",
                             ),
                         DIV(widget,
                             _class="small-11 columns",
                             ),
                         _class="row collapse",
                        )

        # Set explicit columns width for the formstyle
        columns = self.columns
        if columns:
            widget["s3cols"] = columns

        return widget

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
        elif isinstance(value, basestring):
            try:
                value = int(value)
            except ValueError:
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
        except ValueError:
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
        Subclass for use in inline-forms

        - always renders all widget elements (even when empty), so that
          they can be updated from JavaScript
        - adds CSS selectors for widget elements
    """

    @classmethod
    def widget(cls, field, value, download_url=None, **attributes):
        """
        generates a INPUT file tag.

        Optionally provides an A link to the file, including a checkbox so
        the file can be deleted.
        All is wrapped in a DIV.

        @see: :meth:`FormWidget.widget`
        @param download_url: Optional URL to link to the file (default = None)

        """

        T = current.T

        # File input
        default = {"_type": "file",
                   }
        attr = cls._attributes(field, default, **attributes)

        # File URL
        base_url = "/default/download"
        if download_url and value:
            if callable(download_url):
                url = download_url(value)
            else:
                base_url = download_url
                url = download_url + "/" + value
        else:
            url = None

        # Download-link
        link = SPAN("[",
                    A(T(cls.GENERIC_DESCRIPTION),
                      _href = url,
                      ),
                    _class = "s3-upload-link",
                    _style = "white-space:nowrap",
                    )

        # Delete-checkbox
        requires = attr["requires"]
        if requires == [] or isinstance(requires, IS_EMPTY_OR):
            name = field.name + cls.ID_DELETE_SUFFIX
            delete_checkbox = TAG[""]("|",
                                      INPUT(_type = "checkbox",
                                            _name = name,
                                            _id = name,
                                            ),
                                      LABEL(T(cls.DELETE_FILE),
                                            _for = name,
                                            _style = "display:inline",
                                            ),
                                      )
            link.append(delete_checkbox)

        # Complete link-element
        link.append("]")
        if not url:
            link.add_class("hide")

        # Image preview
        preview_class = "s3-upload-preview"
        if value and cls.is_image(value):
            preview_url = url
        else:
            preview_url = None
            preview_class = "%s hide" % preview_class
        image = DIV(IMG(_alt = T("Loading"),
                        _src = preview_url,
                        _width = cls.DEFAULT_WIDTH,
                        ),
                    _class = preview_class,
                    )

        # Construct the widget
        inp = DIV(INPUT(**attr),
                  link,
                  image,
                  _class="s3-upload-widget",
                  data = {"base": base_url,
                          },
                  )

        return inp

# =============================================================================
class S3FixedOptionsWidget(OptionsWidget):
    """ Non-introspective options widget """

    def __init__(self, options, translate=False, sort=True, empty=True):
        """
            Constructor

            @param options: the options for the widget, either as iterable of
                            tuples (value, representation) or as dict
                            {value:representation}, or as iterable of strings
                            if value is the same as representation
            @param translate: automatically translate the representation
            @param sort: alpha-sort options (by representation)
            @param empty: add an empty-option (to select none of the options)
        """

        self.options = options
        self.translate = translate
        self.sort = sort
        self.empty = empty

    def __call__(self, field, value, **attributes):

        default = {"value": value}
        attr = self._attributes(field, default, **attributes)

        options = self.options

        if isinstance(options, dict):
            options = options.items()

        opts = []
        translate = self.translate
        T = current.T
        has_none = False
        for option in options:
            if isinstance(option, tuple):
                k, v = option
            else:
                k, v = option, option
            if v is None:
                v = current.messages["NONE"]
            elif translate:
                v = T(v)
            if k in (None, ""):
                k = ""
                has_none = True
            opts.append((k, v))

        sort = self.sort
        if callable(sort):
            opts = sorted(opts, key=sort)
        elif sort:
            opts = sorted(opts, key=lambda item: item[1])
        if self.empty and not has_none:
            opts.insert(0, ("", current.messages["NONE"]))

        opts = [OPTION(v, _value=k) for (k, v) in opts]
        return SELECT(*opts, **attr)

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
            raise SyntaxError("widget cannot determine options of %s" % field)

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
class S3PasswordWidget(FormWidget):
    """
        Widget for password fields, allows unmasking of passwords
    """

    def __call__(self, field, value, **attributes):

        T = current.T

        tablename = field._tablename
        fieldname = field.name
        js_append = current.response.s3.js_global.append
        js_append('''i18n.password_view="%s"''' % T("View"))
        js_append('''i18n.password_mask="%s"''' % T("Mask"))

        password_input = INPUT(_name = fieldname,
                               _id = "%s_%s" % (tablename, fieldname),
                               _type = "password",
                               _value = value,
                               requires = field.requires,
                               )
        password_unmask = A(T("View"),
                            _class = "s3-unmask",
                            _onclick = '''S3.unmask('%s','%s')''' % (tablename,
                                                                     fieldname),
                            _id = "%s_%s_unmask" % (tablename, fieldname),
                            )
        return DIV(password_input,
                   password_unmask,
                   _class = "s3-password-widget",
                   )

# =============================================================================
class S3PhoneWidget(StringWidget):
    """
        Extend the default Web2Py widget to ensure that the + is at the
        beginning not the end in RTL.
        Adds class to be acted upon by S3.js
    """

    def __call__(self, field, value, **attributes):

        default = {"value": (value is not None and str(value)) or "",
                   }

        attr = StringWidget._attributes(field, default, **attributes)
        attr["_class"] = "string phone-widget"

        widget = INPUT(**attr)

        return widget

# =============================================================================
def s3_comments_widget(field, value, **attr):
    """
        A smaller-than-normal textarea
        to be used by the s3.comments() & gis.desc_field Reusable fields
    """

    _id = attr.get("_id", "%s_%s" % (field._tablename, field.name))

    _name = attr.get("_name", field.name)

    return TEXTAREA(_name = _name,
                    _id = _id,
                    _class = "comments %s" % (field.type),
                    _placeholder = attr.get("_placeholder"),
                    value = value,
                    requires = field.requires)

# =============================================================================
def s3_richtext_widget(field, value):
    """
        A Rich Text field to be used by the CMS Post Body, etc
        - uses CKEditor
        - requires doc module loaded to be able to upload/browse Images
    """

    s3 = current.response.s3
    widget_id = "%s_%s" % (field._tablename, field.name)

    # Load the scripts
    sappend = s3.scripts.append
    ckeditor = URL(c="static", f="ckeditor", args="ckeditor.js")
    sappend(ckeditor)
    adapter = URL(c="static", f="ckeditor", args=["adapters",
                                                  "jquery.js"])
    sappend(adapter)

    table = current.s3db.table("doc_ckeditor")
    if table:
        # Doc module enabled: can upload/browse images
        url = '''filebrowserUploadUrl:'/%(appname)s/doc/ck_upload',filebrowserBrowseUrl:'/%(appname)s/doc/ck_browse',''' \
                % {"appname": current.request.application}
    else:
        # Doc module not enabled: cannot upload/browse images
        url = ""

    # Toolbar options: http://docs.ckeditor.com/#!/guide/dev_toolbar
    js = '''var ck_config={toolbar:[['Format','Bold','Italic','-','NumberedList','BulletedList','-','Link','Unlink','-','Image','Table','-','PasteFromWord','-','Source','Maximize']],toolbarCanCollapse:false,%sremovePlugins:'elementspath'}''' \
            % url
    s3.js_global.append(js)

    js = '''$('#%s').ckeditor(ck_config)''' % widget_id
    s3.jquery_ready.append(js)

    return TEXTAREA(_name=field.name,
                    _id=widget_id,
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

    _vars = current.request.get_vars

    # JQueryUI Autocomplete uses "term" instead of "value"
    # (old JQuery Autocomplete uses "q" instead of "value")
    value = _vars.term or _vars.value or _vars.q or None

    # We want to do case-insensitive searches
    # (default anyway on MySQL/SQLite, but not PostgreSQL)
    value = value.lower().strip()

    fieldname = _vars.get("field", "name")
    fieldname = str.lower(fieldname)
    filter = _vars.get("filter", "~")

    resource = r.resource
    table = resource.table

    limit = int(_vars.limit or 0)

    from .s3query import FS
    field = FS(fieldname)

    # Default fields to return
    fields = ["id", fieldname]
    # Now using custom method
    #if resource.tablename == "org_site":
    #    # Simpler to provide an exception case than write a whole new class
    #    fields.append("instance_type")

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
        output = current.xml.json_message(False, 400,
                    "Unsupported filter! Supported filters: ~, =, <, >")
        raise HTTP(400, body=output)

    if "link" in _vars:
        link_filter = S3EmbeddedComponentWidget.link_filter_query(table,
                                                                  _vars.link,
                                                                  )
        if link_filter:
            query &= link_filter

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

    output = None
    if filter == "~":
        MAX_SEARCH_RESULTS = current.deployment_settings.get_search_max_results()
        if (not limit or limit > MAX_SEARCH_RESULTS) and \
           resource.count() > MAX_SEARCH_RESULTS:
            output = [
                {"label": str(current.T("There are more than %(max)s results, please input more characters.") % \
                    {"max": MAX_SEARCH_RESULTS})
                 }
                ]

    if output is None:
        rows = resource.select(fields,
                               start=0,
                               limit=limit,
                               orderby=field,
                               as_rows=True)
        output = []
        append = output.append
        for row in rows:
            record = {"id": row.id,
                      fieldname: row[fieldname],
                      }
            append(record)

    current.response.headers["Content-Type"] = "application/json"
    return json.dumps(output, separators=SEPARATORS)

# =============================================================================
class S3XMLContents(object):
    """
        Renderer for db-stored XML contents (e.g. CMS)

        Replaces {{page}} expressions inside the contents with local URLs.

        {{page}}                 - gives the URL of the current page
        {{name:example}}         - gives the URL of the current page with
                                   a query ?name=example (can add any number
                                   of query variables)
        {{c:org,f:organisation}} - c and f tokens override controller and
                                   function of the current page, in this
                                   example like /org/organisation
        {{args:arg,arg}}         - override the current request's URL args
                                   (this should come last in the expression)
        {{noargs}}               - strip all URL args

        @note: does not check permissions for the result URLs
    """

    def __init__(self, contents):
        """
            Constructor

            @param contents: the contents (string)
        """

        self.contents = contents

    # -------------------------------------------------------------------------
    def link(self, match):
        """
            Replace {{}} expressions with local URLs, with the ability to
            override controller, function and URL query variables.Called
            from re.sub.

            @param match: the re match object
        """

        # Parse the expression
        tokens = match.group(1).split(",")

        args = True
        parameters = {}
        arguments = []
        collect_args = False
        for token in tokens:
            if not token:
                continue
            elif ":" in token:
                collect_args = False
                key, value = token.split(":")
            else:
                key, value = token, None
            key = key.strip()
            if not value:
                if key == "noargs":
                    args = False
                elif collect_args:
                    arguments.append(key)
            elif key == "args":
                arguments.append(value.strip())
                collect_args = True
            else:
                parameters[key] = value.strip()

        # Construct the URL
        request = current.request
        c = parameters.pop("c", request.controller)
        f = parameters.pop("f", request.function)
        if not arguments:
            arguments = request.args
        args = arguments if args else []
        return URL(c=c, f=f, args=args, vars=parameters, host=True)

    # -------------------------------------------------------------------------
    def xml(self):
        """ Render the output """

        return re.sub(r"\{\{(.+?)\}\}", self.link, self.contents)

# =============================================================================
class S3QuestionEditorWidget(FormWidget):
    """
        A Question Editor widget for DC
        Client-side JS in s3.ui.question.js

        Currently unused.
        - replace with simple DIV + Hidden IINPUT & build UI client-side?
            . less load on server
            . DRYer (no need to read/extend settings in 2 places)
            . faster for user (faster download and hence time before interaction)
        - for now the replacement is in UCCE as styled to it's Theme
    """

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attr):
        """
            Widget builder

            @param field: the Field
            @param value: the current value
            @param attributes: the HTML attributes for the widget
        """

        selector = attr.get("id")
        if not selector:
            if isinstance(field, Field):
                selector = str(field).replace(".", "_")
            else:
                selector = field.name.replace(".", "_")

        # Field name
        name = attr.get("_name")

        if not name:
            name = field.name

        T = current.T
        request = current.request
        s3 = current.response.s3

        # The actual hidden input containing the JSON of the fields
        real_input = INPUT(_id=selector,
                           _name=name,
                           _value=value,
                           _type="hidden",
                           )

        formstyle = s3.crud.formstyle

        if value is None:
            value = "{}"

        value = eval(value)

        type_options = (("string", "String"),
                        ("integer", "Integer"),
                        ("float", "Float"),
                        ("text", "Text"),
                        ("object", "Object"),
                        ("date", "Date"),
                        ("time", "Time"),
                        ("datetime", "DateTime"),
                        ("reference", "Reference"),
                        ("location", "Location"),
                        )

        type_id = "%s_type" % selector

        select_field = Field("type", requires=IS_IN_SET(type_options))
        select_value = value.get("type", "")

        # Used by OptionsWidget for creating DOM id for select input
        select_field.tablename = "dc_question_model"
        select = OptionsWidget.widget(select_field, select_value)

        # Retrieve value of checkboxes
        multiple = value.get("multiple", False)
        if multiple == "true":
            multiple = True
        else:
            multiple = False

        is_required = value.get("is_required", False)
        if is_required == "true":
            is_required = True
        else:
            is_required = False

        # Render visual components
        components = {}
        manual_input = self._input

        components["type"] = ("Type: ", select, type_id)

        components["is_required"] = manual_input(selector,
                                                 "is_required",
                                                 is_required,
                                                 T("Is Required"),
                                                 "checkbox")

        components["description"] = manual_input(selector,
                                                 "description",
                                                 value.get("description", ""),
                                                 T("Description"))

        components["default_answer"] = manual_input(selector,
                                                    "defaultanswer",
                                                    value.get("defaultanswer", ""),
                                                    T("Default Answer"))

        components["max"] = manual_input(selector,
                                         "max",
                                         value.get("max", ""),
                                         T("Maximum"))

        components["min"] = manual_input(selector,
                                         "min",
                                         value.get("min", ""),
                                         T("Minimum"))

        components["filter"] = manual_input(selector,
                                            "filter",
                                            value.get("filter", ""),
                                            T("Filter"))

        components["reference"] = manual_input(selector,
                                               "reference",
                                               value.get("reference", ""),
                                               T("Reference"))

        components["represent"] = manual_input(selector,
                                               "represent",
                                               value.get("represent", ""),
                                               T("Represent"))

        components["location"] = manual_input(selector,
                                              "location",
                                              value.get("location", "[]"),
                                              T("Location Fields"))

        components["options"] = manual_input(selector,
                                             "options",
                                             value.get("options", "[]"),
                                             T("Options"))

        components["multiple"] = manual_input(selector,
                                              "multiple",
                                              multiple,
                                              T("Multiple Options"),
                                              "checkbox")

        # Load the widget script
        scripts = s3.scripts
        script_dir = "/%s/static/scripts" % request.application

        script = "%s/S3/s3.ui.question.js" % script_dir
        if script not in scripts:
            scripts.append(script)

        # Call the widget
        script = '''$('#%(widget_id)s').addQuestion()''' % \
                {"widget_id": "dc_question_model"}

        s3.jquery_ready.append(script)

        # Get the layout for visible components
        visible_components = self._layout(components, formstyle=formstyle)

        return TAG[""](real_input,
                       visible_components)

    # -------------------------------------------------------------------------
    def _layout(self, components, formstyle=None):
        """
            Overall layout for visible components

            @param components: the components as dict
            @param formstyle: the formstyle (falls back to CRUD formstyle)
        """

        if formstyle is None:
            formstyle = current.response.s3.crud.formstyle

        # Test the formstyle
        row = formstyle("test", "test", "test", "test")

        tuple_rows = isinstance(row, tuple)

        inputs = TAG[""]()
        for name in ("type", "is_required", "description", "default_answer",
                     "max", "min", "filter", "reference", "represent",
                     "location", "options", "multiple"):
            if name in components:
                label, widget, input_id = components[name]
                formrow = formstyle("%s__row" % input_id,
                                    label,
                                    widget,
                                    "")

                if tuple_rows:
                    inputs.append(formrow[0])
                    inputs.append(formrow[1])
                else:
                    inputs.append(formrow)
        return inputs

    # -------------------------------------------------------------------------
    def _input(self,
               fieldname,
               name,
               value,
               label,
               _type="text"):
        """
            Render a text input with given attributes

            @param fieldname: the field name (for ID construction)
            @param name: the name for the input field
            @param value: the initial value for the input
            @param label: the label for the input
            @param hidden: render hidden

            @return: a tuple (label, widget, id, hidden)
        """

        input_id = "%s_%s" % (fieldname, name)

        _label = LABEL("%s: " % label, _for=input_id)

        # If the input is of type checkbox
        if name in ("is_required", "multiple"):
            widget = INPUT(_type=_type, _id=input_id, value=s3_str(value))
        else:
            widget = INPUT(_type=_type, _id=input_id, _value=s3_str(value))

        return (_label, widget, input_id)

# =============================================================================
class S3TagCheckboxWidget(FormWidget):
    """
        Simple widget to use a checkbox to toggle a string-type Field
        between two values (default "Y"|"N").
        Like an S3BooleanWidget but real Booleans cannot be stored in strings.
        Designed for use with tag.value

        NB it is usually better to use a boolean Field with a context-specific
           representation function than this.

        NB make sure the field validator accepts the configured on/off values,
           e.g. IS_IN_SET(("Y", "N")) (also for consistency with imports)

        NB when using this with a filtered key-value component (e.g.
           pr_person_tag), make the filtered component multiple=False and
           embed *.value as subtable-field (do not use S3SQLInlineComponent)
    """

    def __init__(self, on="Y", off="N"):
        """
            Constructor

            @param on: the value of the tag for checkbox=on
            @param off: the value of the tag for checkbox=off
        """

        self.on = on
        self.off = off

    # -------------------------------------------------------------------------
    def __call__(self, field, value, **attributes):
        """
            Widget construction

            @param field: the Field
            @param value: the current (or default) value
            @param attributes: overrides for default attributes
        """

        defaults = {"_type": "checkbox",
                    "value": str(value) == self.on,
                    "requires": self.requires,
                    }
        attr = self._attributes(field, defaults, **attributes)
        return INPUT(**attr)

    # -------------------------------------------------------------------------
    def requires(self, value):
        """
            Input-validator to convert the checkbox value into the
            corresponding tag value

            @param value: the checkbox value ("on" if checked)
        """

        v = self.on if value == "on" else self.off
        return v, None

# =============================================================================
class ICON(I):
    """
        Helper class to render <i> tags for icons, mapping abstract
        icon names to theme-specific CSS classes. The standard icon
        set can be configured using settings.ui.icons

        e.g. ICON("book"), gives:
            - font-awesome: <i class="icon icon-book">
            - foundation: <i class="fi-book">

        Standard sets are defined below.

        Additional icons (beyond the standard set) can be configured
        per deployment (settings.ui.custom_icons).

        If <i class=""> is not suitable for the CSS, a custom HTML
        layout can be configured as settings.ui.icon_layout. See
        S3Config for more details.

        @todo: apply in widgets/crud/profile+datalist layouts etc.
        @todo: better abstract names for the icons to indicate what they
               symbolize rather than what they depict, e.g. "sitemap" is
               typically used to symbolize an organisation => rename into
               "organisation".
    """

    # -------------------------------------------------------------------------
    # Standard icon sets,
    # - "_base" can be used to define a common CSS class for all icons
    #
    icons = {
        # Font-Awesome 4
        # https://fontawesome.com/v4.7.0/icons/
        "font-awesome": {
            "_base": "fa",
            "active": "fa-check",
            "activity": "fa-cogs",
            "add": "fa-plus",
            "administration": "fa-cog",
            "alert": "fa-bell",
            "arrow-down": "fa-arrow-down",
            "assessment": "fa-bar-chart",
            "asset": "fa-fire-extinguisher",
            "attachment": "fa-paperclip",
            "bar-chart": "fa-bar-chart",
            "book": "fa-book",
            "bookmark": "fa-bookmark",
            "bookmark-empty": "fa-bookmark-o",
            "briefcase": "fa-briefcase",
            "calendar": "fa-calendar",
            "caret-right": "fa-caret-right",
            "certificate": "fa-certificate",
            "comment-alt": "fa-comment-o",
            "commit": "fa-check-square-o",
            "copy": "fa-copy",
            "delete": "fa-trash",
            "delivery": "fa-thumbs-up",
            "deploy": "fa-plus",
            "deployed": "fa-check",
            "done": "fa-check",
            "down": "fa-caret-down",
            "edit": "fa-edit",
            "event": "fa-bolt",
            "exclamation": "fa-exclamation",
            "eye": "fa-eye",
            "facebook": "fa-facebook",
            "facility": "fa-home",
            "file": "fa-file",
            "file-alt": "fa-file-o",
            "file-text": "fa-file-text",
            "file-text-alt": "fa-file-text-o",
            "flag": "fa-flag",
            "flag-alt": "fa-flag-o",
            "folder": "fa-folder",
            "folder-alt": "fa-folder-o",
            "folder-open-alt": "fa-folder-open-o",
            "fullscreen": "fa-fullscreen",
            "globe": "fa-globe",
            "goods": "fa-cubes",
            "group": "fa-group",
            "hashtag": "fa-hashtag",
            "hint": "fa-hand-o-right",
            "home": "fa-home",
            "inactive": "fa-check-empty",
            "incident": "fa-bolt",
            "info": "fa-info",
            "info-circle": "fa-info-circle",
            #"instructions": "fa-edit", # UCCE
            "link": "fa-external-link",
            "list": "fa-list",
            "location": "fa-globe",
            "mail": "fa-envelope-o",
            "map-marker": "fa-map-marker",
            "minus": "fa-minus",
            "move": "fa-arrows",
            "news": "fa-info",
            "offer": "fa-truck",
            "organisation": "fa-institution",
            "org-network": "fa-umbrella",
            "other": "fa-circle",
            "paper-clip": "fa-paperclip",
            "pause": "fa-pause",
            "pencil": "fa-pencil",
            "phone": "fa-phone",
            "picture": "fa-picture-o",
            "play": "fa-play",
            "plus": "fa-plus",
            "plus-sign": "fa-plus-sign",
            "print": "fa-print",
            "project": "fa-dashboard",
            "radio": "fa-microphone",
            "remove": "fa-remove",
            #"reports": "fi-bar-chart", # UCCE
            "request": "fa-flag",
            "responsibility": "fa-briefcase",
            "return": "fa-arrow-left",
            "rss": "fa-rss",
            "search": "fa-search",
            #"section-break": "fa-minus", # UCCE
            "sent": "fa-check",
            "settings": "fa-wrench",
            "share": "fa-share-alt",
            "shipment": "fa-truck",
            "site": "fa-home",
            "skype": "fa-skype",
            "staff": "fa-user",
            "star": "fa-star",
            "stop": "fa-stop",
            "table": "fa-table",
            "tag": "fa-tag",
            "tags": "fa-tags",
            "tasks": "fa-tasks",
            "time": "fa-time",
            "truck": "fa-truck",
            "twitter": "fa-twitter",
            "unsent": "fa-times",
            "up": "fa-caret-up",
            "upload": "fa-upload",
            "user": "fa-user",
            "volunteer": "fa-hand-paper-o",
            "wrench": "fa-wrench",
            "zoomin": "fa-zoomin",
            "zoomout": "fa-zoomout",
        },
        # Foundation Icon Fonts 3
        # http://zurb.com/playground/foundation-icon-fonts-3
        "foundation": {
            "active": "fi-check",
            "activity": "fi-price-tag",
            "add": "fi-plus",
            "arrow-down": "fi-arrow-down",
            "attachment": "fi-paperclip",
            "bar-chart": "fi-graph-bar",
            "book": "fi-book",
            "bookmark": "fi-bookmark",
            "bookmark-empty": "fi-bookmark-empty",
            "calendar": "fi-calendar",
            "caret-right": "fi-play",
            "certificate": "fi-burst",
            "comment-alt": "fi-comment",
            "commit": "fi-check",
            "copy": "fi-page-copy",
            "delete": "fi-trash",
            "deploy": "fi-plus",
            "deployed": "fi-check",
            "edit": "fi-page-edit",
            "exclamation": "fi-alert",
            "eye": "fi-eye",
            "facebook": "fi-social-facebook",
            "facility": "fi-home",
            "file": "fi-page-filled",
            "file-alt": "fi-page",
            "file-text": "fi-page-filled",
            "file-text-alt": "fi-page",
            "flag": "fi-flag",
            "flag-alt": "fi-flag",
            "folder": "fi-folder",
            "folder-alt": "fi-folder",
            "folder-open-alt": "fi-folder",
            "fullscreen": "fi-arrows-out",
            "globe": "fi-map",
            "group": "fi-torsos-all",
            "home": "fi-home",
            "inactive": "fi-x",
            "info": "fi-info",
            "info-circle": "fi-info",
            #"instructions": "fi-page-edit", # UCCE
            "link": "fi-web",
            "list": "fi-list-thumbnails",
            "location": "fi-map",
            "mail": "fi-mail",
            "map-marker": "fi-marker",
            "minus": "fi-minus",
            "offer": "fi-burst",
            "organisation": "fi-torsos-all",
            "org-network": "fi-asterisk",
            "other": "fi-asterisk",
            "paper-clip": "fi-paperclip",
            "pause": "fi-pause",
            "pencil": "fi-pencil",
            "phone": "fi-telephone",
            "play": "fi-play",
            "plus": "fi-plus",
            "plus-sign": "fi-plus",
            "print": "fi-print",
            "radio": "fi-microphone",
            "remove": "fi-x",
            #"reports": "fi-graph-bar", # UCCE
            "request": "fi-flag",
            "responsibility": "fi-sheriff-badge",
            "return": "fi-arrow-left",
            "rss": "fi-rss",
            "search": "fi-magnifying-glass",
            #"section-break": "fi-minus", # UCCE
            "sent": "fi-check",
            "settings": "fi-wrench",
            "share": "fi-share",
            "site": "fi-home",
            "skype": "fi-social-skype",
            "star": "fi-star",
            "stop": "fi-stop",
            "table": "fi-list-thumbnails",
            "tag": "fi-price-tag",
            "tags": "fi-pricetag-multiple",
            "tasks": "fi-clipboard-notes",
            "time": "fi-clock",
            "twitter": "fi-social-twitter",
            "unsent": "fi-x",
            "upload": "fi-upload",
            "user": "fi-torso",
            "zoomin": "fi-zoom-in",
            "zoomout": "fi-zoom-out",
        },
        # Font-Awesome 3
        # https://fontawesome.com/v3.2.1/icons/
        "font-awesome3": {
            "_base": "icon",
            "active": "icon-check",
            "activity": "icon-tag",
            "add": "icon-plus",
            "administration": "icon-cog",
            "arrow-down": "icon-arrow-down",
            "attachment": "icon-paper-clip",
            "bar-chart": "icon-bar-chart",
            "book": "icon-book",
            "bookmark": "icon-bookmark",
            "bookmark-empty": "icon-bookmark-empty",
            "briefcase": "icon-briefcase",
            "calendar": "icon-calendar",
            "caret-right": "icon-caret-right",
            "certificate": "icon-certificate",
            "comment-alt": "icon-comment-alt",
            "commit": "icon-truck",
            "copy": "icon-copy",
            "delete": "icon-trash",
            "deploy": "icon-plus",
            "deployed": "icon-ok",
            "down": "icon-caret-down",
            "edit": "icon-edit",
            "exclamation": "icon-exclamation",
            "eye": "icon-eye-open",
            "facebook": "icon-facebook",
            "facility": "icon-home",
            "file": "icon-file",
            "file-alt": "icon-file-alt",
            "file-text": "icon-file-text",
            "file-text-alt": "icon-file-text-alt",
            "flag": "icon-flag",
            "flag-alt": "icon-flag-alt",
            "folder": "icon-folder-close",
            "folder-alt": "icon-folder-close-alt",
            "folder-open-alt": "icon-folder-open-alt",
            "fullscreen": "icon-fullscreen",
            "globe": "icon-globe",
            "group": "icon-group",
            "home": "icon-home",
            "inactive": "icon-check-empty",
            "info": "icon-info",
            "info-circle": "icon-info-sign",
            #"instructions": "icon-edit", # UCCE
            "link": "icon-external-link",
            "list": "icon-list",
            "location": "icon-globe",
            "mail": "icon-envelope-alt",
            "map-marker": "icon-map-marker",
            "minus": "icon-minus",
            "offer": "icon-truck",
            "organisation": "icon-sitemap",
            "org-network": "icon-umbrella",
            "other": "icon-circle",
            "paper-clip": "icon-paper-clip",
            "pause": "icon-pause",
            "pencil": "icon-pencil",
            "phone": "icon-phone",
            "picture": "icon-picture",
            "play": "icon-play",
            "plus": "icon-plus",
            "plus-sign": "icon-plus-sign",
            "print": "icon-print",
            "radio": "icon-microphone",
            "remove": "icon-remove",
            #"reports": "icon-bar-chart", # UCCE
            "request": "icon-flag",
            "responsibility": "icon-briefcase",
            "return": "icon-arrow-left",
            "rss": "icon-rss",
            "search": "icon-search",
            #"section-break": "icon-minus", # UCCE
            "sent": "icon-ok",
            "settings": "icon-wrench",
            "share": "icon-share",
            "site": "icon-home",
            "skype": "icon-skype",
            "star": "icon-star",
            "stop": "icon-stop",
            "table": "icon-table",
            "tag": "icon-tag",
            "tags": "icon-tags",
            "tasks": "icon-tasks",
            "time": "icon-time",
            "truck": "icon-truck",
            "twitter": "icon-twitter",
            "unsent": "icon-remove",
            "up": "icon-caret-up",
            "upload": "icon-upload-alt",
            "user": "icon-user",
            "wrench": "icon-wrench",
            "zoomin": "icon-zoomin",
            "zoomout": "icon-zoomout",
        },
    }

    # -------------------------------------------------------------------------
    def __init__(self, name, **attr):
        """
            Constructor

            @param name: the abstract icon name
            @param attr: additional HTML attributes (optional)
        """

        self.name = name
        super(ICON, self).__init__(" ", **attr)

    # -------------------------------------------------------------------------
    def xml(self):
        """
            Render this instance as XML
        """

        # Custom layout?
        layout = current.deployment_settings.get_ui_icon_layout()
        if layout:
            return layout(self)

        css_class = self.css_class(self.name)

        if css_class:
            self.add_class(css_class)

        return super(ICON, self).xml()

    # -------------------------------------------------------------------------
    @classmethod
    def css_class(cls, name):

        settings = current.deployment_settings
        fallback = "font-awesome"

        # Lookup the default set
        icons = cls.icons
        default_set = settings.get_ui_icons()
        default = icons[fallback]
        if default_set != fallback:
            default.pop("_base", None)
            default.update(icons.get(default_set, {}))

        # Custom set?
        custom = settings.get_ui_custom_icons()

        if custom and name in custom:
            css = custom[name]
            base = custom.get("_base")
        elif name in default:
            css = default[name]
            base = default.get("_base")
        else:
            css = name
            base = None

        return " ".join([c for c in (css, base) if c])

# END =========================================================================
