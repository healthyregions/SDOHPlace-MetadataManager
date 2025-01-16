#! /usr/bin/bash

THIS_DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)
PIDFILE=$THIS_DIR/.pid
LOGFILE=$THIS_DIR/.log

set -a # automatically export all variables
source $THIS_DIR/../.env
set +a

$THIS_DIR/../env/bin/gunicorn -w 4 manager.app:app \
    --daemon \
    --pid $PIDFILE \
    --log-file $LOGFILE \
    --log-level DEBUG \
    --bind 0.0.0.0:$PORT \
    --capture-output
