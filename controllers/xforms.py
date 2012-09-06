# -*- coding: utf-8 -*-

"""
    XForms - Controllers
"""

module = request.controller

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
    if len(request.args) == 0:
        session.error = T("Need to specify a table!")
        redirect(URL(r=request))
    _table = request.args[0]

    title = _table
    table = db[_table]

    instance_list = []
    bindings_list = []
    controllers_list = []
    itext_list = [TAG["text"](TAG["value"](s3.crud_strings[_table].title_list), _id="title"),]

    for field in table.fields:
        if field in ["id", "created_on", "modified_on", "uuid", "mci", "deleted",
                     "created_by", "modified_by", "deleted_fk", "owned_by_group",
                     "owned_by_user"]:
            # This will get added server-side
            pass
        elif table[field].writable == False and table[field].readable == False:
            pass
        else:
            ref = "/" + title + "/" + field
            instance_list.append(generate_instance(table, field))
            bindings_list.append(generate_bindings(table, field, ref))
            controller, _itext_list = generate_controllers(table, field, ref)
            controllers_list.append(controller)
            itext_list.extend(_itext_list)

    #bindings_list.append(TAG["itext"](TAG["translation"](itext_list,_lang="eng")))
    instance = TAG[title](instance_list, _xmlns="")
    bindings = bindings_list
    controllers = TAG["h:body"](controllers_list)

    response.headers["Content-Type"] = "text/xml"
    response.view = "xforms.xml"

    return dict(title=title, instance=instance, bindings=bindings, controllers=controllers, itext_list=itext_list)

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

def generate_instance(table, field):
    """
    Generates XML for the instance of the specified field.
    """

    if table[field].default:
        instance = TAG[field](table[field].default)
    else:
        instance = TAG[field]()

    return instance

def generate_bindings(table, field, ref):
    """
    Generates the XML for bindings for the specified database field.
    """

    if "IS_NOT_EMPTY" in str(table[field].requires):
        required = "true()"
    else:
        required = "false()"

    if table[field].type == "string":
        _type = "string"
    elif table[field].type == "double":
        _type = "decimal"
    # Collect doesn't support datetime yet
    elif table[field].type == "date":
        _type = "date"
    elif table[field].type == "datetime":
        _type = "datetime"
    elif table[field].type == "integer":
        _type = "int"
    elif table[field].type == "boolean":
        _type = "boolean"
    elif table[field].type == "upload": # For images
        _type = "binary"
    elif table[field].type == "text":
        _type = "text"
    else:
         # Unknown type
         _type = "string"

    if uses_requirement("IS_INT_IN_RANGE", table[field]) \
       or uses_requirement("IS_FLOAT_IN_RANGE", table[field]):

        if hasattr(table[field].requires, "other"):
            maximum = table[field].requires.other.maximum
            minimum = table[field].requires.other.minimum
        else:
            maximum = table[field].requires.maximum
            minimum = table[field].requires.minimum
        if minimum is None:
            constraint = "(. < " + str(maximum) + ")"
        elif maximum is None:
            constraint = "(. > " + str(minimum) + ")"
        else:
            constraint = "(. > " + str(minimum) + " and . < " + str(maximum) + ")"
        binding = TAG["bind"](_nodeset=ref, _type=_type, _required=required, _constraint=constraint)
#   elif uses_requirement("IS_DATETIME_IN_RANGE", field):
#      pass
#   elif uses_requirement("IS_EMAIL", field):
#      pass
    elif uses_requirement("IS_IN_SET", table[field]):
        binding = TAG["bind"](_nodeset=ref, _required=required)
    else:
        binding = TAG["bind"](_nodeset=ref, _type=_type, _required=required)

    return binding

