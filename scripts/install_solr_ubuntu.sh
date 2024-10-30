#! /usr/bin/bash

THIS_DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)

set -a # automatically export all variables
source $THIS_DIR/../.env
set +a

sudo apt install default-jdk -y

wget https://dlcdn.apache.org/solr/solr/9.1.1/solr-9.1.1.tgz
tar xzf solr-9.1.1.tgz solr-9.1.1/bin/install_solr_service.sh --strip-components=2

sudo bash ./install_solr_service.sh solr-9.1.1.tgz
rm $THIS_DIR/install_solr_service.sh

# now set jetty to be accessible from public ip
# manually change SOLR_JETTY_HOST to "0.0.0.0" and uncomment
sudo cp $THIS_DIR/../solr/solr.in.sh /etc/default/solr.in.sh

sudo service solr restart
