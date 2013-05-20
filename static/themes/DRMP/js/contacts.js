/**
 * Used by the pr/person 'Contacts' page (templates/DRMP/config.py)
 * This script is in Static to allow caching
 * Dynamic constants (e.g. Internationalised strings) are set in server-generated script
 */

$(document).ready(function(){

    // Hide the inline row
    $('#pr_person_sub_human_resourcehuman_resource__row').hide();

    // Select the fields of interest
    var org_td = $('#add-row-human_resourcehuman_resource td:first');
    if (!org_td.length) {
        // Display view
        org_td = $('#pr_person_sub_human_resourcehuman_resource__row tr.read-row td:first()');
    }
    var job_td = org_td.next();
    var office_td = job_td.next();

    // Bootstrap form containers
    var control_group = '<div class="control-group"></div>';
    var controls = '<div class="controls"></div>';
    //var help_block = '<span class="help-block"></span>';

    // i18n labels
    var org_label = '<label id="hrm_human_resource_organisation_id__label" for="sub_human_resourcehuman_resource_human_resourcehuman_resource_i_organisation_id_edit_none" class="control-label"><div>' + i18n.organisation + ':</div></label>';
    var job_label = '<label id="hrm_human_resource_job_title_id__label" for="sub_human_resourcehuman_resource_human_resourcehuman_resource_i_job_title_id_edit_none" class="control-label"><div>' + i18n.job_title + ':</div></label>';
    var office_label = '<label id="hrm_human_resource_site_id__label" for="sub_human_resourcehuman_resource_human_resourcehuman_resource_i_site_id_edit_none" class="control-label"><div>' + i18n.office + ':</div></label>';

    // Move fields to their desired location
    $(control_group).prependTo('form.pr_person fieldset')
                    .append(org_label)
                    .append(controls);
    $('#hrm_human_resource_organisation_id__label').next()
                                                   .append(org_td);
                                                   //.append(help_block);
    
    $('#pr_person_sub_human_resourcehuman_resource__row').after(control_group)
                                                         .next()
                                                         .append(office_label)
                                                         .append(controls);
    $('#hrm_human_resource_site_id__label').next()
                                           .append(office_td);
                                           //.append(help_block);
    
    $('#pr_person_sub_human_resourcehuman_resource__row').after(control_group)
                                                         .next()
                                                         .append(job_label)
                                                         .append(controls);
    $('#hrm_human_resource_job_title_id__label').next()
                                                .append(job_td);
                                                //.append(help_block);
});