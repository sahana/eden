/*
 * Demo script for tree map functionality - to be removed after implementation
 */

var labelType, useGradients, nativeTextSupport, animate;

(function() {
  var ua = navigator.userAgent,
      iStuff = ua.match(/iPhone/i) || ua.match(/iPad/i),
      typeOfCanvas = typeof HTMLCanvasElement,
      nativeCanvasSupport = (typeOfCanvas == 'object' || typeOfCanvas == 'function'),
      textSupport = nativeCanvasSupport
        && (typeof document.createElement('canvas').getContext('2d').fillText == 'function');
  //I'm setting this based on the fact that ExCanvas provides text support for IE
  //and that as of today iPhone/iPad current text support is lame
  labelType = (!nativeCanvasSupport || (textSupport && !iStuff))? 'Native' : 'HTML';
  nativeTextSupport = labelType == 'Native';
  useGradients = nativeCanvasSupport;
  animate = !(iStuff || !nativeCanvasSupport);
})();

var Log = {
  elem: false,
  write: function(text){
    if (!this.elem)
      this.elem = document.getElementById('log');
    this.elem.innerHTML = text;
    this.elem.style.left = (500 - this.elem.offsetWidth / 2) + 'px';
  }
};

var sdata = {
    "name": "CountryX",
    "level": 0,
    "indicators": {
        "0": 3,
        "1": 2,
        "2": 4,
    },
    "population": 21768322,
    "children": [
        {
            "name": "ProvinceA",
            "level": 1,
            "indicators": {
                "0": 4,
                "1": 3,
                "2": 5,
            },
            "population": 1768322,
            "children": [
                {
                    "name": "DistrictA",
                    "level": 2,
                    "indicators": {
                        "0": 3,
                        "1": 1,
                        "2": 5,
                    },
                    "population": 768322,
                    "children": []
                },
                {
                    "name": "DistrictB",
                    "level": 2,
                    "indicators": {
                        "0": 3,
                        "1": 2,
                        "2": 4,
                    },
                    "population": 228322,
                    "children": []
                },
            ]
        },
        {
            "name": "ProvinceB",
            "level": 1,
            "indicators": {
                "0": 4,
                "1": 5,
                "2": 3,
            },
            "population": 4328322,
            "children": [
                {
                    "name": "DistrictC",
                    "level": 2,
                    "indicators": {
                        "0": 5,
                        "1": 5,
                        "2": 5,
                    },
                    "population": 468322,
                    "children": []
                },
                {
                    "name": "DistrictD",
                    "level": 2,
                    "indicators": {
                        "0": 3,
                        "1": 2,
                        "2": 4,
                    },
                    "population": 628322,
                    "children": []
                },
            ]
        },
        {
            "name": "ProvinceC",
            "level": 1,
            "indicators": {
                "0": 1,
                "1": 1,
                "2": 1,
            },
            "population": 301230,
            "children": [
                {
                    "name": "DistrictE",
                    "level": 2,
                    "indicators": {
                        "0": 5,
                        "1": 5,
                        "2": 5,
                    },
                    "population": 27834,
                    "children": []
                },
                {
                    "name": "DistrictF",
                    "level": 2,
                    "indicators": {
                        "0": 2,
                        "1": 3,
                        "2": 1,
                    },
                    "population": 191645,
                    "children": []
                },
            ]
        }
    ]
};

var h = {
    "0": "Country",
    "1": "Province",
    "2": "District",
    "3": "Commune"
};

var colors = ["#999", "#ff5121", "#f4961c", "#d6b317", "#77b82e", "#059346"];

function population(node) {

    var pop = 0;
    if (node.children.length > 0) {
        for (var i=0; i<node.children.length; i++) {
            p = population(node.children[i]);
            pop += p;
        }
    } else {
        pop = node.population;
    }
    return pop;
}

function create_node(node, indicator_index) {

    var children = [];
    for (var i=0; i<node.children.length; i++) {
        var subnode = create_node(node.children[i], indicator_index);
        children.push(subnode);
    }
    var v = node.indicators[indicator_index];
    if (v != null) {
        var color = colors[v];
    }
    var p = population(node);
    var json = {
        "children": children,
        "data": {
            "level": node.level,
            "population": p,
            "indicator_index": indicator_index,
            "indicator": v,
            "$color": color,
            "$area": p
        },
        "id": node.name,
        "name": node.name
    }
    return json;
}

function init(){

  var json = create_node(sdata, 1);

  //init TreeMap
  var tm = new $jit.TM.Squarified({

    //where to inject the visualization
    injectInto: 'infovis',

    //parent box title heights
    titleHeight: 15,

    //enable animations
    animate: false, //animate,

    //box offsets
    offset: 1,

    //Attach left and right click events
    Events: {
      enable: true,
      onClick: function(node) {
        if(node) tm.enter(node);
      },
      onRightClick: function() {
        tm.out();
      }
    },

    duration: 1000,

    //Enable tips
    Tips: {

      enable: true,

      //add positioning offsets
      offsetX: 20,
      offsetY: 20,

      //implement the onShow method to
      //add content to the tooltip when a node
      //is hovered
      onShow: function(tip, node, isLeaf, domElement) {
        var html = "<div class=\"tip-title\">" + node.name
          + "</div><div class=\"tip-text\">";
        var data = node.data;
        if(data.indicator) {
          html += "value: " + data.indicator;
        }
        tip.innerHTML =  html;
      }
    },

    //Add the name of the node in the correponding label
    //This method is called once, on label creation.
    onCreateLabel: function(domElement, node){
        domElement.innerHTML = node.name;
        var style = domElement.style;
        style.display = '';
        style.border = '1px solid transparent';
        domElement.onmouseover = function() {
          style.border = '1px solid #9FD4FF';
        };
        domElement.onmouseout = function() {
          style.border = '1px solid transparent';
        };
    }
  });
  tm.loadJSON(json);
  tm.refresh();
}

$(document).ready(function() {
    init();
});
