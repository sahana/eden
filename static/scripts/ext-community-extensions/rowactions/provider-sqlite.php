<?
// vim: ts=4:sw=4:nu:fdc=4

$user = isset($_COOKIE["user"]) ? $_COOKIE["user"] : (string) rand();
setcookie("user", $user, time() + 365 * 24 * 3600);

// get posted values
$clientArgs->id = isset($_POST["id"]) ? $_POST["id"] : 1;
$clientArgs->user = isset($_POST["user"]) ? $_POST["user"] : $user;
$clientArgs->session = isset($_POST["session"]) ? $_POST["session"] : "session";

// get variables and connection to sqlite
$stateFile = "state.sqlite";
$DSN="sqlite:" . realpath(".") . "/$stateFile";
$odb = new PDO("$DSN");

$sql = 
	 "select name,value from state where "
	."id={$clientArgs->id} and user='{$clientArgs->user}' and session='{$clientArgs->session}'"
;
$ostmt = $odb->query($sql);
$state = $ostmt->fetchAll(PDO::FETCH_OBJ);
$state = json_encode($state);

?>
<script type="text/javascript">
Ext.state.Manager.setProvider(new Ext.ux.state.HttpProvider({
	 url:'state-sqlite.php?#state'
	,user:'<?=$clientArgs->user?>'
	,session:'<?=$clientArgs->session?>'
	,id:'<?=$clientArgs->id?>'
	,readBaseParams:{cmd:'readState'}
	,saveBaseParams:{cmd:'saveState'}
	,autoRead:false
//	,logFailure:true
//	,logSuccess:true
}));
Ext.state.Manager.getProvider().initState(<?=$state;?>);
</script>
<?
// eof
?>
