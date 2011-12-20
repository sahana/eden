// Create user extensions namespace (Ext.ux)
Ext.namespace('Ext.ux');

/**
  * Ext.ux.PasswordMeter Extension Class
  *
  * @author  Eelco Wiersma
  * @version 0.2
  * 
  * Algorithm based on code of Tane
  * http://digitalspaghetti.me.uk/index.php?q=jquery-pstrength
  * and Steve Moitozo
  * http://www.geekwisdom.com/dyn/passwdmeter
  * 
  * @license MIT License: http://www.opensource.org/licenses/mit-license.php
  * 
  * @class Ext.ux.PasswordMeter
  * @extends Ext.form.TextField
  * @constructor
  * Creates new Ext.ux.PasswordMeter
  */
Ext.ux.PasswordMeter = function(config) {

	// call parent constructor
	Ext.ux.PasswordMeter.superclass.constructor.call(this, config);

};

Ext.extend(Ext.ux.PasswordMeter, Ext.form.TextField, {
	    /**
	     * @cfg {String} inputType The type attribute for input fields -- e.g. text, password (defaults to "password").
	     */
		inputType: 'text',
		// private
		onRender: function(ct, position) {
			Ext.ux.PasswordMeter.superclass.onRender.call(this, ct, position);
			
			var elp = this.el.findParent('.x-form-element', 5, true);
			this.objMeter = ct.createChild({tag: "div", 'class': "strengthMeter"});

			this.objMeter.setWidth(elp.getWidth(true)-17);
			this.scoreBar = this.objMeter.createChild({tag: "div", 'class': "scoreBar"});
			
			if(Ext.isIE && !Ext.isIE7) { // Fix style for IE6
				this.objMeter.setStyle('margin-left', '3px');
			}
		},
		// private
		initEvents: function() {
			Ext.ux.PasswordMeter.superclass.initEvents.call(this);
			
			this.el.on('keyup', this.updateMeter, this);
		},
		/**
		 * Sets the width of the meter, based on the score
		 * @param {Object} e 
		 * Private function
		 */
		updateMeter: function(e) {
			var score = 0 
		    var p = e.target.value;
			
			var maxWidth = this.objMeter.getWidth() - 2;
			
			var nScore = this.calcStrength(p);
			
    		// Set new width
    		var nRound = Math.round(nScore * 2);

			if (nRound > 100) {
				nRound = 100;
			}

			var scoreWidth = (maxWidth / 100) * nRound;
			this.scoreBar.setWidth(scoreWidth, true);
		},
		/**
		 * Calculates the strength of a password
		 * @param {Object} p The password that needs to be calculated
		 * @return {int} intScore The strength score of the password
		 */
		calcStrength: function(p) {
			var intScore = 0;

			// PASSWORD LENGTH
			intScore += p.length;
			
			if(p.length > 0 && p.length <= 4) {                    // length 4 or less
				intScore += p.length;
			}
			else if (p.length >= 5 && p.length <= 7) {	// length between 5 and 7
				intScore += 6;
			}
			else if (p.length >= 8 && p.length <= 15) {	// length between 8 and 15
				intScore += 12;
				//alert(intScore);
			}
			else if (p.length >= 16) {               // length 16 or more
				intScore += 18;
				//alert(intScore);
			}
			
			// LETTERS (Not exactly implemented as dictacted above because of my limited understanding of Regex)
			if (p.match(/[a-z]/)) {              // [verified] at least one lower case letter
				intScore += 1;
			}
			if (p.match(/[A-Z]/)) {              // [verified] at least one upper case letter
				intScore += 5;
			}
			// NUMBERS
			if (p.match(/\d/)) {             	// [verified] at least one number
				intScore += 5;
			}
			if (p.match(/.*\d.*\d.*\d/)) {            // [verified] at least three numbers
				intScore += 5;
			}
			
			// SPECIAL CHAR
			if (p.match(/[!,@,#,$,%,^,&,*,?,_,~]/)) {           // [verified] at least one special character
				intScore += 5;
			}
			// [verified] at least two special characters
			if (p.match(/.*[!,@,#,$,%,^,&,*,?,_,~].*[!,@,#,$,%,^,&,*,?,_,~]/)) {
				intScore += 5;
			}
			
			// COMBOS
			if (p.match(/(?=.*[a-z])(?=.*[A-Z])/)) {        // [verified] both upper and lower case
				intScore += 2;
			}
			if (p.match(/(?=.*\d)(?=.*[a-z])(?=.*[A-Z])/)) { // [verified] both letters and numbers
				intScore += 2;
			}
	 		// [verified] letters, numbers, and special characters
			if (p.match(/(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[!,@,#,$,%,^,&,*,?,_,~])/)) {
				intScore += 2;
			}

			return intScore;
		
		},
		// private
		onFocus: function() {
			Ext.ux.PasswordMeter.superclass.onFocus.call(this);
			
        	if(!Ext.isOpera) { // don't touch in Opera
            	this.objMeter.addClass('strengthMeter-focus');
       		}
		},
		// private
		onBlur: function() {
			Ext.ux.PasswordMeter.superclass.onBlur.call(this);
			
        	if(!Ext.isOpera) { // don't touch in Opera
            	this.objMeter.removeClass('strengthMeter-focus');
       		}
		}
});