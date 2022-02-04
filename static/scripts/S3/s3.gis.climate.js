// Workaround: see http://stackoverflow.com/questions/4728852/forcing-an-openlayers-markers-layer-to-draw-on-top-and-having-selectable-layers
// This fixes a problem whereby the marker layer doesn't 
// respond to click events
OpenLayers.Handler.Feature.prototype.activate = function() {
    var activated = false;
    if (OpenLayers.Handler.prototype.activate.apply(this, arguments)) {
        //this.moveLayerToTop();
        this.map.events.on({
            "removelayer": this.handleMapEvents,
            "changelayer": this.handleMapEvents,
            scope: this
        });
        activated = true;
    }
    return activated;
};

// Workaround:
// for some reason some features remain styled after being unselected
// so just unselect all features. Takes longer but doesn't confuse the user.
OpenLayers.Control.SelectFeature.prototype.unselectAll = function(options) {
    var layers = this.layers || [this.layer];
    var layer, feature;
    for (var l=0; l<layers.length; ++l) {
        layer = layers[l];
        for (var i=layer.features.length-1; i>=0; --i) {
            feature = layer.features[i];
            if(!options || options.except != feature) {
                this.unselect(feature);
            }
        }
    }
};

function each(array, fn) {
    for (var i = 0; i < array.length; ++i) {
        fn(array[i], i);
    }
}

function base64_encode(s) {
    var base64chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'.split('');
    var r = ''; 
    var p = ''; 
    var c = s.length % 3;
    if (c > 0) { 
        for (; c < 3; c++) { 
            p += '='; 
            s += '\0'; 
        } 
    }
    for (c = 0; c < s.length; c += 3) {
        if (c > 0 && (c / 3 * 4) % 76 === 0) { 
            r += '\r\n'; 
        }
        var n = (
            (s.charCodeAt(c) << 16) + 
            (s.charCodeAt(c+1) << 8) + 
            s.charCodeAt(c+2)
        );
        n = [
            (n >>> 18) & 63, 
            (n >>> 12) & 63, 
            (n >>> 6) & 63, 
            n & 63
        ];
        r += (
            base64chars[n[0]] + 
            base64chars[n[1]] + 
            base64chars[n[2]] + 
            base64chars[n[3]]
        );
    }
    return r.substring(0, r.length - p.length) + p;
}

function create_bitmap_data() {
    function encode(number, bytes) {
        var oldbase = 1;
        var string = '';
        for (var x = 0; x < bytes; x++) {
            var byt = 0;
            if (number !== 0) {
                var base = oldbase * 256;
                byt = number % base;
                number = number - byt;
                byt = byt / oldbase;
                oldbase = base;
            }
            string += String.fromCharCode(byt);
        }
        return string;
    }
    var width = colour_map.length;

    var data = [];
    for (var x = 0; x < width; x++) {
        var value = colour_map[Math.floor((x/width) * colour_map.length)];
        data.push(
            String.fromCharCode(
                value[2],
                value[1],
                value[0]
            )
        );
    }
    padding = (
        width % 4 ? 
        '\0\0\0'.substr((width % 4) - 1, 3):
        ''
    );
    data.push(padding + padding + padding);
    var data_bytes = data.join('');

    var info_header = (
        encode(40, 4) + // Number of bytes in the DIB header (from this point)
        encode(width, 4) + // Width of the bitmap in pixels
        encode(1, 4) + // Height of the bitmap in pixels
        '\x01\0' + // Number of color planes being used
        encode(24, 2) + // Number of bits per pixel
        '\0\0\0\0'+ // BI_RGB, no Pixel Array compression used
        encode(data_bytes.length, 4)+ // Size of the raw data in the Pixel Array (including padding)
        encode(2835, 4)+ //Horizontal resolution of the image
        encode(2835, 4)+ // Vertical resolution of the image
        '\0\0\0\0\0\0\0\0'
    );

    var header_length = 14 + info_header.length;
    return (
        'BM'+
        encode(header_length + data_bytes.length, 4)+
        '\0\0\0\0'+
        encode(header_length, 4)
    ) + info_header + data_bytes;
}

function node(tag_name, attrs, children) {
    var result = $(document.createElement(tag_name));
    for (var key in attrs) {
        if (attrs.hasOwnProperty(key)) {
            result.attr(key, attrs[key]);
        }
    }
    result.append.apply(result, children);
    return result;
}
function NodeGenerator(tag_name) {
    return function(/* attrs, child1... */) {
        var attrs = Array.prototype.shift.apply(arguments);
        return node(tag_name, attrs, arguments);
    };
}

INPUT = NodeGenerator('input');
DIV = NodeGenerator('div');
TABLE = NodeGenerator('table');
TR = NodeGenerator('tr');
TD = NodeGenerator('td');
SPAN = NodeGenerator('span');
IMG = NodeGenerator('img');
TEXTAREA = NodeGenerator('textarea');

var ColourKey = OpenLayers.Class(OpenLayers.Control, {
    /* The colour key is implemented as an OpenLayers control
       so that it gets rendered on the printed map
       attributes:
         plugin
    */
    destroy: function() {
        var colour_scale = this;
        colour_scale.deactivate();
        OpenLayers.Control.prototype.destroy.apply(colour_scale, arguments);
    },

    activate: function() {
        var colour_scale = this;
        if (OpenLayers.Control.prototype.activate.apply(colour_scale, arguments)) {
            // show colours
            colour_scale.$key_colour_scale_img.attr(
                'src',
                'data:image/bmp;base64,'+
                base64_encode(create_bitmap_data())
            );
            // when the user changes limits, the map colours update instantly
            colour_scale.use_callback = function() {
                if (!!colour_scale.use_limits) {
                    colour_scale.with_limits(colour_scale.use_limits);
                }
            };
            colour_scale.$lower_limit.change(colour_scale.use_callback);
            colour_scale.$upper_limit.change(colour_scale.use_callback);
            return true;
        } else {
            return false;
        }
    },

    deactivate: function() {
        var colour_scale = this;
        if (OpenLayers.Control.prototype.deactivate.apply(colour_scale, arguments)) {
            return true;
        } else {
            return false;
        }
    },

    with_limits: function(use_limits) {
        // immediately use the limits
        var colour_scale = this;
        use_limits(
            parseFloat(colour_scale.$lower_limit.attr('value')),
            parseFloat(colour_scale.$upper_limit.attr('value'))
        );
    },

    on_change: function(use_limits) {
        // provide a callback for when the limits change
        // use_limits needs to accept min and max
        this.use_limits = use_limits;
    },

    update_from: function(new_units, max_value, min_value) {
        // Sets units, and limits (rounded sensibly) from supplied arguments.
        // If the limit lock checkbox is checked, doesn't change limits unless
        // the units change.
        // Calls the callback supplied in on_change with the limits.
        var colour_scale = this;

        var previous_units = colour_scale.$units.html();
        colour_scale.$units.html(new_units);

        if (// user can lock limits
            !colour_scale.$limit_lock.is(':checked')
            // but if units change, old limits become meaningless
            || previous_units != new_units) {
            // sensible range
            var significant_digits = 2;
            function scaling_factor(value) {
                return 10.0^(
                    Math.floor(
                        Math.log(Math.abs(value)) / Math.LN10
                    ) - (significant_digits - 1)
                );
            }
            function sensible(value, round) {
                if (value === 0.0) {
                    return 0.0;
                } else {
                    factor = scaling_factor(value);
                    return round(value/factor) * factor;
                }
            }
            range_mag = scaling_factor(
                sensible(max_value, Math.ceil) - 
                sensible(min_value, Math.floor)
            );
                
            // function set_scale(min_value, max_value) {
            min_value = Math.floor(min_value/range_mag) * range_mag;
            max_value = Math.ceil(max_value/range_mag) * range_mag;
            
            colour_scale.$lower_limit.attr('value', min_value);
            colour_scale.$upper_limit.attr('value', max_value);
        }
        else {
            min_value = parseFloat(colour_scale.$lower_limit.attr('value'));
            max_value = parseFloat(colour_scale.$upper_limit.attr('value'));
        }
        colour_scale.min_value = min_value;
        colour_scale.max_value = max_value;
        colour_scale.use_callback();
    },

    draw: function() {
        var colour_scale = this;
        OpenLayers.Control.prototype.draw.apply(colour_scale, arguments);

        colour_scale.$lower_limit = INPUT({size:5, value:'Min'});
        colour_scale.$upper_limit = INPUT({size:5, value:'Max', 
            style:'text-align:right;'
        });
        colour_scale.$limit_lock = INPUT({type: 'checkbox', name: 'key-lock', id: 'key_lock'});
        colour_scale.$limit_lock_label = $('<label for="key_lock">Lock limits between queries</label>');
        colour_scale.$key_colour_scale_img = IMG({width:'100%', height:'15px'});
        colour_scale.$units = SPAN({}, 'Units');
        var $div = colour_scale.$inner_div = DIV({
                style:'width: 180px; position:absolute; top: 10px; left:55px;'
            },
            TABLE({
                    width:'100%',
                    style:'background-color:white; border:1px solid #CCC;'
                },
                TR({}, 
                    TD({
                            style:'width:33%; text-align:left;'
                        },
                        colour_scale.$lower_limit
                    ),
                    TD({
                            style:'text-align:center;'
                        },
                        colour_scale.$units
                    ),
                    TD({
                            style:'width:33%; text-align:right;'
                        },
                        colour_scale.$upper_limit
                    )
                )
                // key_scale_tr (unused)
            ),
            colour_scale.$key_colour_scale_img,
            colour_scale.$limit_lock,
            colour_scale.$limit_lock_label
        );
        /*
        // code that draws a scale on the colours as lines, to aid 
        // interpretation. Doesn't work well for some scales
        var scale_divisions = range/range_mag;
        alert(''+range+' '+range_mag+' '+scale_divisions);

        var scale_html = '';
        for (
            var i = 0;
            i < scale_divisions-1;
            i++;
        ) {
            scale_html += '<td style="border-left:1px solid black">&nbsp;</td>';
        }
        $('#id_key_scale_tr').html(
            scale_html+
            '<td style="border-left:1px solid black; border-right:1px solid black;">&nbsp;</td>'
        );
        */

        $(colour_scale.div).append($div);
        $div.show();
        return colour_scale.div;
    },

    print_mode: function() {
        var colour_scale = this;
        colour_scale.$limit_lock.hide();
        colour_scale.$limit_lock_label.hide();
        colour_scale.$inner_div.css('width', 300);
        colour_scale.$inner_div.css('left', 10);
    },
    CLASS_NAME: 'ColourKey'
});

