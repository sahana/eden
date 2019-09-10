/*
 * Survey Editor Widget
 */
import { Map, View, Draw, Fill, GeoJSON, getCenter, ImageLayer, Projection, Static, Stroke, Style, VectorLayer, VectorSource } from './ol5.min.js';

(function(factory) {
    'use strict';
    // Use window. for Browser globals (not AMD or Node):
    factory(window.jQuery, window.loadImage, Map, View, Draw, Fill, GeoJSON, getCenter, ImageLayer, Projection, Static, Stroke, Style, VectorLayer, VectorSource);
})(function($, loadImage, Map, View, Draw, Fill, GeoJSON, getCenter, ImageLayer, Projection, Static, Stroke, Style, VectorLayer, VectorSource) {
    'use strict';
    var surveyID = 0,
        draws = {},   // Draw controls on Maps (indexed by QuestionID)
        maps = {},    // Maps (indexed by QuestionID)
        sources = {}, // VectorSources on Maps (indexed by QuestionID)
        imageFiles = {},   // Store {id: questionID, file: filename}
        imageOptions = [], // Store {label: label, (just held locally)
                           //        id: questionID, {Also on server in settings.pipeImage)
                           //        region: regionID {Also on server in settings.pipeImage)
                           //        } for images that can be piped (Questions with Images & Heatmap regions)
        likertOptions = {
            '1': ['Very appropriate', 'Somewhat appropriate', 'Neither appropriate nor inappropriate', 'Somewhat inappropriate', 'Very inappropriate'],
            '2': ['Extremely confident', 'Very confident', 'Moderately confident', 'Slightly confident', 'Not confident at all'],
            '3': ['Always', 'Often', 'Occasionally', 'Rarely', 'Never'],
            '4': ['Extremely safe', 'Very safe', 'Moderately safe', 'Slightly safe', 'Not safe at all'],
            '5': ['Very satisfied', 'Somewhat satisfied', 'Neither satisfied nor dissatisfied', 'Somewhat dissatisfied', 'Very dissatisfied'],
            // Note that for these 2, images will be seen by the users, not the text:
            '6': [],
            '7': []
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
        },
        truncate = function(str) {
            if (str.length > 53) {
                return str.substring(0, 50) + '...';
            } else {
                return str;
            }
        };

    $.widget('s3.surveyLayout', {

        /**
         * Options
         */
        options: {
            readOnly: false
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
        _init: function(options) {

            var el = $(this.element),
                fieldname = el.attr('id');

            if (!fieldname) {
                fieldname = 'surveyEditor-widget-' + this.id;
            }
            this.fieldname = fieldname;

            this.recordID = el.data('id');
            this.data = null; // Gets populated by _deserialize()

            // Use $.searchS3 if available
            // NB Not really interchangeable as processData defaults differently with each
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

                    if (max == '') {
                        return this.optional(element) || true;
                    } else {
                        return this.optional(element) || (parseFloat(value) <= max);
                    }
                },
                'needs to be lower than Maximum'
            );
            $.validator.addMethod(
                'greaterThanMin', 
                function(value, element) {
                    var questionID = element.id.split('-')[1],
                        min = $('#min-' + questionID).val();

                    if (min == '') {
                        return this.optional(element) || true;
                    } else {
                        return this.optional(element) || (parseFloat(value) >= min);
                    }
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

            var item,
                l10n = this.data.l10n,
                questionNumber,
                layout = this.data.layout,
                questions = this.data.questions,
                readOnly = this.options.readOnly;

            if (load) {
                // Read QuestionNumber created during loadSurvey
                for (var i=1, len=Object.keys(questionNumbers).length; i <= len; i++) {
                    if (position == questionNumbers[i]) {
                        questionNumber = i;
                        break;
                    }
                }
            } else {
                if (type != 'instructions') {
                    // Determine QuestionNumber
                    var questionNumbersLength = Object.keys(questionNumbers).length;
                    if (questionNumbersLength) {
                        if (position > Object.keys(layout).length) {
                            // Final item
                            questionNumber = questionNumbersLength + 1;
                        } else {
                            // Locate the previous Question in the layout
                            var thisItem;
                            for (var p=position - 1; p > 0; p--) {
                                thisItem = layout[p];
                                if (thisItem.type == 'question') {
                                    var previousQuestionID = thisItem.id,
                                        previousQuestionNumber = $('#question-' + previousQuestionID).data('number');
                                    questionNumber = previousQuestionNumber + 1;
                                    break;
                                }
                            }
                            if (!questionNumber) {
                                // Existing Questions must only be later in the layout
                                questionNumber = 1;
                            }
                        }
                    } else {
                        // First Question
                        questionNumber = 1;
                    }

                    // Update Data
                    questions[questionID] = {
                        type: typesToInt[type],
                        settings: {},
                        options: []
                    };
                }
            }

            // Build the Question HTML
            var idHtml,
                dataHtml,
                editTab,
                formElements,
                imageHtml,
                itemSelector,
                newChoice,
                newChoiceL10n,
                optionsHtml,
                logicTab,
                mandatory,
                moveUp,
                moveDown,
                question,
                settings,
                thisQuestion,
                translationHidden = '',
                translationTab,
                trash;

            if (!l10n) {
                translationHidden = ' hide';
            }
            var translationTitle = '<li class="tab-title l10n' + translationHidden + '"><a href="#translation-' + position + '">Translation</a></li>';

            if (type == 'instructions') {
                idHtml = 'instructions-' + position;
                dataHtml = '';
                formElements = '#instructions-' + position + ' input, #instructions-' + position + ' select';
                itemSelector = '#instructions-' + position;
                trash = '#instructions-' + position + ' .ucce-delete';
                moveUp = '#instructions-' + position + ' .ucce-up';
                moveDown = '#instructions-' + position + ' .ucce-down';
            } else {
                idHtml = 'question-' + questionID;
                dataHtml = ' data-number="' + questionNumber + '"';
                formElements = '#question-' + questionID + ' input, #question-' + questionID + ' select';
                itemSelector = '#question-' + questionID;
                trash = '#question-' + questionID + ' .ucce-delete';
                moveUp = '#question-' + questionID + ' .ucce-up';
                moveDown = '#question-' + questionID + ' .ucce-down';
                var checked = '';
                thisQuestion = questions[questionID];
                settings = thisQuestion.settings || {};
                if (load) {
                    if (settings.requires && settings.requires.isNotEmpty) {
                        checked = ' checked';
                    }
                }
                mandatory = '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><input id="mandatory-' + questionID + '" type="checkbox" ' + checked + ' class="fleft"><label>Make question mandatory</label></div></div>';
                if (type != 'heatmap') {
                    // Upload or Pipe Image
                    optionsHtml = this.pipeOptionsHtml(questionID);
                    imageHtml = '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><label>Add image</label><span id="preview-' + questionID + '" class="preview-empty fleft"></span><label for="image-' + questionID + '" class="button tiny fleft">Upload image</label><input id="image-' + questionID + '" name="file" type="file" accept="image/png, image/jpeg" class="show-for-sr">' + 
                                '<label class="fleft">or pipe question image:</label><select id="pipe-' + questionID + '" class="fleft">' + optionsHtml + '</select>' +
                                '<a id="image-delete-' + questionID + '">Delete</a></div></div>';
                }
            }

            // <a><i class="ucce ucce-duplicate"> </i></a> Hidden until wired-up
            question = '<div class="thumbnail dl-item survey-item" id="' + idHtml + '" data-page="' + page + '"' + dataHtml + '>' + 
                       '<div class="card-header"><ul class="tabs fleft" data-tab><li class="tab-title active"><a href="#edit-' + position + '">Edit</a></li><li class="tab-title"><a href="#logic-' + position + '">Display logic</a></li> ' + translationTitle + '</ul>' +
                       '<div class="edit-bar fright"><a><i class="ucce ucce-delete"> </i></a><div class="fright"><div class="move-up"><i class="ucce ucce-up"> </i></div><div class="move-down"><i class="ucce ucce-down"> </i></div></div></div>' + 
                       '</div>' + 
                       '<div class="tabs-content">';

            // We need to reload this when Logic tab selected anyway, so don't bother loading now
            //optionsHtml = this.logicOptionsHtml(questionID, position);
            logicTab = '<div class="media content" id="logic-' + position + '">' + 
                        '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><h2 class="fleft">Only display question if...</h2></div></div>' +
                        '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><select id="logic-select-' + position + '"></select></div></div>' +
                        '<div class="row" id="logic-response-row-' + position + '">' +
                         '<div class="columns medium-1"></div>' +
                         '<div class="columns medium-11">' +
                          '<div class="row"><div class="columns medium-2"><label class="fleft">response is</label></div><div class="columns medium-10" id="logic-response-' + position + '"></div></div>' +
                         '</div>' +
                        '</div>' +
                       '</div>';

            switch(type) {

                case 'instructions':
                    var doText = '',
                        doTextL10n = '',
                        sayText = '',
                        sayTextL10n = '';
                    if (load) {
                        var thisLayout = layout[position];
                        doText = thisLayout.do.text;
                        sayText = thisLayout.say.text;
                        if (l10n && thisLayout.do.l10n) {
                            doTextL10n = thisLayout.do.l10n[l10n];
                            sayTextL10n = thisLayout.say.l10n[l10n];
                        }
                    }
                    editTab = '<div class="media content active" id="edit-' + position + '">' +
                               '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><h2 class="fleft">Data collector instructions</h2></div></div>' +
                               '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><label>What data collector should do</label><input id="do-' + position + '" type="text" size=100 placeholder="Type what data collector should do" value="' + doText + '"><label>What data collector should say</label><input id="say-' + position + '" type="text" size=100 placeholder="Type what data collector should say" value="' + sayText + '"></div></div>' +
                              '</div>';
                    translationTab = '<div class="media content" id="translation-' + position + '">' +
                                      '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><h2 class="fleft">Data collector instructions</h2></div></div>' +
                                      '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><label>What data collector should do</label><div class="translate-from"></div><input id="do-l10n-' + position + '" type="text" size=100 placeholder="Type translation..." value="' + doTextL10n + '"><label>What data collector should say</label><div class="translate-from"></div><input id="say-l10n-' + position + '" type="text" size=100 placeholder="Type translation..." value="' + sayTextL10n + '"></div></div>' + 
                                     '</div>';
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
                    editTab = '<div class="media content active" id="edit-' + position + '">' +
                               '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><h2 class="fleft">Text box</h2></div></div>' + 
                               '<div class="row"><div class="columns medium-1"><label id="qlabel-' + questionID + '" class="fright">Q' + questionNumber + '</label></div><div class="columns medium-11"><input id="name-' + questionID + '" type="text" size=100 placeholder="type question" value="' + name + '"></div></div>' +
                               mandatory + imageHtml +
                              '</div>';
                    translationTab = '<div class="media content" id="translation-' + position + '">' +
                                      '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><h2 class="fleft">Text box</h2></div></div>' +
                                      '<div class="row"><div class="columns medium-1"><label id="qlabel-l10n-' + questionID + '" class="fright">Q' + questionNumber + '</label></div><div class="columns medium-11"><div id="name-l10n-from-' + questionID + '" class="translate-from"></div></div></div>' +
                                      '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><input id="name-l10n-' + questionID + '" type="text" size=100 placeholder="type translated question" value="' + nameL10n + '"></div></div>' +
                                     '</div>';
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
                        var requires = settings.requires || {},
                            isIntInRange = requires.isIntInRange;
                        if (isIntInRange) {
                            min = isIntInRange.min || '';
                            max = isIntInRange.max || '';
                        }
                    }
                    editTab = '<div class="media content active" id="edit-' + position + '">' + 
                               '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><h2 class="fleft">Number question</h2></div></div>' +
                               '<div class="row"><div class="columns medium-1"><label id="qlabel-' + questionID + '" class="fright">Q' + questionNumber + '</label></div><div class="columns medium-11"><input id="name-' + questionID + '"type="text" size=100 placeholder="type question" value="' + name + '"></div></div>' +
                               mandatory + imageHtml +
                               '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><h2 class="fleft">Answer</h2></div></div>' +
                               '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><label>Restrict input to:</label></div></div>' +
                               '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><form id="answer-' + questionID + '"><label class="fleft">Minimum:</label><input id="min-' + questionID + '" name="min" type="number" value="' + min + '" class="fleft"><label class="fleft">Maximum:</label><input id="max-' + questionID + '" name="max" type="number" value="' + max + '" class="fleft"></form></div></div>' +
                              '</div>';
                    translationTab = '<div class="media content" id="translation-' + position + '">' +
                                      '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><h2 class="fleft">Number question</h2></div></div>' +
                                      '<div class="row"><div class="columns medium-1"><label id="qlabel-l10n-' + questionID + '" class="fright">Q' + questionNumber + '</label></div><div class="columns medium-11"><div id="name-l10n-from-' + questionID + '" class="translate-from"></div></div></div>' +
                                      '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><input id="name-l10n-' + questionID + '" type="text" size=100 placeholder="type translated question" value="' + nameL10n + '"></div></div>' +
                                     '</div>';
                    break;

                case 'multichoice':
                    newChoice = '<div id="choice-row-' + questionID + '-0" class="row">' +
                                 '<div class="columns medium-1"></div><div class="columns medium-11"><input class="choice-' + questionID + '" type="text" placeholder="Enter an answer choice"><i class="ucce ucce-minus"> </i><i class="ucce ucce-plus"> </i></div>' +
                                '</div>';
                    newChoiceL10n = '<div id="choice-l10n-row-' + questionID + '-0" class="row">' +
                                     '<div class="columns medium-1"></div>' +
                                     '<div class="columns medium-11">' + 
                                      '<div class="row">' + 
                                       '<div class="columns medium-6"><div id="choice-from-' + questionID + '-0" class="translate-from"></div></div>' +
                                       '<div class="columns medium-6"><input class="choice-l10n-' + questionID + '" type="text" placeholder="Type translation..."></div>' +
                                    '</div></div></div>';

                    // @ToDo: Grey the multiple -+ options if they cannot do anything
                    var name = '',
                        nameL10n = '',
                        choices,
                        choicesL10n,
                        other = '',
                        otherDisabled = ' disabled',
                        otherLabel = 'Other (please specify)',
                        otherL10n = '',
                        multiple = 1,
                        multiChecked = '',
                        otherL10nRow;

                    if (load) {
                        name = thisQuestion.name;
                        if (l10n) {
                            nameL10n = thisQuestion.name_l10n || '';
                        }
                        var options = thisQuestion.options || [],
                            optionsL10n = thisQuestion.options_l10n || [],
                            lenOptions = options.length,
                            choiceL10nRow;
                        if (lenOptions) {
                            // Add a row per choice
                            choices = '';
                            choicesL10n = '';
                            var thisOptionL10n;
                            for (var i=0; i < lenOptions; i++) {
                                choices += '<div id="choice-row-' + questionID + '-' + i + '" class="row"><div class="columns medium-1"></div><div class="columns medium-11"><input class="choice-' + questionID + '" type="text" placeholder="Enter an answer choice" value="' + options[i] + '"><i class="ucce ucce-minus"> </i><i class="ucce ucce-plus"> </i></div></div>';
                                thisOptionL10n = optionsL10n[i] || '';
                                choiceL10nRow = '<div id="choice-l10n-row-' + questionID + '-' + i + '" class="row">' +
                                                 '<div class="columns medium-1"></div>' +
                                                 '<div class="columns medium-11">' +
                                                  '<div class="row">' + 
                                                   '<div class="columns medium-6"><div id="choice-from-' + questionID + '-' + i + '" class="translate-from">' + options[i] + '</div></div>' +
                                                   '<div class="columns medium-6"><input class="choice-l10n-' + questionID + '" type="text" placeholder="Type translation..." value="' + thisOptionL10n + '"></div>' +
                                                '</div></div></div>';
                                choicesL10n += choiceL10nRow;
                            }
                        } else {
                            // Add an empty row to hold the first choice
                            choices = newChoice;
                            choicesL10n = newChoiceL10n;
                        }
                        if (settings.other) {
                            otherLabel = settings.other;
                            other = ' checked';
                            otherDisabled = '';
                            otherL10n = settings.otherL10n || '';
                            otherL10nHide = '';
                        } else {
                            otherL10nHide = ' hide';
                        }
                        otherL10nRow = '<div id="other-l10n-row-' + questionID + '" class="row' + otherL10nHide + '">' +
                                        '<div class="columns medium-1"></div>' +
                                        '<div class="columns medium-11">' +
                                         '<div class="row">' +
                                          '<div class="columns medium-6"><div id="other-l10n-from-' + questionID + '" class="translate-from">' + otherLabel + '</div></div>' +
                                          '<div class="columns medium-6"><input id="other-l10n-' + questionID + '" type="text" placeholder="Type translation..." value="' + otherL10n + '"></div>' +
                                       '</div></div></div>';
                        choicesL10n += otherL10nRow;
                        multiple = settings.multiple || 1;
                        if (multiple > 1) {
                            multiChecked = ' checked';
                        }
                    } else {
                        // Add an empty row to hold the first choice
                        choices = newChoice;
                        otherL10nRow = '<div id="other-l10n-row-' + questionID + '" class="row hide">' +
                                        '<div class="columns medium-1"></div>' +
                                        '<div class="columns medium-11">' +
                                         '<div class="row">' +
                                          '<div class="columns medium-6"><div id="other-l10n-from-' + questionID + '" class="translate-from"></div></div>' +
                                          '<div class="columns medium-6"><input id="other-l10n-' + questionID + '" type="text" placeholder="Type translation..."></div>' +
                                       '</div></div></div>';
                        choicesL10n = newChoiceL10n + otherL10nRow;
                    }
                    editTab = '<div class="media content active" id="edit-' + position + '">' +
                               '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><h2 class="left">Multiple choice question</h2></div></div>' +
                               '<div class="row"><div class="columns medium-1"><label id="qlabel-' + questionID + '" class="fright">Q' + questionNumber + '</label></div><div class="columns medium-11"><input id="name-' + questionID + '"type="text" size=100 placeholder="type question" value="' + name + '"></div></div>' +
                               mandatory + imageHtml +
                               '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><h2 class="fleft">Answer</h2></div></div>' +
                               '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><label>Choices</label></div></div>' +
                               choices +
                               '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><input id="other-' + questionID + '" type="checkbox"' + other + '><label>Add \'other field\'</label></div></div>' + 
                               '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><label class="fleft">Field label</label><input id="other-label-' + questionID + '" type="text" value="' + otherLabel + '"' + otherDisabled + '></div></div>' + 
                               '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><input id="multiple-' + questionID + '" type="checkbox"' + multiChecked + '><label>Allow multiple responses</label></div></div>' +
                               '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><label class="fleft">Maximum No. of responses:</label><i class="ucce ucce-minus"> </i> <span id="multiple-count-' + questionID + '">' + multiple + '</span> <i class="ucce ucce-plus"> </i></div></div>' +
                              '</div>';
                    
                    translationTab = '<div class="media content" id="translation-' + position + '">' +
                                      '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><h2 class="fleft">Multiple choice question</h2></div></div>' +
                                      '<div class="row"><div class="columns medium-1"><label id="qlabel-l10n-' + questionID + '" class="fright">Q' + questionNumber + '</label></div><div class="columns medium-11"><div id="name-l10n-from-' + questionID + '" class="translate-from"></div></div></div>' +
                                      '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><input id="name-l10n-' + questionID + '" type="text" size=100 placeholder="type translated question" value="' + nameL10n + '"></div></div>' +
                                      '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><h2 class="fleft">Answer</h2></div></div>' +
                                      '<div class="row" id="choices-l10n-row-' + questionID + '"><div class="columns medium-1"></div><div class="columns medium-11"><label>Choices</label></div></div>' +
                                      choicesL10n + 
                                     '</div>';
                    break;

                case 'likert':
                    var name = '',
                        nameL10n = '',
                        choicesL10n = '',
                        displayOptions = '',
                        scales = [
                            '<option value="1">Appropriateness (Very appropriate - Very inappropriate)</option>',
                            '<option value="2">Confidence (Extremely confident - Not confident at all)</option>',
                            '<option value="3">Frequency (Always - Never)</option>',
                            '<option value="4">Safety (Extremely safe - Not safe at all)</option>',
                            '<option value="5">Satisfaction (Satisfied - Dissatisfied)</option>',
                            '<option value="6">Smiley scale (5 point)</option>',
                            '<option value="7">Smiley scale (3 point)</option>'
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
                                var result = this.likertOptionsHtml(questionID, scale);
                                choicesL10n = result.choicesL10n;
                                displayOptions = result.displayOptions;
                            }
                        }
                    }
                    var scaleOptions = scales.join();
                    editTab = '<div class="media content active" id="edit-' + position + '">' +
                               '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><h2 class="left">Likert-scale</h2></div></div>' +
                               '<div class="row"><div class="columns medium-1"><label id="qlabel-' + questionID + '" class="fright">Q' + questionNumber + '</label></div><div class="columns medium-11"><input id="name-' + questionID + '"type="text" size=100 placeholder="type question" value="' + name + '"></div></div>' +
                               mandatory + imageHtml +
                               '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><h2 class="left">Answer</h2></div></div>' +
                               '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><label>Choices</label><select id="scale-' + questionID + '"><option value="">Please choose scale</option>' + scaleOptions + '</select></div></div>' +
                               '<div class="row"><div class="columns medium-1"></div><div id="display-' + questionID + '" class="columns medium-11">' + displayOptions + '</div></div>' +
                              '</div>';
                    translationTab = '<div class="media content" id="translation-' + position + '">' +
                                      '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><h2 class="left">Likert-scale</h2></div></div>' +
                                      '<div class="row"><div class="columns medium-1"><label id="qlabel-l10n-' + questionID + '" class="fright">Q' + questionNumber + '</label></div><div class="columns medium-11"><div id="name-l10n-from-' + questionID + '" class="translate-from"></div></div></div>' +
                                      '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><input id="name-l10n-' + questionID + '" type="text" size=100 placeholder="type translated question" value="' + nameL10n + '"></div></div>' +
                                      choicesL10n +
                                     '</div>';
                    break;

                case 'heatmap':
                    newChoice = '<div id="choice-row-' + questionID + '-0" class="row"><a class="button tiny secondary choice-define-' + questionID + '">Add region 1</a><input type="hidden" id="choice-json-' + questionID + '-0"><input class="choice-' + questionID + '" type="text" placeholder="enter label" disabled><i class="ucce ucce-minus hide"> </i></div>';
                    var name = '',
                        nameL10n = '',
                        numClicks = 1,
                        choices = newChoice,
                        choicesL10n = '',
                        optionsL10n = '';
                    if (load) {
                        name = thisQuestion.name;
                        if (l10n) {
                            nameL10n = thisQuestion.name_l10n || '';
                        }
                        var options = thisQuestion.options || [],
                            optionsL10n = thisQuestion.options_l10n || [],
                            lenOptions = options.length,
                            choiceL10nRow;
                        if (lenOptions) {
                            choices = '';
                            var regions = thisQuestion.settings.regions;
                                thisOptionL10n;
                            for (var i=0; i < lenOptions; i++) {
                                choices += '<div id="choice-row-' + questionID + '-' + i + '" class="row"><a class="button tiny choice-define-' + questionID + '">Add region ' + (i + 1) + '</a><input type="hidden" id="choice-json-' + questionID + '-' + i + '" value=\'' + regions[i] + '\'><input class="choice-' + questionID + '" type="text" placeholder="enter label" value="' + options[i] + '"><i class="ucce ucce-minus"> </i></div>';
                                thisOptionL10n = optionsL10n[i] || '';
                                choiceL10nRow = '<div id="choice-l10n-row-' + questionID + '-' + i + '" class="row">' +
                                                 '<div class="columns medium-1"></div>' +
                                                 '<div class="columns medium-11">' +
                                                  '<div class="row">' + 
                                                   '<div class="columns medium-6"><div id="choice-from-' + questionID + '-' + i + '" class="translate-from">' + options[i] + '</div></div>' +
                                                   '<div class="columns medium-6"><input class="choice-l10n-' + questionID + '" type="text" placeholder="Type translation..." value="' + thisOptionL10n + '"></div>' +
                                                '</div></div></div>';
                                choicesL10n += choiceL10nRow;
                            }
                            choices += newChoice.replace('-0', '-' + lenOptions).replace('region 1', 'region ' + (lenOptions + 1));
                        }
                        numClicks = thisQuestion.settings.numClicks || 1
                    }
                    //<span id="preview-' + questionID + '" class="preview-empty fleft"></span>
                    editTab = '<div class="media content active" id="edit-' + position + '">' +
                               '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><h2 class="left">Heatmap</h2></div></div>' +
                               '<div class="row"><div class="columns medium-1"><label id="qlabel-' + questionID + '" class="fright">Q' + questionNumber + '</label></div><div class="columns medium-11"><input id="name-' + questionID + '"type="text" size=100 placeholder="type question" value="' + name + '"></div></div>' +
                               mandatory +
                               '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><h2 class="fleft">Image</h2></div></div>' +
                               '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><label for="image-' + questionID + '" class="button tiny fleft">Upload image</label><input id="image-' + questionID + '" name="file" type="file" accept="image/png, image/jpeg" class="show-for-sr"></div></div>' +
                               '<div class="row">' +
                                '<div class="columns medium-8">' +
                                 '<div class="heatmap" id="map-' + questionID + '"><span id="preview-' + questionID + '" class="preview-empty fleft"></span></div>' +
                                '</div>' +
                                '<div class="columns medium-4">' +
                                 '<div class="row"><h3>Number of clicks allowed:</h3></div>' +
                                 '<div class="row" id="clicks-row-' + questionID + '"><i class="ucce ucce-minus"> </i><span> ' + numClicks + ' </span><i class="ucce ucce-plus"> </i></div>' +
                                 '<div class="row"><h3>Tap regions:</h3></div>' +
                                 choices +
                               '</div></div></div>';
                    translationTab = '<div class="media content" id="translation-' + position + '">' +
                                      '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><h2 class="left">Heatmap</h2></div></div>' +
                                      '<div class="row"><div class="columns medium-1"><label id="qlabel-l10n-' + questionID + '" class="fright">Q' + questionNumber + '</label></div><div class="columns medium-11"><div id="name-l10n-from-' + questionID + '" class="translate-from"></div></div></div>' +
                                      '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><input id="name-l10n-' + questionID + '" type="text" size=100 placeholder="type translated question" value="' + nameL10n + '"></div></div>' +
                                      '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><h2 class="fleft">Answer</h2></div></div>' +
                                      '<div class="row" id="choices-l10n-row-' + questionID + '"><div class="columns medium-1"></div><div class="columns medium-11"><label>Regions</label></div></div>' +
                                      choicesL10n + 
                                     '</div>';
                    break;
            }

            question += editTab;
            question += logicTab;
            question += translationTab;
            question += '</div></div>';

            if (type == 'instructions') {
                item = {
                    type: 'instructions',
                    do: {text: ''},
                    say: {text: ''}
                };
            } else{
                item = {
                    type: 'question',
                    id: questionID
                };
            }

            if (!load) {
                // Update the elements on the section
                // Add to Layout
                // Save Layout
                this.rePosition(item, null, position);
            }

            // Add to DOM
            if (readOnly) { 
                // Place after other elements
                $(this.element).parent().append(question);
            } else if (load || position == Object.keys(layout).length) {
                // Place before droppable
                $('#survey-droppable').before(question);
            } else {
                // Place after previous element
                var previousPosition = position - 1,
                    previousItem = layout[previousPosition];
                if (previousItem.type == 'break') {
                    $('#section-break-' + previousPosition).parent().after(question);
                } else if (previousItem.type == 'instructions') {
                    $('#instructions-' + previousPosition).after(question);
                } else {
                    // Question
                    $('#question-' + previousItem.id).after(question);
                }
            }

            // Event Handlers
            var ns = this.eventNamespace,
                self = this,
                $item = $(itemSelector);

            if (!readOnly) {
                // (Drag)'n'Drop
                $(itemSelector).droppable({
                    drop: function(event, ui) {
                        // Open QuestionEditorWidget with correct options for type
                        var questionType = ui.draggable[0].id,
                            // Cannot trust originals as they may have moved
                            currentPosition,
                            currentPage = $(this).data('page');
                        if (type == 'instructions') {
                            currentPosition = parseInt(this.id.split('-')[1]);
                        } else {
                            // Question
                            var currentQuestionNumber = $(this).data('number');
                            currentPosition = questionNumbers[currentQuestionNumber];
                        }
                        if (questionType == 'break') {
                            self.addSectionBreak(currentPosition + 1, currentPage);
                        } else {
                            self.addQuestion(currentPosition + 1, currentPage, questionType);
                        }
                    }
                });
            }

            var inputEvents = function() {
                $(formElements).off('change' + ns)
                               .on('change' + ns, function(/* event */) {
                    var parts = this.id.split('-');
                    if (parts[0] == 'logic') {
                        // Display Logic 1st select has been selected
                        // Can't trust original position as it may have changed
                        var currentPosition = parseInt(parts[parts.length - 1]);
                        // Show 2nd Logic select
                        self.logicSelected($(this), currentPosition);
                    } else {
                        // If form elements change, then Save
                        if (type == 'instructions') {
                            // Update Data
                            // Can't trust original position as it may have changed
                            var currentPosition = parseInt(parts[parts.length - 1]),
                                thisLayout = layout[currentPosition];
                            thisLayout.do.text = $('#do-' + currentPosition).val();
                            thisLayout.say.text = $('#say-' + currentPosition).val();
                            // Can't trust original l10n
                            var l10n = self.data.l10n;
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
                    }
                });
                
                if (!readOnly && (type != 'instructions') && (type != 'heatmap')) {
                    // Image Pipe
                    $('#pipe-' + questionID).on('change'+ ns, function() {
                        var value = $(this).val();
                        if (value) {
                            var img,
                                imageQuestionID;
                            for (var i=0, len=imageOptions.length; i < len; i++) {
                                img = imageOptions[i];
                                if (img.label == value) {
                                    imageQuestionID = img.id;
                                    thisQuestion.settings.pipeImage = {
                                        id: imageQuestionID,
                                        region: img.region
                                    };
                                    break;
                                }
                            }
                            // Remove any Image
                            self.deleteImage(questionID);
                            // Show Preview of selected Image
                            loadImage(S3.Ap.concat('/default/download/' + imageFiles[imageQuestionID]), function(img) {
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
                            
                        } else {
                            delete thisQuestion.settings.pipeImage;
                            $('#preview-' + questionID).addClass('preview-empty')
                                                       .empty()
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
                        imageFiles[questionID] = file;
                        if (type == 'heatmap') {
                            self.heatMap(questionID, file, load);
                        } else {
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
                    } else if (thisQuestion.settings.pipeImage) {
                        // If there is an existing pipeImage, then load preview now
                        $('#pipe-' + questionID).trigger('change');
                    }
                }
                if (!readOnly) {
                    $('#image-delete-' + questionID).on('click' + ns, function() {
                        self.deleteImage(questionID);
                    });
                    // Image Upload
                    var options;
                    if (type == 'heatmap') {
                        options = {
                            dataType: 'json',
                            dropZone: $('#preview-' + questionID + ', #image-' + questionID),
                            disableImageResize: false,
                            imageMaxWidth: 480,
                            imageMaxHeight: 480,
                            imageMinWidth: 480,
                            imageMinheight: 480,
                            maxNumberOfFiles: 1,
                            url: S3.Ap.concat('/dc/question/') + questionID + '/image_upload.json',
                            add: function(e, data) {
                                if (e.isDefaultPrevented()) {
                                    return false;
                                }
                                if (data.autoUpload || (data.autoUpload !== false && $(this).fileupload('option', 'autoUpload'))) {
                                    data.process().done(function() {
                                        data.submit();
                                    });
                                }
                            },
                            done: function (e, data) {
                                var file = data.result.file;
                                imageFiles[questionID] = file;
                                self.data.questions[questionID].file = file;
                                self.heatMap(questionID, file);
                            }
                        };
                    } else {
                        options = {
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
                                            // Ensure that we aren't trying to Pipe at the same time
                                            if (thisQuestion.settings.hasOwnProperty('pipeImage')) {
                                                $('#pipe-' + questionID).val('')
                                                                        .trigger('change');
                                            }
                                            return img;
                                        }, {}); // Empty Options
                                    });
                                }
                            },
                            done: function (e, data) {
                                var file = data.result.file;
                                imageFiles[questionID] = file;
                                self.data.questions[questionID].file = file;
                                // Update ImageOptions
                                self.updateImageOptions();
                            }
                        };
                    }
                    $('#image-' + questionID).fileupload(options);
                }
            }
            
            if (!readOnly) {
                $(trash).on('click' + ns, function(/* event */) {
                    // Delete the Question
                    self.deleteQuestion(type, questionID, this);
                });
                $(moveUp).on('click' + ns, function(/* event */) {
                    var currentPosition;
                    if (type == 'instructions') {
                        currentPosition = parseInt($(this).closest('.survey-item').attr('id').split('-')[1]);
                    } else {
                        // Question
                        var currentQuestionNumber = $(this).closest('.survey-item').data('number');
                        currentPosition = questionNumbers[currentQuestionNumber];
                    }
                    if (currentPosition > 1) {
                        var newPosition = currentPosition - 1;
                        // Update DOM
                        var movingItem;
                        if (type == 'instructions') {
                            movingItem = $('#instructions-' + currentPosition).detach();
                        } else {
                            movingItem = $('#question-' + questionID).detach();
                        }
                        if (layout[newPosition].type == 'question') {
                            $('#question-' + layout[newPosition].id).before(movingItem);
                        } else if (layout[newPosition].type == 'instructions') {
                            $('#instructions-' + newPosition).before(movingItem);
                        } else {
                            // Moving after Section Break
                            $('#section-break-' + newPosition).parent().before(movingItem);
                        }
                        // Update Layout & IDs
                        self.rePosition(item, currentPosition, newPosition);
                    }
                });
                $(moveDown).on('click' + ns, function(/* event */) {
                    var currentPosition;
                    if (type == 'instructions') {
                        currentPosition = parseInt($(this).closest('.survey-item').attr('id').split('-')[1]);
                    } else {
                        // Question
                        var currentQuestionNumber = $(this).closest('.survey-item').data('number');
                        currentPosition = questionNumbers[currentQuestionNumber];
                    }
                    if (currentPosition < Object.keys(layout).length) {
                        var newPosition = currentPosition + 1;
                        // Update DOM
                        var movingItem;
                        if (type == 'instructions') {
                            movingItem = $('#instructions-' + currentPosition).detach();
                        } else {
                            movingItem = $('#question-' + questionID).detach();
                        }
                        if (layout[newPosition].type == 'question') {
                            $('#question-' + layout[newPosition].id).after(movingItem);
                        } else if (layout[newPosition].type == 'instructions') {
                            $('#instructions-' + newPosition).after(movingItem);
                        } else {
                            // Moving after Section Break
                            $('#section-break-' + newPosition).parent().after(movingItem);
                        }
                        // Update Layout & IDs
                        self.rePosition(item, currentPosition, newPosition);
                    }
                });
            }

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
                        multipleCount = $('#multiple-count-' + questionID);
                    // non-Form element events don't need to be re-instantiated when choices added/removed
                    multipleCount.prev().off('click' + ns)
                                        .on('click' + ns, function() {
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
                    multipleCount.next().off('click' + ns)
                                        .on('click' + ns, function() {
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
                    var multichoiceEvents = function() {
                        // New elements need to be instantiated when choices added/removed
                        // Options
                        var deleteOption = $('.choice-' + questionID).next();
                        deleteOption.off('click' + ns)
                                    .on('click' + ns, function() {
                            var optionInput = $(this).prev(),
                                value = optionInput.val();
                            if ($('.choice-' + questionID).length > 1) {
                                // Remove Option
                                var currentRow = $(this).closest('.row'),
                                    index = parseInt(currentRow.attr('id').split('-')[3]);
                                currentRow.remove();
                                // & from l10n
                                $('#choice-l10n-row-' + questionID + '-' + index).remove();

                                // Update IDs for all subsequent rows
                                var newIndex,
                                    optionsCount = $('.choice-' + questionID).length;

                                for (var i = index + 1; i <= optionsCount; i++) {
                                    newIndex = i - 1;
                                    $('#choice-row-' + questionID + '-' + i).attr('id', 'choice-row-' + questionID + '-' + newIndex);
                                    $('#choice-l10n-row-' + questionID + '-' + i).attr('id', 'choice-l10n-row-' + questionID + '-' + newIndex);
                                    $('#choice-from-' + questionID + '-' + i).attr('id', 'choice-from-' + questionID + '-' + newIndex);
                                }

                                // Check if we now have fewer options than multipleCount
                                var multiple = parseInt(multipleCount.html());
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
                                // Just remove value - since we always need at least 1 option available
                                optionInput.val('');
                            }
                            if (value) {
                                // Remove any outdated displayLogic
                                var thisItem;
                                for (var i=currentPosition + 1, len=Object.keys(layout).length; i <= len; i++) {
                                    thisItem = layout[i];
                                    if (thisItem.displayLogic && thisItem.displayLogic.id == questionID && thisItem.displayLogic.eq == value) {
                                        delete thisItem.displayLogic;
                                        $('#logic-select-' + i).val('')
                                                               .trigger('change');
                                    }
                                }
                            }
                        });
                        deleteOption.next().off('click' + ns)
                                           .on('click' + ns, function() {
                            // Pepare to add a new Option
                            // Update IDs for all subsequent rows
                            var currentRow = $(this).closest('.row'),
                                index = parseInt(currentRow.attr('id').split('-')[3]),
                                newIndex,
                                optionsCount = $('.choice-' + questionID).length;
                            for (var i = optionsCount - 1; i > index; i--) {
                                newIndex = i + 1;
                                $('#choice-row-' + questionID + '-' + i).attr('id', 'choice-row-' + questionID + '-' + newIndex);
                                $('#choice-l10n-row-' + questionID + '-' + i).attr('id', 'choice-l10n-row-' + questionID + '-' + newIndex);
                                $('#choice-from-' + questionID + '-' + i).attr('id', 'choice-from-' + questionID + '-' + newIndex);
                            }
                            // Add new Option after current row
                            newIndex = index + 1;
                            currentRow.after(newChoice.replace('-0', '-' + newIndex));
                            // & in l10n
                            $('#choice-l10n-row-' + questionID + '-' + index).after(newChoiceL10n.replace(/-0/g, '-' + newIndex));
                            // Add Events
                            inputEvents();
                            multichoiceEvents();
                        });
                        // Form element events need to be re-instantiated when choices added/removed
                        // Other field
                        $('#other-' + questionID).off('change' + ns)
                                                 .on('change' + ns, function() {
                            if ($(this).prop('checked')) {
                                $('#other-label-' + questionID).prop('disabled', false);
                                $('#other-l10n-row-' + questionID).removeClass('hide')
                                                                  .show();
                            } else {
                                $('#other-label-' + questionID).prop('disabled', true);
                                $('#other-l10n-row-' + questionID).hide();
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
                            self.saveQuestion(type, questionID);
                        });
                        // Multiple
                        multipleCheckbox.off('change' + ns)
                                        .on('change' + ns, function() {
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
                    };
                    multichoiceEvents();
                    break;

                case 'likert':
                    // Display options when scale selected
                    $('#scale-' + questionID).on('change' + ns, function() {
                        // Remove old display
                        $('#display-' + questionID).empty();
                        var choicesRow = $('#choices-l10n-row-' + questionID);
                        if (choicesRow.length) {
                            choicesRow.prev().remove();
                            for (var i=0; i < 5; i++) {
                                choicesRow.next().remove();
                            }
                            choicesRow.remove();
                        }
                        var scale = $(this).val();
                        if (scale) {
                            var result = self.likertOptionsHtml(questionID, scale),
                                choicesL10n = result.choicesL10n,
                                displayOptions = result.displayOptions;
                            $('#display-' + questionID).append(displayOptions);
                            // Can't trust original position as it may have changed
                            var currentPosition = parseInt($(this).closest('.media').attr('id').split('-')[1]);
                            $('#translation-' + currentPosition).append(choicesL10n);
                            // Add Events to new inputs
                            inputEvents();
                        }
                    });
                    break;

                case 'heatmap':
                    var multichoiceEvents = function() {
                        // Options
                        var deleteOption = $('.choice-' + questionID).next();
                        deleteOption.off('click' + ns)
                                    .on('click' + ns, function() {
                            var $this = $(this),
                                // Parse currentPosition now...as can't do it after we .remove()
                                currentPosition = parseInt($this.closest('.media').attr('id').split('-')[1]);
                            
                            if ($('.choice-' + questionID).length > 1) {
                                // Remove Region
                                var currentRow = $this.closest('.row'),
                                    index = parseInt(currentRow.attr('id').split('-')[3]);
                                currentRow.remove();
                                // & from l10n
                                $('#choice-l10n-row-' + questionID + '-' + index).remove();

                                // Update IDs for all subsequent rows
                                var newIndex,
                                    optionsCount = $('.choice-' + questionID).length;

                                for (var i = index + 1; i <= optionsCount; i++) {
                                    newIndex = i - 1;
                                    $('#choice-row-' + questionID + '-' + i).attr('id', 'choice-row-' + questionID + '-' + newIndex);
                                    $('#choice-row-' + questionID + '-' + newIndex + ' > .button').html('Add region ' + (newIndex + 1));
                                    $('#choice-l10n-row-' + questionID + '-' + i).attr('id', 'choice-l10n-row-' + questionID + '-' + newIndex);
                                    $('#choice-from-' + questionID + '-' + i).attr('id', 'choice-from-' + questionID + '-' + newIndex);
                                }
                                self.saveQuestion(type, questionID);
                            } else {
                                // Just remove value - since we always need at least 1 region available
                                $this.hide()
                                     .prev()
                                     .val('')
                                     .prop('disabled', true)
                                     .prev().addClass('secondary');
                            }

                            // Remove existing Region Polygon
                            var callback = function(feature) {
                                if (feature.get('region') == index) {
                                    source.removeFeature(feature);
                                    // Stop Iterating
                                    return true;
                                }
                                // Continue Iterating
                                return false;
                            };
                            source.forEachFeature(callback);

                            // Loop through Layout to remove outdated displayLogic &/or pipeImage
                            var layoutLength = Object.keys(layout).length,
                                thisItem,
                                thisQuestionID,
                                thisQuestionSettings;
                            for (var i=1; i <= layoutLength; i++) {
                                thisItem = layout[i];
                                if (thisItem.type == 'question') {
                                    thisQuestionID = thisItem.id;
                                    thisQuestionSettings = questions[thisQuestionID].settings;
                                    if (thisQuestionSettings.pipeImage && thisQuestionSettings.pipeImage.id == questionID && thisQuestionSettings.pipeImage.region == index) {
                                        // Remove outdated pipeImage
                                        delete thisQuestionSettings.pipeImage;
                                        $('#pipe-' + thisQuestionID).val('')
                                                                    .trigger('change');
                                    }
                                }
                                if (i > currentPosition + 1) {
                                    if (thisItem.displayLogic && thisItem.displayLogic.id == questionID && thisItem.displayLogic.eq == index) {
                                        // Remove outdated displayLogic
                                        delete thisItem.displayLogic;
                                        $('#logic-select-' + i).val('')
                                                               .trigger('change');
                                    }
                                }
                            }
                        });
                        $('.choice-define-' + questionID).off('click' + ns)
                                                         .on('click' + ns, function() {
                            // Prepare to Define a Region
                            var $this = $(this),
                                currentRow = $this.closest('.row'),
                                index = parseInt(currentRow.attr('id').split('-')[3]),
                                regions = questions[questionID].settings.regions;

                            // Maintain Hover colour until Polygon defined
                            // - remove from all others 1st
                            currentRow.parent().find('.defining').removeClass('defining');
                            $this.addClass('defining');

                            if ($this.hasClass('secondary')) {
                                // Add new Region after current row
                                var newIndex = index + 1;
                                currentRow.after(newChoice.replace(/-0/g, '-' + newIndex));
                                $('#choice-row-' + questionID + '-' + newIndex + ' > .button').html('Add region ' + (newIndex + 1));

                                // & in l10n
                                var choiceL10nRow = '<div id="choice-l10n-row-' + questionID + '-' + index + '" class="row">' +
                                                     '<div class="columns medium-1"></div>' +
                                                     '<div class="columns medium-11">' + 
                                                      '<div class="row">' + 
                                                       '<div class="columns medium-6"><div id="choice-from-' + questionID + '-' + index + '" class="translate-from"></div></div>' +
                                                       '<div class="columns medium-6"><input class="choice-l10n-' + questionID + '" type="text" placeholder="Type translation..."></div>' +
                                                     '</div></div></div>';
                                if (index == 0) {
                                    $('#choices-l10n-row-' + questionID).after(choiceL10nRow);
                                } else {
                                    $('#choice-l10n-row-' + questionID + '-' + (index - 1)).after(choiceL10nRow);
                                }

                                // Add Events
                                inputEvents();
                                multichoiceEvents();
                                $this.removeClass('secondary')
                                     .next().next().prop('disabled', false)
                                                   .next().removeClass('hide')
                                                          .show();
                            }
                            // Show existing Region Polygon in a different Colour
                            var callback = function(feature) {
                                if (feature.get('region') == index) {
                                    var style = new Style({
                                        fill: new Fill({
                                          color: '#ffc0cb' // pink
                                        }),
                                        stroke: new Stroke({
                                          color: 'red'
                                        })
                                    });
                                    feature.setStyle(style);
                                } else {
                                    // Ensure has default Style
                                    feature.setStyle(null);
                                }
                                // Continue Iterating
                                return false;
                            };
                            sources[questionID].forEachFeature(callback); 
                            // Define Region
                            var draw = draws[questionID];
                            draw.set('questionID', questionID, true);
                            draw.set('region', index, true);
                            maps[questionID].addInteraction(draw);
                        });
                    };
                    multichoiceEvents();

                    // numClicks
                    var minusClick = $('#clicks-row-' + questionID).children().first();
                    minusClick.off('click' + ns)
                              .on('click' + ns, function() {

                        var $this = $(this),
                            value = parseInt($this.next().html());

                        if (value > 1) {
                            // Decrement value
                            value--;
                            // Update Data
                            questions[questionID].settings.numClicks = value;
                            // Save Question
                            self.saveQuestion(type, questionID);
                            // Update visual element
                            $this.next().html(' ' + value + ' ');
                        }
                    });
                    minusClick.next().next().off('click' + ns)
                                            .on('click' + ns, function() {

                        var $prev = $(this).prev(),
                            value = parseInt($prev.html());

                        // Increment value
                        value++;
                        // Update Data
                        questions[questionID].settings.numClicks = value;
                        // Save Question
                        self.saveQuestion(type, questionID);
                        // Update visual element
                        $prev.html(' ' + value + ' ');
                    });
                break;
            }

            // Run Foundation JS on new Item
            //- needed for Tabs to work at all & allows us to add callback
            $item.foundation('tab', 'reflow');
        },

        /**
          * Delete a Question
          */
        deleteQuestion: function(type, questionID, deleteBtn) {

            var currentPosition,
                layout = this.data.layout;

            if (type == 'instructions') {
                // Read the position (can't trust original as it may have changed)
                currentPosition = parseInt($(deleteBtn).closest('.survey-item').attr('id').split('-')[1]);
            } else {
                // Question

                // Read the questionNumber (can't trust original as it may have changed)
                var questionNumber = $('#question-' + questionID).data('number');
                // Read the position (can't trust original as it may have changed)
                currentPosition = questionNumbers[questionNumber];

                // Cleanup Maps
                delete draws[questionID];
                delete maps[questionID];
                delete sources[questionID];
            }

            this.rePosition(layout[currentPosition], currentPosition, null);

            // Remove from DOM
            if (type == 'instructions') {
                $('#instructions-' + currentPosition).remove();
            } else {
                $('#question-' + questionID).remove();
            }

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
          * Turn an Image into a (Heat)Map
          */
        heatMap: function(questionID, file, load) {

            var self = this,
                url = S3.Ap.concat('/default/download/' + file);

            // Add image to DOM to get the height/width
            $('<img>').attr('src', url).load(function() {
                var width = this.width,     // Should always be 480
                    height = this.height;   // Should always be 480

                // Remove preview
                $('#map-' + questionID).empty();

                // Map views always need a projection.  Here we just want to map image
                // coordinates directly to map coordinates, so we create a projection that uses
                // the image extent in pixels.
                var extent = [0, 0, width, height];
                var projection = new Projection({
                    code: 'preview-image',
                    units: 'pixels',
                    extent: extent
                });

                var raster = new ImageLayer({
                    source: new Static({
                        url: url,
                        projection: projection,
                        imageExtent: extent
                    })
                });

                var source = new VectorSource({wrapX: false});
                sources[questionID] = source;

                var vector = new VectorLayer({
                    source: source
                });

                var map = new Map({
                    controls: [],
                    interactions: [],
                    layers: [
                      raster,
                      vector
                    ],
                    target: 'map-' + questionID,
                    view: new View({
                        projection: projection,
                        center: getCenter(extent),
                        zoom: 1,
                        maxZoom: 1
                    })
                });
                maps[questionID] = map;

                const format = new GeoJSON({featureProjection: projection});

                var draw = new Draw({
                    source: source,
                    type: 'Polygon'
                });
                draws[questionID] = draw;

                draw.on('drawstart', function(event) {

                    // We only want a single Polygon per Region
                    var region = draw.get('region'),
                        callback = function(feature) {
                            if (feature.get('region') == region) {
                                source.removeFeature(feature);
                                // Stop Iterating
                                return true;
                            }
                            // Continue Iterating
                            return false;
                        };
                
                    source.forEachFeature(callback);
                });

                draw.on('drawend', function(event) {

                    var feature = event.feature,
                        questionID = draw.get('questionID'),
                        region = draw.get('region');

                    // Tag the feature to link it to the input
                    feature.set('region', region);

                    // Store the GeoJSON
                    var geojson = format.writeFeatureObject(feature, {decimals: 0});
                    $('#choice-json-' + questionID + '-' + region).val(JSON.stringify(geojson))
                                                                  // Reset the Button to normal colours
                                                                  .prev().removeClass('defining');
                    self.saveQuestion('heatmap', questionID);

                    // We only want a single Polygon per Region
                    map.removeInteraction(draw);
                });

                if (load) {
                    // Show existing features
                    var feature,
                        geojson,
                        region,
                        regions = self.data.questions[questionID].settings.regions || [];
                    for (var i=0, len=regions.length; i < len; i++) {
                        region = regions[i];
                        if (region && region != 'null') {
                            geojson = JSON.parse(region);
                            feature = format.readFeatureFromObject(geojson);
                            source.addFeature(feature);
                        }
                    }
                }
            });
        },

        /**
          * Provide the HTML for Likert Options Display & L10n
          */
        likertOptionsHtml: function(questionID, scale) {

            var choicesL10n = '',
                displayOptions,
                nameL10n = '',
                optionsL10nHidden = ' hide';

            if (scale == 6) {
                // 5-point smiley
                displayOptions = '<ul><li><i class="ucce ucce-smiley-1"> </i></li><li><i class="ucce ucce-smiley-2"> </i></li><li><i class="ucce ucce-smiley-3"> </i></li><li><i class="ucce ucce-smiley-4"> </i></li><li><i class="ucce ucce-smiley-6"> </i></li></ul>';
            } else if (scale == 7) {
                // 3-point smiley
                displayOptions = '<ul><li><i class="ucce ucce-smiley-3"> </i></li><li><i class="ucce ucce-smiley-4"> </i></li><li><i class="ucce ucce-smiley-5"> </i></li></ul>';
            } else {
                var choiceL10nRow,
                    options = likertOptions[scale],
                    optionsLength = options.length,
                    optionsL10n = this.data.questions[questionID].options_l10n || [],
                    thisOptionL10n;
                displayOptions = '<ul>';
                optionsL10nHidden = '';
                for (var i=0; i < optionsLength; i++) {
                    displayOptions += '<li>' + options[i] + '</li>';
                    thisOptionL10n = optionsL10n[i] || '';
                    choiceL10nRow = '<div id="choice-l10n-row-' + questionID + '-' + i + '" class="row">' +
                                     '<div class="columns medium-1"></div>' +
                                     '<div class="columns medium-11">' +
                                      '<div class="row">' + 
                                       '<div class="columns medium-6"><div id="choice-from-' + questionID + '-' + i + '" class="translate-from">' + options[i] + '</div></div>' +
                                       '<div class="columns medium-6"><input class="choice-l10n-' + questionID + '" type="text" placeholder="Type translation..." value="' + thisOptionL10n + '"></div>' +
                                    '</div></div></div>';
                    choicesL10n += choiceL10nRow;
                }
                displayOptions += '</ul>';
            }

            var choicesL10nHtml = '<div class="row' + optionsL10nHidden + '"><div class="columns medium-1"></div><div class="columns medium-11"><h2 class="fleft">Answer</h2></div></div>' +
                                  '<div class="row' + optionsL10nHidden + '" id="choices-l10n-row-' + questionID + '"><div class="columns medium-1"></div><div class="columns medium-11"><label>Choices</label></div></div>' +
                                  choicesL10n;
            return {
                choicesL10n: choicesL10nHtml,
                displayOptions: displayOptions
            }
        },

        /**
          * Produce the Options HTML for the Pipe dropdown
          */
        pipeOptionsHtml: function(questionID) {

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
          * Update the ImageOptions lookup
          * - if loading, also update the questionNumbers lookup
          * - otherwise, also update all pipeOptionsHtml
          *
          * optionally, also cleanup stale pipeOptions from deleted Question
          *
          */
        updateImageOptions: function(load, deletedQuestionID) {

            var item,
                questionNumber = 0,
                base_label,
                label,
                layout = this.data.layout,
                layoutLength = Object.keys(layout).length,
                options,
                questions = this.data.questions,
                regions,
                thisQuestion,
                thisQuestionID,
                thisQuestionSettings,
                thisQuestionType;

            // Start with an empty imageOptions
            imageOptions = [];

            // Loop through the layout
            for (var position=1; position <= layoutLength; position++) {
                item = layout[position];
                if (item.type == 'break') {
                    // Skip: No Image or QuestionNumber
                    continue;
                } else if (item.type == 'instructions') {
                    // Skip: No Image or QuestionNumber
                    continue;
                } else {
                    // Question

                    questionNumber++

                    thisQuestionID = item.id;
                    thisQuestion = questions[thisQuestionID];
                    if (thisQuestion === undefined) {
                        // We have a deleted question in the layout somehow!
                        continue;
                    }
                    thisQuestionSettings = thisQuestion.settings;
                    thisQuestionType = thisQuestion.type;

                    if (load) {
                        // We're in loadSurvey
                        questionNumbers[questionNumber] = position;
                    } else {
                        if (thisQuestionType != 13) {
                            // Update the Pipe Options HTML
                            $('#pipe-' + thisQuestionID).empty()
                                                        .append(this.pipeOptionsHtml(thisQuestionID));
                        }
                        if (deletedQuestionID) {
                            if (thisQuestionSettings.pipeImage && thisQuestionSettings.pipeImage.id == deletedQuestionID) {
                                // Remove the stale pipeImage
                                delete thisQuestionSettings.pipeImage
                                // & it's preview
                                $('#preview-' + thisQuestionID).addClass('preview-empty')
                                                               .empty()
                            }
                        }
                    }

                    if (thisQuestion.file) {
                        if (thisQuestionType == 13) {
                            // Heatmap
                            options = thisQuestion.options;
                            regions = thisQuestionSettings.regions;
                            if (regions) {
                                base_label = 'Q' + questionNumber + ' Heatmap; ';
                                for (var i=0, len=regions.length; i < len; i++) {
                                    label = base_label + '\'' + options[i] + '\'';
                                    imageOptions.push({
                                        label: label,
                                        id: thisQuestionID,
                                        region: i
                                    });
                                }
                            }
                        } else {
                            label = 'Q' + questionNumber + ' ' + typesToText[thisQuestion.type];
                            imageOptions.push({
                                label: label,
                                id: thisQuestionID
                            });
                        }
                    }
                }
            }
            
        },

        /**
          * Produce the Options HTML for the Logic Questions dropdown
          */
        logicOptionsHtml: function(questionID, currentPosition) {

            var optionsHtml = '<option value="">select question</option>';

            // Loop through Layout: Build list of all questions which are multichoice, likert, heatmap or number
            // - only include questions earlier in the Layout
            var layout = this.data.layout,
                displayLogic = layout[currentPosition].displayLogic,
                displayLogicID,
                questions = this.data.questions,
                questionNumber,
                qtype,
                label,
                position,
                selected,
                thisQuestion,
                thisQuestionID;

            if (displayLogic) {
                // Current setting to display as selected in dropdown
                displayLogicID = displayLogic.id;
            }

            // Invert questionNumbers array
            var posnToNumber = {};
            for (questionNumber = 1; questionNumber <= Object.keys(questionNumbers).length; questionNumber++) {
                position = questionNumbers[questionNumber];
                posnToNumber[position] = questionNumber;
            }

            for (position=1; position < currentPosition; position++) {
                thisQuestionID = layout[position].id;
                if (thisQuestionID === undefined) {
                    // Instructions or Section Break
                    continue;
                }
                thisQuestion = questions[thisQuestionID];
                qtype = typesToText[thisQuestion.type];
                if ((qtype == 'number') || (qtype == 'multichoice') || (qtype == 'likert') || (qtype == 'heatmap')) {
                    questionNumber = posnToNumber[position];
                    label = 'Q' + questionNumber + ': ' + truncate(thisQuestion.name || '');
                    if (thisQuestionID == displayLogicID) {
                        selected = ' selected';
                    } else {
                        selected = '';
                    }
                    optionsHtml += '<option value="' + thisQuestionID + '"' + selected + '>' + label + '</option>';
                }
            }

            return optionsHtml;
        },

        /**
          * Produce the Sub Options Form for the Display Logic tabs
          */
        logicSubOptions: function(currentPosition, logicQuestionID) {

            var ns = this.eventNamespace,
                self = this,
                displayLogic = this.data.layout[currentPosition].displayLogic,
                logicQuestion = this.data.questions[logicQuestionID],
                type = typesToText[logicQuestion.type];

            if (type == 'number') {
                // Display 2 sets of operator / term
                var displayLogicEquals = '',
                    displayLogicGreaterThan,
                    displayLogicLessThan,
                    value = '';
                if (displayLogic) {
                    displayLogicEquals = displayLogic.eq || '';
                    displayLogicGreaterThan = displayLogic.gt;
                    displayLogicLessThan = displayLogic.lt;
                    if (displayLogicEquals) {
                        value = displayLogicEquals;
                    } else if (displayLogicLessThan) {
                        value = displayLogicLessThan;
                    } else if (displayLogicGreaterThan) {
                        value = displayLogicGreaterThan;
                    }
                }
                var row1 = '<select id="logic-operator-1-' + currentPosition + '">';
                if (!displayLogic || displayLogicEquals) {
                    row1 += '<option value="eq" selected>equal to ( = )</option>';
                } else {
                    row1 += '<option value="eq">equal to ( = )</option>';
                }
                if (displayLogicLessThan) {
                    row1 += '<option value="lt" selected>less than ( &lt; )</option>';
                    row1 += '<option value="gt">more than ( &gt; )</option>';
                } else {
                    row1 += '<option value="lt">less than ( &lt; )</option>';
                    if (displayLogicGreaterThan) {
                        row1 += '<option value="gt" selected>more than ( &gt; )</option>';
                    } else {
                        row1 += '<option value="gt">more than ( &gt; )</option>';
                    }
                }
                row1 += '</select><input id="logic-term-1-' + currentPosition + '" type="number" placeholder="type number" value="' + value + '">';
                $('#logic-response-' + currentPosition).html(row1);

                var hide;
                if (!displayLogicEquals && (displayLogicLessThan || displayLogicGreaterThan)) {
                    hide = '';
                    if (displayLogicLessThan && displayLogicGreaterThan) {
                        value = displayLogicGreaterThan;
                    } else {
                        value = '';
                    }
                } else {
                    value = '';
                    hide = ' hide';
                }
                var optionsHtml;
                if (!displayLogicLessThan && displayLogicGreaterThan) {
                    optionsHtml = '<option value="lt" selected>less than ( &lt; )</option><option value="gt">more than ( &gt; )</option>';
                } else {
                    optionsHtml = '<option value="lt">less than ( &lt; )</option><option value="gt" selected>more than ( &gt; )</option>';
                }
                var row2 = '<div class="row' + hide + '">' +
                            '<div class="columns medium-1"></div>' +
                            '<div class="columns medium-11">' +
                             '<div class="row"><div class="columns medium-2"><label class="fleft">AND</label></div><div class="columns medium-10"><select id="logic-operator-2-' + currentPosition + '">' + optionsHtml + '</select><input id="logic-term-2-' + currentPosition + '" type="number" placeholder="type number" value="' + value + '"></div></div>' +
                            '</div>' +
                           '</div>';
                var logicResponseRow = $('#logic-response-row-' + currentPosition);
                logicResponseRow.after(row2);
                
                // Add Events
                // @ToDo: Add validation that gt/lt cannot be impossible combination
                // @ToDo: Add validation that gt/lt cannot be outside min/max?
                // - listen to operator dropdowns
                var operator,
                    logicOperator1 = $('#logic-operator-1-' + currentPosition),
                    logicOperator2 = $('#logic-operator-2-' + currentPosition);
                var logicTerm1 = $('#logic-term-1-' + currentPosition),
                    logicTerm2 = $('#logic-term-2-' + currentPosition);
                logicOperator1.on('change' + ns, function(/* event */) {
                    operator = $(this).val();
                    value = parseInt(logicTerm1.val());
                    displayLogic = {
                        id: logicQuestionID
                    };
                    if (operator == 'eq') {
                        // Hide row 2
                        logicResponseRow.next().hide();
                        // Update Data
                        if (value) {
                            displayLogic.eq = value;
                        }
                    } else if (operator == 'gt') {
                        // Show row 2
                        logicResponseRow.next().removeClass('hide')
                                               .show();
                        // Set other as lt selected
                        logicOperator2.val('lt');
                        // Update Data
                        if (value) {
                            displayLogic.gt = value;
                        }
                        value = parseInt(logicTerm2.val());
                        if (value) {
                            displayLogic.lt = value;
                        }
                    } else if (operator == 'lt') {
                        // Show row 2
                        logicResponseRow.next().removeClass('hide')
                                               .show();
                        // Set other as gt selected
                        logicOperator2.val('gt');
                        // Update Data
                        if (value) {
                            displayLogic.lt = value;
                        }
                        value = parseInt(logicTerm2.val());
                        if (value) {
                            displayLogic.gt = value;
                        }
                    }
                    self.data.layout[currentPosition].displayLogic = displayLogic;
                    self.saveLayout();
                });
                logicOperator2.on('change' + ns, function(/* event */) {
                    operator = $(this).val();
                    value = logicTerm2.val();
                    displayLogic = {
                        id: logicQuestionID
                    };
                    if (operator == 'gt') {
                        // Set other as lt selected
                        logicOperator1.val('lt');
                        // Update Data
                        if (value) {
                            displayLogic.gt = parseInt(value);
                        }
                        value = logicTerm1.val();
                        if (value) {
                            displayLogic.lt = parseInt(value);
                        }
                    } else if (operator == 'lt') {
                        // Set other as gt selected
                        logicOperator1.val('gt');
                        // Update Data
                        if (value) {
                            displayLogic.lt = value;
                        }
                        value = logicTerm1.val();
                        if (value) {
                            displayLogic.gt = parseInt(value);
                        }
                    }
                    self.data.layout[currentPosition].displayLogic = displayLogic;
                    self.saveLayout();
                });

                // - listen to terms
                logicTerm1.on('change' + ns, function(/* event */) {
                    value = $(this).val();
                    if (value) {
                        // Update Data
                        displayLogic = {
                            id: logicQuestionID
                        };
                        operator = logicOperator1.val();
                        if (operator == 'eq') {
                            displayLogic.eq = parseInt(value);
                        } else {
                            if (operator == 'gt') {
                                displayLogic.gt = parseInt(value);
                            } else {
                                displayLogic.lt = parseInt(value);
                            }
                            value = logicTerm2.val();
                            if (value) {
                                operator = logicOperator2.val();
                                if (operator == 'gt') {
                                    displayLogic.gt = parseInt(value);
                                } else {
                                    displayLogic.lt = parseInt(value);
                                }
                            }
                        }
                        self.data.layout[currentPosition].displayLogic = displayLogic;
                    } else {
                        value = logicTerm2.val();
                        if (value) {
                            // Update Data
                            displayLogic = {
                                id: logicQuestionID
                            };
                            operator = logicOperator1.val();
                            if (operator == 'gt') {
                                displayLogic.gt = parseInt(value);
                            } else {
                                displayLogic.lt = parseInt(value);
                            }
                            self.data.layout[currentPosition].displayLogic = displayLogic;
                        } else {
                            delete self.data.layout[currentPosition].displayLogic;
                        }
                    }
                    // Save Layout
                    self.saveLayout();
                });
                logicTerm2.on('change' + ns, function(/* event */) {
                    value = $(this).val();
                    if (value) {
                        // Update Data
                        displayLogic = {
                            id: logicQuestionID
                        };
                        operator = logicOperator2.val();
                        if (operator == 'gt') {
                            displayLogic.gt = parseInt(value);
                        } else {
                            displayLogic.lt = parseInt(value);
                        }
                        value = logicTerm1.val();
                        if (value) {
                            operator = logicOperator1.val();
                            if (operator == 'gt') {
                                displayLogic.gt = parseInt(value);
                            } else {
                                displayLogic.lt = parseInt(value);
                            }
                        }
                        self.data.layout[currentPosition].displayLogic = displayLogic;
                    } else {
                        value = logicTerm1.val();
                        if (value) {
                            // Update Data
                            displayLogic = {
                                id: logicQuestionID
                            };
                            operator = logicOperator1.val();
                            if (operator == 'eq') {
                                displayLogic.eq = parseInt(value);
                            } else if (operator == 'gt') {
                                displayLogic.gt = parseInt(value);
                            } else {
                                displayLogic.lt = parseInt(value);
                            }
                            self.data.layout[currentPosition].displayLogic = displayLogic;
                        } else {
                            delete self.data.layout[currentPosition].displayLogic;
                        }
                    }
                    // Save Layout
                    self.saveLayout();
                });

                return;

            } else {
                // Display a dropdown of Options for the selected Question

                var label,
                    operator;

                if (type == 'heatmap') {
                    label = 'region';
                    operator = 'selectedRegion';
                } else {
                    // Multichoice or Likert
                    label = 'option';
                    operator = 'eq';
                }

                var displayLogicOption,
                    opt,
                    options = logicQuestion.options,
                    selected,
                    subOptionSelect = '<select id="sub-logic-select-' + currentPosition + '"><option value="">select ' + label + '</option>';

                if (displayLogic) {
                    displayLogicOption = displayLogic[operator];
                }

                for (var i=0, len=options.length; i < len; i++) {
                    if (i == displayLogicOption) {
                        selected = ' selected';
                    } else {
                        selected = '';
                    }
                    subOptionSelect += '<option value="' + i + '"' + selected + '>' + options[i] + '</option>';
                }

                if (type == 'multichoice') {
                    var otherLabel = logicQuestion.settings.other;
                    if (otherLabel) {
                        if (displayLogicOption == '_other') {
                            selected = ' selected';
                        } else {
                            selected = '';
                        }
                        subOptionSelect += '<option value="_other"' + selected + '>' + otherLabel + '</option>';
                    }
                }

                subOptionSelect += '</select>';

                $('#logic-response-' + currentPosition).html(subOptionSelect);

                // Add Events
                // - listen to dropdown of options
                $('#sub-logic-select-' + currentPosition).on('change' + ns, function(/* event */) {
                    // Update Data
                    var newDisplayLogic = {
                        id: logicQuestionID,
                    };
                    newDisplayLogic[operator] = parseInt($(this).val());
                    self.data.layout[currentPosition].displayLogic = newDisplayLogic;
                    // Save Layout
                    self.saveLayout();
                });
            }
        },

        /**
          * Display Logic Selector changed
          */
        logicSelected: function(logicSelect, currentPosition) {

            var value = logicSelect.val();

            // Clear any previous 2nd select
            $('#logic-response-' + currentPosition).empty();

            // Clear any previous additional row (for Number Conditions)
            $('#logic-response-row-' + currentPosition).next().remove();

            if (value) {
                // Show 2nd select
                this.logicSubOptions(currentPosition, parseInt(value));
            } else {
                // Update Data
                delete this.data.layout[currentPosition].displayLogic;
                // Save Layout
                this.saveLayout();
            }
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
                        // Update questions lookup
                        delete self.data.questions[questionID].file;
                        // Clean up imageFiles
                        delete imageFiles[questionID];
                        // Update imageOptions
                        self.updateImageOptions(false, questionID);
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
        addSectionBreak: function(newPosition, page, load) {

            var ns = this.eventNamespace,
                thisElements = 0,
                thisElementsText;

            if (newPosition == 0) {
                // 1st section break
                pages[1] = newPosition;
                var layout = this.data.layout,
                    layoutLength = Object.keys(layout).length;
                    
                if (layoutLength) {
                    // We're loading, so find how many elements on this page
                    var item;
                    for (var position=1; position <= layoutLength; position++) {
                        item = layout[position];
                        if (item.type == 'break') {
                            // Stop iteration
                            break;
                        } else {
                            thisElements++;
                        }
                    }
                } else {
                    // Empty Survey
                    //thisElements = 0;
                }
                pageElements[1] = thisElements;
                if (thisElements == 1) {
                    thisElementsText = '1 ELEMENT';
                } else {
                    thisElementsText = thisElements + ' ELEMENTS';
                }
                var sectionBreak = '<div class="row"><div class="section-break medium-11 columns" id="section-break-0" data-page="1"><span>PAGE 1 (' + thisElementsText + ')</span></div><div class="medium-1 columns"><i class="ucce ucce-up-alt"> </i></div></div>';
                $(this.element).parent().append(sectionBreak);

            } else {

                page++;

                if (load) {
                    // We're loading, so find how many elements on this page
                    var item,
                        layout = this.data.layout,
                        layoutLength = Object.keys(layout).length;
                    for (var position=newPosition + 1; position <= layoutLength; position++) {
                        item = layout[position];
                        if (item.type == 'break') {
                            // Stop iteration
                            break;
                        } else {
                            thisElements++;
                        }
                    }
                    pageElements[page] = thisElements;
                    pages[page] = newPosition;
                } else {
                    this.rePosition({type: 'break'}, null, newPosition);
                    thisElements = pageElements[page];
                }

                var delete_btn,
                    readOnly = this.options.readOnly;

                if (readOnly) {
                    delete_btn = '';
                } else {
                    delete_btn = '<i class="ucce ucce-delete-page"> </i>';
                }

                if (thisElements == 1) {
                    thisElementsText = '1 ELEMENT';
                } else {
                    thisElementsText = thisElements + ' ELEMENTS';
                }

                var sectionBreak = '<div class="row"><div class="section-break medium-11 columns" id="section-break-' + newPosition + '" data-page="' + page + '"><span>PAGE ' + page + ' (' + thisElementsText + ')</span></div><div class="medium-1 columns">' + delete_btn + '<i class="ucce ucce-up-alt"> </i></div></div>';

                if (readOnly) { 
                    // Place after other elements
                    $(this.element).parent().append(sectionBreak);
                } else {
                    var layout = this.data.layout;
                    if (load || newPosition == Object.keys(layout).length) {
                        // Place before droppable
                        $('#survey-droppable').before(sectionBreak);
                    } else {
                        // Place after previous element
                        var previousPosition = newPosition - 1,
                            previousItem = layout[previousPosition];
                        if (previousItem.type == 'break') {
                            $('#section-break-' + previousPosition).parent().after(sectionBreak);
                        } else if (previousItem.type == 'instructions') {
                            $('#instructions-' + previousPosition).after(sectionBreak);
                        } else {
                            // Question
                            $('#question-' + previousItem.id).after(sectionBreak);
                        }
                    }
                    // Events
                    var self = this;
                    $('#section-break-' + newPosition).next().children('.ucce-delete-page').on('click' + ns, function(/* event */){
                        // Delete this section-break

                        // Read the page & position (can't trust originals as they may have changed)
                        var $el = $(this).parent().prev(),
                            currentPage = $el.data('page'),
                            currentPosition = parseInt($el.attr('id').split('-')[2]);

                        self.deleteSectionBreak(currentPage, currentPosition);

                    });
                }
            }
            $('#section-break-' + newPosition).next().children('.ucce-up-alt').on('click' + ns, function(/* event */){
                var $this = $(this),
                    currentPage = $this.parent().prev().data('page');
                
                if ($this.hasClass('ucce-up-alt')) {
                    // Hide elements on this page
                    // NB This selector requires HTML attr to be modified when changing data, not just .data()
                    $('.survey-item[data-page="' + currentPage + '"]').hide();

                    // Change arrow
                    $this.removeClass('ucce-up-alt')
                         .addClass('ucce-down-alt');
                } else {
                    // Show elements on this page
                    // NB This selector requires HTML attr to be modified when changing data, not just .data()
                    $('.survey-item[data-page="' + currentPage + '"]').show();

                    // Change arrow
                    $this.removeClass('ucce-down-alt')
                         .addClass('ucce-up-alt');
                }
            });
        },

        /**
          * Delete a Section Break
          */
        deleteSectionBreak: function(currentPage, currentPosition) {

            // Show elements on this page
            // NB This selector requires HTML attr to be modified when changing data, not just .data()
            $('.survey-item[data-page="' + currentPage + '"]').show();

            // Update layout & all subsequent items in it
            this.rePosition({type: 'break'}, currentPosition, null);

            // Remove from DOM
            $('#section-break-' + currentPosition).parent().remove();
        },

        /**
          * Reposition elements in the layout
          * - Move - both currentPosition & newPosition not-null
          * - Add - currentPosition is null
          * - Delete - newPosition is null
          */
        rePosition: function(item, currentPosition, newPosition) {

            var itemType = item.type,
                questionID,
                layout = this.data.layout,
                layoutLength = Object.keys(layout).length,
                pagesLength = Object.keys(pages).length,
                currentPage,
                newPage,
                oldQuestionNumber,
                newQuestionNumber,
                thisElements,
                thisElementsText;

            if (itemType == 'question') {
                questionID = item.id;
            }

            if (currentPosition) {
                if (itemType == 'instructions') {
                    currentPage = $('#instructions-' + currentPosition).data('page');
                } else if (itemType == 'question') {
                    var oldElement = $('#question-' + questionID);
                    currentPage = oldElement.data('page');
                    oldQuestionNumber = oldElement.data('number');
                } else if (itemType == 'break') {
                    currentPage = $('#section-break-' + currentPosition).data('page');
                }
            }

            if (newPosition) {
                if (newPosition == 1) {
                    // 1st item, so no previousItem
                    newPage = 1;
                    newQuestionNumber = 1;
                } else {
                    var previousPosition;
                    
                    if (currentPosition == newPosition - 1) {
                        // moveDown (by 1)
                        previousPosition = newPosition;
                    } else {
                        previousPosition = newPosition - 1;
                    }
                    var previousItem = layout[previousPosition],
                        previousType = previousItem.type;

                    if (previousType == 'instructions') {
                        newPage = $('#instructions-' + previousPosition).data('page');
                    } else if (previousType == 'question') {
                        var previousQuestionID = previousItem.id,
                            previousElement = $('#question-' + previousQuestionID);
                        newPage = previousElement.data('page');
                        var previousQuestionNumber = previousElement.data('number');
                        newQuestionNumber = previousQuestionNumber + 1;
                    } else if (previousType == 'break') {
                        newPage = $('#section-break-' + previousPosition).data('page');
                    }

                    if (itemType == 'question') {
                        var questionNumbersLength = Object.keys(questionNumbers).length;
                        if (questionNumbersLength) {
                            if (newPosition > layoutLength) {
                                // Final item
                                if (currentPosition) {
                                    // Move, so this becomes final
                                    newQuestionNumber = questionNumbersLength;
                                } else {
                                    // Create, so this is appended to final
                                    newQuestionNumber = questionNumbersLength + 1;
                                }
                            } else {
                                // Locate the previous Question in the layout
                                var thisItem;
                                for (var p=newPosition - 1; p > 0; p--) {
                                    thisItem = layout[p];
                                    if (thisItem.type == 'question') {
                                        var previousQuestionID = thisItem.id,
                                            previousQuestionNumber = $('#question-' + previousQuestionID).data('number');
                                        newQuestionNumber = previousQuestionNumber + 1;
                                        break;
                                    }
                                }
                                if (!newQuestionNumber) {
                                    // Existing Questions must only be later in the layout
                                    newQuestionNumber = 1;
                                }
                            }
                        } else {
                            // First Question
                            newQuestionNumber = 1;
                        }
                    }
                }
                if (itemType == 'break') {
                    newPage++;
                }
            }

            // Update Layout
            if (currentPosition && newPosition) {
                // Move
                if (currentPosition == newPosition - 1 || currentPosition == newPosition + 1) {
                    // moveDown (by 1) or moveUp (by 1)
                    var swapItem = layout[newPosition],
                        swapItemType = swapItem.type;

                    if (swapItemType == 'break') {

                        var currentItem = layout[currentPosition],
                            $currentItem,
                            oldHref,
                            newHref;

                        // Swap items in layout
                        layout[currentPosition] = swapItem;
                        layout[newPosition] = currentItem;

                        if (oldQuestionNumber) {
                            $currentItem = $('#question-' + questionID);
                        } else {
                            $currentItem = $('#instructions-' + currentPosition);
                        }

                        // Update Pages
                        $currentItem.data('page', newPage);
                        $currentItem.attr('data-page', newPage); // Update attribute too so that show/hide page works

                        $('#section-break-' + newPosition).attr('id', 'section-break-' + currentPosition);
                        if (currentPosition == newPosition - 1) {
                            // moveDown
                            pages[newPage] = currentPosition;
                        } else {
                            // moveUp
                            pages[currentPage] = currentPosition;
                        }
                        pageElements[currentPage] --;
                        pageElements[newPage] ++;
                        // Update visual elements
                        thisElements = pageElements[currentPage];
                        if (thisElements == 1) {
                            thisElementsText = '1 ELEMENT';
                        } else {
                            thisElementsText = thisElements + ' ELEMENTS';
                        }
                        $('#section-break-' + pages[currentPage] + ' > span').html('PAGE ' + currentPage + ' (' + thisElementsText + ')');
                        thisElements = pageElements[newPage];
                        if (thisElements == 1) {
                            thisElementsText = '1 ELEMENT';
                        } else {
                            thisElementsText = thisElements + ' ELEMENTS';
                        }
                        $('#section-break-' + pages[newPage] + ' > span').html('PAGE ' + newPage + ' (' + thisElementsText + ')');

                        // Update IDs
                        if (itemType == 'instructions') {
                            $('#instructions-' + currentPosition).attr('id', 'instructions-' + newPosition);
                            $('#do-' + currentPosition).attr('id', 'do-' + newPosition);
                            $('#say-' + currentPosition).attr('id', 'say-' + newPosition);
                            $('#do-l10n-' + currentPosition).attr('id', 'do-' + newPosition);
                            $('#say-l10n-' + currentPosition).attr('id', 'say-' + newPosition);
                        } else {
                            // questionNumber unchanged but position has
                            questionNumbers[oldQuestionNumber] = newPosition;
                        }
                        // Update Tab contents
                        $('#edit-' + currentPosition).attr('id', 'edit-' + newPosition);
                        $('#logic-' + currentPosition).attr('id', 'logic-' + newPosition);
                        $('#logic-select-' + currentPosition).attr('id', 'logic-select-' + newPosition);
                        $('#sub-logic-select-' + currentPosition).attr('id', 'sub-logic-select-' + newPosition);
                        $('#logic-response-' + currentPosition).attr('id', 'logic-response-' + newPosition);
                        $('#logic-response-row-' + currentPosition).attr('id', 'logic-response-row-' + newPosition);
                        $('#logic-operator-1-' + currentPosition).attr('id', 'logic-operator-1-' + newPosition);
                        $('#logic-operator-2-' + currentPosition).attr('id', 'logic-operator-2-' + newPosition);
                        $('#logic-term-1-' + currentPosition).attr('id', 'logic-term-1-' + newPosition);
                        $('#logic-term-2-' + currentPosition).attr('id', 'logic-term-2-' + newPosition);
                        $('#translation-' + currentPosition).attr('id', 'translation-' + newPosition);
                        // Update links to Tabs
                        $currentItem.find('li.tab-title > a').each(function() {
                            var $this = $(this);
                            oldHref = $this.attr('href');
                            newHref = oldHref.split('-')[0];
                            newHref = newHref.substring(1, newHref.length);
                            $this.attr('href', '#' + newHref + '-' + newPosition);
                        });

                    } else {
                        // Simple swap of items (no need to touch pages)
                        var currentItem = layout[currentPosition];
                        layout[currentPosition] = swapItem;
                        layout[newPosition] = currentItem;

                        var $currentItem,
                            $swapItem,
                            oldHref,
                            newHref,
                            swapQuestionID = swapItem.id;

                        if (oldQuestionNumber) {
                            $currentItem = $('#question-' + questionID);
                        } else {
                            $currentItem = $('#instructions-' + currentPosition);
                        }

                        if (swapItemType == 'question') {
                            $swapItem = $('#question-' + swapQuestionID);
                        } else {
                            $swapItem = $('#instructions-' + newPosition);
                        }

                        if (oldQuestionNumber && swapItemType == 'question') {
                            // Swap Question Numbers (no need to update questionNumbers as that remains the same)

                            $currentItem.data('number', newQuestionNumber);
                            //$currentItem.attr('data-number', newQuestionNumber);
                            // Update visual elements
                            $('#qlabel-' + questionID).html('Q' + newQuestionNumber);
                            $('#qlabel-l10n-' + questionID).html('Q' + newQuestionNumber);

                            $swapItem.data('number', oldQuestionNumber);
                            //$swapItem.attr('data-number', oldQuestionNumber);
                            // Update visual elements
                            $('#qlabel-' + swapQuestionID).html('Q' + oldQuestionNumber);
                            $('#qlabel-l10n-' + swapQuestionID).html('Q' + oldQuestionNumber);
                        } else {
                            if (oldQuestionNumber) {
                                // questionNumber unchanged but position has
                                questionNumbers[oldQuestionNumber] = newPosition;
                            } else if (swapItemType == 'question') {
                                // questionNumber unchanged but position has
                                var swapQuestionNumber = $swapItem.data('number');
                                questionNumbers[swapQuestionNumber] = currentPosition;
                            }
                        }

                        // Update swapItem IDs to an interim value
                        if (swapItemType == 'instructions') {
                            $('#instructions-' + newPosition).attr('id', 'instructions-' + 'interim');
                            $('#do-' + newPosition).attr('id', 'do-' + 'interim');
                            $('#say-' + newPosition).attr('id', 'say-' + 'interim');
                            $('#do-l10n-' + newPosition).attr('id', 'do-' + 'interim');
                            $('#say-l10n-' + newPosition).attr('id', 'say-' + 'interim');
                        }
                        // Update Tab contents
                        $('#edit-' + newPosition).attr('id', 'edit-' + 'interim');
                        $('#logic-' + newPosition).attr('id', 'logic-' + 'interim');
                        $('#logic-select-' + newPosition).attr('id', 'logic-select-' + 'interim');
                        $('#logic-response-' + newPosition).attr('id', 'logic-response-' + 'interim');
                        $('#logic-response-row-' + newPosition).attr('id', 'logic-response-row-' + 'interim');
                        $('#sub-logic-select-' + newPosition).attr('id', 'sub-logic-select-' + 'interim');
                        $('#logic-operator-1-' + newPosition).attr('id', 'logic-operator-1-' + 'interim');
                        $('#logic-operator-2-' + newPosition).attr('id', 'logic-operator-2-' + 'interim');
                        $('#logic-term-1-' + newPosition).attr('id', 'logic-term-1-' + 'interim');
                        $('#logic-term-2-' + newPosition).attr('id', 'logic-term-2-' + 'interim');
                        $('#translation-' + newPosition).attr('id', 'translation-' + 'interim');

                        // Update currentItem IDs to swapItem values
                        if (itemType == 'instructions') {
                            $('#instructions-' + currentPosition).attr('id', 'instructions-' + newPosition);
                            $('#do-' + currentPosition).attr('id', 'do-' + newPosition);
                            $('#say-' + currentPosition).attr('id', 'say-' + newPosition);
                            $('#do-l10n-' + currentPosition).attr('id', 'do-' + newPosition);
                            $('#say-l10n-' + currentPosition).attr('id', 'say-' + newPosition);
                        }
                        // Update Tab contents
                        $('#edit-' + currentPosition).attr('id', 'edit-' + newPosition);
                        $('#logic-' + currentPosition).attr('id', 'logic-' + newPosition);
                        $('#logic-select-' + currentPosition).attr('id', 'logic-select-' + newPosition);
                        $('#logic-response-' + currentPosition).attr('id', 'logic-response-' + newPosition);
                        $('#logic-response-row-' + currentPosition).attr('id', 'logic-response-row-' + newPosition);
                        $('#sub-logic-select-' + currentPosition).attr('id', 'sub-logic-select-' + newPosition);
                        $('#logic-operator-1-' + currentPosition).attr('id', 'logic-operator-1-' + newPosition);
                        $('#logic-operator-2-' + currentPosition).attr('id', 'logic-operator-2-' + newPosition);
                        $('#logic-term-1-' + currentPosition).attr('id', 'logic-term-1-' + newPosition);
                        $('#logic-term-2-' + currentPosition).attr('id', 'logic-term-2-' + newPosition);
                        $('#translation-' + currentPosition).attr('id', 'translation-' + newPosition);
                        // Update links to Tabs
                        $currentItem.find('li.tab-title > a').each(function() {
                            var $this = $(this);
                            oldHref = $this.attr('href');
                            newHref = oldHref.split('-')[0];
                            newHref = newHref.substring(1, newHref.length);
                            $this.attr('href', '#' + newHref + '-' + newPosition);
                        });

                        // Update swapItem IDs to currentItem values
                        if (swapItemType == 'instructions') {
                            $('#instructions-' + 'interim').attr('id', 'instructions-' + currentPosition);
                            $('#do-' + 'interim').attr('id', 'do-' + currentPosition);
                            $('#say-' + 'interim').attr('id', 'say-' + currentPosition);
                            $('#do-l10n-' + 'interim').attr('id', 'do-' + currentPosition);
                            $('#say-l10n-' + 'interim').attr('id', 'say-' + currentPosition);
                        }
                        // Update Tab contents
                        $('#edit-' + 'interim').attr('id', 'edit-' + currentPosition);
                        $('#logic-' + 'interim').attr('id', 'logic-' + currentPosition);
                        $('#logic-select-' + 'interim').attr('id', 'logic-select-' + currentPosition);
                        $('#logic-response-' + 'interim').attr('id', 'logic-response-' + currentPosition);
                        $('#logic-response-row-' + 'interim').attr('id', 'logic-response-row-' + currentPosition);
                        $('#sub-logic-select-' + 'interim').attr('id', 'sub-logic-select-' + currentPosition);
                        $('#logic-operator-1-' + 'interim').attr('id', 'logic-operator-1-' + currentPosition);
                        $('#logic-operator-2-' + 'interim').attr('id', 'logic-operator-2-' + currentPosition);
                        $('#logic-term-1-' + 'interim').attr('id', 'logic-term-1-' + currentPosition);
                        $('#logic-term-2-' + 'interim').attr('id', 'logic-term-2-' + currentPosition);
                        $('#translation-' + 'interim').attr('id', 'translation-' + currentPosition);
                        // Update links to Tabs
                        $swapItem.find('li.tab-title > a').each(function() {
                            var $this = $(this);
                            oldHref = $this.attr('href');
                            newHref = oldHref.split('-')[0];
                            newHref = newHref.substring(1, newHref.length);
                            $this.attr('href', '#' + newHref + '-' + currentPosition);
                        });

                        // Remove any outdated displayLogic
                        if (currentPosition == newPosition - 1) {
                            // moveDown
                            if (questionID && swapItem.displayLogic && swapItem.displayLogic.id == questionID) {
                                delete swapItem.displayLogic;
                                $('#logic-select-' + currentPosition).val('')
                                                                     .trigger('change');
                            }
                        } else {
                            // moveUp
                            if (swapQuestionID && currentItem.displayLogic && currentItem.displayLogic.id == swapQuestionID) {
                                delete currentItem.displayLogic;
                                $('#logic-select-' + newPosition).val('')
                                                                 .trigger('change');
                            }
                        }
                        
                    }
                } else {
                    // @ToDo (beyond requirements for UCCE)
                }

                // Update the ImageOptions lookup
                this.updateImageOptions();

            } else if (newPosition) {
                // Create
                if (itemType == 'break') {
                    if (newPosition > layoutLength) {
                        // New Section Break at the end of the Survey
                        pages[newPage] = newPosition;
                        pageElements[newPage] = 0;
                    } else {
                        // Not the final element, so:
                        // Update subsequent pages & their pageElements
                        for (var i=pagesLength; i >= newPage ; i--) {
                            pages[i + 1] = pages[i] + 1; // newPosition
                            pageElements[i + 1] = pageElements[i];
                        }
                        // Store this page
                        pages[newPage] = newPosition;
                        // Update pageElements for newPage & previousPage
                        var previousPage = newPage - 1,
                            previousPagePosition = pages[previousPage], 
                            previousPageElements = newPosition - previousPagePosition - 1,
                            newPageElements;
                        if (previousPageElements < 0){
                            previousPageElements = 0;
                        }
                        newPageElements = pageElements[previousPage] - previousPageElements;
                        pageElements[previousPage] = previousPageElements;
                        pageElements[newPage] = newPageElements;
                        if (previousPageElements == 1) {
                            thisElementsText = '1 ELEMENT';
                        } else {
                            thisElementsText = previousPageElements + ' ELEMENTS';
                        }
                        $('#section-break-' + previousPagePosition + ' > span').html('PAGE ' + previousPage + ' (' + thisElementsText + ')');
                    }
                } else {
                    // Question/Instructions

                    // Update the elements on the section
                    pageElements[newPage]++;
                    var pagePosition = pages[newPage];
                    thisElements = pageElements[newPage];
                    if (thisElements == 1) {
                        thisElementsText = '1 ELEMENT';
                    } else {
                        thisElementsText = thisElements + ' ELEMENTS';
                    }
                    $('#section-break-' + pagePosition + ' > span').html('PAGE ' + newPage + ' (' + thisElementsText + ')');

                    if (newPage != pagesLength) {
                        // Not the final page, so:
                        // Update page positions for all subsequent pages
                        for (var i=newPage + 1; i >= pagesLength ; i--) {
                            pages[i]++; // newPosition
                        }
                    }
                }
                if (newPosition <= layoutLength) {
                    // Not added at the end of the Survey
                    // Update Layout & all subsequent items in it
                    // @ToDo: DRY with Delete? (That loops upward from currentPosition)
                    var thisItem,
                        $thisItem,
                        thisPage,
                        thisNewPosition,
                        oldPosition,
                        oldHref,
                        newHref,
                        thisQuestionID,
                        thisNewQuestionNumber,
                        thisOldQuestionNumber;
                    for (var i=layoutLength; i >= newPosition; i--) {
                        oldPosition = i;
                        thisNewPosition = i + 1;
                        thisItem = layout[oldPosition];
                        // Move item to it's new position in the layout
                        layout[thisNewPosition] = thisItem;
                        if (thisItem.type == 'break') {
                            if (itemType == 'break') {
                                $thisItem = $('#section-break-' + oldPosition);
                                // Read Page
                                thisPage = $thisItem.data('page') + 1;
                                // Update Page
                                $thisItem.data('page', thisPage);
                                //$thisItem.attr('data-page', thisPage); // Section Breaks not affected by show/hide page
                                // Update visual elements
                                thisElements = pageElements[thisPage];
                                if (thisElements == 1) {
                                    thisElementsText = '1 ELEMENT';
                                } else {
                                    thisElementsText = thisElements + ' ELEMENTS';
                                }
                                $('#section-break-' + oldPosition + ' > span').html('PAGE ' + thisPage + ' (' + thisElementsText + ')');
                            }
                            // Update ID
                            $('#section-break-' + oldPosition).attr('id', 'section-break-' + thisNewPosition);
                        } else {
                            if (thisItem.type == 'question') {
                                thisQuestionID = thisItem.id;
                                $thisItem = $('#question-' + thisQuestionID);

                                // Update questionNumbers
                                thisOldQuestionNumber = $thisItem.data('number');
                                if (itemType == 'question') {
                                    // Question added so need to update numbers

                                    // Update questionNumber
                                    thisNewQuestionNumber = thisOldQuestionNumber + 1;
                                    $thisItem.data('number', thisNewQuestionNumber);
                                    //$thisItem.attr('data-number', thisNewQuestionNumber);
                                    // Update visual elements
                                    $('#qlabel-' + thisQuestionID).html('Q' + thisNewQuestionNumber);
                                    $('#qlabel-l10n-' + thisQuestionID).html('Q' + thisNewQuestionNumber);
                                } else {
                                    thisNewQuestionNumber = thisOldQuestionNumber;
                                }
                                // Update position
                                questionNumbers[thisNewQuestionNumber] = thisNewPosition;
                            } else {
                                // Instructions
                                $thisItem = $('#instructions-' + thisNewPosition);

                                // Update IDs
                                $('#instructions-' + oldPosition).attr('id', 'instructions-' + thisNewPosition);
                                $('#do-' + oldPosition).attr('id', 'do-' + thisNewPosition);
                                $('#say-' + oldPosition).attr('id', 'say-' + thisNewPosition);
                                $('#do-l10n-' + oldPosition).attr('id', 'do-' + thisNewPosition);
                                $('#say-l10n-' + oldPosition).attr('id', 'say-' + thisNewPosition);
                            }

                            if (itemType == 'break') {
                                // Read Page
                                thisPage = $thisItem.data('page') + 1;
                                // Update Page
                                $thisItem.data('page', thisPage);
                                $thisItem.attr('data-page', thisPage); // Update attribute too so that show/hide page works
                            }

                            // Update Tab contents
                            $('#edit-' + oldPosition).attr('id', 'edit-' + thisNewPosition);
                            $('#logic-' + oldPosition).attr('id', 'logic-' + thisNewPosition);
                            $('#logic-select-' + oldPosition).attr('id', 'logic-select-' + thisNewPosition);
                            $('#logic-response-' + oldPosition).attr('id', 'logic-response-' + thisNewPosition);
                            $('#logic-response-row-' + oldPosition).attr('id', 'logic-response-row-' + thisNewPosition);
                            $('#sub-logic-select-' + oldPosition).attr('id', 'sub-logic-select-' + thisNewPosition);
                            $('#logic-operator-1-' + oldPosition).attr('id', 'logic-operator-1-' + thisNewPosition);
                            $('#logic-operator-2-' + oldPosition).attr('id', 'logic-operator-2-' + thisNewPosition);
                            $('#logic-term-1-' + oldPosition).attr('id', 'logic-term-1-' + thisNewPosition);
                            $('#logic-term-2-' + oldPosition).attr('id', 'logic-term-2-' + thisNewPosition);
                            $('#translation-' + oldPosition).attr('id', 'translation-' + thisNewPosition);

                            // Update links to Tabs
                            $thisItem.find('li.tab-title > a').each(function() {
                                var $this = $(this);
                                oldHref = $this.attr('href');
                                newHref = oldHref.split('-')[0];
                                newHref = newHref.substring(1, newHref.length);
                                $this.attr('href', '#' + newHref + '-' + thisNewPosition);
                            });
                        }
                    }
                }
                // Insert into correct position in the layout
                layout[newPosition] = item;

                if (itemType == 'question') {
                    questionNumbers[newQuestionNumber] = newPosition;
                    if (newPosition <= layoutLength) {
                        // Not added at the end of the Survey, so imageOptions needs updating for amended questionNumbers
                        this.updateImageOptions();
                    }
                }

            } else {
                // Delete
                if (itemType == 'break') {
                    // Fix the Pages
                    var currentPageElements = pageElements[currentPage];
                    if (currentPageElements) {
                        // Update elements on previous section-break
                        var previousPage = currentPage - 1;
                        pageElements[previousPage] += currentPageElements;
                        var previousPagePosition = pages[previousPage];
                        thisElements = pageElements[previousPage];
                        if (thisElements == 1) {
                            thisElementsText = '1 ELEMENT';
                        } else {
                            thisElementsText = thisElements + ' ELEMENTS';
                        }
                        $('#section-break-' + previousPagePosition + ' > span').html('PAGE ' + previousPage + ' (' + thisElementsText + ')');
                    }

                    // Update subsequent pages & pageElements
                    for (var i=currentPage; i < pagesLength; i++) {
                        pages[i] = pages[i + 1] - 1; // newPosition
                        pageElements[i] = pageElements[i + 1];
                    }
                    delete pages[pagesLength];
                    delete pageElements[pagesLength];

                } else {
                    // Question/Instructions

                    // Update this pageElements
                    pageElements[currentPage]--;
                    // Update visual elements
                    thisElements = pageElements[currentPage];
                    if (thisElements == 1) {
                        thisElementsText = '1 ELEMENT';
                    } else {
                        thisElementsText = thisElements + ' ELEMENTS';
                    }
                    $('#section-break-' + pages[currentPage] + ' > span').html('PAGE ' + currentPage + ' (' + thisElementsText + ')');

                    // Update subsequent pages
                    for (var i=currentPage + 1; i <= pagesLength; i++) {
                        pages[i]--; // newPosition
                    }
                }
                
                if (currentPosition != layoutLength) {
                    // Not the final item in the layout, so:
                    // Update Layout & all subsequent items in it
                    // @ToDo: DRY with Create? (That loops downward to newPosition)
                    var thisItem,
                        $thisItem,
                        thisPage,
                        thisNewPosition,
                        oldPosition,
                        oldHref,
                        newHref,
                        thisQuestionID,
                        thisQuestionNumber;
                    for (var i=currentPosition; i < layoutLength; i++) {
                        oldPosition = i + 1;
                        thisNewPosition = i;
                        thisItem = layout[oldPosition];
                        // Move item to it's new position in the layout
                        layout[thisNewPosition] = thisItem;
                        if (thisItem.type == 'break') {
                            if (itemType == 'break') {
                                // Read Page
                                thisPage = $('#section-break-' + oldPosition).data('page') - 1;
                                // Update Page
                                $('#section-break-' + oldPosition).data('page', thisPage);
                                //$('#section-break-' + oldPosition).attr('data-page', thisPage); // Section Breaks not affected by show/hide page
                                // Update visual elements
                                thisElements = pageElements[thisPage];
                                if (thisElements == 1) {
                                    thisElementsText = '1 ELEMENT';
                                } else {
                                    thisElementsText = thisElements + ' ELEMENTS';
                                }
                                $('#section-break-' + oldPosition + ' > span').html('PAGE ' + thisPage + ' (' + thisElementsText + ')');
                            }
                            // Update ID
                            $('#section-break-' + oldPosition).attr('id', 'section-break-' + thisNewPosition);
                        } else {
                            if (thisItem.type == 'question') {
                                thisQuestionID = thisItem.id;
                                $thisItem = $('#question-' + thisQuestionID);

                                // Update questionNumbers
                                thisQuestionNumber = $thisItem.data('number');
                                if (itemType == 'question') {
                                    // Question deleted so need to update both numbers & positions

                                    // Update questionNumber
                                    newQuestionNumber = thisQuestionNumber - 1;
                                    $thisItem.data('number', newQuestionNumber);
                                    //$thisItem.attr('data-number', newQuestionNumber);
                                    // Update visual elements
                                    $('#qlabel-' + thisQuestionID).html('Q' + newQuestionNumber);
                                    $('#qlabel-l10n-' + thisQuestionID).html('Q' + newQuestionNumber);
                                }
                                // Update position
                                questionNumbers[thisQuestionNumber] = thisNewPosition;
                            } else {
                                // Instructions
                                $thisItem = $('#instructions-' + thisNewPosition);

                                // Update IDs
                                $('#instructions-' + oldPosition).attr('id', 'instructions-' + thisNewPosition);
                                $('#do-' + oldPosition).attr('id', 'do-' + thisNewPosition);
                                $('#say-' + oldPosition).attr('id', 'say-' + thisNewPosition);
                                $('#do-l10n-' + oldPosition).attr('id', 'do-' + thisNewPosition);
                                $('#say-l10n-' + oldPosition).attr('id', 'say-' + thisNewPosition);
                            }

                            if (itemType == 'break') {
                                // Read Page
                                thisPage = $thisItem.data('page') - 1;
                                // Update Page
                                $thisItem.data('page', thisPage);
                                $thisItem.attr('data-page', thisPage); // Update attribute too so that show/hide page works
                            }

                            // Update Tab contents
                            $('#edit-' + oldPosition).attr('id', 'edit-' + thisNewPosition);
                            $('#logic-' + oldPosition).attr('id', 'logic-' + thisNewPosition);
                            $('#logic-select-' + oldPosition).attr('id', 'logic-select-' + thisNewPosition);
                            $('#logic-response-' + oldPosition).attr('id', 'logic-response-' + thisNewPosition);
                            $('#logic-response-row-' + oldPosition).attr('id', 'logic-response-row-' + thisNewPosition);
                            $('#sub-logic-select-' + oldPosition).attr('id', 'sub-logic-select-' + thisNewPosition);
                            $('#logic-operator-1-' + oldPosition).attr('id', 'logic-operator-1-' + thisNewPosition);
                            $('#logic-operator-2-' + oldPosition).attr('id', 'logic-operator-2-' + thisNewPosition);
                            $('#logic-term-1-' + oldPosition).attr('id', 'logic-term-1-' + thisNewPosition);
                            $('#logic-term-2-' + oldPosition).attr('id', 'logic-term-2-' + thisNewPosition);
                            $('#translation-' + oldPosition).attr('id', 'translation-' + thisNewPosition);

                            // Update links to Tabs
                            $thisItem.find('li.tab-title > a').each(function() {
                                var $this = $(this);
                                oldHref = $this.attr('href');
                                newHref = oldHref.split('-')[0];
                                newHref = newHref.substring(1, newHref.length);
                                $this.attr('href', '#' + newHref + '-' + thisNewPosition);
                            });

                            // Remove any outdated displayLogic
                            if (questionID && thisItem.displayLogic && thisItem.displayLogic.id == questionID) {
                                delete thisItem.displayLogic;
                                $('#logic-select-' + thisNewPosition).val('')
                                                                     .trigger('change');
                            }
                        }
                    }
                }

                // Remove final item from layout (we've already copied it to the previous position)
                delete layout[layoutLength];

                if (itemType == 'question') {
                    // Remove final questionNumber from questionNumbers
                    delete questionNumbers[Object.keys(questionNumbers).length];
                    // Clean up imageFiles
                    delete imageFiles[questionID];
                }
                // Update the ImageOptions lookup
                this.updateImageOptions(false, questionID);
            }

            // Save Layout
            this.saveLayout();
        },

        /**
          * Add a new Droppable section at the end of the Survey
          * - only done once
          */
        droppable: function() {
            var self = this,
                layout = this.data.layout,
                droppable = '<div id="survey-droppable"><span>Drag and drop questions here</span></div>';
            $(this.element).parent().append(droppable);

            // (Drag)'n'Drop
            $('#survey-droppable').droppable({
                drop: function(event, ui) {
                    // Open QuestionEditorWidget with correct options for type
                    var type = ui.draggable[0].id,
                        currentPosition = Object.keys(layout).length + 1,
                        currentPage = Object.keys(pages).length;
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

            var deleted,
                item,
                page = 1,
                position,
                questionID,
                label,
                layoutLength = Object.keys(layout).length,
                questions = this.data.questions,
                thisQuestion;

            // Loop through layout to find any deleted Questions
            for (position=1; position <= layoutLength; position++) {
                item = layout[position];
                if (item.type == 'question') {
                    // Question
                    questionID = item.id;
                    thisQuestion = questions[questionID];
                    if (thisQuestion === undefined) {
                        // Deleted Question! (e.g. 2 people editing the survey at the same time?)
                        delete layout[position];
                        deleted = true;
                    }
                }
            }

            if (deleted) {
                // Loop through layout to reposition elements after the deleted Questions
                var i,
                    oldPosition,
                    newPosition;
                for (position=1; position <= layoutLength; position++) {
                    if (layout[position] === undefined) {
                        for (i=position; i < layoutLength; i++) {
                            // Move item to it's new position in the layout
                            oldPosition = i + 1;
                            newPosition = i;
                            item = layout[oldPosition];
                            if (item === undefined) {
                                // Next Item is also deleted so get from next place up
                                oldPosition = i + 2;
                                item = layout[oldPosition];
                                if ((item === undefined) && (oldPosition < layoutLength)) {
                                    // Next Item is also deleted so get from next place up
                                    oldPosition = i + 3;
                                    item = layout[oldPosition];
                                    if ((item === undefined) && (oldPosition < layoutLength)) {
                                        // Next Item is also deleted so get from next place up
                                        oldPosition = i + 4;
                                        item = layout[oldPosition];
                                        if ((item === undefined) && (oldPosition < layoutLength)) {
                                            // Next Item is also deleted so get from next place up
                                            oldPosition = i + 5;
                                            item = layout[oldPosition];
                                            if ((item === undefined) && (oldPosition < layoutLength)) {
                                                // Next Item is also deleted so get from next place up
                                                oldPosition = i + 6;
                                                item = layout[oldPosition];
                                                if ((item === undefined) && (oldPosition < layoutLength)) {
                                                    // Next Item is also deleted so get from next place up
                                                    oldPosition = i + 7;
                                                    item = layout[oldPosition];
                                                    if ((item === undefined) && (oldPosition < layoutLength)) {
                                                        // Next Item is also deleted so get from next place up
                                                        oldPosition = i + 8;
                                                        item = layout[oldPosition];
                                                        if ((item === undefined) && (oldPosition < layoutLength)) {
                                                            pass;
                                                        } else {
                                                            layout[newPosition] = item;
                                                        }
                                                    } else {
                                                        layout[newPosition] = item;
                                                    }
                                                } else {
                                                    layout[newPosition] = item;
                                                }
                                            } else {
                                                layout[newPosition] = item;
                                            }
                                        } else {
                                            layout[newPosition] = item;
                                        }
                                    } else {
                                        layout[newPosition] = item;
                                    }
                                } else {
                                    layout[newPosition] = item;
                                }
                            } else {
                                layout[newPosition] = item;
                            }
                        }
                        // Remove final item from layout (we've already copied it to the previous position)
                        delete layout[i];
                    }
                }

                // Update layoutLength
                layoutLength = Object.keys(layout).length;

                // Update elements on 1st page
                var thisElements = 0,
                    thisElementsText;
                for (position=1; position <= layoutLength; position++) {
                    item = layout[position];
                    if (item.type == 'break') {
                        // Stop iteration
                        break;
                    } else {
                        thisElements++;
                    }
                }
                pageElements[1] = thisElements;
                if (thisElements == 1) {
                    thisElementsText = '1 ELEMENT';
                } else {
                    thisElementsText = thisElements + ' ELEMENTS';
                }
                $('#section-break-0 > span').html('PAGE 1 (' + thisElementsText + ')');
            }

            // Loop through layout to build imageOptions & questionNumbers
            this.updateImageOptions(true);

            // Loop through layout to add items to page
            for (position=1; position <= layoutLength; position++) {
                item = layout[position];
                if (item.type == 'break') {
                    this.addSectionBreak(position, page, true);
                    page++;
                } else if (item.type == 'instructions') {
                    this.addQuestion(position, page, 'instructions', true);
                } else {
                    // Question
                    questionID = item.id;
                    thisQuestion = questions[questionID];
                    this.addQuestion(position, page, typesToText[thisQuestion.type], questionID);
                }
            }
        },

        /**
         * Redraw widget contents
         */
        refresh: function() {
            this._unbindEvents();
            this._deserialize();

            // Add an initial section break
            this.addSectionBreak(0, 0);

            if (!this.options.readOnly) {
                // Add droppable
                this.droppable();
            }

            this.loadSurvey();

            //this._serialize();
            this._bindEvents();
        },

        /**
         * Ajax-update the Question
         */
        saveQuestion: function(type, questionID) {

            if (this.options.readOnly) {
                return;
            }

            var name = $('#name-' + questionID).val();

            if (!name) {
                // name is required to save
                return;
            }

            var ajaxURL = S3.Ap.concat('/dc/question/') + questionID + '/update_json.json',
                mandatory = $('#mandatory-' + questionID).prop('checked'),
                data = {
                    name: name
                },
                l10n = this.data.l10n,
                settings = {},
                thisQuestion = this.data.questions[questionID];

            if (mandatory) {
                settings.requires = {
                    // No parameters needed
                    isNotEmpty: {}
                };
            }

            thisQuestion.name = name;

            if (l10n) {
                var name_l10n = $('#name-l10n-' + questionID).val();
                if (name_l10n) {
                    data.name_l10n = name_l10n;
                    thisQuestion.name_l10n = name_l10n;
                }
            }

            var pipeImage = thisQuestion.settings.pipeImage;
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
                    }
                    if (!($('#max-' + questionID).hasClass('req'))) {
                        max = $('#max-' + questionID).val();
                        if (max) {
                            max = parseInt(max);
                        }
                    }
                    if (min || max) {
                        settings.requires = {
                            isIntInRange: {
                                min: min,
                                max: max
                            }
                        };
                        if (mandatory) {
                            // No parameters needed
                            settings.requires.isNotEmpty = {};
                        }
                    }
                    break;
                case 'multichoice':
                    var options = [];
                    $('.choice-' + questionID).each(function() {
                        options.push($(this).val());
                    });
                    data.options = options;
                    thisQuestion.options = options;
                    if (l10n) {
                        var options_l10n = [];
                        $('.choice-l10n-' + questionID).each(function() {
                            options_l10n.push($(this).val());
                        });
                        data.options_l10n = options_l10n;
                    }
                    if ($('#other-' + questionID).prop('checked')) {
                        settings.other = $('#other-label-' + questionID).val() || 'Other (please specify)';
                        if (l10n) {
                            settings.otherL10n = $('#other-l10n-' + questionID).val();
                        }
                    } else {
                        settings.other = null;
                        if (l10n) {
                            settings.otherL10n = null;
                        }
                    }
                    if ($('#multiple-' + questionID).prop('checked')) {
                        settings.multiple = parseInt($('#multiple-count-' + questionID).html());
                    } else {
                        settings.multiple = 1;
                    }
                    break;
                case 'likert':
                    var options,
                        scale = $('#scale-' + questionID).val();
                    if (scale) {
                        options = likertOptions[scale];
                        settings.scale = parseInt(scale);
                    } else {
                        options = [];
                        settings.scale = null;
                    }
                    data.options = options;
                    thisQuestion.options = options;
                    if (l10n) {
                        var options_l10n = [];
                        $('.choice-l10n-' + questionID).each(function() {
                            options_l10n.push($(this).val());
                        });
                        data.options_l10n = options_l10n;
                    }
                    break;
                case 'heatmap':
                    var options = [],
                        regions = [];
                    $('.choice-' + questionID).each(function() {
                        options.push($(this).val());
                    });
                    // Remove final option as this is the placeholder to add next one
                    options.pop();
                    data.options = options;
                    thisQuestion.options = options;
                    if (l10n) {
                        var options_l10n = [];
                        $('.choice-l10n-' + questionID).each(function() {
                            options_l10n.push($(this).val());
                        });
                        data.options_l10n = options_l10n;
                    }
                    // Regions (GeoJSON)
                    for (var i=0, len=options.length; i < len; i++) {
                        regions.push($('#choice-json-'+ questionID + '-' + i).val());
                    }
                    settings.regions = regions;
                    // numClicks
                    var numClicks = thisQuestion.settings.numClicks;
                    if (numClicks) {
                        settings.numClicks = numClicks;
                    }
                    break;
            }

            data.settings = settings;
            thisQuestion.settings = settings;

            if (type == 'heatmap') {
                // Update ImageOptions (regions may have been added/removed)
                this.updateImageOptions();
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
         * Ajax-update the Template's Layout
         */
        saveLayout: function() {

            if (this.options.readOnly) {
                return;
            }

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

        },

        /**
         * Bind event handlers (after refresh)
         *
         */
        _bindEvents: function() {

            var self = this,
                ns = this.eventNamespace,
                surveyName = $('#survey-name');

            // Foundation Tabs
            $(document).foundation({
                tab: {
                    callback : function (tab) {
                        var tabText = tab.text();
                        if (tabText == 'Display logic') {
                            // Update list of Questions to select from
                            var currentPosition = parseInt(tab.children().first().attr('href').split('-')[1]),
                                logicSelect = $('#logic-select-' + currentPosition),
                                parts = tab.closest('.survey-item').attr('id').split('-'),
                                type = parts[0];
                            if (type == 'instructions') {
                                logicSelect.html(self.logicOptionsHtml(null, currentPosition));
                            } else {
                                var questionID = parts[1];
                                logicSelect.html(self.logicOptionsHtml(questionID, currentPosition));
                            }
                            self.logicSelected(logicSelect, currentPosition);
                        } else if (tabText == 'Translation') {
                            // Copy original language to 'translate-from' div
                            var currentPosition = parseInt(tab.children().first().attr('href').split('-')[1]),
                                parts = tab.closest('.survey-item').attr('id').split('-'),
                                type = parts[0];
                            if (type == 'instructions') {
                                $('#do-l10n-' + currentPosition).prev().html($('#do-' + currentPosition).val());
                                $('#say-l10n-' + currentPosition).prev().html($('#say-' + currentPosition).val());
                            } else {
                                var questionID = parts[1],
                                    thisQuestion = self.data.questions[questionID];
                                $('#name-l10n-from-' + questionID).html($('#name-' + questionID).val());

                                type = typesToText[thisQuestion.type];
                                switch(type) {

                                    case 'text':
                                        // Nothing needed here
                                        break;
                                    case 'number':
                                        // Nothing needed here
                                        break;
                                    case 'multichoice':
                                        // Options
                                        $('.choice-' + questionID).each(function(index) {
                                            $('#choice-from-' + questionID + '-' + index).html($(this).val());
                                        });
                                        // Other option
                                        $('#other-l10n-from-' + questionID).html($('#other-label-' + questionID).val());
                                        break;
                                    case 'likert':
                                        // Nothing needed here
                                        // - if we assume that Scale Options are translated centrally
                                        break;
                                    case 'heatmap':
                                        // Options
                                        $('.choice-' + questionID).each(function(index) {
                                            $('#choice-from-' + questionID + '-' + index).html($(this).val());
                                        });
                                        break;

                                }
                            }
                        }
                    }
                }
            });

            if (!this.options.readOnly) {

                // Edit Survey Name
                surveyName.on('change' + ns, function(/* event */) {
                    var name = surveyName.val(),
                        recordID = surveyName.data('id');
                    self.ajaxMethod({
                        'url': S3.Ap.concat('/dc/target/') + recordID + '/name.json',
                        'type': 'POST',
                        // $.searchS3 defaults to processData: false
                        'data': JSON.stringify({name: name}),
                        'dataType': 'json',
                        'success': function(/* data */) {
                            // Nothing needed here
                        },
                        'error': function(request, status, error) {
                            var msg;
                            if (error == 'UNAUTHORIZED') {
                                msg = i18n.gis_requires_login;
                            } else {
                                msg = request.responseText;
                            }
                            console.log(msg);
                        }
                    });
                });

                // Edit Survey Language
                $('#survey-l10n').on('change' + ns, function(/* event */) {
                    var l10n = $(this).val(),
                        recordID = surveyName.data('id');
                    self.ajaxMethod({
                        'url': S3.Ap.concat('/dc/target/') + recordID + '/l10n.json',
                        'type': 'POST',
                        // $.searchS3 defaults to processData: false
                        'data': JSON.stringify({l10n: l10n}),
                        'dataType': 'json',
                        'success': function(/* data */) {
                            // Update data
                            self.data.l10n = l10n;
                            if (l10n) {
                                // Show Translation Tabs
                                $('li.l10n').removeClass('hide')
                                            .show();
                                // Re-apply events
                                $(document).foundation('tab', 'reflow');
                                // Enable Upload/Download
                                $('div[data-magellan-expedition="fixed"] #upload-translation').prop('disabled', false)
                                                                                              .parent().parent().parent().removeClass('hide').show();
                            } else {
                                // Hide Translation Tabs
                                $('li.l10n').hide();
                                // Disable Upload/Download
                                $('div[data-magellan-expedition="fixed"] #upload-translation').prop('disabled', true)
                                                                                              .parent().parent().parent().hide();
                            }
                        },
                        'error': function(request, status, error) {
                            var msg;
                            if (error == 'UNAUTHORIZED') {
                                msg = i18n.gis_requires_login;
                            } else {
                                msg = request.responseText;
                            }
                            console.log(msg);
                        }
                    });
                });

                // Drag ('n'Drop handled in droppable())
                $('.draggable').draggable({
                    revert: true,
                    revertDuration: 250
                });
            }

            // Translation Upload
            $('#upload-translation').fileupload({
                dataType: 'json',
                maxNumberOfFiles: 1,
                url: S3.Ap.concat('/dc/template/') + self.recordID + '/upload_l10n.json',
                done: function (e, data) {
                    var result = data.result;
                    if (result) {
                        var message = result.message;
                        if (message) {
                            if (result.status == 'failed') {
                                // Note that fileupload() still sees this as a success
                                S3.showAlert(message, 'error');
                            } else {
                                var callback = function() {
                                    // Reload the page (much easier than loading all the affected elements)
                                    /*
                                    window.addEventListener('beforeunload', function(event) {
                                        // Cancel the event as stated by the standard.
                                        event.preventDefault();
                                        // Chrome requires returnValue to be set (although all modern browsers ignore the message)
                                        event.returnValue = message;
                                    });*/
                                    location.reload();
                                }
                                S3.showAlert(message, 'success', callback);

                            }
                        }
                    }
                },
                fail: function (e, data) {
                    var textStatus = data.textStatus,
                        jqXHR = data.jqXHR,
                        httpStatus = jqXHR.status,
                        readyState = jqXHR.readyState,
                        navigateAway = !httpStatus && readyState === 0;

                    if (textStatus == 'abort' || navigateAway) {
                        // Request aborted, or navigating away...don't show nasty messages
                        return;

                    } else if (textStatus == 'timeout') {

                        // Request timeout
                        // @ToDo: retry?

                        // Show final error
                        message = i18n.ajax_wht + ' ' + 1 + ' ' + i18n.ajax_gvn;
                        S3.showAlert(message, 'error');

                    } else if (httpStatus == 500) {
                        // Internal server error
                        S3.showAlert(i18n.ajax_500, 'error');
                    }
                }
            });
            $('#question-bar').on('after-clone.fndtn.magellan', function(/* event */) {
                // Remove file input from clone, otherwise the label 'for' doesn't change the correct onem,which means that the 'change' event never gets fired & hence fileupload fails
                $('div[data-magellan-expedition-clone] #upload-translation').remove();
            });
        },

        /**
         * Unbind events (before refresh)
         */
        _unbindEvents: function() {

            var ns = this.eventNamespace;

            $('#survey-name').unbind(ns);
            $('#survey-l10n').unbind(ns);
            var draggable_el = $('.draggable');
            if (draggable_el.draggable('instance') != undefined) {
                draggable_el.draggable('destroy');
            }

            return true;
        }

    });
});
