#! /usr/bin/bash

THIS_DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)
PIDFILE=$THIS_DIR/.pid
LOGFILE=$THIS_DIR/.log

$THIS_DIR/../env/bin/gunicorn -w 4 MetadataManager.manager.app:app \
    --daemon \
    --pid $PIDFILE \
    --log-file $LOGFILE \
    --log-level DEBUG \
    --bind 0.0.0.0