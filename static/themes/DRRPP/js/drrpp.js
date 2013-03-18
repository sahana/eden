/* Custom JS for DRRPPP Template */

$(document).ready(function(){
    // If no Cook Islands are checked, then check them all
    // NOT WANTED
    //if( $('[name=sub_drrpp_L1]').is(':checked')==false) {
    //    $('[name=sub_drrpp_L1]').attr('checked','checked')
    //}
    
    var selCountry = $('#sub_defaultlocation_defaultlocation_i_location_id_edit_none');
    var CookIslandsInline = '#project_project_sub_defaultlocation__row tr.read-row td:contains("Cook Islands")';
        
    function ToggleCookIslandFields() {
        var Show;
        if ($(CookIslandsInline).length < 1) {
            // Cook Islands not in list - show/hide based on select option
            Show = selCountry.children('option:selected').text() == 'Cook Islands';
        } else {
            Show = true; 
        }
        if (Show) {
            $('#project_project_sub_drrpp_L1__row1').show();
            $('#project_project_sub_drrpp_L1__row').show();
            $('#project_project_drrpp_pifacc__subheading').show();
            $('#project_project_sub_drrpp_pifacc__row1').show();
            $('#project_project_sub_drrpp_pifacc__row').show();
            $('#project_project_drrpp_jnap__subheading').show();
            $('#project_project_sub_drrpp_jnap__row1').show();
            $('#project_project_sub_drrpp_jnap__row').show();
        } else {
            $('#project_project_sub_drrpp_L1__row1').hide();
            $('#project_project_sub_drrpp_L1__row').hide();
            $('#project_project_drrpp_pifacc__subheading').hide();
            $('#project_project_sub_drrpp_pifacc__row1').hide();
            $('#project_project_sub_drrpp_pifacc__row').hide();
            $('#project_project_drrpp_jnap__subheading').hide();
            $('#project_project_sub_drrpp_jnap__row1').hide();
            $('#project_project_sub_drrpp_jnap__row').hide();
        };
    }
    
    // Show the Cook Islands fields if this option is selected
    selCountry.change(ToggleCookIslandFields);
    
    // Shortcut to remove the Cook Islands fields if the .inline-rmv doesn't bubble
    selCountry.click(ToggleCookIslandFields);
    
    $('.inline-rmv').click(function() {
        // Check if the Cook Islands item has been removed
        ToggleCookIslandFields();
    });
    // Show fields if Cook Islands are already selected
    ToggleCookIslandFields();
});
