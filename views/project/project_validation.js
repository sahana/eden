<script type="text/javascript">//<![CDATA[
jQuery(document).ready(function() {
    $('.form-container > form').submit(function () {
        var datePattern = /^(19|20)\d\d([-\/.])(0[1-9]|1[012])\2(0[1-9]|[12][0-9]|3[01])$/;
        var start_date = this.start_date.value;
        var end_date = this.end_date.value;
        var error_msg;
        if ( (start_date && !(datePattern.test(start_date))) | (end_date && !(datePattern.test(end_date))) ) {
            error_msg = '{{=T("Start date and end date should have valid date values")}}';
            jQuery('#project_project_start_date__row > td').last().text(error_msg);
            jQuery('#project_project_start_date__row > td').last().addClass('red');
            return false;
        }
        start_date = start_date.split('-');
        start_date = new Date(start_date[0], start_date[1], start_date[2]);
        end_date = end_date.split('-');
        end_date = new Date(end_date[0], end_date[1], end_date[2]);
        if (start_date > end_date) {
            error_msg = '{{=T("End date should be after start date")}}';
            jQuery('#project_project_end_date__row > td').last().text(error_msg);
            jQuery('#project_project_end_date__row > td').last().addClass('red');
            return false;
        } else {
            return true;
        }
    });
});
//]]></script>
