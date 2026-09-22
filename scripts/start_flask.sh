#! /usr/bin/bash

THIS_DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)
PIDFILE=$THIS_DIR/.pid
LOGFILE=$THIS_DIR/.log

set -a # automatically export all variables
source $THIS_DIR/../.env
set +a

# Spatial uploads stream through Flask on their way to S3, so a worker can be
# busy for minutes on a large file. The default 30s timeout kills those workers
# mid-request; keep this at least as high as the proxy's read timeout.
$THIS_DIR/../env/bin/gunicorn -w 4 manager.app:app \
    --daemon \
    --timeout 900 \
    --graceful-timeout 900 \
    --pid $PIDFILE \
    --log-file $LOGFILE \
    --log-level DEBUG \
    --bind 0.0.0.0:$PORT \
    --capture-output
