/*
    debate_blackboard.js - Javascript containing the engine for the debate
                           system.
                           
    License: GPLv3
    Copyright: 2011 Cidadania S. Coop. Galega
    Author: Oscar Carballal Prego <info@oscarcp.com>
*/



/*
    NOTE FUNCTIONS
*/

function showDelete() {
    /*
        showDelete() - Show/hide the delete button when hovering a note.
    */
    $('.note').hover(
        function () {
            var getID = $(this).attr('id');
            $('#' + getID + ' a#deletenote').toggle();
        }
    );
}

function createNote() {
    /*
        createNote() - Appends a new note within the sortable dispatcher.
    */
    var noteLength = $('.note').length;
    var debateID = $('table').attr('id');
    
    $('#sortable-dispatcher').append("<div id='" + debateID + "-note" + (noteLength+1) + "' class='note'><a href='javascript:getClickedNote()' id='deletenote' class='hidden'></a><textarea>Write here</textarea></div>").hide().show("slow");
    
    showDelete();
    saveOnChangeNote();
    var noteID = debateID + "-note" + (noteLength+1);
    
    $.post("../create_note/", {
        noteid: noteID,
        parent: $('#' + noteID).parent('td').attr('id'),
        title: $('#' + noteID + ' textarea').val(),
        message: "Blablbla",
    });
}

function updateNote(noteObj) {
    /*
        saveNote(noteObj) - Saves the notes making an AJAX call to django. This
        function is meant to be used with a Sortable 'stop' event.
        Arguments: noteObj, note object.
    */
    var noteID = noteObj.attr('id');
    
    $.post("../update_note/", {
        noteid: noteID,
        parent: $('#' + noteID).parent('td').attr('id'),
        title: $('#' + noteID + ' textarea').val(),
        message: "Blablbla",
    });
}

function saveOnChangeNote() {
    /*
        saveOnChangeNote() - Call the updateNote() function every time a note
        is modified but not moved. This works for changes in textareas, inputs
        and selects.
    */
    $('.note').change( function() {
        updateNote($(this));
    });
}

function deleteNote(noteObj) {
    /*
        deleteNote() - Delete a note making an AJAX call. This function is called
        through getClickedNote(). We locate the note ID, and post it to django,
        after that we remove the note from the board.
    */
    var noteID = noteObj.attr('id');
    
    $.post('../delete_note/', {
        noteid: noteID,
    });
    
    $('#' + noteID).remove();
}

function getClickedNote() {
    $('.note a').click(function (){
        var noteObj = $(this).parent();
        deleteNote(noteObj);
    });
}

/*
    TABLE FUNCTIONS
*/

function makeSortable() {
    /*
        makeSortable() - Makes every element with id starting by 'sortable'
        sortable through the connectedSortable class lists. It uses jQuery
        Sortable. This function has to be called whenever a new element is on
        the page (note, table column or row) to make the new elements sortable.
    */
    
    // Get all the div elements starting by sortable
    $('#[id^=sortable]').sortable({
        connectWith: ".connectedSortable",
    	cursor: "move",
    	placeholder: "note-alpha",
    	start: function(e,ui) { 
            $(ui.placeholder).hide("slow"); // Remove popping
        },
        change: function(e,ui) {
            $(ui.placeholder).hide().show("normal");
        },
        stop: function(e,ui) {
            updateNote(ui.item);
        }
    }).disableSelection();
}

function addTableRow() {
    /*
        addTableRow() - This function adds new rows to an existent table numbering
        the sortables according to the debate number and current ULs.
    */

    var tableID = $('table').attr('id');
    
    $('#' + tableID).each(function(){
        var $table = $(this);
        // Number of td's in the last table row
        var n = $("tr:last td", this).length;
        var tds = '<tr>';
        var inputs = $('#' + tableID + ' input').length;
        for(var i = 0; i < n; i++){
            var tdlength = $('#' + tableID + ' td').length;
            if (i == 0) {
                // The first TD must be empty, only with a form for the title.
                tds += "<td id='debate-hcriteria' class='criteria-title'><div id='debate-ttitle'><input class='small' id='debate1-criteria" + (inputs+1) + "' type='text' value='Test criteria'></div></td>";
                // Remove the first TD from the tds count.
                n -= 1;
            }
            tds += "<td id='sortable" + (tdlength+1) + "-" + tableID + "' class='connectedSortable'></td>";
        }
        tds += '</tr>';
        if($('tbody', this).length > 0){
            $('tbody', this).append(tds).children(':last').hide().fadeIn("slow");
        } else {
            $(this).append(tds).children(':last').hide().slideDown("slow");
        }
        makeSortable();
    });
}

function removeTableRow() {
    /*
        removeTableRow() - Remove the last row in the table. It removes
        also the TDs and the notes.
    */
    var tableID = $('table').attr('id');
    var trs = $('#' + tableID + ' tbody tr').length;
    
    if (trs > 1) {
        $('#' + tableID + ' tr:last').fadeOut("fast", function() {
            $(this).remove();
        });
    } else {
        $('#jsnotify').notify("create", {
            title: "Can't delete row",
            text: "There must be at least one row in the table.",
            icon: "alert.png"
        });
    }
}
        
function addTableColumn() {
    /*
        addTableColumn() - Create a new column ny creating a new sortable TD in
        all the rows.
    */
    var tableID = $('table').attr('id');
    var inputs = $('#' + tableID + ' input').length;
    var tdlength = $('#' + tableID + ' td').length;
    $('#' + tableID + ' tr:first').append("<th id='debate-vcriteria'><input id='" + tableID + "-criteria" + (inputs+1) + "' type='text' class='small' value='Test criteria'></th>");
    $('#' + tableID + ' tbody tr').append("<td id='sortable" + (tdlength+1) + "-" + tableID + "' class='connectedSortable'></td>").fadeIn("slow");
    makeSortable();
}

function removeTableColumn() {
    /*
        removeTableColumn() - Deletes the last column (all the last TDs).
    */
    var tableID = $('table').attr('id');
    var columns = $('#' + tableID+ ' tr:last td').length;
    if (columns > 2) {
        $('#' + tableID + ' th:last-child, #' + tableID + ' td:last-child').fadeOut("fast", function() {
            $(this).remove();
        });
    } else {
        $('#jsnotify').notify("create", {
            title: "Can't delete column",
            text: "There must be at least one column in the table.",
            icon: "alert.png"
        });
    }
}

function saveTable() {
    /*
        saveTable() - Saves the table data. Instead of using a standard form,
        we submite the data trough ajax post, and treat it as a form in the
        django view.
    */
    $('#ajaxform').ajaxForm();
    
    
}

/*******************
    MAIN LOOP
********************/

$(document).ready(function() {
    // Activate javascript notifications.
    $('#jsnotify').notify();
    // Activate sortables
    makeSortable();
    // Run some functions on every debate, just in case
    showDelete();
    saveOnChangeNote();    
});

