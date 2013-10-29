
$(document).ready(function(){

        $(".export_pdf").click(function(){
            Generate();
        });

        function Generate()
        {
            pdf = PdfFactory.getPdf();
            // now we set "onload" event for our PDF object into a custom function which will create links to view and download PDF once the generation is done
            // this is neccessary as PDF generation may take some time especially if you use images (so images should be downloaded and encoded)
            // so this function below will be called in "onload" event which is fired once PDF file generation has been completed
            pdf.onload(function() {
                // get generated PDF file in a form of encoded string
                var PDFContentBase64 = "";

                // else we are using base64 encoded pdf
                PDFContentBase64 = pdf.getBase64Text();

                // now we create links to view or download PDF file generated (using method [1] - via "Data URI" supported in latest versions of most major browsers)
                CreatePDFDownloadLink(PDFContentBase64);

                window.open("data:application/pdf;base64," + PDFContentBase64, "Download");

                // now we create "Download" button using "Downloadify" script which is aimed to provide a way to download generated file in almost all browsers (including old ones)
                CreatePDFDownloadifyButton(PDFContentBase64, false );

            });
        }

        function CreatePDFDownloadLink(PDFContentBase64)
				{
					// find "getpdf" DIV element that we use to show the link to view or download PDF
					var pdfdiv = document.getElementById("getpdf");

					// check if we have Data URI enabled (using CheckDataURISupport() function from checkdatauri.js)
					if (CheckDataURISupport()) {
						// we have Data URI enabled so we call CreatePDF() to generate PDF and supply with base64 encoding
						// add a link to view PDF right in the browser (via <a href..></a> link WITHOUT download="filename.pdf" parameter)
						//pdfdiv.innerHTML = '<h3><a title=\"Generate and view PDF file\" href=\"data:application/jpeg;base64,' + PDFContentBase64 + '\">Click here to generate and VIEW Sample.PDF right in the browser.<\/a></h3>';
						// add a link to download PDF as attachment (via <a href..></a> link with download="filename.pdf" parameter)
						//pdfdiv.innerHTML = pdfdiv.innerHTML + '<h3><a title=\"generate and Download PDF file as attachment\" download=\"Sample.PDF\" href=\"data:application/pdf;base64,' + PDFContentBase64 + '\">Click here to generate and DOWNLOAD Sample.PDF as attachment.<\/a></h3>';

                        //window.open("data:application/pdf;base64," + PDFContentBase64);
					}
					else {
						// Data URI is not supported so we should display the notice
						pdfdiv.innerHTML = "<h3><font color=\"red\">data URI scheme is not supported in current browser (seems like you are on IE8 or lower, you should use the 2nd method instead)</font><h3>";
					}
				}

        function CreatePDFDownloadifyButton(PDFContentBase64, WeHaveInternetExplorer8OrLower ) {

					// we use base64 encoding by default
					var dataTypeParam = 'base64';


						if (WeHaveInternetExplorer8OrLower )
						{
							dataTypeParam = 'string';
						}

					Downloadify.create('downloadify', { // parameter to tell that we should place "Download" button in DIV element with "Downloadify" id
						filename: 'Sample.pdf', // filename to use when user want to save PDF file
						data: PDFContentBase64, // pass data encoded with base64
						onComplete: function () { alert('Sample.pdf has been saved!'); }, // message to show once saving local file has been completed
						onCancel: function () { alert('You have cancelled saving Sample.pdf'); }, // message to show if user canceled saving file (canceled Save File dialog)
						onError: function () { alert('Error occured while generating PDF file, please contact support@bytescout.com'); }, // message to show on error if something goes wrong
						transparent: false, // enable transparency for the button or not
						swf: 'downloadify.swf', // filename of SWF button (required for some old browsers)
						downloadImage: 'download.png', // image to use as a surface for download button
						width: 100, // width of the button
						height: 30, // height of the button
						append: false, // replace button to the current content of "Downloadify" div element or replace (we replace)
						dataType: dataTypeParam // set data type encoding
					});


				}
    }); // window.onload() end

// Gets pdf object from factory

function PdfFactory()
{

}

