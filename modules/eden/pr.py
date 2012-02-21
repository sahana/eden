# -*- coding: utf-8 -*-

""" Sahana Eden Person Registry Model

    @author: Dominic König <dominic[at]aidiq.com>

    @copyright: 2009-2012 (c) Sahana Software Foundation
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

__all__ = ["S3PersonEntity",
           "S3PersonModel",
           "S3GroupModel",
           "S3ContactModel",
           "S3PersonComponents",
           "S3SavedSearch",
           "S3PersonPresence",
           "S3PersonDescription",
           "pr_pentity_represent",
           "pr_person_represent",
           "pr_person_comment",
           "pr_rheader"]

from gluon import *
from gluon.dal import Row
from gluon.storage import Storage
from gluon.sqlhtml import RadioWidget
from ..s3 import *

# =============================================================================
class S3PersonEntity(S3Model):
    """ Person Super-Entity """

    names = ["pr_pentity",
             "pr_affiliation",
             "pr_role",
             "pr_pe_label"]

    def model(self):

        db = current.db
        T = current.T
        s3 = current.response.s3

        define_table = self.define_table
        super_entity = self.super_entity
        super_link = self.super_link
        super_key = self.super_key
        configure = self.configure
        add_component = self.add_component

        # ---------------------------------------------------------------------
        # Person Super-Entity
        #
        pe_types = Storage(pr_person = T("Person"),
                           pr_group = T("Group"),
                           org_organisation = T("Organization"),
                           org_office = T("Office"),
                           dvi_body = T("Body"))

        tablename = "pr_pentity"
        table = super_entity(tablename, "pe_id", pe_types,
                             Field("pe_label", length=128))

        # Search method
        pentity_search = S3PentitySearch(name = "pentity_search_simple",
                                         label = T("Name and/or ID"),
                                         comment = T(""),
                                         field = ["pe_label"])

        pentity_search.pentity_represent = pr_pentity_represent

        # Resource configuration
        configure(tablename,
                  editable=False,
                  deletable=False,
                  listadd=False,
                  search_method=pentity_search)

        # Reusable fields
        pr_pe_label = S3ReusableField("pe_label", length=128,
                                      label = T("ID Tag Number"),
                                      requires = IS_NULL_OR(IS_NOT_ONE_OF(db,
                                                            "pr_pentity.pe_label")))

        # Components
        pe_id = super_key(table)
        add_component("pr_contact_emergency", pr_pentity=pe_id)
        add_component("pr_address", pr_pentity=pe_id)
        add_component("pr_pimage", pr_pentity=pe_id)
        add_component("pr_contact", pr_pentity=pe_id)
        add_component("pr_note", pr_pentity=pe_id)
        add_component("pr_physical_description",
                      pr_pentity=dict(joinby=pe_id,
                                      multiple=False))
        add_component("dvi_identification",
                      pr_pentity=dict(joinby=pe_id,
                                      multiple=False))
        add_component("dvi_effects",
                      pr_pentity=dict(joinby=pe_id,
                                      multiple=False))
        add_component("dvi_checklist",
                      pr_pentity=dict(joinby=pe_id,
                                      multiple=False))
        # Map Configs
        #   - Personalised configurations
        #   - OU configurations (Organisation/Branch/Facility/Team)
        add_component("gis_config",
                      pr_pentity=dict(joinby=pe_id,
                                      multiple=False))

        # ---------------------------------------------------------------------
        # Person <-> User
        #
        utable = current.auth.settings.table_user
        tablename = "pr_person_user"
        table = define_table(tablename,
                             super_link("pe_id", "pr_pentity"),
                             Field("user_id", utable),
                             *s3.meta_fields())

        # ---------------------------------------------------------------------
        # Affiliation link table
        #
        tablename = "pr_affiliation"
        table = define_table(tablename,
                             Field("hierarchy"),
                             Field("parent",
                                   "reference pr_pentity",
                                   requires = IS_ONE_OF(db, "pr_pentity.pe_id",
                                                        pr_pentity_represent,
                                                        sort=True),
                                   represent = pr_pentity_represent),
                             Field("child",
                                   "reference pr_pentity",
                                   requires = IS_ONE_OF(db, "pr_pentity.pe_id",
                                                        pr_pentity_represent,
                                                        sort=True),
                                   represent = pr_pentity_represent),
                             *s3.meta_fields())

        # ---------------------------------------------------------------------
        # Role
        #
        tablename = "pr_role"
        table = define_table(tablename,
                             super_link("pe_id", "pr_pentity",
                                        readable=True,
                                        writable=True),
                             Field("hierarchy"),
                             Field("role"),
                             Field("affiliation",
                                   "reference pr_affiliation",
                                   requires = IS_EMPTY_OR(IS_ONE_OF(db,
                                                "pr_affiliation.id",
                                                self.pr_affiliation_represent,
                                                sort=True)),
                                   represent = self.pr_affiliation_represent),
                             *s3.meta_fields())

        table.pe_id.requires = IS_ONE_OF(db, "pr_pentity.pe_id",
                                         pr_pentity_represent, sort=True)
        table.pe_id.represent = pr_pentity_represent

        # ---------------------------------------------------------------------
        # Return model-global names to response.s3
        #
        return Storage(
            pr_pe_label=pr_pe_label,
        )

    # -------------------------------------------------------------------------
    @staticmethod
    def pr_affiliation_represent(affiliation_id):

        db = current.db
        s3db = current.s3db

        if isinstance(affiliation_id, Row):
            affiliation = affiliation_id
        else:
            atable = s3db.pr_affiliation
            query = (atable.deleted != True) & \
                    (atable.id == affiliation_id)
            affiliation = db(query).select(atable.parent, atable.child,
                                           limitby=(0, 1)).first()
        if affiliation:
            return "%s => %s" % (pr_pentity_represent(affiliation.child),
                                 pr_pentity_represent(affiliation.parent))
        else:
            return current.messages.NONE

# =============================================================================
class S3PersonModel(S3Model):
    """ Persons and Groups """

    names = ["pr_person",
             "pr_person_user",
             "pr_gender",
             "pr_gender_opts",
             "pr_age_group",
             "pr_age_group_opts",
             "pr_person_id",
            ]

    def model(self):

        T = current.T
        db = current.db
        request = current.request
        s3 = current.response.s3
        gis = current.gis
        settings = current.deployment_settings

        pe_label = self.pr_pe_label

        location_id = self.gis_location_id

        messages = current.messages
        NONE = messages.NONE
        UNKNOWN_OPT = messages.UNKNOWN_OPT
        SELECT_LOCATION = messages.SELECT_LOCATION

        define_table = self.define_table
        super_link = self.super_link
        add_component = self.add_component

        # ---------------------------------------------------------------------
        # Person
        #
        pr_gender_opts = {
            1:"",
            2:T("female"),
            3:T("male")
        }
        pr_gender = S3ReusableField("gender", "integer",
                                    requires = IS_IN_SET(pr_gender_opts, zero=None),
                                    default = 1,
                                    label = T("Gender"),
                                    represent = lambda opt: \
                                                pr_gender_opts.get(opt, UNKNOWN_OPT))

        pr_age_group_opts = {
            1:T("unknown"),
            2:T("Infant (0-1)"),
            3:T("Child (2-11)"),
            4:T("Adolescent (12-20)"),
            5:T("Adult (21-50)"),
            6:T("Senior (50+)")
        }
        pr_age_group = S3ReusableField("age_group", "integer",
                                       requires = IS_IN_SET(pr_age_group_opts,
                                                            zero=None),
                                       default = 1,
                                       label = T("Age Group"),
                                       represent = lambda opt: \
                                                   pr_age_group_opts.get(opt,
                                                                         UNKNOWN_OPT))

        pr_marital_status_opts = {
            1:T("unknown"),
            2:T("single"),
            3:T("married"),
            4:T("separated"),
            5:T("divorced"),
            6:T("widowed"),
            9:T("other")
        }

        pr_religion_opts = settings.get_L10n_religions()

        pr_impact_tags = {
            1: T("injured"),
            4: T("diseased"),
            2: T("displaced"),
            5: T("separated from family"),
            3: T("suffered financial losses")
        }

        if settings.get_L10n_mandatory_lastname():
            last_name_validate = IS_NOT_EMPTY(error_message = T("Please enter a last name"))
        else:
            last_name_validate = None

        s3_date_format = settings.get_L10n_date_format()

        tablename = "pr_person"
        table = define_table(tablename,
                             super_link("pe_id", "pr_pentity"),
                             super_link("track_id", "sit_trackable"),
                             location_id(readable=False,
                                         writable=False),       # base location
                             pe_label(comment = DIV(DIV(_class="tooltip",
                                                        _title="%s|%s" % (T("ID Tag Number"),
                                                                          T("Number or Label on the identification tag this person is wearing (if any)."))))),
                             Field("missing", "boolean",
                                   readable=False,
                                   writable=False,
                                   default=False,
                                   represent = lambda missing: \
                                               (missing and ["missing"] or [""])[0]),
                             Field("volunteer", "boolean",
                                   readable=False,
                                   writable=False,
                                   default=False),
                             Field("first_name", notnull=True,
                                   length=64, # Mayon Compatibility
                                   # NB Not possible to have an IS_NAME() validator here
                                   # http://eden.sahanafoundation.org/ticket/834
                                   requires = IS_NOT_EMPTY(error_message = T("Please enter a first name")),
                                   comment =  DIV(_class="tooltip",
                                                  _title="%s|%s" % (T("First name"),
                                                                    T("The first or only name of the person (mandatory)."))),
                                   label = T("First Name")),
                             Field("middle_name",
                                   length=64, # Mayon Compatibility
                                   label = T("Middle Name")),
                             Field("last_name",
                                   length=64, # Mayon Compatibility
                                   label = T("Last Name"),
                                   requires = last_name_validate),
                             Field("initials",
                                   length=8,
                                   label = T("Initials")),
                             Field("preferred_name",
                                   label = T("Preferred Name"),
                                   comment = DIV(DIV(_class="tooltip",
                                                     _title="%s|%s" % (T("Preferred Name"),
                                                                       T("The name to be used when calling for or directly addressing the person (optional).")))),
                                   length=64), # Mayon Compatibility
                             Field("local_name",
                                   label = T("Local Name"),
                                    comment = DIV(DIV(_class="tooltip",
                                                        _title="%s|%s" % (T("Local Name"),
                                                                        T("Name of the person in local language and script (optional)."))))),
                             pr_gender(label = T("Gender")),
                             Field("date_of_birth", "date",
                                   label = T("Date of Birth"),
                                   requires = [IS_EMPTY_OR(IS_DATE_IN_RANGE(
                                                format = s3_date_format,
                                                maximum=request.utcnow.date(),
                                                error_message="%s %%(max)s!" %
                                                              T("Enter a valid date before")))],
                                   widget = S3DateWidget(past=1320,  # Months, so 110 years
                                                         future=0)),
                             pr_age_group(label = T("Age group")),
                             Field("nationality",
                                   requires = IS_NULL_OR(IS_IN_SET_LAZY(
                                                lambda: gis.get_countries(key_type="code"),
                                                zero = SELECT_LOCATION)),
                                   label = T("Nationality"),
                                   comment = DIV(DIV(_class="tooltip",
                                                     _title="%s|%s" % (T("Nationality"),
                                                                       T("Nationality of the person.")))),
                                   represent = lambda code: \
                                               gis.get_country(code, key_type="code") or UNKNOWN_OPT),
                             Field("occupation",
                                   label = T("Profession"),
                                   length=128), # Mayon Compatibility
                             Field("picture", "upload",
                                   autodelete=True,
                                   label = T("Picture"),
                                   requires = IS_EMPTY_OR(IS_IMAGE(maxsize=(800, 800),
                                                                   error_message=T("Upload an image file (bmp, gif, jpeg or png), max. 300x300 pixels!"))),
                                   represent = lambda image: image and \
                                                        DIV(A(IMG(_src=URL(c="default", f="download",
                                                                           args=image),
                                                                  _height=60,
                                                                  _alt=T("View Picture")),
                                                                  _href=URL(c="default", f="download",
                                                                            args=image))) or
                                                            T("No Picture"),
                                   comment = DIV(_class="tooltip",
                                                 _title="%s|%s" % (T("Picture"),
                                                                   T("Upload an image file here.")))),
                             s3.comments(),
                             *(s3.lx_fields() + s3.meta_fields()))

        # CRUD Strings
        ADD_PERSON = current.messages.ADD_PERSON
        LIST_PERSONS = T("List Persons")
        s3.crud_strings[tablename] = Storage(
            title_create = T("Add a Person"),
            title_display = T("Person Details"),
            title_list = LIST_PERSONS,
            title_update = T("Edit Person Details"),
            title_search = T("Search Persons"),
            subtitle_create = ADD_PERSON,
            subtitle_list = T("Persons"),
            label_list_button = LIST_PERSONS,
            label_create_button = ADD_PERSON,
            label_delete_button = T("Delete Person"),
            msg_record_created = T("Person added"),
            msg_record_modified = T("Person details updated"),
            msg_record_deleted = T("Person deleted"),
            msg_list_empty = T("No Persons currently registered"))

        # Search method
        pr_person_search = S3PersonSearch(
                                name="person_search_simple",
                                label=T("Name and/or ID"),
                                comment=T("To search for a person, enter any of the first, middle or last names and/or an ID number of a person, separated by spaces. You may use % as wildcard. Press 'Search' without input to list all persons."),
                                field=["pe_label",
                                       "first_name",
                                       "middle_name",
                                       "last_name",
                                       "local_name",
                                       "identity.value"
                                      ])

        # Resource configuration
        self.configure(tablename,
                       super_entity=("pr_pentity", "sit_trackable"),
                       list_fields = ["id",
                                      "first_name",
                                      "middle_name",
                                      "last_name",
                                      "picture",
                                      "gender",
                                      "age_group",
                                      (T("Organization"), "hrm_human_resource:organisation_id$name")
                                     ],
                       onvalidation=self.pr_person_onvalidation,
                       search_method=pr_person_search,
                       deduplicate=self.person_deduplicate,
                       main="first_name",
                       extra="last_name")

        person_id_comment = pr_person_comment(
                                    T("Person"),
                                    T("Type the first few characters of one of the Person's names."))

        person_id = S3ReusableField("person_id", db.pr_person,
                                    sortby = ["first_name", "middle_name", "last_name"],
                                    requires = IS_NULL_OR(IS_ONE_OF(db, "pr_person.id",
                                                                    pr_person_represent,
                                                                    orderby="pr_person.first_name",
                                                                    sort=True,
                                                                    error_message=T("Person must be specified!"))),
                                    represent = lambda id, row=None: (id and \
                                                   [pr_person_represent(id)] or [NONE])[0],
                                    label = T("Person"),
                                    comment = person_id_comment,
                                    ondelete = "RESTRICT",
                                    widget = S3PersonAutocompleteWidget())

        # Components
        add_component("pr_group_membership", pr_person="person_id")
        add_component("pr_identity", pr_person="person_id")
        add_component("pr_save_search", pr_person="person_id")
        add_component("msg_subscription", pr_person="person_id")

        # Add HR Record as component of Persons
        add_component("hrm_human_resource", pr_person="person_id")

        # Add Skills as components of Persons
        add_component("hrm_certification", pr_person="person_id")
        add_component("hrm_competency", pr_person="person_id")
        add_component("hrm_credential", pr_person="person_id")
        add_component("hrm_experience", pr_person="person_id")
        # @ToDo: Double link table to show the Courses attended?
        add_component("hrm_training", pr_person="person_id")

        # ---------------------------------------------------------------------
        # Return model-global names to response.s3
        #
        return Storage(
            pr_gender = pr_gender,
            pr_gender_opts = pr_gender_opts,
            pr_age_group = pr_age_group,
            pr_age_group_opts = pr_age_group_opts,
            pr_person_id = person_id,
        )

    # -------------------------------------------------------------------------
    @staticmethod
    def pr_person_onvalidation(form):
        """ Onvalidation callback """

        try:
            age = int(form.vars.get("age_group", None))
        except (ValueError, TypeError):
            age = None
        dob = form.vars.get("date_of_birth", None)

        if age and age != 1 and dob:
            now = request.utcnow
            dy = int((now.date() - dob).days / 365.25)
            if dy < 0:
                ag = 1
            elif dy < 2:
                ag = 2
            elif dy < 12:
                ag = 3
            elif dy < 21:
                ag = 4
            elif dy < 51:
                ag = 5
            else:
                ag = 6

            if age != ag:
                form.errors.age_group = T("Age group does not match actual age.")
                return False

        return True

    # -------------------------------------------------------------------------
    @staticmethod
    def person_deduplicate(item):
        """ Import item deduplication """

        db = current.db
        s3db = current.s3db

        # Ignore this processing if the id is set
        if item.id:
            return
        if item.tablename == "pr_person":
            ptable = s3db.pr_person
            ctable = s3db.pr_contact

            # Match by first name and last name, and if given, by email address
            fname = "first_name" in item.data and item.data.first_name
            lname = "last_name" in item.data and item.data.last_name
            if fname and lname:
                # "LIKE" is inappropriate here:
                # E.g. "Fran Boon" would overwrite "Frank Boones"
                #query = (ptable.first_name.lower().like('%%%s%%' % fname.lower())) & \
                        #(ptable.last_name.lower().like('%%%s%%' % lname.lower()))

                # But even an exact name match does not necessarily indicate a
                # duplicate: depending on the scope of the deployment, you could
                # have thousands of people with exactly the same names (or just
                # two of them - and it can already go wrong).
                # We take the email address as additional criterion, however, where
                # person data do not usually contain email addresses you might need
                # to add more/other criteria here
                query = (ptable.first_name.lower() == fname.lower()) & \
                        (ptable.last_name.lower() == lname.lower())
                email = False
                for citem in item.components:
                    if citem.tablename == "pr_contact":
                        if "contact_method" in citem.data and \
                        citem.data.contact_method == "EMAIL":
                            email = citem.data.value
                if email != False:
                    query = query & \
                            (ptable.pe_id == ctable.pe_id) & \
                            (ctable.value.lower() == email.lower())

            else:
                # Try Initials (this is a weak test but works well in small teams)
                initials = "initials" in item.data and item.data.initials
                if not initials:
                    # Nothing we can do
                    return
                query = (ptable.initials.lower() == initials.lower())

            # Look for details on the database
            _duplicate = db(query).select(ptable.id,
                                          limitby=(0, 1)).first()
            if _duplicate:
                item.id = _duplicate.id
                item.data.id = _duplicate.id
                item.method = item.METHOD.UPDATE
                for citem in item.components:
                    citem.method = citem.METHOD.UPDATE

# =============================================================================
class S3GroupModel(S3Model):
    """ Groups """

    names = ["pr_group",
             "pr_group_id",
             "pr_group_represent",
             "pr_group_membership"]

    def model(self):

        T = current.T
        db = current.db
        request = current.request
        s3 = current.response.s3

        person_id = self.pr_person_id

        messages = current.messages
        NONE = messages.NONE
        UNKNOWN_OPT = messages.UNKNOWN_OPT

        # ---------------------------------------------------------------------
        # Group
        #
        pr_group_types = {
            1:T("Family"),
            2:T("Tourist Group"),
            3:T("Relief Team"),
            4:T("other")
        }

        tablename = "pr_group"
        table = self.define_table(tablename,
                                  self.super_link("pe_id", "pr_pentity"),
                                  Field("group_type", "integer",
                                        requires = IS_IN_SET(pr_group_types, zero=None),
                                        default = 4,
                                        label = T("Group Type"),
                                        represent = lambda opt: \
                                                    pr_group_types.get(opt, UNKNOWN_OPT)),
                                  Field("system", "boolean",
                                        default=False,
                                        readable=False,
                                        writable=False),
                                  Field("name",
                                        label=T("Group Name"),
                                        requires = IS_NOT_EMPTY()),
                                  Field("description",
                                        label=T("Group Description")),
                                  s3.comments(),
                                  *s3.meta_fields())

        # Field configuration
        table.description.comment = DIV(DIV(_class="tooltip",
                                            _title="%s|%s" % (T("Group description"),
                                                              T("A brief description of the group (optional)"))))

        # CRUD Strings
        ADD_GROUP = T("Add Group")
        LIST_GROUPS = T("List Groups")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_GROUP,
            title_display = T("Group Details"),
            title_list = LIST_GROUPS,
            title_update = T("Edit Group"),
            title_search = T("Search Groups"),
            subtitle_create = T("Add New Group"),
            subtitle_list = T("Groups"),
            label_list_button = LIST_GROUPS,
            label_create_button = ADD_GROUP,
            label_delete_button = T("Delete Group"),
            msg_record_created = T("Group added"),
            msg_record_modified = T("Group updated"),
            msg_record_deleted = T("Group deleted"),
            msg_list_empty = T("No Groups currently registered"))

        # Resource configuration
        self.configure(tablename,
                       super_entity="pr_pentity",
                       main="name",
                       extra="description")

        # Reusable fields
        group_represent = lambda id: (id and [db.pr_group[id].name] or [NONE])[0]
        group_id = S3ReusableField("group_id", db.pr_group,
                                   sortby="name",
                                   requires = IS_NULL_OR(IS_ONE_OF(db, "pr_group.id",
                                                                   "%(id)s: %(name)s",
                                                                   filterby="system",
                                                                   filter_opts=(False,))),
                                   represent = group_represent,
                                    comment = \
                                        DIV(A(s3.crud_strings.pr_group.label_create_button,
                                              _class="colorbox",
                                              _href=URL(c="pr", f="group", args="create",
                                                        vars=dict(format="popup")),
                                              _target="top",
                                              _title=s3.crud_strings.pr_group.label_create_button),
                                            DIV(DIV(_class="tooltip",
                                                    _title="%s|%s" % (T("Create Group Entry"),
                                                                      T("Create a group entry in the registry."))))),
                                   ondelete = "RESTRICT")

        # Components
        self.add_component("pr_group_membership", pr_group="group_id")

        # ---------------------------------------------------------------------
        # Group membership
        #
        resourcename = "group_membership"
        tablename = "pr_group_membership"
        table = self.define_table(tablename,
                                  group_id(label = T("Group")),
                                  person_id(label = T("Person")),
                                  Field("group_head", "boolean",
                                        label = T("Group Head"),
                                        default=False),
                                  Field("description",
                                        label = T("Description")),
                                  s3.comments(),
                                  *s3.meta_fields())

        # Field configuration
        table.group_head.represent = lambda group_head: \
                                        (group_head and [T("yes")] or [""])[0]

        # CRUD strings
        request = current.request
        if request.function in ("person", "group_membership"):
            s3.crud_strings[tablename] = Storage(
                title_create = T("Add Membership"),
                title_display = T("Membership Details"),
                title_list = T("Memberships"),
                title_update = T("Edit Membership"),
                title_search = T("Search Membership"),
                subtitle_create = T("Add New Membership"),
                subtitle_list = T("Current Memberships"),
                label_list_button = T("List All Memberships"),
                label_create_button = T("Add Membership"),
                label_delete_button = T("Delete Membership"),
                msg_record_created = T("Membership added"),
                msg_record_modified = T("Membership updated"),
                msg_record_deleted = T("Membership deleted"),
                msg_list_empty = T("No Memberships currently registered"))

        elif request.function == "group":
            s3.crud_strings[tablename] = Storage(
                title_create = T("Add Member"),
                title_display = T("Membership Details"),
                title_list = T("Group Members"),
                title_update = T("Edit Membership"),
                title_search = T("Search Member"),
                subtitle_create = T("Add New Member"),
                subtitle_list = T("Current Group Members"),
                label_list_button = T("List Members"),
                label_create_button = T("Add Group Member"),
                label_delete_button = T("Delete Membership"),
                msg_record_created = T("Group Member added"),
                msg_record_modified = T("Membership updated"),
                msg_record_deleted = T("Membership deleted"),
                msg_list_empty = T("No Members currently registered"))

        # Resource configuration
        self.configure(tablename,
                       list_fields=["id",
                                    "group_id",
                                    "person_id",
                                    "group_head",
                                    "description"
                                   ])

        # ---------------------------------------------------------------------
        # Return model-global names to response.s3
        #
        return Storage(
            pr_group_id = group_id,
            pr_group_represent = group_represent
        )

# =============================================================================
class S3ContactModel(S3Model):
    """ Person Contacts """

    names = ["pr_contact",
             "pr_contact_emergency"
             ]

    def model(self):

        T = current.T
        db = current.db
        msg = current.msg
        request = current.request
        s3 = current.response.s3

        UNKNOWN_OPT = current.messages.UNKNOWN_OPT

        comments = s3.comments
        define_table = self.define_table
        meta_fields = s3.meta_fields
        super_link = self.super_link

        # ---------------------------------------------------------------------
        # Contact
        #
        # @ToDo: Provide widgets which can be dropped into the main person form to have
        #        the relevant ones for that deployment/context collected on that same
        #        form
        #
        contact_methods = msg.CONTACT_OPTS

        tablename = "pr_contact"
        table = define_table(tablename,
                             super_link("pe_id", "pr_pentity"),
                             Field("contact_method",
                                   length=32,
                                   requires = IS_IN_SET(contact_methods,
                                                        zero=None),
                                   default = "SMS",
                                   label = T("Contact Method"),
                                   represent = lambda opt: \
                                               contact_methods.get(opt, UNKNOWN_OPT)),
                             Field("value",
                                   label= T("Value"),
                                   notnull=True,
                                   requires = IS_NOT_EMPTY()),
                             Field("priority", "integer",
                                   label= T("Priority"),
                                   comment = DIV(_class="tooltip",
                                                 _title="%s|%s" % (T("Priority"),
                                                                   T("What order to be contacted in."))),
                                   requires = IS_IN_SET(range(1, 10), zero=None)),
                             comments(),
                             *meta_fields())

        # Field configuration
        table.pe_id.requires = IS_ONE_OF(db, "pr_pentity.pe_id",
                                         pr_pentity_represent,
                                         orderby="instance_type",
                                         filterby="instance_type",
                                         filter_opts=("pr_person", "pr_group"))

        # CRUD Strings
        s3.crud_strings[tablename] = Storage(
            title_create = T("Add Contact Information"),
            title_display = T("Contact Details"),
            title_list = T("Contact Information"),
            title_update = T("Edit Contact Information"),
            title_search = T("Search Contact Information"),
            subtitle_create = T("Add Contact Information"),
            subtitle_list = T("Contact Information"),
            label_list_button = T("List Contact Information"),
            label_create_button = T("Add Contact Information"),
            label_delete_button = T("Delete Contact Information"),
            msg_record_created = T("Contact Information Added"),
            msg_record_modified = T("Contact Information Updated"),
            msg_record_deleted = T("Contact Information Deleted"),
            msg_list_empty = T("No contact information available"))

        # Resource configuration
        self.configure(tablename,
                       onvalidation=self.contact_onvalidation,
                       deduplicate=self.contact_deduplicate,
                       list_fields=["id",
                                    "contact_method",
                                    "value",
                                    "priority",
                                   ])

        # ---------------------------------------------------------------------
        # Emergency Contact Information
        #
        tablename = "pr_contact_emergency"
        table = define_table(tablename,
                             super_link("pe_id", "pr_pentity"),
                             Field("name",
                                   label= T("Name")),
                             Field("relationship",
                                   label= T("Relationship")),
                             Field("phone",
                                   label = T("Phone"),
                                   requires = IS_NULL_OR(s3_phone_requires)),
                             comments(),
                             *meta_fields())

        # ---------------------------------------------------------------------
        # Return model-global names to response.s3
        #
        return Storage(
        )

    # -------------------------------------------------------------------------
    @staticmethod
    def contact_onvalidation(form):
        """ Contact form validation """

        if form.vars.contact_method == "EMAIL":
            email, error = IS_EMAIL()(form.vars.value)
            if error:
                form.errors.value = T("Enter a valid email")
        return False

    # -------------------------------------------------------------------------
    @staticmethod
    def contact_deduplicate(item):
        """ Contact information de-duplication """

        db = current.db

        if item.id:
            return
        if item.tablename == "pr_contact":
            table = item.table
            pe_id = item.data.get("pe_id", None)
            contact_method = item.data.get("contact_method", None)
            value = item.data.get("value", None)

            if pe_id is None:
                return

            query = (table.pe_id == pe_id) & \
                    (table.contact_method == contact_method) & \
                    (table.value == value) & \
                    (table.deleted != True)
            duplicate = db(query).select(table.id,
                                         limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE
        return

# =============================================================================
class S3PersonComponents(S3Model):
    """ Addresses, Images and Identities for Persons """

    names = ["pr_address",
             "pr_pimage",
             "pr_identity"]

    def model(self):

        T = current.T
        db = current.db
        request = current.request
        s3 = current.response.s3

        person_id = self.pr_person_id
        location_id = self.gis_location_id

        UNKNOWN_OPT = current.messages.UNKNOWN_OPT

        # Shortcuts
        comments = s3.comments
        configure = self.configure
        crud_strings = s3.crud_strings
        define_table = self.define_table
        meta_fields = s3.meta_fields
        super_link = self.super_link

        # ---------------------------------------------------------------------
        # Address
        #
        pr_address_type_opts = {
            1:T("Home Address"),
            2:T("Office Address"),
            3:T("Holiday Address"),
            9:T("other")
        }

        tablename = "pr_address"
        table = define_table(tablename,
                             super_link("pe_id", "pr_pentity"),
                             Field("type", "integer",
                                   requires = IS_IN_SET(pr_address_type_opts, zero=None),
                                   widget = RadioWidget.widget,
                                   default = 1,
                                   label = T("Address Type"),
                                   represent = lambda opt: \
                                               pr_address_type_opts.get(opt, UNKNOWN_OPT)),
                             location_id(),
                             comments(),
                             *(s3.address_fields() + meta_fields()))

        table.pe_id.requires = IS_ONE_OF(db, "pr_pentity.pe_id",
                                         pr_pentity_represent,
                                         orderby="instance_type",
                                         filterby="instance_type",
                                         filter_opts=("pr_person", "pr_group"))

        # Field configuration
        if not self.settings.get_gis_building_name():
            table.building_name.readable = False

        # CRUD Strings
        ADD_ADDRESS = T("Add Address")
        LIST_ADDRESS = T("List of addresses")
        crud_strings[tablename] = Storage(
            title_create = ADD_ADDRESS,
            title_display = T("Address Details"),
            title_list = LIST_ADDRESS,
            title_update = T("Edit Address"),
            title_search = T("Search Addresses"),
            subtitle_create = T("Add New Address"),
            subtitle_list = T("Addresses"),
            label_list_button = LIST_ADDRESS,
            label_create_button = ADD_ADDRESS,
            msg_record_created = T("Address added"),
            msg_record_modified = T("Address updated"),
            msg_record_deleted = T("Address deleted"),
            msg_list_empty = T("There is no address for this person yet. Add new address."))

        # Resource configuration
        configure(tablename,
                  onaccept=self.address_onaccept,
                  onvalidation=s3.address_onvalidation,
                  list_fields = ["id",
                                 "type",
                                 "address",
                                 "postcode",
                                 #"L4",
                                 "L3",
                                 "L2",
                                 "L1",
                                 "L0"
                                ])

        # ---------------------------------------------------------------------
        # Image
        #
        pr_pimage_type_opts = {
            1:T("Photograph"),
            2:T("Sketch"),
            3:T("Fingerprint"),
            4:T("X-Ray"),
            5:T("Document Scan"),
            9:T("other")
        }

        tablename = "pr_pimage"
        table = define_table(tablename,
                             super_link("pe_id", "pr_pentity"),
                             Field("type", "integer",
                                   requires = IS_IN_SET(pr_pimage_type_opts, zero=None),
                                   default = 1,
                                   label = T("Image Type"),
                                   represent = lambda opt: pr_pimage_type_opts.get(opt,
                                                                                   UNKNOWN_OPT)),
                             Field("title", label=T("Title"),
                                   requires = IS_NOT_EMPTY(),
                                   comment = DIV(_class="tooltip",
                                                 _title="%s|%s" % (T("Title"),
                                                                   T("Specify a descriptive title for the image.")))),
                             Field("image", "upload", autodelete=True,
                                   represent = lambda image: image and \
                                              DIV(A(IMG(_src=URL(c="default", f="download",
                                                                  args=image),
                                                         _height=60, _alt=T("View Image")),
                                                         _href=URL(c="default", f="download",
                                                                   args=image))) or T("No Image"),
                                   comment =  DIV(_class="tooltip",
                                                  _title="%s|%s" % (T("Image"),
                                                                    T("Upload an image file here. If you don't upload an image file, then you must specify its location in the URL field.")))),
                             Field("url",
                                   label = T("URL"),
                                   represent = lambda url: url and \
                                                           DIV(A(IMG(_src=url, _height=60), _href=url)) or T("None"),
                                   comment = DIV(_class="tooltip",
                                                 _title="%s|%s" % (T("URL"),
                                                                   T("The URL of the image file. If you don't upload an image file, then you must specify its location here.")))),
                             Field("description",
                                   label=T("Description"),
                                   comment = DIV(_class="tooltip",
                                                 _title="%s|%s" % (T("Description"),
                                                                   T("Give a brief description of the image, e.g. what can be seen where on the picture (optional).")))),
                             comments(),
                             *meta_fields())

        # CRUD Strings
        LIST_IMAGES = T("List Images")
        crud_strings[tablename] = Storage(
            title_create = T("Image"),
            title_display = T("Image Details"),
            title_list = LIST_IMAGES,
            title_update = T("Edit Image Details"),
            title_search = T("Search Images"),
            subtitle_create = T("Add New Image"),
            subtitle_list = T("Images"),
            label_list_button = LIST_IMAGES,
            label_create_button = T("Add Image"),
            label_delete_button = T("Delete Image"),
            msg_record_created = T("Image added"),
            msg_record_modified = T("Image updated"),
            msg_record_deleted = T("Image deleted"),
            msg_list_empty = T("No Images currently registered"))

        # Resource configuration
        configure(tablename,
                  onvalidation = self.pr_pimage_onvalidation,
                  mark_required = ["url", "image"],
                  list_fields=["id",
                               "title",
                               "type",
                               "image",
                               "url",
                               "description"
                              ])

        # ---------------------------------------------------------------------
        # Identity
        #
        # http://docs.oasis-open.org/emergency/edxl-have/cs01/xPIL-types.xsd
        # <xs:simpleType name="DocumentTypeList">
        #  <xs:enumeration value="Passport"/>
        #  <xs:enumeration value="DriverLicense"/>
        #  <xs:enumeration value="CreditCard"/>
        #  <xs:enumeration value="BankCard"/>
        #  <xs:enumeration value="KeyCard"/>
        #  <xs:enumeration value="AccessCard"/>
        #  <xs:enumeration value="IdentificationCard"/>
        #  <xs:enumeration value="Certificate"/>
        #  <xs:enumeration value="MileageProgram"/>
        #
        pr_id_type_opts = {
            1:T("Passport"),
            2:T("National ID Card"),
            3:T("Driving License"),
            #4:T("Credit Card"),
            99:T("other")
        }

        tablename = "pr_identity"
        table = define_table(tablename,
                             person_id(label = T("Person")),
                             Field("type", "integer",
                                   requires = IS_IN_SET(pr_id_type_opts, zero=None),
                                   default = 1,
                                   label = T("ID type"),
                                   represent = lambda opt: \
                                               pr_id_type_opts.get(opt,
                                                                   UNKNOWN_OPT)),
                             Field("value"),
                             Field("description"),
                             Field("country_code", length=4),
                             Field("ia_name", label = T("Issuing Authority")),
                             #Field("ia_subdivision"), # Name of issuing authority subdivision
                             #Field("ia_code"), # Code of issuing authority (if any)
                             comments(),
                             *meta_fields())

        # Field configuration
        table.value.requires = [IS_NOT_EMPTY(),
                                IS_NOT_ONE_OF(db, "%s.value" % tablename)]

        # CRUD Strings
        ADD_IDENTITY = T("Add Identity")
        crud_strings[tablename] = Storage(
            title_create = ADD_IDENTITY,
            title_display = T("Identity Details"),
            title_list = T("Known Identities"),
            title_update = T("Edit Identity"),
            title_search = T("Search Identity"),
            subtitle_create = T("Add New Identity"),
            subtitle_list = T("Current Identities"),
            label_list_button = T("List Identities"),
            label_create_button = ADD_IDENTITY,
            msg_record_created = T("Identity added"),
            msg_record_modified = T("Identity updated"),
            msg_record_deleted = T("Identity deleted"),
            msg_list_empty = T("No Identities currently registered"))

        # Resource configuration
        configure(tablename,
                  list_fields=["id",
                               "type",
                               "type",
                               "value",
                               "country_code",
                               "ia_name"
                               ])

        # ---------------------------------------------------------------------
        # Return model-global names to response.s3
        #
        return Storage()

    # -------------------------------------------------------------------------
    @staticmethod
    def address_onaccept(form):
        """
            Updates the Base Location to be the same as the Address

            If the base location hasn't yet been set or if this is specifically
            requested
        """

        s3db = current.s3db
        request = current.request

        vars = form.vars
        location_id = vars.location_id

        if location_id:
            pe_id = vars.pe_id
            table = s3db.pr_person
            if "base_location" in request.vars and \
               request.vars.base_location == "on":
                # Specifically requested
                S3Tracker()(s3db.pr_pentity, pe_id).set_base_location(location_id)
                pe = current.db(table.pe_id == pe_id).select(table.id).first()
                if pe:
                    # Update the Lx fields
                    current.response.s3.lx_update(table, pe.id)
            else:
                # Check if a base location already exists
                pe = current.db(table.pe_id == pe_id).select(table.id,
                                                             table.location_id).first()
                if pe and not pe.location_id:
                    # Hasn't yet been set so use this
                    S3Tracker()(s3db.pr_pentity, pe_id).set_base_location(location_id)
                    # Update the Lx fields
                    current.response.s3.lx_update(table, pe.id)

        return

    # -------------------------------------------------------------------------
    @staticmethod
    def pr_pimage_onvalidation(form):
        """ Image form validation """

        db = current.db
        s3db = current.s3db
        request = current.request

        table = s3db.pr_pimage
        image = form.vars.image

        if not hasattr(image, "file"):
            id = request.post_vars.id
            if id:
                record = db(table.id == id).select(table.image,
                                                   limitby=(0, 1)).first()
                if record:
                    image = record.image

        url = form.vars.url
        if not hasattr(image, "file") and not image and not url:
            form.errors.image = \
            form.errors.url = T("Either file upload or image URL required.")
        return

# =============================================================================
class S3SavedSearch(S3Model):
    """ Saved Searches """

    names = ["pr_save_search"]

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth
        request = current.request
        s3 = current.response.s3

        pr_person = self.table("pr_person")
        person_id = s3.pr_person_id

        # ---------------------------------------------------------------------
        # Saved Searches
        #
        tablename = "pr_save_search"
        table = self.define_table(tablename,
                                  Field("user_id", "integer",
                                        readable = False,
                                        writable = False,
                                        default = auth.user_id),
                                  Field("search_vars","string",
                                        label = T("Search Criteria")),
                                  Field("subscribed","boolean",
                                        default=False),
                                  person_id(label = T("Person"),
                                            default = auth.s3_logged_in_person()),
                                  *s3_timestamp())

        # Field configuration
        table.search_vars.represent = lambda id : self.get_criteria(id=id)

        # CRUD Strings
        s3.crud_strings[tablename] = Storage(
            title_create = T("Save Search"),
            title_display = T("Saved Search Details"),
            title_list = T("Saved Searches"),
            title_update = T("Edit Saved Search"),
            title_search = T("Search Saved Searches"),
            subtitle_create = T("Add Saved Search"),
            subtitle_list = T("Saved Searches"),
            label_list_button = T("List Saved Searches"),
            label_create_button = T("Save Search"),
            label_delete_button = T("Delete Saved Search"),
            msg_record_created = T("Saved Search added"),
            msg_record_modified = T("Saved Search updated"),
            msg_record_deleted = T("Saved Search deleted"),
            msg_list_empty = T("No Search saved"))

        # Resource configuration
        self.configure(tablename,
                       insertable = False,
                       editable = False,
                       listadd = False,
                       deletable = True,
                       list_fields=["search_vars"])

        # ---------------------------------------------------------------------
        # Return model-global names to response.s3
        #
        return Storage()

    # -------------------------------------------------------------------------
    @staticmethod
    def get_criteria(id):
        import cPickle

        s = ""
        try:
            id = id.replace("&apos;", "'")
            search_vars = cPickle.loads(id)
            s = "<p>"
            pat = '_'
            for var in search_vars.iterkeys():
                if var == "criteria" :
                    c_dict = search_vars[var]
                    #s = s + crud_string("pr_save_search", "Search Criteria")
                    for j in c_dict.iterkeys():
                        if not re.match(pat,j):
                            st = str(j)
                            st = st.replace("_search_", " ")
                            st = st.replace("_advanced", "")
                            st = st.replace("_simple", "")
                            st = st.replace("text", "text matching")
                            """st = st.replace(search_vars["function"], "")
                            st = st.replace(search_vars["prefix"], "")"""
                            st = st.replace("_", " ")
                            s = "%s <b> %s </b>: %s <br />" %(s, st.capitalize(), str(c_dict[j]))
                elif var == "simple" or var == "advanced":
                    continue
                else:
                    if var == "function":
                        v1 = "Resource Name"
                    elif var == "prefix":
                        v1 = "Module"
                    s = "%s<b>%s</b>: %s<br />" %(s, v1, str(search_vars[var]))
            s = s + "</p>"
            return XML(s)
        except:
            return XML(s)

# =============================================================================
class S3PersonPresence(S3Model):
    """
        Presence Log for Persons

        @todo: deprecate
        currently still used by CR
    """

    names = ["pr_presence",
             "pr_trackable_types",
             "pr_default_trackable",
             "pr_presence_opts",
             "pr_presence_conditions",
             "pr_default_presence"]

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth
        request = current.request
        s3 = current.response.s3

        person_id = self.pr_person_id
        location_id = self.gis_location_id

        ADD_LOCATION = current.messages.ADD_LOCATION
        UNKNOWN_OPT = current.messages.UNKNOWN_OPT

        datetime_represent = S3DateTime.datetime_represent

        # Trackable types
        pr_trackable_types = {
            1:current.T("Person"),          # an individual
            2:current.T("Group"),           # a group
            3:current.T("Body"),            # a dead body or body part
            4:current.T("Object"),          # other objects belonging to persons
            5:current.T("Organization"),    # an organisation
            6:current.T("Office"),          # an office
        }
        pr_default_trackable = 1

        # Presence conditions
        pr_presence_opts = Storage(
            SEEN = 1,
            TRANSIT = 2,
            PROCEDURE = 3,
            TRANSITIONAL_PRESENCE = (1, 2, 3),
            CHECK_IN = 11,
            CONFIRMED = 12,
            DECEASED = 13,
            LOST = 14,
            PERSISTANT_PRESENCE = (11, 12, 13, 14),
            TRANSFER = 21,
            CHECK_OUT = 22,
            ABSENCE = (21, 22),
            MISSING = 99
        )
        opts = pr_presence_opts
        pr_presence_conditions = Storage({
            # Transitional presence conditions:
            opts.SEEN: current.T("Seen"),           # seen (formerly "found") at location
            opts.TRANSIT: current.T("Transit"),     # seen at location, between two transfers
            opts.PROCEDURE: current.T("Procedure"), # seen at location, undergoing procedure ("Checkpoint")

            # Persistant presence conditions:
            opts.CHECK_IN: current.T("Check-In"),   # arrived at location for accomodation/storage
            opts.CONFIRMED: current.T("Confirmed"), # confirmation of stay/storage at location
            opts.DECEASED: current.T("Deceased"),   # deceased
            opts.LOST: current.T("Lost"),           # destroyed/disposed at location

            # Absence conditions:
            opts.TRANSFER: current.T("Transfer"),   # Send to another location
            opts.CHECK_OUT: current.T("Check-Out"), # Left location for unknown destination

            # Missing condition:
            opts.MISSING: current.T("Missing"),     # Missing (from a "last-seen"-location)
        })
        pr_default_presence = 1

        resourcename = "presence"
        tablename = "pr_presence"
        table = self.define_table(tablename,
                                  self.super_link("pe_id", "pr_pentity"),
                                  self.super_link("sit_id", "sit_situation"),
                                  person_id("observer",
                                            label=T("Observer"),
                                            default = auth.s3_logged_in_person(),
                                            comment=pr_person_comment(T("Observer"),
                                                                      T("Person who has actually seen the person/group."))),
                                  Field("shelter_id", "integer",
                                        readable = False,
                                        writable = False),
                                  location_id(widget = S3LocationAutocompleteWidget(),
                                              comment = DIV(A(ADD_LOCATION,
                                                              _class="colorbox",
                                                              _target="top",
                                                              _title=ADD_LOCATION,
                                                              _href=URL(c="gis", f="location",
                                                                        args="create",
                                                                        vars=dict(format="popup"))),
                                                            DIV(_class="tooltip",
                                                                _title="%s|%s" % (T("Current Location"),
                                                                                  T("The Current Location of the Person/Group, which can be general (for Reporting) or precise (for displaying on a Map). Enter a few characters to search from available locations."))))),
                                  Field("location_details",
                                        comment = DIV(_class="tooltip",
                                                      _title="%s|%s" % (T("Location Details"),
                                                                        T("Specific Area (e.g. Building/Room) within the Location that this Person/Group is seen.")))),
                                  Field("datetime", "datetime",
                                        label = T("Date/Time"),
                                        default = request.utcnow,
                                        requires = IS_UTC_DATETIME(allow_future=False),
                                        widget = S3DateTimeWidget(future=0),
                                        represent = lambda val: datetime_represent(val, utc=True)),
                                  Field("presence_condition", "integer",
                                        requires = IS_IN_SET(pr_presence_conditions,
                                                             zero=None),
                                        default = pr_default_presence,
                                        label = T("Presence Condition"),
                                        represent = lambda opt: \
                                                    pr_presence_conditions.get(opt, UNKNOWN_OPT)),
                                   Field("proc_desc",
                                         label = T("Procedure"),
                                         comment = DIV(DIV(_class="tooltip",
                                                           _title="%s|%s" % (T("Procedure"),
                                                                             T('Describe the procedure which this record relates to (e.g. "medical examination")'))))),
                                   location_id("orig_id",
                                               label=T("Origin"),
                                               widget = S3LocationAutocompleteWidget(),
                                               comment = DIV(A(ADD_LOCATION,
                                                               _class="colorbox",
                                                               _target="top",
                                                               _title=ADD_LOCATION,
                                                               _href=URL(c="gis", f="location",
                                                                         args="create",
                                                                         vars=dict(format="popup"))),
                                                             DIV(_class="tooltip",
                                                                 _title="%s|%s" % (T("Origin"),
                                                                                   T("The Location the Person has come from, which can be general (for Reporting) or precise (for displaying on a Map). Enter a few characters to search from available locations."))))),
                                   location_id("dest_id",
                                               label=T("Destination"),
                                               widget = S3LocationAutocompleteWidget(),
                                               comment = DIV(A(ADD_LOCATION,
                                                               _class="colorbox",
                                                               _target="top",
                                                               _title=ADD_LOCATION,
                                                               _href=URL(c="gis", f="location",
                                                                         args="create",
                                                                         vars=dict(format="popup"))),
                                                             DIV(_class="tooltip",
                                                                 _title="%s|%s" % (T("Destination"),
                                                                                   T("The Location the Person is going to, which can be general (for Reporting) or precise (for displaying on a Map). Enter a few characters to search from available locations."))))),
                                   Field("comment"),
                                   Field("closed", "boolean",
                                         default=False,
                                         readable = False,
                                         writable = False),
                                   *s3.meta_fields())

        # CRUD Strings
        ADD_LOG_ENTRY = T("Add Log Entry")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_LOG_ENTRY,
            title_display = T("Log Entry Details"),
            title_list = T("Presence Log"),
            title_update = T("Edit Log Entry"),
            title_search = T("Search Log Entry"),
            subtitle_create = T("Add New Log Entry"),
            subtitle_list = T("Current Log Entries"),
            label_list_button = T("List Log Entries"),
            label_create_button = ADD_LOG_ENTRY,
            msg_record_created = T("Log entry added"),
            msg_record_modified = T("Log entry updated"),
            msg_record_deleted = T("Log entry deleted"),
            msg_list_empty = T("No Presence Log Entries currently registered"))

        # Resource configuration
        self.configure(tablename,
                       super_entity = "sit_situation",
                       onvalidation = self.presence_onvalidation,
                       onaccept = self.presence_onaccept,
                       delete_onaccept = self.presence_onaccept,
                       list_fields = ["id",
                                      "datetime",
                                      "location_id",
                                      "shelter_id",
                                      "presence_condition",
                                      "orig_id",
                                      "dest_id"
                                     ],
                       main="time",
                       extra="location_details")

        # ---------------------------------------------------------------------
        # Return model-global names to response.s3
        #
        return Storage(
             pr_trackable_types=pr_trackable_types,
             pr_default_trackable=pr_default_trackable,
             pr_presence_opts=pr_presence_opts,
             pr_presence_conditions=pr_presence_conditions,
             pr_default_presence=pr_default_presence
        )

    # -------------------------------------------------------------------------
    @staticmethod
    def presence_onvalidation(form):
        """ Presence record validation """

        db = current.db
        s3db = current.s3db
        s3 = current.response.s3

        table = s3db.pr_presence
        popts = s3.pr_presence_opts
        shelter_table = s3db.cr_shelter

        location = form.vars.location_id
        shelter = form.vars.shelter_id

        if shelter and shelter_table is not None:
            set = db(shelter_table.id == shelter)
            row = set.select(shelter_table.location_id, limitby=(0, 1)).first()
            if row:
                location = form.vars.location_id = row.location_id
            else:
                shelter = None

        if location or shelter:
            return

        condition = form.vars.presence_condition
        if condition:
            try:
                condition = int(condition)
            except ValueError:
                condition = None
        else:
            condition = table.presence_condition.default
            form.vars.presence_condition = condition

        if condition:
            if condition in popts.PERSISTANT_PRESENCE or \
               condition in popts.ABSENCE:
                if not form.vars.id:
                    if table.location_id.default or \
                       table.shelter_id.default:
                        return
                else:
                    record = db(table.id == form.vars.id).select(table.location_id,
                                                                 table.shelter_id,
                                                                 limitby=(0, 1)).first()
                    if record and \
                       record.location_id or record.shelter_id:
                        return
            else:
                return
        else:
            return

        form.errors.location_id = \
        form.errors.shelter_id = T("Either a shelter or a location must be specified")
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def presence_onaccept(form):
        """
            Update the presence log of a person entity

            - mandatory to be called as onaccept routine at any modification
              of pr_presence records

        """

        db = current.db
        s3db = current.s3db
        s3 = current.response.s3

        table = s3db.pr_presence
        popts = s3.pr_presence_opts

        if isinstance(form, (int, long, str)):
            id = form
        elif hasattr(form, "vars"):
            id = form.vars.id
        else:
            id = form.id

        presence = db(table.id == id).select(table.ALL, limitby=(0,1)).first()
        if not presence:
            return
        else:
            condition = presence.presence_condition

        pe_id = presence.pe_id
        datetime = presence.datetime
        if not datetime or not pe_id:
            return

        this_entity = ((table.pe_id == pe_id) & (table.deleted == False))
        earlier = (table.datetime < datetime)
        later = (table.datetime > datetime)
        same_place = ((table.location_id == presence.location_id) |
                      (table.shelter_id == presence.shelter_id))
        is_present = (table.presence_condition.belongs(popts.PERSISTANT_PRESENCE))
        is_absent = (table.presence_condition.belongs(popts.ABSENCE))
        is_missing = (table.presence_condition == popts.MISSING)

        if not presence.deleted:

            if condition in popts.TRANSITIONAL_PRESENCE:
                if presence.closed:
                    db(table.id == id).update(closed=False)

            elif condition in popts.PERSISTANT_PRESENCE:
                if not presence.closed:
                    query = this_entity & earlier & (is_present | is_missing) & \
                            (table.closed == False)
                    db(query).update(closed=True)

                    query = this_entity & later & \
                            (is_present | (is_absent & same_place))
                    if db(query).count():
                        db(table.id == id).update(closed=True)

            elif condition in popts.ABSENCE:
                query = this_entity & earlier & is_present & same_place
                db(query).update(closed=True)

                if not presence.closed:
                    db(table.id == id).update(closed=True)

        if not presence.closed:

            # Re-open the last persistant presence if no closing event
            query = this_entity & is_present
            presence = db(query).select(table.ALL, orderby=~table.datetime, limitby=(0,1)).first()
            if presence and presence.closed:
                later = (table.datetime > presence.datetime)
                query = this_entity & later & is_absent & same_place
                if not db(query).count():
                    db(table.id == presence.id).update(closed=False)

            # Re-open the last missing if no later persistant presence
            query = this_entity & is_missing
            presence = db(query).select(table.ALL, orderby=~table.datetime, limitby=(0,1)).first()
            if presence and presence.closed:
                later = (table.datetime > presence.datetime)
                query = this_entity & later & is_present
                if not db(query).count():
                    db(table.id == presence.id).update(closed=False)

        pentity = db(db.pr_pentity.pe_id == pe_id).select(db.pr_pentity.instance_type,
                                                          limitby=(0,1)).first()
        if pentity and pentity.instance_type == "pr_person":
            query = this_entity & is_missing & (table.closed == False)
            if db(query).count():
                db(db.pr_person.pe_id == pe_id).update(missing = True)
            else:
                db(db.pr_person.pe_id == pe_id).update(missing = False)

        return

# =============================================================================
class S3PersonDescription(S3Model):
    """ Additional tables for DVI/MPR """

    names = ["pr_note", "pr_physical_description"]

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth
        request = current.request
        s3 = current.response.s3

        person_id = self.pr_person_id
        location_id = self.gis_location_id

        UNKNOWN_OPT = current.messages.UNKNOWN_OPT
        #if deployment_settings.has_module("dvi") or \
           #deployment_settings.has_module("mpr"):

        # ---------------------------------------------------------------------
        # Note
        #
        person_status = {
            1: T("missing"),
            2: T("found"),
            3: T("deceased"),
            9: T("none")
        }

        resourcename = "note"
        tablename = "pr_note"
        table = self.define_table(tablename,
                                  self.super_link("pe_id", "pr_pentity"),
                                  # Reporter
                                  #person_id("reporter"),
                                  Field("confirmed", "boolean",
                                        default=False,
                                        readable=False,
                                        writable=False),
                                  Field("closed", "boolean",
                                        default=False,
                                        readable=False,
                                        writable=False),
                                  Field("status", "integer",
                                        requires=IS_IN_SET(person_status,
                                                           zero=None),
                                        default=9,
                                        label=T("Status"),
                                        represent=lambda opt: \
                                                  person_status.get(opt, UNKNOWN_OPT)),
                                  Field("timestmp", "datetime",
                                        label=T("Date/Time"),
                                        requires=[IS_EMPTY_OR(IS_UTC_DATETIME_IN_RANGE())],
                                        widget = S3DateTimeWidget(),
                                        default=request.utcnow),
                                  Field("note_text", "text",
                                        label=T("Text")),
                                  Field("note_contact", "text",
                                        label=T("Contact Info"),
                                        readable=False,
                                        writable=False),
                                  location_id(label=T("Last known location")),
                                  *s3.meta_fields())

        # CRUD strings
        ADD_NOTE = T("New Entry")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_NOTE,
            title_display = T("Journal Entry Details"),
            title_list = T("Journal"),
            title_update = T("Edit Entry"),
            title_search = T("Search Entries"),
            subtitle_create = T("Add New Entry"),
            subtitle_list = T("Current Entries"),
            label_list_button = T("See All Entries"),
            label_create_button = ADD_NOTE,
            msg_record_created = T("Journal entry added"),
            msg_record_modified = T("Journal entry updated"),
            msg_record_deleted = T("Journal entry deleted"),
            msg_list_empty = T("No entry available"))

        # Resource configuration
        self.configure(tablename,
                       list_fields=["id",
                                    "timestmp",
                                    "location_id",
                                    "note_text",
                                    "status"],
                       editable=False,
                       onaccept=self.note_onaccept,
                       ondelete=self.note_onaccept)

        # =====================================================================
        # Physical Description
        #
        pr_race_opts = {
            1: T("caucasoid"),
            2: T("mongoloid"),
            3: T("negroid"),
            99: T("other")
        }

        pr_complexion_opts = {
            1: T("light"),
            2: T("medium"),
            3: T("dark"),
            99: T("other")
        }

        pr_height_opts = {
            1: T("short"),
            2: T("average"),
            3: T("tall")
        }

        pr_weight_opts = {
            1: T("slim"),
            2: T("average"),
            3: T("fat")
        }

        # http://docs.oasis-open.org/emergency/edxl-have/cs01/xPIL-types.xsd
        pr_blood_type_opts = ("A+", "A-", "B+", "B-", "AB+", "AB-", "0+", "0-")

        pr_eye_color_opts = {
            1: T("blue"),
            2: T("grey"),
            3: T("green"),
            4: T("brown"),
            5: T("black"),
            99: T("other")
        }

        pr_hair_color_opts = {
            1: T("blond"),
            2: T("brown"),
            3: T("black"),
            4: T("red"),
            5: T("grey"),
            6: T("white"),
            99: T("see comment")
        }

        pr_hair_style_opts = {
            1: T("straight"),
            2: T("wavy"),
            3: T("curly"),
            99: T("see comment")
        }

        pr_hair_length_opts = {
            1: T("short<6cm"),
            2: T("medium<12cm"),
            3: T("long>12cm"),
            4: T("shaved"),
            99: T("see comment")
        }

        pr_hair_baldness_opts = {
            1: T("forehead"),
            2: T("sides"),
            3: T("tonsure"),
            4: T("total"),
            99: T("see comment")
        }

        pr_facial_hair_type_opts = {
            1: T("none"),
            2: T("Moustache"),
            3: T("Goatee"),
            4: T("Whiskers"),
            5: T("Full beard"),
            99: T("see comment")
        }

        pr_facial_hair_length_opts = {
            1: T("short"),
            2: T("medium"),
            3: T("long"),
            4: T("shaved")
        }

        # This set is suitable for use in the US
        pr_ethnicity_opts = [
            "American Indian",
            "Alaskan",
            "Asian",
            "African American",
            "Hispanic or Latino",
            "Native Hawaiian",
            "Pacific Islander",
            "Two or more",
            "Unspecified",
            "White"
        ]

        resourcename = "physical_description"
        tablename = "pr_physical_description"
        table = self.define_table(tablename,
                                  self.super_link("pe_id", "pr_pentity"),
                                  # Race and complexion
                                  Field("race", "integer",
                                        requires = IS_EMPTY_OR(IS_IN_SET(pr_race_opts)),
                                        label = T("Race"),
                                        represent = lambda opt: \
                                                    pr_race_opts.get(opt, UNKNOWN_OPT)),
                                  Field("complexion", "integer",
                                        requires = IS_EMPTY_OR(IS_IN_SET(pr_complexion_opts)),
                                        label = T("Complexion"),
                                        represent = lambda opt: \
                                                    pr_complexion_opts.get(opt, UNKNOWN_OPT)),
                                  Field("ethnicity",
                                        #requires=IS_NULL_OR(IS_IN_SET(pr_ethnicity_opts)),
                                        length=64),   # Mayon Compatibility

                                  # Height and weight
                                  Field("height", "integer",
                                        requires = IS_EMPTY_OR(IS_IN_SET(pr_height_opts)),
                                        label = T("Height"),
                                        represent = lambda opt: \
                                                    pr_height_opts.get(opt, UNKNOWN_OPT)),
                                  Field("height_cm", "integer",
                                        requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 300)),
                                        label = T("Height (cm)")),
                                  Field("weight", "integer",
                                        requires = IS_EMPTY_OR(IS_IN_SET(pr_weight_opts)),
                                        label = T("Weight"),
                                        represent = lambda opt: \
                                                    pr_weight_opts.get(opt, UNKNOWN_OPT)),
                                  Field("weight_kg", "integer",
                                        requires = IS_NULL_OR(IS_INT_IN_RANGE(0, 500)),
                                        label = T("Weight (kg)")),

                                  # Blood type, eye color
                                  Field("blood_type",
                                        requires = IS_EMPTY_OR(IS_IN_SET(pr_blood_type_opts)),
                                        label = T("Blood Type (AB0)"),
                                        represent = lambda opt: opt or UNKNOWN_OPT),
                                  Field("eye_color", "integer",
                                        requires = IS_EMPTY_OR(IS_IN_SET(pr_eye_color_opts)),
                                        label = T("Eye Color"),
                                        represent = lambda opt: \
                                                    pr_eye_color_opts.get(opt, UNKNOWN_OPT)),

                                  # Hair of the head
                                  Field("hair_color", "integer",
                                        requires = IS_EMPTY_OR(IS_IN_SET(pr_hair_color_opts)),
                                        label = T("Hair Color"),
                                        represent = lambda opt: \
                                                    pr_hair_color_opts.get(opt, UNKNOWN_OPT)),
                                  Field("hair_style", "integer",
                                        requires = IS_EMPTY_OR(IS_IN_SET(pr_hair_style_opts)),
                                        label = T("Hair Style"),
                                        represent = lambda opt: \
                                                    pr_hair_style_opts.get(opt, UNKNOWN_OPT)),
                                  Field("hair_length", "integer",
                                        requires = IS_EMPTY_OR(IS_IN_SET(pr_hair_length_opts)),
                                        label = T("Hair Length"),
                                        represent = lambda opt: \
                                                    pr_hair_length_opts.get(opt, UNKNOWN_OPT)),
                                  Field("hair_baldness", "integer",
                                        requires = IS_EMPTY_OR(IS_IN_SET(pr_hair_baldness_opts)),
                                        label = T("Baldness"),
                                        represent = lambda opt: \
                                                    pr_hair_baldness_opts.get(opt, UNKNOWN_OPT)),
                                  Field("hair_comment"),

                                  # Facial hair
                                  Field("facial_hair_type", "integer",
                                        requires = IS_EMPTY_OR(IS_IN_SET(pr_facial_hair_type_opts)),
                                        label = T("Facial hair, type"),
                                        represent = lambda opt: \
                                                    pr_facial_hair_type_opts.get(opt, UNKNOWN_OPT)),
                                  Field("facial_hair_color", "integer",
                                        requires = IS_EMPTY_OR(IS_IN_SET(pr_hair_color_opts)),
                                        label = T("Facial hair, color"),
                                        represent = lambda opt: \
                                                    pr_hair_color_opts.get(opt, UNKNOWN_OPT)),
                                  Field("facial_hair_length", "integer",
                                        requires = IS_EMPTY_OR(IS_IN_SET(pr_facial_hair_length_opts)),
                                        label = T("Facial hear, length"),
                                        represent = lambda opt: \
                                                    pr_facial_hair_length_opts.get(opt, UNKNOWN_OPT)),
                                  Field("facial_hair_comment"),

                                  # Body hair and skin marks
                                  Field("body_hair"),
                                  Field("skin_marks", "text"),

                                  # Medical Details: scars, amputations, implants
                                  Field("medical_conditions", "text"),

                                  # Other details
                                  Field("other_details", "text"),

                                  s3.comments(),
                                  *s3.meta_fields())

        # Field configuration
        table.height_cm.comment = DIV(DIV(_class="tooltip",
                                          _title="%s|%s" % (T("Height"),
                                                            T("The body height (crown to heel) in cm."))))
        table.weight_kg.comment = DIV(DIV(_class="tooltip",
                                          _title="%s|%s" % (T("Weight"),
                                                            T("The weight in kg."))))

        table.pe_id.readable = False
        table.pe_id.writable = False

        # CRUD Strings
        # ?

        # Resource Configuration
        # ?

    # -------------------------------------------------------------------------
    @staticmethod
    def note_onaccept(form):
        """ Update missing status for person """

        db = current.db
        s3db = current.s3db

        pe_table = s3db.pr_pentity
        ntable = s3db.pr_note
        ptable = s3db.pr_person

        if isinstance(form, (int, long, str)):
            _id = form
        elif hasattr(form, "vars"):
            _id = form.vars.id
        else:
            _id = form.id

        note = ntable[_id]
        if not note:
            return

        query = (ntable.pe_id == note.pe_id) & \
                (ntable.deleted != True)
        mq = query & ntable.status == 1
        fq = query & ntable.status.belongs((2, 3))
        mr = db(mq).select(ntable.id,
                           ntable.timestmp,
                           orderby=~ntable.timestmp,
                           limitby=(0, 1)).first()
        fr = db(fq).select(ntable.id,
                           ntable.timestmp,
                           orderby=~ntable.timestmp,
                           limitby=(0, 1)).first()
        missing = False
        if mr and not fr or fr.timestmp < mr.timestmp:
            missing = True
        query = ptable.pe_id == note.pe_id
        db(query).update(missing=missing)
        if note.deleted:
            try:
                location_id = form.location_id
            except:
                pass
            else:
                ttable = s3db.sit_presence
                query = (ptable.pe_id == note.pe_id) & \
                        (ttable.uuid == ptable.uuid) & \
                        (ttable.location_id == location_id) & \
                        (ttable.timestmp == note.timestmp)
        if note.location_id:
            tracker = S3Tracker()
            tracker(query).set_location(note.location_id,
                                        timestmp=note.timestmp)
        return

# =============================================================================
def pr_pentity_represent(id, show_label=True, default_label="[No ID Tag]"):
    """ Represent a Person Entity in option fields or list views """

    T = current.T
    db = current.db
    s3db = current.s3db

    if not id:
        return current.messages.NONE

    pe_str = T("None (no such record)")

    pe_table = s3db.pr_pentity
    pe = db(pe_table.pe_id == id).select(pe_table.instance_type,
                                         pe_table.pe_label,
                                         limitby=(0, 1)).first()
    if not pe:
        return pe_str

    instance_type = pe.instance_type
    instance_type_nice = pe_table.instance_type.represent(instance_type)

    table = s3db.table(instance_type, None)
    if not table:
        return pe_str

    label = pe.pe_label or default_label

    if instance_type == "pr_person":
        person = db(table.pe_id == id).select(
                    table.first_name, table.middle_name, table.last_name,
                    limitby=(0, 1)).first()
        if person:
            if show_label:
                pe_str = "%s %s (%s)" % (s3_fullname(person),
                                         label, instance_type_nice)
            else:
                pe_str = "%s (%s)" % (s3_fullname(person),
                                      instance_type_nice)
    elif instance_type == "pr_group":
        group = db(table.pe_id == id).select(table.name,
                                             limitby=(0, 1)).first()
        if group:
            pe_str = "%s (%s)" % (group.name, instance_type_nice)
    elif instance_type == "org_organisation":
        organisation = db(table.pe_id == id).select(table.name,
                                                    limitby=(0, 1)).first()
        if organisation:
            pe_str = "%s (%s)" % (organisation.name, instance_type_nice)
    elif instance_type == "org_office":
        office = db(table.pe_id == id).select(table.name,
                                              limitby=(0, 1)).first()
        if office:
            pe_str = "%s (%s)" % (office.name, instance_type_nice)
    else:
        pe_str = "[%s] (%s)" % (label,
                                instance_type_nice)
    return pe_str

# =============================================================================
def pr_person_represent(id):
    """ Representation """

    db = current.db
    s3db = current.s3db
    cache = current.cache

    table = s3db.pr_person

    def _represent(id):
        if isinstance(id, Row):
            person = id
            id = person.id
        else:
            person = db(table.id == id).select(table.first_name,
                                                table.middle_name,
                                                table.last_name,
                                                limitby=(0, 1)).first()
        if person:
            return s3_fullname(person)
        else:
            return None

    name = cache.ram("pr_person_%s" % id,
                        lambda: _represent(id), time_expire=10)
    return name

# =============================================================================
def pr_rheader(r, tabs=[]):
    """
        Person Registry resource headers
        - used in PR, HRM, DVI, MPR, MSG, VOL
    """

    T = current.T
    db = current.db
    s3db = current.s3db
    gis = current.gis
    s3 = current.response.s3

    if "viewing" in r.vars:
        tablename, record_id = r.vars.viewing.rsplit(".", 1)
        record = db[tablename][record_id]
    else:
        tablename = r.tablename
        record = r.record

    if r.representation == "html":
        rheader_tabs = s3_rheader_tabs(r, tabs)

        if tablename == "pr_person":
            person = record
            if person:
                ptable = r.table
                rheader = DIV(TABLE(
                    TR(TH("%s: " % T("Name")),
                       s3_fullname(person),
                       TH("%s: " % T("ID Tag Number")),
                       "%(pe_label)s" % person,
                       TD(ptable.picture.represent(person.picture),
                          _rowspan=3)),
                    TR(TH("%s: " % T("Date of Birth")),
                       "%s" % (person.date_of_birth or T("unknown")),
                       TH("%s: " % T("Gender")),
                       "%s" % s3.pr_gender_opts.get(person.gender, T("unknown"))),

                    TR(TH("%s: " % T("Nationality")),
                       "%s" % (gis.get_country(person.nationality, key_type="code") or T("unknown")),
                       TH("%s: " % T("Age Group")),
                       "%s" % s3.pr_age_group_opts.get(person.age_group, T("unknown"))),

                    ), rheader_tabs)
                return rheader

        elif tablename == "pr_group":
            group = record
            if group:
                table = s3db.pr_group_membership
                query = (table.group_id == record.id) & \
                        (table.group_head == True)
                leader = db(query).select(table.person_id,
                                          limitby=(0, 1)).first()
                if leader:
                    leader = s3_fullname(leader.person_id)
                else:
                    leader = ""
                rheader = DIV(TABLE(
                                TR(TH("%s: " % T("Name")),
                                   group.name,
                                   TH("%s: " % T("Leader")) if leader else "",
                                   leader),
                                TR(TH("%s: " % T("Description")),
                                   group.description or "",
                                   TH(""),
                                   "")
                                ), rheader_tabs)
                return rheader

    return None

# =============================================================================
pr_person_comment = lambda title, comment, caller=None, child=None: \
                        DIV(A(current.messages.ADD_PERSON,
                              _class="colorbox",
                              _href=URL(c="pr", f="person", args="create",
                              vars=dict(format="popup",
                                        caller=caller,
                                        child=child)),
                              _target="top",
                              _title=current.messages.ADD_PERSON),
                            DIV(DIV(_class="tooltip",
                                    _title="%s|%s" % (title, comment))))

# END =========================================================================
