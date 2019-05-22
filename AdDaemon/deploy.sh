#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $DIR
git pull

lib/update_db.php

ver=$(git describe)

cat > lib/const.php << ENDL
<?php
\$VERSION="$ver";
ENDL
