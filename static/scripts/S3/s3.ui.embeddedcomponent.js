/**
 * jQuery UI EmbeddedComponent Widget (used by S3EmbeddedComponentWidget)
 *
 * @copyright 2015-2021 (c) Sahana Software Foundation
 * @license MIT
 */
(function($, undefined) {

    "use strict";
    var embeddedComponentID = 0;

    /**
     * Embedded Component Widget
     */
    $.widget('s3.embeddedComponent', {

        /**
         * Default options
         *
         * @prop {string} ajaxURL - the URL to retrieve the component data from
         * @prop {string} fieldname - the name of the real input field in the outer form
         * @prop {string} component - the tablename of the component
         * @prop {number} recordID - the currently selected record ID
         * @prop {boolean} autocomplete - whether or not the widget is using
         *                                an autocomplete-selector
         * @prop {script} postprocess - script to execute after selection/deselection
         */
        options: {

            ajaxURL: null,
            fieldname: null,
            component: null,
            recordID: null,
            autocomplete: false
        },

        /**
         * Create the widget
         */
        _create: function() {

            this.id = embeddedComponentID;
            embeddedComponentID += 1;

            // Namespace for events
            this.eventNamespace = '.embeddedComponent';
            this.eventNamespaceID = this.eventNamespace + this.id;
        },

        /**
         * Update the widget options
         */
        _init: function() {

            var fieldname = this.options.fieldname;

            // Element references
            this.input = $(this.element);
            this.fieldname = fieldname;
            this.selectBtn = $('#' + fieldname + '-select');
            this.editBtn = $('#' + fieldname + '-edit');
            this.clearBtn = $('#' + fieldname + '-clear');
            this.loadThrobber = this.selectBtn.siblings('.throbber');
            this.selectRow = $('#' + fieldname + '-select-row');
            this.dummyInput = $('#dummy_' + fieldname);
            this.autocompleteRow = $('#' + fieldname + '-autocomplete-row');
            this.autocompleteLabel = $('#' + fieldname + '-autocomplete-label');

            this.refresh();
        },

        /**
         * Remove generated elements & reset other changes
         */
        _destroy: function() {

            $.Widget.prototype.destroy.call(this);
        },

        /**
         * Redraw contents
         */
        refresh: function() {

            this._unbindEvents();

            this.dummyInput.hide();

            var recordID = this.options.recordID;
            if (recordID != 'None') {
                this.input.val(recordID);
                this.select(recordID);
            }
            if (this.input.val() > 0) {
                this.clearBtn.removeClass('hide').show();
                this.editBtn.removeClass('hide').show();
                this._disableEmbedded();
            }
            this._bindEvents();
        },

        /**
         * Select a record from the registry
         *
         * @param {number} componentID - the record ID (optional, defaults to real input)
         */
        select: function(componentID) {

            if (typeof componentID == 'undefined') {
                componentID = this.input.val();
            } else {
                this.input.val(componentID);
            }

            this.selectBtn.hide();
            this.clearBtn.hide();
            this.loadThrobber.removeClass('hide').show();

            this._clear();

            var componentName = this.options.component,
                url = this.options.ajaxURL + componentID + '.s3json?show_ids=true',
                self = this;

            $.getJSONS3(url, function (data) {

                try {
                    var record = data['$_' + componentName][0];

                    self._disableEmbedded();
                    self.input.val(record['@id']);

                    var re = new RegExp("^[\$|\@].*"),
                        fk = new RegExp("^[\$]k_.*");

                    var field, fieldID;

                    for (field in record) {

                        if (field.match(re)) {
                            if (field.match(fk)) {
                                fieldID = '#' + componentName + "_" + field.slice(3);
                            } else {
                                continue;
                            }
                        } else {
                            fieldID = '#' + componentName + "_" + field;
                        }

                        try {
                            var value = record[field];
                            if (value.hasOwnProperty('@id')) {
                                $(fieldID).val(eval(value['@id']));
                            } else
                            if (value.hasOwnProperty('@value')) {
                                var val;
                                try {
                                    val = JSON.parse(value['@value']);
                                }
                                catch(e) {
                                    val = value['@value'];
                                }
                                $(fieldID).val(val);
                            }
                            else {
                                $(fieldID).val(value);
                            }
                        }
                        catch(e) {
                            // skip
                        }
                    }
                }
                catch(e) {
                    self.input.val('');
                }
                self.loadThrobber.hide();
                self.selectBtn.removeClass('hide').show();
                self.editBtn.removeClass('hide').show();
                self.clearBtn.removeClass('hide').show();

                var postprocess = self.options.postprocess;
                if (postprocess) {
                    eval(postprocess);
                }
            });
            self.autocompleteRow.hide();
            self.selectRow.removeClass('hide').show();
        },

        /**
         * Remove previously selected values
         */
        _clear: function() {

            var input = $(this.input);
            var form = input.closest('form');

            form.find('.embedded-' + this.fieldname).each(function() {
                $(this).find('input, select, textarea').prop('disabled', false)
                                                       .val('');
            });
            input.val('');
            this.clearBtn.hide();
            this.editBtn.hide();

            var postprocess = this.options.postprocess;
            if (postprocess) {
                eval(postprocess);
            }
        },

        /**
         * Enable the embedded fields, hide the Edit-button
         */
        _edit: function() {

            this._enableEmbedded();
            this.editBtn.hide();
        },

        /**
         * Enable the embedded fields
         */
        _enableEmbedded: function() {

            var form = $(this.element).closest('form');

            form.find('.embedded-' + this.fieldname).each(function() {
                $(this).find('input, select, textarea').prop('disabled', false);
            });
        },

        /**
         * Disable the embedded fields
         */
        _disableEmbedded: function() {

            var form = $(this.element).closest('form');

            form.find('.embedded-' + this.fieldname).each(function() {
                $(this).find('input, select, textarea').prop('disabled', true);
            });
        },

        /**
         * Tasks before form submission
         */
        _onFormSubmission: function() {

            S3ClearNavigateAwayConfirm();
            this._enableEmbedded();
        },

        /**
         * Bind event handlers (after refresh)
         */
        _bindEvents: function() {

            var self = this,
                ns = this.eventNamespace;

            this.input.closest('form').bind('submit' + this.eventNamespaceID, function () {
                self._onFormSubmission();
                return true;
            });

            this.selectBtn.bind('click' + ns, function() {
                // Activate search
                self.selectRow.hide();
                self.autocompleteRow.removeClass('hide').show();
                self.autocompleteLabel.removeClass('hide').show();
                self.dummyInput.removeClass('hide').show().focus();
            });

            this.editBtn.bind('click' + ns, function() {
                self._edit();
            });

            this.clearBtn.bind('click' + ns, function() {
                self._clear();
            });

            this.dummyInput.bind('focusout' + ns, function() {
                // Reset form when clicking outside of dummy input
                var componentID = self.input.val();
                $(this).hide();
                self.autocompleteLabel.hide();
                self.selectRow.removeClass('hide').show();
                if (self.input.val() > 0) {
                    self.clearBtn.removeClass('hide').show();
                }
            });

            if (!this.options.autocomplete) {
                this.dummyInput.bind('change' + ns, function() {
                    var value = $(this).val();
                    if (value) {
                        self.input.val(value).change();
                    }
                })
            }

            this.input.bind('change' + ns, function() {
                var value = $(this).val();
                if (value) {
                    self.select(value);
                }
            });

            return true;
        },

        /**
         * Unbind events (before refresh)
         */
        _unbindEvents: function() {

            var ns = this.eventNamespace;

            this.input.closest('form').unbind(this.eventNamespaceID);

            this.selectBtn.unbind(ns);
            this.editBtn.unbind(ns);
            this.clearBtn.unbind(ns);

            this.dummyInput.unbind(ns);

            return true;
        }
    });
})(jQuery);

// END ========================================================================
