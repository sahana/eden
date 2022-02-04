/**
 *   S3LatLonWidget Static JS Code
 */

// Module pattern to hide internal vars
(function() {

    // Set up the lat_lon converter
    var nanError = i18n.gis_only_numbers,
        rangeError = i18n.gis_range_error;

    function isNum(n) {
        return !isNaN(parseFloat(n)) && isFinite(n);
    }

    function get_wrap(e) {
        return e.parents('.gis_coord_wrap').eq(0);
    }

    function set($e) {
        return function(v) {
            // clear and focus or set a field
            $e.val(v || '');
            if (typeof(v) == 'undefined') $e.trigger('focus');
        };
    }

    function get_dms(dec) {
        var d = Math.abs(dec),
            m = (d - parseInt(d, 10)) * 60;

        // Stop integer values of m from being approximated
        if (Math.abs(m - Math.round(m)) < 1e-10) {
            m = Math.round(m);
            s = 0;
        } else {
            var s = (m - parseInt(m, 10)) * 60;

            // Stop integer values of s from being approximated
            if (Math.abs(s - Math.round(s)) < 1e-10)
                s = Math.round(s);
        }

        return {d: parseInt(dec, 10),
                m: parseInt(m, 10),
                s: s
                };
    }

    function get_float(d, m, s) {
        return (d < 0 ? -1 : 1) * 
                (Math.abs(d) +
                 m / 60 +
                 s / 3600);
    }

    function to_decimal(wrap) {

        var d = $('.degrees', wrap).val() || 0,
            m = $('.minutes', wrap).val() || 0,
            s = $('.seconds', wrap).val() || 0,

            set_d = set($('.degrees', wrap)),
            set_m = set($('.minutes', wrap)),
            set_s = set($('.seconds', wrap)),
            set_dec = set($('.decimal', wrap)),

            isLat = $('.decimal', wrap).attr('id') == 'gis_location_lat';

        // validate degrees
        if (!isNum(d)) {
            alert(nanError.degrees);
            set_d();
            return;
        }

        d = Number(d);
        if (Math.abs(d) > (isLat ? 90 : 180)) {
            alert(rangeError.degrees[isLat? 'lat' : 'lon']);
            set_d();
            return;
        }

        // validate minutes
        if (!isNum(m)) {
            alert(nanError.minutes);
            set_m();
            return;
        }

        m = Math.abs(m);
        if (m > 60) {
            alert(rangeError.minutes);
            set_m();
            return;
        }

        // validate seconds
        if (!isNum(s)) {
            alert(nanError.seconds);
            set_s();
            return;
        }

        s = Math.abs(s);
        if (s >= 60) {
            alert(rangeError.seconds);
            set_s();
            return;
        }

        // Normalize all the values
        // Degrees and Minutes as integers
        var decimal = get_float(d, m, s);

        if (Math.abs(decimal) > (isLat ? 90 : 180)) {
            alert(rangeError.decimal[isLat? 'lat' : 'lon']);
            return;
        }

        var dms = get_dms(decimal);

        set_dec('' + decimal);
        set_d(dms.d || '0');
        set_m(dms.m || '0');
        set_s(dms.s || '0');
    }

    $('.gis_coord_dms input').blur(function() {
        to_decimal(get_wrap($(this)));
    }).keypress(function(e) {
        if (e.which == 13) e.preventDefault();
    });

    function to_dms(wrap) {
        var field = $('.decimal', wrap),
            dec = field.val(),
            isLat = $('.decimal', wrap).attr('id') == 'gis_location_lat';
        if (dec === '') return;
        if (!isNum(dec)) {
            alert(nanError.decimal);
            field.val('').trigger('focus');
            return;
        }
        dec = Number(dec);
        if (Math.abs(dec) > (isLat ? 90 : 180)) {
            alert(rangeError.decimal[isLat? 'lat' : 'lon']);
            field.trigger('focus');
            return;
        }
        var dms = get_dms(dec);
        $('.degrees', wrap).val(dms.d || '0');
        $('.minutes', wrap).val(dms.m || '0');
        $('.seconds', wrap).val(dms.s || '0');
    }

    /**
     * document-ready script
     */
    $(document).ready(function() {
        $('.gis_coord_decimal input').on('blur', function() {
            to_dms(get_wrap($(this)));
        }).keypress(function(e) {
            if (e.which == 13) e.preventDefault();
        });

        $('.gis_coord_switch_dms').on('click', function(evt) {
            $('.gis_coord_dms').show();
            $('.gis_coord_decimal').hide();
            $('.gis_coord_wrap').each(function() {
                to_dms($(this));
            });
            evt.preventDefault();
        });

        $('.gis_coord_switch_decimal').on('click', function(evt) {
            $('.gis_coord_decimal').show();
            $('.gis_coord_dms').hide();
            $('.gis_coord_wrap').each(function() {
                to_decimal($(this));
            });
            evt.preventDefault();
        });

        // Initially fill up the dms boxes
        $('.gis_coord_wrap').each(function() {
            to_dms($(this));
        });
    });

})(jQuery);

// END ========================================================================