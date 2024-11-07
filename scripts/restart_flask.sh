#! /usr/bin/bash

THIS_DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)

echo "stopping..."
source $THIS_DIR/stop.sh
sleep 1
echo "starting..."
source $THIS_DIR/start.sh
echo "done."
