<?
$id = $_GET['id'];
foreach(glob("snap/$id-*jpg") as $path) {
  echo "<img src=$path>";
}
