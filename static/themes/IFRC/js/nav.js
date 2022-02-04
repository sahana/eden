$(document).ready(function() {
  $('#nav').children('li').on('mouseover', function() {
    $(this).children('.sub-menu').show();
  });
  $('#nav').children('li').on('mouseout', function() {
    $(this).children('.sub-menu').hide();
  });
});