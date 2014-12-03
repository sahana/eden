$(document).ready(function(){

    var stickyCountry = false;

    var _handlerClickCountry = function() {
        var country = $(this).attr('class');
        var stickyCountryPrev = stickyCountry;
        //Country Is Selected
        if (stickyCountry) {
            // Deselect current country
            stickyCountry = false;
            _handlerOutCountry();
        }
        // A new country is selected 
        if (country != stickyCountryPrev) {
            //Select this country
            stickyCountry = country;
            $( '.menus' ).css('background-color', '#99CCFF');
            $(this).css('background-color', '#99CCFF');
            $(this).css('height', '70px');
            _updateStats(stickyCountry.substring(8));
        }
    }

    var _handlerInCountry = function() {
        if (!stickyCountry) {
            $( '.menus' ).css('background-color', '#99CCFF');
            $(this).css('background-color', '#99CCFF');
            $(this).css('height', '70px');
            // Get data for country 
            _updateStats($(this).attr('class').substring(8));
        }
    }

    var _handlerOutCountry = function() {
        if (!stickyCountry) {
            $( '.menus, .country' ).css('background-color', '#66B2FF');
            $( '.country' ).css('height', '55px');
            // Get global data
            _updateStats('total');
        }
    }

    var _updateStats = function(code) {
        var resources = ['location',
                         'gis_location_L0',
                         'gis_location_L1',
                         'gis_location_L2',
                         'gis_location_L3',
                         'gis_location_L4',
                         'stats_demographic_data_L0',
                         'stats_demographic_data_L1',
                         'stats_demographic_data_L2',
                         'stats_demographic_data_L3',
                         'stats_demographic_data_L4',
                         'vulnerability_data_L0',
                         'vulnerability_data_L1',
                         'vulnerability_data_L2',
                         'vulnerability_data_L3',
                         'vulnerability_data_L4',
                         'event_event'
                         ];
        var len = resources.length,
            resource,
            value;
        for (var i=0; i < len; i++) {
            resource = resources[i];
            value = homepage_data[code][resource];
            if (value == undefined) {
                value = 0;
            }
            $('.badge.' + resource).html(value);
            $('.badge.' + resource).removeClass('throbber');
        }
    }

    _updateStats('total');
    $( '.country' ).click(_handlerClickCountry);
    $( '.country' ).hover( _handlerInCountry, _handlerOutCountry);
});