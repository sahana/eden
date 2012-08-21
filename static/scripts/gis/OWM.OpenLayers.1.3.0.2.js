//
//	Open Weather Map
//	core script for OpenLayers library
//	Version 1.3.0.2
//	2012.07.27
//
//	1.3.0.2
//	Change interface getrect to version 1.9
//	
//	1.3.0.1
//	new icons
//
//	2012.05.23 Version 1.2.1
//	добавлена серверная кластеризация для станций. Она включена по умолчанию для класса 
//	OpenLayers.Layer.Vector.OWMStations
//
//	2012.05.20 Version 1.2
//	добавлена серверная кластеризация. Она включена по умолчанию для класса 
//	OpenLayers.Layer.Vector.OWMWeather
//	для класса OpenLayers.Layer.Vector.OWMStations в настоящий момент серверная кластеризация не работает
//
//	2012.05.10 Version 1.1
//	добавлена клиентская кластеризация

if (typeof OpenLayers == 'undefined') {
  throw "Needs OpenLayers.";
}

//
// WMS
//

OpenLayers.Layer.OWMwms = OpenLayers.Class(OpenLayers.Layer.WMS, {
	initialize:function(name,options)
	{
		if( ! name.layer ) name.layer = GLBETA_PR;
		if( ! name.name ) name.name = name.layer;
	        var newArguments = [
		name.name,
		"http://wms.weatheroffice.gc.ca/geomet/?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap", 	
		{
			layers: name.layer, 
			transparent: "true", 
			format: 'image/png',
			checked : false
		}, 
		{isBaseLayer: false, opacity: 0.4}
		];

//	        newArguments.push(name, options);
		OpenLayers.Layer.WMS.prototype.initialize.apply(this,newArguments);	
	}

});


//
// Weather
//
// A specific format for parsing OpenWeatherMap CWeather API JSON responses.

OpenLayers.Format.OWMWeather = OpenLayers.Class(OpenLayers.Format, {

	read: function(obj) {

		if(obj.cod !== '200') {
			throw new Error(
				['OWM failure response (',  obj.cod,'): ',obj.message].join('') );
		}

		if(!obj || !obj.list || !OpenLayers.Util.isArray(obj.list )) {
                        throw new Error('Unexpected OWM response');
		}
		var list = obj.list, x, y, point, feature, features = [];

		//console.log('time='+obj.calctime+', cnt='+obj.cnt +', '+ obj.message);

		for(var i=0,l=list.length; i<l; i++) {
			feature = new OpenLayers.Feature.Vector(
			new OpenLayers.Geometry.Point(list[i].lng, list[i].lat), 
			{
                            title: list[i].name,
			    station: list[i],
                            temp:  Math.round(100*(list[i].temp-273.15))/100
                        });
			features.push(feature);
		}
		return features;
	}
});

