/**
 * jQuery UI HierarchicalCRUD Widget for S3HierarchyCRUD
 *
 * @copyright 2014 (c) Sahana Software Foundation
 * @license MIT
 *
 * requires jQuery 1.9.1+
 * requires jQuery UI 1.10 widget factory
 * requires jQuery jstree 1.0
 */
(function($, undefined) {

    var hierarchicalcrudID = 0;

    /**
     * HierarchicalCRUD widget
     */
    $.widget('s3.hierarchicalcrud', {

        /**
         * Default options
         */
        options: {
            widgetID: null,
            ajaxURL: null,
            openLabel: 'Open',
            openURL: null,
            editTitle: 'Edit Record',
            editLabel: 'Edit',
            editURL: null,
            deleteLabel: 'Delete',
            deleteURL: null,
            addLabel: 'Add',
            addURL: null,
            themesFolder: 'static/styles/jstree',
            theme: 'default',
            htmlTitles: true
        },

        /**
         * Create the widget
         */
        _create: function() {

            this.id = hierarchicalcrudID;
            hierarchicalcrudID += 1;
        },

        /**
         * Update the widget options
         */
        _init: function() {

            var el = $(this.element);
            
            // The tree
            this.tree = el.find('.s3-hierarchy-tree')
            
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

            var tree = this.tree,
                opts = this.options;

            this._unbindEvents();

            // Select theme
            var rtl,
                theme;
            $.jstree._themes = S3.Ap.concat('/', opts.themesFolder, '/');
            if ($('body').css('direction') == 'ltr') {
                rtl = false;
                theme = opts.theme;
            } else {
                rtl = true;
                theme = opts.theme + '-rtl';
            }

            // If there's only one root node, start with this node open
            var initially_open = [],
                roots = tree.find('> ul > li');
            if (roots.length == 1) {
                initially_open.push(roots.attr('id'));
            }

            var self = this;

            // Render tree
            tree.jstree({
                'core': {
                    animation: 100,
                    check_callback: true,
                    html_titles: opts.htmlTitles,
                    initially_open: initially_open,
                    rtl: rtl
                },
                'themes': {
                    icons: false,
                    theme: theme
                },
                'ui': {
                    select_limit: 1,
                },
                'contextmenu': {
                    items: {
                        "create": null,
                        "rename": null,
                        "remove": null,
                        "ccp": null,
                        "open": {
                            label: self.options.openLabel,
                            action: function(node) {
                                self._openNode(node);
                            },
                            separator_after: true
                        },
                        "edit": {
                            label: self.options.editLabel,
                            action: function(node) {
                                self._editNode(node);
                            }
                        },
                        "delete": {
                            label: self.options.deleteLabel,
                            separator_after: true,
                            _disabled: true
                        },
                        "add": {
                            label: self.options.addLabel,
                            _disabled: true
                        },
                    },
                    select_node: true
                },
                'plugins': ['themes', 'html_data', 'ui', 'sort', 'contextmenu']
            });

            this._bindEvents();
        },

        /**
         * Open a node
         *
         * @param {jQuery} node - the node object (li element)
         */
        _openNode: function(node) {
            
            var openURL = this.options.openURL,
                id = node.attr('id');
            if (!openURL || !id) {
                return;
            }
            var record_id = parseInt(id.split('-').pop());
            if (record_id) {
                openURL = openURL.replace('[id]', record_id)
                                 .replace('%5Bid%5D', record_id);
                window.location.href = openURL;
            }
        },

        /**
         * Refresh a node
         *
         * @param {jQuery} node - the node object (li element)
         */
        refreshNode: function(node) {

            var ajaxURL = this.options.ajaxURL,
                id = node.attr('id');
            if (!ajaxURL || !id) {
                return;
            }
            var record_id = parseInt(id.split('-').pop());
            if (record_id) {
                ajaxURL = ajaxURL + '?node=' + record_id;
                var tree = this.tree;
                $.getJSONS3(ajaxURL, function (data) {
                    if (data.label) {
                        tree.jstree('rename_node', node, data.label);
                    }
                });
            }
            
        },

        /**
         * Edit a node in a popup and refresh the node
         *
         * @param {jQuery} node - the node object (li element)
         */
        _editNode: function(node) {
            
            var editURL = this.options.editURL,
                id = node.attr('id');
            if (!editURL || !id) {
                return;
            }
            var record_id = parseInt(id.split('-').pop());
            if (record_id) {

                var url = editURL.replace('[id]', record_id)
                                 .replace('%5Bid%5D', record_id)
                                 .split('?')[0];

                url += '?node=' + id + '&hierarchy=' + this.options.widgetID;

                // Open a jQueryUI Dialog showing a spinner until iframe is loaded
                var uid = S3.uid();
                var dialog = $('<iframe id="' + uid + '" src=' + url + ' onload="S3.popup_loaded(\'' + uid + '\')" class="loading" marginWidth="0" marginHeight="0" frameBorder="0"></iframe>')
                            .appendTo('body');
                            
                dialog.dialog({
                    // add a close listener to prevent adding multiple divs to the document
                    close: function(event, ui) {
                        if (self.parent) {
                            // There is a parent modal: refresh it to fix layout
                            var iframe = self.parent.$('iframe.ui-dialog-content');
                            var width = iframe.width();
                            iframe.width(0);
                            window.setTimeout(function() {
                                iframe.width(width);
                            }, 300);
                        }
                        // Remove div with all data and events
                        dialog.remove();
                    },
                    minHeight: 480,
                    modal: true,
                    open: function(event, ui) {
                        $('.ui-widget-overlay').bind('click', function() {
                            dialog.dialog('close');
                        });
                    },
                    title: this.options.editTitle,
                    minWidth: 320,
                    closeText: ''
                });
            }
        },

        /**
         * Bind events to generated elements (after refresh)
         */
        _bindEvents: function() {
            return true;
        },

        /**
         * Unbind events (before refresh)
         */
        _unbindEvents: function() {
            return true;
        }
    });
})(jQuery);
