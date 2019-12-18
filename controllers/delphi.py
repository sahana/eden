# coding: utf8

"""
    Delphi Decision Maker - Controllers
"""

module = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# =============================================================================
def index():
    """
        Module Home Page
        - provide the list of currently-Active Problems
    """

    # Simply redirect to the Problems REST controller
    redirect(URL(f="problem"))

    # Alternative dashboard
    module_name = settings.modules[module].name_nice

    table = s3db.delphi_group
    groups = db(table.active == True).select()
    result = []
    for group in groups:
        actions = []
        duser = s3db.delphi_DelphiUser(group)
        if duser.authorised:
            actions.append(("group/%d/update" % group.id, T("Edit")))
            actions.append(("new_problem/create/?group=%s&next=%s" % \
                    (group.id,
                    URL(f="group_summary", args=group.id)),
                    "Add New Problem"))
            actions.append(("group_summary/%s/#request" % group.id, T("Review Requests")))
        else:
            actions.append(("group_summary/%s/#request" % group.id,
                    "Role: %s%s" % (duser.status,
                                    (duser.membership and duser.membership.req) and "*" or "")))

        table = s3db.delphi_problem
        query = (table.group_id == group.id) & \
                (table.active == True)
        latest_problems = db(query).select(orderby =~ table.modified_on)
        result.append((group, latest_problems, actions))

    response.title = module_name
    return {"groups_problems": result,
            "name": T("Active Problems"),
            "module_name": module_name,
            }

# =============================================================================
# Groups
# =============================================================================
def group_rheader(r, tabs = []):
    """ Group rheader """

    if r.representation == "html":
        if r.record is None:
            # List or Create form: rheader makes no sense here
            return None

        tabs = [(T("Basic Details"), None),
                (T("Problems"), "problem"),
                ]

        group = r.record

        # Get this User's permissions for this Group
        duser = s3db.delphi_DelphiUser(group.id)
        if duser.authorised:
            tabs.append((T("Membership"), "membership"))

        rheader_tabs = s3_rheader_tabs(r, tabs)

        rheader = DIV(
                    TABLE(
                        TR(TH("%s: " % T("Group")),
                           group.name,
                           ),
                        TR(TH("%s: " % T("Description")),
                           group.description,
                           ),
                        TR(TH("%s: " % T("Active")),
                           group.active,
                           ),
                        ),
                        rheader_tabs
                    )
        return rheader

# -----------------------------------------------------------------------------
def group():
    """ Problem Group REST Controller """

    if auth.s3_has_role("DelphiAdmin"):
        ADMIN = True
    else:
        ADMIN = False
        s3db.configure("delphi_group",
                       deletable = False,
                       # Remove ability to create new Groups
                       #insertable = False
                       )

    def prep(r):
        if r.interactive:

            if r.component:
                tablename = r.component.tablename
                list_fields = s3db.get_config(tablename,
                                              "list_fields")
                try:
                    list_fields.remove("group_id")
                except:
                    pass
                s3db.configure(tablename,
                               deletable = ADMIN,
                               list_fields = list_fields)
        return True
    s3.prep = prep

    rheader = group_rheader
    return s3_rest_controller(rheader = rheader,
                              # Allow components with components (such as problem) to breakout from tabs
                              native = True,
                              )

# =============================================================================
# Problems
# =============================================================================
def problem_rheader(r, tabs = []):
    """ Problem rheader """

    if r.representation == "html":
        if r.record is None:
            # List or Create form: rheader makes no sense here
            return None

        problem = r.record

        tabs = [# Components & Custom Methods
                (T("Problems"), "problems"),
                (T("Solutions"), "solution"),
                (T("Discuss"), "discuss"),
                (T("Vote"), "vote"),
                (T("Scale of Results"), "results"),
                ]

        # Get this User's permissions for this Group
        duser = s3db.delphi_DelphiUser(problem.group_id)
        if duser.authorised:
            tabs.append((T("Edit"), None))

        rheader_tabs = s3_rheader_tabs(r, tabs)

        rtable = TABLE(TR(TH("%s: " % T("Problem")),
                          problem.name,
                          TH("%s: " % T("Active")),
                          problem.active,
                          ),
                       TR(TH("%s: " % T("Description")),
                          problem.description,
                          ),
                       TR(TH("%s: " % T("Criteria")),
                          problem.criteria,
                          ),
                       )

        if r.component and \
           r.component_name == "solution" and \
           r.component_id:
            stable = s3db.delphi_solution
            query = (stable.id == r.component_id)
            solution = db(query).select(stable.name,
                                        stable.description,
                                        limitby=(0, 1)).first()
            rtable.append(DIV(TR(TH("%s: " % T("Solution")),
                                 solution.name,
                                 ),
                              TR(TH("%s: " % T("Description")),
                                 solution.description,
                                 ),
                              ))

        rheader = DIV(rtable,
                      rheader_tabs)
        return rheader

