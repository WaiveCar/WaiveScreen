<?
include('../AdDaemon/lib/lib.php');
include('lib.php');

function get_screen($id) {
  global $screenMap;
  $screen = $screenMap[$id];
  return $screen['car'] ?: $screen['serial'] ?: substr($screen['uid'], 0, 8) ;
}


$taskMap = get('task_dump');
$keylist = ['command', 'args', 'created_at']; //array_keys($taskMap['task'][0]);
$responseKeys = ['response', 'created_at'];//array_keys($taskMap['response'][0]);
$screentaskMap = [];
$responseMap = [];
$screenMap = [];

$responseKeys = array_filter($responseKeys, function($row) { 
  return ! ( $row == 'task_id' || $row == 'id' );
});
foreach($taskMap['screen'] as $obj) {
  $screenMap[$obj['id']] = $obj;
}

foreach($taskMap['response'] as $obj) {
  $id = $obj['task_id'];
  if (!array_key_exists($id, $responseMap)) {
    $responseMap[$id] = [];
  }
  $responseMap[$id][$obj['screen_id']] = $obj;
}
foreach($taskMap['task_screen'] as $obj) {
  $id = $obj['task_id'];
  if (!array_key_exists($id, $screentaskMap)) {
    $screentaskMap[$id] = [];
  }
  $screentaskMap[$id][] = $obj['screen_id'];
}

?>
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <link href="/css/all.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css" integrity="sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T" crossorigin="anonymous">
    <link rel='stylesheet' href='/engine.css'>
    <link href="/css/sb-admin-2.min.css" rel="stylesheet">
    <title>Commands</title>
    <style>
    form { float: right }
    .form-control-file { display: none }
    .upload-button { margin-bottom: 0 }
    .answer td {border-top: 0}
    .answer { margin-left:10px;border-left: 1px solid #ccc }
    #content-wrapper * { color: #000 }
    #notice { position: fixed; top:0; left:0; width: 100%; z-index: 100;display:none}
    </style>
  </head>
  <body id="page-top">
  <div id="wrapper">
    <? include ('partials/sidebar.php'); ?>
    <div id="content-wrapper" class="d-flex flex-column">
    <? include ('partials/topbar.php'); ?>
        <div class="alert alert-primary" id="notice" role="alert"></div>
        <div class='row'>
          <div class="col-lg-12">
            <table class="table">
              <thead>
                <tr>
                  <? foreach($keylist as $key) { ?>
                    <th scope="col"><?=$key?></th>
                  <? } ?>
                </tr>
              </thead>
              <tbody>
              <? 
                foreach($taskMap['task'] as $task) {  
                  $taskId = $task['id'];
                  echo '<tr>';
                  foreach($keylist as $key) { ?>
                    <td><?= $task[$key]; ?></td>
                  <? } ?>

                  </tr><tr>
                    <td style=border-top:0; colspan=<?= count($keylist); ?>>
                      <table class='answer'>
                        <? foreach($screentaskMap[$task['id']] as $screenId)  {  
                            echo '<tr>';
                            echo '<td style=width:100px;overflow:hidden>' . get_screen($screenId) . '</td>';
                            $response = aget($responseMap, "$taskId.$screenId");
                            if($response) {
                              if(empty($response['response'])) {
                                $response['response'] = 'ran';
                              }
                              foreach($responseKeys as $key) { ?>
                                <td> <?= preg_replace('/\n/', '<br>', $response[$key]); ?></td>
                             <? } 
                            } else {
                              $screen = $screenMap[$screenId];
                              echo "<td style=width:80px>" . (($screen['last_task'] >= $taskId) ? "ran" : "") . "</td>";
                              echo "<td>" . $screen['last_seen'] . "</td>";
                            }
                            echo "</tr>";     
                         } ?>
                      </table>
                    </td>
                  </tr> <?
                } 
              ?>
              </tbody>
            </table>
          </div>
        </div>
        </div>
      </div>
     </div>
   </div>
    <script src="https://unpkg.com/axios/dist/axios.min.js"></script>
    <script src="/engine.js"></script>
    <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.7/umd/popper.min.js" integrity="sha384-UO2eT0CpHqdSJQ6hJty5KVphtPhzWj9WO1clHTMGa3JDZwrnQq4sF86dIHNDz0W1" crossorigin="anonymous"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js" integrity="sha384-JjSmVgyd0p3pXB1rRibZUAYoIIy6OrQ6VrjIEaFf/nJGzIxFDsf4x0xIM+B07jRM" crossorigin="anonymous"></script>
    <script src="/js/sb-admin-2.min.js"></script>
    <script src="/Admin/script.js?1"></script>
  </body>
</html>
