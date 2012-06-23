/**
 * jQuery Form Extensions 1.0
 * http://code.google.com/p/jquery-form-extensions/
 *
 * Copyright (c) 2009 C.Small
 *
 * Licensed under the MIT license.
 * Date: 21:31 20/05/2009
 */
(function($)
{
	/* Checks if a jQuery object exists in the DOM, by checking the length of its child elements. */
	$.fn.elementExists = function()
	{
		///	<summary>
		///	Checks if a jQuery object exists in the DOM, by checking the length of its child elements.
		///	</summary>
		///	<returns type="Boolean" />
		return jQuery(this).length > 0;
	};
})(jQuery);


(function($)
{
	/* Retrieves the form field type based on its type attribute. */
	$.fn.formElementType = function()
	{
		///	<summary>
		///	Retrieves the form field type based on its type attribute.
		///	</summary>
		///	<returns type="String" />
		if (jQuery(this).elementExists())
			return jQuery(this).attr("type");
		else
			return "";
	};
})(jQuery);


(function($)
{
	/* Determines if the element is a textbox. */
	$.fn.isTextBox = function()
	{
		///	<summary>
		///	Determines if the element is a textbox.
		///	</summary>
		///	<returns type="Boolean" />
		return (jQuery(this).formElementType() === "text");
	};
})(jQuery);


(function($)
{
	/* Determines if the element is a textarea. */
	$.fn.isTextArea = function()
	{
		///	<summary>
		///	Determines if the element is a textarea.
		///	</summary>
		///	<returns type="Boolean" />
		return (jQuery(this).formElementType() === "textarea");
	};
})(jQuery);


(function($)
{
	/* Determines if the element is a password textbox. */
	$.fn.isPassword = function()
	{
		///	<summary>
		///	Determines if the element is a password textbox.
		///	</summary>
		///	<returns type="Boolean" />
		return (jQuery(this).formElementType() === "password");
	};
})(jQuery);


(function($)
{
	/* Determines if the element is a hidden input box. */
	$.fn.isHiddenInput = function()
	{
		///	<summary>
		///	Determines if the element is a hidden input box.
		///	</summary>
		///	<returns type="Boolean" />
		return (jQuery(this).formElementType() === "hidden");
	};
})(jQuery);


(function($)
{
	/* Determines if the element is a checkbox. */
	$.fn.isCheckBox = function()
	{
		///	<summary>
		///	Determines if the element is a checkbox.
		///	</summary>
		///	<returns type="Boolean" />
		return (jQuery(this).formElementType() === "checkbox");
	};
})(jQuery);


(function($)
{
	/* Determines if the element is a radiobox. */
	$.fn.isRadioBox = function()
	{
		///	<summary>
		///	Determines if the element is a radiobox.
		///	</summary>
		///	<returns type="Boolean" />
		return (jQuery(this).formElementType() === "radio");
	};
})(jQuery);


(function($)
{
	/* Determines if the element is a button (but not a submit or reset button). */
	$.fn.isButton = function()
	{
		///	<summary>
		///	Determines if the element is a button (but not a submit or reset button).
		///	</summary>
		///	<returns type="Boolean" />
		return (jQuery(this).formElementType() === "button");
	};
})(jQuery);


(function($)
{
	/* Determines if the element is a submit button. */
	$.fn.isSubmitButton = function()
	{
		///	<summary>
		///	Determines if the element is a submit button.
		///	</summary>
		///	<returns type="Boolean" />
		return (jQuery(this).formElementType() === "submit");
	};
})(jQuery);


(function($)
{
	/* Determines if the element is a reset button. */
	$.fn.isResetButton = function()
	{
		///	<summary>
		///	Determines if the element is a reset button.
		///	</summary>
		///	<returns type="Boolean" />
		return (jQuery(this).formElementType() === "reset");
	};
})(jQuery);


(function($)
{
	/* Determines if the element is a single selection 2 or more rows select box. */
	$.fn.isSelectBox = function()
	{
		///	<summary>
		///	Determines if the element is a single selection 2 or more rows select box.
		///	</summary>
		///	<returns type="Boolean" />
		
		var type = jQuery(this).formElementType();
		var size = (this).attr("size");
		
		if (type !== "select-one")
		{
			return false;
		}
		else
		{
			if (typeof size === "undefined")
				return false;
			else
				return (parseInt(size) > 1);
		}
	};
})(jQuery);


