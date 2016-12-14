/**
 * jQuery UI HierarchicalOpts Widget for S3HierarchyWidget/S3HierarchyFilter
 *
 * @copyright 2013-2016 (c) Sahana Software Foundation
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
                this.input.val(JSON.stringify(s));
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
                tree = this.tree;

            if (!tree.find('li').length) {
                this.button.hide();
                this.noopts.show();
                return;
            } else {
                this.noopts.hide();
                this.button.show();
            }

            // Move error-wrapper behind button
            this.input.next('.error_wrapper')
                      .insertAfter(this.button)
                      .one('click', function() { $(this).fadeOut(); });

            // Initially selected nodes
            var currentValue = this.input.val();
            if (currentValue) {
                var selectedValues = JSON.parse(currentValue);
                var treeID = this.treeID;
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
                    var self = this;
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
                        name: 's3',
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
                        }, "first"
                    );
                } else {
                    this.wrapper.find('.s3-hierarchy-header').removeClass('hide').show();
                }
            }

            // Initial update of button text (wait for ready-event)
            var self = this;
            tree.on('ready.jstree', function() {
                var selected = inst.get_checked();
                self._updateButtonText(selected);
            });

            this._bindEvents();
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
                if (inst !== undefined) {
                    inst.uncheck_all();
                    if (value) {
                        this.input.val(JSON.stringify(value));
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

            var old_selected = this.input.val();
            if (old_selected) {
                old_selected = JSON.parse(old_selected);
            } else {
                old_selected = [];
            }

            var new_selected = [],
                selected_ids = [],
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
                        new_selected.push(record_id);
                        selected_ids.push(id);
                    }
                }
            });

            var changed = false,
                diff = $(new_selected).not(old_selected).get();
            if (diff.length) {
                changed = true;
            } else {
                diff = $(old_selected).not(new_selected).get();
                if (diff.length) {
                    changed = true;
                }
            }

            this.input.val(JSON.stringify(new_selected));
            this._updateButtonText(selected_ids);
            if (changed) {
                this.input.change();
                $(this.element).trigger('select.s3hierarchy');
            }
            return true;
        },

        /**
         * Update the button text with the number of selected items
         *
         * @param {Array} selected_ids - the HTML element IDs of the currently selected nodes
         */
        _updateButtonText: function(selected_ids) {

            var text = null,
                options = this.options,
                limit = 1, // @todo: make configurable?
                numSelected = 0;

            if (selected_ids) {
                numSelected = selected_ids.length;
            }
            if (numSelected) {
                if (numSelected > limit) {
                    text = options.selectedText.replace('#', numSelected);
                } else {
                    var items = [];
                    for (var i=0; i < numSelected; i++) {
                        items.push($('#' + selected_ids[i] + " > a").text().replace(/^\s+|\s+$/g, ''));
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
                    wrapper.unbind('mouseleave.hierarchicalopts')
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
                        }, "first"
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
         * Check particular nodes (used by setCurrentFilters)
         *
         * @param {Array} values - the nodeIDs of the nodes to select
         */
        set: function(values) {

            var inst = jQuery.jstree.reference($(this.tree));

            inst.uncheck_all();
            if (values) {
                for (var i=0, len=values.length, nodeID; i < len; i++) {
                    nodeID = $('#' + this.treeID + '-' + values[i]);
                    inst.check_node(nodeID);
                }
            }
        },

        /**
         * Get all checked nodes (used by getCurrentFilters)
         *
         * @returns {Array} the nodeIDs of the currently selected nodes
         */
        get: function() {

            var value = this.input.val();
            if (value) {
                return JSON.parse(value);
            } else {
                return [];
            }
        },

        /**
         * Uncheck all nodes (used by clearFilters)
         */
        reset: function() {

            this._isBulk = true;
            this.tree.jstree('uncheck_all');
            this._isBulk = false;
            this._updateSelectedNodes();

            return true;
        },

        /**
         * Open the tree (triggers 'open'-event)
         */
        openMenu: function() {

            if (this._isOpen) {
                this.closeMenu();
            }

            var button = $(this.button);
            var pos = button.offset();

            $(this.wrapper).css({
                position: 'absolute',
                top: pos.top + button.outerHeight(),
                left: pos.left,
                minWidth: button.outerWidth() - 8
            }).show();

            $(this.tree).jstree('set_focus');
            this._isOpen = true;
            button.addClass('ui-state-active');

            $(this).trigger('open');
        },

        /**
         * Close the tree (triggers 'close'-event)
         */
        closeMenu: function() {

            $(this.tree).jstree('unset_focus')
                        .unbind('click.hierarchicalopts')
                        .unbind('mouseleave.hierarchicalopts');
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

            var tree = this.tree,
                treeID = this.treeID,
                parentNode = '#';

            // Get parent node
            if (parent) {
                parentNode = $('#' + treeID + '-' + parent);
                if (!parentNode.length) {
                    parentNode = '#';
                }
            }

            // Insert the node
            var nodeID = treeID + '-' + id;
            tree.jstree('create_node', parentNode, {
                id: nodeID,
                text: title,
                li_attr: {
                    // HTML attributes of the new node
                    rel: 'leaf'
                }
            }, "last");

            // Update the parent relationship and open the parent node
            if (parent) {
                parentNode.attr({rel: 'parent'});
                tree.jstree('open_node', parentNode);
            }
            if (check) {
                tree.jstree('check_node', $('#' + nodeID));
            }
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
            $(document).bind('context_show.vakata', function() {
                wrapper.unbind('mouseleave.hierarchicalopts');
                $.vakata.context.settings.icons = icons;
            });

            // Open/select/deselect nodes
            tree.bind('select_node.jstree', function (event, data) {
                self._selectNode(data.node);
            }).bind('deselect_node.jstree', function (event, data) {
                self._deselectNode(data.node);
            }).bind("open_node.jstree", function (event, data) {
                self._openNode(data.node);
            });

            // Button events (mimic multiselect)
            button.bind('click' + ns, function() {
                if (!self._isOpen) {
                    self.openMenu();
                } else {
                    self.closeMenu();
                }
            }).bind('keyup' + ns, function(event) {
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
            }).bind('mouseenter' + ns, function() {
                if (!button.hasClass('ui-state-disabled')) {
                    $(this).addClass('ui-state-hover');
                }
            }).bind('mouseleave' + ns, function() {
                $(this).removeClass('ui-state-hover');
            }).bind('focus' + ns, function() {
                if (!button.hasClass('ui-state-disabled')) {
                    $(this).addClass('ui-state-focus');
                }
            }).bind('blur' + ns, function() {
                $(this).removeClass('ui-state-focus');
            });

            if (opts.multiple && opts.bulkSelect && !opts.cascadeOptionInTree) {
                // Bulk selection/de-selection from separate header
                wrapper.find('.s3-hierarchy-select-all')
                    .bind('click' + ns, function(event) {
                    event.preventDefault();
                    inst.select_all();
                    self._updateSelectedNodes();
                });
                wrapper.find('.s3-hierarchy-deselect-all')
                    .bind('click' + ns, function(event) {
                    event.preventDefault();
                    inst.deselect_all();
                    self._updateSelectedNodes();
                });
                // Prevent propagation of click/mousedown events
                wrapper.find('.s3-hierarchy-header')
                       .bind('click' + ns, function(event) {
                    event.preventDefault();
                    event.stopPropagation();
                }).bind('mousedown' + ns, function(event) {
                    event.preventDefault();
                    event.stopPropagation();
                });
            }

            // Auto-close when clicking outside the menu or button
            $(document).bind('mousedown' + ns, function(event) {

                var target = event.target;
                if ($('.jstree-contextmenu').has(target).length || event.which == 3) {
                    // Cancel auto-close when opening/interacting with context menu
                    wrapper.unbind('mouseleave.hierarchicalopts');
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

            tree.unbind('select_node.jstree')
                .unbind('deselect_node.jstree')
                .unbind('loaded.jstree')
                .unbind('open_node.jstree');

            $(this.button).unbind(ns);
            $(document).unbind(ns);

            return true;
        }
    });
})(jQuery);
