function splitview(url, title, ratio) {
    var availablex = window.innerWidth; // Total available width
    var availabley = window.innerHeight; // Total available height
    var leftwindowx = Math.floor(availablex * (1-ratio)); // Left windows' width
    var rightwindowx = Math.floor(availablex * ratio); // Right windows' size
    var tolerance = 20; // Some browsers seem to make measuring mistakes. This ensures there is a gap between the two windows. If the two windows overlay each other, increase this.

    if (typeof window.resizeTo(leftwindowx, availabley) == 'undefined') { // We might not be allowed to change the browsers' size, so there is a fallback.
        console.log('Your browser does not support window resizing, opening a popup instead');
        window.open(document.location.href, 'Sahana Eden', 'innerWidth=' + leftwindowx + ', innerHeight=' + availabley + ', screenY=' + window.screenY + ', screenX=' + window.screenX);
	}
    window.open(url, title, 'innerWidth=' + (rightwindowx - tolerance) + ', innerHeight=' + availabley + ', screenY=' + window.screenY + ', screenX=' + (window.screenX + leftwindowx + tolerance));
}