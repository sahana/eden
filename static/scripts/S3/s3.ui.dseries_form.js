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

    class Group {
        /**
         * @param {number} id
         * @param {string} name
         */
        constructor(id, name) {
            this.id = id;
            this.name = name;
            this._samples = [];
        }

        clone() {
            return new Group(this.id, this.name);
        }

        isEmpty() {
            for (const sample of this._samples) {
                if (!sample.isEmpty()) {
                    return false;
                }
            }

            return true;
        }

        getHtml() {
            const $groupElement = $('<div class="dsform-parameter-group">');

            const $groupTitle =  $('<label class="dsform-parameter-group-title">').text(this.name);
            $groupElement.append($groupTitle);

            for (const sample of this._samples) {
                $groupElement.append(sample.getHtml());
            }

            return $groupElement;
        }

        /**
         * @param {Sample} sample
         */
        addSample(sample) {
            this._samples.push(sample);
        }
    }

    class Sample {
        /**
         * @param {number} id
         * @param {string} name
         */
        constructor(id, name, isFolded=true) {
            this.id = id;
            this.name = name;
            this.isFolded = isFolded;
            this._parameters = [];
            this.container = undefined;
        }

        clone() {
            return new Sample(this.id, this.name, this.isFolded);
        }

        isEmpty() {
            return this._parameters.length === 0;
        }

        getHtml() {
            const sample = $('<div class="dsform-sample">');
            const header = $('<div class="dsform-sample-header">');

            const sampleTitle = $('<label class="dsform-sample-title">').text(this.name);
            const buttonAddSample = $('<input type="button">');
            buttonAddSample.attr('value', '>');
            $(buttonAddSample).on(
                'click',
                () => {
                    for (const parameter of this._parameters) {
                        parameter.setSelected(true);
                    }
                }
            );

            header.append(sampleTitle);
            header.append(buttonAddSample);

            this.container = $('<ul class="dsform-parameters">');

            if (this.isFolded) {
                this.container.hide();
            }

            $(sampleTitle).on(
                'click',
                _ => this.toggle()
            );

            $(this._parameters).each(
                (_index, parameter) => {
                    if (parameter.isSelected) {
                        return true;
                    }

                    this.container.append(parameter.getHtml());
                }
            );

            sample.append(header);
            sample.append(this.container);

            return sample;
        }

        /**
         * @param {Parameter} parameter 
         */
        addParameter(parameter) {
            this._parameters.push(parameter);
        }

        toggle() {
            if (this.isFolded) {
                this.unfold();
            } else {
                this.fold();
            }
        }

        fold() {
            this.isFolded = true;

            $(this.container).slideUp();
        }

        unfold() {
            this.isFolded = false;

            $(this.container).slideDown();
        }
    }

    class Parameter {
        /**
         * @param {object} data
         * @param {number} data.id
         * @param {string} data.name
         * @param {string} data.unit
         * @param {number} data.group
         * @param {number} data.sample
         * @param {boolean} [selected=false] 
         */
        constructor(data, selected = false) {
            this.id = data.id;
            this.name = data.name;
            this.unit = data.unit;
            this.group = data.group;
            this.sample = data.sample;
            this.isSelected = selected;
        }

        getHtml() {
            const parameterElement = $('<li class="dsform-parameter">');

            const header = this._renderHeader(data);
            const body = this._renderBody(data);
        
            parameterElement.append(header);
            parameterElement.append(body);

            return parameterElement;
        }

        /**
         * @param {boolean} isSelected 
         */
        setSelected(isSelected) {
            this.isSelected = isSelected;

            window.dispatchEvent(new Event('dsform-update'));
        }

        _renderHeader() {
            const header = $('<div>');
            header.addClass('dsform-parameter-header');

            const buttonRemove = this._renderButton('<', 'dsform-button-remove');
            $(buttonRemove).on(
                'click',
                _ => this.setSelected(false)
            );

            const buttonAdd = this._renderButton('>', 'dsform-button-add');
            $(buttonAdd).on(
                'click',
                _ => this.setSelected(true)
            );

            const spanTitle = $('<span class="dsform-parameter-title">').html(this.name);

            buttonRemove.appendTo(header);
            spanTitle.appendTo(header);
            buttonAdd.appendTo(header);

            return header;
        }

        _renderBody() {
            const body = $('<div class="measurement">');

            const measurementInput = $('<div class="measurement-input">');

            const elementId = $('<input type="hidden">');
            elementId.attr('value', this.id);
            measurementInput.append(elementId);

            const isAbnormal = $('<input type="hidden" value="0">');
            measurementInput.append(isAbnormal);

            const unitText = $('<span class="measurement-unit">');
            $(unitText).text(this.unit);

            const value = $('<input class="measurement-value" type="number">');
            value.attr('style', 'width: auto !important;');
            measurementInput.append(value);

            const inputButtons = this._renderInputButtons(value, isAbnormal);
            measurementInput.append(inputButtons);

            body.append(measurementInput);
            body.append(unitText);

            return body;
        }

        /**
         * @param {HTMLInputElement} input
         * @param {boolean} isAbnormal
         * 
         * @returns {HTMLDivElement}
         */
        _renderInputButtons(input, isAbnormal) {
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
        }

        /**
         * @param {string} title 
         * @param {string} className
         * 
         * @returns {HTMLInputElement}
         */
        _renderButton(title, className) {
            const button = $('<input>');
            button.addClass(className);
            button.addClass('action-btn');

            button.attr('type', 'button');
            button.attr('value', title);

            return button;
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
                  widgetID = $el.attr('id');

            window.addEventListener(
                'dsform-update',
                () => {
                    this._updateParameterSection();
                    this._updateParameterSelection();
                }
            );

            // Read+parse initial data
            self.rawData = {
                parameters: [
                    {group: 0, sample: 0, id: 0, name: 'H-Heroin', unit: 'He/H'},
                    {group: 0, sample: 0, id: 1, name: 'H-Kokain', unit: 'Nasen'},
                    {group: 0, sample: 0, id: 2, name: 'H-LSD', unit: 'mg'},
                    {group: 0, sample: 1, id: 3, name: 'U-Heroin', unit: 'ml'},
                    {group: 0, sample: 1, id: 4, name: 'U-Kokain', unit: 'mg'},
                    {group: 0, sample: 1, id: 5, name: 'U-LSD', unit: '€'},
                    {group: 1, sample: 2, id: 6, name: 'U-hCG', unit: 'IE/l'},
                ],
                groups: [
                    {id: 0, name: 'Drogentests'},
                    {id: 1, name: 'Schwangerschaftstests'},
                ],
                samples: [
                    {id: 0, name: 'Haarprobe (Drogentests)'},
                    {id: 1, name: 'Urinprobe (Drogentests)'},
                    {id: 2, name: 'Urinprobe (Schwangerschaftstests)'},
                ],
            };

            this.data = this._loadData();

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

            this._renderForm();

            this._bindEvents();
        },

        _renderFormRow: function(title, type) {
            const $row = $('<div class="form-row row">');

            const $label = $('<label>');
            $label.text(title);

            const $input = $('<input>');
            $input.attr('type', type);

            $row.append($label);
            $row.append($input);

            return $row;
        },

        _renderInputHeader: function() {
            const $header = $('<div>');

            const $datetime = $('<input type="datetime-local">');

            const $status = $('<select>');

            $.each(
                ['Pending', 'Preliminary', 'Final'],
                (_index, stat) => {
                    const $option = $('<option>');
                    $option.text(stat);

                    $status.append($option);
                }
            );

            $header.append($datetime);
            $header.append($status);

            return $header;
        },
     
        _renderForm: function() {
            const $el = $(this.element);

            const $header = this._renderInputHeader();

            const parameterGroups = this._renderLeftColumn();
            const selection = this._renderSelection();

            this.selections = selection;

            const measurements = $('<div id="dsform-measurement">')
                .append(parameterGroups)
                .append(selection);

            $el.empty()
                .append($header)
                .append(measurements);

            this._updateParameterSection();
            this._updateParameterSelection();

            parameterGroups.show();
            selection.show();
            measurements.show();
        },

        _renderSearchBar: function(parameterContainer) {
            const bar = $('<input type="search" id="filter" placeholder="Filtern">');
            bar.on(
                'input',
                _ => this._updateParameterSection(parameterContainer, $(bar).val().split(' '))
            );

            return bar;
        },

        _loadData: function() {
            const groups = [];
            const samples = [];

            for (const parameter of this.rawData.parameters) {
                if (!groups.hasOwnProperty(parameter.group)) {
                    const groupName = this.rawData.groups.find(sample => sample.id === parameter.group).name;
                    groups[parameter.group] = new Group(parameter.group, groupName);
                }

                if (!samples.hasOwnProperty(parameter.sample)) {
                    const sampleName = this.rawData.samples.find(sample => sample.id === parameter.sample).name;
                    const sample = new Sample(parameter.sample, sampleName);

                    samples[parameter.sample] = sample;
                    groups[parameter.group].addSample(sample);
                }

                samples[parameter.sample].addParameter(new Parameter(parameter));
            }
            
            return groups;
        },

        _updateParameterSection: function() {
            const groups = this._filterData();

            const container = $('#dsform-parameter-container');
            container.empty();

            for (const group of groups) {
                container.append(group.getHtml());
            }
        },

        _updateParameterSelection: function() {
            const selection = $('#dsform-items-selected');
            selection.empty();

            for (const group of this.data) {
                for (const sample of group._samples) {
                    for (const parameter of sample._parameters) {
                        if (!parameter.isSelected) {
                            continue;
                        }

                        selection.append(parameter.getHtml());
                    }
                }
            }
        },

        _filterEmptySamples(data) {
            const groupsFiltered = [];

            for (const group of data) {
                const samplesFiltered = [];

                for (const sample of group._samples) {
                    if (sample._parameters.filter(parameter => !parameter.isSelected).length > 0) {
                        const clone = sample.clone();
                        clone._parameters = sample._parameters;

                        samplesFiltered.push(clone);
                    }
                }

                if (samplesFiltered.length === 0) {
                    continue;
                }

                const clone = group.clone();
                clone._samples = samplesFiltered;

                groupsFiltered.push(clone);
            }

            return groupsFiltered;
        },

        /**
         * @returns {array<Group>}
         */
        _filterData: function() {
            const filterInput = $('#filter').val();

            const prompts = filterInput.split(' ');
            const hasPrompts = prompts.length > 0 && prompts[0].trim() !== '';

            const groupsFiltered = [];

            for (const group of this.data) {
                const hasGroupMatch = !hasPrompts || this._hasMatch(prompts, group.name);

                const samplesFiltered = [];

                for (const sample of group._samples) {
                    const hasSampleMatch = !hasPrompts || this._hasMatch(prompts, sample.name);

                    if ((hasGroupMatch || hasSampleMatch) && sample._parameters.filter(parameter => !parameter.isSelected).length > 0) {
                        samplesFiltered.push(sample);

                        continue;
                    }

                    const parametersFiltered = sample._parameters.filter(
                        parameter => !parameter.isSelected && (!hasPrompts || this._hasMatch(prompts, parameter.name))
                    );

                    if (parametersFiltered.length > 0) {
                        const clone = sample.clone();
                        clone._parameters = parametersFiltered;

                        samplesFiltered.push(clone);
                    }
                }

                if (samplesFiltered.length === 0) {
                    continue;
                }

                const clone = new Group(group.id, group.name);
                clone._samples = samplesFiltered;

                groupsFiltered.push(clone);
            }

            return groupsFiltered;
        },

        /**
         * @param {array<string>} prompts
         * @param {string} haystack
         * 
         * @returns {boolean}
         */
        _hasMatch: function(prompts, haystack) {
            for (const prompt of prompts) {
                if (prompt.trim() === '') {
                    continue;
                }

                if (haystack.toLowerCase().includes(prompt.toLowerCase())) {
                    return true;
                }
            }

            return false;
        },

        _renderLeftColumn: function() {
            const element = $('<div id="dsform-collection">');

            const parameterContainer = $('<div id="dsform-parameter-container">');
            const searchBar = this._renderSearchBar(parameterContainer);

            element.append(searchBar);
            element.append(parameterContainer);

            return element;
        },

        _renderSelection: function() {
            const selection = $('<ul id="dsform-items-selected">');

            return selection;
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
