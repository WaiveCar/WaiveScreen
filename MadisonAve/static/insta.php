<?
/*
 * Parameters:
 * 
 *   - bigtext: The text to replace the @handle
 *   - smalltext: The text to replace the words below
 *   - user: The user to parse
 *   - duration: The time in seconds to show
 *   - loop: Whether to loop the show or just stop 
 *
 *   Future:
 *     assetlist: Assets to show instead of "detecting" them
 */
function get($what) {
  global $contents;
  preg_match_all('/"' . $what . '...([^"]*)/', $contents, $matchList);
  return $matchList[1][0];
}
function check($x) {
  global $sizes;
  return $sizes[$x] > 1080 ? 'class=fill ' : '';
}
$handle = trim($_GET['user']);
if (!file_exists("/tmp/$handle")) {
  $str = shell_exec("curl 'https://www.instagram.com/$handle/' -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' -H 'Accept-Language: en-US,en;q=0.5' --compressed -H 'Connection: keep-alive' -H 'Upgrade-Insecure-Requests: 1' -H 'TE: Trailers'");
  file_put_contents("/tmp/$handle", $str);
}

$contents = file_get_contents("/tmp/$handle");
$smalltext = $_GET['smalltext'] ?: json_decode('"' . get('full_name') . '"');
$bigtext = $_GET['bigtext'] ?: $handle;
$logo = $_GET['logo'] ?: get('profile_pic_url_hd');
$images = $_GET['images'] ?: [];
$sizes = $_GET['sizes'] ?: [];

preg_match_all('/.height.:(\d*),.width.:1080},.display_url...([^"]*)/', $contents, $matchList);
$sizes = array_merge($sizes, $matchList[1]);
$images = array_merge($images, $matchList[2]);
$iy = 0;
for($ix = count($images); $ix < 6; $ix ++) {
  $images[] = $images[$iy];
  $sizes[] = $sizes[$iy];
  $iy++;
}

$dur = $_GET['duration'] ?: 16;
$loop = $_GET['loop'] ?: 'infinite';

?>
<link href=https://fonts.googleapis.com/css?family=Roboto:300,400&display=swap rel=stylesheet>
<style>
* {
  animation: <?= $dur ?>s <?= $loop ?>;
  animation-fill-mode: forwards;
}
#blur {
  position: absolute;
  top: 0; 
  left: 0;
  height: 35.1vw;
  overflow: hidden;
}
#blur img {
  margin-top: 2vw;
  margin-left: -27.5%;
  height: 70.2vw;
  opacity: 0.05;
  border-radius: 500vw;
  
}
body { 
  background: #fff;
  overflow: hidden;
}
body.dark { 
  color: #fff;
  background: #000 
}
h2,h3,body { 
  margin: 0;
  font-family: 'Roboto', sans-serif;
}
h2 { 
  font-size: 2.85vw;
  font-weight: 400;
  margin-top: 2vw;
}
small {
  display: inline-block;
  font-size: 75%;
  padding-bottom: 0.15em;
  margin-right: 0.1em;
  vertical-align: bottom;
}
h3 {
  font-size: 1.75vw;
  font-weight: 300;
}
#wrap {
  height: 35.1vw;
  position: relative;
  overflow: hidden;
}
#wrap > div {
  width: 35.1vw;
  text-align: center;
}
.row {
  position: absolute;
  display: flex;
  justify-content: center;
  flex-flow: row wrap;
  opacity: 0;
}
.row img {
  object-fit: cover;
  max-height: calc(35.1vw + 1vw);
  min-height: calc(35.1vw);
}
img.fill {
  min-width: calc(35.1vw + 1vw);
}
#wrap > #brand {
  display: flex;
  align-items: center;
  justify-content: space-around;
  height: 35.1vw;
  width: calc(100% - 2 * 34.6vw);
  transition-timing-function: ease;
  animation-name: logo;
}
#logo-wrap {
  display: inline-flex;
  align-items: center;
  justify-content: space-around;
  height: 16.5vw;
  width: 16.5vw;
}
#copy { 
  animation-name: brandslide;
}
#brand img {
  border-radius: 50vw;
  box-shadow: 0 0.2vw 0.8vw 0vw rgba(0,0,0,0.125);
  width: 100%;
  animation-name: zoomout;
}
.row.down {
  bottom: 0;
  animation-name: slidedown;
}
.row.up {
  top: 0;
  animation-name: slideup;
}
.row div {
  display: flex;
  align-items: center;
  justify-content: space-around;
  box-shadow: 0 0.1vw 0.4vw 0vw rgba(0,0,0,0.25);
  border-radius: 2vw;
  height: calc(35.1vw - 2vw);
  width: calc(35.1vw - 2vw);
  margin: 1vw 0;
  overflow: hidden
}
@keyframes zoomout {
  0% { margin-top: -35vw;}
  2% { margin-top: 0 }
  90% { width: 100%; opacity: 1 }
  97%,100% { width: 0; opacity: 0 }
}
@keyframes brandslide {
  90% { transform: translateY(0); opacity: 1 }
  97%,100% { transform: translateY(12vw); opacity: 0 }
}
@keyframes logo {
  0% { margin-left: 33%; opacity: 0 }
  5% { opacity: 1 }
  10%,77% { margin-left: .5vw }
  90%,100% { margin-left: 33% }
}
@keyframes slideup {
  0% { transform: translateY(36.1vw); opacity: 0 }
  10%,23% { transform: translateY(0); opacity: 1 }
  36%,50% { transform: translateY(-35.1vw) }
  63%,77% { transform: translateY(calc(-35.1vw * 2)); opacity: 1 }
  90%,100% { transform: translateY(calc(-35.1vw * 3)); opacity: 0 }
}
@keyframes slidedown {
  from { transform: translateY(-35.1vw); opacity: 0 }
  10%,23% { transform: translateY(0); opacity: 1 }
  36%,50% { transform: translateY(35.1vw) }
  63%,77% { transform: translateY(calc(35.1vw * 2)); opacity: 1 }
  90%,100% { transform: translateY(calc(35.1vw * 3)); opacity: 0 }
}
</style>
<body>
  <div id=blur>
    <img src=<?= $logo ?>>
  </div>
  <div id=wrap>
    <div id=brand>
      <div>
        <div id=logo-wrap>
          <img src=<?= $logo ?>>
        </div>
        <div id=copy>
          <h2><?= $bigtext ?></h2>
          <h3><?= $smalltext ?></h3>
        </div>
      </div>
    </div>
    <div class='row up' style='left:calc(100% - 34.6vw * 2)'>
    <? foreach([0,1,2] as $i){ ?>
    <div><img <?=check($i);?>src=<?= $images[$i] ?>></div>
    <? } ?>
    </div>
    <div class='row down' style='left:calc(100% - 35.1vw)'>
    <? foreach([5,4,3] as $i){ ?>
    <div><img <?=check($i);?>src=<?= $images[$i] ?>></div>
    <? } ?>
    </div>
  </div>
</body>