# -----------------------------------------------------------------------------
def problem():
    """ Problem REST Controller """

    tablename = "%s_%s" % (module, resourcename)
    table = s3db[tablename]

    # Custom Methods
    set_method = s3db.set_method
    set_method(module, resourcename,
               method="problems",
               action=problems)

    set_method(module, resourcename,
               method="discuss",
               action=discuss)

    # Discussion can also be done at the Solution component level
    set_method(module, resourcename,
               component_name="solution",
               method="discuss",
               action=discuss)

    set_method(module, resourcename,
               method="vote",
               action=vote)

    set_method(module, resourcename,
               method="results",
               action=results)

    # Filter to just Active Problems
    s3.filter = (table.active == True)

    if not auth.s3_has_role("DelphiAdmin"):
        s3db.configure(tablename,
                       deletable = False,
                       # Remove ability to create new Problems
                       #insertable = False
                       )

    def prep(r):
        if r.interactive:
            if r.record:
                duser = s3db.delphi_DelphiUser(r.record.group_id)
                if duser.authorised:
                    s3db.configure(tablename,
                                   deletable = True,
                                   )
            if r.component_name == "solution":
                r.component.table.modified_on.label = T("Last Updated")
                s3db.configure(r.component.tablename,
                               deletable = duser.authorised,
                               )
        return True
    s3.prep = prep

    def postp(r, output):
        if r.interactive:
            if not r.component:
                s3.actions = [
                        dict(label=str(T("Solutions")),
                             _class="action-btn",
                             url=URL(args=["[id]", "solution"])),
                        dict(label=str(T("Vote")),
                             _class="action-btn",
                             url=URL(args=["[id]", "vote"])),
                    ]
            elif r.component_name == "solution":
                s3.actions = [
                        dict(label=str(T("Discuss")),
                             _class="action-btn",
                             url=URL(args=[r.id, "solution", "[id]", "discuss"])),
                    ]
        return output
    s3.postp = postp

    rheader = problem_rheader
    return s3_rest_controller(rheader=rheader)

# -----------------------------------------------------------------------------
def problems(r, **attr):
    """
        Redirect to the list of Problems for the Group
        - used for a Tab
    """

    try:
        group_id = r.record.group_id
    except:
        raise HTTP(400)
    else:
        redirect(URL(f="group", args=[group_id, "problem"]))

# -----------------------------------------------------------------------------
def solution():
    """
        Used for Imports
    """

    return s3_rest_controller()

# =============================================================================
# Voting
# =============================================================================
def vote(r, **attr):
    """
        Custom Method to allow Voting on Solutions to a Problem
    """

    problem = r.record

    # Get this User's permissions for this Group
    duser = s3db.delphi_DelphiUser(problem.group_id)

    # Add the RHeader to maintain consistency with the other pages
    rheader = problem_rheader(r)

    # Lookup Solution Options
    stable = s3db.delphi_solution
    query = (stable.problem_id == problem.id)
    rows = db(query).select(stable.id,
                            stable.name)
    options = Storage()
    for row in rows:
        options[row.id] = row.name

    if duser.user_id:
        vtable = s3db.delphi_vote
        query = (vtable.problem_id == problem.id) & \
                (vtable.created_by == auth.user.id)
        votes = db(query).select(vtable.solution_id,
                                 orderby = vtable.rank)
    else:
        votes = []

    rankings = OrderedDict()
    for v in votes:
        # Add to the list of ranked options
        rankings[v.solution_id] = options[v.solution_id]
        # Remove from the unranked options
        options.pop(v.solution_id)

    # Add Custom CSS from Static (cacheable)
    s3.stylesheets.append("S3/delphi.css")

    # Add Custom Javascript
    # Settings to be picked up by Static code
    js = "".join((
'''var problem_id=''', str(problem.id), '''
i18n.delphi_failed="''', str(T("Failed!")), '''"
i18n.delphi_saving="''', str(T("Saving...")), '''"
i18n.delphi_saved="''', str(T("Saved.")), '''"
i18n.delphi_vote="''', str(T("Save Vote")), '''"'''))
    s3.js_global.append(js)

    # Static code which can be cached
    s3.scripts.append(URL(c="static", f="scripts",
                          args=["S3", "s3.delphi.js"]))

    response.view = "delphi/vote.html"
    return {"rheader": rheader,
            "duser": duser,
            "votes": votes,
            "options": options,
            "rankings": rankings,
            }

