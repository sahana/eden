/*
 * Survey Editor Widget
 */
(function(factory) {
  'use strict';
  // Browser globals (not AMD or Node):
  factory(window.jQuery, window.loadImage);
})(function($, loadImage) {
    'use strict';
    var surveyID = 0,
        imageOptions = [], // Store {label: label, (just held locally)
                           //        id: questionID, {Also on server in settings.pipeImage)
                           //        region: regionID {Also on server in settings.pipeImage)
                           //        } for images that can be piped (Questions with Images & Heatmap regions)
        likertOptions = {
            '1': ['Strongly Disagree', 'Disagree', 'Undecided', 'Agree', 'Strongly Agree'],
            '2': ['Very unsatisfied', 'Unsatisfied', 'Neutral', 'Satisfied', 'Very satisfied'],
            '3': ['Very dissatisfied', 'Dissatisfied', 'Neutral', 'Satisfied', 'Very satisfied'],
            '4': ['Pain', 'Neutral', 'No Pain']
        },
        pages = {}, // Store page -> position
        pageElements = {}, // Store page -> #elements
        questionNumbers = {}, // Store question # (in form) -> position
        typesToInt = {
            'text': 1,
            'number': 2,
            'multichoice': 6,
            'likert': 12,
            'heatmap': 13
        },
        typesToText = {
            1: 'text',
            2: 'number',
            6: 'multichoice',
            12: 'likert',
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

            // extend jQuery Validator plugin
            $.validator.addMethod(
                'lessThanMax', 
                function(value, element) {
                    var questionID = element.id.split('-')[1],
                        max = $('#max-' + questionID).val();
                    
                    return this.optional(element) || (parseFloat(value) <= max);
                },
                'needs to be lower than Maximum'
            );
            $.validator.addMethod(
                'greaterThanMin', 
                function(value, element) {
                    var questionID = element.id.split('-')[1],
                        min = $('#min-' + questionID).val();

                    return this.optional(element) || (parseFloat(value) >= min);
                },
                'needs to be higher than Minimum'
            );

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
                } else {
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
                    data = JSON.stringify({type: typesToInt[type],
                                           template_id: this.recordID
                                           });
                    //data = {type: typesToInt[type],
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

            var l10n = this.data.l10n,
                questionNumber;

            if (load) {
                // Read QuestionNumber created during loadSurvey
                for (var i=1, len=Object.keys(questionNumbers).length; i <= len; i++) {
                    if (position == questionNumbers[i]) {
                        questionNumber = i;
                        break;
                    }
                }
            } else {
                if (type == 'instructions') {
                    // Update Data
                    this.data.layout[position] = {
                        type: 'instructions',
                        do: {text: ''},
                        say: {text: ''},
                   };
                } else {
                    // Add QuestionNumber
                    questionNumber = Object.keys(questionNumbers).length + 1;
                    questionNumbers[questionNumber] = position;

                    // Update Data
                    this.data.layout[position] = {
                        type: 'question',
                        id: questionID
                    };
                    this.data.questions[questionID] = {
                        type: typesToInt[type],
                        settings: {}
                    };
                }
                // Save Template
                this.saveLayout();
            }

            // Build the Question HTML
            var idHtml,
                dataHtml,
                editTab,
                formElements,
                imageHtml,
                newChoice,
                optionsHtml,
                logicTab,
                mandatory,
                question,
                thisQuestion,
                translationTab,
                translationTitle = '',
                trash;

            if (l10n) {
                translationTitle = '<li class="tab-title"><a href="#translation-' + position + '">Translation</a></li>';
            }

            if (type == 'instructions') {
                idHtml = 'instruction-' + position;
                dataHtml = '';
            } else {
                idHtml = 'question-' + questionID;
                dataHtml = ' data-number="' + questionNumber + '"';
                var checked = '';
                thisQuestion = this.data.questions[questionID];
                if (load) {
                    if (thisQuestion.mandatory) {
                        checked = ' checked';
                    }
                }
                mandatory = '<div class="row"><input id="mandatory-' + questionID + '" type="checkbox" ' + checked + ' class="fleft"><label>Make question mandatory</label></div>';
                if (type != 'heatmap') {
                    // Upload or Pipe Image
                    optionsHtml = this.pipeOptionsHtml(questionID, load);
                    imageHtml = '<div class="row"><label>Add image</label><span id="preview-' + questionID + '" class="preview-empty fleft"></span><label for="image-' + questionID + '" class="button tiny fleft">Upload image</label><input id="image-' + questionID + '" name="file" type="file" accept="image/png, image/jpeg" class="show-for-sr">' + 
                                '<label class="fleft">or pipe question image:</label><select id="pipe-' + questionID + '" class="fleft">' + optionsHtml + '</select>' +
                                '<a id="image-delete-' + questionID + '">Delete</a></div>';
                }
            }

            question = '<div class="thumbnail dl-item" id="' + idHtml + '" data-page="' + page + '"' + dataHtml + '>' + 
                       '<div class="card-header"><ul class="tabs fleft" data-tab><li class="tab-title active"><a href="#edit-' + position + '">Edit</a></li><li class="tab-title"><a href="#logic-' + position + '">Display Logic</a></li> ' + translationTitle + '</ul>' +
                       '<div class="edit-bar fright"><a><i class="ucce ucce-duplicate"> </i></a><a><i class="ucce ucce-delete"> </i></a><i class="ucce ucce-up"> </i><i class="ucce ucce-down"> </i></div>' + 
                       '</div>' + 
                       '<div class="tabs-content">';

            optionsHtml = this.logicOptionsHtml(questionID, load);
            logicTab = '<div class="media content" id="logic-' + position + '"><h2>Only display question if...</h2><select id="logic-select-' + questionID + '" class="fleft">' + optionsHtml + '</select><label>response is</label></div>';

            switch(type) {

                case 'instructions':
                    var doText = '',
                        doTextL10n = '',
                        sayText = '',
                        sayTextL10n = '';
                    if (load) {
                        var thisLayout = this.data.layout[position];
                        doText = thisLayout.do.text;
                        sayText = thisLayout.say.text;
                        if (l10n && thisLayout.do.l10n) {
                            doTextL10n = thisLayout.do.l10n[l10n];
                            sayTextL10n = thisLayout.say.l10n[l10n];
                        }
                    }
                    editTab = '<div class="media content active" id="edit-' + position + '"><h2>Data collector instructions</h2><label>What to do</label><input id="do-' + position + '" type="text" size=100 placeholder="Type what instructor should do" value="' + doText + '"><label>What to say</label><input id="say-' + position + '" type="text" size=100 placeholder="Type what instructor should say" value="' + sayText + '"></div>';
                    translationTab = '<div class="media content" id="translation-' + position + '"><h2>Data collector instructions</h2><label>What to do</label><input id="do-l10n-' + position + '" type="text" size=100 placeholder="Type translation of what instructor should do" value="' + doTextL10n + '"><label>What to say</label><input id="say-l10n-' + position + '" type="text" size=100 placeholder="Type translation of what instructor should say" value="' + sayTextL10n + '"></div>';
                    formElements = '#instruction-' + position + ' input';
                    trash = '#instruction-' + position + ' .ucce-delete';
                    break;

                case 'text':
                    var name = '',
                        nameL10n = '';
                    if (load) {
                        name = thisQuestion.name;
                        if (l10n) {
                            nameL10n = thisQuestion.name_l10n || '';
                        }
                    }
                    editTab = '<div class="media content active" id="edit-' + position + '"><h2>Text box</h2><div class="row"><label id="qlabel-' + questionID + '" class="fleft">Q' + questionNumber + '</label><input id="name-' + questionID + '" type="text" size=100 placeholder="type question" value="' + name + '"></div>' + mandatory + imageHtml + '</div>';
                    translationTab = '<div class="media content" id="translation-' + position + '"><h2>Text box</h2><div class="row"><label id="qlabel-l10n-' + questionID + '" class="fleft">Q' + questionNumber + '</label><input id="name-l10n-' + questionID + '" type="text" size=100 placeholder="type translated question" value="' + nameL10n + '"></div></div>';
                    formElements = '#question-' + questionID + ' input, #question-' + questionID + ' select';
                    trash = '#question-' + questionID + ' .ucce-delete';
                    break;

                case 'number':
                    var name = '',
                        nameL10n = '',
                        min = '',
                        max = '';
                    if (load) {
                        name = thisQuestion.name;
                        if (l10n) {
                            nameL10n = thisQuestion.name_l10n || '';
                        }
                        var settings = thisQuestion.settings || {},
                            requires = settings.requires || {},
                            isIntInRange = requires.isIntInRange;
                        if (isIntInRange) {
                            min = isIntInRange.min || '';
                            max = isIntInRange.max || '';
                        }
                    }
                    editTab = '<div class="media content active" id="edit-' + position + '"><h2>Number question</h2><div class="row"><label id="qlabel-' + questionID + '" class="fleft">Q' + questionNumber + '</label><input id="name-' + questionID + '"type="text" size=100 placeholder="type question" value="' + name + '"></div>' + mandatory + imageHtml +
                              '<div class="row"><h2>Answer</h2><form id="answer-' + questionID + '"><label>Minimum:</label><input id="min-' + questionID + '" name="min" type="number" value="' + min + '"><label>Maximum:</label><input id="max-' + questionID + '" name="max" type="number" value="' + max + '"></form></div></div>';
                    translationTab = '<div class="media content" id="translation-' + position + '"><h2>Number question</h2><div class="row"><label id="qlabel-l10n-' + questionID + '" class="fleft">Q' + questionNumber + '</label><input id="name-l10n-' + questionID + '"type="text" size=100 placeholder="type translated question" value="' + nameL10n + '"></div';
                    formElements = '#question-' + questionID + ' input, #question-' + questionID + ' select';
                    trash = '#question-' + questionID + ' .ucce-delete';
                    break;

                case 'multichoice':
                    newChoice = '<div class="row"><input class="choice-' + questionID + '" type="text" placeholder="Enter an answer choice"><i class="ucce ucce-minus"> </i><i class="ucce ucce-plus"> </i></div>';
                    // @ToDo: Grey the multiple -+ options if they cannot do anything
                    var name = '',
                        nameL10n = '',
                        choices = newChoice,
                        other = '',
                        other_disabled = ' disabled',
                        other_label = '',
                        multiple = 1,
                        multiChecked = '';
                    if (load) {
                        name = thisQuestion.name;
                        if (l10n) {
                            nameL10n = thisQuestion.name_l10n || '';
                        }
                        var options = thisQuestion.options || [],
                            lenOptions = options.length;
                        if (lenOptions) {
                            choices = '';
                            for (var i=0; i < lenOptions; i++) {
                                choices += '<div class="row"><input class="choice-' + questionID + '" type="text" placeholder="Enter an answer choice" value="' + options[i] + '"><i class="ucce ucce-minus"> </i><i class="ucce ucce-plus"> </i></div>';
                            }
                        }
                        var settings = thisQuestion.settings;
                        other_label = settings.other || '';
                        if (other_label) {
                            other = ' checked';
                            other_disabled = '';
                        }
                        multiple = settings.multiple || 1;
                        if (multiple > 1) {
                            multiChecked = ' checked';
                        }
                    }
                    editTab = '<div class="media content active" id="edit-' + position + '"><h2>Multiple choice question</h2><div class="row"><label id="qlabel-' + questionID + '" class="fleft">Q' + questionNumber + '</label><input id="name-' + questionID + '"type="text" size=100 placeholder="type question" value="' + name + '"></div>' + mandatory + imageHtml +
                              '<div class="row"><h2>Answer</h2><label>Choices</label></div>' + choices +
                              '<div class="row"><input id="other-' + questionID + '" type="checkbox"' + other + '><label>Add \'other field\'</label></div>' + 
                              '<div class="row"><label class="fleft">Field label</label><input id="other-label-' + questionID + '" type="text" placeholder="Other (please specify)" value="' + other_label + '"' + other_disabled + '></div>' + 
                              '<div class="row"><input id="multiple-' + questionID + '" type="checkbox"' + multiChecked + '><label>Allow multiple responses</label></div>' +
                              '<div class="row"><label class="fleft">Maximum No. of responses:</label><i class="ucce ucce-minus"> </i> <span id="multiple-count-' + questionID + '">' + multiple + '</span> <i class="ucce ucce-plus"> </i></div></div>';
                    
                    translationTab = '<div class="media content" id="translation-' + position + '"><h2>Multiple choice question</h2><div class="row"><label id="qlabel-l10n-' + questionID + '" class="fleft">Q' + questionNumber + '</label><input id="name-l10n-' + questionID + '"type="text" size=100 placeholder="type translated question" value="' + nameL10n + '"></div';
                    formElements = '#question-' + questionID + ' input, #question-' + questionID + ' select';
                    trash = '#question-' + questionID + ' .ucce-delete';
                    break;

                case 'likert':
                    var name = '',
                        nameL10n = '',
                        displayOptions = '',
                        scales = [
                            '<option value="1">Agreement (Disagree - Agree)</option>',
                            '<option value="2">Satisfaction (Smiley scale)</option>',
                            '<option value="3">Satisfaction (Dissatisfied - Satisfied)</option>',
                            '<option value="4">Pain scale (3 point)</option>'
                            ];
                    if (load) {
                        name = thisQuestion.name;
                        if (l10n) {
                            nameL10n = thisQuestion.name_l10n || '';
                        }
                        var settings = thisQuestion.settings;
                        if (settings && settings.hasOwnProperty('scale')) {
                            var scale = settings.scale;
                            if (scale) {
                                scales[scale - 1] = scales[scale - 1].replace('">', '" selected>');
                                var options = likertOptions[scale];
                                displayOptions += '<ul>';
                                for (var i=0, len = options.length; i < len; i++) {
                                    displayOptions += '<li>' + options[i] + '</li>';
                                }
                                displayOptions += '</ul>';
                            }
                        }
                    }
                    var scaleOptions = scales.join();
                    editTab = '<div class="media content active" id="edit-' + position + '"><h2>Likert-scale</h2><div class="row"><label id="qlabel-' + questionID + '" class="fleft">Q' + questionNumber + '</label><input id="name-' + questionID + '"type="text" size=100 placeholder="type question" value="' + name + '"></div>' + mandatory + imageHtml +
                              '<div class="row"><h2>Answer</h2><label>Choices</label><select id="scale-' + questionID + '"><option value="">Please choose scale</option>' + scaleOptions + '</select></div><div class="row">' + displayOptions + '</div></div>';
                    translationTab = '<div class="media content" id="translation-' + position + '"><h2>Likert-scale</h2><div class="row"><label id="qlabel-l10n-' + questionID + '" class="fleft">Q' + questionNumber + '</label><input id="name-l10n-' + questionID + '"type="text" size=100 placeholder="type translated question" value="' + nameL10n + '"></div';
                    formElements = '#question-' + questionID + ' input, #question-' + questionID + ' select';
                    trash = '#question-' + questionID + ' .ucce-delete';
                    break;

                case 'heatmap':
                    var name = '',
                        nameL10n = '',
                        optionsL10n = '';
                    if (load) {
                        name = thisQuestion.name;
                        if (l10n) {
                            nameL10n = thisQuestion.name_l10n || '';
                        }
                    }
                    editTab = '<div class="media content active" id="edit-' + position + '"><h2>Heatmap</h2><div class="row"><label id="qlabel-' + questionID + '" class="fleft">Q' + questionNumber + '</label><input id="name-' + questionID + '"type="text" size=100 placeholder="type question" value="' + name + '"></div>' + mandatory +
                              '<div class="row"><h2>Image</h2><span id="preview-' + questionID + '" class="preview-empty fleft"></span><label for="image-' + questionID + '" class="button tiny fleft">Upload image</label><input id="image-' + questionID + '" name="file" type="file" accept="image/png, image/jpeg" class="show-for-sr"><h3>Number of clicks allowed:</h3><i class="ucce ucce-minus"> </i> 1 <i class="ucce ucce-plus"> </i><h3>Tap/click regions:</h3><a class="button tiny">Add region</a><input id="region-' + position + '-1" type="text" placeholder="enter label" disabled></div></div>';
                    translationTab = '<div class="media content" id="translation-' + position + '"><h2>Heatmap</h2><div class="row"><label id="qlabel-l10n-' + questionID + '" class="fleft">Q' + questionNumber + '</label><input id="name-l10n-' + questionID + '"type="text" size=100 placeholder="type translated question" value="' + nameL10n + '"></div';
                    formElements = '#question-' + questionID + ' input';
                    trash = '#question-' + questionID + ' .ucce-delete';
                    break;
            }

            question += editTab;
            question += logicTab;
            if (l10n) {
                question += translationTab;
            }
            question += '</div></div>';

            // Place before droppable
            $('#survey-droppable-' + position).before(question);
            // Update the position of the droppable
            var newPosition = position + 1;
            $('#survey-droppable-' + position).attr('id', 'survey-droppable-' + newPosition);

            // Update the elements on the section
            pageElements[page]++;
            var pagePosition = pages[page];
            $('#section-break-' + pagePosition + ' > span').html('PAGE ' + page + ' (' + pageElements[page] + ' ELEMENTS)');

            // Event Handlers
            var ns = this.eventNamespace,
                self = this;

            var inputEvents = function() {
                $(formElements).off('change' + ns)
                               .on('change' + ns, function(/* event */) {
                    // If form elements change, then Save
                    if (type == 'instructions') {
                        // Can't trust original position as it may have changed
                        var parts = this.id.split('-'),
                            currentPosition = parseInt(parts[parts.length - 1]);
                        // Update Data
                        var thisLayout = self.data.layout[currentPosition];
                        thisLayout.do.text = $('#do-' + currentPosition).val();
                        thisLayout.say.text = $('#say-' + currentPosition).val();
                        if (l10n) {
                            if (!thisLayout.do.hasOwnProperty('10n')) {
                                thisLayout.do.l10n = {};
                            }
                            thisLayout.do.l10n[l10n] = $('#do-l10n-' + currentPosition).val();
                            if (!thisLayout.say.hasOwnProperty('10n')) {
                                thisLayout.say.l10n = {};
                            }
                            thisLayout.say.l10n[l10n] = $('#say-l10n-' + currentPosition).val();
                        }
                        // Save Template
                        self.saveLayout();
                    } else {
                        // Save Question
                        self.saveQuestion(type, questionID);
                    }
                });
                
                if ((type != 'instructions') && (type != 'heatmap')) {
                    // Image Pipe
                    $('#pipe-' + questionID).on('change'+ ns, function() {
                        var value = $(this).val();
                        if (value) {
                            var img;
                            for (var i=0, len=imageOptions.length; i < len; i++) {
                                img = imageOptions[i];
                                if (img.label == value) {
                                    thisQuestion.settings.pipeImage = {
                                        id: img.id,
                                        region: img.region
                                    };
                                    break;
                                }
                            }
                            // Remove any Image
                            self.deleteImage(questionID);
                        } else {
                            delete thisQuestion.settings.pipeImage;
                        }
                        self.saveQuestion(type, questionID);
                    });
                }
            };
            inputEvents();
            
            if (type != 'instructions') {
                if (load) {
                    // Image to Load?
                    var file = thisQuestion.file;
                    if (file) {
                        loadImage(S3.Ap.concat('/default/download/' + file), function(img) {
                            var options = {
                                canvas: true,
                                maxHeight: 80,
                                maxWidth: 80
                            },
                            preview = loadImage.scale(img, options);
                            // Place Preview on the page
                            $('#preview-' + questionID).removeClass('preview-empty')
                                                       .empty()
                                                       .append(preview);
                            return img;
                        }, {}); // Empty Options
                    }
                }
                $('#image-delete-' + questionID).on('click' + ns, function() {
                    self.deleteImage(questionID);
                });
                // Image Upload
                $('#image-' + questionID).fileupload({
                    dataType: 'json',
                    dropZone: $('#preview-' + questionID + ', #image-' + questionID),
                    maxNumberOfFiles: 1,
                    url: S3.Ap.concat('/dc/question/') + questionID + '/image_upload.json',
                    add: function(e, data) {
                        if (e.isDefaultPrevented()) {
                            return false;
                        }

                        if (data.autoUpload || (data.autoUpload !== false && $(this).fileupload('option', 'autoUpload'))) {
                            data.process().done(function() {
                                data.submit();

                                // Create Preview Image
                                var file = data.files[0];
                                // @ToDo: Check file.size &/or file.type are valid?
                                loadImage(file, function(img) {
                                    var options = {
                                        canvas: true,
                                        maxHeight: 80,
                                        maxWidth: 80
                                    },
                                    preview = loadImage.scale(img, options);
                                    // Place Preview on the page
                                    $('#preview-' + questionID).removeClass('preview-empty')
                                                               .empty()
                                                               .append(preview);

                                    var type = thisQuestion.type;
                                    if (type != 13) {
                                        // Ensure that we aren't trying to Pipe at the same time
                                        if (thisQuestion.settings.hasOwnProperty('pipeImage')) {
                                            $('#pipe-' + questionID).val('')
                                                                    .trigger('change');
                                        }

                                        // Check if we should add to ImageOptions
                                        // (not done for Heatmaps, except for regions)
                                        var img,
                                            found = false;
                                        for (img in imageOptions) {
                                            if (img.id == questionID){
                                                found = true;
                                            }
                                        }
                                        if (!found) {
                                            // Read the questionNumber (can't trust original as it may have changed)
                                            var questionNumber = $('#question-' + questionID).data('number');
                                            var label = 'Q' + questionNumber + ' ' + typesToText[type];
                                            // Add to imageOptions
                                            imageOptions.push({
                                                label: label,
                                                id: questionID
                                            });
                                        }

                                        // Update the Pipe Options HTML for each question
                                        var item,
                                            thatQuestionID,
                                            thatQuestion,
                                            questions = self.data.questions,
                                            layout = self.data.layout;
                                        for (var position=1; position <= Object.keys(layout).length; position++) {
                                            item = layout[position];
                                            if (item.type == 'question') {
                                                thatQuestionID = item.id;
                                                thatQuestion = questions[thatQuestionID];
                                                if (thatQuestion.type != 13) {
                                                    $('#pipe-' + thatQuestionID).empty()
                                                                                .append(self.pipeOptionsHtml(thatQuestionID));
                                                }
                                            }
                                        }
                                    }

                                    return img;

                                }, {}); // Empty Options
                                
                            });
                        }
                    }
                });
            }
            
            $(trash).on('click' + ns, function(/* event */) {
                // Delete the Question
                self.deleteQuestion(type, questionID, this);
            });

            switch(type) {

                case 'instructions':
                    // Nothing needed here
                    break;

                case 'text':
                    // Nothing needed here
                    break;

                case 'number':
                    // Field Validation for Minimum/Maximum
                    //  Integers only
                    //  Max must be above Min
                    $('#answer-' + questionID).validate({
                        rules: {
                            min: {
                                required: false,
                                digits: true,
                                lessThanMax: true
                            },
                            max: {
                                required: false,
                                digits: true,
                                greaterThanMin: true
                            }
                        },
                        messages: {
                            // @ToDo: i18n
                            min: {
                                digits: 'Only integers allowed'
                            },
                            max: {
                                digits: 'Only integers allowed'
                            }
                        },
                        errorClass: 'req',
                        focusCleanup: true
                    });
                    break;

                case 'multichoice':
                    var multipleCheckbox = $('#multiple-' + questionID),
                        multipleCount = $('#multiple-count-' + questionID),
                        multichoiceEvents = function() {
                        // Options
                        $('.choice-' + questionID).next().off('click' + ns)
                                                         .on('click' + ns, function() {
                            if ($('.choice-' + questionID).length > 1) {
                                // Remove Option
                                $(this).parent().remove();
                                // Check if we now have fewer options than multipleCount
                                var multiple = parseInt(multipleCount.html()),
                                    optionsCount = $('.choice-' + questionID).length;
                                if ($('#other-' + questionID).prop('checked')) {
                                    optionsCount++;
                                }
                                if (multiple > optionsCount) {
                                    multipleCount.html(optionsCount);
                                    if (optionsCount == 1) {
                                        multipleCheckbox.prop('checked', false);
                                    }
                                }
                                self.saveQuestion(type, questionID);
                            } else {
                                // Remove value
                                $(this).prev().val('');
                            }
                        });
                        $('.choice-' + questionID).next().next().off('click' + ns)
                                                                .on('click' + ns, function() {
                            // Add Option
                            $(this).parent().after(newChoice);
                            // Add Events
                            inputEvents();
                            multichoiceEvents();
                        });
                        // Other field
                        $('#other-' + questionID).on('change' + ns, function(){
                            if ($(this).prop('checked')) {
                                $('#other-label-' + questionID).prop('disabled', false);
                            } else {
                                $('#other-label-' + questionID).prop('disabled', true);
                                // Check if we now have fewer options than multipleCount
                                var multiple = parseInt(multipleCount.html()),
                                    optionsCount = $('.choice-' + questionID).length;
                                if (multiple > optionsCount) {
                                    multipleCount.html(optionsCount);
                                    if (optionsCount == 1) {
                                        multipleCheckbox.prop('checked', false);
                                    }
                                }
                            }
                        });
                        // Multiple
                        multipleCheckbox.on('change' + ns, function() {
                            if (multipleCheckbox.prop('checked')) {
                                // Check if we have more than 1 option
                                var multiple = parseInt(multipleCount.html()),
                                    optionsCount = $('.choice-' + questionID).length;
                                if ($('#other-' + questionID).prop('checked')) {
                                    optionsCount++;
                                }
                                if (optionsCount > 1) {
                                    // Doesn't make sense unless value is at least 2
                                    multipleCount.html(2);
                                } else {
                                    multipleCheckbox.prop('checked', false);
                                }
                            } else {
                                // Reset to 1
                                multipleCount.html(1);
                            }
                            self.saveQuestion(type, questionID);
                        });
                        multipleCount.prev().on('click' + ns, function() {
                            if (multipleCheckbox.prop('checked')) {
                                var multiple = parseInt(multipleCount.html());
                                if (multiple > 2) {
                                    multipleCount.html(multiple - 1);
                                    self.saveQuestion(type, questionID);
                                } else if (multiple == 2) {
                                    multipleCount.html(1);
                                    multipleCheckbox.prop('checked', false);
                                    self.saveQuestion(type, questionID);
                                }
                            }
                        });
                        multipleCount.next().on('click' + ns, function() {
                            if (multipleCheckbox.prop('checked')) {
                                var multiple = parseInt(multipleCount.html()),
                                    optionsCount = $('.choice-' + questionID).length;
                                if ($('#other-' + questionID).prop('checked')) {
                                    optionsCount++;
                                }
                                if (multiple < optionsCount) {
                                    multipleCount.html(multiple + 1);
                                    self.saveQuestion(type, questionID);
                                }
                            }
                        });
                    };
                    multichoiceEvents();
                    break;

                case 'likert':
                    // Display options when scale selected
                    $('#scale-' + questionID).on('change' + ns, function() {
                        var $this = $(this),
                            scale = $this.val();
                        if (scale) {
                            var options = likertOptions[scale],
                                scaleOptions = '';
                            for (var i=0, len = options.length; i < len; i++) {
                                scaleOptions += '<li>' + options[i] + '</li>';
                            }
                            var scaleDisplay = '<ul>' + scaleOptions + '</ul>';
                            $this.parent().next().empty()
                                                 .append(scaleDisplay);
                        } else {
                            // Remove old display
                            $this.parent().next().empty();
                        }
                    });
                    break;

                case 'heatmap':
                    break;
            }

            // Run Foundation JS on new Item
            //- needed for Tabs
            if (type == 'instructions') {
                $('#instruction-' + position).foundation();
            } else {
                $('#question-' + questionID).foundation();
            }

        },

        /**
          * Delete a Question
          */
        deleteQuestion: function(type, questionID, deleteBtn) {

            var currentPage,
                currentPosition,
                questionNumber;

            if (type == 'instructions') {
                // Read the position (can't trust original as it may have changed)
                currentPosition = parseInt($(deleteBtn).closest('.dl-item').attr('id').split('-')[1]);
                // Read the current page
                currentPage = $('#instruction-' + currentPosition).data('page');
            } else {
                // Question

                // Read the questionNumber (can't trust original as it may have changed)
                questionNumber = $('#question-' + questionID).data('number');
                // Read the position (can't trust original as it may have changed)
                currentPosition = questionNumbers[questionNumber];
                // Read the current page
                currentPage = $('#question-' + questionID).data('page');
            }

            // Update this pageElements
            pageElements[currentPage]--;
            // Update visual elements
            $('#section-break-' + pages[currentPage] + ' > span').html('PAGE ' + currentPage + ' (' + pageElements[currentPage] + ' ELEMENTS)');

            // Update subsequent pages
            for (var i=currentPage + 1, len=Object.keys(pages).length; i <= len; i++) {
                pages[i]--; // newPosition
            }

            // Update layout & all subsequent items in it
            var item,
                $item,
                oldPosition,
                thisQuestionID,
                oldQuestionNumber,
                newQuestionNumber,
                oldHref,
                newHref,
                layout = this.data.layout;
            var layoutLength = Object.keys(layout).length;
            for (var i=currentPosition; i < layoutLength; i++) {
                oldPosition = i + 1;
                //newPosition = i;
                item = layout[oldPosition];
                // Move item to it's new position in the layout
                layout[i] = item;
                if (item.type == 'break') {
                    // Update ID
                    $('#section-break-' + oldPosition).attr('id', 'section-break-' + i);
                } else {
                    if (item.type == 'question') {
                        thisQuestionID = item.id;
                        $item = $('#question-' + thisQuestionID);
                        oldQuestionNumber = $item.data('number');
                        if (type == 'instructions') {
                            // Not a Question deleted, so just need to update position
                            //newQuestionNumber = oldQuestionNumber;
                            // Update questionNumbers
                            questionNumbers[oldQuestionNumber] = i;
                        } else {
                            // Question deleted so need to update both numbers & positions

                            // Update questionNumber
                            newQuestionNumber = oldQuestionNumber - 1;
                            $item.data('number', newQuestionNumber);
                            // Update visual elements
                            $('#qlabel-' + thisQuestionID).html('Q' + newQuestionNumber);
                            $('#qlabel-l10n-' + thisQuestionID).html('Q' + newQuestionNumber);
                            // Update questionNumbers
                            questionNumbers[newQuestionNumber] = i;
                        }
                    } else {
                        // Instructions
                        // Update IDs
                        $('#instruction-' + oldPosition).attr('id', 'instruction-' + i);
                        $item = $('#instruction-' + i);
                        $('#do-' + oldPosition).attr('id', 'do-' + i);
                        $('#say-' + oldPosition).attr('id', 'say-' + i);
                        $('#do-l10n-' + oldPosition).attr('id', 'do-l10n-' + i);
                        $('#say-l10n-' + oldPosition).attr('id', 'say-l10n-' + i);
                    }
                    // Update Tab contents
                    $('#edit-' + oldPosition).attr('id', 'edit-' + i);
                    $('#logic-' + oldPosition).attr('id', 'logic-' + i);
                    $('#translation-' + oldPosition).attr('id', 'translation-' + i);
                    // Update links to Tabs
                    $item.find('li.tab-title > a').each(function() {
                        var $this = $(this);
                        oldHref = $this.attr('href');
                        newHref = oldHref.split('-')[0];
                        newHref = newHref.substring(1, newHref.length);
                        $this.attr('href', '#' + newHref + '-' + i);
                    });
                }
            }

            // Remove final item from oldPosition in layout
            delete layout[layoutLength];

            if (type != 'instructions') {
                // Remove final questionNumber from questionNumbers
                delete questionNumbers[oldQuestionNumber];
            }

            // Save Layout
            this.saveLayout();

            // Remove from DOM
            if (type == 'instructions') {
                $('#instruction-' + currentPosition).remove();
            } else {
                $('#question-' + questionID).remove();
            }

            // Update droppable ID
            $('#survey-droppable-' + (layoutLength + 1)).attr('id', 'survey-droppable-' + layoutLength);

            if (type != 'instructions') {
                // Delete Question from Server
                var ajaxURL = S3.Ap.concat('/dc/question/') + questionID + '/delete.json';
                this.ajaxMethod({
                    url: ajaxURL,
                    type: 'POST',
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
            }
        },

        /**
          * Produce the Options HTML for the Pipe dropdown
          */
        pipeOptionsHtml: function(questionID, load) {
        
            var img,
                pipeImage,
                thisQuestion = this.data.questions[questionID],
                optionsHtml = '<option value="">select question</option>';
            if (thisQuestion && thisQuestion.settings && thisQuestion.settings.pipeImage) {
                pipeImage = thisQuestion.settings.pipeImage;
            }
            for (var i=0, len=imageOptions.length; i < len; i++) {
                img = imageOptions[i];
                if (img.id != questionID) {
                    if (pipeImage && pipeImage.id == img.id && pipeImage.region == img.region) {
                        optionsHtml += '<option selected>' + img.label + '</option>';
                    } else {
                        optionsHtml += '<option>' + img.label + '</option>';
                    }
                }
            }
            return optionsHtml;
        },

        /**
          * Produce the Options HTML for the Logic Questions dropdown
          */
        logicOptionsHtml: function(questionID, load) {

            var optionsHtml = '<option value="">select question</option>';
            // @ToDo: Complete this: Build list of all Questions which are multichoice, likert or number

            return optionsHtml;
        },


        /**
          * Delete an Image
          */
        deleteImage: function(questionID) {
            var self = this,
                preview = $('#preview-' + questionID);
            if (!preview.hasClass('preview-empty')) {
                // Remove Image from Server
                var ajaxURL = S3.Ap.concat('/dc/question/') + questionID + '/image_delete.json';
                this.ajaxMethod({
                    url: ajaxURL,
                    type: 'POST',
                    dataType: 'json',
                    success: function(/* data */) {
                        // Remove Image from Preview
                        preview.empty()
                               .addClass('preview-empty');
                        // Remove entry from imageOptions
                        var img,
                            oldOptions = imageOptions;
                        imageOptions = [];
                        for (var i=0, len=oldOptions.length; i < len; i++) {
                            img = oldOptions[i];
                            if (img.id != questionID) {
                                imageOptions.push(img);
                            }
                        }
                        // Update the Pipe Options HTML for each question
                        var item,
                            thisQuestionID,
                            thisQuestion,
                            questions = self.data.questions,
                            layout = self.data.layout;
                        for (var position=1; position <= Object.keys(layout).length; position++) {
                            item = layout[position];
                            if (item.type == 'question') {
                                thisQuestionID = item.id;
                                thisQuestion = questions[thisQuestionID];
                                if (thisQuestion.type != 13) {
                                    $('#pipe-' + thisQuestionID).empty()
                                                                .append(self.pipeOptionsHtml(thisQuestionID));
                                }
                            }
                        }
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
          * Add a new Section Break
          */
        addSectionBreak: function(position, page, load) {
            page++;
            pages[page] = position;
            pageElements[page] = 0;
            var delete_btn;
            if (position) {
                delete_btn = '<i class="ucce ucce-delete-page"> </i>';
            } else {
                // 1st section break: not deletable
                delete_btn = '';
            }
            var sectionBreak = '<div class="row"><div class="section-break medium-11 columns" id="section-break-' + position + '" data-page="' + page + '"><span>PAGE ' + page + ' (0 ELEMENTS)</span></div><div class="medium-1 columns">' + delete_btn + '<i class="ucce ucce-down-alt"> </i></div></div>';
            if (position) {
                // Place before droppable
                $('#survey-droppable-' + position).before(sectionBreak);
                // Update the page & position of the droppable
                var newPosition = position + 1;
                $('#survey-droppable-' + position).data('page', page)
                                                  .attr('id', 'survey-droppable-' + newPosition);
                // @ToDo: Roll-up previous sections
                if (!load) {
                    // Update Data
                    this.data.layout[position] = {type: 'break'};
                    // Save to Server
                    this.saveLayout();
                }
                // Events
                var self = this,
                    ns = this.eventNamespace;
                $('#section-break-' + position).next().children('.ucce-delete-page').on('click' + ns, function(/* event */){
                    // Delete this section-break

                    // Read the position (can't trust original as it may have changed)
                    var currentPosition = parseInt($(this).parent().prev().attr('id').split('-')[2]);

                    self.deleteSectionBreak(currentPosition);

                });
                //$('#section-break-' + position).next().children('.ucce-down-alt').on('click' + ns, function(/* event */){
                    // @ToDo: Unroll this section & rollup others
                //});
            } else {
                // 1st section break
                $(this.element).parent().append(sectionBreak);
            }
        },

        /**
          * Add a new Section Break
          */
        deleteSectionBreak: function(currentPosition) {
            // Read the current page
            var currentPage = $('#section-break-' + currentPosition).data('page');

            var currentPageElements = pageElements[currentPage];
            if (currentPageElements) {
                // Update elements on previous section-break
                var previousPage = currentPage - 1;
                pageElements[previousPage] += currentPageElements;
                var previousPagePosition = pages[previousPage];
                $('#section-break-' + previousPagePosition + ' > span').html('PAGE ' + previousPage + ' (' + pageElements[previousPage] + ' ELEMENTS)');
            }

            // Update subsequent pages & pageElements
            var pagesLength = Object.keys(pages).length;
            for (var i=currentPage; i < pagesLength; i++) {
                pages[i] = pages[i + 1] - 1; // newPosition
                pageElements[i] = pageElements[i + 1];
            }
            delete pages[pagesLength];
            delete pageElements[pagesLength];

            // Update layout & all subsequent items in it
            var layout = this.data.layout,
                layoutLength = Object.keys(layout).length;
            if (currentPosition != layoutLength) {
                var item,
                    thisPage,
                    oldPosition,
                    oldHref,
                    newHref,
                    questionNumber,
                    $item;
                for (var i=currentPosition; i < layoutLength; i++) {
                    oldPosition = i + 1;
                    //newPosition = i;
                    item = layout[oldPosition];
                    // Move item to it's new position in the layout
                    layout[i] = item;
                    if (item.type == 'break') {
                        // Read Page
                        thisPage = $('#section-break-' + oldPosition).data('page') - 1;
                        // Update Page
                        $('#section-break-' + oldPosition).data('page', thisPage);
                        // Update visual elements
                        $('#section-break-' + oldPosition + ' > span').html('PAGE ' + thisPage + ' (' + pageElements[thisPage] + ' ELEMENTS)');
                        // Update ID
                        $('#section-break-' + oldPosition).attr('id', 'section-break-' + i);
                    } else {
                        if (item.type == 'question') {
                            // Update questionNumbers
                            $item = $('#question-' + item.id);
                            questionNumber = $item.data('number');
                            questionNumbers[questionNumber] = i;
                        } else {
                            // Instructions
                            // Update IDs
                            $('#instruction-' + oldPosition).attr('id', 'instruction-' + i);
                            $item = $('#instruction-' + i);
                            $('#do-' + oldPosition).attr('id', 'do-' + i);
                            $('#say-' + oldPosition).attr('id', 'say-' + i);
                            $('#do-l10n-' + oldPosition).attr('id', 'do-' + i);
                            $('#say-l10n-' + oldPosition).attr('id', 'say-' + i);
                        }
                        // Update Tab contents
                        $('#edit-' + oldPosition).attr('id', 'edit-' + i);
                        $('#logic-' + oldPosition).attr('id', 'logic-' + i);
                        $('#translation-' + oldPosition).attr('id', 'translation-' + i);
                        // Update links to Tabs
                        $item.find('li.tab-title > a').each(function() {
                            var $this = $(this);
                            oldHref = $this.attr('href');
                            newHref = oldHref.split('-')[0];
                            newHref = newHref.substring(1, newHref.length);
                            $this.attr('href', '#' + newHref + '-' + i);
                        });
                    }
                }
            }
            // Remove final item from oldPosition in layout
            delete layout[layoutLength];

            // Save Layout
            this.saveLayout();
            // Remove from DOM
            $('#section-break-' + currentPosition).parent().remove();
            // Update droppable ID
            $('#survey-droppable-' + (layoutLength + 1)).data('page', pagesLength - 1)
                                                        .attr('id', 'survey-droppable-' + layoutLength);
        },

        /**
          * Add a new Droppable section into the given position
          * - only done once currently
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
                        // Read the position (can't trust original as it may have changed)
                        currentPosition = parseInt(this.id.split('-')[2]),
                        currentPage = $(this).data('page');
                    if (type == 'break') {
                        self.addSectionBreak(currentPosition, currentPage);
                    } else {
                        self.addQuestion(currentPosition, currentPage, type);
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

            var file,
                item,
                page = 1,
                questionID,
                questionNumber = 0,
                thisQuestion,
                regions,
                base_label,
                label,
                questions = this.data.questions,
                layoutLength = Object.keys(layout).length;

            // Loop through layout to build the list of Images
            // - this requires the Question Numbers too
            for (var position=1; position <= layoutLength; position++) {
                item = layout[position];
                if (item.type == 'break') {
                    // Skip
                } else if (item.type == 'instructions') {
                    // Skip
                } else {
                    // Question
                    questionNumber++
                    questionNumbers[questionNumber] = position;

                    questionID = item.id,
                    thisQuestion = questions[questionID];
                    if (thisQuestion.file) {
                        if (thisQuestion.type == 13) {
                            // Heatmap
                            regions = thisQuestion.settings.regions;
                            if (regions) {
                                base_label = 'Q' + questionNumber + ' Heatmap; ';
                                for (var i=0, len=regions.length; i < len; i++) {
                                    label = base_label + '\'' + regions[i].label + '\'';
                                    imageOptions.push({
                                        label: label,
                                        id: questionID,
                                        region: i
                                    });
                                }
                            }
                        } else {
                            label = 'Q' + questionNumber + ' ' + typesToText[thisQuestion.type];
                            imageOptions.push({
                                label: label,
                                id: questionID
                            });
                        }
                    }
                }
            }

            // Then loop through layout to add items to page
            for (var position=1; position <= layoutLength; position++) {
                item = layout[position];
                if (item.type == 'break') {
                    this.addSectionBreak(position, page, true);
                    page++;
                } else if (item.type == 'instructions') {
                    this.addQuestion(position, page, 'instructions', true);
                } else {
                    // Question
                    questionID = item.id;
                    this.addQuestion(position, page, typesToText[questions[questionID].type], questionID);
                }
            }
        },

        /**
         * Redraw widget contents
         */
        refresh: function() {
            //this._unbindEvents();
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
                settings = {},
                data = {
                    name: name,
                    mandatory: $('#mandatory-' + questionID).prop('checked')
                };

            var pipeImage = this.data.questions[questionID].settings.pipeImage;
            if (pipeImage) {
                settings.pipeImage = pipeImage;
            }

            switch(type) {

                case 'text':
                    // Nothing needed here
                    break;
                case 'number':
                    var min,
                        max;
                    if (!($('#min-' + questionID).hasClass('req'))) {
                        min = $('#min-' + questionID).val();
                        if (min) {
                            min = parseInt(min);
                        }
                    } else {
                        min = null;
                    }
                    if (!($('#max-' + questionID).hasClass('req'))) {
                        max = $('#max-' + questionID).val();
                        if (max) {
                            max = parseInt(max);
                        }
                    } else {
                        max = null;
                    }
                    settings.requires = {
                        isIntInRange: {
                            min: min,
                            max: max
                        }
                    };
                    break;
                case 'multichoice':
                    var options = [];
                    $('.choice-' + questionID).each(function() {
                        options.push($(this).val());
                    });
                    data.options = options;
                    if ($('#other-' + questionID).prop('checked')) {
                        settings.other = $('#other-label-' + questionID).val();
                    } else {
                        settings.other = null;
                    }
                    if ($('#multiple-' + questionID).prop('checked')) {
                        settings.multiple = parseInt($('#multiple-count-' + questionID).html());
                    } else {
                        settings.multiple = 1;
                    }
                    break;
                case 'likert':
                    var scale = $('#scale-' + questionID).val();
                    if (scale) {
                        data.options = likertOptions[scale];
                        settings.scale = scale;
                    } else {
                        data.options = [];
                        settings.scale = null;
                    }
                    break;
                case 'heatmap':
                    break;

            }

            data.settings = settings;

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
         * Ajax-update the Template's Layout
         */
        saveLayout: function() {

            var ajaxURL = S3.Ap.concat('/dc/template/') + this.recordID + '/update_json.json';

            // Encode this.data as JSON and write into real input
            //this._serialize();

            this.ajaxMethod({
                url: ajaxURL,
                type: 'POST',
                // $.searchS3 defaults to processData: false
                //data: {layout: this.data.layout},
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
         *
        _serialize: function() {

            var json = JSON.stringify(this.data);
            $(this.element).val(json);
            return json;

        },*/

        /**
         * Parse the JSON from real input into this.data
         *
         * @returns {object} this.data
         */
        _deserialize: function() {

            var value = $(this.element).val() || '{}';
            this.data = JSON.parse(value);
            return this.data;

        }

        /**
         * Bind event handlers (after refresh)
         *
         * (unused)
         *
        _bindEvents: function() {

            var self = this,
                ns = this.eventNamespace;

            var selector = '#' + this.fieldname;

            this.inputFields.bind('change' + ns, function() {
                self._collectData(this);
            });

        }, */

        /**
         * Unbind events (before refresh)
         *
        _unbindEvents: function() {

            var ns = this.eventNamespace,
                el = $(this.element);

            //this.inputFields.unbind(ns);
            el.unbind(ns);

            return true;
        }*/

    });
});
