# -*- coding: utf-8 -*-

"""
    Application Admin Controllers
"""

import os
import copy
import datetime
import re
from shutil import rmtree
#import socket

import gluon.contenttype
import gluon.fileutils

DEBUG = False
if DEBUG:
    print >> sys.stderr, "APPADMIN: DEBUG MODE"
    def _debug(m):
        print >> sys.stderr, m
else:
    _debug = lambda m: None

# ## critical --- make a copy of the environment

global_env = copy.copy(globals())
global_env["datetime"] = datetime

#
# Native Web2Py Auth (localhost & site password)
#
#http_host = request.env.http_host.split(":")[0]
#remote_addr = request.env.remote_addr
#try:
#    hosts = (http_host, socket.gethostbyname(remote_addr))
#except:
#    hosts = (http_host, )
#if remote_addr not in hosts:
#    raise HTTP(400)
#if not gluon.fileutils.check_credentials(request):
#    redirect("/admin")

#
# S3 Auth
#
if not s3_has_role(ADMIN):
    auth.permission.fail()

# Load all models
s3db.load_all_models()
_tables = db.tables
if settings.get_security_policy() not in (1, 2, 3, 4, 5, 6, 7, 8):
    # Web2Py security
    db.auth_permission.table_name.requires = IS_IN_SET(_tables)
#s3db.pr_pe_subscription.resource.requires = IS_IN_SET(_tables)
#s3db.msg_tag.resource.requires = IS_IN_SET(_tables)

module = "admin"

ignore_rw = True
response.view = "admin/appadmin.html"
#response.menu = [[T("design"), False, URL(a="admin", c="default", f="design",
#                 args=[appname])], [T("db"), False,
#                 URL(f="index")], [T("state"), False,
#                 URL(f="state")]]


# ##########################################################
# ## auxiliary functions
# ###########################################################


def get_databases(request):
    dbs = {}
    for (key, value) in global_env.items():
        cond = False
        try:
            cond = isinstance(value, GQLDB)
        except:
            cond = isinstance(value, SQLDB)
        if cond:
            dbs[key] = value
    return dbs


databases = get_databases(None)


def eval_in_global_env(text):
    exec ("_ret=%s" % text, {}, global_env)
    return global_env["_ret"]


def get_database(request):
    if request.args and request.args[0] in databases:
        return eval_in_global_env(request.args[0])
    else:
        session.flash = T("invalid request")
        redirect(URL(f="index"))


def get_table(request):
    db = get_database(request)
    if len(request.args) > 1 and request.args[1] in db.tables:
        return (db, request.args[1])
    else:
        session.flash = T("invalid request")
        redirect(URL(f="index"))


def get_query(request):
    try:
        return eval_in_global_env(request.vars.query)
    except Exception:
        return None


# ##########################################################
# ## list all databases and tables
# ###########################################################


def index():
    return dict(databases=databases)


# ##########################################################
# ## insert a new record
# ###########################################################


def insert():
    (db, table) = get_table(request)
    form = SQLFORM(db[table], ignore_rw=ignore_rw)
    if form.accepts(request.vars, session):
        response.flash = T("new record inserted")
    return dict(form=form)


# ##########################################################
# ## list all records in table and insert new record
# ###########################################################


def download():
    import os
    db = get_database(request)
    return response.download(request,db)

def csv():
    import gluon.contenttype
    response.headers["Content-Type"] = \
        gluon.contenttype.contenttype(".csv")
    db = get_database(request)
    query = get_query(request)
    if not query:
        return None
    response.headers["Content-disposition"] = "attachment; filename=%s_%s.csv"\
         % tuple(request.vars.query.split(".")[:2])
    return str(db(query).select())


def import_csv(table, file):
    table.import_from_csv_file(file)

