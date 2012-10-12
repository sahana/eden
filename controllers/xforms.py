# -*- coding: utf-8 -*-

"""
    XForms - Controllers
"""

module = request.controller

# -----------------------------------------------------------------------------
def create():
    """
        Given a Table, returns an XForms to create an instance:
        http://code.javarosa.org/wiki/buildxforms
        http://www.w3schools.com/xforms/
        http://oreilly.com/catalog/9780596003692/preview.html
        Known field requirements that don't work properly:
        IS_IN_DB
        IS_NOT_ONE_OF
        IS_EMAIL
        IS_DATE_IN_RANGE
        IS_DATETIME_IN_RANGE
    """

    try:
        tablename = request.args[0]
    except:
        session.error = T("Need to specify a table!")
        redirect(URL(r=request))

    title = tablename
    table = s3db[tablename]

    instance_list = []
    bindings_list = []
    controllers_list = []
    itext_list = [TAG["text"](TAG["value"](s3.crud_strings[tablename].title_list),
                              _id="title")]

    for fieldname in table.fields:
        if fieldname in ["id", "created_on", "modified_on", "uuid", "mci",
                         "deleted", "created_by", "modified_by", "deleted_fk",
                         "owned_by_group", "owned_by_user"]:
            # These will get added server-side
            pass
        elif table[fieldname].writable == False:
            pass
        else:
            ref = "/" + title + "/" + fieldname
            instance_list.append(generate_instance(table, fieldname))
            bindings_list.append(generate_bindings(table, fieldname, ref))
            controller, _itext_list = generate_controllers(table, fieldname, ref)
            controllers_list.append(controller)
            itext_list.extend(_itext_list)

    #bindings_list.append(TAG["itext"](TAG["translation"](itext_list, _lang="eng")))
    instance = TAG[title](instance_list, _xmlns="")
    bindings = bindings_list
    controllers = TAG["h:body"](controllers_list)

    response.headers["Content-Type"] = "text/xml"
    response.view = "xforms.xml"

    return dict(title=title, instance=instance, bindings=bindings,
                controllers=controllers, itext_list=itext_list)

# -----------------------------------------------------------------------------
def uses_requirement(requirement, field):
    """
        Check if a given database field uses the specified requirement
        (IS_IN_SET, IS_INT_IN_RANGE, etc)
    """

    if hasattr(field.requires, "other") or requirement in str(field.requires):
        if hasattr(field.requires, "other"):
            if requirement in str(field.requires.other):
                return True
        elif requirement in str(field.requires):
            return True
    return False

# -----------------------------------------------------------------------------
def generate_instance(table, fieldname):
    """
        Generates XML for the instance of the specified field.
    """

    if table[fieldname].default:
        instance = TAG[fieldname](table[fieldname].default)
    else:
        instance = TAG[fieldname]()

    return instance

# -----------------------------------------------------------------------------
def generate_bindings(table, fieldname, ref):
    """
        Generates the XML for bindings for the specified database field.
    """

    field = table[fieldname]
    if "IS_NOT_EMPTY" in str(field.requires):
        required = "true()"
    else:
        required = "false()"

    if field.type == "string":
        _type = "string"
    elif field.type == "double":
        _type = "decimal"
    # Collect doesn't support datetime yet
    elif field.type == "date":
        _type = "date"
    elif field.type == "datetime":
        _type = "datetime"
    elif field.type == "integer":
        _type = "int"
    elif field.type == "boolean":
        _type = "boolean"
    elif field.type == "upload": # For images
        _type = "binary"
    elif field.type == "text":
        _type = "text"
    else:
         # Unknown type
         _type = "string"

    if uses_requirement("IS_INT_IN_RANGE", field) \
       or uses_requirement("IS_FLOAT_IN_RANGE", field):

        if hasattr(field.requires, "other"):
            maximum = field.requires.other.maximum
            minimum = field.requires.other.minimum
        else:
            maximum = field.requires.maximum
            minimum = field.requires.minimum
        if minimum is None:
            constraint = "(. < " + str(maximum) + ")"
        elif maximum is None:
            constraint = "(. > " + str(minimum) + ")"
        else:
            constraint = "(. > " + str(minimum) + " and . < " + str(maximum) + ")"
        binding = TAG["bind"](_nodeset=ref,
                              _type=_type,
                              _required=required,
                              _constraint=constraint)

    #elif uses_requirement("IS_DATETIME_IN_RANGE", field):
    #   pass

    #elif uses_requirement("IS_EMAIL", field):
    #   pass

    elif uses_requirement("IS_IN_SET", field):
        binding = TAG["bind"](_nodeset=ref, _required=required)

    else:
        binding = TAG["bind"](_nodeset=ref, _type=_type, _required=required)

    return binding

