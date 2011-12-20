# -*- coding: utf-8 -*-
"""
Reads a collection of Web2py .table files, extracts the foreign key
constraints, forms the tables and their dependencies into a directed graph,
verifies that the graph has no cycles, does a topological sort, and writes
out tables in order, with the non-dependent tables at the front.  If the
tables are dumped in this order, reading them back in will not cause
constraint errors.  Uses LANL NetworkX for graph algorithms.
"""

import sys, os, os.path
import networkx as nx

# Tables are nodes in the graph, and constraints are edges that point from
# the dependent table to the primary table.

def add_table_to_graph(dbdir_str, file_str, graph):
    """"
    Adds nodes and edges extracted from one .table file

    Reads the supplied .table file.  Adds its table name, and the names of
    other tables found in constraints, as nodes to the supplied graph.
    Adds constraints as edges, pointing from primary to dependent table.
    """

    # Make sure we can read it.
    try:
        file = open(os.path.join(dbdir_str, file_str), "r")
    except:
        print >> sys.stderr, "Couldn't read file %s" % file_str

    # Add the table name as a node.
    table_name = file_str.split(".", 1)[0].split("_", 1)[1]
    graph.add_node(table_name)  # does nothing if name already in graph

    # Find constraint lines in the file, add the primary table as a node,
    # and add an edge from the primary to this table.
    for line in file:
        terms = line.split(" ", 3)
        if len(terms) >= 3 and terms[1] == "REFERENCES":
            primary_name = terms[2].split("(", 1)[0]
            # Self-references are ok, so exclude those.
            if table_name != primary_name:
                graph.add_edge(primary_name, table_name)

def order_tables(dbdir_str):
    """
    Sorts tables in constraint order, primary tables first

    Constructs a constraint graph for the tables in the supplied directory,
    sorts it in topological order, and returns the table names in that
    order in a list.
    """

    graph = nx.DiGraph()

    for file_str in os.listdir(dbdir_str):
        if file_str.endswith(".table"):
            add_table_to_graph(dbdir_str, file_str, graph)

    ordered_tables = None
    try:
        ordered_tables = nx.topological_sort(graph)
    except nx.NetworkXUnfeasible:
        print >> sys.stderr, "Tables and their constraints do not form a DAG"
        # The NetworkX package does not include a function that finds cycles
        # in a directed graph.  Lacking that, report the undirected cycles.
        # Since our tables currently contain no cycles other than self-loops,
        # no need to implement a directed cycle finder.
        cycles = nx.cycle_basis(nx.Graph(graph))
        print >> sys.stderr, "Found possible cycles:"
        print >> sys.stderr, cycles
        sys.exit(1)

    return ordered_tables

if __name__ == "__main__":
    # If run as a command, usage is:
    #   python topo.py application-path output-path
    # where application-path should contain a databases directory with the
    # .table files to read, and output-path is where to write the results.
    # These default to the current directory and stdout.

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
    dbdir_str = os.path.join(appdir_str, "databases")
    if not os.path.isdir(dbdir_str):
        print >> sys.stderr, "Unable to read directory %s" % dbdir_str
        sys.exit(1)

    ordered_tables = order_tables(dbdir_str)
    ordered_tables_str = " ".join(ordered_tables)
    output.write(ordered_tables_str)
    output.close()

    sys.exit(0)
