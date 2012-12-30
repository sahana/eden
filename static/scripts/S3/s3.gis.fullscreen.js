$(function() {
    function is_fullscreen() {
        return document.fullscreen || document.mozFullScreen || document.webkitIsFullScreen;
    }

    function enable_fullscreen() {
        // Remove map elements
        S3.gis.mapWestPanelContainer.removeAll(false);
        S3.gis.mapPanelContainer.removeAll(false);
        S3.gis.mapWin.items.items = [];
        S3.gis.mapWin.doLayout();
        S3.gis.mapWin.destroy();
        // Add Window
        addMapWindow();
        // Request browser to go full-screen
        if (document.body.requestFullScreen) {
            document.body.requestFullScreen();
        } else if (document.body.webkitRequestFullScreen) {
            document.body.webkitRequestFullScreen();
        } else if (document.body.mozRequestFullScreen) {
            document.body.mozRequestFullScreen();
        }
    }

    function disable_fullscreen() {
        // Remove map elements
        S3.gis.mapWestPanelContainer.removeAll(false);
        S3.gis.mapPanelContainer.removeAll(false);
        S3.gis.mapWin.items.items = [];
        S3.gis.mapWin.doLayout();
        S3.gis.mapWin.destroy();
        // Add embedded Panel
        addMapPanel();
    }

    $('#gis_fullscreen_map-btn').click(function(evt) {
        if (navigator.appVersion.indexOf('MSIE') != -1) {
            // Not supported on IE
            return;
        } else {
            enable_fullscreen();
            evt.preventDefault();
        }
    });

    $('body').bind('webkitfullscreenchange', function() {
        if (!is_fullscreen())
            disable_fullscreen();
    });

    $(document).bind('mozfullscreenchange', function() {
        if (!is_fullscreen())
            disable_fullscreen();
    });

    $('body').bind('webkitfullscreenchange', function() {
        if (!is_fullscreen())
            disable_fullscreen();
    });
});