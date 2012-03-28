# -*- coding: utf-8 -*-
""" Sorts db tables in topological order of their constraint graph.

Reads a collection of Web2py .table files or SHOW CREATE TABLE info from
MySQL, extracts the foreign key constraints, forms the tables and their
dependencies into a directed graph, verifies that the graph has no cycles,
does a topological sort, and supplies the tables in order, with the
non-dependent tables at the front.  Can be run as a script or called as
a function.

If the tables are dumped in this order, reading them back in will not
cause constraint errors.  The reverse order (most dependent to least) is
the appropriate order in which to alter tables to fit a new schema.

Note do not define a table or field named (uppercase) REFERENCES -- all
the forms of schema info use that as a keyword.

Uses LANL NetworkX for graph algorithms.  Works with v1.3 or v1.2 -- the
latter is usable under Python 2.5, where v1.3 requires Python 2.6 or above.
NetworkX site: http://networkx.lanl.gov/index.html
Get older versions from: http://networkx.lanl.gov/download/networkx/
"""

import sys, os, os.path, string
import networkx as nx

# Tables are nodes in the graph, and constraints are edges that point from
# the dependent table to the primary table.

class OrderTables:
    """ Sorts tables in order by constraints, least constrained first

    The base class is not instantiated -- see subclasses.
    """

    def __init__(self):
        self.graph = nx.DiGraph()
        self.trans_tbl = string.maketrans("()`',", "     ")  # for cleanup()

    def cleanup(self, line):
        """ Replaces assorted punctuation with space. """

        return line.translate(self.trans_tbl)

    def add_table_to_graph(self, table_id):
        """"Adds nodes and edges extracted from one table's schema

        Adds the table name, and the names of other tables found in
        constraints, as nodes to the supplied graph.
        Adds constraints as edges, pointing from primary to dependent table.

        @param table_id: table identifier, as needed by subclass method
        get_table_info(table_id).
        """

        (table_name, constraint_iter) = self.get_table_info(table_id)

        # Add the table name as a node.
        self.graph.add_node(table_name)  # does nothing if name already in graph

        # Step through constraints, add the primary table as a node,
        # and add an edge from the primary to this table.  (add_edge will
        # add nodes if not in graph.)
        for primary_name in constraint_iter():
            # Self-references are ok, so exclude those.
            if table_name != primary_name:
                self.graph.add_edge(primary_name, table_name)

    def order_tables(self):
        """ Sorts tables in constraint order, least constrained tables first

        Constructs a constraint graph for the tables in the supplied database
        or databases directory, sorts it in topological order with the least
        constained tables first, and returns the table names in that order in
        a list.
        """

        self.add_all_tables_to_graph()

        # With NetworkX v1.3, topological_sort raises NetworkXUnfeasible if
        # the graph is not acyclic.  With v1.2, it returns None.
        ordered_tables = None
        try:
            ordered_tables = nx.topological_sort(self.graph)
        except:
            ordered_tables = None
        if not ordered_tables:
            # Fails only if the graph has cycles.
            # The NetworkX package does not include a function that finds
            # cycles in a directed graph.  Lacking that, report the undirected
            # cycles.  Since our tables currently contain no cycles other than
            # self-loops, no need to implement a directed cycle finder.
            # @ToDo: Add a warning to the wiki about not putting cycles in
            # table relationships.  It's never necessary -- show a proper
            # relationship hierarchy.
            cycles = nx.cycle_basis(nx.Graph(self.graph))
            errmsg = "Tables and their constraints do not form a DAG.\n" + \
                     "Found possible cycles:\n" + str(cycles)
            raise ValueError, errmsg

        return ordered_tables

class OrderTablesFromDatabases(OrderTables):
    """ Sorts tables in topological order by constraints, least constrained 1st.
    This variant gets its data from the application's databases directory.
    @param appdir_str: the path to the application's directory containing
    its databases directory.  Default is current directory.
    """

    def __init__(self, appdir_str=None):
        OrderTables.__init__(self)
        if not appdir_str:
            appdir_str = os.curdir
        self.dbdir_str = os.path.join(appdir_str, "databases")
        if not os.path.isdir(self.dbdir_str):
            raise ValueError, "Unable to read directory %s" % self.dbdir_str
            

    def get_table_info(self, file_str):
        """ Extracts table name and constraints from given .table file.
        @param file_str: the name of a .table file.
        @return: (table_name, constraint_iter) where constraint_iter yields
        the names of tables on which this table depends.
        """

        try:
            table_file = open(os.path.join(self.dbdir_str, file_str), "r")
        except:
            raise ValueError, "Couldn't read file %s" % file_str

        table_name = file_str.split(".", 1)[0].split("_", 1)[1]

        def constraint_iter():
            """ Find constraint lines in the file, yield the primary table name.

            Constraint lines contain the word REFERENCES and the following
            term (minus punctuation) is the primary table name for this
            foreign key reference.
            """

            for line in table_file:
                terms = self.cleanup(line).split()
                try:
                    primary_index = terms.index("REFERENCES") + 1
                except:
                    continue
                if len(terms) > primary_index:
                    primary_name = terms[primary_index]
                    yield primary_name

        return (table_name, constraint_iter)

    def add_all_tables_to_graph(self):
        """ Add tables and constraints from databases directory to graph. """

        for file_str in os.listdir(self.dbdir_str):
            if file_str.endswith(".table"):
                self.add_table_to_graph(file_str)

