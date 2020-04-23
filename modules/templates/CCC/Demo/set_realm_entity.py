# Set the Realm Entity of prepop Persons
current.log.debug("Setting Realm Entity...")
ptable = s3db.pr_person
persons = db(ptable.deleted == False).select(ptable.id,
                                             ptable.pe_id)
auth.set_realm_entity("pr_person", persons, force_update=True)