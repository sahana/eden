
test_utils = local_import("test_utils")

find_JSON_format_data_structure = test_utils.find_JSON_format_data_structure

import unittest

def fail(message):
    def thrower(*args, **kwargs):
        raise Exception(message % dict(args= args, kwargs = kwargs))
    return thrower

def ok(*args, **kwargs):
    pass

class Test_find_JSON_format_data_structure(unittest.TestCase):
    def test_bad_javascript(test):
        test_utils.find_JSON_format_data_structure(
            string = "x = ksdkjnsdf;ajndflkj",
            name = "x",
            found = fail("shouldn't be found"),
            not_found = fail("should bork"),
            cannot_parse_JSON = ok
        )
        
    def test_missing_data_structure(test):
        test_utils.find_JSON_format_data_structure(
            string = "ksdkjnsdf;ajndflkj",
            name = "x",
            found = fail("shouldn't be found"),
            not_found = ok,
            cannot_parse_JSON = fail("shoudn't bork")
        )

    def test_found_data_structure(test):
        test_utils.find_JSON_format_data_structure(
            string = "ksdkjnsdf;ajndflkj; x = {\"a\": 1}\n ksjndfkjsd",
            name = "x",
            found = ok,
            not_found = fail("should be found"),
            cannot_parse_JSON = fail("shoudn't bork")
        )

    def test_complex_name_data_structure(test):
        test_utils.find_JSON_format_data_structure(
            string = "ksdkjnsdf;ajndflkj; x.y.z = {\"a\": 1}\n sdkfjnk",
            name = "x.y.z",
            found = ok,
            not_found = fail("should be found"),
            cannot_parse_JSON = fail("shoudn't bork")
        )

