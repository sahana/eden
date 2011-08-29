/*
    debate_blackboard.js - Javascript containing the engine for the debate
                           system.
                           
    License: GPLv3
    Copyright: 2011 Cidadania S. Coop. Galega
    Author: Oscar Carballal Prego <info@oscarcp.com>
*/


/*
    DEBATE FUNCTIONS
*/
function createNewDebate(space) {
    /*
        createNewDebate(space) - Creates a new debate on the current space. The debate
        will always fit to the maximum screen size.
    */
    
    
    
}

function makeSortable() {
    /*
        makeSortable() - Makes every note object in the page sortable through
        the connectedSortable class lists. It uses jQuery Sortable. This function
        has to be called whenever a new element is on the page (note, table
        column or row) to make the new elements sortable.
    */
    
    // Get all the UL elements starting by sortable
    $("ul[id^=sortable]").sortable({
        connectWith: ".connectedSortable",
    	cursor: "move",
    	placeholder: "note-alpha",
    	start: function (e,ui){ 
            $(ui.placeholder).hide("slow"); // Remove popping
        },
        change: function (e,ui){
            $(ui.placeholder).hide().show("normal");
        }
    }).disableSelection();
}

function addTableRow(jQtable){
    /*
        addTableRow() - This function adds new rows to an existent table numbering
        the sortables according to the debate number and current ULs.
    */

    jQtable.each(function(){
        var $table = $(this);
        // Number of td's in the last table row
        var n = $("tr:last td", this).length;
        var tds = '<tr>';
        var uls = $('#debate ul').length;
        var inputs = $('#debate input').length;
        for(var i = 0; i < n; i++){
            if (i == 0) {
                // The first TD must be empty, only with a form for the title.
                tds += "<td><input id='debate1-criteria" + (inputs+1) + "' value='Test criteria'></td>";
                // Remove the first TD from the tds count.
                n -= 1;
            }
            tds += "<td><ul id='sortable" + (uls+1) + "' class='connectedSortable'></ul></td>";
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
        removeTableRow() - Remove the last table row in the table. It removes
        also the TDs and the notes.
    */
    var trs = $('#debate tbody tr').length;
    if (trs > 1) {
        $('#debate tr:last').fadeOut("slow").remove();
    } else {
        $('#jsnotify').notify();
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
    var uls = $('#debate ul').length;
    var inputs = $('#debate input').length;
    $('#debate tr:first ').append("<th id='foo'><input id='debate1-criteria" + (inputs+1) + "' value='Test criteria'></td></th>");    
    $("#debate tbody tr").append("<td><ul id='sortable" + (uls+1) + "' class='connectedSortable'></ul></td>").fadeIn("slow");
    makeSortable();
}

function removeTableColumn() {
    /*
        removeTableColumn() - Deletes the last column (all the last TDs).
    */
    $("#debate th:last-child, #debate td:last-child").remove();
/*    $('#debate thead tr th:last').remove();
    $('#debate tbody tr').each(function() {
          $(this).children('td, th').slice(-1).remove();
/*        $(this).remove('td:last');
    });*/
}

function editDebate() {}

function saveDebate() {}
    /* 
        function deleteDebate() {} - This function is not available yet. The task of
        deleting debates will probably be for the site admin or space admin.
    */


/*
    PHASE FUNCTIONS
*/
function createNewPhase() {}

function newScaleItem() {
    /*
        When creating a new scale item, we populate the dictionary.
    */
    
    var scale_x = ''
    var scale_y = ''
}

function deleteScaleItem() {}
function deletePhase() {}

/*
    NOTE FUNCTIONS
*/
function createNote() {
    $('#sortable-dispatcher').append("<li class='note'><textarea>Write here</textarea></li>").hide().show("slow");
}
function saveNote() {}
function deleteNote() {}


/*******************
    MAIN LOOP
********************/

$(document).ready(function() {
    makeSortable();
});

