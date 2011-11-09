-----------------------------------------------------------------------
      			CeMoSShE  v11.11.08
 	   2011- by Stefan Adams <stefan@cogentinnovators.com>
-----------------------------------------------------------------------

CeMoSShE (CEntral MOnitoring in a Simple SHell Environment) is a simple,
lightweight (both in size and system requirements) server monitoring
package designed for secure and in-depth monitoring of a handful of
typical/critical internet systems.

-----------------------------------------------------------------------
      			MoSShE  v11.6.27
 	   2003- by Volker Tanger <volker.tanger@wyae.de>
-----------------------------------------------------------------------

As most of the servers/services I want to monitor are remote systems,
traditional NMS (relying on close-looped and/or unencrypted sessions) are
either big, complicated to install for safe remote monitoring, ressource
intense (when doing remote checks), lack a status history or a combination
thereof.

Thus I wrote this small, easily configured system. It originally was
intended for monitoring of single a handful of typical internet
systems. With the more recent system and grouping features monitoring
of serious numbers of systems is easily possible.

MoSSHe supports email alerts and SLA monitoring out of the box - and
whatever you can script. 

The system is programmed in plain (Bourne) SH, and to be compatible
with BASH and Busybox so it can easily be deployed on embedded systems.

Monitoring is designed to be distributed over multiple systems,
usually running locally. As no parameters are accepted from outside,
checks cannot be tampered or misused from outside. 

The system is designed to allow decentralized checks and evaluation as
well as classical agent-based checks with centralized data
accumulation. 

Agent data is transferred via HTTP, so available web servers can be
co-used for agent data transfer. Additionally each agent creates
simple (static) HTML pages with full and condensed status reports on
each system, allowing simple local checks.


Requirements for CeMoSSHe:
	* Unix Shell (Bourne-SH, BASH, Busybox)
	* standard Unix text tools (fgrep, cut, head, mail, time, date,
	  paste, sed...)
	* "netcat" networking tool
	* curl >= 7.18.0
	
for single checks only if performed:
	* "pstree" for tree view of process list
	* "dig" for DNS check
	* "free" memory display for memory check
	* "lpq" BSD(compatible) printing for printing check
	* "mailq" if running the mail queue check
	* "mbmon" or "lm-sensors" motherboard check for temp/fan check
	* "smbclient" for samba check
	* [future] "snmp" networking tools (especiall "snmpget") for SNMP check
	* /proc/mdstat for Linux MD0 SoftRAID checks
	* "smartctl" (smartmontools) for HD health checks
	* "tw_cli" from 3ware (now: LSI) for Raid3ware checks 
	* "lspci" for view of hardware
	* "lshw" for view of hardware
	
for PUSH configuration: 
	* ftp server with incoming directory 
	* SCP server with incoming directory 
	* fileserver (SMB) with incoming directory


Hardware requirements:
	A difficult question. As the checks are run and evaluated
	locally on each system it is nearly impossible to "overload"
	the server as is with other monitoring systems. 

	The system is a shell script, so no big size components here,
	either. For a webserver (nearly) any HTTPD is fine. No
	database needed - everything is plain text. 



KNOWN ISSUES:
	- currently (11.10.x) only works in BASH, but not in BOURNE 
	  shell / Busybox, needs compatibility cleanup


FEATURE WISH LIST / ROADMAP:
	* SNMP query (general)
	* SNMP especially for Windows servers	
	* local checks for Windows writing to file for passive checks
	  see above: PUSH reaper - ideas for builtins:
	  	systeminfo.exe
		fsutil fsinfo ntfsinfo C:
	  or 	http://www.paulsadowski.com/WSH/cmdprogs.htm
	* local checks:
		- disk usage of single directory	  
		- disk usage of subdirectories (poor-mans-quota)
		- check number of users (via "w" command)
		  (implemented as a "show" -- should this be a check?)
	* network checks:
		- MySQL checks	
	* alerting:
		- IM alerts via jabber
		- send alerts on ALERT status only


Updates will be available at   http://www.cogent-it.com/software/cemosshe/
Please check there for updates prior to submitting patches!

There currently NO user/developer mailing list available. Stay tuned.

For bug reports and suggestions or if you just want to talk to me
please contact me at stefan@cogentinnovators.com


-----------------------------------------------------------------------
Monitoring server Setup
-----------------------------------------------------------------------

Get and unzip the archive - usually in /usr/local/lib/cemosshe.



