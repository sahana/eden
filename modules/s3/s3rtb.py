# -*- coding: utf-8 -*-

""" S3 Resource Tree Builder (for scalable XML Exports)

    @copyright: 2021-2021 (c) Sahana Software Foundation
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

__all__ = ("S3ResourceTree",
           )

import json
from lxml import etree

from gluon import current
from gluon.storage import Storage

from .s3resource import DEFAULT, MAXDEPTH
from .s3query import FS, S3URLQuery
from .s3fields import S3Represent, S3RepresentLazy
from .s3utils import s3_get_foreign_key, s3_str

from s3dal import original_tablename

# =============================================================================
class S3ResourceTree:
    """ Resource Tree Builder """

    def __init__(self, resource, location_data=None, map_data=None):
        """
            Args:
                resource: the S3Resource to build the tree from
                location_data: dictionary of location data which has been
                               looked-up in bulk ready for xml.gis_encode()
                map_data: dictionary of options which can be read by the map
        """

        self.resource = resource

        self.location_data = location_data if location_data else DEFAULT
        self.map_data = map_data

        if current.xml.show_urls:
            self.base_url = current.response.s3.base_url
        else:
            self.base_url = None

        # Initialize

        # Map of identities of exported records
        # {(tablename, id): (original_tablename, original_id, uid)}
        self.exported = {}

        # List of all root nodes of the tree
        self.masters = None

        # List of all nodes in the tree
        self.nodes = None

        # Map of pending dependencies
        # {tablename: [record_ids]}
        self.pending_dependencies = {}

    # -------------------------------------------------------------------------
    def build(self,
              start = 0,
              limit = None,
              msince = None,
              sync_filters = None,
              xmlformat = None,
              fields = None,
              references = None,
              mcomponents = DEFAULT,
              target = None,
              dereference = True,
              maxdepth = MAXDEPTH,
              rcomponents = None,
              mdata = False,
              maxbounds = False,
              ):
        """
            Build the resource tree

            Args:
                start: index of the first record to export (slicing)
                limit: maximum number of records to export (slicing)
                msince: export only records which have been modified
                        after this datetime
                sync_filters: additional URL filters (Sync), as dict
                              {tablename: {url_var: string}}
                xmlformat: pre-parsed XSLT stylesheet wrapper
                fields: data fields to include (default: all)
                references: foreign keys to include (default: all)
                mcomponents: components of the master resource to
                             include (list of aliases), empty list
                             for all available components
                target: alias of component targeted
                        (or None to target master resource)
                dereference: include referenced resources
                maxdepth: maximum depth for reference exports
                rcomponents: components of referenced resources to
                             include (list of "tablename:alias")
                mdata: mobile data export
                       (=>reduced field set, lookup-only option)
                maxbounds: include lat/lon boundaries in the top
                           level element (off by default)

            Returns:
                ElementTree
        """

        if mcomponents is DEFAULT:
            mcomponents = []

        xml = current.xml
        s3db = current.s3db

        # Use lazy representations
        lazy = []
        current.auth_user_represent = S3Represent(lookup = "auth_user",
                                                  fields = ["email"],
                                                  )

        # Initialize masters
        self.masters = []
        self.nodes = []
        self.pending_dependencies = {}

        # Export resource
        resource = self.resource
        masters, nodes = self.export_resource(resource,
                                              start = start,
                                              limit = limit,
                                              fields = fields,
                                              references = references,
                                              components = mcomponents,
                                              msince = msince,
                                              sync_filters = sync_filters,
                                              xmlformat = xmlformat,
                                              mdata = mdata,
                                              target = target,
                                              location_data = self.location_data,
                                              )
        results = len(masters)
        if masters:
            self.masters.extend(masters)
            self.nodes.extend(nodes)

        depth = maxdepth if dereference else 0

        # Export dependencies
        dependencies = self.pending_dependencies
        while dependencies and depth:

            self.pending_dependencies = {}

            loadmap = self.generate_loadmap(dependencies)

            for rtablename, ids in loadmap.items():

                rresource = s3db.resource(rtablename, id=list(ids))

                masters, nodes = self.export_resource(rresource,
                                                      start = 0,
                                                      limit = len(ids),
                                                      fields = fields,
                                                      references = references,
                                                      components = rcomponents,
                                                      msince = None,
                                                      sync_filters = sync_filters,
                                                      xmlformat = xmlformat,
                                                      mdata = mdata,
                                                      target = target,
                                                      location_data = None,
                                                      )
                if masters:
                    self.masters.extend(masters)
                    self.nodes.extend(nodes)

            dependencies = self.pending_dependencies
            depth -= 1

        # Export identities of remaining dependencies, so references
        # can be resolved
        if dependencies:
            self.export_identities(dependencies)

        # Create root element
        root = etree.Element(xml.TAG.root)

        # Add map data to root element
        map_data = self.map_data
        if map_data:
            # Gets loaded before re-dumping, so no need to compact
            # or avoid double-encoding
            # NB Ensure we don't double-encode unicode!
            #root.set("map", json.dumps(map_data, separators=SEPARATORS,
            #                           ensure_ascii=False))
            root.set("map", json.dumps(map_data))

        # Render all master nodes
        location_references = []
        for node in self.masters:
            lref = node.add_element_to(root, lazy=lazy)
            if lref:
                location_references.extend(lref)

        # Add Lat/Lon attributes to all location references
        if location_references:
            xml.latlon(location_references)

        # Render all pending lazy representations
        if lazy:
            for renderer, element, attr, f in lazy:
                renderer.render_node(element, attr, f)

        # Complete the tree
        tree = xml.tree(None,
                        root = root,
                        domain = xml.domain,
                        url = self.base_url,
                        results = results,
                        start = start,
                        limit = limit,
                        maxbounds = maxbounds,
                        )

        # Store number of results in resource
        resource.results = results

        return tree

    # -------------------------------------------------------------------------
    def export_resource(self,
                        resource,
                        start = 0,
                        limit = None,
                        msince = None,
                        sync_filters = None,
                        xmlformat = None,
                        fields = None,
                        references = None,
                        components = None,
                        target = None,
                        mdata = None,
                        location_data = DEFAULT,
                        ):
        """
            Load the records in a resource and generate nodes for them

            Args:
                resource: the S3Resource
                start: index of the first record to export (slicing)
                limit: maximum number of records to export (slicing)
                msince: export only records which have been modified
                        after this datetime
                sync_filters: additional URL filters (Sync), as dict
                              {tablename: {url_var: string}}
                xmlformat: pre-parsed XSLT stylesheet wrapper
                fields: data fields to include (default: all)
                references: foreign keys to include (default: all)
                components: components to include (list of aliases),
                            empty list for all available components
                target: alias of component targeted
                        (or None to target master resource)
                mdata: mobile data export
                       (=>reduced field set, lookup-only option)
                location_data: dictionary of location data which has been
                               looked-up in bulk ready for xml.gis_encode()
        """

        s3db = current.s3db

        masters, nodes = [], []

        xml = current.xml
        MTIME = xml.MTIME

        prefix = resource.prefix
        name = resource.name

        # Load records in the master resource
        self.load_records(resource,
                          start = start,
                          limit = limit,
                          msince = msince,
                          sync_filters = sync_filters,
                          xmlformat = xmlformat,
                          target = target,
                          )

        # Establish the base URL of the resource
        base_url = self.base_url
        resource_url = "%s/%s/%s" % (base_url, prefix, name) if base_url else None

        # Establish dfields, rfields, and llrepr for master resource
        rfields, dfields, llrepr = self.fields_to_export(resource,
                                                         fields = fields,
                                                         references = references,
                                                         mdata = mdata,
                                                         )

        # Determine components to export
        if llrepr is None:
            components = self.components_to_export(resource.tablename,
                                                   components,
                                                   )
        else:
            components = []

        # Establish location_data if not passed-in from caller
        if not target and location_data is DEFAULT:
            location_data = current.gis.get_location_data(resource,
                                                          count = resource.count(),
                                                          )
            if not location_data:
                location_data = {}

        get_hierarchy_link = current.s3db.hierarchy_link

        # Determine the super-keys of the resource table
        table = resource.table
        superkeys = s3db.get_super_keys(table)

        crow_dict = {}
        for record in resource._rows:

            # Preliminary msince decision
            add = True
            if msince:
                mtime = record.get(MTIME)
                if mtime and mtime < msince:
                    add = False

            # Generate the node
            master = S3ResourceNode(self,
                                    resource,
                                    record,
                                    dfields = dfields,
                                    rfields = rfields,
                                    superkeys = superkeys,
                                    url = resource_url,
                                    master = not target,
                                    llrepr = llrepr,
                                    location_data = location_data,
                                    )
            master_id = record[resource._id]
            master_url = "%s/%s" % (resource_url, master_id) if resource_url else None

            # Export all related component records
            for alias in components:

                # Get the component
                component_ = resource.components.get(alias)
                if not component_:
                    # Invalid alias
                    continue

                hierarchy_link = get_hierarchy_link(component_.tablename)

                # Export the link rather than the linked record
                # - the linked record will then be exported as dependency of the link
                if component_.link is not None:
                    component = component_.link

                    # TODO solve this:
                    # - if both link and linked table are components, the link would be exported
                    #   twice => avoid exporting linked components if the link table is in the
                    #   component list, or: avoid exporting a component if it is the link table
                    #   of another component
                    if component.name in components:
                        # Do not export the linked component if the linktable is in the components list
                        continue
                else:
                    component = component_

                # Load the component records
                # - load once for all master records, then use resource.get() to separate them
                if component._rows is None:
                    self.load_records(component,
                                      start = 0,
                                      limit = None,
                                      msince = msince,
                                      sync_filters = sync_filters,
                                      xmlformat = xmlformat,
                                      hierarchy_link = hierarchy_link,
                                      add = add,
                                      target = target,
                                      )

                # Get the component records
                crecords = self.get_component_records(crow_dict,
                                                      alias,
                                                      record[component.pkey],
                                                      component
                                                      )
                if not crecords:
                    continue
                if not component.multiple and len(crecords):
                    crecords = [crecords[0]]

                # Establish component_url
                if resource_url:
                    cname = component.name if component.linked else component.alias
                    component_url = "%s/%s" % (master_url, cname)
                else:
                    component_url = None

                # Add alias if required
                calias = component_.alias
                if calias == component_.name:
                    calias = None

                # Determine if master
                if target == component.tablename:
                    is_master = True
                    if location_data is DEFAULT:
                        location_data = current.gis.get_location_data(component,
                                                                      count = component.count(),
                                                                      )
                        if not location_data:
                            location_data = {}
                else:
                    is_master = False

                # Separate references and data fields
                crfields, cdfields = component.split_fields(skip=[component.fkey])

                ctable = component.table
                csuperkeys = s3db.get_super_keys(ctable)
                # Append component nodes
                for crecord in crecords:
                    # TODO do not export this node if it already is in this master
                    cnode = S3ResourceNode(self,
                                           component,
                                           crecord,
                                           dfields = cdfields,
                                           rfields = crfields,
                                           superkeys = csuperkeys,
                                           url = component_url,
                                           master = is_master,
                                           alias = calias,
                                           location_data = location_data,
                                           )
                    master.append(cnode)

            # Final msince decision
            if add or master.components:

                # Keep the master
                masters.append(master)
                nodes.append(master)
                self.exported.update(master.identities)

                if master.components:
                    nodes.extend(master.components)
                    for node in master.components:
                        self.exported.update(node.identities)

        dependencies = self.pending_dependencies
        for node in nodes:
            for tn, ids in node.dependencies.items():
                d = dependencies.get(tn)
                dependencies[tn] = d | ids if d is not None else ids

        return masters, nodes

    # -------------------------------------------------------------------------
    @staticmethod
    def load_records(resource,
                     start = 0,
                     limit = None,
                     msince = None,
                     sync_filters = None,
                     xmlformat = None,
                     target = None,
                     # TODO can these parameters be avoided?:
                     hierarchy_link = None,
                     add = True,
                     ):
        """
            Load records in a resource

            Args:
                resource: the S3Resource
                start: index of the first record to export (slicing)
                limit: maximum number of records to export (slicing)
                msince: export only records which have been modified
                        after this datetime
                sync_filters: additional URL filters (Sync), as dict
                              {tablename: {url_var: string}}
                xmlformat: pre-parsed XSLT stylesheet wrapper
                target: alias of component targeted
                        (or None to target master resource)
                hierarchy_link: TODO
                add: flag for the preliminary msince-decision (if component)
        """

        table = resource.table
        tablename = resource.tablename

        xml = current.xml
        MCI = xml.MCI
        MTIME = xml.MTIME

        # MCI filter
        if xml.filter_mci and MCI in table.fields:
            resource.add_filter(FS(MCI) >= 0)

        # Sync filters
        if sync_filters and tablename in sync_filters:
            parsed_filters = S3URLQuery.parse(resource, sync_filters[tablename])
            for queries in parsed_filters.values():
                for query in queries:
                    resource.add_filter(query)

        # Msince filter
        if msince and (resource.alias != hierarchy_link or add) and MTIME in table.fields:
            resource.add_filter(FS(MTIME) >= msince)

        # Order by modified_on if msince is requested
        if msince and MTIME in table.fields:
            orderby = "%s ASC" % table[MTIME]
        else:
            orderby = None

        # Fields to load
        if xmlformat:
            include, exclude = xmlformat.get_fields(target or tablename) # TODO must always use tablename?
        else:
            include, exclude = None, None

        # Load the records
        # NB this is only done once for all master records,
        # subset per master record is selected by self.get
        resource.load(fields = include,
                      skip = exclude,
                      start = start,
                      limit = limit,
                      orderby = orderby,
                      virtual = False,
                      cacheable = True,
                      )

    # -------------------------------------------------------------------------
    @staticmethod
    def get_component_records(data, alias, master_id, component):

        if alias not in data:

            rows = component._rows
            if rows is None:
                raise RuntimeError("Component not loaded")

            row_dict = data[alias] = {}

            fkey = component.fkey
            for row in component._rows:
                k = row[fkey]
                if k in row_dict:
                    row_dict[k].append(row)
                else:
                    row_dict[k] = [row]
        else:
            row_dict = data.get(alias)

        return row_dict.get(master_id)

    # -------------------------------------------------------------------------
    @staticmethod
    def fields_to_export(resource, fields=None, references=None, mdata=False):
        """
            Establish fields to export for a resource

            Args:
                resource: the S3Resource
                fields: the requested data fields
                references: the requested references
                mdata: look up fields/references from mobile schema

            Returns:
                tuple (rfields, dfields, llrepr), with
                    rfields = list of reference field names to include
                    dfields = list of data field names to include
                    llrepr = lookup-list representation method (mobile schema)
        """

        llrepr = None
        if mdata:
            from .s3mobile import S3MobileSchema
            ms = S3MobileSchema(resource)
            if ms.lookup_only:
                # Override fields/references (only meta fields)
                llrepr = ms.llrepr
                fields, references = [], []
            else:
                # Determine fields/references from mobile schema
                fields = references = [f.name for f in ms.fields()]

        # Separate references and data fields
        rfields, dfields = resource.split_fields(data = fields,
                                                 references = references,
                                                 )

        return rfields, dfields, llrepr

    # -------------------------------------------------------------------------
    @staticmethod
    def components_to_export(tablename, aliases):
        """
            Get a list of aliases of components that shall be exported
            together with the master resource

            Args:
                tablename: the tablename of the master resource
                aliases: the list of required components

            Returns:
                A list of component aliases
        """

        # TODO prevent exporting both link table and linked table (only include the linked table)
        #      - if both are declared as components via the same lkey

        s3db = current.s3db

        if aliases is not None:
            names = aliases if aliases else None
            hooks = s3db.get_components(tablename, names=names)
        else:
            hooks = {}
        hierarchy_link = s3db.hierarchy_link(tablename)

        filtered, unfiltered = {}, {}
        for alias, hook in hooks.items():
            key = (hook.tablename,
                   hook.pkey,
                   hook.lkey,
                   hook.rkey,
                   hook.fkey,
                   )
            if hook.filterby:
                filtered[alias] = key
            else:
                unfiltered[key] = alias

        components = []

        for alias, key in filtered.items():
            if key in unfiltered:
                # Skip the filtered subset if the unfiltered set will be exported
                if alias == hierarchy_link:
                    hierarchy_link = unfiltered[key]
                continue
            if alias != hierarchy_link:
                components.append(alias)

        for key, alias in unfiltered.items():
            if alias != hierarchy_link:
                components.append(alias)

        # Hierarchy parent link must be last in the list
        if hierarchy_link:
            components.append(hierarchy_link)

        return components

    # -------------------------------------------------------------------------
    def generate_loadmap(self, dependencies):
        """
            Generate a load map from pending dependencies

            Args:
                dependencies: a dict {tablename: {record_ids}}

            Returns:
                A dict {tablename: [record_ids]} with the
                records that still need to be exported
        """

        s3db = current.s3db

        exported = self.exported

        loadmap = {}
        for tablename, record_ids in dependencies.items():

            table = s3db.table(tablename)
            if not table:
                continue
            required = {i for i in record_ids if (tablename, i) not in exported}
            if not required:
                continue

            if table._id.name != "id" and "instance_type" in table.fields:
                sloadmap = self.resolve_super_ids(table, required)
                for tn, ids in sloadmap.items():
                    if tn in loadmap:
                        loadmap[tn] |= ids
                    else:
                        loadmap[tn] = ids
            else:
                loadmap[tablename] = required

        return loadmap

    # -------------------------------------------------------------------------
    @staticmethod
    def resolve_super_ids(table, ids):
        """
            Resolve a list of super-entity record IDs into their
            corresponding instance table names and IDs

            Args:
                table: the super-entity table
                ids: the list of super-entity record IDs

            Returns:
                A dict {tablename: {record_ids}} with the
                corresponding instance table names and IDs
        """

        resolved = {}

        if not isinstance(ids, (set, list, tuple)) or not ids:
            return resolved

        db = current.db
        s3db = current.s3db

        pkey = table._id.name

        # Get instance types and uuids
        pkey_f = table[pkey]
        query = (pkey_f.belongs(ids)) if len(ids) > 1 else (pkey_f == list(ids)[0])
        srows = db(query).select(pkey_f,
                                 table.instance_type,
                                 limitby = (0, len(ids)),
                                 ).as_dict(key=pkey)

        # Prepare lookup lists per instance type
        lookup = {}
        for k, srow in srows.items():
            instance_type = srow["instance_type"]
            if instance_type not in lookup:
                lookup[instance_type] = {k}
            else:
                lookup[instance_type].add(k)

        # Look up record IDs per instance
        for instance_type, keys in lookup.items():

            itable = s3db.table(instance_type)
            if not itable:
                continue

            # TODO add accessible query already here (reduces the effort later)?
            # => should measure it, not useful if admin or having global access

            skey_f = itable[pkey]
            query = skey_f.belongs(keys)
            irows = db(query).select(itable._id, limitby=(0, len(keys)))
            resolved[instance_type] = {row[itable._id] for row in irows}

        return resolved

    # -------------------------------------------------------------------------
    def export_identities(self, dependencies):
        """
            Resolve the record identities of dependencies and add them
            to the exported-map (rather than exporting the referenced
            records)

            Args:
                dependencies: dict of dependencies,
                              {tablename: {record_ids}}
        """

        db = current.db
        s3db = current.s3db

        UID = current.xml.UID
        accessible_query = current.auth.s3_accessible_query

        exported = self.exported
        for tablename, record_ids in dependencies.items():

            table = s3db.table(tablename)
            if not table:
                continue

            # Check which identities are missing
            ids = {i for i in record_ids if (tablename, i) not in exported}

            pkey = table._id.name
            if pkey != "id" and "instance_type" in table.fields:

                # Lookup the instance type per super-ID
                query = table._id.belongs(ids)
                srows = db(query).select(table._id,
                                         table.instance_type,
                                         limitby = (0, len(ids)),
                                         )

                # Group the super-IDs by instance type
                loadmap = {}
                for srow in srows:
                    instance_type = srow.instance_type
                    if instance_type not in loadmap:
                        loadmap[instance_type] = {srow[pkey]}
                    else:
                        loadmap[instance_type].add(srow[pkey])

                for tn, super_ids in loadmap.items():

                    # Get the instance table
                    itable = s3db.table(tn)
                    if not itable or \
                       any (fn not in itable.fields for fn in (pkey, UID)):
                        continue

                    # Look up the instance record identities
                    query = itable[pkey].belongs(super_ids) & \
                            accessible_query("read", itable)
                    rows = db(query).select(itable._id,
                                            itable[UID],
                                            itable[pkey],
                                            limitby = (0, len(super_ids)),
                                            )

                    # Add identities to exported
                    for row in rows:
                        super_id = row[pkey]
                        record_id = row[itable._id]
                        exported[(tablename, super_id)] = (instance_type,
                                                           record_id,
                                                           row[UID],
                                                           )

            elif UID in table.fields:

                # Look up the UID for each accessible record
                query = table._id.belongs(ids) & \
                        accessible_query("read", table)
                rows = db(query).select(table._id,
                                        table[UID],
                                        limitby = (0, len(ids)),
                                        )

                # Add identities to exported
                for row in rows:
                    record_id = row[pkey]
                    exported[(tablename, record_id)] = (tablename,
                                                        record_id,
                                                        row[UID],
                                                        )

    # -------------------------------------------------------------------------
    def resolve_reference(self, tablename, ids):
        """
            Resolve a reference against the map of exported records

            Args:
                tablename: the referenced table (or super-entity)
                ids: the referenced record IDs

            Returns:
                tuple (target, target_ids, target_uids), where:
                    target = name of the (instance) table
                    target_ids = list of referenced (instance) record ids
                    target_uids = list of the corresponding record UIDs
        """

        if not isinstance(ids, list):
            ids = [ids]

        default = None, None, None

        resolved = self.exported

        if not resolved:
            return default

        target = None
        target_ids = []
        target_uids = []
        for ref in ids:
            referenced = resolved.get((tablename, ref))
            if referenced:
                t, tid, tuid = referenced
                if target and target != t:
                    return default
                target = t
                target_ids.append(tid)
                target_uids.append(tuid)

        return target, target_ids, target_uids

# =============================================================================
class S3ResourceReference:
    """ A pending reference in a tree node """

    def __init__(self, table, fieldname, rtablename, pkey, value, multiple=False):
        """
            Args:
                table: the referencing table
                fieldname: the field name in the referencing table
                rtablename: the name of the referenced table
                pkey: the primary key in the referenced table
                value: the value of the field in the referencing table
                multiple: whether this is a list:reference
        """

        self.table = table
        self.fieldname = fieldname
        self.pkey = pkey
        self.value = value

        self.rtablename = rtablename

        self.multiple = multiple

    # -------------------------------------------------------------------------
    def dependency(self):
        """
            The dependency of this reference

            Returns:
                A tuple (tablename, {record_ids}) with
                    tablename = the referenced table
                    record_ids = list of record IDs in the referenced table
        """

        ids = self.value
        if not isinstance(ids, list):
            ids = [ids]
        return self.rtablename, set(ids)

    # -------------------------------------------------------------------------
    def resolve(self, tree):
        """
            Resolve this reference against the tree

            Args:
                tree: the S3ResourceTree

            Returns:
                Storage - a reference map entry suitable
                          for S3XML.add_references()
        """

        xml = current.xml

        fn = self.fieldname
        isrb = fn == xml.REPLACEDBY

        value = self.value
        target, ids, uids = tree.resolve_reference(self.rtablename, value)
        if not ids:
            return None

        entry = {"field": fn,
                 "table": target,
                 "multiple": False if isrb else self.multiple,
                 "id": ids,
                 "uid": uids,
                 }

        if isrb:
            entry.update({"value": None, "text": None, "lazy": False})
        else:
            dbfield = self.table[fn]

            formatted = s3_str(dbfield.formatter(value))
            lazy = text = None
            renderer = dbfield.represent
            if renderer is not None:
                if hasattr(renderer, "bulk"):
                    lazy = S3RepresentLazy(value, renderer)
                else:
                    text = xml.represent(self.table, fn, value)
            else:
                text = formatted

            entry.update({"value": formatted, "text": text, "lazy": lazy})

        return Storage(entry)

# =============================================================================
class S3ResourceNode:
    """ A node in the resource tree, representing an exported record """

    def __init__(self,
                 tree,
                 resource,
                 record,
                 dfields = None,
                 rfields = None,
                 superkeys = None,
                 url = None,
                 master = False,
                 alias = None,
                 llrepr = None,
                 location_data = None,
                 ):
        """
            Args:
                tree: the S3ResourceTree
                resource: the S3Resource
                record: the record (Row)
                dfields: the data fields to export
                rfields: the reference fields to export
                superkeys: all super-keys in the table
                url: the URL of the resource
                master: whether this is the master resource
                        of the export (for GIS-encoding)
                alias: the component alias (if the resource is a component)
                llrepr: lookup-list representation function (for EdenMobile)
                location_data: dictionary of location data which has been
                               looked-up in bulk ready for xml.gis_encode()
        """

        self.tree = tree
        self.master = master
        self.alias = alias
        self.llrepr = llrepr
        self.location_data = location_data

        self.resource = resource
        self.record = record
        self.dfields = dfields
        self.rfields = rfields
        self.superkeys = superkeys

        self.table = table = resource.table

        # Construct the record URL
        self.url = "%s/%s" % (url, record[table._id]) if url else None

        self.components = []

        self.element = None # The etree.Element generated for this

        self._references = None
        self._dependencies = None
        self._identities = None

    # -------------------------------------------------------------------------
    def append(self, node):
        """
            Append a component-node to this node

            @param node: the component node
        """

        # Append a component node to this node
        self.components.append(node)

    # -------------------------------------------------------------------------
    @property
    def identities(self):
        """
            A map over all identities of this node, i.e. the actual table
            name and ID, as well as all super entity names and IDs of the
            record (lazy property); this can be used to resolve any references
            to this record, including via super-links

            Returns:
                A map {(tablename, id): (itablename, iid, uid)},
                where:
                    - tablename is the table / supertable name
                    - id is the record ID / super ID
                    - itablename is the (instance) table name
                    - iid is the (instance) record id
                    - uid is the record UID
        """

        table = self.table
        pkey = table._id.name

        # Super-records have no identities themselves
        if pkey != "id" and "instance_type" in table.fields:
            return {}

        identities = self._identities
        if identities is None:

            record = self.record

            tablename = original_tablename(table)
            record_id = record[pkey]

            # The base identity
            identity = (tablename,
                        record_id,
                        record.uuid if "uuid" in table.fields else None,
                        )
            identities = self._identities = {(tablename, record_id): identity}

            # Add all known super-records
            for superkey in self.superkeys:
                super_id = self.record.get(superkey)
                if not super_id:
                    continue
                tn = s3_get_foreign_key(table[superkey])[0]
                if tn:
                    identities[(tn, super_id)] = identity

        return identities

    # -------------------------------------------------------------------------
    @property
    def references(self):
        """
            The references of this node (lazy property)

            Returns:
                A list of S3ResourceReferences
        """

        references = self._references
        if references is None:

            self._references = references = []

            table = self.table
            record = self.record

            xml = current.xml
            DELETED = xml.DELETED
            REPLACEDBY = xml.REPLACEDBY

            if DELETED in record and record[DELETED] and \
               REPLACEDBY in record and record[REPLACEDBY]:
                fields = [REPLACEDBY]
            else:
                fields = self.rfields
            if not fields:
                return references

            for fn in fields:
                # Skip super-keys
                if fn in self.superkeys:
                    continue

                # Skip unavailable/empty fields
                value = record.get(fn)
                if not value:
                    continue

                if fn == REPLACEDBY:
                    # Special handling since not a foreign key
                    tn = original_tablename(table)
                    key = table._id.name
                    multiple = False
                else:
                    # Inspect the DB field
                    try:
                        dbfield = getattr(table, fn)
                    except AttributeError:
                        continue
                    tn, key, multiple = s3_get_foreign_key(dbfield)
                    if not tn:
                        continue

                # Add the reference
                reference = S3ResourceReference(table, fn, tn, key, value,
                                                multiple = multiple,
                                                )
                references.append(reference)

        return references

    # -------------------------------------------------------------------------
    @property
    def dependencies(self):
        """
            All dependencies of this node (lazy property)

            Returns:
                A dict {tablename: {record_ids}} with
                  tablename = the name of the referenced table
                  record_ids = the IDs of the referenced records
        """

        dependencies = self._dependencies

        if dependencies is None:
            dependencies = self._dependencies = {}
            for reference in self.references:
                tn, ids = reference.dependency()
                d = dependencies.get(tn)
                dependencies[tn] = d | ids if d is not None else ids

        return dependencies

    # -------------------------------------------------------------------------
    def add_element_to(self,
                       parent,
                       lazy = None,
                       ):
        """
            Append the XML Element for this node to a parent element

            Args:
                parent: the parent Element
                lazy: list of lazy representation nodes (written to)

            Returns:
                A list of rmap entries for any location references
                in the record, suitable for S3XML.latlon()
        """

        table = self.table

        # Replace user ID representation by lazy method
        auth_user_represent = Storage()
        if hasattr(current, "auth_user_represent"):
            user_ids = ("created_by", "modified_by", "owned_by_user")
            for fn in user_ids:
                if hasattr(table, fn):
                    f = table[fn]
                    auth_user_represent[fn] = f.represent
                    f.represent = current.auth_user_represent

        xml = current.xml

        resource = self.resource
        record = self.record

        # Generate the XML for this record
        postprocess = resource.get_config("xml_post_render")
        element = xml.resource(parent,
                               self.table,
                               record,
                               fields = self.dfields,
                               alias = self.alias,
                               lazy = lazy,
                               url = self.url,
                               llrepr = self.llrepr,
                               postprocess = postprocess,
                               )

        # Add the <reference> elements
        rmap, lref = self.rmap()
        xml.add_references(element,
                           rmap,
                           show_ids = xml.show_ids,
                           lazy = lazy,
                           )

        if self.master:
            # GIS-encode the element
            # @ToDo: Do this 1/tree not 1/record
            xml.gis_encode(self.resource,
                           record,
                           element,
                           location_data = self.location_data,
                           )

        # Generate the XML for all sub-nodes
        for node in self.components:
            clref = node.add_element_to(element, lazy=lazy)
            lref.extend(clref)

        self.element = element

        # Restore normal user_id representations
        for fn in auth_user_represent:
            table[fn].represent = auth_user_represent[fn]

        return lref

    # -------------------------------------------------------------------------
    def rmap(self):
        """
            Generate reference map entries for this node, suitable
            for S3XML.add_references/S3XML.latlon

            Returns:
                tuple (rmap, lref) with
                    rmap = all reference map entries for this node
                    lref = subset of rmap with only location reference entries
        """

        rmap, lref = [], []

        # Resolve all references against the tree
        tree = self.tree
        for reference in self.references:
            entry = reference.resolve(tree)
            if entry:
                rmap.append(entry)
                if entry.table == "gis_location" and len(entry.id) == 1:
                    lref.append(entry)

        return rmap, lref

# END =========================================================================
