#!/usr/bin/perl

use strict; 
use warnings;

sub trim { my $s = shift; $s =~ s/^\s+|\s+$//g; return $s };
if ($#ARGV < 0) {
  die "You need to name your script";
}

my $ref = trim(`/usr/bin/git log -1 --format='%at'`);
my @matchList = glob "'${ref}*'";
my $num = sprintf("%02d", $#matchList);
my $name = "$ref$num-$ARGV[0].script";

open (my $fh, ">", $name) or die "Can't open $name";
print $fh qq{#!/bin/bash
#
# ^ Replace with your scripting language of choice
# The screen has:
#   
#   /usr/bin/perl    5.28
#   /usr/bin/python3 3.7.3rc1
#   /usr/bin/bash    5.0.3
#   /usr/bin/dash    0.5.10.2-5
#
# These will be run as root and will inherit the 
# environment variables defined in const.sh
#

upgrade() {
  return 0
}

rollback() {
  return 0
}

#
# Here's the important thing.
#
# There's two possible command line parameters
# that will come in. You need to account for them.
# Either
#  
#   - upgrade
#   - rollback
#
# The upgrade should do the incremental changes 
# needed and the rollback should undo them if it
# fails.
#

case \$1 in 
  upgrade)
    upgrade

    # The 0 exit code is used to mark success
    exit 0
    ;;

  rollback)
    rollback

    # A non-zero means that it failed
    exit 1
    ;;
esac

exit 1
};
close $fh;

print "Template $name created. Now you need to edit it\n";
