#!/usr/bin/python
'''
NINJA SNAP for ZFS
@author: The Ninja Geek <ninjageek@theninjageek.co.za>

This file is used for creating ZFS snapshots of datasets.
It has an option to create snapshots locally and optionally copy to remote ZFS server and restore
'''

import subprocess
import datetime
import time
import argparse
import sys

# Arguments to be parsed via command line
parser=argparse.ArgumentParser(description="take some snapshots")
parser.add_argument("-d", help="The name of the ZFS pool/dataset to Snapshot")
parser.add_argument("-n",help="The prefix name used for the snapshot(s)")
parser.add_argument("-r",help="Recursively take snapshots",action="store_true")
parser.add_argument("-k",type=int, metavar="n",help="Keep n older snapshots with same name. Otherwise delete none.")
parser.add_argument("--list", help="List the Snapshots for a ZFS dataset", action="store_true")
parser.add_argument("--verbose", help="verbose output", action="store_true")
parser.add_argument("--target", help="e.g. \"hostname\""" - the hostname of the target system to backup and restore(only if --restore option is set) snapshots to.", default=None)

args = parser.parse_args()

#code variables:
dataset = args.d
prefix = args.n
remote = args.target
timenow = datetime.datetime.today().strftime("%a.%d.%b.%Y-%H:%M:%S") 

#code definitions:
def ninja_info(dataset):
    '''check ZFS info/list'''
    info = subprocess.check_output("zfs list -o name -t snapshot -H -r "+dataset, shell=True).split("\n")
    info_list = []
    dataset = dataset+"@"
    for snapshot in info:
        if not snapshot.startswith(dataset):
            info_list.append(snapshot)
    map(info.remove, info_list)
    return info

def ninja_info_rem(remote, dataset):
    '''check ZFS info/list'''
    info = subprocess.check_output("ssh "+remote+" zfs list -o name -t snapshot -H -r "+dataset, shell=True).split("\n")
    info_list = []
    dataset = dataset+"@"
    for snapshot in info:
        if not snapshot.startswith(dataset):
            info_list.append(snapshot)
    map(info.remove, info_list)
    return info

def scrub_check(fs):
    '''Check if Scrub is running'''
    pool = fs.split("/")[0]
    output = subprocess.check_output("zpool status "+pool, shell=True)
    return "scrub in process" in output

def ninja_snap(dataset, prefix, verbose=False):
    '''Create Snapshot'''
    if prefix == None:
        prefix = "ninja_snap"
    if args.r == True:
        snap = "zfs snapshot -r "+dataset+"@"+prefix+"-"+timenow
    else:
        snap = "zfs snapshot "+dataset+"@"+prefix+"-"+timenow+"-FULL"
    if scrub_check(dataset):
        raise Exception, "Unable to perform snapshot as scrub is still running. Please wait for scrub to complete and then try again."
    if verbose:
        print snap
    subprocess.check_call(snap, shell=True)
    
def ninja_rem(remote, prefix, verbose=False):
    '''Send Snapshot to remote server'''
    if prefix == None:
        prefix = "ninja_snap"
    pool = dataset.split("/")[0]
    snapshot = dataset+"@"+prefix+"-"+timenow
    if len(ninja_info(dataset)) > 1:
        previous = ninja_info(dataset)[-2]
        send = "zfs send -R -I "+previous+" "+snapshot+" | ssh "+remote+" zfs receive -F "+dataset
        if verbose:
            print "Running Remote check"
        if ninja_remcheck(remote) != "":
            if verbose:
                print "Remote check did not find any errors, comparing local and remote snapshots"
            try:
                while ninja_remcompare(remote, dataset) != None:
                    sync = "zfs send -R -I "+ninja_remcompare(remote, dataset)+" "+previous+" | ssh "+remote+" zfs receive -F "+dataset
                    if verbose:
                        print "Local and Remote snapshots do not match, syncing older snapshots."
                        print sync
                    subprocess.check_output(sync, shell = True)
                else:
                    if verbose:
                        print "Local and Remote snapshots match, beginning send and recieve"
                        print send
                    subprocess.check_output(send, shell = True)
                if verbose:
                    print "Send/Recieve completed without Errors"
            except Exception:
                sys.exit(0)           
        else:
            raise Exception, "Matching dataset does not exist on remote server, please create dataset before continuing with backup process."
            sys.exit(0)
    if len(ninja_info(dataset)) <= 1:
        send = "zfs send -R "+snapshot+" | ssh "+remote+" zfs receive -F "+dataset
        if verbose:
            print "Running Remote check"
        if ninja_remcheck(remote) != "":
            if verbose:
                print "Remote check did not find any errors, beginning send and receive."
            try:
                subprocess.check_output(send, shell = True)
                if verbose:
                    print "Send/Recieve completed without Errors"
            except Exception:
                sys.exit(0)
        else:
            raise Exception, "Matching dataset does not exist on remote server, please create dataset before continuing with backup process."
            sys.exit(0)
    
