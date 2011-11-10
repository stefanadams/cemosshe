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

our $VERSION = '11.11.09';

use strict;
use warnings;

use CGI qw/:standard *table/;
use CGI::Session;
use File::Path;
use Date::Manip;
use Digest::MD5 qw/md5_hex/;

use lib '/usr/local/lib/cemosshe';
use Table::Wave;

my $root = "/home/cemosshe/csv";

new CGI;
my $session = new CGI::Session;
my ($user, $pass) = &setupsession;

my $TIMESTAMP = UnixDate(ParseDate('now'), '%Y-%m-%d %H:%M:%S');
my $TIMESTAMPS = UnixDate(ParseDate($TIMESTAMP), '%s');
my $COUNT = {};

if ( !$user || param('logout') ) {
	print "[Login form]";
	$session->delete;
	print &htmlhead;
	print start_form('POST', '/');
	print "Username: ", textfield('user'), br;
	print "Password: ", password_field('pass'), br;
	print submit('login', 'Login');
	print end_form;
} elsif ( param('details') || param('sla') ) {
	print STDERR "$user -=- $pass -=- ".param('systemgroup')." -=- ".param('systemname');
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
	print STDERR "$user -=- $pass";
	param('list', 'groups') unless param('list');
	print a({-href=>'/?logout=1'}, $user),br;
	print htmlhead();
	if ( my ($details, $lmi) = &details ) {
		print "<div class=\"ok\">000 checks are OK</div> - <div class=\"notok\">000 show problems</div>", br, br;
		if ( param('list') && param('list') eq 'groups' ) {
			my @menu = ();
			push @menu, a({-href=>'/?list=details&status=!INFO&status=!OK'}, 'All Not OK');
			push @menu, a({-href=>'/?list=groups'}, 'Group List');
			print htmlmenu(\@menu);
			print start_table;
			print Tr({-bgcolor=>'#dddddd', -class=>'border datarowhead'}, [ th(['Group', 'Status']) ]);
			foreach my $g ( sort keys %{$details} ) {
				my $count = $COUNT->{$g}->{_};
				print Tr({-class=>'datarow'}, [
					td({-bgcolor=>'white', class=>'border', width=>'150px'}, [bar($count->{TSOK}, $count->{TSWARN}, $count->{TSALERT}, a({-href=>"/?list=systems&group=$g"}, $g) .' '. $lmi->{$g}->{_})]).
					td({-bgcolor=>'white', class=>'border', width=>'300px'}, [bar($count->{OK}, $count->{WARN}, $count->{ALERT})])
				 ]), "\n";
			}
			print Tr({-bgcolor=>'#dddddd', -class=>'border datarowhead'}, [ th(['Group', 'Status']) ]);
			print end_table;
		} elsif ( param('list') && param('list') eq 'systems' ) {
			my @menu = ();
			push @menu, a({-href=>'/?list=details&status=!INFO&status=!OK'}, 'All Not OK');
			push @menu, a({-href=>'/?list=groups'}, 'Group List');
			my @submenu = ();
			push @submenu, a({-href=>'/?list=details&'.qs('group').'&status=!INFO&status=!OK'}, 'Not OK');
			push @submenu, a({-href=>'/?list=details&'.qs('group').'&status=INFO'}, 'Info');
			push @submenu, a({-href=>'/?list=details&'.qs('group')}, 'All');
			print htmlmenu(\@menu, \@submenu);
			print start_table;
			print Tr({-bgcolor=>'#dddddd', -class=>'border datarowhead'}, [ th(['Group', 'System', 'Status']) ]);
			my $tw = new Table::Wave;
			foreach my $g ( sort keys %{$details} ) {
				foreach my $s ( sort keys %{$details->{$g}} ) {
					my ($group) = $tw->wave($g);
					my $count = $COUNT->{$g}->{$s};
					print Tr({-class=>'datarow'}, [
						td({-bgcolor=>'white', class=>$group?'border':''}, [$group]).
						td({-bgcolor=>'white', class=>'border', width=>'200px'}, [bar($count->{TSOK}, $count->{TSWARN}, $count->{TSALERT}, a({-href=>'/?list=details&'.qs('group')."&system=$s&status=!INFO&status=!OK"}, $s) .' '. $lmi->{$g}->{$s})]).
						td({-bgcolor=>'white', class=>'border', width=>'300px'}, [bar($count->{OK}, $count->{WARN}, $count->{ALERT})])
					]), "\n";
				}
			}
			print Tr({-bgcolor=>'#dddddd', -class=>'border datarowhead'}, [ th(['Group', 'System', 'Status']) ]);
			print end_table;
		} elsif ( param('list') && param('list') eq 'details' ) {
			my @menu = ();
			push @menu, a({-href=>'/?list=details&status=!INFO&status=!OK'}, 'All Not OK');
			push @menu, a({-href=>'/?list=groups'}, 'Group List');
			push @menu, a({-href=>'/?list=systems&'.qs('group')}, 'System List');
			my @submenu = ();
			push @submenu, a({-href=>'/?list=details&'.qs('group', 'system').'&status=!INFO&status=!OK'}, 'Not OK');
			push @submenu, a({-href=>'/?list=details&'.qs('group', 'system').'&status=INFO'}, 'Info');
			push @submenu, a({-href=>'/?list=details&'.qs('group', 'system')}, 'All');
			print htmlmenu(\@menu, \@submenu);
			print start_table;
			my $tw = new Table::Wave;
			foreach my $g ( sort keys %{$details} ) {
				print Tr({-bgcolor=>'#dddddd', -class=>'border datarowhead'}, [ th(['Timestamp', 'System Group', 'System', 'Property Group', 'Property','Status','%-OK','Time on Status','Value','Details']) ]);
				foreach my $s ( sort keys %{$details->{$g}} ) {
					foreach my $rec ( sort {$a <=> $b } keys %{$details->{$g}->{$s}} ) {
						my $detail = $details->{$g}->{$s}->{$rec};
						my ($group, $system, $pgroup) = $tw->wave(@$detail{qw/group system pgroup/});
						my $timestamp = $group || ($detail->{tsstatus} ne 'OK' && $system) ? $detail->{timestamp} : '';
						print Tr({-class=>'datarow'}, [
							td({-bgcolor=>$timestamp?$detail->{tscolor}:'white', class=>$timestamp?'border':''}, [$timestamp]).
							td({-bgcolor=>'white', class=>$group?'border':''}, [a({-href=>"/?list=systems&group=$g"}, $group) .' '. ($group?$lmi->{$g}->{_}:'')]).
							td({-bgcolor=>'white', class=>$system?'border':''}, [a({-href=>"/?list=details&group=$g&system=$s"}, $system) .' '. ($system?$lmi->{$g}->{$s}:'')]).
							td({-bgcolor=>'white', class=>$pgroup?'border':''}, [$pgroup]).
							td({-bgcolor=>$detail->{color}, class=>"border$detail->{tscolor}"}, [@$detail{qw/property status up_percent up_time value details/}])
						]);
					}
				}
			}
			print Tr({-bgcolor=>'#dddddd', -class=>'border datarowhead'}, [ th(['Timestamp', 'System Group', 'System', 'Property Group', 'Property','Status','%-OK','Time on Status','Value','Details']) ]);
			print end_table;
		} else {
			print br, "404";
		}
	} else {
		print br,'Nothing to report.';
	}
	print &htmlfoot;
}
$session->flush;

