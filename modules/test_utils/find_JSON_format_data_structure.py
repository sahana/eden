
import re
from json.decoder import JSONDecoder

__all__ = (
    "not_found",
    "cannot_parse_JSON",
    "find_JSON_format_data_structure"
)

def not_found(name, string):
    raise Exception(
        u"Cannot find %s in %s" % (name, string)
    )
    
def cannot_parse_JSON(string):
    raise Exception(
        u"Cannot parse JSON: '%s'" % string
    )

def find_JSON_format_data_structure(
    string,
    name,
    found,
    not_found,
    cannot_parse_JSON
):
    """Finds a named JSON-format data structure in the string.
    
    The name can be any string.
    The pattern "name = " will be looked for in the string,
        and the data structure following it parsed and returned as a python 
        data structure. 
    """
    try:
        name_start = string.index(name)
    except ValueError:
        not_found(name, string)
    else:
        name_length = len(name)
        name_end = name_start + name_length
        
        _, remaining = re.Scanner([
            (r"\s*=\s*", lambda scanner, token: None)
        ]).scan(
            string[name_end:]
        )
        
        try:
            data, end_position = JSONDecoder().raw_decode(remaining)
        except ValueError, value_error:
            cannot_parse_JSON(remaining)
        else:
            found(data)
