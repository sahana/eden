$(document).ready(function(){

    var appsBtn = $('#apps-btn'),
        appsFrame = $('#apps-frame'),
        menuBtn = $('#menu-btn'),
        menuDiv = $('#menu-options');

    appsBtn.on('click', function() {
        if (appsFrame.hasClass('hide')) {
            // Show the App Switcher
            appsFrame.removeClass('hide')
                     .parent().css('margin-top', '57px');
            // Highlight the active control
            appsBtn.css('background-color', '#d9dadb');
        } else {
            // Hide the App Switcher
            appsFrame.addClass('hide')
                     .parent().css('margin-top', '250px');
            // Remove Highlight
            appsBtn.css('background-color', '');
        }
    });

    menuBtn.on('click', function() {
        if (menuDiv.hasClass('hide')) {
            // Show the Side Menu
            menuDiv.removeClass('hide');
            // Highlight the active control
            menuBtn.css('background-color', '#d9dadb');
        } else {
            // Hide the Side Menu
            menuDiv.addClass('hide');
            // Remove Highlight
            menuBtn.css('background-color', '');
        }
    });
});