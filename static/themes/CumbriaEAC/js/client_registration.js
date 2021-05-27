$(document).ready(function(){

    // Hide 'Other Ethnicity' and 'Other Religion' fields
    // - unless appropriate entries selected

    var ethnicity = $('#pr_person_sub_physical_description_ethnicity'),
        ethnicity_other = $('#pr_person_sub_physical_description_ethnicity_other__row'),
        religion = $('#pr_person_sub_person_details_religion'),
        religion_other = $('#pr_person_sub_person_details_religion_other__row');

    ethnicity_other.hide();
    religion_other.hide();

    ethnicity.change(function() {
        if (['White: Any other White background',
             'Mixed/Multiple ethnic groups: Any other Mixed/Multiple ethnic background',
             'Asian/Asian British: Any other Asian background',
             'Black/African/Caribbean/Black British: Any other Black/African/Caribbean background',
             'Other ethnic group: Any other ethnic group'
             ].includes(ethnicity.val())) {
            // Show
            ethnicity_other.show();
        } else {
            // Hide
            ethnicity_other.hide();
        }
    });

    religion.change(function() {
        if (religion.val() == 'other') {
            // Show
            religion_other.show();
        } else {
            // Hide
            religion_other.hide();
        }
    });

});