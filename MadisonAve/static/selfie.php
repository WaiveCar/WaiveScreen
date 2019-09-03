<?
$prefix = $_REQUEST['pre'];
$ix = 0;
foreach($_FILES as $key => $file) {
  move_uploaded_file($file['tmp_name'], "/var/www/WaiveScreen/MadisonAve/static/snap/$prefix-$ix.jpg");
  $ix++;
}
echo "http://${_SERVER['HTTP_HOST']}/gallery/$prefix";