// Vector 
//cluster.geometry.getBounds().getCenterLonLat(); 
OpenLayers.Layer.Vector.OWMWeather = OpenLayers.Class( OpenLayers.Layer.Vector, {
	projection: new OpenLayers.Projection("EPSG:4326"),
	strategies: [new OpenLayers.Strategy.BBOX({resFactor: 1})],
	protocol: new OpenLayers.Protocol.Script({
                        url: "http://openweathermap.org/data/1.9/getrect",
                        params: {
				type: 'city',
				cluster: 'yes',
				cnt: 200,
				format: 'json',
				layer: this		// идиотское решение, но я не понял как иначе достать OpenLayers.Layer.Vector
                        },
                        filterToParams: function(filter, params) {
				if (filter.type === OpenLayers.Filter.Spatial.BBOX) {
					params.bbox = filter.value.toArray();
					params.bbox.push(params.layer.map.getZoom());	//магия - добавляю zoom в параметры
					if (filter.projection) {
						params.bbox.push(filter.projection.getCode());
					}
				}
				return params;
			}, 
                        callbackKey: 'callback',
                        format: new OpenLayers.Format.OWMWeather()
                    }),
	styleMap: new OpenLayers.StyleMap(
		new OpenLayers.Style({
			fontColor: "black",
			fontSize: "12px",
			fontFamily: "Arial, Courier New",
			labelAlign: "lt",
			labelXOffset: "-15",
			labelYOffset: "-17",
			labelOutlineColor: "white",
			labelOutlineWidth: 3,
			externalGraphic: "${icon}",
			graphicWidth: 50,
                	label : "${temp}"+ "°C"
			},
			{
			context: 
			{
				icon:  function(feature) {
					return GetWeatherIcon(feature.attributes.station);
				}
			}
			}

		)),
	initialize:function(name,options)
	{

		if (options == undefined) { 
		// конечно надо сделать аккуратнее. сейчас добавиви любую иную кроме eventListeners опцию, я отключу показ попапов
			options =  {eventListeners:
			{
			featureselected:  this.onSelect, 
			featureunselected: this.onUnselect
			}
			}; 
		} 
//		alert(options.toSource());
//		alert(arguments[1].eventListeners.featureselected.toSource());

	        var newArguments = [];
	        newArguments.push(name, options);
		OpenLayers.Layer.Vector.prototype.initialize.apply(this,newArguments);	
//		OpenLayers.Layer.Vector.prototype.initialize.apply(this,arguments);

	},

onPopupClose: function(evt) {
                // 'this' is the popup.
                var feature = this.feature;
                if (feature.pois) { // The feature is not destroyed
                    selectControl.unselect(feature);
                } else { // After "moveend" or "refresh" events on POIs layer all 
                         //     features have been destroyed by the Strategy.BBOX
                    this.destroy();
                }

},

onSelect: function(evt) {
                feature = evt.feature;
		var html = GetWeatherBuble(feature.attributes.station);
		popup = new OpenLayers.Popup("FramedCloud",
                       feature.geometry.getBounds().getCenterLonLat(), 
                       new OpenLayers.Size(170,175),
			html, "City", 
//			true, this.onPopupClose);
			false);

                feature.popup = popup;
                popup.feature = feature;
                map.addPopup(popup, true);

},

onUnselect: function (evt) {
                feature = evt.feature;
                if (feature.popup) {
                    popup.feature = null;
                    map.removePopup(feature.popup);
                    feature.popup.destroy();
                    feature.popup = null;
                }
}

});


// Vector for Strategy.Cluster
OpenLayers.Layer.Vector.OWMClusterWeather = OpenLayers.Class( OpenLayers.Layer.Vector, {
//	projection: "EPSG:4326",
	strategies: [
		new OpenLayers.Strategy.Cluster({distance: 80}),
		new OpenLayers.Strategy.BBOX({resFactor: 1})],
	protocol: new OpenLayers.Protocol.Script({
                        url: "http://openweathermap.org/data/1.9/getrect",
                        params: {
				type: 'city',
				cluster: 'no',
				format: 'json'
                        },
                        callbackKey: 'callback',
                        format: new OpenLayers.Format.OWMWeather()
                    }),
	styleMap: new OpenLayers.StyleMap(
		new OpenLayers.Style({
			fontColor: "black",
			fontSize: "12px",
			fontFamily: "Arial,Courier New, monospace",
			labelAlign: "lt",
			labelXOffset: "-15",
			labelYOffset: "-17",
			labelOutlineColor: "white",
			labelOutlineWidth: 3,
			externalGraphic: "${icon}",
			graphicWidth: 50,
                	label : "${label}"
			},
			{
			context: 
				{
				label: function(feature) { return feature.attributes.label; },
				icon: function(feature) 
				{
					var maxImportance = 0;
					var mainFeature = 0;
					for(var c = 0; c < feature.cluster.length; c++) {
						if(feature.cluster[c].attributes.station.rang*1.0 > maxImportance) {
							maxImportance = feature.cluster[c].attributes.station.rang;
							mainFeature = c;
						}
					}
					feature.attributes.icon = GetWeatherIcon(feature.cluster[mainFeature].attributes.station);
					feature.attributes.label = feature.cluster[mainFeature].attributes.temp + "°C";
					feature.attributes.station = feature.cluster[mainFeature].attributes.station;
					return feature.attributes.icon;
				}
				}
		}
	)),
	initialize:function(name,options)
	{
		if (options == undefined) { 
			options =  {eventListeners:
			{
			featureselected:  this.onSelect, 
			featureunselected: this.onUnselect
			}
			}; 
		} 
	        var newArguments = [];
	        newArguments.push(name, options);
		OpenLayers.Layer.Vector.prototype.initialize.apply(this,newArguments);	

	},

onPopupClose: function(evt) {
                // 'this' is the popup.
                var feature = this.feature;
                if (feature.pois) { // The feature is not destroyed
                    selectControl.unselect(feature);
                } else { // After "moveend" or "refresh" events on POIs layer all 
                         //     features have been destroyed by the Strategy.BBOX
                    this.destroy();
                }

},

onSelect: function(evt) {
                feature = evt.feature;
		var html = GetWeatherBuble(feature.attributes.station);
		popup = new OpenLayers.Popup("FramedCloud",
                       feature.geometry.getBounds().getCenterLonLat(), 
                       new OpenLayers.Size(160,170),
			html,
                       "City", true, this.onPopupClose);
                feature.popup = popup;
                popup.feature = feature;
                map.addPopup(popup, true);

},

onUnselect: function (evt) {
                feature = evt.feature;
                if (feature.popup) {
                    popup.feature = null;
                    map.removePopup(feature.popup);
                    feature.popup.destroy();
                    feature.popup = null;
                }
}

});


