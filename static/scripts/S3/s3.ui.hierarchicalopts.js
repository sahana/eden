/**
 * jQuery UI HierarchicalOpts Widget for S3HierarchyFilter
 *
 * @copyright 2013-14 (c) Sahana Software Foundation
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
         * @todo document options
         */
        options: {
            selected: null,
            noneSelectedText: 'Select',
            selectedText: 'selected',
            noOptionsText: 'No options available',
            multiple: true,
            leafonly: true,
            cascade: false,
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
                contextMenu = null;

            if ((cascade || leafonly ) && multiple) {
                three_state = true;
            } else if (multiple) {
                var self = this;
                contextMenu = function(node) {
                    if (tree.jstree('is_parent', node)) {
                        // Context menu for "manual" cascade select
                        $.vakata.context.settings.icons = false;
                        return {
                            'select_all': {
                                label: "Select All",
                                icon: false,
                                action: function(obj) {
                                    self._selectBranch(node);
                                }
                            },
                            'deselect_all': {
                                label: "Deselect All",
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
                'contextmenu': {
                    items: contextMenu,
                    select_node: false,
                    icons: false
                },
                'plugins': ['sort', 'checkbox', 'contextmenu']
            });

            var selected = tree.jstree('get_checked');
            this._updateButtonText(selected);
            this.wrapper.find('.s3-hierarchy-header')
                        .removeClass('hide')
                        .show();
            this._bindEvents();
        },

        /**
         * Get all selected nodes and store the result in the hidden input
         */
        _updateSelectedNodes: function() {


            var old_selected = this.input.val();
            if (old_selected) {
                old_selected = JSON.parse(old_selected);
            } else {
                old_selected = [];
            }

            var tree = this.tree,
                new_selected = [],
                selected_ids = [],
                multiple = this.options.multiple,
                leafonly = this.options.leafonly;

            var nodes = tree.jstree('get_checked', true);

            $(nodes).each(function() {
                var id = $(this).attr('id');
                if (id && (!leafonly || tree.jstree('is_leaf', this))) {
                    var record_id = parseInt(id.split('-').pop());
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
         * Recursively select a branch
         *
         * @param {jQuery} node - the top node of the branch
         */
        _selectBranch: function(node) {

            var tree = this.tree,
                self = this;

            this._isBulk = true;
            tree.jstree('open_node', node, function() {
                var children = tree.jstree('get_children_dom', node);
                $(children).each(function() {self._selectBranch(this);});
                tree.jstree('check_node', node);
            });

            this._isBulk = false;
            this._updateAndClose();
        },

        /**
         * Recursively de-select a branch
         *
         * @param {jQuery} node - the top node of the branch
         */
        _deselectBranch: function(node) {

            var tree = this.tree,
                self = this;
            this._isBulk = true;
            tree.jstree('open_node', node, function() {
                var children = tree.jstree('get_children_dom', node);
                $(children).each(function() {self._deselectBranch(this);});
                tree.jstree('uncheck_node', node);
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

            this.tree.jstree('uncheck_all');
            if (values) {
                for (var i=0, len=values.length, node; i < len; i++) {
                    node = $('#' + this.treeID + '-' + values[i]);
                    this.tree.jstree('check_node', node);
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

            return;
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

            // Cancel auto-close when opening a context menu
            var icons = $.vakata.context.settings.icons;
            $(document).bind('context_show.vakata', function() {
                wrapper.unbind('mouseleave.hierarchicalopts');
                $.vakata.context.settings.icons = icons;
            });

            // Open/select/deselect nodes
            tree.bind('select_node.jstree', function (event, data) {
                var multiple = opts.multiple,
                    leafonly = opts.leafonly,
                    node = data.node,
                    inst = jQuery.jstree.reference(tree);
                if (!multiple) {
                    var nodeID = $(node).attr("id");
                    $(inst.get_checked(true)).each(function () {
                        if (nodeID != this.id) {
                            if (!leafonly || inst.is_leaf(this)) {
                                inst.uncheck_node(this);
                            }
                        }
                    });
                }
                // Technically correct, but confusing UX (better to allow
                // selection of parent nodes in spite of leafonly, and
                // reduce to leaf nodes only internally):
                //if (leafonly && !inst.is_leaf(node)) {
                //   inst.deselect_node(node);
                //   return false;
                //}
                self._updateAndClose();
            }).bind('deselect_node.jstree', function (event, data) {
                self._updateSelectedNodes();
            }).bind("open_node.jstree", function (event, data) {
                var instance = data.instance,
                    node = data.node;
                var parent = instance.get_parent(node);
                if(parent.length) {
                    instance.open_node(parent, false, true);
                }
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

            // Bulk selection/de-selection
            wrapper.find('.s3-hierarchy-select-all')
                   .bind('click' + ns, function(e) {
                e.preventDefault();
                tree.jstree('select_all');
                self._updateSelectedNodes();
            });
            wrapper.find('.s3-hierarchy-deselect-all')
                   .bind('click' + ns, function(e) {
                e.preventDefault();
                tree.jstree('deselect_all');
                self._updateSelectedNodes();
            });
            wrapper.find('.s3-hierarchy-header')
                   .bind('click' + ns, function(e) {
                e.preventDefault();
                e.stopPropagation();
            }).bind('mousedown' + ns, function(e) {
                e.preventDefault();
                e.stopPropagation();
            });

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
