<?php

$EMAILDIR = 'templates/';

function email($user, $name, $vars) {
  global $EMAILDIR;

  $data = file($EMAILDIR . $name);
  if(!$data) {
    throw new Exception("Can't find $name");
  }

  $subject = array_shift($data);

  extract($vars);
  ob_start();
  {
    include($EMAILDIR . '_header');
    echo implode('\n', $data);
    include($EMAILDIR . '_footer');
  }
  $output = ob_get_clean();
}

