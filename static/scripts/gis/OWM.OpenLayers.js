//
//	Open Weather Map
//	core script for OpenLayers library
//	http://openweathermap.org/wiki/API/OWM.OpenLayers.js
//
//
//	Version 1.3.5
//	2012.11.21
//		NEW tile server
//
//	Version 1.3.4
//	2012.09.17
//		NEW json API 
//		text weather conditions
//
//	Version 1.3.2
//	2012.08.13
//
//	Version 1.3.0.3
//	2012.08.03
//	bug fixed
//
//	2012.08.03 1.3.0.3
//	Add Composite layers for clouds and etc
//	
//	1.3.0.2
//	Change interface getrect function to version 1.9
//	add WMS layers 
//	
//	1.3.0.1
//	new weather icons
//
//	2012.05.23 Version 1.2.1
//	OpenLayers.Layer.Vector.OWMStations
//
//	2012.05.20 Version 1.2
//	добавлена серверная кластеризация. Она включена по умолчанию для класса 
//	OpenLayers.Layer.Vector.OWMWeather
//	для класса OpenLayers.Layer.Vector.OWMStations в настоящий момент серверная кластеризация не работает
//
//	2012.05.10 Version 1.1
//	добавлена клиентская кластеризация

//if (typeof OpenLayers == 'undefined') {
//  throw "Needs OpenLayers.";
//	console.log("Needs OpenLayers.");
//}


// Композитный слой tiles
OpenLayers.Layer.OWMComposite = OpenLayers.Class(OpenLayers.Layer.WMS, {

initialize:function(layer,name, params)
{
	this.l = layer;

	if(params == undefined) { 
		params = {isBaseLayer: false, opacity: 0.6}
	}
	params.attribution = 'Forecast layers from <a href="http://openweathermap.org/wiki/Models/GDPRS">Environment Canada</a>';
	

        var newArguments = [
		name,
		"http://tile.openweathermap.org/wms",
		{
			layers: 'GLBETA_'+this.l,
			SERVICE: 'WMS',
			VERSION: "1.1.1",
			REQUEST: 'GetMap',
			transparent: "true", 
			format: 'image/png'
		}, 
		params
	];

	OpenLayers.Layer.WMS.prototype.initialize.apply(this,newArguments);	
},

getURL: function (bounds) {
	var z=this.map.getZoom();

	this.params.LAYERS = 'GLBETA_'+this.l;

	if(z > 5) {
		b= this.map.getExtent();
		if ( isREGETA(b) ) {
			this.params.LAYERS = 'REGETA_'+this.l;
			if(z > 7) { 
				if( isLAMARCTICETA(b) )		this.params.LAYERS = 'LAMARCTICETA_'+this.l; 
				else if( isLAMWESTETA(b) ) 	this.params.LAYERS = 'LAMWESTETA_'+this.l; 
				else if( isLAMMARITIMEETA(b) )	this.params.LAYERS = 'LAMMARITIMEETA_'+this.l; 
				else if( isLAMEASTETA(b) )	this.params.LAYERS = 'LAMEASTETA_'+this.l; 
			}
			//console.log(this.params.LAYERS);
		}
	}

	bounds = this.adjustBounds(bounds); 
	       
	var imageSize = this.getImageSize();
	var newParams = {};
	// WMS 1.3 introduced axis order
	var reverseAxisOrder = this.reverseAxisOrder();
	newParams.BBOX = this.encodeBBOX ?
	            bounds.toBBOX(null, reverseAxisOrder) :
	            bounds.toArray(reverseAxisOrder);
	newParams.WIDTH = imageSize.w;
	newParams.HEIGHT = imageSize.h;
	var requestString = this.getFullRequestString(newParams);
	return requestString;
}

});


// Radar compozite wms layer