var TextAreaAutoResizer = function(
    $text_area,
    min_height,
    max_height
) {
    var resizer = this;
    resizer.min_height = min_height || 0;
    resizer.max_height = max_height || Infinity;

    function resize(force) {
        var value_length = $text_area.val().length, 
            $text_area_width = $text_area.width;
        if (force || (value_length != resizer.previous_value_length || 
                      $text_area_width != resizer.previous_width)) {
            $text_area.height(0);
            var height = Math.max(
                resizer.min_height,
                Math.min(
                    $text_area[0].scrollHeight,
                    resizer.max_height
                )
            );
            $text_area.css('overflow', 
                $text_area.height() > height ? 'auto' : 'hidden'
            );
            $text_area.height(height);

            resizer.previous_value_length = value_length;
            resizer.previous_width = $text_area_width;
        }
        return true;
    }
    resizer.resize = resize;
    resize();
    $text_area.css('padding-top', 0);
    $text_area.css('padding-bottom', 0);
    $text_area.on('keyup', resize);
    $text_area.on('focus', resize);
    return resizer;
};

var QueryBox = OpenLayers.Class(OpenLayers.Control, {
    CLASS_NAME: 'QueryBox',
    destroy: function() {
        var query_box = this;
        query_box.deactivate();
        query_box.resizer.destroy();
        delete query_box.resizer;
        OpenLayers.Control.prototype.destroy.apply(query_box, arguments);
    },

    activate: function() {
        var query_box = this;
        if (OpenLayers.Control.prototype.activate.apply(query_box, arguments)) {
            return true;
        } else {
            return false;
        }
    },

    deactivate: function() {
        var query_box = this;
        if (OpenLayers.Control.prototype.deactivate.apply(query_box, arguments)) {
            return true;
        } else {
            return false;
        }
    },

    update: function(query_expression) {
        var query_box = this;
        $(query_box.div).css('background-color', 'white');
        query_box.$text_area.val(query_expression);
        query_box.$update_button.hide();
        query_box.previous_query = query_expression;
        query_box.resizer.resize();
    },

    error: function(position) {
        // inform the query box that there is an error, 
        var query_box = this;
        var text = query_box.$text_area.val();
        var message = '# Syntax error (highlighted):\n';
        if (text.substr(0, message.length) == message) {
            message = '';
        }
        // highlight where it starts
        var following_text = text.substr(position);
        var selection_size = following_text.search(new RegExp('\\s|$'));
        if (selection_size + message.length <= 0) {
            selection_size = following_text.search(new RegExp('\n|$'));
        }
        query_box.$text_area.blur();

        query_box.$text_area.val(message + text);

        var textarea = query_box.$text_area[0];
        textarea.setSelectionRange(
            position + message.length, 
            position + message.length + selection_size
        );
        $(query_box.div).css('background-color', 'red');
    },

    draw: function() {
        var query_box = this;
        OpenLayers.Control.prototype.draw.apply(query_box, arguments);
        var $query_box_div = $(query_box.div);
        var $text_area = query_box.$text_area = TEXTAREA({
            style: (
                'border: none;'+
                'width: 100%;'+
                'font-family: Monaco, Lucida Console, Courier New, monospace;'+
                'font-size: 0.9em;'
            )
            },
            // @ToDo: i18n
            'Query'
        );

        var $update_button = query_box.$update_button = INPUT({
            type: 'button',
            // @ToDo: i18n
            value: 'Compute and show on map',
            style: 'margin-top:5px;'
        });
        $update_button.hide();
        $update_button.on('click', function() {
            query_box.updated(query_box.$text_area.val());
        });
        $query_box_div.append($text_area);
        $query_box_div.append(
            DIV({
                    style:'text-align: center;'
                }, 
                $update_button
            )
        );

        function show_update_button() {
            $update_button.show();
            //$update_button.toggle($text_area.html() != query_box.previous_query);
        }

        $text_area.on('keyup', show_update_button);

        $text_area.show();
        query_box.resizer = new TextAreaAutoResizer(
            $text_area,
            15
        );
        $query_box_div.css({
            position: 'absolute',
            bottom: '10px',
            left: '120px',
            right: '160px',
            backgroundColor: 'white',
            border: '1px solid black',
            padding: '0.5em'
        });
        return query_box.div;
    },

    print_mode: function() {
        var query_box = this;
        query_box.$text_area.css('text-align', 'center');
    }
});

colour_map = [
    [240, 10, 135],
	[255, 62, 62],
    [240, 130, 40],
    [230, 220, 50],
    [160, 230, 55],
    [10, 210, 140],
    [10, 200, 200],
    [30, 60, 255],
    [130, 0, 220],
    [160, 0, 200]
];

function compute_colour_map() {
    var i;
    with (Math) {
        /*
        // Blue green red, cosines,
        for (i = -900; i < 900; i++) {
            var x = i/1000 * PI;
            var red = floor((1- (2 * abs(PI/2-x))/PI) * 255) //floor(sin(x) * 255);
            var green = floor((1- (2 * abs(x))/PI) * 255) //floor(cos(x) *255);
            var blue = floor((1- (2 * abs(PI/2+x))/PI) * 255) //floor(-sin(x) *255);
            colour_map.push([
                red < 0 ? 0 : red,
                green < 0 ? 0 : green,
                blue < 0 ? 0 : blue
            ]);
        }
        */
        for (i = -500; i < 900; i++) {
            var x = i/1000 * PI;
            var red = floor(sin(x) * 255);
            var green = floor(sin(x + (PI/3)) *255);
            var blue = floor(sin(x + (2 * PI/3)) *255);
            colour_map.push([
                red < 0 ? 0 : red,
                green < 0 ? 0 : green,
                blue < 0 ? 0 : blue
            ]);
        }
    }
}
//compute_colour_map();