# -----------------------------------------------------------------------------
def save_vote():
    """
        Function accessed by AJAX from vote() to save the results of a Vote
    """

    try:
        problem_id = request.args[0]
    except:
        raise HTTP(400)

    ptable = s3db.delphi_problem
    query = (ptable.id == problem_id)
    problem = db(query).select(ptable.group_id,
                               limitby=(0, 1)).first()
    if not problem:
        raise HTTP(404)

    # Get this User's permissions for this Group
    duser = s3db.delphi_DelphiUser(problem.group_id)

    if not duser.can_vote:
        auth.permission.fail()

    # Decode the data
    try:
        rankings = list(request.post_vars.keys())[0].split(",")
    except IndexError:
        status = current.xml.json_message(False, 400, "No Options Ranked")
        raise HTTP(400, body=status)

    # Check the votes are valid
    stable = s3db.delphi_solution
    query = (stable.problem_id == problem_id)
    solutions = db(query).select(stable.id)
    options = []
    for row in solutions:
        options.append(row.id)
    for ranked in rankings:
        if int(ranked) not in options:
            status = current.xml.json_message(False, 400, "Option isn't valid!")
            raise HTTP(400, body=status)

    # Convert to a format suitable for comparisons
    votes = []
    count = 1
    for ranked in rankings:
        votes.append(Storage(solution_id=int(ranked), rank=count))
        count += 1

    # Read the old votes
    vtable = s3db.delphi_vote
    query = (vtable.problem_id == problem_id) & \
            (vtable.created_by == auth.user.id)
    old_votes = db(query).select(vtable.solution_id,
                                 vtable.rank)
    if old_votes:
        # Calculate changes
        ranks = {}
        old_ranks = {}
        used = []
        for solution in solutions:
            s1 = solution.id
            ranks[s1] = 0
            old_ranks[s1] = 0
            for vote in votes:
                if vote.solution_id == s1:
                    ranks[s1] = vote.rank
                    continue
            for vote in old_votes:
                if vote.solution_id == s1:
                    old_ranks[s1] = vote.rank
                    continue
            for sol_2 in solutions:
                changed = False
                s2 = sol_2.id
                if s2 == s1:
                    continue
                if (s2, s1) in used:
                    # We've already evaluated this pair
                    continue
                ranks[s2] = 0
                old_ranks[s2] = 0
                for vote in votes:
                    if vote.solution_id == s2:
                        ranks[s2] = vote.rank
                        continue
                for vote in old_votes:
                    if vote.solution_id == s2:
                        old_ranks[s2] = vote.rank
                        continue
                if (ranks[s1] > ranks[s2]) and \
                   (old_ranks[s1] < old_ranks[s2]):
                    changed = True
                elif (ranks[s1] < ranks[s2]) and \
                     (old_ranks[s1] > old_ranks[s2]):
                    changed = True
                elif (ranks[s1] == ranks[s2]) and \
                     (old_ranks[s1] != old_ranks[s2]):
                    changed = True
                elif (ranks[s1] != ranks[s2]) and \
                     (old_ranks[s1] == old_ranks[s2]):
                    changed = True
                if changed:
                    # This pair has changed places, so update Solution
                    db(stable.id.belongs((s1, s2))).update(changes=stable.changes + 1)
                used.append((s1, s2))

    # Clear the old votes
    db(query).delete()

    # Save the new votes
    count = 1
    for ranked in rankings:
        vtable.insert(problem_id=problem_id, solution_id=ranked, rank=count)
        count += 1

    status = current.xml.json_message(True, 200, "Vote saved")
    return status

