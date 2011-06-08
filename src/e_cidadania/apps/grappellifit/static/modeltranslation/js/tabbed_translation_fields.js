(function ($) {
    $(function() {
        $.modeltranslation = (function() {
            var mt = {
                options: {
                    fieldTypes: 'input[type=text], input[type=file], textarea',
                },

                init: function(opts) {
                    this.options = $.extend(this.options, opts)

                    if ($('body').hasClass('change-form')) {
                        var fields = this._getTranslatedFields()
                        var tabs = this._createInlineTabs()
                        this._createMainSwitch(tabs, fields)
                        var $self = this
                        $('.add-item .add-handler').bind('click.modeltranslation', function(){
                            var group = $(this).parents('.group')
                            setTimeout(function(){
                                $self._createInlineTabs(group.find('.items > .module:last').prev())
                            }, 200)
                        })
                    }
                    else if ($('body').hasClass('change-list')) {
                        var tabs = this._createChangelistTabs()
                    }
                },

                // Inserts a select box to select language globally
                _createMainSwitch: function(tabs, fields) {
                    var grouped_translations = fields,
                      unique_languages = [],
                      select = $('<select>');
                    $.each(grouped_translations, function (name, languages) {
                        $.each(languages, function (lang, el) {
                            if ($.inArray(lang, unique_languages) < 0) {
                                unique_languages.push(lang);
                            }
                        });
                    });
                    $.each(unique_languages, function (i, language) {
                        select.append($('<option value="' + i + '">' + language + '</option>'));
                    });
                    select.change(function (e) {
                        $.each(tabs, function (i, tab) {
                            tab.tabs('select', parseInt(select.val()));
                        });
                    });
                    $('#content h1').append('&nbsp;').append(select);
                },

                // Create change list tabbing
                _createChangelistTabs: function() {
                    var translations = this._getTranslatedFields()
                    var tabs = []
                    var container = $('<div class="modeltranslation-switcher-container ui-tabs ui-widget ui-widget-content ui-corner-all"></div>').css('margin-bottom', 6)
                    var tabs = $('<ul class="modeltranslation-switcher ui-tabs-nav ui-helper-reset ui-helper-clearfix ui-widget-header ui-corner-all"></ul>').appendTo(container)
                    $.each(this.options.languages, function(i, lang) {
                        $('<li class="required ui-state-default ui-corner-top"><a></a></li>')
                            .css({float: 'left'}).appendTo(tabs)
                            .find('a').bind('click.modeltranslation', function(){
                                var l = $(this).attr('href').replace('#', '')
                                $('.translated-field:not(.translation-'+ l +')').hide()
                                $('.translation-'+ l).show()
                                $(this).parent().addClass('ui-tabs-selected').siblings().removeClass('ui-tabs-selected')
                            }).attr('href', '#'+lang).text(lang)
                    })

                    // Insert toolbar only if there is translated fields
                    if (tabs.find('li').length) {
                        // Tweak table header
                        $('.changelist-results').find('thead th').each(function(i, t){
                            var th    = $(t)
                            var label = $.trim(th.find('a').text())
                            if (/\[\w{2}\]/.test(label)) {
                                match = label.match(/\[(\w{2})\]/)
                                if (match.length > 1) {
                                    th.addClass('translated-field translation-'+ match[1])
                                        .find('a').text(label.replace(/\ \[.+\]/, ''))
                                }
                            }
                        })

                        // Tweak rows
                        var fields = $('.modeltranslation')
                            .filter(this.options.fieldTypes).each(function(i, f){
                                var field = $(f)
                                $(f).parent().addClass('translated-field translation-'+ $(f).attr('id').slice(-2))
                            })

                        // hide innactive translations
                        $('.translated-field:not(.translation-'+ this.options.languages[0] +')').hide()

                        tabs.find('li:first').addClass('ui-tabs-selected')
                        return container.insertBefore('#changelist-form')
                    }
                },

                // Create change form tabbing
                _createInlineTabs: function(p) {
                    var translations = this._getTranslatedFields(p)
                    var tabs = []
                    $.each(translations, function (name, languages) {
                        var tabs_container = $('<div class="modeltranslation-switcher-container"></div>'),
                          tabs_list = $('<ul class="modeltranslation-switcher"></ul>'),
                          insertion_point;
                        tabs_container.append(tabs_list);
                        $.each(languages, function (lang, el) {
                            var container = $(el).closest('.row'),
                              label = $('label', container),
                              field_label = container.find('label'),
                              id = 'tab_' + [name, lang].join('_'),
                              panel, tab;
                            // Remove language and brackets from field label, they are
                            // displayed in the tab already.
                            if (field_label.html()) {
                                field_label.html(field_label.html().replace(/\ \[.+\]/, ''));
                            }
                            if (!insertion_point) {
                                insertion_point = {
                                    'insert': container.prev().length ? 'after' : container.next().length ? 'prepend' : 'append',
                                    'el': container.prev().length ? container.prev() : container.parent()
                                };
                            }
                            container.find('script').remove();
                            panel = $('<div id="' + id + '"></div>').append(container);
                            tab = $('<li' + (label.hasClass('required') ? ' class="required"' : '') + '><a href="#' + id + '">' + lang + '</a></li>');
                            tabs_list.append(tab);
                            tabs_container.append(panel);
                        });
                        insertion_point.el[insertion_point.insert](tabs_container);
                        tabs_container.tabs();
                        tabs.push(tabs_container);
                    });
                    return tabs;
                },
                
                _getTranslatedFields: function(p) {
                    /** Returns a grouped set of all text based model translation fields.
                     * The returned datastructure will look something like this:
                     * {
                     *   'title': {
                     *     'en': HTMLInputElement,
                     *     'fr': HTMLInputElement
                     *   },
                     *   'body': {
                     *     'en': HTMLTextAreaElement,
                     *     'fr': HTMLTextAreaElement
                     *   }
                     * }
                     */
                    if (p) {
                        var fields = $(p).find('.modeltranslation').filter(this.options.fieldTypes)
                    }
                    else {
                        var fields = $('.modeltranslation').filter(this.options.fieldTypes)
                    }
                    var out    = {}
                    var langs  = []
                    //onAfterAdded
                    
                    fields.each(function (i, el) {
                        var name = $(el).attr('name').split('_')
                        var lang = name.pop()
                        name = name.join('_')
                        langs.push(lang)
                        if (!/__prefix__/.test(name)) {
                            if (!out[name]) { out[name] = {} }
                            out[name][lang] = el
                        }
                    })
                    this.options.languages = $.unique(langs.sort())
                    return out
                }
            }
            return mt
        }())
        $.modeltranslation.init()
    })
}(django.jQuery || jQuery || $))
