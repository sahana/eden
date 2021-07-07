/**
 * Test Result Registration - client-side logic
 *
 * @copyright 2021 (c) Sahana Software Foundation
 * @license MIT
 */
(function($, undefined) {

    "use strict";

    $(document).ready(function() {

        var ns = '.register-result',
            reportToCWA = $('#test_result_report_to_cwa'),
            pdata = $('#test_result_first_name, #test_result_last_name, #test_result_date_of_birth');

        // Toggle consent options depending on CWA options
        var toggleConsentOption = function() {
            var cwaOption = reportToCWA.val();

            var consentRequired;
            switch(cwaOption) {
                case "ANONYMOUS":
                    consentRequired = "CWA_ANONYMOUS";
                    pdata.val('').closest('.form-row').hide();
                    break;
                case "PERSONAL":
                    consentRequired = "CWA_PERSONAL";
                    pdata.closest('.form-row').show();
                    break;
                default:
                    pdata.val('').closest('.form-row').hide();
                    break;
            }

            var consentWidget = $('#consent-consent'),
                inst = consentWidget.consentQuestion('instance');
            if (consentRequired) {
                // Show only relevant consent option, deselect+hide all others
                consentWidget.closest('.form-row').show();
                $('.consent-checkbox', consentWidget).each(function() {
                    var $this = $(this),
                        code = $this.data('code');
                    if (code && consentRequired && code == consentRequired) {
                        $this.closest('.consent-option').show();
                    } else {
                        if (inst !== undefined) {
                            inst.deselect(code);
                        }
                        $this.closest('.consent-option').hide();
                    }
                });
            } else {
                // Hide the consent row altogether
                consentWidget.closest('.form-row').hide();
                // Deselect all consent options
                if (inst) {
                    $('.consent-checkbox', consentWidget).each(function() {
                        inst.deselect($(this).data('code'));
                    });
                }
            }
        };
        toggleConsentOption();
        reportToCWA.off(ns).on('change' + ns, function() {
            toggleConsentOption();
        });

        // Toggle personal certificate option depending on result
        var togglePersonalOption = function() {
            var result = $('#test_result_result').val();

            if (!result) {
                // No result entered yet
                reportToCWA.val('NO');
                $('option', reportToCWA).each(function() {
                    var $this = $(this);
                    $this.prop('disabled', $this.val() != "NO");
                });
            } else if (result == 'NEG') {
                // Negative result => all options available
                $('option', reportToCWA).each(function() {
                    $(this).prop('disabled', false);
                });
            } else {
                // Positive result => disallow personal
                if (reportToCWA.val() == "PERSONAL") {
                    // Reduce to anonymous reporting
                    reportToCWA.val('ANONYMOUS');
                }
                $('option', reportToCWA).each(function() {
                    var $this = $(this);
                    $this.prop('disabled', $this.val() == "PERSONAL");
                });
            }
            toggleConsentOption();
        };
        $('#test_result_result').off(ns).on('change' + ns, function() {
            togglePersonalOption();
        });
        togglePersonalOption();

    });
})(jQuery);
