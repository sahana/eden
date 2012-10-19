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

var h = {
    "0": "Country",
    "1": "Province",
    "2": "District",
    "3": "Commune"
};

var colors = ["#999", "#ff5121", "#f4961c", "#d6b317", "#77b82e", "#059346"];

var tm = null;

function tmGetData(indicator_index) {

    if (tm != null) {
        $.ajax({
            'url': S3.Ap.concat('/vulnerability/tmdata'),
            'success': function(data) {
                var json = tmCreateNode(s, indicator_index);
                tm.loadJSON(json);
                tm.refresh();
            },
            'error': function(request, status, error) {
                if (error == 'UNAUTHORIZED') {
                    msg = S3.i18n.gis_requires_login;
                } else {
                    msg = request.responseText;
                }
                console.log(msg);
            },
            'dataType': 'script'
        });
    }
}

function tmPopulation(node) {

    var pop = 0;
    if (node.children.length > 0) {
        for (var i=0; i<node.children.length; i++) {
            p = tmPopulation(node.children[i]);
            pop += p;
        }
    } else {
        pop = node.population;
    }
    return pop;
}

function tmCreateNode(node, indicator_index) {

    var children = [];
    for (var i=0; i<node.children.length; i++) {
        var subnode = tmCreateNode(node.children[i], indicator_index);
        children.push(subnode);
    }
    var v = node.indicators[indicator_index];
    if (v != null) {
        var color = colors[v];
    }
    var p = tmPopulation(node);
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

function tmInit(){

  //init TreeMap
  tm = new $jit.TM.Squarified({

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
}

$(document).ready(function() {
    tmInit();
    tmGetData(0);
});
