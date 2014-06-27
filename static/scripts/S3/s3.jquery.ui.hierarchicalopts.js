/**
 * jQuery UI HierarchicalOpts Widget for S3HierarchyFilter
 * 
 * @copyright: 2013-14 (c) Sahana Software Foundation
 * @license: MIT
 *
 * requires: jQuery 1.9.1+
 * requires: jQuery UI 1.10 widget factory
 * requires: jQuery JStree 1.0
 * 
 * status: experimental
 * @todo: Ajax-refresh, dynamic insertion of nodes via add-popups
 * 
 */

(function($, undefined) {

    var hierarchicaloptsID = 0;

    $.widget('s3.hierarchicalopts', {

        // Default options
        options: {
            selected: null,
            noneSelectedText: 'Select',
            selectedText: 'selected',
            noOptionsText: 'No options available',
            multiple: true,
            leafonly: true,
            themesFolder: 'static/styles/jstree',
            theme: 'default',
            htmlTitles: true
        },

        _create: function() {
            // Create the widget
            var el = $(this.element),
                opts = this.options;

            this.id = hierarchicaloptsID;
            hierarchicaloptsID += 1;

            this._namespace = '.hierarchicalopts' + hierarchicaloptsID;
            
            this.treeID = el.attr('id') + '-tree';

            // The hidden input field
            this.input = el.find('.s3-hierarchy-input').first();

            // The button
            this.button = $('<button type="button" class="s3-hierarchy-button ui-multiselect ui-widget ui-state-default ui-corner-all"><span class="ui-icon ui-icon-triangle-1-s"></span></button>');
            this.buttonText = $('<span>' + opts.noneSelectedText + '</span>').appendTo(this.button);

            // No-options section
            this.noopts = $('<span class="no-options-available">' + opts.noOptionsText + '</span>').hide();

            // The tree
            this.tree = el.find('.s3-hierarchy-tree')
                          .first()
                          .hide()
                          .before(this.noopts)
                          .before(this.button)
                          .detach()
                          .appendTo('body');
            this._isOpen = false;
        },

        _init: function() {
            // Update widget options
            this.refresh();
        },

        _destroy: function() {
            // Remove generated elements & reset other changes
            $.Widget.prototype.destroy.call(this);
            
            this._unbindEvents();
            $(this.button).remove();
            $(this.noopts).remove();
            $(this.tree).detach()
                        .appendTo(this.element)
                        .show();
        },

        refresh: function() {
            // Re-draw contents
            this._unbindEvents();

            var opts = this.options;

            if (!this.tree.find('li').length) {
                this.button.hide();
                this.noopts.show();
                return;
            } else {
                this.noopts.hide();
                this.button.show();
            }
            
            var selected = [],
                s = opts.selected;
            if (s) {
                var treeID = this.treeID;
                for (var i=0, len=s.length; i<len; i++) {
                    selected.push(treeID + '-' + s[i]);
                }
                this._updateButtonText(selected);
            }

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

            var multiple = opts.multiple,
                leafonly = opts.leafonly;

            this.tree.jstree({
                'core': {
                    animation: 100,
                    rtl: rtl,
                    html_titles: opts.htmlTitles
                },
                'themes': {
                    'theme': theme,
                    'icons': false
                },
                'ui': {
                    'select_limit': multiple ? -1 : 1,
                    'select_multiple_modifier': 'on',
                    'initially_select' : selected
                },
                'checkbox': {
                    'override_ui': true,
                    'two_state': !leafonly
                },
                'plugins': ['themes', 'html_data', 'ui', 'sort', 'checkbox']
            });

            if (!multiple) {
                var tree = this.tree;
                var inst = jQuery.jstree._reference(tree);
                tree.bind('check_node.jstree', function(e, data) {
                    var currentNode = data.rslt.obj.attr("id");
                    inst.get_checked(null, true).each(function () {
                        if (currentNode != this.id){
                            if (!leafonly || inst.is_leaf('#' + this.id)) {
                                inst.uncheck_node('#' + this.id);
                            }
                        }
                    });
                });
            }

            this._bindEvents();
        },

        _updateSelectedNodes: function(data) {
            // Get all selected nodes and store the result in the hidden input

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

            var nodes = tree.jstree('get_checked', null, true);
                
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
                $(this.element).trigger('select.s3hierarchy');
            }
            return true;
        },

        _updateButtonText: function(selected_ids) {
            // Update the button text with the number of selected items

            var text = null,
                options = this.options;

            var limit = 1; // @todo: make configurable?

            numSelected = selected_ids ? selected_ids.length : 0;
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

        set: function(values) {
            // Check particular nodes (used by setCurrentFilters)

            this.tree.jstree('uncheck_all');
            if (values) {
                for (var i=0, len=values.length, node_id; i < len; i++) {
                    node = $('#' + this.treeID + '-' + values[i]);
                    this.tree.jstree('check_node', node);
                }
            }
        },

        get: function() {
            // Get all checked nodes (used by getCurrentFilters)

            var value = this.input.val();
            if (value) {
                return JSON.parse(value);
            } else {
                return [];
            }
        },

        reset: function() {
            // Uncheck all nodes (used by clearFilters)

            this.tree.jstree('uncheck_all');
            this._updateSelectedNodes();
            return;
        },

        openMenu: function() {
            // Open the tree

            if (this._isOpen) {
                this.closeMenu();
            }
            
            var button = $(this.button);
            var pos = button.offset();
            
            $(this.tree).css({
                position: 'absolute',
                top: pos.top + button.outerHeight(),
                left: pos.left,
                minWidth: button.outerWidth() - 8,
                'z-index': 999999
            }).show();
            this._isOpen = true;
            button.addClass('ui-state-active');
            $(this).trigger('open');
        },

        closeMenu: function() {
            // Close the tree
            
            $(this.tree).hide();
            this._isOpen = false;
            $(this.button).removeClass('ui-state-active');
            $(this).trigger('close');
        },

        _bindEvents: function() {
            // Bind events to generated elements (after refresh)

            var widget = this,
                tree = $(this.tree),
                button = $(this.button),
                namespace = this._namespace;

            tree.bind('check_node.jstree', function (event, data) {
                widget._updateSelectedNodes();
            }).bind('uncheck_node.jstree', function (event, data) {
                widget._updateSelectedNodes();
            });
            
            button.bind('click' + namespace, function() {
                if (!widget._isOpen) {
                    widget.openMenu();
                } else {
                    widget.closeMenu();
                }
            }).bind('keyup' + namespace, function(event) {
                event.preventDefault();
                switch(event.keyCode) {
                    case 27: // esc
                    case 38: // up
                    case 37: // left
                        widget.closeMenu();
                        break;
                    case 39: // right
                    case 40: // down
                        widget.openMenu();
                        break;
                }
            }).bind('mouseenter' + namespace, function() {
                if (!button.hasClass('ui-state-disabled')) {
                    $(this).addClass('ui-state-hover');
                }
            }).bind('mouseleave' + namespace, function() {
                $(this).removeClass('ui-state-hover');
            }).bind('focus' + namespace, function() {
                if (!button.hasClass('ui-state-disabled')) {
                    $(this).addClass('ui-state-focus');
                }
            }).bind('blur' + namespace, function() {
                $(this).removeClass('ui-state-focus');
            });
            $(document).bind('mousedown' + namespace, function(event) {
                var target = event.target;
                if (!tree.is(target) && !button.is(target) &&
                    tree.has(event.target).length === 0 &&
                    button.has(event.target).length === 0) {
                    widget.closeMenu();
                }
            });
            return true;
        },
        
        _unbindEvents: function() {
            // Unbind events (before refresh)

            var tree = $(this.tree),
                button = $(this.button),
                namespace = this._namespace;

            tree.unbind('check_node.jstree')
                .unbind('uncheck_node.jstree')
                .unbind('loaded.jstree');

            $(this.button).unbind(namespace);
            $(document).unbind(namespace);

            return true;
        }
    });
})(jQuery);
