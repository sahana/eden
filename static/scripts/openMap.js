var opened = false;
function openMap(start, end){
    if(!opened){
         var dialog = document.createElement("DIALOG");
        $(dialog).width("800px");
        $(dialog).height("700px");
        $(dialog).html('<div id="map-canvas" style="width:400px; height:600px;"></div><div id="directions" style="width:200px; height:600px;"></div>');
        $(dialog).appendTo('body');
        $(dialog).appendTo('body');
        setmap(start,end);
        opened = true;
    }
    dialog.showModal();
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
					directionsDisplay.setPanel(document.getElementById("directions"));
					var start = st;	//Worksite address
					var end = en;
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