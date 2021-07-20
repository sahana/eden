$(document).ready(function(){

    var appsBtn = $('#apps-btn'),
        appsFrame = $('#apps-frame'),
        menuBtn = $('#menu-btn'),
        menuDiv = $('#menu-options')
        userBtn = $('#user-btn'),
        userDiv = $('#user-menu');

    var showAppsMenu = function() {
        // Show the App Switcher
        appsFrame.removeClass('hide')
                 .parent().css('margin-top', '57px');
        // Highlight the active control
        appsBtn.css('background-color', '#d9dadb');
    }

    var hideAppsMenu = function() {
        // Hide the App Switcher
        appsFrame.addClass('hide')
                 .parent().css('margin-top', '-500px');
        // Remove Highlight
        appsBtn.css('background-color', '');
    }

    var showUserMenu = function() {
        // Show the User Menu
        userDiv.removeClass('hide')
                 .css('margin-top', '57px');
    }

    var hideUserMenu = function() {
        // Hide the User Menu
        userDiv.addClass('hide')
                 .css('margin-top', '-500px');
    }

    appsBtn.on('click', function() {
        if (appsFrame.hasClass('hide')) {
            hideUserMenu();
            showAppsMenu();
            // Hide the tooltip
            var tooltipSelector = appsBtn.data('selector');
            $('span[data-selector="' + tooltipSelector + '"]').hide();
        } else {
            hideAppsMenu();
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

    userBtn.on('click', function() {
        if (userDiv.hasClass('hide')) {
            hideAppsMenu();
            showUserMenu();
            // Hide the tooltip
            var tooltipSelector = userBtn.parent().data('selector');
            $('span[data-selector="' + tooltipSelector + '"]').hide();
        } else {
            hideUserMenu();
        }
    });

});