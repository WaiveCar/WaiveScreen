<?php
$fieldList = [
  'Name',
  'Logo URL', // todo, add an upload option
  'Description',
  'Phone',
  'Address',
  'Website',
  'Twitter',
  'Facebook'
  'Instagram'
]

foreach($fieldList as $field) {
  echo "<label for='$field'>$field";
  echo "<input name='$field'>";
  echo "</label>";
}
?>