//
//	Stations
//	A specific format for parsing OpenWeatherMap Stations API JSON responses.
//
OpenLayers.Format.OWMStations = OpenLayers.Class(OpenLayers.Format, {

	read: function(obj) {
                    if(obj.cod !== '200') {
                        throw new Error(
                            ['OWM failure response (',  obj.cod,'): ',obj.message].join('') );
                    }

                    if(!obj || !obj.list || !OpenLayers.Util.isArray(obj.list )) {
                        throw new Error(
                            'Unexpected OWM response');
                    }
					
					//console.log('time='+obj.calctime+', cnt='+obj.cnt +', '+ obj.message);
					
                    var list = obj.list, x, y, point,
					feature, features = [];					

                    for(var i=0,l=list.length; i<l; i++) {
			list[i].type = list[i].type*1.0;
                        feature = new OpenLayers.Feature.Vector(new OpenLayers.Geometry.Point(list[i].lng, list[i].lat), 
			{
                            title: list[i].name,
			    station: list[i],
			    stationType: list[i].type,
                            temp:  Math.round(100*(list[i].temp-273.15))/100
                        });
                        features.push(feature);
                    }
                    return features;
	}
});

// Vector Class
OpenLayers.Layer.Vector.OWMStations = OpenLayers.Class( OpenLayers.Layer.Vector, {

		projection: new OpenLayers.Projection("EPSG:4326"),
                    strategies: [
				new OpenLayers.Strategy.BBOX({resFactor: 1})],
                    protocol: new OpenLayers.Protocol.Script({
                        url: "http://openweathermap.org/data/1.9/getrect",
                        params: {
				type: 'station',
				cluster_distance: 120,
				cluster: 'yes',
				format: 'json',
				layer: this		// идиотское решение, но я не понял как иначе достать OpenLayers.Layer.Vector
                        },
                        filterToParams: function(filter, params) {
				if (filter.type === OpenLayers.Filter.Spatial.BBOX) {
					params.bbox = filter.value.toArray();
					params.bbox.push(params.layer.map.getZoom());	//магия - добавляю zoom в параметры
					if (filter.projection) {
						params.bbox.push(filter.projection.getCode());
					}
				}
				return params;
			},
                        callbackKey: 'callback',
                        format: new OpenLayers.Format.OWMStations()
                    }),
		styleMap: new OpenLayers.StyleMap(
		new OpenLayers.Style({
			fontColor: "black",
			fontSize: "12px",
			fontFamily: "Courier New, monospace",
			labelAlign: "lt",
			labelXOffset: "-15",
			labelYOffset: "-17",
			labelOutlineColor: "white",
			labelOutlineWidth: 3,
			externalGraphic: "http://openweathermap.org/img/s/istation.png",
			graphicWidth: 25,
                	label : "${temp}°C"
		})),
		initialize:function(name,options)
		{
			if (options == undefined) { 
				options =  {eventListeners:
				{
				featureselected:  this.onSelect, 
				featureunselected: this.onUnselect
				}
				}; 
			} 
			var newArguments = [];
			newArguments.push(name, options);

			// create a lookup table with different images for stations type
			var stationTypeLookup = {
				1: {externalGraphic: "http://openweathermap.org/img/s/iplane.png"},
				2: {externalGraphic: "http://openweathermap.org/img/s/istation.png"},
				5: {externalGraphic: "http://openweathermap.org/img/s/istation.png"}
			};
			this.styleMap.addUniqueValueRules("default", "stationType", stationTypeLookup);

			OpenLayers.Layer.Vector.prototype.initialize.apply(this,newArguments);			
		},

onPopupClose: function(evt) {
                var feature = this.feature;
                if (feature.pois) { 
                    selectControl.unselect(feature);
                } else { 
                    this.destroy();
                }

},

onSelect: function(evt) {
                feature = evt.feature;
		html = GetStationData(feature.attributes.station);
		popup = new OpenLayers.Popup("Popup",
                       feature.geometry.getBounds().getCenterLonLat(), 
                       new OpenLayers.Size(150,240),
			html, "Station", 
//			true, onPopupClose);
			false);	

                feature.popup = popup;
                popup.feature = feature;
                map.addPopup(popup, true);
},

onUnselect: function (evt) {
                feature = evt.feature;
                if (feature.popup) {
                    popup.feature = null;
                    map.removePopup(feature.popup);
                    feature.popup.destroy();
                    feature.popup = null;
                }
}

});


