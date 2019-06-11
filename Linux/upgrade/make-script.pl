#!/usr/bin/perl

use strict; 
use warnings;

sub trim { my $s = shift; $s =~ s/^\s+|\s+$//g; return $s };
if ($#ARGV < 0) {
  die "You need to name your script";
}

my $ref = trim(`/usr/bin/git log -1 --format='%at'`);
my @matchList = glob "'${ref}*'";
my $count = $#matchList + 2;
my $num = sprintf("%02d", $count);
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
# Here's the important thing.
#
# There's a few possible command line parameters
# that will come in. You need to account for them:
#  
#   - upgradepre   : run prior to the new stack starting
#   - upgradepost  : run after the new stack starting
#   - rollback     : a way to undo the command
#
# The upgrade should do the incremental changes 
# needed and the rollback should undo them if it
# fails.
#
# In the example below we are very cheap and
# use an eval

upgradepre() {
}

upgradepost() {
}

rollback() {
}

eval \$1

};
close $fh;

chmod 0755, $name;
print "Template $name created. Now you need to edit it\n";
