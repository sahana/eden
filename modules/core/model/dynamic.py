"""
    Dynamic Table Models

    Copyright: 2009-2022 (c) Sahana Software Foundation

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

__all__ = ("DynamicTableModel",
           "DYNAMIC_PREFIX",
           "SERIALIZABLE_OPTS",
           )

from collections import OrderedDict

from gluon import current, IS_EMPTY_OR, IS_FLOAT_IN_RANGE, IS_INT_IN_RANGE, \
                  IS_IN_SET, IS_NOT_EMPTY, SQLFORM
from gluon.storage import Storage

from s3dal import Field

from ..tools import IS_ONE_OF, IS_JSONS3, S3Represent
from ..ui import s3_comments_widget, s3_richtext_widget

DYNAMIC_PREFIX = "s3dt"
# Table options that are always JSON-serializable objects,
# and can thus be passed as-is from dynamic model "settings"
# to s3db.configure (& thence to mobile table.settings)
SERIALIZABLE_OPTS = ("autosync",
                     "autototals",
                     "card",
                     "grids",
                     "insertable",
                     "show_hidden",
                     "subheadings",
                     )

DEFAULT = lambda: None

# =============================================================================
class DynamicTableModel:
    """
        Class representing a dynamic table model
    """

    def __init__(self, tablename):
        """
            Args:
                tablename: the table name
        """

        self.tablename = tablename
        table = self.define_table(tablename)
        if table:
            self.table = table
        else:
            raise AttributeError("Undefined dynamic model: %s" % tablename)

    # -------------------------------------------------------------------------
    def define_table(self, tablename):
        """
            Instantiate a dynamic Table

            Args:
                tablename: the table name

            Returns:
                a Table instance
        """

        # Is the table already defined?
        db = current.db
        redefine = tablename in db

        # Load the table model
        s3db = current.s3db
        ttable = s3db.s3_table
        ftable = s3db.s3_field
        query = (ttable.name == tablename) & \
                (ttable.deleted == False) & \
                (ftable.table_id == ttable.id)
        rows = db(query).select(ftable.name,
                                ftable.field_type,
                                ftable.label,
                                ftable.require_unique,
                                ftable.require_not_empty,
                                ftable.options,
                                ftable.default_value,
                                ftable.settings,
                                ftable.comments,
                                )
        if not rows:
            return None

        # Instantiate the fields
        fields = []
        for row in rows:
            field = self._field(tablename, row)
            if field:
                fields.append(field)

        # Automatically add standard meta-fields
        from .fields import MetaFields
        fields.extend(MetaFields())

        # Define the table
        if fields:
            # Enable migrate
            # => is globally disabled when settings.base.migrate
            #    is False, overriding the table parameter
            migrate_enabled = db._migrate_enabled
            db._migrate_enabled = True

            # Define the table
            db.define_table(tablename,
                            migrate = True,
                            redefine = redefine,
                            *fields)

            # Instantiate table
            # => otherwise lazy_tables may prevent it
            table = db[tablename]

            # Restore global migrate_enabled
            db._migrate_enabled = migrate_enabled

            # Configure the table
            self._configure(tablename)

            return table
        else:
            return None

    # -------------------------------------------------------------------------
    @staticmethod
    def _configure(tablename):
        """
            Configure the table (e.g. CRUD strings)
        """

        s3db = current.s3db

        # Load table configuration settings
        ttable = s3db.s3_table
        query = (ttable.name == tablename) & \
                (ttable.deleted == False)
        row = current.db(query).select(ttable.title,
                                       ttable.settings,
                                       limitby = (0, 1),
                                       ).first()
        if row:
            # Configure CRUD strings
            title = row.title
            if title:
                current.response.s3.crud_strings[tablename] = Storage(
                    title_list = current.T(title),
                    )

            # Table Configuration
            settings = row.settings
            if settings:

                config = {"orderby": "%s.created_on" % tablename,
                          }

                # CRUD Form
                crud_fields = settings.get("form")
                if crud_fields:
                    from ..ui import CustomForm
                    try:
                        crud_form = CustomForm(**crud_fields)
                    except:
                        pass
                    else:
                        config["crud_form"] = crud_form

                # Mobile Form
                mobile_form = settings.get("mobile_form")
                if type(mobile_form) is list:
                    config["mobile_form"] = mobile_form

                # JSON-serializable config options can be configured
                # without pre-processing
                for key in SERIALIZABLE_OPTS:
                    setting = settings.get(key)
                    if setting:
                        config[key] = setting

                # Apply config
                if config:
                    s3db.configure(tablename, **config)

    # -------------------------------------------------------------------------
    @classmethod
    def _field(cls, tablename, row):
        """
            Convert a s3_field Row into a Field instance

            Args:
                tablename: the table name
                row: the s3_field Row

            Returns:
                a Field instance
        """

        field = None

        if row:

            # Type-specific field constructor
            fieldtype = row.field_type
            if row.options:
                construct = cls._options_field
            elif fieldtype == "date":
                construct = cls._date_field
            elif fieldtype == "datetime":
                construct = cls._datetime_field
            elif fieldtype[:9] == "reference":
                construct = cls._reference_field
            elif fieldtype == "boolean":
                construct = cls._boolean_field
            elif fieldtype in ("integer", "double"):
                construct = cls._numeric_field
            elif fieldtype == "json":
                construct = cls._json_field
            else:
                construct = cls._generic_field

            field = construct(tablename, row)
            if not field:
                return None

            requires = field.requires

            # Handle require_not_empty
            if fieldtype != "boolean":
                if row.require_not_empty:
                    if not requires:
                        requires = IS_NOT_EMPTY()
                elif requires:
                    requires = IS_EMPTY_OR(requires)

            field.requires = requires

            # Field label and comment
            T = current.T
            label = row.label
            if not label:
                fieldname = row.name
                label = " ".join(s.capitalize() for s in fieldname.split("_"))
            if label:
                field.label = T(label)
            comments = row.comments
            if comments:
                field.comment = T(comments)

            # Field settings
            settings = row.settings
            if settings:
                field.s3_settings = settings

        return field

    # -------------------------------------------------------------------------
    @staticmethod
    def _generic_field(tablename, row):
        """
            Generic field constructor

            Args:
                tablename: the table name
                row: the s3_field Row

            Returns:
                the Field instance
        """

        fieldname = row.name
        fieldtype = row.field_type

        multiple = fieldtype[:5] == "list:"

        if row.require_unique and not multiple:
            from ..tools import IS_NOT_ONE_OF
            requires = IS_NOT_ONE_OF(current.db, "%s.%s" % (tablename,
                                                            fieldname,
                                                            ),
                                     )
        else:
            requires = None

        if fieldtype in ("string", "text"):
            default = row.default_value
            settings = row.settings or {}
            widget = settings.get("widget")
            if widget == "richtext":
                widget = s3_richtext_widget
            elif widget == "comments":
                widget = s3_comments_widget
            else:
                widget = None
        else:
            default = None
            widget = None

        field = Field(fieldname, fieldtype,
                      default = default,
                      requires = requires,
                      widget = widget,
                      )
        return field

    # -------------------------------------------------------------------------
    @staticmethod
    def _options_field(tablename, row):
        """
            Options-field constructor

            Args:
                tablename: the table name
                row: the s3_field Row

            Returns:
                the Field instance
        """

        fieldname = row.name
        fieldtype = row.field_type
        fieldopts = row.options

        settings = row.settings or {}

        # Always translate options unless translate_options is False
        translate = settings.get("translate_options", True)
        T = current.T

        from ..tools import s3_str

        multiple = fieldtype[:5] == "list:"
        sort = False
        zero = ""

        if isinstance(fieldopts, dict):
            options = fieldopts
            if translate:
                options = {k: T(v) for k, v in options.items()}
            options_dict = options
            # Sort options unless sort_options is False (=default True)
            sort = settings.get("sort_options", True)

        elif isinstance(fieldopts, list):
            options = []
            for opt in fieldopts:
                if isinstance(opt, (tuple, list)) and len(opt) >= 2:
                    k, v = opt[:2]
                else:
                    k, v = opt, s3_str(opt)
                if translate:
                    v = T(v)
                options.append((k, v))
            options_dict = dict(options)
            # Retain list order unless sort_options is True (=default False)
            sort = settings.get("sort_options", False)

        else:
            options_dict = options = {}

        # Apply default value (if it is a valid option)
        default = row.default_value
        if default is not None:
            if multiple:
                if default and default[0] == "[":
                    # Attempt to JSON-parse the default value
                    import json
                    from ..tools import JSONERRORS
                    try:
                        default = json.loads(default)
                    except JSONERRORS:
                        pass
                if not isinstance(default, list):
                    default = [default]
                zero = None
            elif s3_str(default) in (s3_str(k) for k in options_dict):
                # No zero-option if we have a default value and
                # the field must not be empty:
                zero = None if row.require_not_empty else ""
            else:
                default = None

        # Widget?
        widget = settings.get("widget")
        len_options = len(options)
        if multiple:
            if widget and widget == "groupedopts" or \
               not widget and len_options < 8:
                from ..ui import S3GroupedOptionsWidget
                widget = S3GroupedOptionsWidget(cols=4)
            else:
                from ..ui import S3MultiSelectWidget
                widget = S3MultiSelectWidget()
        elif widget and widget == "radio" or \
             not widget and len_options < 4:
            widget = lambda field, value: \
                         SQLFORM.widgets.radio.widget(field,
                                                      value,
                                                      cols = len_options,
                                                      )
        else:
            widget = None

        if multiple and row.require_not_empty and len_options:
            # Require at least one option selected, otherwise
            # IS_IN_SET will pass with no options selected:
            multiple = (1, len_options + 1)

        field = Field(fieldname, fieldtype,
                      default = default,
                      represent = S3Represent(options = options_dict,
                                              multiple = multiple,
                                              translate = translate,
                                              ),
                      requires = IS_IN_SET(options,
                                           multiple = multiple,
                                           sort = sort,
                                           zero = zero,
                                           ),
                      widget = widget,
                      )
        return field

    # -------------------------------------------------------------------------
    @staticmethod
    def _date_field(tablename, row):
        """
            Date field constructor

            Args:
                tablename: the table name
                row: the s3_field Row

            Returns:
                the Field instance
        """

        fieldname = row.name
        settings = row.settings or {}

        attr = {}
        for keyword in ("past", "future"):
            setting = settings.get(keyword, DEFAULT)
            if setting is not DEFAULT:
                attr[keyword] = setting
        attr["empty"] = False

        default = row.default_value
        if default:
            if default == "now":
                attr["default"] = default
            else:
                from ..tools import s3_decode_iso_datetime
                try:
                    dt = s3_decode_iso_datetime(default)
                except ValueError:
                    # Ignore
                    pass
                else:
                    attr["default"] = dt.date()

        from .fields import DateField
        field = DateField(fieldname, **attr)

        return field

    # -------------------------------------------------------------------------
    @staticmethod
    def _datetime_field(tablename, row):
        """
            DateTime field constructor

            Args:
                tablename: the table name
                row: the s3_field Row

            Returns:
                the Field instance
        """

        fieldname = row.name
        settings = row.settings or {}

        attr = {}
        for keyword in ("past", "future"):
            setting = settings.get(keyword, DEFAULT)
            if setting is not DEFAULT:
                attr[keyword] = setting
        attr["empty"] = False

        default = row.default_value
        if default:
            if default == "now":
                attr["default"] = default
            else:
                from ..tools import s3_decode_iso_datetime
                try:
                    dt = s3_decode_iso_datetime(default)
                except ValueError:
                    # Ignore
                    pass
                else:
                    attr["default"] = dt

        from .fields import DateTimeField
        field = DateTimeField(fieldname, **attr)

        return field

    # -------------------------------------------------------------------------
    @staticmethod
    def _reference_field(tablename, row):
        """
            Reference field constructor

            Args:
                tablename: the table name
                row: the s3_field Row

            Returns:
                the Field instance
        """

        fieldname = row.name
        fieldtype = row.field_type

        ktablename = fieldtype.split(" ", 1)[1].split(".", 1)[0]
        ktable = current.s3db.table(ktablename)
        if ktable:
            if "name" in ktable.fields:
                represent = S3Represent(lookup = ktablename,
                                        translate = True,
                                        )
            else:
                represent = None
            requires = IS_ONE_OF(current.db, str(ktable._id),
                                 represent,
                                 )
            field = Field(fieldname, fieldtype,
                          represent = represent,
                          requires = requires,
                          )
        else:
            field = None

        return field

    # -------------------------------------------------------------------------
    @staticmethod
    def _numeric_field(tablename, row):
        """
            Numeric field constructor

            Args:
                tablename: the table name
                row: the s3_field Row

            Returns:
                the Field instance
        """

        fieldname = row.name
        fieldtype = row.field_type

        settings = row.settings or {}
        minimum = settings.get("min")
        maximum = settings.get("max")

        if fieldtype == "integer":
            parse = int
            requires = IS_INT_IN_RANGE(minimum=minimum,
                                       maximum=maximum,
                                       )
        elif fieldtype == "double":
            parse = float
            requires = IS_FLOAT_IN_RANGE(minimum=minimum,
                                         maximum=maximum,
                                         )
        else:
            parse = None
            requires = None

        default = row.default_value
        if default and parse is not None:
            try:
                default = parse(default)
            except ValueError:
                default = None
        else:
            default = None

        field = Field(fieldname, fieldtype,
                      default = default,
                      requires = requires,
                      )
        return field

    # -------------------------------------------------------------------------
    @staticmethod
    def _boolean_field(tablename, row):
        """
            Boolean field constructor

            Args:
                tablename: the table name
                row: the s3_field Row

            Returns:
                the Field instance
        """

        fieldname = row.name
        fieldtype = row.field_type

        default = row.default_value
        if default:
            default = default.lower()
            if default == "true":
                default = True
            elif default == "none":
                default = None
            else:
                default = False
        else:
            default = False

        settings = row.settings or {}

        # NB no IS_EMPTY_OR for boolean-fields:
        # => NULL values in SQL are neither True nor False, so always
        #    require special handling; to prevent that, we remove the
        #    default IS_EMPTY_OR and always set a default
        # => DAL converts everything that isn't True to False anyway,
        #    so accepting an empty selection would create an
        #    implicit default with no visible feedback (poor UX)

        widget = settings.get("widget")
        if widget == "radio":
            # Render two radio-buttons Yes|No
            T = current.T
            requires = [IS_IN_SET(OrderedDict([(True, T("Yes")),
                                               (False, T("No")),
                                               ]),
                                  # better than "Value not allowed"
                                  error_message = T("Please select a value"),
                                  ),
                        # Form option comes in as str
                        # => convert to boolean
                        lambda v: (str(v) == "True", None),
                        ]
            widget = lambda field, value: \
                     SQLFORM.widgets.radio.widget(field, value, cols=2)
        else:
            # Remove default IS_EMPTY_OR
            requires = None

            # Default single checkbox widget
            widget = None

        from ..tools import s3_yes_no_represent
        field = Field(fieldname, fieldtype,
                      default = default,
                      represent = s3_yes_no_represent,
                      requires = requires,
                      )

        if widget:
            field.widget = widget

        return field

    # -------------------------------------------------------------------------
    @staticmethod
    def _json_field(tablename, row):
        """
            Boolean field constructor

            Args:
                tablename: the table name
                row: the s3_field Row

            Returns:
                the Field instance
        """

        fieldname = row.name
        fieldtype = row.field_type

        default = row.default_value
        if default:
            value, error = IS_JSONS3()(default)
            default = None if error else value

        field = Field(fieldname, fieldtype,
                      default = default,
                      requires = IS_JSONS3(),
                      )

        return field

# END =========================================================================
