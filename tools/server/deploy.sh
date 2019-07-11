#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $DIR
git pull

$DIR/../../AdDaemon/lib/update_db.php

cat > $DIR/../../AdDaemon/lib/const.php << ENDL
<?php
\$VERSION="$(git describe)";
\$LASTCOMMIT=$(git log -1 --format="%at")
ENDL