def ninja_remcheck(remote):
    pool = dataset.split("/")[0]
    check = "ssh "+remote+" zfs list | grep "+pool
    try:
        subprocess.check_output(check, shell=True)
    except Exception:
        print "Error: dataset doesn't exist on remote server or remote server does not exist."
        sys.exit(0)

def ninja_remcompare(remote, dataset):
    local_snap = ninja_info(dataset)
    remote_snap = ninja_info_rem(remote, dataset)
    for snap in range(len(local_snap)-1):
        if local_snap[snap] not in remote_snap:
            return local_snap[snap-1]

def ninja_purge(dataset, prefix, keep_amount, verbose=False):
    '''purge snapshots older than defined amount'''
    if prefix == None:
        prefix = "ninja_snap"
    snaps = ninja_info(dataset)
    sremove = []
    for snapshot in snaps:
        s_part = snapshot.split("@")
        if (not s_part[1].startswith(prefix)) or (s_part[0] != dataset):
            sremove.append(snapshot)
    map(snaps.remove, sremove)

    remove_amount = len(snaps) - keep_amount
    if remove_amount > 0:
        for snap_to_purge in snaps[:remove_amount]:
            purge = "zfs destroy "+snap_to_purge
            if verbose:
                print purge
            subprocess.check_call(purge, shell=True)

def ninja_purge_rem(remote, dataset, prefix, keep_amount, verbose=False):
    '''purge snapshots older than defined amount'''
    if prefix == None:
        prefix = "ninja_snap"
    snaps = ninja_info_rem(remote, dataset)
    sremove = []
    for snapshot in snaps:
        s_part = snapshot.split("@")
        if (not s_part[1].startswith(prefix)) or (s_part[0] != dataset):
            sremove.append(snapshot)
    map(snaps.remove, sremove)

    remove_amount = len(snaps) - keep_amount
    if remove_amount > 0:
        for snap_to_purge in snaps[:remove_amount]:
            purge_rem = "ssh "+remote+" zfs destroy "+snap_to_purge
            if verbose:
                print purge_rem
            subprocess.check_call(purge_rem, shell=True)

#Program Code:

if args.d == None and args.list == True:
    print " --list command must have a valid dataset specified"
    sys.exit(0)
        
#Run Info arg:
if args.list == True:
    if args.target == None:
        print ninja_info(dataset)
    else:
        print ninja_info_rem(remote, dataset)

#Create Snapshots:
if args.d != None and args.list == False:
    #Locally only:
    if args.target == None:
        ninja_snap(dataset, prefix, verbose=args.verbose)
    #Local and remotely:
    else:
        ninja_snap(dataset, prefix, verbose=args.verbose)
        ninja_rem(remote, prefix, verbose=args.verbose)

#Cleanup Snapshots
if args.k != None and args.k >= 0:
    ninja_purge(dataset, prefix, args.k, verbose=args.verbose)
    if args.target != None:
        ninja_purge_rem(remote, dataset, prefix, args.k, verbose=args.verbose)
      
if args.d == None and args.list == False:
    print "Please enter a option or use -h for help, also -k and --target must be accompanied by a valid -d option"

