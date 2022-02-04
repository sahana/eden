/**
 * jQuery UI PersonContacts Widget
 *
 * @copyright 2015-2021 (c) Sahana Software Foundation
 * @license MIT
 */
(function($, undefined) {

    "use strict";
    var personcontactsID = 0;

    /**
     * Person Contacts Widget
     */
    $.widget('s3.personcontacts', {

        /**
         * Default options
         *
         * @prop {number} access - the default access level for contacts,
         *                         1 = private, 2 = public
         * @prop {string} controller - the controller prefix
         * @prop {number} personID - the person record ID
         * @prop {string} cancelButtonText - the text for the cancel button
         */
        options: {

            access: 1,
            controller: 'pr',
            personID: null,
            cancelButtonText: 'Cancel',
            placeholderText: 'Click to edit',
        },

        /**
         * Create the widget
         */
        _create: function() {

            this.id = personcontactsID;
            personcontactsID += 1;

            // Namespace for events
            this.eventNamespace = '.personcontacts';
        },

        /**
         * Update the widget options
         */
        _init: function() {

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

            this._bindEvents();
        },

        /**
         * Add a contact
         *
         * @param {jQuery} button - the add-button
         */
        _addContact: function(button) {

            var $button = $(button);

            // Remove any previous popup
            $('.iframe-container').remove();
            this._showAll();

            // Hide add-button and show throbber
            $button.hide().siblings('.throbber').removeClass('hide').show();

            var opts = this.options;
            var access = opts.access,
                personID = opts.personID,
                controller = opts.controller;
            var url = S3.Ap.concat('/pr/contact/create.iframe?person=' + personID);
            if (access) {
                url += '&access=' + access;
            }
            $.get(url, function(data) {
                var frame = $('<div class="iframe-container">').hide().html(data);
                // Modify form action
                var url2 = S3.Ap.concat('/pr/contact/create?person=' + personID + '&controller=' + controller);
                if (access) {
                    url2 += '&access=' + access;
                }
                var form = frame.find('form').attr('action', url2);
                // Add a cancel button
                var cancelButton = $('<a class="cancel action-lnk">' + opts.cancelButtonText + '</a>').on('click', function() {
                        form.slideUp('mediun', function() { frame.remove(); });
                        $(button).show();
                    });
                form.find('input[type="submit"]').after(cancelButton);
                // Show the form
                frame.find('#popup').show();
                form.show();
                frame.insertAfter(button).slideDown('medium', function() {
                    $(button).siblings('.throbber').hide();
                });
            });
        },

        /**
         * Add an emergency contact
         *
         * @param {jQuery} button - the add-button
         */
        _addEmergencyContact: function(button) {

            var $button = $(button);

            // Remove any previous popup
            $('.iframe-container').remove();
            this._showAll();

            // Hide add-button and show throbber
            $button.hide().siblings('.throbber').removeClass('hide').show();

            var opts = this.options;
            var access = opts.access,
                personID = opts.personID,
                controller = opts.controller;
            var url = S3.Ap.concat('/pr/contact_emergency/create.iframe?person_id=' + personID);
            if (access) {
                url += '&access=' + access;
            }
            $.get(url, function(data) {
                var frame = $('<div class="iframe-container">').hide().html(data);
                // Modify form action
                var url2 = S3.Ap.concat('/pr/contact_emergency/create?person=' + personID + '&controller=' + controller);
                if (access) {
                    url2 += '&access=' + access;
                }
                var form = frame.find('form').attr('action', url2);
                // Add a cancel button
                var cancelButton = $('<a class="cancel action-lnk">' + opts.cancelButtonText + '</a>').on('click', function() {
                        form.slideUp('mediun', function() { frame.remove(); });
                        $(button).show();
                    });
                form.find('input[type="submit"]').after(cancelButton);
                // Show the form
                frame.find('#popup').show();
                form.show();
                frame.insertAfter(button).slideDown('medium', function() {
                    $(button).siblings('.throbber').hide();
                });
            });
        },

        /**
         * Edit a contact
         *
         * @param {jQuery} element - the contact container (.pr-contact)
         */
        _editContact: function(element) {

            var contact = $(element),
                opts = this.options,
                self = this;

            // Remove any existing form
            $('.iframe-container').remove();
            this._showAll();

            // Hide actions, show throbber
            contact.find('.pr-contact-actions').children().toggle();

            var personID = opts.personID,
                controller = opts.controller,
                recordID = contact.data('id'),
                access = opts.access;

            var url = S3.Ap.concat('/pr/contact/' + recordID + '.iframe/update?person=' + personID);

            // Load the edit form
            $.get(url, function(data) {
                // Create a form container
                var frame = $('<div class="iframe-container">').hide().html(data);
                // Modify the submission URL, Display form
                var url2 = S3.Ap.concat('/pr/contact/' + recordID + '/update?person=' + personID + '&controller=' + controller);
                if (access) {
                    url2 += '&access=' + access;
                }
                var form = frame.find('form').attr('action', url2);
                // Add a cancel button
                var cancelButton = $('<a class="cancel action-lnk">' + opts.cancelButtonText + '</a>').on('click', function() {
                        form.slideUp('mediun', function() { frame.remove(); });
                        self._showAll();
                    });
                form.find('input[type="submit"]').after(cancelButton);
                // Show the form
                contact.after(frame).hide();
                frame.find('#popup').show();
                form.show();
                frame.slideDown('medium');
            });
        },

        /**
         * Edit an emergency contact
         *
         * @param {jQuery} element - the contact container (.pr-emergency-contact)
         */
        _editEmergencyContact: function(element) {

            var contact = $(element),
                opts = this.options,
                self = this;

            // Remove any existing form
            $('.iframe-container').remove();
            this._showAll();

            // Hide actions, show throbber
            contact.find('.pr-contact-actions').children().toggle();

            var personID = opts.personID,
                controller = opts.controller,
                recordID = contact.data('id'),
                access = opts.access;

            var url = S3.Ap.concat('/pr/contact_emergency/' + recordID + '.iframe/update?person=' + personID);

            // Load the edit form
            $.get(url, function(data) {
                // Create a form container
                var frame = $('<div class="iframe-container">').hide().html(data);
                // Modify the submission URL, Display form
                var url2 = S3.Ap.concat('/pr/contact_emergency/' + recordID + '/update?person=' + personID + '&controller=' + controller);
                if (access) {
                    url2 += '&access=' + access;
                }
                var form = frame.find('form').attr('action', url2);
                // Add a cancel button
                var cancelButton = $('<a class="cancel action-lnk">' + opts.cancelButtonText + '</a>').on('click', function() {
                        form.slideUp('mediun', function() { frame.remove(); });
                        self._showAll();
                    });
                form.find('input[type="submit"]').after(cancelButton);
                // Show the form
                contact.after(frame).hide();
                frame.find('#popup').show();
                form.show();
                frame.slideDown('medium');
            });
        },

        /**
         * Delete a contact (Ajax)
         *
         * @param {jQuery} element - the contact container (.pr-contact)
         */
        _deleteContact: function(element) {

            // @todo: show throbber
            if (confirm(i18n.delete_confirmation)) {
                var recordID = element.data('id');
                // @todo: check for success
                // @todo: show confirmation message
                $.post(S3.Ap.concat('/pr/contact/' + recordID + '/delete.json'));
                element.hide();
            }
        },

        /**
         * Delete an emergency contact (Ajax)
         *
         * @param {jQuery} element - the contact container (.pr-emergency-contact)
         */
        _deleteEmergencyContact: function(element) {

            // @todo: show throbber
            if (confirm(i18n.delete_confirmation)) {
                var recordID = element.data('id');
                // @todo: check for success
                // @todo: show confirmation message
                $.post(S3.Ap.concat('/pr/contact_emergency/' + recordID + '/delete.json'));
                element.remove();
            }
        },

        /**
         * Inline update contact data (jeditable)
         *
         * @param {jQuery} element - the container element (.pr-contact)
         * @param {object} data - the data to update
         */
        _inlineUpdateContact: function(element, data) {

            var contact = $(element);

            var recordID = contact.data('id');
            if (!data.value) {
                data.value = contact.data('value');
            }
            var url = S3.Ap.concat('/pr/contact/' + recordID + '.s3json'),
                success = false;
            $.ajaxS3({
                type: 'POST',
                url: url,
                data: JSON.stringify({'$_pr_contact': data}),
                dataType: 'JSON',
                async: false,
                // gets moved to .done() inside .ajaxS3
                success: function(response) {
                    if (response.status == 'success') {
                        success = true;
                    }
                }
            });
            return success;
        },

        /**
         * Inline update emergency contact data (jeditable)
         *
         * @param {jQuery} element - the container element (.pr-contact)
         * @param {object} data - the data to update
         */
        _inlineUpdateEmergencyContact: function(element, data) {

            var contact = $(element);

            var recordID = contact.data('id');
            var url = S3.Ap.concat('/pr/contact_emergency/' + recordID + '.s3json'),
                success = false;
            $.ajaxS3({
                type: 'POST',
                url: url,
                data: JSON.stringify({'$_pr_contact_emergency': data}),
                dataType: 'JSON',
                async: false,
                // gets moved to .done() inside .ajaxS3
                success: function(response) {
                    if (response.status == 'success') {
                        success = true;
                    }
                }
            });
            return success;
        },

        /**
         * Show all read-rows and add buttons, hide all throbbers
         */
        _showAll: function() {

            var el = $(this.element);
            el.find('.pr-contact, .pr-emergency-contact').each(function() {
                var $this = $(this);
                $this.find('.pr-contact-actions a').show();
                $this.find('.throbber, .inline-throbber').hide();
                $this.show();
            });
            el.find('.contact-add-btn').show();
        },

        /**
         * Bind event handlers (after refresh)
         */
        _bindEvents: function() {

            var self = this,
                element = $(this.element),
                ns = this.eventNamespace;

            element.find('.pr-contacts .contact-add-btn').on('click' + ns, function() {
                // Add new contact
                self._addContact(this);
                return false;
            });

            element.find('.pr-emergency-contacts .contact-add-btn').on('click' + ns, function() {
                // Add new emergency contact
                self._addEmergencyContact(this);
                return false;
            });

            element.on('click' + ns, '.pr-contacts .edit-btn', function() {
                // Edit contact
                self._editContact($(this).closest('.pr-contact'));
                return false;

            }).on('click' + ns, '.pr-emergency-contacts .edit-btn', function() {
                // Edit emergency contact
                self._editEmergencyContact($(this).closest('.pr-emergency-contact'));
                return false;

            }).on('click' + ns, '.pr-contacts .delete-btn-ajax', function() {
                // Delete contact
                self._deleteContact($(this).closest('.pr-contact'));
                return false;

            }).on('click' + ns, '.pr-emergency-contacts .delete-btn-ajax', function() {
                // Delete emergency contact
                self._deleteEmergencyContact($(this).closest('.pr-emergency-contact'));
                return false;
            });

            var opts = {style: 'display: inline',
                        cssclass: 'pr-contacts-editable',
//                         height: 24,
                        indicator : '<div class="throbber">',
                        placeholder: this.options.placeholderText,
                        };
            element.find('.pr-contact-value').editable(function(value) {
                var contact = $(this).closest('.pr-contact');
                if (self._inlineUpdateContact(contact, {'value': value})) {
                    contact.data('value', value);
                    return value;
                } else {
                    return contact.data('value');
                }
            }, opts);
            element.find('.pr-contact-description').editable(function(value) {
                var contact = $(this).closest('.pr-contact');
                if (self._inlineUpdateContact(contact, {'contact_description': value})) {
                    contact.data('description', value);
                    return value;
                } else {
                    return contact.data('description');
                }
            }, opts);
            element.find('.pr-contact-comments').editable(function(value) {
                var contact = $(this).closest('.pr-contact');
                if (self._inlineUpdateContact(contact, {'comments': value})) {
                    contact.data('comments', value);
                    return value;
                } else {
                    return contact.data('comments');
                }
            }, opts);
            element.find('.pr-emergency-name').editable(function(value) {
                var contact = $(this).closest('.pr-emergency-contact');
                if (self._inlineUpdateEmergencyContact(contact, {'name': value})) {
                    contact.data('name', value);
                    return value;
                } else {
                    return contact.data('name');
                }
            }, opts);
            element.find('.pr-emergency-relationship').editable(function(value) {
                var contact = $(this).closest('.pr-emergency-contact');
                if (self._inlineUpdateEmergencyContact(contact, {'relationship': value})) {
                    contact.data('relationship', value);
                    return value;
                } else {
                    return contact.data('relationship');
                }
            }, opts);
            element.find('.pr-emergency-phone').editable(function(value) {
                var contact = $(this).closest('.pr-emergency-contact');
                if (self._inlineUpdateEmergencyContact(contact, {'phone': value})) {
                    contact.data('phone', value);
                    return value;
                } else {
                    return contact.data('phone');
                }
            }, opts);
            element.find('.pr-emergency-address').editable(function(value) {
                var contact = $(this).closest('.pr-emergency-contact');
                if (self._inlineUpdateEmergencyContact(contact, {'address': value})) {
                    contact.data('address', value);
                    return value;
                } else {
                    return contact.data('address');
                }
            }, opts);
            element.find('.pr-emergency-comments').editable(function(value) {
                var contact = $(this).closest('.pr-emergency-contact');
                if (self._inlineUpdateEmergencyContact(contact, {'comments': value})) {
                    contact.data('comments', value);
                    return value;
                } else {
                    return contact.data('comments');
                }
            }, opts);
            var priority_opts = {
                style: 'display: inline-block;',
                cssclass: 'pr-contacts-editable',
                data: function(value) {
                    var opts = '{';
                    for (var i = 1; i < 10; i++) {
                        opts += '"' + i + '":"' + i + '",';
                    }
                    opts += '"selected":"' + value + '"}';
                    return opts;
                },
                type: 'select',
                submit: 'ok'
            };
            element.find('.pr-contact-priority').editable(function(value) {
                var contact = $(this).closest('.pr-contact');
                if (self._inlineUpdateContact(contact, {'priority': value})) {
                    contact.data('priority', value);
                    return value;
                } else {
                    return contact.data('priority');
                }
            }, priority_opts);

            return true;
        },

        /**
         * Unbind events (before refresh)
         */
        _unbindEvents: function() {

            var element = $(this.element),
                ns = this.eventNamespace;

            element.off(ns);
            element.find('.pr-contact-add, .pr-emergency-add, .pr-contact-form').of(ns);

            return true;
        }
    });
})(jQuery);

// END ========================================================================
