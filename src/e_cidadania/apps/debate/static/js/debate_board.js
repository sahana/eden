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
    var lastnote = parseInt($('#last-note').text());
    
    $('#sortable-dispatcher').append("<div id='" + (lastnote+1) + "' class='note'><a href='javascript:getClickedNote()' id='deletenote' class='hidden'></a><textarea id='text" + (lastnote+1) + "'>Write here</textarea></div>").hide().show("slow");
    lastnote = lastnote + 1;
    
    showDelete();
    saveOnChangeNote();
    var noteID = debateID + "-note" + (noteLength+1);

    $.post("../create_note/", {
        debateid: $('#debate-number').text(),
        title: "Write here",
        message: "Write here your message"
    });
}

function updateNote(noteObj) {
    /*
        saveNote(noteObj) - Saves the notes making an AJAX call to django. This
        function is meant to be used with a Sortable 'stop' event.
        Arguments: noteObj, note object.
    */
    var noteID = noteObj.attr('id');
    var position = noteObj.parent().attr('headers').split(" ");

    $.post("../update_note/", {
        noteid: noteID,
        column: position[0],
        row: position[1],
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
    var answer = confirm("Are you sure?");
    
    if (answer) {
        $.post('../delete_note/', {
            noteid: noteID
        });
    
        $('#' + noteID).remove();
    } else {
        alert("Gracias!");
    }
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

var tdlength = 0;

function addTableColumn() {
    /*
        addTableColumn() - Create a new column ny creating a new sortable TD in
        all the rows.
    */
    var tableID = $('table').attr('id');
    var inputs = $('#' + tableID + ' input').length;
    var tdlength = $('#' + tableID + ' td').length;
    var criteriacount = $('#' + tableID + ' th[id^=debate-vcriteria]').length;
    
    $('#' + tableID + ' tr:first').append("<th id='debate-vcriteria" + (criteriacount+1) + "' class='criteria-vtitle'><input id='" + tableID + "-criteria" + (inputs+1) + "' type='text' class='small' value='Test criteria'></th>");
    $('#' + tableID + ' tbody tr').each(function(){
        //var tdlength = $('#' + tableID + ' td').length;
        $(this).append("<td id='sortable" + (tdlength) + "-" + tableID + "' class='connectedSortable'></td>").fadeIn("slow");
        tdlength += 1;
    });
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
    $('#ajaxform').submit( function() {
        var tableID = $('table').attr('id');

        var xvalues = [];
        var xfields = $('th.criteria-vtitle :input');
        $.each(xfields, function(i, field){
            xvalues.push(field.value);
        });
        $('#id_columns').val(xvalues);
        
        var sortable = [];
        var rows = $('#' + tableID + ' tbody tr');
        alert('Tengo ' + rows.length + ' filas')
        $.each(rows, function(i, field) {
            alert('Deberia manipular un row y manipulo: '+ this);
            var rowID = this.attr('id');
            $(rowID + ' td').each(function() {
                alert('Deberia manipular un TD y pillo: ' + this);
                sortable.push($(this).attr('id'));
            })
            alert('Estos son los sortables: ' + sortable[0]);
            $(this).val(sortable);
            sortable.length = 0;
        })
              
        return true;
  });
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
    //showDelete();
    saveOnChangeNote();    
    saveTable();
});