//
// A specific format for parsing OpenWeatherMap Stations API JSON responses. and Cluster
//
OpenLayers.Layer.Vector.OWMClusterStations = OpenLayers.Class( OpenLayers.Layer.Vector, {
//                    projection: "EPSG:4326",
                    strategies: [
				new OpenLayers.Strategy.Cluster({distance: 40}),
				new OpenLayers.Strategy.BBOX({resFactor: 1})],
                    protocol: new OpenLayers.Protocol.Script({
                        url: "http://openweathermap.org/data/1.9/getrect",
                        params: {
				type: 'station',
				cluster: 'no',	
				format: 'json'
                        },
                        callbackKey: 'callback',
                        format: new OpenLayers.Format.OWMStations()
                    }),
		styleMap: new OpenLayers.StyleMap(
		new OpenLayers.Style(
		{
			fontColor: "black",
			fontSize: "12px",
			fontFamily: "Arial, Courier New",
			labelAlign: "lt",
			labelXOffset: "-15",
			labelYOffset: "-17",
			labelOutlineColor: "white",
			labelOutlineWidth: 3,
			externalGraphic: "${icon}",
			graphicWidth: 25,
                	label : "${label}"
		},
		{
			context: 
				{
				label: function(feature) { return feature.attributes.label; },
				icon: function(feature) 
					{
						feature.attributes.icon = "http://openweathermap.org/img/s/iplane.png";
						var maxImportance = 0;
						var mainFeature = 0;
						if(feature.cluster){
						for(var c = 0; c < feature.cluster.length; c++) {
							if(feature.cluster[c].attributes.station.dt>maxImportance){
								maxImportance = feature.cluster[c].attributes.station.dt;
								mainFeature   = c;
							}
						}

		switch(feature.cluster[mainFeature].attributes.stationType)
		{
			case 1: feature.attributes.icon = "http://openweathermap.org/img/s/iplane.png"; break;
			case 2: feature.attributes.icon = "http://openweathermap.org/img/s/istation.png"; break;
			case 5: feature.attributes.icon = "http://openweathermap.org/img/s/istation.png"; break;
		}

		feature.attributes.label = feature.cluster[mainFeature].attributes.temp + "°C";
		feature.attributes.station = feature.cluster[mainFeature].attributes.station;
						}

						return feature.attributes.icon;
					}
				}
		}

)),

		initialize:function(name,options)
		{
			if (options == undefined) { 
				options =  {eventListeners:
				{
				featureselected:  this.onSelect, 
				featureunselected: this.onUnselect
				}
				}; 
			} 
			var newArguments = [];
			newArguments.push(name, options);

			OpenLayers.Layer.Vector.prototype.initialize.apply(this,newArguments);			
		},

onPopupClose: function(evt) {
                // 'this' is the popup.
                var feature = this.feature;
                if (feature.pois) { // The feature is not destroyed
                    selectControl.unselect(feature);
                } else { // After "moveend" or "refresh" events on POIs layer all 
                         //     features have been destroyed by the Strategy.BBOX
                    this.destroy();
                }

},

onSelect: function(evt) {
                feature = evt.feature;
		//alert(feature.attributes.station.toSource());
		html = GetStationData(feature.attributes.station);
/*		if(feature.attributes.count>1){
			html = html + '<div style="display: block; clear: left; color: gray; font-size: x-small;" > count:'+feature.attributes.count+'</div>';
		}*/

		popup = new OpenLayers.Popup("Popup",
                       feature.geometry.getBounds().getCenterLonLat(), 
                       new OpenLayers.Size(150,240),
			html, "Station", 
//			true, this.onPopupClose);
			false);
                feature.popup = popup;
                popup.feature = feature;
                map.addPopup(popup, true);
},

onUnselect: function (evt) {
                feature = evt.feature;
                if (feature.popup) {
                    popup.feature = null;
                    map.removePopup(feature.popup);
                    feature.popup.destroy();
                    feature.popup = null;
                }
}

});



