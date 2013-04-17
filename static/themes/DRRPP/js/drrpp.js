/* Custom JS for DRRPPP Template */

$(document).ready(function(){
    var selCountry = $('#sub_defaultlocation_defaultlocation_i_location_id_edit_none');

    function ToggleCookIslandFields() {
        var CountriesInline = $('#project_project_sub_defaultlocation__row_widget tr.read-row td').length / 3;
        var CookIslandsInline = $('#project_project_sub_defaultlocation__row_widget tr.read-row td:contains("Cook Islands")').length;
        var Show;
        if ( (CountriesInline == 1 && CookIslandsInline == 1) || 
              (CountriesInline == 0 && selCountry.children('option:selected').text() == 'Cook Islands')
              ) {
            // Cook Islands only country selected
            Show = true; 
        } else {
            Show = false;
        }
        if (Show) {
            $('#project_project_sub_drrpp_L1__row_label').show();
            $('#project_project_sub_drrpp_L1__row_widget').show();
            $('#project_project_sub_drrpp_L1__row_comment').show();
            $('#project_project_drrpp_pifacc__subheading').show();
            $('#project_project_sub_drrpp_pifacc__row_label').show();
            $('#project_project_sub_drrpp_pifacc__row_widget').show();
            $('#project_project_sub_drrpp_pifacc__row_comment').show();
            $('#project_project_drrpp_jnap__row_subheading').show();
            $('#project_project_sub_drrpp_jnap__row_label').show();
            $('#project_project_sub_drrpp_jnap__row_widget').show();
            $('#project_project_sub_drrpp_jnap__row_comment').show();
        } else {
            $('.edit #project_project_sub_drrpp_L1__row_label').hide();
            $('.edit #project_project_sub_drrpp_L1__row_widget').hide();
            $('.edit #project_project_sub_drrpp_L1__row_comment').hide();
            $('.edit #project_project_drrpp_pifacc__subheading').hide();
            $('.edit #project_project_sub_drrpp_pifacc__row_label').hide();
            $('.edit #project_project_sub_drrpp_pifacc__row_widget').hide();
            $('.edit #project_project_sub_drrpp_pifacc__row_comment').hide();
            $('.edit #project_project_drrpp_jnap__subheading').hide();
            $('.edit #project_project_sub_drrpp_jnap__row_label').hide();
            $('.edit #project_project_sub_drrpp_jnap__row_widget').hide();
            $('.edit #project_project_sub_drrpp_jnap__row_comment').hide();
        };
    }

    // Show the Cook Islands fields if this option is selected
    selCountry.change(ToggleCookIslandFields);

    // Shortcut to remove the Cook Islands fields if the .inline-rmv doesn't bubble
    selCountry.click(ToggleCookIslandFields);

    $('.inline-rmv').click(ToggleCookIslandFields);
    $('.inline-add').click(ToggleCookIslandFields);

    // Show fields if Cook Islands are already selected
    ToggleCookIslandFields();
});
