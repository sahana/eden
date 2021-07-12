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

        // TODO if cwa-retry button exists:
        // - disable + hide the cwa-pdf button in the same form
        // - set retry-counter to 5
        // otherwise:
        // - enable + show the cwa-pdf button

        // TODO register action for cwa-retry button if it exists
        // Render a throbber in place of the retry-button, hide the button
        // Make an ajax-request to url using POST and JSON-data
        // if Ajax is successful:
        // - enable + show cwa-pdf button
        // - set retry-counter to 0
        // - remove the throbber and the retry-button
        // otherwise:
        // - remove the throbber
        // - decrease retry-counter
        // - remove retry-button if retry-count is 0 otherwise show the retry-button

        // Action for cwa-pdf button
        var downloadCertificatePDF = function(pdfButton) {

            var certificate = pdfButton.closest('form'),
                cwadata = $('input[name="cwadata"]', certificate).val(),
                formurl = $('input[name="formurl"]', certificate).val(),
                formkey = $('input[name="_formkey"]', certificate).val();

            if (!cwadata || !formurl || !formkey) {
                return;
            }

            var form = document.createElement('form');

            form.action = formurl + '/certify.pdf';
            form.method = 'POST';
            form.target = '_blank';
            form.enctype = 'multipart/form-data';

            var input;

            input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'cwadata';
            input.value = cwadata;
            form.appendChild(input);

            input = document.createElement('input');
            input.type = 'hidden';
            input.name = '_formkey';
            input.value = formkey;
            form.appendChild(input);

            form.style.display = 'none';
            document.body.appendChild(form);
            form.submit();
        };

        $('button.cwa-pdf').off(ns).on('click' + ns, function() {
            downloadCertificatePDF($(this));
        });
    });
})(jQuery);
