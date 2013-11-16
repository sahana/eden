/**
 * jQuery UI HierarchicalOpts Widget for S3HierarchyFilter
 * 
 * @copyright: 2013 (c) Sahana Software Foundation
 * @license: MIT
 *
 * requires: jQuery 1.9.1+
 * requires: jQuery UI 1.10 widget factory
 * requires: jQuery JStree 1.0
 * 
 * status: experimental
 * 
 */

(function($, undefined) {

    var hierarchicaloptsID = 0;

    $.widget('s3.hierarchicalopts', {

        // Default options
        options: {
            selected: null
        },

        _create: function() {
            // Create the widget
            var el = $(this.element);

            this.treeID = el.attr('id') + '-tree';
            
            this.input = el.find('.s3-hierarchy-input').first();
            this.tree = el.find('.s3-hierarchy-tree').first();

            this.id = hierarchicaloptsID;
            hierarchicaloptsID += 1;
        },

        _init: function() {
            // Update widget options
            this.refresh();
        },

        _destroy: function() {
            // @todo: Remove generated elements & reset other changes
        },

        refresh: function() {
            // Re-draw contents
            this._unbindEvents();

            var opts = this.options;
            
            var selected = [], s = opts.selected;
            if (s) {
                var treeID = this.treeID;
                for (var i=0, len=s.length; i<len; i++) {
                    selected.push(treeID + '-' + s[i]);
                }
            }

            $.jstree._themes = S3.Ap.concat('/static/styles/jstree/');
            if ($('body').css('direction') == 'ltr') {
                rtl = false;
            } else {
                rtl = true;
            }
            if (rtl) {
                theme = 'default-rtl';
            } else {
                theme = 'default';
            }
            this.tree.jstree({
                'core': {
                    animation: 100,
                    rtl: rtl
                },
                'themes': {
                    'theme' : theme,
                    'icons': false
                },
                'ui': {
                    'initially_select' : selected
                },
                'checkbox': {
                    'override_ui': true
                },
                'plugins': ['themes', 'html_data', 'ui', 'checkbox', 'sort']
            });

            this._bindEvents();
        },

        _updateSelectedNodes: function(data) {
            // Get all selected nodes and store the result in the hidden input

            var old_selected = this.input.val(),
                new_selected = [];

            if (old_selected) {
                old_selected = JSON.parse(old_selected);
            } else {
                old_selected = [];
            }

            var nodes = this.tree.jstree('get_checked', null, true)
                
            $(nodes).each(function() {
                var id = $(this).attr('id');
                if (id) {
                    id = parseInt(id.split('-').pop());
                    if (id) {
                        new_selected.push(id);
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
            if (changed) {
                $(this.element).trigger('select.s3hierarchy');
            }
            return true;
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

        _bindEvents: function() {
            // Bind events to generated elements (after refresh)

            var tree = $(this.tree);

            var hw = this;
            tree.bind('check_node.jstree', function (event, data) {
                hw._updateSelectedNodes();
            }).bind('uncheck_node.jstree', function (event, data) {
                hw._updateSelectedNodes();
            });
            
            return true;
        },
        
        _unbindEvents: function() {
            // Unbind events (before refresh)

            var tree = $(this.tree);

            tree.unbind('check_node.jstree')
                .unbind('uncheck_node.jstree');

            return true;
        }
    });
})(jQuery);