(function($)
{
	/* Determines if the element is a multi selection select box. */
	$.fn.isMultiSelectBox = function()
	{
		///	<summary>
		///	Determines if the element is a multi selection select box. 
		///	</summary>
		///	<returns type="Boolean" />
		return (jQuery(this).formElementType() === "select-multiple");
	};
})(jQuery);


(function($)
{
	/* Determines if the element is a drop down list, that is a select box with 1 row and items appear when clicked, rather
	   than just a scrollbar. */
	$.fn.isDropDownList = function()
	{
		///	<summary>
		///	Determines if the element is a drop down list, that is a select box with 1 row and items appear when clicked, rather than just a scrollbar.
		///	</summary>
		///	<returns type="Boolean" />
		var type = jQuery(this).formElementType();
		var size = (this).attr("size");
		
		if (type !== "select-one")
		{
			return false;
		}
		else
		{
			if (typeof size === "undefined")
				return true;
			else
				return (parseInt(size) <= 1);
		}
	};
})(jQuery);


(function($)
{
	/* Determines if the element is checked. The pre-condition for this is the element is a checkbox. */
	$.fn.isChecked = function()
	{
		///	<summary>
		///	Determines if the element is checked. The pre-condition for this is the element is a checkbox.
		///	</summary>
		///	<returns type="Boolean" />
		var current = jQuery(this);
		return current.is(":checked");
	};
})(jQuery);


(function($)
{
	/* Determines if the list of provided values are selected. The pre-condition for this is the element is a select box. 
	   This performs an 'AND' search - all the values must be selected for the function to return true.
	   Example: $("#element").isSelected("1","2");
	   @param arguments A list of values to see if they are selected.
	*/
	$.fn.isSelected = function()
	{
		///	<summary>
        ///	Determines if the list of provided values are selected. The pre-condition for this is the element is a select box. 
		/// This performs an 'AND' search - all the values must be selected for the function to return true.
        ///	</summary>
        ///	<param name="args" type="Array">A list of values to see if they are selected.</param>
        ///	<returns type="Boolean" />
		var current = jQuery(this);
		
		if (arguments.length === 0)
		{
			return false; // throw?
		}
			
		var result = false;
		var compareTo = arguments[0];
		var argumentsIn = arguments; // copy for scope inside the jQuery.each

		if (current.isRadioBox())
		{
			var selected = jQuery("input[type='radio'][name='" + current.attr("name") + "'][checked]");
			if (selected.length === 1)
				return (compareTo === selected.val());
		}
		else if (current.isSelectBox() || current.isDropDownList())
		{
			var selected = jQuery("#" + current.attr("id") + " option:selected");
			if (selected.length === 1)
				return (compareTo === selected.val());
		}
		else if (current.isMultiSelectBox())
		{
			var selected = jQuery("#" + current.attr("id") + " option:selected");
			
			jQuery.each(selected, function()
			{
				var option = jQuery(this);
				result = false;
				
				// This is an AND operation
				for (var i = 0; i < argumentsIn.length; i++)
				{
					if (argumentsIn[i] === option.val())
					{
						result = true;
						break;
					}
				}
			});
		}

		return result;
	};
})(jQuery);