# -----------------------------------------------------------------------------
def _getUnitNormalDeviation(zscore):
    """
        Utility function used by Scale of Results

        Looks up the Unit Normal Deviation based on the Z-Score (Proportion/Probability)
        http://en.wikipedia.org/wiki/Standard_normal_table

        @ToDo: Move to S3Statistics module
    """

    UNIT_NORMAL = (
        ( 0.0, .0, .01, .02, .03, .04, .05, .06, .07, .08, .09 ),
        ( .0, .5000, .5040, .5080, .5120, .5160, .5199, .5239, .5279, .5319, .5359 ),
        ( .1, .5398, .5438, .5478, .5517, .5557, .5596, .5636, .5675, .5714, .5753 ),
        ( .2, .5793, .5832, .5871, .5910, .5948, .5987, .6026, .6064, .6103, .6141 ),
        ( .3, .6179, .6217, .6255, .6293, .6331, .6368, .6406, .6443, .6480, .6517 ),
        ( .4, .6554, .6591, .6628, .6664, .6700, .6736, .6772, .6808, .6844, .6879 ),

        ( .5, .6915, .6950, .6985, .7019, .7054, .7088, .7123, .7157, .7190, .7224 ),
        ( .6, .7257, .7291, .7324, .7357, .7389, .7422, .7454, .7486, .7517, .7549 ),
        ( .7, .7580, .7611, .7642, .7673, .7703, .7734, .7764, .7794, .7823, .7852 ),
        ( .8, .7881, .7910, .7939, .7967, .7995, .8023, .8051, .8078, .8106, .8133 ),
        ( .9, .8159, .8186, .8212, .8238, .8264, .8289, .8315, .8340, .8365, .8389 ),

        ( 1.0, .8415, .8438, .8461, .8485, .8508, .8531, .8554, .8577, .8509, .8621 ),
        ( 1.1, .8643, .8665, .8686, .8708, .8729, .8749, .8770, .8790, .8810, .8830 ),
        ( 1.2, .8849, .8869, .8888, .8907, .8925, .8944, .8962, .8980, .8997, .90147 ),
        ( 1.3, .90320, .90490, .90658, .90824, .90988, .91149, .91309, .91466, .91621, .91774 ),
        ( 1.4, .91924, .92073, .92220, .92364, .92507, .92647, .92785, .92922, .93056, .93189 ),

        ( 1.5, .93319, .93448, .93574, .93699, .93822, .93943, .94062, .94179, .94295, .94408 ),
        ( 1.6, .94520, .94630, .94738, .94845, .94950, .95053, .95154, .95254, .95352, .95449 ),
        ( 1.7, .95543, .95637, .95728, .95818, .95907, .95994, .96080, .96164, .96246, .96327 ),
        ( 1.8, .96407, .96485, .96562, .96638, .96712, .96784, .97856, .96926, .96995, .97062 ),
        ( 1.9, .97128, .97193, .97257, .97320, .97381, .97441, .97500, .97558, .97615, .97670 ),

        ( 2.0, .97725, .97778, .97831, .97882, .97932, .97982, .98030, .98077, .98124, .98169 ),
        ( 2.1, .98214, .98257, .98300, .98341, .98382, .98422, .98461, .98500, .98537, .98574 ),
        ( 2.2, .98610, .98645, .98679, .98713, .98745, .98778, .98809, .98840, .98870, .98899 ),
        ( 2.3, .98928, .98956, .98983, .990097, .990358, .990613, .990863, .991106, .991344, .991576 ),
        ( 2.4, .991802, .992024, .992240, .992451, .992656, .992857, .993053, .993244, .993431, .993613 ),

        ( 2.5, .993790, .993963, .994132, .994297, .994457, .994614, .994766, .994915, .995060, .995201 ),
        ( 2.6, .995339, .995473, .995604, .995731, .995855, .995975, .996093, .996207, .996319, .996427 ),
        ( 2.7, .996533, .996636, .996736, .996833, .996928, .997020, .997110, .997197, .997282, .997365 ),
        ( 2.8, .997445, .997523, .997599, .997673, .997744, .997814, .997882, .997948, .998012, .998074 ),
        ( 2.9, .998134, .998193, .998250, .998305, .998359, .998411, .998460, .998511, .998559, .998605 ),

        ( 3.0, .998650, .998694, .998736, .998777, .998817, .998856, .998893, .998930, .998965, .998999 ),
        ( 3.1, .9990324, .9990646, .9990957, .9991260, .9991553, .9991836, .9992112, .9992378, .9992636, .9992886 ),
        ( 3.2, .9993129, .9993363, .9993590, .9993810, .9994024, .9994230, .9994429, .9994623, .9994810, .9994991 ),
        ( 3.3, .9995166, .9995335, .9995499, .9995658, .9995811, .9995959, .9996103, .9996242, .9996376, .9996505 ),
        ( 3.4, .9996631, .9996752, .9996869, .9996982, .9997091, .9997197, .9997299, .9997398, .9997493, .9997585 ),

        ( 3.5, .9997674, .9997759, .9997842, .9997922, .9997999, .9998074, .9998146, .9998215, .9998282, .9998347 ),
        ( 3.6, .9998409, .9998469, .9998527, .9998583, .9998637, .9998689, .9998739, .9998787, .9998834, .9998879 ),
        ( 3.7, .9998922, .9998964, .99990039, .99990426, .99990799, .99991158, .99991504, .99991838, .99992159, .99992468 ),
        ( 3.8, .99992765, .99993052, .99993327, .99993593, .99993848, .99994094, .99994331, .99994558, .99994777, .99994988 ),
        ( 3.9, .99995190, .99995385, .99995573, .99995753, .99995926, .99996092, .99996253, .99996406, .99996554, .99996696 ),

        ( 4.0, .99996833, .99996964, .99997090, .99997211, .99997327, .99997439, .99997546, .99997649, .99997748, .99997843 ),
        ( 4.1, .99997934, .99998022, .99998106, .99998186, .99998263, .99998338, .99998409, .99998477, .99998542, .99998605 ),
        ( 4.2, .99998665, .99998723, .99998778, .99998832, .99998882, .99998931, .99998978, .999990226, .999990655, .999991066 ),
        ( 4.3, .999991460, .999991837, .999992199, .999992545, .999992876, .999993193, .999993497, .999993788, .999994066, .999994332 ),
        ( 4.4, .999994587, .999994831, .999995065, .999995288, .999995502, .999995706, .999995902, .999996089, .999996268, .999996439 ),

        ( 4.5, .999996602, .999996759, .999996908, .999997051, .999997187, .999997318, .999997442, .999997561, .999997675, .999997784 ),
        ( 4.6, .999997888, .999997987, .999998081, .999998172, .999998258, .999998340, .999998419, .999998494, .999998566, .999998634 ),
        ( 4.7, .999998699, .999998761, .999998821, .999998877, .999998931, .999998983, .9999990320, .9999990789, .9999991235, .9999991661 ),
        ( 4.8, .9999992067, .9999992453, .9999992822, .9999993173, .9999993508, .9999993827, .9999994131, .9999994420, .9999994696, .9999994958 ),
        ( 4.9, .9999995208, .9999995446, .9999995673, .9999995889, .9999996094, .9999996289, .9999996475, .9999996652, .9999996821, .9999996981 )
    )

    # Assume indifference
    unitDeviation = 0.0

    for j in range(1, 50):
        if zscore == UNIT_NORMAL[j][1]:
            unitDeviation = UNIT_NORMAL[j][0]
        elif (UNIT_NORMAL[j][1] < zscore) and (zscore < UNIT_NORMAL[j + 1][1]):
            for i in range(2, 10):
                if (UNIT_NORMAL[j][i - 1] < zscore) and (zscore <= UNIT_NORMAL[j][i]):
                    unitDeviation = UNIT_NORMAL[j][0] + UNIT_NORMAL[0][i]
            if zscore > UNIT_NORMAL[j][10]:
                unitDeviation = UNIT_NORMAL[j + 1][0]

    if zscore > UNIT_NORMAL[50][10]:
        # maximum value
        unitDeviation = 5.0

    return unitDeviation

