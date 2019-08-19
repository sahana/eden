/*
 * Survey Editor Widget
 */
import { Map, View, Draw, GeoJSON, getCenter, ImageLayer, Projection, Static, VectorLayer, VectorSource } from './ol5.min.js';

(function(factory) {
    'use strict';
    // Use window. for Browser globals (not AMD or Node):
    factory(window.jQuery, window.loadImage, Map, View, Draw, GeoJSON, getCenter, ImageLayer, Projection, Static, VectorLayer, VectorSource);
})(function($, loadImage, Map, View, Draw, GeoJSON, getCenter, ImageLayer, Projection, Static, VectorLayer, VectorSource) {
    'use strict';
    var surveyID = 0,
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
            '6': ['Very happy', 'Happy', 'Neutral', 'Sad', 'Very sad'],
            '7': ['Happy', 'Neutral', 'Sad']
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
                        settings: {},
                        options: []
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
                translationHidden = '',
                translationTab,
                trash;

            if (!l10n) {
                translationHidden = ' hide';
            }
            var translationTitle = '<li class="tab-title l10n' + translationHidden + '"><a href="#translation-' + position + '">Translation</a></li>';

            if (type == 'instructions') {
                idHtml = 'instruction-' + position;
                dataHtml = '';
                formElements = '#instruction-' + position + ' input, #instruction-' + position + ' select';
                trash = '#instruction-' + position + ' .ucce-delete';
            } else {
                idHtml = 'question-' + questionID;
                dataHtml = ' data-number="' + questionNumber + '"';
                formElements = '#question-' + questionID + ' input, #question-' + questionID + ' select';
                trash = '#question-' + questionID + ' .ucce-delete';
                var checked = '';
                thisQuestion = this.data.questions[questionID];
                if (load) {
                    if (thisQuestion.mandatory) {
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

            question = '<div class="thumbnail dl-item" id="' + idHtml + '" data-page="' + page + '"' + dataHtml + '>' + 
                       '<div class="card-header"><ul class="tabs fleft" data-tab><li class="tab-title active"><a href="#edit-' + position + '">Edit</a></li><li class="tab-title"><a href="#logic-' + position + '">Display logic</a></li> ' + translationTitle + '</ul>' +
                       '<div class="edit-bar fright"><a><i class="ucce ucce-duplicate"> </i></a><a><i class="ucce ucce-delete"> </i></a><i class="ucce ucce-up"> </i><i class="ucce ucce-down"> </i></div>' + 
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
                        var thisLayout = this.data.layout[position];
                        doText = thisLayout.do.text;
                        sayText = thisLayout.say.text;
                        if (l10n && thisLayout.do.l10n) {
                            doTextL10n = thisLayout.do.l10n[l10n];
                            sayTextL10n = thisLayout.say.l10n[l10n];
                        }
                    }
                    editTab = '<div class="media content active" id="edit-' + position + '">' +
                               '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><h2 class="fleft">Data collector instructions</h2></div></div>' +
                               '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><label>What instructor should do</label><input id="do-' + position + '" type="text" size=100 placeholder="Type what instructor should do" value="' + doText + '"><label>What instructor should say</label><input id="say-' + position + '" type="text" size=100 placeholder="Type what instructor should say" value="' + sayText + '"></div></div>' +
                              '</div>';
                    translationTab = '<div class="media content" id="translation-' + position + '">' +
                                      '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><h2 class="fleft">Data collector instructions</h2></div></div>' +
                                      '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><label>What instructor should do</label><div class="translate-from"></div><input id="do-l10n-' + position + '" type="text" size=100 placeholder="Type translation..." value="' + doTextL10n + '"><label>What instructor should say</label><div class="translate-from"></div><input id="say-l10n-' + position + '" type="text" size=100 placeholder="Type translation..." value="' + sayTextL10n + '"></div></div>' + 
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
                        var settings = thisQuestion.settings || {},
                            requires = settings.requires || {},
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
                    newChoice = '<div id="choice-row-' + questionID + '-0" class="row"><div class="columns medium-1"></div><div class="columns medium-11"><input class="choice-' + questionID + '" type="text" placeholder="Enter an answer choice"><i class="ucce ucce-minus"> </i><i class="ucce ucce-plus"> </i></div></div>';
                    // @ToDo: Grey the multiple -+ options if they cannot do anything
                    var name = '',
                        nameL10n = '',
                        choices = newChoice,
                        choicesL10n = '',
                        other = '',
                        otherDisabled = ' disabled',
                        otherLabel = '',
                        otherL10n = '',
                        multiple = 1,
                        multiChecked = '';
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
                        }
                        var settings = thisQuestion.settings,
                            otherL10n = '',
                            otherL10nHide = ' hide';
                        otherLabel = settings.other || '';
                        if (otherLabel) {
                            other = ' checked';
                            otherDisabled = '';
                            otherL10n = settings.otherL10n || '';
                            otherL10nHide = '';
                        }
                        choiceL10nRow = '<div id="other-l10n-row-' + questionID + '" class="row' + otherL10nHide + '">' +
                                         '<div class="columns medium-1"></div>' +
                                         '<div class="columns medium-11">' +
                                          '<div class="row">' +
                                           '<div class="columns medium-6"><div id="other-l10n-from-' + questionID + '" class="translate-from">' + otherLabel + '</div></div>' +
                                           '<div class="columns medium-6"><input id="other-l10n-' + questionID + '" type="text" placeholder="Type translation..." value="' + otherL10n + '"></div>' +
                                        '</div></div></div>';
                        choicesL10n += choiceL10nRow;
                        multiple = settings.multiple || 1;
                        if (multiple > 1) {
                            multiChecked = ' checked';
                        }
                    }
                    editTab = '<div class="media content active" id="edit-' + position + '">' +
                               '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><h2 class="left">Multiple choice question</h2></div></div>' +
                               '<div class="row"><div class="columns medium-1"><label id="qlabel-' + questionID + '" class="fright">Q' + questionNumber + '</label></div><div class="columns medium-11"><input id="name-' + questionID + '"type="text" size=100 placeholder="type question" value="' + name + '"></div></div>' +
                               mandatory + imageHtml +
                               '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><h2 class="fleft">Answer</h2></div></div>' +
                               '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><label>Choices</label></div></div>' +
                               choices +
                               '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><input id="other-' + questionID + '" type="checkbox"' + other + '><label>Add \'other field\'</label></div></div>' + 
                               '<div class="row"><div class="columns medium-1"></div><div class="columns medium-11"><label class="fleft">Field label</label><input id="other-label-' + questionID + '" type="text" placeholder="Other (please specify)" value="' + otherLabel + '"' + otherDisabled + '></div></div>' + 
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
                                     '</div>';
                    break;

                case 'heatmap':
                    newChoice = '<div id="choice-row-' + questionID + '-0" class="row"><a class="button tiny secondary choice-define-' + questionID + '">Add region 1</a><input class="choice-' + questionID + '" type="text" placeholder="enter label" disabled><i class="ucce ucce-minus"> </i></div>';
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
                            var thisOptionL10n;
                            for (var i=0; i < lenOptions; i++) {
                                choices += '<div id="choice-row-' + questionID + '-' + i + '" class="row"><a class="button tiny">Add region ' + (i + 1) + '</a><input class="choice-' + questionID + '" type="text" placeholder="enter label" value="' + options[i] + '"><i class="ucce ucce-minus"> </i></div>';
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
                                '<div class="columns medium-1"></div>' + 
                                '<div class="columns medium-11">' +
                                 '<div class="row">' + 
                                  '<div class="columns medium-6 heatmap" id="map-' + questionID + '"><span id="preview-' + questionID + '" class="preview-empty fleft"></span></div>' +
                                  '<div class="columns medium-6">' + 
                                   '<div class="row"><h3>Number of clicks allowed:</h3></div>' +
                                   '<div class="row" id="clicks-row-' + questionID + '"><i class="ucce ucce-minus"> </i><span> ' + numClicks + ' </span><i class="ucce ucce-plus"> </i></div>' +
                                   '<div class="row"><h3>Tap/click regions:</h3></div>' +
                                   choices +
                              '</div></div></div></div></div>';
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
                                thisLayout = self.data.layout[currentPosition];
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
                            // @ToDo: Show Preview of selected Image
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
                        if (type == 'heatmap') {
                            self.heatMap(questionID, file);
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

                                if (type != 'heatmap') {
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
                                            var label = 'Q' + questionNumber + ' ' + type;
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

                                        return img;

                                    }, {}); // Empty Options
                                }
                                
                            });
                        }
                    },
                    done: function (e, data) {
                        if (type == 'heatmap') {
                            self.heatMap(questionID, data.result.file);
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
                        var deleteOption = $('.choice-' + questionID).next();
                        deleteOption.off('click' + ns)
                                    .on('click' + ns, function() {
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
                                $(this).prev().val('');
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
                            var choiceL10nRow = '<div id="choice-l10n-row-' + questionID + '-' + newIndex + '" class="row">' +
                                                 '<div class="columns medium-1"></div>' +
                                                 '<div class="columns medium-11">' + 
                                                  '<div class="row">' + 
                                                   '<div class="columns medium-6"><div id="choice-from-' + questionID + '-' + newIndex + '" class="translate-from"></div></div>' +
                                                   '<div class="columns medium-6"><input class="choice-l10n-' + questionID + '" type="text" placeholder="Type translation..."></div>' +
                                                 '</div></div></div>';
                            $('#choice-l10n-row-' + questionID + '-' + index).after(choiceL10nRow);
                            // Add Events
                            inputEvents();
                            multichoiceEvents();
                        });
                        // Other field
                        $('#other-' + questionID).on('change' + ns, function(){
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
                        var scale = $(this).val();
                        if (scale) {
                            var options = likertOptions[scale],
                                scaleOptions = '';
                            for (var i=0, len = options.length; i < len; i++) {
                                scaleOptions += '<li>' + options[i] + '</li>';
                            }
                            var scaleDisplay = '<ul>' + scaleOptions + '</ul>';
                            $('#display-' + questionID).empty()
                                                       .append(scaleDisplay);
                        } else {
                            // Remove old display
                            $('#display-' + questionID).empty();
                        }
                    });
                    break;

                case 'heatmap':
                    var multichoiceEvents = function() {
                        // Options
                        var deleteOption = $('.choice-' + questionID).next();
                        deleteOption.off('click' + ns)
                                    .on('click' + ns, function() {
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
                                    $('#choice-row-' + questionID + '-' + newIndex + ' > .button').html('Add region ' + (newIndex + 1));
                                    $('#choice-l10n-row-' + questionID + '-' + i).attr('id', 'choice-l10n-row-' + questionID + '-' + newIndex);
                                    $('#choice-from-' + questionID + '-' + i).attr('id', 'choice-from-' + questionID + '-' + newIndex);
                                }
                                self.saveQuestion(type, questionID);
                            } else {
                                // Just remove value - since we always need at least 1 option available
                                var input = $(this).prev();
                                input.val('')
                                     .prop('disabled', true);
                                input.prev().addClass('secondary');
                            }
                        });
                        $('.choice-define-' + questionID).off('click' + ns)
                                                         .on('click' + ns, function() {
                            var $this = $(this),
                                currentRow = $this.closest('.row'),
                                index = parseInt(currentRow.attr('id').split('-')[3]),
                                regions = self.data.questions[questionID].settings.regions;

                            if ($this.hasClass('secondary')) {
                                // Add new Option after current row
                                var newIndex = index + 1;
                                currentRow.after(newChoice.replace('-0', '-' + newIndex));
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
                            }
                            $this.removeClass('secondary');
                            $this.next().prop('disabled', false);
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
                            self.data.questions[questionID].settings.numClicks = value;
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
                        self.data.questions[questionID].settings.numClicks = value;
                        // Save Question
                        self.saveQuestion(type, questionID);
                        // Update visual element
                        $prev.html(' ' + value + ' ');
                    });
                break;
            }

            // Run Foundation JS on new Item
            //- needed for Tabs to work at all & allows us to add callback
            if (type == 'instructions') {
                $('#instruction-' + position).foundation('tab', 'reflow');
            } else {
                $('#question-' + questionID).foundation('tab', 'reflow');
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
                oldQuestionNumber = questionNumber,
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
          * Turn an Image into a (Heat)Map
          */
        heatMap: function(questionID, file) {

            var url = S3.Ap.concat('/default/download/' + file);

            // Add image to DOM to get the height/width
            $('<img>').attr('src', url).load(function() {
                var width = this.width,
                    height = this.height;

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
                var draw = new Draw({
                    source: source,
                    type: 'Polygon'
                });
                map.addInteraction(draw);
                
            });
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
          * Produce the Options HTML for the Logic Questions dropdown
          */
        logicOptionsHtml: function(questionID, currentPosition) {

            var optionsHtml = '<option value="">select question</option>';

            // Loop through Questions: Build list of all which are multichoice, likert, heatmap or number
            var questions = this.data.questions,
                layout = this.data.layout,
                label,
                position,
                qtype,
                displayLogic = layout[currentPosition].displayLogic,
                displayLogicID,
                selected,
                thisQuestion,
                thisQuestionID;

            if (displayLogic) {
                displayLogicID = displayLogic.id;
            }

            for (var i=1, len=Object.keys(questionNumbers).length; i <= len; i++) {
                position = questionNumbers[i];
                thisQuestionID = layout[position].id;
                if (thisQuestionID == questionID) {
                    // Don't include this Question
                } else {
                    thisQuestion = questions[thisQuestionID];
                    qtype = typesToText[thisQuestion.type];
                    if ((qtype == 'number') || (qtype == 'multichoice') || (qtype == 'likert') || (qtype == 'heatmap')) {
                        label = 'Q' + i + ': ' + truncate(thisQuestion.name || '');
                        if (thisQuestionID == displayLogicID) {
                            selected = ' selected';
                        } else {
                            selected = '';
                        }
                        optionsHtml += '<option value="' + thisQuestionID + '"' + selected + '>' + label + '</option>';
                    }
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
                label,
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
                    value = logicTerm1.val();
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
                        value = logicTerm2.val();
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
                        value = logicTerm2.val();
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
                            displayLogic.gt = value;
                        }
                        value = logicTerm1.val();
                        if (value) {
                            displayLogic.lt = value;
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
                            displayLogic.gt = value;
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
                            displayLogic.eq = value;
                        } else {
                            if (operator == 'gt') {
                                displayLogic.gt = value;
                            } else {
                                displayLogic.lt = value;
                            }
                            value = logicTerm2.val();
                            if (value) {
                                operator = logicOperator2.val();
                                if (operator == 'gt') {
                                    displayLogic.gt = value;
                                } else {
                                    displayLogic.lt = value;
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
                                displayLogic.gt = value;
                            } else {
                                displayLogic.lt = value;
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
                            displayLogic.gt = value;
                        } else {
                            displayLogic.lt = value;
                        }
                        value = logicTerm1.val();
                        if (value) {
                            operator = logicOperator1.val();
                            if (operator == 'gt') {
                                displayLogic.gt = value;
                            } else {
                                displayLogic.lt = value;
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
                                displayLogic.eq = value;
                            } else if (operator == 'gt') {
                                displayLogic.gt = value;
                            } else {
                                displayLogic.lt = value;
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

            } else if (type == 'heatmap') {
                label = 'region';
            } else {
                // Multichoice or Likert
                label = 'option';
            }

            // Display a dropdown of Options for the selected Question

            var displayLogicOption,
                opt,
                options = logicQuestion.options,
                selected,
                subOptionSelect = '<select id="sub-logic-select-' + currentPosition + '"><option value="">select ' + label + '</option>';

            if (displayLogic) {
                displayLogicOption = displayLogic.eq;
            }

            for (var i=0, len=options.length; i < len; i++) {
                opt = options[i];
                if (opt == displayLogicOption) {
                    selected = ' selected';
                } else {
                    selected = '';
                }
                subOptionSelect += '<option value="' + opt + '"' + selected + '>' + opt + '</option>';
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
                self.data.layout[currentPosition].displayLogic = {
                    id: logicQuestionID,
                    eq: $(this).val()
                };
                // Save Layout
                self.saveLayout();
            });
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
                this.logicSubOptions(currentPosition, value);
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
                thisRegions,
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
                            var regions = thisQuestion.settings.regions;
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
            this._unbindEvents();
            this._deserialize();

            // Add an initial section break
            this.addSectionBreak(0, 0);

            // Add droppable
            this.droppable(1, 1);

            this.loadSurvey();

            //this._serialize();
            this._bindEvents();
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
                mandatory = $('#mandatory-' + questionID).prop('checked'),
                data = {
                    name: name,
                    mandatory: mandatory
                },
                l10n = this.data.l10n,
                settings = {},
                thisQuestion = this.data.questions[questionID];

            thisQuestion.name = name;
            thisQuestion.mandatory = mandatory;

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
                    thisQuestion.options = options;
                    if (l10n) {
                        var options_l10n = [];
                        $('.choice-l10n-' + questionID).each(function() {
                            options_l10n.push($(this).val());
                        });
                        data.options_l10n = options_l10n;
                    }
                    if ($('#other-' + questionID).prop('checked')) {
                        settings.other = $('#other-label-' + questionID).val();
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
                        settings.scale = scale;
                    } else {
                        options = [];
                        settings.scale = null;
                    }
                    data.options = options;
                    thisQuestion.options = options;
                    break;
                case 'heatmap':
                    var options = [];
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
                    // numClicks
                    var numClicks = thisQuestion.settings.numClicks;
                    if (numClicks) {
                        settings.numClicks = numClicks;
                    }
                    break;
            }

            data.settings = settings;
            thisQuestion.settings = settings;

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
                            var currentPosition = tab.children().first().attr('href').split('-')[1],
                                logicSelect = $('#logic-select-' + currentPosition),
                                parts = tab.closest('.dl-item').attr('id').split('-'),
                                type = parts[0];
                            if (type == 'instruction') {
                                logicSelect.html(self.logicOptionsHtml(null, currentPosition));
                            } else {
                                var questionID = parts[1];
                                logicSelect.html(self.logicOptionsHtml(questionID, currentPosition));
                            }
                            self.logicSelected(logicSelect, currentPosition);
                        } else if (tabText == 'Translation') {
                            // Copy original language to 'translate-from' div
                            var currentPosition = tab.children().first().attr('href').split('-')[1],
                                parts = tab.closest('.dl-item').attr('id').split('-'),
                                type = parts[0];
                            if (type == 'instruction') {
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
                        } else{
                            // Hide Translation Tabs
                            $('li.l10n').hide();
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