var FilterBox = OpenLayers.Class(OpenLayers.Control, {
    CLASS_NAME: 'FilterBox',
    // updated(filter_function): callback
    // example: object with example attributes, should match places
    title: (
        'Enter filter expressions here to filter the map overlay. '+
        '"unfiltered" means the map overlay is not being filtered. '+
        'You can use any attribute that is shown in the overlay '+
        'popup box, and logical operators "and", "not" and "or". \n'+
        'within("Region name") and within_Nepal() filter by region.'
    ),
    destroy: function() {
        var filter_box = this;
        filter_box.deactivate();
        filter_box.resizer.destroy();
        OpenLayers.Control.prototype.destroy.apply(filter_box, arguments);
    },

    activate: function() {
        var filter_box = this;
        if (OpenLayers.Control.prototype.activate.apply(filter_box, arguments)) {
            return true;
        } else {
            return false;
        }
    },

    deactivate: function() {
        var filter_box = this;
        if (OpenLayers.Control.prototype.deactivate.apply(filter_box, arguments)) {
            return true;
        } else {
            return false;
        }
    },

    set_filter: function(filter_expression) {
        var filter_box = this;
        filter_box.$text_area.val(filter_expression);
        filter_box.update_plugin();
    },

    update_plugin: function() {
        var filter_box = this;
        var $text_area = filter_box.$text_area;
        var filter_expression = $text_area.val();
        if (new RegExp('^\\s*$').test(filter_expression)) {
            var filter_function = function() {
                return true;
            };
            $text_area.val('unfiltered');
        }
        else {
            try {
                filter_function = filter_box.plugin.create_filter_function($text_area.val());
                // test it a bit
                filter_function(filter_box.example, 0);
            }
            catch(error) {
                $(filter_box.div).css('background-color', 'red');
                var error_name = error.name;
                $(filter_box.div).attr('title', error.message);
                if (error_name == 'ReferenceError') {
                    var bad_ref = error.message.substr(
                        error.message.lastIndexOf(':') + 2
                    );
                    var bad_ref_first_pos = filter_expression.indexOf(bad_ref);
                    $text_area[0].setSelectionRange(
                        bad_ref_first_pos,
                        bad_ref_first_pos + bad_ref.length
                    );
                    return;
                }
                else {
                    throw error;
                }
                return;
            }
        }
        filter_box.updated(filter_function);
        filter_box.$update_button.hide();
        $(filter_box.div).css('background-color', 'white');
    },

    draw: function() {
        var filter_box = this;
        OpenLayers.Control.prototype.draw.apply(filter_box, arguments);
        var $filter_box_div = $(filter_box.div);
        var $text_area = filter_box.$text_area = TEXTAREA({
            style: (
                'border: none;'+
                'width: 100%;'+
                'font-family: Monaco, Lucida Console, Courier New, monospace;'+
                'font-size: 0.9em;'+
                'text-align: center;'+
                'overflow: scroll;'
            )
            },
            filter_box.initial_filter || 'unfiltered'
        );

        $filter_box_div.append($text_area);

        var $update_button = filter_box.$update_button = INPUT({
            type: 'button',
            value: 'Filter map overlay',
            style: 'margin-top:5px;'
        });
        $update_button.hide();
        $update_button.on('click', function() {
            filter_box.update_plugin();
        });
        $filter_box_div.append($text_area);
        $filter_box_div.append(
            DIV({
                    style:'text-align: center;'
                }, 
                $update_button
            )
        );

        function show_update_button() {
            $update_button.show();
        }

        $text_area.on('keyup', show_update_button);

        $text_area.show();
        filter_box.resizer = new TextAreaAutoResizer(
            $text_area,
            15
        );

        $filter_box_div.css({
            position: 'absolute',
            top: '10px',
            right: '10px',
            width: '200px',
            backgroundColor: 'white',
            border: '1px solid black',
            padding: '0.5em'
        });
        return filter_box.div;
    }
});

// Shapes on the map
function Vector(geometry, attributes, style) {
    style.strokeColor = 'none';
    style.fillOpacity = 0.8;
    style.strokeWidth = 1;
    return new OpenLayers.Feature.Vector(
        geometry, attributes, style
    );
}
function Polygon(components) {
    return new OpenLayers.Geometry.Polygon(components);
}
function Point(lon, lat) {
    var point = new OpenLayers.Geometry.Point(lon, lat);
    return point.transform(
        S3.gis.proj4326,
        S3.gis.maps['default_map'].getProjectionObject()
    );
}
function LinearRing(point_list) {
    point_list.push(point_list[0]);
    return new OpenLayers.Geometry.LinearRing(point_list);
}

function Place(data) {
    var place = this;
    place.data = data;
    place.data.latitude = Math.round(place.data.latitude * 1000) / 1000;
    place.data.longitude = Math.round(place.data.longitude * 1000) / 1000;

    place.spaces = [];
    var projection_current = S3.gis.maps['default_map'].getProjectionObject();
    var point = place.point = new OpenLayers.Geometry.Point(data.longitude, data.latitude).transform(S3.gis.proj4326, projection_current);
    var lonlat = place.lonlat = new OpenLayers.LonLat(point.x, point.y);
}
var station_marker_icon_size = new OpenLayers.Size(21, 25);
var station_marker_icon = new OpenLayers.Icon(
    'http://www.openlayers.org/dev/img/marker.png', 
    station_marker_icon_size,
    new OpenLayers.Pixel(
        -(station_marker_icon_size.w / 2),
        -station_marker_icon_size.h
    )
);
Place.prototype = {
    within: function() {
        for (var i = 0; i < arguments.length; i++) {
            if (this.spaces.indexOf(arguments[i]) != -1) {
                return true;
            }
        }
        return false;
    },
    within_Nepal: function() {
        return this.spaces.length > 0;
    },
    generate_marker: function(use_marker) {
        // only for stations
        var place = this;
        if (place.data.station_id) {
            var station_marker = new OpenLayers.Marker(
                place.lonlat,
                station_marker_icon.clone()
            );
            station_marker.place = place;
            var show_place_info_popup = function(event) { 
                var marker = this;
                var place = marker.place;
                var info = [
                    // popup is styled with div.olPopup
                    '<div class="place_info_popup">'
                ];
                function add_attribute(attribute) {
                    var value = place.data[attribute];
                    if (!!value) {
                        info.push(
                            //'<li>',
                            attribute.replace('_', ' '), ': ', value,
                            //'</li>'
                            '<br />'
                        );
                    }
                }
                add_attribute('station_id');
                add_attribute('station_name');
                add_attribute('latitude');
                add_attribute('longitude');
                add_attribute('elevation');

                info.push('</div>');

                var popup = new OpenLayers.Popup(
                    'info_bubble', 
                    marker.lonlat,
                    new OpenLayers.Size(170, 125),
                    info.join(''),
                    true
                );
                marker.popup = popup;
                var map = S3.gis.maps['default_map'];
                map.addPopup(popup);
                function remove_place_info_popup() {
                    map.removePopup(marker.popup);
                    marker.popup.destroy();
                    marker.popup = null;
                }
                marker.events.register('mouseup', marker,
                    remove_place_info_popup
                );
                marker.events.register('mouseout', marker, 
                    remove_place_info_popup
                );
                OpenLayers.Event.stop(event);
            };
            station_marker.events.register(
                'mousedown',
                station_marker,
                show_place_info_popup
            );
            use_marker(station_marker);
        }
    },
    add_space: function(space) {
        this.spaces.push(space.name);
    },
    popup: function(feature, value, use_popup) {
        var place = this;
        var info = [
            // popup is styled with div.olPopup
            '<div class="place_info_popup">', 
            'value: ', value, '<br />'
            //'</li>'
        ];
        var data = place.data;
        for (var p in data) {
            if (data.hasOwnProperty(p)) {
                value = data[p];
                if (!!value) {
                    info.push(
                        //'<li>',
                        p.replace('_',' '),': ', value,
                        //'</li>'
                        '<br />'
                    );
                }
            }
        }
        info.push('</div>');
        var popup = new OpenLayers.Popup(
            'info_bubble', 
            feature.geometry.getBounds().getCenterLonLat(),
            new OpenLayers.Size(170, 125),
            info.join(''),
            true
        );
        use_popup(popup);
    }
};

function PointInLinearRingDetector(linear_ring) {
    /* Cache line information to speed up queries when we have many
    points to test.
    */
    var detector = this;
    var steps = linear_ring.components;
    var bounds = detector.bounds = linear_ring.getBounds();
    var top = bounds.top;
    var bottom = bounds.bottom;
    // sort polygon edges into horizontal parallel strips
    // any line that has either end inside or crosses a strip
    // gets added to the set of lines for that strip
    // The aim is to have as few lines as possible per strip
    // without having too many strips duplicating lots of lines
    // containsPoint test can now be orders of magnitude faster, as far fewer
    // lines need consideration.
    var strips_count = parseInt(steps.length / 2, 10);
    var strips = detector.strips = new Array(strips_count + 1); // up and down again
    for (var i=0; i<strips.length; i++) {
        strips[i] = [];
    }

    // strips run from bottom (0) to top
    var latitude_range = top - bottom;
    var acos = Math.acos;
    var floor = Math.floor, max = Math.max, min = Math.min;
    var strips_count_over_pi = strips_count / Math.PI;
    var strip_selector = detector.strip_selector = function(latitude) {
        // for efficient strip sizes, assume polygons approximate a circle
        // i.e. the top lines are much more likely to run horizontally,
        // and the side lines vertically. Strip sizes reflect this.
        return floor(
            acos(
                // Some loss of floating point precision seems to have been 
                // introduced by OpenLayers (getBounds?)
                1 - (2 * max(min(((latitude - bottom) / latitude_range), 1.0), 0.0))
            ) * strips_count_over_pi
        );
    };

    var start_point = steps[0];
    var start_y = start_point.y;
    var start_coords = [start_point.x, start_y];
    var start_strip = strip_selector(start_y);
    var end_point, end_y, end_coords, end_strip;
    var line, direction, strip_number;
    for (var j=1, len=steps.length; j < len; ++j) {
        end_point = steps[j];
        end_y = end_point.y;
        end_coords = [end_point.x, end_y];
        end_strip = strip_selector(end_y);

        line = [start_coords, end_coords];
        direction = parseInt((end_y-start_y) / Math.abs(end_y-start_y) || 0, 10);
        strip_number = start_strip;
        strips[strip_number].push(line);
        while (strip_number != end_strip) {
            strip_number += direction;
            strips[strip_number].push(line);
        }  
        start_coords = end_coords;
        start_y = end_y;
        start_strip = end_strip;
    }
}