# -----------------------------------------------------------------------------
def online_variance(data):
    """
        A numerically stable algorithm for calculating variance
        http://en.wikipedia.org/wiki/Algorithms_for_calculating_variance#On-line_algorithm
    """

    n = 0
    mean = 0
    M2 = 0

    for x in data:
        n = n + 1
        delta = x - mean
        mean = mean + delta/n
        M2 = M2 + delta*(x - mean)

    variance_n = M2/n
    variance = M2/(n - 1)
    return (variance, variance_n)

# -----------------------------------------------------------------------------
def results(r, **attr):
    """
        Custom Method to show the Scale of Results
    """

    def NBSP():
        return XML("&nbsp;")

    # Add the RHeader to maintain consistency with the other pages
    rheader = problem_rheader(r)

    response.view = "delphi/results.html"

    empty = dict(rheader=rheader,
                 num_voted=0,
                 chart="",
                 table_color="",
                 grids="",
                 summary=""
                 )

    problem = r.record

    # Lookup Votes
    if problem:
        vtable = s3db.delphi_vote
        query = (vtable.problem_id == problem.id)
        votes = db(query).select(vtable.solution_id,
                                 vtable.rank,
                                 vtable.created_by)
    else:
        votes = None
    if not votes:
        return empty

    # Lookup Solutions
    stable = s3db.delphi_solution
    query = (stable.problem_id == problem.id)
    solutions = db(query).select(stable.id,
                                 stable.name,
                                 stable.problem_id, # Needed for Votes virtual field
                                 stable.changes)

    if not solutions:
        return empty

    # Initialise arrays of pairwise comparisons
    arrayF = {}
    arrayP = {}
    arrayX = {}
    arrayP2 = {}
    arrayU = {}
    for solution in solutions:
        s1 = solution.id
        for sol_2 in solutions:
            s2 = sol_2.id
            if s1 == s2:
                arrayF[(s1, s2)] = None
                arrayP[(s1, s2)] = None
                arrayX[(s1, s2)] = None
                arrayP2[(s1, s2)] = None
                arrayU[(s1, s2)] = None
                continue
            arrayF[(s1, s2)] = 0
            # Allow new solutions to start at an indifferent probability
            arrayP[(s1, s2)] = 0.5
            arrayX[(s1, s2)] = 0
            arrayP2[(s1, s2)] = 0.5
            arrayU[(s1, s2)] = 0.5

    # List of Voters
    voters = []
    for vote in votes:
        voter = vote.created_by
        if voter not in voters:
            voters.append(voter)
    num_voted = len(voters)

    # Update array of pairwise comparisons based on votes
    # Create array F which is the number of time a solution has been preferred compared to it'a partner
    for voter in voters:
        ranks = {}
        for vote in votes:
            if vote.created_by != voter:
                continue
            ranks[vote.rank] = vote.solution_id
        for rank_1 in range(1, len(ranks)):
            for rank_2 in range(rank_1 + 1, len(ranks) + 1):
                arrayF[(ranks[rank_1], ranks[rank_2])] += 1

    grids = DIV()
    header = TR(TD())
    rows = TBODY()
    for solution in solutions:
        header.append(TH(solution.name))
        s1 = solution.id
        row = TR(TH(solution.name))
        for sol_2 in solutions:
            s2 = sol_2.id
            # Preferred should be the columns
            value = arrayF[(s2, s1)]
            if value is None:
                row.append(TD("-"))
            else:
                row.append(TD(value))
        rows.append(row)
    output = TABLE(THEAD(header), rows,
                   _class="delphi_wide")
    output = DIV(H4(T("Array F: # times that solution in column is preferred over it's partner in row")),
                 output)
    grids.append(output)
    grids.append(NBSP())

    # Use the pairwise comparisons to build a Dynamic Thurstone scale of results
    # http://en.wikipedia.org/wiki/Thurstone_scale
    # http://www.brocku.ca/MeadProject/Thurstone/Thurstone_1927a.html
    # http://www.brocku.ca/MeadProject/Thurstone/Thurstone_1927f.html
    # @ToDo: For incomplete data, the calculation is more complex: Gulliksen
    # Convert array F to array P by converting totals to proportions
    # Convert array P to array X, which is the unit normal deviate
    for solution in solutions:
        s1 = solution.id
        for sol_2 in solutions:
            s2 = sol_2.id
            if s1 == s2:
                continue
            total = float(arrayF[(s1, s2)] + arrayF[(s2, s1)])
            # Preferred should be the columns
            if total:
                proportion = arrayF[(s2, s1)] / total
            else:
                # No votes yet, so assume indifference
                proportion = 0.5
            arrayP[(s2, s1)] = proportion
            # Cannot do unit normal deviation for 0/1 so approximate in order to not have to do the incomplete data maths
            if proportion == 0.0:
                arrayX[(s2, s1)] = _getUnitNormalDeviation(0.01)
            elif proportion == 1.0:
                arrayX[(s2, s1)] = _getUnitNormalDeviation(0.99)
            else:
                arrayX[(s2, s1)] = _getUnitNormalDeviation(proportion)
            # Now calculate the uncertainty scale
            # i.e. assume that every user who didn't vote on a particular pair drags that back towards indifference
            novotes = num_voted - total
            if proportion == 0.5:
                pass
            elif proportion > 0.5:
                # Assume the novotes vote against
                proportion = (arrayF[s2, s1] - novotes) / num_voted
            else:
                # Assume the novotes vote for
                proportion = (arrayF[s2, s1] + novotes) / num_voted
            arrayP2[(s2, s1)] = proportion
            # Cannot do unit normal deviation for 0/1 so approximate in order to not have to do the incomplete data maths
            if proportion == 0.0:
                arrayU[(s2, s1)] = _getUnitNormalDeviation(0.01)
            elif proportion == 1.0:
                arrayU[(s2, s1)] = _getUnitNormalDeviation(0.99)
            else:
                arrayU[(s2, s1)] = _getUnitNormalDeviation(proportion)

    header = TR(TD())
    rows = TBODY()
    for solution in solutions:
        header.append(TH(solution.name))
        s1 = solution.id
        row = TR(TH(solution.name))
        for sol_2 in solutions:
            s2 = sol_2.id
            # Preferred should be the columns
            value = arrayP[(s2, s1)]
            if value is None:
                row.append(TD("-"))
            else:
                row.append(TD(value))

        rows.append(row)
    output = TABLE(THEAD(header), rows,
                   _class="delphi_wide")
    output = DIV(H4(T("Array P: proportion of times that solution in column is preferred over it's partner in row, assuming that pairs not ranked start at the level of indifference (0.5)")),
                 output)
    grids.append(output)
    grids.append(NBSP())

    header = TR(TD())
    rows = TBODY()
    footer = TR(TH("Total"))
    footer2 = TR(TH("Scale"))
    totals = {}
    counts = {}
    for solution in solutions:
        s1 = solution.id
        totals[s1] = 0
        counts[s1] = 0
    for solution in solutions:
        header.append(TH(solution.name))
        s1 = solution.id
        row = TR(TH(solution.name))
        for sol_2 in solutions:
            s2 = sol_2.id
            # Preferred should be the columns
            value = arrayX[(s2, s1)]
            if value is None:
                row.append(TD("-"))
            else:
                row.append(TD(value))
            if value is not None:
                totals[s2] += value
                counts[s2] += 1
        rows.append(row)

    # Least-squares estimate of the scale values
    # Average of the columns
    for solution in solutions:
        s1 = solution.id
        footer.append(TH(totals[s1]))
        if counts[s1]:
            solution.scale = totals[s1]/counts[s1]
            footer2.append(TH(solution.scale))
        else:
            solution.scale = 0
            footer2.append(TH())

    output = TABLE(THEAD(header), rows, footer, footer2,
                   _class="delphi_wide")
    output = DIV(H4(T("Array X: unit normal deviate")),
                 output)
    grids.append(output)
    grids.append(NBSP())

    header = TR(TD())
    rows = TBODY()
    for solution in solutions:
        header.append(TH(solution.name))
        s1 = solution.id
        row = TR(TH(solution.name))
        for sol_2 in solutions:
            s2 = sol_2.id
            # Preferred should be the columns
            value = arrayP2[(s2, s1)]
            if value is None:
                row.append(TD("-"))
            else:
                row.append(TD(value))

        rows.append(row)
    output = TABLE(THEAD(header), rows,
                   _class="delphi_wide")
    output = DIV(H4(T("Array P2: proportion of times that solution in column is preferred over it's partner in row, assuming that non-votes move towards indifference")),
                 output)
    grids.append(output)
    grids.append(NBSP())

    header = TR(TD())
    rows = TBODY()
    footer = TR(TH("Total"))
    footer2 = TR(TH("Scale"))
    totals = {}
    counts = {}
    for solution in solutions:
        s1 = solution.id
        totals[s1] = 0
        counts[s1] = 0
    for solution in solutions:
        header.append(TH(solution.name))
        s1 = solution.id
        row = TR(TH(solution.name))
        for sol_2 in solutions:
            s2 = sol_2.id
            # Preferred should be the columns
            value = arrayU[(s2, s1)]
            if value is None:
                row.append(TD("-"))
            else:
                row.append(TD(value))
            if value is not None:
                totals[s2] += value
                counts[s2] += 1
        rows.append(row)

    # Least-squares estimate of the uncertainty values
    # Average of the columns
    for solution in solutions:
        s1 = solution.id
        footer.append(TH(totals[s1]))
        if counts[s1]:
            solution.uncertainty = totals[s1]/counts[s1]
            footer2.append(TH(solution.uncertainty))
        else:
            solution.uncertainty = 0
            footer2.append(TH())

    output = TABLE(THEAD(header), rows, footer, footer2,
                   _class="delphi_wide")
    output = DIV(H4(T("Array U: unit normal deviate of the uncertainty value (assuming that all unvoted items return the probability towards indifference)")),
                 output)
    grids.append(output)

    # Sort the Solutions by Scale
    def scale(solution):
        return float(solution.scale)

    solutions = solutions.sort(scale, reverse=True)

    n = len(solutions)

    # @ToDo: deployment_setting
    image = ""
    if image:
        # Canvas of 900x600
        from s3chart import S3Chart
        chart = S3Chart(9, 6)
        fig = chart.fig
        # Add Axes with padding of 10px for the labels (fractional left, bottom, width, height)
        ax = fig.add_axes([0.35, 0.1, 0.6, 0.8])

        problem = r.record
        ax.set_title(problem.name)

        labels = []
        scales = []
        uncertainties = []
        for solution in solutions:
            labels.append(solution.name)
            scales.append(solution.scale)
            uncertainties.append(solution.uncertainty)
        from numpy import arange
        ind = arange(n)
        width = .35
        ax.set_yticks(ind + width)
        ax.set_yticklabels(labels)
        labels = ax.get_yticklabels()
        for label in labels:
            label.set_size(8)

        ax.set_xlabel("Scale") # rotation="vertical" or rotation = 45
        ax.xaxis.grid(True)

        rects1 = ax.barh(ind, scales, width, linewidth=0) # color="blue"
        rects2 = ax.barh(ind + width, uncertainties, width, linewidth=0, color="red")

        ax.legend( (rects1[0], rects2[0]), ("Scale", "Uncertainty") )

        image = chart.draw()

    # Colour the rows
    # Calculate Breaks
    classes = 5
    q = []
    qappend = q.append
    for i in range(classes - 1):
        qappend(1.0 / classes * (i + 1))
    values = [float(solution.scale) for solution in solutions]
    breaks = s3db.stats_quantile(values, q)
    # Make mutable
    breaks = list(breaks)
    values_min = min(values)
    values_max = max(values)
    breaks.insert(0, values_min)
    breaks.append(values_max)
    # Apply colours
    # 5-class BuGn from ColorBrewer.org
    colours = ["edf8fb",
               "b2e2e2",
               "66c2a4",
               "2ca25f",
               "006d2c",
               ]
    for solution in solutions:
        for i in range(classes):
            value = solution.scale
            if value >= breaks[i] and \
               value <= breaks[i + 1]:
                solution.color = colours[i]
                break

    # A table showing overall rankings
    thead = THEAD(
                TR(
                    TH(T("Solution Item"), _rowspan="2"),
                    TH(T("Scale"), _rowspan="2"),
                    TH(T("Uncertainty"), _rowspan="2"),
                    TH(T("Activity Level"), _colspan="3"),
                ),
                TR(
                    TH(T("Voted on")),
                    TH(T("Times Changed")),
                    TH(T("Comments")),
                ),
            )
    tbody = TBODY()
    for solution in solutions:
        rows = True
        tbody.append(
                TR(
                    TD(solution.name),
                    TD(solution.scale,
                       _class="taright"),
                    TD(solution.uncertainty,
                      _class="taright"),
                    TD(solution.votes(),
                       _class="tacenter"),
                    TD(solution.changes,
                       _class="tacenter"),
                    TD(solution.comments(),
                       _class="tacenter"),
                    _style="background:#%s" % solution.color
                    )
            )
    summary = TABLE(thead,
                    tbody,
                    _class="delphi_wide")

    # Add Custom CSS from Static (cacheable)
    s3.stylesheets.append("S3/delphi.css")

    return dict(rheader=rheader,
                num_voted=num_voted,
                chart=image,
                summary=summary,
                grids=grids
                )

