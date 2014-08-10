// Used by smoke tests to get all the links in the current page

var anchor_elems = document.getElementsByTagName('a');
var urls = [];
var url;
for (var i = 0; i< anchor_elems.length; i++)
{
    url = anchor_elems[i].href;
    urls.push(url);
}
return urls;
