module = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)


def suggestion_rheader(r, tabs=[]):
    if r.representation != "html":
        # RHeader is a UI facility & so skip for other formats
        return None
    if r.record is None:
        # List or Create form: rheader makes no sense here
        return None

    tabs = [(T("Basic Details"), None),
            (T("Comments"), "comments")]
    rheader_tabs = s3_rheader_tabs(r, tabs)

    suggestion = r.record

    rheader = DIV(TABLE(
        TR(
            TH("%s: " % T("Suggested By")),
            s3db.pr_person_represent(suggestion.created_by),
            TH("%s: " % T("Priority")),
            suggestion.priority,
            ),
        TR(
            TH("%s: " % T("Suggested On")),
            suggestion.created_on,
            )
        ), rheader_tabs)

    return rheader


def suggestions():
    return s3_rest_controller(rheader=suggestion_rheader)

def index():
	return {}