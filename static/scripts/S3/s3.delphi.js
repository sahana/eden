/* Static JavaScript code for the Delphi 'Vote' page */

// Status Functions for the AJAX Save
update_status = function() {
    $('#vote_button').removeClass('saving');
    $('#vote_button').addClass('saved');
    $('#vote_button').html(S3.i18n.delphi_saved);

    setTimeout(function(){
        window.location = S3.Ap.concat('/delphi/problem/' + problem_id + '/results');
    }, 100);
};

error = function(a) {
    $('#vote_button').html(S3.i18n.delphi_failed);

    setTimeout(function(){
        // @ToDo: Do this if rankings are changed
        $('#vote_button').removeClass('saved');
        $('#vote_button').html(S3.i18n.delphi_vote);
    }, 5000);
};

$(document).ready(function() {
    // Make the listings sortable
    $( '#solutions, #rankings' ).sortable({
        connectWith: '.connectedSortable',
        placeholder: 'ui-state-highlight'
    }).disableSelection();

    // AJAX Save
    $( '#vote_button' ).click(function() {
        $(this).html(S3.i18n.delphi_saving);
        $(this).addClass('saving');
        var ranks = $('#rankings').sortable('toArray').toString();
        var url = S3.Ap.concat('/delphi/save_vote/', problem_id);
        $.ajax({
            url: url,
            type: 'post',
            dataType: 'json',
            data: ranks,
            success: update_status,
            error: error
        });
    });
});