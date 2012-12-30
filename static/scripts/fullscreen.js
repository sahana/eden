$(function () {
	function is_fullscreen() {
	    return document.fullscreen||document.mozFullScreen||document.webkitIsFullScreen;
	}
	
	function enable_fullscreen(state) {
	    if(state) {
	        S3.gis.mapWestPanelContainer.removeAll(false);
	        S3.gis.mapPanelContainer.removeAll(false);
	        S3.gis.mapWin.items.items=[];
	        S3.gis.mapWin.doLayout();
	        S3.gis.mapWin.destroy();
	        addMapWindow();
	        if(document.body.requestFullScreen){
	            document.body.requestFullScreen();
	        }else if(document.body.webkitRequestFullScreen){
	            document.body.webkitRequestFullScreen();
	        }else if(document.body.mozRequestFullScreen){
	            document.body.mozRequestFullScreen();
	        }
	    } else {
	        S3.gis.mapWestPanelContainer.removeAll(false);
	        S3.gis.mapPanelContainer.removeAll(false);
	        S3.gis.mapWin.items.items=[];
	        S3.gis.mapWin.doLayout();
	        S3.gis.mapWin.destroy();
	        addMapPanel();
	    }
	}
	
	$('#gis_fullscreen_map-btn').click(function(evt) {
		if(navigator.appVersion.indexOf("MSIE")!=-1) {
			return;
		} else {
			enable_fullscreen(true);
			evt.preventDefault();
		}
	});
	
	$('body').bind('webkitfullscreenchange', function () {
	    if(!is_fullscreen())
	        enable_fullscreen(false);
	});
	
	$(document).bind('mozfullscreenchange', function () {
	    if(!is_fullscreen())
	        enable_fullscreen(false);
	});
	
	$('body').bind('webkitfullscreenchange', function () {
	    if(!is_fullscreen())
	        enable_fullscreen(false);
	});
});