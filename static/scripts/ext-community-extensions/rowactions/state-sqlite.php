<?
// vim: ts=4:sw=4:nu:fdc=4

// get posted values
$cmd = isset($_POST["cmd"]) ? $_POST["cmd"] : false;
$clientArgs->id = isset($_POST["id"]) ? $_POST["id"] : 1;
$clientArgs->user = isset($_POST["user"]) ? $_POST["user"] : "jozo";
$clientArgs->session = isset($_POST["session"]) ? $_POST["session"] : "session";
$clientArgs->data = isset($_POST["data"]) ? json_decode($_POST["data"]) : array();

// get variables and connection to sqlite
$stateFile = "state.sqlite";
$DSN="sqlite:" . realpath(".") . "/$stateFile";
$odb = new PDO("$DSN");
$odb->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

createTable($odb);

if(!$cmd) {
	echo '{"success":false,"error":"No command"}';
	exit;
}

// execute command
$cmd($odb, $clientArgs);
exit;

// {{{
/**
  * readState: reads state
  *
  * @author    Ing. Jozef Sakáloš <jsakalos@aariadne.com>
  * @date      24. March 2008
  * @return    void
  * @param     PDO $odb
  * @param     object $clientArgs
  */
function readState($odb, $clientArgs) {
	$sql = 
		 "select name,value from state where "
		."id={$clientArgs->id} and user='{$clientArgs->user}' and session='{$clientArgs->session}'"
	;
	try {
		$ostmt = $odb->query($sql);
		$data = $ostmt->fetchAll(PDO::FETCH_OBJ);
	}
	catch(PDOException $e) {
		echo "{\"success\":false,\"error\":\"$e\"}";
		exit;
	}

	$o = array(
		 "success"=>true
		,"data"=>json_encode($data)
	);
	echo json_encode($o);
} // eo function readState
// }}}
// {{{
/**
  * saveState: saves state
  *
  * @author    Ing. Jozef Sakáloš <jsakalos@aariadne.com>
  * @date      24. March 2008
  * @return    void
  * @param     PDO $odb
  * @param     object $clientArgs
  */
function saveState($odb, $clientArgs) {
	foreach($clientArgs->data as $row) {
		$sql = 
			 "replace into state (id,user,session,name,value) values"
			." ({$clientArgs->id},'{$clientArgs->user}','{$clientArgs->session}','{$row->name}','{$row->value}')"
		;
		try {
			$odb->exec($sql);
		}
		catch(PDOException $e) {
			echo "{\"success\":false,\"error\":\"$e\"}";
			exit;
		}
	}
	echo '{"success":true}';
} // eo function saveState
// }}}
// {{{
/**
  * createTable: create state table if it doesn't exist
  *
  * @author    Ing. Jozef Sakáloš <jsakalos@aariadne.com>
  * @date      24. March 2008
  * @param     PDO $odb
  * @return    void
  */
function createTable($odb) {
	// check if table exists
	$ostmt = $odb->query("select name from sqlite_master where type='table' and name='state'");
	$table = $ostmt->fetchAll(PDO::FETCH_NUM);
	if(!sizeof($table)) {
		// create table
		$sql = 
			 "create table state"
			."(id integer"
			.",user varchar(40)"
			.",session varchar(80)"
			.",name varchar(80)"
			.",value text"
			.")"
		;
		$odb->exec($sql);

		// create unique index
		$sql = "create unique index idx on state(id,user,session,name)";
		$odb->exec($sql);
	} 
} // eo function createTable
// }}}

// eof
?> 