function GetStationIcon(st)
{
	if(st.type == 1)
		return 'http://openweathermap.org/img/s/iplane.png';
	return 'http://openweathermap.org/img/s/istation.png';
}

function GetWeatherIcon(st)
{
	var dt= new Date();
	var times = SunCalc.getTimes(dt, st.lat, st.lng);
	if( dt>times.sunrise && dt < times.sunset ) var day='d'; else var day='n';

	var cl = st.cloud;

	var img = 'transparent';
	if(cl < 1 && cl >= 0 ) 	 img = '01';
	if(cl < 5 && cl >= 1 ) 	 img = '01';
	if(cl < 25 && cl >= 5 )  img = '01';
	if(cl < 50 && cl >= 25 ) img = '02';
	if(cl < 75 && cl >= 50 ) img = '03';
	if(cl >= 75 ) img = '04';

	switch(st.prcp_type)
	{
		case 1: if(st.prcp>0) img = '13'; break;
		//case '2': img = '13'; break;
		//case '3': img = '13'; break;
		case 4: if(st.prcp>0) {
			img = '09';	
			if(cl < 30 ) img = '10';
			break;
		}
	}

	return 'http://openweathermap.org/img/w/'+img+day+'.png';
}


/*
 Copyright (c) 2011, Vladimir Agafonkin
 SunCalc is a JavaScript library for calculating sun position and sunlight phases.
 https://github.com/mourner/suncalc
*/
(function(c){function n(a){return new Date((a+0.5-o)*p)}var c="undefined"!==typeof exports?exports:c.SunCalc={},b=Math,f=b.PI/180,a=b.sin,i=b.cos,p=864E5,o=2440588,t=357.5291*f,u=0.98560028*f,v=1.9148*f,w=0.02*f,x=3.0E-4*f,y=102.9372*f,q=23.45*f,D=280.16*f,E=360.9856235*f,r=[[-0.83,"sunrise","sunset"],[-0.3,"sunriseEnd","sunsetStart"],[-6,"dawn","dusk"],[-12,"nauticalDawn","nauticalDusk"],[-18,"nightEnd","night"],[6,"goldenHourEnd","goldenHour"]];c.addTime=function(a,b,d){r.push([a,b,d])};c.getTimes=
function(m,h,d){var d=f*-d,h=f*h,m=b.round(m.valueOf()/p-0.5+o-2451545-9.0E-4-d/(2*b.PI)),e=2451545.0009+(0+d)/(2*b.PI)+m,g=t+u*(e-2451545),c=v*a(g)+w*a(2*g)+x*a(3*g),c=g+y+c+b.PI,z=b.asin(a(c)*a(q)),e=e+0.0053*a(g)+-0.0069*a(2*c),s={solarNoon:n(e)},k,A,j,l,B,C;for(k=0,A=r.length;k<A;k+=1)j=r[k],l=j[0],B=j[1],j=j[2],l=2451545.0009+(b.acos((a(l*f)-a(h)*a(z))/(i(h)*i(z)))+d)/(2*b.PI)+m+0.0053*a(g)+-0.0069*a(2*c),C=e-(l-e),s[B]=n(C),s[j]=n(l);return s};c.getPosition=function(c,h,d){var d=f*-d,h=f*h,
c=c.valueOf()/p-0.5+o,e=t+u*(c-2451545),g=v*a(e)+w*a(2*e)+x*a(3*e),g=e+y+g+b.PI,e=b.asin(a(g)*a(q)),g=b.atan2(a(g)*i(q),i(g)),d=D+E*(c-2451545)-d-g;return{azimuth:b.atan2(a(d),i(d)*a(h)-b.tan(e)*i(h)),altitude:b.asin(a(h)*a(e)+i(h)*i(e)*i(d))}}})(this);
// 
// HTML bubles
// 