# --------------------------------------------------

sub qs {
	my @qs = ();
	foreach ( @_ ) {
		next unless param($_);
		push @qs, join '&', $_.'='.param($_);
	}
	return join '&', @qs;
}

sub bar {
	@_ = map { $_ || 0 } @_;
	my ($green, $yellow, $red, $display) = @_;
	my $number = $green + $yellow + $red;
	return undef unless $number;
	$green = $green/$number*100;
	$yellow = $green+($yellow/$number*100);
	$red = $yellow+($red/$number*100);
	my $Green = "display: inline; background-color: green; position: absolute; width: $green%; z-index: 3;";
	my $Yellow = "display: inline; background-color: yellow; position: absolute; width: $yellow%; z-index: 2;";
	my $Red = "display: inline; background-color: red; position: absolute; width: $red%; z-index: 1;";
	my $Number = "display: inline; position: absolute; width: 100%; z-index: 4; vertical-align: center;".($display?'':'text-align: center; font-size: 10px;');
	return div({-style=>"position: relative; vertical-align: top; "}, div({-style=>$Number}, $display||"$_[0]/$_[1]/$_[2] ( $number )").div({-style=>$Green}, '&nbsp;').div({-style=>$Yellow}, '&nbsp;').div({-style=>$Red}, '&nbsp;')).br;
}

