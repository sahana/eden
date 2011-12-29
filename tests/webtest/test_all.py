def test_all(db):
    """
        Unit Test all modules within Sahana using CherryPy's WebTest
        NB This doesn't yet work
    """
    # Shelter Registry
    from applications.sahana.modules.test_cr import *
    test_cr(db)
    # Organisation Registry
    from applications.sahana.modules.test_or import *
    test_or(db)
    # Person Registry
    from applications.sahana.modules.test_pr import *
    test_pr(db)

if __name__ == "__main__":
    test_all(db)