// Weather buble
function GetWeatherBuble(st)
{

var temp = Math.round((st.temp -273.15)*100)/100;
var temp_min = Math.round((st.temp_min -273.15)*100)/100;
var temp_max = Math.round((st.temp_max -273.15)*100)/100;
var dtat = new Date(st.dt * 1000 );
var dt = dtat.toTimeString();

h_header = '<p><a href="/city/'+st.id+'">'+st.name+'</a></p> \
<div style="float: left; width: 145px;" >\
<div style="display: block; clear: left;" >\
<div style="float: left;" title="'+GetWeatherText(st)+'">\
<img height="45" width="50" style="border: medium none; width: 50px; height: 45px; background: url(&quot;'+GetWeatherIcon(st)+'&quot;) repeat scroll 0% 0% transparent;" alt="'+GetWeatherText(st)+'" src="/images/transparent.png"/></div>\
<div style="float: left;" >\
<div style="display: block; clear: left; font-size: medium; font-weight: bold; padding: 0pt 3pt;" title="Current Temperature">'+temp+'°C</div>\
<div style="display: block; width: 85px; overflow: visible;" >\
<div style="float: left; text-align: center; font-size: small; padding: 0pt 3pt;" title="High Temperature">'+temp_max+'°C</div>\
<div style="float: left; text-align: center; color: gray; font-size: small; padding: 0pt 3pt;" title="Low Temperature">'+temp_min+'°C</div>\
</div></div></div>\
<div style="display: block; clear: left; font-size: x-small;">'+GetWeatherText(st)+'</div>\
<div style="display: block; clear: left; color: gray; font-size: x-small;" >Humidity: ' + st.humidity +'%</div>\
<div style="display: block; clear: left; color: gray; font-size: x-small;" >rang: ' + st.rang +'</div>\
<div style="display: block; clear: left; color: gray; font-size: x-small;" >Wind: '+st.wind_ms+' m/s</div></div>';

h_footer = '</div>';

return h_header + h_footer;
}

function GetStationData(st)
{
var temp = Math.round((st.temp -273.15)*100)/100;
var dt = new Date(st.dt * 1000 );

var html_h=
'<p><a href="/station/'+st.id+'">'+st.name+'</a></p> \
<div style="float: left; width: 130px;" >\
<div style="display: block; clear: left;" >\
<div style="float: left;" title="'+GetWeatherText(st)+'">\
<img height="30" width="30" style="border: medium none; width: 25px; height: 25px; background: url(&quot;'+GetStationIcon(st)+'&quot;) scroll 0% 0% transparent;" alt="" src="/images/transparent.png"/></div>\<div style="float: left;" >\
<div style="display: block; clear: left; font-size: medium; font-weight: bold; padding: 0pt 3pt;" title="Current Temperature">'+temp+'°C</div>\
<div style="display: block; width: 85px; overflow: visible;" >\
</div></div></div>';

if(st.humidity)
html_h += '<div style="display: block; clear: left; color: gray; font-size: x-small;" >Humidity: ' + st.humidity +'%</div>';
if(st.wind_ms)
html_h += '<div style="display: block; clear: left; color: gray; font-size: x-small;" >Wind: '+st.wind_ms+' m/s</div>';
if(st.pressure)
html_h += '<div style="display: block; clear: left; color: gray; font-size: x-small;" >Pressure: '+st.pressure+' hpa</div>';

html_h += '<div style="display: block; clear: left; color: gray; font-size: x-small;" title="'+dt.toString()+'" >Recived at '+dt.toTimeString()+'</div></div>';

html_h += '</div>';

return html_h;
}



function GetWeatherText(st)
{
	var txt='Clear';
	switch(st.prcp_type)
	{
		case 1:	if( st.prcp > 0) txt = 'Snow ' + '( ' + st.prcp +'мм )'; 
			else txt = 'possible snow'; 
			break;
		case 2:	if( st.prcp > 0 ) txt = 'Ice ' + '( ' + st.prcp +'мм )'; 
			else  txt = 'possible ice'; 
			break;
		case 3:	txt = 'rain';
			break;
		case 4:	if( st.prcp > 0 ) txt = 'Rain ' + '( ' + st.prcp +'мм )'; 
			else txt = 'possible rain'; 
			break;
		default:txt = 'Clear';
	}
	return txt;
}




