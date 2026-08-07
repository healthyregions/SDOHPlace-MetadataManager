#! /usr/bin/bash

THIS_DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)

echo "stopping..."
bash $THIS_DIR/stop_flask.sh
sleep 2
echo "starting..."
bash $THIS_DIR/start_flask.sh
echo "done."
