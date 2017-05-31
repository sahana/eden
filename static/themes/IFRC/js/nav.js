$(document).ready(function() {
  $('#nav').children('li').mouseover(function() {
    $(this).children('.sub-menu').show();
  });
  $('#nav').children('li').mouseout(function() {
    $(this).children('.sub-menu').hide();
  });
});