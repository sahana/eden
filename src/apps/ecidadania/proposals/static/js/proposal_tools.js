/*
    proposal_tools.js - Javascript containing tools for the proposal forms
    like maps and FX.
                           
    License: GPLv3
    Copyright: 2011 Cidadania S. Coop. Galega
    Author: Oscar Carballal Prego <oscar.carballal@cidadania.coop>
*/

// Translation scrings
var hidemap = gettext('Hide map');
var showmap = gettext('Show map');

/* Some general variables */
var map;
var lonlat; // This way lonlat is accesible all the way in the JS
// Transform from WGS 1984
var fromProjection = new OpenLayers.Projection("EPSG:4326");
// to Spherical Mercator Projection
var toProjection   = new OpenLayers.Projection("EPSG:900913");


function toggleMap() {
    /* toggleMap() - Show or hide the map div. */

    $("#showmap").toggle(
        function() {
            $("#map").show();
            $("#showmap").text(hidemap);
        },
        function() {
            $("#map").hide();
            $("#showmap").text(showmap);
        }
    )
}

function clickMap() {
    /*
        clickMap() - This function replaces the Click layer and adds the
        functionality of getting the coorniates when the user clicks a point
        in the map. This function MUST be initialized before startMap().
    */

    OpenLayers.Control.Click = OpenLayers.Class(OpenLayers.Control, {                
        defaultHandlerOptions: {
            'single': true,
            'double': false,
            'pixelTolerance': 0,
            'stopSingle': false,
            'stopDouble': false
        },

        initialize: function(options) {
            this.handlerOptions = OpenLayers.Util.extend(
                {}, this.defaultHandlerOptions
            );
            OpenLayers.Control.prototype.initialize.apply(
                this, arguments
            ); 
            this.handler = new OpenLayers.Handler.Click(
                this, {
                    'click': this.trigger
                }, this.handlerOptions
            );
        }, 

        trigger: function(e) {
            var getcoords = map.getLonLatFromViewPortPx(e.xy);
            lonlat = getcoords.transform(toProjection, fromProjection);
            // Save coordinates to form. First we truncate them to 6 decimals
            trunclon = Math.floor(lonlat.lon * 1000) / 1000;
            trunclat = Math.floor(lonlat.lat * 1000) / 1000;
            $("input[name='longitude']").val(trunclon);
            $("input[name='latitude']").val(trunclat);
            var markers = new OpenLayers.Layer.Markers( "Markers" );
            map.addLayer(markers); 
            markers.addMarker(new OpenLayers.Marker(lonlat));
            // For debugging
            //alert("You clicked near " + lonlat.lat + " N, " +
            //                          + lonlat.lon + " E");
        }
    }); 
}

function startMap() {
    /*
        startMap() - Creates a new map on the div "map" and adds a layer for
        OpenStreetMap (OSM). After that it points towards Santiago de
        Compostela and adds the click control from clickMap() to get the
        coordinates.
    */

    map = new OpenLayers.Map('map');
    var osm = new OpenLayers.Layer.OSM();
    var defaultcoord = new OpenLayers.LonLat(-8.55, 42.88).transform(fromProjection, toProjection);
    map.addLayer(osm);
    map.setCenter(defaultcoord, 10);

    var click = new OpenLayers.Control.Click();
    map.addControl(click);
    click.activate();

    // MARKER STUFF. It's not the best place to be but we need it working now.
    // This is shitty code that needs to be improved ASAP.
    map.events.register("click", map , function(e){
        var markers = new OpenLayers.Layer.Markers( "Markers" );
        marker = new OpenLayers.Marker(lonlat) ;
        markers.addMarker(marker);
        map.addLayer(markers);
        var opx = map.getLayerPxFromViewPortPx(e.xy) ;
        marker.map = map ;
        marker.moveTo(opx) ;
    });
}

function viewMap(lat, lon) {
    /*
        viewMap() - View the stored coordinates in the proposal.
    */
    map = new OpenLayers.Map('map');
    var osm = new OpenLayers.Layer.OSM();
    var markers = new OpenLayers.Layer.Markers( "Markers" );
    var defaultcoord = new OpenLayers.LonLat(lon, lat).transform(fromProjection, toProjection);
    
    map.addLayer(osm);
    map.addLayer(markers);
    map.setCenter(defaultcoord, 10);

    var size = new OpenLayers.Size(21,25);
    var offset = new OpenLayers.Pixel(-(size.w/2), -size.h);
    var icon = new OpenLayers.Icon('http://www.openlayers.org/dev/img/marker.png',size,offset);
    markers.addMarker(new OpenLayers.Marker(defaultcoords,icon));
}

/*******************
    MAIN LOOP
********************/

$(document).ready(function() {
    clickMap();
    startMap();
    toggleMap();
});