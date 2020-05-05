/**
 * jQuery UI Widget to edit permissions of a user role
 *
 * @copyright 2018-2020 (c) Sahana Software Foundation
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
        rm_AddRule: 'Add Rule',
        rm_AllEntities: 'All Entities',
        rm_AllRecords: 'All Records',
        rm_AssignedEntities: 'Assigned Entities',
        rm_Cancel: 'Cancel',
        rm_CollapseAll: 'Collapse All',
        rm_ConfirmDeleteRule: 'Do you want to delete this rule?',
        rm_Default: 'default',
        rm_DeleteRule: 'Delete',
        rm_ExpandAll: 'Expand All',
        rm_NoAccess: 'No access',
        rm_NoRestrictions: 'No restrictions',
        rm_Others: 'Others',
        rm_OwnedRecords: 'Owned Records',
        rm_Page: 'Page',
        rm_RestrictedTables: 'Restricted Tables',
        rm_Scope: 'Scope',
        rm_SystemTables: 'System Tables',
        rm_Table: 'Table',
        rm_UnrestrictedTables: 'Unrestricted Tables',
    };

    /**
     * Helper function to compare permission rules
     * => rules are equivalent if they have the same target and scope
     *
     * @param {Array} a - the first rule
     * @param {Array} b - the second rule
     *
     * @returns {boolean} - true if the rules are equivalent, else false
     */
    var equivalent = function(a, b) {

        var check;
        if (a[0] === null || b[0] === null) {
            check = [1, 2, 3];
        } else {
            check = [1, 2, 3, 6];
        }

        for (var i = check.length, idx; i--; ) {
            idx = check[i];
            if (a[idx] !== b[idx]) {
                return false;
            }
        }
        return true;
    };

    /**
     * Helper function to get the target of a permission rule
     * => target = table name, or page as string "controller/function"
     *
     * @param {Array} rule - the permission rule
     *
     * @returns {string} - the rule target, or undefined if the rule
     *                     has no target (i.e. empty rule in add-row)
     */
    var getTarget = function(rule) {

        var target,
            tablename = rule[3];

        if (tablename) {
            if (tablename !== true) {
                target = tablename;
            }
        } else {
            if (rule[2] !== true) {
                target = rule[1] + '/' + (rule[2] || '*');
            }
        }
        return target;
    };

    var permissionEditID = 0;

    /**
     * Permission Editor
     */
    $.widget('s3.permissionEdit', {

        /**
         * Default options
         *
         * @prop {boolean} fRules - use function rules
         * @prop {boolean} tRules - use table rules
         * @prop {boolean} useRealms - use realms
         *
         * @prop {Array} permissions - permission bits to manage, array of objects:
         *                             {l: label,
         *                              b: permission bitmap,
         *                              o: applicable for owned records
         *                              }
         *
         * @prop {object} modules - list of active modules
         * @prop {object} models - active data models and their restrictions, format:
         *                         {prefix: {tablename: numberOfRestrictions}}
         * @prop {object} defaultPermissions: default permissions (i.e. those granted by
         *                                    roles the user has by default), format:
         *                                    {tablename: [uACL, oACL]}
         *
         * @prop {object} icons - CSS classes for icons
         */
        options: {

            fRules: false,
            tRules: false,
            useRealms: false,

            permissions: [
                {l: "CREATE", b: 0x0001, o: false},
                {l: "READ",   b: 0x0002, o: true },
                {l: "UPDATE", b: 0x0004, o: true },
                {l: "DELETE", b: 0x0008, o: true }
            ],
            modules: {},
            models: {},
            defaultPermissions: {},

            icons: {
                expanded: 'fa fa-caret-down',
                collapsed: 'fa fa-caret-right'
            }
        },

        /**
         * Create the widget
         */
        _create: function() {

            //var el = $(this.element);

            this.id = permissionEditID;
            permissionEditID += 1;

            this.eventNamespace = '.permissionEdit';
        },

        /**
         * Update the widget options
         */
        _init: function() {

            var el = $(this.element),
                widgetID = el.attr('id');

            this.input = $('#' + widgetID + '-input');

            if (this.options.useRealms) {
                this.tableWidth = 5;
            } else {
                this.tableWidth = 4;
            }

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

            var el = $(this.element),
                opts = this.options;

            this._unbindEvents();
            this._deserialize();

            var rules = this._ruleSets(),
                container = $('.rm-rules', el).first();

            // Render page rules
            var self = this,
                ruleSet = rules.pages,
                tab = $('.rm-page-rules', el);

            this._renderExpandCollapseAll().appendTo(tab);

            Object.keys(opts.modules).sort().forEach(function(prefix) {
                if (opts.modules[prefix][1]) {
                    self._ruleTable('p', prefix, ruleSet[prefix]).appendTo(tab);
                }
            });
            if (ruleSet._other.length) {
                this._ruleTable('p', '_other', ruleSet._other).appendTo(tab);
            }

            // Render table rules
            if (opts.tRules) {

                ruleSet = rules.tables;
                tab = $('.rm-table-rules', el);

                this._renderExpandCollapseAll().appendTo(tab);

                Object.keys(opts.models).sort().forEach(function(prefix) {
                    if (prefix != '_system') {
                        self._ruleTable('t', prefix, ruleSet[prefix]).appendTo(tab);
                    }
                });
                this._ruleTable('t', '_system', ruleSet._system).appendTo(tab);

                if (ruleSet._other.length) {
                    this._ruleTable('t', '_other', ruleSet._other).appendTo(tab);
                }
            }

            // Instantiate tabs
            container.tabs().removeClass('hide').show();

            this._bindEvents();
        },

        /**
         * Parse the JSON from the main input, and populate this.rules
         */
        _deserialize: function() {

            try {
                this.rules = JSON.parse(this.input.val());
            } catch(e) {
                this.rules = [];
                this._serialize();
            }
        },

        /**
         * Serialize this.rules as JSON, and write it to the main input
         */
        _serialize: function() {

            // Disregard default rules and newly-added-then-deleted rules
            var rules = this.rules.filter(function(rule) {
                return rule[0] !== null && (rule[0] !== 0 || !rule[7]);
            });

            this.input.val(JSON.stringify(rules)).change();
        },

        /**
         * Sort the rules by rule type and module
         *
         * @returns {object} - an object like {pages:  {"prefix": [rules], ...},
         *                                     tables: {"prefix": [rules], ...}
         *                                     }
         */
        _ruleSets: function() {

            var rules = this.rules,
                pRules = {_other: []},
                tRules = {_other: []},
                opts = this.options;

            rules.forEach(function(rule) {

                var ruleSet,
                    module,
                    prefixes,
                    tablename = rule[3];

                if (tablename) {
                    // This is a table rule
                    ruleSet = tRules;
                    prefixes = opts.models;

                    module = tablename.split('_')[0];

                } else {
                    // This is a page rule
                    ruleSet = pRules;
                    prefixes = opts.modules;

                    var c = rule[1],
                        f = rule[2];
                    if (c == 'default' && (f == 'table' || f == 'tables')) {
                        // Special controllers for dynamic models
                        // (always restricted, even if default is not)
                        module = 'default/dt';
                    } else {
                        module = c;
                    }
                }

                if (prefixes.hasOwnProperty(module)) {
                    if (ruleSet[module] === undefined) {
                        ruleSet[module] = [];
                    }
                } else {
                    // Undefined or inactive module
                    module = '_other';
                }
                ruleSet[module].push(rule);
            });

            return {pages: pRules, tables: tRules};
        },

        /**
         * Render "Expand/Collapse All" actions
         *
         * @returns {jQuery} - the DOM tree for the toggles
         */
        _renderExpandCollapseAll: function() {

            var expand = $('<span class="action-lnk rm-expand-all">'),
                collapse = $('<span class="action-lnk rm-collapse-all">');

            expand.text(labels.rm_ExpandAll);
            collapse.text(labels.rm_CollapseAll);

            return $('<div class="rm-toggle-all">').append(expand).append(collapse);
        },

        /**
         * Render a rule table
         *
         * @param {string} ruleType - 'p'=page rules, 't'= table rules
         * @param {string} prefix - the module prefix
         * @param {Array} rule - the rules in this rule table
         *
         * @returns {jQuery} - the rule table (table)
         */
        _ruleTable: function(ruleType, prefix, rules) {

            if (!rules) {
                rules = [];
            }

            var table = $('<table class="rm-module-rules">').data({module: prefix});

            table.append(this._ruleTableHeader(prefix))
                 .append(this._ruleTableBody(ruleType, prefix, rules))
                 .append(this._ruleTableFooter(ruleType, prefix, rules));

            this._indicateNumRules(table, rules.length);

            return table;
        },

        /**
         * Render the rule table header
         *
         * @param {string} prefix - the module prefix
         *
         * @returns {jQuery} - the table header (thead)
         */
        _ruleTableHeader: function(prefix) {

            // Create the header
            var thead = $('<thead class="rm-module-header">'),
                header = $('<th>').attr('colspan', this.tableWidth);

            // Add expand/collapse icons
            var icons = this.options.icons;
            if (icons) {
                var expanded = $('<i class="' + icons.expanded + '">').hide(),
                    collapsed = $('<i class="' + icons.collapsed + '">');
                $('<div class="rm-module-toggle">').append(expanded)
                                                   .append(collapsed)
                                                   .appendTo(header);
            }

            // Add module name and title
            var module,
                title;
            switch(prefix) {
                case '_system':
                    module = 'SYSTEM';
                    title = labels.rm_SystemTables;
                    break;
                case '_other':
                    module = '*';
                    title = labels.rm_Others;
                    break;
                case 's3dt':
                    module = 'S3DT';
                    title = labels.rm_DynamicTables;
                    break;
                default:
                    if (prefix == 'default/dt') {
                        module = 'DEFAULT';
                    } else {
                        module = prefix.toLocaleUpperCase();
                    }
                    if (this.options.modules.hasOwnProperty(prefix)) {
                        title = this.options.modules[prefix][0];
                    } else {
                        title = '';
                    }
                    break;
            }
            $('<div class="rm-module-prefix">').text(module).appendTo(header);
            $('<div class="rm-module-title">').text(title).appendTo(header);

            // Add div for rule number indicator
            $('<div class="rm-module-numrules">').appendTo(header);

            // Wrap in table row and append to thead
            $('<tr>').append(header).appendTo(thead);

            return thead;
        },

        /**
         * Render the body of a rule table
         *
         * @param {string} ruleType - the rule type ('p'|'t')
         * @param {string} prefix - the module prefix
         * @param {Array} rules - the rules
         *
         * @returns {jQuery} - the table body (tbody)
         */
        _ruleTableBody: function(ruleType, prefix, rules) {

            var opts = this.options,
                tbody = $('<tbody>').hide(),
                hasRules = true,
                targets = rules.map(getTarget),
                targetLabel;

            if (ruleType == 't') {

                // Append default-rules for restricted tables
                var tables = opts.models[prefix];
                if (tables) {
                    for (var tablename in tables) {
                        if (tables[tablename] && targets.indexOf(tablename) == -1) {
                            rules.push([null, null, null, tablename, null, null, null, false]);
                        }
                    }
                }

                // Set the target label
                targetLabel = labels.rm_Table;

                // Show default rules if no rules available
                if (rules.length === 0) {
                    // No restricted tables in this module
                    hasRules = false;
                    tbody.append(this._defaultRule(false));
                }
            } else {
                var dynamicTables = prefix == 'default/dt',
                    page,
                    match,
                    f;

                // Append default-rules for pages where available
                for (var target in opts.defaultPermissions) {
                    if (dynamicTables) {
                        match = target == 'default/tables' || target == 'default/table';
                    } else {
                        match = target.slice(0, prefix.length + 1) == prefix + '/';
                    }
                    if (match && targets.indexOf(target) == -1) {
                        page = target.split('/');
                        f = page[1];
                        if (f == '*') {
                            f = null;
                        } else if (!opts.fRules) {
                            continue;
                        }
                        rules.push([null, page[0], f, null, null, null, null, false]);
                    }
                }

                // Set the target label
                targetLabel = labels.rm_Page;

                // Show default rules if no rules available
                if (rules.length === 0) {
                    // Restricted controller, but no access rules defined
                    hasRules = false;
                    tbody.append(this._defaultRule(true));
                }
            }

            // Render column labels
            var labelRow = $('<tr class="rm-rule-labels">').hide().appendTo(tbody);
            labelRow.append('<th>' + targetLabel + '</th>')
                    .append('<th>' + (labels.rm_AllRecords) + '</th>')
                    .append('<th>' + (labels.rm_OwnedRecords) + '</th>');
            if (opts.useRealms) {
                $('<th>').text(labels.rm_Scope).appendTo(labelRow);
            }
            labelRow.append('<th></th>');

            if (hasRules) {
                // Show the label row
                labelRow.show();

                // Order rules by target name
                rules = rules.sort(function(a, b) {
                    var aStr = a.slice(1, 4).join(' '),
                        bStr = b.slice(1, 4).join(' ');
                    if (aStr === bStr) {
                        return 0;
                    } else {
                        return aStr > bStr && 1 || -1;
                    }
                });

                // Render the rules
                var self = this;
                rules.forEach(function(rule) {
                    self._ruleTableRow(rule).appendTo(tbody);
                });
            }

            return tbody;
        },

        /**
         * Render the footer of a rule table
         *
         * @param {string} ruleType - the rule type ('p'|'t')
         * @param {string} prefix - the module prefix
         * @param {Array} rules - the rules
         *
         * @returns {jQuery} - the table footer (tfoot)
         */
        _ruleTableFooter: function(ruleType, prefix, rules) {

            var tfoot = $('<tfoot>').hide();

            if (prefix != '_other') {

                var addRow = $('<tr class="rm-module-add">'),
                    cell = $('<td>').attr('colspan', this.tableWidth),
                    addRule = $('<span class="action-lnk rm-add-rule">');

                addRule.text(labels.rm_AddRule).appendTo(cell);

                if (ruleType != 't' && !this.options.fRules && rules.length) {
                    addRow.hide();
                }
                addRow.append(cell).appendTo(tfoot);
            }

            return tfoot;
        },

        /**
         * Render an access rule as row in the rule table
         *
         * @param {Array} rule - the rule [id, c, f, t, uACL, oACL, entity, deleted]
         *
         * @returns {jQuery} - the table row (tr)
         */
        _ruleTableRow: function(rule) {

            var row = $('<tr class="rm-rule">').data({rule: rule}),
                opts = this.options,
                target = getTarget(rule);

            if (target) {
                // Add target name
                $('<td class="rm-rule-target">').text(target).appendTo(row);
            } else {
                // Render target selector
                var targetSelector = this._targetSelector(rule);
                $('<td class="rm-rule-target">').append(targetSelector).appendTo(row);
            }

            if (target && rule[0] === null) {
                // Target is restricted but no access rule defined for this role
                // => show default and option to add a rule

                row.addClass('rm-default-permissions');

                // Render the default permissions
                var defaultPermissions = this._defaultPermissions(target);
                if (defaultPermissions.oACL) {
                    $('<td>').text(defaultPermissions.uACL)
                             .appendTo(row);
                    $('<td>').text(defaultPermissions.oACL)
                             .appendTo(row);
                } else {
                    $('<td>').attr('colspan', 2)
                             .text(defaultPermissions.uACL)
                             .appendTo(row);
                }
                if (opts.useRealms) {
                    $('<td>').appendTo(row);
                }

                // Action column with add-rule action
                var addRule = $('<a class="rm-add-rule action-lnk">');
                $('<td>').append(addRule.text(labels.rm_AddRule))
                         .appendTo(row);

            } else {
                // Render permission selectors
                var pSelector = this._permissionSelector(rule);
                row.append(pSelector.uACL)
                   .append(pSelector.oACL);

                // Add scope selector if using realms
                if (opts.useRealms) {
                    $('<td>').append(this._scopeSelector(rule)).appendTo(row);
                }

                // Action column
                if (target) {
                    // Existing rule => show delete option
                    var deleteRule = $('<a class="rm-delete-rule delete-btn-ajax">');
                    $('<td>').append(deleteRule.text(labels.rm_DeleteRule))
                             .appendTo(row);
                } else {
                    // New rule => show confirm/cancel options
                    var submitRule = $('<a class="rm-submit-rule action-btn">'),
                        cancelAdd = $('<span class="rm-cancel-add action-lnk">');
                    $('<td>').append(submitRule.text(labels.rm_Add))
                             .append(cancelAdd.text(labels.rm_Cancel))
                             .appendTo(row);
                }
            }

            return row;
        },

        /**
         * Render a page/table selector for a new rule
         *
         * @param {Array} rule - the new rule
         *
         * @returns {jQuery} - the selector DOM tree
         */
        _targetSelector: function(rule) {

            var opts = this.options,
                wrapper = $('<div>'),
                selector,
                prefix = rule[1];

            var selectOption = function(value, label) {
                if (label === undefined) {
                    label = value;
                }
                return $('<option value="' + value + '">').text(label);
            };

            var emptyOption = function() {
                return $('<option value="">').prop('selected', true)
                                             .prop('disabled', true)
                                             .hide();
            };

            if (rule[3]) {
                // Table selector
                var tables = opts.models[prefix],
                    rGroup = $('<optgroup>').attr('label', labels.rm_RestrictedTables),
                    uGroup = $('<optgroup>').attr('label', labels.rm_UnrestrictedTables),
                    numRestricted = 0,
                    numUnrestricted = 0;

                Object.keys(tables).sort().forEach(function(tableName) {
                    if (tables[tableName]) {
                        numRestricted += 1;
                        rGroup.append(selectOption(tableName));
                    } else {
                        numUnrestricted += 1;
                        uGroup.append(selectOption(tableName));
                    }
                });

                selector = $('<select>').append(emptyOption());
                if (numRestricted) {
                    selector.append(rGroup);
                }
                if (numUnrestricted) {
                    selector.append(uGroup);
                }

            } else {
                // Page selector
                if (prefix == '_other') {
                    // Free input
                    selector = $('<input type="text" size="20">');
                    selector.data('pattern', /^(\w+)(\/(\*|[\w]+))?$/);
                } else {
                    if (prefix == 'default/dt') {
                        // Limited selection
                        selector = $('<select>');
                        selector.append(emptyOption())
                                .append(selectOption('default/table'))
                                .append(selectOption('default/tables'));
                    } else {
                        // Function input
                        wrapper.append('<span>' + prefix + ' / </span>');
                        selector = $('<input type="text" size="10">');
                        selector.data('pattern', /^(\w+|\*)$/);
                    }
                }
            }

            selector.addClass('rm-target-select').appendTo(wrapper);
            return wrapper;
        },

        /**
         * Validate the target input
         *
         * @param {jQuery} input - the input field
         *
         * @returns {boolean} - whether the input is valid
         */
        _validateTarget: function(input) {

            var value = input.val(),
                valid = input.data('pattern');

            valid.lastIndex = 0;
            if (value && valid && !valid.exec(value)) {
                input.addClass('rm-invalid');
                return false;
            } else {
                input.removeClass('rm-invalid');
                return true;
            }
        },

        /**
         * Render default permissions for a target as labels
         *
         * @param {string} target - the target (e.g. table name)
         *
         * @returns {object} - an object {uACL: 'label', oACL: 'label'}
         */
        _defaultPermissions: function(target) {

            var opts = this.options,
                permissions = opts.defaultPermissions[target],
                result = {},
                defaultLabel = ' (' + labels.rm_Default + ')';

            if (permissions !== undefined) {

                var uACL = permissions[0],
                    oACL = permissions[1] & ~uACL;

                var pLabel = function(bitmap) {
                    var l = [];
                    opts.permissions.forEach(function(p) {
                        if (bitmap & p.b) {
                            l.push(p.l);
                        }
                    });
                    return l.join(', ');
                };

                if (uACL) {
                    result.uACL = pLabel(uACL) + defaultLabel;
                }
                if (oACL) {
                    result.oACL = pLabel(oACL) + defaultLabel;
                }
            }

            if (!result.uACL) {
                result.uACL = labels.rm_NoAccess + defaultLabel;
            }

            return result;
        },

        /**
         * Render the default rule for a module (when no rules are defined)
         *
         * @param {boolean} restricted - whether the module is restricted or not
         */
        _defaultRule: function(restricted) {

            var defaultRule;
            if (restricted) {
                defaultRule = labels.rm_NoAccess;
            } else {
                defaultRule = labels.rm_NoRestrictions;
            }

            defaultRule = $('<td>').attr('colspan', this.tableWidth)
                                   .text(defaultRule);

            return $('<tr class="rm-default-rule">').append(defaultRule);
        },

        /**
         * Render the table cells with permission selectors for a rule
         *
         * @param {Array} rule - the rule, containing the current
         *                       permission bitmaps of the rule
         *
         * @returns {object} - an object with the table cells
         *                     {uACL: [jQuery], oACL: [jQuery]}
         */
        _permissionSelector: function(rule) {

            var uBox = $('<td class="rm-permission-all">'),
                oBox = $('<td class="rm-permission-own">');

            this.options.permissions.forEach(function(permission) {

                // Create one checkbox each, append it to the respective box
                var uCheckbox = $('<input class="rm-permission" type="checkbox">'),
                    oCheckbox = $('<input class="rm-permission" type="checkbox">');

                $('<label>').append(uCheckbox)
                            .append(permission.l)
                            .appendTo(uBox);

                $('<label>').append(oCheckbox)
                            .append(permission.l)
                            .css({visibility: permission.o && 'visible' || 'hidden'})
                            .appendTo(oBox);

                // Set status and data for oACL checkbox
                var selected = rule[5] & permission.b;
                oCheckbox.prop('checked', selected);
                oCheckbox.data({
                    bit: permission.b,
                    selected: selected,
                    implied: false
                });

                // Set status and data for uACL checkbox
                selected = rule[4] & permission.b;
                uCheckbox.prop('checked', selected);
                uCheckbox.data({
                    bit: permission.b,
                    selected: selected,
                    implied: false
                });

                // Set implied initial status for oACĹ checkbox
                oCheckbox.data('implied', selected);
                if (selected) {
                    // Set checked and disable it
                    oCheckbox.prop({checked: true, disabled: true});
                }

                // Link oACL checkbox to uACL checkbox for future
                // implied status updates
                uCheckbox.data('imply', oCheckbox);
            });

            return {uACL: uBox, oACL: oBox};
        },

        /**
         * Render a scope selector
         *
         * @param {Array} rule - the current rule
         *
         * @returns {jQuery} - the DOM tree of the scope selector
         *
         * TODO support specific entities
         */
        _scopeSelector: function(rule) {

            var selector = $('<select class="rm-scope-select">'),
                assigned = $('<option value="">').text(labels.rm_AssignedEntities),
                any = $('<option value="any">').text(labels.rm_AllEntities);

            if (rule) {
                switch(rule[6]) {
                    case 'any':
                        any.prop('selected', true);
                        break;
                    default:
                        assigned.prop('selected', true);
                        rule[6] = null;
                        break;
                }
            }

            selector.append(assigned)
                    .append(any);

            return $('<div>').append(selector);
        },

        /**
         * Replace a default rule with a real rule; or open a row in
         * in the rule table to add a new rule
         *
         * @param {jQuery} trigger - the element that triggered the call
         */
        _addRule: function(trigger) {

            var opts = this.options,
                ruleTable = trigger.closest('.rm-module-rules'),
                prefix = ruleTable.data('module'),
                models = opts.models[prefix];

            // Close all open add-rows
            var self = this;
            $('tfoot .rm-rule', $(this.element)).each(function() {
                self._cancelAdd($(this));
            });

            // Trigger can be in the footer or in a default-permissions row
            var row = trigger.closest('.rm-rule'),
                newRow,
                rule;
            if (row.length) {
                // Adding a new rule from a default-permissions row
                rule = row.data('rule');

                // Create a new rule
                var tablename = rule[3];
                if (tablename) {
                    rule = [0, null, null, tablename, 0, 0, null, false];
                } else {
                    rule = [0, rule[1], rule[2], null, 0, 0, null, false];
                }

                // Pre-set default permissions (if any)
                var defaultPermissions = opts.defaultPermissions[getTarget(rule)];
                if (defaultPermissions) {
                    rule[4] = defaultPermissions[0];
                    rule[5] = defaultPermissions[1];
                }

                // Add to this.rules
                this.rules.push(rule);

                // Create a new row and replace the default-permissions row with it
                newRow = this._ruleTableRow(rule);
                row.after(newRow).remove();

                if (tablename) {
                    // Count the new rule as restriction for this table
                    models[tablename] += 1;
                }

                this._serialize();

            } else {
                // Adding a new rule from rule table footer
                var editNewRule = true;

                if (trigger.closest('.rm-table-rules').length) {
                    // New table rule
                    rule = [0, prefix, null, true, 0, 0, null, false];
                } else {
                    // New page rule
                    if (!opts.fRules) {
                        // Can only add one rule per module, fixed target
                        if (!$('tbody .rm-rule', ruleTable).length) {
                            rule = [0, prefix, null, null, 0, 0, null, false];
                            editNewRule = false;
                        }
                    } else {
                        rule = [0, prefix, true, null, 0, 0, null, false];
                    }
                }

                if (rule) {
                    // Generate a new row
                    newRow = this._ruleTableRow(rule);
                    if (editNewRule) {
                        // Append the new row to the footer
                        trigger.closest('.rm-module-add').hide().after(newRow);
                    } else {
                        // Append the new row to the tbody immediately
                        $('tbody', ruleTable).append(newRow);
                        trigger.closest('.rm-module-add').hide();
                    }
                }

                // Hide default rule, show column labels
                $('.rm-default-rule', ruleTable).hide();
                $('.rm-rule-labels', ruleTable).show();
            }
        },

        /**
         * Submit a new rule
         *
         * @param {jQuery} row - the add-row
         */
        _submitAdd: function(row) {

            var ruleTable = row.closest('.rm-module-rules'),
                rule = row.data('rule'),
                c = null,
                f = null,
                t = null,
                target = $('.rm-target-select', row).val().replace(/\s/, '');

            // Identify the selected target
            if (rule[3]) {
                // Table Rule
                t = target;
                if (!t) {
                    return;
                }
            } else {
                // Page Rule
                c = rule[1];
                f = target;

                var isOther = c == '_other';
                if (c == 'default/dt' || isOther) {

                    // Parse the target input
                    var r = /^(\w+)(\/(\*|[\w]+))?$/.exec(target);
                    if (r) {
                        c = r[1];
                        f = r[3];
                    } else {
                        // Invalid
                        return;
                    }

                    if (isOther) {
                        // Do not add to _other directly unless there is no
                        // specific rule table for this controller
                        var ruleTables = $('.rm-module-rules' ,row.closest('.rm-page-rules'));
                        for (var i = ruleTables.length; i--; ) {
                            var rt = $(ruleTables[i]);
                            if (rt.data('module') == c) {
                                ruleTable = rt;
                                break;
                            }
                        }
                    }
                }
                if (!f || f == '*') {
                    f = null;
                } else if (!/^\w+$/.exec(f)) {
                    // Invalid
                    return;
                }
            }

            // Update the target in the rule
            rule[1] = c && c.toLowerCase();
            rule[2] = f && f.toLowerCase();
            rule[3] = t && t.toLowerCase();

            // Find duplicate and/or following row in the rule table
            var duplicate,
                existing,
                following;

            $('tbody .rm-rule', ruleTable).each(function() {

                var $this = $(this),
                    other = $this.data('rule');

                if (!duplicate) {
                    if (equivalent(rule, other)) {
                        existing = other;
                        duplicate = $this;
                        following = duplicate;
                    } else if (!following) {
                        if (t) {
                            if (other[3] > t) {
                                following = $this;
                            }
                        } else {
                            if (other[2] && (f && other[2] > f || !f)) {
                                following = $this;
                            }
                        }
                    }
                }
            });

            // Update this.rules and main input
            if (existing && existing[0] !== null) {
                // Change the rule in place
                existing.splice(1, rule.length - 1);
                existing.push.apply(existing, rule.slice(1));
                rule = existing;
            } else {
                // Add new rule to this.rules
                this.rules.push(rule);
                var tablename = rule[3];
                if (tablename) {
                    // Count new restriction
                    var models = this.options.models[ruleTable.data('module')];
                    if (models[tablename] !== undefined) {
                        models[tablename] += 1;
                    } else {
                        models[tablename] = 1;
                    }
                }
            }
            this._serialize();

            // Generate new row and add it to the table body
            var newRow = this._ruleTableRow(rule);
            if (following) {
                newRow.insertBefore(following);
            } else {
                newRow.appendTo($('tbody', ruleTable));
            }
            if (duplicate) {
                duplicate.remove();
            }

            // Update rule number indication
            this._indicateNumRules(ruleTable, $('tbody .rm-rule', ruleTable).length);

            // Show add-action, then remove the add-row
            row.siblings('.rm-module-add').show();
            row.remove();
        },

        /**
         * Cancel adding a new rule
         *
         * @param {jQuery} row - the add-row
         */
        _cancelAdd: function(row) {

            var ruleTable = row.closest('.rm-module-rules');

            if ($('tbody .rm-rule', ruleTable).length === 0) {
                $('.rm-rule-labels', ruleTable).hide();
                $('.rm-default-rule', ruleTable).show();
            }

            row.siblings('.rm-module-add').show();
            row.remove();
        },

        /**
         * Update the rule of a rule table row
         *
         * @param {jQuery} row - the rule table row
         * @param {object} data - an object with the details to update
         */
        _updateRule: function(row, data) {

            var rule = row.data('rule');
            if (!rule) {
                return;
            }

            for (var k in data) {
                var v = data[k];
                if (v === undefined) {
                    continue;
                }
                switch(k) {
                    case 'c':
                        rule[1] = v;
                        break;
                    case 'f':
                        rule[2] = v;
                        break;
                    case 't':
                        rule[3] = v;
                        break;
                    case 'uACL':
                        rule[4] = v;
                        break;
                    case 'oACL':
                        rule[5] = v;
                        break;
                    case 'scope':
                        rule[6] = v;
                        break;
                    case 'deleted':
                        rule[7] = !!v;
                        break;
                    default:
                        break;
                }
            }

            // Update main input
            this._serialize();
        },

        /**
         * Delete a rule
         *
         * @param {jQuery} row - the rule table row
         */
        _deleteRule: function(row) {

            if (confirm(labels.rm_ConfirmDeleteRule)) {

                // Get the rule
                var opts = this.options,
                    ruleTable = row.closest('.rm-module-rules'),
                    moduleRestricted = false,
                    rule = row.data('rule'),
                    otherRules,
                    defaultRule;

                // Mark the rule as deleted
                rule[7] = true;
                this._serialize();

                var tablename = rule[3];
                if (tablename) {
                    // Do we have another rule for this table?
                    otherRules = this.rules.filter(function(r) {
                        return r[3] == tablename && !r[7];
                    });
                    if (!otherRules.length) {
                        // We removed the last rule for this table
                        var prefix = ruleTable.data('module'),
                            models = opts.models[prefix];

                        // Update restrictions
                        models[tablename] -= 1;
                        if (models[tablename] > 0) {
                            // Table is still restricted => show default permissions
                            defaultRule = [null, null, null, tablename, null, null, null, false];
                            this._ruleTableRow(defaultRule).insertBefore(row);
                        }
                    }
                } else {
                    otherRules = this.rules.filter(function(r) {
                        return r[1] == rule[1] && r[2] == rule[2] && !r[7];
                    });
                    if (!otherRules.length) {
                        if (opts.defaultPermissions[getTarget(rule)]) {
                            defaultRule = [null, rule[1], rule[2], null, null, null, null, false];
                            this._ruleTableRow(defaultRule).insertBefore(row);
                        }
                    }
                    moduleRestricted = true;
                }

                // Update number of rules in this rule table
                var remainingRules = $('.rm-rule', ruleTable).length - 1;
                if (!remainingRules) {
                    // Show default rule
                    this._defaultRule(moduleRestricted).insertBefore(row);
                    // Hide header
                    $('.rm-rule-labels', ruleTable).hide();
                    // Show add-row
                    $('.rm-module-add', ruleTable).show();
                }
                this._indicateNumRules(ruleTable, remainingRules);

                // Remove this row
                row.remove();
            }
        },

        /**
         * Update the permissions in the rule of a rule table row
         *
         * @param {jQuery} row - the rule table row
         */
        _updatePermissions: function(row) {

            this._updateRule(row, {
                uACL: this._getPermissions($('.rm-permission-all', row)),
                oACL: this._getPermissions($('.rm-permission-own', row))
            });
        },

        /**
         * Get the permissions bitmap from a permission selector
         *
         * @param {jQuery} cbContainer - the checkbox container (table cell)
         *
         * @returns {integer} - the permissions bitmap
         */
        _getPermissions: function(cbContainer) {

            var permissions = 0;

            $('.rm-permission', cbContainer).each(function() {
                var cb = $(this);
                if (!cb.data('implied') && cb.data('selected')) {
                    var bit = cb.data('bit');
                    if (bit) {
                        permissions |= bit;
                    }
                }
            });

            return permissions;
        },

        /**
         * Indicate the number of rules in a rule table
         *
         * @param {jQuery} ruleTable - the rule table
         * @param {integer} numRules - the number of rules in this table
         */
        _indicateNumRules: function(ruleTable, numRules) {

            var indicator = $('.rm-module-numrules', ruleTable);

            if (numRules) {
                indicator.text('[' + numRules + ']');
                ruleTable.addClass('hasrules');
            } else {
                indicator.empty();
                ruleTable.removeClass('hasrules');
            }
        },

        /**
         * Toggle a rule table
         *
         * @param {jQuery} table - the table
         */
        _toggleRuleTable: function(table) {

            if (table.hasClass('rm-expanded')) {
                $('tbody, tfoot', table).hide();
                table.removeClass('rm-expanded');
            } else {
                $('tbody, tfoot', table).show();
                table.addClass('rm-expanded');
            }
            $('.rm-module-toggle i', table).toggle();
        },

        /**
         * Expand/Collapse all rule tables on a tab
         *
         * @param {jQuery} tab - the tab-div
         * @param {boolean} visibility - false=collapse, true=expand
         */
        _toggleAll: function(tab, visibility) {

            var self = this;
            if (visibility) {
                $('.rm-module-rules:not(.rm-expanded)', tab).each(function(index, table) {
                    self._toggleRuleTable($(table));
                });
            } else {
                $('.rm-module-rules.rm-expanded', tab).each(function(index, table) {
                    self._toggleRuleTable($(table));
                });
            }

        },

        /**
         * Actions when a permission checkbox changes status
         *
         * @param {jQuery} checkbox - the permission checkbox
         */
        _permissionChanged: function(checkbox) {

            if (checkbox.data('implied')) {
                // Set checked and disable
                checkbox.prop({
                    checked: true,
                    disabled: true
                });
            } else if (checkbox.prop('disabled')) {
                // Re-enable and restore selection
                checkbox.prop({
                    disabled: false,
                    checked: checkbox.data('selected')
                });
            } else {
                // Store selection and propagate to implied checkbox
                var selected = checkbox.prop('checked'),
                    implied = checkbox.data('imply');

                checkbox.data({selected: selected});
                if (implied && implied.length) {
                    implied.data('implied', selected).change();
                }
            }

            // Update the rule
            this._updatePermissions(checkbox.closest('.rm-rule'));
        },

        /**
         * Actions when the scope selection changes
         *
         * @param {jQuery} selector - the scope selector
         *
         * TODO support specific entities
         * TODO use updateRule
         */
        _scopeChanged: function(selector) {

            var row = selector.closest('.rm-rule'),
                rule = row.data('rule');

            switch(selector.val()) {
                case 'any':
                    rule[6] = 'any';
                    break;
                default:
                    rule[6] = null;
                    break;
            }

            this._serialize();
        },

        /**
         * Bind events to generated elements (after refresh)
         */
        _bindEvents: function() {

            var el = $(this.element),
                ns = this.eventNamespace,
                self = this;

            $('.rm-table-rules, .rm-page-rules', el)
                .on('click' + ns, '.rm-expand-all', function() {
                    // Expand all rule tables on the tab
                    self._toggleAll($(this).closest('.rm-table-rules, .rm-page-rules'), true);
                    return false;
                })
                .on('click' + ns, '.rm-collapse-all', function() {
                    // Collapse all rule tables on the tab
                    self._toggleAll($(this).closest('.rm-table-rules, .rm-page-rules'), false);
                    return false;
                });

            $('.rm-module-rules', el)
                .on('click' + ns, '.rm-module-header', function() {
                    // Toggle visibility of a rule table
                    self._toggleRuleTable($(this).closest('.rm-module-rules'));
                    return false;
                })
                .on('change' + ns, '.rm-permission', function() {
                    // Handle status change of a permission checkbox
                    self._permissionChanged($(this));
                    return false;
                })
                .on('change' + ns, '.rm-scope-select', function() {
                    self._scopeChanged($(this));
                    return false;
                })
                .on('click' + ns, '.rm-delete-rule', function() {
                    // Delete a rule
                    self._deleteRule($(this).closest('.rm-rule'));
                    return false;
                })
                .on('click' + ns, '.rm-add-rule', function() {
                    self._addRule($(this));
                })
                .on('click' + ns, '.rm-cancel-add', function() {
                    self._cancelAdd($(this).closest('.rm-rule'));
                })
                .on('click' + ns, '.rm-submit-rule', function() {
                    self._submitAdd($(this).closest('.rm-rule'));
                })
                .on('input' + ns, 'input.rm-target-select', function() {
                    self._validateTarget($(this));
                });

            return true;
        },

        /**
         * Unbind events (before refresh)
         */
        _unbindEvents: function() {

            var el = $(this.element),
                ns = this.eventNamespace;

            $('.rm-module-rules, .rm-table-rules, .rm-page-rules', el).off(ns);

            return true;
        }

    });
})(jQuery);