PointInLinearRingDetector.prototype = {
    containsPoint: function(point, is_contained) {
        if (this.bounds.contains(point.x, point.y)) {
            var digs = 14;
            var px = point.x;
            var py = point.y;
            function getX(y, x1, y1, x2, y2) {
                // this should be commited to OpenLayers source
                var y1_ = y1-y, y2_ = y2-y;
                return (((x2 * y1_) - (x1 * y2_))) / (y1_ - y2_);
            }
            var lines_to_test = this.strips[this.strip_selector(py)];
            var line, x1, y1, x2, y2, cx, cy;
            var crosses = 0;
            for (var i=0, len=lines_to_test.length; i < len; ++i) {
                line = lines_to_test[i];
                x1 = line[0][0];
                y1 = line[0][1];
                x2 = line[1][0];
                y2 = line[1][1];

                /**
                 * The following conditions enforce five edge-crossing rules:
                 *    1. points coincident with edges are considered contained;
                 *    2. an upward edge includes its starting endpoint, and
                 *    excludes its final endpoint;
                 *    3. a downward edge excludes its starting endpoint, and
                 *    includes its final endpoint;
                 *    4. horizontal edges are excluded; and
                 *    5. the edge-ray intersection point must be strictly right
                 *    of the point P.
                 */
                if (y1 == y2) {
                    // horizontal edge
                    if (py == y1) {
                        // point on horizontal line
                        if (x1 <= x2 && (px >= x1 && px <= x2) || // right or vert
                            x1 >= x2 && (px <= x1 && px >= x2)) { // left or vert
                            // point on edge
                            crosses = -1;
                            break;
                        }
                    }
                    // ignore other horizontal edges
                    continue;
                }
                cx = getX(py, x1, y1, x2, y2);
                if (cx == px) {
                    // point on line
                    if (y1 < y2 && (py >= y1 && py <= y2) || // upward
                        y1 > y2 && (py <= y1 && py >= y2)) { // downward
                        // point on edge
                        crosses = -1;
                        break;
                    }
                }
                if (cx <= px) {
                    // no crossing to the right
                    continue;
                }

                if (x1 != x2 && (cx < Math.min(x1, x2) || cx > Math.max(x1, x2))) {
                    // no crossing                
                    continue;
                }

                if (y1 < y2 && (py >= y1 && py < y2) || // upward
                    y1 > y2 && (py < y1 && py >= y2)) { // downward
                   ++crosses;
                }
            }
            if (
                (crosses == -1) ?
                // on edge
                1 :
                // even (out) or odd (in)
                !!(crosses & 1)
            ) {
                is_contained();
            }
        }
    }
};

VariableResolutionVectorLayer = OpenLayers.Class(OpenLayers.Layer.Vector, {
        CLASS_NAME: 'VariableResolutionVectorLayer',
        drawFeature: function(feature) {
            var map = this.map;
            var zoom = map.zoom;
            OpenLayers.Layer.Vector.prototype.drawFeature.call(
                this,
                feature.atZoom(zoom, map)
            );
        },
        moveTo: function(bounds, zoomChanged, dragging) {
            OpenLayers.Layer.prototype.moveTo.apply(this, arguments);

            var ng = (OpenLayers.Renderer.NG && this.renderer instanceof OpenLayers.Renderer.NG);
            if (ng) {
                if (zoomChanged) {
                    this.renderer.updateDimensions();
                }
            } else {
                var coordSysUnchanged = true;

                if (!dragging) {
                    this.renderer.root.style.visibility = 'hidden';

                    this.div.style.left = -parseInt(this.map.layerContainerDiv.style.left, 10) + 'px';
                    this.div.style.top = -parseInt(this.map.layerContainerDiv.style.top, 10) + 'px';
                    var extent = this.map.getExtent();
                    coordSysUnchanged = this.renderer.setExtent(extent, zoomChanged);

                    this.renderer.root.style.visibility = 'visible';

                    // Force a reflow on gecko based browsers to prevent jump/flicker.
                    // This seems to happen on only certain configurations; it was originally
                    // noticed in FF 2.0 and Linux.
                    if (OpenLayers.IS_GECKO === true) {
                        this.div.scrollLeft = this.div.scrollLeft;
                    }
                    if(!zoomChanged && coordSysUnchanged) {
                        for (var i in this.unrenderedFeatures) {
                            var feature = this.unrenderedFeatures[i];
                            this.drawFeature(feature);
                        }
                    }
                }
            }
            if (!this.drawn || (!ng && (zoomChanged || !coordSysUnchanged))) {
                this.drawn = true;
                this.renderer.clear();
                this.unrenderedFeatures = {};
                var features = this.features;
                for (var j=0, len=features.length; j<len; j++) {
                    this.renderer.locked = (j !== (len - 1));
                    this.drawFeature(
                        features[j]
                    );
                }
            }    
        }
    }
);
OpenLayers.Feature.prototype.atZoom = function(zoom, map) {
    return this;
};
OpenLayers.Feature.Vector.prototype.atZoom = function(zoom, map) {
    var feature = this;
    var by_zoom = feature.by_zoom;
    if (!by_zoom) {
        by_zoom = feature.by_zoom = [];
    }
    var simplified_feature = by_zoom[zoom];
    if (!simplified_feature) {
        // ToDo: there are more accurate ways to get a decent 
        // tolerance, but this is fast, which is the whole point
        // of simplifying the vectors
        var centre_lonlat = map.getCenter();
        var offset_lonlat = map.getLonLatFromPixel(
            map.getPixelFromLonLat(centre_lonlat).offset(
                new OpenLayers.Pixel(1,1)
            )
        );
        max_x_diff = Math.abs(offset_lonlat.lon - centre_lonlat.lon);
        max_y_diff = Math.abs(centre_lonlat.lat - offset_lonlat.lat);
        simplified_feature = new OpenLayers.Feature.Vector(
            feature.geometry ? feature.geometry.atZoom(max_x_diff, max_y_diff) : null,
            feature.attributes,
            feature.style
        );
        delete simplified_feature.state;
        simplified_feature.prototype = feature;
        by_zoom[zoom] = simplified_feature;
    }
    return simplified_feature;
};
// It is safe not to simplify the feature in all cases, also we cannot 
// simplify the following:
// Rectangle
// Point
// Surface
OpenLayers.Geometry.prototype.atZoom = function() {
    return this;
};

// simplifying a Collection is like cloning its simplified components:

// Multipolygon,
// Polygon,
// MultiLineString

OpenLayers.Geometry.Collection.prototype.atZoom = function(max_x_diff, max_y_diff) {
    var geometry = eval("new " + this.CLASS_NAME + "()");
    for (var i=0, len=this.components.length; i<len; i++) {
        geometry.addComponent(this.components[i].atZoom(max_x_diff, max_y_diff));
    }
    OpenLayers.Util.applyDefaults(geometry, this);
    return geometry;
};

// Geometries that use Points are the ones we need to simplify:

//Multipoint
// Curve
//  LineString
//   LinearRing
OpenLayers.Geometry.MultiPoint.prototype.atZoom = function(max_x_diff, max_y_diff) {
    var geometry = eval("new " + this.CLASS_NAME + "()");
    var points = this.components;
    var points_length = points.length;
    if (points_length > 0) {
        var previous_point = points[0];
        var previous_x = previous_point.x;
        var previous_y = previous_point.y;

        // Always add the first point if there are any
        geometry.addComponent(previous_point);

        if (points_length > 1) {
            var i = 1; // we added the first point already
            var abs = Math.abs;
            while (i < points_length - 1) {
                var point = points[i];
                if (abs(point.x - previous_x) > max_x_diff ||
                    abs(point.y - previous_y) > max_y_diff) {
                    // the point is far away enough from the previous point
                    // such that the difference is discernible on a pixel basis
                    geometry.addComponent(point.clone());
                    previous_point = point;
                    previous_x = previous_point.x;
                    previous_y = previous_point.y;
                }
                i++;
            }
            // Always add the last point if there is one
            geometry.addComponent(points[points_length -1]);
        }
    }
    OpenLayers.Util.applyDefaults(geometry, this);
    return geometry;
};

