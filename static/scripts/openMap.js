var opened = false;
function openMap(start, end){
  if( !opened )
  {
    var dialog = document.createElement('div');
    $(dialog).html('<div id="map-canvas" style="width:95%;height:400px;"></div> <div id="map-dirs" style="width:95%;height:40%;"></div>');
    $(dialog).width('500px');
    $(dialog).height('800px');
    dialog.id = 'map-dialog';
    document.body.appendChild(dialog);
    setmap(start,end);
    opened = true;
  }
  $('#map-dialog').dialog({title: 'Directions',maxHeight: 800});
}

function setmap(st, en) {
  var map;
  var directionsService = new google.maps.DirectionsService();
  var directionsDisplay = new google.maps.DirectionsRenderer();

  //set lat lang to Raleigh by default
  var latlng = new google.maps.LatLng(35.779943, -78.641617);
  var mapOptions = {
    zoom: 10,
    center: latlng
  }
  map = new google.maps.Map(document.getElementById("map-canvas"), mapOptions);

  //if worksite address is set, show it on the map
  directionsDisplay.setMap(map);
  directionsDisplay.setPanel(document.getElementById("map-dirs"));
  var request = {
  origin:st,
  destination:en,
  travelMode: google.maps.DirectionsTravelMode.DRIVING,
  unitSystem: google.maps.UnitSystem.IMPERIAL
  };
  directionsService.route(request, function(response, status) {
    if (status == google.maps.DirectionsStatus.OK) {
       directionsDisplay.setDirections(response);
    }
  });
}
