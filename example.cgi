#!/usr/bin/perl

#############################################################################
# CeMoSSHe: CEntral MOnitoring in a Simple SHell Environment
#
# Copyright (C) 2011- Stefan Adams
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# For bug reports and suggestions or if you just want to talk to me please
# contact me at stefan@cogentinnovators.com
#
# Updates will be available at  http://www.cogent-it.com/software/cemosshe/
# please check there for updates prior to submitting patches!
#
# For list of changes please refer to the HISTORY file. Thanks.
#############################################################################

# This cgi is still a work in progress, but it's a start

our $VERSION = '11.11.08';

use strict;
use warnings;

use CGI qw/:standard/;
use CGI::Session;
use File::Path;
use Sort::Fields;
use Date::Manip;
use Digest::MD5 qw/md5_hex/;

my $root = "/home/cemosshe/csv";

new CGI;
my $session = new CGI::Session;

my $user = $ENV{USER} if $ENV{USER};
$user = param('user') if param('user');
$user = $session->param('user') if $session->param('user');
$user ||= '';
my $pass = md5_hex($ENV{PASS}) if $ENV{PASS};
$pass = md5_hex(param('pass')) if param('pass');
$pass = $session->param('pass') if $session->param('pass');
$pass ||= '';

print STDERR "$user -=- $pass";
if ( $user && $pass ) {
	open USERS, '.htpasswd' or die $!;
	my @users = <USERS>;
	close USERS;
	if ( ! grep { /^$user:$pass$/ } @users ) {
		# User / Password not found
		if ( ! grep { /^$user:/ } @users ) {
			# User not found
			open USERS, '>>.htpasswd' or die $!;
			print USERS "$user:$pass\n";
			close USERS;
			print STDERR "$0 added user $user\n";
			$session->param('user', $user);
			$session->param('pass', $pass);
		} else {
			# User found, therefore wrong password
			$session->clear(['user','pass']);
		}
	} else {
		$session->param('user', $user);
		$session->param('pass', $pass);
	}
	undef @users;
} else {
	$session->clear(['user','pass']);
}
$user = $session->param('user');
undef $pass;

my $TIMESTAMP = UnixDate(ParseDate('now'), '%Y-%m-%d %H:%M:%S');
my $TIMESTAMPS = UnixDate(ParseDate($TIMESTAMP), '%s');
my %COUNT = (OK=>0, NOTOK=>0);

print $session->header;

