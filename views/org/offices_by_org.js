// User selects Organisation first
// the Office select fills up with related offices
var load_offices = function(selectlast) {
    var url = '{{=URL(c='org',f='office', args="search.json", vars={"filter":"=", "field":"organisation_id", "value":""})}}' + 
                $("#org_staff_organisation_id").val();
    var offices_ok = function(data, status){
	    var options = '';
	    var v = '';
	    if (data.length == 0) {
            options += '<option value="">' + '{{=T("No offices registered for organisation")}}</options>';
        } else {
            $("#org_staff_office_id").val(data[0].id);
            if(!selectlast)
                options += '<option value="" selected>' + '{{=T("Select an office")}}' + '...</option>';
            for (var i = 0; i < data.length; i++){
                v = data[i].id;
                options += '<option value="' +  data[i].id + '">' + data[i].name + '</option>';
            }
	    }
	    $('#org_staff_office_id').html(options); 
	    if(selectlast)
            $('#org_staff_office_id').val(v); 
	};	
    $.getJSONS3(url, offices_ok, '{{=T("offices by organisation")}}');
};