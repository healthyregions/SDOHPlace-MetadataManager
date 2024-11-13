#! /usr/bin/bash

THIS_DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)

sudo mv /var/solr/data/$1/conf /var/solr/data/$1/conf-backup-$(date +"%Y%m%d%H%M")
sudo cp $THIS_DIR/../solr/conf /var/solr/data/$1/ -r

sudo sed -i -e "s/{{SOLR_CORE}}/$1/g" /var/solr/data/$1/conf/solrconfig.xml

sudo service solr restart