OpenLayers.Layer.OWMRadar = OpenLayers.Class(OpenLayers.Layer.WMS, {
initialize:function(name, params)
{
	if(params == undefined) { 
		params = {isBaseLayer: false, opacity: 0.4}
	}
	params.attribution = 'Radar layer from <a href="http://openweathermap.org/wiki/Layer/radar">Environment Canada</a>';
        var newArguments = [
		name,
		"http://tile.openweathermap.org/wms",
		{
			layers: 'RADAR.12KM',
			SERVICE: 'WMS',
			VERSION: "1.1.1",
			REQUEST: 'GetMap',
			transparent: "true", 
			format: 'image/png'
		}, 
		params
	];

	OpenLayers.Layer.WMS.prototype.initialize.apply(this,newArguments);	
},

getURL: function (bounds) {
	var z=this.map.getZoom();
	this.params.LAYERS = z > 8 ? 'RADAR.2KM' : 'RADAR.12KM';

	bounds = this.adjustBounds(bounds); 
	       
	var imageSize = this.getImageSize();
	var newParams = {};
	// WMS 1.3 introduced axis order
	var reverseAxisOrder = this.reverseAxisOrder();
	newParams.BBOX = this.encodeBBOX ?
	            bounds.toBBOX(null, reverseAxisOrder) :
	            bounds.toArray(reverseAxisOrder);
	newParams.WIDTH = imageSize.w;
	newParams.HEIGHT = imageSize.h;
	var requestString = this.getFullRequestString(newParams);
	return requestString;
}

});



//
// WMS
//

OpenLayers.Layer.OWMwms = OpenLayers.Class(OpenLayers.Layer.WMS, {
	initialize:function(layer, name, params)
	{
		if(params == undefined) { 
			params = {isBaseLayer: false, opacity: 0.3}
		}
		if( ! layer ) layer = GLBETA_PR;
		if( ! name ) name = layer;
	        var newArguments = [
		name,
		"http://tile.openweathermap.org/wms",
		{
			layers: layer, 
			SERVICE: 'WMS',
			VERSION: "1.1.1",
			REQUEST: 'GetMap',
			transparent: "true", 
			format: 'image/png'
		}, 
			params
		];

		OpenLayers.Layer.WMS.prototype.initialize.apply(this,newArguments);	
	}

});

OpenLayers.Layer.OWMCanada = OpenLayers.Class(OpenLayers.Layer.WMS, {
	initialize:function(layer, name, params)
	{
		if(params == undefined) { 
			params = {isBaseLayer: false, opacity: 0.3}
		}
		if( ! layer ) layer = GLBETA_PR;
		if( ! name ) name = layer;
	        var newArguments = [
		name,
		"",
		{
			layers: layer, 
			SERVICE: 'WMS',
			VERSION: "1.1.1",
			REQUEST: 'GetMap',
			transparent: "true", 
			format: 'image/png'
		}, 
			params
		];

		OpenLayers.Layer.WMS.prototype.initialize.apply(this,newArguments);	
	},

getURL: function (bounds) {

	bounds = this.adjustBounds(bounds); 
	       
	var imageSize = this.getImageSize();
	var newParams = {};
	// WMS 1.3 introduced axis order
	var reverseAxisOrder = this.reverseAxisOrder();
	newParams.BBOX = this.encodeBBOX ?
	            bounds.toBBOX(null, reverseAxisOrder) :
	            bounds.toArray(reverseAxisOrder);
	newParams.WIDTH = imageSize.w;
	newParams.HEIGHT = imageSize.h;
	var requestString = this.getFullRequestString(newParams);
	requestString = "http://openweathermap.org/t/t?url="+requestString.replace(/&/g,"%26");
	return requestString;
}

});


