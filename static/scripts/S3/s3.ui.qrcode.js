/**
 * jQuery UI Widget for QR code input
 *
 * @copyright 2021 (c) Sahana Software Foundation
 * @license MIT
 */
(function($, undefined) {

    "use strict";
    var qrScannerWidgetID = 0;

    /**
     * qrScannerWidget
     */
    $.widget('s3.qrScannerWidget', {

        /**
         * Default options
         *
         * @todo document options
         */
        options: {

            workerPath: null

        },

        /**
         * Create the widget
         */
        _create: function() {

            this.id = qrScannerWidgetID;
            qrScannerWidgetID += 1;

            this.eventNamespace = '.qrScannerWidget';
        },

        /**
         * Update the widget options
         */
        _init: function() {

            this.scanButton = $('.qrscan-btn', $(this.element).closest('.qrinput'));

            // Set up qr-scanner worker
            var workerPath = this.options.workerPath;
            if (workerPath) {
                QrScanner.WORKER_PATH = this.options.workerPath;
            }

            this.refresh();
        },

        /**
         * Remove generated elements & reset other changes
         */
        _destroy: function() {

            var scanner = this.scanner,
                videoInput = this.videoInput;

            if (scanner) {
                scanner.destroy();
                this.scanner = null;
            }

            if (videoInput) {
                videoInput.remove();
                this.videoInput = null;
            }

            $.Widget.prototype.destroy.call(this);
        },

        /**
         * Redraw contents
         */
        refresh: function() {

            var $el = $(this.element),
                self = this;

            this._unbindEvents();

            if (self.scanButton.length) {

                QrScanner.hasCamera().then(function(hasCamera) {

                    var scanButton = self.scanButton;

                    if (!hasCamera) {
                        scanButton.prop('disabled', true);
                        return;
                    } else {
                        scanButton.prop('disabled', false);
                    }

                    var scanner,
                        scanForm = $('<div>'),
                        // TODO make success-message configurable
                        success = $('<div>').html('<i class="fa fa-check">').hide().appendTo(scanForm),
                        videoInput = $('<video>').appendTo(scanForm);

                    // TODO move styles into CSS
                    success.css({
                        'text-align': 'center',
                        'font-size': '4rem',
                        'padding': '1rem',
                        'color': 'darkgreen',
                    });

                    // TODO make width/height configurable or auto-adapt to screen size
                    videoInput.css({width: '300', height: '300'});

                    var dialog = scanForm.dialog({
                        title: 'Scan QR Code',
                        autoOpen: false,
                        modal: true,
                        close: function() {
                            if (scanner) {
                                scanner.stop();
                                scanner.destroy();
                                scanner = null;
                            }
                        }
                    });

                    scanButton.on('click', function() {
                        videoInput.show();
                        success.hide();
                        dialog.dialog('open');
                        scanner = new QrScanner(videoInput.get(0),
                            function(result) {
                                videoInput.hide();
                                success.show();
                                $el.val(result);
                                setTimeout(function() {
                                    dialog.dialog('close');
                                }, 1000);
                            },
                            function( /* error */ ) {
                                // TODO handle error
                            });

                        scanner.start();
                        // TODO auto-close after timeout?
                    });
                });
            }

            this._bindEvents();
        },

        /**
         * Bind events to generated elements (after refresh)
         */
        _bindEvents: function() {
            return true;
        },

        /**
         * Unbind events (before refresh)
         */
        _unbindEvents: function() {
            return true;
        }
    });
})(jQuery);
