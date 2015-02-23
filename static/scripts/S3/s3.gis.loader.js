/**
 * Loader for OpenLayers, GeoExt & GXP
 * - without this some components can load before their dependencies
 *
 * This script is in Static to allow caching
 * Dynamic constants (e.g. Internationalised strings) are set in server-generated script
 *
 *  Used by modules/s3/s3gis.py
 *
 *  based on /static/scripts/gis/openlayers/lib/OpenLayers.js
 */

/**
 * Function: s3_gis_loadjs
 * Load the JavaScript required for a Map.
 *
 * Parameters:
 * debug - {Boolean} Whether to run in Debug mode or not
 * projection - {Integer} The projection to run the map in (900913 & 4236 are handled natively. Other projections require a Proj4 file to be loadable)
 * callback - {Function} The function to be called after the JS is loaded (requires yepnope.js to be loaded)
 * scripts - {Array} A list of additional scripts to load after the core OpenLayers/GeoExt but before the callback is run (These come from Layers & Plugins)
 */
var s3_gis_loadjs = function(debug, projection, callback, scripts) {

    // Instantiate OpenLayers object
    window.OpenLayers = {
        _getScriptLocation: (function() {
            var r = new RegExp("(^|(.*?\\/))(OpenLayers.js)(\\?|$)"),
                s = document.getElementsByTagName('script'),
                src, m, l = '';
            for(var i=0, len=s.length; i<len; i++) {
                src = s[i].getAttribute('src');
                if(src) {
                    m = src.match(r);
                    if(m) {
                        l = m[1];
                        break;
                    }
                }
            }
            return (function() { return l; });
        })(),
        ImgPath : ''
    };

    // The JavaScript files to load
    var jsFiles = [];
    if (debug) {

        if ((projection != 900913) && (projection != 4326)) {
            jsFiles.push('gis/proj4js/lib/proj4js-combined.js');
            jsFiles.push('gis/proj4js/lib/defs/EPSG' + projection + '.js');
        }
        // OpenLayers
        var ol_files = [
            /* List of files needs syncing with:
                /static/scripts/gis/openlayers/lib/OpenLayers.js
                /static/scripts/tools/sahana.js.ol.cfg
            */
            'gis/openlayers/lib/OpenLayers/BaseTypes/Class.js',
            'gis/openlayers/lib/OpenLayers/Util.js',
            'gis/openlayers/lib/OpenLayers/Util/vendorPrefix.js',
            'gis/openlayers/lib/OpenLayers/Animation.js',
            'gis/openlayers/lib/OpenLayers/BaseTypes.js',
            'gis/openlayers/lib/OpenLayers/BaseTypes/Bounds.js',
            'gis/openlayers/lib/OpenLayers/BaseTypes/Date.js',
            'gis/openlayers/lib/OpenLayers/BaseTypes/Element.js',
            'gis/openlayers/lib/OpenLayers/BaseTypes/LonLat.js',
            'gis/openlayers/lib/OpenLayers/BaseTypes/Pixel.js',
            'gis/openlayers/lib/OpenLayers/BaseTypes/Size.js',
            'gis/openlayers/lib/OpenLayers/Console.js',
            'gis/openlayers/lib/OpenLayers/Tween.js',
            'gis/openlayers/lib/OpenLayers/Kinetic.js',
            'gis/openlayers/lib/OpenLayers/Events.js',
            'gis/openlayers/lib/OpenLayers/Events/buttonclick.js',
            'gis/openlayers/lib/OpenLayers/Events/featureclick.js',
            'gis/openlayers/lib/OpenLayers/Request.js',
            'gis/openlayers/lib/OpenLayers/Request/XMLHttpRequest.js',
            'gis/openlayers/lib/OpenLayers/Projection.js',
            'gis/openlayers/lib/OpenLayers/Map.js',
            'gis/openlayers/lib/OpenLayers/Layer.js',
            // Used by Marker layers
            //'gis/openlayers/lib/OpenLayers/Icon.js',
            //'gis/openlayers/lib/OpenLayers/Marker.js',
            //'gis/openlayers/lib/OpenLayers/Marker/Box.js',
            'gis/openlayers/lib/OpenLayers/Popup.js',
            'gis/openlayers/lib/OpenLayers/Tile.js',
            'gis/openlayers/lib/OpenLayers/Tile/Image.js',
            'gis/openlayers/lib/OpenLayers/Tile/Image/IFrame.js',
            'gis/openlayers/lib/OpenLayers/Tile/UTFGrid.js',
            'gis/openlayers/lib/OpenLayers/Layer/Image.js',
            'gis/openlayers/lib/OpenLayers/Layer/SphericalMercator.js',
            'gis/openlayers/lib/OpenLayers/Layer/EventPane.js',
            'gis/openlayers/lib/OpenLayers/Layer/FixedZoomLevels.js',
            'gis/openlayers/lib/OpenLayers/Layer/Google.js',
            'gis/openlayers/lib/OpenLayers/Layer/Google/v3.js',
            'gis/openlayers/lib/OpenLayers/Layer/HTTPRequest.js',
            'gis/openlayers/lib/OpenLayers/Layer/Grid.js',
            //'gis/openlayers/lib/OpenLayers/Layer/MapGuide.js',
            //'gis/openlayers/lib/OpenLayers/Layer/MapServer.js',
            //'gis/openlayers/lib/OpenLayers/Layer/KaMap.js',
            //'gis/openlayers/lib/OpenLayers/Layer/KaMapCache.js',
            //'gis/openlayers/lib/OpenLayers/Layer/Markers.js',
            // Works with Markers not Vectors
            //'gis/openlayers/lib/OpenLayers/Layer/Text.js',
            //'gis/openlayers/lib/OpenLayers/Layer/Text.js',
            //'gis/openlayers/lib/OpenLayers/Layer/WorldWind.js',
            'gis/openlayers/lib/OpenLayers/Layer/ArcGIS93Rest.js',
            'gis/openlayers/lib/OpenLayers/Layer/WMS.js',
            //'gis/openlayers/lib/OpenLayers/Layer/WMTS.js',
            //'gis/openlayers/lib/OpenLayers/Layer/ArcIMS.js',
            // Uses Markers layer
            //'gis/openlayers/lib/OpenLayers/Layer/GeoRSS.js',
            // Markers layers
            //'gis/openlayers/lib/OpenLayers/Layer/Boxes.js',
            'gis/openlayers/lib/OpenLayers/Layer/XYZ.js',
            'gis/openlayers/lib/OpenLayers/Layer/UTFGrid.js',
            'gis/openlayers/lib/OpenLayers/Layer/OSM.js',
            'gis/openlayers/lib/OpenLayers/Layer/Bing.js',
            'gis/openlayers/lib/OpenLayers/Layer/TMS.js',
            'gis/openlayers/lib/OpenLayers/Layer/TileCache.js',
            // oldmapsonline.org
            //'gis/openlayers/lib/OpenLayers/Layer/Zoomify.js',
            //'gis/openlayers/lib/OpenLayers/Layer/ArcGISCache.js',
            'gis/openlayers/lib/OpenLayers/Popup/Anchored.js',
            'gis/openlayers/lib/OpenLayers/Popup/Framed.js',
            'gis/openlayers/lib/OpenLayers/Popup/FramedCloud.js',
            'gis/openlayers/lib/OpenLayers/Feature.js',
            'gis/openlayers/lib/OpenLayers/Feature/Vector.js',
            'gis/openlayers/lib/OpenLayers/Handler.js',
            'gis/openlayers/lib/OpenLayers/Handler/Click.js',
            //'gis/openlayers/lib/OpenLayers/Handler/Hover.js',
            'gis/openlayers/lib/OpenLayers/Handler/Point.js',
            'gis/openlayers/lib/OpenLayers/Handler/Path.js',
            'gis/openlayers/lib/OpenLayers/Handler/Polygon.js',
            //'gis/openlayers/lib/OpenLayers/Handler/Feature.js',
            'gis/openlayers/lib/OpenLayers/Handler/Drag.js',
            'gis/openlayers/lib/OpenLayers/Handler/Pinch.js',
            'gis/openlayers/lib/OpenLayers/Handler/RegularPolygon.js',
            'gis/openlayers/lib/OpenLayers/Handler/Box.js',
            'gis/openlayers/lib/OpenLayers/Handler/MouseWheel.js',
            'gis/openlayers/lib/OpenLayers/Handler/Keyboard.js',
            'gis/openlayers/lib/OpenLayers/Control.js',
            'gis/openlayers/lib/OpenLayers/Control/Attribution.js',
            'gis/openlayers/lib/OpenLayers/Control/Button.js',
            'gis/openlayers/lib/OpenLayers/Control/CacheRead.js',
            'gis/openlayers/lib/OpenLayers/Control/CacheWrite.js',
            'gis/openlayers/lib/OpenLayers/Control/ZoomBox.js',
            'gis/openlayers/lib/OpenLayers/Control/ZoomToMaxExtent.js',
            'gis/openlayers/lib/OpenLayers/Control/DragPan.js',
            'gis/openlayers/lib/OpenLayers/Control/Navigation.js',
            'gis/openlayers/lib/OpenLayers/Control/PinchZoom.js',
            'gis/openlayers/lib/OpenLayers/Control/TouchNavigation.js',
            'gis/openlayers/lib/OpenLayers/Control/MousePosition.js',
            'gis/openlayers/lib/OpenLayers/Control/OverviewMap.js',
            'gis/openlayers/lib/OpenLayers/Control/KeyboardDefaults.js',
            'gis/openlayers/lib/OpenLayers/Control/PanZoom.js',
            //'gis/openlayers/lib/OpenLayers/Control/PanZoomBar.js',
            'gis/openlayers/lib/OpenLayers/Control/ArgParser.js',
            'gis/openlayers/lib/OpenLayers/Control/Permalink.js',
            'gis/openlayers/lib/OpenLayers/Control/Scale.js',
            'gis/openlayers/lib/OpenLayers/Control/ScaleLine.js',
            //'gis/openlayers/lib/OpenLayers/Control/Snapping.js',
            //'gis/openlayers/lib/OpenLayers/Control/Split.js',
            //'gis/openlayers/lib/OpenLayers/Control/LayerSwitcher.js',
            'gis/openlayers/lib/OpenLayers/Control/DrawFeature.js',
            'gis/openlayers/lib/OpenLayers/Control/DragFeature.js',
            'gis/openlayers/lib/OpenLayers/Control/ModifyFeature.js',
            'gis/openlayers/lib/OpenLayers/Control/ModifyFeature/BySegment.js',
            'gis/openlayers/lib/OpenLayers/Control/Panel.js',
            //'gis/openlayers/lib/OpenLayers/Control/SelectFeature.js',
            'gis/openlayers/lib/OpenLayers/Control/NavigationHistory.js',
            'gis/openlayers/lib/OpenLayers/Control/Measure.js',
            'gis/openlayers/lib/OpenLayers/Control/WMSGetFeatureInfo.js',
            //'gis/openlayers/lib/OpenLayers/Control/WMTSGetFeatureInfo.js',
            'gis/openlayers/lib/OpenLayers/Control/Graticule.js',
            'gis/openlayers/lib/OpenLayers/Control/TransformFeature.js',
            'gis/openlayers/lib/OpenLayers/Control/UTFGrid.js',
            'gis/openlayers/lib/OpenLayers/Control/SLDSelect.js',
            'gis/openlayers/lib/OpenLayers/Control/Zoom.js',
            'gis/openlayers/lib/OpenLayers/Geometry.js',
            'gis/openlayers/lib/OpenLayers/Geometry/Collection.js',
            'gis/openlayers/lib/OpenLayers/Geometry/Point.js',
            'gis/openlayers/lib/OpenLayers/Geometry/MultiPoint.js',
            'gis/openlayers/lib/OpenLayers/Geometry/Curve.js',
            'gis/openlayers/lib/OpenLayers/Geometry/LineString.js',
            'gis/openlayers/lib/OpenLayers/Geometry/LinearRing.js',
            'gis/openlayers/lib/OpenLayers/Geometry/Polygon.js',
            'gis/openlayers/lib/OpenLayers/Geometry/MultiLineString.js',
            'gis/openlayers/lib/OpenLayers/Geometry/MultiPolygon.js',
            'gis/openlayers/lib/OpenLayers/Geometry/GeodesicPolygon.js',
            'gis/openlayers/lib/OpenLayers/Renderer.js',
            'gis/openlayers/lib/OpenLayers/Renderer/Elements.js',
            'gis/openlayers/lib/OpenLayers/Renderer/SVG.js',
            'gis/openlayers/lib/OpenLayers/Renderer/Canvas.js',
            'gis/openlayers/lib/OpenLayers/Renderer/VML.js',
            'gis/openlayers/lib/OpenLayers/Layer/Vector.js',
            'gis/openlayers/lib/OpenLayers/Layer/PointGrid.js',
            'gis/openlayers/lib/OpenLayers/Layer/Vector/RootContainer.js',
            'gis/openlayers/lib/OpenLayers/Strategy.js',
            'gis/openlayers/lib/OpenLayers/Strategy/Filter.js',
            'gis/openlayers/lib/OpenLayers/Strategy/Fixed.js',
            'gis/openlayers/lib/OpenLayers/Strategy/Cluster.js',
            'gis/openlayers/lib/OpenLayers/Strategy/Paging.js',
            'gis/openlayers/lib/OpenLayers/Strategy/BBOX.js',
            //'gis/openlayers/lib/OpenLayers/Strategy/Save.js',
            'gis/openlayers/lib/OpenLayers/Strategy/Refresh.js',
            'gis/openlayers/lib/OpenLayers/Strategy/ZoomBBOX.js',
            'gis/openlayers/lib/OpenLayers/Filter.js',
            //'gis/openlayers/lib/OpenLayers/Filter/FeatureId.js',
            //'gis/openlayers/lib/OpenLayers/Filter/Logical.js',
            'gis/openlayers/lib/OpenLayers/Filter/Comparison.js',
            // Used by GetFeature
            'gis/openlayers/lib/OpenLayers/Filter/Spatial.js',
            //'gis/openlayers/lib/OpenLayers/Filter/Function.js',                
            'gis/openlayers/lib/OpenLayers/Protocol.js',
            'gis/openlayers/lib/OpenLayers/Protocol/HTTP.js',
            'gis/openlayers/lib/OpenLayers/Protocol/WFS.js',
            'gis/openlayers/lib/OpenLayers/Protocol/WFS/v1.js',
            'gis/openlayers/lib/OpenLayers/Protocol/WFS/v1_0_0.js',
            'gis/openlayers/lib/OpenLayers/Protocol/WFS/v1_1_0.js',
            'gis/openlayers/lib/OpenLayers/Protocol/WFS/v2_0_0.js',
            //'gis/openlayers/lib/OpenLayers/Protocol/CSW.js', 
            //'gis/openlayers/lib/OpenLayers/Protocol/CSW/v2_0_2.js',
            'gis/openlayers/lib/OpenLayers/Protocol/Script.js',
            //'gis/openlayers/lib/OpenLayers/Protocol/SOS.js',
            //'gis/openlayers/lib/OpenLayers/Protocol/SOS/v1_0_0.js',
            'gis/openlayers/lib/OpenLayers/Layer/PointTrack.js',
            'gis/openlayers/lib/OpenLayers/Style.js',
            'gis/openlayers/lib/OpenLayers/Style2.js',
            'gis/openlayers/lib/OpenLayers/StyleMap.js',
            'gis/openlayers/lib/OpenLayers/Rule.js',
            'gis/openlayers/lib/OpenLayers/Format.js',
            'gis/openlayers/lib/OpenLayers/Format/QueryStringFilter.js',
            'gis/openlayers/lib/OpenLayers/Format/XML.js',
            'gis/openlayers/lib/OpenLayers/Format/XML/VersionedOGC.js',
            'gis/openlayers/lib/OpenLayers/Format/Context.js',
            //'gis/openlayers/lib/OpenLayers/Format/ArcXML.js',
            //'gis/openlayers/lib/OpenLayers/Format/ArcXML/Features.js',
            'gis/openlayers/lib/OpenLayers/Format/GML.js',
            'gis/openlayers/lib/OpenLayers/Format/GML/Base.js',
            'gis/openlayers/lib/OpenLayers/Format/GML/v2.js',
            'gis/openlayers/lib/OpenLayers/Format/GML/v3.js',
            'gis/openlayers/lib/OpenLayers/Format/Atom.js',
            //'gis/openlayers/lib/OpenLayers/Format/EncodedPolyline.js',
            'gis/openlayers/lib/OpenLayers/Format/KML.js',
            'gis/openlayers/lib/OpenLayers/Format/GeoRSS.js',
            'gis/openlayers/lib/OpenLayers/Format/WFS.js',
            'gis/openlayers/lib/OpenLayers/Format/OWSCommon.js',
            'gis/openlayers/lib/OpenLayers/Format/OWSCommon/v1.js',
            'gis/openlayers/lib/OpenLayers/Format/OWSCommon/v1_0_0.js',
            'gis/openlayers/lib/OpenLayers/Format/OWSCommon/v1_1_0.js',
            'gis/openlayers/lib/OpenLayers/Format/WCSCapabilities.js',
            'gis/openlayers/lib/OpenLayers/Format/WCSCapabilities/v1.js',
            'gis/openlayers/lib/OpenLayers/Format/WCSCapabilities/v1_0_0.js',
            'gis/openlayers/lib/OpenLayers/Format/WCSCapabilities/v1_1_0.js',
            'gis/openlayers/lib/OpenLayers/Format/WFSCapabilities.js',
            'gis/openlayers/lib/OpenLayers/Format/WFSCapabilities/v1.js',
            'gis/openlayers/lib/OpenLayers/Format/WFSCapabilities/v1_0_0.js',
            'gis/openlayers/lib/OpenLayers/Format/WFSCapabilities/v1_1_0.js',
            'gis/openlayers/lib/OpenLayers/Format/WFSCapabilities/v2_0_0.js',
            'gis/openlayers/lib/OpenLayers/Format/WFSDescribeFeatureType.js',
            'gis/openlayers/lib/OpenLayers/Format/WMSDescribeLayer.js',
            'gis/openlayers/lib/OpenLayers/Format/WMSDescribeLayer/v1_1.js',
            'gis/openlayers/lib/OpenLayers/Format/WKT.js',
            //'gis/openlayers/lib/OpenLayers/Format/CQL.js',
            'gis/openlayers/lib/OpenLayers/Format/OSM.js',
            'gis/openlayers/lib/OpenLayers/Format/GPX.js',
            'gis/openlayers/lib/OpenLayers/Format/Filter.js',
            'gis/openlayers/lib/OpenLayers/Format/Filter/v1.js',
            'gis/openlayers/lib/OpenLayers/Format/Filter/v2.js',
            'gis/openlayers/lib/OpenLayers/Format/Filter/v1_0_0.js',
            'gis/openlayers/lib/OpenLayers/Format/Filter/v1_1_0.js',
            'gis/openlayers/lib/OpenLayers/Format/Filter/v2_0_0.js',
            'gis/openlayers/lib/OpenLayers/Format/SLD.js',
            'gis/openlayers/lib/OpenLayers/Format/SLD/v1.js',
            'gis/openlayers/lib/OpenLayers/Format/SLD/v1_0_0.js',
            'gis/openlayers/lib/OpenLayers/Format/SLD/v1_0_0_GeoServer.js',
            'gis/openlayers/lib/OpenLayers/Format/OWSCommon.js',
            'gis/openlayers/lib/OpenLayers/Format/OWSCommon/v1.js',
            'gis/openlayers/lib/OpenLayers/Format/OWSCommon/v1_0_0.js',
            'gis/openlayers/lib/OpenLayers/Format/OWSCommon/v1_1_0.js',
            //'gis/openlayers/lib/OpenLayers/Format/CSWGetDomain.js',
            //'gis/openlayers/lib/OpenLayers/Format/CSWGetDomain/v2_0_2.js',
            //'gis/openlayers/lib/OpenLayers/Format/CSWGetRecords.js',
            //'gis/openlayers/lib/OpenLayers/Format/CSWGetRecords/v2_0_2.js',
            'gis/openlayers/lib/OpenLayers/Format/WFST.js',
            'gis/openlayers/lib/OpenLayers/Format/WFST/v1.js',
            'gis/openlayers/lib/OpenLayers/Format/WFST/v1_0_0.js',
            'gis/openlayers/lib/OpenLayers/Format/WFST/v1_1_0.js',
            'gis/openlayers/lib/OpenLayers/Format/WFST/v2_0_0.js',
            'gis/openlayers/lib/OpenLayers/Format/Text.js',
            'gis/openlayers/lib/OpenLayers/Format/JSON.js',
            'gis/openlayers/lib/OpenLayers/Format/GeoJSON.js',
            //'gis/openlayers/lib/OpenLayers/Format/WMC.js',
            //'gis/openlayers/lib/OpenLayers/Format/WMC/v1.js',
            //'gis/openlayers/lib/OpenLayers/Format/WMC/v1_0_0.js',
            //'gis/openlayers/lib/OpenLayers/Format/WMC/v1_1_0.js',
            //'gis/openlayers/lib/OpenLayers/Format/WCSGetCoverage.js',
            'gis/openlayers/lib/OpenLayers/Format/WMSCapabilities.js',
            'gis/openlayers/lib/OpenLayers/Format/WMSCapabilities/v1.js',
            'gis/openlayers/lib/OpenLayers/Format/WMSCapabilities/v1_1.js',
            'gis/openlayers/lib/OpenLayers/Format/WMSCapabilities/v1_1_0.js',
            'gis/openlayers/lib/OpenLayers/Format/WMSCapabilities/v1_1_1.js',
            'gis/openlayers/lib/OpenLayers/Format/WMSCapabilities/v1_3.js',
            'gis/openlayers/lib/OpenLayers/Format/WMSCapabilities/v1_3_0.js',
            'gis/openlayers/lib/OpenLayers/Format/WMSCapabilities/v1_1_1_WMSC.js',
            'gis/openlayers/lib/OpenLayers/Format/WMSGetFeatureInfo.js',
            //'gis/openlayers/lib/OpenLayers/Format/SOSCapabilities.js',
            //'gis/openlayers/lib/OpenLayers/Format/SOSCapabilities/v1_0_0.js',
            //'gis/openlayers/lib/OpenLayers/Format/SOSGetFeatureOfInterest.js',
            //'gis/openlayers/lib/OpenLayers/Format/SOSGetObservation.js',
            //'gis/openlayers/lib/OpenLayers/Format/OWSContext.js',
            //'gis/openlayers/lib/OpenLayers/Format/OWSContext/v0_3_1.js',
            //'gis/openlayers/lib/OpenLayers/Format/WMTSCapabilities.js',
            //'gis/openlayers/lib/OpenLayers/Format/WMTSCapabilities/v1_0_0.js',
            //'gis/openlayers/lib/OpenLayers/Format/WPSCapabilities.js',
            //'gis/openlayers/lib/OpenLayers/Format/WPSCapabilities/v1_0_0.js',
            //'gis/openlayers/lib/OpenLayers/Format/WPSDescribeProcess.js',
            //'gis/openlayers/lib/OpenLayers/Format/WPSExecute.js',
            //'gis/openlayers/lib/OpenLayers/Format/XLS.js',
            //'gis/openlayers/lib/OpenLayers/Format/XLS/v1.js',
            //'gis/openlayers/lib/OpenLayers/Format/XLS/v1_1_0.js',
            'gis/openlayers/lib/OpenLayers/Format/OGCExceptionReport.js',
            'gis/openlayers/lib/OpenLayers/Control/GetFeature.js',
            //'gis/openlayers/lib/OpenLayers/Control/NavToolbar.js',
            'gis/openlayers/lib/OpenLayers/Control/PanPanel.js',
            'gis/openlayers/lib/OpenLayers/Control/Pan.js',
            'gis/openlayers/lib/OpenLayers/Control/ZoomIn.js',
            'gis/openlayers/lib/OpenLayers/Control/ZoomOut.js',
            'gis/openlayers/lib/OpenLayers/Control/ZoomPanel.js',
            //'gis/openlayers/lib/OpenLayers/Control/EditingToolbar.js',
            'gis/openlayers/lib/OpenLayers/Control/Geolocate.js',
            'gis/openlayers/lib/OpenLayers/Symbolizer.js',
            'gis/openlayers/lib/OpenLayers/Symbolizer/Point.js',
            'gis/openlayers/lib/OpenLayers/Symbolizer/Line.js',
            'gis/openlayers/lib/OpenLayers/Symbolizer/Polygon.js',
            'gis/openlayers/lib/OpenLayers/Symbolizer/Text.js',
            'gis/openlayers/lib/OpenLayers/Symbolizer/Raster.js',
            'gis/openlayers/lib/OpenLayers/Lang.js',
            'gis/openlayers/lib/OpenLayers/Lang/en.js',
            'gis/openlayers/lib/OpenLayers/Spherical.js',
            'gis/openlayers/lib/OpenLayers/TileManager.js',
            //'gis/openlayers/lib/OpenLayers/WPSClient.js',
            //'gis/openlayers/lib/OpenLayers/WPSProcess.js',
            'gis/openlayers/lib/OpenLayers/Strategy/AttributeCluster.js'
        ]
        jsFiles = jsFiles.concat(ol_files)

        try {
            if (Ext) {
                // GeoExt
                var gxt_files = [
                    'gis/GeoExt/lib/GeoExt/data/AttributeReader.js',
                    'gis/GeoExt/lib/GeoExt/data/AttributeStore.js',
                    'gis/GeoExt/lib/GeoExt/data/FeatureRecord.js',
                    'gis/GeoExt/lib/GeoExt/data/FeatureReader.js',
                    'gis/GeoExt/lib/GeoExt/data/FeatureStore.js',
                    'gis/GeoExt/lib/GeoExt/data/LayerRecord.js',
                    'gis/GeoExt/lib/GeoExt/data/LayerReader.js',
                    'gis/GeoExt/lib/GeoExt/data/LayerStore.js',
                    'gis/GeoExt/lib/GeoExt/data/ScaleStore.js',
                    'gis/GeoExt/lib/GeoExt/data/StyleReader.js',
                    'gis/GeoExt/lib/GeoExt/data/WMSCapabilitiesReader.js',
                    'gis/GeoExt/lib/GeoExt/data/WMSCapabilitiesStore.js',
                    'gis/GeoExt/lib/GeoExt/data/WFSCapabilitiesReader.js',
                    'gis/GeoExt/lib/GeoExt/data/WFSCapabilitiesStore.js',
                    'gis/GeoExt/lib/GeoExt/data/WMSDescribeLayerReader.js',
                    'gis/GeoExt/lib/GeoExt/data/WMSDescribeLayerStore.js',
                    'gis/GeoExt/lib/GeoExt/data/WMCReader.js',
                    'gis/GeoExt/lib/GeoExt/widgets/Action.js',
                    'gis/GeoExt/lib/GeoExt/data/ProtocolProxy.js',
                    'gis/GeoExt/lib/GeoExt/widgets/FeatureRenderer.js',
                    'gis/GeoExt/lib/GeoExt/widgets/MapPanel.js',
                    'gis/GeoExt/lib/GeoExt/widgets/Popup.js',
                    'gis/GeoExt/lib/GeoExt/widgets/form.js',
                    'gis/GeoExt/lib/GeoExt/widgets/form/SearchAction.js',
                    'gis/GeoExt/lib/GeoExt/widgets/form/BasicForm.js',
                    'gis/GeoExt/lib/GeoExt/widgets/form/FormPanel.js',
                    'gis/GeoExt/lib/GeoExt/widgets/grid/SymbolizerColumn.js',
                    'gis/GeoExt/lib/GeoExt/widgets/tips/SliderTip.js',
                    'gis/GeoExt/lib/GeoExt/widgets/tips/LayerOpacitySliderTip.js',
                    'gis/GeoExt/lib/GeoExt/widgets/tips/ZoomSliderTip.js',
                    'gis/GeoExt/lib/GeoExt/widgets/tree/LayerNode.js',
                    'gis/GeoExt/lib/GeoExt/widgets/tree/TreeNodeUIEventMixin.js',
                    'gis/GeoExt/lib/GeoExt/plugins/TreeNodeComponent.js',
                    'gis/GeoExt/lib/GeoExt/plugins/TreeNodeRadioButton.js',
                    'gis/GeoExt/lib/GeoExt/plugins/TreeNodeActions.js',
                    'gis/GeoExt/lib/GeoExt/widgets/tree/LayerLoader.js',
                    'gis/GeoExt/lib/GeoExt/widgets/tree/LayerContainer.js',
                    'gis/GeoExt/lib/GeoExt/widgets/tree/BaseLayerContainer.js',
                    'gis/GeoExt/lib/GeoExt/widgets/tree/OverlayLayerContainer.js',
                    'gis/GeoExt/lib/GeoExt/widgets/tree/LayerParamNode.js',
                    'gis/GeoExt/lib/GeoExt/widgets/tree/LayerParamLoader.js',
                    'gis/GeoExt/lib/GeoExt/widgets/tree/WMSCapabilitiesLoader.js',
                    'gis/GeoExt/lib/GeoExt/widgets/LayerOpacitySlider.js',
                    'gis/GeoExt/lib/GeoExt/widgets/LayerLegend.js',
                    'gis/GeoExt/lib/GeoExt/widgets/LegendImage.js',
                    //'gis/GeoExt/lib/GeoExt/widgets/OSMLegend.js',
                    'gis/GeoExt/lib/GeoExt/widgets/UrlLegend.js',
                    'gis/GeoExt/lib/GeoExt/widgets/WMSLegend.js',
                    'gis/GeoExt/lib/GeoExt/widgets/VectorLegend.js',
                    'gis/GeoExt/lib/GeoExt/widgets/LegendPanel.js',
                    'gis/GeoExt/lib/GeoExt/widgets/ZoomSlider.js',
                    'gis/GeoExt/lib/GeoExt/widgets/grid/FeatureSelectionModel.js',
                    'gis/GeoExt/lib/GeoExt/data/PrintPage.js',
                    'gis/GeoExt/lib/GeoExt/data/PrintProvider.js',
                    'gis/GeoExt/lib/GeoExt/plugins/PrintPageField.js',
                    'gis/GeoExt/lib/GeoExt/plugins/PrintProviderField.js',
                    'gis/GeoExt/lib/GeoExt/plugins/PrintExtent.js',
                    'gis/GeoExt/lib/GeoExt/plugins/AttributeForm.js',
                    'gis/GeoExt/lib/GeoExt/widgets/PrintMapPanel.js',
                    'gis/GeoExt/lib/GeoExt/state/PermalinkProvider.js',
                    'gis/GeoExt/lib/GeoExt/Lang.js',

                    // GXP
                    'ext-community-extensions/RowExpander.js',
                    'gis/gxp/widgets/NewSourceWindow.js',
                    'gis/gxp/plugins/LayerSource.js',
                    'gis/gxp/plugins/WMSSource.js',
                    'gis/gxp/plugins/Tool.js',
                    'gis/gxp/plugins/AddLayers.js',
                    'gis/gxp/plugins/RemoveLayer.js'
                ];
                if (i18n.gis_search) {
                    gxt_files.push('gis/GeoExt/ux/GeoNamesSearchCombo.js');
                }
                if (i18n.gis_uploadlayer) {
                    gxt_files.push('ext-community-extensions/FileUploadField.js');
                    gxt_files.push('gis/gxp/widgets/LayerUploadPanel.js');
                }
                jsFiles = jsFiles.concat(gxt_files)
            }
        } catch(err) {};

        if (S3.gis.mgrs) {
            jsFiles.push('gis/usng2.js');
            jsFiles.push('gis/MP.js');
        }

        if (S3.gis.custom != 'undefined') {
            // S3
            jsFiles.push('S3/s3.gis.js');
        }
    } else {
        // Non-Debug
        if ((projection != 900913) && (projection != 4326)) {
            jsFiles.push('gis/proj4js/lib/proj4js-compressed.js');
            jsFiles.push('gis/proj4js/lib/defs/EPSG' + projection + '.js');
        }
        jsFiles.push('gis/OpenLayers.js');
        try {
            if (Ext) {
                jsFiles.push('gis/GeoExt.js');
                if (i18n.gis_search) {
                    jsFiles.push('gis/GeoExt/ux/GeoNamesSearchCombo.min.js');
                }
                if (i18n.gis_uploadlayer) {
                    jsFiles.push('gis/gxp_upload.js');
                }
            }
        } catch(err) {};
        if (S3.gis.mgrs) {
            jsFiles.push('gis/MGRS.min.js');
        }
        if (S3.gis.custom != 'undefined') {
            jsFiles.push('S3/s3.gis.min.js');
        }
    }

    // Add the additional scritps from Layers/Plugins
    jsFiles = jsFiles.concat(scripts)

    var path = S3.Ap.concat('/static/scripts/');
    if (callback) {
        // Add the full path
        for (var i=0, len=jsFiles.length; i < len; i++) {
            jsFiles[i] = path + jsFiles[i];
        }
        // Use yepnope for guaranteed execution order & ability to run a callback once-completed
        yepnope({
            load: jsFiles,
            complete: function() {
                // Hide the Loader
                $('.map_loader').hide();
                // Loading complete, now we can run the callback
                callback.call();
            }
        });
    } else {
        // Use "parser-inserted scripts" for guaranteed execution order
        // http://hsivonen.iki.fi/script-execution/
        var src, script;
        var head = document.getElementsByTagName('head');
        for (var i=0, len=jsFiles.length; i < len; i++) {
            src = path + jsFiles[i];
            script = document.createElement('script');
            script.src = src;
            // Maintain execution order
            script.async = false;
            head[0].appendChild(script);
        }
        // Hide the Loader
        $('.map_loader').hide();
    }
}