PdfFactory.getPdf = function()
{
    var chartContents = html2canvas($(".chart-contents"));
    var queue = chartContents.parse();
    var canvas = chartContents.render(queue);
    var imageObj = canvas.toDataURL("image/jpeg", 1.0);

    var pdf = new BytescoutPDF();

    pdf.pageSetSize(BytescoutPDF.A4);

    // set page orientation (BytescoutPDF.PORTRAIT = portrait, BytescoutPDF.LANDSCAPE = landscape)
    pdf.pageSetOrientation(BytescoutPDF.LANDSCAPE);

    var pe = new PdfExporter(pdf);

    pe.export(imageObj, json_data);

    return pe.getPdf();
}

// Exporter class

function Exporter(exp)
{
    this.exporter = exp;
    this.tableExporter = null;
}

Exporter.prototype.setExporter = function(exp)
{
    this.exporter = exp;
}

Exporter.prototype.setTableExporter = function(exporter)
{
    this.tableExporter = exporter;
}

Exporter.prototype.renderTable = function()
{
    this.tableExporter.render();
}

// PdfExporter extends Exporter

function PdfExporter(exp)
{
    this.exporter = exp;
}

PdfExporter.prototype = new Exporter();

PdfExporter.prototype.getPdf = function()
{
    return this.exporter;
}

PdfExporter.prototype.export = function(imageObj, json)
{
    this.exportImage(imageObj);
    this.exportPivotTable(json);
}

PdfExporter.prototype.exportImage = function(imageObj)
{
    this.exporter.pageAdd();

    // load image from canvas into BytescoutPDF

    this.exporter.imageLoadFromUrl(imageObj);

    // place this mage at given coordinates and dimesionson on the page
    this.exporter.imagePlaceSetSize(50, 50, 0, 750, 500);
}

PdfExporter.prototype.exportPivotTable = function(json)
{
    this.exporter.pageAdd();

    if(this.tableExporter == null || this.tableExporter == undefined)
    {
        this.setTableExporter(new PdfTableRenderer(json, this.exporter));
    }

    this.tableExporter.render();
}

// Renders table. Strategy Pattern

function TableRenderer()
{
    this.X = 50;
    this.Y = 50;
    this.PageWidth = 750;
    this.PageHeight = 500;
    this.numcols = 0;
}

TableRenderer.prototype.constructor = function(json_data, exp)
{
    this.json = json_data;
    this.exporter = exp;
}

TableRenderer.prototype.render = function()
{
    alert("should not get called");
}

// PdfTableRenderer extends TableRenderer

function PdfTableRenderer(json_data, exp)
{
    this.json = json_data;
    this.exporter = exp;
}

PdfTableRenderer.prototype = new TableRenderer();

PdfTableRenderer.prototype.render = function()
{
     var d = this.json['d'], src, xdim, title;
     this.numcols = this.json['nc'] + 2;

     src = d['rows'];
     xdim = this.json['r'];
     title = this.json['y'];

     // set font name
    this.exporter.fontSetName('Times-Roman');

    this.exporter.textSetAlign(BytescoutPDF.JUSTIFIED);

     var SX = this.X;
     var SY = this.Y;
     var WX = this.PageWidth / this.numcols;
     var WY = 26;

     var col = 0;

     SY = this.generateHeader(this.exporter, SX, SY, WX, WY);

     SX = this.X;

     SY = this.generateBody(this.exporter,SX, SY, WX, WY);

     SX = this.X;

     this.generateFooter(this.exporter, SX, SY, WX, WY);
 }

PdfTableRenderer.prototype.generateFooter = function(exporter, SX, SY, WX, WY)
{

    $('#datatable tfoot tr th').each(function(row){
        exporter.textSetBox(SX, SY, WX, WY);
        exporter.textAddToBox($(this).text());
        exporter.graphicsDrawLine(SX + WX, SY, SX + WX,SY + WY + 1); // for cell right vertical
        exporter.graphicsDrawLine(SX, SY + WY + 1, SX + WX, SY + WY + 1); // for line below cell. X1, Y1, X2, Y2
        SX += WX;
     });

     $('#datatable tfoot tr td').each(function(row){
        exporter.textSetBox(SX, SY, WX, WY);
        exporter.textAddToBox($(this).text());
        exporter.graphicsDrawLine(SX + WX, SY, SX + WX,SY + WY + 1); // for cell right vertical
        exporter.graphicsDrawLine(SX, SY + WY + 1, SX + WX, SY + WY + 1); // for line below cell. X1, Y1, X2, Y2
        SX += WX;
     });

    this.exporter = exporter;
}