//
// Weather
//
// A specific format for parsing OpenWeatherMap Weather API JSON responses.

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
			new OpenLayers.Geometry.Point(list[i].coord.lon, list[i].coord.lat), 
			{
                            title: list[i].name,
			    station: list[i],
                            temp:  Math.round(10*(list[i].main.temp-273.15))/10
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
/*	protocol: new OpenLayers.Protocol.Script({
                        url: "http://openweathermap.org/data/2.1/find/city",
                        params: {
//				type: 'city',
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
                    }), */
	styleMap: new OpenLayers.StyleMap(
		new OpenLayers.Style({
			fontColor: "black",
			fontSize: "12px",
			fontFamily: "Arial, Courier New",
			graphicXOffset: -20,
			graphicYOffset: -5,
			labelAlign: "lt",
			labelXOffset: "-5",
			labelYOffset: "-35",
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
					if (feature.layer) {
                        return feature.layer.options.getIcon(feature.attributes.station);
                    } else {
                        // @ToDo: 1 Feature/layer doesn't have the layer set for some reason
                        return S3.Ap.concat("/static/img/gis/openlayers/blank.gif")
                    }
				}
			}
			}

		)),
	initialize:function(name,options)
	{

		if (options == undefined) options =  {}; 

		if (options.eventListeners == undefined)
			options.eventListeners = {
				featureselected:  this.onSelect, 
				featureunselected: this.onUnselect
			}

		if (options.iconsets == undefined) options.iconsets='main';
		
		options.attribution = 'Weather from <a href="http://openweathermap.org/" alt="World Map and worldwide Weather Forecast online">OpenWeatherMap</a>';

		if (options.getIcon == undefined)	options.getIcon = this.getIcon;
		if (options.getPopupHtml == undefined)	{
			options.getPopupHtml = this.getPopupHtml;
			if (options.popupX == undefined)	options.popupX = 150;
			if (options.popupY == undefined)	options.popupY = 175;
		}

	        var newArguments = [];
	        newArguments.push(name, options);
		OpenLayers.Layer.Vector.prototype.initialize.apply(this,newArguments);	

		this.protocol = new OpenLayers.Protocol.Script({
                        url: "http://openweathermap.org/data/2.1/find/city",
                        params: {
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
                    });

	},

onPopupClose: function(evt) {
	var feature = this.feature;
	if (feature.pois) { // The feature is not destroyed
		selectControl.unselect(feature);
	} else { // After "moveend" or "refresh" events on POIs layer all 
		this.destroy();
	}
},

onSelect: function(evt) {
	feature = evt.feature;
	var html = this.options.getPopupHtml(feature.attributes.station);
	popup = new OpenLayers.Popup("FramedCloud", feature.geometry.getBounds().getCenterLonLat(), 
	new OpenLayers.Size(this.options.popupX, this.options.popupY), html, "City", false);

	feature.popup = popup;
	popup.feature = feature;
	this.map.addPopup(popup, true);

},

onUnselect: function (evt) {
	feature = evt.feature;
	if (feature.popup) {
		popup.feature = null;
		this.map.removePopup(feature.popup);
		feature.popup.destroy();
		feature.popup = null;
	}
},

getPopupHtml: function(station) {
	return GetWeatherPopupHtml(station);
},

getIcon: function(station) {
	if( station.weather.length > 0 ) {
		return 'http://openweathermap.org/img/w/' + station.weather[0].icon + '.png';
	}else{
		var dt= new Date();
		var times = SunCalc.getTimes(dt, station.coord.lat, station.coord.lon);
		if( dt>times.sunrise && dt < times.sunset ) var day='day'; else var day='night';
		var icon = GetWeatherIconDay(station, day);
		return 'http://openweathermap.org/img/w/' + icon;
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
//			list[i].type = list[i].type;
			if(!list[i].main) continue;

                        feature = new OpenLayers.Feature.Vector(new OpenLayers.Geometry.Point(list[i].coord.lon, list[i].coord.lat), 
			{
                            title: list[i].name,
			    station: list[i],
			    stationType: list[i].type,
                            temp:  Math.round(10*(list[i].main.temp-273.15))/10
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
/*                    protocol: new OpenLayers.Protocol.Script({
                        url: "http://openweathermap.org/data/2.1/find/station",
                        params: {
//				type: 'station',
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
                    }), */
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
			externalGraphic: "${icon}",
			graphicWidth: 25,
                	label : "${temp}°C"
		},{
			context: 
			{
				icon:  function(feature) {
					if (feature.layer) {
                        return feature.layer.options.getIcon(feature.attributes.station);
                    } else {
                        // @ToDo: 1 Feature/layer doesn't have the layer set for some reason
                        return S3.Ap.concat("/static/img/gis/openlayers/blank.gif");
                    }
				}
			}
		}
		)),

		initialize:function(name,options)
		{
			if (options == undefined) options =  {}; 

			if (options.eventListeners == undefined)
				options.eventListeners = {
					featureselected:  this.onSelect, 
					featureunselected: this.onUnselect
				}


			options.attribution = 'Weather from <a href="http://openweathermap.org/" alt="World Map and worldwide Weather Forecast online">OpenWeatherMap</a>';
			var newArguments = [];

			if (options.getIcon == undefined)	options.getIcon = this.getIcon;
			if (options.getPopupHtml == undefined)	{
				options.getPopupHtml = this.getPopupHtml;
				if (options.popupX == undefined)	options.popupX = 150;
				if (options.popupY == undefined)	options.popupY = 200;
			}

			newArguments.push(name, options);

			OpenLayers.Layer.Vector.prototype.initialize.apply(this,newArguments);			

			this.StationPopupHtml =  GetStationPopupHtml;
			this.protocol = new OpenLayers.Protocol.Script({
                        url: "http://openweathermap.org/data/2.1/find/station",
                        params: {
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
                    });


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
	var html = this.options.getPopupHtml(feature.attributes.station);

	popup = new OpenLayers.Popup("Popup",
                       feature.geometry.getBounds().getCenterLonLat(), 
                       new OpenLayers.Size(this.options.popupX, this.options.popupY), html, "Station", false);	

	feature.popup = popup;
	popup.feature = feature;
	this.map.addPopup(popup, true);
},

onUnselect: function (evt) {
	feature = evt.feature;
	if (feature.popup) {
		popup.feature = null;
		this.map.removePopup(feature.popup);
		feature.popup.destroy();
		feature.popup = null;
	}
},

getPopupHtml: function(station) {
	return GetStationPopupHtml(station);
},

getIcon: function(station) {
//	console.log(feature.layer.options.iconsets);
	var stationTypeLookup = {
		1: {externalGraphic: "http://openweathermap.org/img/s/iplane.png"},
		2: {externalGraphic: "http://openweathermap.org/img/s/istation.png"},
		5: {externalGraphic: "http://openweathermap.org/img/s/istation.png"}
	};
	return stationTypeLookup[station.type].externalGraphic;
}

});




function GetWeatherIconDay(st, hr)
{
	if(hr == undefined || hr == 'day' )
		var day='d';
	else
		var day='n';
	var cl =0
	if(st.clouds && st.clouds.all ) cl = st.clouds.all;

	var img = 'transparent';
	if(cl < 1 && cl >= 0 ) 	 img = '01';
	if(cl < 5 && cl >= 1 ) 	 img = '01';
	if(cl < 25 && cl >= 5 )  img = '01';
	if(cl < 50 && cl >= 25 ) img = '02';
	if(cl < 75 && cl >= 50 ) img = '03';
	if(cl >= 75 ) img = '04';

	if(st.rain  && st.rain['3h']) {
		img = '09';
		if(cl < 30 ) img = '10';
	}

	return img+day+'.png';
}


/* Geometry functions */
function isboundsinrect(bounds, r)
{
	var position = new OpenLayers.LonLat(bounds.left, bounds.bottom);
	position.transform(
		    new OpenLayers.Projection("EPSG:900913"),
		    new OpenLayers.Projection("EPSG:4326")
	);

	var position2 = new OpenLayers.LonLat(bounds.right, bounds.top);
	position2.transform(
		    new OpenLayers.Projection("EPSG:900913"),
		    new OpenLayers.Projection("EPSG:4326")
	);

	p1 = {x: position.lat, y:position.lon};
	p2 = {x: position2.lat, y:position2.lon};
	return inRectangle(p1, r[0], r[1], r[2], r[3]) && inRectangle(p2, r[0], r[1], r[2], r[3]);
}


function isLAMEASTETA(bounds)
{
	var r = [{x:37.990, y:-92.055}, {x:38.718, y:-70.551}, {x:51.323, y:-68.764}, {x:50.421, y:-95.476}];
	if ( isboundsinrect(bounds, r) ) 
		return true;
	return false;
}

function isLAMWESTETA(bounds)
{
	var r = [{x:44.167, y:-130.909}, {x:45.990, y:-108.855}, {x:57.208, y:-108.123}, {x:54.903, y:-136.010}];
	if ( isboundsinrect(bounds, r) ) 
		return true;
	return false;
}

function isLAMMARITIMEETA(bounds)
{
	var r = [{x:40.210, y:-66.554},	{x:44.907, y:-50.824}, {x:54.596, y:-54.152}, {x:49.002, y:-73.506}];
	if ( isboundsinrect(bounds, r) ) 
		return true;
	return false;
}


function isLAMARCTICETA(bounds)
{
	var r = [{x:58.252, y:-77.123}, {x:59.478, y:-56.694}, {x:70.236, y:-55.179}, {x:68.439, y:-85.106}];
	if ( isboundsinrect(bounds, r) ) 
		return true;
	return false;
}

function isREGETA(bounds)
{
	var r = [{x:20, y:-163.696}, {x:15, y:-71.801}, {x:66, y:-17}, {x:80, y:-179.9}]
	if ( isboundsinrect(bounds, r) ) 
		return true;
	return false;
}

function areaOfTriangle(p1, p2, p3)
{
	var p1s = {x: (p1.x-p3.x), y: (p1.y-p3.y)};
	var p2s = {x: (p2.x-p3.x), y: (p2.y-p3.y)};
	var s = ( p1s.x*p2s.y - p2s.x*p1s.y )/2.0
	return Math.abs(s);
} 

function inTriangle(p0, p1, p2, p3)
{
	var s = areaOfTriangle(p1, p2, p3);
	var sall = areaOfTriangle(p0, p1, p2) + areaOfTriangle(p0, p1, p3) + areaOfTriangle(p0, p2, p3);
	if( Math.abs(s - sall) < 0.001 ) return true;
	return false;
}

function inRectangle(p, p1, p2, p3, p4)
{
	return inTriangle(p, p1, p2, p4) || inTriangle(p, p3, p2, p4);
}



// 
// HTML bubles
// 

var WeekDayText = {
months: ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"],
days: ["воскресенье", "понедельник", "вторник", "среда", "четверг", "пятница", "суббота"],
//days_small: ["вс", "пн", "вт", "ср", "чт", "пт", "сб"]
days_small: ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
}

function GetWeatherText2(st)
{
	var txt='';
	if( st.snow && st.snow['3h'] )
		txt = 'Snow ' + '( ' + st.snow['3h'] +'мм )'; 

	if( st.rain && st.rain['3h'] )
		txt = 'Rain:' + '(' + st.rain['3h'] +'мм)'; 
	return txt;
}

function GetWeatherIcon2(st, we)
{
	var dt= new Date();
	var times = SunCalc.getTimes(dt, st.lat, st.lng);
	if( dt>times.sunrise && dt < times.sunset ) var day='d'; else var day='n';

	var cl = we.clouds.all;
	var img = 'transparent';

	if(cl < 1 && cl >= 0 ) 	 img = '01';
	if(cl < 5 && cl >= 1 ) 	 img = '01';
	if(cl < 25 && cl >= 5 )  img = '01';
	if(cl < 50 && cl >= 25 ) img = '02';
	if(cl < 75 && cl >= 50 ) img = '03';
	if(cl >= 75 ) img = '04';

	if(we.rain  && we.rain['3h'])
		img = '09';

//	if(we.snow['3h'])img = '09';

	return img+day+'.png';
}

function GetWeatherForecastBubleHtml( st, forecast, cnt )
{
var curdate = new Date( (new Date()).getTime()- 280 * 60 * 1000 );
var temp = Math.round((st.main.temp -273)*10)/10;
var temp_min = Math.round((st.main.temp_min -273)*100)/100;
var temp_max = Math.round((st.main.temp_max -273)*100)/100;
var dtat = new Date(st.dt * 1000 );
//var dt = dtat.toTimeString();
//var dt = st.dt;

var times = SunCalc.getTimes(dtat, st.coord.lat, st.coord.lon);
if( st.dt>times.sunrise && st.dt< times.sunset ) var day='d'; else var day='n';

//http://openweathermap.org/img/w/ + GetWeatherIconDay(st,day)

var wtext = GetWeatherText2(st);

var h_header = 
'<p class="weather_title"><a style="weather_title_link" href="http://openweathermap.org/city/'+st.id+'">'+st.name+'</a></p> \
<div style="float: left;" >\
\
<div class="weather_block">\
 <div class="cur_weather_block" title="'+wtext+'">\
  <img class="weather_image" alt="'+wtext+'" src="http://openweathermap.org/img/w/'+GetWeatherIconDay(st,day)+'"/>\
  <div class="temp_block" >\
   <div class="big_temp" title="Current Temperature '+dt+'">'+temp+'°</div>\
   <div class="small_temp_block" >\
    <div class="small_temp">'+wtext+'</div>\
   </div>\
  </div>\
 </div>\
 <div class="small_val_grey" title="Min and max temperature">Min t: '+temp_min+' / Max t: '+temp_max+' °C</div>\
 <div class="small_val_grey">Humidity: ' + st.main.humidity +'%</div>\
 <div class="small_val_grey">Wind: '+st.wind.speed+' m/s</div>\
</div>';

h_footer = '</div>';

h_body = '';
for(var j = 0; j < cnt ; j++)
	if( curdate  < new Date(forecast[j].dt * 1000 ) ) break;


for(var i = j; i < cnt+j ; i++){
	var dt= new Date();
	var times = SunCalc.getTimes(dtat, st.coord.lat, st.coord.lon);

	if( dt>times.sunrise && dt < times.sunset ) var day='d'; else var day='n';

	temp = Math.round(forecast[i].main.temp -273);
	temp_min = Math.round((forecast[i].main.temp_min -273)*100)/100;
	temp_max = Math.round((forecast[i].main.temp_max -273)*100)/100;
	dtat = new Date(forecast[i].dt * 1000 );
	if( curdate  > dtat )	continue;
	hr = dtat.getHours(); 
	dt = hr + ':00';
	if(hr<10) dt = '0' + dt; 
 

h_o = 
'<div style="font-size: small; float: left; text-align: center;" >\
 <div title="' + WeekDayText.days[dtat.getDay()] + '">'+WeekDayText.days_small[dtat.getDay()]+'</div>\
 <div title="' + dtat.toString() + '">'+dt+'</div>\
 <img alt="'+GetWeatherText2(forecast[i])+'" src="http://openweathermap.org/img/w/'+GetWeatherIcon2(st, forecast[i])+'"/>\
 <div class="small_val" title="Temperature">'+temp+'°C</div>\
 <div class="small_val" title="Ветер">'+forecast[i].wind.speed+' m/s</div>\
 <div class="small_val_grey" title="Давление">'+forecast[i].main.pressure+'</div>\
</div>'
//<div style="font-size: small; padding: 0pt 3pt;" title="High Temperature">'+temp_max+'°C</div>\
//<div style="color: gray; font-size: small; padding: 0pt 3pt;" title="Low Temperature">'+temp_min+'°C</div>\

	h_body = h_body + h_o;
}

return h_header + h_body + h_footer;

}


//
// generate html for Weather Popoup window
//
function GetWeatherPopupHtml(st)
{

var temp = Math.round((st.main.temp -273.15)*10)/10;
var temp_min = Math.round((st.main.temp_min -273.15)*10)/10;
var temp_max = Math.round((st.main.temp_max -273.15)*10)/10;

if( st.weather.length > 0 ) {
	var icon_url  = 'http://openweathermap.org/img/w/' + st.weather[0].icon + '.png';
	var wtext = st.weather[0].main;
	var wdescription = st.weather[0].description;

}else{
	var dtat = new Date(st.dt * 1000 );
	var times = SunCalc.getTimes(dtat, st.coord.lat, st.coord.lon);
	if( st.dt>times.sunrise && st.dt< times.sunset ) var day='d'; else var day='n';
	var icon_url  = GetWeatherIconDay(st,day)
	var wtext = GetWeatherText2(st);
}


var html = 
'<p class="weather_title"><a class="weather_title_link"  href="http://openweathermap.org/city/'+st.id+'">'+st.name+'</a></p> \
<div class="weather_block">\
 <div class="cur_weather_block" title="'+wdescription+'">\
  <img class="weather_image" alt="'+wdescription+'" src="'+icon_url+'"/>\
  <div class="temp_block" >\
   <div class="big_temp" title="Current Temperature">'+temp+'°</div>\
   <div class="small_temp_block" >\
    <div class="small_temp">'+wtext+'</div>\
   </div>\
  </div>\
 </div>\
 <div class="small_val_grey" title="Min and max temperature">Min t: '+temp_min+' / Max t: '+temp_max+' °C</div>\
 <div class="small_val_grey">Humidity: ' + st.main.humidity +'%</div>\
 <div class="small_val_grey">Wind: '+st.wind.speed+' m/s</div>\
 <div class="small_val_grey">Clouds: '+st.clouds.all+' %</div>\
</div>';

return html;
}

function GetStationPopupHtml(st)
{
var temp = Math.round((st.main.temp -273.15)*10)/10;
var dt = new Date(st.dt * 1000 );

var html_h=
'<p class="weather_title"><a href="http://openweathermap.org/station/'+st.id+'">'+st.name+'</a></p> \
<div class="weather_block">\
	<div class="cur_weather_block" >\
		<img class="station_image" alt="'+GetWeatherText2(st)+'" src="'+GetStationIcon(st)+'"/>\
		<div class="temp_block">\
			<div class="big_temp" title="Current Temperature">'+temp+'°</div>\
		</div>\
	</div>';

if(st.main.humidity)
	html_h += '<div class="small_val_grey">Humidity: ' + st.main.humidity +'%</div>';
if(st.wind)
	html_h += '<div class="small_val_grey">Wind: '+st.wind.speed+' m/s</div>';
if(st.main.pressure)
	html_h += '<div class="small_val_grey">Pressure: '+st.main.pressure+' hpa</div>';

if(st.rain && st.rain['1h'])
	html_h += '<div class="small_val_grey">Rain: '+st.rain['1h']+' mm</div>';

html_h += '<div class="small_val_grey" title="'+dt.toString()+'" >Recived at '+dt.toTimeString()+'</div></div>';

html_h += '</div>';

return html_h;
}


function GetStationIcon(st)
{
	if(st.type == 1)
		return 'http://openweathermap.org/img/s/iplane.png';
	return 'http://openweathermap.org/img/s/istation.png';
}


/*
 Copyright (c) 2011, Vladimir Agafonkin
 SunCalc is a JavaScript library for calculating sun position and sunlight phases.
 https://github.com/mourner/suncalc
*/
(function(c){function n(a){return new Date((a+0.5-o)*p)}var c="undefined"!==typeof exports?exports:c.SunCalc={},b=Math,f=b.PI/180,a=b.sin,i=b.cos,p=864E5,o=2440588,t=357.5291*f,u=0.98560028*f,v=1.9148*f,w=0.02*f,x=3.0E-4*f,y=102.9372*f,q=23.45*f,D=280.16*f,E=360.9856235*f,r=[[-0.83,"sunrise","sunset"],[-0.3,"sunriseEnd","sunsetStart"],[-6,"dawn","dusk"],[-12,"nauticalDawn","nauticalDusk"],[-18,"nightEnd","night"],[6,"goldenHourEnd","goldenHour"]];c.addTime=function(a,b,d){r.push([a,b,d])};c.getTimes=
function(m,h,d){var d=f*-d,h=f*h,m=b.round(m.valueOf()/p-0.5+o-2451545-9.0E-4-d/(2*b.PI)),e=2451545.0009+(0+d)/(2*b.PI)+m,g=t+u*(e-2451545),c=v*a(g)+w*a(2*g)+x*a(3*g),c=g+y+c+b.PI,z=b.asin(a(c)*a(q)),e=e+0.0053*a(g)+-0.0069*a(2*c),s={solarNoon:n(e)},k,A,j,l,B,C;for(k=0,A=r.length;k<A;k+=1)j=r[k],l=j[0],B=j[1],j=j[2],l=2451545.0009+(b.acos((a(l*f)-a(h)*a(z))/(i(h)*i(z)))+d)/(2*b.PI)+m+0.0053*a(g)+-0.0069*a(2*c),C=e-(l-e),s[B]=n(C),s[j]=n(l);return s};c.getPosition=function(c,h,d){var d=f*-d,h=f*h,
c=c.valueOf()/p-0.5+o,e=t+u*(c-2451545),g=v*a(e)+w*a(2*e)+x*a(3*e),g=e+y+g+b.PI,e=b.asin(a(g)*a(q)),g=b.atan2(a(g)*i(q),i(g)),d=D+E*(c-2451545)-d-g;return{azimuth:b.atan2(a(d),i(d)*a(h)-b.tan(e)*i(h)),altitude:b.asin(a(h)*a(e)+i(h)*i(e)*i(d))}}})(this);
