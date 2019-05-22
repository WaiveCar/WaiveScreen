#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $DIR
git pull

ver=$(git describe)

cat > lib/const.php << ENDL
<?php
\$VERSION="$ver";
ENDL
