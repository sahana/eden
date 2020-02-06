/**
 * jQuery UI Widget to Assign Roles to Users
 *
 * @copyright 2018-2019 (c) Sahana Software Foundation
 * @license MIT
 *
 * requires jQuery 1.9.1+
 * requires jQuery UI 1.10 widget factory
 */
(function($, undefined) {

    "use strict";

    // Default labels
    var labels = {
        rm_Add: 'Add',
        rm_Cancel: 'Cancel',
        rm_ConfirmDeleteAssignment: 'Do you want to remove this assignment?',
        rm_Delete: 'Delete',
        rm_DeletionFailed: 'Deletion Failed',
        rm_ForEntity: 'For Entity',
        rm_Role: 'Role',
        rm_SubmissionFailed: 'Submission Failed',
        rm_User: 'User'
    };

    var roleManagerID = 0;

    /**
     * Role Manager Widget
     */
    $.widget('s3.roleManager', {

        /**
         * Default options
         *
         * @prop {string} mode - what to assign ("roles"|"users")
         * @prop {object} items - the users or roles, an object with the structure:
         *                        {itemID: {l: label,
         *                                  t: (sub)title,
         *                                  a: assignable,     // default true
         *                                  r: removable,      // default true
         *                                  u: unrestrictable  // default false
         *                                  }, ...}
         * @prop {boolean} useRealm - use realms
         * @prop {Array} realmTypes - an array of realm types, structure:
         *                            [[instanceType, label], ...]
         *                            NB: the order of this array determines the order
         *                                of assignments in the table and realms in the
         *                                selector
         * @prop {object} realms - the selectable realms, an object with the structure:
         *                         {entityID: {l: label, t: instanceType}, ...}
         * @prop {string} ajaxURL - the Ajax URL for adding/removing assignments,
         *                          can contain a URL-escaped "[id]" which will be
         *                          replaced with the context role/user ID
         */
        options: {

            mode: 'roles',

            items: {},

            useRealms: false,
            realmTypes: null,
            realms: null,

            ajaxURL: null
        },

        /**
         * Create the widget
         */
        _create: function() {

            this.id = roleManagerID;
            roleManagerID += 1;

            this.eventNamespace = '.roleManager';
        },

        /**
         * Update the widget options
         */
        _init: function() {

            // Translate all labels
            for (var key in labels) {
                labels[key] = i18n[key] || labels[key];
            }

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

            // Remove any existing assignment table and reset DOM pointers
            $('.rm-assign', el).remove();
            this.addRow = null;
            this.addButton = null;
            this.realmSelector = null;
            this.itemSelector = null;

            // Parse the current assignments and create a new assignment table
            this._deserialize();
            el.append(this._assignmentTable());

            this._bindEvents();
        },

        /**
         * Parse input data and store them in this.assignments
         */
        _deserialize: function() {

            var widgetID = $(this.element).attr('id'),
                data = $('#' + widgetID + '-data').val();

            try {
                this.assignments = JSON.parse(data);
            } catch(e) {
                this.assignments = [];
            }

            this.recordID = $('#' + widgetID + '-id').val();
        },

        /**
         * Update data input with current assignments
         */
        _serialize: function() {

            var widgetID = $(this.element).attr('id');

            $('#' + widgetID + '-data').val(JSON.stringify(this.assignments));
        },

        /**
         * Render the assignment table
         *
         * @returns {jQuery} - the table (table)
         */
        _assignmentTable: function() {

            var opts = this.options,
                table = $('<table class="rm-assign">');

            table.append(this._assignmentTableHead())
                 .append(this._assignmentTableBody());

            if (opts.ajaxURL) {
                var items = opts.items,
                    assignable = false;
                for (var key in items) {
                    if (items[key].a !== false) {
                        assignable = true;
                        break;
                    }
                }
                if (assignable) {
                    table.append(this._assignmentTableFooter());
                }
            }

            return table;
        },

        /**
         * Render the assignment table head
         *
         * @returns {jQuery} - the table head (thead)
         */
        _assignmentTableHead: function() {

            var opts = this.options,
                thead = $('<thead>'),
                columnLabels = $('<tr>').appendTo(thead),
                targetLabel;

            // The label for the assignable items
            if (opts.mode == 'users') {
                targetLabel = labels.rm_User;
            } else {
                targetLabel = labels.rm_Role;
            }
            $('<th>').text(targetLabel).appendTo(columnLabels);

            // The realm column
            if (opts.useRealms) {
                $('<th>').text(labels.rm_ForEntity).appendTo(columnLabels);

            }

            // The action column (no label)
            $('<th>').appendTo(columnLabels);

            return thead;
        },

        /**
         * Render the assignment table body
         *
         * @returns {jQuery} - the table body (tbody)
         */
        _assignmentTableBody: function() {

            var tbody = $('<tbody>'),
                assignments = this.assignments,
                self = this;

            if (!assignments.length) {
                // Need at least an empty row for proper styling
                tbody.append('<tr>');
            }

            // Sort the assignments, then render a row for each
            assignments.sort(function(a, b) {
                return self._compareAssignments(a, b);
            }).forEach(function(assignment) {
                tbody.append(self._assignmentTableRow(assignment));
            });

            return tbody;
        },

        /**
         * Render a table row for an existing assignment
         *
         * @param {Array} assignment - the assignment [itemID, realmID]
         *
         * @returns {jQuery} - the table row (tr)
         */
        _assignmentTableRow: function(assignment) {

            var row = $('<tr class="rm-assignment">').data('assignment', assignment),
                opts = this.options,
                item = opts.items[assignment[0]];

            // Item name
            var nameCol = $('<td>').appendTo(row);
            $('<span class="rm-item-name">').text(item.l).appendTo(nameCol);
            if (item.t) {
                $('<span class="rm-item-title">').text(item.t).appendTo(nameCol);
            }

            // Realm column
            if (opts.useRealms) {
                var realm = !item.u && opts.realms[assignment[1]].l || '';
                $('<td>').text(realm).appendTo(row);
            }

            // Action column
            var actions = $('<td>');
            if (item.r !== false && opts.ajaxURL) {
                var deleteButton = $('<span class="rm-delete-assignment delete-btn-ajax">');
                actions.append(deleteButton.text(labels.rm_Delete));
            }

            return row.append(actions);
        },

        /**
         * Render the assignment table footer
         *
         * @returns {jQuery} - the table footer (tfoot)
         */
        _assignmentTableFooter: function() {

            var tfoot = $('<tfoot>'),
                addRow = $('<tr>').appendTo(tfoot);

            // User/Role selector
            $('<td>').append(this._itemSelector()).appendTo(addRow);

            // Realm selector (if using realms)
            if (this.options.useRealms) {
                $('<td>').append(this._realmSelector()).appendTo(addRow);
            }

            // Add + Cancel buttons
            var addButton = $('<a class="rm-submit-add action-btn">').text(labels.rm_Add),
                cancel = $('<span class="rm-cancel-add action-lnk">').text(labels.rm_Cancel);

            // Disable Add button initially
            // - explicitly set attribute for CSS
            addButton.prop('disabled', true)
                     .attr('disabled', 'disabled');

            // Complete the row with the action column
            $('<td class="rm-row-actions">').append(addButton)
                                            .append(cancel)
                                            .appendTo(addRow);
            this.addRow = addRow;

            return tfoot;
        },

        /**
         * Render the item selector (to select roles/users)
         *
         * @returns {jQuery} - the item selector (select)
         */
        _itemSelector: function() {

            var selector = $('<select class="rm-item-select">'),
                opts = this.options,
                items = opts.items,
                itemList = [];

            // Empty option
            $('<option value="">').prop('selected', true)
                                  .prop('disabled', true)
                                  .hide()
                                  .appendTo(selector);

            // Selectable items
            var item,
                label;
            for (var key in items) {
                item = items[key];
                if (item.a !== false) {
                    label = item.l;
                    if (item.t) {
                        label += ' (' + item.t + ')';
                    }
                    itemList.push([key, label]);
                }
            }
            itemList.sort(function(a, b) {
                return a[1] !== b[1] && (a[1] > b[1] && 1 || -1) || 0;
            }).forEach(function(o) {
                $('<option>').attr('value', o[0]).text(o[1]).appendTo(selector);
            });

            this.itemSelector = selector;
            return selector;
        },

        /**
         * Render the realm selector
         *
         * @returns {jQuery} - the realm selector (select)
         */
        _realmSelector: function() {

            var selector = $('<select class="rm-realm-select">'),
                opts = this.options,
                realms = opts.realms,
                self = this;

            // Sort realm entities
            var entities = Object.keys(realms).sort(function(a, b) {
                return self._compareRealms(a, b);
            });

            // Group realm entities by type
            var realmOptions = {};
            entities.forEach(function(entityID) {
                var entity = realms[entityID],
                    entityType = entity.t,
                    entityOpt = [entityID, entity.l],
                    group = realmOptions[entityType];

                if (group === undefined) {
                    realmOptions[entityType] = [entityOpt];
                } else {
                    group.push(entityOpt);
                }
            });

            // Empty option
            $('<option value="">').prop('selected', true)
                                  .prop('disabled', true)
                                  .hide()
                                  .appendTo(selector);

            // Selectable options
            opts.realmTypes.forEach(function(realmType) {
                var entityOpts = realmOptions[realmType[0]];
                if (entityOpts) {
                    var optGroup = $('<optgroup>').attr('label', realmType[1])
                                                  .appendTo(selector);
                    entityOpts.forEach(function(entity) {
                        $('<option>').attr('value', entity[0])
                                     .text(entity[1])
                                     .appendTo(optGroup);
                    });
                }
            });

            this.realmSelector = selector;
            this._resetRealmSelector();
            return selector.prop('disabled', true).css({visibility: 'hidden'});
        },

        /**
         * Enable or disable the add-button
         *
         * @param {boolean} on - true to enable
         */
        _toggleAdd: function(on) {

            var addButton = $('.rm-submit-add', this.addRow);
            if (addButton.length) {
                if (on) {
                    addButton.prop('disabled', false)
                             .removeAttr('disabled');
                } else {
                    addButton.prop('disabled', true)
                             .attr('disabled', 'disabled');
                }
            }
        },

        /**
         * Reset the add-row
         */
        _resetAddRow: function() {

            var addRow = this.addRow,
                itemSelector = $('.rm-item-select', addRow);

            if (itemSelector.length) {
                itemSelector.val('').change();
            }
            this._checkNewAssignment();
        },

        /**
         * Reset the realm selector:
         */
        _resetRealmSelector: function() {

            var realmSelector = this.realmSelector;
            if (realmSelector) {
                // Select the 'null' option if present, else empty
                if ($('option[value="null"]', realmSelector).length) {
                    realmSelector.val('null');
                } else {
                    realmSelector.val('');
                }
            }
        },

        /**
         * Actions when a role/user is selected
         */
        _optionSelected: function() {

            var opts = this.options,
                itemSelector = this.itemSelector,
                realmSelector = this.realmSelector;

            if (itemSelector === undefined) {
                return;
            }

            var selectedOpt = itemSelector.val();
            if (selectedOpt) {
                // Get the selected item
                var item = opts.items[selectedOpt];
                if (!item) {
                    return;
                }
                // Update realm selector status
                if (realmSelector) {
                    if (item.u) {
                        // Unrestrictable item => hide realm selector
                        this._resetRealmSelector();
                        realmSelector.prop('disabled', true)
                                     .css({visibility: 'hidden'});
                    } else {
                        // Show realm selector
                        realmSelector.prop('disabled', false)
                                     .css({visibility: 'visible'});
                    }
                }

                if (this._checkNewAssignment() === false) {
                    // Duplicate
                    this._toggleAdd(false);
                } else {
                    // Enable the add-button
                    this._toggleAdd(true);
                }

            } else {
                // Hide the realmSelector, if any
                if (realmSelector) {
                    this._resetRealmSelector();
                    realmSelector.prop('disabled', true)
                                 .css({visibility: 'hidden'});
                }
                // Disable the add button
                this._toggleAdd(false);
            }
        },

        /**
         * Actions when a realm gets selected
         */
        _realmSelected: function() {

            // Check new assignment
            if (this._checkNewAssignment() === false) {
                // Duplicate => disable add
                this._toggleAdd(false);
            } else {
                // Enable add
                this._toggleAdd(true);
            }
        },

        /**
         * Read the new assignment from the add-row
         *
         * @returns {Array} - the new assignment [itemID, realmID]
         */
        _getNewAssignment: function() {

            var itemSelector = this.itemSelector;

            if (itemSelector) {
                var realm = null,
                    selectedOpt = itemSelector.val();
                if (!selectedOpt || isNaN(selectedOpt - 0)) {
                    return;
                }
                if (this.options.useRealms) {
                    realm = this.realmSelector.val();
                    if (realm !== null) {
                        realm -= 0;
                        if (isNaN(realm)) {
                            realm = null;
                        }
                    }
                }
                return [selectedOpt - 0, realm];
            }
        },

        /**
         * Checks whether the new assignment is a duplicate of an
         * existing assignment; toggles 'rm-duplicate' CSS class
         * for duplicate rows
         *
         * @returns {mixed} - the new assignment {2-tuple} if valid and
         *                    not a duplicate
         *                  - false if duplicate
         *                  - undefined if invalid or no input
         */
        _checkNewAssignment: function() {

            var assignment = this._getNewAssignment(),
                rows = $('.rm-assignment', $(this.element)).removeClass('rm-duplicate');

            if (assignment) {
                for (var i = rows.length; i--;) {
                    var otherRow = $(rows[i]),
                        otherAss = otherRow.data('assignment');
                    if (assignment[0] === otherAss[0] && assignment[1] === otherAss[1]) {
                        otherRow.addClass('rm-duplicate');
                        return false;
                    }
                }
                return assignment;
            }
        },

        /**
         * Add a new role assignment (Ajax)
         */
        _addAssignment: function() {

            var url = this.options.ajaxURL,
                assignment = this._checkNewAssignment();
            if (!url || !assignment) {
                return;
            }

            // Show throbber, hide delete-button
            var addRow = this.addRow,
                addBtn = $('.rm-submit-add', addRow).hide(),
                cancel = $('.rm-cancel-add', addRow).hide(),
                throbber = $('<div class="inline-throbber">').insertBefore(addBtn),
                self = this;

            $.ajaxS3({
                type: 'POST',
                url: url.replace(/%5Bid%5D/g, this.recordID),
                data: JSON.stringify({add: [assignment]}),
                dataType: 'json',
                retryLimit: 0,
                contentType: 'application/json; charset=utf-8',
                success: function() {
                    // Add the new assignment to this.assignments
                    self.assignments.push(assignment);
                    self._serialize();

                    // Add a new table row for this assignment
                    var rows = $('.rm-assignment', $(self.element)),
                        newRow = self._assignmentTableRow(assignment).hide();
                    for (var i = rows.length; i--; ) {
                        var otherRow = $(rows[i]),
                            otherAss = otherRow.data('assignment');
                        if (self._compareAssignments(otherAss, assignment) == -1) {
                            newRow.insertAfter(otherRow).fadeIn();
                            newRow = null;
                            break;
                        }
                    }
                    if (newRow) {
                        // Reached top of list
                        $('tbody', addRow.closest('.rm-assign')).prepend(newRow);
                        newRow.fadeIn();
                    }

                    // Clean up UI elements
                    throbber.remove();
                    addBtn.show();
                    cancel.show();
                    self._resetAddRow();
                },
                error: function() {
                    // Show an error message in place of the throbber
                    var msg = $('<span class="rm-error">').insertBefore(throbber.hide());
                    msg.text(labels.rm_SubmissionFailed);
                    throbber.remove();

                    // Fade out the message and restore the buttons
                    window.setTimeout(function() {
                        msg.fadeOut(function() {
                            addBtn.show();
                            cancel.show();
                        });
                    }, 1000);
                }
            });
        },

        /**
         * Delete an assignment (Ajax)
         */
        _deleteAssignment: function(row) {

            var opts = this.options,
                url = opts.ajaxURL,
                assignment = row.data('assignment');
            if (!url || !assignment) {
                return;
            }

            // Ask user confirmation
            var question = labels.rm_ConfirmDeleteAssignment,
                label = opts.items[assignment[0]].l;
            question = question.replace(/%\((role|user)\)s/g, '"' + label + '"');
            if (!confirm(question)) {
                return;
            }

            // Show throbber, hide delete-button
            var deleteBtn = $('.rm-delete-assignment', row).hide(),
                throbber = $('<div class="inline-throbber">').insertBefore(deleteBtn),
                self = this;

            $.ajaxS3({
                type: 'POST',
                url: url.replace(/%5Bid%5D/g, this.recordID),
                data: JSON.stringify({remove: [assignment]}),
                dataType: 'json',
                retryLimit: 0,
                contentType: 'application/json; charset=utf-8',
                success: function() {
                    // Update self.assignments
                    self.assignments = self.assignments.filter(function(other) {
                        return (other[0] !== assignment[0] || other[1] !== assignment[1]);
                    });
                    self._serialize();

                    // Remove all table rows which match this assignment
                    $('.rm-assignment', $(self.element)).each(function() {
                        var other = $(this).data('assignment');
                        if (other[0] === assignment[0] && other[1] === assignment[1]) {
                            $(this).fadeOut(function() {
                                throbber.remove();
                                $(this).remove();
                                // Update add-button
                                if (self._checkNewAssignment()) {
                                    self._toggleAdd(true);
                                }
                            });
                        }
                    });
                },
                error: function() {
                    // Show an error message in place of the throbber
                    var msg = $('<span class="rm-error">').insertBefore(throbber.hide());
                    msg.text(labels.rm_DeletionFailed);
                    throbber.remove();

                    // Fade out the message and restore the delete button
                    window.setTimeout(function() {
                        msg.fadeOut(function() {
                            deleteBtn.show();
                        });
                    }, 1000);
                }
            });
        },

        /**
         * Compare two assignments (for sorting)
         *
         * @param {Array} a - the first assignment
         * @param {Array} b - the second assignment
         *
         * @returns: 0 if assignments are equal,
         *           negative integer if a comes before b
         *           positive integer if b comes before a
         */
        _compareAssignments: function(a, b) {

            var items = this.options.items,
                aName = items[a[0]].l,
                bName = items[b[0]].l;

            if (aName == bName) {
                // If items are equal => order by realm
                return this._compareRealms(a[1], b[1]);
            } else {
                // Otherwise, order by names
                return aName > bName && 1 || -1;
            }
        },

        /**
         * Compare two realm entities (for sorting)
         *
         * @param {integer|null} a - ID of the first entity
         * @param {integer|null} b - ID of the second entity
         *
         * @returns: 0 if entities are equal,
         *           negative integer if a comes before b
         *           positive integer if b comes before a
         */
        _compareRealms: function(a, b) {

            if (a === b) {
                return 0;
            }

            var realms = this.options.realms,
                aType = realms[a].t,
                bType = realms[b].t,
                realmTypeOrder = this._compareRealmTypes(aType, bType);

            if (!realmTypeOrder) {
                // null (= all entities) comes first
                // 0 (= default realm) comes second
                // sort all other entities by their names
                if (a) {
                    if (b) {
                        var aName = realms[a].l,
                            bName = realms[b].l;
                        return aName > bName && 1 || -1;
                    } else {
                        return -1;
                    }
                } else {
                    return a === null && 1 || (b === null && -1 || 1);
                }
            } else {
                return realmTypeOrder;
            }
        },

        /**
         * Compare two realm entity types (for sorting)
         *
         * @param {string} a - first entity type
         * @param {string} b - second entity type
         *
         * @returns: 0 if types are equal,
         *           negative integer if a comes before b
         *           positive integer if b comes before a
         */
        _compareRealmTypes: function(a, b) {

            if (a === b) {
                return 0;
            } else {
                // Sort according to the given realmTypes order
                var realmTypes = this.options.realmTypes.map(function(t) {
                    return t[0];
                });
                var aIndex = realmTypes.indexOf(a),
                    bIndex = realmTypes.indexOf(b);
                return aIndex - bIndex;
            }
        },

        /**
         * Bind events to generated elements (after refresh)
         */
        _bindEvents: function() {

            var ns = this.eventNamespace,
                self = this;

            if (this.addRow !== undefined) {
                this.addRow
                    .on('change' + ns, '.rm-item-select', function() {
                        self._optionSelected();
                    })
                    .on('change' + ns, '.rm-realm-select', function() {
                        self._realmSelected();
                    })
                    .on('click' + ns, '.rm-cancel-add', function() {
                        self._resetAddRow();
                    })
                    .on('click' + ns, '.rm-submit-add', function() {
                        self._addAssignment();
                    });
            }

            $(this.element)
                .on('click' + ns, '.rm-delete-assignment', function() {
                    self._deleteAssignment($(this).closest('.rm-assignment'));
                });

            return true;
        },

        /**
         * Unbind events (before refresh)
         */
        _unbindEvents: function() {

            var el = $(this.element),
                ns = this.eventNamespace;

            if (this.addRow !== undefined) {
                this.addRow.off(ns);
            }

            el.off(ns);

            return true;
        }
    });
})(jQuery);
