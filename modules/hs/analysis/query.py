"""                                                                                                                            
    Healthscapes Geolytics Module                                                                                                   
                                                                                                                                                                               
                                                                                                                               
    @author: Nico Preston <nicopresto@gmail.com>                                                                                 
    @author: Colin Burreson <kasapo@gmail.com>                                                                         
    @author: Zack Krejci <zack.krejci@gmail.com>                                                                             
    @copyright: (c) 2010 Healthscapes                                                                             
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




from re import sub


class Query:
    def __init__ (self, connection):
        self._vars = {}
        self._cursor = connection.cursor ()
        self.selectList = []
        self.tableList = []
        self.where = 'True'
        self.numEntries = 0

    def setVariable (self, name, value):
        value = clean (str(value))
        try:
            self._vars[name] = value
        except KeyError:
            self._vars.update ([(name, value)])

    def SELECT (self, column, table, func=None):
        column = clean (column)
        table = clean (table)
        if func != None:
            func = clean(func)
        flag = False
        for entry in self.selectList:
            if entry[0] == column and entry[1] == table:
                flag = True
                break
        if flag == False:
            self.selectList.append ((column, table, func))
            self.numEntries += 1    
        self.FROM (table)

    def _selectEntries (self):
        list = []
        for entry in self.selectList:
            item = entry[1] + '.' + entry[0]
            if entry[2]:
                item = entry[2] + '(' + item + ')'
            list.append (item)
        return list

    def FROM (self, table):
        flag = False
        for entry in self.tableList:
            if entry == table:
                flag = True
        if flag == False:
            self.tableList.append (table)

    def WHERE (self, string):
        self.where = string

    def whereFrom (self, field):
        for entry in self.selectList:
            if entry[0] == field:
                return entry[1]
        return None
    
    def __str__ (self):
        query = 'SELECT '
        spacer = ', '
        select = spacer.join (self._selectEntries ())
        query += select
        qFrom = spacer.join (self.tableList)
        query += ' FROM ' + qFrom
        query += ' WHERE ' + self.where
        return query

    def __iter__ (self):
        q = str(self) % self._vars
        self._cursor.execute (q)
        return QueryIterator (self)


class QueryIterator:
    def __init__ (self, query):
        self.current = 0
        self._query = query

    def next (self):
        if self.current >= self._query._cursor.rowcount:
            raise StopIteration ()
        self.current += 1
        row =  self._query._cursor.fetchone ()
        dictionary = {}
        for i, entry in enumerate(row):
            dictionary.update ([(self._query.selectList[i][0], entry)])
        return dictionary
        
    def __iter__ (self):
        return self


class SQLTable:
    def __init__ (self,connection, name, pk=None):
        name = clean (name)
        self._cursor = connection.cursor ()
        self._name = name
        self._columns = []
        self.columnType = {}
        inputString = 'CREATE TABLE ' + name + '('
        if pk:
            inputString += pk + ' SERIAL PRIMARY KEY'
        inputString += ')'
        self._cursor.execute (inputString)

    def addColumn (self, columnName, type, notNull=False):
        self.columnType[columnName] = type
        columnName = clean(columnName)
        type = clean (type)
        for c in self._columns:
            if c == columnName:
                return False
        inputString = 'ALTER TABLE ' + self._name
        inputString += ' ADD COLUMN ' + columnName + ' ' + type
        if notNull:
            inputString += ' NOT NULL'
        self._cursor.execute (inputString)
        self._columns.append (columnName)
        return True

    def addGeometryColumn (self, column, srid, geomType, dim):
        self.columnType[column] ='geom'
        args = []
        args.append ("'" + self._name + "'")
        args.append ("'" + clean (column) + "'")
        args.append (srid)
        args.append ("'" + clean(geomType) + "'")
        args.append (dim)
        arguments = ', '.join (args)
        inputString = 'SELECT AddGeometryColumn (' + arguments + ')'
        self._cursor.execute (inputString)

    def insert (self, **kwargs):
        keyList = []
        valueList = []
        for key, value in kwargs.iteritems ():
            keyList.append (clean(key))
            if self.columnType[key] == 'varchar':
                valueList.append ("'" + clean(value) + "'")
            else:
                valueList.append (str(value))
        keyString = ', '.join (keyList)
        valueString = ', '.join (valueList)
        inputString = 'INSERT INTO ' + self._name + ' (' + keyString
        inputString += ') VALUES (' + valueString + ')'
        self._cursor.execute (inputString)
        
    def save (self):
        self._cursor.execute ('COMMIT')
        

def clean (string):
    return string
    s = sub ('([;\'\"])',r'\\\1', string)
    return s