# -----------------------------------------------------------------------------
def generate_controllers(table, fieldname, ref):
    """
        Generates the controllers XML for the database table field.
    """

    itext_list = [] # Internationalization
    controllers_list = []

    field = table[fieldname]
    itext_list.append(TAG["text"](TAG["value"](field.label),
                                  _id=ref + ":label"))
    itext_list.append(TAG["text"](TAG["value"](field.comment),
                                  _id=ref + ":hint"))

    if hasattr(field.requires, "option"):
        items_list = []
        for option in field.requires.theset:
            items_list.append(TAG["item"](TAG["label"](option), TAG["value"](option)))
        controllers_list.append(TAG["select1"](items_list, _ref=fieldname))

    #elif uses_requirement("IS_IN_DB", field):
        # ToDo (similar to IS_IN_SET)?
        #pass

    #elif uses_requirement("IS_NOT_ONE_OF", field):
        # ToDo
        #pass

    elif uses_requirement("IS_IN_SET", field): # Defined below
        if hasattr(field.requires, "other"):
            insetrequires = field.requires.other
        else:
            insetrequires = field.requires
        theset = insetrequires.theset
        items_list = []
        items_list.append(TAG["label"](_ref="jr:itext('" + ref + ":label')"))
        items_list.append(TAG["hint"](_ref="jr:itext('" + ref + ":hint')"))

        if theset:
            option_num = 0 # for formatting something like "jr:itext('stuff:option0')"
            for option in theset:
                if field.type == "integer":
                    option = int(option)
                option_ref = ref + ":option" + str(option_num)
                items_list.append(TAG["item"](TAG["label"](_ref="jr:itext('" + option_ref + "')"),
                                              TAG["value"](option)))
                #itext_list.append(TAG["text"](TAG["value"](field.represent(option)), _id=option_ref))
                itext_list.append(TAG["text"](TAG["value"](insetrequires.labels[theset.index(str(option))]),
                                              _id=option_ref))
                option_num += 1
        if insetrequires.multiple:
            controller = TAG["select"](items_list, _ref=ref)
        else:
            controller = TAG["select1"](items_list, _ref=ref)

    elif field.type == "boolean": # Using select1, is there an easier way to do this?
        items_list=[]

        items_list.append(TAG["label"](_ref="jr:itext('" + ref + ":label')"))
        items_list.append(TAG["hint"](_ref="jr:itext('" + ref + ":hint')"))
        # True option
        items_list.append(TAG["item"](TAG["label"](_ref="jr:itext('" + ref + ":option0')"),
                                      TAG["value"](1)))
        itext_list.append(TAG["text"](TAG["value"]("True"),
                                      _id=ref + ":option0"))
        # False option
        items_list.append(TAG["item"](TAG["label"](_ref="jr:itext('" + ref + ":option1')"),
                                      TAG["value"](0)))
        itext_list.append(TAG["text"](TAG["value"]("False"),
                                      _id=ref + ":option1"))

        controller = TAG["select1"](items_list, _ref=ref)

    elif field.type == "upload": # For uploading images
        items_list=[]
        items_list.append(TAG["label"](_ref="jr:itext('" + ref + ":label')"))
        items_list.append(TAG["hint"](_ref="jr:itext('" + ref + ":hint')"))
        controller = TAG["upload"](items_list, _ref=ref, _mediatype="image/*")

    elif field.writable == False:
        controller = TAG["input"](TAG["label"](field.label), _ref=ref,
                                  _readonly="true",
                                  _default=field.default.upper())

    else:
        # Normal Input field
        controller = TAG["input"](TAG["label"](field.label), _ref=ref)

    return controller, itext_list

# -----------------------------------------------------------------------------
def csvdata(nodelist):
    """
        Returns the data in the given node as a comma separated string
    """

    data = ""
    for subnode in nodelist:
        if (subnode.nodeType == subnode.ELEMENT_NODE):
            try:
                data = data + "," + subnode.childNodes[0].data
            except:
                data = data+ ","
    return data[1:] + "\n"

