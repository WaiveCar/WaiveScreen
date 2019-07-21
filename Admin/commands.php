<?
include('../MadisonAve/lib/lib.php');
include('../AdDaemon/lib/lib.php');
include('lib.php');

$taskMap = get('task_dump');
?>
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css" integrity="sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T" crossorigin="anonymous">
    <link rel='stylesheet' href='/engine.css'>
    <title>Campaign admin</title>
    <style>
    form { float: right }
    .form-control-file { display: none }
    .upload-button { margin-bottom: 0 }
    #notice { position: fixed; top:0; left:0; width: 100%; z-index: 100;display:none}
    </style>
  </head>
  <body>
    <div class="alert alert-primary" id="notice" role="alert"></div>
    <div class='row'>
    <? 
      $keylist = array_keys($taskMap['task'][0]);
      foreach($taskMap['task'] as $task) {  
        foreach($keylist as $key) { ?>
        <span><?= $task[$key]; ?></span>
        <? }
      } 
    ?>
    </div>
    <script src="https://unpkg.com/axios/dist/axios.min.js"></script>
    <script src="/engine.js"></script>
    <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.7/umd/popper.min.js" integrity="sha384-UO2eT0CpHqdSJQ6hJty5KVphtPhzWj9WO1clHTMGa3JDZwrnQq4sF86dIHNDz0W1" crossorigin="anonymous"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js" integrity="sha384-JjSmVgyd0p3pXB1rRibZUAYoIIy6OrQ6VrjIEaFf/nJGzIxFDsf4x0xIM+B07jRM" crossorigin="anonymous"></script>
    <script src="/Admin/script.js?1"></script>
  </body>
</html>
