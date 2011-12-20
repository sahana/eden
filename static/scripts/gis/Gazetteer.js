Gazetteer = OpenLayers.Class({
    initialize: function() { 
    },

    osmGaz: function(search) {
        try { 
            var u = new USNG2();
            var data = u.toLonLat(search);
            if (data && data.lon && data.lat) {
                var lonlat = new OpenLayers.LonLat(data.lon, data.lat);
                var zoom = HAITI.map.getZoom() > 14 ? HAITI.map.getZoom() : 14;
                HAITI.map.setCenter(lonlat.transform(new OpenLayers.Projection("EPSG:4326"), new OpenLayers.Projection("EPSG:900913")), zoom);
                return;
            }
        } catch (E) {
        }
        var reg = /([\d-.]+),\s*([\d-.]+)/.exec(search);
        if (reg) {
            var lon = parseFloat(reg[2]);
            var lat = parseFloat(reg[1]);
            if (lon < 0 && lat > 0) { 
                var lonlat = new OpenLayers.LonLat(lon, lat);
            } else {
                var lonlat = new OpenLayers.LonLat(lat, lon);
            }    
            var zoom = HAITI.map.getZoom() > 14 ? HAITI.map.getZoom() : 14;
            HAITI.map.setCenter(lonlat.transform(new OpenLayers.Projection("EPSG:4326"), new OpenLayers.Projection("EPSG:900913")), zoom);
        }    
        var s = document.createElement("script");
        s.src="http://nominatim.openstreetmap.org/haiti/?viewbox=-76.24%2C21%2C-69.2%2C17&format=json&json_callback=gazhandleOsmLoc&q="+encodeURIComponent(search);
        document.body.appendChild(s);
      },
      handleOsmLoc: function(data) {
        if(this.panel) { 
            ltPanel.remove(this.panel);
        }    
            var html = '';
            for (var i = 0; i < data.length; i++) {
                data[i]['lon'] = data[i].lon.toFixed(4);
                data[i]['lat'] = data[i].lat.toFixed(4);
              html += OpenLayers.String.format('<div class="result" onClick="gaz.go(${lon}, ${lat});"> <span class="name">${display_name}</span> <span class="latlon">Lat/Lon: ${lat}, ${lon}</span> <span class="place_id">${place_id}</span> <span class="type">(${type})</span> </div>', data[i]);
          }       
        var panel = new Ext.Panel({'title':"Gazetter", html: html, autoScroll: true})
        ltPanel.add(panel);
        ltPanel.doLayout();
        panel.expand();
        ltPanel.doLayout();
        this.panel = panel;
      }, 
      go: function(lon, lat) {
         var lonlat = new OpenLayers.LonLat(lon, lat);
         lonlat.transform(HAITI.map.displayProjection, HAITI.map.getProjectionObject());
         lookupLayer.destroyFeatures();
         lookupLayer.addFeatures(new OpenLayers.Feature.Vector(new OpenLayers.Geometry.Point(lonlat.lon, lonlat.lat)));
         var zoom = HAITI.map.getZoom() > 15 ? HAITI.map.getZoom() : 15;
         HAITI.map.setCenter(lonlat, zoom);
       }           
});      
var gaz = new Gazetteer();
gazhandleOsmLoc = gaz.handleOsmLoc;
