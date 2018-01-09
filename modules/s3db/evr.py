# -*- coding: utf-8 -*-

""" Sahana Eden Evacuees Registry Model

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

__all__ = ("S3EVRCaseModel",
           "evr_rheader",
           "evr_AddGroupMembers",
           )

from gluon import *
from ..s3 import *

# =============================================================================
class S3EVRCaseModel(S3Model):

    names = ("evr_case",
             "evr_medical_details",
             )

    def model(self):

        T = current.T
        settings = current.deployment_settings

        define_table = self.define_table
        person_id = self.pr_person_id

        # ---------------------------------------------------------------------
        # Case Data
        #
        enable_evr_organisation = settings.get_evr_link_to_organisation()
        organisation_label = settings.get_hrm_organisation_label()

        org_organisation_represent = self.org_OrganisationRepresent()
        org_widget = S3HierarchyWidget(lookup="org_organisation",
                                       represent=org_organisation_represent,
                                       multiple=False,
                                       leafonly=False,)

        tablename = "evr_case"
        define_table(tablename,
                     person_id(ondelete = "CASCADE"),
                     self.org_organisation_id(
                        empty = not settings.get_hrm_org_required(),
                        label = organisation_label,
                        requires = self.org_organisation_requires(required=True),
                        comment = DIV(_class="tooltip",
                                      _title="%s|%s" % (T("Designed Organisation"),
                                                        T("Organisation designed to take care of evacuee"))),
                        widget = org_widget,
                        readable = enable_evr_organisation,
                        writable = enable_evr_organisation,
                        ),
                     Field("fiscal_code", "string", length=16,
                           label = T("Fiscal Code"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Fiscal Code"),
                                                           T("Insert the fiscal code with no spaces")
                                                           )
                                         ),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # If fiscal code is present, it's unique
#         fiscal_code = db.evr_case.fiscal_code
#         fiscal_code.requires = IS_EMPTY_OR(
#                                   IS_NOT_IN_DB(db(db.evr_case.deleted != True),
#                                                fiscal_code),
#                                                null=''
#                                                )

        self.configure(tablename,
                       onaccept = self.evr_case_onaccept,
                       )

        # ---------------------------------------------------------------------
        # Medical Details
        #

        # @todo: use string-codes for option fields for better
        #        maintainability/interoperability
        #
        evr_therapy_opts = {1: T("Vital Long-Term Medication"),
                            2: T("Dialysis"),
                            3: T("Chronic Oxygen Supply"),
                            4: T("Intermittend Ventilator Support"),
                            5: T("Ventilator Dependend"),
                            6: T("Cardiac Assist Device"),
                            }

        evr_allergy_opts = {1: T("Drug"),
                            2: T("Food"),
                            3: T("Olive Tree"),
                            4: T("Grass"),
                            5: T("Dust"),
                            6: T("Other"),
                            }

        evr_disability_opts = {1: T("Visually Impaired"),
                               2: T("Blind"),
                               3: T("Hearing-Impaired"),
                               4: T("Deaf"),
                               5: T("Deaf-Mute"),
                               6: T("Deaf-Blind"),
                               7: T("Aphasic"),
                               8: T("Mobility-Impaired"),
                               9: T("Paralysed"),
                               10: T("Amputated"),
                               11: T("Other Physical Disability"),
                               12: T("Mentally Disabled"),
                               }

        evr_aids_appliances_opts = {1: ("Guide Dog"),
                                    2: ("Wheelchair"),
                                    3: ("Walking stick"),
                                    4: ("Crutch"),
                                    5: ("Tripod"),
                                    6: ("Artificial limb"),
                                    7: ("Catheter"),
                                    8: ("Sanity Napkin"),
                                    }

        def med_multiopt_field(fieldname, options, label=None):
            """ Simple generator for option fields """
            return Field(fieldname, "list:integer",
                         label = label,
                         represent = S3Represent(options = options,
                                                 multiple = True),
                         requires = IS_IN_SET(options, multiple = True),
                         widget = S3MultiSelectWidget(filter = False,
                                                      selectedList = 3,
                                                      noneSelectedText = "Select",
                                                     )
                         )

        evr_source_opts = {1: "Self",
                           2: "Mother",
                           3: "Father",
                           4: "Uncle",
                           5: "Grandfather",
                           6: "Grandmother",
                           7: "Official",
                           8: "Attendant",
                           9: "Neighbour",
                           10: "Teacher",
                           11: "Priest",
                           12: "Other",
                           }

        tablename = "evr_medical_details"
        define_table(tablename,
                     person_id(),
                     med_multiopt_field("therapy",
                                        evr_therapy_opts,
                                        label = T("Therapy"),
                                        ),
                     Field("therapy_comment"),
                     Field("pregnancy", "boolean",
                           label = T("Pregnancy"),
                           ),
                     med_multiopt_field("allergy",
                                        evr_allergy_opts,
                                        label = T("Allergies"),
                                        ),
                     Field("diet",
                           label = T("Food intolerance"),
                           ),
                     med_multiopt_field("disability",
                                        evr_disability_opts,
                                        label = T("Disabilities"),
                                        ),
                     Field("self_sufficient", "boolean",
                           label = T("Self-Sufficient"),
                           ),
                     med_multiopt_field("aids_appliances",
                                        evr_aids_appliances_opts,
                                        label = T("Aids and Appliances"),
                                        ),
                     Field("declared_by_name",
                           label = T("Declared by (Name)"),
                           ),
                     Field("declared_by_relationship", "integer",
                           label = T("Declared by (Relationship)"),
                           represent=S3Represent(options=evr_source_opts),
                           requires = IS_IN_SET(evr_source_opts,
                                                zero=None),
                           ),
                     Field("declared_by_phone",
                           label = T("Declared by (Phone)"),
                           requires = IS_NULL_OR(IS_PHONE_NUMBER()),
                           ),
                     Field("declared_by_email",
                           label = T("Declared by (Email)"),
                           requires = IS_NULL_OR(IS_EMAIL()),
                           ),
                     Field("has_attendant", "boolean",
                           label = T("Has Attendant"),
                           ),
                     Field("attendant_name",
                           label = T("Attendant (Name)"),
                           ),
                     Field("attendant_phone",
                           label = T("Attendant (Phone)"),
                           requires = IS_NULL_OR(IS_PHONE_NUMBER()),
                           ),
                     Field("attendant_email",
                           label = T("Attendant (Email)"),
                           requires = IS_NULL_OR(IS_EMAIL()),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Socio-economic Background
        #
        tablename = "evr_background"
        define_table(tablename,
                     person_id(),
                     Field("legal_measure",
                           label = T("Legal measure / Home warrant"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Legal measure / Home warrant"),
                                                           T("Evacuee subject to special or legal measures/penalities")
                                                           )
                                         ),
                           ),
                     Field("diet_restrictions",
                           label = T("Food Restrictions")
                           ),
                     Field("social_welfare",
                           label = T("Social Welfare"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Social Welfare"),
                                                           T("Evacuee subject to Social Welfare")
                                                           )
                                         ),
                           ),
                     Field("interpreter",
                           label = T("Interpreter / Cultural Mediator Required"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Interpreter / Cultural Mediator"),
                                                           T("Specific language interpreter and/or cultural mediator required")
                                                           )
                                         ),
                           ),
                     Field("home_help", "boolean",
                           label = T("Home Help"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Home Help"),
                                                           T("Evacuee requiring dedicated assistance at home")
                                                           )
                                         ),
                           ),
                     Field("distance_from_shelter", "integer",
                           label = T("Working Distance from Shelter (km)")
                           ),
                     Field("job_lost_by_event", "boolean",
                           label = T("Job lost by event")
                           ),
                     Field("domestic_animal", "boolean",
                           label = T("With Domestic Animals")
                           ),
                     Field("car_available", "boolean",
                           label = T("Car available")
                           ),
                     s3_comments(),
                     *s3_meta_fields())

    # -------------------------------------------------------------------------
    @staticmethod
    def evr_case_onaccept(form):
        """
            After DB I/O, check the correctness of fiscal code (ITALY)
            @ToDo: The function should be made a deployment_setting when anyone else wishes to use this module
        """

        # Initialization
        fiscal_code = form.vars.fiscal_code
        if fiscal_code == "" or fiscal_code == None:
            return
        fiscal_code = fiscal_code.upper()

        MALE = 3
        CONSONANTS = "BCDFGHJKLMNPQRSTVWXYZ"
        VOWELS = "AEIOU"
        MONTHS = "ABCDEHLMPRST"
        T = current.T

        ptable = current.s3db.pr_person
        query = (form.vars.person_id == ptable.id)
        row = current.db(query).select(ptable.first_name,
                                       ptable.last_name,
                                       ptable.date_of_birth,
                                       ptable.gender,
                                       limitby = (0, 1)
                                       ).first()
        name = row.first_name.upper()
        surname = row.last_name.upper()
        date_of_birth = row.date_of_birth
        year = date_of_birth.year
        month = date_of_birth.month
        day = date_of_birth.day
        gender = row.gender

        # Check surname
        cons = ""
        for c in surname:
            if c in CONSONANTS:
                cons += c
        vow = ""
        for c in surname:
            if c in VOWELS:
                vow += c
        chars = cons + vow
        if len(chars) < 3:
            chars += ["X", "X"]
        if fiscal_code[:3] != chars[0:3].upper():
            current.response.warning = T("Warning: fiscal code isn't \
                                         consistent with personal data")
            return

        # Check name
        cons = ""
        for c in name:
            if c in CONSONANTS:
                cons += c
        if len(cons) > 3:
            chars = cons[0] + cons[2] + cons[3]
        else:
            vow = ""
            for c in name:
                if c in VOWELS:
                    vow += c
            chars = cons + vow
            if len(chars) < 3:
                chars += ["X", "X"]
        if fiscal_code[3:6] != chars[0:3].upper():
            current.response.warning = T("Warning: fiscal code isn't \
                                         consistent with personal data")
            return

        # Check date of birth and gender
        year = str(year)[2:4] # Convert to string and take only the last two elements
        if fiscal_code[6:8] != year or \
                        fiscal_code[8] != MONTHS[month - 1]:
            current.response.warning = T("Warning: fiscal code isn't \
                                         consistent with personal data")
            return
        if gender == MALE:
            birthday_in_cf = fiscal_code[9:11]
            if not birthday_in_cf.isdigit():
                current.response.warning = T("Warning: fiscal code isn't \
                                             consistent with personal data")
                return
            else:
                birthday_in_cf = int(birthday_in_cf)
                if birthday_in_cf != day:
                    current.response.warning = T("Warning: fiscal code isn't \
                                                 consistent with personal data")
                    return
        else: # if gender == FEMALE
            if fiscal_code[9:11] != str(day + 40):
                current.response.warning = T("Warning: fiscal code isn't \
                                             consistent with personal data")
                return

        return

# =============================================================================
def evr_rheader(r):
    """
        EVR Resource Headers

        @param r: the S3Request
    """

    T = current.T
    settings = current.deployment_settings

    if r.representation != "html" or not r.record:
        return None

    resourcename = r.name
    rheader_fields = None

    if resourcename == "person":

        tabs = [(T("Person"), None),
                (T("Addresses"), "address"),
                (T("Contact Data"), "contacts"),
                (T("Groups"), "group_membership"),
                # these can be hidden since inline in the main form,
                # but can enabled to verify the functionality:
                #(T("Identity Documents"), "identity"),
                #(T("Case Details"), "case"),
                (T("Images"), "image"),
                (T("Medical Information"), "medical_details"),
                (T("Socio-Economic Background"), "background"),
                ]
        if settings.get_evr_show_physical_description():
            tabs.append((T("Physical Description"), "physical_description"))

        if settings.has_module("cr"):
            tabs.append((T("Shelter Registration"), "shelter_registration"))

        rheader_fields = [["first_name", "last_name"],
                          ["date_of_birth"],
                          ]

        # Show profile picture in rheader
        itable = current.s3db.pr_image
        query = (itable.pe_id == r.record.pe_id) & \
                (itable.profile == True)
        image = current.db(query).select(itable.image,
                                        limitby=(0, 1)).first()
        if image:
            image = itable.image.represent(image.image)
        else:
            image = A(IMG(_src=URL(c="static", f="img", args="blank-user.gif"),
                          _height=60,
                          _title=T("No image available")),
                      _class="th",
                      _href=URL(f="person", args=[r.id, "image", "create"]),
                      )

        return DIV(DIV(image, _style="float:left"),
                   S3ResourceHeader(rheader_fields, tabs)(r))

    elif resourcename == "group":

        tabs = [("Group Details", None),
                (T("Contact Data"), "contact"),
                (T("Members"), "group_membership"),
                ]

        # Show "Add Members" tab only when we action it explicitly
        # (=> from action-button in the group members list)
        if r.method == "add_members":
            tabs.append((T("Add Members"), "add_members"))

        rheader_fields = [["name"],
                          ["description"],
                          ]

        return S3ResourceHeader(rheader_fields, tabs)(r)

    return None

# =============================================================================
class evr_AddGroupMembers(S3Method):
    """
        Custom method to select multiple persons from a filtered list
        and add them to a group
    """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Entry point for REST controller

            @param r: the S3Request
            @param attr: dictionary of parameters for the method handler

            @return: output object to send to the view
        """

        # Add button "Add Members" to members tab
        if r.http in ("GET", "POST"):
            if r.representation == "html" and r.id or \
               r.representation == "aadata":
                return self.add_members(r, **attr)
            else:
                r.error(415, current.ERROR.BAD_FORMAT)
        else:
            r.error(405, current.ERROR.BAD_METHOD)

    # -------------------------------------------------------------------------
    def add_members(self, r, **attr):
        """
            Add-members action: renders a filtered multi-select datatable
            form, and creates group_memberships on POST

            @param r: the S3Request
            @param attr: dictionary of parameters for the method handler

            @return: output object to send to the view
        """

        T = current.T
        db = current.db
        s3db = current.s3db

        unaffiliated = ((S3FieldSelector("group_membership.id") == None) & \
                        (S3FieldSelector("case.id") != None))

        if r.http == "POST":
            # Form submission

            group_id = r.id

            added = 0
            post_vars = r.post_vars
            if all([name in post_vars
                    for name in ("add", "selected", "mode")]):

                # Get selection
                selected = post_vars.selected
                if selected:
                    selected = selected.split(",")
                else:
                    selected = []

                # Handle exclusion filter
                if post_vars.mode == "Exclusive":
                    if "filterURL" in post_vars:
                        filters = S3URLQuery.parse_url(post_vars.filterURL)
                    else:
                        filters = None
                    query = unaffiliated & \
                            (~(S3FieldSelector("id").belongs(selected)))
                    resource = s3db.resource("pr_person",
                                             filter=query,
                                             vars=filters)
                    rows = resource.select(["id"], as_rows=True)
                    selected = [str(row.id) for row in rows]

                # Avoid duplicates
                gtable = s3db.pr_group_membership
                query = (gtable.group_id == group_id) & \
                        (gtable.person_id.belongs(selected)) & \
                        (gtable.deleted != True)
                rows = db(query).select(gtable.person_id)
                skip = set(row.person_id for row in rows)

                # Add new group members
                for record_id in selected:
                    try:
                        person_id = int(record_id.strip())
                    except ValueError:
                        continue
                    if person_id in skip:
                        continue
                    gtable.insert(group_id = group_id,
                                  person_id = person_id,
                                  )
                    added += 1

            # Confirmation message (in session because we redirect)
            session = current.session
            if not selected:
                session.warning = T("No Persons Selected!")
            else:
                session.confirmation = T("%(number)s Members added to Group") % \
                                        dict(number=added)

            # Go back to list of existing group members
            redirect(r.url(method = "",
                           id = group_id,
                           component = "group_membership"))

        else:
            resource = s3db.resource("pr_person", vars=r.get_vars)
            resource.add_filter(unaffiliated)
            get_config = resource.get_config

            # Filter widgets
            filter_widgets = get_config("filter_widgets", [])
            filter_widgets.append(S3DateFilter("created_on",
                                               label = T("Registered on"),
                                               )
                                  )

            # List fields
            list_fields = ["id",
                           "first_name",
                           "last_name",
                           "gender",
                           "date_of_birth",
                           ]

            response = current.response

            # Data table boundaries
            get_vars = self.request.get_vars
            if "displayStart" in get_vars:
                start = int(get_vars["displayStart"])
            else:
                start = None
            if "pageLength" in get_vars:
                display_length = int(get_vars["pageLength"])
            else:
                display_length = response.s3.ROWSPERPAGE
            limit = 4 * display_length

            # Apply datatable filter and sorting
            totalrows = resource.count()
            filter, orderby, left = resource.datatable_filter(list_fields, get_vars)
            if not orderby:
                # Most recently created records on top
                orderby = "pr_person.created_on desc"
            resource.add_filter(filter)

            # Retrieve the data
            data = resource.select(list_fields,
                                   start=start,
                                   limit=limit,
                                   orderby=orderby,
                                   left=left,
                                   count=True,
                                   represent=True)

            filteredrows = data["numrows"]

            # Generate the datatable
            dt = S3DataTable(data["rfields"], data["rows"])
            dt_id = "datatable"

            # Bulk Action
            dt_bulk_actions = [(T("Add as Group Members"), "add")]

            if r.representation == "html":
                # Page load

                # Custom open-button, no delete-option
                resource.configure(deletable = False)
                open_url = URL(f = "person", args = ["[id]"])
                S3CRUD.action_buttons(r,
                                      deletable = False,
                                      read_url = open_url,
                                      update_url = open_url)

                # Need no export formats (as this is a form)
                response.s3.no_formats = True

                # Data table (items)
                items = dt.html(totalrows,
                                filteredrows,
                                dt_id,
                                dt_ajax_url=URL(c="evr",
                                                f="group",
                                                args=["add_members"],
                                                vars={},
                                                extension="aadata",
                                                ),
                                dt_bulk_actions=dt_bulk_actions,
                                dt_pageLength=display_length,
                                dt_pagination="true",
                                dt_searching="false",
                                )

                resource.configure(deletable = False)

                # Filter form
                if filter_widgets:

                    # Where to retrieve filtered data from:
                    _vars = resource.crud._remove_filters(r.get_vars)
                    filter_submit_url = r.url(vars=_vars)

                    # Where to retrieve updated filter options from:
                    filter_ajax_url = URL(f="person",
                                          args=["filter.options"],
                                          vars={},
                                          )

                    # Define filter form
                    filter_clear = get_config("filter_clear", True)
                    filter_submit = get_config("filter_submit", True)
                    filter_form = S3FilterForm(filter_widgets,
                                               clear=filter_clear,
                                               submit=filter_submit,
                                               ajax=True,
                                               url=filter_submit_url,
                                               ajaxurl=filter_ajax_url,
                                               _class="filter-form",
                                               _id="datatable-filter-form",
                                               )

                    # Render filter form
                    fresource = s3db.resource(resource.tablename)
                    alias = resource.alias if r.component else None
                    ff = filter_form.html(fresource,
                                          r.get_vars,
                                          target="datatable",
                                          alias=alias)
                else:
                    ff = ""

                output = dict(items = items,
                              title = T("Add Members to Group"),
                              addheader = "%s:" % T("Select People to add them to the Group"),
                              list_filter_form = ff,
                              )
                response.view = "list_filter.html"
                return output

            else:
                # Ajax refresh
                if "draw" in get_vars:
                    echo = int(get_vars.draw)
                else:
                    echo = None
                items = dt.json(totalrows,
                                filteredrows,
                                dt_id,
                                echo,
                                dt_bulk_actions=dt_bulk_actions,
                                )

                response.headers["Content-Type"] = "application/json"
                return items

# END =========================================================================
