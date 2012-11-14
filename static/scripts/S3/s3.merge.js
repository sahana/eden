/**
    S3Merge Static JS Code
*/

$(document).ready(function() {
    $('.swap_button').click(function() {
        // Swap widgets between original and duplicate side
        var id = this.id;
        var name = id.slice(5);

        var original = $('#original_' + name);
        var original_name = original.attr('name');
        var original_id = original.attr('id');
        var original_parent = original.parent();

        var duplicate = $('#duplicate_' + name);
        var duplicate_name = duplicate.attr('name');
        var duplicate_id = duplicate.attr('id');
        var duplicate_parent = duplicate.parent();

        var o = original.detach();
        o.attr('id', duplicate_id);
        o.attr('name', duplicate_name);

        var d = duplicate.detach();
        d.attr('id', original_id);
        d.attr('name', original_name);

        o.appendTo(duplicate_parent);
        d.appendTo(original_parent);
    });
});
