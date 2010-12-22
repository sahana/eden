$(document).ready(function(){
    var latlng = new google.maps.LatLng( {{ user.get_profile.latitude|stringformat:"s" }}, {{ user.get_profile.longitude|stringformat:"s" }} );
    var opts = {
        zoom: 15,
        center: latlng,
        mapTypeId: google.maps.MapTypeId.ROADMAP
    };
    var map = new google.maps.Map(document.getElementById("location"), opts);
    var marker = new google.maps.Marker({
        position: latlng,
        map: map,
        title:"User!"
    });
});
