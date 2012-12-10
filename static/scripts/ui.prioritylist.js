(function( $ ) {

	var self;

    $.widget( "ui.prioritylist", {
	options: { 
	    
	},
	
	_create: function() {
		self = this;
	    var needsField = this.element;
	    var form = $(needsField).closest('form');
	    form.children().hide(':input');
	    
	    // Wrap the prioritylist in a <div>
	    var container = $('<div class="pl-container"></div>').appendTo(form);
	    
	    // Add form elements for adding needs
	    var addNeedWrap = $('<div id="need-wrap"></div>').appendTo(container);
	    var newNeedBox = $('<input id="new-need" />').appendTo(addNeedWrap);
	    var needButton = $('<input id="add-need" type="button" value="Need"/>').insertAfter(newNeedBox);
	    var acceptingButton = $('<input id="add-accepting" type="button" value="Accepting"/>').insertAfter(needButton);
	    var noNeedButton = $('<input id="add-no-need" type="button" value="Do Not Send"/>').insertAfter(acceptingButton);	 	    
	    
	    /* Convert the JSON string into a dict e.g.:
	     * 
	     * {"need": [ "pants", "shoes", "shovels" ],
	     * "no_need": [ "blankets", "pasta" ],
	     * "accepting": [ "AAA batteries", "twine", "peanut butter & jelly" ]}
	     */
	     
	    this.beginningNeeds = JSON.parse(needsField.val());
	    this.needs = jQuery.extend(true, {}, this.beginningNeeds);	 
		this.updatedNeeds = jQuery.extend(true, {}, this.needs);
		this.changedNeeds = {'need': [], 'accepting': [], 'no_need': []};	    
		    
		// Define the labels for each category of needs
	    var labels = { 'need': 'Urgent Need', 'accepting': 'Accepting More', 'no_need': 'No more needed' };

		// Cycle through each category and create a connectedSortable <ul> for each
	    for (var key in labels) {
			var list_container = $('<div id="needs-sortable"></div>');
			container.append(list_container);
			list_container.append($('<label for="' + key + '">' + labels[key] + '</label>'));
			var list = $('<ul id="' + key + '" class="connectedSortable"></ul>');
			list_container.append(list);
			var category = this.needs[key];

			for (var i = 0; i < category.length; i++) {
			    list.append('<li>' + category[i] + '</li>');
			}
	    }
	    
	    // Add form elements for sending tweets
	    var tweetWrap = $('<div class="tweet-box"></div>').appendTo(container);
	    var tweetCheck = $('<input type="checkbox" id="tweet-changes" /> tweet changes to:').appendTo(tweetWrap);
	    var tweetLabel = $('<label id="tweet-label">tweet changes to:</label>').appendTo(tweetWrap);
	    var tweetBox = $('<textarea id="tweet-box" disabled></textarea>').appendTo(tweetWrap);
	    var tweetButton = $('<input type="button" id="tweet-button" value="Send" disabled/>').insertAfter(tweetBox);	    	    

        $( ".connectedSortable" ).sortable({
			connectWith: ".connectedSortable",
			items: "li:not(.immobile)",
			receive: this._receive,
			remove: this._remove
        }).disableSelection();

        needButton.click(function() {
        	self.addNeed( 'need' );
        });
        
        noNeedButton.click(function() {
			self.addNeed( 'no-need' );
        });
        
        acceptingButton.click(function() {
			self.addNeed( 'accepting' );
        });
        
        $('#tweet-changes').change(function() {
        	if ( $(this).attr("checked") == "checked" ) {
				$('#tweet-box').removeAttr('disabled')
				$('#tweet-button').removeAttr('disabled');
			} else {        
				$('#tweet-box').attr("disabled","disabled");
				$('#tweet-button').attr("disabled","disabled");
			}
		});
		
	    this.refresh();
	},

	refresh: function() {

	},	
	
	// Move a new item to the appropriate list
	addNeed: function( to ) {	
		var newNeed =  $('#new-need')
		var text = newNeed.val();
		var item = $('<li>' + text + '</li>')
		$('#' + to).append( item );
		self.moveNeed( text, null, to );
		self.updateTweet(to);
		newNeed.val('');
	},		
	
	// Update the JSON object of existing needs
	moveNeed: function( item, from, to ) {
		if(from) {	
			self.changedNeeds[from].remove(item);
			self.updatedNeeds[from].remove(item);
		}
		self.changedNeeds[to].push(item);
		self.updatedNeeds[to].push(item);
		
		/*
		$.ajax({
	        type: 'POST',
	        url: '',
	        data: { 'req_site_needs_needs': JSON.stringify(self.updatedNeeds) }
	    }).done(function(data) {
			alert(data);
	    }).fail(function() {
	        alert('error');
	    });
	    */
		
	},	
	
	updateTweet: function( to ) {
		var newItemString = "";
		
		// Build a string of new items in this category
		for (var i = 0; i < self.changedNeeds[to].length; i++) {
			newItemString += self.changedNeeds[to][i];
		
			if( self.changedNeeds[to].length > 1) {
				if( i == self.changedNeeds[to].length - 2 ) {
					newItemString += " and ";
				} else if ( i < self.changedNeeds[to].length - 1 ) {
					newItemString += ", "; 
				}
			}
		}
	
		var tweetBox = $('#tweet-box');
		switch(to) {			
	    	case "need":
				tweetBox.val('We are in urgent need of ' + newItemString);
				break;
	    	case "no_need":
				tweetBox.val('We have plenty of ' + newItemString);
				break;
	    }		
	},

	// When a connectedSortable receives a new <li>, update the DB and the tweet box
	_receive: function( event, ui ) {
	    var to = $( event.target ).attr("id");
		var from = $( ui.sender ).attr("id");

		self.moveNeed( $( ui.item ).text() , from, to );
	    self.updateTweet(to);
	},

	_remove: function( event, ui ) {
	    console.log( $( event.target ).val() );
	},

	// Use the _setOption method to respond to changes to options

	_setOption: function( key, value ) {
	    // In jQuery UI 1.8, you have to manually invoke the _setOption method from the base widget
	    $.Widget.prototype._setOption.apply( this, arguments );
	    // In jQuery UI 1.9 and above, you use the _super method instead
	    this._super( "_setOption", key, value );
	},
	
	// Use the destroy method to clean up any modifications your widget has made to the DOM

	destroy: function() {
	    // In jQuery UI 1.8, you must invoke the destroy method from the base widget
	    $.Widget.prototype.destroy.call( this );
	    // In jQuery UI 1.9 and above, you would define _destroy instead of destroy and not call the base method
	}

    });


}( jQuery ) );

if(!Array.prototype.indexOf) {
    Array.prototype.indexOf = function(what, i) {
        i = i || 0;
        var L = this.length;
        while (i < L) {
            if(this[i] === what) return i;
            ++i;
        }
        return -1;
    };
}

Array.prototype.remove = function() {
    var what, a = arguments, L = a.length, ax;
    while (L && this.length) {
        what = a[--L];
        while ((ax = this.indexOf(what)) !== -1) {
            this.splice(ax, 1);
        }
    }
    return this;
};