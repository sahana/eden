//maintains the dialog state so content is not regenerated
var prevOpened = false;

/*
 * Method to open a directions map from a starting location
 * to an established destination using Google Maps JavaScript API v3
 * @param start The starting street address
 * @param end The destination street address
 */
function openMap(start, end){
   //first instance
   if( !prevOpened )
   {
      var dialog = document.createElement('div');
       $(dialog).html('<a class="action-btn center" style="text-align:center;margin:10px 10px 10px 0px; padding:15px;" onclick="printDiv()">Print Directions</a><div id="map-canvas" style="width:95%;height:400px;"></div> <div id="map-dirs" style="width:95%;height:40%;"></div>');
       $(dialog).width('500px');
       $(dialog).height('800px');
       dialog.id = 'map-dialog';
       document.body.appendChild(dialog);

       //set the created map and directions div
       setEndpoints(start,end);
       //set state to open
       prevOpened = true;
   }

   //map dialog is already instantiated, popup the div
   $('#map-dialog').dialog({title: 'Directions',maxHeight: 800});
}

/*
 * Method to print the directions of the delivery route
 * @return true
 */
function printDiv() {
   //open a new window
   var printWindow = window.open();

   //get directions from the div and append to new window
   var data = $('#map-dirs').html();
   printWindow.document.write('<html><head><title>Shipment Directions</title>');
   printWindow.document.write('</head><body >');
   printWindow.document.write(data);
   printWindow.document.write('</body></html>');

   //close new window and grant focus
   printWindow.document.close();
   printWindow.focus();

   //print the direction window and
   printWindow.print();
   printWindow.close();

   return true;
 }

/*
 * Method to set the staring and ending locations of the Google map and directions
 * @param start The starting street address
 * @param end The destination street address
 */
function setEndpoints(start, end) {
   var map;
   //initialize the directions service
   var directionsService = new google.maps.DirectionsService();
   var directionsDisplay = new google.maps.DirectionsRenderer();

   //set map options
   var mapOptions = {
     zoom: 8
   }
   //assign the map to the map-canvas div
   map = new google.maps.Map(document.getElementById("map-canvas"), mapOptions);

   //link the directions display to the map and assign it to the map-dirs div
   directionsDisplay.setMap(map);
   directionsDisplay.setPanel(document.getElementById("map-dirs"));

   //set parameters for the directions request, set travel mode to driving
   var request = {
      origin:start,
      destination:end,
      travelMode: google.maps.DirectionsTravelMode.DRIVING,
      unitSystem: google.maps.UnitSystem.IMPERIAL
   };

   //request the route to populate the directions display
   directionsService.route(request, function(response, status) {
      if (status == google.maps.DirectionsStatus.OK) {
         directionsDisplay.setDirections(response);
      }
   });
}
