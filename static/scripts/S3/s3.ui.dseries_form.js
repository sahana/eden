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
            self.data = {};
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

        _addItem: function(item) {
            $('#dsform-items-selected').append(item);
        },

        _removeItem: function(item, items) {
            let itemBefore = undefined;
            const title = item.find('.dsform-category-title')
                .text()
                .toLowerCase();

            items.children().each(
                (_index, element) => {
                    const titleChild = $(element).find('.dsform-category-title').text().toLowerCase();

                    if (title < titleChild) {
                        itemBefore = element;
                        return false;
                    }
                }
            );

            if (itemBefore === undefined) {
                items.append(item);
                return;
            }

            item.insertBefore(itemBefore);
        },

        _renderForm: function(data) {
            const $el = $(this.element);

            const parameterGroups = this._renderParameterGroups();
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

        _renderParameterGroups: function(data) {
            const parameterGroups = $('<div id="dsform-collection">');
            const test = $('<div class="dsform-collection-item-group">');
            const testTitle = $('<label class="dsform-collection-group-title">').text('Drogentest');
            test.append(testTitle);

            const group = $('<div class="dsform-collection-item-group">');
            const groupTitle = $('<label class="dsform-collection-group-title">').text('Haarprobe (Drogentest)');
            const groupContent = $('<ul class="dsform-items-group-content">');
            groupContent.hide();

            groupTitle.on(
                'click',
                () => {
                    groupContent.toggle();
                }
            );

            group.append(groupTitle);
            group.append(groupContent);

            for (const param of ['Kokain', 'LSD', 'Heroin', 'Marihuana', 'Crystal Meth', 'Ecstacy']) {
                const parameter = this._renderParameter(
                    param,
                    () => {this._addItem(parameter)},
                    () => {this._removeItem(parameter, groupContent)},
                );
                groupContent.append(parameter);
            }

            test.append(group);
            parameterGroups.append(test);

            return parameterGroups;
        },

        _renderSelection: function() {
            const selection = $('<ul id="dsform-items-selected">');

            return selection;
        },

        _renderParameter: function(title, onadd, onremove) {
            const parameter = $('<li>');
            parameter.addClass('dsform-category');

            const header = this._renderHeader(title, onadd, onremove);
            const body = this._renderBody("Nasen");
        
            parameter.append(header);
            parameter.append(body);

            return parameter;
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

        _renderBody: function(unit) {
            const body = $('<div class="measurement">');

            const measurementInput = $('<div class="measurement-input">');
            const inputButtons = this._renderInputButtons();

            const unitText = $('<span class="measurement-unit">');
            $(unitText).text(unit);

            const value = $('<input class="measurement-value" type="number">');
            measurementInput.append(value);
            measurementInput.append(inputButtons);

            body.append(measurementInput);
            body.append(unitText);

            return body;
        },

        _renderInputButtons: function() {
            const container = $('<div class="measurement-input-buttons">');

            const switchText = $('<button class="measurement-input-switch measurement-input-switch-text">T</button>');
            const switchAbnormal = $('<button class="measurement-input-switch measurement-input-switch-abnormal">!</button>');

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