Edit the 'cemosshe' file and set the environment

	SYSTEMGROUP	GROUPname for this server

	SYSTEMNAME	HOSTname of this server
	
	PROPERTYGROUP	GROUPname for this property
	
	DATADIR	location of CEMOSSHE scripts (/usr/local/lib/cemosshe/Data)

	TEMPDIR	for temporary files (default: /tmp)


In the 'cemosshe' shell script file you now can configure the checks to be
run - usually you can set warning and alert trigger levels


#=========================================================
# Local Shows
#=========================================================

PstreeShow	pstree -capuA (collapsable)
IfconfigShow	ifconfig (custom display) (collapsable)
DfShow		df -hP (collapsable)
RouteShow	route -n (collapsable)
WShow		w (collapsable)
UptimeShow	uptime (collapsable)
FreeShow	free (collapsable)
NetstatShow	netstat -pan | grep "^tcp.*LISTEN" (collapsable)
LastLoginShow	last -1 (collapsable)
HostNotesShow	cat /etc/host-notes (collapsable)
PackagesShow	rpm -qa (OR) dpkg-query -l (collapsable)
SysInfoShow	landscape-sysinfo --exclude-sysinfo-plugins=LandscapeLink

#=========================================================
# Local Checks
#=========================================================

SnapshotsCheck		Check for recent snapshots

DaysUpCheck		notify of recent reboot

UbuntuUpdatesAvailable	number of package updates available (ubuntu)
UbuntuReleaseUpgrade	is a release upgrade available? (ubuntu)
UbuntuRebootRequired	is a reboot required according to system? (ubuntu)

HDCheck 		minimum free space on a filesystem
LoadCheck		maximum load of a system
MemCheck		minimum free RAM

ProcessCheck		maximum processes running
ZombieCheck		maximum zombie processes
ShellCheck		maximum shells for root / other users

NetworkErrorsCheck	percentage of errors on interface
NetworkTrafficCheck	maximum kbit/s network throughput

FileCheck		check file existing (check PIDs or named pipes)
ProcCheck		check for process existing

FileTooOld 		check whether file was modified not too long ago
			(e.g. for checking whether a backup has run)
FileTooBig		check for files growing too much - esp. useful
			for logfiles (no logrotate/gallopping problems) 

MailqCheck		maximum number of mails in queue
PrintCheck		maximum number of print jobs in queue

MBMonCheck		Motherboard-checks: maximum temperature, fan speeds (mbmon)
HardwareFan		Hardware-Check: checks for too low or too high fan speed (lm-sensors) 
HardwareTemp		Hardware-Check: checks for too temperatures (lm-sensors) 

SmartMonHealth		health status of hard discs
Raid3ware		OK status of 3ware RAID controllers
RaidCheck		checks md0 RAID  (WARN=syncing, ALERT=fail)

LogEntryCheck		maximum number of message matches in logfiles
			(used to check for bruteforcing, see examples in CEMOSSHE)

CheckFileChanges	compare current file to known-good copy
CheckConfigChanges	compare config (command) to known-good copy


#=========================================================
# Network Checks
#=========================================================

PingPartner		maximum ping loss and avg. roundtrip
PingTime 		max roundtrip time regardless loss
PingLoss		max % Loss regardless roundtrip

TCPing			generic TCP connect ping

SAMBA			checks for Microsoft file server (SMB/CIFS/Samba)

HTTPheader		http server return code
HTTPheadermatch		checks for named return code (usually 302-Moved)
HTTPcontentmatch	 check for web site content

FTPcheck		checks for FTP service

SSHcheck		checks for SSH service

POP3check		checks for POP3 service
IMAPcheck		checks for IMAP service
SMTPcheck		checks for SMTP mail service

RBLcheckIP		checks whether an IP address is listed on RBL
RBLcheckFQDN		checks whether a named system is listed on RBL

DNSquery		checks whether a DNS response is given
DNSmatch		checks a DNS response against expected value


#=========================================================
# Centralize data *to* other servers
#=========================================================

Typical setup is to monitor multiple customer servers without opening
a TCP listener on them to reduce possible attack surface on those
systems. Instead have them send the information files to your own,
dedicated incoming monitoring system using battle-proven file transfer
system servers and methods:  ftp-incoming, ssh/scp.

Or to monitor systems within a LAN without having to run additional
network services (except maybe the network file system mounter).

