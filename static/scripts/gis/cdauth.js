/*
	This file is part of cdauth’s map.

	cdauth’s map is free software: you can redistribute it and/or modify
	it under the terms of the GNU Affero General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	cdauth’s map is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU Affero General Public License for more details.

	You should have received a copy of the GNU Affero General Public License
	along with cdauth’s map.  If not, see <http://www.gnu.org/licenses/>.

	Obtain the source code from http://gitorious.org/cdauths-map
	or git://gitorious.org/cdauths-map/map.git.
*/

/**
 * requires OpenLayers/Layer/Vector.js
 */

OpenLayers.Layer.cdauth = { };

/**
 * A coordinate grid on the map. Draws coordinate lines on the map in a scale that maxHorizontalLines and maxVerticalLines aren’t exceeded.
*/
OpenLayers.Layer.cdauth.CoordinateGrid = OpenLayers.Class(OpenLayers.Layer.Vector, {
	/**
	 * The maximum number of horizontal coordinate lines on the viewport.
	 * @var Number
	*/
	maxHorizontalLines : 6,

	/**
	 * The maximum number of vertical coordinate lines on the viewport. If set to null, is automatically calculated from the viewport aspect ratio.
	 * @var Number
	*/
	maxVerticalLines : null,

	/**
	 * The line style of normal coordinate lines.
	 * @var OpenLayers.Feature.Vector.style
	*/
	styleMapNormal : { stroke: true, stokeWidth: 1, strokeColor: "black", strokeOpacity: 0.2 },

	/**
	 * The line style of an important coordinate line, such as a number dividable by 10.
	 * @var OpenLayers.Feature.Vector.style
	*/
	styleMapHighlight : { stroke: true, stokeWidth: 2, strokeColor: "black", strokeOpacity: 0.5 },

	/**
	 * The style of the grid line captions that display the degree number.
	 * @var OpenLayers.Feature.Vector.style
	*/
	labelStyleMapNormal : { fontColor: "#777", fontSize: "10px" },

	/**
	 * The style of the highlighted (see styleMapHighlight) grid line captions that display the degree number.
	 * @var OpenLayers.Feature.Vector.style
	*/
	labelStyleMapHighlight : { fontColor: "#666", fontSize: "10px", fontWeight: "bold" },

	horizontalLines : { },
	verticalLines : { },
	degreeLabels : [ ],

	initialize : function(name, options) {
		if(typeof name == "undefined" || name == null)
			name = OpenLayers.i18n("Coordinate grid");
		options = OpenLayers.Util.extend(options, { projection : new OpenLayers.Projection("EPSG:4326") });
		OpenLayers.Layer.Vector.prototype.initialize.apply(this, [ name, options ]);
	},
	setMap : function() {
		OpenLayers.Layer.Vector.prototype.setMap.apply(this, arguments);

		this.map.events.register("moveend", this, this.drawGrid);
		this.map.events.register("mapResize", this, this.drawGrid);
		this.events.register("visibilitychanged", this, this.drawGrid);
	},
	drawGrid : function() {
		if(!this.map || !this.map.getExtent() || !this.getVisibility()) return;

		var extent = this.map.getExtent().transform(this.map.getProjectionObject(), this.projection);
		var maxExtent = this.map.maxExtent.clone().transform(this.map.getProjectionObject(), this.projection);

		var addFeatures = [ ];
		var destroyFeatures = [ ];

		this.destroyFeatures(this.degreeLabels);
		this.degreeLabels = [ ];

		// Display horizontal grid
		var horizontalDistance = (extent.top-extent.bottom)/this.maxHorizontalLines;
		var horizontalDivisor = Math.pow(10, Math.ceil(Math.log(horizontalDistance)/Math.LN10));
		if(5*(extent.top-extent.bottom)/horizontalDivisor <= this.maxHorizontalLines)
			horizontalDivisor /= 5;
		else if(2*(extent.top-extent.bottom)/horizontalDivisor <= this.maxHorizontalLines)
			horizontalDivisor /= 2;

		for(var i in this.horizontalLines)
		{
			var r = i/horizontalDivisor;
			var highlight = (r % 5 == 0);
			var highlighted = (this.horizontalLines[i].style == this.styleMapHighlight);
			if(Math.floor(r) != r || highlight != highlighted)
			{
				destroyFeatures.push(this.horizontalLines[i]);
				delete this.horizontalLines[i];
			}
		}

		for(var coordinate = Math.ceil(extent.bottom/horizontalDivisor)*horizontalDivisor; coordinate < extent.top; coordinate += horizontalDivisor)
		{
			if(coordinate < -90 || coordinate > 90)
				continue;

			var highlight = (coordinate/horizontalDivisor % 5 == 0);

			this.degreeLabels.push(new OpenLayers.Feature.Vector(
				new OpenLayers.Geometry.Point(extent.left, coordinate).transform(this.projection, this.map.getProjectionObject()),
				null,
				OpenLayers.Util.extend({ label: (Math.round(coordinate*100000000)/100000000)+"°", labelAlign: "lm" }, highlight ? this.labelStyleMapHighlight : this.labelStyleMapNormal)
			));

			this.degreeLabels.push(new OpenLayers.Feature.Vector(
				new OpenLayers.Geometry.Point(extent.right, coordinate).transform(this.projection, this.map.getProjectionObject()),
				null,
				OpenLayers.Util.extend({ label: (Math.round(coordinate*100000000)/100000000)+"°", labelAlign: "rm" }, highlight ? this.labelStyleMapHighlight : this.labelStyleMapNormal)
			));

			if(this.horizontalLines[coordinate])
				continue;
			this.horizontalLines[coordinate] = new OpenLayers.Feature.Vector(
				new OpenLayers.Geometry.LineString([ new OpenLayers.Geometry.Point(maxExtent.left, coordinate).transform(this.projection, this.map.getProjectionObject()), new OpenLayers.Geometry.Point(maxExtent.right, coordinate).transform(this.projection, this.map.getProjectionObject()) ]),
				null,
				highlight ? this.styleMapHighlight : this.styleMapNormal
			);
			addFeatures.push(this.horizontalLines[coordinate]);
		}

		// Display vertical grid
		var maxVerticalLines = (this.maxVerticalLines != null ? this.maxVerticalLines : Math.round(this.maxHorizontalLines * this.map.size.w / this.map.size.h));
		var verticalDistance = (extent.right-extent.left)/maxVerticalLines;
		var verticalDivisor = Math.pow(10, Math.ceil(Math.log(verticalDistance)/Math.LN10));
		if(5*(extent.right-extent.left)/verticalDivisor <= maxVerticalLines)
			verticalDivisor /= 5;
		else if(2*(extent.right-extent.left)/verticalDivisor <= maxVerticalLines)
			verticalDivisor /= 2;

		for(var i in this.verticalLines)
		{
			var r = i/verticalDivisor;
			var highlight = (r % 5 == 0);
			var highlighted = (this.verticalLines[i].style == this.styleMapHighlight);
			if(Math.floor(r) != r || highlight != highlighted)
			{
				destroyFeatures.push(this.verticalLines[i]);
				delete this.verticalLines[i];
			}
		}

		for(var coordinate = Math.ceil(extent.left/verticalDivisor)*verticalDivisor; coordinate < extent.right; coordinate += verticalDivisor)
		{
			if(coordinate <= -180 || coordinate > 180)
				continue;

			var highlight = (coordinate/verticalDivisor % 5 == 0);

			this.degreeLabels.push(new OpenLayers.Feature.Vector(
				new OpenLayers.Geometry.Point(coordinate, extent.top).transform(this.projection, this.map.getProjectionObject()),
				null,
				OpenLayers.Util.extend({ label: (Math.round(coordinate*100000000)/100000000)+"°", labelAlign: "ct" }, highlight ? this.labelStyleMapHighlight : this.labelStyleMapNormal)
			));

			this.degreeLabels.push(new OpenLayers.Feature.Vector(
				new OpenLayers.Geometry.Point(coordinate, extent.bottom).transform(this.projection, this.map.getProjectionObject()),
				null,
				OpenLayers.Util.extend({ label: (Math.round(coordinate*100000000)/100000000)+"°", labelAlign: "cb" }, highlight ? this.labelStyleMapHighlight : this.labelStyleMapNormal)
			));

			if(this.verticalLines[coordinate])
				continue;
			this.verticalLines[coordinate] = new OpenLayers.Feature.Vector(
				new OpenLayers.Geometry.LineString([ new OpenLayers.Geometry.Point(coordinate, maxExtent.top).transform(this.projection, this.map.getProjectionObject()), new OpenLayers.Geometry.Point(coordinate, maxExtent.bottom).transform(this.projection, this.map.getProjectionObject()) ]),
				null,
				highlight ? this.styleMapHighlight : this.styleMapNormal
			);
			addFeatures.push(this.verticalLines[coordinate]);
		}

		this.destroyFeatures(destroyFeatures);
		this.addFeatures(addFeatures);
		this.addFeatures(this.degreeLabels);
	}
});