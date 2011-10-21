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

our $VERSION = '11.10.21';

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
	mkpath '/home/cemosshe/csv/'.param('systemgroup').'/'.param('systemname');
	if ( param('details') && param('systemgroup') && param('systemname') && ($user eq 'admin' || $user eq param('systemgroup')) ) {
		rename '/home/cemosshe/csv/'.param('systemgroup').'/'.param('systemname').'/details.csv', '/home/cemosshe/csv/'.param('systemgroup').'/'.param('systemname').'/details.csv~';
		open DETAILS, '>/home/cemosshe/csv/'.param('systemgroup').'/'.param('systemname').'/details.csv' or die $!;
		print DETAILS param('details');
		close DETAILS;
		chmod 0664, glob('/home/cemosshe/csv/'.param('systemgroup').'/'.param('systemname').'/*');
		print '/home/cemosshe/csv/'.param('systemgroup').'/'.param('systemname')."/details.csv\n";
	}
	if ( param('sla') && param('systemgroup') && param('systemname') && ($user eq 'admin' || $user eq param('systemgroup')) ) {
		rename '/home/cemosshe/csv/'.param('systemgroup').'/'.param('systemname').'/sla.csv', '/home/cemosshe/csv/'.param('systemgroup').'/'.param('systemname').'/sla.csv~';
		open DETAILS, '>/home/cemosshe/csv/'.param('systemgroup').'/'.param('systemname').'/sla.csv' or die $!;
		print DETAILS param('sla');
		close DETAILS;
		chmod 0664, glob('/home/cemosshe/csv/'.param('systemgroup').'/'.param('systemname').'/*');
		print '/home/cemosshe/csv/'.param('systemgroup').'/'.param('systemname')."/sla.csv\n";
	}
} else {
	print a({-href=>'/?logout=1'}, $user),br;
	if ( param('list') eq 'full' ) {
		print &htmlhead;
		my @details = &details;
		my @last = (('')x12);
		foreach ( @details ) {
			my @detail = split m!;!;
			my %color = ();
			if ( $TIMESTAMPS-UnixDate(ParseDate("$detail[0] $detail[1]"), '%s') >= 24*60*60 ) {
				$color{timestamp}='red';
			} elsif ( $TIMESTAMPS-UnixDate(ParseDate("$detail[0] $detail[1]"), '%s') >= 1*60*60 ) {
				$color{timestamp}='yellow';
			} else {
				$color{timestamp}='green';
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
				td({-bgcolor=>'white', class=>$detail[2]?'border':''}, [a({-href=>"/?list=full&group=$detail[2]"}, $detail[2])]).
				td({-bgcolor=>'white', class=>$detail[3]?'border':''}, [a({-href=>"/?list=full&group=$detail[2]&system=$detail[3]"}, $detail[3])]).
				td({-bgcolor=>'white', class=>$detail[4]?'border':''}, [$detail[4]]).
				td({-bgcolor=>$color{status}, class=>'border'}, [@detail[5..10]])
			]);
			@last = split m!;!;
		}
		print Tr({-bgcolor=>'#dddddd', -class=>'border datarowhead'}, [ th(['Timestamp', 'System Group', 'System', 'Property Group', 'Property','Status','%-OK','Time on Status','Value','Details']) ]);
		print &htmlfoot;
	} elsif ( !param('list') || param('list') eq 'groups' ) {
		print &htmlhead;
		my @details = &details;
		my @last = (('')x12);
		print Tr({-bgcolor=>'#dddddd', -class=>'border datarowhead'}, [ th(['Group', 'Systems', 'OK', 'WARN', 'ALERT', 'UNDEF']) ]);
		my %details = ();
		foreach ( @details ) {
			my @detail = split m!;!;
			my %color = ();
			if ( $TIMESTAMPS-UnixDate(ParseDate("$detail[0] $detail[1]"), '%s') >= 24*60*60 ) {
				$color{timestamp}='red';
			} elsif ( $TIMESTAMPS-UnixDate(ParseDate("$detail[0] $detail[1]"), '%s') >= 1*60*60 ) {
				$color{timestamp}='yellow';
			} else {
				$color{timestamp}='green';
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
			$details{$detail[2]}{SYSTEMS}++ if $detail[3] ne $last[3];
			$details{$detail[2]}{$detail[6]} = 0 unless $details{$detail[2]}{$detail[6]};
			$details{$detail[2]}{$detail[6]}++;
			@last = split m!;!;
		}
		foreach ( keys %details ) {
			print Tr({-class=>'datarow'}, [
				td({-bgcolor=>'white', class=>'border'}, [a({-href=>"/?list=full&group=$_"}, $_)]).
				td({-bgcolor=>'white', class=>'border'}, [$details{$_}{SYSTEMS}]).
				td({-bgcolor=>'green', class=>'border'}, [$details{$_}{OK}]).
				td({-bgcolor=>'yellow', class=>'border'}, [$details{$_}{WARN}]).
				td({-bgcolor=>'red', class=>'border'}, [$details{$_}{ALERT}]).
				td({-bgcolor=>'blue', class=>'border'}, [$details{$_}{UNDEF}])
			]);
		}
		print Tr({-bgcolor=>'#dddddd', -class=>'border datarowhead'}, [ th(['Group', 'Systems', 'OK', 'WARN', 'ALERT', 'UNDEF']) ]);
		print &htmlfoot;
	} elsif ( param('list') eq 'properties' ) {
		print &htmlhead;
		my @details = &details;
		my @last = (('')x12);
		foreach ( @details ) {
			my @detail = split m!;!;
			my %color = ();
			if ( $TIMESTAMPS-UnixDate(ParseDate("$detail[0] $detail[1]"), '%s') >= 24*60*60 ) {
				$color{timestamp}='red';
			} elsif ( $TIMESTAMPS-UnixDate(ParseDate("$detail[0] $detail[1]"), '%s') >= 1*60*60 ) {
				$color{timestamp}='yellow';
			} else {
				$color{timestamp}='green';
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
				td({-bgcolor=>'white', class=>$detail[2]?'border':''}, [a({-href=>"/?list=full&group=$detail[2]"}, $detail[2])]).
				td({-bgcolor=>'white', class=>$detail[3]?'border':''}, [a({-href=>"/?list=full&group=$detail[2]&system=$detail[3]"}, $detail[3])]).
				td({-bgcolor=>'white', class=>$detail[4]?'border':''}, [$detail[4]]).
				td({-bgcolor=>$color{status}, class=>'border'}, [@detail[5..10]])
			]);
			@last = split m!;!;
		}
		print Tr({-bgcolor=>'#dddddd', -class=>'border datarowhead'}, [ th(['Timestamp', 'System Group', 'System', 'Property Group', 'Property','Status','%-OK','Time on Status','Value','Details']) ]);
		print &htmlfoot;
	} elsif ( param('list') eq 'notok' ) {
		print &htmlhead;
		my @details = &details;
		my @last = (('')x12);
		foreach ( @details ) {
			my @detail = split m!;!;
			my %color = ();
			if ( $TIMESTAMPS-UnixDate(ParseDate("$detail[0] $detail[1]"), '%s') >= 24*60*60 ) {
				$color{timestamp}='red';
			} elsif ( $TIMESTAMPS-UnixDate(ParseDate("$detail[0] $detail[1]"), '%s') >= 1*60*60 ) {
				$color{timestamp}='yellow';
			} else {
				$color{timestamp}='green';
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
				td({-bgcolor=>'white', class=>$detail[2]?'border':''}, [a({-href=>"/?list=full&group=$detail[2]"}, $detail[2])]).
				td({-bgcolor=>'white', class=>$detail[3]?'border':''}, [a({-href=>"/?list=full&group=$detail[2]&system=$detail[3]"}, $detail[3])]).
				td({-bgcolor=>'white', class=>$detail[4]?'border':''}, [$detail[4]]).
				td({-bgcolor=>$color{status}, class=>'border'}, [@detail[5..10]])
			]);
			@last = split m!;!;
		}
		print Tr({-bgcolor=>'#dddddd', -class=>'border datarowhead'}, [ th(['Timestamp', 'System Group', 'System', 'Property Group', 'Property','Status','%-OK','Time on Status','Value','Details']) ]);
		print &htmlfoot;
	}
}
$session->flush;

# --------------------------------------------------
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
return fieldsort ';', [-3], @details;
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
-->
</style> 
</head>

<body>
<center>
<h1>CeMoSSHe System Status</h1>
<a href="/?list=full">Full Status of All</a> 
&nbsp; / &nbsp;
<a href="/?list=groups">Group List</a>
<!--
&nbsp; / &nbsp;
<a href="/?list=properties">Properties List</a> 
&nbsp; / &nbsp;
<a href="/?list=notok">Reduced Status - Not OK</a>
-->
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
