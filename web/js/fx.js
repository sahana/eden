$(document).ready(function() {
  
// main vertical scroll
$("#main").scrollable({
 
	// basic settings
	vertical: true,
 
	// up/down keys will always control this scrollable
	keyboard: 'static',
 
	// assign left/right keys to the actively viewed scrollable
	onSeek: function(event, i) {
		horizontal.eq(i).data("scrollable").focus();
	}
 
// main navigator (thumbnail images)
}).navigator("#main_navi");
 
// horizontal scrollables. each one is circular and has its own navigator instance
var horizontal = $(".scrollable").scrollable({ circular: true }).navigator(".navi");
 
 
// when page loads setup keyboard focus on the first horzontal scrollable
horizontal.eq(0).data("scrollable").focus();
 
});
