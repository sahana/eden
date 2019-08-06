/*
 * Survey Editor Widget
 */
(function($, undefined) {
    "use strict";
    var surveyID = 0,
        images = {}, // Store position -> label for images to pipe (Questions with Images & Heatmap regions)
        pages = {}, // Store page -> position
        pageElements = {}, // Store page -> #elements
        questions = {}, // Store question # (in form) -> position
        types = {
            'text': 1,
            'number': 2,
            'multichoice': 6,
            'likert': 12,
            'heatmap': 13,
        };

    $.widget('s3.surveyLayout', {

        /**
         * Options
         */
        options: {
            ajaxURL: S3.Ap.concat('/dc/template/')
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
        addQuestion: function(position, page, type) {

            if (type == 'instructions') {
                // Not a real Question so don't try to get an ID from server
                this._addQuestion(position, page, type);
            } else {
                // Create record on server to get the question_id
                var self = this,
                    ajaxURL = S3.Ap.concat('/dc/question/create_json.json'),
                    data = JSON.stringify({type: types[type],
                                           template_id: this.recordID
                                           });

                this.ajaxMethod({
                    'url': ajaxURL,
                    'type': 'POST',
                    'data': data,
                    'dataType': 'json',
                    'success': function(data) {
                        self._addQuestion(position, page, type, data.question_id);
                    },
                    'error': function(jqXHR, textStatus, errorThrown) {
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
        _addQuestion: function(position, page, type, questionID) {

            // Update Data
            if (type == 'instructions') {
                this.data[position] = {
                    type: 'instructions',
                    do: {text: ''},
                    say: {text: ''},
               };
            } else {
                this.data[position] = {
                    type: 'question',
                    id: questionID
                };
            }
            // Save Template
            this.save();

            var idHtml; // declare outside if/else as otherwise JS compiler always processes both branches
            if (type == 'instructions') {
                idHtml = '';
            } else {
                var questionNumber = Object.keys(questions).length + 1;
                questions[questionNumber] = position;
                idHtml = ' data-id="' + questionID + '"';
                var mandatory = '<div class="row"><input id="mandatory-' + position + '"type="checkbox" class="fleft"><label>Make question mandatory</label></div>';
                if (type != 'heatmap') {
                    var imageOptions = ''; // @ToDo: Read <option>s from images dict
                    var imageHtml = '<div class="row"><label>Add graphic</label><input type="file" accept="image/png, image/jpeg" class="fleft"><label class="fleft">or pipe question image:</label><select class="fleft"><option value="">select question</option>' + imageOptions + '</select><a>Delete</a></div>';
                }
            }

            // Build the Question HTML
            var question = '<div class="thumbnail dl-item" id="question-' + position + '" data-page="' + page + '"' + idHtml + '><div class="card-header"><div class="fleft">Edit</div> <div class="fleft">Display Logic</div> <div class="fleft">Translation</div> <div class="edit-bar fright"><a><i class="fa fa-copy"> </i></a><a><i class="fa fa-trash"> </i></a><i class="fa fa-arrows-v"> </i></div></div>';

            var editTab,
                formElements;

            switch(type) {

                case 'instructions':
                    editTab = '<div class="media"><h2>Data collector instructions</h2><label>What to do</label><input id="do-' + position + '" type="text" size=100 placeholder="Type what instructor should do"><label>What to say</label><input id="say-' + position + '" type="text" size=100 placeholder="Type what instructor should say"></div>';
                    formElements = '#question-' + position + ' input';
                    break;
                case 'text':
                    editTab = '<div class="media"><h2>Text box</h2><div class="row"><label class="fleft">Q' + questionNumber + '</label><input id="name-' + position + '" type="text" size=100 placeholder="type question"></div>' + mandatory + imageHtml;
                    formElements = '#question-' + position + ' input, #question-' + position + ' select';
                    break;
                case 'number':
                    // @ToDo: Validation of correct input format
                    var answer = '<div class="row"><h2>Answer</h2><label>Restrict input to:</label><input id="restrict-' + position + '" type="text" placeholder="specific input"></div>';
                    editTab = '<div class="media"><h2>Number question</h2><div class="row"><label class="fleft">Q' + questionNumber + '</label><input id="name-' + position + '"type="text" size=100 placeholder="type question"></div>' + mandatory + imageHtml + answer;
                    formElements = '#question-' + position + ' input, #question-' + position + ' select';
                    break;
                case 'multichoice':
                    editTab = '<div class="media"><h2>Multiple choice question</h2><div class="row"><label class="fleft">Q' + questionNumber + '</label><input id="name-' + position + '"type="text" size=100 placeholder="type question"></div>' + mandatory + imageHtml;
                    formElements = '#question-' + position + ' input, #question-' + position + ' select';
                    break;
                case 'likert':
                    editTab = '<div class="media"><h2>Likert-scale</h2><div class="row"><label class="fleft">Q' + questionNumber + '</label><input id="name-' + position + '"type="text" size=100 placeholder="type question"></div>' + mandatory + imageHtml;
                    formElements = '#question-' + position + ' input, #question-' + position + ' select';
                    break;
                case 'heatmap':
                    editTab = '<div class="media"><h2>Heatmap</h2><div class="row"><label class="fleft">Q' + questionNumber + '</label><input id="name-' + position + '"type="text" size=100 placeholder="type question"></div>' + mandatory;
                    formElements = '#question-' + position + ' input';
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
                    // Update Data
                    self.data[position].do.text = $('#do-' + position).val();
                    self.data[position].say.text = $('#say-' + position).val();
                    // Save Template
                    self.save();
                } else {
                    // Save Question
                    self.saveQuestion(position, type, questionID);
                }
            });
        },

        /**
          * Add a new Section Break
          */
        sectionBreak: function(position, page) {
            page++;
            pages[page] = position;
            pageElements[page] = 0;
            var sectionBreak = '<div class="row"><div class="section-break medium-11 columns" id="section-break-' + position + '"><span>PAGE ' + page + ' (0 ELEMENTS)</span></div><div class="medium-1 columns"><i class="fa fa-caret-down"> </i></div></div>';
            if (position) {
                // Place before droppable
                $('#survey-droppable-' + position).before(sectionBreak);
                // Update the position of the droppable
                var newPosition = position + 1;
                $('#survey-droppable-' + position).attr('id', 'survey-droppable-' + newPosition);
                // Update the page of the droppable
                $('#survey-droppable-' + newPosition).data('page', page);
                // @ToDo: Roll-up previous sections
                // Update Data
                this.data[position] = {type: 'break'};
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
                        self.sectionBreak(current_position, page);
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
         * Ajax-reload the data and refresh all widget elements
         * @ToDo: Complete if-required
         */
        reload: function() {

            var self = this,
                ajaxURL = this.options.ajaxURL + this.recordID + '.json';

            this.ajaxMethod({
                'url': ajaxURL,
                'type': 'GET',
                'dataType': 'json',
                'success': function(data) {
                    self.input.val(JSON.stringify(data));
                    self.data = data;
                    self.refresh();
                },
                'error': function(jqXHR, textStatus, errorThrown) {
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
            this.sectionBreak(0, 0);

            // Add an initial droppable
            this.droppable(1, 1);
            
            if (this.data) {
                // @ToDo: Handle opening existing surveys
            }

            //this._serialize();
            this._bindEvents();
        },

        /**
         * Ajax-update the Question
         */
        saveQuestion: function(position, type, questionID) {

            var name = $('#name-' + position).val();

            // name is required
            if (name) {

                var ajaxURL = S3.Ap.concat('/dc/question/') + questionID + '/update_json.json';

                var data = {
                    name: name,
                    mandatory: $('#mandatory-' + position).prop('checked')
                };
                if (type == 'number') {
                    var rawValue = $('#restrict-' + position).val();
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
                }
            }

            this.ajaxMethod({
                'url': ajaxURL,
                'type': 'POST',
                // $.searchS3 defaults to processData: false
                'data': JSON.stringify(data),
                'dataType': 'json',
                'success': function(/* data */) {
                    // Nothing needed here
                },
                'error': function(jqXHR, textStatus, errorThrown) {
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

            var ajaxURL = this.options.ajaxURL + this.recordID + '/update_json.json';

            // Encode this.data as JSON and write into real input
            //this._serialize();

            this.ajaxMethod({
                'url': ajaxURL,
                'type': 'POST',
                // $.searchS3 defaults to processData: false
                'data': JSON.stringify({layout: this.data}),
                'dataType': 'json',
                'success': function(/* data */) {
                    // Nothing needed here
                },
                'error': function(jqXHR, textStatus, errorThrown) {
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
