# -*- coding: utf-8 -*-

""" Sahana Eden Person Registry Model

    @author: Dominic König <dominic[at]aidiq.com>

    @copyright: 2009-2011 (c) Sahana Software Foundation
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
           "pr_pentity_represent",
           "pr_person_represent"]

from gluon import *
from gluon.dal import Row
from gluon.storage import Storage
from ..s3 import *

# =============================================================================
class S3PersonEntity(S3Model):

    names = ["pr_pentity",
             "pr_pe_label"]

    def model(self):
        """
            Table definitions

            If this function returns a dict, then all its items will
            be added to response.s3.
        """

        db = current.db
        T = current.T

        pe_types = Storage(pr_person = T("Person"),
                           pr_group = T("Group"),
                           org_organisation = T("Organization"),
                           org_office = T("Office"),
                           dvi_body = T("Body"))

        tablename = "pr_pentity"
        table = self.super_entity(tablename, "pe_id", pe_types,
                                  Field("pe_label", length=128))

        pentity_search = S3PentitySearch(name = "pentity_search_simple",
                                         label = T("Name and/or ID"),
                                         comment = T(""),
                                         field = ["pe_label"])

        pentity_search.pentity_represent = pr_pentity_represent

        self.configure(tablename,
                       editable=False,
                       deletable=False,
                       listadd=False,
                       search_method=pentity_search)

        pr_pe_label = S3ReusableField("pe_label", length=128,
                                      label = T("ID Tag Number"),
                                      requires = IS_NULL_OR(IS_NOT_ONE_OF(db,
                                                            "pr_pentity.pe_label")))

        return Storage(
            pr_pe_label=pr_pe_label,
        )

    # -------------------------------------------------------------------------
    def defaults(self):
        """
            Return safe defaults for model globals

            If this function returns a dict, then all its items will
            be added to response.s3.
        """

        return Storage(
            pe_label=S3ReusableField("pe_label", length=128,
                                     label = T("ID Tag Number")),
        )

# =============================================================================
class S3PersonModel(S3Model):

    names = ["pr_person",
             "pr_gender",
             "pr_gender_opts",
             "pr_age_group",
             "pr_age_group_opts",
             "pr_person_id",
             "pr_person_comment",
             "pr_group_id",
             "pr_group_represent"]

    def model(self):

        T = current.T
        db = current.db
        request = current.request
        s3 = current.response.s3
        gis = current.gis

        pr_pentity = self.table("pr_pentity")
        sit_trackable = self.table("sit_trackable")
        pe_label = s3.pr_pe_label

        NONE = T("None")
        UNKNOWN_OPT = T("Unknown")
        SELECT_LOCATION = T("Select a location")

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

        pr_religion_opts = self.settings.get_L10n_religions()

        pr_impact_tags = {
            1: T("injured"),
            4: T("diseased"),
            2: T("displaced"),
            5: T("separated from family"),
            3: T("suffered financial losses")
        }

        if self.settings.get_L10n_mandatory_lastname():
            last_name_validate = IS_NOT_EMPTY(error_message = T("Please enter a last name"))
        else:
            last_name_validate = None

        s3_date_format = self.settings.get_L10n_date_format()

        tablename = "pr_person"
        table = self.define_table(tablename,
                                  self.super_link(pr_pentity),          # pe_id
                                  self.super_link(sit_trackable),       # track_id
                                  s3.location_id(readable=False,
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
                                  Field("preferred_name",
                                        comment = DIV(DIV(_class="tooltip",
                                                          _title="%s|%s" % (T("Preferred Name"),
                                                                            T("The name to be used when calling for or directly addressing the person (optional).")))),
                                        length=64), # Mayon Compatibility
                                  Field("local_name", label = T("Local Name"),
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
                                        length=128), # Mayon Compatibility
                                  Field("picture", "upload",
                                        autodelete=True,
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
                                        comment =  DIV(_class="tooltip",
                                                       _title="%s|%s" % (T("Picture"),
                                                                         T("Upload an image file here.")))),
                                  s3.comments(),
                                  *s3.meta_fields())

        ADD_PERSON = T("Add Person")
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

        self.configure(tablename,
                       super_entity=(pr_pentity, sit_trackable),
                       list_fields = ["id",
                                      "first_name",
                                      "middle_name",
                                      "last_name",
                                      "picture",
                                      "gender",
                                      "age_group"
                                     ],
                       onvalidation=self.pr_person_onvalidation,
                       search_method=pr_person_search,
                       deduplicate=self.person_deduplicate,
                       main="first_name",
                       extra="last_name")

        pr_person_comment = lambda title, comment, caller=None, child=None: \
                                DIV(A(ADD_PERSON,
                                      _class="colorbox",
                                      _href=URL(c="pr", f="person", args="create",
                                      vars=dict(format="popup",
                                                caller=caller,
                                                child=child)),
                                      _target="top",
                                      _title=ADD_PERSON),
                                    DIV(DIV(_class="tooltip",
                                            _title="%s|%s" % (title, comment))))

        pr_person_id_comment = pr_person_comment(
                                    T("Person"),
                                    T("Type the first few characters of one of the Person's names."))

        pr_person_id = S3ReusableField("person_id", db.pr_person,
                                       sortby = ["first_name", "middle_name", "last_name"],
                                       requires = IS_NULL_OR(IS_ONE_OF(db, "pr_person.id",
                                                                       pr_person_represent,
                                                                       orderby="pr_person.first_name",
                                                                       sort=True,
                                                                       error_message=T("Person must be specified!"))),
                                       represent = lambda id, row=None: (id and \
                                                   [pr_person_represent(id)] or [NONE])[0],
                                       label = T("Person"),
                                       comment = pr_person_id_comment,
                                       ondelete = "RESTRICT",
                                       widget = S3PersonAutocompleteWidget())

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
                                  self.super_link(pr_pentity), # pe_id
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

        table.description.comment = DIV(DIV(_class="tooltip",
                                            _title="%s|%s" % (T("Group description"),
                                                              T("A brief description of the group (optional)"))))

        self.configure(tablename,
                       super_entity=pr_pentity,
                       main="name",
                       extra="description")

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

        pr_group_represent = lambda id: (id and [db.pr_group[id].name] or [NONE])[0]

        pr_group_id = S3ReusableField("group_id", db.pr_group,
                                      sortby="name",
                                      requires = IS_NULL_OR(IS_ONE_OF(db, "pr_group.id",
                                                                      "%(id)s: %(name)s",
                                                                      filterby="system",
                                                                      filter_opts=(False,))),
                                      represent = pr_group_represent,
                                      comment = \
                                        DIV(A(s3.crud_strings.pr_group.label_create_button,
                                              _class="colorbox",
                                              _href=URL(c="pr", f="group", args="create", vars=dict(format="popup")),
                                              _target="top",
                                              _title=s3.crud_strings.pr_group.label_create_button),
                                            DIV(DIV(_class="tooltip",
                                                    _title="%s|%s" % (T("Create Group Entry"),
                                                                      T("Create a group entry in the registry."))))),
                                      ondelete = "RESTRICT")

        # ---------------------------------------------------------------------
        # Return model-global names to response.s3
        #
        return Storage(
            pr_gender = pr_gender,
            pr_gender_opts = pr_gender_opts,
            pr_age_group = pr_age_group,
            pr_age_group_opts = pr_age_group_opts,
            pr_person_id = pr_person_id,
            pr_person_comment = pr_person_comment,
            pr_group_id = pr_group_id,
            pr_group_represent = pr_group_represent
        )

    # -----------------------------------------------------------------------------
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

    # -----------------------------------------------------------------------------
    @staticmethod
    def person_deduplicate(item):
        """ Import item deduplication """

        db = current.db

        # Ignore this processing if the id is set
        if item.id:
            return
        if item.tablename == "pr_person":
            ptable = S3Model.table("pr_person")
            ctable = S3Model.table("pr_contact")

            # Match by first name and last name, and if given, by email address
            fname = "first_name" in item.data and item.data.first_name
            lname = "last_name" in item.data and item.data.last_name
            if not fname or not lname:
                return

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
def pr_pentity_represent(id, show_label=True, default_label="[No ID Tag]"):
    """ Represent a Person Entity in option fields or list views """

    T = current.T
    db = current.db

    if not id:
        return NONE

    pe_str = T("None (no such record)")

    pe_table = S3Model.table("pr_pentity")
    pe = db(pe_table.pe_id == id).select(pe_table.instance_type,
                                         pe_table.pe_label,
                                         limitby=(0, 1)).first()
    if not pe:
        return pe_str

    instance_type = pe.instance_type
    instance_type_nice = pe_table.instance_type.represent(instance_type)

    table = S3Model.table(instance_type, None)
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

# -----------------------------------------------------------------------------
def pr_person_represent(id):
    """ Representation """

    db = current.db
    cache = current.cache

    table = S3Model.table("pr_person")

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

# END =========================================================================
