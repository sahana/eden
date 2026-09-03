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

    function FilterResult() {
        this.hasDirectMatch = false;
        this.items = [];

        this.hasMatch = function() {
            return this.hasDirectMatch || this._hasItemMatch();
        }

        this._hasItemMatch = function() {
            for (const item of this.items) {
                if (item.hasMatch()) {
                    return true;
                }
            }

            return false;
        }
    }

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

        _addItem: function(parameterGroup, item, group) {
            $('#dsform-items-selected').append(item);

            const children = group.children();

            if (children.length == 0) {
                group.parent().hide();

                for (const sample of parameterGroup.find('.dsform-sample')) {
                    if ($(sample).is(':visible')) {
                        return;
                    }
                }

                parameterGroup.hide();
            }

            this._filterParameters();
        },

        _addGroupItems: function(group) {
            for (const button of group.find('.dsform-button-add')) {
                button.click();
            }
        },

        _removeItem: function(item, items) {
            let itemBefore = undefined;
            const title = item.find('.dsform-parameter-title')
                .text()
                .toLowerCase();

            items.children().each(
                (_index, element) => {
                    const titleChild = $(element)
                        .find('.dsform-parameter-title')
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

            this._filterParameters();
        },

        _filter: function(prompt) {

        },

        _renderInputHeader: function() {

        },

        _filterParameters: function() {
            const prompt = $('#filter').val();
            const tags = prompt.toLowerCase().split(' ');

            const groupResults = [];

            $('#dsform-collection').find('.dsform-parameter-group').each(
                (_index, group) => {
                    const $samples = $(group).find('.dsform-sample');
                    const result = new FilterResult();
                    result.hasDirectMatch = false;

                    $samples.each(
                        (_index, parameter) => {
                            const $parameters = $(parameter).find('.dsform-parameter');

                            const parameterResult = new FilterResult();
                            parameterResult.hasDirectMatch = $parameters.length > 0 
                                ? (result.hasDirectMatch || this._hasMatch(tags, [$(parameter).attr('data-filter-prompt').toLowerCase()]))
                                : false;

                            $parameters.each(
                                (_index, item) => {
                                    const itemResult = new FilterResult();
                                    itemResult.hasDirectMatch = parameterResult.hasDirectMatch || this._hasMatch(tags, [$(item).attr('data-filter-prompt').toLowerCase()]);

                                    parameterResult.items.push(itemResult);
                                }
                            );

                            result.items.push(parameterResult);
                        }
                    );

                    groupResults.push(result);
                }
            );

            $('#dsform-collection').find('.dsform-parameter-group').each(
                (groupIndex, group) => {
                    if (prompt !== '' && !groupResults[groupIndex].hasMatch()) {
                        $(group).hide();

                        return true;
                    }

                    $(group).show();

                    $(group).find('.dsform-sample').each(
                        (parameterIndex, parameter) => {
                            if (prompt !== '' && !groupResults[groupIndex].items[parameterIndex].hasMatch()) {
                                $(parameter).hide();

                                return true;
                            }

                            $(parameter).show()

                            $(parameter).find('.dsform-parameter').each(
                                (itemIndex, item) => {
                                    if (prompt !== '' && !groupResults[groupIndex].items[parameterIndex].items[itemIndex].hasMatch()) {
                                        $(item).hide();

                                        return true;
                                    }

                                    $(item).show();
                                }
                            );
                        }
                    );
                }
            );
        },
     
        _hasMatch: function(tags, haystacks) {
            for (const tag of tags) {
                for (const haystack of haystacks) {
                    if (haystack.includes(tag)) {
                        return true;
                    }
                }
            }

            return false;
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

        _renderParameterGroups: function(container) {
            const parameterGroups = [];

            for (const test of self.data.tests) {
                const testElement = $('<div class="dsform-parameter-group">');
                testElement.attr('data-filter-prompt', test.title.toLowerCase());

                const testTitle = $('<label class="dsform-parameter-group-title">').text(test.title);
                testElement.append(testTitle);

                for (const group of test.groups) {
                    const groupElement = this._renderSample(testElement, group.title, group.parameters);

                    testElement.append(groupElement);
                }

                parameterGroups.push(testElement);
            }

            return parameterGroups;
        },

        _renderSearchBar: function() {
            const bar = $('<input type="search" id="filter" placeholder="Filtern">');
            bar.on(
                'input',
                () => {
                    this._filterParameters();
                }
            );

            return bar;
        },

        _renderSample: function(parameterGroup, title, parameters) {
            const sample = $('<div class="dsform-sample">');
            sample.attr('data-filter-prompt', title.toLowerCase());

            const header = $('<div class="dsform-sample-header">');

            const sampleTitle = $('<label class="dsform-sample-title">').text(title);
            const buttonAddSample = $('<input type="button">');
            buttonAddSample.attr('value', '>');
            buttonAddSample.on(
                'click',
                () => {
                    this._addGroupItems(sample);
                }
            );

            header.append(sampleTitle);
            header.append(buttonAddSample);

            const parameterContainer = $('<ul class="dsform-parameters">');
            parameterContainer.hide();

            for (const parameter of parameters) {
                const parameterElement = this._renderParameter(
                    parameter,
                    () => {this._addItem(parameterGroup, parameterElement, parameterContainer)},
                    () => {this._removeItem(parameterElement, parameterContainer)},
                );

                parameterContainer.append(parameterElement);
            }

            sampleTitle.on(
                'click',
                () => {
                    parameterContainer.slideToggle();
                }
            );

            sample.append(header);
            sample.append(parameterContainer);

            return sample;
        },

        _renderLeftColumn: function(data) {
            const element = $('<div id="dsform-collection">');
            const searchBar = this._renderSearchBar();

            element.append(searchBar);

            for (const parameterGroup of this._renderParameterGroups(element)) {
                element.append(parameterGroup);
            }

            return element;
        },

        _renderSelection: function() {
            const selection = $('<ul id="dsform-items-selected">');

            return selection;
        },

        _renderParameter: function(parameter, onadd, onremove) {
            const parameterElement = $('<li class="dsform-parameter">');
            parameterElement.attr('data-filter-prompt', parameter.title.toLowerCase());

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
            header.addClass('dsform-parameter-header');

            const buttonRemove = this._renderButton('<', 'dsform-button-remove')
                .on('click', onremove);

            const buttonAdd = this._renderButton('>', 'dsform-button-add')
                .on('click', onadd);

            const spanTitle = $('<span class="dsform-parameter-title">').html(title);

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