# =============================================================================
# Discussions
# =============================================================================
def discuss(r, **attr):
    """ Custom Method to manage the discussion of a Problem or Solution """

    if r.component:
        resourcename = "solution"
        id = r.component_id
    else:
        resourcename = "problem"
        id = r.id

    # Add the RHeader to maintain consistency with the other pages
    rheader = problem_rheader(r)

    ckeditor = URL(c="static", f="ckeditor", args="ckeditor.js")
    s3.scripts.append(ckeditor)
    adapter = URL(c="static", f="ckeditor", args=["adapters",
                                                  "jquery.js"])
    s3.scripts.append(adapter)

    # Toolbar options: http://docs.cksource.com/CKEditor_3.x/Developers_Guide/Toolbar
    js = "".join((
'''i18n.reply="''', str(T("Reply")), '''"
var img_path=S3.Ap.concat('/static/img/jCollapsible/')
var ck_config={toolbar:[['Bold','Italic','-','NumberedList','BulletedList','-','Link','Unlink','-','Smiley','-','Source','Maximize']],toolbarCanCollapse:false,removePlugins:'elementspath'}
function comment_reply(id){
 $('#delphi_comment_solution_id__row').hide()
 $('#delphi_comment_solution_id__row1').hide()
 $('#comment-title').html(i18n.reply)
 var ed = $('#delphi_comment_body').ckeditorGet()
 ed.destroy()
 $('#delphi_comment_body').ckeditor(ck_config)
 $('#comment-form').insertAfter($('#comment-'+id))
 $('#delphi_comment_parent').val(id)
 var solution_id=$('#comment-'+id).attr('solution_id')
 if(undefined!=solution_id){
  $('#delphi_comment_solution_id').val(solution_id)
 }
}'''))

    s3.js_global.append(js)

    response.view = "delphi/discuss.html"
    return dict(rheader=rheader,
                resourcename=resourcename,
                id=id)

