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

        // Toggle QR Code / PDF-Download depending on CWA-send success
        var retryButton = $('button.cwa-retry'),
            pdfButton = $('button.cwa-pdf'),
            qrCode = $('div.cwa-qrcode'),
            retryCounter = 4;

        if (retryButton.length) {
            pdfButton.prop('disabled', true).hide();
            qrCode.hide();
        } else {
            pdfButton.prop('disabled', false).removeClass('hide').show();
            qrCode.removeClass('hide').show();
        }

        // Action for cwa-retry button
        var retrySendToCWA = function(btn) {

            var certificate = btn.closest('form'),
                cwadata = $('input[name="cwadata"]', certificate).val(),
                formurl = $('input[name="formurl"]', certificate).val(),
                formkey = $('input[name="_formkey"]', certificate).val();
            if (!cwadata || !formurl || !formkey) {
                return;
            }

            $('#alert-space .alert').fadeOut(200).remove();

            var throbber = $('<div class="inline-throbber">').insertAfter(btn.hide()),
                ajaxData = {
                    'cwadata': JSON.parse(cwadata),
                    'formkey': formkey,
                };

            $.ajaxS3({
                type: 'POST',
                url: formurl + '/cwaretry.json',
                data: JSON.stringify(ajaxData),
                dataType: 'json',
                retryLimit: 0,
                contentType: 'application/json; charset=utf-8',
                success: function() {
                    throbber.remove();
                    btn.remove();
                    retryCounter = 0;
                    pdfButton.prop('disabled', false).removeClass('hide').show();
                    qrCode.removeClass('hide').show();
                },
                error: function() {
                    throbber.remove();
                    if (retryCounter > 0) {
                        retryCounter--;
                        btn.show();
                    } else {
                        btn.remove();
                    }
                }
            });
        };

        // Action for cwa-pdf button
        var downloadCertificatePDF = function(btn) {

            var certificate = btn.closest('form'),
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

        // Attach actions to click-events
        retryButton.off(ns).on('click' + ns, function() {
            retrySendToCWA($(this));
        });
        pdfButton.off(ns).on('click' + ns, function() {
            downloadCertificatePDF($(this));
        });
    });
})(jQuery);
