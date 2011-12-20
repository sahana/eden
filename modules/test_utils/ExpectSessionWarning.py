
class ExpectSessionWarning(object):
    def __init__(self, session, warning):
        self.warning = warning
        self.session = session

    def __enter__(self):
        session = self.session
        warnings = []
        self.warnings = session.warning = warnings

    def __exit__(self, type, value, traceback):
        if type is None:
            assert self.warning in self.warnings
