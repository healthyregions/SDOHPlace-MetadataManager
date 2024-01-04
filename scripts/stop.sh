#! /usr/bin/bash

THIS_DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)
PIDFILE=$THIS_DIR/.pid

if test -e $PIDFILE; then
    sudo kill $(cat $PIDFILE)
else
    echo "no $PIDFILE"
fi