# -----------------------------------------------------------------------------
def csvheader(parent, nodelist):
    """
        Gives the header for the CSV
    """

    header = ""
    for subnode in nodelist:
        if (subnode.nodeType == subnode.ELEMENT_NODE):
            header = header + "," + parent + "." + subnode.tagName
    return header[1:] + "\n"

# -----------------------------------------------------------------------------
def importxml(db, xmlinput):
    """
        Converts the XML to a CSV compatible with the import_from_csv_file of web2py
        @ToDo: rewrite this to go via S3Resource for proper Auth checking, Audit.
    """

    import cStringIO
    import xml.dom.minidom

    try:
        doc = xml.dom.minidom.parseString(xmlinput)
    except:
        raise Exception("XML parse error")

    parent = doc.childNodes[0].tagName
    csvout = csvheader(parent, doc.childNodes[0].childNodes)
    for subnode in doc.childNodes:
        csvout = csvout + csvdata(subnode.childNodes)
    fh = cStringIO.StringIO()
    fh.write(csvout)
    fh.seek(0, 0)
    db[parent].import_from_csv_file(fh)

# -----------------------------------------------------------------------------
@auth.s3_requires_membership(1)
def post():
    data = importxml(db, request.body.read())
    return data

# -----------------------------------------------------------------------------
def formList():
    """
        Generates a list of Xforms based on database tables for ODK Collect
        http://code.google.com/p/opendatakit/
    """

    # Test statements
    #xml = TAG.forms(*[TAG.form(getName("Name"), _url = "http://" + request.env.http_host + URL(c="static", "current.xml"))])
    #xml = TAG.forms(*[TAG.form(getName(t), _url = "http://" + request.env.http_host + URL(f="create", args=t)) for t in db.tables()])

    # List of a couple simple tables to avoid a giant list of all the tables
    #tables = ["pf_missing_report", "pr_presence"]
    tables = ["irs_ireport", "rms_req", "cr_shelter", "pr_person", "pr_image"]
    xml = TAG.forms()
    for tablename in tables:
        xml.append(TAG.form(get_name(tablename),
                            _url = "http://" + request.env.http_host + URL(f="create", args=tablename)))

    response.headers["Content-Type"] = "text/xml"
    response.view = "xforms.xml"
    return xml

# -----------------------------------------------------------------------------
@auth.s3_requires_membership(2)
def submission():
    """
        Allows for submission of Xforms by ODK Collect
        http://code.google.com/p/opendatakit/
    """

    try:
        from cStringIO import StringIO    # Faster, where available
    except:
        from StringIO import StringIO
    import cgi
    from lxml import etree

    source = request.post_vars.get("xml_submission_file", None)
    if isinstance(source, cgi.FieldStorage):
        if source.filename:
            xmlinput = source.file
        else:
            xmlinput = source.value

        if isinstance(xmlinput, basestring):
            xmlinput = StringIO(xmlinput)
    else:
        raise HTTP(400, "Invalid Request: Expected an XForm")

    tree = etree.parse(xmlinput)
    tablename = tree.getroot().tag

    resource = s3db.resource(tablename)

    stylesheet = os.path.join(request.folder, "static", "formats", "odk", "import.xsl")

    try:
        result = resource.import_xml(source=tree, stylesheet=stylesheet)
    except IOError, SyntaxError:
        raise HTTP(500, "Internal server error")

    # Parse response
    status = json.loads(result)["statuscode"]

    if status == 200:
        r = HTTP(201, "Saved") # ODK Collect only accepts 201
        r.headers["Location"] = request.env.http_host
        raise r
    else:
        raise HTTP(status, result)

# -----------------------------------------------------------------------------
@auth.s3_requires_membership(2)
def submission_old():
    """
        Allows for submission of xforms by ODK Collect
        http://code.google.com/p/opendatakit/
    """
    response.headers["Content-Type"] = "text/xml"
    xml = str(request.post_vars.xml_submission_file.value)
    if len(xml) == 0:
        raise HTTP(400, "Need some xml!")
    importxml(db, xml)
    r = HTTP(201, "Saved.")
    r.headers["Location"] = request.env.http_host
    raise r

# -----------------------------------------------------------------------------
def get_name(tablename):
    """
        Generates a pretty(er) name from a database table name.
    """

    return tablename[tablename.find("_") + 1:].replace("_", " ").capitalize()

# END =========================================================================
