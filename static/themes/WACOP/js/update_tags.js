// Tags for Posts (Alerts/Updates) in create/update forms (dataList tags done in controllers.py _updates_html()
function wacop_update_tags(tags) {
    // @ToDo: i18n
    var tags_row = '<div class="form-row row" id="cms_post_tags__row"><div class="small-12 columns"><label class="" for="cms_post_tags" id="cms_post_tags__label">Tags:</label><div class="controls"><input class="hide" id="cms_post_tags" name="tags" type="text"></input><ul id="cms_post_tags_ul"></ul></div></div></div>';

    $('#cms_post_body__row').after(tags_row);

    // Populate for Update forms
    $('#cms_post_tags').val(tags);

    $('#cms_post_tags_ul').tagit({
        // @ToDo: i18n
        placeholderText: 'Add tags here…',
        singleField: true,
        singleFieldNode: $('#cms_post_tags'),
        autocomplete: {
            source: S3.Ap.concat('/cms/tag/tag_list.json')
        }//,
    });    
}
