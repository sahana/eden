/**
 * Used by the User Manager's Roles Tab
 * - Hide Entity except for OrgAdmin
 */

$(document).ready(function() {
    var component = $('#component'),
        role,
        $this;

    // Bind to top-level element to catch new additions
    component.on('change.s3', '.rm-item-select', function() {
        $this = $(this);
        role = $this.val();
        if (role == 5) {
            // Org Admin: Show the Realm Entity
            $this.parent().next().show();
        } else {
            // Hide the Realm Entity (we automate the assignment)
            $this.parent().next().hide();
        }
    });

});