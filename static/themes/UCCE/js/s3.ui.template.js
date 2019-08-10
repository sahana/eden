/*
 * Survey Editor Widget
 */
(function(factory) {
  'use strict';
  // Browser globals (not AMD or Node):
  factory(window.jQuery, window.loadImage);
})(function($, loadImage) {
  'use strict';
    'use strict';
    var surveyID = 0,
        images = {}, // Store questionID -> label for images to pipe (Questions with Images & Heatmap regions)
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
                thisQuestion,
                questionNumber,
                editTab,
                mandatory,
                imageHtml,
                newChoice,
                formElements,
                trash;

            if (type == 'instructions') {
                question = '<div class="thumbnail dl-item" id="instruction-' + position + '" data-page="' + page + '"><div class="card-header"><div class="fleft">Edit</div> <div class="fleft">Display Logic</div> <div class="fleft">Translation</div> <div class="edit-bar fright"><a><i class="fa fa-copy"> </i></a><a><i class="fa fa-trash"> </i></a><i class="fa fa-arrows-v"> </i></div></div>';
            } else {
                thisQuestion = this.data.questions[questionID];
                questionNumber = Object.keys(questionNumbers).length + 1;
                questionNumbers[questionNumber] = position;
                question = '<div class="thumbnail dl-item" id="question-' + questionID + '" data-page="' + page + '" data-number="' + questionNumber + '"><div class="card-header"><div class="fleft">Edit</div> <div class="fleft">Display Logic</div> <div class="fleft">Translation</div> <div class="edit-bar fright"><a><i class="fa fa-copy"> </i></a><a><i class="fa fa-trash"> </i></a><i class="fa fa-arrows-v"> </i></div></div>';
                var checked = '';
                if (load) {
                    if (thisQuestion.mandatory) {
                        checked = ' checked';
                    }
                }
                mandatory = '<div class="row"><input id="mandatory-' + questionID + '" type="checkbox" ' + checked + ' class="fleft"><label>Make question mandatory</label></div>';
                if (type != 'heatmap') {
                    var imageOptions = ''; // @ToDo: Read <option>s from images dict
                    imageHtml = '<div class="row"><label>Add graphic</label><span id="preview-' + questionID + '" class="preview-empty fleft"></span><label for="image-' + questionID + '" class="button tiny fleft">Upload image</label><input id="image-' + questionID + '" name="file" type="file" accept="image/png, image/jpeg" class="show-for-sr"><label class="fleft">or pipe question image:</label><select class="fleft"><option value="">select question</option>' + imageOptions + '</select><a id="image-delete-' + questionID + '">Delete</a></div>';
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
                    trash = '#instruction-' + position + ' .fa-trash';
                    break;

                case 'text':
                    var name = '';
                    if (load) {
                        name = thisQuestion.name;
                    }
                    editTab = '<div class="media"><h2>Text box</h2><div class="row"><label id="qlabel-' + questionID + '" class="fleft">Q' + questionNumber + '</label><input id="name-' + questionID + '" type="text" size=100 placeholder="type question" value="' + name + '"></div>' + mandatory + imageHtml;
                    formElements = '#question-' + questionID + ' input, #question-' + questionID + ' select';
                    trash = '#question-' + questionID + ' .fa-trash';
                    break;

                case 'number':
                    var name = '',
                        min = '',
                        max = '';
                    if (load) {
                        name = thisQuestion.name;
                        var settings = thisQuestion.settings || {},
                            requires = settings.requires || {},
                            isIntInRange = requires.isIntInRange;
                        if (isIntInRange) {
                            min = isIntInRange.min || '';
                            max = isIntInRange.max || '';
                        }
                    }
                    var answer = '<div class="row"><h2>Answer</h2><form id="answer-' + questionID + '"><label>Minimum:</label><input id="min-' + questionID + '" name="min" type="number" value="' + min + '"><label>Maximum:</label><input id="max-' + questionID + '" name="max" type="number" value="' + max + '"></form></div>';
                    editTab = '<div class="media"><h2>Number question</h2><div class="row"><label id="qlabel-' + questionID + '" class="fleft">Q' + questionNumber + '</label><input id="name-' + questionID + '"type="text" size=100 placeholder="type question" value="' + name + '"></div>' + mandatory + imageHtml + answer;
                    formElements = '#question-' + questionID + ' input, #question-' + questionID + ' select';
                    trash = '#question-' + questionID + ' .fa-trash';
                    break;

                case 'multichoice':
                    newChoice = '<div class="row"><input class="choice-' + questionID + '" type="text" placeholder="Enter an answer choice"><i class="fa fa-minus-circle"> </i><i class="fa fa-plus-circle"> </i></div>';
                    // @ToDo: Grey the multiple -+ options if they cannot do anything
                    var name = '',
                        choices = newChoice,
                        other = '',
                        other_disabled = ' disabled',
                        other_label = '',
                        multiple = 1,
                        multiChecked = '';
                    if (load) {
                        name = thisQuestion.name;
                        var options = thisQuestion.options || [],
                            lenOptions = options.length;
                        if (lenOptions) {
                            choices = '';
                            for (var i=0; i < lenOptions; i++) {
                                choices += '<div class="row"><input class="choice-' + questionID + '" type="text" placeholder="Enter an answer choice" value="' + options[i] + '"><i class="fa fa-minus-circle"> </i><i class="fa fa-plus-circle"> </i></div>';
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
                    var answer = '<div class="row"><h2>Answer</h2><label>Choices</label></div>' + choices +
                                 '<div class="row"><input id="other-' + questionID + '" type="checkbox"' + other + '><label>Add \'other field\'</label></div>' + 
                                 '<div class="row"><label class="fleft">Field label</label><input id="other-label-' + questionID + '" type="text" placeholder="Other (please specify)" value="' + other_label + '"' + other_disabled + '></div>' + 
                                 '<div class="row"><input id="multiple-' + questionID + '" type="checkbox"' + multiChecked + '><label>Allow multiple responses</label></div>' +
                                 '<div class="row"><label class="fleft">Maximum No. of responses:</label><i class="fa fa-minus-circle"> </i> <span id="multiple-count-' + questionID + '">' + multiple + '</span> <i class="fa fa-plus-circle"> </i></div>';
                    editTab = '<div class="media"><h2>Multiple choice question</h2><div class="row"><label id="qlabel-' + questionID + '" class="fleft">Q' + questionNumber + '</label><input id="name-' + questionID + '"type="text" size=100 placeholder="type question" value="' + name + '"></div>' + mandatory + imageHtml + answer;
                    formElements = '#question-' + questionID + ' input, #question-' + questionID + ' select';
                    trash = '#question-' + questionID + ' .fa-trash';
                    break;

                case 'likert':
                    var name = '',
                        displayOptions = '',
                        scales = [
                            '<option value="1">Agreement (Disagree - Agree)</option>',
                            '<option value="2">Satisfaction (Smiley scale)</option>',
                            '<option value="3">Satisfaction (Dissatisfied - Satisfied)</option>',
                            '<option value="4">Pain scale (3 point)</option>'
                            ];
                    if (load) {
                        name = thisQuestion.name;
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
                    var answer = '<div class="row"><h2>Answer</h2><label>Choices</label><select id="scale-' + questionID + '"><option value="">Please choose scale</option>' + scaleOptions + '</select></div><div class="row">' + displayOptions + '</div>';
                    editTab = '<div class="media"><h2>Likert-scale</h2><div class="row"><label id="qlabel-' + questionID + '" class="fleft">Q' + questionNumber + '</label><input id="name-' + questionID + '"type="text" size=100 placeholder="type question" value="' + name + '"></div>' + mandatory + imageHtml + answer;
                    formElements = '#question-' + questionID + ' input, #question-' + questionID + ' select';
                    trash = '#question-' + questionID + ' .fa-trash';
                    break;

                case 'heatmap':
                    var name = '';
                    if (load) {
                        name = thisQuestion.name;
                    }
                    var imageRow = '<div class="row"><h2>Image</h2><input type="file" accept="image/png, image/jpeg" class="fleft"><h3>Number of clicks allowed:</h3><i class="fa fa-minus-circle"> </i> 1 <i class="fa fa-plus-circle"> </i><h3>Tap/click regions:</h3><a class="button tiny">Add region</a><input id="region-' + position + '-1" type="text" placeholder="enter label" disabled></div>';
                    editTab = '<div class="media"><h2>Heatmap</h2><div class="row"><label id="qlabel-' + questionID + '" class="fleft">Q' + questionNumber + '</label><input id="name-' + questionID + '"type="text" size=100 placeholder="type question" value="' + name + '"></div>' + mandatory + imageRow;
                    formElements = '#question-' + questionID + ' input';
                    trash = '#question-' + questionID + ' .fa-trash';
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

            // Event Handlers
            var ns = this.eventNamespace,
                self = this;

            var inputEvents = function() {
                $(formElements).off('change' + ns)
                               .on('change' + ns, function(/* event */) {
                    // If form elements change, then Save
                    if (type == 'instructions') {
                        // Can't trust original position as it may have changed
                        var currentPosition = parseInt(this.id.split('-')[1]);
                        // Update Data
                        self.data.layout[currentPosition].do.text = $('#do-' + currentPosition).val();
                        self.data.layout[currentPosition].say.text = $('#say-' + currentPosition).val();
                        // Save Template
                        self.save();
                    } else {
                        // Save Question
                        self.saveQuestion(type, questionID);
                    }
                });
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
                    // Remove Image from Server
                    var ajaxURL = S3.Ap.concat('/dc/question/') + questionID + '/image_delete.json';
                    self.ajaxMethod({
                        url: ajaxURL,
                        type: 'POST',
                        dataType: 'json',
                        success: function(/* data */) {
                            // Remove Image from Preview
                            $('#preview-' + questionID).empty()
                                                       .addClass('preview-empty');
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
                                    return img;
                                }, {}); // Empty Options
                                
                            });
                        }
                    }
                });
            }
            
            $(trash).on('click' + ns, function(/* event */) {
                // Delete the Question
                self.deleteQuestion(type, questionID);
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
        },

        /**
          * Delete a Question
          */
        deleteQuestion: function(type, questionID) {

            var currentPage,
                currentPosition,
                questionNumber;

            if (type == 'instructions') {
                // Read the position (can't trust original as it may have changed)
                currentPosition = parseInt($(this).closest('.dl-item').attr('id').split('-')[1]);
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
                oldPosition,
                thisQuestionID,
                oldQuestionNumber,
                newQuestionNumber,
                layout = this.data.layout;
            var layoutLength = Object.keys(layout).length;
            for (var i=currentPosition; i < layoutLength; i++) {
                oldPosition = i + 1;
                //newPosition = i;
                item = layout[oldPosition];
                // Move item to it's new position in the layout
                layout[i] = item;
                if (item.type == 'question') {
                    thisQuestionID = item.id;
                    oldQuestionNumber = $('#question-' + thisQuestionID).data('number');
                    if (type == 'instructions') {
                        // Not a Question deleted, so just need to update position
                        //newQuestionNumber = oldQuestionNumber;
                        // Update questionNumbers
                        questionNumbers[oldQuestionNumber] = i;
                    } else {
                        // Question deleted so need to update both numbers & positions

                        // Update questionNumber
                        newQuestionNumber = oldQuestionNumber - 1;
                        $('#question-' + thisQuestionID).data('number', newQuestionNumber);
                        // Update visual element
                        $('#qlabel-' + thisQuestionID).html('Q' + newQuestionNumber);
                        // Update questionNumbers
                        questionNumbers[newQuestionNumber] = i;
                    }
                } else {
                    if (item.type == 'break') {
                        // Update ID
                        $('#section-break-' + oldPosition).attr('id', 'section-break-' + i);
                    } else {
                        // Instructions
                        // Update IDs
                        $('#instruction-' + oldPosition).attr('id', 'instruction-' + i);
                        $('#do-' + oldPosition).attr('id', 'do-' + i);
                        $('#say-' + oldPosition).attr('id', 'say-' + i);
                    }
                }
            }

            // Remove final item from oldPosition in layout
            delete layout[layoutLength];

            if (type != 'instructions') {
                // Remove final questionNumber from questionNumbers
                delete questionNumbers[oldQuestionNumber];
            }

            // Save Layout
            this.save();

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
          * Add a new Section Break
          */
        addSectionBreak: function(position, page, load) {
            page++;
            pages[page] = position;
            pageElements[page] = 0;
            var delete_btn;
            if (position) {
                delete_btn = '<i class="fa fa-times-circle"> </i>';
            } else {
                // 1st section break: not deletable
                delete_btn = '';
            }
            var sectionBreak = '<div class="row"><div class="section-break medium-11 columns" id="section-break-' + position + '" data-page="' + page + '"><span>PAGE ' + page + ' (0 ELEMENTS)</span></div><div class="medium-1 columns">' + delete_btn + '<i class="fa fa-chevron-circle-down"> </i></div></div>';
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
                    this.save();
                }
                // Events
                var self = this,
                    ns = this.eventNamespace;
                $('#section-break-' + position).next().children('.fa-times-circle').on('click' + ns, function(/* event */){
                    // Delete this section-break

                    // Read the position (can't trust original as it may have changed)
                    var currentPosition = parseInt($(this).parent().prev().attr('id').split('-')[2]);

                    self.deleteSectionBreak(currentPosition);

                });
                //$('#section-break-' + position).next().children('.fa-chevron-circle-down').on('click' + ns, function(/* event */){
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
                    questionNumber;
                for (var i=currentPosition; i < layoutLength; i++) {
                    oldPosition = i + 1;
                    //newPosition = i;
                    item = layout[oldPosition];
                    // Move item to it's new position in the layout
                    layout[i] = item;
                    if (item.type == 'question') {
                        // Update questionNumbers
                        questionNumber = $('#question-' + item.id).data('number');
                        questionNumbers[questionNumber] = i;
                    } else {
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
                            // Instructions
                            // Update IDs
                            $('#instruction-' + oldPosition).attr('id', 'instruction-' + i);
                            $('#do-' + oldPosition).attr('id', 'do-' + i);
                            $('#say-' + oldPosition).attr('id', 'say-' + i);
                        }
                    }
                }
            }
            // Remove final item from oldPosition in layout
            delete layout[layoutLength];

            // Save Layout
            this.save();
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

            var item,
                page = 1,
                questionID,
                questions = this.data.questions;

            for (var position=1, len=Object.keys(layout).length; position <= len; position++) {
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
                    data.settings = {
                        requires: {
                            isIntInRange: {
                                min: min,
                                max: max
                            }
                        }
                    };
                    break;
                case 'multichoice':
                    var options = [];
                    $('.choice-' + questionID).each(function() {
                        options.push($(this).val());
                    });
                    data.options = options;
                    var settings = {};
                    if ($('#other-' + questionID).prop('checked')) {
                        settings['other'] = $('#other-label-' + questionID).val();
                    } else {
                        settings['other'] = null;
                    }
                    if ($('#multiple-' + questionID).prop('checked')) {
                        settings['multiple'] = parseInt($('#multiple-count-' + questionID).html());
                    } else {
                        settings['multiple'] = 1;
                    }
                    data.settings = settings;
                    break;
                case 'likert':
                    var scale = $('#scale-' + questionID).val();
                    if (scale) {
                        data.options = likertOptions[scale];
                        data.settings = {
                            scale: scale
                        };
                    } else {
                        data.options = [];
                        data.settings = {
                            scale: null
                        };
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
});
