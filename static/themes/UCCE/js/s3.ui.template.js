/*
 * Survey Editor Widget
 */
(function($, undefined) {
    "use strict";
    var surveyID = 0,
        pages = {}, // Store page -> position
        pageElements = {}, // Store page -> #elements
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
            this.data = el.val();

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
                        self._addQuestion(position, page, type, data['question_id']);
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

            if (type == 'instructions') {
                var idHtml = '';
            } else {
                var idHtml = ' data-id="' + questionID + '"';
            }

            // Build the Question HTML
            var question = '<div class="thumbnail dl-item" id="question-' + position + '" data-page="' + page + '"' + idHtml + '><div class="card-header"><div class="fleft">Edit</div> <div class="fleft">Display Logic</div> <div class="fleft">Translation</div> <div class="edit-bar fright"><a><i class="fa fa-copy"> </i></a><a><i class="fa fa-trash"> </i></a><i class="fa fa-arrows-v"> </i></div></div>';

            //var selector = '#' + fieldname,
            var editTab;

            switch(type) {

                case 'instructions':
                    editTab = '<div class="media"></div>';
                case 'text':
                    editTab = '<div class="media"></div>';
                case 'number':
                    editTab = '<div class="media"></div>';
                case 'multichoice':
                    editTab = '<div class="media"></div>';
                case 'likert':
                    editTab = '<div class="media"></div>';
                case 'heatmap':
                    editTab = '<div class="media"></div>';
            }

            question += editTab;
            question += '</div>';

            // Place before droppable
            $('#survey-droppable-' + position).before(question);
            // Update the position of the droppable
            var newPosition = position + 1
            $('#survey-droppable-' + position).attr('id', 'survey-droppable-' + newPosition);
            // Update the elements on the section
            pageElements[page]++;
            var pagePosition = pages[page];
            $('#section-break-' + pagePosition + ' > span').html('PAGE ' + page + ' (' + pageElements[page] + ' ELEMENTS)');

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
                var newPosition = position + 1
                $('#survey-droppable-' + position).attr('id', 'survey-droppable-' + newPosition);
                // Update the page of the droppable
                $('#survey-droppable-' + newPosition).data('page', page);
                // @ToDo: Roll-up previous sections
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
         */
        reload: function() {

            // Reload data and refresh
            var self = this;

            // Ajax URL
            var ajaxURL = this.options.ajaxURL + this.recordID + '.json';

            this.ajaxMethod({
                'url': ajaxURL,
                'type': 'POST',
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

            this._serialize();
            this._bindEvents();
        },

        /**
         * Encode this.data as JSON and write into real input
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
         * Collect Data from all the input fields
         */
        _collectData: function(inputObj) {

            var selector = '#' + inputObj.id,
                value = $(selector).val(),
                name = inputObj.id.substr(18);

            // For input type - checkbox
            // true => checkbox checked
            // false => empty checkbox
            if ($(selector).is(':checkbox')) {
                value = $(selector).prop('checked').toString();
            }

            this.data[name] = value;
            this._serialize();
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
