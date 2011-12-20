

def compare_lines(test, expected, actual):
    line = 1
    expected_lines = expected.split('\n')
    actual_lines = actual.split('\n')
    for expected_line, actual_line in zip(expected_lines, actual_lines):
        test.assertEquals(
            actual_line,
            expected_line,
            "%s: '%s' != '%s'" % (line, actual_line, expected_line)
        )
        line += 1
    test.assertEquals(len(expected_lines), len(actual_lines))

