<script type="text/javascript">//<![CDATA[
$(function() {
    var loading_categories = '<option value="">' + '{{=T("Loading Categories...")}}</option>';
    var select_category = '<option value="" selected>' + '{{=T("Select a category")}}' + '...</option>';
    var empty_set = '<option value="">' + '{{=T("No categories found")}}</option>';
    $('#gis_feature_class_category__row').hide();
    // When the Resource changes:
	$("select[name='resource']").change(function() {
		// What is the new resource?
        resource = $(this).val();
        if (resource == 'irs_ireport') {
            var widget = "<select id='gis_feature_class_category'>" + loading_categories + '</select>';
            $('#gis_feature_class_category__row > td.w2p_fw').html(widget);
            $('#gis_feature_class_category__row').show();
            var url = '{{=URL(c='irs',f='ireport', args="options.s3json", vars={"field":"category"})}}';
            load_categories = function(data, status){
                var options;
                if (data.option.length == 0) {
                    options = empty_set;
                } else {
                    options = select_category;
                    for (var i = 0; i < data.option.length; i++){
                        if (data.option[i].@value != '') {
                            options += '<option value="' +  data.option[i].@value + '">' + data.option[i].$ + '</option>';
                        }
                    }
                }
                $('#gis_feature_class_category').html(options);
            };
            $.getJSONS3(url, load_categories, false);
        } else {
            $('#gis_feature_class_category__row').hide();
        }
    })
});
//]]></script>