if ( !$user || param('logout') ) {
	$session->delete;
	print &htmlhead;
	print start_form('POST', '/');
	print "Username: ", textfield('user'), br;
	print "Password: ", password_field('pass'), br;
	print submit;
	print end_form;
} elsif ( param('details') || param('sla') ) {
	mkpath "$root/".param('systemgroup').'/'.param('systemname');
	if ( param('details') && param('systemgroup') && param('systemname') && ($user eq 'admin' || $user eq param('systemgroup')) ) {
		rename "$root/".param('systemgroup').'/'.param('systemname').'/details.csv', "$root/".param('systemgroup').'/'.param('systemname').'/details.csv~';
		open DETAILS, ">$root/".param('systemgroup').'/'.param('systemname').'/details.csv' or die $!;
		print DETAILS param('details');
		close DETAILS;
		chmod 0664, glob("$root/".param('systemgroup').'/'.param('systemname').'/*');
		print "$root/".param('systemgroup').'/'.param('systemname')."/details.csv\n";
	}
	if ( param('sla') && param('systemgroup') && param('systemname') && ($user eq 'admin' || $user eq param('systemgroup')) ) {
		rename "$root/".param('systemgroup').'/'.param('systemname').'/sla.csv', "$root/".param('systemgroup').'/'.param('systemname').'/sla.csv~';
		open DETAILS, ">$root/".param('systemgroup').'/'.param('systemname').'/sla.csv' or die $!;
		print DETAILS param('sla');
		close DETAILS;
		chmod 0664, glob("$root/".param('systemgroup').'/'.param('systemname').'/*');
		print "$root/".param('systemgroup').'/'.param('systemname')."/sla.csv\n";
	}
} else {
	print a({-href=>'/?logout=1'}, $user),br;
	@_ = grep { !/(details|sla|logout|user|pass)$/ } param;
	if ( $#_ == -1 || (param('list') && param('list') eq 'groups') ) {
		print htmlhead(a({-href=>"/?status=!INFO&status=!OK"}, "Not OK").' / '.a({-href=>"/"}, "Group List"));
		my @details = &details;
		my @last = (('')x12);
		print Tr({-bgcolor=>'#dddddd', -class=>'border datarowhead'}, [ th(['Group', '#', 'Timestamp', 'Status']) ]);
		my %details = ();
		foreach ( @details ) {
			my @detail = split m!;!;
			my %color = ();
			my $timestamp;
next if $detail[3] eq 'TODO';
			@{$details{$detail[2]}{LMI}} = lmi($detail[2], $detail[3]);
			if ( $TIMESTAMPS-UnixDate(ParseDate("$detail[0] $detail[1]"), '%s') >= 24*60*60 ) {
				$timestamp = 'ALERT';
				$color{timestamp}='red';
			} elsif ( $TIMESTAMPS-UnixDate(ParseDate("$detail[0] $detail[1]"), '%s') >= 1*60*60 ) {
				$timestamp = 'WARN';
				$color{timestamp}='yellow';
			} else {
				$timestamp = 'OK';
				$color{timestamp}='green';
			}
			if ( my @timestamp = param('timestamp') ) {
				next unless grep { $_ eq $timestamp } @timestamp;
			}
			if ( $detail[6] eq 'ALERT' ) {
				$color{status}='red';
				$COUNT{NOTOK}++;
			} elsif ( $detail[6] eq 'WARN' ) {
				$color{status}='yellow';
				$COUNT{NOTOK}++;
			} elsif ( $detail[6] eq 'OK' ) {
				$color{status}='green';
				$COUNT{OK}++;
			} elsif ( $detail[6] eq 'INFO' ) {
				$color{status}='white';
			} else {
				$color{status}='blue';
				$COUNT{NOTOK}++;
			}
			$detail[7] =~ s/(\.\d)0%$/$1%/;
			$detail[7] =~ s/\.0%$/%/;
			$details{$detail[2]}{SYSTEMS} = 0 unless $details{$detail[2]}{SYSTEMS};
			$details{$detail[2]}{TSALERT} = 0 unless $details{$detail[2]}{TSALERT};
			$details{$detail[2]}{TSWARN} = 0 unless $details{$detail[2]}{TSWARN};
			$details{$detail[2]}{TSOK} = 0 unless $details{$detail[2]}{TSOK};
			if ( $detail[3] ne $last[3] && $detail[3] ne 'TODO' ) {
				$details{$detail[2]}{SYSTEMS}++;
				$details{$detail[2]}{TSALERT}++ if $timestamp eq 'ALERT';
				$details{$detail[2]}{TSWARN}++ if $timestamp eq 'WARN';
				$details{$detail[2]}{TSOK}++ if $timestamp eq 'OK';
			}
			$details{$detail[2]}{$detail[6]} = 0 unless $details{$detail[2]}{$detail[6]};
			$details{$detail[2]}{$detail[6]}++;
			@last = split m!;!;
		}
		foreach ( sort keys %details ) {
			my @lmi = @{$details{$_}{LMI}};
			print Tr({-class=>'datarow'}, [
				td({-bgcolor=>'white', class=>'border'}, [a({-href=>"/?status=!INFO&status=!OK&group=$_"}, $_).($lmi[0] ? ' '.a({href=>$lmi[0]}, img({-src=>"/lmi_title_rc.png", -border=>0, -width=>16, -height=>16})) : '')]).
				td({-bgcolor=>'white', class=>'border'}, [$details{$_}{SYSTEMS}]).
				td({-bgcolor=>'white', class=>'border', width=>'100px'}, [bar($details{$_}{TSOK}, $details{$_}{TSWARN}, $details{$_}{TSALERT}, $details{$_}{SYSTEMS})]).
				td({-bgcolor=>'white', class=>'border', width=>'300px'}, [bar($details{$_}{OK}, $details{$_}{WARN}, $details{$_}{ALERT})])
				#td({-bgcolor=>'green', class=>'border'}, [$details{$_}{OK}]).
				#td({-bgcolor=>'yellow', class=>'border'}, [$details{$_}{WARN}]).
				#td({-bgcolor=>'red', class=>'border'}, [$details{$_}{ALERT}]).
				#td({-bgcolor=>'blue', class=>'border'}, [$details{$_}{UNDEF}])
			]), "\n";
		}
		print Tr({-bgcolor=>'#dddddd', -class=>'border datarowhead'}, [ th(['Group', '#', 'Timestamp', 'Status']) ]);
		print &htmlfoot;
	} else {
		print htmlhead(a({-href=>"/?status=!INFO&status=!OK"}, "Not OK").' / '.a({-href=>"/"}, "Group List"));
		my @details = &details;
		my @last = (('')x12);
		foreach ( @details ) {
			my @detail = split m!;!;
			my @lmi = lmi($detail[2], $detail[3]);
			my @status = ();
			if ( @status = grep { /^!/ } param('status') ) {
				next if grep { $_ eq "!$detail[6]" } @status;
			} elsif ( @status = grep { /^[^!]/ } param('status') ) {
				next unless grep { $_ eq $detail[6] } @status;
			}
			my %color = ();
			my $timestamp;
			if ( $TIMESTAMPS-UnixDate(ParseDate("$detail[0] $detail[1]"), '%s') >= 24*60*60 ) {
				$timestamp = 'ALERT';
				$color{timestamp}='red';
			} elsif ( $TIMESTAMPS-UnixDate(ParseDate("$detail[0] $detail[1]"), '%s') >= 1*60*60 ) {
				$timestamp = 'WARN';
				$color{timestamp}='yellow';
			} else {
				$timestamp = 'OK';
				$color{timestamp}='green';
			}
			if ( my @timestamp = param('timestamp') ) {
				next unless grep { $_ eq $timestamp } @timestamp;
			}
			if ( $detail[6] eq 'ALERT' ) {
				$color{status}='red';
				$COUNT{NOTOK}++;
			} elsif ( $detail[6] eq 'WARN' ) {
				$color{status}='yellow';
				$COUNT{NOTOK}++;
			} elsif ( $detail[6] eq 'OK' ) {
				$color{status}='green';
				$COUNT{OK}++;
			} elsif ( $detail[6] eq 'INFO' ) {
				$color{status}='white';
			} else {
				$color{status}='blue';
				$COUNT{NOTOK}++;
			}
			$detail[7] =~ s/(\.\d)0%$/$1%/;
			$detail[7] =~ s/\.0%$/%/;
			do { $detail[0]=''; $detail[1]=''; } if $detail[3] eq $last[3];
			$detail[2]='' if $detail[2] eq $last[2];
			$detail[3]='' if $detail[3] eq $last[3] && !$detail[2];
			$detail[4]='' if $detail[4] eq $last[4] && !$detail[3];
			$detail[5]='' if $detail[5] eq $last[5] && !$detail[4];
			print Tr({-bgcolor=>'#dddddd', -class=>'border datarowhead'}, [ th(['Timestamp', 'System Group', 'System', 'Property Group', 'Property','Status','%-OK','Time on Status','Value','Details']) ]) if $detail[0] && $detail[1] && $detail[2] && $detail[3] && $detail[4] && $detail[5];
			print Tr({-class=>'datarow'}, [
				td({-bgcolor=>$detail[0]||$detail[1]?$color{timestamp}:'white', class=>$detail[0]||$detail[1]?'border':''}, ["$detail[0] $detail[1]"]).
				td({-bgcolor=>'white', class=>$detail[2]?'border':''}, [a({-href=>"/?group=$detail[2]"}, $detail[2]).($detail[2] && $lmi[0] ? ' '.a({href=>$lmi[0]}, img({-src=>"/lmi_title_rc.png", -border=>0, -width=>16, -height=>16})) : '')]).
				td({-bgcolor=>'white', class=>$detail[3]?'border':''}, [a({-href=>"/?group=$detail[2]&system=$detail[3]"}, $detail[3]).($detail[3] && $lmi[1] ? ' '.a({href=>$lmi[1]}, img({-src=>"/lmi_title_rc.png", -border=>0, -width=>16, -height=>16})) : '')]).
				td({-bgcolor=>'white', class=>$detail[4]?'border':''}, [$detail[4]]).
				td({-bgcolor=>$color{status}, class=>"border$color{timestamp}"}, [@detail[5..10]])
			]);
			@last = split m!;!;
		}
		print Tr({-bgcolor=>'#dddddd', -class=>'border datarowhead'}, [ th(['Timestamp', 'System Group', 'System', 'Property Group', 'Property','Status','%-OK','Time on Status','Value','Details']) ]);
		print &htmlfoot;
	}
}
$session->flush;

