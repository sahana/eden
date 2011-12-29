// S3.checkboxes.widget.js

// JS function which is used by the S3CheckboxesWidget
// @author: Michael Howden (michael@aidiq.com)
// @date: 2010-05-18

jQuery(document).ready(function() {    
    jQuery(".s3_checkbox_label").cluetip({activation: "hover",  
                                          positionBy: "auto",
                                          local: true,
                                          hideLocal: false,
                                          showTitle: false, 
                                          topOffset: 0,
                                          mouseOutClose: true,
                                          arrows: true, 
                                          clickThrough:true//,           
                                         });
});      