sub details {
	my $details = {};
	my $lmi = {};
	opendir ROOT, $root or die $!;
	while ( my $group = readdir(ROOT) ) {
		next if $group =~ /^\./;
		next if param('group') && param('group') ne $group;
		next unless $user eq 'admin' || $user eq $group;
		next unless -d "$root/$group";
		open LMI, "$root/$group/.lmi" and do {
			$lmi->{$group}->{_} = a({-href=><LMI>}, img({-src=>'/lmi_title_rc.png', -border=>0, -width=>16, -height=>16}));
			close LMI;
		};
		$lmi->{$group}->{_} ||= '';
		opendir SYSTEMGROUP, "$root/$group" or die $!;
		while ( my $system = readdir(SYSTEMGROUP) ) {
			next if $system =~ /^\./;
			next if param('system') && param('system') ne $system;
			next unless -d "$root/$group/$system";
			open LMI, "$root/$group/$system/.lmi" and do {
				$lmi->{$group}->{$system} = a({-href=><LMI>}, img({-src=>'/lmi_title_rc.png', -border=>0, -width=>16, -height=>16}));
				close LMI;
			};
			$lmi->{$group}->{$system} ||= '';
			open DETAILS, "$root/$group/$system/details.csv" or next;
			my @last = (('')x12);
			while ( $_ = <DETAILS> ) {
				local @_ = split m!;!;
				my $tscolor = '';
				my $tsstatus = '';
				if ( $TIMESTAMPS-UnixDate(ParseDate("$_[0] $_[1]"), '%s') >= 24*60*60 ) {
					$tsstatus = 'ALERT';
					$tscolor = 'red';
				} elsif ( $TIMESTAMPS-UnixDate(ParseDate("$_[0] $_[1]"), '%s') >= 1*60*60 ) {
					$tsstatus = 'WARN';
					$tscolor = 'yellow';
				} else {
					$tsstatus = 'OK';
					$tscolor = 'green';
				}
				my $color = '';
				if ( $_[6] eq 'ALERT' ) {
					$color='red';
				} elsif ( $_[6] eq 'WARN' ) {
					$color='yellow';
				} elsif ( $_[6] eq 'OK' ) {
					$color='green';
				} elsif ( $_[6] eq 'INFO' ) {
					$color='white';
				} else {
					$color='blue';
				}
				$_[7] =~ s/(\.\d)0%$/$1%/;
				$_[7] =~ s/\.0%$/%/;
				next if $_[6] eq 'INFO' && !param('system') && not grep { $_ eq 'INFO' } param('status');

				next unless want({timestamp=>0,group=>2,system=>3,pgroup=>4,property=>5,status=>6}, $tsstatus, @_[1..$#_]);

				$COUNT->{$_[2]}->{_}->{$_[6]} ||= 0;
				$COUNT->{$_[2]}->{_}->{$_[6]}++;
				$COUNT->{$_[2]}->{$_[3]}->{$_[6]} ||= 0;
				$COUNT->{$_[2]}->{$_[3]}->{$_[6]}++;
				$COUNT->{$_[2]}->{_}->{NOTOK} ||= 0;
				$COUNT->{$_[2]}->{_}->{NOTOK}++ unless $_[6] eq 'INFO' || $_[6] eq 'OK';
				$COUNT->{$_[2]}->{$_[3]}->{NOTOK} ||= 0;
				$COUNT->{$_[2]}->{$_[3]}->{NOTOK}++ unless $_[6] eq 'INFO' || $_[6] eq 'OK';
				$COUNT->{$_[2]}->{_}->{'TS'.$tsstatus} ||= 0;
				$COUNT->{$_[2]}->{_}->{'TS'.$tsstatus}++ unless $COUNT->{$_[2]}->{$_[3]}->{'TS'.$tsstatus};
				$COUNT->{$_[2]}->{$_[3]}->{'TS'.$tsstatus} ||= 0;
				$COUNT->{$_[2]}->{$_[3]}->{'TS'.$tsstatus}=1;

				$details->{$group}->{$system}->{$.} = {
					date=>$_[0],
					time=>$_[1],
					timestamp=>"$_[0] $_[1]",
					tsstatus=>$tsstatus,
					tscolor=>$tscolor,
					group=>$_[2],
					system=>$_[3],
					pgroup=>$_[4],
					property=>$_[5],
					status=>$_[6],
					color=>$color,
					up_percent=>$_[7],
					up_time=>$_[8],
					value=>$_[9],
					details=>$_[6] eq 'INFO' && !param('system') && (grep { $_ eq 'INFO' } param('status')) && length($_[-1]) > 1000 ? a({-href=>"/?list=details&group=$_[2]&system=$_[3]&status=INFO"}, "Too large, click here to drill down") : $_[-1],
				};
	#			push @details, $_ if (!param('pgroup') && !param('property')) || (param('pgroup') && param('pgroup') eq $_[4]) || (param('property') && param('property') eq $_[5]);
			}
			close DETAILS;
		}
		closedir SYSTEMGROUP;
	}
	closedir ROOT;
	return (keys %{$details} ? $details : undef), (keys %{$lmi} ? $lmi : undef);
}

sub want {
	my $want = shift;
	my $ok = 0;
	while ( my ($param, $field) = each(%{$want}) ) {
		my @param = ();
		if ( @param = grep { /^!/ } param($param) ) {
			return 0 if grep { $_ eq "!$_[$field]" } @param;
		} elsif ( @param = grep { /^[^!]/ } param($param) ) {
			return 0 unless grep { $_ eq $_[$field] } @param;
		}
	}
	return 1;
}

sub setupsession {
	my $user = $ENV{USER} if $ENV{USER};
	$user = param('user') if param('user');
	$user = $session->param('user') if $session->param('user');
	$user ||= '';
	my $pass = md5_hex($ENV{PASS}) if $ENV{PASS};
	$pass = md5_hex(param('pass')) if param('pass');
	$pass = $session->param('pass') if $session->param('pass');
	$pass ||= '';

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

	print $session->header;

	return $user, $pass;
}

sub htmlmenu {
	my @menu = ref $_[0] eq 'ARRAY' ? @{$_[0]} : ();
	my @submenu = ref $_[1] eq 'ARRAY' ? @{$_[1]} : ();
	return join(br, join(' / ', @menu), join (' / ', @submenu));
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
<p>
$TIMESTAMP
<br>
HEAD
}

sub htmlfoot {
return <<FOOT;
<p>&nbsp;<p>
<font size="-2">Monitoring with <a href="http://www.cogent-it.com/software/cemosshe/">CeMoSShE</a>
</center>
</body>
</html>
FOOT
}