load_layer_and_locate_places_in_spaces = function(name, layer_URL, format, label_colour, label_size) {
    // can load the KML from http://maps.worldbank.org/overlays/3388.kml
    var map = S3.gis.maps['default_map'];
    var vector_layer = new VariableResolutionVectorLayer(
        name,
        {
            projection: map.displayProjection,
            strategies: [new OpenLayers.Strategy.Fixed()],
            protocol: new OpenLayers.Protocol.HTTP({
                url: layer_URL,
                format: format
            })
        }
    );
    map.addLayer(vector_layer);
  
    var region_names_layer = new OpenLayers.Layer.Vector(
        name + " names",
        {
            projection: map.displayProjection,
            styleMap: new OpenLayers.StyleMap({'default': {
                label : "${name}",
                
                fontColor: label_colour || "black",
                fontSize: label_size || "10px",
                //fontFamily: "Courier New, monospace",
                fontWeight: "bold",
                labelAlign: "cm",
                labelOutlineColor: "white",
                labelOutlineWidth: 1
            }}),
            renderers: ["Canvas"]
        }
    );
    map.addLayer(region_names_layer);
    vector_layer.events.register(
        'loadend', 
        vector_layer,
        function() {
            region_names_layer.setZIndex(109);
            each(
                vector_layer.features,
                function(feature) {
                    var geometry = feature.geometry;
                    var polygon = geometry.components[0];
                    var district = feature.data.District || feature.data.DISTRICT;
                    var pointFeature = new OpenLayers.Feature.Vector(geometry.getCentroid());
                    pointFeature.attributes = {
                        name: district.value ? district.value : district
                    };
                    region_names_layer.addFeatures([pointFeature]);
                }
            );
        }
    );
    map.panDuration = 0;
    vector_layer.events.register(
        'loadend', 
        vector_layer,
        function() {
            vector_layer.setVisibility(false);
            setTimeout(
                function() {
                    vector_layer.setZIndex(
                        110
                    );
                    var linear_rings = [];

                    function find_linear_rings(geometry, name) {
                        if (geometry.CLASS_NAME == "OpenLayers.Geometry.LinearRing") {
                            var linear_ring = geometry;
                            linear_ring.name = name;
                            plugin.spaces.push([name, name]);
                            linear_rings.push(linear_ring);
                        } else if (geometry.components) {
                            each(
                                geometry.components,
                                function(geometry) {
                                    find_linear_rings(geometry, name);
                                }
                            );
                        }
                    }

                    each(
                        vector_layer.features,
                        function(feature) {
                            var data = feature.data;
                            if (data) {
                                var district = data.District || data.DISTRICT;
                                if (district.value) {
                                    name = district.value;
                                }
                                else {
                                    name = district;
                                }
                            }
                            find_linear_rings(feature.geometry, name);
                        }
                    );
                    each(linear_rings,
                        function(linear_ring) {
                            plugin.when_places_loaded(
                                function(places) {
                                    var detector = new PointInLinearRingDetector(
                                        linear_ring
                                    );
                                    for (p in places) {
                                        if (places.hasOwnProperty(p)) {
                                            var place = places[p];
                                            detector.containsPoint(
                                                place.point,
                                                function() {
                                                    place.add_space(linear_ring);
                                                }
                                            );
                                        }
                                    }
                                }
                            );
                        }
                    );

                    plugin.quick_filter_data_store.loadData(plugin.spaces);
                    plugin.quick_filter_data_store.sort('name', 'ASC');
                    //vector_layer.redraw();
                },
                1
            );
        }
    );
};

var Logo = OpenLayers.Class(OpenLayers.Control, {
    draw: function() {
        return (
            DIV({
                    style:'width: 120px; position:absolute; left: 5px; bottom:60px;'
                },
                IMG({
                    src:'static/img/Nepal-Government-Logo.png',
                    width: '120px'
                })
            )
        )[0];
    }
});

