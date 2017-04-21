// Tags for Posts (Alerts/Updates)
$(document).ready(function() {
    // @ToDo: i18n
    // @ToDo: Populate for Update forms
    var tags_row = '<div class="form-row row" id="cms_post_tags__row"><div class="small-12 columns"><label class="" for="cms_post_tags" id="cms_post_tags__label">Tags:</label><div class="controls"><input class="hide" id="cms_post_tags" name="tags" type="text"></input><ul id="cms_post_create_tags_ul"></ul></div></div></div>';

    $('#cms_post_body__row').after(tags_row);

    $('#cms_post_create_tags_ul').tagit({
        // @ToDo: i18n
        placeholderText: 'Add tags here…',
        singleField: true,
        singleFieldNode: $('#cms_post_create_tags')//,
        // @ToDo: make options visible
        //autocomplete: {
        //    source: S3.Ap.concat('/cms/tag/search_ac.json')
        //}
    });
});