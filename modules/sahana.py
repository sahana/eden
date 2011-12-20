# -*- coding: utf-8 -*-

"""
    S3 Class (deprecated)

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @author: Fran Boon <fran@aidiq.com>
    @copyright: 2009-2010 (c) Sahana Software Foundation
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

from gluon import *
from gluon.storage import Storage
#import traceback


class S3:
    "The T2 functions we still use extracted from t2.py"

    IMAGE_EXT = ['.jpg', '.gif', '.png']
    def __init__(self, request, response, session, cache, T, db,
            all_in_db = False):
        self.messages = Storage()
        self.messages.record_deleted = T("Record Deleted")
        self.error_action = 'error'
        self.request = request
        self.response = response
        self.session = session
        self.cache = cache
        self.T = T
        self.db = db
        self.all_in_db = all_in_db
        if self.db._dbname == 'gql':
            self.is_gae = True
            self.all_in_db = True
        else:
            self.is_gae = False
        if all_in_db:
            session.connect(request, response, db=db)
        if not session.t2:
            session.t2 = Storage()
        try:
            self.id = int(request.args[-1])
        except:
            self.id = 0

    def _globals(self):
        """
        Returns (request, response, session, cache, T, db)
        """
        return self.request, self.response, self.session, \
               self.cache, self.T, self.db

    def _error(self):
        """
        Redirects to the self.error_action (='error'?) page.
        """
        self.redirect(self.error_action)

    def action(self, f=None, args=[], vars={}):
        """
        self.action('name', [], {}) is a shortcut for

            URL(f='name', args=[], vars={})
        """
        if not f:
            f = self.request.function
        if not isinstance(args, (list, tuple)):
            args = [args]
        return URL(r=self.request, f=f, args=args, vars=vars)

    def redirect(self, f=None, args=[], vars={}, flash=None):
        """
        self.redirect('name', [], {}, 'message') is a shortcut for

            session.flash = 'message'
            redirect(URL(f='name', args=[], vars={})
        """
        if flash:
            self.session.flash = flash
        redirect(self.action(f, args, vars))

    # Deprecated
    def itemize(self, *tables, **opts):
        """
        Lists all records from tables.
        opts include: query, orderby, nitems, header where nitems is items per page;
        """
        ### FIX - ADD PAGINATION BUTTONS
        import re
        request, response, session, cache, T, db = self._globals()
        if not len(tables):
            raise SyntaxError
        query = opts.get('query', None)
        orderby = opts.get('orderby', None)
        nitems = opts.get('nitems', 25)
        g = re.compile('^(?P<min>\d+)$').match(request.vars.get('_page', ''))
        page = int(g.group('min')) if g else 0
        limitby = opts.get('limitby', (page*nitems, page*nitems + nitems))
        if not query:
            query = tables[0].id > 0
        rows_count = tables[0]._db(query).count()
        rows = tables[0]._db(query).select(orderby=orderby, limitby=limitby,
                                         *[t.ALL for t in tables])
        if not rows:
            return None # rather than 'No data'. Give caller a chance to do his i18n issue
        def represent(t, r):
            try:
                rep = t.represent(r) # Note: custom represent() should generate a string or a list, but NOT a TR(...) instance
            except KeyError:
                rep = ([r[f] for f in t.displays] # Default depends on t.displays, if any
                if 'displays' in t else ['#%i'%r.id, str(r[t.fields[1]])]) # Fall back to TR(id,FirstField)
            return rep if isinstance(rep, list) else [rep] # Ensure to return a list
        header = opts.get('header',# Input can be something like TR(TH('ID'),TH('STAMP'))
          TR(*[TH(tables[0][f].label) for f in tables[0].displays])
            if 'displays' in tables[0] else '') # Default depends on tables[0].displays, if any
        headerList = [header] if header else []
        nav = DIV( # Iceberg at 21cn dot com prefers this style of page navigation :-)
          INPUT(_type='button', _value='|<', _onclick='javascript:location="%s"'
            %self.action(args=request.args, vars={'_page':0})) if page else '',
          INPUT(_type='button', _value='<', _onclick='javascript:location="%s"'
            %self.action(args=request.args, vars={'_page':page-1})) if page else '',
          SELECT(value=page,
            _onchange = 'javascript:location="%s?_page="+this.value' % self.action(args=request.args),
            # Intentionally "hide" it here for professional users. Cuz I doubt it is not intuitive enough for non-english common users.
            _title=query,
            # I hope the marks here are universal therefore no need for i18n
            *[OPTION('P%d (#%d~#%d)' %
              (i+1, i*nitems+1, min(rows_count, (i+1)*nitems)),
              _value=i) for i in xrange(rows_count/nitems+1)]
            ) if nitems < rows_count else '',
          INPUT(_type='button', _value='>', _onclick='javascript:location="%s"'
            %self.action(args=request.args, vars={'_page':page+1})
            ) if page*nitems+len(rows) < rows_count else '',
          INPUT(_type='button', _value='>|', _onclick='javascript:location="%s"'
            %self.action(args=request.args, vars={'_page':rows_count/nitems})
            ) if page*nitems+len(rows) < rows_count else '',
          ) if nitems < rows_count else None
        if len(tables) == 1:
            return DIV(
                # It shouldn't be inside the table otherwise it is tricky to set the correct _colspan for IE7
                nav if nav else '',
                # sorry, I don't know how to setup css to make _class='t2-itemize' looks cool, so I stick to "sortable"
                TABLE(_class='sortable',
                    *headerList+[TR(*represent(tables[0], row)) for row in rows]),
                nav if nav else '') # See above
        else:
            import itertools
            return DIV(
                # And don't try to make it "align=right", because the table might be too wide to show in the screen.
                nav if nav else '',
                TABLE(_class='sortable', # see above
                    *headerList+[TR(*list(itertools.chain(
                        *[represent(table,row[table._tablename]) for table in tables])))
                        for row in rows]),
                    nav if nav else '') # See above

    SEARCH_OP_PREFIX = '_op_'
    SEARCH_LOW_PREFIX, SEARCH_HIGH_PREFIX = '_low_', '_high_' # For date and datetime
    def field_search_widget(self, field):
        "Build a search widget for a db field"
        if isinstance(field.requires, IS_NULL_OR):
            requires = field.requires.other
        else:
            requires = field.requires
        if isinstance(requires, IS_IN_SET):
            return DIV(
                SELECT(OPTION('=', _value='is'),OPTION('!=', _value='isnot'),
                        _name = '%s%s' % (self.SEARCH_OP_PREFIX,field.name)
                      ),
                SELECT(_name=field.name, requires=IS_NULL_OR(requires),
                        *[OPTION('', _value='')]
                            +[OPTION(l, _value=v) for v, l in requires.options()]
                      ),
                      )
        if isinstance(requires, (IS_DATE, IS_DATETIME)):
            lowName = '%s%s' % (self.SEARCH_LOW_PREFIX, field.name)
            highName = '%s%s' % (self.SEARCH_HIGH_PREFIX, field.name)
            return DIV(
                        INPUT(
                            _class='date' if isinstance(requires, IS_DATE) else 'datetime',
                            _type='text',
                            _name=lowName,
                            _id=lowName,
                            requires=IS_NULL_OR(requires)
                        ),
                    '<= X <=',
                    INPUT(_class='date' if isinstance(requires,IS_DATE) else 'datetime',
                        _type='text',
                        _name=highName,
                        _id=highName,
                        requires=IS_NULL_OR(requires)),
                     )
        if field.name == 'id':
            return DIV('=',
                    # we still need this to trigger the search anyway
                    INPUT(_type='hidden',
                            _value='is',
                            _name='%s%s' % (self.SEARCH_OP_PREFIX, field.name)),
                    INPUT(_class='integer', _name='id'))
        if field.type in ('text', 'string'): # the last exit
            return DIV(
                SELECT(
                    OPTION(self.T('contains'), _value='contain'),
                    OPTION(self.T('does not contain'), _value='notcontain'),
                    _name = '%s%s'%(self.SEARCH_OP_PREFIX, field.name)),
                #Use naive INPUT(...) to waive all validators, such as IS_URL()
                INPUT(_type='text', _name=field.name, _id=field.name))
        import logging
        logging.warn('Oops, this field is not yet supported. Please report it.')

    def search(self, *tables, **opts):
        """
        Makes a search widgets to search records in tables.
        opts can be query, orderby, limitby
        """
        request, response, session, cache, T, db = self._globals()
        if self.is_gae and len(tables) != 1:
            self._error()
        def is_integer(x):
            try:
                int(x)
            except:
                return False
            else:
                return True
        def is_double(x):
            try:
                float(x)
            except:
                return False
            else:
                return True
        options = []
        orders = []
        query = opts.get('query', None)
        def option(s):
            return OPTION(s if s[:3] != 't2_' else s[3:], _value=s)
        for table in tables:
            for field in table.get('displays', table.fields):
                tf = str(table[field])
                t = table[field].type
                if not self.is_gae and (t=='string' or t=='text'):
                    options.append(option('%s contains' % tf))
                    options.append(option('%s starts with' % tf))
                if t != 'upload':
                    options.append(option('%s greater than' % tf))
                options.append(option('%s equal to' % tf))
                options.append(option('%s not equal to' % tf))
                if t != 'upload':
                    options.append(option('%s less than' % tf))
                orders.append(option('%s ascending' % tf))
                orders.append(option('%s descending' % tf))
        form = FORM(SELECT(_name='cond', *options),
                  INPUT(_name='value', value=request.vars.value or '0'),
                  ' ordered by ',
                  SELECT(_name='order', *orders),' refine? ',
                  INPUT(_type='checkbox', _name='refine'),
                  INPUT(_type='submit'))
        if form.accepts(request.vars, formname='search'):
            db = tables[0]._db
            p = (request.vars.cond, request.vars.value, request.vars.order)
            if not request.vars.refine:
                session.t2.query = []
            session.t2.query.append(p)
            orderby, message1, message2 = None, '', ''
            prev = [None, None, None]
            for item in session.t2.query:
                c, value, order = item
                if c != prev[0] or value != prev[1]:
                    tf, cond = c.split(' ', 1)
                    table, field = tf.split('.')
                    f = db[table][field]
                    if (f.type=='integer' or f.type=='id') and \
                       not is_integer(value):
                        session.flash = self.messages.invalid_value
                        self.redirect(args=request.args)
                    elif f.type=='double' and not is_double(value):
                        session.flash = self.messages.invalid_value
                        self.redirect(args=request.args)
                    elif cond=='contains':
                        q = f.lower().like('%%%s%%' %value.lower())
                    elif cond=='starts with':
                        q = f.lower().like('%s%%' % value.lower())
                    elif cond=='less than':
                        q = f < value
                    elif cond=='equal to':
                        q = f == value
                    elif cond=='not equal to':
                        q = f != value
                    elif cond=='greater than':
                        q = f > value
                    query = query&q if query else q
                    message1 += '%s "%s" AND ' % (c, value)
                if order != prev[2]:
                    p = None
                    c, d = request.vars.order.split(' ')
                    table, field = c.split('.')
                    if d == 'ascending':
                        p = f
                    elif d == 'descending':
                        p = ~f
                    orderby = orderby|p if orderby else p
                    message2 += '%s ' % order
                prev = item
            message = 'QUERY %s ORDER %s' % (message1, message2)
            return DIV(TABLE(TR(form), TR(message),
                TR(self.itemize(query=query, orderby=orderby, *tables))),
                _class='t2-search')
        else:
            session.t2.query = []
        return DIV(TABLE(TR(form)), _class='t2-search')