ClimateDataMapPlugin = function(config) {
    var plugin = this; // let's be explicit!
    var map = plugin.map;
    window.plugin = plugin;
    plugin.data_type_option_names = config.data_type_option_names;
    plugin.parameter_names = config.parameter_names;
    plugin.aggregation_names = config.aggregation_names;
    plugin.year_min = config.year_min;
    plugin.year_max = config.year_max;

    plugin.data_type_label = config.data_type_label;
    plugin.overlay_data_URL = config.overlay_data_URL;
    plugin.places_URL = config.places_URL;
    plugin.chart_URL = config.chart_URL;
    plugin.data_URL = config.data_URL;
    plugin.station_parameters_URL = config.station_parameters_URL;
    plugin.years_URL = config.years_URL;

    plugin.chart_popup_URL = config.chart_popup_URL;
    plugin.request_image_URL = config.request_image_URL;
    var display_mode = config.display_mode;
    var initial_query_expression;
    if (config.expression) {
        initial_query_expression = decodeURI(config.expression);
    } else {
        initial_query_expression = (
            plugin.aggregation_names[0]+'('+
                '"'+ //form_values.data_type+' '+
                plugin.parameter_names[0].replace(
                    new RegExp('\\+','g'),
                    ' '
                )+'", '+
                'From(' + plugin.year_min + '), '+
                'To(' + plugin.year_max + ')'+
            ')'
        );
    }
    var initial_filter = decodeURI(config.filter || 'unfiltered');

    delete config;

    plugin.last_query_expression = null;

    plugin.places = {};
    plugin.spaces = [];

    plugin.places_events = [];
    plugin.when_places_loaded = function(places_function) {
        places_function(plugin.places);
        plugin.places_events.push(places_function);
    };

    plugin.create_filter_function = function(filter_expression) {
        var replacements = {
            '(\\W)and(\\W)': '$1&&$2',
            '(^|\\W)not(\\W)': '$1!$2',
            '(\\W)or(\\W)': '$1||$2',
            '([^=<>])=([^\\=])': '$1==$2'
        };
        for (var pattern in replacements) {
            if (replacements.hasOwnProperty(pattern)) {
                var reg_exp = new RegExp(pattern, 'g');
                filter_expression = filter_expression.replace(reg_exp, replacements[pattern]);
            }
        }

        var function_string = (
            'unfiltered = true;\n'+
            'with (Math) {'+
                'with (place) {' +
                    'with (place.data) { '+
                        'return '+ filter_expression + ';' +
                    '}'+
                '}'+
            '}'
        );
        var filter_function = new Function(
            'place', 
            'value', 
            function_string
        );
        return filter_function;
    };
    if (initial_filter) {
        plugin.filter = plugin.create_filter_function(initial_filter);
    }

    var tooltips = [];
    function add_tooltip(config) {
        tooltips.push(config);
    }

    function init_tooltips() {
        each(tooltips,
            function(config) {
                new Ext.ToolTip(config);
            }
        );
        //Ext.QuickTips.init(); // done by addMapUI()
    }

    plugin.setup = function() {
        var overlay_layer = plugin.overlay_layer = new OpenLayers.Layer.Vector(
            'Query result values',
            {
                isBaseLayer:false
            }
        );
        map.addLayer(overlay_layer);
        // hovering over a square pops up a box showing details
        var hover_timeout = null, 
            hover_delay = 1000,
            hover_delay_clear_timeout = null;
        function onFeatureSelect(feature) {
            if (hover_delay_clear_timeout !== null) {
                clearTimeout(hover_delay_clear_timeout);
                hover_delay_clear_timeout = null;
            }
            if (hover_timeout === null) {
                hover_timeout = setTimeout(
                    function() {
                        hover_delay = 0;
                        var place = plugin.places[feature.attributes.place_id];
                        if (!!place) {
                            place.popup(
                                feature,
                                feature.attributes.value,
                                function(popup) {
                                    feature.popup = popup;
                                    map.addPopup(popup);
                                    setTimeout(
                                        function() {
                                            onFeatureUnselect(feature);
                                            hover_delay = 1000;
                                        },
                                        10000
                                    );
                                }
                            );
                        }
                    },
                    hover_delay
                );
            }
        }
        function onFeatureUnselect(feature) {
            if (hover_timeout !== null) {
                clearTimeout(hover_timeout);
                hover_timeout = null;
            }
            if (feature.popup && feature.popup.div) {
                map.removePopup(feature.popup);
                feature.popup.destroy();
                feature.popup = null;
            }
            if (hover_delay_clear_timeout === null) {
                hover_delay_clear_timeout = setTimeout(
                    function() {
                        hover_delay = 1000;
                    },
                    3000
                );
            }
        }
        var hoverControl = new OpenLayers.Control.SelectFeature(
            overlay_layer,
            {
                title: 'Show detail by hovering over a square',
                hover: true,
                onSelect: onFeatureSelect,
                onUnselect: onFeatureUnselect
            }
        );
        map.addControl(hoverControl);
        hoverControl.activate();

        var SelectDragHandler = OpenLayers.Class(OpenLayers.Handler.Drag, {
            // Ensure that we propagate clicks (so we can still use other controls)
            down: function() {
                OpenLayers.Handler.Drag.prototype.down.apply(arguments);
                //OpenLayers.Event.stop(evt);
                return true;
            },
            CLASS_NAME: 'SelectHandler'
        });
        // selection of overlay squares
        OpenLayers.Feature.Vector.style['default']['strokeWidth'] = '2';
        var selectCtrl = new OpenLayers.Control.SelectFeature(
            overlay_layer,
            {
                clickout: true,
                toggle: false,
                toggleKey: 'altKey',
                multiple: false,
                multipleKey: 'shiftKey',
                hover: false,
                box: true,
                onSelect: function(feature) {
                    feature.style.strokeColor = 'black';
                    feature.style.strokeDashstyle = 'dash';
                    overlay_layer.drawFeature(feature);
                    plugin.show_chart_button.enable();
                },
                onUnselect: function(feature) {
                    feature.style.strokeColor = 'none';
                    overlay_layer.drawFeature(feature);
                    if (plugin.overlay_layer.selectedFeatures.length === 0) {
                        plugin.show_chart_button.disable();
                    }
                }
            }
        );
        // workaround: is this a bug in OpenLayers?
        selectCtrl.handlers.box.dragHandler.dragstart = function(evt) {
            var propagate = true;
            this.dragging = false;
            if (this.checkModifiers(evt) &&
                   (OpenLayers.Event.isLeftClick(evt) ||
                    OpenLayers.Event.isSingleTouch(evt))) {
                this.started = true;
                this.start = evt.xy;
                this.last = evt.xy;
                OpenLayers.Element.addClass(
                    this.map.viewPortDiv, 'olDragDown'
                );
                this.down(evt);
                this.callback('down', [evt.xy]);

                //OpenLayers.Event.stop(evt);

                if(!this.oldOnselectstart) {
                    this.oldOnselectstart = document.onselectstart ?
                        document.onselectstart : OpenLayers.Function.True;
                }
                document.onselectstart = OpenLayers.Function.False;

                propagate = !this.stopDown;
            } else {
                this.started = false;
                this.start = null;
                this.last = null;
            }
            return true;
        };
        map.controls[0].deactivate();

        map.addControl(selectCtrl);

        selectCtrl.activate();

        $.ajax({
            url: plugin.places_URL,
            dataType: 'json',
            success: function(rearranged_places_data) {
                // Add marker layer for places
                // NB This isn't in the standard Eden OpenLayers build, so added manually by MapPlugin.py
                var station_markers_layer = new OpenLayers.Layer.Markers(
                    // @ToDo: i18n
                    'Observation stations'
                );
                places_data = {};
                each(
                    rearranged_places_data,
                    function(places_by_attribute_group) {
                        var attributes = places_by_attribute_group.attributes;
                        var compression = places_by_attribute_group.compression;
                        var places = places_by_attribute_group.places;
                        var id_index = attributes.indexOf('id');
                        var id_attribute = places[id_index];
                        var previous_id = 0;
                        each(id_attribute,
                            function(id_offset, position) {
                                var place_id = id_offset + previous_id;
                                if (places_data[place_id] == undefined) {
                                    places_data[place_id] = {};
                                }
                                id_attribute[position] = previous_id = place_id;
                            }
                        );
                        attributes.splice(id_index, 1);
                        places.splice(id_index, 1);
                        compression.splice(id_index, 1);
                        each(
                            attributes,
                            function(attribute_name, index) {
                                if (compression[index] == 'similar_numbers') {
                                    var previous = 0;
                                    each(
                                        places[index],
                                        function(value, position) {
                                            var place_id = id_attribute[position];
                                            var place_data = places_data[place_id];
                                            previous = place_data[attribute_name] = previous + value;
                                        }
                                    );
                                }
                                else {
                                    // no compression
                                    each(
                                        places[index],
                                        function(value, position) {
                                            var place_id = id_attribute[position];
                                            var place_data = places_data[place_id];
                                            place_data[attribute_name] = value;
                                        }
                                    );
                                }
                            }
                        );
                    }
                );
                var new_places = [];
                for (var place_id in places_data) {
                    if (places_data.hasOwnProperty(place_id)) {
                        var place_data = places_data[place_id];
                        // store place data
                        var place = new Place(place_data);
                        new_places.push(place);
                        plugin.places[place_id] = place;
                        // add marker
                        place.generate_marker(
                            function(marker) { 
                                station_markers_layer.addMarker(marker);
                            }
                        );
                    }
                }
                each(
                    plugin.places_events,
                    function(places_function) {
                        places_function(new_places);
                    }
                );
                station_markers_layer.setVisibility(false);
                map.addLayer(station_markers_layer);
                plugin.station_markers_layer = station_markers_layer;

                plugin.update_map_layer(initial_query_expression);
                plugin.filter_box = new FilterBox({
                    updated: function(filter_function) {
                        plugin.filter = filter_function;
                        plugin.colour_scale.with_limits(
                            plugin.render_map_layer
                        );
                    },
                    example: new Place(places_data[place_id]),
                    initial_filter: initial_filter,
                    plugin: plugin
                });
                map.addControl(plugin.filter_box);
                plugin.filter_box.activate();
                plugin.logo = new Logo();
                plugin.logo.activate();
                map.addControl(plugin.logo);
            },
            error: function(jqXHR, textStatus, errorThrown) {
                plugin.set_status(
                    '<a target= "_blank" href="climate/places">Could not load place data!</a>'
                );
            }
        });
        var print_window = function() {
            // this breaks event handling in the widgets, but that's ok for printing
            var map_div = map.div;
            var $map_div = $(map_div);
            $(map_div).remove();
            var body = $('body');
            body.remove();
            var new_body = $('<body></body>');
            new_body.css({position:'absolute', top:0, bottom:0, left:0, right:0});
            new_body.append($map_div);
            $('html').append(new_body);
            $map_div.css('width', '100%');
            $map_div.css('height', '100%');
            map.updateSize();
        };

        plugin.expand_to_full_window = function() {
            // this makes the map use the full browser window, 
            // events still work, but it leaves a scroll bar
            $(map.div).css({
                position:'fixed',
                top:0, bottom:0, left:0, right:0,
                width:'100%', height:'100%',
                zIndex: 10000
            });
            $('body').children().css('display', 'none');
            $('div.fullpage').css('display', '');
            $('html').css('overflow', 'hidden');
            map.updateSize();
        };

        // make room by closing the layer tree
        setTimeout(
            function() {
                load_layer_and_locate_places_in_spaces(
                    'Nepal districts (World Bank)',
                    'http://maps.worldbank.org/overlays/3388.kml',
                    new OpenLayers.Format.KML({
                        //maxDepth: 2, 
                        extractStyles: true,
                        extractAttributes: true
                    }),
                    'black',
                    '9px'
                );

                load_layer_and_locate_places_in_spaces(
                    'Nepal development regions',
                    '/eden/static/data/NP_L1.geojson',
                    new OpenLayers.Format.GeoJSON(),
                    'black',
                    '11px'
                );
                init_tooltips();
            },
            1000 // what is this waiting for?
        );
    };

    var conversion_functions = {
        'Kelvin': function(value) {
            return value - 273.16;
        }
    };
    var display_units_conversions = {
        'Kelvin': '&#176;C',
        'Δ Kelvin': 'Δ &#176;C' // Δ i.e. \u0394 is Greek uppercase delta
    };

    plugin.render_map_layer = function(min_value, max_value) {
        plugin.overlay_layer.destroyFeatures();
        var feature_data = plugin.feature_data;
        var place_ids = feature_data.keys;
        var values = feature_data.values;
        var units = feature_data.units;
        var grid_size = feature_data.grid_size;

        var converter = plugin.converter;
        var display_units = plugin.display_units;

        var range = max_value - min_value;
        var features = [];
        var filter = plugin.filter || function() { return true; };
        for (var i = 0; i < place_ids.length; i++) {
            var place_id = place_ids[i];
            var place = plugin.places[place_id];
            if (place == undefined) {
                // some places outside of nepal may be filtered out.
                continue;
            }
            var value = values[i];
            if (place == undefined) {
                console.log(i);
                console.log(place);
                console.log(place_id);
            }
            var converted_value = converter(value);
            if (
                filter(place, converted_value)
            ) {
            	var normalised_value;
            	if (range) {
                    normalised_value = (converted_value - min_value) / range;
                } else {
                    normalised_value = 0;
                }
                if ((0.0 <= normalised_value) && 
                    (normalised_value <= 1.0)) {
                    var colour_value = colour_map[Math.floor(
                        normalised_value * (colour_map.length-1)
                    )];
                    function hexFF(value) {
                        return (256+value).toString(16).substr(-2);
                    }
                    var colour_string = (
                        '#'+
                        hexFF(colour_value[0]) + 
                        hexFF(colour_value[1]) + 
                        hexFF(colour_value[2])
                    );

                    var data = place.data;
                    var lat = data.latitude;
                    var lon = data.longitude;

                    if (grid_size === 0) {
                        features.push(
                            Vector(
                                Point(lon, lat),
                                {
                                    value: converted_value.toPrecision(6)+' '+display_units,
                                    id: id,
                                    place_id: place_id
                                },
                                {
                                    fillColor: colour_string,
                                    pointRadius: 6
                                }
                            )
                        );
                    } else {
                        var border = grid_size / 220;

                        north = lat + border;
                        south = lat - border;
                        east = lon + border;
                        west = lon - border;

                        features.push(
                            Vector(
                                Polygon([
                                    LinearRing([
                                        Point(west, north),
                                        Point(east, north),
                                        Point(east, south),
                                        Point(west, south)
                                    ])
                                ]),
                                {
                                    value: converted_value.toPrecision(6) + ' ' + display_units,
                                    id: id,
                                    place_id: place_id
                                },
                                {
                                    fillColor: colour_string
                                }
                            )
                        );
                    }
                }                        
            }
        }
        plugin.overlay_layer.addFeatures(features);
        
        plugin.request_image = function() {
            var coords = map.getCenter().transform(
                map.getProjectionObject(),
                S3.gis.proj4326
            );
            window.location.href = encodeURI([
                plugin.request_image_URL, 
                '?expression=', plugin.last_query_expression ,
                '&filter=', plugin.filter_box.$text_area.val() ,
                '&width=', $('html').width(),
                '&height=', $('html').height(),
                '&zoom=', map.zoom,
                '&coords=', coords.lon, ',', coords.lat
            ].join(''));
        };
        plugin.print_button.enable();
        if (display_mode == 'print') {
            //console.log('print requested')
            plugin.expand_to_full_window();
            setTimeout(
                // this setTimeout is to allow the map to expand.
                // otherwise some map tiles might be missed
                function() { 
                    var allowed_control_class_names = [
                        "OpenLayers.Control.Attribution",
                        "OpenLayers.Control.ScaleLine",
                        "ColourKey",
                        "FilterBox",
                        "QueryBox"
                    ];
                    each(map.controls,
                        function(control) {
                            if (allowed_control_class_names.indexOf(control.__proto__.CLASS_NAME) == -1) {
                                $(control.div).hide();
                            } else if (control.print_mode) {
                                control.print_mode();
                            }
                        }
                    );

                    var images_waiting = [];
                    function print_if_no_more_images() {
                        if (images_waiting.length === 0) {
                            console.log('All images loaded, now printing.');
                            setTimeout(function() {
                                window.print();
                            }, 0);
                        }
                    }

                    function image_done(img) {
                        var image_pos = images_waiting.indexOf(img);
                        images_waiting.splice(image_pos, 1);
                        print_if_no_more_images();
                    }
                    each(document.getElementsByTagName('img'),
                         function(img) {
                            if (!img.complete) {
                                images_waiting.push(img);
                                $(img).load(image_done).error(image_done);
                                if (img.complete) {
                                    image_done.call(img);
                                }
                            }
                        }
                    );
                    print_if_no_more_images();

                    // 10 sec max wait
                    setTimeout(
                        function() { 
                            console.log('Could not load all images in time.');
                            window.print();
                        },
                        20000
                    );
                },
                0
            );
        }
    };

    plugin.update_query = function(query_expression) {
        plugin.query_box.update(query_expression);
        plugin.last_query_expression = query_expression;
    };

    plugin.update_map_layer = function(query_expression) {
        // request new features
        plugin.overlay_layer.destroyFeatures();
        plugin.set_status('Updating...');
        plugin.query_box.update(query_expression);
        plugin.show_chart_button.disable();
        $.ajax({
            url: plugin.overlay_data_URL,
            dataType: 'json',
            data: {
                query_expression: query_expression
            },
            //timeout: 1000 * 20, // timeout doesn't seem to work
            success: function(feature_data, status_code) {
                if (feature_data.values.length === 0) {
                    plugin.set_status(
                        'Query was successful but contains no data. '+
                        'Data might be unavailable for this time range. '+
                        'Gridded data runs from 1971 to 2009. '+
                        'For Observed data please refer to '+
                        '<a href="'+plugin.station_parameters_URL+
                        '">Station Parameters</a>. '+
                        'Projected data depends on the dataset.'
                    );
                } else {
                    plugin.feature_data = feature_data;
                    var units = feature_data.units;
                    var converter = plugin.converter = conversion_functions[units] || function(x) { return x; };
                    var display_units = plugin.display_units = display_units_conversions[units] || units;
                    var values = feature_data.values;
                    
                    plugin.colour_scale.update_from(
                        display_units,
                        converter(Math.max.apply(null, values)), 
                        converter(Math.min.apply(null, values))
                    );
                    plugin.update_query(feature_data.understood_expression);
                    // not right place for this:
                    plugin.filter_box.resizer.resize(true);
                    plugin.set_status('');
                }
            },
            error: function(jqXHR, textStatus, errorThrown) {
                plugin.set_status(
                    'An error occurred: ' + (
                        jqXHR.statusText == 'error' ? 
                            'Is the connection OK?'
                            : jqXHR.statusText
                    )
                );
                var responseText = jqXHR.responseText;
                var error_message = responseText.substr(
                    0, 
                    responseText.indexOf('<!--')
                );
                var error = $.parseJSON(error_message);
                if (error.error == 'SyntaxError') {
                    // don't update the last expression if it's invalid
                    plugin.query_box.update(error.understood_expression);
                    plugin.query_box.error(error.offset);
                    plugin.set_status('');
                } else {
                    if (error.error == 'MeaninglessUnits' ||
                        error.error == 'DSLTypeError' || 
                        error.error == 'DimensionError') {
                        window.analysis = error.analysis;
                        plugin.query_box.update(error.analysis);
                    } else {
                        plugin.set_status(
                            '<a target= "_blank" href="'+
                                plugin.overlay_data_URL+'?'+
                                $.param(query_expression)+
                            '">Error</a>'
                        );
                    }
                }
            },
            complete: function(jqXHR, status) {
                if (status != 'success' && status != 'error') {
                    plugin.set_status(status);
                }
            }
        });
    };
    var months = [
        '', 'Jan', 'Feb', 'Mar', 'Apr', 'May',
        'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ];

    function SpecPanel(panel_id, panel_title, collapsed) {
        function make_combo_box(data, fieldLabel, hiddenName, combo_box_size) {
            var options = [];
            each(
                data,
                function(option) {
                    options.push([option, option]);
                }
            );
            var combo_box = new Ext.form.ComboBox({
                fieldLabel: fieldLabel,
                hiddenName: hiddenName,
                store: new Ext.data.SimpleStore({
                    fields: ['name', 'option'],
                    data: options
                }),
                displayField: 'name',
                typeAhead: true,
                mode: 'local',
                triggerAction: 'all',
                emptyText:'',
                selectOnFocus: true,
                forceSelection: true
            });
            combo_box.setSize(combo_box_size);
            if (!!options[0]) {
                combo_box.setValue(options[0][0]);
            }
            return combo_box;
        }

        /*
        var data_type_combo_box = make_combo_box(
            plugin.data_type_option_names,
            'Data type',
            'data_type',
            {
                width: 115,
                heigth: 25
            }
        );*/

        var variable_combo_box = make_combo_box(
            plugin.parameter_names,
            'Parameter',
            'parameter',
            {
                width: 160,
                heigth: 25
            }
        );
        // add tooltips to ease selection of datasets with long names
        variable_combo_box.tpl = new Ext.XTemplate(
            '<tpl for=".">'+
                '<div ext:qtip="{name}" class="x-combo-list-item">'+
                    '{name}'+
                '</div>'+
            '</tpl>'
        );

        var statistic_combo_box = make_combo_box(
            plugin.aggregation_names,
            'Statistic',
            'statistic',
            {
                width: 115,
                heigth: 25
            }
        );

        function inclusive_range(start, end) {
            var values = [];
            for (var i = start; i <= end; i++) {
                values.push(i);
            }
            return values;
        }
        var years = inclusive_range(plugin.year_min, plugin.year_max);

        var from_year_combo_box = make_combo_box(
            years,
            null,
            'from_year',
            {width:60, height:25}
        );
        from_year_combo_box.setValue(plugin.year_min);

        var from_month_combo_box = make_combo_box(
            months,
            null,
            'from_month',
            {width:50, height:25}
        );

        var to_year_combo_box = make_combo_box(
            years,
            null,
            'to_year',
            {width:60, height:25}
        );
        to_year_combo_box.setValue(2011);

        variable_combo_box.year_ranges = [];
        // when a dataset is selected, request the years.
        function update_years(dataset_name) {
            $.ajax({
                url: plugin.years_URL+'?dataset_name='+dataset_name,
                dataType: 'json',
                success: function(year_ranges) {
                    variable_combo_box.year_ranges = year_ranges;
                }
            });
        }
        variable_combo_box.on(
            'select', 
            function(a, value) {
                update_years(value.json[0]);
            }
        );
        update_years(plugin.parameter_names[0]);
        // grey out (but don't disable) any years in the from and to year
        // combo boxes if no data is available for those years
        each(
            [from_year_combo_box, to_year_combo_box],
            function(combo_box) {
                combo_box.on(
                    'expand',
                    function() {
                        $(combo_box.list.dom).find(
                            '.x-combo-list-item'
                        ).each(
                            function(i, option_div) {
                                $option_div = $(option_div);
                                $option_div.css('color', '');
                                if (
                                    variable_combo_box.year_ranges.indexOf(
                                        parseInt($option_div.text(), 10)
                                    ) == -1
                                ) {
                                    $option_div.css('color', '#DDD');
                                }
                            }
                        );
                    }
                );
            }
        );

        var to_month_combo_box = make_combo_box(
            months,
            null,
            'to_month',
            {width:50, height:25}
        );
        add_tooltip({
            target: to_year_combo_box.id,
            html: 'If month is not specified, the end of the year will be used.'
        });
        add_tooltip({
            target: to_month_combo_box.id,
            html: 'If month is not specified, the end of the year will be used.'
        });

        var month_letters = [];
        var month_checkboxes = [];
        // if none are picked, don't do annual aggregation
        // if some are picked, aggregate those months
        // if all are picked, aggregate for whole year
        each('DJFMAMJJASOND',
            function(month_letter, month_index) {
                month_letters.push(
                    {
                        html: month_letter, 
                        border: false
                    }
                );
                var name = 'month-'+month_index;
                month_checkboxes.push(
                    new Ext.form.Checkbox({
                        id: panel_id+'_'+name,
                        name: name,
                        checked: (month_index > 0)
                    })
                );
            }
        );
        add_tooltip({
            target: panel_id+'_month-0',
            html: 'Include Previous December. Years will also start in Previous December and end in November.'
        });
        month_checkboxes[0].on('check', function(a, value) {
            if (value && month_checkboxes[12].checked) {
                month_checkboxes[12].setValue(false);
            }
        });
        month_checkboxes[12].on('check', function(a, value) {
            if (value && month_checkboxes[0].checked) {
                month_checkboxes[0].setValue(false);
            }
        });
        var month_filter = month_letters.concat(month_checkboxes);
        var annual_aggregation_check_box = new Ext.form.Checkbox({
            id: panel_id+'_annual_aggregation_checkbox',
            name: 'annual_aggregation',
            checked: true,
            fieldLabel: 'Annual aggregation'
        });
        add_tooltip({
            target: panel_id+'_annual_aggregation_checkbox',
            html: 'Aggregate monthly values into yearly values. Only affects charts.'
        });
        var month_checkboxes_id = panel_id+'_month_checkboxes';
        annual_aggregation_check_box.on('check', function(a, value) {
            var month_checkboxes = $('#'+month_checkboxes_id);
            if (value) {
                month_checkboxes.show(300);
            } else {
                month_checkboxes.hide(300);
            }
        });

        var form_panel = new Ext.FormPanel({
            id: panel_id,
            title: panel_title,
            collapsible: true,
            collapseMode: 'mini',
            collapsed: collapsed,
            labelWidth: 60,
            items: [{
                region: 'center',
                items: [
                    new Ext.form.FieldSet({
                        style: 'margin: 0px; border: none;',
                        items: [
                            //data_type_combo_box,
                            variable_combo_box,
                            statistic_combo_box,
                            annual_aggregation_check_box,
                            // month filter checkboxes
                            {
                                id: month_checkboxes_id,
                                border: false,
                                layout: {
                                    type: 'table',
                                    columns: month_filter.length /2
                                },
                                defaults: {
                                    width: '15px',
                                    height: '1.3em',
                                    style: 'margin: 0.1em;'
                                },
                                items: month_filter
                            },
                            new Ext.form.CompositeField(
                                {
                                    fieldLabel: 'From',
                                    items:[
                                        from_year_combo_box,
                                        from_month_combo_box
                                    ]
                                }
                            ),
                            new Ext.form.CompositeField(
                                {
                                    fieldLabel: 'To',
                                    items:[
                                        to_year_combo_box,
                                        to_month_combo_box
                                    ]
                                }
                            )
                        ]
                    })
                ]
            }]
        });
        add_tooltip({
            target: month_checkboxes_id,
            html: 'Select months that will be used in the aggregation.'
        });
        return form_panel;
    }
    var filter_months = [
        'PrevDec', 'Jan', 'Feb', 'Mar', 'Apr', 'May',
        'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ];

    function form_query_expression(ext_form) {
        form_values = ext_form.getValues();
        var month_names = [];
        each(
            [0,1,2,3,4,5,6,7,8,9,10,11,12],
            function(month_number) {
                if (form_values['month-'+month_number] == 'on') {
                    month_names.push(
                        filter_months[month_number]
                    );
                }
            }
        );
        return (
            [
                form_values.statistic,
                '(',
                    '"', form_values.parameter.replace(new RegExp('\\+','g'),' '), '", ',
                    'From(',
                        form_values.from_year ,
                        (form_values.from_month?', '+form_values.from_month:''),
                    '), ',
                    'To(',
                        form_values.to_year ,
                        (form_values.to_month?', '+form_values.to_month:''),
                    ')',
                    (
                        form_values.annual_aggregation ?
                        (', Months('+month_names.join(', ')+')'):''
                    ),
                ')'
            ].join('')
        );
    }

    plugin.addToMapWindow = function(items) {
        // create the panels
        var climate_data_panel = SpecPanel(
            'climate_data_panel',
            'Select data: (A)',
            false
        );
        // This button does the simplest "show me data" overlay
        plugin.update_map_layer_from_form = function() {
            plugin.update_map_layer(
                form_query_expression(climate_data_panel.getForm())
            );
        };
        var update_map_layer_button = new Ext.Button({
            text: 'Show on map (A)',
            disabled: false,
            handler: plugin.update_map_layer_from_form
        });
        climate_data_panel.addButton(update_map_layer_button);
        items.push(climate_data_panel);

        var comparison_panel = SpecPanel(
            'comparison_panel',
            'Compare with data (B)',
            true
        );
        // This button does the comparison overlay
        plugin.update_map_layer_from_comparison = function() {
            plugin.update_map_layer(
                form_query_expression(comparison_panel.getForm()) + ' - ' +
                form_query_expression(climate_data_panel.getForm())
            );
        };
        var update_map_layer_comparison_button = new Ext.Button({
            text: 'Compare on map (B - A)',
            disabled: false,
            handler: plugin.update_map_layer_from_comparison
        });
        comparison_panel.addButton(update_map_layer_comparison_button);
        items.push(comparison_panel);

        var quick_filter_data_store = plugin.quick_filter_data_store = new Ext.data.SimpleStore({
            fields: ['name', 'option']
        });
        var quick_filter_combo_box = new Ext.form.ComboBox({
            fieldLabel: 'Region',
            hiddenName: 'region',
            store: quick_filter_data_store,
            displayField: 'name',
            typeAhead: true,
            mode: 'local',
            triggerAction: 'all',
            emptyText: '',
            selectOnFocus: true,
            forceSelection: true
        });
        var quick_filter_panel = new Ext.Panel({
            id: 'quick_filter_panel',
            title: 'Region filter',
            collapsible: true,
            collapseMode: 'mini',
            collapsed: false,
            items: [
                quick_filter_combo_box
            ]
        });
        quick_filter_combo_box.on(
            'select',
            function(combo_box, record, index) {
                plugin.filter_box.set_filter('within("'+record.data.name+'")');
            }
        );
        items.push(quick_filter_panel);

        var show_chart_button = new Ext.Button({
            text: 'Show chart for selected places',
            disabled: true,
            handler: function() {
                // create URL
                var place_ids = [];
                var place_names = [];
                each(
                    plugin.overlay_layer.selectedFeatures, 
                    function(feature) {
                        var place_id = feature.attributes.place_id;
                        place_ids.push(place_id);
                        var place = plugin.places[place_id];
                        var place_data = place.data;
                        if (place_data.station_name != undefined) {
                            place_names.push(place_data.station_name);
                        }
                        else {
                            place_names.push(
                                '('+place_data.latitude+','+place_data.longitude+')'
                            );
                        }
                    }
                );
                place_names.sort();
                plugin.last_query_expression;
                var query_expression = plugin.last_query_expression;
                var spec = JSON.stringify({
                    place_ids: place_ids,
                    query_expression: query_expression
                });

                var chart_name = [
                    query_expression.replace(
                        new RegExp('[",]', 'g'), ''
                    ).replace(
                        new RegExp('[()]', 'g'), ' '
                    ),
                    'for '+place_names.join(', ')
                ].join(' ').replace(
                    new RegExp('\\s+', 'g'), ' '
                );

                // get hold of a chart manager instance
                if (!plugin.chart_window || typeof plugin.chart_window.chart_manager == 'undefined') {
                    var chart_window = plugin.chart_window = window.open(
                        plugin.chart_popup_URL,
                        'chart', 
                        'width=660,height=600,toolbar=0,resizable=0'
                    );
                    chart_window.onload = function() {
                        chart_window.chart_manager = new chart_window.ChartManager(plugin.chart_URL);
                        chart_window.chart_manager.addChartSpec(
                            spec, 
                            chart_name
                        );
                    };
                    chart_window.onbeforeunload = function() {
                        delete plugin.chart_window;
                    };
                } else {
                    // some duplication here:
                    plugin.chart_window.chart_manager.addChartSpec(spec, chart_name);
                }
            }
        });
        plugin.show_chart_button = show_chart_button;

        items.push(show_chart_button);

        var print_button = new Ext.Button({
            text: 'Download printable map image',
            disabled: false,
            handler: function() {
                // make the map use the full window
                // plugin.full_window()
                // add a button on the map "Download image"
                plugin.request_image();
                print_button.disable();
            }
        });
        plugin.print_button = print_button;
        print_button.disable();
        items.push(print_button);

        items.push({
            autoEl: {
                    tag: 'div',
                    id: 'error_div'
                }                
            }
        );
        plugin.set_status = function(html_message) {
            $('#error_div').html(html_message);
        };

        plugin.colour_scale = new ColourKey();
        plugin.colour_scale.on_change(plugin.render_map_layer);
        map.addControl(plugin.colour_scale);
        plugin.colour_scale.activate();

        plugin.query_box = new QueryBox({
            updated: plugin.update_map_layer
        });
        map.addControl(plugin.query_box);

        plugin.query_box.activate();
    };
};
