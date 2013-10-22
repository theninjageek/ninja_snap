Ninja Snap ZFS snapshot creation script

This is a python script for creating Full and recursive ZFS snapshots locally and remotely.
With this script you can either create the snapshots on your local ZFS server or you can also copy the snapshots across to a remote ZFS server for backup purposes.

When using the remote option to backup snapshots to a remote server, the script will first check that the remote server has the same pool created as the local server, as this is required for the script to pass correctly.

In the event that a single run has issues backing up to the remote server, such as when a connection drops mid backup, the next run will not complete correctly as the remote snapshots need to match the local snapshots for an zfs send -I to succeed. To combat this the script will compare the snapshots between the local and remote server on each run, when the snapshots on the local server is more than 1, and will sync any missing snapshots before proceeding with the current snapshot send/receive.

Usage:
./ninja_snap.py -d {dataset} -n {prefix name} -r -k {number} --list --verbose --target

Arguments explained:
-h = help
-d = valid dataset name (required)
-n = snapshot prefix name (optional - if not supplied snapshots will be named ninja_snap-{Date})
-r = recursive (optional - if not used then snapshots will have FULL at the end of snapshot file name)
-k = amount of snapshots to keep (optional - keep the latest amount of snapshots and purge the rest)
--list = list all snapshots belonging to the specified dataset (optional)
--verbose = verbose output (optional)
--target = target hostname or IP address (optional - if supplied, the snapshots will backup to a remote server)

In the event the --target option is supplied then the "--list" option will display the remote snapshots not the local and "-k" will run a purge against the local and the remote snapshots.

This script is free to use and fork if you like.

Created by Lionel "The Ninja Geek".

ninjageek_at_theninjageek.co.za