(function($)
{
	/**
       Retrieves the Nth selected item from a radiobox or select box list. If N is greater than the number of selected items
	   then the last item is returned.
	   Example: $("#element").selectedItem(2); // the 3rd selected item.
	   @param index The selected index to retrieve, this is zero based. 
	*/
	$.fn.selectedItem = function(index)
	{
		///	<summary>
        ///	Retrieves the Nth selected item from a radiobox or select box list. If N is greater than the number of selected items
		/// then the last item is returned.
		/// Example: $("#element").selectedItem(2); // the 3rd selected item.
        ///	</summary>
        ///	<param name="index" type="Number"> The selected index to retrieve, this is zero based. </param>
        ///	<returns type="jQuery" />
		var current = jQuery(this);
		if (typeof index === "undefined" || isNaN(index))
			index = 0;
		
		if (current.isRadioBox())
		{
			var selected = jQuery("input[type='radio'][name='" +current.attr("name")+ "'][checked]");
			if (index > selected.length -1)
				index = selected.length -1;
			else if (index < 0)
				index = 0;
			
			if (selected.length > 0)
				return jQuery(selected[index]);
		}
		else if (current.isSelectBox() || current.isMultiSelectBox() || current.isDropDownList())
		{
			var selected = jQuery("#" +current.attr("id")+ " option:selected");
			if (index > selected.length -1)
				index = selected.length -1;
			else if (index< 0)
				index = 0;
				
			if (selected.length > 0)
				return jQuery(selected[index]);
		}
		
		return current; // is this the proper behaviour?
	};
})(jQuery);


(function($)
{
	/* Gets the first selected item from a radiobox list or select box list.
	   @returns A jQuery object.
	*/
	$.fn.firstSelectedItem = function()
	{
		///	<summary>
        ///	Gets the first selected item from a radiobox list or select box list.
        ///	</summary>
        ///	<returns type="jQuery" />
		return jQuery(this).selectedItem();
	};
})(jQuery);


(function($)
{
	/* Gets the last selected item from a radiobox list or select box list.
	   @returns A jQuery object.
	*/
	$.fn.lastSelectedItem = function()
	{
		///	<summary>
        ///	Gets the last selected item from a radiobox list or select box list.
        ///	</summary>
        ///	<returns type="jQuery" />
		return jQuery(this).selectedItem(Number.MAX_VALUE); // can assume there's not 2^32 options
	};
})(jQuery);


(function($)
{
	/* Gets the value of the first selected item in a radiobox list or select box list.
	   @returns A string value for the selected item.
	*/
	$.fn.selectedValue = function()
	{
		///	<summary>
        ///	Gets the value of the first selected item in a radiobox list or select box list.
        ///	</summary>
        ///	<returns type="String" />
		var current = jQuery(this);		
		return current.selectedItem(0).val();
	};
})(jQuery);


(function($)
{
	/* Gets the values of the all selected items in multiple selection select box list.
	   @returns An array of string values for all selected items.
	*/
	$.fn.selectedValues = function()
	{
		///	<summary>
        ///	Gets the values of the all selected items in multiple selection select box list.
        ///	</summary>
        ///	<returns type="Array" />
		var results = [];
		var current = jQuery(this);

		if (current.isMultiSelectBox())
		{
			var selected = jQuery("#" + current.attr("id") + " option:selected");
			jQuery.each(selected, function()
			{
				results.push(jQuery(this).val());
			});
		}
		else
		{
			// Not the most efficient way of doing this
			results.push(current.selectedValue());
		}

		return results;
	};
})(jQuery);

/* 
	
*/
(function($)
{
	/* Determines if the provided item exists as a value in a radiobox or select box list
	   @param item The value to check.
	*/
	$.fn.itemExists = function(item)
	{
		///	<summary>
        ///	Determines if the provided item exists as a value in a radiobox or select box list
        ///	</summary>
        ///	<param name="item" type="String">The value to check</param>
        ///	<returns type="Boolean" />
		
		var current = jQuery(this);
		var result = false;
		
		if (current.isRadioBox())
		{
			var selected = jQuery("input[type='radio'][name='" +current.attr("name")+ "'][value='" +item+"']");
			result = (selected.length === 1);
		}
		else if (current.isSelectBox() || current.isMultiSelectBox() || current.isDropDownList())
		{
			var items = jQuery("#" +current.attr("id")+" option");
			jQuery.each(items, function()
			{
				if (jQuery(this).val() === item)
				{
					result = true;
					return false;
				}
			});
		}
		else
		{
			return (jQuery(this).val() === item);
		}
		
		return result;
	};
})(jQuery);

/* 
Used for debugging	

(function($)
{
	$.fn.log = function()
	{
		if (typeof console !== "undefined")
		{
			var str = "";
			for (var i = 0; i < arguments.length; i++)
				str += arguments[i];
				
			console.log(str);
		}
	};
})(jQuery);

*/