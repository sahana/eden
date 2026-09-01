/**
 * jQuery UI Widget for DataSeriesMeasurement
 *
 * @copyright 2026 (c) Sahana Software Foundation
 * @license MIT
 */

/* jshint esversion: 6 */

(function($, undefined) {
    "use strict";
    var dsFormID = 0;

    /**
     * dsTable
     */
    $.widget('s3.dsForm', {

        /**
         * Default options
         *
         * @todo document options
         */
        options: {

        },

        /**
         * Create the widget
         */
        _create: function() {
            this.id = dsFormID;
            dsFormID += 1;

            this.eventNamespace = '.dsForm';
            this.selections;

            this._initializeButton();
        },

        /**
         * Update the widget options
         */
        _init: function() {
            self = this;

            const $el = $(this.element),
                  widgetID = $el.attr('id'),
                  dataInput = $('#' + widgetID + '-data');

            // Read+parse initial data
            self.data = {
                tests: [
                    {
                        title: 'Drogentests',
                        groups: [
                            {
                                title: 'Haarprobe (Drogentests)',
                                parameters: [
                                    {id: 0, title: 'H-Heroin', unit: 'He/H'},
                                    {id: 1, title: 'H-Kokain', unit: 'Nasen'},
                                    {id: 2, title: 'H-LSD', unit: 'mg'},
                                ],
                            },
                            {
                                title: 'Urinprobe (Drogentests)',
                                parameters: [
                                    {id: 3, title: 'U-Heroin', unit: 'ml'},
                                    {id: 4, title: 'U-Kokain', unit: 'mg'},
                                    {id: 5, title: 'U-LSD', unit: '€'},
                                ],
                            },
                        ]
                    },
                    {
                        title: 'Schwangerschaftstests',
                        groups: [
                            {
                                title: 'Urinprobe (Schwangerschaftstests)',
                                parameters: [
                                    {id: 6, title: 'U-hCG', unit: 'IE/l'},
                                ],
                            },
                        ]
                    }
                ]
            };
            if (dataInput.length) {
                try {
                    self.data = JSON.parse(dataInput.val());
                } catch(e) {
                    // pass
                }
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
            this._unbindEvents();

            this._renderForm(self.data);

            this._bindEvents();
        },

        _addItem: function(category, item, group) {
            $('#dsform-items-selected').append(item);

            const children = group.children();

            if (children.length == 0) {
                group.parent().hide();

                for (const parameter of category.find('.dsform-parameter')) {
                    if ($(parameter).is(':visible')) {
                        return;
                    }
                }

                category.hide();
            }
        },

        _addGroupItems: function(group) {
            for (const button of group.find('.dsform-button-add')) {
                button.click();
            }
        },

        _removeItem: function(category, item, items) {
            let itemBefore = undefined;
            const title = item.find('.dsform-category-title')
                .text()
                .toLowerCase();

            items.children().each(
                (_index, element) => {
                    const titleChild = $(element)
                        .find('.dsform-category-title')
                        .text()
                        .toLowerCase();

                    if (title < titleChild) {
                        itemBefore = element;
                        return false;
                    }
                }
            );

            if (itemBefore === undefined) {
                items.append(item);
            } else {
                item.insertBefore(itemBefore);
            }

            item.parent().parent().show();

            category.show();
        },

        _renderForm: function(data) {
            const $el = $(this.element);

            const parameterGroups = this._renderLeftColumn();
            const selection = this._renderSelection();

            this.selections = selection;

            const measurements = $('<div id="dsform-measurement">')
                .append(parameterGroups)
                .append(selection);

            $el.empty()
                .append(measurements);

            parameterGroups.show();
            selection.show();
            measurements.show();
        },

        _renderTests: function(container) {
            const tests = [];

            for (const test of self.data.tests) {
                const testElement = $('<div class="dsform-parameter-group">');
                const testTitle = $('<label class="dsform-parameter-group-title">').text(test.title);
                testElement.append(testTitle);

                for (const group of test.groups) {
                    const groupElement = this._renderParameterGroup(testElement, group.title, group.parameters);

                    testElement.append(groupElement);
                }

                tests.push(testElement);
            }

            return tests;
        },

        _renderSearchBar: function() {
            const bar = $('<input type="search" placeholder="Filtern">');

            return bar;
        },

        _renderParameterGroup: function(category, title, parameters) {
            const group = $('<div class="dsform-parameter">');

            const header = $('<div class="dsform-parameter-header">');

            const groupTitle = $('<label class="dsform-parameter-title">').text(title);
            const button = $('<input type="button">');
            button.attr('value', '>');
            button.on(
                'click',
                () => {
                    this._addGroupItems(group);
                }
            );

            header.append(groupTitle);
            header.append(button);

            const groupContent = $('<ul class="dsform-items-group-content">');
            groupContent.hide();

            for (const parameter of parameters) {
                const parameterElement = this._renderParameter(
                    parameter,
                    () => {this._addItem(category, parameterElement, groupContent)},
                    () => {this._removeItem(category, parameterElement, groupContent)},
                );

                groupContent.append(parameterElement);
            }

            groupTitle.on(
                'click',
                () => {
                    groupContent.slideToggle();
                }
            );

            group.append(header);
            group.append(groupContent);

            return group;
        },

        _renderLeftColumn: function(data) {
            const searchBar = this._renderSearchBar();

            const parameterGroups = $('<div id="dsform-collection">');
            parameterGroups.append(searchBar);

            for (const test of this._renderTests(parameterGroups)) {
                parameterGroups.append(test);
            }

            return parameterGroups;
        },

        _renderSelection: function() {
            const selection = $('<ul id="dsform-items-selected">');

            return selection;
        },

        _renderParameter: function(parameter, onadd, onremove) {
            const parameterElement = $('<li>');
            parameterElement.addClass('dsform-category');

            const header = this._renderHeader(parameter.title, onadd, onremove);
            const body = this._renderBody(parameter.id, parameter.unit);
        
            parameterElement.append(header);
            parameterElement.append(body);

            return parameterElement;
        },

        _renderButton: function(title, className) {
            const button = $('<input>');
            button.addClass(className);
            button.addClass('action-btn');

            button.attr('type', 'button');
            button.attr('value', title);

            return button;
        },

        _renderHeader: function(title, onadd, onremove) {
            const header = $('<div>');
            header.addClass('dsform-category-header');

            const buttonRemove = this._renderButton('<', 'dsform-button-remove')
                .on('click', onremove);

            const buttonAdd = this._renderButton('>', 'dsform-button-add')
                .on('click', onadd);

            const spanTitle = $('<span class="dsform-category-title">').html(title);

            buttonRemove.appendTo(header);
            spanTitle.appendTo(header);
            buttonAdd.appendTo(header);

            return header;
        },

        _renderBody: function(id, unit) {
            const body = $('<div class="measurement">');

            const measurementInput = $('<div class="measurement-input">');

            const elementId = $('<input type="hidden">');
            elementId.attr('value', id);
            measurementInput.append(elementId);

            const isAbnormal = $('<input type="hidden" value="0">');
            measurementInput.append(isAbnormal);

            const unitText = $('<span class="measurement-unit">');
            $(unitText).text(unit);

            const value = $('<input class="measurement-value" type="number">');
            value.attr('style', 'width: auto !important;');
            measurementInput.append(value);

            const inputButtons = this._renderInputButtons(value, isAbnormal);
            measurementInput.append(inputButtons);

            body.append(measurementInput);
            body.append(unitText);

            return body;
        },

        _renderInputButtons: function(input, isAbnormal) {
            const container = $('<div class="measurement-input-buttons">');

            const switchText = $('<button class="measurement-input-switch measurement-input-switch-text">T</button>');
            switchText.on(
                'click',
                (event) => {
                    event.preventDefault();

                    switchText.toggleClass('dsform-switch-on');

                    if (input.attr('type') === 'text') {
                        input.attr('type', 'number');
                    } else {
                        input.attr('type', 'text');
                    }
                }
            );

            const switchAbnormal = $('<button class="measurement-input-switch measurement-input-switch-abnormal">!</button>');
            switchAbnormal.on(
                'click',
                (event) => {
                    event.preventDefault();

                    switchAbnormal.toggleClass('dsform-switch-on');

                    isAbnormal.attr('value', isAbnormal.attr('value') === "0" ? "1" : "0");
                    input.toggleClass('measurement-input-abnormal');
                }
            )

            container.append(switchText);
            container.append(switchAbnormal);

            return container;
        },

        _initializeButton: function() {
            const button = $('#dsform-button');
            button.on(
                'click',
                () => {
                    button.hide();
                    $('#dsForm').slideDown();
                }
            );
        },

        /**
         * Bind events to generated elements (after refresh)
         */
        _bindEvents: function() {
            let $el = $(this.element),
                ns = this.eventNamespace,
                self = this;

            return true;
        },

        /**
         * Unbind events (before refresh)
         */
        _unbindEvents: function() {
            let $el = $(this.element),
                ns = this.eventNamespace;

            return true;
        }
    });
})(jQuery);
