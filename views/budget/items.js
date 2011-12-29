<script type="text/javascript">//<![CDATA[
$(function() {
    // Default to One-time costs
    // Hide the Running Cost inputs
    $("#budget_item_monthly_cost__row").hide();
    $("#budget_item_minute_cost__row").hide();
    $("#budget_item_megabyte_cost__row").hide();
            
    // When the Cost type changes:
	$("select[name='cost_type']").change(function() {
		// What is the new cost type?
        cost_type=$(this).val();
        if (cost_type==2) {
            // Hide the Category
            $("#budget_item_category_type__row").hide();
            // Hide the Unit Cost input
            $("#budget_item_unit_cost__row").hide();
            // Show the Running Cost inputs
            $("#budget_item_monthly_cost__row").show();
            $("#budget_item_minute_cost__row").show();
            $("#budget_item_megabyte_cost__row").show();
        } else if (cost_type==1) {
            // Hide the Running Cost inputs
            $("#budget_item_monthly_cost__row").hide();
            $("#budget_item_minute_cost__row").hide();
            $("#budget_item_megabyte_cost__row").hide();
            // Show the Category & Unit Cost input
            $("#budget_item_category_type__row").show();
            $("#budget_item_unit_cost__row").show();
        }
	})
    
    // Set unused values before submitting form
    $("input[type='submit']:last").click(function(event){
        // What is the final cost type?
        cost_type=$("select[name='cost_type']").val();
        if (cost_type==2) {
            // Set the Category
            $('#budget_item_category_type').val("Running Cost")
            // Set the Unit Cost input
            $('#budget_item_unit_cost').val('0.0')
        } else if (cost_type==1) {
            // Set the Running Cost inputs
            $('#budget_item_monthly_cost').val('0.0')
            $('#budget_item_minute_cost').val('0.0')
            $('#budget_item_megabyte_cost').val('0.0')
        }
        // Pass to RESTlike CRUD controller
        event.default();
        return false;
    })
});
//]]></script>
