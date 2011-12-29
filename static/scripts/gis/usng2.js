// Library to convert between NAD83 Lat/Lon and US National Grid
// Based on the FGDC-STS-011-2001 spec at http://www.fgdc.gov/standards/projects/FGDC-standards-projects/usng/fgdc_std_011_2001_usng.pdf
// Also based on the UTM library already in GeoMOOSE
// (c) Jim Klassen 4/2008
// Not tested in southern hemisphere...
// Known to fail for USNG zones A and B

/*
 * License:
 * 
 * Copyright (c) 2008-2009 James Klassen
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the 'Software'), to
 * deal in the Software without restriction, including without limitation the
 * rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
 * sell copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in
 * all copies of this Software or works derived from this Software.
 * 
 * THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
 * IN THE SOFTWARE.
 */

function USNG2() {
	// Note: grid locations are the SW corner of the grid square (because easting and northing are always positive)
	//                   0   1   2   3   4   5   6   7   8   9  10  11  12  13  14  15  16  17  18  19   x 100,000m northing
	var NSLetters135 = ['A','B','C','D','E','F','G','H','J','K','L','M','N','P','Q','R','S','T','U','V'];
	var NSLetters246 = ['F','G','H','J','K','L','M','N','P','Q','R','S','T','U','V','A','B','C','D','E'];

	//                  1   2   3   4   5   6   7   8   x 100,000m easting
	var EWLetters14 = ['A','B','C','D','E','F','G','H'];
	var EWLetters25 = ['J','K','L','M','N','P','Q','R'];
	var EWLetters36 = ['S','T','U','V','W','X','Y','Z'];

	//                  -80  -72  -64  -56  -48  -40  -32  -24  -16  -8   0    8   16   24   32   40   48   56   64   72   (*Latitude) 
	var GridZones    = ['C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X'];
	var GridZonesDeg = [-80, -72, -64, -56, -48, -40, -32, -24, -16, -8,  0,   8,  16,  24,  32,  40,  48,  58,  64,  72];
	
	// TODO: This is approximate and actually depends on longitude too.
	var GridZonesNorthing = new Array(20);	
	for(i = 0 ; i < 20; i++) {
		GridZonesNorthing[i] = 110946.259 * GridZonesDeg[i]; // == 2 * PI * 6356752.3 * (latitude / 360.0)
	}

	// http://en.wikipedia.org/wiki/Great-circle_distance
	// http://en.wikipedia.org/wiki/Vincenty%27s_formulae 
	this.llDistance = function(ll_start, ll_end)
	{
		lat_s = ll_start.lat * Math.PI / 180;
		lat_f = ll_end.lat * Math.PI / 180;
		d_lon = (ll_end.lon - ll_start.lon) * Math.PI / 180;
		return( Math.atan2( Math.sqrt( Math.pow(Math.cos(lat_f) * Math.sin(d_lon),2) + Math.pow(Math.cos(lat_s)*Math.sin(lat_f) - Math.sin(lat_s)*Math.cos(lat_f)*Math.cos(d_lon),2)) ,
							Math.sin(lat_s)*Math.sin(lat_f) + Math.cos(lat_s)*Math.cos(lat_f)*Math.cos(d_lon) )
				);
	}

	/* Returns a USNG String for a UTM point, and zone id's, and precision
	 * utm_zone => 15 ; grid_zone => 'T' (calculated from latitude); 
	 * utm_easting => 491000, utm_northing => 49786000; precision => 2 
	 */
	this.fromUTM = function(utm_zone, grid_zone, utm_easting, utm_northing, precision) {
		var utm_zone;
		var grid_zone;
		var grid_square;
		var grid_easting;
		var grid_northing;
		var precision;
		
		grid_square_set = utm_zone % 6;
		
		ew_idx = Math.floor(utm_easting / 100000) - 1; // should be [100000, 9000000]
		ns_idx = Math.floor((utm_northing % 2000000) / 100000); // should [0, 10000000) => [0, 2000000)
		switch(grid_square_set) {
			case 1:
				grid_square = EWLetters14[ew_idx] + NSLetters135[ns_idx];
				break;
			case 2:
				grid_square = EWLetters25[ew_idx] + NSLetters246[ns_idx];
				break;
			case 3:
				grid_square = EWLetters36[ew_idx] + NSLetters135[ns_idx];
				break;
			case 4:
				grid_square = EWLetters14[ew_idx] + NSLetters246[ns_idx];
				break;
			case 5:
				grid_square = EWLetters25[ew_idx] + NSLetters135[ns_idx];
				break;
			case 0: // Calculates as zero, but is technically 6 */
				grid_square = EWLetters36[ew_idx] + NSLetters246[ns_idx];
				break;
			default:
				throw("USNG: can't get here");
		}

		
		// Calc Easting and Northing integer to 100,000s place
		var easting  = Math.floor(utm_easting % 100000).toString();
		var northing = Math.floor(utm_northing % 100000).toString()

		// Pad up to meter precision (5 digits)
		while(easting.length < 5) easting = '0' + easting;
		while(northing.length < 5) northing = '0' + northing;
		
		if(precision > 5) {
			// Calculate the fractional meter parts
			digits = precision - 5;
			grid_easting  = easting + (utm_easting % 1).toFixed(digits).substr(2,digits);
			grid_northing = northing + (utm_northing % 1).toFixed(digits).substr(2,digits);		
		} else {
			// Remove unnecessary digits
			grid_easting  = easting.substr(0, precision);
			grid_northing = northing.substr(0, precision);
		}
		
		usng_string = String(utm_zone) + grid_zone + grid_square + grid_easting + grid_northing; 
		return(usng_string);
	}

	// Calculate UTM easting and northing from full, parsed USNG coordinate
	this.toUTMFromFullParsedUSNG = function(utm_zone, grid_zone, grid_square, easting, northing, precision)
	{
		var utm_easting = 0;
		var utm_northing = 0;

		var grid_square_set = utm_zone % 6;
		var ns_grid;
		var ew_grid;
		switch(grid_square_set) {
			case 1:
				ns_grid = NSLetters135;
				ew_grid = EWLetters14;
				break;
			case 2:
				ns_grid = NSLetters246;
				ew_grid = EWLetters25;
				break;
			case 3:
				ns_grid = NSLetters135;
				ew_grid = EWLetters36;
				break;
			case 4:
				ns_grid = NSLetters246;
				ew_grid = EWLetters14;
				break;
			case 5:
				ns_grid = NSLetters135;
				ew_grid = EWLetters25;
				break;
			case 0: // grid_square_set will == 0, but it is technically group 6 
				ns_grid = NSLetters246;
				ew_grid = EWLetters36;
				break;
			default:
				throw("Can't get here");
		}
		ew_idx = ew_grid.indexOf(grid_square[0]);
		ns_idx = ns_grid.indexOf(grid_square[1]);
		
		if(ew_idx == -1 || ns_idx == -1)
			throw("USNG: Invalid USNG 100km grid designator.");
			//throw(RangeError("USNG: Invalid USNG 100km grid designator."));
		
		utm_easting = ((ew_idx + 1) * 100000) + easting; // Should be [100000, 9000000]
		utm_northing = ((ns_idx + 0) * 100000) + northing; // Should be [0, 2000000)

		// TODO: this really depends on easting too...
		// At this point know UTM zone, Grid Zone (min latitude), and easting
		// Right now this is lookup table returns a max number based on lon == utm zone center 	
		min_northing = GridZonesNorthing[GridZones.indexOf(grid_zone)]; // Unwrap northing to ~ [0, 10000000]
		utm_northing += 2000000 * Math.ceil((min_northing - utm_northing) / 2000000);

		// Check that the coordinate is within the utm zone and grid zone specified:
		ll = utm_proj.invProj(utm_zone, utm_easting, utm_northing);
		ll_utm_zone = Math.floor((ll.lon - (-180.0)) / 6.0) + 1;
		ll_grid_zone = GridZones[Math.floor((ll.lat - (-80.0)) / 8)];

		// If error from the above TODO mattered... then need to move north a grid
		if( ll_grid_zone != grid_zone) {
			utm_northing -= 2000000;
			ll = utm_proj.invProj(utm_zone, utm_easting, utm_northing);
			ll_utm_zone = Math.floor((ll.lon - (-180.0)) / 6.0) + 1;
			ll_grid_zone = GridZones[Math.floor((ll.lat - (-80.0)) / 8)];
		}

		if(ll_utm_zone != utm_zone || ll_grid_zone != grid_zone) {
			throw("USNG: calculated coordinate not in correct UTM or grid zone! Supplied: "+utm_zone+grid_zone+" Calculated: "+ll_utm_zone+ll_grid_zone);
			//throw(RangeError("USNG: calculated coordinate not in correct UTM or grid zone! Supplied: "+utm_zone+grid_zone+" Calculated: "+ll_utm_zone+ll_grid_zone));
		}
		
		return { zone : utm_zone, easting : utm_easting, northing : utm_northing, precision : precision };	
	}

	/* Method to convert a USNG coordinate string into a NAD83/WGS84 LonLat Point 
	 * First parameter: usng = A valid USNG coordinate string (possibly truncated)
	 *	Possible cases:
	 *		Full USNG: 14TPU3467
	 *		Truncated:   TPU3467
	 *		Truncated:    PU3467
	 *		Truncated:      3467
	 *		Truncated: 14TPU
	 *		Truncated: 14T
	 *		Truncated:    PU
	 * Second parameter: a LonLat point to use to disambiguate a truncated USNG point
	 * Returns: The LonLat point
	 */ 
	this.toUTM = function(usng, initial_lonlat) {
		// Parse USNG into component parts
		var easting = 0;
		var northing = 0;
		var precision = 0;

		var digits = null; /* don't really need this if using call to parsed... */
		var grid_square = null;
		var grid_zone = null;
		var utm_zone = null;
		
		// Remove Whitespace (shouldn't be any)
		usng = usng.replace(/ /g, "");

		// Strip Coordinate values off of end, if any
		// This will be any trailing digits.
		re = new RegExp("([0-9]+)$");
		fields = re.exec(usng);
		if(fields) {
			digits = fields[0];
			precision = digits.length / 2; // TODO: throw an error if #digits is odd.
			scale_factor = Math.pow(10, (5 - precision)); // 1 digit => 10k place, 2 digits => 1k ...
			easting = Number(digits.substr(0, precision)) * scale_factor;
			northing = Number(digits.substr(precision, precision)) * scale_factor;
		}
		usng = usng.substr(0, usng.length-(precision*2));

		// Get 100km Grid Designator, if any
		re = new RegExp("([A-Z][A-Z]$)");
		fields = re.exec(usng);
		if(fields) {
			grid_square = fields[0];
		}
		usng = usng.substr(0, usng.length - 2);

		// Get UTM and Grid Zone
		re = new RegExp("([0-9]+)([A-Z])");
		fields = re.exec(usng);
		if(fields) {
			utm_zone = fields[1];
			grid_zone = fields[2];
		}

		// Use lonlat Point as approx Location to fill in missing prefix info
		// Note: actual prefix need not be the same as that of the llPoint (we could cross 100km grid squares, utm zones, etc.)
		// Our job is to find the closest point to the llPoint given what we know about the USNG point.

		// Calculate the UTM zone, easting and northing from what we know
		
		/* Method: we can only guess missing prefix information so our cases are:
		 * We have everything (14TPU)
		 * We are missing the UTM zone (PU)
		 * We are missing the UTM zone and the grid designator
		 * TODO: Need to throw an exception if utm_zone and no grid_zone as invalid
		 * TODO: Also need to throw an exception if don't have at least one of grid_zone and coordinate...maybe
		 * TODO: Error if grid_zone is not in GridZones
		 */	
		if(utm_zone && grid_zone && grid_square) {
			; // We have everything so there is nothing more to do.
		} else if(grid_square && initial_lonlat) {
			// We need to find the utm_zone and grid_zone
			// We know the grid zone so first we need to find the closest matching grid zone
			// to the initial point. Then add in the easting and northing (if any).
			//throw("USNG: Truncated coordinate support not implemented");
			
			// Linear search all possible points (TODO: try to put likely guesses near top of list)
			var min_arc_distance = 1000;
			var min_utm_zone  = null;
			var min_grid_zone = null;
			
			ll_utm_zone = Math.floor((initial_lonlat.lon - (-180.0)) / 6.0) + 1;
			ll_grid_zone_idx = Math.floor((initial_lonlat.lat - (-80.0)) / 8); 

			// Check the min ranges that need to be searched based on the spec.
			// Need to wrap UTM zones mod 60
			for(utm_zone = ll_utm_zone - 1; utm_zone <= ll_utm_zone+1; utm_zone++) { // still true at 80*?
				for(grid_zone_idx = 0; grid_zone_idx < 20; grid_zone_idx++) {
					grid_zone = GridZones[grid_zone_idx];
					try {
						//alert(utm_zone + grid_zone + grid_square + digits);
						result = this.toLonLat((utm_zone%60) + grid_zone + grid_square + digits); // usng should be [A-Z][A-Z][0-9]+

						arc_distance = this.llDistance(initial_lonlat, result);
						if(arc_distance < min_arc_distance) {
							min_arc_distance = arc_distance;
							min_utm_zone = utm_zone % 60;
							min_grid_zone = grid_zone;
						}
					} catch(e) {
						;//alert("USNG: upstream: "+e); // catch range errors and ignore
					}
				}
			}
				
			if(min_utm_zone && min_grid_zone) {
				utm_zone = min_utm_zone;
				grid_zone = min_grid_zone;
			} else {
				throw("USNG: Couldn't find a match");
			}
		} else if(initial_lonlat) {
			// We need to find the utm_zone, grid_zone and 100km grid designator
			// Find the closest grid zone within the specified easting and northing
			// Note: may cross UTM zone boundries!
			// Linear search all possible points (TODO: try to put likely guesses near top of list)
			var min_arc_distance = 1000;
			var min_utm_zone  = null;
			var min_grid_zone = null;
			var min_grid_square = null;
			
			var ll_utm_zone = Math.floor((initial_lonlat.lon - (-180.0)) / 6.0) + 1;
			var ll_grid_zone_idx = Math.floor((initial_lonlat.lat - (-80.0)) / 8); 

			// Check the min ranges that need to be searched based on the spec.
			for(utm_zone = ll_utm_zone-1; utm_zone <= ll_utm_zone+1; utm_zone++) { // still true at 80*?
				for(grid_zone_idx = ll_grid_zone_idx - 1; grid_zone_idx <= ll_grid_zone_idx + 1; grid_zone_idx++) {
					grid_zone = GridZones[grid_zone_idx];
					var grid_square_set = utm_zone % 6;
					var ns_grid;
					var ew_grid;
					switch(grid_square_set) {
						case 1:
							ns_grid = NSLetters135;
							ew_grid = EWLetters14;
							break;
						case 2:
							ns_grid = NSLetters246;
							ew_grid = EWLetters25;
							break;
						case 3:
							ns_grid = NSLetters135;
							ew_grid = EWLetters36;
							break;
						case 4:
							ns_grid = NSLetters246;
							ew_grid = EWLetters14;
							break;
						case 5:
							ns_grid = NSLetters135;
							ew_grid = EWLetters25;
							break;
						case 0: // grid_square_set will == 0, but it is technically group 6 
							ns_grid = NSLetters246;
							ew_grid = EWLetters36;
							break;
						default:
							throw("Can't get here");
					}
					//alert(utm_zone + grid_zone);
					for(ns_idx = 0; ns_idx < 20; ns_idx++) {
						for(ew_idx = 0; ew_idx < 8; ew_idx++) {
							try {
								grid_square = ew_grid[ew_idx]+ns_grid[ns_idx];
								result = this.toLonLat((utm_zone%60) + grid_zone + grid_square + digits); // usng should be [A-Z][A-Z][0-9]+

								arc_distance = this.llDistance(initial_lonlat, result);
								if(arc_distance < min_arc_distance) {
									min_arc_distance = arc_distance;
									min_utm_zone = utm_zone % 60;
									min_grid_zone = grid_zone;
									min_grid_square = grid_square;
								}
							} catch(e) {
								; //alert("USNG: upstream: "+e); // catch range errors and ignore
							}
						}
					}
				}
			}
				
			if(min_utm_zone && min_grid_zone) {
				utm_zone = min_utm_zone;
				grid_zone = min_grid_zone;
				grid_square = min_grid_square;
			} else {
				throw("USNG: Couldn't find a match");
			}

		} else {
			throw("USNG: Not enough information to locate point.");
		}
		return(this.toUTMFromFullParsedUSNG(utm_zone, grid_zone, grid_square, easting, northing, precision));
	}

	// Converts a lat, lon point (NAD83) into a USNG coordinate string
	// of precision where precision indicates the number of digits used
	// per coordinate (0 = 100,000m, 1 = 10km, 2 = 1km, 3 = 100m, 4 = 10m, ...)
	this.fromLonLat = function(lonlat, precision) {
		usng_string = new String();
		var lon = lonlat.lon;
		var lat = lonlat.lat;

		// Normalize Latitude and Longitude
		while(lon < -180) {
			lon += 180;
		}
		while(lon > 180) {
			lon -= 180;
		}
		
		// Calculate UTM Zone number from Longitude
		// -180 = 180W is grid 1... increment every 6 degrees going east
		// Note [-180, -174) is in grid 1, [-174,-168) is 2, [174, 180) is 60 
		utm_zone = Math.floor((lon - (-180.0)) / 6.0) + 1;
		
		// Calculate USNG Grid Zone Designation from Latitude
		// Starts at -80 degrees and is in 8 degree increments
		if(! ((lat > -80) && (lat < 80) )) {
			throw("USNG: Latitude must be between -80 and 80. (Zones A and B are not implemented yet.)");
		}
		
		var grid_zone = GridZones[Math.floor((lat - (-80.0)) / 8)]; 
		var utm_pt = utm_proj.proj(utm_zone, lon, lat);
		
		return this.fromUTM(utm_zone, grid_zone, utm_pt.utm_easting, utm_pt.utm_northing, precision);
	}
	
	this.toLonLat = function(usng, initial_lonlat)
	{
		result = this.toUTM(usng, initial_lonlat);
		ll = utm_proj.invProj(result.zone, result.easting, result.northing);
		ll.precision = result.precision;
		return (ll);
	}
	
	this.UTM = function() {		
		// Functions to convert between lat,lon and utm. Derived from visual basic
		// routines from Craig Perault. This assumes a NAD83 datum.
		
		// constants
		var MajorAxis = 6378137.0;
		var MinorAxis = 6356752.3;
		var Ecc = (MajorAxis * MajorAxis - MinorAxis * MinorAxis) / (MajorAxis * MajorAxis);
		var Ecc2 = Ecc / (1.0 - Ecc);
		var K0 = 0.9996;
		var E4 = Ecc * Ecc;
		var E6 = Ecc * E4;
		var degrees2radians = Math.PI / 180.0;
		
		// Computes the meridian distance for the GRS-80 Spheroid.
		// See equation 3-22, USGS Professional Paper 1395.
		function meridianDist(lat) {
			var c1 = MajorAxis * (1 - Ecc / 4 - 3 * E4 / 64 - 5 * E6 / 256);
			var c2 = -MajorAxis * (3 * Ecc / 8 + 3 * E4 / 32 + 45 * E6 / 1024);
			var c3 = MajorAxis * (15 * E4 / 256 + 45 * E6 / 1024);
			var c4 = -MajorAxis * 35 * E6 / 3072;
			
			return(c1 * lat + c2 * Math.sin(lat * 2) + c3 * Math.sin(lat * 4) + c4 * Math.sin(lat * 6));
		}
		
		// Convert lat/lon (given in decimal degrees) to UTM, given a particular UTM zone.
		this.proj = function(zone, in_lon, in_lat) {
			var centeralMeridian = -((30 - zone) * 6 + 3) * degrees2radians;
			
			var lat = in_lat * degrees2radians;
			var lon = in_lon * degrees2radians;
			
			var latSin = Math.sin(lat);
			var latCos = Math.cos(lat);
			var latTan = latSin / latCos;
			var latTan2 = latTan * latTan;
			var latTan4 = latTan2 * latTan2;
			
			var N = MajorAxis / Math.sqrt(1 - Ecc * (latSin*latSin));
			var c = Ecc2 * latCos*latCos;
			var a = latCos * (lon - centeralMeridian);
			var m = meridianDist(lat);
			
			var temp5 = 1.0 - latTan2 + c;
			var temp6 = 5.0 - 18.0 * latTan2 + latTan4 + 72.0 * c - 58.0 * Ecc2;
			var temp11 = Math.pow(a, 5);
			
			x = K0 * N * (a + (temp5 * Math.pow(a, 3)) / 6.0 + temp6 * temp11 / 120.0) + 500000;
			
			var temp7 = (5.0 - latTan2 + 9.0 * c + 4.0 * (c*c)) * Math.pow(a,4) / 24.0;
			var temp8 = 61.0 - 58.0 * latTan2 + latTan4 + 600.0 * c - 330.0 * Ecc2;
			var temp9 = temp11 * a / 720.0;
			
			y = K0 * (m + N * latTan * ((a * a) / 2.0 + temp7 + temp8 * temp9))
				
			return( { utm_zone: zone, utm_easting : x, utm_northing : y } );
		}
		
		// Convert UTM coordinates (given in meters) to Lat/Lon (in decimal degrees), given a particular UTM zone.
		this.invProj = function(zone, easting, northing) {
			var centeralMeridian = -((30 - zone) * 6 + 3) * degrees2radians;
			
			var temp1 = Math.sqrt(1.0 - Ecc);
			var ecc1 = (1.0 - temp1) / (1.0 + temp1);
			var ecc12 = ecc1 * ecc1;
			var ecc13 = ecc1 * ecc12;
			var ecc14 = ecc12 * ecc12;
			
			easting = easting - 500000.0;
			
			var m = northing / K0;
			var um = m / (MajorAxis * (1.0 - (Ecc / 4.0) - 3.0 * (E4 / 64.0) - 5.0 * (E6 / 256.0)));
			
			var temp8 = (1.5 * ecc1) - (27.0 / 32.0) * ecc13;
			var temp9 = ((21.0 / 16.0) * ecc12) - ((55.0 / 32.0) * ecc14);
			
			var latrad1 = um + temp8 * Math.sin(2 * um) + temp9 * Math.sin(4 * um) + (151.0 * ecc13 / 96.0) * Math.sin(6.0 * um);
			
			var latsin1 = Math.sin(latrad1);
			var latcos1 = Math.cos(latrad1);
			var lattan1 = latsin1 / latcos1;
			var n1 = MajorAxis / Math.sqrt(1.0 - Ecc * latsin1 * latsin1);
			var t2 = lattan1 * lattan1;
			var c1 = Ecc2 * latcos1 * latcos1;
			
			var temp20 = (1.0 - Ecc * latsin1 * latsin1);
			var r1 = MajorAxis * (1.0 - Ecc) / Math.sqrt(temp20 * temp20 * temp20);
			
			var d1 = easting / (n1*K0);
			var d2 = d1 * d1;
			var d3 = d1 * d2;
			var d4 = d2 * d2;
			var d5 = d1 * d4;
			var d6 = d3 * d3;
			
			var t12 = t2 * t2;
			var c12 = c1 * c1;
			
			temp1 = n1 * lattan1 / r1;
			temp2 = 5.0 + 3.0 * t2 + 10.0 * c1 - 4.0 * c12 - 9.0 * Ecc2;
			temp4 = 61.0 + 90.0 * t2 + 298.0 * c1 + 45.0 * t12 - 252.0 * Ecc2 - 3.0 * c12;
			temp5 = (1.0 + 2.0 * t2 + c1) * d3 / 6.0;
			temp6 = 5.0 - 2.0 * c1 + 28.0 * t2 - 3.0 * c12 + 8.0 * Ecc2 + 24.0 * t12;

			lat = (latrad1 - temp1 * (d2 / 2.0 - temp2 * (d4 / 24.0) + temp4 * d6 / 720.0)) * 180 / Math.PI;
			lon = (centeralMeridian + (d1 - temp5 + temp6 * d5 / 120.0) / latcos1) * 180 / Math.PI;
			easting = easting + 500000.0;
			
			return ({ lon: lon, lat: lat});
		}
		
	}
	utm_proj = new this.UTM();
}
