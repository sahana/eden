# -*- coding: utf-8 -*-

"""
    Data Collection
"""

module = request.controller

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    module_name = settings.modules[module].name_nice
    response.title = module_name
    return dict(module_name=module_name)

# -----------------------------------------------------------------------------
def template():
    """ Manage Data Collection Templates """

    def prep(r):

        if r.record and r.component_name == "question":

            # Allow adding of new questions if they are not linked
            # to this template yet
            qtable = s3db.dc_question
            ltable = s3db.dc_template_question
            left = ltable.on((ltable.question_id == qtable.id) & \
                             (ltable.deleted != True))
            query = (qtable.deleted != True) & \
                    ((ltable.template_id != r.id) | \
                     (ltable.template_id == None))

            # Restrict field options accordingly
            db = current.db
            field = ltable.question_id
            field.requires = IS_ONE_OF(db(query),
                                       "dc_question.id",
                                       field.represent,
                                       left=left)

        return True
    s3.prep = prep

    return s3_rest_controller(rheader = s3db.dc_rheader)

# -----------------------------------------------------------------------------
def question():
    """ Manage Data Collection Questions """

    def prep(r):
        record = r.record
        if record and r.component_name == "question_l10n":
            ttable = r.component.table
            if r.method != "update":
                ttable.question.default = record.question
                ttable.options.default = record.options

            # Remove language options for which we already have
            # a translation of this question
            requires = ttable.language.requires
            if isinstance(requires, IS_ISO639_2_LANGUAGE_CODE):
                all_options = dict(requires.language_codes())
                selectable = requires._select
                if not selectable:
                    selectable = all_options
                selectable = dict(selectable)
                query = (ttable.question_id == r.id) & \
                        (ttable.deleted != True)
                if r.component_id:
                    query &= (ttable.id != r.component_id)
                rows = db(query).select(ttable.language)
                for row in rows:
                    selectable.pop(row.language, None)
                if len(selectable) == 0 or \
                    not any(opt in all_options for opt in selectable):
                    # No more languages to translate into
                    # => hide create form
                    r.component.configure(insertable = False)
                requires._select = selectable
        return True
    s3.prep = prep

    return s3_rest_controller(rheader = s3db.dc_rheader)

# -----------------------------------------------------------------------------
def collection():
    """ Manage Data Collections """

    def prep(r):

        if r.record and r.component_name == "answer":

            # Allow only unanswered questions
            atable = s3db.dc_answer
            qtable = s3db.dc_question
            left = [atable.on((atable.question_id == qtable.id) & \
                              (atable.collection_id == r.id) & \
                              (atable.deleted != True))]
            if r.component_id:
                query = (atable.id == None) | (atable.id == r.component_id)
            else:
                query = (atable.id == None)

            # Allow only questions from the selected template
            template_id = r.record.template_id
            if template_id:
                ltable = s3db.dc_template_question
                left.append(ltable.on((ltable.question_id == qtable.id) & \
                                      (ltable.deleted != True)))
                query &= (ltable.template_id == template_id)

            # Restrict field options accordingly
            db = current.db
            field = atable.question_id
            field.requires = IS_ONE_OF(db(query),
                                       "dc_question.id",
                                       field.represent,
                                       left=left)

            # Hide create form when all questions have been answered
            if r.method != "update":
                count = qtable.id.count()
                row = db(query).select(count,
                                       left=left,
                                       limitby=(0, 1)).first()
                if not row or not row[count]:
                    r.component.configure(insertable=False)

        return True
    s3.prep = prep

    return s3_rest_controller(rheader = s3db.dc_rheader)

# -----------------------------------------------------------------------------
def template_question():
    """
        RESTful CRUD controller for options.s3json lookups
        - needed for adding questions to a template
    """

    s3.prep = lambda r: r.method == "options" and r.representation == "s3json"

    return s3_rest_controller()

# END =========================================================================
