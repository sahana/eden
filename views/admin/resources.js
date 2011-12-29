<script type="text/javascript">//<![CDATA[
// These are the resources available to import/export functions
$(function() {
    // When the Module changes:
	$("select[name='module']").change(function() {
		// What is the new module?
        module = $(this).val();
        if (module == "cr") {
            var options_resource = ["shelter"];
        } else if (module == "org") {
            var options_resource = ["organisation", "office", "staff"];
        } else if (module == "pr") {
            var options_resource = ["person"];
        } else if (module == "gis") {
            var options_resource = ["location"];
        } else if (module == "budget") {
            var options_resource = ["item", "kit_item"];
        }
        // Refresh the resource lookuplist
        // ToDo: Pull from Database using AJAX/JSON:
        // http://remysharp.com/2007/01/20/auto-populating-select-boxes-using-jquery-ajax/
        // http://groups.google.com/group/web2py/msg/b2d536d444001565
		var options = '';
        //for (var i = 0; i < options_subtype.length; i++) {
        for(key in options_resource) {
            options += '<option value="' + options_resource[key] + '">' + options_resource[key] + '</option>';
        }
        $("select[name='resource']").html(options);
        // ToDo: Provide option to update the Key field from DB using AJAX/JSON
	})
});
//]]></script>
