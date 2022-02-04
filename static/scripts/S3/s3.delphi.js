/* Static JavaScript code for the Delphi 'Vote' page */

$(document).ready(function() {
    // Make the listings sortable
    $('#solutions, #rankings').sortable({
        connectWith: '.connectedSortable',
        placeholder: 'ui-state-highlight'
    }).disableSelection();

    // AJAX Save
    $('#vote_button').on('click', function() {
        $(this).html(i18n.delphi_saving);
        $(this).addClass('saving');
        var ranks = $('#rankings').sortable('toArray').toString();
        var url = S3.Ap.concat('/delphi/save_vote/', problem_id);
        $.ajax({
            url: url,
            type: 'post',
            dataType: 'json',
            data: ranks
        }).done(function(data) {
            $('#vote_button').removeClass('saving');
            $('#vote_button').addClass('saved');
            $('#vote_button').html(i18n.delphi_saved);

            setTimeout(function(){
                window.location = S3.Ap.concat('/delphi/problem/' + problem_id + '/results');
            }, 100);
        }).fail(function(jqXHR, textStatus, errorThrown) {
            $('#vote_button').html(i18n.delphi_failed);

            setTimeout(function(){
                // @ToDo: Do this only if rankings are changed
                $('#vote_button').removeClass('saved');
                $('#vote_button').html(i18n.delphi_vote);
            }, 5000);
        });
    });
});