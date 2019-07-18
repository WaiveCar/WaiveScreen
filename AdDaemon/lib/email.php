<?php
require $_SERVER['DOCUMENT_ROOT'] .  'AdDaemon/vendor/autoload.php';
use Mailgun\Mailgun;

function email($user, $name, $vars) {
  $DIR = 'templates/';

  if(! ($data = file($DIR . $name) ) ) {
    throw new Exception("Can't find $name");
  }

  $subject = array_shift($data);

  extract($vars);

  ob_start();
  {
    include $DIR . '_header';
    echo implode('\n', $data);
    include $DIR . '_footer';
  }
  $body = ob_get_clean();

  $mg = Mailgun::create('key-example');

  $mg->messages()->send('waivecar.com', [
    'from'    => 'ads@waivecar.com',
    'to'      => $user['email'],
    'subject' => $subject,
    'text'    => $body
  ]);
}

