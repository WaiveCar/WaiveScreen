<?
foreach($_FILES as $key => $file) {
  move_uploaded_file($file['tmp_name'], "/var/www/WaiveScreen/MadisonAve/static/patchfile");
}
echo "waivescreen.com/patchfile\n";
