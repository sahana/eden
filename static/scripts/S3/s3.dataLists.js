/**
 * Used by data lists (views/datalist.html)
 * This script is in Static to allow caching
 * Dynamic constants (e.g. Internationalised strings) are set in server-generated script
 */

function dlAutoRetrieve(item) {
    $(item).closest('.dl').infinitescroll('retrieve');
};

var url_append = function(url, query) {
    var parts = url.split('?'), q = '';
    var newurl = parts[0];
    if (parts.length > 1) {
        if (query) {
            q = '&' + query;
        }
        return (newurl + '?' + parts[1] + q);
    } else {
        if (query) {
            q = '?' + query;
        }
        return (newurl + q);
    }
}

function dlInfiniteScroll(datalist) {

    var pagination = $(datalist).find('.dl-pagination');
    if (!pagination.length) {
        // This dataList doesn't paginate
        return;
    }
    var dl_data = JSON.parse($(pagination[0]).val());

    // Read dl_data
    var startindex = dl_data['startindex'],
        maxitems = dl_data['maxitems'],
        pagesize = dl_data['pagesize'],
        ajaxurl = dl_data['ajaxurl'];

    // Compute bounds
    var maxindex = startindex + maxitems,
        initialitems = $(datalist).find('.dl-item').length;

    // Compute maxpage
    var maxpage = 1, ajaxitems = (maxitems - initialitems);
    if ( ajaxitems > 0) {
        maxpage += Math.ceil(ajaxitems / pagesize);
    } else {
        if (pagination.length) {
            pagination.css({display:'none'});
        }
        return;
    }

    if (pagination.length) {
        $(datalist).infinitescroll({
                debug: false,
                loading: {
                    finishedMsg: "no more items to load",
                    msgText: "loading...",
                    img: S3.Ap.concat('/static/img/indicator.gif')
                },
                navSelector: "div.dl-navigation",
                nextSelector: "div.dl-navigation a:first",
                itemSelector: "div.dl-item",
                path: function(page) {
                    // Compute start+limit
                    var start = initialitems + (page - 2) * pagesize;
                    var limit = Math.min(pagesize, maxindex - start);
                    // Construct Ajax URL
                    var url = url_append(ajaxurl, 'start=' + start + '&limit=' + limit);
                    return url;
                },
                maxPage: maxpage

            },
            function(data) {
                $('.dl').each(function() {
                    $(this).find('.dl-item:last:in-viewport').each(function() {
                        if (!$(this).hasClass('autoretrieve')) {
                            $(this).addClass('autoretrieve');
                            dlAutoRetrieve(this);
                        }
                    });
                });
            }
        );
    }
}

$(document).ready(function(){

    $('.dl').each(function() {
        dlInfiniteScroll(this);
    });
    $('.dl').each(function() {
        $(this).find('.dl-item:last:in-viewport').each(function() {
            $(this).addClass('autoretrieve');
            dlAutoRetrieve(this);
        });
    });
});

// END ========================================================================
