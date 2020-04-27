/**
 * Used by the Timeline custom methods in IRS & Project
 * This script is in Static to allow caching
 * Dynamic constants (e.g. Internationalised strings) are set in server-generated script
 */

// Replace timeline-api.js
Timeline = new Object();
Timeline.DateTime = window.SimileAjax.DateTime; // for backward compatibility
// @ToDo: restore locales
Timeline.serverLocale = 'en';
Timeline.clientLocale = 'en';
Timeline.urlPrefix = Timeline_urlPrefix;

// Module pattern to hide internal vars
(function () {

    var eventSource;

    /* Google Calendar */
    // Called as Callback so needs to be in global scope
    S3.timeline.loadGDataCallback = function(json) {
        var entries = json.feed.entry;
        var events = new Array();
        for (var i = 0; i < entries.length; ++i) {
            var entry = entries[i];
            if ( entry["gd$when"] === null ) continue;
            var when = entry["gd$when"][0];
            var start = convertFromGDataDate(when.startTime);
            var end = convertFromGDataDate(when.endTime);
            var title = entry.title.$t;
            var description = entry.content.$t;
            var link = entry.link[0].href;
            var event = {'start': start,
                         'end': end,
                         'title': title,
                         'description': description,
                         'link': link
                        };
            events.push(event);
        }
        S3.timeline.data = {'dateTimeFormat': 'iso8601',
                            'events': events
                            };
        var url = '.';
        eventSource.loadJSON(S3.timeline.data, url);
        var tl = S3.timeline.tl;
        tl.hideLoadingMessage();
        tl.layout();
    };

    var zeroPad = function(n) {
        if (n < 0) {
            throw new Error('n is negative');
        }
        return (n < 10) ? '0' + n : n;
    };

    var convertToGDataDate = function(/*Date*/ date) {
      return date.getFullYear() + '-' +
             zeroPad(date.getMonth() + 1) + '-' +
             zeroPad(date.getDate());
    };

    var convertFromGDataDate = function(/*string<YYYY-MM-DD>*/ date) {
        var match = date.match(/(\d{4})-(\d{2})-(\d{2})/);
        return new Date(parseInt(match[1], 10), parseInt(match[2], 10) - 1, parseInt(match[3], 10));
    };

    // Called from $(document).ready() so needs to be in global scope
    S3.timeline.onLoadCalendar = function() {
        eventSource = new Timeline.DefaultEventSource();
        var tl_el = document.getElementById('s3timeline');
        var theme = Timeline.ClassicTheme.create();
        theme.event.bubble.width = 320;
        theme.event.bubble.height = 180;

        // centering the timeline three months previous makes it look nicer on load
        var threeDaysFromNow = new Date(((new Date).getTime()) + 3 * 24 * 60 * 60 * 1000);
        var bandInfos = [
            Timeline.createBandInfo({
                eventSource:    eventSource,
                date:           threeDaysFromNow,
                width:          "40%", 
                intervalUnit:   Timeline.DateTime.WEEK, 
                intervalPixels: 300,
                theme:          theme
            }),
            Timeline.createBandInfo({
                eventSource:    eventSource,
                date:           threeDaysFromNow,
                width:          "60%", 
                intervalUnit:   Timeline.DateTime.MONTH, 
                intervalPixels: 550,
                theme:          theme
            })
        ];
        bandInfos[1].syncWith = 0;
        bandInfos[1].highlight = true;
        var tl = Timeline.create(tl_el, bandInfos);
        // Pass to global scope
        S3.timeline.tl = tl;

        tl.showLoadingMessage();
        // Atom feed from a Google calendar
        var feedUrl = S3.timeline.calendar;
        var startDate = new Date((new Date).getDate());
        var endDate = new Date(((new Date).getTime()) + 3 * 30 * 24 * 60 * 60 * 1000);
        var getParams = '?start-min=' + convertToGDataDate(startDate) +
                        '&start-max=' + convertToGDataDate(endDate) +
                        '&alt=json-in-script' +
                        '&callback=S3.timeline.loadGDataCallback' +
                        '&max-results=5000'; // choose 5000 as an arbitrarily large number
        feedUrl += getParams;
        var scriptTag = document.createElement('script');
        scriptTag.src = feedUrl;
        document.body.appendChild(scriptTag);
    };

    /* Data provided as JSON: S3.timeline.data */
    // Called from $(document).ready() so needs to be in global scope
    S3.timeline.onLoad = function() {
        eventSource = new Timeline.DefaultEventSource();
        var tl_el = document.getElementById('s3timeline');
        var theme = Timeline.ClassicTheme.create();
        theme.timeline_start = new Date(S3.timeline.tl_start);
        theme.timeline_stop  = new Date(S3.timeline.tl_end);
        theme.event.bubble.width = 320;
        theme.event.bubble.height = 180;
        var now = Timeline.DateTime.parseIso8601DateTime(S3.timeline.now);
        var bandInfos = [
            Timeline.createBandInfo({
                width:          '90%',
                intervalUnit:   Timeline.DateTime.DAY,
                intervalPixels: 140,
                eventSource:    eventSource,
                date:           now,
                theme:          theme
            }),
            Timeline.createBandInfo({
                overview:       true,
                width:          '10%',
                intervalUnit:   Timeline.DateTime.MONTH,
                intervalPixels: 200,
                eventSource:    eventSource,
                date:           now
            })
        ];
        bandInfos[1].syncWith = 0;
        bandInfos[1].highlight = true;
        var tl = Timeline.create(tl_el, bandInfos, Timeline.HORIZONTAL);
        var url = '.';
        eventSource.loadJSON(S3.timeline.data, url);
        tl.layout();
        // Pass to global scope
        S3.timeline.tl = tl;
    };

    /* Common functions */
    var resizeTimerID = null;

    // Called from $(document).ready() so needs to be in global scope
    S3.timeline.onResize = function() {
        if (resizeTimerID === null) {
            resizeTimerID = window.setTimeout(function() {
                resizeTimerID = null;
                S3.timeline.tl.layout();
            }, 500);
        }
    };
}());
 
$(document).ready(function() {
    $(window).on('load', function() {
        if (S3.timeline.calendar) {
            SimileAjax.History.enabled = false;
            // Google Calendar
            S3.timeline.onLoadCalendar();
        } else if (S3.timeline.tl_start) {
            SimileAjax.History.enabled = false;
            // Normal Timeline
            S3.timeline.onLoad();
        }
    });
    $(window).resize(function() {
        if (S3.timeline.tl) {
            // Resize the Timeline when the window changes size
            S3.timeline.onResize();
        }
    });
}); 
