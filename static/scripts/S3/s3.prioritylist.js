/**
 * Used by the S3PriorityListWidget (modules/s3/s3widgets.py)
 * This script is in Static to allow caching
 * Dynamic constants (e.g. Internationalised strings) are set in server-generated script
 * 
 * @ToDo: minified version
 */

 (function( $ ) {

    var self;

    $.widget( 'ui.prioritylist', {
        options: {},

        _create: function() {
            self = this;
            var needsField = this.element;
            this.form = $(needsField).closest('form');
            self.element.hide();
            $('label[for="' + self.element.attr('id') + '"]').hide();

            // Wrap the prioritylist in a <div>
            var container = $('<div class="pl-container"></div>').insertAfter(this.element);

            // Add form elements for adding needs
            var addNeedWrap = $('<div id="need-wrap"></div>').appendTo(container);
            var newNeedLabel = $('<label id="new-need-label" for="new-need">Add need to list</lable>').appendTo(addNeedWrap);
            var newNeedBox = $('<input id="new-need" />').appendTo(addNeedWrap);
            var urgentButton = $('<input id="add-urgent" type="button" value="Need Urgently"/>').insertAfter(newNeedBox);
            var acceptingButton = $('<input id="add-accepting" type="button" value="Accepting"/>').insertAfter(urgentButton);
            var noNeedButton = $('<input id="add-no-need" type="button" value="Do Not Send"/>').insertAfter(acceptingButton);

            /* Convert the JSON string into a dict e.g.:
             * 
             * {"urgent": [ "pants", "shoes", "shovels" ],
             * "no": [ "blankets", "pasta" ],
             * "need": [ "AAA batteries", "twine", "peanut butter & jelly" ]}
             */

            var val = needsField.val();
            if (val) {
                try {
                    this.beginningNeeds = JSON.parse(val);
                } catch(err) {
                    s3_debug('Error parsing Needs');
                    this.beginningNeeds = {'urgent': [], 'need': [], 'no': []};
                }
            } else {
                this.beginningNeeds = {'urgent': [], 'need': [], 'no': []};
            }
            this.needs = jQuery.extend(true, {}, this.beginningNeeds);
            this.updatedNeeds = jQuery.extend(true, {}, this.needs);
            this.changedNeeds = {'urgent': [], 'need': [], 'no': []};

            // Define the labels for each category of needs
            var labels = { 'urgent': 'Urgent Need', 'need': 'Accepting More', 'no': 'No more needed' };

            // Cycle through each category and create a connectedSortable <ul> for each
            for (var key in labels) {
                var list_container = $('<div id="needs-sortable"></div>');
                container.append(list_container);
                list_container.append($('<label for="' + key + '">' + labels[key] + '</label>'));

                var list = $('<ul id="' + key + '" class="connectedSortable"></ul>');
                list_container.append(list);

                var category = this.needs[key];

                for (var i = 0; i < category.length; i++) {
                    list.append('<li><span>' + category[i] + '</span><a href="#" class="delete-need">x</a></li>');
                }
            }

            $( '.connectedSortable' ).sortable({
                connectWith: '.connectedSortable',
                items: 'li:not(.immobile)',
                receive: this._receive,
                remove: this._remove
            }).disableSelection();

            urgentButton.on('click', function() {
                self.addNeed( 'urgent' );
            });

            noNeedButton.on('click', function() {
                self.addNeed( 'no' );
            });
            
            acceptingButton.on('click', function() {
                self.addNeed( 'need' );
            });
            
            $('.delete-need').on('click', function() {
                self.deleteNeed( $(this).parent() );
            });
        },
        
        // Move a new item to the appropriate list
        addNeed: function( to ) {	
            var newNeed =  $('#new-need');
            var text = newNeed.val();
            var item = $('<li><span>' + text + '</span><a href="#" class="delete-need">x</a></li>');

            $('#' + to).append( item );
            self.moveNeed( item, null, to );
            newNeed.val('');
        },		
        
        // Update the JSON object of existing needs
        moveNeed: function( item, from, to ) {
            var itemText = item.children('span').text();

            if (from) {
                self._removeItem(self.changedNeeds[from], itemText);
                self._removeItem(self.updatedNeeds[from], itemText);
            }

            self.changedNeeds[to].push(itemText);
            self.updatedNeeds[to].push(itemText);

            self.updateForm();
        },	
        
        // Remove an item
        deleteNeed: function( item ) {	
            var itemText = item.children('span').text();
            var from = item.parent('ul').attr('id');

	    self._removeItem(self.changedNeeds[from], itemText);
            self._removeItem(self.updatedNeeds[from], itemText);
            item.remove();
            self.updateForm();
        },		

        updateForm: function() {
            // Update the JSON data in the hidden form element
            self.element.val(JSON.stringify(self.updatedNeeds));
        },

        // When a connectedSortable receives a new <li>, update the DB and the tweet box
        _receive: function( event, ui ) {
            var to = $( event.target ).attr('id');
            var from = $( ui.sender ).attr('id');

            self.moveNeed( $( ui.item ), from, to );
        },

        // Use the _setOption method to respond to changes to options
        _setOption: function( key, value ) {
            // In jQuery UI 1.8, you have to manually invoke the _setOption method from the base widget
            $.Widget.prototype._setOption.apply( this, arguments );
            // In jQuery UI 1.9 and above, you use the _super method instead
            this._super( '_setOption', key, value );
        },

	// Remove an item from an array
	_removeItem: function( anArray, item ) {
	    var i = 0;
            var L = anArray.length;

            while (i < L) {
		if(anArray[i] === item) {
		    anArray.splice(i);
		    return 1;
		}
		++i;
            }
            return -1;
	},

        // Use the destroy method to clean up any modifications your widget has made to the DOM
        destroy: function() {
            // In jQuery UI 1.8, you must invoke the destroy method from the base widget
            $.Widget.prototype.destroy.call( this );
            // In jQuery UI 1.9 and above, you would define _destroy instead of destroy and not call the base method
        }
    });
}( jQuery ) );