# -----------------------------------------------------------------------------
def comment_parse(comment, comments, solution_id=None):
    """
        Parse a Comment

        @param: comment - a gluon.sql.Row: the current comment
        @param: comments - a gluon.sql.Rows: full list of comments
        @param: solution_id - a reference ID: optional solution commented on
    """

    author = B(T("Anonymous"))
    if comment.created_by:
        utable = s3db.auth_user
        ptable = s3db.pr_person
        ltable = s3db.pr_person_user
        query = (utable.id == comment.created_by)
        left = [ltable.on(ltable.user_id == utable.id),
                ptable.on(ptable.pe_id == ltable.pe_id)]
        row = db(query).select(utable.email,
                               ptable.first_name,
                               ptable.middle_name,
                               ptable.last_name,
                               left=left, limitby=(0, 1)).first()
        if row:
            person = row.pr_person
            user = row[utable._tablename]
            username = s3_fullname(person)
            email = user.email.strip().lower()
            import hashlib
            hash = hashlib.md5(email).hexdigest()
            url = "http://www.gravatar.com/%s" % hash
            author = B(A(username, _href=url, _target="top"))
    if not solution_id and comment.solution_id:
        solution = "re: %s" % s3db.delphi_solution_represent(comment.solution_id)
        header = DIV(author, " ", solution)
        solution_id = comment.solution_id
    else:
        header = author
    thread = LI(DIV(s3base.s3_avatar_represent(comment.created_by),
                    DIV(DIV(header,
                            _class="comment-header"),
                        DIV(XML(comment.body)),
                        _class="comment-text"),
                        DIV(DIV(comment.created_on,
                                _class="comment-date"),
                            DIV(A(T("Reply"),
                                  _class="action-btn"),
                                _onclick="comment_reply(%i);" % comment.id,
                                _class="comment-reply"),
                            _class="fright"),
                    _id="comment-%i" % comment.id,
                    _solution_id=solution_id,
                    _class="comment-box"))

    # Add the children of this thread
    children = UL(_class="children")
    id = comment.id
    count = 0
    for comment in comments:
        if comment.parent == id:
            count = 1
            child = comment_parse(comment, comments, solution_id=solution_id)
            children.append(child)
    if count == 1:
        thread.append(children)

    return thread