def select():
    import re
    db = get_database(request)
    dbname = request.args[0]
    regex = re.compile('(?P<table>\w+)\.(?P<field>\w+)=(?P<value>\d+)')
    if request.vars.query:
        match = regex.match(request.vars.query)
        if match:
            request.vars.query = '%s.%s.%s==%s' % (request.args[0],
                    match.group('table'), match.group('field'),
                    match.group('value'))
    else:
        request.vars.query = session.last_query
    query = get_query(request)
    if request.vars.start:
        start = int(request.vars.start)
    else:
        start = 0
    nrows = 0
    stop = start + 50
    table = None
    rows = []
    orderby = request.vars.orderby
    if orderby:
        orderby = dbname + '.' + orderby
        if orderby == session.last_orderby:
            if orderby[0] == '~':
                orderby = orderby[1:]
            else:
                orderby = '~' + orderby
    session.last_orderby = orderby
    session.last_query = request.vars.query
    form = FORM(TABLE(TR(T('Query') + ':', '', INPUT(_style='width:400px',
                _name='query', _value=request.vars.query or '',
                requires=IS_NOT_EMPTY(error_message=T("Cannot be empty")))), TR(T('Update') + ':',
                INPUT(_name='update_check', _type='checkbox',
                value=False), INPUT(_style='width:400px',
                _name='update_fields', _value=request.vars.update_fields
                 or '')), TR(T('Delete') + ":", INPUT(_name='delete_check',
                _class='delete', _type='checkbox', value=False), ''),
                TR('', '', INPUT(_type='submit', _value='submit'))),
                _action=URL(args=request.args))
    if request.vars.csvfile != None:
        try:
            import_csv(db[request.vars.table],
                       request.vars.csvfile.file)
            response.flash = T('data uploaded')
        except:
            response.flash = T('unable to parse csv file')
    if form.accepts(request.vars, formname=None):
        regex = re.compile(request.args[0] + '\.(?P<table>\w+)\.id\>0')
        match = regex.match(form.vars.query.strip())
        if match:
            table = match.group('table')
        try:
            nrows = db(query).count()
            if form.vars.update_check and form.vars.update_fields:
                db(query).update(**eval_in_global_env('dict(%s)'
                                  % form.vars.update_fields))
                response.flash = T('%s rows updated', nrows)
            elif form.vars.delete_check:
                db(query).delete()
                response.flash = T('%s rows deleted', nrows)
            nrows = db(query).count()
            if orderby:
                rows = db(query).select(limitby=(start, stop),
                        orderby=eval_in_global_env(orderby))
            else:
                rows = db(query).select(limitby=(start, stop))
        except:
            (rows, nrows) = ([], 0)
            response.flash = T('Invalid Query')
    return dict(
        form=form,
        table=table,
        start=start,
        stop=stop,
        nrows=nrows,
        rows=rows,
        query=request.vars.query
        )


# ##########################################################
# ## edit delete one record
# ###########################################################


def update():
    (db, table) = get_table(request)
    try:
        id = int(request.args[2])
        record = db(db[table].id == id).select().first()
    except:
        session.flash = T('record does not exist')
        redirect(URL(f='select', args=request.args[:1],
                 vars=dict(query='%s.%s.id>0'
                  % tuple(request.args[:2]))))
    form = SQLFORM(db[table], record, deletable=True, delete_label=T('Check to delete'), ignore_rw=ignore_rw,
                   linkto=URL(f='select',
                   args=request.args[:1]), upload=URL(f='download', args=request.args[:1]))
    if form.accepts(request.vars, session):
        response.flash = T('done!')
        redirect(URL(f='select', args=request.args[:1],
                 vars=dict(query='%s.%s.id>0'
                  % tuple(request.args[:2]))))
    return dict(form=form)


# ##########################################################
# ## get global variables
# ###########################################################


def state():
    return dict()

# ##########################################################
# ## drop schema
# ###########################################################

def dropall():
    def dropUnRefTables(tables):
        tableList = []
        for table in tables:
            tableList.append(table)
        refList = []
        for table in tableList:
            # Only drop the table if it is not referenced by another table
            if table._referenced_by == []:
                try:
                    table.drop()
                except:
                    pass # something is referencing it
            # Drop the table if it's only reference is a self reference
            elif (len(table._referenced_by) == 1) and (str(table._referenced_by[0][0]) == str(table)):
                table.drop()
            # store the table on refList for furterh processing
            else:
                refList.append(table)
        return refList

    def dropRefTables(tableList, sqlite):
        for table in tableList:
            _debug ("%s is referenced by:" % table)
            for ref in table._referenced_by:
                _debug ("   %s, %s" % ref)
            if not sqlite:
                query = 'DROP TABLE %s CASCADE;' % table
                table._db._adapter.execute(query)
                table._db.commit()
                del table._db[table._tablename]
                del table._db.tables[table._db.tables.index(table._tablename)]
                table._db._update_referenced_by(table._tablename)
            if table._dbt:
                os.unlink(table._dbt)

    db = databases["db"]
    if db._dbname.find("sqlite") != -1:
        sqlite = True
    else:
        sqlite = False
    integrityError = False
    tableList = []
    for table in db:
        tableList.append(table)
    total = len(tableList)
    newTotal = 0
    runCnt = 1
    finished = False
    while not finished:
        _debug ("Run number %s tables in db = %s" % (runCnt, total))
        tableList = dropUnRefTables(tableList)
        newTotal = len(tableList)
        if (total-newTotal == 0) or (newTotal == 0):
            finished = True
        _debug ('   Deleted %s tables' % (total-newTotal))
        _debug ('   Remaining %s tables' % (newTotal))
        total = len(tableList)
        runCnt += 1
    dropRefTables(tableList, sqlite)
    session.forget()
    sessionDir = os.path.dirname(response.session_filename)
    rmtree(sessionDir, ignore_errors=True)
    return dict(databases=databases)

