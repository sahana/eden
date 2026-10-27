"""
    Data Import Tools

    Copyright: 2011-2022 (c) Sahana Software Foundation

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

__all__ = ("XMLImporter",
           "ImportJob",
           "ImportItem",
           "SyncPolicy",
           "S3Duplicate",
           )

import datetime
import json
import pickle
import sys
import uuid

from copy import deepcopy
from io import StringIO
from lxml import etree

from gluon import current, IS_EMPTY_OR
from gluon.storage import Storage
from gluon.tools import callback

from s3dal import Field, filter_fields

from ..tools import s3_format_datetime, s3_get_foreign_key, \
                    s3_has_foreign_key, s3_str, s3_utc

# =============================================================================
class XMLImporter:
    """ S3XML Importer Utility """

    # -------------------------------------------------------------------------
    @classmethod
    def parse_source(cls,
                     tablename,
                     source,
                     source_type = "xml",
                     stylesheet = None,
                     extra_data = None,
                     **args):
        """
            Parse a data source for import, and convert it into a S3XML
            element tree.

            Args:
                tablename: the name of the target table
                source: the data source; accepts a single source, a list of
                        sources or a list of tuples (name, source); each
                        source must be either an ElementTree or a file-like
                        object
                source_type: the source type (xml|json|csv|xls|xlsx)
                stylesheet: the transformation stylesheet
                extra_data: for CSV imports, dict of extra columns to add
                            to each row
                args: parameters to pass to the transformation stylesheet
        """

        xml = current.xml
        tree = None

        if not isinstance(source, (list, tuple)):
            source = [source]

        for item in source:

            if isinstance(item, (list, tuple)):
                name, s = item[:2]
            else:
                name, s = None, item

            if isinstance(s, etree._ElementTree):
                t = s
            elif source_type == "json":
                if isinstance(s, str):
                    t = xml.json2tree(StringIO(s))
                else:
                    t = xml.json2tree(s)
            elif source_type == "csv":
                t = xml.csv2tree(s, resourcename=name, extra_data=extra_data)
            elif source_type == "xls":
                t = xml.xls2tree(s, resourcename=name, extra_data=extra_data)
            elif source_type == "xlsx":
                t = xml.xlsx2tree(s, resourcename=name, extra_data=extra_data)
            else:
                t = xml.parse(s)

            if not t:
                raise SyntaxError(xml.error if xml.error else current.ERROR.BAD_SOURCE)

            if stylesheet is not None:
                prefix, name = tablename.split("_", 1)
                args.update(domain = xml.domain,
                            base_url = current.response.s3.base_url,
                            prefix = prefix,
                            name = name,
                            utcnow = s3_format_datetime(),
                            )
                t = xml.transform(t, stylesheet, **args)
                if not t:
                    raise SyntaxError(xml.error)

            if not tree:
                tree = t.getroot()
            else:
                tree.extend(list(t.getroot()))

        return tree

    # -------------------------------------------------------------------------
    @classmethod
    def import_tree(cls,
                    tablename,
                    tree,
                    files = None,
                    record_id = None,
                    components = None,
                    commit = True,
                    ignore_errors = False,
                    job_id = None,
                    select_items = None,
                    strategy = None,
                    sync_policy = None,
                    ):
        """
            Import data from an S3XML element tree.

            Args:
                tablename: the name of the target table
                tree: the S3XML element tree (ElementTree)
                files: file attachments referenced by the tree (dict)
                record_id: the target record ID
                list components: list of importable components
                commit: commit the import job, if False, the import job
                        will be rolled back and stored for committing at
                        a later time
                ignore_errors: ignore any errors, import what is possible
                job_id: the job UID, to restore and commit a previously
                        stored import job
                list select_items: only restore these items from the job
                                   (list of import item record IDs)
                strategy: list of allowed import methods
                sync_policy: the synchronization policy (SyncPolicy)
        """

        db = current.db
        s3db = current.s3db

        s3 = current.response.s3

        table = s3db.table(tablename)
        if not table or "id" not in table.fields:
            return ImportResult(False, current.ERROR.BAD_RESOURCE)

        if tree is not None:
            # Run import_prep callback
            import_prep = s3.import_prep
            if import_prep:
                if not isinstance(tree, etree._ElementTree):
                    tree = etree.ElementTree(tree)
                callback(import_prep, tree, tablename=tablename)

            # Select matching elements from tree
            elements = cls.matching_elements(tree, tablename, record_id=record_id)
            if not elements:
                # Nothing to import
                # - this is only an error if an update of a specific record
                #   was expected
                error = current.ERROR.NO_MATCH if record_id else None
                return ImportResult(not record_id, error)

            # Create import job
            import_job = ImportJob(table,
                                   tree = tree,
                                   files = files,
                                   strategy = strategy,
                                   sync_policy = sync_policy,
                                   )

            # Add import items for matching elements
            error = None
            s3.bulk = True
            add_item = import_job.add_item
            for element in elements:
                success = add_item(element = element,
                                   components = components,
                                   )
                if not success:
                    error = import_job.error
            if error and not ignore_errors:
                s3.bulk = False
                return ImportResult(False, error, job=import_job)

        elif not commit:
            raise ValueError("Element tree required for trial import")

        elif job_id is not None:

            # Re-instate the stored import job
            try:
                import_job = ImportJob(table,
                                       job_id = job_id,
                                       strategy = strategy,
                                       sync_policy = sync_policy,
                                       )
            except SyntaxError:
                return ImportResult(False, current.ERROR.BAD_SOURCE)

            # Select items for target table
            item_table = s3db.s3_import_item
            query = (item_table.job_id == job_id)
            if select_items:
                # Limit to selected items for the resource table
                query &= (item_table.tablename != tablename) | \
                         (item_table.id.belongs(select_items))
            items = db(query).select()

            # Restore the items and references
            s3.bulk = True
            load_item = import_job.load_item
            error = None
            for item in items:
                success = load_item(item)
                if not success:
                    error = import_job.error
            import_job.restore_references()
            if error and not ignore_errors:
                s3.bulk = False
                return ImportResult(False, error)

            # Run import_prep callback
            import_prep = s3.import_prep
            if import_prep:
                tree = import_job.get_tree()
                callback(import_prep, tree, tablename=tablename)

        else:
            raise ValueError("Element tree or job ID required")

        # Commit the import job
        s3.bulk = True
        auth = current.auth
        auth.rollback = not commit
        success = import_job.commit(ignore_errors=ignore_errors)
        auth.rollback = False
        s3.bulk = False

        # Rollback on failure or if so requested
        if not success or not commit:
            db.rollback()

        # Prepare result
        error = import_job.error
        if error:
            if ignore_errors:
                error = "%s - invalid items ignored" % import_job.error
        elif not success:
            raise RuntimeError("Import failed without error message")
        result = ImportResult(error is None or ignore_errors,
                              error = error,
                              job = import_job,
                              )

        if not commit:
            # Save the job
            import_job.store()
        else:
            # Delete the import job when committed
            import_job.delete()
            result.job_id = None

        return result

    # -------------------------------------------------------------------------
    @staticmethod
    def matching_elements(tree, tablename, record_id=None):
        """
            Find elements in the source tree that belong to the target
            record, or the target table if no record is specified.

            Args:
                tree: the source tree (ElementTree)
                tablename: the name of the target table
                record_id: the target record ID

            Returns:
                list of matching elements, or None
        """

        xml = current.xml

        db = current.db

        # Select the elements for this table
        elements = xml.select_resources(tree, tablename)
        if not elements:
            return None

        # Find matching elements, if a target record ID is given
        UID = xml.UID
        table = current.s3db[tablename]
        if record_id and UID in table:

            if not isinstance(record_id, (tuple, list)):
                query = (table._id == record_id)
            else:
                query = (table._id.belongs(record_id))
            originals = db(query).select(table[UID])

            uids = [row[UID] for row in originals]

            matches = []
            import_uid = xml.import_uid
            append = matches.append
            for element in elements:
                element_uid = import_uid(element.get(UID, None))
                if not element_uid:
                    continue
                if element_uid in uids:
                    append(element)
            if not matches:
                first = elements[0]
                if len(elements) and not first.get(UID, None):
                    first.set(UID, uids[0])
                    matches = [first]
            elements = matches

        return elements if elements else None

# =============================================================================
class ImportResult:
    """
        Result of an ImportJob
    """

    def __init__(self, success, error=None, job=None):
        """
            Args:
                success: whether the job was successful (bool)
                error: error message
                job: the ImportJob
        """

        self.success = success
        self.error = error
        if job:
            self.job_id = job.job_id
            self.count = job.count
            self.failed = job.errors
            self.created = job.created
            self.updated = job.updated
            self.deleted = job.deleted
            self.skipped = job.skipped
            self.mtime = job.mtime
            self.error_tree = job.error_tree
        else:
            self.job_id = None
            self.count = 0
            self.failed = 0
            self.created = []
            self.updated = []
            self.deleted = []
            self.skipped = []
            self.mtime = None
            self.error_tree = None

    # -------------------------------------------------------------------------
    def json_message(self):
        """
            Generate a JSON message from this result

            Returns:
                the JSON message (str)
        """

        xml = current.xml

        if self.error_tree is not None:
            tree = xml.tree2json(self.error_tree)
        else:
            tree = None

        # Import Summary Info
        info = {"records": self.count,
                }
        if self.created:
            info["created"] = list(set(self.created))
        if self.updated:
            info["updated"] = list(set(self.updated))
        if self.deleted:
            info["deleted"] = list(set(self.deleted))
        if self.skipped:
            info["skipped"] = list(set(self.skipped))

        if self.success:
            msg = xml.json_message(message = self.error,
                                   tree = tree,
                                   **info)
        else:
            msg = xml.json_message(False, 400,
                                   message = self.error,
                                   tree = tree,
                                   )
        return msg

# =============================================================================
class ImportJob():
    """
        Class to import an element tree into the database
    """

    def __init__(self,
                 table,
                 tree = None,
                 files = None,
                 job_id = None,
                 strategy = None,
                 sync_policy = None,
                 ):
        """
            Args:
                tree: the element tree to import
                files: files attached to the import (for upload fields)
                job_id: restore job from database (record ID or job_id)
                strategy: the import strategy
                sync_policy: the synchronization policy
        """

        self.error = None # the last error
        self.error_tree = etree.Element(current.xml.TAG.root)

        self.table = table
        self.tree = tree
        self.files = files
        self.directory = Storage()

        self._uidmap = None

        # Mandatory fields
        self.mandatory_fields = Storage()

        self.elements = Storage()
        self.items = Storage()
        self.references = []

        self.count = 0 # total number of records imported
        self.errors = 0 # total number of records in error
        self.created = [] # IDs of created records
        self.updated = [] # IDs of updated records
        self.deleted = [] # IDs of deleted records
        self.skipped = [] # IDs of skipped records

        self.log = None

        # Import strategy
        if strategy is None:
            METHOD = ImportItem.METHOD
            strategy = [METHOD.CREATE,
                        METHOD.UPDATE,
                        METHOD.DELETE,
                        METHOD.MERGE,
                        ]
        if not isinstance(strategy, (tuple, list)):
            strategy = [strategy]
        self.strategy = strategy

        # Synchronization settings
        if sync_policy:
            self.update_policy = sync_policy.update_policy or SyncPolicy.OTHER
            self.conflict_policy = sync_policy.conflict_policy or SyncPolicy.MASTER
            self.last_sync = sync_policy.last_sync
            self.onconflict = sync_policy.onconflict
        else:
            self.update_policy = SyncPolicy.OTHER
            self.conflict_policy = SyncPolicy.MASTER
            self.last_sync = None
            self.onconflict = None

        self.mtime = None
        if job_id:
            s3db = current.s3db
            jobtable = s3db.s3_import_job
            if str(job_id).isdigit():
                query = (jobtable.id == job_id)
            else:
                query = (jobtable.job_id == job_id)
            row = current.db(query).select(jobtable.job_id,
                                           jobtable.tablename,
                                           limitby=(0, 1)).first()
            if not row:
                raise SyntaxError("Job record not found")
            self.job_id = row.job_id
            self.second_pass = True
            if not self.table:
                tablename = row.tablename
                try:
                    table = s3db[tablename]
                except AttributeError:
                    pass
        else:
            self.job_id = uuid.uuid4() # unique ID for this job
            self.second_pass = False

    # -------------------------------------------------------------------------
    @property
    def uidmap(self):
        """
            Map uuid/tuid => element, for faster reference lookups
        """

        uidmap = self._uidmap
        tree = self.tree

        if uidmap is None and tree is not None:

            root = tree if isinstance(tree, etree._Element) else tree.getroot()

            xml = current.xml
            UUID = xml.UID
            TUID = xml.ATTRIBUTE.tuid
            NAME = xml.ATTRIBUTE.name

            elements = root.xpath(".//%s" % xml.TAG.resource)
            self._uidmap = uidmap = {UUID: {},
                                     TUID: {},
                                     }
            uuidmap = uidmap[UUID]
            tuidmap = uidmap[TUID]
            for element in elements:
                name = element.get(NAME)
                r_uuid = element.get(UUID)
                if r_uuid and r_uuid not in uuidmap:
                    uuidmap[(name, r_uuid)] = element
                r_tuid = element.get(TUID)
                if r_tuid and r_tuid not in tuidmap:
                    tuidmap[(name, r_tuid)] = element

        return uidmap

    # -------------------------------------------------------------------------
    def add_item(self,
                 element = None,
                 original = None,
                 components = None,
                 parent = None,
                 joinby = None):
        """
            Parse and validate an XML element and add it as new item
            to the job.

            Args:
                element: the element
                original: the original DB record (if already available,
                          will otherwise be looked-up by this function)
                components: a dictionary of components (as in CRUDResource)
                            to include in the job (defaults to all
                            defined components)
                parent: the parent item (if this is a component)
                joinby: the component join key(s) (if this is a component)

            Returns:
                a unique identifier for the new item, or None if there
                was an error. self.error contains the last error, and
                self.error_tree an element tree with all failing elements
                including error attributes.
        """

        if element in self.elements:
            # element has already been added to this job
            return self.elements[element]

        # Parse the main element
        item = ImportItem(self)

        # Update lookup lists
        item_id = item.item_id
        self.items[item_id] = item
        if element is not None:
            self.elements[element] = item_id

        if not item.parse(element,
                          original = original,
                          files = self.files):
            self.error = item.error
            item.accepted = False
            if parent is None:
                self.error_tree.append(deepcopy(item.element))

        else:
            # Now parse the components
            table = item.table

            s3db = current.s3db
            components = s3db.get_components(table, names=components)
            super_keys = s3db.get_super_keys(table)

            cnames = Storage()
            cinfos = Storage()
            for alias in components:

                component = components[alias]

                ctable = component.table
                if ctable._id != "id" and "instance_type" in ctable.fields:
                    # Super-entities cannot be imported to directly => skip
                    continue

                # Determine the keys
                pkey = component.pkey

                if pkey != table._id.name and pkey not in super_keys:
                    # Pseudo-component cannot be imported => skip
                    continue

                if component.linktable:
                    ctable = component.linktable
                    fkey = component.lkey
                else:
                    fkey = component.fkey

                ctablename = ctable._tablename
                if ctablename in cnames:
                    cnames[ctablename].append(alias)
                else:
                    cnames[ctablename] = [alias]

                cinfos[(ctablename, alias)] = Storage(component = component,
                                                      ctable = ctable,
                                                      pkey = pkey,
                                                      fkey = fkey,
                                                      first = True,
                                                      )
            add_item = self.add_item
            xml = current.xml
            UID = xml.UID
            for celement in xml.components(element, names=list(cnames.keys())):

                # Get the component tablename
                ctablename = celement.get(xml.ATTRIBUTE.name, None)
                if not ctablename or ctablename not in cnames:
                    continue

                # Get the component alias (for disambiguation)
                calias = celement.get(xml.ATTRIBUTE.alias, None)
                if calias is None:
                    aliases = cnames[ctablename]
                    if len(aliases) == 1:
                        calias = aliases[0]
                    else:
                        calias = ctablename.split("_", 1)[1]

                if (ctablename, calias) not in cinfos:
                    continue
                cinfo = cinfos[(ctablename, calias)]

                component = cinfo.component
                ctable = cinfo.ctable

                pkey = cinfo.pkey
                fkey = cinfo.fkey

                original = None

                if not component.multiple:
                    # Single-component: skip all subsequent items after
                    # the first under the same master record
                    if not cinfo.first:
                        continue
                    cinfo.first = False

                    # Single component = the first component record
                    # under the master record is always the original,
                    # only relevant if the master record exists in
                    # the db and hence item.id is not None
                    if item.id:
                        db = current.db
                        query = (table.id == item.id) & \
                                (table[pkey] == ctable[fkey])
                        if UID in ctable.fields:
                            # Load only the UUID now, parse will load any
                            # required data later
                            row = db(query).select(ctable[UID],
                                                   limitby = (0, 1)
                                                   ).first()
                            if row:
                                original = row[UID]
                        else:
                            # Not nice, but a rare edge-case
                            original = db(query).select(ctable.ALL,
                                                        limitby = (0, 1)
                                                        ).first()

                # Recurse
                item_id = add_item(element = celement,
                                   original = original,
                                   parent = item,
                                   joinby = (pkey, fkey))
                if item_id is None:
                    item.error = self.error
                    self.error_tree.append(deepcopy(item.element))
                else:
                    citem = self.items[item_id]
                    citem.parent = item
                    item.components.append(citem)

            lookahead = self.lookahead
            directory = self.directory

            # Handle references
            table = item.table
            data = item.data
            tree = self.tree

            def schedule(reference):
                """ Schedule a referenced item for implicit import """
                entry = reference.entry
                if entry and entry.element is not None and not entry.item_id:
                    item_id = add_item(element=entry.element)
                    if item_id:
                        entry.item_id = item_id

            # Foreign key fields in table
            if tree is not None:
                fields = [table[f] for f in table.fields]
                rfields = [f for f in fields if s3_has_foreign_key(f)]
                item.references = lookahead(element,
                                            table = table,
                                            fields = rfields,
                                            tree = tree,
                                            directory = directory,
                                            )
                for reference in item.references:
                    schedule(reference)

            references = item.references
            rappend = references.append

            # Parent reference
            if parent is not None:
                entry = Storage(item_id = parent.item_id,
                                element = parent.element,
                                tablename = parent.tablename,
                                )
                rappend(Storage(field = joinby,
                                entry = entry,
                                ))

            # References in JSON field data
            json_references = s3db.get_config(table, "json_references")
            if json_references:
                if json_references is True:
                    # Discover references in any JSON fields
                    fields = table.fields
                else:
                    # Discover references in fields specified by setting
                    fields = json_references
                    if not isinstance(fields, (tuple, list)):
                        fields = [fields]
                for fieldname in fields:
                    value = data.get(fieldname)
                    field = table[fieldname]
                    if value and field.type == "json":
                        objref = ObjectReferences(value)
                        for ref in objref.refs:
                            rl = lookahead(None,
                                           tree = tree,
                                           directory = directory,
                                           lookup = ref,
                                           )
                            if rl:
                                reference = rl[0]
                                schedule(reference)
                                rappend(Storage(field = fieldname,
                                                objref = objref,
                                                refkey = ref,
                                                entry = reference.entry,
                                                ))

            # Replacement reference
            deleted = data.get(xml.DELETED, False)
            if deleted:
                fieldname = xml.REPLACEDBY
                replaced_by = data.get(fieldname)
                if replaced_by:
                    rl = lookahead(element,
                                   tree = tree,
                                   directory = directory,
                                   lookup = (table, replaced_by),
                                   )
                    if rl:
                        reference = rl[0]
                        schedule(reference)
                        rappend(Storage(field = fieldname,
                                        entry = reference.entry,
                                        ))

        return item.item_id

    # -------------------------------------------------------------------------
    def lookahead(self,
                  element,
                  table = None,
                  fields = None,
                  tree = None,
                  directory = None,
                  lookup = None):
        """
            Find referenced elements in the tree

            Args:
                element: the element
                table: the DB table
                fields: the FK fields in the table
                tree: the import tree
                directory: a dictionary to lookup elements in the tree
                           (will be filled in by this function)
        """

        db = current.db
        s3db = current.s3db

        xml = current.xml
        import_uid = xml.import_uid

        ATTRIBUTE = xml.ATTRIBUTE
        TAG = xml.TAG
        UID = xml.UID

        reference_list = []
        rlappend = reference_list.append

        root = None
        if tree is not None:
            root = tree if isinstance(tree, etree._Element) else tree.getroot()
        uidmap = self.uidmap

        references = [lookup] if lookup else element.findall("reference")
        for reference in references:
            if lookup:
                field = None
                if element is None:
                    tablename, attr, uid = reference
                    ktable = s3db.table(tablename)
                    if ktable is None:
                        continue
                    uids = [import_uid(uid)] if attr == "uuid" else [uid]
                else:
                    tablename = element.get(ATTRIBUTE.name, None)
                    ktable, uid = reference
                    attr = UID
                    uids = [import_uid(uid)]
            else:
                field = reference.get(ATTRIBUTE.field, None)

                # Ignore references without valid field-attribute
                if not field or field not in fields or field not in table:
                    continue

                # Find the key table
                ktablename, _, multiple = s3_get_foreign_key(table[field])
                if not ktablename:
                    continue
                try:
                    ktable = s3db[ktablename]
                except AttributeError:
                    continue

                tablename = reference.get(ATTRIBUTE.resource, None)
                # Ignore references to tables without UID field:
                if UID not in ktable.fields:
                    continue
                # Fall back to key table name if tablename is not specified:
                if not tablename:
                    tablename = ktablename
                # Super-entity references must use the super-key:
                if tablename != ktablename:
                    field = (ktable._id.name, field)
                # Ignore direct references to super-entities:
                if tablename == ktablename and ktable._id.name != "id":
                    continue
                # Get the foreign key
                uids = reference.get(UID, None)
                attr = UID
                if not uids:
                    uids = reference.get(ATTRIBUTE.tuid, None)
                    attr = ATTRIBUTE.tuid
                if uids and multiple:
                    uids = json.loads(uids)
                elif uids:
                    uids = [uids]

            # Find the elements and map to DB records
            relements = []

            # Create a UID<->ID map
            id_map = {}
            if attr == UID and uids:
                if len(uids) == 1:
                    uid = import_uid(uids[0])
                    query = (ktable[UID] == uid)
                    record = db(query).select(ktable.id,
                                              cacheable = True,
                                              limitby = (0, 1),
                                              ).first()
                    if record:
                        id_map[uid] = record.id
                else:
                    uids_ = [import_uid(uid) for uid in uids]
                    query = (ktable[UID].belongs(uids_))
                    records = db(query).select(ktable.id,
                                               ktable[UID],
                                               limitby = (0, len(uids_)),
                                               )
                    for r in records:
                        id_map[r[UID]] = r.id

            if not uids:
                # Anonymous reference: <resource> inside the element
                expr = './/%s[@%s="%s"]' % (TAG.resource,
                                            ATTRIBUTE.name,
                                            tablename,
                                            )
                relements = reference.xpath(expr)
                if relements and not multiple:
                    relements = relements[:1]

            elif root is not None:

                for uid in uids:

                    entry = None

                    # Entry already in directory?
                    if directory is not None:
                        entry = directory.get((tablename, attr, uid))

                    if not entry:
                        e = uidmap[attr].get((tablename, uid)) if uidmap else None
                        if e is not None:
                            # Element in the source => append to relements
                            relements.append(e)
                        else:
                            # No element found, see if original record exists
                            _uid = import_uid(uid)
                            if _uid and _uid in id_map:
                                _id = id_map[_uid]
                                entry = Storage(tablename = tablename,
                                                element = None,
                                                uid = uid,
                                                id = _id,
                                                item_id = None,
                                                )
                                rlappend(Storage(field = field,
                                                 element = reference,
                                                 entry = entry,
                                                 ))
                            else:
                                continue
                    else:
                        rlappend(Storage(field = field,
                                         element = reference,
                                         entry = entry,
                                         ))

            # Create entries for all newly found elements
            for relement in relements:
                uid = relement.get(attr, None)
                if attr == UID:
                    _uid = import_uid(uid)
                    _id = _uid and id_map and id_map.get(_uid, None) or None
                else:
                    _uid = None
                    _id = None
                entry = Storage(tablename = tablename,
                                element = relement,
                                uid = uid,
                                id = _id,
                                item_id = None,
                                )
                # Add entry to directory
                if uid and directory is not None:
                    directory[(tablename, attr, uid)] = entry
                # Append the entry to the reference list
                rlappend(Storage(field = field,
                                 element = reference,
                                 entry = entry,
                                 ))

        return reference_list

    # -------------------------------------------------------------------------
    def load_item(self, row):
        """
            Load an item from the item table (counterpart to add_item
            when restoring a job from the database)
        """

        item = ImportItem(self)
        if not item.restore(row):
            self.error = item.error
            if item.load_parent is None:
                self.error_tree.append(deepcopy(item.element))
        # Update lookup lists
        item_id = item.item_id
        self.items[item_id] = item
        return item_id

    # -------------------------------------------------------------------------
    def resolve(self, item_id, import_list):
        """
            Resolve the reference list of an item

            Args:
                item_id: the import item UID
                import_list: the ordered list of items (UIDs) to import
        """

        item = self.items[item_id]
        if item.lock or item.accepted is False:
            return False
        references = []
        for reference in item.references:
            ritem_id = reference.entry.item_id
            if ritem_id and ritem_id not in import_list:
                references.append(ritem_id)
        for ritem_id in references:
            item.lock = True
            if self.resolve(ritem_id, import_list):
                import_list.append(ritem_id)
            item.lock = False
        return True

    # -------------------------------------------------------------------------
    def commit(self, ignore_errors=False, log_items=None):
        """
            Commit the import job to the DB

            Args:
                ignore_errors: skip any items with errors
                               (does still report the errors)
                log_items: callback function to log import items
                           before committing them
        """

        ATTRIBUTE = current.xml.ATTRIBUTE
        METHOD = ImportItem.METHOD

        # Resolve references
        import_list = []
        for item_id in self.items:
            self.resolve(item_id, import_list)
            if item_id not in import_list:
                import_list.append(item_id)
        # Commit the items
        items = self.items
        count = 0
        errors = 0
        mtime = None
        created = []
        updated = []
        deleted = []
        skipped = []
        tablename = self.table._tablename

        self.log = log_items
        failed = False
        for item_id in import_list:
            item = items[item_id]
            error = None

            if item.accepted is not False:
                logged = False
                success = item.commit(ignore_errors=ignore_errors)
            else:
                # Field validation failed
                logged = True
                success = ignore_errors

            if not success:
                failed = True

            error = item.error
            if error:
                current.log.error(error)
                self.error = error
                element = item.element
                if element is not None:
                    if not element.get(ATTRIBUTE.error, False):
                        element.set(ATTRIBUTE.error, s3_str(error))
                    if not logged:
                        self.error_tree.append(deepcopy(element))
                if item.tablename == tablename:
                    errors += 1

            elif item.tablename == tablename:
                count += 1
                if mtime is None or item.mtime > mtime:
                    mtime = item.mtime
                if item.id:
                    if item.skip:
                        skipped.append(item.id)
                    elif item.method == METHOD.CREATE:
                        created.append(item.id)
                    elif item.method == METHOD.UPDATE:
                        updated.append(item.id)
                    elif item.method in (METHOD.MERGE, METHOD.DELETE):
                        deleted.append(item.id)

        if failed:
            return False

        self.count = count
        self.errors = errors
        self.mtime = mtime
        self.created = created
        self.updated = updated
        self.deleted = deleted
        self.skipped = skipped
        return True

    # -------------------------------------------------------------------------
    def store(self):
        """
            Store this job and all its items in the job table
        """

        db = current.db
        s3db = current.s3db

        jobtable = s3db.s3_import_job
        query = (jobtable.job_id == self.job_id)
        row = db(query).select(jobtable.id, limitby=(0, 1)).first()
        if row:
            record_id = row.id
        else:
            record_id = None
        record = Storage(job_id=self.job_id)
        try:
            tablename = self.table._tablename
        except AttributeError:
            pass
        else:
            record.update(tablename=tablename)
        for item in self.items.values():
            item.store(item_table=s3db.s3_import_item)
        if record_id:
            db(jobtable.id == record_id).update(**record)
        else:
            record_id = jobtable.insert(**record)

        return record_id

    # -------------------------------------------------------------------------
    def get_tree(self):
        """
            Reconstruct the element tree of this job
        """

        if self.tree is not None:
            return self.tree
        else:
            xml = current.xml
            ATTRIBUTE = xml.ATTRIBUTE
            UID = xml.UID
            root = etree.Element(xml.TAG.root)
            for item in self.items.values():
                element = item.element
                if element is not None and not item.parent:
                    if item.tablename == self.table._tablename or \
                       element.get(UID, None) or \
                       element.get(ATTRIBUTE.tuid, None):
                        root.append(deepcopy(element))
            return etree.ElementTree(root)

    # -------------------------------------------------------------------------
    def delete(self):
        """
            Delete this job and all its items from the job table
        """

        db = current.db
        s3db = current.s3db

        job_id = self.job_id

        item_table = s3db.s3_import_item
        db(item_table.job_id == job_id).delete()

        job_table = s3db.s3_import_job
        db(job_table.job_id == job_id).delete()

    # -------------------------------------------------------------------------
    def restore_references(self):
        """
            Restore the job's reference structure after loading items
            from the item table
        """

        db = current.db
        UID = current.xml.UID

        for item in self.items.values():
            for citem_id in item.load_components:
                if citem_id in self.items:
                    item.components.append(self.items[citem_id])
            item.load_components = []
            for ritem in item.load_references:
                field = ritem["field"]
                if "item_id" in ritem:
                    item_id = ritem["item_id"]
                    if item_id in self.items:
                        _item = self.items[item_id]
                        entry = Storage(tablename=_item.tablename,
                                        element=_item.element,
                                        uid=_item.uid,
                                        id=_item.id,
                                        item_id=item_id)
                        item.references.append(Storage(field=field,
                                                       entry=entry))
                else:
                    _id = None
                    uid = ritem.get("uid", None)
                    tablename = ritem.get("tablename", None)
                    if tablename and uid:
                        try:
                            table = current.s3db[tablename]
                        except AttributeError:
                            continue
                        if UID not in table.fields:
                            continue
                        query = table[UID] == uid
                        row = db(query).select(table._id,
                                               limitby=(0, 1)).first()
                        if row:
                            _id = row[table._id.name]
                        else:
                            continue
                        entry = Storage(tablename = ritem["tablename"],
                                        element=None,
                                        uid = ritem["uid"],
                                        id = _id,
                                        item_id = None)
                        item.references.append(Storage(field=field,
                                                       entry=entry))
            item.load_references = []
            if item.load_parent is not None:
                parent = self.items[item.load_parent]
                if parent is None:
                    # Parent has been removed
                    item.skip = True
                else:
                    item.parent = parent
                item.load_parent = None

# =============================================================================
class ImportItem:
    """ Class representing an import item (=a single record) """

    METHOD = Storage(
        CREATE = "create",
        UPDATE = "update",
        DELETE = "delete",
        MERGE = "merge"
    )

    def __init__(self, job):
        """
            Args:
                job: the import job this item belongs to
        """

        self.job = job

        # Locking and error handling
        self.lock = False
        self.error = None

        # Identification
        self.item_id = uuid.uuid4() # unique ID for this item
        self.id = None
        self.uid = None

        # Data elements
        self.table = None
        self.tablename = None
        self.element = None
        self.data = None
        self.original = None
        self.components = []
        self.references = []
        self.load_components = []
        self.load_references = []
        self.parent = None
        self.load_parent = None
        self.skip = False

        # Conflict handling
        self.mci = 2
        self.mtime = datetime.datetime.utcnow()
        self.modified = True
        self.conflict = False

        # Allowed import methods
        self.strategy = job.strategy
        # Update and conflict resolution policies
        self.update_policy = job.update_policy
        self.conflict_policy = job.conflict_policy

        # Actual import method
        self.method = None

        self.onvalidation = None
        self.onaccept = None

        # Item import status flags
        self.accepted = None
        self.permitted = False
        self.committed = False

        # Writeback hook for circular references:
        # Items which need a second write to update references
        self.update = []

    # -------------------------------------------------------------------------
    def __repr__(self):
        """ Helper method for debugging """

        _str = "<ImportItem %s {item_id=%s uid=%s id=%s error=%s data=%s}>" % \
               (self.table, self.item_id, self.uid, self.id, self.error, self.data)
        return _str

    # -------------------------------------------------------------------------
    def parse(self,
              element,
              original = None,
              table = None,
              tree = None,
              files = None
              ):
        """
            Read data from a <resource> element

            Args:
                element: the element
                table: the DB table
                tree: the import tree
                files: uploaded files

            Returns:
                True if successful, False if not (sets self.error)
        """

        s3db = current.s3db
        xml = current.xml

        ERROR = xml.ATTRIBUTE["error"]

        self.element = element
        if table is None:
            tablename = element.get(xml.ATTRIBUTE["name"])
            table = s3db.table(tablename)
            if table is None:
                self.error = current.ERROR.BAD_RESOURCE
                element.set(ERROR, s3_str(self.error))
                return False
        else:
            tablename = table._tablename

        self.table = table
        self.tablename = tablename

        UID = xml.UID

        from ..resource import CRUDResource
        if original is None:
            original = CRUDResource.original(table,
                                             element,
                                             mandatory = self._mandatory_fields(),
                                             )
        elif isinstance(original, str) and UID in table.fields:
            # Single-component update in add-item => load the original now
            query = (table[UID] == original)
            pkeys = set(fname for fname in table.fields if table[fname].unique)
            fields = CRUDResource.import_fields(table,
                                                pkeys,
                                                mandatory = self._mandatory_fields(),
                                                )
            original = current.db(query).select(limitby=(0, 1), *fields).first()
        else:
            original = None

        postprocess = s3db.get_config(tablename, "xml_post_parse")
        data = xml.record(table, element,
                          files = files,
                          original = original,
                          postprocess = postprocess)

        if data is None:
            self.error = current.ERROR.VALIDATION_ERROR
            self.accepted = False
            if not element.get(ERROR, False):
                element.set(ERROR, s3_str(self.error))
            return False

        self.data = data

        MCI = xml.MCI
        MTIME = xml.MTIME

        self.uid = data.get(UID)
        if original is not None:

            self.original = original
            self.id = original[table._id.name]

            if not current.response.s3.synchronise_uuids and UID in original:
                self.uid = self.data[UID] = original[UID]

        if MTIME in data:
            self.mtime = data[MTIME]
        if MCI in data:
            self.mci = data[MCI]

        #current.log.debug("New item: %s" % self)
        return True

    # -------------------------------------------------------------------------
    def deduplicate(self):
        """
            Detect whether this is an update or a new record
        """

        table = self.table
        if table is None or self.id:
            return

        from ..resource import CRUDResource

        METHOD = self.METHOD
        CREATE = METHOD["CREATE"]
        UPDATE = METHOD["UPDATE"]
        DELETE = METHOD["DELETE"]
        MERGE = METHOD["MERGE"]

        xml = current.xml
        UID = xml.UID

        data = self.data
        if self.job.second_pass and UID in table.fields:
            uid = data.get(UID)
            if uid and not self.element.get(UID) and not self.original:
                # Previously identified original does no longer exist
                del data[UID]

        mandatory = self._mandatory_fields()

        if self.original is not None:
            original = self.original
        elif self.data:
            original = CRUDResource.original(table,
                                             self.data,
                                             mandatory = mandatory,
                                             )
        else:
            original = None

        synchronise_uuids = current.response.s3.synchronise_uuids

        deleted = data[xml.DELETED]
        if deleted:
            if data[xml.REPLACEDBY]:
                self.method = MERGE
            else:
                self.method = DELETE

        self.uid = data.get(UID)

        if original is not None:

            # The original record could be identified by a unique-key-match,
            # so this must be an update
            self.id = original[table._id.name]

            if not deleted:
                self.method = UPDATE

        else:

            if UID in data and not synchronise_uuids:
                # The import item has a UUID but there is no match
                # in the database, so this must be a new record
                self.id = None
                if not deleted:
                    self.method = CREATE
                else:
                    # Nonexistent record to be deleted => skip
                    self.method = DELETE
                    self.skip = True
            else:
                # Use the resource's deduplicator to identify the original
                resolve = current.s3db.get_config(self.tablename, "deduplicate")
                if data and resolve:
                    resolve(self)

            if self.id and self.method in (UPDATE, DELETE, MERGE):
                # Retrieve the original
                fields = CRUDResource.import_fields(table,
                                                    data,
                                                    mandatory = mandatory,
                                                    )
                original = current.db(table._id == self.id) \
                                  .select(limitby=(0, 1), *fields).first()

        # Retain the original UUID (except in synchronise_uuids mode)
        if original and not synchronise_uuids and UID in original:
            self.uid = data[UID] = original[UID]

        self.original = original

    # -------------------------------------------------------------------------
    def authorize(self):
        """
            Authorize the import of this item, sets self.permitted
        """

        if not self.table:
            return False

        auth = current.auth
        tablename = self.tablename

        # Check whether self.table is protected
        if not auth.override and tablename.split("_", 1)[0] in auth.PROTECTED:
            return False

        # Determine the method
        METHOD = self.METHOD
        if self.data.deleted is True:
            if self.data.deleted_rb:
                self.method = METHOD["MERGE"]
            else:
                self.method = METHOD["DELETE"]
            self.accepted = True if self.id else False
        elif self.id:
            if not self.original:
                from ..resource import CRUDResource
                fields = CRUDResource.import_fields(self.table,
                                                    self.data,
                                                    mandatory = self._mandatory_fields(),
                                                    )
                query = (self.table.id == self.id)
                self.original = current.db(query).select(limitby=(0, 1),
                                                         *fields).first()
            if self.original:
                self.method = METHOD["UPDATE"]
            else:
                self.method = METHOD["CREATE"]
        else:
            self.method = METHOD["CREATE"]

        # Set self.id
        if self.method == METHOD["CREATE"]:
            self.id = 0

        # Authorization
        authorize = current.auth.s3_has_permission
        if authorize:
            self.permitted = authorize(self.method,
                                       tablename,
                                       record_id=self.id)
        else:
            self.permitted = True

        return self.permitted

    # -------------------------------------------------------------------------
    def validate(self):
        """
            Validate this item (=record onvalidation), sets self.accepted
        """

        data = self.data

        if self.accepted is not None:
            return self.accepted
        if data is None or not self.table:
            self.accepted = False
            return False

        xml = current.xml
        ERROR = xml.ATTRIBUTE["error"]

        METHOD = self.METHOD
        DELETE = METHOD.DELETE
        MERGE = METHOD.MERGE

        # Detect update
        if not self.id:
            self.deduplicate()
        if self.accepted is False:
            # Item rejected by deduplicator (e.g. due to ambiguity)
            return False

        # Don't need to validate skipped or deleted records
        if self.skip or self.method in (DELETE, MERGE):
            self.accepted = True if self.id else False
            return True

        # Set dynamic defaults for new records
        if not self.id:
            self._dynamic_defaults(data)

        # Check for mandatory fields
        required_fields = self._mandatory_fields()

        all_fields = list(data.keys())

        failed_references = []
        items = self.job.items
        for reference in self.references:
            resolvable = resolved = True
            entry = reference.entry
            if entry and not entry.id:
                if entry.item_id:
                    item = items[entry.item_id]
                    if item.error:
                        relement = reference.element
                        if relement is not None:
                            # Repeat the errors from the referenced record
                            # in the <reference> element (better reasoning)
                            msg = "; ".join(xml.collect_errors(entry.element))
                            relement.set(ERROR, msg)
                        else:
                            resolvable = False
                        resolved = False
                else:
                    resolvable = resolved = False
            field = reference.field
            if isinstance(field, (tuple, list)):
                field = field[1]
            if resolved:
                all_fields.append(field)
            elif resolvable:
                # Both reference and referenced record are in the XML,
                # => treat foreign key as mandatory, and mark as failed
                if field not in required_fields:
                    required_fields.append(field)
                if field not in failed_references:
                    failed_references.append(field)

        missing = [fname for fname in required_fields
                         if fname not in all_fields]

        original = self.original
        if missing:
            if original:
                missing = [fname for fname in missing
                                 if fname not in original]
            if missing:
                fields = [f for f in missing
                            if f not in failed_references]
                if fields:
                    errors = ["%s: value(s) required" % ", ".join(fields)]
                else:
                    errors = []
                if failed_references:
                    fields = ", ".join(failed_references)
                    errors.append("%s: reference import(s) failed" %
                                  ", ".join(failed_references))
                self.error = "; ".join(errors)
                self.element.set(ERROR, self.error)
                self.accepted = False
                return False

        # Run onvalidation
        form = Storage(method = self.method,
                       vars = data,
                       request_vars = data,
                       # Useless since always incomplete:
                       #record = original,
                       )
        if self.id:
            form.vars.id = self.id

        form.errors = Storage()
        tablename = self.tablename
        key = "%s_onvalidation" % self.method
        get_config = current.s3db.get_config
        onvalidation = get_config(tablename, key,
                       get_config(tablename, "onvalidation"))
        if onvalidation:
            try:
                callback(onvalidation, form, tablename=tablename)
            except:
                from traceback import format_exc
                current.log.error("S3Import %s onvalidation exception:" % tablename)
                current.log.debug(format_exc(10))
        accepted = True
        if form.errors:
            element = self.element
            for k in form.errors:
                e = element.findall("data[@field='%s']" % k)
                if not e:
                    e = element.findall("reference[@field='%s']" % k)
                if not e:
                    e = element
                    form.errors[k] = "[%s] %s" % (k, form.errors[k])
                else:
                    e = e[0]
                e.set(ERROR, s3_str(form.errors[k]))
            self.error = current.ERROR.VALIDATION_ERROR
            accepted = False

        self.accepted = accepted
        return accepted

    # -------------------------------------------------------------------------
    def commit(self, ignore_errors=False):
        """
            Commit this item to the database

            Args:
                ignore_errors: skip invalid components (still reports errors)
        """

        if self.committed:
            # already committed
            return True

        # If the parent item gets skipped, then skip this item as well
        if self.parent is not None and self.parent.skip:
            return True

        # Globals
        db = current.db
        s3db = current.s3db

        xml = current.xml
        ATTRIBUTE = xml.ATTRIBUTE

        # Methods
        METHOD = self.METHOD
        CREATE = METHOD.CREATE
        UPDATE = METHOD.UPDATE
        DELETE = METHOD.DELETE
        MERGE = METHOD.MERGE

        # Policies
        THIS = SyncPolicy.THIS
        OTHER = SyncPolicy.OTHER
        NEWER = SyncPolicy.NEWER
        MASTER = SyncPolicy.MASTER
        POLICY = {THIS, OTHER, NEWER, MASTER}

        # Constants
        UID = xml.UID
        MCI = xml.MCI
        MTIME = xml.MTIME
        VALIDATION_ERROR = current.ERROR.VALIDATION_ERROR

        # Make item mtime TZ-aware
        self.mtime = s3_utc(self.mtime)

        # Resolve references
        self._resolve_references()

        # Deduplicate and validate
        if not self.validate():
            self.skip = True

            # Notify the error in the parent to have reported in the
            # interactive (2-phase) importer
            # Note that the parent item is already written at this point,
            # so this notification can NOT prevent/rollback the import of
            # the parent item if ignore_errors is True (forced commit), or
            # if the user deliberately chose to import it despite error.
            parent = self.parent
            if parent is not None:
                parent.error = VALIDATION_ERROR
                element = parent.element
                if not element.get(ATTRIBUTE.error, False):
                    element.set(ATTRIBUTE.error, s3_str(parent.error))

            return ignore_errors

        elif self.method not in (MERGE, DELETE) and self.components:
            for component in self.components:
                if component.accepted is False or \
                   component.data is None:
                    component.skip = True
                    # Skip this item on any component validation errors
                    self.skip = True
                    self.error = VALIDATION_ERROR
                    return ignore_errors

        elif self.method in (MERGE, DELETE) and not self.accepted:
            self.skip = True
            # Deletion of non-existent record: ignore silently
            return True

        # Authorize item
        if not self.authorize():
            self.error = "%s: %s, %s, %s" % (current.ERROR.NOT_PERMITTED,
                                             self.method,
                                             self.tablename,
                                             self.id)
            self.skip = True
            return ignore_errors

        # Update the method
        method = self.method

        # Check if import method is allowed in strategy
        strategy = self.strategy
        if not isinstance(strategy, (list, tuple)):
            strategy = [strategy]
        if method not in strategy:
            self.error = current.ERROR.NOT_PERMITTED
            self.skip = True
            return True

        # Check mtime and mci
        table = self.table
        original = self.original
        original_mtime = None
        original_mci = 0
        if original:
            if hasattr(table, MTIME):
                original_mtime = s3_utc(original[MTIME])
            if hasattr(table, MCI):
                original_mci = original[MCI]
            original_deleted = "deleted" in original and original.deleted
        else:
            original_deleted = False

        # Detect conflicts
        job = self.job
        original_modified = True
        self.modified = True
        self.conflict = False
        last_sync = s3_utc(job.last_sync)
        if last_sync:
            if original_mtime and original_mtime < last_sync:
                original_modified = False
            if self.mtime and self.mtime < last_sync:
                self.modified = False
            if self.modified and original_modified:
                self.conflict = True
        if self.conflict and method in (UPDATE, DELETE, MERGE):
            if job.onconflict:
                job.onconflict(self)

        if self.data is not None:
            data = filter_fields(table, self.data, allow_id=True)
        else:
            data = Storage()

        # Update policy
        if isinstance(self.update_policy, dict):
            def update_policy(f):
                setting = self.update_policy
                p = setting.get(f,
                    setting.get("__default__", THIS))
                if p not in POLICY:
                    return THIS
                return p
        else:
            def update_policy(f):
                p = self.update_policy
                if p not in POLICY:
                    return THIS
                return p

        # Log this item
        if callable(job.log):
            job.log(self)

        tablename = self.tablename
        enforce_realm_update = False

        # Update existing record
        if method == UPDATE:

            if original:
                if original_deleted:
                    policy = update_policy(None)
                    if policy == NEWER and \
                       original_mtime and original_mtime > self.mtime or \
                       policy == MASTER and \
                       (original_mci == 0 or self.mci != 1):
                        self.skip = True
                        return True

                for f in list(data.keys()):
                    if f in original:
                        # Check if unchanged
                        if isinstance(original[f], datetime.datetime):
                            if s3_utc(data[f]) == s3_utc(original[f]):
                                del data[f]
                                continue
                        else:
                            if data[f] == original[f]:
                                del data[f]
                                continue
                    remove = False
                    policy = update_policy(f)
                    if policy == THIS:
                        remove = True
                    elif policy == NEWER:
                        if original_mtime and original_mtime > self.mtime:
                            remove = True
                    elif policy == MASTER:
                        if original_mci == 0 or self.mci != 1:
                            remove = True
                    if remove:
                        del data[f]

                if original_deleted:
                    # Undelete re-imported records
                    data["deleted"] = False
                    if hasattr(table, "deleted_fk"):
                        data["deleted_fk"] = ""

                    # Set new author stamp
                    if hasattr(table, "created_by"):
                        data["created_by"] = table.created_by.default
                    if hasattr(table, "modified_by"):
                        data["modified_by"] = table.modified_by.default

                    # Restore defaults for foreign keys
                    for fieldname in table.fields:
                        field = table[fieldname]
                        default = field.default
                        if str(field.type)[:9] == "reference" and \
                           fieldname not in data and \
                           default is not None:
                            data[fieldname] = default

                    # Enforce update of realm entity
                    enforce_realm_update = True

            if not self.skip and not self.conflict and \
               (len(data) or self.components or self.references):
                if self.uid and hasattr(table, UID):
                    data[UID] = self.uid
                if MTIME in table:
                    data[MTIME] = self.mtime
                if MCI in data:
                    # retain local MCI on updates
                    del data[MCI]
                query = (table._id == self.id)
                try:
                    db(query).update(**dict(data))
                except:
                    self.error = sys.exc_info()[1]
                    self.skip = True
                    return ignore_errors
                else:
                    self.committed = True
            else:
                # Nothing to update
                self.committed = True

        # Create new record
        elif method == CREATE:

            # Do not apply field policy to UID and MCI
            if UID in data:
                del data[UID]
            if MCI in data:
                del data[MCI]

            for f in data:
                if update_policy(f) == MASTER and self.mci != 1:
                    del data[f]

            if self.skip:
                return True

            elif len(data) or self.components or self.references:

                # Restore UID and MCI
                if self.uid and UID in table.fields:
                    data[UID] = self.uid
                if MCI in table.fields:
                    data[MCI] = self.mci

                # Insert the new record
                try:
                    success = table.insert(**dict(data))
                except:
                    self.error = sys.exc_info()[1]
                    self.skip = True
                    return ignore_errors
                if success:
                    self.id = success
                    self.committed = True

            else:
                # Nothing to create
                self.skip = True
                return True

        # Delete local record
        elif method == DELETE:

            if original:
                if original_deleted:
                    self.skip = True
                policy = update_policy(None)
                if policy == THIS:
                    self.skip = True
                elif policy == NEWER and \
                     (original_mtime and original_mtime > self.mtime):
                    self.skip = True
                elif policy == MASTER and \
                     (original_mci == 0 or self.mci != 1):
                    self.skip = True
            else:
                self.skip = True

            if not self.skip and not self.conflict:

                resource = s3db.resource(tablename, id=self.id)
                # Use cascade=True so that the deletion can be
                # rolled back (e.g. trial phase, subsequent failure)
                success = resource.delete(cascade=True)
                if resource.error:
                    self.error = resource.error
                    self.skip = True
                    return ignore_errors

            return True

        # Merge records
        elif method == MERGE:

            if UID not in table.fields:
                self.skip = True
            elif original:
                if original_deleted:
                    self.skip = True
                policy = update_policy(None)
                if policy == THIS:
                    self.skip = True
                elif policy == NEWER and \
                     (original_mtime and original_mtime > self.mtime):
                    self.skip = True
                elif policy == MASTER and \
                     (original_mci == 0 or self.mci != 1):
                    self.skip = True
            else:
                self.skip = True

            if not self.skip and not self.conflict:

                row = db(table[UID] == data[xml.REPLACEDBY]) \
                                        .select(table._id, limitby=(0, 1)) \
                                        .first()
                if row:
                    original_id = row[table._id]
                    resource = s3db.resource(tablename,
                                             id = [original_id, self.id],
                                             )
                    try:
                        success = resource.merge(original_id, self.id)
                    except:
                        self.error = sys.exc_info()[1]
                        self.skip = True
                        return ignore_errors
                    if success:
                        self.committed = True
                else:
                    self.skip = True

            return True

        else:
            raise RuntimeError("unknown import method: %s" % method)

        # Audit + onaccept on successful commits
        if self.committed:

            # Create a pseudo-form for callbacks
            form = Storage()
            form.method = method
            form.table = table
            form.vars = self.data
            prefix, name = tablename.split("_", 1)
            if self.id:
                form.vars.id = self.id

            # Audit
            current.audit(method, prefix, name,
                          form = form,
                          record = self.id,
                          representation = "xml",
                          )

            # Prevent that record post-processing breaks time-delayed
            # synchronization by implicitly updating "modified_on"
            if MTIME in table.fields:
                modified_on = table[MTIME]
                modified_on_update = modified_on.update
                modified_on.update = None
            else:
                modified_on_update = None

            # Update super entity links
            s3db.update_super(table, form.vars)
            if method == CREATE:
                # Set record owner
                current.auth.s3_set_record_owner(table, self.id)
            elif method == UPDATE:
                # Update realm
                update_realm = enforce_realm_update or \
                               s3db.get_config(table, "update_realm")
                if update_realm:
                    current.auth.set_realm_entity(table, self.id,
                                                  force_update = True,
                                                  )
            # Onaccept
            key = "%s_onaccept" % method
            onaccept = current.deployment_settings.get_import_callback(tablename, key)
            if onaccept:
                callback(onaccept, form, tablename=tablename)

            # Restore modified_on.update
            if modified_on_update is not None:
                modified_on.update = modified_on_update

        # Update referencing items
        if self.update and self.id:
            for u in self.update:

                # The other import item that shall be updated
                item = u.get("item")
                if not item:
                    continue

                # The field in the other item that shall be updated
                field = u.get("field")
                if isinstance(field, (list, tuple)):
                    # The field references something else than the
                    # primary key of this table => look it up
                    pkey, fkey = field
                    query = (table.id == self.id)
                    row = db(query).select(table[pkey], limitby=(0, 1)).first()
                    ref_id = row[pkey]
                else:
                    # The field references the primary key of this table
                    pkey, fkey = None, field
                    ref_id = self.id

                if "refkey" in u:
                    # Target field is a JSON object
                    item._update_objref(fkey, u["refkey"], ref_id)
                else:
                    # Target field is a reference or list:reference
                    item._update_reference(fkey, ref_id)

        return True

    # -------------------------------------------------------------------------
    def _dynamic_defaults(self, data):
        """
            Applies dynamic defaults from any keys in data that start with
            an underscore, used only for new records and only if the respective
            field is not populated yet.

            Args:
                data: the data dict
        """

        for k, v in list(data.items()):
            if k[0] == "_":
                fn = k[1:]
                if fn in self.table.fields and fn not in data:
                    data[fn] = v

    # -------------------------------------------------------------------------
    def _mandatory_fields(self):

        job = self.job

        mandatory = None
        tablename = self.tablename

        mfields = job.mandatory_fields
        if tablename in mfields:
            mandatory = mfields[tablename]

        if mandatory is None:
            mandatory = []
            for field in self.table:
                if field.default is not None:
                    continue
                requires = field.requires
                if requires:
                    if not isinstance(requires, (list, tuple)):
                        requires = [requires]
                    if isinstance(requires[0], IS_EMPTY_OR):
                        continue
                    error = field.validate("")[1]
                    if error:
                        mandatory.append(field.name)
            mfields[tablename] = mandatory

        return mandatory

    # -------------------------------------------------------------------------
    def _resolve_references(self):
        """
            Resolve the references of this item (=look up all foreign
            keys from other items of the same job). If a foreign key
            is not yet available, it will be scheduled for later update.
        """

        table = self.table
        if not table:
            return

        db = current.db
        items = self.job.items
        for reference in self.references:

            entry = reference.entry
            if not entry:
                continue

            field = reference.field

            # Resolve key tuples
            if isinstance(field, (list, tuple)):
                pkey, fkey = field
            else:
                pkey, fkey = ("id", field)

            f = table[fkey]
            multiple = False
            if f.type == "json":
                is_json = True
                objref = reference.objref
                if not objref:
                    objref = ObjectReferences(self.data.get(fkey))
                refkey = reference.refkey
                if not refkey:
                    continue
            else:
                is_json = False
                refkey = objref = None
                ktablename, _, multiple = s3_get_foreign_key(f)
                if not ktablename:
                    continue

            # Get the lookup table
            if entry.tablename:
                ktablename = entry.tablename
            try:
                ktable = current.s3db[ktablename]
            except AttributeError:
                continue

            # Resolve the foreign key (value)
            item = None
            fk = entry.id
            if entry.item_id:
                item = items[entry.item_id]
                if item:
                    if item.original and \
                       item.original.get("deleted") and \
                       not item.committed:
                        # Original is deleted and has not been updated
                        fk = None
                    else:
                        fk = item.id
            if fk and pkey != "id":
                row = db(ktable._id == fk).select(ktable[pkey], limitby=(0, 1)).first()
                if not row:
                    fk = None
                    continue
                fk = row[pkey]

            # Update record data
            if fk:
                if is_json:
                    objref.resolve(refkey[0], refkey[1], refkey[2], fk)
                elif multiple:
                    val = self.data.get(fkey, [])
                    if fk not in val:
                        val.append(fk)
                    self.data[fkey] = val
                else:
                    self.data[fkey] = fk
            else:
                if fkey in self.data and not multiple and not is_json:
                    del self.data[fkey]
                if item:
                    update = {"item": self, "field": fkey}
                    if is_json:
                        update["refkey"] = refkey
                    item.update.append(update)

    # -------------------------------------------------------------------------
    def _update_reference(self, field, value):
        """
            Helper method to update a foreign key in an already written
            record. Will be called by the referenced item after (and only
            if) it has been committed. This is only needed if the reference
            could not be resolved before commit due to circular references.

            Args:
                field: the field name of the foreign key
                value: the value of the foreign key
        """

        table = self.table
        record_id = self.id

        if not value or not table or not record_id or not self.permitted:
            return

        db = current.db
        update = None

        fieldtype = str(table[field].type)
        if fieldtype.startswith("list:reference"):
            query = (table._id == record_id)
            record = db(query).select(table[field],
                                      limitby = (0, 1),
                                      ).first()
            if record:
                values = record[field]
                if value not in values:
                    values.append(value)
                    update = {field: values}
        else:
            update = {field: value}

        if update:
            if "modified_on" in table.fields:
                update["modified_on"] = table.modified_on
            if "modified_by" in table.fields:
                update["modified_by"] = table.modified_by
            db(table._id == record_id).update(**update)

    # -------------------------------------------------------------------------
    def _update_objref(self, field, refkey, value):
        """
            Update object references in a JSON field

            Args:
                fieldname: the name of the JSON field
                refkey: the reference key, a tuple (tablename, uidtype, uid)
                value: the foreign key value
        """


        table = self.table
        record_id = self.id

        if not value or not table or not record_id or not self.permitted:
            return

        db = current.db
        query = (table._id == record_id)
        record = db(query).select(table._id,
                                  table[field],
                                  limitby = (0, 1),
                                  ).first()
        if record:
            obj = record[field]

            tn, uidtype, uid = refkey
            ObjectReferences(obj).resolve(tn, uidtype, uid, value)

            update = {field: obj}
            if "modified_on" in table.fields:
                update["modified_on"] = table.modified_on
            if "modified_by" in table.fields:
                update["modified_by"] = table.modified_by
            record.update_record(**update)

    # -------------------------------------------------------------------------
    def store(self, item_table=None):
        """
            Store this item in the DB
        """

        if item_table is None:
            return None

        item_id = self.item_id
        db = current.db
        row = db(item_table.item_id == item_id).select(item_table.id,
                                                       limitby=(0, 1)
                                                       ).first()
        if row:
            record_id = row.id
        else:
            record_id = None

        record = Storage(job_id = self.job.job_id,
                         item_id = item_id,
                         tablename = self.tablename,
                         record_uid = self.uid,
                         skip = self.skip,
                         error = self.error or "",
                         )

        if self.element is not None:
            element_str = current.xml.tostring(self.element,
                                               xml_declaration=False)
            record.update(element=element_str)

        self_data = self.data
        if self_data is not None:
            table = self.table
            fields = table.fields
            data = Storage()
            for f in self_data.keys():
                if f not in fields:
                    continue
                field = table[f]
                field_type = str(field.type)
                if field_type == "id" or s3_has_foreign_key(field):
                    continue
                data_ = self_data[f]
                if isinstance(data_, Field):
                    # Not picklable
                    # This is likely to be a modified_on to avoid updating this field, which skipping does just fine too
                    continue
                data.update({f: data_})
            record["data"] = pickle.dumps(data)

        ritems = []
        for reference in self.references:
            field = reference.field
            entry = reference.entry
            store_entry = None
            if entry:
                if entry.item_id is not None:
                    store_entry = {"field": field,
                                   "item_id": str(entry.item_id),
                                   }
                elif entry.uid is not None:
                    store_entry = {"field": field,
                                   "tablename": entry.tablename,
                                   "uid": str(entry.uid),
                                   }
                if store_entry is not None:
                    ritems.append(json.dumps(store_entry))
        if ritems:
            record.update(ritems=ritems)
        citems = [c.item_id for c in self.components]
        if citems:
            record.update(citems=citems)
        if self.parent:
            record.update(parent=self.parent.item_id)
        if record_id:
            db(item_table.id == record_id).update(**record)
        else:
            record_id = item_table.insert(**record)

        return record_id

    # -------------------------------------------------------------------------
    def restore(self, row):
        """
            Restore an item from a item table row. This does not restore
            the references (since this can not be done before all items
            are restored), must call job.restore_references() to do that

            Args:
                row: the item table row
        """

        xml = current.xml

        self.item_id = row.item_id
        self.accepted = None
        self.permitted = False
        self.committed = False
        tablename = row.tablename
        self.id = None
        self.uid = row.record_uid
        self.skip = row.skip
        if row.data is not None:
            self.data = pickle.loads(row.data)
        else:
            self.data = Storage()
        data = self.data
        if xml.MTIME in data:
            self.mtime = data[xml.MTIME]
        if xml.MCI in data:
            self.mci = data[xml.MCI]
        UID = xml.UID
        if UID in data:
            self.uid = data[UID]
        self.element = etree.fromstring(row.element)
        if row.citems:
            self.load_components = row.citems
        if row.ritems:
            self.load_references = [json.loads(ritem) for ritem in row.ritems]
        self.load_parent = row.parent
        s3db = current.s3db
        try:
            table = s3db[tablename]
        except AttributeError:
            self.error = current.ERROR.BAD_RESOURCE
            return False
        else:
            self.table = table
            self.tablename = tablename
        from ..resource import CRUDResource
        original = CRUDResource.original(table,
                                         self.data,
                                         mandatory = self._mandatory_fields(),
                                         )
        if original is not None:
            self.original = original
            self.id = original[table._id.name]
            if not current.response.s3.synchronise_uuids and UID in original:
                self.uid = self.data[UID] = original[UID]
        self.error = row.error
        postprocess = s3db.get_config(self.tablename, "xml_post_parse")
        if postprocess:
            postprocess(self.element, self.data)
        if self.error and not self.data:
            # Validation error
            return False
        return True

# =============================================================================
class SyncPolicy:
    """ Synchronization Policy """

    THIS   = "THIS"   # never update
    OTHER  = "OTHER"  # always update
    NEWER  = "NEWER"  # keep the newer record
    MASTER = "MASTER" # keep the record with the lower MCI

    def __init__(self,
                 onupdate = None,
                 onconflict = None,
                 resolve = None,
                 last_sync = None,
                 ):
        """
            Args:
                onupdate: update policy (str)
                onconflict: conflict policy (str)
                resolve: callback to resolve conflicts, receives
                         the import item as parameter
                last_sync: datetime of the last sync run with the remote
                           repository
        """

        self.update_policy = onupdate
        self.conflict_policy = onconflict
        self.conflict_resolver = resolve
        self.last_sync = last_sync

# =============================================================================
class ObjectReferences:
    """
        Utility to discover and resolve references in a JSON object;
        handles both uuid- and tuid-based references

        - traverses the object to find dict items of any of these formats:
                "$k_<name>": {"r": <tablename>, "u": <uuid>}
                "$k_<name>": {"@resource": <tablename>, "@uuid": <uuid>}
                "$k_<name>": {"r": <tablename>, "t": <tuid>}
                "$k_<name>": {"@resource": <tablename>, "@tuid": <tuid>}

        - resolve() replaces them with:
                "<name>": <db_id>

        Examples:
            # Get a list of all references in obj
            refs = ObjectReferences(obj).refs

            # Resolve a reference in obj
            ObjectReferences(obj).resolve("req_req", "uuid", "REQ1", 57)
    """

    TABLENAME_KEYS = ("@resource", "r")
    UUID_KEYS = ("@uuid", "u")
    TUID_KEYS = ("@tuid", "t")

    def __init__(self, obj):
        """
            Args:
                obj: the object to inspect (parsed)
        """

        self.obj = obj

        self._refs = None
        self._objs = None

    # -------------------------------------------------------------------------
    @property
    def refs(self):
        """
            List of references discovered in the object (lazy property)

            Returns:
                a list of tuples (tablename, uidtype, uid)
        """

        if self._refs is None:
            self._refs = []
            self._objs = {}
            self._traverse(self.obj)
        return self._refs

    # -------------------------------------------------------------------------
    @property
    def objs(self):
        """
            A dict with pointers to the references inside the object

            Returns:
                a dict {(tablename, uidtype, uid): (obj, key)}
        """

        if self._objs is None:
            self._refs = []
            self._objs = {}
            self._traverse(self.obj)
        return self._objs

    # -------------------------------------------------------------------------
    def _traverse(self, obj):
        """
            Traverse a (possibly nested) object and find all references,
            populates self.refs and self.objs

            Args:
                obj: the object to inspect
        """

        refs = self._refs
        objs = self._objs

        if isinstance(obj, list):
            for item in obj:
                self._traverse(item)

        elif isinstance(obj, dict):

            for key, value in obj.items():

                if key[:3] == "$k_" and isinstance(value, dict):

                    tablename = uid = uid_type = None

                    for k in self.TABLENAME_KEYS:
                        tablename = value.get(k)
                        if tablename:
                            break
                    if tablename:
                        for k in self.UUID_KEYS:
                            uid = value.get(k)
                            if uid:
                                uid_type = "uuid"
                                break
                    if tablename and not uid:
                        for k in self.TUID_KEYS:
                            uid = value.get(k)
                            if uid:
                                uid_type = "tuid"
                                break
                    if not tablename or not uid:
                        self._traverse(value)
                    else:
                        ref = (tablename, uid_type, uid)
                        if ref not in objs:
                            refs.append(ref)
                            objs[ref] = [(obj, key)]
                        else:
                            objs[ref].append((obj, key))
                else:
                    self._traverse(value)

    # -------------------------------------------------------------------------
    def resolve(self, tablename, uidtype, uid, value):
        """
            Resolve a reference in self.obj with the given value; will
            resolve all occurences of the reference

            Args:
                tablename: the referenced table
                uidtype: the type of uid (uuid or tuid)
                uid: the uuid or tuid
                value: the value to resolve the reference
        """

        items = self.objs.get((tablename, uidtype, uid))
        if items:
            for obj, key in items:
                if len(key) > 3:
                    obj[key[3:]] = value
                obj.pop(key, None)

# =============================================================================
class S3Duplicate:
    """ Standard deduplicator method """

    def __init__(self,
                 primary = None,
                 secondary = None, *,
                 ignore_case = True,
                 ignore_deleted = False,
                 noupdate = False,
                 nomatch_require = None,
                 ):
        """
            Args:
                primary: list or tuple of primary fields to find a
                         match, must always match (mandatory, defaults
                         to "name" field)
                secondary: list or tuple of secondary fields to
                           find a match, must match if values are
                           present in the import item
                ignore_case: ignore case for string/text fields
                ignore_deleted: do not match deleted records
                noupdate: match, but do not update
                nomatch_require: fields required for creation of new records,
                                 i.e. items without these fields must match
                                 an existing record, otherwise they will be
                                 skipped
        """

        if not primary:
            primary = ("name",)
        self.primary = set(primary)

        if not secondary:
            self.secondary = set()
        else:
            self.secondary = set(secondary)

        self.ignore_case = ignore_case
        self.ignore_deleted = ignore_deleted
        self.noupdate = noupdate

        self.nomatch_require = nomatch_require

    # -------------------------------------------------------------------------
    def __call__(self, item):
        """
            Entry point for importer

            Args:
                item: the import item

            Returns:
                the duplicate Row if match found, otherwise None

            Raises:
                SyntaxError: if any of the query fields doesn't exist in
                             the item table
        """

        data = item.data
        table = item.table

        query = None
        error = "Invalid field for duplicate detection: %s (%s)"

        # Primary query (mandatory)
        primary = self.primary
        for fname in primary:

            if fname not in table.fields:
                raise SyntaxError(error % (fname, table))

            field = table[fname]
            value = data.get(fname)

            q = self.match(field, value)
            query = q if query is None else query & q

        # Secondary queries (optional)
        secondary = self.secondary
        for fname in secondary:

            if fname not in table.fields:
                raise SyntaxError(error % (fname, table))

            field = table[fname]
            value = data.get(fname)
            if value:
                query &= self.match(field, value)

        # Ignore deleted records?
        if self.ignore_deleted and "deleted" in table.fields:
            query &= (table.deleted == False)

        # Find a match
        duplicate = current.db(query).select(table._id,
                                             limitby = (0, 1)
                                             ).first()

        if duplicate:
            # Match found: Update import item
            item.id = duplicate[table._id]
            if not data.deleted:
                item.method = item.METHOD.UPDATE
            if self.noupdate:
                item.skip = True

        elif self.nomatch_require:
            # No match found, sufficient data to create new record?
            if any(k not in data for k in self.nomatch_require):
                error = "Invalid reference"
                item.accepted = False
                item.error = error
                if item.element is not None:
                    item.element.set(current.xml.ATTRIBUTE["error"], error)

        # For uses outside of imports:
        return duplicate

    # -------------------------------------------------------------------------
    def match(self, field, value):
        """
            Helper function to generate a match-query

            Args:
                field: the Field
                value: the value

            Returns:
                a Query
        """

        ftype = str(field.type)
        ignore_case = self.ignore_case

        if ignore_case and \
           hasattr(value, "lower") and ftype in ("string", "text"):
            # NB Must convert to unicode before lower() in order to correctly
            #    convert certain unicode-characters (e.g. İ=>i, or Ẽ=>ẽ)
            # => PostgreSQL LOWER() on Windows may not convert correctly, (same for SQLite)
            #    which seems to be a locale issue:
            #    http://stackoverflow.com/questions/18507589/the-lower-function-on-international-characters-in-postgresql
            # => works fine on Debian servers if the locale is a .UTF-8 before
            #    the Postgres cluster is created
            query = (field.lower() == s3_str(value).lower())
        else:
            query = (field == value)

        return query

# END =========================================================================