You can combine centralizing functions sequentially. You can set up a
"internet monitoring" server in a DMZ, receiving monitoring data from
customers servers via FTP and SCP - and pulling other infos off other
hosting systems via ImportAgent. Using separate (password-protected)
customer incoming monitoring directories, you even can offer split
monitoring: you pull all your customers from the incoming server - and
each customer can pull the already accumulated monitoring for their
systems from that machine, too.

You can mix and combine ad lib - just make damn sure not to create
loops, otherwise your logs will explode.


Finalize		Run this after all the checks for processing
			for Syslog, SLA, etc
PushResults		Server to push data results to
LogTo			Keep a running log of the data results


-----------------------------------------------------------------------
Usage
-----------------------------------------------------------------------

Adapt the "cemosshe" script. 

Quick setup:
------------
* make sure you have NMAP installed
* change to the TOOLS directory.
* run  ./create_cemosshe.sh MYNETWORKFILE ipaddress/mask
* adapt MYNETWORKFILE (especially setting the right mail addresses and 
  paths!) and rename it to ../cemosshe

For example running
	./create_cemosshe.sh ../cemosshe 192.168.0.0/16
will scan your local network (in this example: 192.168.0.0/16) and 
create a basic monitoring from the services found.


-----------------------------------------------------------------------
Known/common Problems and Maintenance
-----------------------------------------------------------------------

(none yet)



-----------------------------------------------------------------------
Customizing Checks & Writing your own
-----------------------------------------------------------------------

Writing your own:

A check must terminate within a given (short) timeframe regardless
circumstances - so make sure there are timeouts builtin or configured.
If not, your complete MoSSHe might hang when this check stops.

Scripts (better: shell funcrions) must write a status line to
	$TEMPDIR/tmp.$$.collected.tmp

A check *must* give back the results in ONE LINE PER STATUS ONLY in
the format: 
date;time;systemgroup;systemname;propertygroup;propertyname;status;numeric;long


DATE	in ISO format: yyyy-mm-dd   
	with yyyy = 4digit year, mm=2digit month, dd=2digit day
	
TIME	HH:MM:SS - 24hour time, all 2digit
	this is the time local to MoSSHe server for all PING and service
	checks, but local time of the server checked when using imported
	checks

SYSTEMGROUP
	Domain name or some group name for the system as configured in mosshe

SYSTEMNAME
	Host name or IP address of the system as configured in mosshe

PROPERTYGROUP
	Groupname for the coming list of checks

PROPERTYNAME
	(short) name of the check. 

STATUS	any status of: OK, INFO, WARN, ALERT, UNDEF

NUMERIC	the numeric value of the test, e.g. LOAD number, free megabytes, etc.
	It must be a valid FLOAT or INT number to be displayed nicely.

LONG	A longer text with details to the status. Should be short enough to
	fit into one line of the web display for nicer display, though.


Here an example of the output of a number of checks - the first 6 checks
after PING are all from a single LOCALCHECK script, btw.

	2004-07-23;23:55:32;Home;kali;Network Checks;ping;OK;1;host up
	2004-07-23;23:55:32;Home;kali;System Checks;/dev/hda1;OK;4054;Disk free
	2004-07-23;23:55:32;Home;kali;System Checks;/dev/hda2;OK;1395;Disk free
	2004-07-23;23:55:32;Home;kali;System Checks;/dev/hdb3;OK;2817;Disk free
	2004-07-23;23:55:32;Home;kali;System Checks;load;OK;0.80;Load: 0.80
	2004-07-23;23:55:32;Home;kali;System Checks;processes;OK;76;Total processes: 76
	2004-07-23;23:55:32;Home;kali;System Checks;zombies;OK;0;Zombie processes: 0 = ok
	2004-07-23;23:55:34;Home;hermes;Network Checks;ping;OK;1;host up


Please keep in mind that CeMoSSHe is designed to be lean, small, efficient.
Thus having to install a JSP/EJB server only to install one singular check
usually is not considered overly adequate. 

Small, simple, secure - that's the way we should go.


If you have a nice (free) check that could be of use to other people, please
send it to me so I can include it into the distribution.


-----------------------------------------------------------------------
Shortcut: Distributable under  GPL
-----------------------------------------------------------------------
Copyright (C) 2003- Volker Tanger
Copyright (C) 2011- Stefan Adams

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or (at
your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
USA. or on their website http://www.gnu.org/copyleft/gpl.html

-----------------------------------------------------------------------