# -----------------------------------------------------------------------------
def comments():
    """ Function accessed by AJAX from discuss() to handle Comments """

    try:
        resourcename = request.args[0]
    except:
        raise HTTP(400)

    try:
        id = request.args[1]
    except:
        raise HTTP(400)

    if resourcename == "problem":
        problem_id = id
        solution_id = None
    elif resourcename == "solution":
        stable = s3db.delphi_solution
        query = (stable.id == id)
        solution = db(query).select(stable.problem_id,
                                    limitby=(0, 1)).first()
        if solution:
            problem_id = solution.problem_id
            solution_id = id
        else:
            raise HTTP(400)
    else:
        raise HTTP(400)

    table = s3db.delphi_comment
    field = table.problem_id
    field.default = problem_id
    field.writable = field.readable = False
    sfield = table.solution_id
    if solution_id:
        sfield.default = solution_id
        sfield.writable = sfield.readable = False
    else:
        sfield.label = T("Related to Solution (optional)")
        sfield.requires = IS_EMPTY_OR(
                            IS_ONE_OF(db, "delphi_solution.id",
                                      s3.delphi_solution_represent,
                                      filterby="problem_id",
                                      filter_opts=(problem_id,)
                                      ))

    # Form to add a new Comment
    from gluon.tools import Crud
    form = Crud(db).create(table, formname="delphi_%s/%s" % (resourcename, id))

    # List of existing Comments
    if solution_id:
        comments = db(sfield == solution_id).select(table.id,
                                                    table.parent,
                                                    table.body,
                                                    table.created_by,
                                                    table.created_on)
    else:
        comments = db(field == problem_id).select(table.id,
                                                  table.parent,
                                                  table.solution_id,
                                                  table.body,
                                                  table.created_by,
                                                  table.created_on)

    output = UL(_id="comments")
    for comment in comments:
        if not comment.parent:
            # Show top-level threads at top-level
            thread = comment_parse(comment, comments, solution_id=solution_id)
            output.append(thread)

    # Also see the outer discuss()
    script = \
'''$('#comments').collapsible({xoffset:'-5',yoffset:'50',imagehide:img_path+'arrow-down.png',imageshow:img_path+'arrow-right.png',defaulthide:false})
$('#delphi_comment_parent__row1').hide()
$('#delphi_comment_parent__row').hide()
$('#delphi_comment_body').ckeditor(ck_config)
$('#submit_record__row input').click(function(){$('#comment-form').hide();$('#delphi_comment_body').ckeditorGet().destroy();return true;})'''

    # No layout in this output!
    #s3.jquery_ready.append(script)

    output = DIV(output,
                 DIV(H4(T("New Post"),
                        _id="comment-title"),
                     form,
                     _id="comment-form",
                     _class="clear"),
                 SCRIPT(script))

    return XML(output)

# END =========================================================================
