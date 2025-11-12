"""
    Field Types and Standards

    Copyright: 2009-2023 (c) Sahana Software Foundation

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

__all__ = ("CommentsField",
           "CurrencyField",
           "DateField",
           "DateTimeField",
           "LanguageField",
           "TimeField",
           "FieldTemplate",
           "MetaFields",
           "s3_fieldmethod",
           "s3_role_required",
           "s3_roles_permitted",
           "META_FIELD_NAMES",
           )

import datetime
from uuid import uuid4

from gluon import current, DIV, Field, IS_EMPTY_OR, IS_IN_SET, IS_NOT_EMPTY, IS_TIME, TAG
from gluon.sqlhtml import TimeWidget
from gluon.tools import DEFAULT

from s3dal import SQLCustomType

from ..tools import IS_ISO639_2_LANGUAGE_CODE, IS_ONE_OF, IS_UTC_DATE, \
                    IS_UTC_DATETIME, S3DateTime, S3Represent, s3_str, \
                    s3_text_represent
from ..ui import S3ScriptItem, S3CalendarWidget

# =============================================================================
def s3_fieldmethod(name, f, represent=None, search_field=None):
    """
        Helper to attach a representation method to a Field.Method.

        Args:
            name: the field name
            f: the field method
            represent: the representation function
            search_field: the field to use for searches
                          - only used by datatable_filter currently
                          - can only be a single field in the same table currently
    """

    if represent is None and search_field is None:
        fieldmethod = Field.Method(name, f)

    else:
        class Handler:
            def __init__(self, method, row):
                self.method=method
                self.row=row
            def __call__(self, *args, **kwargs):
                return self.method(self.row, *args, **kwargs)

        if represent is not None:
            if hasattr(represent, "bulk"):
                Handler.represent = represent
            else:
                Handler.represent = staticmethod(represent)

        if search_field is not None:
            Handler.search_field = search_field

        fieldmethod = Field.Method(name, f, handler=Handler)

    return fieldmethod

# =============================================================================
class FieldTemplate:
    """
        Field templates (=anonymous Field subclasses); useful to avoid
        repeating the same Field definition in multiple tables

        Example:
            # Define once:
            person_id = FieldTemplate("person_id", "reference pr_person.id",
                                      label = ...,
                                      requires = ...,
                                      represent = ...,
                                      widget = ...,
                                      )

            # Use many times:
            define_table("some_table",
                         person_id(),
                         )

            define_table("other_table",
                         person_id(),
                         )
    """

    def __init__(self, name, type="string", **args):
        """
            Args:
                name: the field name
                type: the field type
                args: default keyword args for instances
        """

        class Template(Field):

            def __init__(self, fieldname=None, empty=None, **kwargs):

                ia = dict(args)
                ia.update(kwargs)

                if not fieldname:
                    fieldname = name

                if empty is not None and "requires" not in kwargs:
                    requires = ia.get("requires")
                    validate = requires[0] \
                               if isinstance(requires, (list, tuple)) else requires

                    if empty:
                        if validate and not isinstance(validate, IS_EMPTY_OR):
                            validate = IS_EMPTY_OR(validate)
                    else:
                        if not validate:
                            validate = IS_NOT_EMPTY()
                        elif isinstance(validate, IS_EMPTY_OR):
                            validate = validate.other

                    if isinstance(requires, (list, tuple)):
                        ia["requires"] = [validate] + list(requires[1:])
                    else:
                        ia["requires"] = validate

                script = ia.pop("script", None)
                if script:
                    comment = ia.get("comment")
                    if comment:
                        ia["comment"] = TAG[""](comment, S3ScriptItem(script))
                    else:
                        ia["comment"] = S3ScriptItem(script)

                super().__init__(fieldname, type=type, **ia)

        self.template = Template

    # -------------------------------------------------------------------------
    def __call__(self, fieldname=None, empty=None, **kwargs):
        """
            Generates an instance of the Field template

            Args:
                fieldname: alternative field name
                empty: whether to allow empty field values
                       - None: use the default validator
                       - True: allow empty values
                       - False: reject empty values
                kwargs: any additional keyword arguments, including
                        overrides for default keyword arguments
        """

        # Cannot override the field type
        kwargs.pop("type", None)

        return self.template(fieldname, empty=empty, **kwargs)

    # -------------------------------------------------------------------------
    @staticmethod
    def dummy(fname="dummy_id", ftype="integer"):
        """
            A dummy FieldTemplate; for safe defaults in models

            Args:
                fname: the dummy field name
                ftype: the dummy field type

            Returns:
                a lambda with the same call signature as a FieldTemplate,
                which ignores all keyword arguments except the field name
                and produces a hidden dummy field without constraints and
                default=None
        """

        return lambda fieldname=fname, **attr: Field(fieldname,
                                                     ftype,
                                                     readable = False,
                                                     writable = False,
                                                     )

# =============================================================================
# Meta-fields
#
# Use URNs according to http://tools.ietf.org/html/rfc4122
s3uuid = SQLCustomType(type = "string",
                       native = "VARCHAR(128)",
                       encoder = lambda x: \
                                 "%s" % (uuid4().urn if x == "" else s3_str(x)),
                       decoder = lambda x: x,
                       )

# Representation of user roles (auth_group)
auth_group_represent = S3Represent(lookup="auth_group", fields=["role"])

META_FIELD_NAMES = ("uuid",
                    "mci",
                    "deleted",
                    "deleted_fk",
                    "deleted_rb",
                    "created_on",
                    "created_by",
                    "modified_on",
                    "modified_by",
                    "approved_by",
                    "owned_by_user",
                    "owned_by_group",
                    "realm_entity",
                    )

# -----------------------------------------------------------------------------
class MetaFields:
    """ Pseudoclass to standardize meta-fields """

    # -------------------------------------------------------------------------
    def __new__(cls, *args, **kwargs):
        """
            Returns a tuple of meta-fields

            For use in table definitions:
                db.define_table(..., *MetaFields())
        """

        return (cls.uuid(),
                cls.mci(),
                cls.deleted(),
                cls.deleted_fk(),
                cls.deleted_rb(),
                cls.created_on(),
                cls.created_by(),
                cls.modified_on(),
                cls.modified_by(),
                cls.approved_by(),
                cls.owned_by_user(),
                cls.owned_by_group(),
                cls.realm_entity(),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def uuid():
        """
            Universally unique record identifier according to RFC4122, as URN
            (e.g. "urn:uuid:fd8f97ab-1252-4d62-9982-8e3f3025307f"); uuids are
            mandatory for synchronization (incl. EdenMobile)
        """

        return Field("uuid", type=s3uuid,
                     default = "",
                     length = 128,
                     notnull = True,
                     unique = True,
                     readable = False,
                     writable = False,
                     )

    # -------------------------------------------------------------------------
    @staticmethod
    def mci():
        """
            Master-Copy-Index - whether this record has been created locally
            or imported ("copied") from another source:
                - mci=0 means "created here"
                - mci>0 means "copied n times"
        """

        return Field("mci", "integer",
                     default = 0,
                     readable = False,
                     writable = False,
                     )

    # -------------------------------------------------------------------------
    @staticmethod
    def deleted():
        """
            Deletion status (True=record is deleted)
        """

        return Field("deleted", "boolean",
                     default = False,
                     readable = False,
                     writable = False,
                     )

    # -------------------------------------------------------------------------
    @staticmethod
    def deleted_fk():
        """
            Foreign key values of this record before deletion (foreign keys
            are set to None during deletion to derestrict constraints)
        """

        return Field("deleted_fk", #"json",
                     readable = False,
                     writable = False,
                     )

    # -------------------------------------------------------------------------
    @staticmethod
    def deleted_rb():
        """
            De-duplication: ID of the record that has replaced this record
        """

        return Field("deleted_rb", "integer",
                     readable = False,
                     writable = False,
                     )

    # -------------------------------------------------------------------------
    @staticmethod
    def created_on():
        """
            Date/time when the record was created
        """

        return Field("created_on", "datetime",
                     readable = False,
                     writable = False,
                     default = datetime.datetime.utcnow,
                     )

    # -------------------------------------------------------------------------
    @staticmethod
    def modified_on():
        """
            Date/time when the record was last modified
        """

        return Field("modified_on", "datetime",
                     readable = False,
                     writable = False,
                     default = datetime.datetime.utcnow,
                     update = datetime.datetime.utcnow,
                     )

    # -------------------------------------------------------------------------
    @classmethod
    def created_by(cls):
        """
            Auth_user ID of the user who created the record
        """

        return Field("created_by", current.auth.settings.table_user,
                     readable = False,
                     writable = False,
                     requires = None,
                     default = cls._current_user(),
                     represent = cls._represent_user(),
                     ondelete = "RESTRICT",
                     )

    # -------------------------------------------------------------------------
    @classmethod
    def modified_by(cls):
        """
            Auth_user ID of the last user who modified the record
        """

        current_user = cls._current_user()
        return Field("modified_by", current.auth.settings.table_user,
                     readable = False,
                     writable = False,
                     requires = None,
                     default = current_user,
                     update = current_user,
                     represent = cls._represent_user(),
                     ondelete = "RESTRICT",
                     )

    # -------------------------------------------------------------------------
    @classmethod
    def approved_by(cls):
        """
            Auth_user ID of the user who has approved the record:
                - None means unapproved
                - 0 means auto-approved
        """

        return Field("approved_by", "integer",
                     readable = False,
                     writable = False,
                     requires = None,
                     represent = cls._represent_user(),
                     )

    # -------------------------------------------------------------------------
    @classmethod
    def owned_by_user(cls):
        """
            Auth_user ID of the user owning the record
        """

        return Field("owned_by_user", current.auth.settings.table_user,
                     readable = False,
                     writable = False,
                     requires = None,
                     default = cls._current_user(),
                     represent = cls._represent_user(),
                     ondelete = "RESTRICT",
                     )

    # -------------------------------------------------------------------------
    @staticmethod
    def owned_by_group():
        """
            Auth_group ID of the user role owning the record
        """

        return Field("owned_by_group", "integer",
                     default = None,
                     readable = False,
                     writable = False,
                     requires = None,
                     represent = auth_group_represent,
                     )

    # -------------------------------------------------------------------------
    @staticmethod
    def realm_entity():
        """
            PE ID of the entity managing the record
        """

        return Field("realm_entity", "integer",
                     default = None,
                     readable = False,
                     writable = False,
                     requires = None,
                     # using a lambda here as we don't want the model
                     # to be loaded yet:
                     represent = lambda pe_id: \
                                 current.s3db.pr_pentity_represent(pe_id),
                     )

    # -------------------------------------------------------------------------
    @classmethod
    def sync_meta_fields(cls):
        """
            Meta-fields required for sync

            Returns:
                tuple of Fields
        """

        return (cls.uuid(),
                cls.mci(),
                cls.deleted(),
                cls.deleted_fk(),
                cls.deleted_rb(),
                cls.created_on(),
                cls.modified_on(),
                )

    # -------------------------------------------------------------------------
    @classmethod
    def owner_meta_fields(cls):
        """
            Record ownership meta-fields

            Returns:
                tuple of Fields
        """

        return (cls.owned_by_user(),
                cls.owned_by_group(),
                cls.realm_entity(),
                )

    # -------------------------------------------------------------------------
    @classmethod
    def timestamps(cls):
        """
            Timestamp meta-fields

            Returns:
                tuple of Fields
        """

        return (cls.created_on(),
                cls.modified_on(),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def _current_user():
        """
            Get the user ID of the currently logged-in user

            Returns:
                auth_user ID
        """

        if current.auth.is_logged_in():
            # Not current.auth.user to support impersonation
            return current.session.auth.user.id
        else:
            return None

    # -------------------------------------------------------------------------
    @staticmethod
    def _represent_user():
        """
            Representation method for auth_user IDs

            Returns:
                representation function
        """

        return current.auth.user_represent

# =============================================================================
# Reusable roles fields

def s3_role_required():
    """
        Role Required to access a resource
        - used by GIS for map layer permissions management
    """

    T = current.T
    gtable = current.auth.settings.table_group
    represent = S3Represent(lookup="auth_group", fields=["role"])
    return Field("role_required", gtable,
                 sortby="role",
                 requires = IS_EMPTY_OR(
                                IS_ONE_OF(current.db, "auth_group.id",
                                          represent,
                                          zero=T("Public"))),
                 #widget = S3AutocompleteWidget("admin",
                 #                              "group",
                 #                              fieldname="role"),
                 represent = represent,
                 label = T("Role Required"),
                 comment = DIV(_class="tooltip",
                               _title="%s|%s" % (T("Role Required"),
                                                 T("If this record should be restricted then select which role is required to access the record here."),
                                                 ),
                               ),
                 ondelete = "RESTRICT",
                 )

# -----------------------------------------------------------------------------
def s3_roles_permitted(name="roles_permitted", **attr):
    """
        List of Roles Permitted to access a resource
        - used by CMS
    """

    T = current.T
    represent = S3Represent(lookup="auth_group", fields=["role"])
    if "label" not in attr:
        attr["label"] = T("Roles Permitted")
    if "sortby" not in attr:
        attr["sortby"] = "role"
    if "represent" not in attr:
        attr["represent"] = represent
    if "requires" not in attr:
        attr["requires"] = IS_EMPTY_OR(IS_ONE_OF(current.db,
                                                 "auth_group.id",
                                                 represent,
                                                 multiple=True))
    if "comment" not in attr:
        attr["comment"] = DIV(_class="tooltip",
                              _title="%s|%s" % (T("Roles Permitted"),
                                                T("If this record should be restricted then select which role(s) are permitted to access the record here.")))
    if "ondelete" not in attr:
        attr["ondelete"] = "RESTRICT"

    return Field(name, "list:reference auth_group", **attr)

# =============================================================================
class CommentsField(Field):
    """
        Standard comments field with suitable defaults
    """

    def __init__(self,
                 fieldname = "comments",
                 label = DEFAULT,
                 comment = DEFAULT,
                 represent = DEFAULT,
                 widget = DEFAULT,
                 placeholder = None,
                 **args):
        """
            Args:
                placeholder: a placeholder text for the input

            Other Args:
                - see Field
        """

        T = current.T

        if label is DEFAULT:
            label = T("Comments")

        if comment is DEFAULT:
            comment = DIV(_class="tooltip",
                          _title="%s|%s" % (T("Comments"),
                                            T("Please use this field to record any additional information, including a history of the record if it is updated."),
                                            ),
                          )

        if represent is DEFAULT:
            represent = s3_text_represent

        if widget is DEFAULT:
            from ..ui import s3_comments_widget
            if placeholder:
                widget = lambda f, v: \
                         s3_comments_widget(f, v, _placeholder=placeholder)
            else:
                widget = s3_comments_widget

        super().__init__(fieldname,
                         type = "text",
                         label = label,
                         comment = comment,
                         represent = represent,
                         widget = widget,
                         **args)

# =============================================================================
class CurrencyField(Field):
    """
        Standard currency field with suitable defaults
    """

    def __init__(self,
                 fieldname = "currency",
                 length = 3,
                 default = DEFAULT,
                 label = DEFAULT,
                 requires = DEFAULT,
                 writable = DEFAULT,
                 **args):
        """
            Args:
                - see Field
        """

        settings = current.deployment_settings

        if label is DEFAULT:
            label = current.T("Currency")

        if default is DEFAULT:
            default = settings.get_fin_currency_default()

        if requires is DEFAULT:
            currency_opts = settings.get_fin_currencies()
            requires = IS_IN_SET(list(currency_opts.keys()), zero=None)

        if writable is DEFAULT:
            writable = settings.get_fin_currency_writable()

        super().__init__(fieldname,
                         #type = "string",
                         default = default,
                         label = label,
                         length = length,
                         requires = requires,
                         writable = writable,
                         **args)

# =============================================================================
class LanguageField(Field):
    """
        Standard language selection field with suitable defaults
    """

    def __init__(self,
                 fieldname = "language",
                 length = 8,
                 default = DEFAULT,
                 label = DEFAULT,
                 represent = DEFAULT,
                 requires = DEFAULT,
                 empty = None,
                 select = DEFAULT,
                 translate = True,
                 **args):
        """

            Args:
                empty: allow the field to remain empty:
                       - None: accept empty, don't show empty-option (default)
                       - True: accept empty, show empty-option
                       - False: reject empty, don't show empty-option
                       (keyword ignored if a "requires" is passed)
                select: language selection as dict {code:name}, or None
                        to allow all available languages; if omitted, the
                        L10n_languages deployment setting will be used
                translate: translate the language names into the
                           current UI language

            Other Args:
                - see Field
        """

        if label is DEFAULT:
            label = current.T("Language")

        if default is DEFAULT:
            default = current.deployment_settings.get_L10n_default_language()

        if requires is DEFAULT:
            zero = "" if empty else None
            if select is DEFAULT:
                # Use L10n_languages deployment setting
                validator = IS_ISO639_2_LANGUAGE_CODE(sort = True,
                                                      translate = translate,
                                                      zero = zero,
                                                      )
            else:
                # Use language selection as specified
                # - can be None to denote "all available languages"
                validator = IS_ISO639_2_LANGUAGE_CODE(select = select,
                                                      sort = True,
                                                      translate = translate,
                                                      zero = zero,
                                                      )
            requires = validator if empty is False else IS_EMPTY_OR(validator)
        else:
            validator = None

        if represent is DEFAULT:
            if not validator:
                validator = IS_ISO639_2_LANGUAGE_CODE(translate=translate)
            represent = validator.represent

        # Remove any conflicting type argument
        args.pop("type", None)

        super().__init__(fieldname,
                         #type = "string",
                         label = label,
                         default = default,
                         represent = represent,
                         requires = requires,
                         **args)

# =============================================================================
class DateField(Field):
    """
        Standard date field with suitable defaults and options
    """

    def __init__(self,
                 fieldname = "date",
                 default = None,
                 label = DEFAULT,
                 represent = DEFAULT,
                 requires = DEFAULT,
                 widget = None,
                 calendar = None,
                 empty = None,
                 future = None,
                 past = None,
                 **args):
        """
            Args:
                default: the default date, or "now"
                calendar: the calendar to use
                empty: empty values allowed
                future: selectable future interval (months)
                past: selectable past interval (months)
            Keyword Args:
                set_min: set dynamic minimum for this date widget (DOM ID)
                set_max: set dynamic maximum for this date widget (DOM ID)
                month_selector: activate month-selector in calendar widget
            Other Args:
                - see Field

            Notes:
                - timezone-aware by default (stored as UTC)
        """

        # Default label
        if label is DEFAULT:
            label = current.T("Date")

        # Default value
        now = current.request.utcnow.date()
        if default == "now":
            default = now

        # Default widget
        if widget is None or widget == "calendar":

            widget_options = ("set_min", "set_max", "month_selector")
            widget_args = {}

            for option in widget_options:
                if option in args:
                    widget_args[option] = args.pop(option)

            widget_args["calendar"] = calendar

            # Past/future options
            if past is not None:
                widget_args["past_months"] = past
            if future is not None:
                widget_args["future_months"] = future

            widget = S3CalendarWidget(**widget_args)

        # Default representation
        if represent is DEFAULT:
            represent = lambda dt: \
                        S3DateTime.date_represent(dt, utc=True, calendar=calendar)

        # Default validation
        if requires is DEFAULT:
            if past is None and future is None:
                requires = IS_UTC_DATE(calendar=calendar)
            else:
                from dateutil.relativedelta import relativedelta
                minimum = maximum = None
                if past is not None:
                    minimum = now - relativedelta(months = past)
                if future is not None:
                    maximum = now + relativedelta(months = future)
                requires = IS_UTC_DATE(calendar = calendar,
                                       minimum = minimum,
                                       maximum = maximum,
                                       )

            if empty is not False:
                requires = IS_EMPTY_OR(requires)

        # Remove any conflicting type argument
        args.pop("type", None)

        super().__init__(fieldname,
                         type = "date",
                         default = default,
                         label = label,
                         represent = represent,
                         requires = requires,
                         widget = widget,
                         calendar = calendar,
                         **args)

# =============================================================================
class DateTimeField(Field):
    """
        Standard date+time field with suitable defaults and options

        Notes:
            - timezone-aware by default (stored as UTC)
    """

    def __init__(self,
                 fieldname = "date",
                 default = None,
                 label = DEFAULT,
                 represent = DEFAULT,
                 requires = DEFAULT,
                 widget = None,
                 calendar = None,
                 past = None,
                 future = None,
                 minimum = None,
                 maximum = None,
                 empty = None,
                 **args):
        """
            Args:
                default: the default datetime, or "now"
                widget: the widget, or one of "date"|"datetime"
                represent: the representation method, or one of "date"|"datetime"
                calendar: the calendar to use
                past: selectable past interval (hours)
                future: selectable future interval (hours)
                minimum: the earliest selectable datetime (overrides past)
                maximum: the latest selectable datetime (overrides future)
                empty: empty values allowed
            Keyword Args:
                set_min: set dynamic minimum for this date/time widget (DOM ID)
                set_max: set dynamic maximum for this date/time widget (DOM ID)
                month_selector: activate month-selector in calendar widget
            Other Args:
                - see Field
        """

        # Default label
        if label is DEFAULT:
            label = current.T("Date")

        # Default value
        now = current.request.utcnow
        if default == "now":
            default = now

        date_only = widget == "date"

        # Determine earliest/latest
        if date_only:
            if not minimum and past is not None:
                minimum = self._limit(-past, now=now)
            if not maximum and future is not None:
                maximum = self._limit(future, now=now)
        else:
            if not minimum and past is not None:
                minimum = now - datetime.timedelta(hours=past)
            if not maximum and future is not None:
                maximum = now + datetime.timedelta(hours=future)

        # Default widget
        if widget is None or widget in ("date", "datetime"):

            widget_options = ("set_min", "set_max", "month_selector", "minute_step")
            widget_args = {}
            for option in widget_options:
                if option in args:
                    widget_args[option] = args.pop(option)

            widget = S3CalendarWidget(calendar = calendar,
                                      timepicker = not date_only,
                                      minimum = minimum,
                                      maximum = maximum,
                                      **widget_args)

        # Default representation
        represent_method = None
        if represent is DEFAULT:
            represent = "date" if date_only else "datetime"
        if represent == "date":
            represent_method = S3DateTime.date_represent
        elif represent == "datetime":
            represent_method = S3DateTime.datetime_represent
        if represent_method:
            represent = lambda dt: \
                        represent_method(dt, utc=True, calendar=calendar)

        # Default validator and empty-option
        if requires is DEFAULT:
            valid = IS_UTC_DATE if date_only else IS_UTC_DATETIME
            requires = valid(calendar = calendar,
                             minimum = minimum,
                             maximum = maximum,
                             )
            if empty is not False:
                requires = IS_EMPTY_OR(requires)

        # Remove any conflicting type argument
        args.pop("type", None)

        super().__init__(fieldname,
                         type = "datetime",
                         label = label,
                         default = default,
                         widget = widget,
                         represent = represent,
                         requires = requires,
                         calendar = calendar,
                         **args)

    # -------------------------------------------------------------------------
    @staticmethod
    def _limit(delta, now=None):
        """
            Helper function to convert past/future hours into earliest/latest
            datetime, retaining day of month and time of day
        """

        if now is None:
            now = current.request.utcnow

        current_month = now.month
        years, hours = divmod(-delta, 8760)

        months = divmod(hours, 744)[0]
        if months > current_month:
            years += 1

        month = divmod((current_month - months) + 12, 12)[1]
        year = now.year - years

        return now.replace(month=month, year=year)

# =============================================================================
class TimeField(Field):
    """
        Standard time field with suitable defaults

        Notes:
            - not timezone-aware, default "now" is local time
    """

    def __init__(self,
                 fieldname = "time_of_day",
                 default = None,
                 label = DEFAULT,
                 represent = DEFAULT,
                 requires = DEFAULT,
                 widget = None,
                 empty = None,
                 **args):
        """
            Args:
                default: the default time, or "now"
                empty: empty values allowed

            Other Args:
                - see Field
        """

        if label is DEFAULT:
            label = current.T("Time of Day")

        now = S3DateTime.to_local(current.request.utcnow).time().replace(microsecond=0)
        if default == "now":
            default = now

        if widget is None:
            # adds .time class which launches fgtimepicker from s3.datepicker.js
            widget = TimeWidget.widget

        if requires is DEFAULT:
            requires = IS_TIME()
            if empty is not False:
                requires = IS_EMPTY_OR(requires)

        if represent is DEFAULT:
            represent = S3DateTime.time_represent

        # Remove any conflicting type argument
        args.pop("type", None)

        super().__init__(fieldname,
                         type = "time",
                         label = label,
                         default = default,
                         widget = widget,
                         represent = represent,
                         requires = requires,
                         **args)

# END =========================================================================
