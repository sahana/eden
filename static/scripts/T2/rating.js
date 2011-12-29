// JavaScript Document
/*************************************************
Star Rating System
First Version: 21 November, 2006
Author: Ritesh Agrawal, Modified heavily by Massimo Di Pierro 2008
Inspriation: 
Will Stuckey's star rating system (http://sandbox.wilstuckey.com/jquery-ratings/)
Demonstration: http://php.scripts.psu.edu/rja171/widgets/rating.php
Usage: $('#rating').rating({url:'www.url.to.post.com',maxvalue:5});

options
        url : required -- post changes to (null for no post)
	maxvalue: number of stars
	curvalue: number of selected stars
************************************************/

jQuery.fn.rating = function(options) {	
    curvalue=$(this).val()
    if(curvalue=='') curvalue=0;
    var settings = {
        url       : null, // post changes to 
        maxvalue  : 5,   // max number of stars
        curvalue  : curvalue,    // number of selected stars
        cancel: true,
        readonly: false
    };
    if(options) jQuery.extend(settings, options);
    input=$(this)
    container=$(this).after('<div class="rating"></div>').next();
    if (!settings.readonly && settings.cancel)
	 container.append('<div class="cancel"><a></a></div>');
    for(var i=settings.curvalue; i>0; i--)
          container.append('<div class="star on"><a></a></div>');	
    for(var i=settings.maxvalue; i>settings.curvalue; i--)
         container.append('<div class="star"><a></a></div>');	
    if(!settings.readonly) {
      var stars = $(container).children('.star');
      var cancel = $(container).children('.cancel');	
      stars
	    .mouseover(function(){
                value=stars.index(this) + 1;
                stars.filter(':lt('+value+')').addClass('hover');
            })
            .mouseout(function(){
                stars.removeClass('hover');
            })
            .click(function(){
                settings.curvalue = stars.index(this) + 1;
                input.val(settings.curvalue);
	        stars.filter(':lt('+settings.curvalue+')').addClass('on');
	        stars.filter(':gt('+(settings.curvalue-1)+')').removeClass('on');
                if(container.url) jQuery.post(container.url, {
                   "rating": $(this).children('a')[0].href.split('#')[1] 
                });
   	        return false;
            });

        // cancel button events
        cancel
            .mouseover(function(){
                $(this).addClass('on')
            })
            .mouseout(function(){
                $(this).removeClass('on')
            })
            .click(function(){               
	        settings.curvalue = 0;
                input.val(settings.curvalue);
                stars.removeClass('on');
                if(container.url) jQuery.post(container.url, {
                   "rating": $(this).children('a')[0].href.split('#')[1] 
                });
                return false;
            });
        }
	return(this);	
}
