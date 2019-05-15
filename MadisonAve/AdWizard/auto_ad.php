<?php
$data = file_get_contents($_GET['url']);
$map = [];
foreach([
  ['title', '/title>(.*)<.title/i'],
  ['description', '/.description.\s*content=.([^"\']*)/i'],
  ['twitter', "/twitter.com/(\w*)/i"],
  ['instagram', "/instagram.com/([\-\/\w]*)/i"],
  ['facebook', "/href=[\"'htps:\/w\.]*facebook.com/([\-\/\w]*)/i"],
  ['phone', "/(\(?\d{3}\)?\s?\d{3}-\d{4})/i"],
  ['address', "/(\d+)((?:\s\w+){2,4})[,\.](<br.?>)((?:\s\w+){1,3})/i"],
  ['logo', "/src=[\"']([^\s]*logo[^\s\"']*)/i"]
] as $row) {
  list($field, $term) = $row; 
  if(preg_match_all($term, $data, $matches)) {
    $map[$field] = $matches[1][0];
  } else {
    $map[$field] = null;
  }
}
if($map['title']) {
  $parts = explode('|', $map['title']);
  $map['title'] = $parts[0];
}
if($map['description']) {
  $parts = explode('.', $map['description']);
  $map['description'] = $parts[0];
}
var_dump($map);