def generate_controllers(table, field, ref):
    """
    Generates the controllers XML for the database table field.
    """
    itext_list = [] # Internationalization
    controllers_list = []

    itext_list.append(TAG["text"](TAG["value"](table[field].label), _id=ref + ":label"))
    itext_list.append(TAG["text"](TAG["value"](table[field].comment), _id=ref + ":hint"))

    if hasattr(table[field].requires, "option"):
        items_list = []
        for option in table[field].requires.theset:
            items_list.append(TAG["item"](TAG["label"](option), TAG["value"](option)))
        controllers_list.append(TAG["select1"](items_list, _ref=field))
    #elif uses_requirement("IS_IN_DB", field):
        # ToDo (similar to IS_IN_SET)?
        #pass
    #elif uses_requirement("IS_NOT_ONE_OF", field):
        # ToDo
        #pass
    elif uses_requirement("IS_IN_SET", table[field]): # Defined below
        if hasattr(table[field].requires, "other"):
            insetrequires = table[field].requires.other
        else:
            insetrequires = table[field].requires
        theset = insetrequires.theset
        items_list=[]
        items_list.append(TAG["label"](_ref="jr:itext('" + ref + ":label')"))
        items_list.append(TAG["hint"](_ref="jr:itext('" + ref + ":hint')"))

        option_num = 0 # for formatting something like "jr:itext('stuff:option0')"
        for option in theset:
            if table[field].type == "integer":
                option = int(option)
            option_ref = ref + ":option" + str(option_num)
            items_list.append(TAG["item"](TAG["label"](_ref="jr:itext('" + option_ref + "')"), TAG["value"](option)))
            #itext_list.append(TAG["text"](TAG["value"](table[field].represent(option)), _id=option_ref))
            itext_list.append(TAG["text"](TAG["value"](insetrequires.labels[theset.index(str(option))]), _id=option_ref))
            option_num += 1
        if insetrequires.multiple:
            controller = TAG["select"](items_list, _ref=ref)
        else:
            controller = TAG["select1"](items_list, _ref=ref)

    elif table[field].type == "boolean": # Using select1, is there an easier way to do this?
        items_list=[]

        items_list.append(TAG["label"](_ref="jr:itext('" + ref + ":label')"))
        items_list.append(TAG["hint"](_ref="jr:itext('" + ref + ":hint')"))
        # True option
        items_list.append(TAG["item"](TAG["label"](_ref="jr:itext('" + ref + ":option0')"), TAG["value"](1)))
        itext_list.append(TAG["text"](TAG["value"]("True"), _id=ref + ":option0"))
        # False option
        items_list.append(TAG["item"](TAG["label"](_ref="jr:itext('" + ref + ":option1')"), TAG["value"](0)))
        itext_list.append(TAG["text"](TAG["value"]("False"), _id=ref + ":option1"))

        controller = TAG["select1"](items_list, _ref=ref)

    elif table[field].type == "upload": # For uploading images
        items_list=[]

        items_list.append(TAG["label"](_ref="jr:itext('" + ref + ":label')"))
        items_list.append(TAG["hint"](_ref="jr:itext('" + ref + ":hint')"))
        controller = TAG["upload"](items_list, _ref=ref, _mediatype="image/*")
    elif table[field].writable == False:
        controller = TAG["input"](TAG["label"](table[field].label), _ref=ref, _readonly="true", _default=table[field].default.upper())
    else:
        # Normal Input field
        controller = TAG["input"](TAG["label"](table[field].label), _ref=ref)

    return controller, itext_list

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

def csvheader(parent, nodelist):
    """
    Gives the header for the CSV
    """

    header = ""
    for subnode in nodelist:
        if (subnode.nodeType == subnode.ELEMENT_NODE):
            header = header + "," + parent + "." + subnode.tagName
    return header[1:] + "\n"

def importxml(db, xmlinput):
    """
    Converts the XML to a CSV compatible with the import_from_csv_file of web2py
    ToDo: rewrite this to go via S3XRC for proper Authz checking, Audit, Create/Update checking.
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

@auth.s3_requires_membership(1)
def post():
    data = importxml(db, request.body.read())
    return data

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

@auth.s3_requires_membership(2)
def submission():
    """
    Allows for submission of Xforms by ODK Collect
    using the S3XRC framework.
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
    resource = tree.getroot().tag

    prefix, name = resource.split("_")
    res = current.s3db.resource(resource)

    stylesheet = os.path.join(request.folder, "static", "formats", "odk", "import.xsl")

    try:
        result = res.import_xml(source=tree, stylesheet=stylesheet)
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

def formList():
    """
    Generates a list of Xforms based on database tables for ODK Collect
    http://code.google.com/p/opendatakit/
    ToDo: Provide a static list of forms, such as RMS_Req, GIS_Landmark, MPR_Missing_Report, CR_Shelter, PR_Presence
    """
    # Test statements
    #xml = TAG.forms(*[TAG.form(getName("Name"), _url = "http://" + request.env.http_host + URL(c="static", "current.xml"))])
    #xml = TAG.forms(*[TAG.form(getName(t), _url = "http://" + request.env.http_host + URL(f="create", args=t)) for t in db.tables()])

    # List of a couple simple tables to avoid a giant list of all the tables
    tables = ["rms_req", "pf_missing_report", "cr_shelter", "pr_presence", "pr_person", "pr_image"]
    xml = TAG.forms()
    for table in tables:
        xml.append(TAG.form(get_name(table), _url = "http://" + request.env.http_host + URL(f="create", args=db[table])))

    response.headers["Content-Type"] = "text/xml"
    response.view = "xforms.xml"
    return xml

def get_name(name):
    """
        Generates a pretty(er) name from a database table name.
    """
    return name[name.find("_") + 1:].replace("_", " ").capitalize()


