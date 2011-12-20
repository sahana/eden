

def assert_same_type(expected, actual):
    assert isinstance(actual, type(expected)), "%s vs. %s" % (type(expected), type(actual))

def assert_equal_sequence(expected, actual):
    assert len(expected) == len(actual), "length should be %i, not %i:\n%s" % (
        len(expected), len(actual), actual
    )
    for i in range(len(expected)):
        try:
            assert_equal(expected[i], actual[i])
        except AssertionError, assertion_error:
            raise AssertionError(
                str(assertion_error)
            )

def assert_equal_set(expected, actual):
    missing = expected.difference(actual)
    assert not missing, "Missing: %s" % ", ".join(missing)

    extra = actual.difference(expected)
    assert not extra, "Extra: %s" % ", ".join(extra)    

def assert_equal_dict(expected, actual):
    assert_equal_set(
        expected = set(expected.keys()),
        actual = set(actual.keys())
    )    
    for key in expected.iterkeys():
        try:
            assert_equal(expected[key], actual[key])
        except AssertionError, assertion_error:
            raise AssertionError(
                "[%s] %s" % (
                    key,
                    str(assertion_error),
                )
            )

def assert_equal_value(expected, actual):
    assert expected == actual, "%s != %s" % (expected, actual)

_compare_procs = {
    list: assert_equal_sequence,
    int: assert_equal_value,
    float: assert_equal_value,
    str: assert_equal_value,
    unicode: assert_equal_value, #sequence,
    dict: assert_equal_dict,
    set: assert_equal_set,
}

def assert_equal(expected, actual):
    assert_same_type(expected, actual)
    compare_proc = _compare_procs.get(type(expected), assert_equal_value)
    compare_proc(
        expected,
        actual
    )
