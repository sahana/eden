/**
 * jQuery UI HierarchicalOpts Widget for S3HierarchyWidget/S3HierarchyFilter
 *
 * @copyright 2013-2021 (c) Sahana Software Foundation
 * @license MIT
 *
 * requires jQuery 1.9.1+
 * requires jQuery UI 1.10 widget factory
 * requires jQuery jstree 3.0.3
 *
 */
(function($, undefined) {

    "use strict";
    var hierarchicaloptsID = 0;

    /**
     * HierarchicalOpts widget
     */
    $.widget('s3.hierarchicalopts', {

        /**
         * Default options
         *
         * @prop {array} selected - the record IDs of initially selected nodes
         * @prop {bool} multiple - allow selection of multiple nodes (default: true)
         * @prop {bool} leafonly - return only leaf nodes (default: true); with
         *                         multiple=true, this will automatically select all
         *                         child nodes when selecting a parent node  - with
         *                         multiple=false, this will inhibit the selection of
         *                         any parent nodes
         * @prop {bool} cascade - automatically select child nodes when selecting a
         *                        parent node, only with multiple=true and leafonly=false;
         *                        if set to false, an explicit option to select/deselect
         *                        all child nodes will be available
         * @prop {bool} cascadeOptionInTree - see cascade; if true, the explicit option to
         *                                    select/deselect all child nodes will be shown
         *                                    as nodes inside the tree - if false, the
         *                                    option will be rendered as context-menu for
         *                                    parent nodes; default is true
         * @prop {bool} bulkSelect - provide an option to select/deselect all available nodes;
         *                           this option will be rendered inside the tree when
         *                           cascadeOptionInTree=true, otherwise separate as header
         * @prop {string} noneSelectedText - localized button label when no options selected
         * @prop {string} selectedText - localized button label when options selected
         * @prop {string} noOptionsText - localized message for 'no options available'
         * @prop {string} selectAllText - localized label for 'select all'
         * @prop {string} deselectAllText - localized label for 'deselect all'
         * @prop {bool} icons - show icons for nodes (default: false)
         * @prop {bool} sep - separator to use to concatenate the hierarchy to represent the selected node (default: don't concatenate)
         * @prop {bool} stripes - render alternating background for even/odd rows (default: true)
         * @prop {bool} htmlTitles - treat node titles as HTML (default: true)
         */
        options: {
            selected: null,

            multiple: true,
            leafonly: true,
            cascade: false,
            bulkSelect: false,
            cascadeOptionInTree: true,

            noneSelectedText: 'Select',
            selectedText: 'selected',
            noOptionsText: 'No options available',
            selectAllText: 'Select All',
            deselectAllText: 'Deselect All',

            icons: false,
            sep: null,
            stripes: true,
            htmlTitles: true
        },

        /**
         * Create the widget
         */
        _create: function() {

            var el = $(this.element),
                opts = this.options;

            this.id = hierarchicaloptsID;
            hierarchicaloptsID += 1;

            this._namespace = '.hierarchicalopts' + hierarchicaloptsID;

            this.treeID = el.attr('id') + '-tree';

            // The hidden input field
            this.input = el.find('.s3-hierarchy-input').first();
            this.input.data('input', true);
            var s = opts.selected;
            if (s) {
                this.input.val(this._stringifySelection(s));
            }

            // The button
            this.button = $('<button type="button" class="s3-hierarchy-button ui-multiselect ui-widget ui-state-default ui-corner-all"><span class="ui-icon ui-icon-triangle-1-s"></span></button>');
            this.buttonText = $('<span>' + opts.noneSelectedText + '</span>').appendTo(this.button);

            // No-options section
            this.noopts = $('<span class="no-options-available">' + opts.noOptionsText + '</span>').hide();

            // The tree
            this.tree = el.find('.s3-hierarchy-tree').first();

            // The wrapper
            this.wrapper = this.tree.closest('.s3-hierarchy-wrapper')
                                    .hide()
                                    .before(this.noopts)
                                    .before(this.button)
                                    .detach()
                                    .appendTo('body');

            this._isOpen = false;
            this._isBulk = false;
            this.manualCascadeOption = false;
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

            this._unbindEvents();
            $(this.button).remove();
            $(this.noopts).remove();
            $(this.tree).detach()
                        .appendTo(this.element)
                        .show();
        },

        /**
         * Redraw contents
         */
        refresh: function() {

            this._unbindEvents();

            var opts = this.options,
                tree = this.tree,
                self = this;

            if (!tree.find('li').length) {
                // .hide() not strong enough to beat the !important on .form-container form .ui-multiselect
                this.button.attr('style', 'display:none!important');
                this.noopts.show();
                return;
            } else {
                this.noopts.hide();
                this.button.attr('style', '');
            }

            // Move error-wrapper behind button
            this.input.next('.error_wrapper')
                      .insertAfter(this.button)
                      .one('click', function() { $(this).fadeOut(); });

            // Initially selected nodes
            var currentValue = this.input.val();
            if (currentValue) {
                var selectedValues = this._parseSelection(currentValue),
                    treeID = this.treeID;
                $.each(selectedValues, function() {
                    $('#' + treeID + '-' + this).data('jstree', {selected: true});
                });
            }

            // If there's only one root node, start with this node open
            var roots = tree.find('> ul > li');
            if (roots.length == 1) {
                var root = roots.first();
                var node_data = root.data('jstree');
                root.data('jstree', $.extend({}, node_data, {'opened': true}));
            }

            var multiple = opts.multiple,
                leafonly = opts.leafonly,
                cascade = opts.cascade,
                three_state = false,
                contextMenu = null,
                plugins = ['sort', 'checkbox'];

            this.input.data('multiple', multiple);

            if ((cascade || leafonly ) && multiple) {
                three_state = true;
            } else if (multiple) {
                // Provide a manual cascade-select option
                if (!opts.cascadeOptionInTree) {
                    contextMenu = function(node) {
                        if (tree.jstree('is_parent', node)) {
                            // Context menu for "manual" cascade select
                            $.vakata.context.settings.icons = false;
                            return {
                                'select_all': {
                                    label: self.options.selectAllText,
                                    icon: false,
                                    action: function(obj) {
                                        self._selectBranch(node);
                                    }
                                },
                                'deselect_all': {
                                    label: self.options.deselectAllText,
                                    icon: false,
                                    action: function(obj) {
                                        self._deselectBranch(node);
                                    }
                                }
                            };
                        } else {
                            return null;
                        }
                    };
                    plugins.push('contextmenu');
                } else {
                    this.manualCascadeOption = true;
                }
            }

            tree.jstree({
                'core': {
                    'themes': {
                        //name: 'default', // 'default-dark' available, although not in our sources
                        icons: opts.icons,
                        stripes: opts.stripes
                    },
                    animation: 100,
                    multiple: multiple,
                    check_callback: true
                },
                'checkbox': {
                    three_state: three_state
                },
                'sort' : function (a, b) {
                    // Bulk-select nodes go always first
                    var sorted = this.get_text(a) > this.get_text(b) ? 1 : -1,
                        aRel,
                        bRel;
                    try {
                        aRel = this.get_node(a).li_attr.rel;
                    } catch (e) {
                        aRel = null;
                    }
                    try {
                        bRel = this.get_node(b).li_attr.rel;
                    } catch (e) {
                        bRel = null;
                    }
                    if (aRel == 'bulk') {
                        return -1;
                    } else if (bRel == 'bulk') {
                        return 1;
                    } else if (aRel == 'none') {
                        return -1;
                    } else if (bRel == 'none') {
                        return 1;
                    } else {
                        return sorted;
                    }
                },
                'contextmenu': {
                    items: contextMenu,
                    select_node: false,
                    icons: false
                },
                'plugins': plugins
            });

            var inst = jQuery.jstree.reference(tree);

            // Render bulk-select option?
            if (multiple) {
                if ((opts.bulkSelect || this.manualCascadeOption) && opts.cascadeOptionInTree) {
                    this.wrapper.find('.s3-hierarchy-header').hide();
                    inst.create_node('#', {
                            id: this.treeID + '-select-all',
                            text: opts.selectAllText,
                            li_attr: {
                                'rel': 'bulk',
                                'class': 's3-hierarchy-action-node'
                            }
                        }, 'first');
                } else {
                    this.wrapper.find('.s3-hierarchy-header').removeClass('hide').show();
                }
            }

            // Initial update of button text (wait for ready-event)
            tree.on('ready.jstree', function() {
                var selected = inst.get_checked();
                self._updateButtonText(selected);
            });

            this._bindEvents();
        },

        /**
         * Reload Tree
         * - called from scripts similar to filterOptionsS3
         */
        reload: function(ajaxURL) {
            // Load the data
            var self = this;
            if (ajaxURL.includes('?')) {
                ajaxURL += '&widget_id=' + $(this.element).attr('id');
            } else {
                ajaxURL += '?widget_id=' + $(this.element).attr('id');
            }

            // Remove old JSTree
            this.tree.jstree('destroy');

            // Remove old Value(s)
            this.input.val('');

            $.getS3(ajaxURL, function (data) {

                // Update the DOM
                self.tree.html(data);

                // Redraw the Tree
                self.refresh();

            }, 'html');
        },

        /**
         * Custom actions for option updates
         *
         * @param {string} key - they option key
         * @param {mixed} value - the option value
         */
        _setOption: function(key, value) {

            if ( key === "selected" ) {

                // Check selected nodes and update hidden input
                var inst = jQuery.jstree.reference($(this.tree));
                if (inst) {
                    inst.uncheck_all();
                    if (value) {
                        this.input.val(this._stringifySelection(value));
                        var treeID = this.treeID;
                        $.each(value, function() {
                            inst.check_node('#' + treeID + '-' + this);
                        });
                        this._updateButtonText(value);
                    }
                }
            }
            this._super(key, value);
        },

        /**
         * Get all selected nodes and store the result in the hidden input
         */
        _updateSelectedNodes: function() {

            var inst = jQuery.jstree.reference($(this.tree));

            var oldSelected = this._parseSelection(this.input.val()),
                newSelected = [],
                selectedIDs = [],
                multiple = this.options.multiple,
                leafonly = this.options.leafonly;

            var nodes = inst.get_checked(true);

            $(nodes).each(function() {
                var id = $(this).attr('id');
                if ($(this).attr('rel') == 'bulk') {
                    return; // skip bulk nodes
                }
                if (id && (!leafonly || inst.is_leaf(this))) {
                    var record_id = id.split('-').pop();
                    if (record_id != 'None') {
                        record_id = parseInt(record_id);
                    }
                    if (record_id) {
                        newSelected.push(record_id);
                        selectedIDs.push(id);
                    }
                }
            });

            var changed = false,
                diff = $(newSelected).not(oldSelected).get();
            if (diff.length) {
                changed = true;
            } else {
                diff = $(oldSelected).not(newSelected).get();
                if (diff.length) {
                    changed = true;
                }
            }

            var input = this.input.val(this._stringifySelection(newSelected));

            this._updateButtonText(selectedIDs);
            if (changed) {
                input.trigger('change');
                $(this.element).trigger('select.s3hierarchy');
            }
            return true;
        },

        /**
         * Update the button text with the number of selected items
         *
         * @param {Array} selectedIDs - the HTML element IDs of the currently selected nodes
         */
        _updateButtonText: function(selectedIDs) {

            var text = null,
                options = this.options,
                limit = 1, // @todo: make configurable?
                numSelected = 0;

            if (selectedIDs) {
                numSelected = selectedIDs.length;
            }
            if (numSelected) {
                if (numSelected > limit) {
                    text = options.selectedText.replace('#', numSelected);
                } else {
                    var inst = jQuery.jstree.reference($(this.tree)),
                        items = [],
                        label,
                        parent,
                        selector,
                        sep = options.sep;
                    for (var i = 0; i < numSelected; i++) {
                        if (sep) {
                            // Concatenate the hierarchy
                            selector = selectedIDs[i];
                            label = $('#' + selector + ' > a').text().replace(/^\s+|\s+$/g, '');
                            parent = inst.get_parent(selector);
                            while(parent != '#') {
                                label = $('#' + parent + ' > a').text().replace(/^\s+|\s+$/g, '') + sep + label;
                                parent = inst.get_parent(parent);
                            }
                        } else {
                            // Just show the node Text
                            label = $('#' + selectedIDs[i] + ' > a').text().replace(/^\s+|\s+$/g, '');
                        }
                        items.push(label);
                    }
                    text = items.length ? items.join(' ') : options.noneSelectedText;
                }
            } else {
                text = options.noneSelectedText;
            }
            this.buttonText.text(text);
        },

        /**
         * Update selected nodes and automatically close the menu on mouse-leave
         */
        _updateAndClose: function() {

            if (!this._isBulk) {
                this._updateSelectedNodes();
                var wrapper = this.wrapper,
                    self = this;
                if (self.options.multiple) {
                    wrapper.off('mouseleave.hierarchicalopts')
                           .one('mouseleave.hierarchicalopts', function() {
                        window.setTimeout(function() {
                            self.closeMenu();
                        }, 100);
                    });
                } else {
                    window.setTimeout(function() {
                        self.closeMenu();
                    }, 100);
                }
            }
        },

        /**
         * Actions when selecting a node
         *
         * @param {mixed} node - the node to select
         */
        _selectNode: function(node) {

            var opts = this.options,
                inst = jQuery.jstree.reference($(this.tree));

            var multiple = opts.multiple,
                leafonly = opts.leafonly;

            if (!multiple) {
                // De-select all other selected nodes
                var nodeID = node.id;
                $(inst.get_checked(true)).each(function () {
                    if (nodeID != this.id) {
                        if (!leafonly || inst.is_leaf(this)) {
                            inst.uncheck_node(this);
                        }
                    }
                });
            } else if (!this._isBulk) {
                if (node.li_attr.rel == 'bulk') {
                    var parentID = inst.get_parent(node);
                    if (!parentID || parentID == '#') {
                        // Top-level bulk-select node
                        inst.select_all();
                    } else {
                        // Branch-level bulk-select node
                        var parentNode = inst.get_node(parentID);
                        this._selectBranch(parentNode, true);
                    }
                }
            }
            if (leafonly && !multiple && !inst.is_leaf(node)) {
              inst.deselect_node(node);
              return false;
            }
            this._updateAndClose();
        },

        /**
         * Actions when deselecting a node
         *
         * @param {mixed} node - the node to deselect
         */
        _deselectNode: function(node) {

            var inst = jQuery.jstree.reference($(this.tree));

            if (!this._isBulk) {
                if (node.li_attr.rel == 'bulk') {
                    var parentID = inst.get_parent(node);
                    if (!parentID || parentID == '#') {
                        inst.deselect_all();
                    } else {
                        var parentNode = inst.get_node(parentID);
                        this._deselectBranch(parentNode, true);
                    }
                } else {
                    var parentID = inst.get_parent(node);
                    if (parentID) {
                        var bulkNode = inst.get_node(parentID + '-select-all');
                        if (bulkNode) {
                            this._isBulk = true;
                            inst.uncheck_node(bulkNode);
                            this._isBulk = false;
                        }
                    }
                }
                var selectAllNode = inst.get_node(this.treeID + '-select-all');
                if (selectAllNode) {
                    this._isBulk = true;
                    inst.uncheck_node(selectAllNode);
                    this._isBulk = false;
                }
            }
            this._updateSelectedNodes();
        },

        /**
         * Action when opening a node
         *
         * @param {mixed} node - the node to open
         */
        _openNode: function(node) {

            var inst = jQuery.jstree.reference($(this.tree));

            var parent = inst.get_parent(node);
            if(parent.length) {
                inst.open_node(parent, false, true);
            }
            if (this.manualCascadeOption) {
                var nodeID = node.id;
                var bulkNode = inst.get_node(nodeID + '-select-all');
                if (!bulkNode) {
                    var bulkNodeID = inst.create_node(node, {
                            id: nodeID + '-select-all',
                            text: this.options.selectAllText,
                            li_attr: {
                                'rel': 'bulk',
                                'class': 's3-hierarchy-action-node'
                            }
                        }, 'first'
                    );
                    bulkNode = inst.get_node(bulkNodeID);
                }
                var selectAllNode = inst.get_node(this.treeID + '-select-all');
                if (selectAllNode && inst.is_checked(selectAllNode)) {
                    this._isBulk = true;
                    inst.check_node(bulkNode);
                    this._isBulk = false;
                }
            }
        },

        /**
         * Recursively select a branch
         *
         * @param {jQuery} node - the top node of the branch
         */
        _selectBranch: function(node, exceptParent) {

            var inst = jQuery.jstree.reference($(this.tree)),
                self = this;

            this._isBulk = true;
            inst.open_node(node, function() {
                var children = inst.get_children_dom(node);
                $(children).each(function() {
                    self._selectBranch(this);
                });
                if (!exceptParent) {
                    inst.check_node(node);
                }
            });
            this._isBulk = false;
            this._updateAndClose();
        },

        /**
         * Recursively de-select a branch
         *
         * @param {jQuery} node - the top node of the branch
         */
        _deselectBranch: function(node, exceptParent) {

            var inst = jQuery.jstree.reference($(this.tree)),
                self = this;

            this._isBulk = true;
            inst.open_node(node, function() {
                var children = inst.get_children_dom(node);
                $(children).each(function() {
                    self._deselectBranch(this);
                });
                if (!exceptParent) {
                    inst.uncheck_node(node);
                }
            });
            this._isBulk = false;
            this._updateSelectedNodes();
        },

        /**
         * Check particular nodes
         * - used by setCurrentFilters, s3.inv_req_item.js and s3.inv_send_item.js
         *
         * @param {Array} values - the record IDs of the nodes to select
         */
        set: function(values) {

            var inst = jQuery.jstree.reference($(this.tree)),
                node,
                self = this,
                treeID = this.treeID;

            this._isBulk = true;
            inst.uncheck_all();
            inst.close_all();
            if (values) {
                var openAncestors = function(nodeID, callback) {
                    var parent = inst.get_parent(nodeID);
                    if (parent) {
                        if (parent != '#') {
                            openAncestors(parent);
                            inst.open_node(parent, callback);
                        } else if (callback) {
                            callback();
                        }
                    }
                };
                values.forEach(function(index) {
                    var node = inst.get_node(treeID + '-' + index);
                    if (node) {
                        // must open all ancestors to make sure
                        // there is a DOM node for check_node (otherwise
                        // nothing gets checked), and for better UX anyway
                        openAncestors(node, function() {
                            inst.check_node(node);
                        });
                    }
                });
            }
            this._isBulk = false;
            this._updateSelectedNodes();
        },

        /**
         * Show just particular nodes
         * - used by s3.inv_req_item.js
         *
         * @param {Array} values - the record IDs of the nodes to select
         * @param {Boolean} uncheck - whether to uncheck all nodes
         */
        show: function(values, uncheck) {

            var inst = jQuery.jstree.reference($(this.tree)),
                node,
                treeID = this.treeID;

            this._isBulk = true;
            if (uncheck) {
                inst.uncheck_all();
            }
            inst.hide_all();
            if (values) {
                var showAncestors = function(nodeID, callback) {
                    var parent = inst.get_parent(nodeID);
                    if (parent != '#') {
                        showAncestors(parent, callback);
                        inst.show_node(parent);
                    } else if (callback) {
                        callback();
                    }
                };
                values.forEach(function(index) {
                    var node = inst.get_node(treeID + '-' + index);
                    if (node) {
                        // must show all ancestors to make sure
                        // there is a DOM node for show_node (otherwise
                        // nothing gets shown)
                        showAncestors(node, function() {
                            inst.show_node(node);
                        });
                    }
                });
            }
            this._isBulk = false;
            if (uncheck) {
                this._updateSelectedNodes();
            }
        },

        /**
         * Get all checked nodes (used by getCurrentFilters)
         *
         * @returns {Array} the nodeIDs of the currently selected nodes
         */
        get: function() {

            return this._parseSelection(this.input.val());
        },

        /**
         * Uncheck all nodes (used by clearFilters)
         */
        reset: function() {

            var inst = jQuery.jstree.reference($(this.tree));

            this._isBulk = true;
            inst.uncheck_all();
            inst.close_all();
            this._isBulk = false;

            this._updateSelectedNodes();
            return true;
        },

        /**
         * Helper to set correct position of menu
         *
         * @param {jQuery} wrapper - the menu wrapper
         * @param {jQuery} button - the menu button
         */
        _setMenuPosition: function(wrapper, button) {

            var pos = button.offset(),
                css = {
                    position: 'absolute',
                    top: pos.top + button.outerHeight(),
                    minWidth: button.outerWidth() - 8
                };

            if ($('body').css('direction') === 'rtl') {
                // Right-align with button
                css.right = ($(window).width() - (pos.left + button.outerWidth()));
            } else {
                // Left-align with button
                css.left = pos.left;
            }
            wrapper.css(css);
        },

        /**
         * Open the tree (triggers 'open'-event)
         */
        openMenu: function() {

            if (this._isOpen) {
                this.closeMenu();
            }

            // Set correct menu position (+update on resize)
            var button = $(this.button),
                wrapper = $(this.wrapper),
                self = this;

            this._setMenuPosition(wrapper, button);
            $(window).on('resize' + this._namespace + '-mpos', function() {
                self._setMenuPosition(wrapper, button);
            });

            wrapper.show();

            $(this.tree).jstree('set_focus');

            this._isOpen = true;
            button.addClass('ui-state-active');

            $(this).trigger('open');
        },

        /**
         * Close the tree (triggers 'close'-event)
         */
        closeMenu: function() {

            // Disable resize event handler
            $(window).off(this._namespace + '-mpos');

            $(this.tree).jstree('unset_focus')
                        .off('click.hierarchicalopts')
                        .off('mouseleave.hierarchicalopts');
            $(this.wrapper).fadeOut(50);
            this._isOpen = false;
            $(this.button).removeClass('ui-state-active');
            $(this).trigger('close');
        },

        /**
         * Add a new node
         *
         * @param {Number} parent - the parent nodeID
         * @param {Number} id - the new nodeID
         * @param {String} title - the node title
         * @param {bool} check - check the node after adding it
         */
        addNode: function(parent, id, title, check) {

            var manual,
                tree = this.tree,
                treeID = this.treeID,
                nodeID = treeID + '-' + id,
                inst = jQuery.jstree.reference(tree);

            if (inst) {
                // We have an instance to add a node to
                var parentNode = '#';

                // Get parent node
                if (parent) {
                    var parentNode = $('#' + treeID + '-' + parent + '_anchor');
                    if (!parentNode.length) {
                        // parentNode not yet in the tree, so need to open it's parent
                        //tree.jstree('open_all', '#'); // Would be better if we knew which root node to open, but we don't, so need to open all
                        tree.jstree('open_all');
                        parentNode = $('#' + treeID + '-' + parent + '_anchor');
                    }
                }
                // Insert the node
                tree.jstree('create_node', parentNode, {
                    id: nodeID,
                    text: title,
                    li_attr: {
                        // HTML attributes of the new node
                        rel: 'leaf'
                    }
                }, "last");

                if (parent) {
                    // Update the parent relationship and open the parent node
                    parentNode.attr({rel: 'parent'});
                    tree.jstree('open_node', parentNode);
                }
            } else {
                // We do not have an instance to add a node to, so need to add manually & refresh
                var node = '<li rel="leaf" class="s3-hierarchy-node" id="' + nodeID + '">' + title + '</li>';
                $('#' + treeID).append(node);
                this.refresh();
            }

            if (check) {
                tree.jstree('check_node', $('#' + nodeID));
            }
        },

        /**
         * Parse the current selection from the real input (JSON)
         *
         * @param {string} value - the JSON value of the real input
         * @returns {Array} - the selected values as Array
         */
        _parseSelection: function(value) {

            if (!!value) {
                var selected = JSON.parse(value);
            } else {
                return [];
            }

            if (!!selected) {
                if (selected.constructor !== Array) {
                    // Single select => convert to array
                    selected = [selected];
                }
            } else {
                selected = [];
            }
            return selected;
        },

        /**
         * Stringify the current selection for the real input (JSON)
         *
         * @param {Array} selected - the selected node IDs
         * @returns {string} - the value for the real input (JSON)
         */
        _stringifySelection: function(selected) {

            if (!this.options.multiple) {
                if (selected.length) {
                    // Single select => convert to single value
                    selected = selected[0];
                } else {
                    return '';
                }
            }
            return JSON.stringify(selected);
        },

        /**
         * Bind events to generated elements (after refresh)
         */
        _bindEvents: function() {

            var self = this,
                wrapper = $(this.wrapper),
                tree = $(this.tree),
                button = $(this.button),
                ns = this._namespace,
                opts = this.options;

            // Get the instance
            var inst = jQuery.jstree.reference(tree);

            // Cancel auto-close when opening a context menu
            var icons = $.vakata.context.settings.icons;
            $(document).on('context_show.vakata', function() {
                wrapper.off('mouseleave.hierarchicalopts');
                $.vakata.context.settings.icons = icons;
            });

            // Open/select/deselect nodes
            tree.on('select_node.jstree', function (event, data) {
                self._selectNode(data.node);
            }).on('deselect_node.jstree', function (event, data) {
                self._deselectNode(data.node);
            }).on("open_node.jstree", function (event, data) {
                self._openNode(data.node);
            });

            // Button events (mimic multiselect)
            button.on('click' + ns, function() {
                if (!self._isOpen) {
                    self.openMenu();
                } else {
                    self.closeMenu();
                }
            }).on('keyup' + ns, function(event) {
                event.preventDefault();
                switch(event.keyCode) {
                    case 27: // esc
                    case 38: // up
                    case 37: // left
                        self.closeMenu();
                        break;
                    case 39: // right
                    case 40: // down
                        self.openMenu();
                        break;
                }
            }).on('mouseenter' + ns, function() {
                if (!button.hasClass('ui-state-disabled')) {
                    $(this).addClass('ui-state-hover');
                }
            }).on('mouseleave' + ns, function() {
                $(this).removeClass('ui-state-hover');
            }).on('focus' + ns, function() {
                if (!button.hasClass('ui-state-disabled')) {
                    $(this).addClass('ui-state-focus');
                }
            }).on('blur' + ns, function() {
                $(this).removeClass('ui-state-focus');
            });

            if (opts.multiple && opts.bulkSelect && !opts.cascadeOptionInTree) {
                // Bulk selection/de-selection from separate header
                wrapper.find('.s3-hierarchy-select-all')
                    .on('click' + ns, function(event) {
                    event.preventDefault();
                    inst.select_all();
                    self._updateSelectedNodes();
                });
                wrapper.find('.s3-hierarchy-deselect-all')
                    .on('click' + ns, function(event) {
                    event.preventDefault();
                    inst.deselect_all();
                    self._updateSelectedNodes();
                });
                // Prevent propagation of click/mousedown events
                wrapper.find('.s3-hierarchy-header')
                       .on('click' + ns, function(event) {
                    event.preventDefault();
                    event.stopPropagation();
                }).on('mousedown' + ns, function(event) {
                    event.preventDefault();
                    event.stopPropagation();
                });
            }

            // Auto-close when clicking outside the menu or button
            $(document).on('mousedown' + ns, function(event) {

                var target = event.target;
                if ($('.jstree-contextmenu').has(target).length || event.which == 3) {
                    // Cancel auto-close when opening/interacting with context menu
                    wrapper.off('mouseleave.hierarchicalopts');
                    return true;
                }
                if (!tree.is(target) && !button.is(target) &&
                    tree.has(target).length === 0 &&
                    button.has(target).length === 0) {
                    self.closeMenu();
                }
            });
            return true;
        },

        /**
         * Unbind events (before refresh)
         */
        _unbindEvents: function() {

            var tree = $(this.tree),
                button = $(this.button),
                ns = this._namespace;

            tree.off('select_node.jstree')
                .off('deselect_node.jstree')
                .off('loaded.jstree')
                .off('open_node.jstree');

            $(this.button).off(ns);
            $(document).off(ns);

            return true;
        }
    });
})(jQuery);