# --------------------------------------------------

sub bar {
	my ($green, $yellow, $red, $number) = @_;
	$number = $green + $yellow + $red unless $number;
	return undef unless $number;
	$green = $green/$number*100;
	$yellow = $green+($yellow/$number*100);
	$red = $yellow+($red/$number*100);
	$green = "display: inline; background-color: green; position: absolute; width: $green%; height: 10px;  z-index: 3; vertical-align: top; ";
	$yellow = "display: inline; background-color: yellow; position: absolute; width: $yellow%; height: 10px;  z-index: 2; vertical-align: top; ";
	$red = "display: inline; background-color: red; position: absolute; width: $red%; height: 10px;  z-index: 1; vertical-align: top; ";
	$number = "display: inline; position: absolute; width: 100%; height: 10px;  z-index: 4; text-align: center; vertical-align: top; ";
	return div({-style=>"position: relative; vertical-align: top; ", -alt=>"$_[0] / $_[1] / $_[2]"}, div({-style=>$green}, '&nbsp;').div({-style=>$yellow}, '&nbsp;').div({-style=>$red}, '&nbsp;'));
}

sub lmi {
	my ($group, $system) = @_;
	my @lmi = ('', '');
	open LMI, "$root/$group/.lmi" and do {
		$lmi[0] = <LMI>;
		close LMI;
	};
	open LMI, "$root/$group/$system/.lmi" and do {
		$lmi[1] = <LMI>;
		close LMI;
	};
	return @lmi;
}