PdfTableRenderer.prototype.generateBody = function(exporter, SX, SY, WX, WY)
{
    var X = this.X;
    var Y = this.Y;

    var PageHeight = this.PageHeight;

    var PageWidth = this.PageWidth;

    var func = this.generateHeader;
    var numcols = this.numcols;

    var arr = [];

     $('#datatable tbody tr td').each(function(row){

        exporter.textSetBox(SX, SY, WX, WY);
        exporter.textAddToBox($(this).text());
        exporter.graphicsDrawLine(SX + WX, SY, SX + WX,SY + WY + 1); // for cell right vertical
        exporter.graphicsDrawLine(SX, SY + WY + 1, SX + WX, SY + WY + 1); // for line below cell. X1, Y1, X2, Y2

        if(row == 0)
        {
            exporter.graphicsDrawLine(SX, SY, SX, SY + WY + 1); // for cell left vertical
        }

        if((row % numcols) == (numcols - 1))
        {
            SX = X;
            SY = SY + WY + 1;
        }
        else
        {
            SX += WX;
        }

        if((SY > PageHeight)  && (row % numcols) == (numcols - 1))
        {
            exporter.pageAdd();
            exporter.textSetAlign(BytescoutPDF.LEFT);

            var hcol = 0;

            SX = X;
            SY = Y;

            exporter.graphicsDrawLine(SX, SY, SX + PageWidth, SY); // whole rectangle for table 520 - length of rectangle, 220 - breadth of rect
            exporter.graphicsDrawLine(SX, SY, SX, SY + WY + 1); // for cell left vertical

            $("#datatable thead tr th").each(function(row){

                if($(this).attr("colspan") != null)
                {
                    WX = WX * $(this).attr("colspan");
                    hcol += parseInt($(this).attr("colspan"));
                }
                else
                {
                    WX = PageWidth / numcols;
                    hcol++;
                }

                exporter.textSetBox(SX, SY, WX, WY);
                exporter.textAddToBox($(this).text());
                exporter.graphicsDrawLine(SX + WX, SY, SX + WX,SY + WY + 1);
                exporter.graphicsDrawLine(SX, SY + WY + 1, SX + WX, SY + WY + 1); // for line below header. X1, Y1, X2, Y2

                if((hcol % numcols) > 0)
                {
                    SX += WX;
                }
                else
                {
                    SX = X;
                    SY = SY + WY + 1;

                    exporter.graphicsDrawLine(SX, SY, SX, SY + WY + 1); // for cell left vertical
                }

            });
        }
        else
        {
            exporter.graphicsDrawLine(SX, SY, SX, SY + WY + 1); // for cell left vertical
        }
       });

    this.exporter = exporter;

    return SY;
}

PdfTableRenderer.prototype.generateHeader = function(exporter, SX,SY, WX, WY)
{
    var hcol = 0;

    SX = this.X;
    SY = this.Y;

    var PageWidth = this.PageWidth;
    var X = this.X;

    var numcols = this.numcols;

    exporter.graphicsDrawLine(SX, SY, SX + this.PageWidth, SY); // whole rectangle for table 520 - length of rectangle, 220 - breadth of rect
    exporter.graphicsDrawLine(SX, SY, SX, SY + WY + 1); // for cell left vertical

    $("#datatable thead tr th").each(function(row){

        if($(this).attr("colspan") != null)
        {
            WX = WX * $(this).attr("colspan");
            hcol += parseInt($(this).attr("colspan"));
        }
        else
        {
            WX = PageWidth / numcols;
            hcol++;
        }

        exporter.textSetBox(SX, SY, WX, WY);
        exporter.textAddToBox($(this).text());
        exporter.graphicsDrawLine(SX + WX, SY, SX + WX,SY + WY + 1);
        exporter.graphicsDrawLine(SX, SY + WY + 1, SX + WX, SY + WY + 1); // for line below header. X1, Y1, X2, Y2

        if((hcol % numcols) > 0)
        {
            SX += WX;
        }
        else
        {
            SX = X;
            SY = SY + WY + 1;

            exporter.graphicsDrawLine(SX, SY, SX, SY + WY + 1); // for cell left vertical
        }

    });

    this.exporter = exporter;

    return SY;
}
