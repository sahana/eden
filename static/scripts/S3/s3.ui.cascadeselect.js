/**
 * jQuery UI Widget for S3CascadeSelectWidget
 *
 * @copyright 2019 (c) Sahana Software Foundation
 * @license MIT
 *
 * requires jQuery 1.9.1+
 * requires jQuery UI 1.10 widget factory
 * requires jQuery UI MultiSelect Widget 1.14 by Eric Hynds
 */
(function($, undefined) {

    "use strict";
    var cascadeSelectID = 0;

    /**
     * cascadeSelect
     */
    $.widget('s3.cascadeSelect', {

        /**
         * Default options
         *
         * @prop {bool} multiple - allow selection of multiple nodes (default: true)
         * @prop {bool} leafonly - return only leaf nodes
         * @prop {bool} cascade - automatically select the entire branch if a
         *                        parent node is selected
         */
        options: {

            multiple: true,
            leafonly: true,
            cascade: true,
        },

        /**
         * Create the widget
         */
        _create: function() {

            this.id = cascadeSelectID;
            cascadeSelectID += 1;

            this.eventNamespace = '.cascadeSelect';
        },

        /**
         * Update the widget options
         */
        _init: function() {

            var el = $(this.element);

            this.hiddenInput = $('.s3-cascade-input', el).first();

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

            var el = $(this.element);

            this._unbindEvents();

            // Initialize the selector array
            var selectors = [];
            $('select.s3-cascade-select', el).each(function() {
                selectors.push($(this).empty().data('available', {}));
            });
            selectors.sort(function(a, b) {
                return a.data('level') - b.data('level');
            });
            this.selectors = selectors;

            // Store the available options in the selectors
            var hierarchy = this._getHierarchy();
            for (var nodeID in hierarchy) {
                this._addAvailableOption(null, 0, nodeID, hierarchy[nodeID]);
            }

            // Render the top-level options (they won't change)
            this._renderOptions(selectors[0], Object.keys(hierarchy), []);

            // Get the selected values and populate the selectors
            var selected = this._deserialize();
            this._updateOptions(selectors[selectors.length - 1], selected);

            // Initialize multiselect
            this._multiSelectInit();

            this._bindEvents();
        },

        /**
         * Get the currently selected values
         *
         * @returns {Array} - the currently selected values
         */
        get: function() {

            return this._deserialize();
        },

        /**
         * Programmatically set the selected value(s)
         *
         * @param {integer|string|Array} value - the selected value(s)
         *
         * @returns {Widget} - the instance, for chaining
         */
        set: function(value) {

            this.reset();

            if (!value) {
                return;
            }
            if (value.constructor !== Array) {
                value = [value];
            }
            value = value.map(function(v) { return '' + v; });

            var selectors = this.selectors;
            this._updateOptions(selectors[selectors.length - 1], value);

            this._serialize();

            return this;
        },

        /**
         * Clear the current selection and reset the widget
         *
         * @returns {Widget} - the instance, for chaining
         */
        reset: function() {

            this.selectors.forEach(function(selector, index) {
                selector.val('');
                if (index > 0) {
                    $('option', selector).remove();
                }
                var multiSelect = selector.multiselect('instance');
                if (multiSelect) {
                    multiSelect.refresh();
                }
            });

            this._serialize();
            this._toggleSelectors();

            return this;
        },

        /**
         * Read the currently selected values from the hidden input
         *
         * @returns {Array} - the currently selected values (node IDs)
         */
        _deserialize: function() {

            var values = JSON.parse(this.hiddenInput.val());
            if (values) {
                return values.map(function(v) { return '' + v; });
            } else {
                return [];
            }
        },

        /**
         * Get the currently selected values from the selectors and write
         * them into the hidden input field (as JSON Array)
         */
        _serialize: function() {

            var opts = this.options,
                selection = [],
                selectors = this.selectors;

            for (var i = selectors.length; i--;) {

                var selector = selectors[i],
                    multiple = selector.prop('multiple'),
                    available = selector.data('available'),
                    selected = this._getSelected(selector);

                for (var j = 0, len = selected.length; j < len; j++) {

                    var value = selected[j],
                        node = available[value];
                    if (!node || opts.leafonly && node[3]) {
                        continue;
                    }
                    if (selection.indexOf(value) == -1) {
                        selection.push(value);
                    }
                    if (selection.length && !multiple) {
                        break;
                    }
                }
                if (selection.length && !multiple) {
                    break;
                }
            }

            // Update the hidden input
            this.hiddenInput.val(JSON.stringify(selection))
                            .trigger('select.s3hierarchy');
        },

        /**
         * Initialize multiselect widgets for multiple-selectors,
         * or refresh them if instances already exist
         */
        _multiSelectInit: function() {

            this.selectors.forEach(function(selector) {

                if (selector.multiselect('instance')) {
                    selector.multiselect('refresh');
                } else {
                    if (selector.prop('multiple')) {
                        selector.multiselect({});
                    }
                }
            });
        },

        /**
         * Parse the hierarchy JSON data from the corresponding
         * hidden input (.s3-cascade)
         *
         * @returns {object} - the hierarchy data
         */
        _getHierarchy: function() {

            var el = $(this).element,
                hierarchy = this.hierarchy;

            if (hierarchy === undefined) {
                var dataInput = $('.s3-cascade', el);
                this.hierarchy = hierarchy = JSON.parse(dataInput.val());
            }
            return hierarchy;
        },

        /**
         * Update options after a selection change; double recursion,
         * first upwards to collect selected options, then downwards
         * to roll out child options
         *
         * @param {jQuery} selector: the selector that has changed
         * @param {Array} selected: the selected options
         * @param {Array} propagate: node IDs of the child options to roll
         *                           out after parent selection
         */
        _updateOptions: function(selector, selected, propagate) {

            var level = selector.data('level'),
                available = selector.data('available'),
                subNodes = [];

            // Retain previously selected nodes
            selected = selected.slice(0);
            this._getSelected(selector).forEach(function(nodeID) {
                if (selected.indexOf(nodeID) == -1 && (!propagate || propagate.indexOf(nodeID) != -1)) {
                    selected.push(nodeID);
                }
            });

            if (level === 0) {
                // Update the selection at the top level
                this._setSelected(selector, selected);

            } else if (propagate) {

                // Roll out the child options of the selected options at the
                // parent level (=propagate)
                this._renderOptions(selector, propagate, selected);

            } else {

                // Add the parents of the selected nodes to the selection
                var selection = selected.slice(0);
                selected.forEach(function(nodeID) {
                    var node = available[nodeID];
                    if (node !== undefined) {
                        var parentID = node[0];
                        if (selection.indexOf(parentID) == -1) {
                            selection.push(node[0]);
                        }
                    }
                });

                // Update selected options in the previous level
                this._updateOptions(this.selectors[level-1], selection);
            }

            if (level === 0 || propagate) {

                var nextLevel = this.selectors[level + 1];
                if (nextLevel !== undefined) {

                    // Find the children of the selected options in the current level
                    selected.forEach(function(nodeID) {
                        var node = available[nodeID];
                        if (node !== undefined) {
                            subNodes = subNodes.concat(Object.keys(node[3]));
                        }
                    });

                    // Roll out the child options at the next level
                    this._updateOptions(nextLevel, selected, subNodes);
                } else {
                    this._toggleSelectors();
                }
            }
        },

        /**
         * Roll out options for a selector
         *
         * @param {jQuery} selector - the selector
         * @param {Array} options - the options to roll out
         * @param {Array} selected - the selected options
         */
        _renderOptions: function(selector, options, selected) {

            var opts = this.options;

            // In single-select cascade mode, automatically select
            // single child options
            if (!opts.multiple && opts.cascade && options.length == 1) {
                var singleOpt = options[0];
                if (selected.indexOf(singleOpt) == -1) {
                    selected.push(singleOpt);
                }
            }

            var available = selector.data('available');

            selector.empty();

            var items = [];
            options.forEach(function(nodeID) {
                var node = available[nodeID];
                if (node) {
                    items.push([nodeID, node[1]]);
                }
            });

            // Sort alphabetically according to client locale
            items.sort(function(a, b) {
                return a[1].localeCompare(b[1]);
            });
            items.forEach(function(item) {
                $('<option>').val(item[0]).text(item[1]).appendTo(selector);
            });

            this._setSelected(selector, selected);
        },

        /**
         * Get the currently selected options of a selector
         *
         * @param {jQuery} selector - the selector
         *
         * @returns {Array} - the selected options
         */
        _getSelected: function(selector) {

            var value = $(selector).val();
            if (!value) {
                return [];
            }
            if (value.constructor === Array) {
                return value.map(function(v) { return '' + v; });
            } else {
                return ['' + value];
            }
        },

        /**
         * Programmatically select available options in a selector
         *
         * @param {jQuery} selector - the selector
         * @param {Array} values - the options; unavailable options
         *                         are ignored
         */
        _setSelected: function(selector, values) {

            var available = selector.data('available'),
                multiSelect = selector.multiselect('instance');

            var selected = values.filter(function(value) {
                return available['' + value] !== undefined;
            });

            if (selector.prop('multiple')) {
                selector.val(selected);
            } else {
                selector.val(selected[0]);
            }
            // If selector is multi-select, refresh it
            if (multiSelect) {
                multiSelect.refresh();
            }
        },

        /**
         * Store an available option in the corresponding selector
         *
         * @param {integer|string} parent - the parent node ID
         * @param {integer} level - the hierarchy level of the node
         * @param {integer|string} nodeID - the node ID
         * @param {Array} node - the node data [label, category, {children}]
         */
        _addAvailableOption: function(parent, level, nodeID, node) {

            var selector = this.selectors[level];
            if (!selector) {
                return;
            }

            var available = selector.data('available');
            if (available === undefined || available === null) {
                available = {};
            }
            available['' + nodeID] = ['' + parent].concat(node);
            selector.data('available', available);

            var subNodes = node[2];
            if (subNodes && subNodes !== true) {
                for (var subNodeID in subNodes) {
                    this._addAvailableOption(nodeID, level + 1, subNodeID, subNodes[subNodeID]);
                }
            }
        },

        /**
         * Enable/disable selectors depending on whether they have options
         */
        _toggleSelectors: function() {

            this.selectors.forEach(function(selector) {
                var multiSelect = selector.multiselect('instance');
                if ($('option', selector).length) {
                    selector.prop('disabled', false);
                    if (multiSelect) {
                        multiSelect.enable();
                    }
                } else {
                    selector.prop('disabled', true);
                    if (multiSelect) {
                        multiSelect.disable();
                    }
                }
            });
        },

        /**
         * Get all currently hidden descendants of selected nodes
         *
         * @param {jQuery} selector - the selector
         * @param {Array} values - the currently selected values
         *
         * @returns {Array} - the node IDs of all descendants of values that
         *                    are not currently rolled out (and thus, not selected)
         */
        _hiddenBranches: function(selector, values) {

            var hidden = [],
                level = selector.data('level'),
                nextLevel = this.selectors[level + 1];

            if (nextLevel) {

                var available = selector.data('available'),
                    branches = {};

                // Get all children of values
                values.forEach(function(value) {
                    var node = available[value];
                    if (node) {
                        var subNodes = node[3];
                        if (subNodes && subNodes !== true) {
                            for (var nodeID in subNodes) {
                                branches['' + nodeID] = true;
                            }
                        }
                    }
                });

                // Check which of the children are not selectable
                // at the moment
                $('option', nextLevel).each(function() {
                    branches[$(this).val()] = false;
                });

                // Collect the hidden node IDs, recurse into next level
                hidden = Object.keys(branches).filter(function(nodeID) {
                    return branches[nodeID];
                });
                hidden = hidden.concat(this._hiddenBranches(nextLevel, hidden));
            }

            return hidden;
        },

        /**
         * Bind events to generated elements (after refresh)
         */
        _bindEvents: function() {

            var el = $(this.element),
                ns = this.eventNamespace,
                opts = this.options,
                self = this;

            $('select.s3-cascade-select', el).on('change' + ns, function() {
                var selector = $(this),
                    selected = self._getSelected(selector);

                // If in cascade-mode with multi-select: auto-select all
                // descendants which are currently invisible but about to
                // be rolled out due to the selection change (=auto-select
                // the entire branch when a parent has been newly selected)
                if (opts.multiple && opts.cascade) {
                    var hidden = self._hiddenBranches(selector, selected);
                    hidden.forEach(function(nodeID) {
                        if (selected.indexOf(nodeID) == -1) {
                            selected.push(nodeID);
                        }
                    });
                }

                self._updateOptions(selector, selected);
                self._serialize();
            });

            return true;
        },

        /**
         * Unbind events (before refresh)
         */
        _unbindEvents: function() {

            var el = $(this.element),
                ns = this.eventNamespace;

            $('select.s3-cascade-select', el).off(ns);

            return true;
        }
    });
})(jQuery);
