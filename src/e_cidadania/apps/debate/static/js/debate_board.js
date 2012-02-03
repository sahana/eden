/*
    debate_blackboard.js - Javascript containing the engine for the debate
                           system.
                           
    License: GPLv3
    Copyright: 2011 Cidadania S. Coop. Galega
    Author: Oscar Carballal Prego <info@oscarcp.com>
*/

// We put here the string for translation. This is meant to be translated by
// django jsi18n
var newTitle = gettext('Write here your title');
var newMessage = gettext('Write here your message');
var editString = gettext('Edit');
var errorMsg = gettext('There has been an error.');
var errorCreate = gettext("Couldn't create note.");
var errorGetNote = gettext("Couldn't get note data.");
var errorSave = gettext("Couldn't save note.");
var errorSavePos = gettext("Couldn't save note position.");
var errorDelete = gettext("Couldn't delete note.");
var confirmDelete = gettext('Are you sure?');

/*
    NOTE FUNCTIONS
*/

function showControls() {
    /*
     showControls() - Hides the edit and delete controls from the notes. If the
     users hovers over a note created by himself, the note shows the controls.
     */
    $(".mine").hover(function(){
            $(this).find(".deletenote").show();
            $(this).find("#edit-note").show();
            $(this).find("#view-note").show();
        },
        function() {
            $(this).find(".deletenote").hide();
            $(this).find("#edit-note").hide();
            $(this).find("#view-note").hide();
        }
    );
}

function createNote() {
    /*
        createNote() - Creates a new note related with the debate. Frist the
        function creates the note in the server and after that we create a "fake"
        note in the debate board with the data returned by the view. If for some
        reason the user creates the note and leaves it before moving or editing the
        note is positioned in position [1,1].
    */

    var request = $.ajax({
        type:"POST",
        url:"../create_note/",
        data:{
            debateid:$('#debate-number').text(),
            title: newTitle,
            message: newMessage,
            column:1,
            row:1
        }
    });

    request.done(function (note) {
        var newNote = $("#sortable-dispatcher").append("<div id='" + note.id + "' style='display:hidden;' class='note mine'>" +
            "<div class='handler'><div class='deletenote hidden'>" + "<a href='#' onclick='deleteNote(this)'" +
            " id='deletenote'>x</a></div></div><p class='note-text'>" + note.title + "</p>" +
            "<span id='edit-note' class='label hidden'><a href='#' onclick='editNote(this)'" +
            " data-controls-modal='edit-current-note' data-backdrop='true'" +
            " data-keyboard='true'>" + editString + "</a></span>" +
            "</div>");
        newNote.show("slow");
        showControls();
    });

    request.fail(function (jqXHR, textStatus) {
        $('#jsnotify').notify("create", {
            title: errorCreate,
            text: errorMsg + textStatus,
            icon:"alert.png"
        });
    });

    // Activate control show/hide for the new note
}

function viewNote(obj) {
    /*
        editNote(obj) - This function detects the note the user clicked and raises
        a modal dialog, after that it checks the note in the server and returns
        it's data, prepopulating the fields.
    */
    var noteID = $(obj).parent().parent().attr('id');

    var request = $.ajax({
        url: "../update_note/",
        data: { noteid: noteID }
    });

    request.done(function(note) {
        $('h3#view-note-title').text(note.title);
        $('p#view-note-desc').text(note.message);
    });

    request.fail(function (jqXHR, textStatus) {
        $('#edit-current-note').modal('hide');
        $('#jsnotify').notify("create", {
            title: errorGetNote,
            text: errorMsg + textStatus,
            icon:"alert.png"
        });
    });
}

function editNote(obj) {
    /*
        editNote(obj) - This function detects the note the user clicked and raises
        a modal dialog, after that it checks the note in the server and returns
        it's data, prepopulating the fields.
    */
    var noteID = $(obj).parent().parent().attr('id');

    var request = $.ajax({
        url: "../update_note/",
        data: { noteid: noteID }
    });

    request.done(function(note) {

        $("input[name='notename']").val(note.title);
        $("textarea#id_note_message").val(note.message);
        $("#last-edited-note").text(noteID);
    });

    request.fail(function (jqXHR, textStatus) {
        $('#edit-current-note').modal('hide');
        $('#jsnotify').notify("create", {
            title: errorGetNote,
            text: errorMsg + textStatus,
            icon:"alert.png"
        });
    });
}

function saveNote() {
    /*
        saveNote() - Saves the current edited note, only the title and message
        field, since the other fields are managed through makeSortable() or by
        django itself.
    */
    var noteID = $('#last-edited-note').text();

    var request = $.ajax({
        type: "POST",
        url: "../update_note/",
        data: {
            noteid: noteID,
            title: $("input[name='notename']").val(),
            message: $("textarea#id_note_message").val()
        }
    });

    request.done(function(msg) {
        $('#edit-current-note').modal('hide');
        var newTitle = $("input[name='notename']").val();
        $("div#" + noteID + " > p").text(newTitle);
    });

    request.fail(function(jqXHR, textStatus) {
        $('#edit-current-note').modal('hide');
        $('#jsnotify').notify("create", {
            title: errorSave,
            text: errorMsg + textStatus,
            icon:"alert.png"
        });
    })
}

function deleteNote(obj) {
    /*
        deleteNote() - Delete a note making an AJAX call. This function is called
        through getClickedNote(). We locate the note ID, and post it to django,
        after that we hide the note from the board and when it's hidden we remove it
        from the DOM.
    */
    var noteID = $(obj).parents('.note').attr('id');
    var answer = confirm(confirmDelete);

    if (answer) {
        var request = $.ajax({
            type: "POST",
            url: "../delete_note/",
            data: { noteid: noteID }
        });

        request.done(function(msg) {
           $('#' + noteID).hide("normal", function() {
               $('#' + noteID).remove();
           });
        });

        request.fail(function(jqXHR, textStatus) {
            $('#jsnotify').notify("create", {
                title: errorDelete,
                text: errorMsg + textStatus,
                icon:"alert.png"
            });
        });
    }
}

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
            var noteObj = ui.item;
            var noteID = noteObj.attr('id');
            var position = noteObj.parent().attr('headers').split("-");

            $.ajax({
                type: "POST",
                url: "../update_position/",
                data: {
                    noteid: noteID,
                    column: position[0],
                    row: position[1]
                }
            }).fail(function(jqXHR, textStatus) {
                $('#jsnotify').notify("create", {
                    title: errorSavePos,
                    text: errorMsg + textStatus,
                    icon:"alert.png"
                });
            });
        }
    }).disableSelection();
}

/* DEBATE CREATION */

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
    // Show controls for some notes
    showControls();
});

