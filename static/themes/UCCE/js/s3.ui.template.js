/*
 * Survey Editor Widget
 */
(function($, undefined) {
    "use strict";
    var surveyID = 0,
        images = {}, // Store position -> label for images to pipe (Questions with Images & Heatmap regions)
        likert_options = {
            '1': ['Strongly Disagree', 'Disagree', 'Undecided', 'Agree', 'Strongly Agree'],
            '2': ['Very unsatisfied', 'Unsatisfied', 'Neutral', 'Satisfied', 'Very satisfied'],
            '3': ['Very dissatisfied', 'Dissatisfied', 'Neutral', 'Satisfied', 'Very satisfied'],
            '4': ['Pain', 'Neutral', 'No Pain']
        },
        pages = {}, // Store page -> position
        pageElements = {}, // Store page -> #elements
        questionNumbers = {}, // Store question # (in form) -> position
        types_to_int = {
            'text': 1,
            'number': 2,
            'multichoice': 6,
            'likert': 12,
            'heatmap': 13
        },
        types_to_text = {
            1: 'text',
            2: 'number',
            6: 'multichoice',
            7: 'likert',
            13: 'heatmap'
        };

    $.widget('s3.surveyLayout', {

        /**
         * Options
         */
        options: {
        },

        /**
         * Create the widget
         */
        _create: function() {

            this.id = surveyID;
            surveyID += 1;
            this.eventNamespace = '.surveyEditor';

        },

        /**
         * Initialize the widget
         */
        _init: function() {

            var el = $(this.element),
                fieldname = el.attr('id');

            if (!fieldname) {
                fieldname = 'surveyEditor-widget-' + this.id;
            }
            this.fieldname = fieldname;

            this.recordID = el.data('id');
            this.data = null; // Gets populated by _deserialize()

            // Use $.searchS3 if available
            // Not interchangeable as processData defaults differently with each
            if ($.searchS3 !== undefined) {
                this.ajaxMethod = $.searchS3;
            } else {
                this.ajaxMethod = $.ajaxS3;
            }

            this.refresh();

        },

        /**
          * Add a new Question
          *
          */
        addQuestion: function(position, page, type, questionID) {

            if (type == 'instructions') {
                // Not a real Question, so don't try to get an ID from server
                if (questionID) {
                    // We are loading an existing Survey
                    this._addQuestion(position, page, type, null, true);
                } else{
                    this._addQuestion(position, page, type);
                }
            } else if (questionID) {
                // We are loading an existing Survey, so don't try to get an ID from server
                this._addQuestion(position, page, type, questionID, true);
            } else {
                // Create record on server to get the question_id
                var self = this,
                    ajaxURL = S3.Ap.concat('/dc/question/create_json.json'),
                    // $.searchS3 defaults to processData: false
                    data = JSON.stringify({type: types_to_int[type],
                                           template_id: this.recordID
                                           });
                    //data = {type: types_to_int[type],
                    //        template_id: this.recordID
                    //        };
                this.ajaxMethod({
                    url: ajaxURL,
                    type: 'POST',
                    data: data,
                    dataType: 'json',
                    success: function(data) {
                        self._addQuestion(position, page, type, data.question_id);
                    },
                    error: function(jqXHR, textStatus, errorThrown) {
                        var msg;
                        if (errorThrown == 'UNAUTHORIZED') {
                            msg = i18n.gis_requires_login;
                        } else {
                            msg = jqXHR.responseText;
                        }
                        console.log(msg);
                    }
                });
            }
        },

        /**
          * DRY Helper for addQuestion
          */
        _addQuestion: function(position, page, type, questionID, load) {

            if (!load) {
                // Update Data
                if (type == 'instructions') {
                    this.data.layout[position] = {
                        type: 'instructions',
                        do: {text: ''},
                        say: {text: ''},
                   };
                } else {
                    this.data.layout[position] = {
                        type: 'question',
                        id: questionID
                    };
                }
                // Save Template
                this.save();
            }

            // Build the Question HTML
            var question,
                editTab,
                formElements;

            if (type == 'instructions') {
                question = '<div class="thumbnail dl-item" id="instruction-' + position + '" data-page="' + page + '"><div class="card-header"><div class="fleft">Edit</div> <div class="fleft">Display Logic</div> <div class="fleft">Translation</div> <div class="edit-bar fright"><a><i class="fa fa-copy"> </i></a><a><i class="fa fa-trash"> </i></a><i class="fa fa-arrows-v"> </i></div></div>';
            } else {
                question = '<div class="thumbnail dl-item" id="question-' + questionID + '" data-page="' + page + '"><div class="card-header"><div class="fleft">Edit</div> <div class="fleft">Display Logic</div> <div class="fleft">Translation</div> <div class="edit-bar fright"><a><i class="fa fa-copy"> </i></a><a><i class="fa fa-trash"> </i></a><i class="fa fa-arrows-v"> </i></div></div>';
                var questionNumber = Object.keys(questionNumbers).length + 1;
                questionNumbers[questionNumber] = position;
                var checked = '';
                if (load) {
                    if (this.data.questions[questionID].mandatory) {
                        checked = ' checked';
                    }
                }
                var mandatory = '<div class="row"><input id="mandatory-' + questionID + '" type="checkbox" ' + checked + ' class="fleft"><label>Make question mandatory</label></div>';
                if (type != 'heatmap') {
                    var imageOptions = ''; // @ToDo: Read <option>s from images dict
                    var imageHtml = '<div class="row"><label>Add graphic</label><input type="file" accept="image/png, image/jpeg" class="fleft"><label class="fleft">or pipe question image:</label><select class="fleft"><option value="">select question</option>' + imageOptions + '</select><a>Delete</a></div>';
                }
            }

            switch(type) {

                case 'instructions':
                    var doText = '',
                        sayText = '';
                    if (load) {
                        doText = this.data.layout[position].do.text;
                        sayText = this.data.layout[position].say.text;
                    }
                    editTab = '<div class="media"><h2>Data collector instructions</h2><label>What to do</label><input id="do-' + position + '" type="text" size=100 placeholder="Type what instructor should do" value="' + doText + '"><label>What to say</label><input id="say-' + position + '" type="text" size=100 placeholder="Type what instructor should say" value="' + sayText + '"></div>';
                    formElements = '#instruction-' + position + ' input';
                    break;
                case 'text':
                    var name = '';
                    if (load) {
                        name = this.data.questions[questionID].name;
                    }
                    editTab = '<div class="media"><h2>Text box</h2><div class="row"><label class="fleft">Q' + questionNumber + '</label><input id="name-' + questionID + '" type="text" size=100 placeholder="type question" value="' + name + '"></div>' + mandatory + imageHtml;
                    formElements = '#question-' + questionID + ' input, #question-' + questionID + ' select';
                    break;
                case 'number':
                    var name = '';
                    if (load) {
                        name = this.data.questions[questionID].name;
                    }
                    // @ToDo: Validation of correct input format for restrict
                    var answer = '<div class="row"><h2>Answer</h2><label>Restrict input to:</label><input id="restrict-' + questionID + '" type="text" placeholder="specific input"></div>';
                    editTab = '<div class="media"><h2>Number question</h2><div class="row"><label class="fleft">Q' + questionNumber + '</label><input id="name-' + questionID + '"type="text" size=100 placeholder="type question" value="' + name + '"></div>' + mandatory + imageHtml + answer;
                    formElements = '#question-' + questionID + ' input, #question-' + questionID + ' select';
                    break;
                case 'multichoice':
                    var name = '';
                    if (load) {
                        name = this.data.questions[questionID].name;
                    }
                    var answer = '<div class="row"><h2>Answer</h2><label>Choices</label><input class="choice-' + questionID + '" type="text" placeholder="Enter an answer choice"><i class="fa fa-minus-circle"> </i><i class="fa fa-plus-circle"> </i></div>' +
                                 '<div class="row"><input id="other-' + questionID + '" type="checkbox"><label>Add \'other field\'</label></div>' + 
                                 '<div class="row"><label class="fleft">Field label</label><input id="other-label-' + questionID + '" type="text" placeholder="Other (please specify)" disabled></div>' + 
                                 '<div class="row"><input id="multiple-' + questionID + '" type="checkbox"><label>Allow multiple responses</label></div>' +
                                 '<div class="row"><label class="fleft">Maximum No. of responses:</label><i class="fa fa-minus-circle"> </i> 1 <i class="fa fa-plus-circle"> </i></div>';
                    editTab = '<div class="media"><h2>Multiple choice question</h2><div class="row"><label class="fleft">Q' + questionNumber + '</label><input id="name-' + questionID + '"type="text" size=100 placeholder="type question" value="' + name + '"></div>' + mandatory + imageHtml + answer;
                    formElements = '#question-' + questionID + ' input, #question-' + questionID + ' select';
                    break;
                case 'likert':
                    var name = '';
                    if (load) {
                        name = this.data.questions[questionID].name;
                    }
                    var scaleOptions = '<option value="1">Agreement (Disagree - Agree)</option><option value="2">Satisfaction (Smiley scale)</option><option value="3">Satisfaction (Dissatisfied - Satisfied)</option><option value="4">Pain scale (3 point)</option>';
                    var answer = '<div class="row"><h2>Answer</h2><label>Choices</label><select id="scale-' + questionID + '"><option value="">Please select a scale</option>' + scaleOptions + '</select></div>';
                    editTab = '<div class="media"><h2>Likert-scale</h2><div class="row"><label class="fleft">Q' + questionNumber + '</label><input id="name-' + questionID + '"type="text" size=100 placeholder="type question" value="' + name + '"></div>' + mandatory + imageHtml + answer;
                    formElements = '#question-' + questionID + ' input, #question-' + questionID + ' select';
                    break;
                case 'heatmap':
                    var name = '';
                    if (load) {
                        name = this.data.questions[questionID].name;
                    }
                    var image = '<div class="row"><h2>Image</h2><input type="file" accept="image/png, image/jpeg" class="fleft"><h3>Number of clicks allowed:</h3><i class="fa fa-minus-circle"> </i> 1 <i class="fa fa-plus-circle"> </i><h3>Tap/click regions:</h3><a class="button tiny">Add region</a><input id="region-' + position + '-1" type="text" placeholder="enter label" disabled></div>';
                    editTab = '<div class="media"><h2>Heatmap</h2><div class="row"><label class="fleft">Q' + questionNumber + '</label><input id="name-' + questionID + '"type="text" size=100 placeholder="type question" value="' + name + '"></div>' + mandatory + image;
                    formElements = '#question-' + questionID + ' input';
                    break;
            }

            question += editTab;
            question += '</div>';

            // Place before droppable
            $('#survey-droppable-' + position).before(question);
            // Update the position of the droppable
            var newPosition = position + 1;
            $('#survey-droppable-' + position).attr('id', 'survey-droppable-' + newPosition);

            // Update the elements on the section
            pageElements[page]++;
            var pagePosition = pages[page];
            $('#section-break-' + pagePosition + ' > span').html('PAGE ' + page + ' (' + pageElements[page] + ' ELEMENTS)');

            // Change Handlers
            var ns = this.eventNamespace,
                self = this;
            $(formElements).on('change' + ns, function(/* event */) {
                if (type == 'instructions') {
                    // Can't trust original position as it may have changed
                    var current_position = parseInt(this.id.split('-')[1]);
                    // Update Data
                    self.data.layout[position].do.text = $('#do-' + position).val();
                    self.data.layout[position].say.text = $('#say-' + position).val();
                    // Save Template
                    self.save();
                } else {
                    // Save Question
                    self.saveQuestion(type, questionID);
                }
            });
        },

        /**
          * Add a new Section Break
          */
        addSectionBreak: function(position, page, load) {
            page++;
            pages[page] = position;
            pageElements[page] = 0;
            var sectionBreak = '<div class="row"><div class="section-break medium-11 columns" id="section-break-' + position + '"><span>PAGE ' + page + ' (0 ELEMENTS)</span></div><div class="medium-1 columns"><i class="fa fa-times-circle"> </i><i class="fa fa-chevron-circle-down"> </i></div></div>';
            if (position) {
                // Place before droppable
                $('#survey-droppable-' + position).before(sectionBreak);
                // Update the position of the droppable
                var newPosition = position + 1;
                $('#survey-droppable-' + position).attr('id', 'survey-droppable-' + newPosition);
                // Update the page of the droppable
                $('#survey-droppable-' + newPosition).data('page', page);
                // @ToDo: Roll-up previous sections
                if (!load) {
                    // Update Data
                    this.data.layout[position] = {type: 'break'};
                }
            } else {
                // 1st section break
                $(this.element).parent().append(sectionBreak);
            }
        },

        /**
          * Add a new Droppable section into the given position
          */
        droppable: function(position, page) {
            var self = this,
                droppable = '<div class="survey-droppable" id="survey-droppable-' + position + '" data-page="' + page + '"><span>Drag and drop questions here</span></div>';
            $(this.element).parent().append(droppable);

            // (Drag)'n'Drop
            $('#survey-droppable-' + position).droppable({
                drop: function(event, ui) {
                    // Open QuestionEditorWidget with correct options for type
                    var type = ui.draggable[0].id,
                        // Can't trust original position as it may have changed
                        current_position = parseInt(this.id.split('-')[2]),
                        page = $(this).data('page');
                    if (type == "break") {
                        self.addSectionBreak(current_position, page);
                    } else {
                        self.addQuestion(current_position, page, type);
                    }
                }
            });
        },

        /**
          * Remove generated elements & reset other changes
          */
        _destroy: function() {
            $.Widget.prototype.destroy.call(this);
        },

        /**
         * Load an existing Survey layout
         */
        loadSurvey: function() {

            var layout = this.data.layout;
            if (!layout){
                return;
            }

            var item,
                page = 1,
                questionID,
                questions = this.data.questions;

            for (var position=1, len=Object.keys(layout).length + 1; position < len; position++) {
                item = layout[position];
                if (item.type == 'break') {
                    this.addSectionBreak(position, page, true);
                    page++;
                } else if (item.type == 'instructions') {
                    this.addQuestion(position, page, 'instructions', true);
                } else{
                    // Question
                    questionID = item.id;
                    this.addQuestion(position, page, types_to_text[questions[questionID].type], questionID);
                }
            }
        },

        /**
         * Ajax-reload the data and refresh all widget elements
         * @ToDo: Complete if-required
         */
        reload: function() {

            var self = this,
                ajaxURL = S3.Ap.concat('/dc/template/') + this.recordID + '.json';

            this.ajaxMethod({
                url: ajaxURL,
                type: 'GET',
                dataType: 'json',
                success: function(data) {
                    self.input.val(JSON.stringify(data));
                    self.data = data;
                    self.refresh();
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    var msg;
                    if (errorThrown == 'UNAUTHORIZED') {
                        msg = i18n.gis_requires_login;
                    } else {
                        msg = jqXHR.responseText;
                    }
                    console.log(msg);
                }
            });

        },

        /**
         * Redraw widget contents
         */
        refresh: function() {
            this._unbindEvents();
            this._deserialize();

            // Add an initial section break
            this.addSectionBreak(0, 0);

            // Add droppable
            this.droppable(1, 1);

            this.loadSurvey();

            //this._serialize();
            //this._bindEvents();
        },

        /**
         * Ajax-update the Question
         */
        saveQuestion: function(type, questionID) {

            var name = $('#name-' + questionID).val();

            if (!name) {
                // name is required to save
                return;
            }

            var ajaxURL = S3.Ap.concat('/dc/question/') + questionID + '/update_json.json',
                data = {
                    name: name,
                    mandatory: $('#mandatory-' + questionID).prop('checked')
                };

            switch(type) {

                case 'text':
                    // Nothing needed here
                    break;
                case 'number':
                    var rawValue = $('#restrict-' + questionID).val();
                    if (rawValue) {
                        var parts = rawValue.split('-'),
                            min = parts[0],
                            max = parts[1];
                        data.settings = {
                            requires: {
                                isIntInRange: {
                                    min: min,
                                    max: max
                                }
                            }
                        };
                    }
                    break;
                case 'multichoice':
                    break;
                case 'likert':
                    var scale = $('#scale-' + questionID).val();
                    if(scale) {
                        data.options = likert_options[scale];
                    }
                    break;
                case 'heatmap':
                    break;

            }

            this.ajaxMethod({
                url: ajaxURL,
                type: 'POST',
                // $.searchS3 defaults to processData: false
                //data: data,
                data: JSON.stringify(data),
                dataType: 'json',
                success: function(/* data */) {
                    // Nothing needed here
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    var msg;
                    if (errorThrown == 'UNAUTHORIZED') {
                        msg = i18n.gis_requires_login;
                    } else {
                        msg = jqXHR.responseText;
                    }
                    console.log(msg);
                }
            });
        },

        /**
         * Ajax-update the Template
         */
        save: function() {

            var ajaxURL = S3.Ap.concat('/dc/template/') + this.recordID + '/update_json.json';

            // Encode this.data as JSON and write into real input
            //this._serialize();

            this.ajaxMethod({
                url: ajaxURL,
                type: 'POST',
                // $.searchS3 defaults to processData: false
                //data: {layout: this.data},
                data: JSON.stringify({layout: this.data.layout}),
                //processData: false,
                dataType: 'json',
                success: function(/* data */) {
                    // Nothing needed here
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    var msg;
                    if (errorThrown == 'UNAUTHORIZED') {
                        msg = i18n.gis_requires_login;
                    } else {
                        msg = jqXHR.responseText;
                    }
                    console.log(msg);
                }
            });

        },

        /**
         * Encode this.data as JSON and write into real input
         *
         * (unused)
         *
         * @returns {JSON} the JSON data
         */
        _serialize: function() {

            var json = JSON.stringify(this.data);
            $(this.element).val(json);
            return json;

        },

        /**
         * Parse the JSON from real input into this.data
         *
         * @returns {object} this.data
         */
        _deserialize: function() {

            var value = $(this.element).val() || '{}';
            this.data = JSON.parse(value);
            return this.data;

        },

        /**
         * Bind event handlers (after refresh)
         *
         * (unused)
         */
        _bindEvents: function() {

            var self = this,
                ns = this.eventNamespace;

            /* Bind change event for all the input fields
            var selector = '#' + this.fieldname;

            this.inputFields.bind('change' + ns, function() {
                self._collectData(this);
            }); */

        },

        /**
         * Unbind events (before refresh)
         */
        _unbindEvents: function() {

            var ns = this.eventNamespace,
                el = $(this.element);

            /* this.inputFields.unbind(ns); */
            el.unbind(ns);

            return true;
        }

    });
})(jQuery);