sub details {
my @details = ();
opendir ROOT, $root or die $!;
while ( my $systemgroup = readdir(ROOT) ) {
	next if $systemgroup =~ /^\./;
	next if param('group') && param('group') ne $systemgroup;
	next unless $user eq 'admin' || $user eq $systemgroup;
	next unless -d "$root/$systemgroup";
	opendir SYSTEMGROUP, "$root/$systemgroup" or die $!;
	while ( my $system = readdir(SYSTEMGROUP) ) {
		next if $system =~ /^\./;
		next if param('system') && param('system') ne $system;
		next unless -d "$root/$systemgroup/$system";
		open DETAILS, "$root/$systemgroup/$system/details.csv" or next;
		while ( $_ = <DETAILS> ) {
			local @_ = split m!;!;
			push @details, $_ if (!param('pgroup') && !param('property')) || (param('pgroup') && param('pgroup') eq $_[4]) || (param('property') && param('property') eq $_[5]);
		}
		close DETAILS;
	}
	closedir SYSTEMGROUP;
}
closedir ROOT;
return fieldsort ';', [3,4], @details;
}

sub htmlhead {
return <<HEAD;
<html>
<head>
<meta http-equiv="refresh" content="300" />
<title>
CeMoSSHe System Status
</title>
<script type="text/javascript">
<!--
/*
http://www.weberdev.com/get_example-4263.html
author : Ioannis Cherouvim
web : http://cherouvim.com
date : 2005-12-03
*/

var COLLAPSABLE_PARENT_NAME = "collapsable";
var COLLAPSABLE_PARENT_TYPE = "div";
var COLLAPSABLE_CHILD_TYPE = "pre";

var COLLAPSABLE_EXPAND = "[expand]";
var COLLAPSABLE_SHRINK = "[shrink]";

init = function() {
    if(document.getElementById && document.createTextNode) {
        var entries = document.getElementsByTagName(COLLAPSABLE_PARENT_TYPE);
        for(i=0;i<entries.length;i++)
            if (entries[i].className==COLLAPSABLE_PARENT_NAME)
                assignCollapse(entries[i]);
    }
}

assignCollapse = function (div) {
    var button = document.createElement('a');
    button.style.cursor='pointer';
    button.setAttribute('expand', COLLAPSABLE_EXPAND);
    button.setAttribute('shrink', COLLAPSABLE_SHRINK);
    button.setAttribute('state', -1);
    button.innerHTML='dsds';
    div.insertBefore(button, div.getElementsByTagName(COLLAPSABLE_CHILD_TYPE)[0]);

    button.onclick=function(){
        var state = -(1*this.getAttribute('state'));
        this.setAttribute('state', state);
        this.parentNode.getElementsByTagName(COLLAPSABLE_CHILD_TYPE)[0].style.display=state==1?'none':'block';
        this.innerHTML = this.getAttribute(state==1?'expand':'shrink');
    };               
    button.onclick();
}
window.onload=init;
-->
</script>
<style type='text/css'>
<!--
.ok { color: green; display: inline; }
.notok { color: red; display: inline; }
.collapsable { border: 0px solid black; }
table { padding: 2px; border-collapse: collapse; }
.border { border: 1px solid black; }
.bordergreen { border: 1px solid black; }
.borderyellow { border: 3px solid gold; }
.borderred { border: 3px solid firebrick; }
<<<<<<< HEAD:example.cgi
=======
.nospacing { border-collapse: collapse; padding: 0px; border-spacing: 0px; margin: 0px; }
>>>>>>> 2e892e1909de67acdac4edbb8286a49ed50e5a24:example.cgi
-->
</style> 
</head>

<body>
<center>
<h1>CeMoSSHe System Status</h1>
$_[0]
<p>
$TIMESTAMP
<br>
<table>
HEAD
}

sub htmlfoot {
return <<FOOT;
</table>
Totals: <div class="ok">$COUNT{OK} checks are OK</div> - <div class="notok">$COUNT{NOTOK} show problems</div>

<p>&nbsp;<p>

<font size="-2">Monitoring with <a href="http://www.cogent-it.com/software/cemosshe/">CeMoSShE</a>

</center>

</body>
</html>
FOOT
}
