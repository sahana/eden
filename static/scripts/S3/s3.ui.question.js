/*
 * Client-side JS for S3QuestionEditorWidget
 */
(function($, undefined) {
    "use strict";
    var addQuestionID = 0;

    $.widget('s3.addQuestion', {

        options: {

        },

        /**
         * Create the widget
         */
        _create: function() {

            this.id = addQuestionID;
            addQuestionID += 1;
            this.eventNamespace = '.addQuestion';

        },

        /**
         * Initialize the widget
         */
        _init: function() {

            var fieldname = $(this.element).attr('id');

            if (!fieldname) {
                fieldname = 'addQuestion-widget-' + this.id;
            }
            this.fieldname = fieldname;
            this.data = null;

            var selector = '#' + fieldname;

            this.inputFields = $(selector + '_represent, ' +
                                 selector + '_multiple, ' +
                                 selector + '_description, ' +
                                 selector + '_reference, ' +
                                 selector + '_min, ' +
                                 selector + '_max, ' +
                                 selector + '_defaultanswer, ' +
                                 selector + '_filter, ' +
                                 selector + '_location, ' +
                                 selector + '_is_required, ' +
                                 selector + '_type, ' +
                                 selector + '_options');

            this.refresh();

        },

        /**
          * Remove generated elements & reset other changes
          */
        _destroy: function() {
            $.Widget.prototype.destroy.call(this);
        },

        /**
         * Redraw widget contents
         */
        refresh: function() {
            this._unbindEvents();

            this._deserialize();
            this._handleForm();
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
         * Hide the fields provided as a list
         */
        hideFields: function(fields) {

            var selector = '#' + this.fieldname + '_';

            $.each(fields, function(index, field) {
                $(selector + field + '__row').hide();
            });
        },
        /**
         * Manipulate the form based on the type selected
         */
        _handleForm: function() {
            var selector = '#' + this.fieldname,
                type = this.data.type;

            $(selector + '_represent__row, ' +
              selector + '_multiple__row, ' +
              selector + '_reference__row, ' +
              selector + '_min__row, ' +
              selector + '_max__row, ' +
              selector + '_filter__row, ' +
              selector + '_location__row, ' +
              selector + '_options__row').show();

            switch(type) {

                case 'string':
                case 'text':
                    this.hideFields(['max', 'min', 'filter', 'reference', 'represent', 'location', 'options', 'multiple']);
                    break;

                case 'integer':
                case 'float':
                    this.hideFields(['filter', 'reference', 'represent', 'location', 'options', 'multiple']);
                    break;

                case 'date':
                case 'time':
                case 'datetime':
                    this.hideFields(['filter', 'reference', 'location', 'options', 'multiple']);
                    break;

                case 'object':
                    this.hideFields(['max', 'min', 'filter', 'reference', 'represent', 'location']);
                    break;

                case 'reference':
                    this.hideFields(['max', 'min', 'filter', 'represent', 'location', 'options', 'multiple']);
                    break;

                case 'location':
                    this.hideFields(['max', 'min', 'filter', 'reference', 'represent', 'options', 'multiple']);
                    break;

                default:
                    break;
            }

        },

        /**
         * Bind event handlers (after refresh)
         */
        _bindEvents: function() {

            var self = this,
                ns = this.eventNamespace;

            // Bind change event for all the input fields
            var selector = '#' + this.fieldname;

            this.inputFields.on('change' + ns, function() {
                self._collectData(this);
                if (this.id.slice(-4) === 'type') {
                    self._handleForm();
                }
            });

            // Trigger the change event for Type field
            var form = $(selector).closest('form');
            $(form).on('submit', function() {
                $(selector + '_type').trigger('change' + ns);
            });

        },

        /**
         * Unbind events (before refresh)
         */
        _unbindEvents: function() {

            var ns = this.eventNamespace,
                el = $(this.element);

            this.inputFields.off(ns);
            el.off(ns);

            return true;
        }

    });
})(jQuery);
