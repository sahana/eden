/**
 * Customisations for s3.ui.locationselector.js
 *
 * @copyright 2021 (c) Sahana Software Foundation
 * @license MIT
 */
(function($, undefined) {

    "use strict";

    $.widget('rlp.locationselector', $.s3.locationselector, {

        /**
         * Client-side validation of the widget before main-form submission
         * - checks for required fields
         *
         * @returns {bool} - whether widget input is valid or not
         */
        _validate: function() {

            var fieldname = this.fieldname;

            // Remove previous errors
            this._removeErrors();

            // Do we have a value to submit?
            var selector = '#' + fieldname,
                data = this.data,
                featureRequired = this.options.featureRequired;

            // Check mandatory map feature (wkt or lat/lon)
            if (featureRequired) {
                var valid = false;
                switch (featureRequired) {
                    case 'latlon':
                        valid = data.lat || data.lon;
                        break;
                    case 'wkt':
                        valid = data.wkt;
                        break;
                    default:
                        // Any map feature is valid
                        valid = data.lat || data.lon || data.wkt;
                        break;
                }
                if (!valid) {
                    this._fieldError($(selector + '_map_icon'), i18n.map_feature_required);
                    return false;
                }
            }

            var isVisible = function(field) {
                if (field.hasClass('multiselect')) {
                    return field.next('button.ui-multiselect').is(':visible');
                } else {
                    return field.is(':visible');
                }
            };

            // Check mandatory Lx
            var missingInput = false,
                suffix = ['L5', 'L4', 'L3', 'L2', 'L1', 'L0'],
                s, f;
            for (var i=0; i < 6; i++) {
                var level = suffix[i];
                s = selector + '_' + level;
                f = $(s);
                if (f.length && f.hasClass('required') && isVisible(f) && !data[level]) {
                    this._fieldError(f, i18n.enter_value);
                    missingInput = true;
                    break;
                }
            }

            // Check mandatory text inputs
            ["address", "postcode"].forEach(function(suffix) {
                s = selector + '_' + suffix;
                f = $(s);
                if (f.length && f.hasClass('required') && isVisible(f) && !data[suffix]) {
                    this._fieldError(f, i18n.enter_value);
                    missingInput = true;
                }
            }, this);

            return !missingInput;
        },

        /**
         * Add an error message
         *
         * @param {jQuery} element - the input element
         * @param {string} error - the error message
         */
        _fieldError: function(element, error) {

            element.addClass('invalidinput')
                   .after('<div class="error" style="display: block;">' + error + '</div>');

            $('.invalidinput').get(0).scrollIntoView();
        },

        /**
         * Remove error messages
         *
         * @param {jQuery} element - the input field (removes all error messages
         *                           in the widget if no field specified)
         */
        _removeErrors: function(element) {

            if (!element) {
                var selector = '#' + this.fieldname;
                element = selector + '_L0,' +
                          selector + '_L1,' +
                          selector + '_L2,' +
                          selector + '_L3,' +
                          selector + '_L4,' +
                          selector + '_L5,' +
                          selector + '_address,' +
                          selector + '_postcode,' +
                          selector + '_map_icon';
            }
            $(element).removeClass('invalidinput').siblings('.error').remove();
        }
    });
})(jQuery);
