<?
$start = @$_REQUEST["start"];
$limit = @$_REQUEST["limit"];

$start = $start ? $start : 0;
$limit = $limit ? $limit : 5;

$data = array(
	array("company"=>'General Motors Corporation',                  "hide2"=>false,"action1"=>"icon-disk","action2"=>"icon-cross","action3"=>"icon-key","qtip1"=>"Tooltip 1","qtip2"=>"Tooltip 2","qtip3"=>"Tooltip 3", "lastChange"=>'9/1 12:00am', "industry"=>'Automotive'),
	array("company"=>'Hewlett-Packard Co.',                         "hide2"=>false,"action1"=>"icon-disk","action2"=>"icon-cross","action3"=>"icon-key","qtip1"=>"Tooltip 1","qtip2"=>"Tooltip 2","qtip3"=>"Tooltip 3", "lastChange"=>'9/1 12:00am', "industry"=>'Computer'),
	array("company"=>'Intel Corporation',                           "hide2"=>false,"action1"=>"icon-disk","action2"=>"icon-cross","action3"=>"icon-key","qtip1"=>"Tooltip 1","qtip2"=>"Tooltip 2","qtip3"=>"Tooltip 3", "lastChange"=>'9/1 12:00am', "industry"=>'Computer'),
	array("company"=>'International Business Machines',             "hide2"=>false,"action1"=>"icon-disk","action2"=>"icon-cross","action3"=>"icon-key","qtip1"=>"Tooltip 1","qtip2"=>"Tooltip 2","qtip3"=>"Tooltip 3", "lastChange"=>'9/1 12:00am', "industry"=>'Computer'),
	array("company"=>'Microsoft Corporation',                       "hide2"=>false,"action1"=>"icon-disk","action2"=>"icon-cross","action3"=>"icon-key","qtip1"=>"Tooltip 1","qtip2"=>"Tooltip 2","qtip3"=>"Tooltip 3", "lastChange"=>'9/1 12:00am', "industry"=>'Computer'),
	array("company"=>'United Technologies Corporation',             "hide2"=>false,"action1"=>"icon-disk","action2"=>"icon-cross","action3"=>"icon-key","qtip1"=>"Tooltip 1","qtip2"=>"Tooltip 2","qtip3"=>"Tooltip 3", "lastChange"=>'9/1 12:00am', "industry"=>'Computer'),
	array("company"=>'American Express Company',                    "hide2"=>false,"action1"=>"icon-save-table","action2"=>"icon-add-col","action3"=>"icon-key","qtip1"=>"Tooltip 1","qtip2"=>"Tooltip 2","qtip3"=>"Tooltip 3", "lastChange"=>'9/1 10:00am', "industry"=>'Finance', "desc"=>"An example of description"),
	array("company"=>'Citigroup, Inc.',                             "hide2"=>false,"action1"=>"icon-disk","action2"=>"icon-cross","action3"=>"icon-key","qtip1"=>"Tooltip 1","qtip2"=>"Tooltip 2","qtip3"=>"Tooltip 3", "lastChange"=>'9/1 12:00am', "industry"=>'Finance', "desc"=>"A nice place for summary"),
	array("company"=>'JP Morgan & Chase & Co',                      "hide2"=>false,"action1"=>"icon-disk","action2"=>"icon-cross","action3"=>"icon-key","qtip1"=>"Tooltip 1","qtip2"=>"Tooltip 2","qtip3"=>"Tooltip 3", "lastChange"=>'9/1 12:00am', "industry"=>'Finance'),
	array("company"=>'McDonald\'s Corporation',                     "hide2"=>false,"action1"=>"icon-disk","action2"=>"icon-cross","action3"=>"icon-key","qtip1"=>"Tooltip 1","qtip2"=>"Tooltip 2","qtip3"=>"Tooltip 3", "lastChange"=>'9/1 12:00am', "industry"=>'Food'),
	array("company"=>'The Coca-Cola Company',                       "hide2"=>false,"action1"=>"icon-disk","action2"=>"icon-cross","action3"=>"icon-key","qtip1"=>"Tooltip 1","qtip2"=>"Tooltip 2","qtip3"=>"Tooltip 3", "lastChange"=>'9/1 12:00am', "industry"=>'Food'),
	array("company"=>'3m Co',                                       "hide2"=>true,"action1"=>"icon-open","action2"=>"icon-cross","action3"=>"icon-key","qtip1"=>"Click to Open","qtip2"=>"Click to Delete","qtip3"=>"Click to Lock", "lastChange"=>'8/1 12:00am', "industry"=>'Manufacturing',"desc"=>"A description"),
	array("company"=>'Alcoa Inc',                                   "hide2"=>false,"action1"=>"icon-undo","action2"=>"icon-rename","action3"=>"icon-key","qtip1"=>"Click to Undo","qtip2"=>"Click to Rename","qtip3"=>"Tooltip 3", "lastChange"=>'9/1 12:00am', "industry"=>'Manufacturing',"desc"=>"Summary"),
	array("company"=>'Altria Group Inc',                            "hide2"=>true,"action1"=>"icon-coins","action2"=>"icon-clock","action3"=>"icon-key","qtip1"=>"Click to Save","qtip2"=>"Tooltip 2","qtip3"=>"Tooltip 3", "lastChange"=>'10/1 12:00am', "industry"=>'Manufacturing', "desc"=>"A note can come here"),
	array("company"=>'Boeing Co.',                                  "hide2"=>false,"action1"=>"icon-disk","action2"=>"icon-plus","action3"=>"icon-key","qtip1"=>"Tooltip 1","qtip2"=>"With callback","qtip3"=>"Tooltip 3", "lastChange"=>'9/1 12:00am', "industry"=>'Manufacturing'),
	array("company"=>'E.I. du Pont de Nemours and Company',         "hide2"=>false,"action1"=>"icon-disk","action2"=>"icon-cross","action3"=>"icon-key","qtip1"=>"Tooltip 1","qtip2"=>"Tooltip 2","qtip3"=>"Tooltip 3", "lastChange"=>'9/1 12:00am', "industry"=>'Manufacturing'),
	array("company"=>'Exxon Mobil Corp',                            "hide2"=>false,"action1"=>"icon-disk","action2"=>"icon-cross","action3"=>"icon-key","qtip1"=>"Tooltip 1","qtip2"=>"Tooltip 2","qtip3"=>"Tooltip 3", "lastChange"=>'9/1 12:00am', "industry"=>'Manufacturing'),
	array("company"=>'General Electric Company',                    "hide2"=>false,"action1"=>"icon-disk","action2"=>"icon-cross","action3"=>"icon-key","qtip1"=>"Tooltip 1","qtip2"=>"Tooltip 2","qtip3"=>"Tooltip 3", "lastChange"=>'9/1 12:00am', "industry"=>'Manufacturing'),
	array("company"=>'Honeywell Intl Inc',                          "hide2"=>false,"action1"=>"icon-disk","action2"=>"icon-cross","action3"=>"icon-key","qtip1"=>"Tooltip 1","qtip2"=>"Tooltip 2","qtip3"=>"Tooltip 3", "lastChange"=>'9/1 12:00am', "industry"=>'Manufacturing'),
	array("company"=>'The Procter & Gamble Company',                "hide2"=>false,"action1"=>"icon-disk","action2"=>"icon-cross","action3"=>"icon-key","qtip1"=>"Tooltip 1","qtip2"=>"Tooltip 2","qtip3"=>"Tooltip 3", "lastChange"=>'9/1 12:00am', "industry"=>'Manufacturing'),
	array("company"=>'Johnson & Johnson',                           "hide2"=>false,"action1"=>"icon-disk","action2"=>"icon-cross","action3"=>"icon-key","qtip1"=>"Tooltip 1","qtip2"=>"Tooltip 2","qtip3"=>"Tooltip 3", "lastChange"=>'9/1 12:00am', "industry"=>'Medical'),
	array("company"=>'Merck & Co., Inc.',                           "hide2"=>false,"action1"=>"icon-disk","action2"=>"icon-cross","action3"=>"icon-key","qtip1"=>"Tooltip 1","qtip2"=>"Tooltip 2","qtip3"=>"Tooltip 3", "lastChange"=>'9/1 12:00am', "industry"=>'Medical'),
	array("company"=>'Pfizer Inc',                                  "hide2"=>false,"action1"=>"icon-disk","action2"=>"icon-cross","action3"=>"icon-key","qtip1"=>"Tooltip 1","qtip2"=>"Tooltip 2","qtip3"=>"Tooltip 3", "lastChange"=>'9/1 12:00am', "industry"=>'Medical'),
	array("company"=>'The Home Depot, Inc.',                        "hide2"=>false,"action1"=>"icon-disk","action2"=>"icon-cross","action3"=>"icon-key","qtip1"=>"Tooltip 1","qtip2"=>"Tooltip 2","qtip3"=>"Tooltip 3", "lastChange"=>'9/1 12:00am', "industry"=>'Retail'),
	array("company"=>'Wal-Mart Stores, Inc.',                       "hide2"=>false,"action1"=>"icon-disk","action2"=>"icon-cross","action3"=>"icon-key","qtip1"=>"Tooltip 1","qtip2"=>"Tooltip 2","qtip3"=>"Tooltip 3", "lastChange"=>'9/1 12:00am', "industry"=>'Retail'),
	array("company"=>'AT&T Inc.',                                   "hide2"=>false,"action1"=>"icon-disk","action2"=>"icon-cross","action3"=>"icon-key","qtip1"=>"Tooltip 1","qtip2"=>"Tooltip 2","qtip3"=>"Tooltip 3", "lastChange"=>'9/1 12:00am', "industry"=>'Services'),
	array("company"=>'Caterpillar Inc.',                            "hide2"=>false,"action1"=>"icon-disk","action2"=>"icon-cross","action3"=>"icon-key","qtip1"=>"Tooltip 1","qtip2"=>"Tooltip 2","qtip3"=>"Tooltip 3", "lastChange"=>'9/1 12:00am', "industry"=>'Services'),
	array("company"=>'Verizon Communications',                      "hide2"=>false,"action1"=>"icon-disk","action2"=>"icon-cross","action3"=>"icon-key","qtip1"=>"Tooltip 1","qtip2"=>"Tooltip 2","qtip3"=>"Tooltip 3", "lastChange"=>'9/1 12:00am', "industry"=>'Services'),
	array("company"=>'Walt Disney Company (The) (Holding Company)', "hide2"=>false,"action1"=>"icon-disk","action2"=>"icon-cross","action3"=>"icon-key","qtip1"=>"Tooltip 1","qtip2"=>"Tooltip 2","qtip3"=>"Tooltip 3", "lastChange"=>'9/1 12:00am', "industry"=>'Services'),
	array("company"=>'American International Group, Inc.',          "hide2"=>false,"action1"=>"icon-disk","action2"=>"icon-cross","action3"=>"icon-del-col","qtip1"=>"Tooltip 1","qtip2"=>"Tooltip 2","qtip3"=>"Tooltip 3", "lastChange"=>'9/1 11:00am', "industry"=>'Services')
);

$a = array();
for($i = $start; $i < $start + $limit; $i++) {
	$a[] = $data[$i];
}
$o = array(
	 "success"=>true
	,"totalCount"=>sizeof($data)
	,"rows"=>$a
);

echo json_encode($o);

// eof
?>
