# This file is used to specify the mappings for updating the the values of an 
# field according to the mappings given through the methods defined
#
# A select query is done to feed the values mapping function , All the fields 
# that are required to generate the new field values are given through the 
# argument to the mapping function

def fields(db):    
    """
    This function specify the fields that are needed for the select query
    """
    fields = []
    fields.append(db["org_organisation"].ALL)
    return fields

def query(db):    
    """
    This function specify the query for the select query
    """
    query = db.org_organisation.organisation_type_id == db.org_organisation_type.id
    return query

def mapping(row):
    """
    @param row : The row which is generated as a result of the select query done
    
    The new values are returned which are are generarated for each row .
    """
    return row["id"]