class OrderTablesFromMySQL(OrderTables):
    """ Sort tables in topological order by constraints, least constrained 1st.
    This variant gets its data from the application's MySQL database.
    There are two ways to supply a connection to the database.  First, if
    there is already an open connection, pass that:
    @param db: An open database connection.
    If not, pass the info needed to connect:
    @param user: MySQL user for the database.
    @param password: password for the database.
    @param dbname: name of the database.
    """

    def __init__(self,
                 db=None,
                 user="sahana" , password="password", dbname="sahana"):
        """ Connect to datbase, init graph.

        If a database connection is supplied in db, use that, else connect
        using the supplied or defaulted user, password, and database name.
        """

        import MySQLdb
        OrderTables.__init__(self)
        if db:
            self.db = db
        else:
            self.db = MySQLdb.connection(
                host="localhost", user=user, passwd=password, db=dbname)

    def get_table_info(self, table_name):
        """ Extracts constraints for table from schema.
        @param table_name: name of the table to process.
        @return: (table_name, constraint_iter) where constraint_iter yields
        the names of tables on which this table depends.
        """

        self.db.query("SHOW CREATE TABLE %s;" % table_name)
        result = self.db.store_result()
        table_schema = result.fetch_row(1)[0][1]

        def constraint_iter():
            """ Find constraints in the schema, yield the primary table name.

            SHOW CREATE TABLE returns one line with the entire create table
            command.  As with .table files, onstraint clauses contain the word
            REFERENCES and the following term (minus punctuation) is the
            dependent table name).
            """

            terms = self.cleanup(table_schema).split()

            while len(terms) > 0:
                try:
                    primary_index = terms.index("REFERENCES") + 1
                except:
                    break
                if len(terms) > primary_index:
                    primary_name = terms[primary_index]
                    terms = terms[primary_index + 1:]
                    yield primary_name

        return (table_name, constraint_iter)

    def add_all_tables_to_graph(self):
        """ Add tables and constraints from MySQL database to graph. """

        self.db.query("SHOW TABLES;")
        result = self.db.store_result()

        for row in result.fetch_row(1000):
            table_name = row[0]
            self.add_table_to_graph(table_name)

def order_tables_from_databases(appdir_str=None):
    """ Sorts tables in constraint order, least constrained tables first.

    Constructs a constraint graph for the tables in the specified web2py
    databases directory, sorts it in topological order, and returns the table
    names in order, from least dependent to most, in a list.
    """

    order_tool = OrderTablesFromDatabases(appdir_str)
    return order_tool.order_tables()

def order_tables_from_mysql(db=None, user=None, password=None, dbname=None):
    """ Sorts tables in constraint order, least constrained tables first.

    Uses open database connection if supplied in db, else opens a connection
    using the supplied user, password, and database name.  Expects a MySQL
    database.

    Constructs a constraint graph for the tables in the specified database,
    sorts it in topological order, and returns the table names in order,
    from least dependent to most, in a list.
    """

    order_tool = OrderTablesFromMySQL(
        db=db, user=user, password=password, dbname=dbname)
    return order_tool.order_tables()

if __name__ == "__main__":
    # If run as a command, usage is:
    #   python topo.py application-path output-path
    # where application-path should contain a databases directory with the
    # .table files to read, and output-path is where to write the results.
    # These default to the current directory and stdout.
    # @ToDo: Command line doesn't yet have args for direct MySQL version.

    if len(sys.argv) > 2:
        output_str = sys.argv[2]
        try:
            output = open(output_str, mode="w")
        except:
            print >> sys.stderr, "Unable to write to %s" % output_str
            sys.exit(1)
    else:
        output = sys.stdout
    if len(sys.argv) > 1:
        appdir_str = sys.argv[1]
    else:
        appdir_str = os.curdir

    ordered_tables = order_tables_from_databases(appdir_str)
    ordered_tables_str = " ".join(ordered_tables)
    output.write(ordered_tables_str)
    output.close()

    sys.exit(0)
