// Module pattern to hide internal vars
(function() {
    // Module scope
    var map;

    function is_fullscreen() {
        return document.fullscreen || document.mozFullScreen || document.webkitIsFullScreen;
    }

    function enable_fullscreen(map) {
        // Remove map elements
        var s3 = map.s3;
        s3.westPanelContainer.removeAll(false);
        s3.mapPanelContainer.removeAll(false);
        var mapWin = s3.mapWin;
        mapWin.items.items = [];
        mapWin.doLayout();
        mapWin.destroy();
        // Add Window
        S3.gis.addMapWindow(map);
        // Request browser to go full-screen
        if (document.body.requestFullScreen) {
            document.body.requestFullScreen();
        } else if (document.body.webkitRequestFullScreen) {
            document.body.webkitRequestFullScreen();
        } else if (document.body.mozRequestFullScreen) {
            document.body.mozRequestFullScreen();
        }
        // Modify the CSS for the Legend Panel & Save Panel
        var map_id = s3.id;
        $('#' + map_id).addClass('fullscreen');
    }

    function disable_fullscreen(map) {
        // Remove map elements
        var s3 = map.s3;
        s3.westPanelContainer.removeAll(false);
        s3.mapPanelContainer.removeAll(false);
        var mapWin = s3.mapWin;
        mapWin.items.items = [];
        mapWin.doLayout();
        mapWin.destroy();
        // Add embedded Panel
        S3.gis.addMapPanel(map);
        // Modify the CSS for the Legend Panel & Save Panel
        var map_id = s3.id;
        $('#' + map_id).removeClass('fullscreen');
    }

    $('.gis_fullscreen_map-btn').on('click', function(evt) {
        if (navigator.appVersion.indexOf('MSIE') != -1) {
            // Not supported on IE => do full-page reload instead
            return;
        } else {
            // Read map_id from the Button to determine which Map to make fullscreen
            var map_id;
            var attributes = this.attributes;
            for (var i=0; i < attributes.length; i++) {
                if (attributes[i].name == 'map') {
                    map_id = attributes[i].value;
                    break;
                }
            }
            if (undefined == map_id) {
                map_id = 'default_map';
            }
            map = S3.gis.maps[map_id];
            enable_fullscreen(map);
            evt.preventDefault();
        }
    });

    $('body').on('webkitfullscreenchange', function() {
        if (!is_fullscreen())
            disable_fullscreen(map);
    });

    $(document).on('mozfullscreenchange', function() {
        if (!is_fullscreen())
            disable_fullscreen(map);
    });

    $('body').on('webkitfullscreenchange', function() {
        if (!is_fullscreen())
            disable_fullscreen(map);
    });
}());