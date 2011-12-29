function style_osm_feature(feature) {
    feature.style = OpenLayers.Util.extend({'fill':'black'}, OpenLayers.Feature.Vector.style['default']);
    if (feature.attributes.highway == "motorway") {
        feature.style.strokeColor = "blue";
        feature.style.strokeWidth = 5;
    } else if (feature.attributes.highway == "primary") {
        feature.style.strokeColor = "red";
    } else if (feature.attributes.highway == "secondary") {
        feature.style.strokeColor = "orange";
    } else if (feature.attributes.highway) {
        feature.style.strokeColor = "black";
    }
}
